# Storage Troubleshooting

Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem.

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
| `aquilia/storage/__init__.py` | 155 | 0 | 0 | Aquilia Storage -- Production-grade, async-first file storage abstraction. |
| `aquilia/storage/backends/__init__.py` | 25 | 0 | 0 | Storage Backends -- concrete StorageBackend implementations. |
| `aquilia/storage/backends/azure.py` | 324 | 1 | 0 | Azure Blob Storage Backend. |
| `aquilia/storage/backends/composite.py` | 167 | 1 | 0 | Composite / Multi-Backend Storage. |
| `aquilia/storage/backends/gcs.py` | 279 | 1 | 0 | Google Cloud Storage Backend. |
| `aquilia/storage/backends/local.py` | 211 | 1 | 0 | Local Filesystem Storage Backend. |
| `aquilia/storage/backends/memory.py` | 158 | 1 | 0 | In-Memory Storage Backend. |
| `aquilia/storage/backends/s3.py` | 300 | 1 | 0 | Amazon S3 / S3-Compatible Storage Backend. |
| `aquilia/storage/backends/sftp.py` | 277 | 1 | 0 | SFTP / SSH Storage Backend. |
| `aquilia/storage/base.py` | 585 | 10 | 0 | Storage Base -- Abstract backend contract and core types. |
| `aquilia/storage/configs.py` | 209 | 8 | 1 | Storage Configs -- Typed configuration dataclasses for each backend. |
| `aquilia/storage/effects.py` | 81 | 1 | 0 | Storage Effect Provider -- Bridges storage into the Aquilia Effect system. |
| `aquilia/storage/registry.py` | 224 | 1 | 1 | Storage Registry -- Named backend registry. |
| `aquilia/storage/subsystem.py` | 171 | 1 | 0 | Storage Subsystem -- Aquilia boot lifecycle integration for storage. |
