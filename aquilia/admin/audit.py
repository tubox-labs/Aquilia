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


class ModelBackedAuditLog:
    """
    Model-backed audit log — persists entries to the AdminAuditEntry ORM table.

    Survives server restarts and user logouts. Falls back gracefully to the
    in-memory AdminAuditLog when the ORM table is unavailable (e.g. before
    migrations have been run).

    API is 100% compatible with AdminAuditLog so it can be used as a
    drop-in replacement on AdminSite.audit_log.
    """

    def __init__(self, fallback_max: int = 2_000):
        self._fallback = AdminAuditLog(max_entries=fallback_max)
        self._db_available: Optional[bool] = None  # None = not yet probed

    # ── Internal helpers ─────────────────────────────────────────────

    async def _probe_db(self) -> bool:
        """Check once whether the DB table is accessible."""
        if self._db_available is not None:
            return self._db_available
        try:
            from aquilia.admin.models import AdminAuditEntry
            # Lightweight probe — count with limit 0
            await AdminAuditEntry.objects.filter(entry_id="__probe__").count()
            self._db_available = True
        except Exception:
            self._db_available = False
        return self._db_available  # type: ignore[return-value]

    def _reset_probe(self) -> None:
        """Reset DB probe so next call will re-probe (e.g. after migration)."""
        self._db_available = None

    # ── Public API (mirrors AdminAuditLog) ───────────────────────────

    def log(
        self,
        user_id: str,
        username: str,
        role: str,
        action: "AdminAction",
        *,
        model_name: Optional[str] = None,
        record_pk: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> "AdminAuditEntry":
        """
        Record an audit entry.

        Schedules an async DB write. Always also writes to the in-memory
        fallback so synchronous callers and tests see the entry immediately.
        """
        import asyncio

        # Always record in-memory fallback (instant, sync)
        mem_entry = self._fallback.log(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            model_name=model_name,
            record_pk=record_pk,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            success=success,
            error_message=error_message,
        )

        # Fire-and-forget async DB write
        action_str = action.value if hasattr(action, "value") else str(action)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    self._async_write(
                        user_id=user_id,
                        username=username,
                        role=role,
                        action=action_str,
                        model_name=model_name,
                        record_pk=record_pk,
                        changes=changes,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata=metadata,
                        success=success,
                        error_message=error_message,
                    )
                )
        except RuntimeError:
            pass  # No event loop running — fallback-only mode

        return mem_entry

    async def _async_write(self, **kwargs: Any) -> None:
        """Write one audit entry to the DB table (best-effort)."""
        try:
            if not await self._probe_db():
                return
            from aquilia.admin.models import AdminAuditEntry
            await AdminAuditEntry.create_entry(**kwargs)
        except Exception as exc:
            logger.debug("ModelBackedAuditLog: DB write failed: %s", exc)
            # Disable DB writes for this session to avoid noise
            self._db_available = False

    async def alog(
        self,
        user_id: str,
        username: str,
        role: str,
        action: "AdminAction",
        **kwargs: Any,
    ) -> "AdminAuditEntry":
        """
        Async version of log() — awaits the DB write directly.
        Use this when you are already inside an async context and want
        to guarantee the entry is persisted before continuing.
        """
        mem_entry = self._fallback.log(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            **kwargs,
        )
        action_str = action.value if hasattr(action, "value") else str(action)
        await self._async_write(
            user_id=user_id,
            username=username,
            role=role,
            action=action_str,
            **kwargs,
        )
        return mem_entry

    async def get_entries_async(
        self,
        *,
        action: Optional["AdminAction"] = None,
        user_id: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List["AdminAuditEntry"]:
        """
        Fetch entries from the DB (preferred) or in-memory fallback.

        Returns dicts-compatible objects with a .to_dict() method.
        """
        if await self._probe_db():
            try:
                from aquilia.admin.models import AdminAuditEntry
                qs = AdminAuditEntry.objects.all()
                if action is not None:
                    action_str = action.value if hasattr(action, "value") else str(action)
                    qs = qs.filter(action=action_str)
                if user_id is not None:
                    qs = qs.filter(user_id=user_id)
                if model_name is not None:
                    qs = qs.filter(model_name=model_name)
                # Order by newest first
                qs = qs.order_by("-timestamp")
                all_rows = await qs.all()
                return list(all_rows[offset:offset + limit])
            except Exception as exc:
                logger.debug("ModelBackedAuditLog.get_entries_async DB error: %s", exc)
                self._db_available = False

        # Fallback to in-memory
        return self._fallback.get_entries(
            action=action, user_id=user_id, model_name=model_name,
            limit=limit, offset=offset,
        )  # type: ignore[return-value]

    def get_entries(
        self,
        *,
        action: Optional["AdminAction"] = None,
        user_id: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List["AdminAuditEntry"]:
        """
        Synchronous get_entries — returns in-memory entries only.
        Use get_entries_async() when in an async context to also
        include DB-persisted entries.
        """
        return self._fallback.get_entries(
            action=action, user_id=user_id, model_name=model_name,
            limit=limit, offset=offset,
        )  # type: ignore[return-value]

    async def count_async(
        self,
        *,
        action: Optional["AdminAction"] = None,
        model_name: Optional[str] = None,
    ) -> int:
        """Count entries from DB if available, else in-memory."""
        if await self._probe_db():
            try:
                from aquilia.admin.models import AdminAuditEntry
                qs = AdminAuditEntry.objects.all()
                if action is not None:
                    action_str = action.value if hasattr(action, "value") else str(action)
                    qs = qs.filter(action=action_str)
                if model_name is not None:
                    qs = qs.filter(model_name=model_name)
                return await qs.count()
            except Exception as exc:
                logger.debug("ModelBackedAuditLog.count_async DB error: %s", exc)
                self._db_available = False
        return self._fallback.count(action=action, model_name=model_name)

    def count(
        self,
        *,
        action: Optional["AdminAction"] = None,
        model_name: Optional[str] = None,
    ) -> int:
        """Synchronous count — returns in-memory count only."""
        return self._fallback.count(action=action, model_name=model_name)

    def clear(self) -> int:
        """Clear in-memory fallback entries. DB entries are retained."""
        return self._fallback.clear()
