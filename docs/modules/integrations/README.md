# Integrations Documentation

Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup.

## Coverage Snapshot

- Source files: 21
- Source lines: 2978
- Public classes: 42
- Public module functions: 0
- Constants/module flags: 4
- Public exports in `__all__`: 42

## Source Files Read

- `aquilia/integrations/__init__.py`: Aquilia Integrations — Typed, validated configuration objects.
- `aquilia/integrations/_protocol.py`: IntegrationConfig protocol — the contract every integration type satisfies.
- `aquilia/integrations/admin.py`: Admin integration — typed admin dashboard configuration.
- `aquilia/integrations/auth.py`: AuthIntegration — typed auth configuration.
- `aquilia/integrations/cache.py`: CacheIntegration — typed cache configuration.
- `aquilia/integrations/database.py`: DatabaseIntegration — typed database configuration.
- `aquilia/integrations/i18n.py`: I18nIntegration — typed internationalization configuration.
- `aquilia/integrations/logging_cfg.py`: LoggingIntegration — typed request/response logging configuration.
- `aquilia/integrations/mail.py`: Mail integration — typed, flat-namespace mail configuration.
- `aquilia/integrations/mlops.py`: MLOpsIntegration — typed MLOps platform configuration.
- `aquilia/integrations/mw.py`: Middleware chain integration — typed middleware configuration.
- `aquilia/integrations/openapi.py`: OpenAPIIntegration — typed OpenAPI documentation configuration.
- `aquilia/integrations/render.py`: RenderIntegration — typed Render PaaS deployment configuration.
- `aquilia/integrations/security.py`: Security integrations — CORS, CSP, Rate-Limit, CSRF.
- `aquilia/integrations/sessions.py`: SessionIntegration — typed session configuration.
- `aquilia/integrations/simple.py`: Simple integrations — small typed configs for DI, routing, faults, etc.
- `aquilia/integrations/static.py`: StaticFilesIntegration — typed static file serving configuration.
- `aquilia/integrations/storage.py`: StorageIntegration — typed file storage configuration.
- `aquilia/integrations/tasks.py`: TasksIntegration — typed background task configuration.
- `aquilia/integrations/templates.py`: TemplatesIntegration — typed template configuration.
- `aquilia/integrations/versioning_cfg.py`: VersioningIntegration — typed API versioning configuration.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
