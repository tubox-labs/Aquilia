"""
AquilaSessions - Production-grade session management for Aquilia.

This package provides explicit, policy-driven session management with:
- Cryptographic session IDs (256-bit entropy, OWASP compliant)
- Multiple backend stores (memory, Redis, file)
- Policy-based lifecycle management (TTL, idle timeout, absolute timeout)
- Transport-agnostic design (HTTP cookies, headers)
- OWASP session fingerprinting for hijack detection
- Deep integration with Aquilia's DI, Flow, and Faults systems

Philosophy:
- Sessions are capabilities (grant scoped access)
- Sessions are explicit (no hidden globals)
- Sessions are policy-driven (declared behavior)
- Sessions are observable (auditable mutations)
- Sessions are transport-agnostic (not tied to cookies)
"""

from .core import (
    Session,
    SessionFlag,
    SessionID,
    SessionPrincipal,
    SessionScope,
)

# Session decorators + guards (includes merged enhanced.py features)
from .decorators import (
    AdminGuard,
    AuthenticationRequiredFault,
    SessionContext,
    SessionGuard,
    SessionRequiredFault,
    VerifiedEmailGuard,
    authenticated,
    requires,
    session,
    stateful,
)
from .engine import SessionEngine
from .faults import (
    SessionAbsoluteTimeoutFault,
    SessionConcurrencyViolationFault,
    SessionExpiredFault,
    SessionFault,
    SessionFingerprintMismatchFault,
    SessionForgeryAttemptFault,
    SessionHijackAttemptFault,
    SessionIdleTimeoutFault,
    SessionInvalidFault,
    SessionLockedFault,
    SessionNotFoundFault,
    SessionPolicyViolationFault,
    SessionRotationFailedFault,
    SessionStoreCorruptedFault,
    SessionStoreUnavailableFault,
    SessionTransportFault,
)
from .policy import (
    ADMIN_POLICY,
    API_TOKEN_POLICY,
    DEFAULT_USER_POLICY,
    EPHEMERAL_POLICY,
    ConcurrencyPolicy,
    PersistencePolicy,
    SessionPolicy,
    SessionPolicyBuilder,
    TransportPolicy,
)
from .state import (
    CartState,
    Field,
    SessionState,
    UserPreferencesState,
)
from .store import (
    FileStore,
    MemoryStore,
    SessionStore,
)
from .transport import (
    CookieTransport,
    HeaderTransport,
    SessionTransport,
    create_transport,
)

__all__ = [
    # Core types
    "Session",
    "SessionID",
    "SessionPrincipal",
    "SessionScope",
    "SessionFlag",
    # Policy types
    "SessionPolicy",
    "SessionPolicyBuilder",
    "PersistencePolicy",
    "ConcurrencyPolicy",
    "TransportPolicy",
    "DEFAULT_USER_POLICY",
    "API_TOKEN_POLICY",
    "EPHEMERAL_POLICY",
    "ADMIN_POLICY",
    # Engine
    "SessionEngine",
    # Storage
    "SessionStore",
    "MemoryStore",
    "FileStore",
    # Transport
    "SessionTransport",
    "CookieTransport",
    "HeaderTransport",
    "create_transport",
    # Faults (complete set)
    "SessionFault",
    "SessionExpiredFault",
    "SessionIdleTimeoutFault",
    "SessionAbsoluteTimeoutFault",
    "SessionInvalidFault",
    "SessionNotFoundFault",
    "SessionConcurrencyViolationFault",
    "SessionStoreUnavailableFault",
    "SessionStoreCorruptedFault",
    "SessionRotationFailedFault",
    "SessionPolicyViolationFault",
    "SessionTransportFault",
    "SessionForgeryAttemptFault",
    "SessionHijackAttemptFault",
    "SessionFingerprintMismatchFault",
    "SessionLockedFault",
    # Decorators + Guards
    "session",
    "authenticated",
    "stateful",
    "SessionRequiredFault",
    "AuthenticationRequiredFault",
    "SessionContext",
    "SessionGuard",
    "requires",
    "AdminGuard",
    "VerifiedEmailGuard",
    # State
    "SessionState",
    "Field",
    "CartState",
    "UserPreferencesState",
]

from aquilia._version import __version__  # noqa: F401 — re-exported
