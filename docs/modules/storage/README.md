# storage Module

## Purpose

Async storage abstraction. Use this module for local, memory, S3, GCS, Azure Blob, SFTP, composite storage, metadata, registry, effects, and subsystem startup.

## Source Coverage

- Python files: 14
- Public classes: 28
- Dataclasses: 9
- Enums: 0
- Public functions: 2

## How It Fits In Aquilia

1. Import the package from `aquilia.storage` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `StorageError` | `aquilia/storage/base.py` | Base fault for all storage operations. |
| `FileNotFoundError` | `aquilia/storage/base.py` | Raised when a file does not exist in the storage backend. |
| `PermissionError` | `aquilia/storage/base.py` | Raised when the caller lacks permission for the operation. |
| `StorageFullError` | `aquilia/storage/base.py` | Raised when the storage quota is exceeded. |
| `BackendUnavailableError` | `aquilia/storage/base.py` | Raised when the storage backend is unreachable or not configured. |
| `StorageIOFault` | `aquilia/storage/base.py` | Raised on I/O operation errors (closed file, wrong mode). |
| `StorageConfigFault` | `aquilia/storage/base.py` | Raised on storage configuration / registry errors. |
| `StorageMetadata` | `aquilia/storage/base.py` | Immutable metadata for a stored file. |
| `StorageFile` | `aquilia/storage/base.py` | Async file wrapper returned by ``StorageBackend.open()``. |
| `StorageBackend` | `aquilia/storage/base.py` | Abstract storage backend. |
| `StorageConfig` | `aquilia/storage/configs.py` | Base storage configuration. |
| `LocalConfig` | `aquilia/storage/configs.py` | Configuration for the local filesystem storage backend. |
| `MemoryConfig` | `aquilia/storage/configs.py` | Configuration for the in-memory storage backend (testing). |
| `S3Config` | `aquilia/storage/configs.py` | Configuration for Amazon S3 or S3-compatible storage. |
| `GCSConfig` | `aquilia/storage/configs.py` | Configuration for Google Cloud Storage. |
| `AzureBlobConfig` | `aquilia/storage/configs.py` | Configuration for Azure Blob Storage. |
| `SFTPConfig` | `aquilia/storage/configs.py` | Configuration for SFTP/SSH storage. |
| `CompositeConfig` | `aquilia/storage/configs.py` | Configuration for the composite (multi-backend) storage. |
| `StorageEffectProvider` | `aquilia/storage/effects.py` | Effect provider that yields ``StorageBackend`` instances |
| `StorageRegistry` | `aquilia/storage/registry.py` | Named registry of storage backends. |
| `StorageSubsystem` | `aquilia/storage/subsystem.py` | Subsystem initializer for the Aquilia storage system. |
| `AzureBlobStorage` | `aquilia/storage/backends/azure.py` | Azure Blob Storage backend. |
| `CompositeStorage` | `aquilia/storage/backends/composite.py` | Composite storage that routes files to sub-backends by rules. |
| `GCSStorage` | `aquilia/storage/backends/gcs.py` | Google Cloud Storage backend. |
| `LocalStorage` | `aquilia/storage/backends/local.py` | Local filesystem storage backend. |
| `MemoryStorage` | `aquilia/storage/backends/memory.py` | In-memory storage backend. |
| `S3Storage` | `aquilia/storage/backends/s3.py` | Amazon S3 / S3-compatible storage backend. |
| `SFTPStorage` | `aquilia/storage/backends/sftp.py` | SFTP storage backend. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `config_from_dict` | `aquilia/storage/configs.py` | Instantiate a typed StorageConfig from a raw dict. |
| `create_backend` | `aquilia/storage/registry.py` | Instantiate a ``StorageBackend`` from a ``StorageConfig``. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/storage/__init__.py` | Aquilia Storage -- Production-grade, async-first file storage abstraction. |
| `aquilia/storage/backends/__init__.py` | Storage Backends -- concrete StorageBackend implementations. |
| `aquilia/storage/backends/azure.py` | Azure Blob Storage Backend. |
| `aquilia/storage/backends/composite.py` | Composite / Multi-Backend Storage. |
| `aquilia/storage/backends/gcs.py` | Google Cloud Storage Backend. |
| `aquilia/storage/backends/local.py` | Local Filesystem Storage Backend. |
| `aquilia/storage/backends/memory.py` | In-Memory Storage Backend. |
| `aquilia/storage/backends/s3.py` | Amazon S3 / S3-Compatible Storage Backend. |
| `aquilia/storage/backends/sftp.py` | SFTP / SSH Storage Backend. |
| `aquilia/storage/base.py` | Storage Base -- Abstract backend contract and core types. |
| `aquilia/storage/configs.py` | Storage Configs -- Typed configuration dataclasses for each backend. |
| `aquilia/storage/effects.py` | Storage Effect Provider -- Bridges storage into the Aquilia Effect system. |
| `aquilia/storage/registry.py` | Storage Registry -- Named backend registry. |
| `aquilia/storage/subsystem.py` | Storage Subsystem -- Aquilia boot lifecycle integration for storage. |

## Testing Pointers

Search `tests/` for `storage` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
