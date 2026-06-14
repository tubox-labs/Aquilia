# Structured Faults

Aquilia uses a structured fault system instead of raw exceptions. Every framework-domain error uses `Fault` subclasses with stable codes, severity levels, domain classification, and recovery semantics.

## Fault Base Class

```python
class Fault(Exception):
    """
    Base fault class - structured, typed fault object.

    A fault is NOT a bare exception. It is a first-class value with:
    - Stable machine-readable code
    - Human-readable message
    - Severity level
    - Domain classification
    - Retry semantics
    - Public exposure control

    Faults may be raised OR returned from handlers (Flow Engine supports both).
    """

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

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `code` | `str` | Stable machine-readable identifier (e.g. `"USER_NOT_FOUND"`) |
| `message` | `str` | Human-readable summary |
| `severity` | `Severity` | Fault severity level |
| `domain` | `FaultDomain` | Fault domain classification |
| `retryable` | `bool` | Whether this fault can be retried |
| `public` | `bool` | Whether safe to expose to clients |
| `metadata` | `dict` | Additional context data |

### Methods

```python
def to_dict(self) -> dict[str, Any]:
    """Serialize fault to dictionary."""

def __rshift__(self, other: type[Fault] | Fault) -> Fault:
    """Fault transform chain operator. Transforms this fault into another."""

def _hash_identifier(self, identifier: str) -> str:
    """Hash sensitive identifiers for logging/metadata."""
```

### Transform Chain (`>>` operator)

```python
raise DatabaseFault(...) >> ApiFault("USER_FETCH_FAILED")
# Results in a new fault with the original as _cause in metadata
```

---

## Severity

```python
class Severity(str, Enum):
    INFO = "info"        # Informational, no action needed
    WARN = "warn"        # Warning, should be reviewed
    ERROR = "error"      # Error, immediate attention
    FATAL = "fatal"      # Fatal, unrecoverable, abort

    # Aliases
    LOW = INFO
    MEDIUM = WARN
    HIGH = ERROR
    CRITICAL = FATAL
```

---

## RecoveryStrategy

```python
class RecoveryStrategy(str, Enum):
    PROPAGATE = "propagate"  # Default: Bubble up to next handler
    RETRY = "retry"          # Retry operation (with backoff)
    FALLBACK = "fallback"    # Return fallback value
    MASK = "mask"            # Suppress error (log only)
    CIRCUIT_BREAK = "break"  # Trip circuit breaker
```

---

## FaultDomain

```python
class FaultDomain:
    """Fault domains (taxonomy). Identifies the functional area where a fault occurred."""

    def __init__(self, name: str, description: str = ""):

    @classmethod
    def custom(cls, name: str, description: str = "") -> FaultDomain:
        """Create a custom module-specific fault domain."""

    def __str__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...
```

### Standard Domains

| Domain | Name | Description | Default Severity | Retryable |
|---|---|---|---|---|
| `CONFIG` | `"config"` | Configuration errors | FATAL | No |
| `REGISTRY` | `"registry"` | Aquilary registry errors | FATAL | No |
| `DI` | `"di"` | Dependency injection errors | ERROR | No |
| `ROUTING` | `"routing"` | Route matching errors | ERROR | No |
| `FLOW` | `"flow"` | Handler execution errors | ERROR | No |
| `EFFECT` | `"effect"` | Side effect failures | ERROR | Yes |
| `IO` | `"io"` | I/O operations | WARN | Yes |
| `SECURITY` | `"security"` | Security and auth | ERROR | No |
| `SYSTEM` | `"system"` | System level faults | FATAL | No |
| `MODEL` | `"model"` | Model ORM and database | ERROR | No |
| `CACHE` | `"cache"` | Cache subsystem | ERROR | Yes |
| `STORAGE` | `"storage"` | File storage | ERROR | No |
| `TASKS` | `"tasks"` | Background task | ERROR | Yes |
| `TEMPLATE` | `"template"` | Template engine | ERROR | No |
| `HTTP` | `"http"` | HTTP protocol errors | WARN | No |
| `PROVIDER` | `"provider"` | Cloud provider integration | ERROR | Yes |
| `DEPLOY` | `"deploy"` | Deployment orchestration | ERROR | No |

Custom domains:
```python
MY_DOMAIN = FaultDomain.custom("my_module", "My module faults")
```

---

## FaultContext

```python
@dataclass(slots=True)
class FaultContext:
    """
    Runtime context wrapper for faults.

    Every fault is wrapped with runtime context when it propagates through
    the system. Context is appended, never overwritten.
    """

    fault: Fault
    trace_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    app: str | None = None
    route: str | None = None
    request_id: str | None = None
    cause: Exception | None = None
    stack: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    parent: FaultContext | None = None
