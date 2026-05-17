# Faults Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `FaultDomain` | `aquilia/faults/core.py` | Fault domains (taxonomy). |
| `Fault` | `aquilia/faults/core.py` | Base fault class - structured, typed fault object. |
| `FaultContext` | `aquilia/faults/core.py` | Runtime context wrapper for faults. |
| `SecurityFaultHandler` | `aquilia/faults/default_handlers.py` | Mask sensitive information in security faults. |
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
| `PayloadTooLargeFault` | `aquilia/faults/domains.py` | 413 Content Too Large. |
| `URITooLongFault` | `aquilia/faults/domains.py` | 414 URI Too Long. |
| `UnsupportedMediaTypeFault` | `aquilia/faults/domains.py` | 415 Unsupported Media Type. |
| `UnprocessableEntityFault` | `aquilia/faults/domains.py` | 422 Unprocessable Content. |
| `LockedFault` | `aquilia/faults/domains.py` | 423 Locked. |
| `TooEarlyFault` | `aquilia/faults/domains.py` | 425 Too Early. |
| `PreconditionRequiredFault` | `aquilia/faults/domains.py` | 428 Precondition Required. |
| `TooManyRequestsFault` | `aquilia/faults/domains.py` | 429 Too Many Requests. |
| `RequestHeaderFieldsTooLargeFault` | `aquilia/faults/domains.py` | 431 Request Header Fields Too Large. |
| `UnavailableForLegalReasonsFault` | `aquilia/faults/domains.py` | 451 Unavailable For Legal Reasons. |
| `InternalServerErrorFault` | `aquilia/faults/domains.py` | 500 Internal Server Error. |
| `NotImplementedFault` | `aquilia/faults/domains.py` | 501 Not Implemented. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/faults/__init__.py`: AquilaFaults - Production-grade fault handling system.
- `aquilia/faults/core.py`: AquilaFaults - Core types and fault taxonomy.
- `aquilia/faults/default_handlers.py`: AquilaFaults - Default Handlers.
- `aquilia/faults/domains.py`: AquilaFaults - Domain-specific fault types.
- `aquilia/faults/engine.py`: AquilaFaults - Fault Engine.
- `aquilia/faults/handlers.py`: AquilaFaults - Fault handlers.
- `aquilia/faults/integrations/__init__.py`: AquilaFaults - Subsystem Integrations.
- `aquilia/faults/integrations/di.py`: AquilaFaults - DI Integration.
- `aquilia/faults/integrations/flow.py`: AquilaFaults - Flow Engine Integration.
- `aquilia/faults/integrations/models.py`: AquilaFaults - Model/Database Integration.
- `aquilia/faults/integrations/registry.py`: AquilaFaults - Registry Integration.
- `aquilia/faults/integrations/routing.py`: AquilaFaults - Routing Integration.
