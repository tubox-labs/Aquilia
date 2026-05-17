# Filesystem API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`AsyncFile`, `AsyncFileLock`, `AsyncFileStream`, `AsyncPath`, `AsyncTemporaryDirectory`, `AsyncTemporaryFile`, `AsyncWriteStream`, `DirEntry`, `DiskFullFault`, `FileClosedFault`, `FileExistsFault`, `FileNotFoundFault`, `FileStat`, `FileSystem`, `FileSystemConfig`, `FileSystemFault`, `FileSystemIOFault`, `FileSystemMetrics`, `FileSystemPool`, `IsDirectoryFault`, `LockAcquisitionError`, `NotDirectoryFault`, `PathTooLongFault`, `PathTraversalFault`, `PermissionDeniedFault`, `append_file`, `async_open`, `async_tempdir`, `async_tempfile`, `copy_file`, `copy_tree`, `delete_file`, `file_exists`, `file_stat`, `list_dir`, `make_dir`, `move_file`, `read_file`, `remove_dir`, `remove_tree`, `sanitize_filename`, `scan_dir`, `stream_copy`, `stream_read`, `validate_path`, `walk`, `wrap_os_error`, `write_file`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `FileSystemConfig` | `aquilia/filesystem/_config.py` | object | Configuration for the Aquilia filesystem module. |
| `DirEntry` | `aquilia/filesystem/_directory.py` | object | Async-friendly directory entry (mirrors ``os.DirEntry``). |
| `FileSystemFault` | `aquilia/filesystem/_errors.py` | Fault | Base class for all filesystem faults. |
| `FileNotFoundFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a file or directory does not exist. |
| `PermissionDeniedFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when the process lacks permission for the operation. |
| `FileExistsFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a file already exists and overwrite is not allowed. |
| `IsDirectoryFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a file operation is attempted on a directory. |
| `NotDirectoryFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a directory operation is attempted on a file. |
| `DiskFullFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when no space is left on device. |
| `PathTraversalFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a path traversal attack is detected. |
| `PathTooLongFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when a path exceeds the configured maximum length. |
| `FileSystemIOFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Generic I/O error for unclassified OS errors. |
| `FileClosedFault` | `aquilia/filesystem/_errors.py` | FileSystemFault | Raised when an operation is attempted on a closed file. |
| `AsyncFile` | `aquilia/filesystem/_handle.py` | object | Async file handle with buffered I/O. |
| `LockAcquisitionError` | `aquilia/filesystem/_lock.py` | FileSystemFault | Raised when a file lock cannot be acquired. |
| `AsyncFileLock` | `aquilia/filesystem/_lock.py` | object | Async advisory file lock. |
| `FileSystemMetrics` | `aquilia/filesystem/_metrics.py` | object | Aggregated filesystem operation metrics. |
| `FileStat` | `aquilia/filesystem/_ops.py` | object | File status information. |
| `AsyncPath` | `aquilia/filesystem/_path.py` | object | Async filesystem path with I/O delegation to the thread pool. |
| `FileSystemPool` | `aquilia/filesystem/_pool.py` | object | Dedicated thread pool for filesystem operations. |
| `FileSystem` | `aquilia/filesystem/_service.py` | object | High-level async filesystem service. |
| `AsyncFileStream` | `aquilia/filesystem/_streaming.py` | object | Chunked async iterator for streaming file reads. |
| `AsyncWriteStream` | `aquilia/filesystem/_streaming.py` | object | Buffered async writer for streaming file writes. |
| `AsyncTemporaryFile` | `aquilia/filesystem/_tempfile.py` | object | Async temporary file with automatic cleanup. |
| `AsyncTemporaryDirectory` | `aquilia/filesystem/_tempfile.py` | object | Async temporary directory with automatic cleanup. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `list_dir` | `aquilia/filesystem/_directory.py` | `async def list_dir(path: str \| Path, *, pool: FileSystemPool \| None=None)` | List directory contents (names only). |
| `scan_dir` | `aquilia/filesystem/_directory.py` | `async def scan_dir(path: str \| Path, *, pool: FileSystemPool \| None=None)` | Scan directory contents with metadata. |
| `make_dir` | `aquilia/filesystem/_directory.py` | `async def make_dir(path: str \| Path, *, mode: int=511, parents: bool=False, exist_ok: bool=False, pool: FileSystemPool \| None=None)` | Create a directory. |
| `remove_dir` | `aquilia/filesystem/_directory.py` | `async def remove_dir(path: str \| Path, *, pool: FileSystemPool \| None=None)` | Remove an empty directory. |
| `remove_tree` | `aquilia/filesystem/_directory.py` | `async def remove_tree(path: str \| Path, *, ignore_errors: bool=False, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None)` | Recursively remove a directory tree. |
| `copy_tree` | `aquilia/filesystem/_directory.py` | `async def copy_tree(src: str \| Path, dst: str \| Path, *, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, symlinks: bool=False, dirs_exist_ok: bool=False)` | Recursively copy a directory tree. |
| `walk` | `aquilia/filesystem/_directory.py` | `async def walk(top: str \| Path, *, topdown: bool=True, followlinks: bool=False, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None)` | Recursively walk a directory tree. |
| `wrap_os_error` | `aquilia/filesystem/_errors.py` | `def wrap_os_error(exc: BaseException, operation: str='', path: str='')` | Convert an OS-level exception to a typed ``FileSystemFault``. |
| `async_open` | `aquilia/filesystem/_ops.py` | `def async_open(path: str \| Path, mode: str='r', buffering: int=-1, encoding: str \| None=None, errors: str \| None=None, newline: str \| None=None, *, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, metrics: FileSystemMetrics \| None=None, sandbox: str \| Path \| None=None)` | Open a file asynchronously. |
| `read_file` | `aquilia/filesystem/_ops.py` | `async def read_file(path: str \| Path, *, encoding: str \| None=None, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, metrics: FileSystemMetrics \| None=None, sandbox: str \| Path \| None=None)` | Read the entire contents of a file. |
| `write_file` | `aquilia/filesystem/_ops.py` | `async def write_file(path: str \| Path, data: str \| bytes, *, encoding: str='utf-8', atomic: bool \| None=None, mkdir: bool=False, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, metrics: FileSystemMetrics \| None=None, sandbox: str \| Path \| None=None)` | Write data to a file. |
| `append_file` | `aquilia/filesystem/_ops.py` | `async def append_file(path: str \| Path, data: str \| bytes, *, encoding: str='utf-8', pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, metrics: FileSystemMetrics \| None=None, sandbox: str \| Path \| None=None)` | Append data to a file.  Creates the file if it doesn't exist. |
| `copy_file` | `aquilia/filesystem/_ops.py` | `async def copy_file(src: str \| Path, dst: str \| Path, *, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Copy a file from *src* to *dst*. |
| `move_file` | `aquilia/filesystem/_ops.py` | `async def move_file(src: str \| Path, dst: str \| Path, *, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Move (rename) a file from *src* to *dst*. |
| `delete_file` | `aquilia/filesystem/_ops.py` | `async def delete_file(path: str \| Path, *, missing_ok: bool=False, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Delete a file. |
| `file_exists` | `aquilia/filesystem/_ops.py` | `async def file_exists(path: str \| Path, *, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Check if a file exists. |
| `file_stat` | `aquilia/filesystem/_ops.py` | `async def file_stat(path: str \| Path, *, follow_symlinks: bool \| None=None, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Get file status (stat) information. |
| `validate_path` | `aquilia/filesystem/_security.py` | `def validate_path(path: str \| Path, *, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None, operation: str='')` | Validate and resolve a filesystem path through multiple security layers. |
| `validate_relative_path` | `aquilia/filesystem/_security.py` | `def validate_relative_path(name: str, *, config: FileSystemConfig \| None=None, operation: str='')` | Validate a relative path/filename (no sandbox, just safety checks). |
| `sanitize_filename` | `aquilia/filesystem/_security.py` | `def sanitize_filename(filename: str, *, max_length: int=255, replacement: str='_')` | Sanitize a filename for safe storage. |
| `stream_copy` | `aquilia/filesystem/_streaming.py` | `async def stream_copy(src: str \| Path, dst: str \| Path, *, chunk_size: int=65536, pool: FileSystemPool \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Copy a file via streaming. |
| `stream_read` | `aquilia/filesystem/_streaming.py` | `async def stream_read(path: str \| Path, *, chunk_size: int=65536, pool: FileSystemPool \| None=None, offset: int=0, end: int \| None=None, config: FileSystemConfig \| None=None, sandbox: str \| Path \| None=None)` | Stream a file in chunks. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_CONFIG_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemConfig'}` |
| `_ERROR_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemFault', 'FileNotFoundFault', 'PermissionDeniedFault', 'FileExistsFault', 'IsDirectoryFault', 'NotDirectoryFault', 'DiskFullFault', 'PathTraversalFault', 'PathTooLongFault', 'FileSystemIOFault', 'FileClosedFault', 'wrap_os_error'}` |
| `_SECURITY_NAMES` | `aquilia/filesystem/__init__.py` | `{'validate_path', 'sanitize_filename'}` |
| `_POOL_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemPool'}` |
| `_METRICS_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemMetrics'}` |
| `_HANDLE_NAMES` | `aquilia/filesystem/__init__.py` | `{'AsyncFile'}` |
| `_PATH_NAMES` | `aquilia/filesystem/__init__.py` | `{'AsyncPath'}` |
| `_OPS_NAMES` | `aquilia/filesystem/__init__.py` | `{'async_open', 'read_file', 'write_file', 'append_file', 'copy_file', 'move_file', 'delete_file', 'file_exists', 'file_stat', 'FileStat'}` |
| `_STREAMING_NAMES` | `aquilia/filesystem/__init__.py` | `{'AsyncFileStream', 'AsyncWriteStream', 'stream_read', 'stream_copy'}` |
| `_DIR_NAMES` | `aquilia/filesystem/__init__.py` | `{'list_dir', 'scan_dir', 'make_dir', 'remove_dir', 'remove_tree', 'copy_tree', 'walk', 'DirEntry'}` |
| `_TEMP_NAMES` | `aquilia/filesystem/__init__.py` | `{'AsyncTemporaryFile', 'AsyncTemporaryDirectory', 'async_tempfile', 'async_tempdir'}` |
| `_LOCK_NAMES` | `aquilia/filesystem/__init__.py` | `{'AsyncFileLock', 'LockAcquisitionError'}` |
| `FS_DOMAIN` | `aquilia/filesystem/_errors.py` | `FaultDomain.IO` |
| `T` | `aquilia/filesystem/_pool.py` | `TypeVar('T')` |
| `_UNSAFE_CHARS` | `aquilia/filesystem/_security.py` | `frozenset('<>:"\|?*\x00')` |
| `_CONTROL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset((chr(c) for c in range(32)))` |
| `_SHELL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset(';\|&$`(){}[]!~')` |
| `_WINDOWS_RESERVED` | `aquilia/filesystem/_security.py` | `frozenset({'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))})` |
| `_DANGEROUS` | `aquilia/filesystem/_security.py` | `_UNSAFE_CHARS \| _CONTROL_CHARS \| _SHELL_CHARS \| frozenset('/\\')` |

## Detailed Classes And Methods

### `FileSystemConfig`

- Source: `aquilia/filesystem/_config.py`
- Bases: `object`
- Summary: Configuration for the Aquilia filesystem module.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `min_pool_threads` | `int` | `2` |
| `max_pool_threads` | `int` | `8` |
| `write_buffer_size` | `int` | `65536` |
| `default_chunk_size` | `int` | `65536` |
| `max_path_length` | `int` | `1024` |
| `follow_symlinks` | `bool` | `False` |
| `sandbox_root` | `str \| None` | `None` |
| `atomic_writes` | `bool` | `True` |
| `fsync_on_write` | `bool` | `False` |
| `enable_metrics` | `bool` | `True` |
| `temp_dir` | `str \| None` | `None` |
| `max_recursion_depth` | `int` | `100` |
| `max_filename_length` | `int` | `255` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `effective_max_pool_threads` | `def effective_max_pool_threads(self)` | Return the effective max pool thread count, accounting for auto-detection when set to 0. |
| `from_dict` | `def from_dict(cls, data: dict)` | Create config from a dictionary (e.g. from workspace config). |

### `DirEntry`

- Source: `aquilia/filesystem/_directory.py`
- Bases: `object`
- Summary: Async-friendly directory entry (mirrors ``os.DirEntry``).
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `path` | `str` | `` |
| `is_file_cached` | `bool` | `` |
| `is_dir_cached` | `bool` | `` |
| `is_symlink_cached` | `bool` | `` |
| `inode` | `int` | `0` |

### `FileSystemFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `Fault`
- Summary: Base class for all filesystem faults.

### `FileNotFoundFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file or directory does not exist.

### `PermissionDeniedFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when the process lacks permission for the operation.

### `FileExistsFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file already exists and overwrite is not allowed.

### `IsDirectoryFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file operation is attempted on a directory.

### `NotDirectoryFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a directory operation is attempted on a file.

### `DiskFullFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when no space is left on device.

### `PathTraversalFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a path traversal attack is detected.

### `PathTooLongFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a path exceeds the configured maximum length.

### `FileSystemIOFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Generic I/O error for unclassified OS errors.

### `FileClosedFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when an operation is attempted on a closed file.

### `AsyncFile`

- Source: `aquilia/filesystem/_handle.py`
- Bases: `object`
- Summary: Async file handle with buffered I/O.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | The file path/name. |
| `mode` | `def mode(self)` | The mode the file was opened with. |
| `closed` | `def closed(self)` | Whether the file has been closed. |
| `encoding` | `def encoding(self)` | Text encoding (None for binary files). |
| `read` | `async def read(self, size: int=-1)` | Read up to ``size`` bytes/characters. |
| `readline` | `async def readline(self)` | Read a single line. |
| `readlines` | `async def readlines(self)` | Read all lines into a list. |
| `readinto` | `async def readinto(self, buffer: bytearray)` | Read bytes into a pre-allocated buffer (binary mode only). |
| `write` | `async def write(self, data: bytes \| str)` | Write data to the file. |
| `writelines` | `async def writelines(self, lines: Iterable[bytes \| str])` | Write an iterable of lines. |
| `flush` | `async def flush(self)` | Flush write buffer and OS buffers. |
| `truncate` | `async def truncate(self, size: int \| None=None)` | Truncate the file to at most ``size`` bytes. |
| `seek` | `async def seek(self, offset: int, whence: int=0)` | Move the file position. |
| `tell` | `async def tell(self)` | Return the current file position. |
| `close` | `async def close(self)` | Flush buffers and close the underlying file descriptor. |
| `chunks` | `async def chunks(self, chunk_size: int=65536)` | Iterate over the file in fixed-size chunks. |

### `LockAcquisitionError`

- Source: `aquilia/filesystem/_lock.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file lock cannot be acquired.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `timeout` | `def timeout(self)` |  |

### `AsyncFileLock`

- Source: `aquilia/filesystem/_lock.py`
- Bases: `object`
- Summary: Async advisory file lock.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `path` | `def path(self)` | Lock file path. |
| `is_locked` | `def is_locked(self)` | Whether the lock is currently held. |
| `acquire` | `async def acquire(self)` | Acquire the file lock. |
| `release` | `async def release(self)` | Release the file lock. |

### `FileSystemMetrics`

- Source: `aquilia/filesystem/_metrics.py`
- Bases: `object`
- Summary: Aggregated filesystem operation metrics.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `reads` | `int` | `0` |
| `writes` | `int` | `0` |
| `deletes` | `int` | `0` |
| `copies` | `int` | `0` |
| `moves` | `int` | `0` |
| `stats` | `int` | `0` |
| `directory_ops` | `int` | `0` |
| `errors` | `int` | `0` |
| `bytes_read` | `int` | `0` |
| `bytes_written` | `int` | `0` |
| `read_latency_ns` | `int` | `0` |
| `write_latency_ns` | `int` | `0` |
| `pool_submissions` | `int` | `0` |
| `pool_peak_active` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `record_read` | `def record_read(self, bytes_count: int, elapsed_ns: int)` | Record a completed read operation. |
| `record_write` | `def record_write(self, bytes_count: int, elapsed_ns: int)` | Record a completed write operation. |
| `record_error` | `def record_error(self)` | Record a failed operation. |
| `to_dict` | `def to_dict(self)` | Export metrics as a dictionary. |
| `reset` | `def reset(self)` | Reset all counters to zero.  Useful for testing. |

### `FileStat`

- Source: `aquilia/filesystem/_ops.py`
- Bases: `object`
- Summary: File status information.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `size` | `int` | `` |
| `mode` | `int` | `` |
| `uid` | `int` | `` |
| `gid` | `int` | `` |
| `atime_ns` | `int` | `` |
| `mtime_ns` | `int` | `` |
| `ctime_ns` | `int` | `` |
| `is_file` | `bool` | `` |
| `is_dir` | `bool` | `` |
| `is_symlink` | `bool` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `atime` | `def atime(self)` |  |
| `mtime` | `def mtime(self)` |  |
| `ctime` | `def ctime(self)` |  |

### `AsyncPath`

- Source: `aquilia/filesystem/_path.py`
- Bases: `object`
- Summary: Async filesystem path with I/O delegation to the thread pool.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | The final component of the path. |
| `stem` | `def stem(self)` | The final component without suffix. |
| `suffix` | `def suffix(self)` | The file extension. |
| `suffixes` | `def suffixes(self)` | All file extensions. |
| `parent` | `def parent(self)` | The parent directory. |
| `parents` | `def parents(self)` | All ancestor directories. |
| `parts` | `def parts(self)` | Path components as a tuple. |
| `anchor` | `def anchor(self)` | The drive + root (e.g. '/' or 'C:\'). |
| `drive` | `def drive(self)` | The drive letter (Windows) or empty string. |
| `root` | `def root(self)` | The root of the path. |
| `is_absolute` | `def is_absolute(self)` | Whether the path is absolute. |
| `is_relative_to` | `def is_relative_to(self, other: str \| Path \| AsyncPath)` | Whether this path is relative to another. |
| `path` | `def path(self)` | Access the underlying ``pathlib.Path``. |
| `with_name` | `def with_name(self, name: str)` | Return a new path with the filename changed. |
| `with_stem` | `def with_stem(self, stem: str)` | Return a new path with the stem changed. |
| `with_suffix` | `def with_suffix(self, suffix: str)` | Return a new path with the suffix changed. |
| `relative_to` | `def relative_to(self, other: str \| Path \| AsyncPath)` | Return a relative version of this path. |
| `resolve` | `def resolve(self)` | Resolve the path to an absolute canonical path. |
| `joinpath` | `def joinpath(self, *others: str \| Path \| AsyncPath)` | Join one or more path components. |
| `exists` | `async def exists(self)` | Check whether the path exists on disk. |
| `is_file` | `async def is_file(self)` | Check whether the path is a regular file. |
| `is_dir` | `async def is_dir(self)` | Check whether the path is a directory. |
| `is_symlink` | `async def is_symlink(self)` | Check whether the path is a symbolic link. |
| `stat` | `async def stat(self)` | Get file status (size, permissions, timestamps, etc.). |
| `lstat` | `async def lstat(self)` | Like ``stat()`` but don't follow symlinks. |
| `read_bytes` | `async def read_bytes(self)` | Read the entire file as bytes. |
| `read_text` | `async def read_text(self, encoding: str='utf-8', errors: str='strict')` | Read the entire file as text. |
| `open` | `async def open(self, mode: str='r', buffering: int=-1, encoding: str \| None=None, errors: str \| None=None, newline: str \| None=None)` | Open the file and return an ``AsyncFile`` handle. |
| `write_bytes` | `async def write_bytes(self, data: bytes)` | Write bytes to the file (creates or overwrites). |
| `write_text` | `async def write_text(self, data: str, encoding: str='utf-8', errors: str \| None=None, newline: str \| None=None)` | Write text to the file (creates or overwrites). |
| `mkdir` | `async def mkdir(self, mode: int=511, parents: bool=False, exist_ok: bool=False)` | Create a directory. |
| `rmdir` | `async def rmdir(self)` | Remove an empty directory. |
| `unlink` | `async def unlink(self, missing_ok: bool=False)` | Remove a file or symbolic link. |
| `rename` | `async def rename(self, target: str \| Path \| AsyncPath)` | Rename/move the file or directory. |
| `replace` | `async def replace(self, target: str \| Path \| AsyncPath)` | Atomically rename, replacing the target if it exists. |
| `touch` | `async def touch(self, mode: int=438, exist_ok: bool=True)` | Create the file (or update its access/modification times). |
| `chmod` | `async def chmod(self, mode: int)` | Change file permissions. |
| `iterdir` | `async def iterdir(self)` | Iterate over directory contents. |
| `glob` | `async def glob(self, pattern: str)` | Glob for matching paths. |
| `rglob` | `async def rglob(self, pattern: str)` | Recursive glob for matching paths. |

### `FileSystemPool`

- Source: `aquilia/filesystem/_pool.py`
- Bases: `object`
- Summary: Dedicated thread pool for filesystem operations.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialized` | `def initialized(self)` | Whether the pool has been initialized. |
| `active_count` | `def active_count(self)` | Number of currently active pool operations. |
| `initialize` | `def initialize(self)` | Create the thread pool. |
| `run` | `async def run(self, fn: Callable[..., T], *args: Any)` | Execute a blocking function in the dedicated pool. |
| `shutdown` | `async def shutdown(self, timeout: float=5.0)` | Drain and shut down the thread pool. |

### `FileSystem`

- Source: `aquilia/filesystem/_service.py`
- Bases: `object`
- Summary: High-level async filesystem service.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `config` | `def config(self)` | Current filesystem configuration. |
| `pool` | `def pool(self)` | The underlying thread pool. |
| `metrics` | `def metrics(self)` | Operation metrics. |
| `open` | `def open(self, path: str \| Path, mode: str='r', buffering: int=-1, encoding: str \| None=None, errors: str \| None=None, newline: str \| None=None, *, sandbox: str \| Path \| None=None)` | Open a file asynchronously. |
| `read_file` | `async def read_file(self, path: str \| Path, *, encoding: str \| None=None, sandbox: str \| Path \| None=None)` | Read entire file contents. |
| `write_file` | `async def write_file(self, path: str \| Path, data: str \| bytes, *, encoding: str='utf-8', atomic: bool \| None=None, mkdir: bool=False, sandbox: str \| Path \| None=None)` | Write data to a file. Returns bytes written. |
| `append_file` | `async def append_file(self, path: str \| Path, data: str \| bytes, *, encoding: str='utf-8', sandbox: str \| Path \| None=None)` | Append data to a file. Returns bytes written. |
| `copy_file` | `async def copy_file(self, src: str \| Path, dst: str \| Path, *, sandbox: str \| Path \| None=None)` | Copy a file. Returns destination path. |
| `move_file` | `async def move_file(self, src: str \| Path, dst: str \| Path, *, sandbox: str \| Path \| None=None)` | Move/rename a file. Returns destination path. |
| `delete_file` | `async def delete_file(self, path: str \| Path, *, missing_ok: bool=False, sandbox: str \| Path \| None=None)` | Delete a file. Returns True if deleted. |
| `file_exists` | `async def file_exists(self, path: str \| Path, *, sandbox: str \| Path \| None=None)` | Check if a file exists. |
| `file_stat` | `async def file_stat(self, path: str \| Path, *, follow_symlinks: bool \| None=None, sandbox: str \| Path \| None=None)` | Get file status information. |
| `stream_read` | `def stream_read(self, path: str \| Path, chunk_size: int \| None=None, offset: int=0, end: int \| None=None, *, sandbox: str \| Path \| None=None)` | Stream file contents in chunks. |
| `stream_copy` | `async def stream_copy(self, src: str \| Path, dst: str \| Path, chunk_size: int \| None=None, *, sandbox: str \| Path \| None=None)` | Stream-copy a file. Returns bytes copied. |
| `list_dir` | `async def list_dir(self, path: str \| Path, *, sandbox: str \| Path \| None=None)` | List directory contents (names only). |
| `scan_dir` | `async def scan_dir(self, path: str \| Path, *, sandbox: str \| Path \| None=None)` | Scan directory with metadata (os.scandir). |
| `make_dir` | `async def make_dir(self, path: str \| Path, *, parents: bool=False, exist_ok: bool=False, mode: int=493, sandbox: str \| Path \| None=None)` | Create a directory. |
| `remove_dir` | `async def remove_dir(self, path: str \| Path, *, sandbox: str \| Path \| None=None)` | Remove an empty directory. |
| `remove_tree` | `async def remove_tree(self, path: str \| Path, *, sandbox: str \| Path \| None=None)` | Recursively remove a directory tree. |
| `tempfile` | `def tempfile(self, *, suffix: str='', prefix: str='aquilia-tmp-', dir: str \| Path \| None=None, delete: bool=True)` | Create an async temporary file context manager. |
| `tempdir` | `def tempdir(self, *, suffix: str='', prefix: str='aquilia-tmpdir-', dir: str \| Path \| None=None)` | Create an async temporary directory context manager. |
| `lock` | `def lock(self, path: str \| Path, *, timeout: float=-1, shared: bool=False)` | Create an async file lock. |
| `initialize` | `async def initialize(self)` | Initialize the filesystem service (start thread pool). |
| `shutdown` | `async def shutdown(self, timeout: float=5.0)` | Shut down the filesystem service. |
| `health_check` | `async def health_check(self)` | Return health status and metrics. |

### `AsyncFileStream`

- Source: `aquilia/filesystem/_streaming.py`
- Bases: `object`
- Summary: Chunked async iterator for streaming file reads.

### `AsyncWriteStream`

- Source: `aquilia/filesystem/_streaming.py`
- Bases: `object`
- Summary: Buffered async writer for streaming file writes.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `total_written` | `def total_written(self)` | Total bytes written so far. |
| `write` | `async def write(self, data: bytes)` | Write data to the stream. |
| `flush` | `async def flush(self)` | Force-flush the buffer to disk. |
| `close` | `async def close(self)` | Flush remaining data and close the file. |

### `AsyncTemporaryFile`

- Source: `aquilia/filesystem/_tempfile.py`
- Bases: `object`
- Summary: Async temporary file with automatic cleanup.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | The temporary file path. |

### `AsyncTemporaryDirectory`

- Source: `aquilia/filesystem/_tempfile.py`
- Bases: `object`
- Summary: Async temporary directory with automatic cleanup.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | The temporary directory path. |
