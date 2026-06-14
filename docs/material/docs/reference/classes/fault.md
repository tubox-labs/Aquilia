# Fault System

## Overview

Aquilia's **Fault** system replaces bare Python exceptions with structured, typed fault signals. Every fault carries a stable `code`, human-readable `message`, `domain`, `severity`, and optional `metadata`. Faults flow through the system with context, lifecycle, and intent — they are first-class values, not surprises.

!!! quote "Philosophy"
    - Errors are data, not surprises
    - Errors flow through pipelines
    - Errors are scoped, observable, and explicit

---

## `Fault` Base Class

!!! abstract "`aquilia.faults.Fault`"
    Extends `Exception`

```python
class Fault(Exception):
    def __init__(
        self,
        code: str | None = None,
        message: str | None = None,
        *,
        domain: FaultDomain | None = None,
        severity: Severity | None = None,
        retryable: bool | None = None,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `code` | `str \| None` | Class default | Stable machine-readable identifier (`"USER_NOT_FOUND"`) |
| `message` | `str \| None` | Class default | Human-readable summary |
| `domain` | `FaultDomain \| None` | Class default | Fault domain classification |
| `severity` | `Severity \| None` | Domain default | Severity level |
| `retryable` | `bool \| None` | Domain default | Whether fault can be retried |
| `public` | `bool` | `False` | Safe to expose to client? |
| `metadata` | `dict[str, Any] \| None` | `None` | Additional context data |
| `**kwargs` | — | — | Merged into `metadata` |

### Properties Set at Init

| Property | Type | Description |
|---|---|---|
| `code` | `str` | Stable machine-readable identifier |
| `message` | `str` | Human-readable summary |
| `domain` | `FaultDomain` | Fault domain |
| `severity` | `Severity` | Severity level |
| `retryable` | `bool` | Retry semantics |
| `public` | `bool` | Client exposure flag |
| `metadata` | `dict[str, Any]` | Additional context |

### Methods

```python
def to_dict(self) -> dict[str, Any]:
    """Serialize to dict for logging/serialization."""

def _hash_identifier(self, identifier: str) -> str:
    """Hash sensitive identifiers (SHA-256, 16-char hex)."""

def __rshift__(self, other: type[Fault] | Fault) -> Fault:
    """Transform fault chain operator."""
```

#### Transform Operator (`>>`)

```python
raise DatabaseFault(...) >> ApiFault("USER_FETCH_FAILED")
```

Preserves causality in `metadata["_cause"]` and `metadata["_transform_chain"]`.

---

## `Severity` Enum

```python
class Severity(str, Enum):
    INFO = "info"     # alias: LOW
    WARN = "warn"     # alias: MEDIUM
    ERROR = "error"   # alias: HIGH
    FATAL = "fatal"   # alias: CRITICAL
```

| Level | Meaning | Logging | Default For |
|---|---|---|---|
| `INFO` | Informational | `logger.info` | Rare |
| `WARN` | Should be reviewed | `logger.warning` | HTTP errors, I/O, cache misses |
| `ERROR` | Immediate attention | `logger.error` | Flow, DI, security, model |
| `FATAL` | Unrecoverable | `logger.critical` | Config, registry, system |

---

## `RecoveryStrategy` Enum

```python
class RecoveryStrategy(str, Enum):
    PROPAGATE = "propagate"   # Bubble up to next handler (default)
    RETRY = "retry"           # Retry with backoff
    FALLBACK = "fallback"     # Return fallback value
    MASK = "mask"             # Suppress, log only
    CIRCUIT_BREAK = "break"   # Trip circuit breaker
```

---

## `FaultDomain` — Standard Domains

```python
class FaultDomain:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.value = name
        self.description = description

    @classmethod
    def custom(cls, name: str, description: str = "") -> FaultDomain:
```

### All 17 Standard Domains

| Domain | Name | Severity | Retryable | Description |
|---|---|---|---|---|
| `CONFIG` | `"config"` | FATAL | No | Configuration errors |
| `REGISTRY` | `"registry"` | FATAL | No | Aquilary registry errors |
| `DI` | `"di"` | ERROR | No | Dependency injection errors |
| `ROUTING` | `"routing"` | ERROR | No | Route matching errors |
| `FLOW` | `"flow"` | ERROR | No | Handler execution errors |
| `EFFECT` | `"effect"` | ERROR | Yes | Side effect failures |
| `IO` | `"io"` | WARN | Yes | I/O operations |
| `SECURITY` | `"security"` | ERROR | No | Security and auth |
| `SYSTEM` | `"system"` | FATAL | No | System level faults |
| `MODEL` | `"model"` | ERROR | No | ORM and database |
| `CACHE` | `"cache"` | ERROR | Yes | Cache subsystem |
| `STORAGE` | `"storage"` | ERROR | No | File storage |
| `TASKS` | `"tasks"` | ERROR | Yes | Background tasks |
| `TEMPLATE` | `"template"` | ERROR | No | Template engine |
| `HTTP` | `"http"` | WARN | No | HTTP protocol errors |
| `PROVIDER` | `"provider"` | ERROR | Yes | Cloud provider integration |
| `DEPLOY` | `"deploy"` | ERROR | No | Deployment orchestration |

```python
# Custom domain
PAYMENT_DOMAIN = FaultDomain.custom("payment", "Payment processing faults")
```

---

## `FaultContext`

!!! abstract "`aquilia.faults.FaultContext`"
    Slotted dataclass

```python
@dataclass(slots=True)
class FaultContext:
    fault: Fault
    trace_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Scope
    app: str | None = None
    route: str | None = None
    request_id: str | None = None

    # Causality
    cause: Exception | None = None
    stack: list[Any] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Nesting
    parent: FaultContext | None = None
