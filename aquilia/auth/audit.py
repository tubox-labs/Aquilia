"""
AquilAuth - Security Audit Trail

Structured security event logging for authentication, authorization,
and access control decisions. OWASP-compliant audit logging.
"""

from __future__ import annotations

import enum
import json
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aquilia.auth.audit")


# ============================================================================
# Audit Event Types
# ============================================================================


class AuditEventType(str, enum.Enum):
    """Categories of security events."""

    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_ISSUED = "auth.token.issued"
    AUTH_TOKEN_REFRESHED = "auth.token.refreshed"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_TOKEN_EXPIRED = "auth.token.expired"
    AUTH_TOKEN_INVALID = "auth.token.invalid"
    AUTH_API_KEY_USED = "auth.apikey.used"
    AUTH_API_KEY_REJECTED = "auth.apikey.rejected"

    # MFA events
    AUTH_MFA_CHALLENGE = "auth.mfa.challenge"
    AUTH_MFA_SUCCESS = "auth.mfa.success"
    AUTH_MFA_FAILURE = "auth.mfa.failure"

    # Authorization events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_CLEARANCE_GRANTED = "authz.clearance.granted"
    AUTHZ_CLEARANCE_DENIED = "authz.clearance.denied"
    AUTHZ_POLICY_EVALUATED = "authz.policy.evaluated"

    # Session events
    SESSION_CREATED = "session.created"
    SESSION_DESTROYED = "session.destroyed"
    SESSION_EXPIRED = "session.expired"
    SESSION_HIJACK_ATTEMPT = "session.hijack_attempt"

    # Account events
    ACCOUNT_LOCKED = "account.locked"
    ACCOUNT_UNLOCKED = "account.unlocked"
    ACCOUNT_SUSPENDED = "account.suspended"
    ACCOUNT_RATE_LIMITED = "account.rate_limited"
    ACCOUNT_PASSWORD_CHANGED = "account.password_changed"
    ACCOUNT_CREATED = "account.created"

    # OAuth events
    OAUTH_AUTH_CODE_ISSUED = "oauth.authcode.issued"
    OAUTH_CLIENT_AUTH = "oauth.client.auth"
    OAUTH_DEVICE_AUTH = "oauth.device.auth"

    # System events
    SECURITY_KEY_ROTATED = "security.key.rotated"
    SECURITY_KEY_REVOKED = "security.key.revoked"
    SECURITY_CONFIG_CHANGED = "security.config.changed"


