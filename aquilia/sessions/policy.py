"""
AquilaSessions - Policy types.

Defines session policies that govern behavior:
- SessionPolicy: Master policy contract
- PersistencePolicy: How sessions persist
- ConcurrencyPolicy: Concurrent session limits
- TransportPolicy: How sessions travel
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .core import Session, SessionPrincipal


# ============================================================================
# Sub-Policies
# ============================================================================


@dataclass
class PersistencePolicy:
    """
    Controls how sessions persist to storage.

    Attributes:
        enabled: Whether persistence is enabled
        store_name: Which SessionStore to use
        write_through: Immediate vs eventual consistency
        compress: Compress session data before storage
    """

    enabled: bool = True
    store_name: str = "default"
    write_through: bool = True
    compress: bool = False


@dataclass
class ConcurrencyPolicy:
    """
    Controls concurrent session limits per principal.

    Attributes:
        max_sessions_per_principal: Maximum concurrent sessions (None = unlimited)
        behavior_on_limit: What to do when limit is reached
    """

    max_sessions_per_principal: int | None = None
    behavior_on_limit: Literal["reject", "evict_oldest", "evict_all"] = "evict_oldest"

    def violated(self, principal: SessionPrincipal, active_count: int) -> bool:
        if self.max_sessions_per_principal is None:
            return False
        return active_count > self.max_sessions_per_principal

    def should_reject(self) -> bool:
        return self.behavior_on_limit == "reject"

    def should_evict_oldest(self) -> bool:
        return self.behavior_on_limit == "evict_oldest"

    def should_evict_all(self) -> bool:
        return self.behavior_on_limit == "evict_all"


@dataclass
class TransportPolicy:
    """
    Controls how sessions travel across network.
    """

    adapter: Literal["cookie", "header", "token"] = "cookie"

    # Cookie options
    cookie_name: str = "aquilia_session"
    cookie_httponly: bool = True
    cookie_secure: bool = True
    cookie_samesite: Literal["strict", "lax", "none"] = "lax"
    cookie_path: str = "/"
    cookie_domain: str | None = None

    # Header options
    header_name: str = "X-Session-ID"


# ============================================================================
# Master Policy
# ============================================================================


@dataclass
class SessionPolicy:
    """
    Master policy that defines how sessions behave.

    Policies are the source of truth for:
    - Lifetime management (TTL, idle timeout, absolute timeout)
    - Rotation rules (when to rotate IDs)
    - Persistence strategy
    - Concurrency limits
    - Transport mechanism
    - Fingerprint binding (OWASP hijack detection)
    """

    name: str
    ttl: timedelta | None = None
    idle_timeout: timedelta | None = None
    absolute_timeout: timedelta | None = None  # OWASP: max total session lifetime
    rotate_on_use: bool = False
    rotate_on_privilege_change: bool = True
    fingerprint_binding: bool = False  # OWASP: bind session to client IP+UA
    persistence: PersistencePolicy = dc_field(default=None)  # type: ignore[assignment]
    concurrency: ConcurrencyPolicy = dc_field(default=None)  # type: ignore[assignment]
    transport: TransportPolicy = dc_field(default=None)  # type: ignore[assignment]
    scope: str = "user"

    def __post_init__(self):
        """Initialize sub-policies with defaults if not provided."""
        if self.persistence is None:
            object.__setattr__(self, "persistence", PersistencePolicy())

        if self.concurrency is None:
            object.__setattr__(self, "concurrency", ConcurrencyPolicy())

        if self.transport is None:
            object.__setattr__(self, "transport", TransportPolicy())

    def should_rotate(self, session: Session, privilege_changed: bool = False) -> bool:
        if privilege_changed and self.rotate_on_privilege_change:
            return True
        return bool(self.rotate_on_use)

    def calculate_expiry(self, now: datetime | None = None) -> datetime | None:
        if not self.ttl:
            return None
        if now is None:
            now = datetime.now(timezone.utc)
        return now + self.ttl

    def is_valid(self, session: Session, now: datetime | None = None) -> tuple[bool, str]:
        """
        Validate session against policy.

        Returns:
            Tuple of (is_valid, reason)
            - (True, "valid")
            - (False, "expired")
            - (False, "idle_timeout")
            - (False, "absolute_timeout")
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Check expiry (TTL)
        if session.is_expired(now):
            return False, "expired"

        # Check idle timeout
        if self.idle_timeout:
            idle_duration = session.idle_duration(now)
            if idle_duration >= self.idle_timeout:
                return False, "idle_timeout"

        # Check absolute timeout (OWASP)
        if self.absolute_timeout:
            age = session.age(now)
            if age >= self.absolute_timeout:
                return False, "absolute_timeout"

        return True, "valid"

    def should_persist(self, session: Session) -> bool:
        if not self.persistence.enabled:
            return False
        if session.is_ephemeral:
            return False
        return session.scope.requires_persistence()

    def requires_store(self) -> bool:
        return self.persistence.enabled

    @classmethod
    def from_dict(cls, name: str, config: dict) -> SessionPolicy:
        """Create policy from configuration dictionary."""

        ttl = None
        if config.get("ttl"):
            ttl = timedelta(seconds=config["ttl"])

        idle_timeout = None
        if config.get("idle_timeout"):
            idle_timeout = timedelta(seconds=config["idle_timeout"])

        absolute_timeout = None
        if config.get("absolute_timeout"):
            absolute_timeout = timedelta(seconds=config["absolute_timeout"])

        persistence_config = config.get("persistence", {})
        persistence = PersistencePolicy(
            enabled=persistence_config.get("enabled", True),
            store_name=persistence_config.get("store_name", "default"),
            write_through=persistence_config.get("write_through", True),
            compress=persistence_config.get("compress", False),
        )

        concurrency_config = config.get("concurrency", {})
        concurrency = ConcurrencyPolicy(
            max_sessions_per_principal=concurrency_config.get("max_sessions_per_principal"),
            behavior_on_limit=concurrency_config.get("behavior_on_limit", "evict_oldest"),
        )

        transport_config = config.get("transport", {})
        transport = TransportPolicy(
            adapter=transport_config.get("adapter", "cookie"),
            cookie_name=transport_config.get("cookie_name", "aquilia_session"),
            cookie_httponly=transport_config.get("cookie_httponly", True),
            cookie_secure=transport_config.get("cookie_secure", True),
            cookie_samesite=transport_config.get("cookie_samesite", "lax"),
            cookie_path=transport_config.get("cookie_path", "/"),
            cookie_domain=transport_config.get("cookie_domain"),
            header_name=transport_config.get("header_name", "X-Session-ID"),
        )

        scope_str = config.get("scope", "user")

        return cls(
            name=name,
            ttl=ttl,
            idle_timeout=idle_timeout,
            absolute_timeout=absolute_timeout,
            rotate_on_use=config.get("rotate_on_use", False),
            rotate_on_privilege_change=config.get("rotate_on_privilege_change", True),
            fingerprint_binding=config.get("fingerprint_binding", False),
            persistence=persistence,
            concurrency=concurrency,
            transport=transport,
            scope=scope_str,
        )

    # ========================================================================
    # Unique Aquilia Fluent Builders
    # ========================================================================

    @classmethod
    def for_web_users(cls) -> SessionPolicyBuilder:
        return SessionPolicyBuilder().web_defaults()

    @classmethod
    def for_api_tokens(cls) -> SessionPolicyBuilder:
        return SessionPolicyBuilder().api_defaults()

    @classmethod
    def for_mobile_users(cls) -> SessionPolicyBuilder:
        return SessionPolicyBuilder().mobile_defaults()

    @classmethod
    def for_admin_users(cls) -> SessionPolicyBuilder:
        return SessionPolicyBuilder().admin_defaults()


