# Faults API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/faults/__init__.py` | 292 | 0 | 0 | AquilaFaults - Production-grade fault handling system. |
| `aquilia/faults/core.py` | 490 | 8 | 0 | AquilaFaults - Core types and fault taxonomy. |
| `aquilia/faults/default_handlers.py` | 535 | 8 | 0 | AquilaFaults - Default Handlers. |
| `aquilia/faults/domains.py` | 1540 | 92 | 1 | AquilaFaults - Domain-specific fault types. |
| `aquilia/faults/engine.py` | 499 | 2 | 2 | AquilaFaults - Fault Engine. |
| `aquilia/faults/handlers.py` | 193 | 3 | 0 | AquilaFaults - Fault handlers. |
| `aquilia/faults/integrations/__init__.py` | 130 | 0 | 2 | AquilaFaults - Subsystem Integrations. |
| `aquilia/faults/integrations/di.py` | 185 | 3 | 2 | AquilaFaults - DI Integration. |
| `aquilia/faults/integrations/flow.py` | 355 | 3 | 7 | AquilaFaults - Flow Engine Integration. |
| `aquilia/faults/integrations/models.py` | 223 | 1 | 4 | AquilaFaults - Model/Database Integration. |
| `aquilia/faults/integrations/registry.py` | 148 | 4 | 2 | AquilaFaults - Registry Integration. |
| `aquilia/faults/integrations/routing.py` | 211 | 3 | 3 | AquilaFaults - Routing Integration. |

## Public Exports

