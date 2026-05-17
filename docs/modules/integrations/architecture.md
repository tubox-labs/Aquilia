# Integrations Architecture

Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/integrations/__init__.py` | 191 | 0 | 0 | Aquilia Integrations — Typed, validated configuration objects. |
| `aquilia/integrations/_protocol.py` | 25 | 1 | 0 | IntegrationConfig protocol — the contract every integration type satisfies. |
| `aquilia/integrations/admin.py` | 924 | 8 | 0 | Admin integration — typed admin dashboard configuration. |
| `aquilia/integrations/auth.py` | 54 | 1 | 0 | AuthIntegration — typed auth configuration. |
| `aquilia/integrations/cache.py` | 65 | 1 | 0 | CacheIntegration — typed cache configuration. |
| `aquilia/integrations/database.py` | 75 | 1 | 0 | DatabaseIntegration — typed database configuration. |
| `aquilia/integrations/i18n.py` | 56 | 1 | 0 | I18nIntegration — typed internationalization configuration. |
| `aquilia/integrations/logging_cfg.py` | 52 | 1 | 0 | LoggingIntegration — typed request/response logging configuration. |
| `aquilia/integrations/mail.py` | 519 | 7 | 0 | Mail integration — typed, flat-namespace mail configuration. |
| `aquilia/integrations/mlops.py` | 99 | 1 | 0 | MLOpsIntegration — typed MLOps platform configuration. |
| `aquilia/integrations/mw.py` | 100 | 2 | 0 | Middleware chain integration — typed middleware configuration. |
| `aquilia/integrations/openapi.py` | 77 | 1 | 0 | OpenAPIIntegration — typed OpenAPI documentation configuration. |
| `aquilia/integrations/render.py` | 50 | 1 | 0 | RenderIntegration — typed Render PaaS deployment configuration. |
| `aquilia/integrations/security.py` | 180 | 4 | 0 | Security integrations — CORS, CSP, Rate-Limit, CSRF. |
| `aquilia/integrations/sessions.py` | 60 | 1 | 0 | SessionIntegration — typed session configuration. |
| `aquilia/integrations/simple.py` | 112 | 6 | 0 | Simple integrations — small typed configs for DI, routing, faults, etc. |
| `aquilia/integrations/static.py` | 48 | 1 | 0 | StaticFilesIntegration — typed static file serving configuration. |
| `aquilia/integrations/storage.py` | 49 | 1 | 0 | StorageIntegration — typed file storage configuration. |
| `aquilia/integrations/tasks.py` | 55 | 1 | 0 | TasksIntegration — typed background task configuration. |
| `aquilia/integrations/templates.py` | 102 | 1 | 0 | TemplatesIntegration — typed template configuration. |
| `aquilia/integrations/versioning_cfg.py` | 85 | 1 | 0 | VersioningIntegration — typed API versioning configuration. |

## Internal Shape

`integrations` has 21 Python files, 42 public classes, 0 public module-level functions, and 4 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `aquilia.integrations._protocol` | 1 |
| `aquilia.integrations.admin` | 1 |
| `aquilia.integrations.auth` | 1 |
| `aquilia.integrations.cache` | 1 |
| `aquilia.integrations.database` | 1 |
| `aquilia.integrations.i18n` | 1 |
| `aquilia.integrations.logging_cfg` | 1 |
| `aquilia.integrations.mail` | 1 |
| `aquilia.integrations.mlops` | 1 |
| `aquilia.integrations.mw` | 1 |
| `aquilia.integrations.openapi` | 1 |
| `aquilia.integrations.render` | 1 |
| `aquilia.integrations.security` | 1 |
| `aquilia.integrations.sessions` | 1 |
| `aquilia.integrations.simple` | 1 |
| `aquilia.integrations.static` | 1 |
| `aquilia.integrations.storage` | 1 |
| `aquilia.integrations.tasks` | 1 |
| `aquilia.integrations.templates` | 1 |
| `aquilia.integrations.versioning_cfg` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 20 |
| `dataclasses` | 20 |
| `typing` | 20 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | Protocol that all typed integration configs implement. |
| `AdminIntegration` | `aquilia/integrations/admin.py` | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | Typed request logging configuration. |
| `SmtpProvider` | `aquilia/integrations/mail.py` | SMTP / STARTTLS mail provider. |
| `SesProvider` | `aquilia/integrations/mail.py` | AWS Simple Email Service provider. |
| `SendGridProvider` | `aquilia/integrations/mail.py` | SendGrid Web API v3 provider. |
| `ConsoleProvider` | `aquilia/integrations/mail.py` | Console / stdout provider (development only). |
| `FileProvider` | `aquilia/integrations/mail.py` | File / .eml provider (testing & audit). |
| `MailIntegration` | `aquilia/integrations/mail.py` | Typed mail subsystem configuration. |
| `MLOpsIntegration` | `aquilia/integrations/mlops.py` | Typed MLOps platform configuration. |
| `MiddlewareEntry` | `aquilia/integrations/mw.py` | A single middleware entry in the chain. |
| `MiddlewareChain` | `aquilia/integrations/mw.py` | Fluent middleware chain builder. |
| `OpenAPIIntegration` | `aquilia/integrations/openapi.py` | Typed OpenAPI spec / Swagger UI configuration. |
| `RenderIntegration` | `aquilia/integrations/render.py` | Typed Render deployment configuration. |
| `CorsIntegration` | `aquilia/integrations/security.py` | Typed CORS middleware configuration. |
| `CspIntegration` | `aquilia/integrations/security.py` | Typed Content-Security-Policy configuration. |
| `RateLimitIntegration` | `aquilia/integrations/security.py` | Typed rate limiting configuration. |
| `CsrfIntegration` | `aquilia/integrations/security.py` | Typed CSRF protection configuration. |
| `SessionIntegration` | `aquilia/integrations/sessions.py` | Typed session integration config. |
| `DiIntegration` | `aquilia/integrations/simple.py` | Dependency injection configuration. |
| `RoutingIntegration` | `aquilia/integrations/simple.py` | Routing configuration. |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | Fault handling configuration. |
| `PatternsIntegration` | `aquilia/integrations/simple.py` | Patterns configuration. |
| `RegistryIntegration` | `aquilia/integrations/simple.py` | Registry configuration. |
| `SerializersIntegration` | `aquilia/integrations/simple.py` | Global serializer settings. |
| `StaticFilesIntegration` | `aquilia/integrations/static.py` | Typed static file serving configuration. |
| `StorageIntegration` | `aquilia/integrations/storage.py` | Typed file storage configuration. |
| `TasksIntegration` | `aquilia/integrations/tasks.py` | Typed background tasks configuration. |
| `TemplatesIntegration` | `aquilia/integrations/templates.py` | Typed template engine configuration. |
| `VersioningIntegration` | `aquilia/integrations/versioning_cfg.py` | Typed API versioning configuration. |

## Error Handling

Fault/error classes defined here:

`FaultHandlingIntegration`