class AuditSeverity(str, enum.Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ALERT = "alert"


# ============================================================================
# Audit Event
# ============================================================================


@dataclass
class AuditEvent:
    """Structured security audit event."""

    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: float = field(default_factory=time.time)
    identity_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    action: str | None = None
    outcome: str = "success"  # "success" | "failure" | "error"
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    session_id: str | None = None
    tenant_id: str | None = None

    @property
    def timestamp_iso(self) -> str:
        """ISO 8601 timestamp."""
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for logging/storage."""
        d = {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp_iso,
            "timestamp_epoch": self.timestamp,
            "outcome": self.outcome,
        }
        if self.identity_id:
            d["identity_id"] = self.identity_id
        if self.ip_address:
            d["ip_address"] = self.ip_address
        if self.user_agent:
            d["user_agent"] = self.user_agent
        if self.resource:
            d["resource"] = self.resource
        if self.action:
            d["action"] = self.action
        if self.details:
            d["details"] = self.details
        if self.request_id:
            d["request_id"] = self.request_id
        if self.session_id:
            d["session_id"] = self.session_id
        if self.tenant_id:
            d["tenant_id"] = self.tenant_id
        return d

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)


# ============================================================================
# Audit Store Protocol
# ============================================================================


class AuditStore:
    """
    Base class for audit event storage.

    Override ``emit`` to persist events to your preferred backend
    (database, file, external service, etc.).
    """

    async def emit(self, event: AuditEvent) -> None:
        """Store/emit an audit event."""
        raise NotImplementedError

    async def query(
        self,
        event_type: AuditEventType | None = None,
        identity_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query stored events. Optional -- not all stores support this."""
        return []


class MemoryAuditStore(AuditStore):
    """In-memory audit store for development/testing."""

    def __init__(self, max_events: int = 10000):
        self._events: list[AuditEvent] = []
        self._max_events = max_events

    async def emit(self, event: AuditEvent) -> None:
        """Store event in memory."""
        self._events.append(event)
        # Ring buffer: discard oldest if over limit
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

    async def query(
        self,
        event_type: AuditEventType | None = None,
        identity_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query events from memory store."""
        results = self._events

        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]
        if identity_id is not None:
            results = [e for e in results if e.identity_id == identity_id]
        if since is not None:
            results = [e for e in results if e.timestamp >= since]
        if until is not None:
            results = [e for e in results if e.timestamp <= until]

        return results[-limit:]

    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()

    @property
    def events(self) -> list[AuditEvent]:
        """Access stored events."""
        return list(self._events)


class LoggingAuditStore(AuditStore):
    """Audit store that logs to Python logging framework."""

    def __init__(self, logger_name: str = "aquilia.audit"):
        self._logger = logging.getLogger(logger_name)

    async def emit(self, event: AuditEvent) -> None:
        """Emit event to logger."""
        level_map = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.CRITICAL: logging.CRITICAL,
            AuditSeverity.ALERT: logging.CRITICAL,
        }
        level = level_map.get(event.severity, logging.INFO)
        self._logger.log(level, event.to_json())


# ============================================================================
# Audit Trail (main interface)
# ============================================================================


class AuditTrail:
    """
    Central audit trail for security events.

    Supports multiple stores (fan-out) and provides convenience methods
    for common event types.
    """

    def __init__(
        self,
        stores: Sequence[AuditStore] | None = None,
        default_tenant: str | None = None,
    ):
        self._stores: list[AuditStore] = list(stores or [])
        self._default_tenant = default_tenant
        if not self._stores:
            self._stores.append(LoggingAuditStore())

    def add_store(self, store: AuditStore) -> None:
        """Add an audit store."""
        self._stores.append(store)

    async def emit(self, event: AuditEvent) -> None:
        """Emit an event to all stores."""
        if event.tenant_id is None and self._default_tenant:
            event.tenant_id = self._default_tenant

        for store in self._stores:
            try:
                await store.emit(event)
            except Exception as e:
                logger.error(f"Audit store error: {e}", exc_info=True)

    def _extract_request_info(
        self,
        request: Any = None,
        ctx: Any = None,
    ) -> dict[str, str | None]:
        """Extract IP, user-agent, request ID from request context."""
        info: dict[str, str | None] = {
            "ip_address": None,
            "user_agent": None,
            "request_id": None,
            "session_id": None,
        }

        if request is not None:
            # IP address
            if hasattr(request, "client") and request.client:
                info["ip_address"] = request.client[0] if isinstance(request.client, tuple) else str(request.client)

            # Headers
            state = getattr(request, "state", {})
            if isinstance(state, dict):
                info["request_id"] = state.get("request_id")
                info["session_id"] = state.get("session_id")

            if hasattr(request, "headers"):
                headers = request.headers
                if hasattr(headers, "get"):
                    info["user_agent"] = headers.get("user-agent")
                    # Fallback for IP
                    if not info["ip_address"]:
                        info["ip_address"] = headers.get("x-forwarded-for", "").split(",")[0].strip() or headers.get(
                            "x-real-ip"
                        )

        return info

    # ---- Convenience methods ----

    async def login_success(
        self,
        identity_id: str,
        request: Any = None,
        method: str = "password",
        **extra,
    ) -> None:
        """Record successful login."""
        info = self._extract_request_info(request)
        await self.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
                identity_id=identity_id,
                action="login",
                details={"method": method, **extra},
                **info,
            )
        )

    async def login_failure(
        self,
        identity_id: str | None,
        request: Any = None,
        reason: str = "invalid_credentials",
        **extra,
    ) -> None:
        """Record failed login attempt."""
        info = self._extract_request_info(request)
        severity = AuditSeverity.WARNING
        if reason in ("rate_limited", "account_locked"):
            severity = AuditSeverity.CRITICAL

        await self.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                severity=severity,
                identity_id=identity_id,
                outcome="failure",
                action="login",
                details={"reason": reason, **extra},
                **info,
            )
        )

    async def access_denied(
        self,
        identity_id: str | None,
        resource: str,
        request: Any = None,
        reason: str = "insufficient_permissions",
        **extra,
    ) -> None:
        """Record access denied event."""
        info = self._extract_request_info(request)
        await self.emit(
            AuditEvent(
                event_type=AuditEventType.AUTHZ_ACCESS_DENIED,
                severity=AuditSeverity.WARNING,
                identity_id=identity_id,
                resource=resource,
                outcome="failure",
                action="access",
                details={"reason": reason, **extra},
                **info,
            )
        )

    async def clearance_evaluated(
        self,
        identity_id: str | None,
        resource: str,
        granted: bool,
        request: Any = None,
        **extra,
    ) -> None:
        """Record clearance evaluation result."""
        info = self._extract_request_info(request)
        event_type = AuditEventType.AUTHZ_CLEARANCE_GRANTED if granted else AuditEventType.AUTHZ_CLEARANCE_DENIED
        await self.emit(
            AuditEvent(
                event_type=event_type,
                severity=AuditSeverity.INFO if granted else AuditSeverity.WARNING,
                identity_id=identity_id,
                resource=resource,
                outcome="success" if granted else "failure",
                action="clearance_check",
                details=extra,
                **info,
            )
        )

    async def token_event(
        self,
        event_type: AuditEventType,
        identity_id: str,
        request: Any = None,
        **extra,
    ) -> None:
        """Record token lifecycle event."""
        info = self._extract_request_info(request)
        await self.emit(
            AuditEvent(
                event_type=event_type,
                severity=AuditSeverity.INFO,
                identity_id=identity_id,
                action="token",
                details=extra,
                **info,
            )
        )

    async def account_locked(
        self,
        identity_id: str,
        request: Any = None,
        reason: str = "max_attempts_exceeded",
        **extra,
    ) -> None:
        """Record account lockout."""
        info = self._extract_request_info(request)
        await self.emit(
            AuditEvent(
                event_type=AuditEventType.ACCOUNT_LOCKED,
                severity=AuditSeverity.CRITICAL,
                identity_id=identity_id,
                outcome="failure",
                action="lockout",
                details={"reason": reason, **extra},
                **info,
            )
        )

    async def session_event(
        self,
        event_type: AuditEventType,
        identity_id: str | None = None,
        request: Any = None,
        **extra,
    ) -> None:
        """Record session lifecycle event."""
        info = self._extract_request_info(request)
        await self.emit(
            AuditEvent(
                event_type=event_type,
                severity=AuditSeverity.INFO,
                identity_id=identity_id,
                action="session",
                details=extra,
                **info,
            )
        )

    async def query(
        self,
        event_type: AuditEventType | None = None,
        identity_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query events from first store that supports it."""
        for store in self._stores:
            try:
                results = await store.query(
                    event_type=event_type,
                    identity_id=identity_id,
                    since=since,
                    until=until,
                    limit=limit,
                )
                if results:
                    return results
            except NotImplementedError:
                continue
        return []


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "AuditStore",
    "MemoryAuditStore",
    "LoggingAuditStore",
    "AuditTrail",
]
