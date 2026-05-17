# Storage Configuration

Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `StorageConfigFault` | `aquilia/storage/base.py` |  | Raised on storage configuration / registry errors. |
| `StorageConfig` | `aquilia/storage/configs.py` | `to_dict` | Base storage configuration. |
| `LocalConfig` | `aquilia/storage/configs.py` |  | Configuration for the local filesystem storage backend. |
| `MemoryConfig` | `aquilia/storage/configs.py` |  | Configuration for the in-memory storage backend (testing). |
| `S3Config` | `aquilia/storage/configs.py` |  | Configuration for Amazon S3 or S3-compatible storage. |
| `GCSConfig` | `aquilia/storage/configs.py` |  | Configuration for Google Cloud Storage. |
| `AzureBlobConfig` | `aquilia/storage/configs.py` |  | Configuration for Azure Blob Storage. |
| `SFTPConfig` | `aquilia/storage/configs.py` |  | Configuration for SFTP/SSH storage. |
| `CompositeConfig` | `aquilia/storage/configs.py` |  | Configuration for the composite (multi-backend) storage. |
| `StorageEffectProvider` | `aquilia/storage/effects.py` | `kind`, `set_registry`, `initialize`, `acquire`, `release`, `finalize` | Effect provider that yields ``StorageBackend`` instances from the ``StorageRegistry``. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
