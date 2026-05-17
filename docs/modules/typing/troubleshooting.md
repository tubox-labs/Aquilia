# Typing Troubleshooting

Shared protocols, typed dictionaries, aliases, and interface contracts for ASGI, containers, config, controllers, effects, manifests, middleware, and request state.

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
| `aquilia/typing/__init__.py` | 144 | 0 | 0 |  |
| `aquilia/typing/asgi.py` | 151 | 21 | 0 |  |
| `aquilia/typing/common.py` | 24 | 0 | 0 |  |
| `aquilia/typing/config.py` | 121 | 4 | 0 | Configuration type definitions for Aquilia. |
| `aquilia/typing/container.py` | 46 | 7 | 0 |  |
| `aquilia/typing/controller.py` | 30 | 1 | 0 |  |
| `aquilia/typing/effects.py` | 21 | 1 | 0 |  |
| `aquilia/typing/manifest.py` | 26 | 2 | 0 |  |
| `aquilia/typing/middleware.py` | 20 | 1 | 0 |  |
| `aquilia/typing/request_state.py` | 10 | 0 | 0 |  |