# ============================================================================
# Unique Aquilia Session Policy Builder
# ============================================================================


class SessionPolicyBuilder:
    """Fluent builder for SessionPolicy with unique Aquilia syntax."""

    def __init__(self):
        self._name = "aquilia_session"
        self._ttl = timedelta(days=7)
        self._idle_timeout = timedelta(hours=1)
        self._absolute_timeout: timedelta | None = None
        self._rotate_on_use = False
        self._rotate_on_privilege_change = True
        self._fingerprint_binding = False
        self._scope = "user"
        self._transport = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_session",
            cookie_secure=True,
            cookie_httponly=True,
            cookie_samesite="lax",
        )
        self._persistence = PersistencePolicy(enabled=True, store_name="default")
        self._concurrency = ConcurrencyPolicy(max_sessions_per_principal=5)

    def named(self, name: str) -> SessionPolicyBuilder:
        self._name = name
        return self

    def lasting(self, days: int = None, hours: int = None, minutes: int = None) -> SessionPolicyBuilder:
        if days:
            self._ttl = timedelta(days=days)
        elif hours:
            self._ttl = timedelta(hours=hours)
        elif minutes:
            self._ttl = timedelta(minutes=minutes)
        return self

    def idle_timeout(self, hours: int = None, minutes: int = None, days: int = None) -> SessionPolicyBuilder:
        if days:
            self._idle_timeout = timedelta(days=days)
        elif hours:
            self._idle_timeout = timedelta(hours=hours)
        elif minutes:
            self._idle_timeout = timedelta(minutes=minutes)
        return self

    def no_idle_timeout(self) -> SessionPolicyBuilder:
        self._idle_timeout = None
        return self

    def absolute_timeout(self, hours: int = None, minutes: int = None, days: int = None) -> SessionPolicyBuilder:
        """Set absolute timeout (OWASP: max total session lifetime)."""
        if days:
            self._absolute_timeout = timedelta(days=days)
        elif hours:
            self._absolute_timeout = timedelta(hours=hours)
        elif minutes:
            self._absolute_timeout = timedelta(minutes=minutes)
        return self

    def with_fingerprint_binding(self) -> SessionPolicyBuilder:
        """Enable OWASP session-to-client fingerprint binding."""
        self._fingerprint_binding = True
        return self

    def rotating_on_auth(self) -> SessionPolicyBuilder:
        self._rotate_on_privilege_change = True
        return self

    def rotating_on_use(self) -> SessionPolicyBuilder:
        self._rotate_on_use = True
        return self

    def scoped_to(self, scope: str) -> SessionPolicyBuilder:
        self._scope = scope
        return self

    def max_concurrent(self, limit: int) -> SessionPolicyBuilder:
        self._concurrency = ConcurrencyPolicy(max_sessions_per_principal=limit, behavior_on_limit="evict_oldest")
        return self

    def unlimited_concurrent(self) -> SessionPolicyBuilder:
        self._concurrency = ConcurrencyPolicy(max_sessions_per_principal=None, behavior_on_limit="evict_oldest")
        return self

    def with_smart_defaults(self) -> SessionPolicyBuilder:
        import os

        if os.getenv("AQUILIA_ENV") == "production":
            return self.lasting(days=1).idle_timeout(minutes=30)
        else:
            return self.lasting(days=7).idle_timeout(hours=2)

    def web_defaults(self) -> SessionPolicyBuilder:
        return self.named("web_session").lasting(days=7).idle_timeout(hours=2).rotating_on_auth().max_concurrent(5)

    def api_defaults(self) -> SessionPolicyBuilder:
        return self.named("api_session").lasting(hours=1).no_idle_timeout().unlimited_concurrent()

    def mobile_defaults(self) -> SessionPolicyBuilder:
        return self.named("mobile_session").lasting(days=90).idle_timeout(days=30).max_concurrent(3)

    def admin_defaults(self) -> SessionPolicyBuilder:
        """Enhanced security defaults for admin users with fingerprint binding."""
        return (
            self.named("admin_session")
            .lasting(hours=8)
            .idle_timeout(minutes=15)
            .absolute_timeout(hours=12)
            .rotating_on_use()
            .with_fingerprint_binding()
            .max_concurrent(1)
        )

    def build(self) -> SessionPolicy:
        return SessionPolicy(
            name=self._name,
            ttl=self._ttl,
            idle_timeout=self._idle_timeout,
            absolute_timeout=self._absolute_timeout,
            rotate_on_use=self._rotate_on_use,
            rotate_on_privilege_change=self._rotate_on_privilege_change,
            fingerprint_binding=self._fingerprint_binding,
            persistence=self._persistence,
            concurrency=self._concurrency,
            transport=self._transport,
            scope=self._scope,
        )

    def __call__(self) -> SessionPolicy:
        return self.build()


