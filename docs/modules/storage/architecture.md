# Storage Architecture

## Runtime Role

The async storage abstraction for local, memory, S3, GCS, Azure Blob, SFTP, composite storage, registry, configs, effects, metadata, and subsystem lifecycle.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 12 |
| `typing` | 12 |
| `base` | 10 |
| `collections` | 9 |
| `configs` | 9 |
| `backends` | 7 |
| `datetime` | 5 |
| `asyncio` | 4 |
| `contextlib` | 4 |
| `os` | 3 |
| `aquilia` | 2 |
| `dataclasses` | 2 |
| `effects` | 2 |
| `filesystem` | 2 |
| `logging` | 2 |
| `pathlib` | 2 |
| `registry` | 2 |
| `abc` | 1 |
| `azure` | 1 |
| `composite` | 1 |
| `fnmatch` | 1 |
| `gcs` | 1 |
| `health` | 1 |
| `importlib` | 1 |
| `json` | 1 |
| `local` | 1 |
| `memory` | 1 |
| `mimetypes` | 1 |
| `s3` | 1 |
| `sftp` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
