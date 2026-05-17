# Integrations Configuration

Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This package is itself the typed integration configuration layer. Each integration class serializes with `to_dict()` and is intended for `Workspace.integrate(...)`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | `to_dict` | Protocol that all typed integration configs implement. |
| `AdminIntegration` | `aquilia/integrations/admin.py` | `to_dict` | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | `to_dict` | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | `to_dict` | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | `to_dict` | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | `to_dict` | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | `to_dict` | Typed request logging configuration. |
| `SmtpProvider` | `aquilia/integrations/mail.py` | `to_dict` | SMTP / STARTTLS mail provider. |
| `SesProvider` | `aquilia/integrations/mail.py` | `to_dict` | AWS Simple Email Service provider. |
| `SendGridProvider` | `aquilia/integrations/mail.py` | `to_dict` | SendGrid Web API v3 provider. |
| `ConsoleProvider` | `aquilia/integrations/mail.py` | `to_dict` | Console / stdout provider (development only). |
| `FileProvider` | `aquilia/integrations/mail.py` | `to_dict` | File / .eml provider (testing & audit). |
| `MailIntegration` | `aquilia/integrations/mail.py` | `to_dict` | Typed mail subsystem configuration. |
| `MLOpsIntegration` | `aquilia/integrations/mlops.py` | `to_dict` | Typed MLOps platform configuration. |
| `MiddlewareEntry` | `aquilia/integrations/mw.py` | `to_dict` | A single middleware entry in the chain. |
| `MiddlewareChain` | `aquilia/integrations/mw.py` | `use`, `to_list`, `chain`, `defaults`, `production`, `minimal` | Fluent middleware chain builder. |
| `OpenAPIIntegration` | `aquilia/integrations/openapi.py` | `to_dict` | Typed OpenAPI spec / Swagger UI configuration. |
| `RenderIntegration` | `aquilia/integrations/render.py` | `to_dict` | Typed Render deployment configuration. |
| `CorsIntegration` | `aquilia/integrations/security.py` | `to_dict` | Typed CORS middleware configuration. |
| `CspIntegration` | `aquilia/integrations/security.py` | `to_dict` | Typed Content-Security-Policy configuration. |
| `RateLimitIntegration` | `aquilia/integrations/security.py` | `to_dict` | Typed rate limiting configuration. |
| `CsrfIntegration` | `aquilia/integrations/security.py` | `to_dict` | Typed CSRF protection configuration. |
| `SessionIntegration` | `aquilia/integrations/sessions.py` | `to_dict` | Typed session integration config. |
| `DiIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Dependency injection configuration. |
| `RoutingIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Routing configuration. |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Fault handling configuration. |
| `PatternsIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Patterns configuration. |
| `RegistryIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Registry configuration. |
| `SerializersIntegration` | `aquilia/integrations/simple.py` | `to_dict` | Global serializer settings. |
| `StaticFilesIntegration` | `aquilia/integrations/static.py` | `to_dict` | Typed static file serving configuration. |
| `StorageIntegration` | `aquilia/integrations/storage.py` | `to_dict` | Typed file storage configuration. |
| `TasksIntegration` | `aquilia/integrations/tasks.py` | `to_dict` | Typed background tasks configuration. |
| `TemplatesIntegration` | `aquilia/integrations/templates.py` | `to_dict`, `builder`, `source`, `defaults` | Typed template engine configuration. |
| `VersioningIntegration` | `aquilia/integrations/versioning_cfg.py` | `to_dict` | Typed API versioning configuration. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
