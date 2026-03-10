"""
AquilaFaults - Domain-specific fault types.

Provides concrete fault classes for each domain:
- CONFIG faults
- REGISTRY faults  
- DI faults
- ROUTING faults
- FLOW faults
- EFFECT faults
- IO faults
- SECURITY faults
- SYSTEM faults
"""

from typing import Any, Optional
from .core import Fault, FaultDomain, Severity


# ============================================================================
# CONFIG Faults
# ============================================================================

class ConfigFault(Fault):
    """Base class for configuration faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.FATAL,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.CONFIG,
            severity=severity,
            retryable=False,
            public=False,
            metadata=metadata,
        )


class ConfigMissingFault(ConfigFault):
    """Required configuration is missing."""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            code="CONFIG_MISSING",
            message=f"Required configuration key '{key}' is missing",
            metadata={"key": key, **kwargs.get("metadata", {})},
        )


class ConfigInvalidFault(ConfigFault):
    """Configuration value is invalid."""
    
    def __init__(self, key: str, reason: str, **kwargs):
        super().__init__(
            code="CONFIG_INVALID",
            message=f"Configuration key '{key}' is invalid: {reason}",
            metadata={"key": key, "reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# REGISTRY Faults
# ============================================================================

class RegistryFault(Fault):
    """Base class for Aquilary registry faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.FATAL,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.REGISTRY,
            severity=severity,
            retryable=False,
            public=False,
            metadata=metadata,
        )


class DependencyCycleFault(RegistryFault):
    """Circular dependency detected in app graph."""
    
    def __init__(self, cycle: list[str], **kwargs):
        cycle_str = " → ".join(cycle)
        super().__init__(
            code="DEPENDENCY_CYCLE",
            message=f"Circular dependency detected: {cycle_str}",
            metadata={"cycle": cycle, **kwargs.get("metadata", {})},
        )


class ManifestInvalidFault(RegistryFault):
    """Manifest validation failed."""
    
    def __init__(self, manifest_name: str, errors: list[str], **kwargs):
        super().__init__(
            code="MANIFEST_INVALID",
            message=f"Manifest '{manifest_name}' validation failed: {'; '.join(errors)}",
            metadata={"manifest": manifest_name, "errors": errors, **kwargs.get("metadata", {})},
        )


# ============================================================================
# DI Faults
# ============================================================================

class DIFault(Fault):
    """Base class for dependency injection faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.DI,
            severity=severity,
            retryable=False,
            public=False,
            metadata=metadata,
        )


class ProviderNotFoundFault(DIFault):
    """DI provider not found."""
    
    def __init__(self, provider_name: str, app: Optional[str] = None, **kwargs):
        super().__init__(
            code="PROVIDER_NOT_FOUND",
            message=f"DI provider '{provider_name}' not found" + (f" in app '{app}'" if app else ""),
            metadata={"provider": provider_name, "app": app, **kwargs.get("metadata", {})},
        )


class ScopeViolationFault(DIFault):
    """DI scope violation."""
    
    def __init__(self, provider: str, expected_scope: str, actual_scope: str, **kwargs):
        super().__init__(
            code="SCOPE_VIOLATION",
            message=f"Provider '{provider}' scope violation: expected {expected_scope}, got {actual_scope}",
            metadata={
                "provider": provider,
                "expected_scope": expected_scope,
                "actual_scope": actual_scope,
                **kwargs.get("metadata", {}),
            },
        )


class DIResolutionFault(DIFault):
    """DI resolution failed."""
    
    def __init__(self, provider: str, reason: str, **kwargs):
        super().__init__(
            code="DI_RESOLUTION_FAILED",
            message=f"Failed to resolve '{provider}': {reason}",
            metadata={"provider": provider, "reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# ROUTING Faults
# ============================================================================

class RoutingFault(Fault):
    """Base class for routing faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        public: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.ROUTING,
            severity=severity,
            retryable=False,
            public=public,
            metadata=metadata,
        )


