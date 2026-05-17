# Sessions Troubleshooting

Session IDs, policies, stores, transports, engine, decorators, typed session state, and session faults.

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
| `aquilia/sessions/__init__.py` | 144 | 0 | 0 | AquilaSessions - Production-grade session management for Aquilia. |
| `aquilia/sessions/core.py` | 602 | 5 | 0 | AquilaSessions - Core types. |
| `aquilia/sessions/decorators.py` | 442 | 4 | 2 | Unique Session Decorators for Aquilia. |
| `aquilia/sessions/engine.py` | 407 | 1 | 0 | AquilaSessions - Session Engine. |
| `aquilia/sessions/faults.py` | 320 | 16 | 0 | AquilaSessions - Fault definitions. |
| `aquilia/sessions/policy.py` | 456 | 5 | 0 | AquilaSessions - Policy types. |
| `aquilia/sessions/state.py` | 189 | 4 | 0 | Typed Session State for Aquilia. |
| `aquilia/sessions/store.py` | 309 | 3 | 0 | AquilaSessions - Session storage abstraction. |
| `aquilia/sessions/transport.py` | 290 | 3 | 1 | AquilaSessions - Transport adapters. |
