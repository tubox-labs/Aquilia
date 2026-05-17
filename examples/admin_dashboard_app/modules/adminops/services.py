from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aquilia.admin.permissions import AdminPermission, AdminRole, has_admin_permission


class DemoIdentity:
    def __init__(self, role: AdminRole):
        self._role = role

    def is_active(self) -> bool:
        return True

    def get_attribute(self, name: str, default: Any = None) -> Any:
        if name == "admin_role":
            return self._role.value
        return default


@dataclass(slots=True)
class TicketRecord:
    key: str
    customer_email: str
    subject: str
    priority: str = "normal"
    assigned_to: str | None = None
    resolved: bool = False


class AdminOpsService:
    def __init__(self) -> None:
        self._tickets: dict[str, TicketRecord] = {}
        self._audit: list[dict[str, Any]] = []

    def create_ticket(self, record: TicketRecord, actor_role: AdminRole = AdminRole.STAFF) -> dict[str, Any]:
        identity = DemoIdentity(actor_role)
        if not has_admin_permission(identity, AdminPermission.MODEL_ADD):
            raise PermissionError("admin.model.add is required")
        self._tickets[record.key] = record
        self._audit.append(self._event("ticket.created", record.key, actor_role))
        return self._serialize(record)

    def assign_ticket(self, key: str, assignee: str, actor_role: AdminRole = AdminRole.STAFF) -> dict[str, Any]:
        identity = DemoIdentity(actor_role)
        if not has_admin_permission(identity, AdminPermission.MODEL_CHANGE):
            raise PermissionError("admin.model.change is required")
        ticket = self._tickets[key]
        ticket.assigned_to = assignee
        self._audit.append(self._event("ticket.assigned", key, actor_role, assignee=assignee))
        return self._serialize(ticket)

    def dashboard(self, actor_role: AdminRole = AdminRole.VIEWER) -> dict[str, Any]:
        identity = DemoIdentity(actor_role)
        can_export = has_admin_permission(identity, AdminPermission.MODEL_EXPORT)
        unresolved = [t for t in self._tickets.values() if not t.resolved]
        return {
            "tickets_total": len(self._tickets),
            "tickets_unresolved": len(unresolved),
            "can_export": can_export,
            "recent_audit": self._audit[-5:],
        }

    def _event(self, action: str, ticket_key: str, role: AdminRole, **extra: Any) -> dict[str, Any]:
        return {
            "action": action,
            "ticket": ticket_key,
            "role": role.value,
            "at": datetime.now(timezone.utc).isoformat(),
            **extra,
        }

    @staticmethod
    def _serialize(record: TicketRecord) -> dict[str, Any]:
        return {
            "key": record.key,
            "customer_email": record.customer_email,
            "subject": record.subject,
            "priority": record.priority,
            "assigned_to": record.assigned_to,
            "resolved": record.resolved,
        }