```

### Methods

```python
@classmethod
def capture(
    cls,
    fault: Fault,
    *,
    app: str | None = None,
    route: str | None = None,
    request_id: str | None = None,
    cause: Exception | None = None,
    parent: FaultContext | None = None,
) -> FaultContext: ...
```
Auto-generates `trace_id` (SHA-256 of `code + timestamp`) and extracts stack trace.

```python
def fingerprint(self) -> str:
    """SHA-256(code + domain + app + route) → 16-char hex. Used for dedup/correlation."""

def to_dict(self) -> dict[str, Any]:
    """Serialize to dict."""
```

---

## `FaultResult` — Handler Outcome Types

Three discriminated result types:

### `Resolved`

```python
@dataclass(frozen=True)
class Resolved:
    """Fault resolved — do not propagate further."""
    response: Any
```

### `Transformed`

```python
@dataclass(frozen=True)
class Transformed:
    """Fault transformed into another fault. Continues propagating."""
    fault: Fault
    preserve_context: bool = True
```

### `Escalate`

```python
@dataclass(frozen=True)
class Escalate:
    """Handler declined — escalate to next handler."""
    pass
```

### Union Type

```python
FaultResult = Resolved | Transformed | Escalate
```

---

## `FaultEngine`

!!! abstract "`aquilia.faults.FaultEngine`"

Central runtime fault handler. Registers `FaultHandler` instances and processes faults through them in priority order.

```python
class FaultEngine:
    def register_handler(self, handler: FaultHandler, *, priority: int = 50) -> None: ...
    def unregister_handler(self, handler_name: str) -> None: ...
    async def handle(self, fault_context: FaultContext) -> Resolved | Transformed | Escalate: ...
    def shutdown(self) -> None: ...
```

### Module-Level Helpers

```python
def get_default_engine() -> FaultEngine:
    """Get the singleton default engine."""

async def process_fault(fault: Fault, **context) -> Any:
    """Convenience: capture + handle a fault."""
```

---

## `FaultHandler` (ABC)

```python
class FaultHandler(ABC):
    """
    A handler that can process specific types of faults.

    Handlers are registered with FaultEngine and called in priority order.
    Each handler decides: Resolve, Transform, or Escalate.
    """

    name: str
    priority: int = 50
    accepts: list[type[Fault]] = []   # fault types this handler processes

    @abstractmethod
    async def handle(self, context: FaultContext) -> FaultResult:
        """Process the fault context. Return Resolved/Transformed/Escalate."""
```

---

## Default Handlers

### `ExceptionAdapter`

Adapts raw Python exceptions into Fault objects.

```python
class ExceptionAdapter(FaultHandler):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

### `RetryHandler`

Retries operations with exponential backoff.

```python
class RetryHandler(FaultHandler):
    def __init__(
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
    ):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

### `SecurityFaultHandler`

Special handling for security-sensitive faults (tamper detection, rate limiting).

```python
class SecurityFaultHandler(FaultHandler):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

### `ResponseMapper`

Maps faults to HTTP responses (the primary integration).

```python
class ResponseMapper(FaultHandler):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

### `FatalHandler`

Last-resort handler for FATAL severity.

```python
class FatalHandler(FaultHandler):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

### `LoggingHandler`

Logs all faults with structured output.

```python
class LoggingHandler(FaultHandler):
    def __init__(self, *, logger: logging.Logger | None = None):
    async def handle(self, context: FaultContext) -> FaultResult: ...
```

---

## Domain Fault Hierarchy

### Config Faults

```python
class ConfigFault(Fault):           # domain=CONFIG, severity=FATAL, retryable=False
class ConfigMissingFault(ConfigFault):
    def __init__(self, key: str, **kwargs): ...
class ConfigInvalidFault(ConfigFault):
    def __init__(self, key: str, reason: str, **kwargs): ...
```

### Registry Faults

