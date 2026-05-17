# Middleware_Ext Troubleshooting

Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging.

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
| `aquilia/middleware_ext/__init__.py` | 99 | 0 | 0 | Extended middleware components for Aquilia framework. |
| `aquilia/middleware_ext/effect_middleware.py` | 260 | 2 | 0 | Effect Middleware -- Per-request effect lifecycle management. |
| `aquilia/middleware_ext/logging.py` | 283 | 4 | 0 | Enhanced Logging Middleware - Structured access logging. |
| `aquilia/middleware_ext/rate_limit.py` | 473 | 2 | 3 | Rate Limiting Middleware - Production-grade request rate limiting. |
| `aquilia/middleware_ext/request_scope.py` | 168 | 2 | 1 | Request Scope Middleware - Creates request-scoped DI container per request. |
| `aquilia/middleware_ext/security.py` | 1187 | 9 | 2 | Security Middleware Suite - Production-grade HTTP security middleware. |
| `aquilia/middleware_ext/session_middleware.py` | 214 | 2 | 1 | Session Middleware - Integrates SessionEngine with request lifecycle. |
| `aquilia/middleware_ext/static.py` | 590 | 1 | 0 | Static File Middleware - Production-grade static asset serving. |