`AMDLParseFault`, `AppContextInvalidFault`, `AsyncResolutionFault`, `AuthenticationFault`, `AuthorizationFault`, `BadGatewayFault`, `BadRequestFault`, `BadSignatureFault`, `CORSViolationFault`, `CSPViolationFault`, `CSRFViolationFault`, `CacheFault`, `CircularDependencyFault`, `ConfigFault`, `ConfigInvalidFault`, `ConfigMissingFault`, `ConflictFault`, `DIFault`, `DIResolutionFault`, `DatabaseConnectionFault`, `DatabaseFault`, `DependencyCycleFault`, `DependencyResolutionFault`, `DeployAppFault`, `DeployConfigFault`, `DeployFault`, `DeployHealthFault`, `DeployImageFault`, `DeployServiceFault`, `EffectFault`, `Escalate`, `ExceptionAdapter`, `FatalHandler`, `Fault`, `FaultContext`, `FaultDomain`, `FaultEngine`, `FaultHandler`, `FaultResult`, `FieldValidationFault`, `FilesystemFault`, `FlowCancelledFault`, `FlowFault`, `ForbiddenFault`, `GatewayTimeoutFault`, `GoneFault`, `HTTPFault`, `HTTPResponse`, `HandlerFault`, `IOFault`, `InternalServerErrorFault`, `LockedFault`, `LoggingHandler`, `ManifestInvalidFault`, `ManifestLoadFault`, `MethodNotAllowedFault`, `MiddlewareFault`, `MigrationConflictFault`, `MigrationFault`, `ModelFault`, `ModelFaultHandler`, `ModelNotFoundFault`, `ModelRegistrationFault`, `NetworkFault`, `NotAcceptableFault`, `NotFoundFault`, `NotImplementedFault`, `PatternInvalidFault`, `PayloadTooLargeFault`, `PaymentRequiredFault`, `PreconditionRequiredFault`, `ProtectedDeleteFault`, `ProviderAPIFault`, `ProviderAuthFault`, `ProviderConnectionFault`, `ProviderCredentialFault`, `ProviderFault`, `ProviderNotFoundFault`, `ProviderRateLimitFault`, `ProviderRegistrationFault`, `ProviderTokenFault`, `QueryFault`, `RateLimitExceededFault`, `RecoveryStrategy`, `RegistryFault`, `RequestHeaderFieldsTooLargeFault`, `RequestTimeoutFault`, `Resolved`, `ResourceExhaustedFault`, `ResponseMapper`, `RestrictedDeleteFault`, `RetryHandler`, `RouteAmbiguousFault`, `RouteCompilationFault`, `RouteConflictFault`, `RouteNotFoundFault`, `RouteParameterFault`, `RoutingFault`, `SchemaFault`, `ScopeViolationFault`, `SecurityFault`, `SecurityFaultHandler`, `ServiceUnavailableFault`, `Severity`, `SignatureExpiredFault`, `SignatureMalformedFault`, `SigningFault`, `SystemFault`, `TooEarlyFault`, `TooManyRequestsFault`, `Transformed`, `URITooLongFault`, `UnauthorizedFault`, `UnavailableForLegalReasonsFault`, `UnprocessableEntityFault`, `UnrecoverableFault`, `UnsupportedAlgorithmFault`, `UnsupportedMediaTypeFault`, `create_di_fault_handler`, `create_model_fault_handler`, `create_registry_fault_handler`, `create_routing_fault_handler`, `get_default_engine`, `http_reason`, `patch_all_model_subsystems`, `patch_database_engine`, `patch_di_container`, `patch_model_registry`, `patch_runtime_registry`, `process_fault`, `safe_route_lookup`, `validate_route_pattern`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `BadSignatureFault` | `aquilia/faults/domains.py` | SigningFault | Signature verification failed — potential tampering. |
| `SignatureExpiredFault` | `aquilia/faults/domains.py` | BadSignatureFault | The signature is valid but the embedded timestamp has exceeded max_age. |
| `SignatureMalformedFault` | `aquilia/faults/domains.py` | SigningFault | The signed value could not be parsed at all (wrong number of parts, non-base64 characters, corrupted JSON, etc.). |
| `UnsupportedAlgorithmFault` | `aquilia/faults/domains.py` | SigningFault | The requested algorithm is not available (e.g. asymmetric algorithm requested but the ``cryptography`` package is not installed). |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `http_reason` | `aquilia/faults/domains.py` | `def http_reason(status: int)` | Return the canonical RFC 9110 reason phrase for *status*. |
| `get_default_engine` | `aquilia/faults/engine.py` | `def get_default_engine()` | Get or create default global fault engine. |
| `process_fault` | `aquilia/faults/engine.py` | `async def process_fault(exception: Exception \| Fault, *, engine: FaultEngine \| None=None)` | Process fault using engine. |
| `patch_all_subsystems` | `aquilia/faults/integrations/__init__.py` | `def patch_all_subsystems()` | Patch all Aquilia subsystems to use AquilaFaults. |
| `create_all_integration_handlers` | `aquilia/faults/integrations/__init__.py` | `def create_all_integration_handlers()` | Create fault handlers for all subsystem integrations. |
| `patch_di_container` | `aquilia/faults/integrations/di.py` | `def patch_di_container()` | Patch DI Container to emit structured faults. |
| `create_di_fault_handler` | `aquilia/faults/integrations/di.py` | `def create_di_fault_handler()` | Create fault handler for DI operations. |
| `fault_handling_middleware` | `aquilia/faults/integrations/flow.py` | `async def fault_handling_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], engine: FaultEngine \| None=None)` | Core fault handling middleware. |
| `timeout_middleware` | `aquilia/faults/integrations/flow.py` | `async def timeout_middleware(request, next_handler: Callable[[Any], Awaitable[Any]], timeout_seconds: float=30.0)` | Timeout middleware with fault emission. |
| `fault_aware_handler` | `aquilia/faults/integrations/flow.py` | `def fault_aware_handler(handler: Callable)` | Decorator to make handler fault-aware. |
| `create_flow_fault_handler` | `aquilia/faults/integrations/flow.py` | `def create_flow_fault_handler()` | Create fault handler for flow operations. |
| `with_cancellation_handling` | `aquilia/faults/integrations/flow.py` | `async def with_cancellation_handling(coro: Awaitable[Any])` | Wrap coroutine with cancellation fault handling. |
| `is_fault_retryable` | `aquilia/faults/integrations/flow.py` | `def is_fault_retryable(fault: Fault)` | Check if fault is retryable. |
| `should_abort_pipeline` | `aquilia/faults/integrations/flow.py` | `def should_abort_pipeline(fault: Fault)` | Check if fault should abort the pipeline. |
| `create_model_fault_handler` | `aquilia/faults/integrations/models.py` | `def create_model_fault_handler(max_retries: int=3, log_queries: bool=True)` | Create a fault handler for the MODEL domain. |
| `patch_model_registry` | `aquilia/faults/integrations/models.py` | `def patch_model_registry()` | Patch model registries to raise structured faults instead of bare exceptions. |
| `patch_database_engine` | `aquilia/faults/integrations/models.py` | `def patch_database_engine()` | Patch AquiliaDatabase to raise structured faults on connection errors. |
| `patch_all_model_subsystems` | `aquilia/faults/integrations/models.py` | `def patch_all_model_subsystems()` | Patch all model-related subsystems with fault integration. |
| `patch_runtime_registry` | `aquilia/faults/integrations/registry.py` | `def patch_runtime_registry()` | Patch RuntimeRegistry to emit structured faults. |
| `create_registry_fault_handler` | `aquilia/faults/integrations/registry.py` | `def create_registry_fault_handler()` | Create fault handler for registry operations. |
| `create_routing_fault_handler` | `aquilia/faults/integrations/routing.py` | `def create_routing_fault_handler()` | Create fault handler for routing operations. |
| `safe_route_lookup` | `aquilia/faults/integrations/routing.py` | `def safe_route_lookup(router, path: str, method: str='GET')` | Safely lookup route, returning fault instead of throwing. |
| `validate_route_pattern` | `aquilia/faults/integrations/routing.py` | `def validate_route_pattern(pattern: str)` | Validate route pattern syntax. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `DOMAIN_DEFAULTS` | `aquilia/faults/core.py` | `{FaultDomain.CONFIG: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.REGISTRY: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.DI: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.ROUTING: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.FLOW: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.EFFECT: {'severity': Severity.ERROR, 'retryable': True}, FaultDomain.IO: {'severity': Severity.WARN, 'retryable': True}, FaultDomain.SECURITY: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.SYSTEM: {'severity': Severity.FATAL, 'retryable': False}, FaultDomain.MODEL: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.CACHE: {'severity': Severity.ERROR, 'retryable': True}, FaultDomain.STORAGE: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.TASKS: {'severity': Severity.ERROR, 'retryable': True}, FaultDomain.TEMPLATE: {'severity': Severity.ERROR, 'retryable': False}, FaultDomain.HTTP: {'severity': Severity.WARN, 'retryable': False}, FaultDomain.PROVIDER: {'severity': Severity.ERROR, 'retryable': True}, FaultDomain.DEPLOY: {'severity': Severity.ERROR, 'retryable': False}}` |
| `_HTTP_REASONS` | `aquilia/faults/domains.py` | `dict[int, str]` |

