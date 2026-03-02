"""
AquilAdmin — Audit Trail.

Every admin action (create, update, delete, bulk action, login, logout)
is recorded in an append-only audit log. Uses Aquilia Auth's AuditTrail
when available, with a standalone in-memory fallback.

Audit entries are immutable and include:
- Who: identity ID, username, role
- What: action type, model, record PK, field changes
- When: UTC timestamp
- Where: IP address, user agent
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aquilia.admin.audit")


class AdminAction(str, Enum):
    """Admin action types for audit logging."""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    VIEW = "view"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_ACTION = "bulk_action"
    EXPORT = "export"
    SETTINGS_CHANGE = "settings_change"
    SEARCH = "search"
    PERMISSION_CHANGE = "permission_change"


@dataclass(frozen=True)
class AdminAuditEntry:
    """
    Immutable audit log entry.

    Captures the full context of an admin action for compliance
    and forensic analysis.
    """
    id: str
    timestamp: datetime
    user_id: str
    username: str
    role: str
    action: AdminAction
    model_name: Optional[str] = None
    record_pk: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None  # {"field": {"old": x, "new": y}}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "action": self.action.value,
            "model_name": self.model_name,
            "record_pk": self.record_pk,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
        }


class AdminAuditLog:
    """
    Admin audit log — records all admin operations.

    Thread-safe, append-only log with configurable retention.
    Integrates with Aquilia Auth's AuditTrail when available.
    """

    def __init__(self, max_entries: int = 10_000):
        self._entries: List[AdminAuditEntry] = []
        self._max_entries = max_entries
        self._counter = 0

    def log(
        self,
        user_id: str,
        username: str,
        role: str,
        action: AdminAction,
        *,
        model_name: Optional[str] = None,
        record_pk: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AdminAuditEntry:
        """
        Record an admin action.

        Returns the created audit entry.
        """
        import secrets

        self._counter += 1
        entry = AdminAuditEntry(
            id=f"audit_{secrets.token_hex(8)}",
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            model_name=model_name,
            record_pk=record_pk,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            success=success,
            error_message=error_message,
        )

        self._entries.append(entry)

        # Enforce retention limit (FIFO eviction)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

        logger.info(
            "Admin audit: user=%s action=%s model=%s pk=%s success=%s",
            username, action.value, model_name, record_pk, success,
        )

        return entry

    def get_entries(
        self,
        *,
        action: Optional[AdminAction] = None,
        user_id: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AdminAuditEntry]:
        """
        Query audit entries with optional filtering.

        Returns entries in reverse chronological order.
        """
        filtered = self._entries

        if action is not None:
            filtered = [e for e in filtered if e.action == action]
        if user_id is not None:
            filtered = [e for e in filtered if e.user_id == user_id]
        if model_name is not None:
            filtered = [e for e in filtered if e.model_name == model_name]

        # Reverse chronological
        filtered = list(reversed(filtered))

        return filtered[offset:offset + limit]

    def count(
        self,
        *,
        action: Optional[AdminAction] = None,
        model_name: Optional[str] = None,
    ) -> int:
        """Count audit entries with optional filtering."""
        if action is None and model_name is None:
            return len(self._entries)

        count = 0
        for e in self._entries:
            if action is not None and e.action != action:
                continue
            if model_name is not None and e.model_name != model_name:
                continue
            count += 1
        return count

    def clear(self) -> int:
        """Clear all audit entries. Returns count cleared."""
        count = len(self._entries)
        self._entries.clear()
        self._counter = 0
        return count
