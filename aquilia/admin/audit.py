"""
AquilAdmin -- Audit Trail.

Every admin action (create, update, delete, bulk action, login, logout)
is recorded in an append-only audit log. Uses Aquilia Auth's AuditTrail
when available, with a standalone in-memory fallback.

Persists entries to a `.crous` file in the workspace's `.aquilia/`
directory when CROUS is available, enabling history to survive restarts.

Audit entries are immutable and include:
- Who: identity ID, username, role
- What: action type, model, record PK, field changes
- When: UTC timestamp
- Where: IP address, user agent
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aquilia.admin.audit")


class AdminAction(str, Enum):
    """Admin action types for audit logging."""
    # ── Auth ─────────────────────────────────────────────────────────
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"

    # ── CRUD / Data ──────────────────────────────────────────────────
    VIEW = "view"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_ACTION = "bulk_action"
    EXPORT = "export"
    SEARCH = "search"

    # ── Settings & Permissions ───────────────────────────────────────
    SETTINGS_CHANGE = "settings_change"
    PERMISSION_CHANGE = "permission_change"

    # ── Module Page Views ────────────────────────────────────────────
    PAGE_VIEW = "page_view"

    # ── Admin User Management ────────────────────────────────────────
    ADMIN_USER_CREATE = "admin_user_create"
    ADMIN_USER_UPDATE = "admin_user_update"
    ADMIN_USER_DELETE = "admin_user_delete"

    # ── Container / Docker Infrastructure ────────────────────────────
    CONTAINER_ACTION = "container_action"
    CONTAINER_EXEC = "container_exec"
    CONTAINER_EXPORT = "container_export"
    DOCKER_PRUNE = "docker_prune"
    DOCKER_BUILD = "docker_build"
    IMAGE_ACTION = "image_action"
    IMAGE_TAG = "image_tag"
    COMPOSE_ACTION = "compose_action"
    VOLUME_ACTION = "volume_action"
    VOLUME_CREATE = "volume_create"
    NETWORK_ACTION = "network_action"
    NETWORK_CREATE = "network_create"

    # ── Storage / File Operations ────────────────────────────────────
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    FILE_DOWNLOAD = "file_download"

    # ── Profile ──────────────────────────────────────────────────────
    PROFILE_UPDATE = "profile_update"
    AVATAR_UPLOAD = "avatar_upload"
    PASSWORD_CHANGE = "password_change"

    # ── MLOps ────────────────────────────────────────────────────────
    ML_INFERENCE = "ml_inference"
    ML_BATCH_INFERENCE = "ml_batch_inference"
    ML_COMPARE = "ml_compare"
    ML_HEALTH_CHECK = "ml_health_check"
    ALERT_CONFIG = "alert_config"
    SNAPSHOT_EXPORT = "snapshot_export"

    # ── API Key Management ───────────────────────────────────────────
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    API_KEY_DELETE = "api_key_delete"

    # ── User Preferences ─────────────────────────────────────────────
    PREFERENCE_UPDATE = "preference_update"
    PREFERENCE_DELETE = "preference_delete"


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

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AdminAuditEntry":
        """Reconstruct an entry from a serialized dictionary."""
        ts = data.get("timestamp", "")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                ts = datetime.now(timezone.utc)
        return AdminAuditEntry(
            id=data.get("id", ""),
            timestamp=ts,
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            role=data.get("role", ""),
            action=AdminAction(data["action"]) if data.get("action") else AdminAction.VIEW,
            model_name=data.get("model_name"),
            record_pk=data.get("record_pk"),
            changes=data.get("changes"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            metadata=data.get("metadata") or {},
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )


# ── CROUS File Storage ──────────────────────────────────────────────


def _resolve_workspace_root() -> Optional[Path]:
    """
    Find the workspace root by looking for ``workspace.py`` or ``starter.py``
    in common locations relative to CWD.
    """
    cwd = Path(os.getcwd())
    for name in ("workspace.py", "starter.py"):
        for candidate in (cwd / name, cwd / "myapp" / name):
            if candidate.is_file():
                return candidate.parent
    return cwd  # fallback to CWD


def _get_crous_audit_path() -> Path:
    """Return the path to the CROUS audit file at ``workspace/.aquilia/audit.crous``."""
    root = _resolve_workspace_root()
    if root is None:
        root = Path(os.getcwd())
    aquilia_dir = root / ".aquilia"
    aquilia_dir.mkdir(parents=True, exist_ok=True)
    return aquilia_dir / "audit.crous"


class CrousAuditStore:
    """
    Thin persistence layer that stores/loads audit entries using the CROUS
    binary format.  Falls back to no-op if ``crous`` is not installed.

    Uses ``crous.append()`` for writes (append-only, perfect for audit)
    and ``crous.load()`` for reads.
    """

    def __init__(self) -> None:
        self._crous = None  # lazy-imported
        self._available: Optional[bool] = None
        self._path: Optional[Path] = None

    def _probe(self) -> bool:
        """Try to import crous once; cache the result."""
        if self._available is not None:
            return self._available
        try:
            import crous  # type: ignore[import-untyped]
            self._crous = crous
            self._path = _get_crous_audit_path()
            self._available = True
        except Exception:
            self._available = False
        return self._available  # type: ignore[return-value]

    # ── Write ────────────────────────────────────────────────────

    def persist(self, entry: "AdminAuditEntry") -> None:
        """Append a single audit entry to the .crous file."""
        if not self._probe():
            return
        try:
            self._crous.append(entry.to_dict(), str(self._path))
        except Exception:
            pass

    # ── Read ─────────────────────────────────────────────────────

    def load_all(self) -> List["AdminAuditEntry"]:
        """Load all persisted entries from the .crous file."""
        if not self._probe() or self._path is None or not self._path.exists():
            return []
        try:
            raw = self._crous.load(str(self._path))
            if raw is None:
                return []
            # crous.load returns a single dict when only one value,
            # or a list when multiple values were appended.
            if isinstance(raw, dict):
                raw = [raw]
            if not isinstance(raw, list):
                return []
            entries: List[AdminAuditEntry] = []
            for item in raw:
                if isinstance(item, dict):
                    try:
                        entries.append(AdminAuditEntry.from_dict(item))
                    except Exception:
                        continue
            return entries
        except Exception as exc:
            return []

    def load_for_record(self, model_name: str, record_pk: str) -> List["AdminAuditEntry"]:
        """Load only entries matching a specific model + pk (case-insensitive)."""
        all_entries = self.load_all()
        model_lower = model_name.lower()
        return [
            e for e in all_entries
            if (e.model_name or "").lower() == model_lower
            and str(e.record_pk or "") == str(record_pk)
        ]

    # ── Maintenance ──────────────────────────────────────────────

    def clear(self) -> None:
        """Remove the .crous audit file."""
        if self._path and self._path.exists():
            try:
                self._path.unlink()
            except Exception:
                pass

    def truncate(self, keep: int = 10_000) -> None:
        """Keep only the *keep* most recent entries."""
        entries = self.load_all()
        if len(entries) <= keep:
            return
        entries = entries[-keep:]
        self.clear()
        for e in entries:
            self.persist(e)


class AdminAuditLog:
    """
    Admin audit log -- records all admin operations.

    Thread-safe, append-only log with configurable retention.
    Integrates with Aquilia Auth's AuditTrail when available.

    Persists entries to a ``.crous`` file via :class:`CrousAuditStore`
    so audit history survives server restarts.
    """

    def __init__(self, max_entries: int = 10_000, *, persist: bool = False):
        self._entries: List[AdminAuditEntry] = []
        self._max_entries = max_entries
        self._counter = 0
        # Admin config reference -- set by AdminSite after config is parsed
        self._admin_config: Any = None
        # CROUS file persistence (opt-in)
        self._persist = persist
        self._crous_store = CrousAuditStore() if persist else None
        # Hydrate in-memory cache from persisted file
        self._hydrated = not persist  # skip hydration when not persisting

    def _hydrate(self) -> None:
        """Load persisted entries from the CROUS file into memory (once)."""
        if self._hydrated:
            return
        self._hydrated = True
        if self._crous_store is None:
            return
        try:
            persisted = self._crous_store.load_all()
            if persisted:
                # Merge: persisted entries first, then any already in memory
                existing_ids = {e.id for e in self._entries}
                for entry in persisted:
                    if entry.id not in existing_ids:
                        self._entries.insert(0, entry)
                # Sort by timestamp
                self._entries.sort(key=lambda e: e.timestamp)
                # Enforce retention
                if len(self._entries) > self._max_entries:
                    self._entries = self._entries[-self._max_entries:]
                self._counter = len(self._entries)
        except Exception:
            pass

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

        Respects the admin config's excluded actions, audit category
        switches (log_logins, log_views, log_searches), and the global
        audit enabled flag.  If the action is excluded, returns a
        sentinel entry but does **not** persist it.

        Returns the created audit entry.
        """
        # ── Check admin config filters ──
        if self._admin_config is not None:
            if not self._admin_config.is_action_allowed(action):
                # Return a stub entry without persisting
                import secrets
                return AdminAuditEntry(
                    id=f"audit_skip_{secrets.token_hex(4)}",
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

        # Persist to CROUS file
        if self._crous_store is not None:
            self._crous_store.persist(entry)

        # Enforce retention limit (FIFO eviction)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]


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
        Hydrates from the CROUS file on the first call.
        """
        self._hydrate()
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
        self._hydrate()
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
        if self._crous_store is not None:
            self._crous_store.clear()
        return count

    def get_history_for_record(
        self,
        model_name: str,
        record_pk: str,
    ) -> List["AdminAuditEntry"]:
        """Return all audit entries for a specific model + pk, newest-first."""
        self._hydrate()
        model_lower = model_name.lower()
        filtered = [
            e for e in self._entries
            if (e.model_name or "").lower() == model_lower
            and str(e.record_pk or "") == str(record_pk)
        ]
        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return filtered


class ModelBackedAuditLog:
    """
    Model-backed audit log -- persists entries to the AdminAuditEntry ORM table.

    Survives server restarts and user logouts. Falls back gracefully to the
    in-memory AdminAuditLog when the ORM table is unavailable (e.g. before
    migrations have been run).

    Also persists entries to a CROUS file in the workspace's ``.aquilia/``
    directory for durable audit history that survives restarts even without
    a database.

    API is 100% compatible with AdminAuditLog so it can be used as a
    drop-in replacement on AdminSite.audit_log.
    """

    def __init__(self, fallback_max: int = 2_000):
        # persist=False for the fallback: ModelBackedAuditLog manages its own
        # CROUS store directly rather than through the fallback's hydration.
        self._fallback = AdminAuditLog(max_entries=fallback_max, persist=False)
        self._db_available: Optional[bool] = None  # None = not yet probed
        # Admin config reference -- set by AdminSite after config is parsed
        self._admin_config: Any = None
        # CROUS file persistence (independent of fallback)
        self._crous_store = CrousAuditStore()
        # Tracks whether in-memory fallback has been hydrated from CROUS file.
        # Set to True by default; call start() to enable hydration from file.
        self._hydrated = True

    @property
    def admin_config(self):
        return self._admin_config

    @admin_config.setter
    def admin_config(self, value):
        self._admin_config = value
        # Propagate to fallback
        self._fallback._admin_config = value

    # ── Internal helpers ─────────────────────────────────────────────

    async def _probe_db(self) -> bool:
        """Check once whether the DB table is accessible."""
        if self._db_available is not None:
            return self._db_available
        try:
            from aquilia.admin.models import AdminAuditEntry
            # Lightweight probe -- count with limit 0
            await AdminAuditEntry.objects.filter(entry_id="__probe__").count()
            self._db_available = True
        except Exception:
            self._db_available = False
        return self._db_available  # type: ignore[return-value]

    def _reset_probe(self) -> None:
        """Reset DB probe so next call will re-probe (e.g. after migration)."""
        self._db_available = None

    def start(self) -> None:
        """
        Enable CROUS hydration and load persisted entries.

        Called by ``AdminSite.initialize()`` so that audit history is
        restored from disk on server startup.  Not called during tests
        so that each test run starts with a clean in-memory log.
        """
        self._hydrated = False
        self._hydrate()

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

        Respects admin config action filtering. Schedules an async DB write.
        Always also writes to the in-memory fallback so synchronous callers
        and tests see the entry immediately.
        """
        import asyncio

        # Always record in-memory fallback (instant, sync)
        # The fallback's _admin_config check will handle filtering
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

        # If the action was filtered out (skip entry), don't write to DB
        if mem_entry.id.startswith("audit_skip_"):
            return mem_entry

        # Persist to CROUS file (best-effort)
        self._crous_store.persist(mem_entry)

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
            pass  # No event loop running -- fallback-only mode

        return mem_entry

    async def _async_write(self, **kwargs: Any) -> None:
        """Write one audit entry to the DB table (best-effort)."""
        try:
            if not await self._probe_db():
                return
            from aquilia.admin.models import AdminAuditEntry
            await AdminAuditEntry.create_entry(**kwargs)
        except Exception as exc:
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
        Async version of log() -- awaits the DB write directly.
        Respects admin config action filtering.
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
        # If the action was filtered out, don't write to DB
        if mem_entry.id.startswith("audit_skip_"):
            return mem_entry
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
                qs = AdminAuditEntry.objects.get_queryset()
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
                self._db_available = False

        # Fallback to in-memory
        return self._fallback.get_entries(
            action=action, user_id=user_id, model_name=model_name,
            limit=limit, offset=offset,
        )  # type: ignore[return-value]

    def _hydrate(self) -> None:
        """Load persisted CROUS entries into the in-memory fallback (once)."""
        if self._hydrated:
            return
        self._hydrated = True
        try:
            persisted = self._crous_store.load_all()
            if persisted:
                existing_ids = {e.id for e in self._fallback._entries}
                for entry in persisted:
                    if entry.id not in existing_ids:
                        self._fallback._entries.insert(0, entry)
                self._fallback._entries.sort(key=lambda e: e.timestamp)
                if len(self._fallback._entries) > self._fallback._max_entries:
                    self._fallback._entries = self._fallback._entries[-self._fallback._max_entries:]
                self._fallback._counter = len(self._fallback._entries)
        except Exception:
            pass

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
        Synchronous get_entries -- returns in-memory entries only.
        Hydrates from the CROUS file on the first call.
        Use get_entries_async() when in an async context to also
        include DB-persisted entries.
        """
        self._hydrate()
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
                qs = AdminAuditEntry.objects.get_queryset()
                if action is not None:
                    action_str = action.value if hasattr(action, "value") else str(action)
                    qs = qs.filter(action=action_str)
                if model_name is not None:
                    qs = qs.filter(model_name=model_name)
                return await qs.count()
            except Exception as exc:
                self._db_available = False
        return self._fallback.count(action=action, model_name=model_name)

    def count(
        self,
        *,
        action: Optional["AdminAction"] = None,
        model_name: Optional[str] = None,
    ) -> int:
        """Synchronous count -- returns in-memory count only."""
        self._hydrate()
        return self._fallback.count(action=action, model_name=model_name)

    def clear(self) -> int:
        """Clear in-memory fallback entries and CROUS file. DB entries are retained."""
        self._crous_store.clear()
        self._hydrated = False
        return self._fallback.clear()

    def get_history_for_record(
        self,
        model_name: str,
        record_pk: str,
    ) -> List["AdminAuditEntry"]:
        """
        Return all audit entries for a specific model + pk.

        Searches both the in-memory log and the CROUS file directly,
        merging and deduplicating by entry id.  Returns newest-first.
        """
        # In-memory results (with hydration)
        self._hydrate()
        mem = self._fallback.get_entries(model_name=model_name, limit=10_000)
        mem_filtered = [
            e for e in mem
            if str(e.record_pk or "") == str(record_pk)
        ]

        # CROUS file direct lookup (catches entries not yet in memory)
        file_entries = self._crous_store.load_for_record(model_name, record_pk)

        # Merge, dedup by id, sort newest-first
        seen: set = set()
        merged: List[AdminAuditEntry] = []
        for e in file_entries + mem_filtered:
            if e.id not in seen:
                seen.add(e.id)
                merged.append(e)
        merged.sort(key=lambda e: e.timestamp, reverse=True)
        return merged
