"""
AquilaSessions - Core types.

Defines fundamental session data structures:
- Session: Core state container
- SessionID: Opaque cryptographic identifier
- SessionPrincipal: Identity binding
- SessionScope: Lifetime semantics
- SessionFlag: Behavioral markers
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Literal

# ============================================================================
# _DirtyTrackingDict - Marks parent Session dirty on any mutation
# ============================================================================


class _DirtyTrackingDict(dict):
    """
    A dict subclass that marks its owning Session dirty whenever
    a mutation occurs (``__setitem__``, ``__delitem__``, ``pop``,
    ``update``, ``setdefault``, ``clear``).

    This solves the class of bugs where code does::

        session.data["key"] = value

    which is a dict mutation and never triggers ``Session.__setattr__``.
    Without this wrapper the session would not be persisted because
    ``_dirty`` stays ``False``.
    """

    __slots__ = ("_owner",)

    def __init__(self, *args: Any, owner: Session | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_owner", owner)

    def _mark_dirty(self) -> None:
        owner = object.__getattribute__(self, "_owner")
        if owner is not None:
            object.__setattr__(owner, "_dirty", True)

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        self._mark_dirty()

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        self._mark_dirty()

    def pop(self, key: str, *args: Any) -> Any:
        result = super().pop(key, *args)
        self._mark_dirty()
        return result

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)
        self._mark_dirty()

    def setdefault(self, key: str, default: Any = None) -> Any:
        had_key = key in self
        result = super().setdefault(key, default)
        if not had_key:
            self._mark_dirty()
        return result

    def clear(self) -> None:
        if len(self) > 0:
            super().clear()
            self._mark_dirty()

    def _bind(self, owner: Session) -> None:
        """Bind (or rebind) this dict to its owning session."""
        object.__setattr__(self, "_owner", owner)


# ============================================================================
# SessionID - Opaque Cryptographic Identifier
# ============================================================================


class SessionID:
    """
    Opaque session identifier with cryptographic randomness.

    Rules:
    - Never encode meaning (no user ID, no timestamps)
    - Cryptographically random (32 bytes = 256 bits entropy)
    - URL-safe encoding
    - Prefixed for identification (sess_)

    Per OWASP: Session IDs must have at least 64 bits of entropy.
    Aquilia uses 256 bits (32 bytes) for maximum security.
    """

    __slots__ = ("_raw", "_encoded")

    ENTROPY_BYTES = 32  # 256 bits entropy (OWASP minimum: 64 bits)
    PREFIX = "sess_"

    def __init__(self, raw: bytes | None = None):
        if raw is None:
            raw = secrets.token_bytes(self.ENTROPY_BYTES)
        elif len(raw) != self.ENTROPY_BYTES:
            from .faults import SessionInvalidFault

            raise SessionInvalidFault()

        self._raw = raw
        self._encoded = f"{self.PREFIX}{base64.urlsafe_b64encode(raw).decode().rstrip('=')}"

    def __str__(self) -> str:
        return self._encoded

    def __repr__(self) -> str:
        return f"SessionID({self._encoded[:16]}...)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionID):
            return False
        return secrets.compare_digest(self._raw, other._raw)

    def __hash__(self) -> int:
        return hash(self._raw)

    # Maximum allowed length for an encoded session ID string.
    # sess_ (5) + base64url of 32 bytes (43) + padding (3) = 51 chars max.
    _MAX_ENCODED_LENGTH = 128

    @classmethod
    def from_string(cls, encoded: str) -> SessionID:
        from .faults import SessionInvalidFault

        # Guard: reject oversized input before any processing
        if not isinstance(encoded, str) or len(encoded) > cls._MAX_ENCODED_LENGTH:
            raise SessionInvalidFault()

        if not encoded.startswith(cls.PREFIX):
            raise SessionInvalidFault()

        raw_b64 = encoded[len(cls.PREFIX) :]

        padding = 4 - (len(raw_b64) % 4)
        if padding != 4:
            raw_b64 += "=" * padding

        try:
            raw = base64.urlsafe_b64decode(raw_b64)
        except Exception:
            raise SessionInvalidFault()

        if len(raw) != cls.ENTROPY_BYTES:
            raise SessionInvalidFault()

        return cls(raw)

    @property
    def raw(self) -> bytes:
        return self._raw

    def fingerprint(self) -> str:
        """Privacy-safe fingerprint for logging."""
        return f"sha256:{hashlib.sha256(self._raw).hexdigest()[:16]}"


# ============================================================================
# SessionScope - Lifetime Semantics
# ============================================================================


class SessionScope(str, Enum):
    REQUEST = "request"
    CONNECTION = "connection"
    USER = "user"
    DEVICE = "device"

    def requires_persistence(self) -> bool:
        return self in (SessionScope.USER, SessionScope.DEVICE, SessionScope.CONNECTION)

    def is_ephemeral(self) -> bool:
        return self == SessionScope.REQUEST


# ============================================================================
# SessionFlag - Behavioral Markers
# ============================================================================


class SessionFlag(str, Enum):
    AUTHENTICATED = "authenticated"
    EPHEMERAL = "ephemeral"
    ROTATABLE = "rotatable"
    RENEWABLE = "renewable"
    READ_ONLY = "read_only"
    LOCKED = "locked"


# ============================================================================
# SessionPrincipal - Identity Binding
# ============================================================================


@dataclass
class SessionPrincipal:
    """
    Represents who the session belongs to.

    A session may exist without a principal (anonymous).
    Principal binding is explicit and auditable.
    """

    kind: Literal["user", "service", "device", "anonymous"]
    id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def is_user(self) -> bool:
        return self.kind == "user"

    def is_service(self) -> bool:
        return self.kind == "service"

    def is_device(self) -> bool:
        return self.kind == "device"

    def is_anonymous(self) -> bool:
        return self.kind == "anonymous"

    def has_attribute(self, key: str) -> bool:
        return key in self.attributes

    def get_attribute(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def remove_attribute(self, key: str) -> None:
        self.attributes.pop(key, None)


# ============================================================================
# Session - Core Data Object
# ============================================================================


@dataclass
class Session:
    """
    Core session object - explicit state container with lifecycle.

    Sessions are NOT implicit cookies. They are explicit capabilities
    that grant scoped access to state and identity.

    The ``data`` dict is wrapped in ``_DirtyTrackingDict`` so that
    *any* mutation (``session.data["k"] = v``, ``.pop()``, etc.)
    automatically marks the session dirty, ensuring it gets persisted.
    """

    id: SessionID
    principal: SessionPrincipal | None = None
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    scope: SessionScope = SessionScope.USER
    flags: set[SessionFlag] = field(default_factory=set)
    version: int = 0

    # Internal tracking
    _dirty: bool = field(default=False, repr=False)
    _policy_name: str = field(default="", repr=False)
    _fingerprint: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        """Wrap self.data in _DirtyTrackingDict bound to this session."""
        raw = object.__getattribute__(self, "data")
        if not isinstance(raw, _DirtyTrackingDict):
            wrapped = _DirtyTrackingDict(raw, owner=self)
            object.__setattr__(self, "data", wrapped)
        else:
            raw._bind(self)
        # __post_init__ may have marked dirty via __setattr__; reset
        object.__setattr__(self, "_dirty", False)

    def __setattr__(self, name: str, value: Any) -> None:
        """Track mutations that should mark dirty."""
        if name == "data" and hasattr(self, "_dirty"):
            # Wrap incoming dicts in _DirtyTrackingDict
            if not isinstance(value, _DirtyTrackingDict):
                value = _DirtyTrackingDict(value, owner=self)
            else:
                value._bind(self)
        super().__setattr__(name, value)
        if hasattr(self, "_dirty") and name in ("data", "principal", "expires_at", "flags"):
            object.__setattr__(self, "_dirty", True)

    # ========================================================================
    # Dict-Like Data Access
    # ========================================================================

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    # Maximum allowed size of session data dict in bytes (approximate).
    MAX_DATA_KEYS = 256

    def _check_writable(self) -> None:
        """Raise SessionLockedFault if session is read-only."""
        if self.is_read_only:
            from .faults import SessionLockedFault

            raise SessionLockedFault()

    def _check_data_limit(self) -> None:
        """Raise SessionPolicyViolationFault if data exceeds key limit."""
        if len(self.data) >= self.MAX_DATA_KEYS:
            from .faults import SessionPolicyViolationFault

            raise SessionPolicyViolationFault(
                violation=f"Session data exceeds {self.MAX_DATA_KEYS} key limit",
                policy_name=self._policy_name or "unknown",
            )

    def __setitem__(self, key: str, value: Any) -> None:
        self._check_writable()
        if key not in self.data:
            self._check_data_limit()
        self.data[key] = value
        self._dirty = True

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __delitem__(self, key: str) -> None:
        self._check_writable()
        del self.data[key]
        self._dirty = True

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._check_writable()
        if key not in self.data:
            self._check_data_limit()
        self.data[key] = value
        self._dirty = True

    def delete(self, key: str) -> None:
        self._check_writable()
        if key in self.data:
            del self.data[key]
            self._dirty = True

    def clear_data(self) -> None:
        self._check_writable()
        self.data.clear()
        self._dirty = True

    # ========================================================================
    # Lifecycle Methods
    # ========================================================================

    def is_expired(self, now: datetime | None = None) -> bool:
        if not self.expires_at:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        return now >= self.expires_at

    def idle_duration(self, now: datetime | None = None) -> timedelta:
        if now is None:
            now = datetime.now(timezone.utc)
        return now - self.last_accessed_at

    def age(self, now: datetime | None = None) -> timedelta:
        """Total session age since creation."""
        if now is None:
            now = datetime.now(timezone.utc)
        return now - self.created_at

    def touch(self, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(timezone.utc)
        object.__setattr__(self, "last_accessed_at", now)
        object.__setattr__(self, "_dirty", True)

    def extend_expiry(self, ttl: timedelta, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(timezone.utc)
        object.__setattr__(self, "expires_at", now + ttl)
        object.__setattr__(self, "_dirty", True)

    # ========================================================================
    # Authentication Methods
    # ========================================================================

    def mark_authenticated(self, principal: SessionPrincipal) -> None:
        self.principal = principal
        self.flags.add(SessionFlag.AUTHENTICATED)
        self.flags.add(SessionFlag.ROTATABLE)
        self._dirty = True

    def clear_authentication(self) -> None:
        self.principal = None
        self.flags.discard(SessionFlag.AUTHENTICATED)
        self.flags.discard(SessionFlag.ROTATABLE)
        self._dirty = True

    @property
    def is_authenticated(self) -> bool:
        return SessionFlag.AUTHENTICATED in self.flags and self.principal is not None

    @property
    def is_anonymous(self) -> bool:
        return not self.is_authenticated

    # ========================================================================
    # State Management
    # ========================================================================

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        object.__setattr__(self, "_dirty", False)

    def mark_dirty(self) -> None:
        object.__setattr__(self, "_dirty", True)

    @property
    def is_ephemeral(self) -> bool:
        return SessionFlag.EPHEMERAL in self.flags or self.scope.is_ephemeral()

    @property
    def is_read_only(self) -> bool:
        return SessionFlag.READ_ONLY in self.flags

    @property
    def is_locked(self) -> bool:
        return SessionFlag.LOCKED in self.flags

    # ========================================================================
    # Client Fingerprinting (OWASP: Bind Session to User Properties)
    # ========================================================================

    def bind_fingerprint(self, ip: str | None = None, user_agent: str | None = None) -> None:
        """Bind session to client properties for hijack detection."""
        parts = []
        if ip:
            parts.append(ip)
        if user_agent:
            parts.append(user_agent)
        if parts:
            fp = hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]
            object.__setattr__(self, "_fingerprint", fp)
            object.__setattr__(self, "_dirty", True)

    def verify_fingerprint(self, ip: str | None = None, user_agent: str | None = None) -> bool:
        """Verify client fingerprint matches. Returns True if unset."""
        if not self._fingerprint:
            return True
        parts = []
        if ip:
            parts.append(ip)
        if user_agent:
            parts.append(user_agent)
        if not parts:
            return True
        fp = hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]
        return secrets.compare_digest(self._fingerprint, fp)

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_dict(self) -> dict[str, Any]:
        # Serialize data as a plain dict (strip _DirtyTrackingDict wrapper)
        serialized_data = dict(self.data)
        return {
            "id": str(self.id),
            "principal": (
                {
                    "kind": self.principal.kind,
                    "id": self.principal.id,
                    "attributes": self.principal.attributes,
                }
                if self.principal
                else None
            ),
            "data": serialized_data,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope.value,
            "flags": sorted(f.value for f in self.flags),
            "version": self.version,
            "_policy_name": self._policy_name,
            "_fingerprint": self._fingerprint,
        }

    # Maximum size of a serialized session dict (in bytes, approximate).
    _MAX_SERIALIZED_SIZE = 1_048_576  # 1 MiB

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        from .faults import SessionStoreCorruptedFault

        if not isinstance(data, dict):
            raise SessionStoreCorruptedFault(
                message="Session data must be a dict",
            )

        # Guard: required keys
        for key in ("id", "created_at", "last_accessed_at", "scope"):
            if key not in data:
                raise SessionStoreCorruptedFault(
                    message=f"Missing required session field: {key}",
                )

        session_id = SessionID.from_string(data["id"])

        principal = None
        if data.get("principal"):
            p = data["principal"]
            if not isinstance(p, dict) or "kind" not in p or "id" not in p:
                raise SessionStoreCorruptedFault(
                    message="Invalid principal structure in session data",
                )
            principal = SessionPrincipal(
                kind=p["kind"],
                id=str(p["id"]),
                attributes=p.get("attributes", {}),
            )

        try:
            created_at = datetime.fromisoformat(data["created_at"])
            last_accessed_at = datetime.fromisoformat(data["last_accessed_at"])
        except (ValueError, TypeError) as e:
            raise SessionStoreCorruptedFault(
                message=f"Invalid timestamp in session data: {e}",
            )

        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(data["expires_at"])
            except (ValueError, TypeError) as e:
                raise SessionStoreCorruptedFault(
                    message=f"Invalid expires_at in session data: {e}",
                )

        try:
            scope = SessionScope(data["scope"])
        except ValueError:
            raise SessionStoreCorruptedFault(
                message=f"Invalid scope value: {data['scope']}",
            )

        flags_raw = data.get("flags", [])
        flags = set()
        for f in flags_raw:
            try:
                flags.add(SessionFlag(f))
            except ValueError:
                pass  # Ignore unknown flags for forward-compat

        # Guard: session data payload size
        session_data = data.get("data", {})
        if not isinstance(session_data, dict):
            raise SessionStoreCorruptedFault(
                message="Session data payload must be a dict",
            )

        session = cls(
            id=session_id,
            principal=principal,
            data=session_data,
            created_at=created_at,
            last_accessed_at=last_accessed_at,
            expires_at=expires_at,
            scope=scope,
            flags=flags,
            version=data.get("version", 0),
        )

        session._policy_name = data.get("_policy_name", "")
        session._fingerprint = data.get("_fingerprint", "")
        session._dirty = False

        return session
