# Integrations Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | Fault handling configuration. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
