# Faults Architecture

Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations.

## Source Boundaries

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

## Internal Shape

`faults` has 12 Python files, 127 public classes, 23 public module-level functions, and 4 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.core` | 5 |
| `aquilia.faults` | 4 |
| `aquilia.faults.domains` | 4 |
| `.domains` | 3 |
| `.handlers` | 3 |
| `..core` | 1 |
| `..domains` | 1 |
| `..handlers` | 1 |
| `.default_handlers` | 1 |
| `.di` | 1 |
| `.engine` | 1 |
| `.models` | 1 |
| `.registry` | 1 |
| `.routing` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 6 |
| `__future__` | 5 |
| `collections` | 4 |
| `asyncio` | 3 |
| `logging` | 3 |
| `dataclasses` | 2 |
| `abc` | 1 |
| `contextvars` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `hashlib` | 1 |
| `inspect` | 1 |
| `sys` | 1 |
| `time` | 1 |
| `traceback` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ExceptionAdapter` | `aquilia/faults/default_handlers.py` | Convert raw Python exceptions to structured Faults. |
| `ConfigFault` | `aquilia/faults/domains.py` | Base class for configuration faults. |
| `ConfigMissingFault` | `aquilia/faults/domains.py` | Required configuration is missing. |
| `ConfigInvalidFault` | `aquilia/faults/domains.py` | Configuration value is invalid. |
| `RegistryFault` | `aquilia/faults/domains.py` | Base class for Aquilary registry faults. |
| `ProviderNotFoundFault` | `aquilia/faults/domains.py` | DI provider not found. |
| `MiddlewareFault` | `aquilia/faults/domains.py` | Middleware execution failed. |
| `ProviderFault` | `aquilia/faults/domains.py` | Base class for cloud provider integration faults. |
| `ProviderAPIFault` | `aquilia/faults/domains.py` | Cloud provider API returned an error response. |
| `ProviderAuthFault` | `aquilia/faults/domains.py` | Cloud provider authentication failure (401/403). |
| `ProviderRateLimitFault` | `aquilia/faults/domains.py` | Cloud provider rate limit exceeded (429). |
| `ProviderTokenFault` | `aquilia/faults/domains.py` | Provider API token is missing, invalid, or expired. |
| `ProviderCredentialFault` | `aquilia/faults/domains.py` | Credential storage or retrieval failure. |
| `ProviderConnectionFault` | `aquilia/faults/domains.py` | Network connection to provider API failed. |
| `DeployConfigFault` | `aquilia/faults/domains.py` | Deployment configuration is invalid or incomplete. |
| `FaultEngine` | `aquilia/faults/engine.py` | Runtime fault processor. |
| `FaultMiddleware` | `aquilia/faults/engine.py` | Middleware that bridges the FaultEngine with the request/response lifecycle. |
| `ScopedHandlerRegistry` | `aquilia/faults/handlers.py` | Registry of fault handlers at different scopes. |
| `ProviderRegistrationFault` | `aquilia/faults/integrations/di.py` | Provider registration failed. |
| `MiddlewareChainFault` | `aquilia/faults/integrations/flow.py` | Middleware chain execution failed. |

## Error Handling

Fault/error classes defined here:

`FaultDomain`, `Fault`, `FaultContext`, `SecurityFaultHandler`, `ConfigFault`, `ConfigMissingFault`, `ConfigInvalidFault`, `DotenvParseFault`, `DotenvNotFoundFault`, `RegistryFault`, `DependencyCycleFault`, `ManifestInvalidFault`, `DIFault`, `ProviderNotFoundFault`, `ScopeViolationFault`, `DIResolutionFault`, `RoutingFault`, `RouteNotFoundFault`, `RouteAmbiguousFault`, `PatternInvalidFault`, `FlowFault`, `HandlerFault`, `MiddlewareFault`, `FlowCancelledFault`, `EffectFault`, `DatabaseFault`, `CacheFault`, `IOFault`, `NetworkFault`, `FilesystemFault`, `SecurityFault`, `AuthenticationFault`, `AuthorizationFault`, `CSRFViolationFault`, `CORSViolationFault`, `RateLimitExceededFault`, `CSPViolationFault`, `SigningFault`, `BadSignatureFault`, `SignatureExpiredFault`, `SignatureMalformedFault`, `UnsupportedAlgorithmFault`, `SystemFault`, `UnrecoverableFault`, `ResourceExhaustedFault`, `ModelFault`, `AMDLParseFault`, `ModelNotFoundFault`, `ModelRegistrationFault`, `MigrationFault`, `MigrationConflictFault`, `QueryFault`, `DatabaseConnectionFault`, `SchemaFault`, `FieldValidationFault`, `ProtectedDeleteFault`, `RestrictedDeleteFault`, `HTTPFault`, `BadRequestFault`, `UnauthorizedFault`, `PaymentRequiredFault`, `ForbiddenFault`, `NotFoundFault`, `MethodNotAllowedFault`, `NotAcceptableFault`, `RequestTimeoutFault`, `ConflictFault`, `GoneFault`, `PayloadTooLargeFault`, `URITooLongFault`, `UnsupportedMediaTypeFault`, `UnprocessableEntityFault`, `LockedFault`, `TooEarlyFault`, `PreconditionRequiredFault`, `TooManyRequestsFault`, `RequestHeaderFieldsTooLargeFault`, `UnavailableForLegalReasonsFault`, `InternalServerErrorFault`, `NotImplementedFault`
