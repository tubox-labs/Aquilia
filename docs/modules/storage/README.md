# Storage Documentation

This directory is the professional documentation set for `storage`. It is implementation-driven and aligned with the current source files under `aquilia/storage`.

## What This Covers

The async storage abstraction for local, memory, S3, GCS, Azure Blob, SFTP, composite storage, registry, configs, effects, metadata, and subsystem lifecycle.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 28
- Configuration or dataclass-like types: 9
- Public functions: 2
- Constants detected: 3

## Fast Start

```python
from aquilia.storage import LocalConfig, LocalStorage

storage = LocalStorage(LocalConfig(root="var/uploads"))
await storage.save("avatars/ada.txt", b"profile data", content_type="text/plain")
file = await storage.open("avatars/ada.txt")
metadata = await storage.stat("avatars/ada.txt")
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
