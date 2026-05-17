# Integrations Troubleshooting

Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
