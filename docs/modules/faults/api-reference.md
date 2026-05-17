# Faults API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `Severity` | `aquilia/faults/core.py` | str, Enum | Fault severity levels. |
| `FaultDomain` | `aquilia/faults/core.py` | object | Fault domains (taxonomy). |
| `RecoveryStrategy` | `aquilia/faults/core.py` | str, Enum | Fault recovery strategies. |
| `Fault` | `aquilia/faults/core.py` | Exception | Base fault class - structured, typed fault object. |
| `FaultContext` | `aquilia/faults/core.py` | object | Runtime context wrapper for faults. |
| `Resolved` | `aquilia/faults/core.py` | object | Fault was resolved and should not propagate further. |
| `Transformed` | `aquilia/faults/core.py` | object | Fault was transformed into another fault. |
| `Escalate` | `aquilia/faults/core.py` | object | Fault should escalate to next handler in chain. |
| `ExceptionMapping` | `aquilia/faults/default_handlers.py` | object | Maps exception type to Fault factory. |
| `ExceptionAdapter` | `aquilia/faults/default_handlers.py` | FaultHandler | Convert raw Python exceptions to structured Faults. |
| `RetryHandler` | `aquilia/faults/default_handlers.py` | FaultHandler | Retry transient failures with exponential backoff. |
| `SecurityFaultHandler` | `aquilia/faults/default_handlers.py` | FaultHandler | Mask sensitive information in security faults. |
| `HTTPResponse` | `aquilia/faults/default_handlers.py` | object | HTTP response representation. |
| `ResponseMapper` | `aquilia/faults/default_handlers.py` | FaultHandler | Map faults to HTTP/WebSocket/RPC responses. |
| `FatalHandler` | `aquilia/faults/default_handlers.py` | FaultHandler | Terminate server on FATAL severity faults. |
| `LoggingHandler` | `aquilia/faults/default_handlers.py` | FaultHandler | Log all faults with structured metadata. |
| `ConfigFault` | `aquilia/faults/domains.py` | Fault | Base class for configuration faults. |
| `ConfigMissingFault` | `aquilia/faults/domains.py` | ConfigFault | Required configuration is missing. |
| `ConfigInvalidFault` | `aquilia/faults/domains.py` | ConfigFault | Configuration value is invalid. |
| `DotenvParseFault` | `aquilia/faults/domains.py` | ConfigFault | Dotenv file contains syntax errors. |
| `DotenvNotFoundFault` | `aquilia/faults/domains.py` | ConfigFault | Dotenv file not found when explicitly requested. |
| `RegistryFault` | `aquilia/faults/domains.py` | Fault | Base class for Aquilary registry faults. |
| `DependencyCycleFault` | `aquilia/faults/domains.py` | RegistryFault | Circular dependency detected in app graph. |
| `ManifestInvalidFault` | `aquilia/faults/domains.py` | RegistryFault | Manifest validation failed. |
| `DIFault` | `aquilia/faults/domains.py` | Fault | Base class for dependency injection faults. |
| `ProviderNotFoundFault` | `aquilia/faults/domains.py` | DIFault | DI provider not found. |
| `ScopeViolationFault` | `aquilia/faults/domains.py` | DIFault | DI scope violation. |
| `DIResolutionFault` | `aquilia/faults/domains.py` | DIFault | DI resolution failed. |
| `RoutingFault` | `aquilia/faults/domains.py` | Fault | Base class for routing faults. |
| `RouteNotFoundFault` | `aquilia/faults/domains.py` | RoutingFault | Route not found. |
| `RouteAmbiguousFault` | `aquilia/faults/domains.py` | RoutingFault | Multiple routes match the pattern. |
| `PatternInvalidFault` | `aquilia/faults/domains.py` | RoutingFault | Route pattern is invalid. |
| `FlowFault` | `aquilia/faults/domains.py` | Fault | Base class for flow execution faults. |
| `HandlerFault` | `aquilia/faults/domains.py` | FlowFault | Handler execution failed. |
| `MiddlewareFault` | `aquilia/faults/domains.py` | FlowFault | Middleware execution failed. |
| `FlowCancelledFault` | `aquilia/faults/domains.py` | FlowFault | Flow was cancelled (timeout or client disconnect). |
| `EffectFault` | `aquilia/faults/domains.py` | Fault | Base class for effect (side-effect) faults. |
| `DatabaseFault` | `aquilia/faults/domains.py` | EffectFault | Database operation failed. |
| `CacheFault` | `aquilia/faults/domains.py` | EffectFault | Cache operation failed. |
| `IOFault` | `aquilia/faults/domains.py` | Fault | Base class for I/O faults. |
| `NetworkFault` | `aquilia/faults/domains.py` | IOFault | Network operation failed. |
| `FilesystemFault` | `aquilia/faults/domains.py` | IOFault | Filesystem operation failed. |
| `SecurityFault` | `aquilia/faults/domains.py` | Fault | Base class for security faults. |
| `AuthenticationFault` | `aquilia/faults/domains.py` | SecurityFault | Authentication failed. |
| `AuthorizationFault` | `aquilia/faults/domains.py` | SecurityFault | Authorization failed. |
| `CSRFViolationFault` | `aquilia/faults/domains.py` | SecurityFault | CSRF token validation failed. |
| `CORSViolationFault` | `aquilia/faults/domains.py` | SecurityFault | CORS origin not allowed. |
| `RateLimitExceededFault` | `aquilia/faults/domains.py` | SecurityFault | Rate limit exceeded for client. |
| `CSPViolationFault` | `aquilia/faults/domains.py` | SecurityFault | Content Security Policy violation reported. |
| `SigningFault` | `aquilia/faults/domains.py` | SecurityFault | Base class for all signing/verification faults. |
| `BadSignatureFault` | `aquilia/faults/domains.py` | SigningFault | Signature verification failed - potential tampering. |
| `SignatureExpiredFault` | `aquilia/faults/domains.py` | BadSignatureFault | The signature is valid but the embedded timestamp has exceeded max_age. |
| `SignatureMalformedFault` | `aquilia/faults/domains.py` | SigningFault | The signed value could not be parsed at all (wrong number of parts, |
| `UnsupportedAlgorithmFault` | `aquilia/faults/domains.py` | SigningFault | The requested algorithm is not available (e.g. asymmetric algorithm |
| `SystemFault` | `aquilia/faults/domains.py` | Fault | Base class for fatal system faults. |
| `UnrecoverableFault` | `aquilia/faults/domains.py` | SystemFault | Unrecoverable system fault. |
| `ResourceExhaustedFault` | `aquilia/faults/domains.py` | SystemFault | System resources exhausted. |
| `ModelFault` | `aquilia/faults/domains.py` | Fault | Base class for model and database faults. |
| `AMDLParseFault` | `aquilia/faults/domains.py` | ModelFault | AMDL file parsing failed. |
| `ModelNotFoundFault` | `aquilia/faults/domains.py` | ModelFault | Model not found in registry. |
| `ModelRegistrationFault` | `aquilia/faults/domains.py` | ModelFault | Model registration failed. |
| `MigrationFault` | `aquilia/faults/domains.py` | ModelFault | Database migration failed. |
| `MigrationConflictFault` | `aquilia/faults/domains.py` | ModelFault | Migration conflict detected (e.g. divergent migration branches). |
| `QueryFault` | `aquilia/faults/domains.py` | ModelFault | Query execution failed. |
| `DatabaseConnectionFault` | `aquilia/faults/domains.py` | ModelFault | Database connection failed. |
| `SchemaFault` | `aquilia/faults/domains.py` | ModelFault | Schema creation or validation failed. |
| `FieldValidationFault` | `aquilia/faults/domains.py` | ModelFault | Field validation failed. |
| `ProtectedDeleteFault` | `aquilia/faults/domains.py` | ModelFault | Cannot delete a protected object due to PROTECT on_delete. |
| `RestrictedDeleteFault` | `aquilia/faults/domains.py` | ModelFault | Cannot delete a restricted object due to RESTRICT on_delete. |
| `HTTPFault` | `aquilia/faults/domains.py` | Fault | Base class for HTTP protocol error faults. |
| `BadRequestFault` | `aquilia/faults/domains.py` | HTTPFault | 400 Bad Request. |
| `UnauthorizedFault` | `aquilia/faults/domains.py` | HTTPFault | 401 Unauthorized. |
| `PaymentRequiredFault` | `aquilia/faults/domains.py` | HTTPFault | 402 Payment Required. |
| `ForbiddenFault` | `aquilia/faults/domains.py` | HTTPFault | 403 Forbidden. |
| `NotFoundFault` | `aquilia/faults/domains.py` | HTTPFault | 404 Not Found. |
| `MethodNotAllowedFault` | `aquilia/faults/domains.py` | HTTPFault | 405 Method Not Allowed. |
| `NotAcceptableFault` | `aquilia/faults/domains.py` | HTTPFault | 406 Not Acceptable. |
| `RequestTimeoutFault` | `aquilia/faults/domains.py` | HTTPFault | 408 Request Timeout. |
| `ConflictFault` | `aquilia/faults/domains.py` | HTTPFault | 409 Conflict. |
| `GoneFault` | `aquilia/faults/domains.py` | HTTPFault | 410 Gone. |
| `PayloadTooLargeFault` | `aquilia/faults/domains.py` | HTTPFault | 413 Content Too Large. |
| `URITooLongFault` | `aquilia/faults/domains.py` | HTTPFault | 414 URI Too Long. |
| `UnsupportedMediaTypeFault` | `aquilia/faults/domains.py` | HTTPFault | 415 Unsupported Media Type. |
| `UnprocessableEntityFault` | `aquilia/faults/domains.py` | HTTPFault | 422 Unprocessable Content. |
| `LockedFault` | `aquilia/faults/domains.py` | HTTPFault | 423 Locked. |
| `TooEarlyFault` | `aquilia/faults/domains.py` | HTTPFault | 425 Too Early. |
| `PreconditionRequiredFault` | `aquilia/faults/domains.py` | HTTPFault | 428 Precondition Required. |
| `TooManyRequestsFault` | `aquilia/faults/domains.py` | HTTPFault | 429 Too Many Requests. |
| `RequestHeaderFieldsTooLargeFault` | `aquilia/faults/domains.py` | HTTPFault | 431 Request Header Fields Too Large. |
| `UnavailableForLegalReasonsFault` | `aquilia/faults/domains.py` | HTTPFault | 451 Unavailable For Legal Reasons. |
| `InternalServerErrorFault` | `aquilia/faults/domains.py` | HTTPFault | 500 Internal Server Error. |
| `NotImplementedFault` | `aquilia/faults/domains.py` | HTTPFault | 501 Not Implemented. |
| `BadGatewayFault` | `aquilia/faults/domains.py` | HTTPFault | 502 Bad Gateway. |
| `ServiceUnavailableFault` | `aquilia/faults/domains.py` | HTTPFault | 503 Service Unavailable. |
| `GatewayTimeoutFault` | `aquilia/faults/domains.py` | HTTPFault | 504 Gateway Timeout. |
| `ProviderFault` | `aquilia/faults/domains.py` | Fault | Base class for cloud provider integration faults. |
| `ProviderAPIFault` | `aquilia/faults/domains.py` | ProviderFault | Cloud provider API returned an error response. |
| `ProviderAuthFault` | `aquilia/faults/domains.py` | ProviderFault | Cloud provider authentication failure (401/403). |
| `ProviderRateLimitFault` | `aquilia/faults/domains.py` | ProviderFault | Cloud provider rate limit exceeded (429). |
| `ProviderTokenFault` | `aquilia/faults/domains.py` | ProviderFault | Provider API token is missing, invalid, or expired. |
| `ProviderCredentialFault` | `aquilia/faults/domains.py` | ProviderFault | Credential storage or retrieval failure. |
| `ProviderConnectionFault` | `aquilia/faults/domains.py` | ProviderFault | Network connection to provider API failed. |
| `DeployFault` | `aquilia/faults/domains.py` | Fault | Base class for deployment orchestration faults. |
| `DeployConfigFault` | `aquilia/faults/domains.py` | DeployFault | Deployment configuration is invalid or incomplete. |
| `DeployImageFault` | `aquilia/faults/domains.py` | DeployFault | Docker image build or push failure. |
| `DeployHealthFault` | `aquilia/faults/domains.py` | DeployFault | Deployed service did not become healthy. |
| `DeployAppFault` | `aquilia/faults/domains.py` | DeployFault | Failed to create or resolve the provider app. |
| `DeployServiceFault` | `aquilia/faults/domains.py` | DeployFault | Failed to create or update the provider service. |
| `FaultEngine` | `aquilia/faults/engine.py` | object | Runtime fault processor. |
| `FaultMiddleware` | `aquilia/faults/engine.py` | object | Middleware that bridges the FaultEngine with the request/response lifecycle. |
| `FaultHandler` | `aquilia/faults/handlers.py` | ABC | Abstract base class for fault handlers. |
| `CompositeHandler` | `aquilia/faults/handlers.py` | FaultHandler | Composite handler that chains multiple handlers. |
| `ScopedHandlerRegistry` | `aquilia/faults/handlers.py` | object | Registry of fault handlers at different scopes. |
| `CircularDependencyFault` | `aquilia/faults/integrations/di.py` | DIFault | Circular dependency detected. |
| `ProviderRegistrationFault` | `aquilia/faults/integrations/di.py` | DIFault | Provider registration failed. |
| `AsyncResolutionFault` | `aquilia/faults/integrations/di.py` | DIFault | Async resolution in sync context. |
| `PipelineAbortedFault` | `aquilia/faults/integrations/flow.py` | FlowFault | Request pipeline aborted by middleware. |
| `HandlerTimeoutFault` | `aquilia/faults/integrations/flow.py` | FlowFault | Handler execution timed out. |
| `MiddlewareChainFault` | `aquilia/faults/integrations/flow.py` | FlowFault | Middleware chain execution failed. |
| `ModelFaultHandler` | `aquilia/faults/integrations/models.py` | FaultHandler | Fault handler for MODEL domain faults. |
| `ManifestLoadFault` | `aquilia/faults/integrations/registry.py` | RegistryFault | Manifest loading failed. |
| `AppContextInvalidFault` | `aquilia/faults/integrations/registry.py` | RegistryFault | App context validation failed. |
| `RouteCompilationFault` | `aquilia/faults/integrations/registry.py` | RegistryFault | Route compilation failed. |
| `DependencyResolutionFault` | `aquilia/faults/integrations/registry.py` | RegistryFault | Dependency resolution failed. |
| `RouteConflictFault` | `aquilia/faults/integrations/routing.py` | RoutingFault | Multiple routes match the same pattern. |
| `MethodNotAllowedFault` | `aquilia/faults/integrations/routing.py` | RoutingFault | HTTP method not allowed for route. |
| `RouteParameterFault` | `aquilia/faults/integrations/routing.py` | RoutingFault | Route parameter validation failed. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `http_reason` | `aquilia/faults/domains.py` | `def http_reason(status: int) -> str` | Return the canonical RFC 9110 reason phrase for *status*. |
| `get_default_engine` | `aquilia/faults/engine.py` | `def get_default_engine() -> FaultEngine` | Get or create default global fault engine. |
| `process_fault` | `aquilia/faults/engine.py` | `async def process_fault(exception: Exception &#124; Fault, *, engine: FaultEngine &#124; None = None) -> FaultResult` | Process fault using engine. |
| `patch_all_subsystems` | `aquilia/faults/integrations/__init__.py` | `def patch_all_subsystems()` | Patch all Aquilia subsystems to use AquilaFaults. |
| `create_all_integration_handlers` | `aquilia/faults/integrations/__init__.py` | `def create_all_integration_handlers()` | Create fault handlers for all subsystem integrations. |
| `patch_di_container` | `aquilia/faults/integrations/di.py` | `def patch_di_container()` | Patch DI Container to emit structured faults. |
| `create_di_fault_handler` | `aquilia/faults/integrations/di.py` | `def create_di_fault_handler()` | Create fault handler for DI operations. |
| `fault_handling_middleware` | `aquilia/faults/integrations/flow.py` | `async def fault_handling_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], engine: FaultEngine &#124; None = None)` | Core fault handling middleware. |
| `timeout_middleware` | `aquilia/faults/integrations/flow.py` | `async def timeout_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], timeout_seconds: float = 30.0)` | Timeout middleware with fault emission. |
| `fault_aware_handler` | `aquilia/faults/integrations/flow.py` | `def fault_aware_handler(handler: Callable)` | Decorator to make handler fault-aware. |
| `create_flow_fault_handler` | `aquilia/faults/integrations/flow.py` | `def create_flow_fault_handler()` | Create fault handler for flow operations. |
| `with_cancellation_handling` | `aquilia/faults/integrations/flow.py` | `async def with_cancellation_handling(coro: Awaitable[Any]) -> Any` | Wrap coroutine with cancellation fault handling. |
| `is_fault_retryable` | `aquilia/faults/integrations/flow.py` | `def is_fault_retryable(fault: Fault) -> bool` | Check if fault is retryable. |
| `should_abort_pipeline` | `aquilia/faults/integrations/flow.py` | `def should_abort_pipeline(fault: Fault) -> bool` | Check if fault should abort the pipeline. |
| `create_model_fault_handler` | `aquilia/faults/integrations/models.py` | `def create_model_fault_handler(max_retries: int = 3, log_queries: bool = True) -> ModelFaultHandler` | Create a fault handler for the MODEL domain. |
| `patch_model_registry` | `aquilia/faults/integrations/models.py` | `def patch_model_registry() -> None` | Patch model registries to raise structured faults instead of bare exceptions. |
| `patch_database_engine` | `aquilia/faults/integrations/models.py` | `def patch_database_engine() -> None` | Patch AquiliaDatabase to raise structured faults on connection errors. |
| `patch_all_model_subsystems` | `aquilia/faults/integrations/models.py` | `def patch_all_model_subsystems() -> None` | Patch all model-related subsystems with fault integration. |
| `patch_runtime_registry` | `aquilia/faults/integrations/registry.py` | `def patch_runtime_registry()` | Patch RuntimeRegistry to emit structured faults. |
| `create_registry_fault_handler` | `aquilia/faults/integrations/registry.py` | `def create_registry_fault_handler()` | Create fault handler for registry operations. |
| `create_routing_fault_handler` | `aquilia/faults/integrations/routing.py` | `def create_routing_fault_handler()` | Create fault handler for routing operations. |
| `safe_route_lookup` | `aquilia/faults/integrations/routing.py` | `def safe_route_lookup(router, path: str, method: str = 'GET')` | Safely lookup route, returning fault instead of throwing. |
| `validate_route_pattern` | `aquilia/faults/integrations/routing.py` | `def validate_route_pattern(pattern: str) -> PatternInvalidFault &#124; None` | Validate route pattern syntax. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `DOMAIN_DEFAULTS` | `aquilia/faults/core.py` | `{FaultDomain.CONFIG: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.REGISTRY: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.DI: {` |
| `_HTTP_REASONS` | `aquilia/faults/domains.py` | `dict[int, str]` |

## Detailed Classes And Methods

### Class: `Severity`

- Source: `aquilia/faults/core.py`
- Bases: `str, Enum`
- Summary: Fault severity levels.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `INFO` |  | `'info'` |
| `WARN` |  | `'warn'` |
| `ERROR` |  | `'error'` |
| `FATAL` |  | `'fatal'` |
| `LOW` |  | `INFO` |
| `MEDIUM` |  | `WARN` |
| `HIGH` |  | `ERROR` |
| `CRITICAL` |  | `FATAL` |

### Class: `FaultDomain`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Fault domains (taxonomy).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `custom` | `def custom(cls, name: str, description: str = '') -> FaultDomain` | classmethod | Create a custom module-specific fault domain. |

### Class: `RecoveryStrategy`

- Source: `aquilia/faults/core.py`
- Bases: `str, Enum`
- Summary: Fault recovery strategies.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PROPAGATE` |  | `'propagate'` |
| `RETRY` |  | `'retry'` |
| `FALLBACK` |  | `'fallback'` |
| `MASK` |  | `'mask'` |
| `CIRCUIT_BREAK` |  | `'break'` |

### Class: `Fault`

- Source: `aquilia/faults/core.py`
- Bases: `Exception`
- Summary: Base fault class - structured, typed fault object.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize fault to dictionary. |

### Class: `FaultContext`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Runtime context wrapper for faults.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fault` | `Fault` |  |
| `trace_id` | `str` |  |
| `timestamp` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `app` | `str &#124; None` | `None` |
| `route` | `str &#124; None` | `None` |
| `request_id` | `str &#124; None` | `None` |
| `cause` | `Exception &#124; None` | `None` |
| `stack` | `list[Any]` | `field(default_factory=list)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `parent` | `FaultContext &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `capture` | `def capture(cls, fault: Fault, *, app: str &#124; None = None, route: str &#124; None = None, request_id: str &#124; None = None, cause: Exception &#124; None = None, parent: FaultContext &#124; None = None) -> FaultContext` | classmethod | Capture fault with runtime context. |
| `fingerprint` | `def fingerprint(self) -> str` |  | Generate stable fingerprint for this fault occurrence. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize context to dictionary. |

### Class: `Resolved`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault was resolved and should not propagate further.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `response` | `Any` |  |

### Class: `Transformed`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault was transformed into another fault.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fault` | `Fault` |  |
| `preserve_context` | `bool` | `True` |

### Class: `Escalate`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault should escalate to next handler in chain.

### Class: `ExceptionMapping`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Maps exception type to Fault factory.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `exception_type` | `type[Exception]` |  |
| `fault_factory` | `Callable[[Exception], Any]` |  |
| `retryable` | `bool` | `False` |

### Class: `ExceptionAdapter`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Convert raw Python exceptions to structured Faults.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Only handle if cause is unmapped exception. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Convert exception to appropriate Fault. |

### Class: `RetryHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Retry transient failures with exponential backoff.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Only handle retryable faults. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Retry fault with exponential backoff. |

### Class: `SecurityFaultHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Mask sensitive information in security faults.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Only handle security faults. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Mask sensitive information. |

### Class: `HTTPResponse`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP response representation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `status_code` | `int` |  |
| `body` | `dict[str, Any]` |  |
| `headers` | `dict[str, str]` |  |

### Class: `ResponseMapper`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Map faults to HTTP/WebSocket/RPC responses.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Handle all faults. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Map fault to HTTP response. |

### Class: `FatalHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Terminate server on FATAL severity faults.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Only handle FATAL severity. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Log and invoke callback. |

### Class: `LoggingHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Log all faults with structured metadata.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Handle all faults. |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Log fault and escalate. |

### Class: `ConfigFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for configuration faults.

### Class: `ConfigMissingFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Required configuration is missing.

### Class: `ConfigInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Configuration value is invalid.

### Class: `DotenvParseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Dotenv file contains syntax errors.

### Class: `DotenvNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Dotenv file not found when explicitly requested.

### Class: `RegistryFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for Aquilary registry faults.

### Class: `DependencyCycleFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RegistryFault`
- Summary: Circular dependency detected in app graph.

### Class: `ManifestInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RegistryFault`
- Summary: Manifest validation failed.

### Class: `DIFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for dependency injection faults.

### Class: `ProviderNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI provider not found.

### Class: `ScopeViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI scope violation.

### Class: `DIResolutionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI resolution failed.

### Class: `RoutingFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for routing faults.

### Class: `RouteNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Route not found.

### Class: `RouteAmbiguousFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Multiple routes match the pattern.

### Class: `PatternInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Route pattern is invalid.

### Class: `FlowFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for flow execution faults.

### Class: `HandlerFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Handler execution failed.

### Class: `MiddlewareFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Middleware execution failed.

### Class: `FlowCancelledFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Flow was cancelled (timeout or client disconnect).

### Class: `EffectFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for effect (side-effect) faults.

### Class: `DatabaseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `EffectFault`
- Summary: Database operation failed.

### Class: `CacheFault`

- Source: `aquilia/faults/domains.py`
- Bases: `EffectFault`
- Summary: Cache operation failed.

### Class: `IOFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for I/O faults.

### Class: `NetworkFault`

- Source: `aquilia/faults/domains.py`
- Bases: `IOFault`
- Summary: Network operation failed.

### Class: `FilesystemFault`

- Source: `aquilia/faults/domains.py`
- Bases: `IOFault`
- Summary: Filesystem operation failed.

### Class: `SecurityFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for security faults.

### Class: `AuthenticationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Authentication failed.

### Class: `AuthorizationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Authorization failed.

### Class: `CSRFViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: CSRF token validation failed.

### Class: `CORSViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: CORS origin not allowed.

### Class: `RateLimitExceededFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Rate limit exceeded for client.

### Class: `CSPViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Content Security Policy violation reported.

### Class: `SigningFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Base class for all signing/verification faults.

### Class: `BadSignatureFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: Signature verification failed - potential tampering.

### Class: `SignatureExpiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `BadSignatureFault`
- Summary: The signature is valid but the embedded timestamp has exceeded max_age.

### Class: `SignatureMalformedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: The signed value could not be parsed at all (wrong number of parts,

### Class: `UnsupportedAlgorithmFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: The requested algorithm is not available (e.g. asymmetric algorithm

### Class: `SystemFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for fatal system faults.

### Class: `UnrecoverableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SystemFault`
- Summary: Unrecoverable system fault.

### Class: `ResourceExhaustedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SystemFault`
- Summary: System resources exhausted.

### Class: `ModelFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for model and database faults.

### Class: `AMDLParseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: AMDL file parsing failed.

### Class: `ModelNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Model not found in registry.

### Class: `ModelRegistrationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Model registration failed.

### Class: `MigrationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Database migration failed.

### Class: `MigrationConflictFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Migration conflict detected (e.g. divergent migration branches).

### Class: `QueryFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Query execution failed.

### Class: `DatabaseConnectionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Database connection failed.

### Class: `SchemaFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Schema creation or validation failed.

### Class: `FieldValidationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Field validation failed.

### Class: `ProtectedDeleteFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Cannot delete a protected object due to PROTECT on_delete.

### Class: `RestrictedDeleteFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Cannot delete a restricted object due to RESTRICT on_delete.

### Class: `HTTPFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for HTTP protocol error faults.

### Class: `BadRequestFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 400 Bad Request.

### Class: `UnauthorizedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 401 Unauthorized.

### Class: `PaymentRequiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 402 Payment Required.

### Class: `ForbiddenFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 403 Forbidden.

### Class: `NotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 404 Not Found.

### Class: `MethodNotAllowedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 405 Method Not Allowed.

### Class: `NotAcceptableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 406 Not Acceptable.

### Class: `RequestTimeoutFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 408 Request Timeout.

### Class: `ConflictFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 409 Conflict.

### Class: `GoneFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 410 Gone.

### Class: `PayloadTooLargeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 413 Content Too Large.

### Class: `URITooLongFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 414 URI Too Long.

### Class: `UnsupportedMediaTypeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 415 Unsupported Media Type.

### Class: `UnprocessableEntityFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 422 Unprocessable Content.

### Class: `LockedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 423 Locked.

### Class: `TooEarlyFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 425 Too Early.

### Class: `PreconditionRequiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 428 Precondition Required.

### Class: `TooManyRequestsFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 429 Too Many Requests.

### Class: `RequestHeaderFieldsTooLargeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 431 Request Header Fields Too Large.

### Class: `UnavailableForLegalReasonsFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 451 Unavailable For Legal Reasons.

### Class: `InternalServerErrorFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 500 Internal Server Error.

### Class: `NotImplementedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 501 Not Implemented.

### Class: `BadGatewayFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 502 Bad Gateway.

### Class: `ServiceUnavailableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 503 Service Unavailable.

### Class: `GatewayTimeoutFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 504 Gateway Timeout.

### Class: `ProviderFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for cloud provider integration faults.

### Class: `ProviderAPIFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider API returned an error response.

### Class: `ProviderAuthFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider authentication failure (401/403).

### Class: `ProviderRateLimitFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider rate limit exceeded (429).

### Class: `ProviderTokenFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Provider API token is missing, invalid, or expired.

### Class: `ProviderCredentialFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Credential storage or retrieval failure.

### Class: `ProviderConnectionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Network connection to provider API failed.

### Class: `DeployFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for deployment orchestration faults.

### Class: `DeployConfigFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Deployment configuration is invalid or incomplete.

### Class: `DeployImageFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Docker image build or push failure.

### Class: `DeployHealthFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Deployed service did not become healthy.

### Class: `DeployAppFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Failed to create or resolve the provider app.

### Class: `DeployServiceFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Failed to create or update the provider service.

### Class: `FaultEngine`

- Source: `aquilia/faults/engine.py`
- Bases: `object`
- Summary: Runtime fault processor.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_global` | `def register_global(self, handler: FaultHandler)` |  | Register global fault handler. |
| `register_app` | `def register_app(self, app: str, handler: FaultHandler)` |  | Register app-scoped fault handler. |
| `register_controller` | `def register_controller(self, controller: str, handler: FaultHandler)` |  | Register controller-scoped fault handler. |
| `register_route` | `def register_route(self, route: str, handler: FaultHandler)` |  | Register route-scoped fault handler. |
| `on_fault` | `def on_fault(self, listener: Callable[[FaultContext], None])` |  | Register fault event listener. |
| `process` | `async def process(self, exception: Exception &#124; Fault, *, app: str &#124; None = None, route: str &#124; None = None, request_id: str &#124; None = None) -> FaultResult` |  | Process exception or fault. |
| `process_async_exception` | `async def process_async_exception(self, exception: Exception) -> FaultResult` |  | Process async exception with automatic context capture. |
| `set_context` | `def set_context(*, app: str &#124; None = None, route: str &#124; None = None, request_id: str &#124; None = None)` | staticmethod | Set fault context for current async task. |
| `clear_context` | `def clear_context()` | staticmethod | Clear fault context for current async task. |
| `get_history` | `def get_history(self) -> list[FaultContext]` |  | Get fault history (debug mode only). |
| `clear_history` | `def clear_history(self)` |  | Clear fault history. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Get fault engine statistics. |

### Class: `FaultMiddleware`

- Source: `aquilia/faults/engine.py`
- Bases: `object`
- Summary: Middleware that bridges the FaultEngine with the request/response lifecycle.

### Class: `FaultHandler`

- Source: `aquilia/faults/handlers.py`
- Bases: `ABC`
- Summary: Abstract base class for fault handlers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` | abstractmethod | Handle fault context. |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Check if this handler can handle the fault. |

### Class: `CompositeHandler`

- Source: `aquilia/faults/handlers.py`
- Bases: `FaultHandler`
- Summary: Composite handler that chains multiple handlers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `handle` | `async def handle(self, ctx: FaultContext) -> FaultResult` |  | Try each handler in order. |

### Class: `ScopedHandlerRegistry`

- Source: `aquilia/faults/handlers.py`
- Bases: `object`
- Summary: Registry of fault handlers at different scopes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_global` | `def register_global(self, handler: FaultHandler)` |  | Register global handler. |
| `register_app` | `def register_app(self, app: str, handler: FaultHandler)` |  | Register app-scoped handler. |
| `register_controller` | `def register_controller(self, controller: str, handler: FaultHandler)` |  | Register controller-scoped handler. |
| `register_route` | `def register_route(self, route: str, handler: FaultHandler)` |  | Register route-scoped handler. |
| `get_handlers` | `def get_handlers(self, *, app: str &#124; None = None, controller: str &#124; None = None, route: str &#124; None = None) -> list[FaultHandler]` |  | Get applicable handlers for context. |

### Class: `CircularDependencyFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Circular dependency detected.

### Class: `ProviderRegistrationFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Provider registration failed.

### Class: `AsyncResolutionFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Async resolution in sync context.

### Class: `PipelineAbortedFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Request pipeline aborted by middleware.

### Class: `HandlerTimeoutFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Handler execution timed out.

### Class: `MiddlewareChainFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Middleware chain execution failed.

### Class: `ModelFaultHandler`

- Source: `aquilia/faults/integrations/models.py`
- Bases: `FaultHandler`
- Summary: Fault handler for MODEL domain faults.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext) -> bool` |  | Check if this handler can handle the fault. |
| `handle` | `def handle(self, ctx: FaultContext) -> FaultResult` |  | Handle a model domain fault. |

### Class: `ManifestLoadFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Manifest loading failed.

### Class: `AppContextInvalidFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: App context validation failed.

### Class: `RouteCompilationFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Route compilation failed.

### Class: `DependencyResolutionFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Dependency resolution failed.

### Class: `RouteConflictFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: Multiple routes match the same pattern.

### Class: `MethodNotAllowedFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: HTTP method not allowed for route.

### Class: `RouteParameterFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: Route parameter validation failed.

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `http_reason` | `aquilia/faults/domains.py` | `def http_reason(status: int) -> str` | Return the canonical RFC 9110 reason phrase for *status*. |
| `get_default_engine` | `aquilia/faults/engine.py` | `def get_default_engine() -> FaultEngine` | Get or create default global fault engine. |
| `process_fault` | `aquilia/faults/engine.py` | `async def process_fault(exception: Exception &#124; Fault, *, engine: FaultEngine &#124; None = None) -> FaultResult` | Process fault using engine. |
| `patch_all_subsystems` | `aquilia/faults/integrations/__init__.py` | `def patch_all_subsystems()` | Patch all Aquilia subsystems to use AquilaFaults. |
| `create_all_integration_handlers` | `aquilia/faults/integrations/__init__.py` | `def create_all_integration_handlers()` | Create fault handlers for all subsystem integrations. |
| `patch_di_container` | `aquilia/faults/integrations/di.py` | `def patch_di_container()` | Patch DI Container to emit structured faults. |
| `create_di_fault_handler` | `aquilia/faults/integrations/di.py` | `def create_di_fault_handler()` | Create fault handler for DI operations. |
| `fault_handling_middleware` | `aquilia/faults/integrations/flow.py` | `async def fault_handling_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], engine: FaultEngine &#124; None = None)` | Core fault handling middleware. |
| `timeout_middleware` | `aquilia/faults/integrations/flow.py` | `async def timeout_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], timeout_seconds: float = 30.0)` | Timeout middleware with fault emission. |
| `fault_aware_handler` | `aquilia/faults/integrations/flow.py` | `def fault_aware_handler(handler: Callable)` | Decorator to make handler fault-aware. |
| `create_flow_fault_handler` | `aquilia/faults/integrations/flow.py` | `def create_flow_fault_handler()` | Create fault handler for flow operations. |
| `with_cancellation_handling` | `aquilia/faults/integrations/flow.py` | `async def with_cancellation_handling(coro: Awaitable[Any]) -> Any` | Wrap coroutine with cancellation fault handling. |
| `is_fault_retryable` | `aquilia/faults/integrations/flow.py` | `def is_fault_retryable(fault: Fault) -> bool` | Check if fault is retryable. |
| `should_abort_pipeline` | `aquilia/faults/integrations/flow.py` | `def should_abort_pipeline(fault: Fault) -> bool` | Check if fault should abort the pipeline. |
| `create_model_fault_handler` | `aquilia/faults/integrations/models.py` | `def create_model_fault_handler(max_retries: int = 3, log_queries: bool = True) -> ModelFaultHandler` | Create a fault handler for the MODEL domain. |
| `patch_model_registry` | `aquilia/faults/integrations/models.py` | `def patch_model_registry() -> None` | Patch model registries to raise structured faults instead of bare exceptions. |
| `patch_database_engine` | `aquilia/faults/integrations/models.py` | `def patch_database_engine() -> None` | Patch AquiliaDatabase to raise structured faults on connection errors. |
| `patch_all_model_subsystems` | `aquilia/faults/integrations/models.py` | `def patch_all_model_subsystems() -> None` | Patch all model-related subsystems with fault integration. |
| `patch_runtime_registry` | `aquilia/faults/integrations/registry.py` | `def patch_runtime_registry()` | Patch RuntimeRegistry to emit structured faults. |
| `create_registry_fault_handler` | `aquilia/faults/integrations/registry.py` | `def create_registry_fault_handler()` | Create fault handler for registry operations. |
| `create_routing_fault_handler` | `aquilia/faults/integrations/routing.py` | `def create_routing_fault_handler()` | Create fault handler for routing operations. |
| `safe_route_lookup` | `aquilia/faults/integrations/routing.py` | `def safe_route_lookup(router, path: str, method: str = 'GET')` | Safely lookup route, returning fault instead of throwing. |
| `validate_route_pattern` | `aquilia/faults/integrations/routing.py` | `def validate_route_pattern(pattern: str) -> PatternInvalidFault &#124; None` | Validate route pattern syntax. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `DOMAIN_DEFAULTS` | `aquilia/faults/core.py` | `{FaultDomain.CONFIG: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.REGISTRY: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.DI: {` |
| `_HTTP_REASONS` | `aquilia/faults/domains.py` | `dict[int, str]` |