## Detailed Classes And Methods

### `Severity`

- Source: `aquilia/faults/core.py`
- Bases: `str, Enum`
- Summary: Fault severity levels.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `INFO` | `` | `'info'` |
| `WARN` | `` | `'warn'` |
| `ERROR` | `` | `'error'` |
| `FATAL` | `` | `'fatal'` |
| `LOW` | `` | `INFO` |
| `MEDIUM` | `` | `WARN` |
| `HIGH` | `` | `ERROR` |
| `CRITICAL` | `` | `FATAL` |

### `FaultDomain`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Fault domains (taxonomy).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `custom` | `def custom(cls, name: str, description: str='')` | Create a custom module-specific fault domain. |

### `RecoveryStrategy`

- Source: `aquilia/faults/core.py`
- Bases: `str, Enum`
- Summary: Fault recovery strategies.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PROPAGATE` | `` | `'propagate'` |
| `RETRY` | `` | `'retry'` |
| `FALLBACK` | `` | `'fallback'` |
| `MASK` | `` | `'mask'` |
| `CIRCUIT_BREAK` | `` | `'break'` |

### `Fault`

- Source: `aquilia/faults/core.py`
- Bases: `Exception`
- Summary: Base fault class - structured, typed fault object.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize fault to dictionary. |

### `FaultContext`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Runtime context wrapper for faults.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `fault` | `Fault` | `` |
| `trace_id` | `str` | `` |
| `timestamp` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `app` | `str \| None` | `None` |
| `route` | `str \| None` | `None` |
| `request_id` | `str \| None` | `None` |
| `cause` | `Exception \| None` | `None` |
| `stack` | `list[Any]` | `field(default_factory=list)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `parent` | `FaultContext \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `capture` | `def capture(cls, fault: Fault, *, app: str \| None=None, route: str \| None=None, request_id: str \| None=None, cause: Exception \| None=None, parent: FaultContext \| None=None)` | Capture fault with runtime context. |
| `fingerprint` | `def fingerprint(self)` | Generate stable fingerprint for this fault occurrence. |
| `to_dict` | `def to_dict(self)` | Serialize context to dictionary. |

### `Resolved`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Fault was resolved and should not propagate further.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `response` | `Any` | `` |

### `Transformed`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Fault was transformed into another fault.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `fault` | `Fault` | `` |
| `preserve_context` | `bool` | `True` |

### `Escalate`

- Source: `aquilia/faults/core.py`
- Bases: `object`
- Summary: Fault should escalate to next handler in chain.
- Decorators: `dataclass(frozen=True)`

### `ExceptionMapping`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `object`
- Summary: Maps exception type to Fault factory.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `exception_type` | `type[Exception]` | `` |
| `fault_factory` | `Callable[[Exception], Any]` | `` |
| `retryable` | `bool` | `False` |

### `ExceptionAdapter`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Convert raw Python exceptions to structured Faults.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Only handle if cause is unmapped exception. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Convert exception to appropriate Fault. |

### `RetryHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Retry transient failures with exponential backoff.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Only handle retryable faults. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Retry fault with exponential backoff. |