```python
class RegistryFault(Fault):         # domain=REGISTRY, severity=FATAL
class DependencyCycleFault(RegistryFault):
    def __init__(self, cycle: list[str], **kwargs): ...
class ManifestInvalidFault(RegistryFault):
    def __init__(self, manifest_name: str, errors: list[str], **kwargs): ...
```

### DI Faults

```python
class DIFault(Fault):               # domain=DI, severity=ERROR
class ProviderNotFoundFault(DIFault):
    def __init__(self, provider_name: str, app: str | None = None, **kwargs): ...
class ScopeViolationFault(DIFault):
    def __init__(self, provider: str, expected_scope: str, actual_scope: str, **kwargs): ...
class DIResolutionFault(DIFault):
    def __init__(self, provider: str, reason: str, **kwargs): ...
```

### Routing Faults

```python
class RoutingFault(Fault):          # domain=ROUTING, severity=ERROR, public=True
class RouteNotFoundFault(RoutingFault):
    def __init__(self, path: str, method: str, **kwargs): ...
class RouteAmbiguousFault(RoutingFault):
    def __init__(self, path: str, matches: list[str], **kwargs): ...
class PatternInvalidFault(RoutingFault):
    def __init__(self, pattern: str, reason: str, **kwargs): ...
```

### Flow Faults

```python
class FlowFault(Fault):             # domain=FLOW, severity=ERROR
class HandlerFault(FlowFault):
    def __init__(self, handler_name: str, reason: str, **kwargs): ...
class MiddlewareFault(FlowFault):
    def __init__(self, middleware_name: str, reason: str, **kwargs): ...
class FlowCancelledFault(FlowFault):
    def __init__(self, reason: str = "timeout", **kwargs): ...
```

### Security Faults

```python
class SecurityFault(Fault):         # domain=SECURITY, severity=ERROR, public=True
class AuthenticationFault(SecurityFault):
    def __init__(self, reason: str = "Invalid credentials", **kwargs): ...
class AuthorizationFault(SecurityFault):
    def __init__(self, resource: str, action: str, **kwargs): ...
class CSRFViolationFault(SecurityFault):
    def __init__(self, reason: str = "CSRF validation failed", **kwargs): ...
class CORSViolationFault(SecurityFault):
    def __init__(self, origin: str, **kwargs): ...
class RateLimitExceededFault(SecurityFault):
    def __init__(self, limit: int, window: float, retry_after: float, **kwargs): ...
class CSPViolationFault(SecurityFault):
    def __init__(self, directive: str, blocked_uri: str = "", **kwargs): ...
```

### Signing Faults

```python
class SigningFault(SecurityFault):        # domain=SECURITY
class BadSignatureFault(SigningFault):
    def __init__(self, message: str = ..., *, original: str | None = None, ...): ...
class SignatureExpiredFault(BadSignatureFault):
    def __init__(self, message: str = ..., *, date_signed=None, age_seconds=None, max_age_seconds=None, ...): ...
class SignatureMalformedFault(SigningFault): ...
class UnsupportedAlgorithmFault(SigningFault):
    def __init__(self, algorithm: str, reason: str = "", **kwargs): ...
```

### Model Faults

```python
class ModelFault(Fault):             # domain=MODEL, severity=ERROR
class ModelNotFoundFault(ModelFault):
    def __init__(self, model_name: str, **kwargs): ...
class ModelRegistrationFault(ModelFault):
    def __init__(self, model_name: str, reason: str, **kwargs): ...
class MigrationFault(ModelFault):
    def __init__(self, migration: str, reason: str, **kwargs): ...
class MigrationConflictFault(ModelFault):
    def __init__(self, conflicting: list[str], **kwargs): ...
class QueryFault(ModelFault):
    def __init__(self, model: str = ..., operation: str = ..., reason: str = ..., **kwargs): ...
class DatabaseConnectionFault(ModelFault):
    def __init__(self, url: str = ..., reason: str = ..., *, backend: str = "", **kwargs): ...
class SchemaFault(ModelFault):
    def __init__(self, table: str, reason: str, **kwargs): ...
class FieldValidationFault(ModelFault):
    def __init__(self, field_name: str, reason: str, **kwargs): ...
class ProtectedDeleteFault(ModelFault):
    def __init__(self, model: str, reason: str, protected_count: int = 0, **kwargs): ...
class RestrictedDeleteFault(ModelFault):
    def __init__(self, model: str, reason: str, restricted_count: int = 0, **kwargs): ...
```

---

## HTTP Faults

Every standard HTTP status code has a corresponding fault. All HTTP faults extend `HTTPFault`.

### `HTTPFault` Base

```python
class HTTPFault(Fault):
    def __init__(
        self,
        status: int,                        # HTTP status code (400-599)
        message: str | None = None,
        *,
        code: str | None = None,
        detail: str = "",                   # human-readable explanation
        severity: Severity = Severity.WARN,
        headers: dict[str, str] | None = None,
        public: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
```

