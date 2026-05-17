# Storage Documentation

Async storage abstraction with local, memory, S3, GCS, Azure, SFTP, composite backends, registry, configs, effects, and lifecycle subsystem.

## Coverage Snapshot

- Source files: 14
- Source lines: 3166
- Public classes: 28
- Public module functions: 2
- Constants/module flags: 5
- Public exports in `__all__`: 29

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

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
