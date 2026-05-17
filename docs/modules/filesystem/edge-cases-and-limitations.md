# Filesystem Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `FileSystemFault` | `aquilia/filesystem/_errors.py` | Base class for all filesystem faults. |
| `FileNotFoundFault` | `aquilia/filesystem/_errors.py` | Raised when a file or directory does not exist. |
| `PermissionDeniedFault` | `aquilia/filesystem/_errors.py` | Raised when the process lacks permission for the operation. |
| `FileExistsFault` | `aquilia/filesystem/_errors.py` | Raised when a file already exists and overwrite is not allowed. |
| `IsDirectoryFault` | `aquilia/filesystem/_errors.py` | Raised when a file operation is attempted on a directory. |
| `NotDirectoryFault` | `aquilia/filesystem/_errors.py` | Raised when a directory operation is attempted on a file. |
| `DiskFullFault` | `aquilia/filesystem/_errors.py` | Raised when no space is left on device. |
| `PathTraversalFault` | `aquilia/filesystem/_errors.py` | Raised when a path traversal attack is detected. |
| `PathTooLongFault` | `aquilia/filesystem/_errors.py` | Raised when a path exceeds the configured maximum length. |
| `FileSystemIOFault` | `aquilia/filesystem/_errors.py` | Generic I/O error for unclassified OS errors. |
| `FileClosedFault` | `aquilia/filesystem/_errors.py` | Raised when an operation is attempted on a closed file. |
| `LockAcquisitionError` | `aquilia/filesystem/_lock.py` | Raised when a file lock cannot be acquired. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
