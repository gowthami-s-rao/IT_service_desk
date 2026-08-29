import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Ticket, TicketMessage, Device, KnowledgeArticle, User
from app.agents.orchestrator import run_service_desk

api_bp = Blueprint("api", __name__)


def _ticket_or_404(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return None
    if not current_user.is_admin() and ticket.employee_id != current_user.id:
        return None
    return ticket


@api_bp.route("/tickets", methods=["GET"])
@login_required
def list_tickets():
    if current_user.is_admin():
        query = Ticket.query
        status = request.args.get("status")
        if status:
            query = query.filter_by(status=status)
        tickets = query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(employee_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tickets])


@api_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def get_ticket(ticket_id):
    ticket = _ticket_or_404(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket.to_dict(include_messages=True))


@api_bp.route("/tickets", methods=["POST"])
@login_required
def create_ticket():
    """
    Creates a ticket AND runs it through the multi-agent orchestration
    pipeline synchronously (Manager -> Troubleshooting -> Knowledge ->
    Database -> Response/Escalation), logging every agent step as a
    TicketMessage so the UI can render the full pipeline trace.
    """
    data = request.get_json(force=True) or {}
    subject = (data.get("subject") or "").strip()
    description = (data.get("description") or "").strip()

    if not subject or not description:
        return jsonify({"error": "Subject and description are required."}), 400

    ticket = Ticket(
        employee_id=current_user.id,
        subject=subject,
        description=description,
        status="in_progress",
    )
    db.session.add(ticket)
    db.session.commit()

    db.session.add(TicketMessage(ticket_id=ticket.id, sender="employee", content=description))
    db.session.commit()

    result = run_service_desk(current_user.id, description)

    for entry in result.get("log", []):
        if entry["agent"] == "employee":
            continue
        db.session.add(TicketMessage(
            ticket_id=ticket.id,
            sender=entry["agent"],
            content=entry["message"],
        ))

    ticket.category = result.get("category", "other")
    ticket.priority = result.get("priority", "medium")
    ticket.resolution = result.get("final_response")
    ticket.status = "escalated" if result.get("escalated") else "resolved"

    final_sender = "human_escalation" if result.get("escalated") else "response_agent"
    db.session.add(TicketMessage(ticket_id=ticket.id, sender=final_sender, content=result.get("final_response", "")))

    db.session.commit()

    return jsonify({
        "ticket": ticket.to_dict(include_messages=True),
        "pipeline_log": result.get("log", []),
        "steps": result.get("steps", []),
        "kb_articles": result.get("kb_articles", []),
        "db_context": result.get("db_context", {}),
    }), 201


@api_bp.route("/tickets/<int:ticket_id>/close", methods=["POST"])
@login_required
def close_ticket(ticket_id):
    ticket = _ticket_or_404(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    ticket.status = "closed"
    db.session.commit()
    return jsonify(ticket.to_dict())


@api_bp.route("/devices", methods=["GET"])
@login_required
def list_devices():
    devices = Device.query.filter_by(owner_id=current_user.id).all()
    return jsonify([d.to_dict() for d in devices])


@api_bp.route("/knowledge", methods=["GET"])
@login_required
def list_knowledge():
    articles = KnowledgeArticle.query.order_by(KnowledgeArticle.category).all()
    return jsonify([a.to_dict() for a in articles])


# ---- Admin-only endpoints ----

def _require_admin():
    if not current_user.is_admin():
        return jsonify({"error": "Admin access required."}), 403
    return None


@api_bp.route("/admin/stats", methods=["GET"])
@login_required
def admin_stats():
    guard = _require_admin()
    if guard:
        return guard
    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status="open").count()
    in_progress = Ticket.query.filter_by(status="in_progress").count()
    resolved = Ticket.query.filter_by(status="resolved").count()
    escalated = Ticket.query.filter_by(status="escalated").count()
    closed = Ticket.query.filter_by(status="closed").count()
    users_count = User.query.count()

    by_category = {}
    for t in Ticket.query.all():
        by_category[t.category] = by_category.get(t.category, 0) + 1

    return jsonify({
        "total_tickets": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "escalated": escalated,
        "closed": closed,
        "users_count": users_count,
        "by_category": by_category,
    })


@api_bp.route("/admin/knowledge", methods=["POST"])
@login_required
def admin_add_knowledge():
    guard = _require_admin()
    if guard:
        return guard
    data = request.get_json(force=True) or {}
    article = KnowledgeArticle(
        title=data.get("title", "").strip(),
        category=data.get("category", "other").strip(),
        keywords=data.get("keywords", "").strip(),
        content=data.get("content", "").strip(),
        steps=data.get("steps", "").strip(),
    )
    if not article.title or not article.content:
        return jsonify({"error": "Title and content are required."}), 400
    db.session.add(article)
    db.session.commit()
    return jsonify(article.to_dict()), 201


@api_bp.route("/admin/knowledge/<int:article_id>", methods=["DELETE"])
@login_required
def admin_delete_knowledge(article_id):
    guard = _require_admin()
    if guard:
        return guard
    article = KnowledgeArticle.query.get(article_id)
    if not article:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(article)
    db.session.commit()
    return jsonify({"deleted": True})
