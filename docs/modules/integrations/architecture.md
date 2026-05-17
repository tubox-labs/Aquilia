# Integrations Architecture

## Runtime Role

Typed configuration dataclasses that serialize workspace integration settings for auth, cache, database, mail, MLOps, middleware, OpenAPI, render, security, sessions, storage, tasks, templates, and versioning.

The implementation is split across 21 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/integrations/__init__.py`: Aquilia Integrations - Typed, validated configuration objects.
- `aquilia/integrations/_protocol.py`: IntegrationConfig protocol - the contract every integration type satisfies.
- `aquilia/integrations/admin.py`: Admin integration - typed admin dashboard configuration.
- `aquilia/integrations/auth.py`: AuthIntegration - typed auth configuration.
- `aquilia/integrations/cache.py`: CacheIntegration - typed cache configuration.
- `aquilia/integrations/database.py`: DatabaseIntegration - typed database configuration.
- `aquilia/integrations/i18n.py`: I18nIntegration - typed internationalization configuration.
- `aquilia/integrations/logging_cfg.py`: LoggingIntegration - typed request/response logging configuration.
- `aquilia/integrations/mail.py`: Mail integration - typed, flat-namespace mail configuration.
- `aquilia/integrations/mlops.py`: MLOpsIntegration - typed MLOps platform configuration.
- `aquilia/integrations/mw.py`: Middleware chain integration - typed middleware configuration.
- `aquilia/integrations/openapi.py`: OpenAPIIntegration - typed OpenAPI documentation configuration.
- `aquilia/integrations/render.py`: RenderIntegration - typed Render PaaS deployment configuration.
- `aquilia/integrations/security.py`: Security integrations - CORS, CSP, Rate-Limit, CSRF.
- `aquilia/integrations/sessions.py`: SessionIntegration - typed session configuration.
- `aquilia/integrations/simple.py`: Simple integrations - small typed configs for DI, routing, faults, etc.
- `aquilia/integrations/static.py`: StaticFilesIntegration - typed static file serving configuration.
- `aquilia/integrations/storage.py`: StorageIntegration - typed file storage configuration.
- `aquilia/integrations/tasks.py`: TasksIntegration - typed background task configuration.
- `aquilia/integrations/templates.py`: TemplatesIntegration - typed template configuration.
- `aquilia/integrations/versioning_cfg.py`: VersioningIntegration - typed API versioning configuration.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 20 |
| `aquilia` | 20 |
| `typing` | 20 |
| `dataclasses` | 19 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
