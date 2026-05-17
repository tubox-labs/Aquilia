# integrations Module

## Purpose

Typed workspace integration configuration. Use this module to wire auth, sessions, database, cache, storage, templates, tasks, mail, OpenAPI, security, MLOps, logging, static files, versioning, and deployment settings into a workspace.

## Source Coverage

- Python files: 21
- Public classes: 42
- Dataclasses: 40
- Enums: 0
- Public functions: 0

## How It Fits In Aquilia

1. Choose typed integration dataclasses or the legacy Integration builder.
2. Attach them with Workspace.integrate, Workspace.database, Workspace.tasks, Workspace.storage, or related shorthand.
3. ConfigLoader consumes the resulting dict during server startup.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | Protocol that all typed integration configs implement. |
| `AdminModules` | `aquilia/integrations/admin.py` | Controls which admin pages are visible. |
| `AdminAudit` | `aquilia/integrations/admin.py` | Audit log configuration. |
| `AdminMonitoring` | `aquilia/integrations/admin.py` | Monitoring dashboard configuration. |
| `AdminSidebar` | `aquilia/integrations/admin.py` | Admin sidebar section visibility. |
| `AdminContainers` | `aquilia/integrations/admin.py` | Docker containers admin page configuration. |
| `AdminPods` | `aquilia/integrations/admin.py` | Kubernetes pods admin page configuration. |
| `AdminSecurity` | `aquilia/integrations/admin.py` | Admin dashboard security configuration (CSRF, rate-limit, passwords, headers). |
| `AdminIntegration` | `aquilia/integrations/admin.py` | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | Typed request logging configuration. |
| `MailAuth` | `aquilia/integrations/mail.py` | Mail authentication credentials. |
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

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| None detected |  |  |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/integrations/__init__.py` | Aquilia Integrations - Typed, validated configuration objects. |
| `aquilia/integrations/_protocol.py` | IntegrationConfig protocol - the contract every integration type satisfies. |
| `aquilia/integrations/admin.py` | Admin integration - typed admin dashboard configuration. |
| `aquilia/integrations/auth.py` | AuthIntegration - typed auth configuration. |
| `aquilia/integrations/cache.py` | CacheIntegration - typed cache configuration. |
| `aquilia/integrations/database.py` | DatabaseIntegration - typed database configuration. |
| `aquilia/integrations/i18n.py` | I18nIntegration - typed internationalization configuration. |
| `aquilia/integrations/logging_cfg.py` | LoggingIntegration - typed request/response logging configuration. |
| `aquilia/integrations/mail.py` | Mail integration - typed, flat-namespace mail configuration. |
| `aquilia/integrations/mlops.py` | MLOpsIntegration - typed MLOps platform configuration. |
| `aquilia/integrations/mw.py` | Middleware chain integration - typed middleware configuration. |
| `aquilia/integrations/openapi.py` | OpenAPIIntegration - typed OpenAPI documentation configuration. |
| `aquilia/integrations/render.py` | RenderIntegration - typed Render PaaS deployment configuration. |
| `aquilia/integrations/security.py` | Security integrations - CORS, CSP, Rate-Limit, CSRF. |
| `aquilia/integrations/sessions.py` | SessionIntegration - typed session configuration. |
| `aquilia/integrations/simple.py` | Simple integrations - small typed configs for DI, routing, faults, etc. |
| `aquilia/integrations/static.py` | StaticFilesIntegration - typed static file serving configuration. |
| `aquilia/integrations/storage.py` | StorageIntegration - typed file storage configuration. |
| `aquilia/integrations/tasks.py` | TasksIntegration - typed background task configuration. |
| `aquilia/integrations/templates.py` | TemplatesIntegration - typed template configuration. |
| `aquilia/integrations/versioning_cfg.py` | VersioningIntegration - typed API versioning configuration. |

## Testing Pointers

Search `tests/` for `integrations` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