### 4xx Client Errors

| Fault | Status | Special |
|---|---|---|
| `BadRequestFault(detail="")` | 400 | |
| `UnauthorizedFault(detail="", *, scheme="Bearer")` | 401 | Sets `WWW-Authenticate` |
| `PaymentRequiredFault(detail="")` | 402 | |
| `ForbiddenFault(detail="")` | 403 | |
| `NotFoundFault(detail="")` | 404 | |
| `MethodNotAllowedFault(allowed=[], *, detail="")` | 405 | Sets `Allow` header |
| `NotAcceptableFault(detail="")` | 406 | |
| `RequestTimeoutFault(detail="")` | 408 | |
| `ConflictFault(detail="")` | 409 | |
| `GoneFault(detail="")` | 410 | |
| `PayloadTooLargeFault(detail="")` | 413 | |
| `URITooLongFault(detail="")` | 414 | |
| `UnsupportedMediaTypeFault(detail="")` | 415 | |
| `UnprocessableEntityFault(detail="")` | 422 | |
| `LockedFault(detail="")` | 423 | |
| `TooEarlyFault(detail="")` | 425 | |
| `PreconditionRequiredFault(detail="")` | 428 | |
| `TooManyRequestsFault(detail="", *, retry_after=None)` | 429 | Sets `Retry-After` |
| `RequestHeaderFieldsTooLargeFault(detail="")` | 431 | |
| `UnavailableForLegalReasonsFault(detail="")` | 451 | |

### 5xx Server Errors

| Fault | Status | Severity |
|---|---|---|
| `InternalServerErrorFault(detail="")` | 500 | ERROR |
| `NotImplementedFault(detail="")` | 501 | ERROR |
| `BadGatewayFault(detail="")` | 502 | ERROR |
| `ServiceUnavailableFault(detail="", *, retry_after=None)` | 503 | ERROR |
| `GatewayTimeoutFault(detail="")` | 504 | ERROR |

### Helper

```python
def http_reason(status: int) -> str:
    """Return RFC 9110 reason phrase."""
```

---

## How Faults Map to HTTP Responses

```
Handler raises Fault
       │
       ▼
ExceptionMiddleware catches
       │
       ▼
FaultEngine.handle(FaultContext.capture(fault))
       │
       ├─▶ LoggingHandler       (log structured fault)
       ├─▶ SecurityFaultHandler (tamper/rate-limit checks)
       ├─▶ RetryHandler         (retryable? queue retry)
       ├─▶ ResponseMapper       (HTTPFault → JSON/HTML response)
       │        │
       │        ├─ 404 → {"error": "Not Found", "code": "HTTP_404"}
       │        ├─ 422 → {"error": "Unprocessable Content", "detail": {...}}
       │        └─ 500 → {"error": "Internal Server Error"} (public=False → generic)
       │
       └─▶ FatalHandler         (last resort for FATAL severity)
```

### Response Format

```json
{
    "error": "Not Found",
    "code": "HTTP_404",
    "detail": "/api/users/999 does not exist",
    "request_id": "a1b2c3d4e5f6g7h8",
    "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Creating Custom Faults

### Simple — subclass an existing domain base

```python
from aquilia.faults.domains import FlowFault, Severity

class PaymentDeclinedFault(FlowFault):
    code = "PAYMENT_DECLINED"
    message = "Payment was declined by processor"

    def __init__(self, transaction_id: str, reason: str, **kwargs):
        super().__init__(
            code="PAYMENT_DECLINED",
            message=f"Payment {transaction_id} declined: {reason}",
            severity=Severity.ERROR,
            public=True,
            metadata={"transaction_id": transaction_id, "reason": reason},
        )

# Usage
raise PaymentDeclinedFault(transaction_id="txn_123", reason="Insufficient funds")
```

### Advanced — with custom domain

```python
from aquilia.faults import Fault, FaultDomain, Severity

PAYMENT_DOMAIN = FaultDomain.custom("payment", "Payment processing")

class PaymentFault(Fault):
    def __init__(self, code: str, message: str, **kwargs):
        super().__init__(
            code=code,
            message=message,
            domain=PAYMENT_DOMAIN,
            severity=Severity.ERROR,
            retryable=True,
            public=True,
            **kwargs,
        )

class PaymentTimeoutFault(PaymentFault):
    def __init__(self, transaction_id: str):
        super().__init__(
            code="PAYMENT_TIMEOUT",
            message=f"Payment {transaction_id} timed out after 30s",
            metadata={"transaction_id": transaction_id},
        )
```

### Transform Chain

```python
try:
    await db.execute(query)
except Exception as e:
    raise DatabaseFault("query", str(e)) >> ApiFault(status=500, detail="Data query failed")
```