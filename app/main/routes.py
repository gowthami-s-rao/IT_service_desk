from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import Ticket

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    if current_user.is_admin():
        return render_template("main/admin_dashboard.html")
    tickets = Ticket.query.filter_by(employee_id=current_user.id).order_by(Ticket.created_at.desc()).limit(6).all()
    return render_template("main/dashboard.html", tickets=tickets)


@main_bp.route("/new-ticket")
@login_required
def new_ticket():
    return render_template("main/new_ticket.html")


@main_bp.route("/tickets")
@login_required
def tickets_list():
    return render_template("main/tickets.html")


@main_bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not current_user.is_admin() and ticket.employee_id != current_user.id:
        abort(403)
    return render_template("main/ticket_detail.html", ticket=ticket)


@main_bp.route("/knowledge-base")
@login_required
def knowledge_base():
    return render_template("main/knowledge_base.html")


@main_bp.route("/admin/knowledge")
@login_required
def admin_knowledge():
    if not current_user.is_admin():
        abort(403)
    return render_template("main/admin_knowledge.html")
