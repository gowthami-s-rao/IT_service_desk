from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")  # employee | agent | admin
    full_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active_flag = db.Column("is_active", db.Boolean, default=True)

    tickets = db.relationship("Ticket", backref="employee", lazy="dynamic",
                               foreign_keys="Ticket.employee_id")
    devices = db.relationship("Device", backref="owner", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_flag

    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "department": self.department,
            "role": self.role,
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    device_name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(50))       # laptop, desktop, mobile, VPN client...
    os_name = db.Column(db.String(80))
    ip_address = db.Column(db.String(45))
    status = db.Column(db.String(30), default="online")  # online, offline, needs_update, flagged
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "os_name": self.os_name,
            "ip_address": self.ip_address,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class KnowledgeArticle(db.Model):
    __tablename__ = "knowledge_articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)  # network, hardware, software, account, other
    keywords = db.Column(db.String(300))  # comma separated
    content = db.Column(db.Text, nullable=False)
    steps = db.Column(db.Text)  # newline separated troubleshooting steps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "keywords": self.keywords,
            "content": self.content,
            "steps": self.steps.split("\n") if self.steps else [],
        }


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), default="uncategorized")
    priority = db.Column(db.String(20), default="medium")  # low, medium, high, critical
    status = db.Column(db.String(30), default="open")  # open, in_progress, resolved, escalated, closed
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship("TicketMessage", backref="ticket", lazy="dynamic",
                                cascade="all, delete-orphan", order_by="TicketMessage.created_at")

    def to_dict(self, include_messages=False):
        data = {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.full_name if self.employee else None,
            "subject": self.subject,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data


class TicketMessage(db.Model):
    __tablename__ = "ticket_messages"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    sender = db.Column(db.String(30), nullable=False)  # employee | manager_agent | troubleshooting_agent |
                                                          # knowledge_agent | database_agent | response_agent | human
    content = db.Column(db.Text, nullable=False)
    meta = db.Column(db.Text)  # optional JSON string with structured agent output
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "content": self.content,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
