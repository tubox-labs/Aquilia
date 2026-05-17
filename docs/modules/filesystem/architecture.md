# Filesystem Architecture

## Runtime Role

The async native filesystem layer with secure path handling, async file handles, directory operations, streaming, locks, temporary files, pools, and metrics.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 14 |
| `_config` | 9 |
| `_errors` | 8 |
| `_pool` | 8 |
| `pathlib` | 8 |
| `os` | 7 |
| `collections` | 6 |
| `contextlib` | 4 |
| `dataclasses` | 4 |
| `typing` | 4 |
| `_handle` | 3 |
| `_metrics` | 3 |
| `shutil` | 3 |
| `time` | 3 |
| `asyncio` | 2 |
| `_directory` | 1 |
| `_ops` | 1 |
| `_security` | 1 |
| `aquilia` | 1 |
| `builtins` | 1 |
| `concurrent` | 1 |
| `errno` | 1 |
| `logging` | 1 |
| `sys` | 1 |
| `tempfile` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