### `SecurityFaultHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Mask sensitive information in security faults.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Only handle security faults. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Mask sensitive information. |

### `HTTPResponse`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `object`
- Summary: HTTP response representation.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `status_code` | `int` | `` |
| `body` | `dict[str, Any]` | `` |
| `headers` | `dict[str, str]` | `` |

### `ResponseMapper`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Map faults to HTTP/WebSocket/RPC responses.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Handle all faults. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Map fault to HTTP response. |

### `FatalHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Terminate server on FATAL severity faults.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Only handle FATAL severity. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Log and invoke callback. |

### `LoggingHandler`

- Source: `aquilia/faults/default_handlers.py`
- Bases: `FaultHandler`
- Summary: Log all faults with structured metadata.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Handle all faults. |
| `handle` | `async def handle(self, ctx: FaultContext)` | Log fault and escalate. |

### `ConfigFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for configuration faults.

### `ConfigMissingFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Required configuration is missing.

### `ConfigInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Configuration value is invalid.

### `DotenvParseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Dotenv file contains syntax errors.

### `DotenvNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ConfigFault`
- Summary: Dotenv file not found when explicitly requested.

### `RegistryFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for Aquilary registry faults.

### `DependencyCycleFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RegistryFault`
- Summary: Circular dependency detected in app graph.

### `ManifestInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RegistryFault`
- Summary: Manifest validation failed.

### `DIFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for dependency injection faults.

### `ProviderNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI provider not found.

### `ScopeViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI scope violation.

### `DIResolutionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DIFault`
- Summary: DI resolution failed.

### `RoutingFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for routing faults.

### `RouteNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Route not found.

### `RouteAmbiguousFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Multiple routes match the pattern.

### `PatternInvalidFault`

- Source: `aquilia/faults/domains.py`
- Bases: `RoutingFault`
- Summary: Route pattern is invalid.

### `FlowFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for flow execution faults.

### `HandlerFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Handler execution failed.

### `MiddlewareFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Middleware execution failed.

### `FlowCancelledFault`

- Source: `aquilia/faults/domains.py`
- Bases: `FlowFault`
- Summary: Flow was cancelled (timeout or client disconnect).

### `EffectFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for effect (side-effect) faults.

### `DatabaseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `EffectFault`
- Summary: Database operation failed.

### `CacheFault`

- Source: `aquilia/faults/domains.py`
- Bases: `EffectFault`
- Summary: Cache operation failed.

### `IOFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for I/O faults.

### `NetworkFault`

- Source: `aquilia/faults/domains.py`
- Bases: `IOFault`
- Summary: Network operation failed.

### `FilesystemFault`

- Source: `aquilia/faults/domains.py`
- Bases: `IOFault`
- Summary: Filesystem operation failed.

### `SecurityFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for security faults.

### `AuthenticationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Authentication failed.

### `AuthorizationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Authorization failed.

### `CSRFViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: CSRF token validation failed.

### `CORSViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: CORS origin not allowed.

### `RateLimitExceededFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Rate limit exceeded for client.

### `CSPViolationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Content Security Policy violation reported.