```

### Methods

```python
@classmethod
def capture(cls, fault, *, app=None, route=None, request_id=None,
            cause=None, parent=None) -> FaultContext:
    """Capture fault with runtime context. Generates trace ID, extracts stack."""

def fingerprint(self) -> str:
    """Generate stable fingerprint: hash(code + domain + app + route)."""

def to_dict(self) -> dict[str, Any]:
    """Serialize context to dictionary."""
```

---

## Fault Result Types

```python
@dataclass(frozen=True)
class Resolved:
    """Fault was resolved and should not propagate further."""
    response: Any

@dataclass(frozen=True)
class Transformed:
    """Fault was transformed into another fault."""
    fault: Fault
    preserve_context: bool = True

@dataclass(frozen=True)
class Escalate:
    """Fault should escalate to next handler in chain."""
    pass

FaultResult = Resolved | Transformed | Escalate
```

---

## FaultEngine

The `FaultEngine` (not shown in detail — see `aquilia/faults/engine.py`) provides:
- Handler registration by fault code or domain
- Chained handler execution (first resolver wins)
- Default handlers for 4xx/5xx HTTP status codes
- Integration with `ExceptionMiddleware`

---

## Complete Fault Subclass Catalog

### CONFIG Faults

| Class | Code | Description |
|---|---|---|
| `ConfigFault` | (base) | Base for configuration faults |
| `ConfigMissingFault` | `CONFIG_MISSING` | Required configuration key is missing |
| `ConfigInvalidFault` | `CONFIG_INVALID` | Configuration value is invalid |
| `DotenvParseFault` | `DOTENV_PARSE_ERROR` | `.env` file contains syntax errors |
| `DotenvNotFoundFault` | `DOTENV_NOT_FOUND` | `.env` file not found |

### REGISTRY Faults

| Class | Code | Description |
|---|---|---|
| `RegistryFault` | (base) | Base for Aquilary registry faults |
| `DependencyCycleFault` | `DEPENDENCY_CYCLE` | Circular dependency in app graph |
| `ManifestInvalidFault` | `MANIFEST_INVALID` | Manifest validation failed |

### DI Faults

| Class | Code | Description |
|---|---|---|
| `DIFault` | (base) | Base for DI faults |
| `ProviderNotFoundFault` | `PROVIDER_NOT_FOUND` | DI provider not found |
| `ScopeViolationFault` | `SCOPE_VIOLATION` | DI scope violation |
| `DIResolutionFault` | `DI_RESOLUTION_FAILED` | DI resolution failed |

### ROUTING Faults

| Class | Code | Description |
|---|---|---|
| `RoutingFault` | (base) | Base for routing faults |
| `RouteNotFoundFault` | `ROUTE_NOT_FOUND` | Route not found |
| `RouteAmbiguousFault` | `ROUTE_AMBIGUOUS` | Multiple routes match the pattern |
| `PatternInvalidFault` | `PATTERN_INVALID` | Route pattern is invalid |

### FLOW Faults

| Class | Code | Description |
|---|---|---|
| `FlowFault` | (base) | Base for flow execution faults |
| `HandlerFault` | `HANDLER_FAILED` | Handler execution failed |
| `MiddlewareFault` | `MIDDLEWARE_FAILED` | Middleware execution failed |
| `FlowCancelledFault` | `FLOW_CANCELLED` | Flow cancelled (timeout/disconnect) |

### EFFECT Faults

| Class | Code | Description |
|---|---|---|
| `EffectFault` | (base) | Base for effect (side-effect) faults |
| `DatabaseFault` | `DATABASE_FAULT` | Database operation failed |
| `CacheFault` | `CACHE_FAULT` | Cache operation failed |

### IO Faults

| Class | Code | Description |
|---|---|---|
| `IOFault` | (base) | Base for I/O faults |
| `NetworkFault` | `NETWORK_FAULT` | Network operation failed |
| `FilesystemFault` | `FILESYSTEM_FAULT` | Filesystem operation failed |

### SECURITY Faults

| Class | Code | Description |
|---|---|---|
| `SecurityFault` | (base) | Base for security faults |
| `AuthenticationFault` | `AUTHENTICATION_FAILED` | Authentication failed |
| `AuthorizationFault` | `AUTHORIZATION_FAILED` | Authorization failed |
| `CSRFViolationFault` | `CSRF_VIOLATION` | CSRF token validation failed |
| `CORSViolationFault` | `CORS_VIOLATION` | CORS origin not allowed |
| `RateLimitExceededFault` | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded for client |
| `CSPViolationFault` | `CSP_VIOLATION` | Content Security Policy violation |
| `SigningFault` | `SIGNING_ERROR` | Signing operation failed |
| `BadSignatureFault` | `SIGNING_BAD_SIGNATURE` | Signature verification failed |
| `SignatureExpiredFault` | (inherits) | Signature valid but expired (subclass of `BadSignatureFault`) |
| `SignatureMalformedFault` | `SIGNING_MALFORMED` | Signed value could not be parsed |
| `UnsupportedAlgorithmFault` | `SIGNING_UNSUPPORTED_ALGORITHM` | Algorithm not available |

### SYSTEM Faults

| Class | Code | Description |
|---|---|---|
| `SystemFault` | (base) | Base for fatal system faults |
| `UnrecoverableFault` | `UNRECOVERABLE` | Unrecoverable system fault |
| `ResourceExhaustedFault` | `RESOURCE_EXHAUSTED` | System resources exhausted |

### MODEL Faults

| Class | Code | Description |
|---|---|---|
| `ModelFault` | (base) | Base for model/database faults |
| `ModelNotFoundFault` | `MODEL_NOT_FOUND` | Model not found in registry |
| `ModelRegistrationFault` | `MODEL_REGISTRATION_FAILED` | Model registration failed |
| `MigrationFault` | `MIGRATION_FAILED` | Database migration failed |
| `MigrationConflictFault` | `MIGRATION_CONFLICT` | Migration conflict |
| `QueryFault` | `QUERY_FAILED` | Query execution failed |
| `DatabaseConnectionFault` | `DB_CONNECTION_FAILED` | Database connection failed |
| `SchemaFault` | `SCHEMA_FAULT` | Schema creation/validation failed |
| `FieldValidationFault` | `FIELD_VALIDATION_FAILED` | Field validation failed |
| `ProtectedDeleteFault` | `PROTECTED_DELETE` | Cannot delete protected object |
| `RestrictedDeleteFault` | `RESTRICTED_DELETE` | Cannot delete restricted object |

### HTTP Faults

All HTTP faults extend `HTTPFault` and carry an explicit `status` attribute.

| Class | Status | Code |
|---|---|---|
| `HTTPFault` | 400-599 | `HTTP_{status}` |
| `BadRequestFault` | 400 | `HTTP_400` |
| `UnauthorizedFault` | 401 | `HTTP_401` |
| `PaymentRequiredFault` | 402 | `HTTP_402` |
| `ForbiddenFault` | 403 | `HTTP_403` |
| `NotFoundFault` | 404 | `HTTP_404` |
| `MethodNotAllowedFault` | 405 | `HTTP_405` |
| `NotAcceptableFault` | 406 | `HTTP_406` |
| `RequestTimeoutFault` | 408 | `HTTP_408` |
| `ConflictFault` | 409 | `HTTP_409` |
| `GoneFault` | 410 | `HTTP_410` |
| `PayloadTooLargeFault` | 413 | `HTTP_413` |
| `URITooLongFault` | 414 | `HTTP_414` |
| `UnsupportedMediaTypeFault` | 415 | `HTTP_415` |
| `UnprocessableEntityFault` | 422 | `HTTP_422` |
| `LockedFault` | 423 | `HTTP_423` |
| `TooEarlyFault` | 425 | `HTTP_425` |
| `PreconditionRequiredFault` | 428 | `HTTP_428` |
| `TooManyRequestsFault` | 429 | `HTTP_429` |
| `RequestHeaderFieldsTooLargeFault` | 431 | `HTTP_431` |
| `UnavailableForLegalReasonsFault` | 451 | `HTTP_451` |
| `InternalServerErrorFault` | 500 | `HTTP_500` |
| `NotImplementedFault` | 501 | `HTTP_501` |
| `BadGatewayFault` | 502 | `HTTP_502` |
| `ServiceUnavailableFault` | 503 | `HTTP_503` |
| `GatewayTimeoutFault` | 504 | `HTTP_504` |

`UnauthorizedFault` automatically sets `WWW-Authenticate` header (default `Bearer`).
`MethodNotAllowedFault` requires an `allowed` list and sets the `Allow` header.
`TooManyRequestsFault` and `ServiceUnavailableFault` support `retry_after` for `Retry-After` header.

### PROVIDER Faults

| Class | Code | Description |
|---|---|---|
| `ProviderFault` | (base) | Base for cloud provider faults |
| `ProviderAPIFault` | `PROVIDER_API_ERROR` | Provider API error |
| `ProviderAuthFault` | `PROVIDER_AUTH_FAILED` | Provider auth failure |
| `ProviderRateLimitFault` | `PROVIDER_RATE_LIMITED` | Provider rate limit |
| `ProviderTokenFault` | `PROVIDER_TOKEN_INVALID` | API token missing/invalid |
| `ProviderCredentialFault` | `PROVIDER_CREDENTIAL_ERROR` | Credential storage error |
| `ProviderConnectionFault` | `PROVIDER_CONNECTION_FAILED` | Network connection failed |

### DEPLOY Faults

| Class | Code | Description |
|---|---|---|
| `DeployFault` | (base) | Base for deployment faults |
| `DeployConfigFault` | `DEPLOY_CONFIG_INVALID` | Deploy config invalid |
| `DeployImageFault` | `DEPLOY_IMAGE_FAILED` | Docker image build/push failure |
| `DeployHealthFault` | `DEPLOY_UNHEALTHY` | Deployed service unhealthy |
| `DeployAppFault` | `DEPLOY_APP_FAILED` | Failed to create/resolve app |
| `DeployServiceFault` | `DEPLOY_SERVICE_FAILED` | Failed to create/update service |

---

## ExceptionMiddleware — Fault-to-HTTP Mapping

The `ExceptionMiddleware` converts faults to HTTP responses with domain-based status code mapping:

| Fault Domain | HTTP Status |
|---|---|
| `ROUTING` | 404 |
| `SECURITY` (default) | 403 |
| `IO` | 502 |
| `EFFECT` | 503 |
| `MODEL` | 404 |
| `CACHE` | 502 |
| `CONFIG` | 500 |
| `REGISTRY` | 500 |
| `DI` | 500 |
| `FLOW` | 500 |
| `SYSTEM` | 500 |
| `STORAGE` | 502 |
| `TASKS` | 503 |
| `TEMPLATE` | 500 |

Special fault codes override this mapping:
- `AUTH_010`, `AUTHENTICATION_REQUIRED`, `SESSION_REQUIRED`, `INVALID_CREDENTIALS` → **401**
- `USER_ALREADY_EXISTS` → **409**
- Faults with `NOT_FOUND`/`MISSING` in code → **404**
- Faults with `VALIDATION`/`INVALID` in code → **400**

HTML browser clients receive styled error pages; API clients receive structured JSON:

```json
{
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User with ID 123 not found",
        "domain": "flow"
    }
}
```