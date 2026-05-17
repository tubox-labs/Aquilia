# Filesystem Architecture

Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/filesystem/__init__.py` | 269 | 0 | 0 | Aquilia Filesystem — High-performance native async file I/O. |
| `aquilia/filesystem/_config.py` | 114 | 1 | 0 | Filesystem Configuration — Typed, frozen dataclass for module settings. |
| `aquilia/filesystem/_directory.py` | 356 | 1 | 7 | Directory Operations — Async wrappers for directory manipulation. |
| `aquilia/filesystem/_errors.py` | 281 | 11 | 1 | Filesystem Errors — Typed fault hierarchy for file operations. |
| `aquilia/filesystem/_handle.py` | 357 | 1 | 0 | Async File Handle — Core I/O primitive for the Aquilia filesystem module. |
| `aquilia/filesystem/_lock.py` | 252 | 2 | 0 | Async File Locking — Advisory file locks for concurrent access safety. |
| `aquilia/filesystem/_metrics.py` | 163 | 1 | 0 | Filesystem Metrics — Lightweight operation counters and latency tracking. |
| `aquilia/filesystem/_ops.py` | 573 | 1 | 9 | Convenience Filesystem Operations — High-level async file I/O functions. |
| `aquilia/filesystem/_path.py` | 525 | 1 | 0 | Async Path — Async equivalent of ``pathlib.Path``. |
| `aquilia/filesystem/_pool.py` | 170 | 1 | 0 | Filesystem Thread Pool — Dedicated executor for blocking file I/O. |
| `aquilia/filesystem/_security.py` | 244 | 0 | 3 | Filesystem Security — Path validation, sanitization, and sandbox enforcement. |
| `aquilia/filesystem/_service.py` | 495 | 1 | 0 | FileSystem Service — DI-injectable facade for async file operations. |
| `aquilia/filesystem/_streaming.py` | 308 | 2 | 2 | Streaming Pipeline — High-performance async file streaming. |
| `aquilia/filesystem/_tempfile.py` | 210 | 2 | 0 | Async Temporary Files — Secure temporary file and directory management. |

## Internal Shape

`filesystem` has 14 Python files, 25 public classes, 22 public module-level functions, and 20 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `._config` | 9 |
| `._errors` | 8 |
| `._pool` | 8 |
| `._handle` | 3 |
| `._metrics` | 3 |
| `._directory` | 1 |
| `._ops` | 1 |
| `._security` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 14 |
| `pathlib` | 8 |
| `os` | 7 |
| `collections` | 6 |
| `contextlib` | 4 |
| `dataclasses` | 4 |
| `typing` | 4 |
| `shutil` | 3 |
| `time` | 3 |
| `asyncio` | 2 |
| `builtins` | 1 |
| `concurrent` | 1 |
| `errno` | 1 |
| `logging` | 1 |
| `sys` | 1 |
| `tempfile` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `FileSystemConfig` | `aquilia/filesystem/_config.py` | Configuration for the Aquilia filesystem module. |

## Error Handling

Fault/error classes defined here:

`FileSystemFault`, `FileNotFoundFault`, `PermissionDeniedFault`, `FileExistsFault`, `IsDirectoryFault`, `NotDirectoryFault`, `DiskFullFault`, `PathTraversalFault`, `PathTooLongFault`, `FileSystemIOFault`, `FileClosedFault`, `LockAcquisitionError`
