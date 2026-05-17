# Filesystem Documentation

This directory is the professional documentation set for `filesystem`. It is implementation-driven and aligned with the current source files under `aquilia/filesystem`.

## What This Covers

The async native filesystem layer with secure path handling, async file handles, directory operations, streaming, locks, temporary files, pools, and metrics.

## Source Files Read

- `aquilia/filesystem/__init__.py`: Aquilia Filesystem - High-performance native async file I/O.
- `aquilia/filesystem/_config.py`: Filesystem Configuration - Typed, frozen dataclass for module settings.
- `aquilia/filesystem/_directory.py`: Directory Operations - Async wrappers for directory manipulation.
- `aquilia/filesystem/_errors.py`: Filesystem Errors - Typed fault hierarchy for file operations.
- `aquilia/filesystem/_handle.py`: Async File Handle - Core I/O primitive for the Aquilia filesystem module.
- `aquilia/filesystem/_lock.py`: Async File Locking - Advisory file locks for concurrent access safety.
- `aquilia/filesystem/_metrics.py`: Filesystem Metrics - Lightweight operation counters and latency tracking.
- `aquilia/filesystem/_ops.py`: Convenience Filesystem Operations - High-level async file I/O functions.
- `aquilia/filesystem/_path.py`: Async Path - Async equivalent of ``pathlib.Path``.
- `aquilia/filesystem/_pool.py`: Filesystem Thread Pool - Dedicated executor for blocking file I/O.
- `aquilia/filesystem/_security.py`: Filesystem Security - Path validation, sanitization, and sandbox enforcement.
- `aquilia/filesystem/_service.py`: FileSystem Service - DI-injectable facade for async file operations.
- `aquilia/filesystem/_streaming.py`: Streaming Pipeline - High-performance async file streaming.
- `aquilia/filesystem/_tempfile.py`: Async Temporary Files - Secure temporary file and directory management.

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
- Public classes: 25
- Configuration or dataclass-like types: 4
- Public functions: 22
- Constants detected: 19

## Fast Start

```python
from aquilia.filesystem import FileSystemConfig, FileSystemService

service = FileSystemService(FileSystemConfig(root="var/data"))
await service.write_bytes("reports/today.txt", b"ready")
content = await service.read_bytes("reports/today.txt")
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