### `SigningFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SecurityFault`
- Summary: Base class for all signing/verification faults.

### `BadSignatureFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: Signature verification failed — potential tampering.

### `SignatureExpiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `BadSignatureFault`
- Summary: The signature is valid but the embedded timestamp has exceeded max_age.

### `SignatureMalformedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: The signed value could not be parsed at all (wrong number of parts, non-base64 characters, corrupted JSON, etc.).

### `UnsupportedAlgorithmFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SigningFault`
- Summary: The requested algorithm is not available (e.g. asymmetric algorithm requested but the ``cryptography`` package is not installed).

### `SystemFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for fatal system faults.

### `UnrecoverableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SystemFault`
- Summary: Unrecoverable system fault.

### `ResourceExhaustedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `SystemFault`
- Summary: System resources exhausted.

### `ModelFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for model and database faults.

### `AMDLParseFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: AMDL file parsing failed.

### `ModelNotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Model not found in registry.

### `ModelRegistrationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Model registration failed.

### `MigrationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Database migration failed.

### `MigrationConflictFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Migration conflict detected (e.g. divergent migration branches).

### `QueryFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Query execution failed.

### `DatabaseConnectionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Database connection failed.

### `SchemaFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Schema creation or validation failed.

### `FieldValidationFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Field validation failed.

### `ProtectedDeleteFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Cannot delete a protected object due to PROTECT on_delete.

### `RestrictedDeleteFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ModelFault`
- Summary: Cannot delete a restricted object due to RESTRICT on_delete.

### `HTTPFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for HTTP protocol error faults.

### `BadRequestFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 400 Bad Request.

### `UnauthorizedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 401 Unauthorized.

### `PaymentRequiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 402 Payment Required.

### `ForbiddenFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 403 Forbidden.

### `NotFoundFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 404 Not Found.

### `MethodNotAllowedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 405 Method Not Allowed.

### `NotAcceptableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 406 Not Acceptable.

### `RequestTimeoutFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 408 Request Timeout.

### `ConflictFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 409 Conflict.

### `GoneFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 410 Gone.

### `PayloadTooLargeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 413 Content Too Large.

### `URITooLongFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 414 URI Too Long.

### `UnsupportedMediaTypeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 415 Unsupported Media Type.

### `UnprocessableEntityFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 422 Unprocessable Content.

### `LockedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 423 Locked.

### `TooEarlyFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 425 Too Early.

### `PreconditionRequiredFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 428 Precondition Required.

### `TooManyRequestsFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 429 Too Many Requests.

### `RequestHeaderFieldsTooLargeFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 431 Request Header Fields Too Large.

### `UnavailableForLegalReasonsFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 451 Unavailable For Legal Reasons.

### `InternalServerErrorFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 500 Internal Server Error.

### `NotImplementedFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 501 Not Implemented.

### `BadGatewayFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 502 Bad Gateway.

### `ServiceUnavailableFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 503 Service Unavailable.

### `GatewayTimeoutFault`

- Source: `aquilia/faults/domains.py`
- Bases: `HTTPFault`
- Summary: 504 Gateway Timeout.

### `ProviderFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for cloud provider integration faults.

### `ProviderAPIFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider API returned an error response.

### `ProviderAuthFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider authentication failure (401/403).

### `ProviderRateLimitFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Cloud provider rate limit exceeded (429).

### `ProviderTokenFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Provider API token is missing, invalid, or expired.

### `ProviderCredentialFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Credential storage or retrieval failure.

### `ProviderConnectionFault`

- Source: `aquilia/faults/domains.py`
- Bases: `ProviderFault`
- Summary: Network connection to provider API failed.

### `DeployFault`

- Source: `aquilia/faults/domains.py`
- Bases: `Fault`
- Summary: Base class for deployment orchestration faults.

### `DeployConfigFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Deployment configuration is invalid or incomplete.

### `DeployImageFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Docker image build or push failure.

### `DeployHealthFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Deployed service did not become healthy.

### `DeployAppFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Failed to create or resolve the provider app.

### `DeployServiceFault`

- Source: `aquilia/faults/domains.py`
- Bases: `DeployFault`
- Summary: Failed to create or update the provider service.

### `FaultEngine`

