# filesystem Module

## Purpose

Native async filesystem service. Use this module for secure file paths, async file handles, locking, streaming, temp files, pools, metrics, and traversal-resistant operations.

## Source Coverage

- Python files: 14
- Public classes: 25
- Dataclasses: 4
- Enums: 0
- Public functions: 22

## How It Fits In Aquilia

1. Import the package from `aquilia.filesystem` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `FileSystemConfig` | `aquilia/filesystem/_config.py` | Configuration for the Aquilia filesystem module. |
| `DirEntry` | `aquilia/filesystem/_directory.py` | Async-friendly directory entry (mirrors ``os.DirEntry``). |
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
| `AsyncFile` | `aquilia/filesystem/_handle.py` | Async file handle with buffered I/O. |
| `LockAcquisitionError` | `aquilia/filesystem/_lock.py` | Raised when a file lock cannot be acquired. |
| `AsyncFileLock` | `aquilia/filesystem/_lock.py` | Async advisory file lock. |
| `FileSystemMetrics` | `aquilia/filesystem/_metrics.py` | Aggregated filesystem operation metrics. |
| `FileStat` | `aquilia/filesystem/_ops.py` | File status information. |
| `AsyncPath` | `aquilia/filesystem/_path.py` | Async filesystem path with I/O delegation to the thread pool. |
| `FileSystemPool` | `aquilia/filesystem/_pool.py` | Dedicated thread pool for filesystem operations. |
| `FileSystem` | `aquilia/filesystem/_service.py` | High-level async filesystem service. |
| `AsyncFileStream` | `aquilia/filesystem/_streaming.py` | Chunked async iterator for streaming file reads. |
| `AsyncWriteStream` | `aquilia/filesystem/_streaming.py` | Buffered async writer for streaming file writes. |
| `AsyncTemporaryFile` | `aquilia/filesystem/_tempfile.py` | Async temporary file with automatic cleanup. |
| `AsyncTemporaryDirectory` | `aquilia/filesystem/_tempfile.py` | Async temporary directory with automatic cleanup. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `list_dir` | `aquilia/filesystem/_directory.py` | List directory contents (names only). |
| `scan_dir` | `aquilia/filesystem/_directory.py` | Scan directory contents with metadata. |
| `make_dir` | `aquilia/filesystem/_directory.py` | Create a directory. |
| `remove_dir` | `aquilia/filesystem/_directory.py` | Remove an empty directory. |
| `remove_tree` | `aquilia/filesystem/_directory.py` | Recursively remove a directory tree. |
| `copy_tree` | `aquilia/filesystem/_directory.py` | Recursively copy a directory tree. |
| `walk` | `aquilia/filesystem/_directory.py` | Recursively walk a directory tree. |
| `wrap_os_error` | `aquilia/filesystem/_errors.py` | Convert an OS-level exception to a typed ``FileSystemFault``. |
| `async_open` | `aquilia/filesystem/_ops.py` | Open a file asynchronously. |
| `read_file` | `aquilia/filesystem/_ops.py` | Read the entire contents of a file. |
| `write_file` | `aquilia/filesystem/_ops.py` | Write data to a file. |
| `append_file` | `aquilia/filesystem/_ops.py` | Append data to a file.  Creates the file if it doesn't exist. |
| `copy_file` | `aquilia/filesystem/_ops.py` | Copy a file from *src* to *dst*. |
| `move_file` | `aquilia/filesystem/_ops.py` | Move (rename) a file from *src* to *dst*. |
| `delete_file` | `aquilia/filesystem/_ops.py` | Delete a file. |
| `file_exists` | `aquilia/filesystem/_ops.py` | Check if a file exists. |
| `file_stat` | `aquilia/filesystem/_ops.py` | Get file status (stat) information. |
| `validate_path` | `aquilia/filesystem/_security.py` | Validate and resolve a filesystem path through multiple security layers. |
| `validate_relative_path` | `aquilia/filesystem/_security.py` | Validate a relative path/filename (no sandbox, just safety checks). |
| `sanitize_filename` | `aquilia/filesystem/_security.py` | Sanitize a filename for safe storage. |
| `stream_copy` | `aquilia/filesystem/_streaming.py` | Copy a file via streaming. |
| `stream_read` | `aquilia/filesystem/_streaming.py` | Stream a file in chunks. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/filesystem/__init__.py` | Aquilia Filesystem - High-performance native async file I/O. |
| `aquilia/filesystem/_config.py` | Filesystem Configuration - Typed, frozen dataclass for module settings. |
| `aquilia/filesystem/_directory.py` | Directory Operations - Async wrappers for directory manipulation. |
| `aquilia/filesystem/_errors.py` | Filesystem Errors - Typed fault hierarchy for file operations. |
| `aquilia/filesystem/_handle.py` | Async File Handle - Core I/O primitive for the Aquilia filesystem module. |
| `aquilia/filesystem/_lock.py` | Async File Locking - Advisory file locks for concurrent access safety. |
| `aquilia/filesystem/_metrics.py` | Filesystem Metrics - Lightweight operation counters and latency tracking. |
| `aquilia/filesystem/_ops.py` | Convenience Filesystem Operations - High-level async file I/O functions. |
| `aquilia/filesystem/_path.py` | Async Path - Async equivalent of ``pathlib.Path``. |
| `aquilia/filesystem/_pool.py` | Filesystem Thread Pool - Dedicated executor for blocking file I/O. |
| `aquilia/filesystem/_security.py` | Filesystem Security - Path validation, sanitization, and sandbox enforcement. |
| `aquilia/filesystem/_service.py` | FileSystem Service - DI-injectable facade for async file operations. |
| `aquilia/filesystem/_streaming.py` | Streaming Pipeline - High-performance async file streaming. |
| `aquilia/filesystem/_tempfile.py` | Async Temporary Files - Secure temporary file and directory management. |

## Testing Pointers

Search `tests/` for `filesystem` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
