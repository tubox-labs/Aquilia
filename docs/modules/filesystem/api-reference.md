# Filesystem API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `list_dir` | `aquilia/filesystem/_directory.py` | `async def list_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> list[str]` | List directory contents (names only). |
| `scan_dir` | `aquilia/filesystem/_directory.py` | `async def scan_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> list[DirEntry]` | Scan directory contents with metadata. |
| `make_dir` | `aquilia/filesystem/_directory.py` | `async def make_dir(path: str &#124; Path, *, mode: int = 511, parents: bool = False, exist_ok: bool = False, pool: FileSystemPool &#124; None = None) -> None` | Create a directory. |
| `remove_dir` | `aquilia/filesystem/_directory.py` | `async def remove_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> None` | Remove an empty directory. |
| `remove_tree` | `aquilia/filesystem/_directory.py` | `async def remove_tree(path: str &#124; Path, *, ignore_errors: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None) -> None` | Recursively remove a directory tree. |
| `copy_tree` | `aquilia/filesystem/_directory.py` | `async def copy_tree(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, symlinks: bool = False, dirs_exist_ok: bool = False) -> str` | Recursively copy a directory tree. |
| `walk` | `aquilia/filesystem/_directory.py` | `async def walk(top: str &#124; Path, *, topdown: bool = True, followlinks: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None) -> AsyncIterator[tuple[str, list[str], list[str]]]` | Recursively walk a directory tree. |
| `wrap_os_error` | `aquilia/filesystem/_errors.py` | `def wrap_os_error(exc: BaseException, operation: str = '', path: str = '') -> FileSystemFault` | Convert an OS-level exception to a typed ``FileSystemFault``. |
| `async_open` | `aquilia/filesystem/_ops.py` | `def async_open(path: str &#124; Path, mode: str = 'r', buffering: int = -1, encoding: str &#124; None = None, errors: str &#124; None = None, newline: str &#124; None = None, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> _AsyncOpenContext` | Open a file asynchronously. |
| `read_file` | `aquilia/filesystem/_ops.py` | `async def read_file(path: str &#124; Path, *, encoding: str &#124; None = None, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str &#124; bytes` | Read the entire contents of a file. |
| `write_file` | `aquilia/filesystem/_ops.py` | `async def write_file(path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', atomic: bool &#124; None = None, mkdir: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Write data to a file. |
| `append_file` | `aquilia/filesystem/_ops.py` | `async def append_file(path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Append data to a file.  Creates the file if it doesn't exist. |
| `copy_file` | `aquilia/filesystem/_ops.py` | `async def copy_file(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str` | Copy a file from *src* to *dst*. |
| `move_file` | `aquilia/filesystem/_ops.py` | `async def move_file(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str` | Move (rename) a file from *src* to *dst*. |
| `delete_file` | `aquilia/filesystem/_ops.py` | `async def delete_file(path: str &#124; Path, *, missing_ok: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> bool` | Delete a file. |
| `file_exists` | `aquilia/filesystem/_ops.py` | `async def file_exists(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> bool` | Check if a file exists. |
| `file_stat` | `aquilia/filesystem/_ops.py` | `async def file_stat(path: str &#124; Path, *, follow_symlinks: bool &#124; None = None, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> FileStat` | Get file status (stat) information. |
| `validate_path` | `aquilia/filesystem/_security.py` | `def validate_path(path: str &#124; Path, *, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None, operation: str = '') -> Path` | Validate and resolve a filesystem path through multiple security layers. |
| `validate_relative_path` | `aquilia/filesystem/_security.py` | `def validate_relative_path(name: str, *, config: FileSystemConfig &#124; None = None, operation: str = '') -> str` | Validate a relative path/filename (no sandbox, just safety checks). |
| `sanitize_filename` | `aquilia/filesystem/_security.py` | `def sanitize_filename(filename: str, *, max_length: int = 255, replacement: str = '_') -> str` | Sanitize a filename for safe storage. |
| `stream_copy` | `aquilia/filesystem/_streaming.py` | `async def stream_copy(src: str &#124; Path, dst: str &#124; Path, *, chunk_size: int = 65536, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Copy a file via streaming. |
| `stream_read` | `aquilia/filesystem/_streaming.py` | `async def stream_read(path: str &#124; Path, *, chunk_size: int = 65536, pool: FileSystemPool &#124; None = None, offset: int = 0, end: int &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> AsyncIterator[bytes]` | Stream a file in chunks. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CONFIG_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemConfig'}` |
| `_ERROR_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemFault', 'FileNotFoundFault', 'PermissionDeniedFault', 'FileExistsFault', 'IsDirectoryFault', 'NotDirectoryFault', 'DiskFullFault', 'PathTraversalFau` |
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
| `_UNSAFE_CHARS` | `aquilia/filesystem/_security.py` | `frozenset('<>:" &#124; ?*\x00')` |
| `_CONTROL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset((chr(c) for c in range(32)))` |
| `_SHELL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset('; &#124; &$`(){}[]!~')` |
| `_WINDOWS_RESERVED` | `aquilia/filesystem/_security.py` | `frozenset({'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))})` |
| `_DANGEROUS` | `aquilia/filesystem/_security.py` | `_UNSAFE_CHARS &#124; _CONTROL_CHARS &#124; _SHELL_CHARS &#124; frozenset('/\\')` |

## Detailed Classes And Methods

### Class: `FileSystemConfig`

- Source: `aquilia/filesystem/_config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for the Aquilia filesystem module.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `min_pool_threads` | `int` | `2` |
| `max_pool_threads` | `int` | `8` |
| `write_buffer_size` | `int` | `65536` |
| `default_chunk_size` | `int` | `65536` |
| `max_path_length` | `int` | `1024` |
| `follow_symlinks` | `bool` | `False` |
| `sandbox_root` | `str &#124; None` | `None` |
| `atomic_writes` | `bool` | `True` |
| `fsync_on_write` | `bool` | `False` |
| `enable_metrics` | `bool` | `True` |
| `temp_dir` | `str &#124; None` | `None` |
| `max_recursion_depth` | `int` | `100` |
| `max_filename_length` | `int` | `255` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `effective_max_pool_threads` | `def effective_max_pool_threads(self) -> int` |  | Return the effective max pool thread count, accounting for |
| `from_dict` | `def from_dict(cls, data: dict) -> FileSystemConfig` | classmethod | Create config from a dictionary (e.g. from workspace config). |

### Class: `DirEntry`

- Source: `aquilia/filesystem/_directory.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Async-friendly directory entry (mirrors ``os.DirEntry``).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `path` | `str` |  |
| `is_file_cached` | `bool` |  |
| `is_dir_cached` | `bool` |  |
| `is_symlink_cached` | `bool` |  |
| `inode` | `int` | `0` |

### Class: `FileSystemFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `Fault`
- Summary: Base class for all filesystem faults.

### Class: `FileNotFoundFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file or directory does not exist.

### Class: `PermissionDeniedFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when the process lacks permission for the operation.

### Class: `FileExistsFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file already exists and overwrite is not allowed.

### Class: `IsDirectoryFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file operation is attempted on a directory.

### Class: `NotDirectoryFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a directory operation is attempted on a file.

### Class: `DiskFullFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when no space is left on device.

### Class: `PathTraversalFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a path traversal attack is detected.

### Class: `PathTooLongFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when a path exceeds the configured maximum length.

### Class: `FileSystemIOFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Generic I/O error for unclassified OS errors.

### Class: `FileClosedFault`

- Source: `aquilia/filesystem/_errors.py`
- Bases: `FileSystemFault`
- Summary: Raised when an operation is attempted on a closed file.

### Class: `AsyncFile`

- Source: `aquilia/filesystem/_handle.py`
- Bases: `object`
- Summary: Async file handle with buffered I/O.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | The file path/name. |
| `mode` | `def mode(self) -> str` | property | The mode the file was opened with. |
| `closed` | `def closed(self) -> bool` | property | Whether the file has been closed. |
| `encoding` | `def encoding(self) -> str &#124; None` | property | Text encoding (None for binary files). |
| `read` | `async def read(self, size: int = -1) -> bytes &#124; str` |  | Read up to ``size`` bytes/characters. |
| `readline` | `async def readline(self) -> bytes &#124; str` |  | Read a single line. |
| `readlines` | `async def readlines(self) -> list[bytes &#124; str]` |  | Read all lines into a list. |
| `readinto` | `async def readinto(self, buffer: bytearray) -> int` |  | Read bytes into a pre-allocated buffer (binary mode only). |
| `write` | `async def write(self, data: bytes &#124; str) -> int` |  | Write data to the file. |
| `writelines` | `async def writelines(self, lines: Iterable[bytes &#124; str]) -> None` |  | Write an iterable of lines. |
| `flush` | `async def flush(self) -> None` |  | Flush write buffer and OS buffers. |
| `truncate` | `async def truncate(self, size: int &#124; None = None) -> int` |  | Truncate the file to at most ``size`` bytes. |
| `seek` | `async def seek(self, offset: int, whence: int = 0) -> int` |  | Move the file position. |
| `tell` | `async def tell(self) -> int` |  | Return the current file position. |
| `close` | `async def close(self) -> None` |  | Flush buffers and close the underlying file descriptor. |
| `chunks` | `async def chunks(self, chunk_size: int = 65536) -> AsyncIterator[bytes]` |  | Iterate over the file in fixed-size chunks. |

### Class: `LockAcquisitionError`

- Source: `aquilia/filesystem/_lock.py`
- Bases: `FileSystemFault`
- Summary: Raised when a file lock cannot be acquired.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `timeout` | `def timeout(self) -> float` | property | Method. |

### Class: `AsyncFileLock`

- Source: `aquilia/filesystem/_lock.py`
- Bases: `object`
- Summary: Async advisory file lock.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `path` | `def path(self) -> str` | property | Lock file path. |
| `is_locked` | `def is_locked(self) -> bool` | property | Whether the lock is currently held. |
| `acquire` | `async def acquire(self) -> None` |  | Acquire the file lock. |
| `release` | `async def release(self) -> None` |  | Release the file lock. |

### Class: `FileSystemMetrics`

- Source: `aquilia/filesystem/_metrics.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregated filesystem operation metrics.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record_read` | `def record_read(self, bytes_count: int, elapsed_ns: int) -> None` |  | Record a completed read operation. |
| `record_write` | `def record_write(self, bytes_count: int, elapsed_ns: int) -> None` |  | Record a completed write operation. |
| `record_error` | `def record_error(self) -> None` |  | Record a failed operation. |
| `to_dict` | `def to_dict(self) -> dict[str, int]` |  | Export metrics as a dictionary. |
| `reset` | `def reset(self) -> None` |  | Reset all counters to zero.  Useful for testing. |

### Class: `FileStat`

- Source: `aquilia/filesystem/_ops.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: File status information.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `size` | `int` |  |
| `mode` | `int` |  |
| `uid` | `int` |  |
| `gid` | `int` |  |
| `atime_ns` | `int` |  |
| `mtime_ns` | `int` |  |
| `ctime_ns` | `int` |  |
| `is_file` | `bool` |  |
| `is_dir` | `bool` |  |
| `is_symlink` | `bool` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `atime` | `def atime(self) -> float` | property | Method. |
| `mtime` | `def mtime(self) -> float` | property | Method. |
| `ctime` | `def ctime(self) -> float` | property | Method. |

### Class: `AsyncPath`

- Source: `aquilia/filesystem/_path.py`
- Bases: `object`
- Summary: Async filesystem path with I/O delegation to the thread pool.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | The final component of the path. |
| `stem` | `def stem(self) -> str` | property | The final component without suffix. |
| `suffix` | `def suffix(self) -> str` | property | The file extension. |
| `suffixes` | `def suffixes(self) -> list[str]` | property | All file extensions. |
| `parent` | `def parent(self) -> AsyncPath` | property | The parent directory. |
| `parents` | `def parents(self) -> tuple[AsyncPath, ...]` | property | All ancestor directories. |
| `parts` | `def parts(self) -> tuple[str, ...]` | property | Path components as a tuple. |
| `anchor` | `def anchor(self) -> str` | property | The drive + root (e.g. '/' or 'C:\'). |
| `drive` | `def drive(self) -> str` | property | The drive letter (Windows) or empty string. |
| `root` | `def root(self) -> str` | property | The root of the path. |
| `is_absolute` | `def is_absolute(self) -> bool` |  | Whether the path is absolute. |
| `is_relative_to` | `def is_relative_to(self, other: str &#124; Path &#124; AsyncPath) -> bool` |  | Whether this path is relative to another. |
| `path` | `def path(self) -> Path` | property | Access the underlying ``pathlib.Path``. |
| `with_name` | `def with_name(self, name: str) -> AsyncPath` |  | Return a new path with the filename changed. |
| `with_stem` | `def with_stem(self, stem: str) -> AsyncPath` |  | Return a new path with the stem changed. |
| `with_suffix` | `def with_suffix(self, suffix: str) -> AsyncPath` |  | Return a new path with the suffix changed. |
| `relative_to` | `def relative_to(self, other: str &#124; Path &#124; AsyncPath) -> AsyncPath` |  | Return a relative version of this path. |
| `resolve` | `def resolve(self) -> AsyncPath` |  | Resolve the path to an absolute canonical path. |
| `joinpath` | `def joinpath(self, *others: str &#124; Path &#124; AsyncPath) -> AsyncPath` |  | Join one or more path components. |
| `exists` | `async def exists(self) -> bool` |  | Check whether the path exists on disk. |
| `is_file` | `async def is_file(self) -> bool` |  | Check whether the path is a regular file. |
| `is_dir` | `async def is_dir(self) -> bool` |  | Check whether the path is a directory. |
| `is_symlink` | `async def is_symlink(self) -> bool` |  | Check whether the path is a symbolic link. |
| `stat` | `async def stat(self) -> os.stat_result` |  | Get file status (size, permissions, timestamps, etc.). |
| `lstat` | `async def lstat(self) -> os.stat_result` |  | Like ``stat()`` but don't follow symlinks. |
| `read_bytes` | `async def read_bytes(self) -> bytes` |  | Read the entire file as bytes. |
| `read_text` | `async def read_text(self, encoding: str = 'utf-8', errors: str = 'strict') -> str` |  | Read the entire file as text. |
| `open` | `async def open(self, mode: str = 'r', buffering: int = -1, encoding: str &#124; None = None, errors: str &#124; None = None, newline: str &#124; None = None) -> AsyncFile` |  | Open the file and return an ``AsyncFile`` handle. |
| `write_bytes` | `async def write_bytes(self, data: bytes) -> int` |  | Write bytes to the file (creates or overwrites). |
| `write_text` | `async def write_text(self, data: str, encoding: str = 'utf-8', errors: str &#124; None = None, newline: str &#124; None = None) -> int` |  | Write text to the file (creates or overwrites). |
| `mkdir` | `async def mkdir(self, mode: int = 511, parents: bool = False, exist_ok: bool = False) -> None` |  | Create a directory. |
| `rmdir` | `async def rmdir(self) -> None` |  | Remove an empty directory. |
| `unlink` | `async def unlink(self, missing_ok: bool = False) -> None` |  | Remove a file or symbolic link. |
| `rename` | `async def rename(self, target: str &#124; Path &#124; AsyncPath) -> AsyncPath` |  | Rename/move the file or directory. |
| `replace` | `async def replace(self, target: str &#124; Path &#124; AsyncPath) -> AsyncPath` |  | Atomically rename, replacing the target if it exists. |
| `touch` | `async def touch(self, mode: int = 438, exist_ok: bool = True) -> None` |  | Create the file (or update its access/modification times). |
| `chmod` | `async def chmod(self, mode: int) -> None` |  | Change file permissions. |
| `iterdir` | `async def iterdir(self) -> AsyncIterator[AsyncPath]` |  | Iterate over directory contents. |
| `glob` | `async def glob(self, pattern: str) -> AsyncIterator[AsyncPath]` |  | Glob for matching paths. |
| `rglob` | `async def rglob(self, pattern: str) -> AsyncIterator[AsyncPath]` |  | Recursive glob for matching paths. |

### Class: `FileSystemPool`

- Source: `aquilia/filesystem/_pool.py`
- Bases: `object`
- Summary: Dedicated thread pool for filesystem operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialized` | `def initialized(self) -> bool` | property | Whether the pool has been initialized. |
| `active_count` | `def active_count(self) -> int` | property | Number of currently active pool operations. |
| `initialize` | `def initialize(self) -> None` |  | Create the thread pool. |
| `run` | `async def run(self, fn: Callable[..., T], *args: Any) -> T` |  | Execute a blocking function in the dedicated pool. |
| `shutdown` | `async def shutdown(self, timeout: float = 5.0) -> None` |  | Drain and shut down the thread pool. |

### Class: `FileSystem`

- Source: `aquilia/filesystem/_service.py`
- Bases: `object`
- Summary: High-level async filesystem service.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `config` | `def config(self) -> FileSystemConfig` | property | Current filesystem configuration. |
| `pool` | `def pool(self) -> FileSystemPool` | property | The underlying thread pool. |
| `metrics` | `def metrics(self) -> FileSystemMetrics` | property | Operation metrics. |
| `open` | `def open(self, path: str &#124; Path, mode: str = 'r', buffering: int = -1, encoding: str &#124; None = None, errors: str &#124; None = None, newline: str &#124; None = None, *, sandbox: str &#124; Path &#124; None = None)` |  | Open a file asynchronously. |
| `read_file` | `async def read_file(self, path: str &#124; Path, *, encoding: str &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str &#124; bytes` |  | Read entire file contents. |
| `write_file` | `async def write_file(self, path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', atomic: bool &#124; None = None, mkdir: bool = False, sandbox: str &#124; Path &#124; None = None) -> int` |  | Write data to a file. Returns bytes written. |
| `append_file` | `async def append_file(self, path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', sandbox: str &#124; Path &#124; None = None) -> int` |  | Append data to a file. Returns bytes written. |
| `copy_file` | `async def copy_file(self, src: str &#124; Path, dst: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> str` |  | Copy a file. Returns destination path. |
| `move_file` | `async def move_file(self, src: str &#124; Path, dst: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> str` |  | Move/rename a file. Returns destination path. |
| `delete_file` | `async def delete_file(self, path: str &#124; Path, *, missing_ok: bool = False, sandbox: str &#124; Path &#124; None = None) -> bool` |  | Delete a file. Returns True if deleted. |
| `file_exists` | `async def file_exists(self, path: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> bool` |  | Check if a file exists. |
| `file_stat` | `async def file_stat(self, path: str &#124; Path, *, follow_symlinks: bool &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> FileStat` |  | Get file status information. |
| `stream_read` | `def stream_read(self, path: str &#124; Path, chunk_size: int &#124; None = None, offset: int = 0, end: int &#124; None = None, *, sandbox: str &#124; Path &#124; None = None) -> AsyncIterator[bytes]` |  | Stream file contents in chunks. |
| `stream_copy` | `async def stream_copy(self, src: str &#124; Path, dst: str &#124; Path, chunk_size: int &#124; None = None, *, sandbox: str &#124; Path &#124; None = None) -> int` |  | Stream-copy a file. Returns bytes copied. |
| `list_dir` | `async def list_dir(self, path: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> list[str]` |  | List directory contents (names only). |
| `scan_dir` | `async def scan_dir(self, path: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> list[DirEntry]` |  | Scan directory with metadata (os.scandir). |
| `make_dir` | `async def make_dir(self, path: str &#124; Path, *, parents: bool = False, exist_ok: bool = False, mode: int = 493, sandbox: str &#124; Path &#124; None = None) -> None` |  | Create a directory. |
| `remove_dir` | `async def remove_dir(self, path: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> None` |  | Remove an empty directory. |
| `remove_tree` | `async def remove_tree(self, path: str &#124; Path, *, sandbox: str &#124; Path &#124; None = None) -> None` |  | Recursively remove a directory tree. |
| `tempfile` | `def tempfile(self, *, suffix: str = '', prefix: str = 'aquilia-tmp-', dir: str &#124; Path &#124; None = None, delete: bool = True)` |  | Create an async temporary file context manager. |
| `tempdir` | `def tempdir(self, *, suffix: str = '', prefix: str = 'aquilia-tmpdir-', dir: str &#124; Path &#124; None = None)` |  | Create an async temporary directory context manager. |
| `lock` | `def lock(self, path: str &#124; Path, *, timeout: float = -1, shared: bool = False)` |  | Create an async file lock. |
| `initialize` | `async def initialize(self) -> None` |  | Initialize the filesystem service (start thread pool). |
| `shutdown` | `async def shutdown(self, timeout: float = 5.0) -> None` |  | Shut down the filesystem service. |
| `health_check` | `async def health_check(self) -> dict` |  | Return health status and metrics. |

### Class: `AsyncFileStream`

- Source: `aquilia/filesystem/_streaming.py`
- Bases: `object`
- Summary: Chunked async iterator for streaming file reads.

### Class: `AsyncWriteStream`

- Source: `aquilia/filesystem/_streaming.py`
- Bases: `object`
- Summary: Buffered async writer for streaming file writes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `total_written` | `def total_written(self) -> int` | property | Total bytes written so far. |
| `write` | `async def write(self, data: bytes) -> int` |  | Write data to the stream. |
| `flush` | `async def flush(self) -> None` |  | Force-flush the buffer to disk. |
| `close` | `async def close(self) -> None` |  | Flush remaining data and close the file. |

### Class: `AsyncTemporaryFile`

- Source: `aquilia/filesystem/_tempfile.py`
- Bases: `object`
- Summary: Async temporary file with automatic cleanup.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | The temporary file path. |

### Class: `AsyncTemporaryDirectory`

- Source: `aquilia/filesystem/_tempfile.py`
- Bases: `object`
- Summary: Async temporary directory with automatic cleanup.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | The temporary directory path. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `list_dir` | `aquilia/filesystem/_directory.py` | `async def list_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> list[str]` | List directory contents (names only). |
| `scan_dir` | `aquilia/filesystem/_directory.py` | `async def scan_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> list[DirEntry]` | Scan directory contents with metadata. |
| `make_dir` | `aquilia/filesystem/_directory.py` | `async def make_dir(path: str &#124; Path, *, mode: int = 511, parents: bool = False, exist_ok: bool = False, pool: FileSystemPool &#124; None = None) -> None` | Create a directory. |
| `remove_dir` | `aquilia/filesystem/_directory.py` | `async def remove_dir(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None) -> None` | Remove an empty directory. |
| `remove_tree` | `aquilia/filesystem/_directory.py` | `async def remove_tree(path: str &#124; Path, *, ignore_errors: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None) -> None` | Recursively remove a directory tree. |
| `copy_tree` | `aquilia/filesystem/_directory.py` | `async def copy_tree(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, symlinks: bool = False, dirs_exist_ok: bool = False) -> str` | Recursively copy a directory tree. |
| `walk` | `aquilia/filesystem/_directory.py` | `async def walk(top: str &#124; Path, *, topdown: bool = True, followlinks: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None) -> AsyncIterator[tuple[str, list[str], list[str]]]` | Recursively walk a directory tree. |
| `wrap_os_error` | `aquilia/filesystem/_errors.py` | `def wrap_os_error(exc: BaseException, operation: str = '', path: str = '') -> FileSystemFault` | Convert an OS-level exception to a typed ``FileSystemFault``. |
| `async_open` | `aquilia/filesystem/_ops.py` | `def async_open(path: str &#124; Path, mode: str = 'r', buffering: int = -1, encoding: str &#124; None = None, errors: str &#124; None = None, newline: str &#124; None = None, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> _AsyncOpenContext` | Open a file asynchronously. |
| `read_file` | `aquilia/filesystem/_ops.py` | `async def read_file(path: str &#124; Path, *, encoding: str &#124; None = None, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str &#124; bytes` | Read the entire contents of a file. |
| `write_file` | `aquilia/filesystem/_ops.py` | `async def write_file(path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', atomic: bool &#124; None = None, mkdir: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Write data to a file. |
| `append_file` | `aquilia/filesystem/_ops.py` | `async def append_file(path: str &#124; Path, data: str &#124; bytes, *, encoding: str = 'utf-8', pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, metrics: FileSystemMetrics &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Append data to a file.  Creates the file if it doesn't exist. |
| `copy_file` | `aquilia/filesystem/_ops.py` | `async def copy_file(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str` | Copy a file from *src* to *dst*. |
| `move_file` | `aquilia/filesystem/_ops.py` | `async def move_file(src: str &#124; Path, dst: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> str` | Move (rename) a file from *src* to *dst*. |
| `delete_file` | `aquilia/filesystem/_ops.py` | `async def delete_file(path: str &#124; Path, *, missing_ok: bool = False, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> bool` | Delete a file. |
| `file_exists` | `aquilia/filesystem/_ops.py` | `async def file_exists(path: str &#124; Path, *, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> bool` | Check if a file exists. |
| `file_stat` | `aquilia/filesystem/_ops.py` | `async def file_stat(path: str &#124; Path, *, follow_symlinks: bool &#124; None = None, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> FileStat` | Get file status (stat) information. |
| `validate_path` | `aquilia/filesystem/_security.py` | `def validate_path(path: str &#124; Path, *, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None, operation: str = '') -> Path` | Validate and resolve a filesystem path through multiple security layers. |
| `validate_relative_path` | `aquilia/filesystem/_security.py` | `def validate_relative_path(name: str, *, config: FileSystemConfig &#124; None = None, operation: str = '') -> str` | Validate a relative path/filename (no sandbox, just safety checks). |
| `sanitize_filename` | `aquilia/filesystem/_security.py` | `def sanitize_filename(filename: str, *, max_length: int = 255, replacement: str = '_') -> str` | Sanitize a filename for safe storage. |
| `stream_copy` | `aquilia/filesystem/_streaming.py` | `async def stream_copy(src: str &#124; Path, dst: str &#124; Path, *, chunk_size: int = 65536, pool: FileSystemPool &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> int` | Copy a file via streaming. |
| `stream_read` | `aquilia/filesystem/_streaming.py` | `async def stream_read(path: str &#124; Path, *, chunk_size: int = 65536, pool: FileSystemPool &#124; None = None, offset: int = 0, end: int &#124; None = None, config: FileSystemConfig &#124; None = None, sandbox: str &#124; Path &#124; None = None) -> AsyncIterator[bytes]` | Stream a file in chunks. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CONFIG_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemConfig'}` |
| `_ERROR_NAMES` | `aquilia/filesystem/__init__.py` | `{'FileSystemFault', 'FileNotFoundFault', 'PermissionDeniedFault', 'FileExistsFault', 'IsDirectoryFault', 'NotDirectoryFault', 'DiskFullFault', 'PathTraversalFau` |
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
| `_UNSAFE_CHARS` | `aquilia/filesystem/_security.py` | `frozenset('<>:" &#124; ?*\x00')` |
| `_CONTROL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset((chr(c) for c in range(32)))` |
| `_SHELL_CHARS` | `aquilia/filesystem/_security.py` | `frozenset('; &#124; &$`(){}[]!~')` |
| `_WINDOWS_RESERVED` | `aquilia/filesystem/_security.py` | `frozenset({'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))})` |
| `_DANGEROUS` | `aquilia/filesystem/_security.py` | `_UNSAFE_CHARS &#124; _CONTROL_CHARS &#124; _SHELL_CHARS &#124; frozenset('/\\')` |