- Source: `aquilia/faults/engine.py`
- Bases: `object`
- Summary: Runtime fault processor.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_global` | `def register_global(self, handler: FaultHandler)` | Register global fault handler. |
| `register_app` | `def register_app(self, app: str, handler: FaultHandler)` | Register app-scoped fault handler. |
| `register_controller` | `def register_controller(self, controller: str, handler: FaultHandler)` | Register controller-scoped fault handler. |
| `register_route` | `def register_route(self, route: str, handler: FaultHandler)` | Register route-scoped fault handler. |
| `on_fault` | `def on_fault(self, listener: Callable[[FaultContext], None])` | Register fault event listener. |
| `process` | `async def process(self, exception: Exception \| Fault, *, app: str \| None=None, route: str \| None=None, request_id: str \| None=None)` | Process exception or fault. |
| `process_async_exception` | `async def process_async_exception(self, exception: Exception)` | Process async exception with automatic context capture. |
| `set_context` | `def set_context(*, app: str \| None=None, route: str \| None=None, request_id: str \| None=None)` | Set fault context for current async task. |
| `clear_context` | `def clear_context()` | Clear fault context for current async task. |
| `get_history` | `def get_history(self)` | Get fault history (debug mode only). |
| `clear_history` | `def clear_history(self)` | Clear fault history. |
| `get_stats` | `def get_stats(self)` | Get fault engine statistics. |

### `FaultMiddleware`

- Source: `aquilia/faults/engine.py`
- Bases: `object`
- Summary: Middleware that bridges the FaultEngine with the request/response lifecycle.

### `FaultHandler`

- Source: `aquilia/faults/handlers.py`
- Bases: `ABC`
- Summary: Abstract base class for fault handlers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `handle` | `async def handle(self, ctx: FaultContext)` | Handle fault context. |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Check if this handler can handle the fault. |

### `CompositeHandler`

- Source: `aquilia/faults/handlers.py`
- Bases: `FaultHandler`
- Summary: Composite handler that chains multiple handlers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `handle` | `async def handle(self, ctx: FaultContext)` | Try each handler in order. |

### `ScopedHandlerRegistry`

- Source: `aquilia/faults/handlers.py`
- Bases: `object`
- Summary: Registry of fault handlers at different scopes.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_global` | `def register_global(self, handler: FaultHandler)` | Register global handler. |
| `register_app` | `def register_app(self, app: str, handler: FaultHandler)` | Register app-scoped handler. |
| `register_controller` | `def register_controller(self, controller: str, handler: FaultHandler)` | Register controller-scoped handler. |
| `register_route` | `def register_route(self, route: str, handler: FaultHandler)` | Register route-scoped handler. |
| `get_handlers` | `def get_handlers(self, *, app: str \| None=None, controller: str \| None=None, route: str \| None=None)` | Get applicable handlers for context. |

### `CircularDependencyFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Circular dependency detected.

### `ProviderRegistrationFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Provider registration failed.

### `AsyncResolutionFault`

- Source: `aquilia/faults/integrations/di.py`
- Bases: `DIFault`
- Summary: Async resolution in sync context.

### `PipelineAbortedFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Request pipeline aborted by middleware.

### `HandlerTimeoutFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Handler execution timed out.

### `MiddlewareChainFault`

- Source: `aquilia/faults/integrations/flow.py`
- Bases: `FlowFault`
- Summary: Middleware chain execution failed.

### `ModelFaultHandler`

- Source: `aquilia/faults/integrations/models.py`
- Bases: `FaultHandler`
- Summary: Fault handler for MODEL domain faults.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_handle` | `def can_handle(self, ctx: FaultContext)` | Check if this handler can handle the fault. |
| `handle` | `def handle(self, ctx: FaultContext)` | Handle a model domain fault. |

### `ManifestLoadFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Manifest loading failed.

### `AppContextInvalidFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: App context validation failed.

### `RouteCompilationFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Route compilation failed.

### `DependencyResolutionFault`

- Source: `aquilia/faults/integrations/registry.py`
- Bases: `RegistryFault`
- Summary: Dependency resolution failed.

### `RouteConflictFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: Multiple routes match the same pattern.

### `MethodNotAllowedFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: HTTP method not allowed for route.

### `RouteParameterFault`

- Source: `aquilia/faults/integrations/routing.py`
- Bases: `RoutingFault`
- Summary: Route parameter validation failed.
