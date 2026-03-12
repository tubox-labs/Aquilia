"""
AquilaSessions - Fault definitions.

Defines session-specific faults that integrate with AquilaFaults system.
All session errors are structured Faults, not bare exceptions.
"""

import hashlib

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Session Fault Base
# ============================================================================


class SessionFault(Fault):
    """
    Base class for session-related faults.

    All session faults use FaultDomain.SECURITY by default.
    """

    domain = FaultDomain.SECURITY

    @staticmethod
    def _hash_session_id(session_id: str) -> str:
        """Hash session ID for privacy-safe logging."""
        return f"sha256:{hashlib.sha256(session_id.encode()).hexdigest()[:16]}"


# ============================================================================
# Session Expiry Faults
# ============================================================================


class SessionExpiredFault(SessionFault):
    """
    Session has expired (TTL exceeded).

    This is a normal condition and should be handled gracefully.
    The client should re-authenticate or create a new session.
    """

    code = "SESSION_EXPIRED"
    message = "Session has expired"
    severity = Severity.WARN
    public = True
    retryable = False

    def __init__(self, session_id: str | None = None, expires_at: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.session_id_hash = self._hash_session_id(session_id) if session_id else None
        self.expires_at = expires_at


class SessionIdleTimeoutFault(SessionFault):
    """
    Session idle timeout exceeded.

    Session was inactive for longer than policy allows.
    """

    code = "SESSION_IDLE_TIMEOUT"
    message = "Session idle timeout exceeded"
    severity = Severity.WARN
    public = True
    retryable = False


class SessionAbsoluteTimeoutFault(SessionFault):
    """
    Session absolute timeout exceeded (OWASP requirement).

    Session total lifetime exceeded the maximum allowed, regardless of activity.
    Forces re-authentication even for active sessions.
    """

    code = "SESSION_ABSOLUTE_TIMEOUT"
    message = "Session absolute timeout exceeded"
    severity = Severity.WARN
    public = True
    retryable = False


# ============================================================================
# Session Validation Faults
# ============================================================================


class SessionInvalidFault(SessionFault):
    """
    Session ID is invalid or malformed.

    This may indicate tampering or data corruption.
    """

    code = "SESSION_INVALID"
    message = "Invalid session identifier"
    severity = Severity.ERROR
    public = True
    retryable = False


class SessionNotFoundFault(SessionFault):
    """
    Session ID not found in store.

    Session may have been deleted or expired.
    """

    code = "SESSION_NOT_FOUND"
    message = "Session not found"
    severity = Severity.WARN
    public = True
    retryable = False


class SessionPolicyViolationFault(SessionFault):
    """
    Session violates policy constraints.
    """

    code = "SESSION_POLICY_VIOLATION"
    message = "Session violates policy constraints"
    severity = Severity.ERROR
    public = False
    retryable = False

    def __init__(self, violation: str, policy_name: str, **kwargs):
        super().__init__(**kwargs)
        self.violation = violation
        self.policy_name = policy_name
        self.message = f"Session policy violation: {violation} (policy={policy_name})"


# ============================================================================
# Concurrency Faults
# ============================================================================


class SessionConcurrencyViolationFault(SessionFault):
    """
    Too many concurrent sessions for principal.
    """

    code = "SESSION_CONCURRENCY_VIOLATION"
    message = "Too many concurrent sessions"
    severity = Severity.ERROR
    public = True
    retryable = False

    def __init__(self, principal_id: str, active_count: int, max_allowed: int, **kwargs):
        super().__init__(**kwargs)
        self.principal_id = principal_id
        self.active_count = active_count
        self.max_allowed = max_allowed
        self.message = f"Concurrent session limit exceeded: {active_count}/{max_allowed} for principal {principal_id}"


class SessionLockedFault(SessionFault):
    """
    Session is locked by another operation. Retry after lock is released.
    """

    code = "SESSION_LOCKED"
    message = "Session is locked"
    severity = Severity.WARN
    public = False
    retryable = True


# ============================================================================
# Storage Faults
# ============================================================================


class SessionStoreUnavailableFault(SessionFault):
    """
    Session store is unavailable. Transient error - retry may succeed.
    """

    code = "SESSION_STORE_UNAVAILABLE"
    message = "Session storage unavailable"
    severity = Severity.ERROR
    public = False
    retryable = True

    def __init__(self, store_name: str, cause: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.store_name = store_name
        self.cause = cause
        if cause:
            self.message = f"Session store '{store_name}' unavailable: {cause}"
        else:
            self.message = f"Session store '{store_name}' unavailable"


class SessionStoreCorruptedFault(SessionFault):
    """
    Session data in store is corrupted.
    """

    code = "SESSION_STORE_CORRUPTED"
    message = "Session data corrupted"
    severity = Severity.ERROR
    public = False
    retryable = False

    def __init__(self, message: str | None = None, session_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        if message:
            self.message = message
        self.session_id_hash = self._hash_session_id(session_id) if session_id else None


# ============================================================================
# Rotation Faults
# ============================================================================


class SessionRotationFailedFault(SessionFault):
    """
    Session ID rotation failed. Session may be in inconsistent state.
    """

    code = "SESSION_ROTATION_FAILED"
    message = "Session rotation failed"
    severity = Severity.ERROR
    public = False
    retryable = True

    def __init__(self, old_id: str, new_id: str, cause: str, **kwargs):
        super().__init__(**kwargs)
        # Use own _hash_session_id instead of fragile cross-class reference
        self.old_id_hash = self._hash_session_id(old_id)
        self.new_id_hash = self._hash_session_id(new_id)
        self.cause = cause
        self.message = f"Session rotation failed: {cause}"


# ============================================================================
# Transport Faults
# ============================================================================


class SessionTransportFault(SessionFault):
    """
    Error extracting or injecting session via transport.
    """

    code = "SESSION_TRANSPORT_ERROR"
    message = "Session transport error"
    severity = Severity.WARN
    public = False
    retryable = False

    def __init__(self, transport_type: str, cause: str, **kwargs):
        super().__init__(**kwargs)
        self.transport_type = transport_type
        self.cause = cause
        self.message = f"Session transport error ({transport_type}): {cause}"


# ============================================================================
# Security Faults
# ============================================================================


class SessionForgeryAttemptFault(SessionFault):
    """
    Suspected session forgery or tampering. Security event.
    """

    code = "SESSION_FORGERY_ATTEMPT"
    message = "Suspected session forgery"
    severity = Severity.ERROR
    public = False
    retryable = False

    def __init__(self, reason: str, **kwargs):
        super().__init__(**kwargs)
        self.reason = reason
        self.message = f"Suspected session forgery: {reason}"


class SessionHijackAttemptFault(SessionFault):
    """
    Suspected session hijacking (IP/User-Agent mismatch).
    """

    code = "SESSION_HIJACK_ATTEMPT"
    message = "Suspected session hijacking"
    severity = Severity.ERROR
    public = False
    retryable = False

    def __init__(self, reason: str, **kwargs):
        super().__init__(**kwargs)
        self.reason = reason
        self.message = f"Suspected session hijacking: {reason}"


class SessionFingerprintMismatchFault(SessionFault):
    """
    Session fingerprint does not match client (OWASP hijack detection).

    The stored fingerprint (hash of IP + User-Agent) does not match the
    current request, indicating possible session hijacking.
    """

    code = "SESSION_FINGERPRINT_MISMATCH"
    message = "Session fingerprint mismatch - possible hijack"
    severity = Severity.ERROR
    public = False
    retryable = False

    def __init__(self, session_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.session_id_hash = self._hash_session_id(session_id) if session_id else None
