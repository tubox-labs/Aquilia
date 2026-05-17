# Tasks Troubleshooting

Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults.

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
| `aquilia/tasks/__init__.py` | 82 | 0 | 0 | AquilaTasks — Industry-Grade Async Background Task Manager. |
| `aquilia/tasks/decorators.py` | 218 | 0 | 4 | AquilaTasks — Task Decorator. |
| `aquilia/tasks/engine.py` | 841 | 3 | 0 | AquilaTasks — Task Engine & Backends. |
| `aquilia/tasks/faults.py` | 130 | 5 | 0 | AquilaTasks — Fault Classes. |
| `aquilia/tasks/job.py` | 179 | 4 | 0 | AquilaTasks — Job Model. |
| `aquilia/tasks/schedule.py` | 254 | 2 | 2 | AquilaTasks — Schedule Definitions. |
| `aquilia/tasks/worker.py` | 98 | 1 | 0 | AquilaTasks — Worker. |
