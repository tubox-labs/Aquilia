# Filesystem Documentation

Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade.

## Coverage Snapshot

- Source files: 14
- Source lines: 4317
- Public classes: 25
- Public module functions: 22
- Constants/module flags: 20
- Public exports in `__all__`: 48

## Source Files Read

- `aquilia/filesystem/__init__.py`: Aquilia Filesystem — High-performance native async file I/O.
- `aquilia/filesystem/_config.py`: Filesystem Configuration — Typed, frozen dataclass for module settings.
- `aquilia/filesystem/_directory.py`: Directory Operations — Async wrappers for directory manipulation.
- `aquilia/filesystem/_errors.py`: Filesystem Errors — Typed fault hierarchy for file operations.
- `aquilia/filesystem/_handle.py`: Async File Handle — Core I/O primitive for the Aquilia filesystem module.
- `aquilia/filesystem/_lock.py`: Async File Locking — Advisory file locks for concurrent access safety.
- `aquilia/filesystem/_metrics.py`: Filesystem Metrics — Lightweight operation counters and latency tracking.
- `aquilia/filesystem/_ops.py`: Convenience Filesystem Operations — High-level async file I/O functions.
- `aquilia/filesystem/_path.py`: Async Path — Async equivalent of ``pathlib.Path``.
- `aquilia/filesystem/_pool.py`: Filesystem Thread Pool — Dedicated executor for blocking file I/O.
- `aquilia/filesystem/_security.py`: Filesystem Security — Path validation, sanitization, and sandbox enforcement.
- `aquilia/filesystem/_service.py`: FileSystem Service — DI-injectable facade for async file operations.
- `aquilia/filesystem/_streaming.py`: Streaming Pipeline — High-performance async file streaming.
- `aquilia/filesystem/_tempfile.py`: Async Temporary Files — Secure temporary file and directory management.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
