# faults Module

## Purpose

Structured error and recovery system. Use this module for typed faults, severity, fault domains, recovery strategies, adapters, handlers, response mapping, and subsystem fault types.

## Source Coverage

- Python files: 12
- Public classes: 127
- Dataclasses: 6
- Enums: 2
- Public functions: 23

## How It Fits In Aquilia

1. Import the package from `aquilia.faults` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `Severity` | `aquilia/faults/core.py` | Fault severity levels. |
| `FaultDomain` | `aquilia/faults/core.py` | Fault domains (taxonomy). |
| `RecoveryStrategy` | `aquilia/faults/core.py` | Fault recovery strategies. |
| `Fault` | `aquilia/faults/core.py` | Base fault class - structured, typed fault object. |
| `FaultContext` | `aquilia/faults/core.py` | Runtime context wrapper for faults. |
| `Resolved` | `aquilia/faults/core.py` | Fault was resolved and should not propagate further. |
| `Transformed` | `aquilia/faults/core.py` | Fault was transformed into another fault. |
| `Escalate` | `aquilia/faults/core.py` | Fault should escalate to next handler in chain. |
| `ExceptionMapping` | `aquilia/faults/default_handlers.py` | Maps exception type to Fault factory. |
| `ExceptionAdapter` | `aquilia/faults/default_handlers.py` | Convert raw Python exceptions to structured Faults. |
| `RetryHandler` | `aquilia/faults/default_handlers.py` | Retry transient failures with exponential backoff. |
| `SecurityFaultHandler` | `aquilia/faults/default_handlers.py` | Mask sensitive information in security faults. |
| `HTTPResponse` | `aquilia/faults/default_handlers.py` | HTTP response representation. |
| `ResponseMapper` | `aquilia/faults/default_handlers.py` | Map faults to HTTP/WebSocket/RPC responses. |
| `FatalHandler` | `aquilia/faults/default_handlers.py` | Terminate server on FATAL severity faults. |
| `LoggingHandler` | `aquilia/faults/default_handlers.py` | Log all faults with structured metadata. |
| `ConfigFault` | `aquilia/faults/domains.py` | Base class for configuration faults. |
| `ConfigMissingFault` | `aquilia/faults/domains.py` | Required configuration is missing. |
| `ConfigInvalidFault` | `aquilia/faults/domains.py` | Configuration value is invalid. |
| `DotenvParseFault` | `aquilia/faults/domains.py` | Dotenv file contains syntax errors. |
| `DotenvNotFoundFault` | `aquilia/faults/domains.py` | Dotenv file not found when explicitly requested. |
| `RegistryFault` | `aquilia/faults/domains.py` | Base class for Aquilary registry faults. |
| `DependencyCycleFault` | `aquilia/faults/domains.py` | Circular dependency detected in app graph. |
| `ManifestInvalidFault` | `aquilia/faults/domains.py` | Manifest validation failed. |
| `DIFault` | `aquilia/faults/domains.py` | Base class for dependency injection faults. |
| `ProviderNotFoundFault` | `aquilia/faults/domains.py` | DI provider not found. |
| `ScopeViolationFault` | `aquilia/faults/domains.py` | DI scope violation. |
| `DIResolutionFault` | `aquilia/faults/domains.py` | DI resolution failed. |
| `RoutingFault` | `aquilia/faults/domains.py` | Base class for routing faults. |
| `RouteNotFoundFault` | `aquilia/faults/domains.py` | Route not found. |
| `RouteAmbiguousFault` | `aquilia/faults/domains.py` | Multiple routes match the pattern. |
| `PatternInvalidFault` | `aquilia/faults/domains.py` | Route pattern is invalid. |
| `FlowFault` | `aquilia/faults/domains.py` | Base class for flow execution faults. |
| `HandlerFault` | `aquilia/faults/domains.py` | Handler execution failed. |
| `MiddlewareFault` | `aquilia/faults/domains.py` | Middleware execution failed. |
| `FlowCancelledFault` | `aquilia/faults/domains.py` | Flow was cancelled (timeout or client disconnect). |
| `EffectFault` | `aquilia/faults/domains.py` | Base class for effect (side-effect) faults. |
| `DatabaseFault` | `aquilia/faults/domains.py` | Database operation failed. |
| `CacheFault` | `aquilia/faults/domains.py` | Cache operation failed. |
| `IOFault` | `aquilia/faults/domains.py` | Base class for I/O faults. |
| `NetworkFault` | `aquilia/faults/domains.py` | Network operation failed. |
| `FilesystemFault` | `aquilia/faults/domains.py` | Filesystem operation failed. |
| `SecurityFault` | `aquilia/faults/domains.py` | Base class for security faults. |
| `AuthenticationFault` | `aquilia/faults/domains.py` | Authentication failed. |
| `AuthorizationFault` | `aquilia/faults/domains.py` | Authorization failed. |
| `CSRFViolationFault` | `aquilia/faults/domains.py` | CSRF token validation failed. |
| `CORSViolationFault` | `aquilia/faults/domains.py` | CORS origin not allowed. |
| `RateLimitExceededFault` | `aquilia/faults/domains.py` | Rate limit exceeded for client. |
| `CSPViolationFault` | `aquilia/faults/domains.py` | Content Security Policy violation reported. |
| `SigningFault` | `aquilia/faults/domains.py` | Base class for all signing/verification faults. |
| `BadSignatureFault` | `aquilia/faults/domains.py` | Signature verification failed - potential tampering. |
| `SignatureExpiredFault` | `aquilia/faults/domains.py` | The signature is valid but the embedded timestamp has exceeded max_age. |
| `SignatureMalformedFault` | `aquilia/faults/domains.py` | The signed value could not be parsed at all (wrong number of parts, |
| `UnsupportedAlgorithmFault` | `aquilia/faults/domains.py` | The requested algorithm is not available (e.g. asymmetric algorithm |
| `SystemFault` | `aquilia/faults/domains.py` | Base class for fatal system faults. |
| `UnrecoverableFault` | `aquilia/faults/domains.py` | Unrecoverable system fault. |
| `ResourceExhaustedFault` | `aquilia/faults/domains.py` | System resources exhausted. |
| `ModelFault` | `aquilia/faults/domains.py` | Base class for model and database faults. |
| `AMDLParseFault` | `aquilia/faults/domains.py` | AMDL file parsing failed. |
| `ModelNotFoundFault` | `aquilia/faults/domains.py` | Model not found in registry. |
| `ModelRegistrationFault` | `aquilia/faults/domains.py` | Model registration failed. |
| `MigrationFault` | `aquilia/faults/domains.py` | Database migration failed. |
| `MigrationConflictFault` | `aquilia/faults/domains.py` | Migration conflict detected (e.g. divergent migration branches). |
| `QueryFault` | `aquilia/faults/domains.py` | Query execution failed. |
| `DatabaseConnectionFault` | `aquilia/faults/domains.py` | Database connection failed. |
| `SchemaFault` | `aquilia/faults/domains.py` | Schema creation or validation failed. |
| `FieldValidationFault` | `aquilia/faults/domains.py` | Field validation failed. |
| `ProtectedDeleteFault` | `aquilia/faults/domains.py` | Cannot delete a protected object due to PROTECT on_delete. |
| `RestrictedDeleteFault` | `aquilia/faults/domains.py` | Cannot delete a restricted object due to RESTRICT on_delete. |
| `HTTPFault` | `aquilia/faults/domains.py` | Base class for HTTP protocol error faults. |
| `BadRequestFault` | `aquilia/faults/domains.py` | 400 Bad Request. |
| `UnauthorizedFault` | `aquilia/faults/domains.py` | 401 Unauthorized. |
| `PaymentRequiredFault` | `aquilia/faults/domains.py` | 402 Payment Required. |
| `ForbiddenFault` | `aquilia/faults/domains.py` | 403 Forbidden. |
| `NotFoundFault` | `aquilia/faults/domains.py` | 404 Not Found. |
| `MethodNotAllowedFault` | `aquilia/faults/domains.py` | 405 Method Not Allowed. |
| `NotAcceptableFault` | `aquilia/faults/domains.py` | 406 Not Acceptable. |
| `RequestTimeoutFault` | `aquilia/faults/domains.py` | 408 Request Timeout. |
| `ConflictFault` | `aquilia/faults/domains.py` | 409 Conflict. |
| `GoneFault` | `aquilia/faults/domains.py` | 410 Gone. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `http_reason` | `aquilia/faults/domains.py` | Return the canonical RFC 9110 reason phrase for *status*. |
| `get_default_engine` | `aquilia/faults/engine.py` | Get or create default global fault engine. |
| `process_fault` | `aquilia/faults/engine.py` | Process fault using engine. |
| `patch_all_subsystems` | `aquilia/faults/integrations/__init__.py` | Patch all Aquilia subsystems to use AquilaFaults. |
| `create_all_integration_handlers` | `aquilia/faults/integrations/__init__.py` | Create fault handlers for all subsystem integrations. |
| `patch_di_container` | `aquilia/faults/integrations/di.py` | Patch DI Container to emit structured faults. |
| `create_di_fault_handler` | `aquilia/faults/integrations/di.py` | Create fault handler for DI operations. |
| `fault_handling_middleware` | `aquilia/faults/integrations/flow.py` | Core fault handling middleware. |
| `timeout_middleware` | `aquilia/faults/integrations/flow.py` | Timeout middleware with fault emission. |
| `fault_aware_handler` | `aquilia/faults/integrations/flow.py` | Decorator to make handler fault-aware. |
| `create_flow_fault_handler` | `aquilia/faults/integrations/flow.py` | Create fault handler for flow operations. |
| `with_cancellation_handling` | `aquilia/faults/integrations/flow.py` | Wrap coroutine with cancellation fault handling. |
| `is_fault_retryable` | `aquilia/faults/integrations/flow.py` | Check if fault is retryable. |
| `should_abort_pipeline` | `aquilia/faults/integrations/flow.py` | Check if fault should abort the pipeline. |
| `create_model_fault_handler` | `aquilia/faults/integrations/models.py` | Create a fault handler for the MODEL domain. |
| `patch_model_registry` | `aquilia/faults/integrations/models.py` | Patch model registries to raise structured faults instead of bare exceptions. |
| `patch_database_engine` | `aquilia/faults/integrations/models.py` | Patch AquiliaDatabase to raise structured faults on connection errors. |
| `patch_all_model_subsystems` | `aquilia/faults/integrations/models.py` | Patch all model-related subsystems with fault integration. |
| `patch_runtime_registry` | `aquilia/faults/integrations/registry.py` | Patch RuntimeRegistry to emit structured faults. |
| `create_registry_fault_handler` | `aquilia/faults/integrations/registry.py` | Create fault handler for registry operations. |
| `create_routing_fault_handler` | `aquilia/faults/integrations/routing.py` | Create fault handler for routing operations. |
| `safe_route_lookup` | `aquilia/faults/integrations/routing.py` | Safely lookup route, returning fault instead of throwing. |
| `validate_route_pattern` | `aquilia/faults/integrations/routing.py` | Validate route pattern syntax. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/faults/__init__.py` | AquilaFaults - Production-grade fault handling system. |
| `aquilia/faults/core.py` | AquilaFaults - Core types and fault taxonomy. |
| `aquilia/faults/default_handlers.py` | AquilaFaults - Default Handlers. |
| `aquilia/faults/domains.py` | AquilaFaults - Domain-specific fault types. |
| `aquilia/faults/engine.py` | AquilaFaults - Fault Engine. |
| `aquilia/faults/handlers.py` | AquilaFaults - Fault handlers. |
| `aquilia/faults/integrations/__init__.py` | AquilaFaults - Subsystem Integrations. |
| `aquilia/faults/integrations/di.py` | AquilaFaults - DI Integration. |
| `aquilia/faults/integrations/flow.py` | AquilaFaults - Flow Engine Integration. |
| `aquilia/faults/integrations/models.py` | AquilaFaults - Model/Database Integration. |
| `aquilia/faults/integrations/registry.py` | AquilaFaults - Registry Integration. |
| `aquilia/faults/integrations/routing.py` | AquilaFaults - Routing Integration. |

## Testing Pointers

Search `tests/` for `faults` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