class RouteNotFoundFault(RoutingFault):
    """Route not found."""
    
    def __init__(self, path: str, method: str, **kwargs):
        super().__init__(
            code="ROUTE_NOT_FOUND",
            message=f"Route not found: {method} {path}",
            metadata={"path": path, "method": method, **kwargs.get("metadata", {})},
        )


class RouteAmbiguousFault(RoutingFault):
    """Multiple routes match the pattern."""
    
    def __init__(self, path: str, matches: list[str], **kwargs):
        super().__init__(
            code="ROUTE_AMBIGUOUS",
            message=f"Multiple routes match '{path}': {', '.join(matches)}",
            severity=Severity.WARN,
            public=False,
            metadata={"path": path, "matches": matches, **kwargs.get("metadata", {})},
        )


class PatternInvalidFault(RoutingFault):
    """Route pattern is invalid."""
    
    def __init__(self, pattern: str, reason: str, **kwargs):
        super().__init__(
            code="PATTERN_INVALID",
            message=f"Invalid route pattern '{pattern}': {reason}",
            severity=Severity.FATAL,
            public=False,
            metadata={"pattern": pattern, "reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# FLOW Faults
# ============================================================================

class FlowFault(Fault):
    """Base class for flow execution faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.FLOW,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


class HandlerFault(FlowFault):
    """Handler execution failed."""
    
    def __init__(self, handler_name: str, reason: str, **kwargs):
        super().__init__(
            code="HANDLER_FAILED",
            message=f"Handler '{handler_name}' failed: {reason}",
            metadata={"handler": handler_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class MiddlewareFault(FlowFault):
    """Middleware execution failed."""
    
    def __init__(self, middleware_name: str, reason: str, **kwargs):
        super().__init__(
            code="MIDDLEWARE_FAILED",
            message=f"Middleware '{middleware_name}' failed: {reason}",
            metadata={"middleware": middleware_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class FlowCancelledFault(FlowFault):
    """Flow was cancelled (timeout or client disconnect)."""
    
    def __init__(self, reason: str = "timeout", **kwargs):
        super().__init__(
            code="FLOW_CANCELLED",
            message=f"Flow cancelled: {reason}",
            severity=Severity.WARN,
            retryable=False,
            public=True,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# EFFECT Faults
# ============================================================================

class EffectFault(Fault):
    """Base class for effect (side-effect) faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.EFFECT,
            severity=severity,
            retryable=retryable,
            public=False,
            metadata=metadata,
        )


class DatabaseFault(EffectFault):
    """Database operation failed."""
    
    def __init__(self, operation: str, reason: str, **kwargs):
        super().__init__(
            code="DATABASE_FAULT",
            message=f"Database {operation} failed: {reason}",
            metadata={"operation": operation, "reason": reason, **kwargs.get("metadata", {})},
        )


class CacheFault(EffectFault):
    """Cache operation failed."""
    
    def __init__(self, operation: str, key: str, reason: str, **kwargs):
        super().__init__(
            code="CACHE_FAULT",
            message=f"Cache {operation} for key '{key}' failed: {reason}",
            severity=Severity.WARN,
            metadata={"operation": operation, "key": key, "reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# IO Faults
# ============================================================================

class IOFault(Fault):
    """Base class for I/O faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.WARN,
        retryable: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.IO,
            severity=severity,
            retryable=retryable,
            public=False,
            metadata=metadata,
        )


class NetworkFault(IOFault):
    """Network operation failed."""
    
    def __init__(self, operation: str, reason: str, **kwargs):
        super().__init__(
            code="NETWORK_FAULT",
            message=f"Network {operation} failed: {reason}",
            metadata={"operation": operation, "reason": reason, **kwargs.get("metadata", {})},
        )


class FilesystemFault(IOFault):
    """Filesystem operation failed."""
    
    def __init__(self, operation: str, path: str, reason: str, **kwargs):
        super().__init__(
            code="FILESYSTEM_FAULT",
            message=f"Filesystem {operation} on '{path}' failed: {reason}",
            metadata={"operation": operation, "path": path, "reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# SECURITY Faults
# ============================================================================

class SecurityFault(Fault):
    """Base class for security faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        public: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.SECURITY,
            severity=severity,
            retryable=False,
            public=public,
            metadata=metadata,
        )


class AuthenticationFault(SecurityFault):
    """Authentication failed."""
    
    def __init__(self, reason: str = "Invalid credentials", **kwargs):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=reason,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class AuthorizationFault(SecurityFault):
    """Authorization failed."""
    
    def __init__(self, resource: str, action: str, **kwargs):
        super().__init__(
            code="AUTHORIZATION_FAILED",
            message=f"Not authorized to {action} resource '{resource}'",
            metadata={"resource": resource, "action": action, **kwargs.get("metadata", {})},
        )


class CSRFViolationFault(SecurityFault):
    """CSRF token validation failed."""
    
    def __init__(self, reason: str = "CSRF validation failed", **kwargs):
        self.reason = reason
        super().__init__(
            code="CSRF_VIOLATION",
            message=reason,
            severity=Severity.WARN,
            public=True,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class CORSViolationFault(SecurityFault):
    """CORS origin not allowed."""
    
    def __init__(self, origin: str, **kwargs):
        super().__init__(
            code="CORS_VIOLATION",
            message=f"Origin '{origin}' is not allowed by CORS policy",
            severity=Severity.WARN,
            public=True,
            metadata={"origin": origin, **kwargs.get("metadata", {})},
        )


class RateLimitExceededFault(SecurityFault):
    """Rate limit exceeded for client."""
    
    def __init__(self, limit: int, window: float, retry_after: float, **kwargs):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded ({limit} requests per {window}s). Retry after {int(retry_after)}s",
            severity=Severity.WARN,
            public=True,
            metadata={
                "limit": limit,
                "window": window,
                "retry_after": retry_after,
                **kwargs.get("metadata", {}),
            },
        )


class CSPViolationFault(SecurityFault):
    """Content Security Policy violation reported."""
    
    def __init__(self, directive: str, blocked_uri: str = "", **kwargs):
        super().__init__(
            code="CSP_VIOLATION",
            message=f"CSP violation: directive '{directive}' blocked '{blocked_uri}'",
            severity=Severity.WARN,
            public=False,
            metadata={
                "directive": directive,
                "blocked_uri": blocked_uri,
                **kwargs.get("metadata", {}),
            },
        )


# ── Signing Faults ──────────────────────────────────────────────────────

class SigningFault(SecurityFault):
    """Base class for all signing/verification faults."""

    def __init__(
        self,
        code: str = "SIGNING_ERROR",
        message: str = "Signing operation failed",
        *,
        severity: Severity = Severity.ERROR,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            severity=severity,
            public=False,
            metadata=metadata,
        )


class BadSignatureFault(SigningFault):
    """
    Signature verification failed — potential tampering.

    Callers should treat this as a security event and **not** use
    the payload value.
    """

    def __init__(
        self,
        message: str = "Signature is invalid",
        *,
        original: str | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        #: The raw signed value that failed verification (for logging).
        self.original = original
        super().__init__(
            code="SIGNING_BAD_SIGNATURE",
            message=message,
            metadata={"original": original, **(metadata or {})},
        )


class SignatureExpiredFault(BadSignatureFault):
    """
    The signature is valid but the embedded timestamp has exceeded max_age.

    Subclasses :class:`BadSignatureFault` so callers that only catch
    ``BadSignatureFault`` also catch expired signatures automatically.
    """

    def __init__(
        self,
        message: str = "Signature has expired",
        *,
        original: str | None = None,
        date_signed: Any = None,
        age_seconds: float | None = None,
        max_age_seconds: float | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        #: When the token was originally signed (UTC).
        self.date_signed = date_signed
        #: How old the token is in seconds.
        self.age_seconds = age_seconds
        #: The configured maximum age in seconds.
        self.max_age_seconds = max_age_seconds
        super().__init__(
            message=message,
            original=original,
            metadata={
                "date_signed": str(date_signed) if date_signed else None,
                "age_seconds": age_seconds,
                "max_age_seconds": max_age_seconds,
                **(metadata or {}),
            },
        )


class SignatureMalformedFault(SigningFault):
    """
    The signed value could not be parsed at all (wrong number of parts,
    non-base64 characters, corrupted JSON, etc.).

    Unlike :class:`BadSignatureFault`, this indicates a malformed input
    rather than a valid-but-wrong signature.
    """

    def __init__(self, message: str = "Signed value is malformed", **kwargs):
        super().__init__(
            code="SIGNING_MALFORMED",
            message=message,
            metadata=kwargs.get("metadata"),
        )


class UnsupportedAlgorithmFault(SigningFault):
    """
    The requested algorithm is not available (e.g. asymmetric algorithm
    requested but the ``cryptography`` package is not installed).
    """

    def __init__(self, algorithm: str, reason: str = "", **kwargs):
        super().__init__(
            code="SIGNING_UNSUPPORTED_ALGORITHM",
            message=f"Unsupported signing algorithm '{algorithm}'"
            + (f": {reason}" if reason else ""),
            severity=Severity.FATAL,
            metadata={"algorithm": algorithm, "reason": reason, **(kwargs.get("metadata") or {})},
        )


# ============================================================================
# SYSTEM Faults
# ============================================================================

class SystemFault(Fault):
    """Base class for fatal system faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.FATAL,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.SYSTEM,
            severity=severity,
            retryable=False,
            public=False,
            metadata=metadata,
        )


class UnrecoverableFault(SystemFault):
    """Unrecoverable system fault."""
    
    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="UNRECOVERABLE",
            message=f"Unrecoverable system fault: {reason}",
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class ResourceExhaustedFault(SystemFault):
    """System resources exhausted."""
    
    def __init__(self, resource: str, *, message: str = "", **kwargs):
        super().__init__(
            code="RESOURCE_EXHAUSTED",
            message=message or f"System resource exhausted: {resource}",
            severity=Severity.FATAL,
            metadata={"resource": resource, **kwargs.get("metadata", {})},
        )


# ============================================================================
# MODEL Faults (ORM / Database)
# ============================================================================

class ModelFault(Fault):
    """Base class for model and database faults."""
    
    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.MODEL,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


class AMDLParseFault(ModelFault):
    """AMDL file parsing failed."""
    
    def __init__(self, file: str, line: int, reason: str, **kwargs):
        super().__init__(
            code="AMDL_PARSE_ERROR",
            message=f"AMDL parse error in '{file}' at line {line}: {reason}",
            severity=Severity.FATAL,
            metadata={"file": file, "line": line, "reason": reason, **kwargs.get("metadata", {})},
        )


class ModelNotFoundFault(ModelFault):
    """Model not found in registry."""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"Model '{model_name}' not found in ModelRegistry",
            metadata={"model": model_name, **kwargs.get("metadata", {})},
        )


class ModelRegistrationFault(ModelFault):
    """Model registration failed."""
    
    def __init__(self, model_name: str, reason: str, **kwargs):
        super().__init__(
            code="MODEL_REGISTRATION_FAILED",
            message=f"Failed to register model '{model_name}': {reason}",
            metadata={"model": model_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class MigrationFault(ModelFault):
    """Database migration failed."""
    
    def __init__(self, migration: str, reason: str, **kwargs):
        super().__init__(
            code="MIGRATION_FAILED",
            message=f"Migration '{migration}' failed: {reason}",
            metadata={"migration": migration, "reason": reason, **kwargs.get("metadata", {})},
        )


class MigrationConflictFault(ModelFault):
    """Migration conflict detected (e.g. divergent migration branches)."""
    
    def __init__(self, conflicting: list[str], **kwargs):
        super().__init__(
            code="MIGRATION_CONFLICT",
            message=f"Migration conflict: {', '.join(conflicting)}",
            severity=Severity.FATAL,
            metadata={"conflicting": conflicting, **kwargs.get("metadata", {})},
        )


class QueryFault(ModelFault):
    """Query execution failed."""
    
    def __init__(self, model: str = "unknown", operation: str = "query", reason: str = "", *, message: str = "", **kwargs):
        if message and not reason:
            reason = message
        super().__init__(
            code="QUERY_FAILED",
            message=message or f"Query on '{model}' ({operation}) failed: {reason}",
            retryable=True,
            metadata={"model": model, "operation": operation, "reason": reason, **kwargs.get("metadata", {})},
        )


class DatabaseConnectionFault(ModelFault):
    """Database connection failed."""
    
    def __init__(self, url: str = "", reason: str = "", *, backend: str = "", **kwargs):
        display = backend or url
        super().__init__(
            code="DB_CONNECTION_FAILED",
            message=f"Database connection failed ({display}): {reason}",
            severity=Severity.FATAL,
            retryable=True,
            metadata={"url": url, "backend": backend, "reason": reason, **kwargs.get("metadata", {})},
        )


class SchemaFault(ModelFault):
    """Schema creation or validation failed."""
    
    def __init__(self, table: str, reason: str, **kwargs):
        super().__init__(
            code="SCHEMA_FAULT",
            message=f"Schema error for table '{table}': {reason}",
            severity=Severity.FATAL,
            metadata={"table": table, "reason": reason, **kwargs.get("metadata", {})},
        )


class FieldValidationFault(ModelFault):
    """Field validation failed."""

    def __init__(self, field_name: str, reason: str, **kwargs):
        super().__init__(
            code="FIELD_VALIDATION_FAILED",
            message=f"Field '{field_name}': {reason}",
            severity=Severity.ERROR,
            metadata={"field": field_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class ProtectedDeleteFault(ModelFault):
    """Cannot delete a protected object due to PROTECT on_delete."""

    def __init__(self, model: str, reason: str, protected_count: int = 0, **kwargs):
        super().__init__(
            code="PROTECTED_DELETE",
            message=f"Cannot delete {model}: {reason}",
            severity=Severity.ERROR,
            metadata={
                "model": model,
                "reason": reason,
                "protected_count": protected_count,
                **kwargs.get("metadata", {}),
            },
        )


class RestrictedDeleteFault(ModelFault):
    """Cannot delete a restricted object due to RESTRICT on_delete."""

    def __init__(self, model: str, reason: str, restricted_count: int = 0, **kwargs):
        super().__init__(
            code="RESTRICTED_DELETE",
            message=f"Cannot delete {model}: {reason}",
            severity=Severity.ERROR,
            metadata={
                "model": model,
                "reason": reason,
                "restricted_count": restricted_count,
                **kwargs.get("metadata", {}),
            },
        )


# ============================================================================
# HTTP Faults — First-class HTTP protocol errors
# ============================================================================
#
# Standard HTTP status codes as typed fault signals.
#
# Design principles:
#   • Every fault carries an explicit ``status`` attribute — no guessing.
#   • ``public=True`` by default: HTTP errors are user-facing.
#   • Each subclass has sensible defaults but accepts overrides.
#   • The ``detail`` kwarg provides the human-readable explanation shown
#     on the styled error page.
#   • Extra headers (e.g. ``Allow`` for 405, ``Retry-After`` for 429/503)
#     are stored in ``metadata["headers"]`` and applied by the transport.
#
# Usage:
#     raise NotFoundFault(detail="/api/users/999 does not exist")
#     raise MethodNotAllowedFault(allowed=["GET", "POST"])
#     raise TooManyRequestsFault(retry_after=60)
# ============================================================================

# Canonical reason phrases (RFC 9110 §15)
_HTTP_REASONS: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Content Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a Teapot",
    421: "Misdirected Request",
    422: "Unprocessable Content",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}


def http_reason(status: int) -> str:
    """Return the canonical RFC 9110 reason phrase for *status*."""
    return _HTTP_REASONS.get(status, "Unknown Error")


class HTTPFault(Fault):
    """Base class for HTTP protocol error faults.

    Every HTTP fault carries:
      * ``status`` — the HTTP status code (e.g. 404)
      * ``detail`` — a human-readable explanation for the error page
      * optional extra ``headers`` in ``metadata["headers"]``

    ``public`` defaults to ``True`` because HTTP errors are user-facing.
    ``domain`` is always ``FaultDomain.HTTP``.
    """

    def __init__(
        self,
        status: int,
        message: str | None = None,
        *,
        code: str | None = None,
        detail: str = "",
        severity: Severity = Severity.WARN,
        headers: dict[str, str] | None = None,
        public: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        if not isinstance(status, int) or not (400 <= status <= 599):
            raise ValueError(
                f"HTTPFault status must be an integer in 400..599, got {status!r}"
            )
        self.status = status
        self.detail = detail
        reason = http_reason(status)
        _code = code or f"HTTP_{status}"
        _message = message or reason
        _meta: dict[str, Any] = metadata.copy() if metadata else {}
        _meta["status"] = status
        _meta["reason"] = reason
        if detail:
            _meta["detail"] = detail
        if headers:
            _meta["headers"] = headers
        super().__init__(
            code=_code,
            message=_message,
            domain=FaultDomain.HTTP,
            severity=severity,
            retryable=False,
            public=public,
            metadata=_meta,
        )

    def __repr__(self) -> str:
        try:
            return (
                f"{type(self).__name__}(status={self.status}, "
                f"code={self.code!r}, detail={self.detail!r})"
            )
        except AttributeError:
            # __init__ may have raised before setting all attributes
            return f"{type(self).__name__}(<incomplete>)"


# ── 4xx Client Errors ────────────────────────────────────────────────

class BadRequestFault(HTTPFault):
    """400 Bad Request."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(400, detail=detail, **kw)


class UnauthorizedFault(HTTPFault):
    """401 Unauthorized."""
    def __init__(self, detail: str = "", *, scheme: str = "Bearer", **kw: Any):
        headers = kw.pop("headers", None) or {}
        if "WWW-Authenticate" not in headers:
            headers["WWW-Authenticate"] = scheme
        super().__init__(401, detail=detail, headers=headers, **kw)


class PaymentRequiredFault(HTTPFault):
    """402 Payment Required."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(402, detail=detail, **kw)


class ForbiddenFault(HTTPFault):
    """403 Forbidden."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(403, detail=detail, **kw)


class NotFoundFault(HTTPFault):
    """404 Not Found."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(404, detail=detail, **kw)


class MethodNotAllowedFault(HTTPFault):
    """405 Method Not Allowed.

    Requires an ``allowed`` list of methods per RFC 9110 §15.5.6.
    The ``Allow`` header is stored in ``metadata["headers"]`` and
    applied automatically by the transport layer.
    """
    def __init__(self, allowed: list[str] | None = None, *, detail: str = "", **kw: Any):
        allowed = allowed or []
        headers = kw.pop("headers", None) or {}
        headers["Allow"] = ", ".join(sorted(allowed))
        _meta = kw.pop("metadata", None) or {}
        _meta["allowed_methods"] = sorted(allowed)
        super().__init__(
            405, detail=detail or f"Allowed methods: {', '.join(sorted(allowed))}",
            headers=headers, metadata=_meta, **kw,
        )


class NotAcceptableFault(HTTPFault):
    """406 Not Acceptable."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(406, detail=detail, **kw)


class RequestTimeoutFault(HTTPFault):
    """408 Request Timeout."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(408, detail=detail, **kw)


class ConflictFault(HTTPFault):
    """409 Conflict."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(409, detail=detail, **kw)


class GoneFault(HTTPFault):
    """410 Gone."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(410, detail=detail, **kw)


class PayloadTooLargeFault(HTTPFault):
    """413 Content Too Large."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(413, detail=detail, **kw)


class URITooLongFault(HTTPFault):
    """414 URI Too Long."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(414, detail=detail, **kw)


class UnsupportedMediaTypeFault(HTTPFault):
    """415 Unsupported Media Type."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(415, detail=detail, **kw)


class UnprocessableEntityFault(HTTPFault):
    """422 Unprocessable Content."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(422, detail=detail, **kw)


class LockedFault(HTTPFault):
    """423 Locked."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(423, detail=detail, **kw)


class TooEarlyFault(HTTPFault):
    """425 Too Early."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(425, detail=detail, **kw)


class PreconditionRequiredFault(HTTPFault):
    """428 Precondition Required."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(428, detail=detail, **kw)


class TooManyRequestsFault(HTTPFault):
    """429 Too Many Requests.

    Includes ``Retry-After`` header when *retry_after* is provided.
    """
    def __init__(self, detail: str = "", *, retry_after: int | None = None, **kw: Any):
        headers = kw.pop("headers", None) or {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        _meta = kw.pop("metadata", None) or {}
        if retry_after is not None:
            _meta["retry_after"] = retry_after
        super().__init__(
            429,
            detail=detail or (f"Retry after {retry_after}s" if retry_after else ""),
            headers=headers, metadata=_meta, **kw,
        )


class RequestHeaderFieldsTooLargeFault(HTTPFault):
    """431 Request Header Fields Too Large."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(431, detail=detail, **kw)


class UnavailableForLegalReasonsFault(HTTPFault):
    """451 Unavailable For Legal Reasons."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(451, detail=detail, **kw)


# ── 5xx Server Errors ────────────────────────────────────────────────

class InternalServerErrorFault(HTTPFault):
    """500 Internal Server Error."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(500, detail=detail, severity=Severity.ERROR, **kw)


class NotImplementedFault(HTTPFault):
    """501 Not Implemented."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(501, detail=detail, severity=Severity.ERROR, **kw)


class BadGatewayFault(HTTPFault):
    """502 Bad Gateway."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(502, detail=detail, severity=Severity.ERROR, **kw)


class ServiceUnavailableFault(HTTPFault):
    """503 Service Unavailable.

    Includes ``Retry-After`` header when *retry_after* is provided.
    """
    def __init__(self, detail: str = "", *, retry_after: int | None = None, **kw: Any):
        headers = kw.pop("headers", None) or {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        _meta = kw.pop("metadata", None) or {}
        if retry_after is not None:
            _meta["retry_after"] = retry_after
        super().__init__(
            503, detail=detail, severity=Severity.ERROR,
            headers=headers, metadata=_meta, **kw,
        )


class GatewayTimeoutFault(HTTPFault):
    """504 Gateway Timeout."""
    def __init__(self, detail: str = "", **kw: Any):
        super().__init__(504, detail=detail, severity=Severity.ERROR, **kw)


# ============================================================================
# PROVIDER Faults
# ============================================================================

class ProviderFault(Fault):
    """Base class for cloud provider integration faults."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.PROVIDER,
            severity=severity,
            retryable=retryable,
            public=False,
            metadata=metadata,
        )


class ProviderAPIFault(ProviderFault):
    """Cloud provider API returned an error response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        detail: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: str = "render",
        **kwargs,
    ):
        self.status_code = status_code
        self.detail = detail
        self.request_id = request_id
        retryable = status_code >= 500
        super().__init__(
            code="PROVIDER_API_ERROR",
            message=f"[{status_code}] {message}",
            severity=Severity.ERROR,
            retryable=retryable,
            metadata={
                "status_code": status_code,
                "provider": provider,
                **({"detail": detail} if detail else {}),
                **({"request_id": request_id} if request_id else {}),
                **kwargs.get("metadata", {}),
            },
        )


class ProviderAuthFault(ProviderFault):
    """Cloud provider authentication failure (401/403)."""

    def __init__(
        self,
        status_code: int = 401,
        message: str = "Authentication failed",
        *,
        request_id: Optional[str] = None,
        provider: str = "render",
        **kwargs,
    ):
        self.status_code = status_code
        self.request_id = request_id
        super().__init__(
            code="PROVIDER_AUTH_FAILED",
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            metadata={
                "status_code": status_code,
                "provider": provider,
                **({"request_id": request_id} if request_id else {}),
                **kwargs.get("metadata", {}),
            },
        )


class ProviderRateLimitFault(ProviderFault):
    """Cloud provider rate limit exceeded (429)."""

    def __init__(
        self,
        retry_after: float,
        *,
        provider: str = "render",
        **kwargs,
    ):
        self.retry_after = retry_after
        super().__init__(
            code="PROVIDER_RATE_LIMITED",
            message=f"Rate limited — retry after {retry_after:.1f}s",
            severity=Severity.WARN,
            retryable=True,
            metadata={
                "retry_after": retry_after,
                "provider": provider,
                **kwargs.get("metadata", {}),
            },
        )


class ProviderTokenFault(ProviderFault):
    """Provider API token is missing, invalid, or expired."""

    def __init__(
        self,
        reason: str = "API token is required",
        *,
        provider: str = "render",
        **kwargs,
    ):
        super().__init__(
            code="PROVIDER_TOKEN_INVALID",
            message=reason,
            severity=Severity.ERROR,
            retryable=False,
            metadata={
                "provider": provider,
                **kwargs.get("metadata", {}),
            },
        )


class ProviderCredentialFault(ProviderFault):
    """Credential storage or retrieval failure."""

    def __init__(
        self,
        reason: str,
        *,
        provider: str = "render",
        path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            code="PROVIDER_CREDENTIAL_ERROR",
            message=f"Credential store error: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={
                "provider": provider,
                "reason": reason,
                **({"path": path} if path else {}),
                **kwargs.get("metadata", {}),
            },
        )


class ProviderConnectionFault(ProviderFault):
    """Network connection to provider API failed."""

    def __init__(
        self,
        reason: str,
        *,
        provider: str = "render",
        **kwargs,
    ):
        super().__init__(
            code="PROVIDER_CONNECTION_FAILED",
            message=f"Connection failed: {reason}",
            severity=Severity.ERROR,
            retryable=True,
            metadata={
                "provider": provider,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


# ============================================================================
# DEPLOY Faults
# ============================================================================

class DeployFault(Fault):
    """Base class for deployment orchestration faults."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.DEPLOY,
            severity=severity,
            retryable=retryable,
            public=False,
            metadata=metadata,
        )


class DeployConfigFault(DeployFault):
    """Deployment configuration is invalid or incomplete."""

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="DEPLOY_CONFIG_INVALID",
            message=f"Invalid deploy configuration: {reason}",
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class DeployImageFault(DeployFault):
    """Docker image build or push failure."""

    def __init__(self, phase: str, reason: str, **kwargs):
        super().__init__(
            code="DEPLOY_IMAGE_FAILED",
            message=f"Docker {phase} failed: {reason}",
            metadata={
                "phase": phase,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


class DeployHealthFault(DeployFault):
    """Deployed service did not become healthy."""

    def __init__(
        self,
        last_status: str,
        *,
        timeout: Optional[int] = None,
        messages: Optional[list[str]] = None,
        **kwargs,
    ):
        super().__init__(
            code="DEPLOY_UNHEALTHY",
            message=f"Deployment unhealthy — last status: {last_status}",
            retryable=True,
            metadata={
                "last_status": last_status,
                **({"timeout": timeout} if timeout else {}),
                **({"messages": messages} if messages else {}),
                **kwargs.get("metadata", {}),
            },
        )


class DeployAppFault(DeployFault):
    """Failed to create or resolve the provider app."""

    def __init__(self, app_name: str, reason: str, **kwargs):
        super().__init__(
            code="DEPLOY_APP_FAILED",
            message=f"App '{app_name}': {reason}",
            metadata={
                "app_name": app_name,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


class DeployServiceFault(DeployFault):
    """Failed to create or update the provider service."""

    def __init__(self, service_name: str, reason: str, **kwargs):
        super().__init__(
            code="DEPLOY_SERVICE_FAILED",
            message=f"Service '{service_name}': {reason}",
            metadata={
                "service_name": service_name,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )