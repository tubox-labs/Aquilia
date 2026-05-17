# Templates Troubleshooting

Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers.

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
| `aquilia/templates/__init__.py` | 115 | 0 | 0 | AquilaTemplates - First-class Jinja2-based template rendering for Aquilia. |
| `aquilia/templates/auth_integration.py` | 433 | 3 | 3 | AquilaTemplates - Auth Integration |
| `aquilia/templates/bytecode_cache.py` | 401 | 4 | 0 | Bytecode Cache - Template compilation caching system. |
| `aquilia/templates/cli.py` | 355 | 0 | 9 | Template CLI - Command-line interface for template management. |
| `aquilia/templates/context.py` | 232 | 1 | 7 | Template Context - Context building and injection helpers. |
| `aquilia/templates/di_providers.py` | 363 | 5 | 4 | AquilaTemplates - DI Providers |
| `aquilia/templates/engine.py` | 407 | 1 | 0 | Template Engine - Core async-capable Jinja2 template rendering engine. |
| `aquilia/templates/extensions.py` | 112 | 1 | 0 | Jinja2 template extensions used by Aquilia templates. |
| `aquilia/templates/faults.py` | 112 | 4 | 0 | AquilaTemplates — Fault Classes. |
| `aquilia/templates/loader.py` | 212 | 2 | 0 | Template Loader - Namespace-aware filesystem and package template loaders. |
| `aquilia/templates/manager.py` | 409 | 3 | 0 | Template Manager - Compilation, linting, and manifest integration. |
| `aquilia/templates/manifest_integration.py` | 345 | 2 | 7 | AquilaTemplates - Manifest Integration |
| `aquilia/templates/middleware.py` | 132 | 1 | 0 | Template Middleware - Automatic context injection for templates. |
| `aquilia/templates/security.py` | 425 | 2 | 2 | Template Security - Sandboxing and security policies. |
| `aquilia/templates/sessions_integration.py` | 356 | 3 | 3 | AquilaTemplates - Session Integration |
