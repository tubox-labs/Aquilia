# Storage Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `StorageError` | `aquilia/storage/base.py` | Base fault for all storage operations. |
| `FileNotFoundError` | `aquilia/storage/base.py` | Raised when a file does not exist in the storage backend. |
| `PermissionError` | `aquilia/storage/base.py` | Raised when the caller lacks permission for the operation. |
| `StorageFullError` | `aquilia/storage/base.py` | Raised when the storage quota is exceeded. |
| `BackendUnavailableError` | `aquilia/storage/base.py` | Raised when the storage backend is unreachable or not configured. |
| `StorageIOFault` | `aquilia/storage/base.py` | Raised on I/O operation errors (closed file, wrong mode). |
| `StorageConfigFault` | `aquilia/storage/base.py` | Raised on storage configuration / registry errors. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/storage/__init__.py`: Aquilia Storage -- Production-grade, async-first file storage abstraction.
- `aquilia/storage/backends/__init__.py`: Storage Backends -- concrete StorageBackend implementations.
- `aquilia/storage/backends/azure.py`: Azure Blob Storage Backend.
- `aquilia/storage/backends/composite.py`: Composite / Multi-Backend Storage.
- `aquilia/storage/backends/gcs.py`: Google Cloud Storage Backend.
- `aquilia/storage/backends/local.py`: Local Filesystem Storage Backend.
- `aquilia/storage/backends/memory.py`: In-Memory Storage Backend.
- `aquilia/storage/backends/s3.py`: Amazon S3 / S3-Compatible Storage Backend.
- `aquilia/storage/backends/sftp.py`: SFTP / SSH Storage Backend.
- `aquilia/storage/base.py`: Storage Base -- Abstract backend contract and core types.
- `aquilia/storage/configs.py`: Storage Configs -- Typed configuration dataclasses for each backend.
- `aquilia/storage/effects.py`: Storage Effect Provider -- Bridges storage into the Aquilia Effect system.
- `aquilia/storage/registry.py`: Storage Registry -- Named backend registry.
- `aquilia/storage/subsystem.py`: Storage Subsystem -- Aquilia boot lifecycle integration for storage.
