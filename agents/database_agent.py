"""
Database Agent — checks employee, device, and past-ticket information
directly from SQLite to ground the response in real account/device state.
"""
from app.models import Device, Ticket


def check_employee_context(employee_id: int, category: str) -> dict:
    devices = Device.query.filter_by(owner_id=employee_id).all()

    flagged_devices = [d for d in devices if d.status in ("offline", "needs_update", "flagged")]

    recent_tickets = (
        Ticket.query.filter_by(employee_id=employee_id, category=category)
        .order_by(Ticket.created_at.desc())
        .limit(3)
        .all()
    )

    similar_open_ticket = (
        Ticket.query.filter_by(employee_id=employee_id, category=category)
        .filter(Ticket.status.in_(["open", "in_progress"]))
        .first()
    )

    return {
        "device_count": len(devices),
        "devices": [d.to_dict() for d in devices],
        "flagged_devices": [d.to_dict() for d in flagged_devices],
        "recent_similar_tickets": [t.to_dict() for t in recent_tickets],
        "has_open_duplicate": similar_open_ticket is not None,
    }
