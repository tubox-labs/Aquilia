# Integrations Documentation

This directory is the professional documentation set for `integrations`. It is implementation-driven and aligned with the current source files under `aquilia/integrations`.

## What This Covers

Typed configuration dataclasses that serialize workspace integration settings for auth, cache, database, mail, MLOps, middleware, OpenAPI, render, security, sessions, storage, tasks, templates, and versioning.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 21
- Public classes: 42
- Configuration or dataclass-like types: 41
- Public functions: 0
- Constants detected: 3

## Fast Start

```python
from aquilia import Module, Workspace
from aquilia.integrations import CacheIntegration, DatabaseIntegration, OpenAPIIntegration

workspace = (
    Workspace("myapp")
    .module(Module("catalog").route_prefix("/catalog"))
    .integrate(DatabaseIntegration(url="sqlite:///app.db", auto_create=True))
    .integrate(CacheIntegration(backend="memory", default_ttl=300))
    .integrate(OpenAPIIntegration(title="My API", version="1.0.0"))
)
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
