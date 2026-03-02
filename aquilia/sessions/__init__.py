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
    SessionID,
    SessionPrincipal,
    SessionScope,
    SessionFlag,
)

from .policy import (
    SessionPolicy,
    SessionPolicyBuilder,
    PersistencePolicy,
    ConcurrencyPolicy,
    TransportPolicy,
    DEFAULT_USER_POLICY,
    API_TOKEN_POLICY,
    EPHEMERAL_POLICY,
    ADMIN_POLICY,
)

from .store import (
    SessionStore,
    MemoryStore,
    FileStore,
)

from .transport import (
    SessionTransport,
    CookieTransport,
    HeaderTransport,
    create_transport,
)

from .engine import SessionEngine

from .faults import (
    SessionFault,
    SessionExpiredFault,
    SessionIdleTimeoutFault,
    SessionAbsoluteTimeoutFault,
    SessionInvalidFault,
    SessionNotFoundFault,
    SessionConcurrencyViolationFault,
    SessionStoreUnavailableFault,
    SessionStoreCorruptedFault,
    SessionRotationFailedFault,
    SessionPolicyViolationFault,
    SessionTransportFault,
    SessionForgeryAttemptFault,
    SessionHijackAttemptFault,
    SessionFingerprintMismatchFault,
    SessionLockedFault,
)

# Session decorators + guards (includes merged enhanced.py features)
from .decorators import (
    session,
    authenticated,
    stateful,
    SessionRequiredFault,
    AuthenticationRequiredFault,
    SessionContext,
    SessionGuard,
    requires,
    AdminGuard,
    VerifiedEmailGuard,
)

from .state import (
    SessionState,
    Field,
    CartState,
    UserPreferencesState,
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

__version__ = "0.1.0"
