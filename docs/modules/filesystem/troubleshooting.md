# Filesystem Troubleshooting

Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade.

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
| `aquilia/filesystem/__init__.py` | 269 | 0 | 0 | Aquilia Filesystem — High-performance native async file I/O. |
| `aquilia/filesystem/_config.py` | 114 | 1 | 0 | Filesystem Configuration — Typed, frozen dataclass for module settings. |
| `aquilia/filesystem/_directory.py` | 356 | 1 | 7 | Directory Operations — Async wrappers for directory manipulation. |
| `aquilia/filesystem/_errors.py` | 281 | 11 | 1 | Filesystem Errors — Typed fault hierarchy for file operations. |
| `aquilia/filesystem/_handle.py` | 357 | 1 | 0 | Async File Handle — Core I/O primitive for the Aquilia filesystem module. |
| `aquilia/filesystem/_lock.py` | 252 | 2 | 0 | Async File Locking — Advisory file locks for concurrent access safety. |
| `aquilia/filesystem/_metrics.py` | 163 | 1 | 0 | Filesystem Metrics — Lightweight operation counters and latency tracking. |
| `aquilia/filesystem/_ops.py` | 573 | 1 | 9 | Convenience Filesystem Operations — High-level async file I/O functions. |
| `aquilia/filesystem/_path.py` | 525 | 1 | 0 | Async Path — Async equivalent of ``pathlib.Path``. |
| `aquilia/filesystem/_pool.py` | 170 | 1 | 0 | Filesystem Thread Pool — Dedicated executor for blocking file I/O. |
| `aquilia/filesystem/_security.py` | 244 | 0 | 3 | Filesystem Security — Path validation, sanitization, and sandbox enforcement. |
| `aquilia/filesystem/_service.py` | 495 | 1 | 0 | FileSystem Service — DI-injectable facade for async file operations. |
| `aquilia/filesystem/_streaming.py` | 308 | 2 | 2 | Streaming Pipeline — High-performance async file streaming. |
| `aquilia/filesystem/_tempfile.py` | 210 | 2 | 0 | Async Temporary Files — Secure temporary file and directory management. |
