# Storage Architecture

Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`storage` has 14 Python files, 28 public classes, 2 public module-level functions, and 5 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `..base` | 7 |
| `..configs` | 7 |
| `.base` | 5 |
| `.configs` | 2 |
| `...filesystem._config` | 1 |
| `...filesystem._pool` | 1 |
| `..effects` | 1 |
| `..health` | 1 |
| `..registry` | 1 |
| `..subsystems.base` | 1 |
| `.azure` | 1 |
| `.backends.azure` | 1 |
| `.backends.composite` | 1 |
| `.backends.gcs` | 1 |
| `.backends.local` | 1 |
| `.backends.memory` | 1 |
| `.backends.s3` | 1 |
| `.backends.sftp` | 1 |
| `.composite` | 1 |
| `.effects` | 1 |
| `.gcs` | 1 |
| `.local` | 1 |
| `.memory` | 1 |
| `.registry` | 1 |
| `.s3` | 1 |
| `.sftp` | 1 |
| `.subsystem` | 1 |
| `aquilia._version` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 12 |
| `typing` | 12 |
| `collections` | 9 |
| `datetime` | 5 |
| `asyncio` | 4 |
| `contextlib` | 4 |
| `os` | 3 |
| `dataclasses` | 2 |
| `logging` | 2 |
| `pathlib` | 2 |
| `abc` | 1 |
| `fnmatch` | 1 |
| `importlib` | 1 |
| `json` | 1 |
| `mimetypes` | 1 |
| `shutil` | 1 |
| `stat` | 1 |
| `uuid` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `BackendUnavailableError` | `aquilia/storage/base.py` | Raised when the storage backend is unreachable or not configured. |
| `StorageConfigFault` | `aquilia/storage/base.py` | Raised on storage configuration / registry errors. |
| `StorageBackend` | `aquilia/storage/base.py` | Abstract storage backend. |
| `StorageConfig` | `aquilia/storage/configs.py` | Base storage configuration. |
| `LocalConfig` | `aquilia/storage/configs.py` | Configuration for the local filesystem storage backend. |
| `MemoryConfig` | `aquilia/storage/configs.py` | Configuration for the in-memory storage backend (testing). |
| `S3Config` | `aquilia/storage/configs.py` | Configuration for Amazon S3 or S3-compatible storage. |
| `GCSConfig` | `aquilia/storage/configs.py` | Configuration for Google Cloud Storage. |
| `AzureBlobConfig` | `aquilia/storage/configs.py` | Configuration for Azure Blob Storage. |
| `SFTPConfig` | `aquilia/storage/configs.py` | Configuration for SFTP/SSH storage. |
| `CompositeConfig` | `aquilia/storage/configs.py` | Configuration for the composite (multi-backend) storage. |
| `StorageEffectProvider` | `aquilia/storage/effects.py` | Effect provider that yields ``StorageBackend`` instances from the ``StorageRegistry``. |
| `StorageRegistry` | `aquilia/storage/registry.py` | Named registry of storage backends. |

## Error Handling

Fault/error classes defined here:

`StorageError`, `FileNotFoundError`, `PermissionError`, `StorageFullError`, `BackendUnavailableError`, `StorageIOFault`, `StorageConfigFault`