# ============================================================================
# Built-in Policies
# ============================================================================

DEFAULT_USER_POLICY = SessionPolicy(
    name="user_default",
    ttl=timedelta(days=7),
    idle_timeout=timedelta(minutes=30),
    rotate_on_use=False,
    rotate_on_privilege_change=True,
    persistence=PersistencePolicy(enabled=True, store_name="default"),
    concurrency=ConcurrencyPolicy(max_sessions_per_principal=5, behavior_on_limit="evict_oldest"),
    transport=TransportPolicy(adapter="cookie"),
    scope="user",
)

API_TOKEN_POLICY = SessionPolicy(
    name="api_token",
    ttl=timedelta(hours=1),
    idle_timeout=None,
    rotate_on_use=False,
    rotate_on_privilege_change=False,
    persistence=PersistencePolicy(enabled=True, store_name="default"),
    concurrency=ConcurrencyPolicy(max_sessions_per_principal=None),
    transport=TransportPolicy(adapter="header", header_name="X-API-Token"),
    scope="user",
)

EPHEMERAL_POLICY = SessionPolicy(
    name="ephemeral",
    ttl=None,
    idle_timeout=None,
    rotate_on_use=False,
    rotate_on_privilege_change=False,
    persistence=PersistencePolicy(enabled=False),
    concurrency=ConcurrencyPolicy(max_sessions_per_principal=None),
    transport=TransportPolicy(adapter="cookie"),
    scope="request",
)

ADMIN_POLICY = SessionPolicy(
    name="admin",
    ttl=timedelta(hours=8),
    idle_timeout=timedelta(minutes=15),
    absolute_timeout=timedelta(hours=12),
    rotate_on_use=True,
    rotate_on_privilege_change=True,
    fingerprint_binding=True,
    persistence=PersistencePolicy(enabled=True, store_name="default"),
    concurrency=ConcurrencyPolicy(max_sessions_per_principal=1, behavior_on_limit="evict_all"),
    transport=TransportPolicy(adapter="cookie", cookie_samesite="strict"),
    scope="user",
)
