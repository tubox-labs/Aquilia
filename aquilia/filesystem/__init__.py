"""
Aquilia Filesystem — High-performance native async file I/O.

This module replaces the ``aiofiles`` dependency with a purpose-built
async filesystem layer that is tightly integrated with Aquilia's
fault system, dependency injection, configuration, and subsystem
lifecycle.

Quick Start
-----------

Module-level convenience functions (use the default pool)::

    from aquilia.filesystem import (
        async_open, read_file, write_file, append_file,
        copy_file, move_file, delete_file, file_exists, file_stat,
    )

    content = await read_file("data.txt", encoding="utf-8")
    await write_file("output.txt", "hello", atomic=True)

    async with async_open("log.txt", "a") as f:
        await f.write("appended line\\n")

AsyncPath (pathlib-style)::

    from aquilia.filesystem import AsyncPath

    p = AsyncPath("data/reports")
    await p.mkdir(parents=True, exist_ok=True)
    await (p / "report.csv").write_text(csv_data)

    async for entry in p.iterdir():
        print(entry.name)

Streaming::

    from aquilia.filesystem import stream_read, stream_copy

    async for chunk in stream_read("large.bin"):
        process(chunk)

    await stream_copy("src.dat", "dst.dat")

Temporary files::

    from aquilia.filesystem import async_tempfile, async_tempdir

    async with async_tempfile(suffix=".json") as tmp:
        await tmp.write(b'{}')

    async with async_tempdir() as tmpdir:
        await (tmpdir / "data.txt").write_text("temp")

File locking::

    from aquilia.filesystem import AsyncFileLock

    async with AsyncFileLock("/tmp/app.lock", timeout=5.0):
        ...  # exclusive access

DI-injectable FileSystem service::

    from aquilia.filesystem import FileSystem

    class MyController:
        def __init__(self, fs: FileSystem):
            self.fs = fs

        async def save(self, data: bytes):
            await self.fs.write_file("output.dat", data)
"""

from __future__ import annotations

__all__ = [
    # Core types
    "FileSystem",
    "AsyncFile",
    "AsyncPath",
    "FileStat",
    # Configuration
    "FileSystemConfig",
    # Pool
    "FileSystemPool",
    # Metrics
    "FileSystemMetrics",
    # File operations
    "async_open",
    "read_file",
    "write_file",
    "append_file",
    "copy_file",
    "move_file",
    "delete_file",
    "file_exists",
    "file_stat",
    # Streaming
    "AsyncFileStream",
    "AsyncWriteStream",
    "stream_read",
    "stream_copy",
    # Directory operations
    "list_dir",
    "scan_dir",
    "make_dir",
    "remove_dir",
    "remove_tree",
    "copy_tree",
    "walk",
    "DirEntry",
    # Temporary files
    "AsyncTemporaryFile",
    "AsyncTemporaryDirectory",
    "async_tempfile",
    "async_tempdir",
    # Locking
    "AsyncFileLock",
    "LockAcquisitionError",
    # Security
    "validate_path",
    "sanitize_filename",
    # Errors
    "FileSystemFault",
    "FileNotFoundFault",
    "PermissionDeniedFault",
    "FileExistsFault",
    "IsDirectoryFault",
    "NotDirectoryFault",
    "DiskFullFault",
    "PathTraversalFault",
    "PathTooLongFault",
    "FileSystemIOFault",
    "FileClosedFault",
    "wrap_os_error",
]


# ═══════════════════════════════════════════════════════════════════════════
# Lazy imports for fast module load
# ═══════════════════════════════════════════════════════════════════════════


def __getattr__(name: str):
    """Lazy import to avoid loading everything at module import time."""

    if name in _CONFIG_NAMES:
        from ._config import FileSystemConfig

        return FileSystemConfig

    if name in _ERROR_NAMES:
        from . import _errors

        return getattr(_errors, name)

    if name in _SECURITY_NAMES:
        from . import _security

        return getattr(_security, name)

    if name in _POOL_NAMES:
        from ._pool import FileSystemPool

        return FileSystemPool

    if name in _METRICS_NAMES:
        from ._metrics import FileSystemMetrics

        return FileSystemMetrics

    if name in _HANDLE_NAMES:
        from ._handle import AsyncFile

        return AsyncFile

    if name in _PATH_NAMES:
        from ._path import AsyncPath

        return AsyncPath

    if name in _OPS_NAMES:
        from . import _ops

        return getattr(_ops, name)

    if name in _STREAMING_NAMES:
        from . import _streaming

        return getattr(_streaming, name)

    if name in _DIR_NAMES:
        from . import _directory

        return getattr(_directory, name)

    if name in _TEMP_NAMES:
        from . import _tempfile

        return getattr(_tempfile, name)

    if name in _LOCK_NAMES:
        from . import _lock

        return getattr(_lock, name)

    if name == "FileSystem":
        from ._service import FileSystem

        return FileSystem

    raise AttributeError(f"module 'aquilia.filesystem' has no attribute {name!r}")


_CONFIG_NAMES = {"FileSystemConfig"}
_ERROR_NAMES = {
    "FileSystemFault",
    "FileNotFoundFault",
    "PermissionDeniedFault",
    "FileExistsFault",
    "IsDirectoryFault",
    "NotDirectoryFault",
    "DiskFullFault",
    "PathTraversalFault",
    "PathTooLongFault",
    "FileSystemIOFault",
    "FileClosedFault",
    "wrap_os_error",
}
_SECURITY_NAMES = {"validate_path", "sanitize_filename"}
_POOL_NAMES = {"FileSystemPool"}
_METRICS_NAMES = {"FileSystemMetrics"}
_HANDLE_NAMES = {"AsyncFile"}
_PATH_NAMES = {"AsyncPath"}
_OPS_NAMES = {
    "async_open",
    "read_file",
    "write_file",
    "append_file",
    "copy_file",
    "move_file",
    "delete_file",
    "file_exists",
    "file_stat",
    "FileStat",
}
_STREAMING_NAMES = {
    "AsyncFileStream",
    "AsyncWriteStream",
    "stream_read",
    "stream_copy",
}
_DIR_NAMES = {
    "list_dir",
    "scan_dir",
    "make_dir",
    "remove_dir",
    "remove_tree",
    "copy_tree",
    "walk",
    "DirEntry",
}
_TEMP_NAMES = {
    "AsyncTemporaryFile",
    "AsyncTemporaryDirectory",
    "async_tempfile",
    "async_tempdir",
}
_LOCK_NAMES = {"AsyncFileLock", "LockAcquisitionError"}
