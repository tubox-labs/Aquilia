"""
FileSystem Service — DI-injectable facade for async file operations.

This is the primary integration point with Aquilia's dependency
injection system.  Register it as a singleton and inject it into
controllers, services, and subsystems.

Usage::

    from aquilia.filesystem import FileSystem

    # In your app setup
    container.register_singleton(FileSystem)

    # In a controller
    class ReportController:
        def __init__(self, fs: FileSystem):
            self.fs = fs

        async def generate(self):
            data = await self.fs.read_file("template.html", encoding="utf-8")
            await self.fs.write_file("report.html", rendered, atomic=True)
"""

from __future__ import annotations

from pathlib import Path
from typing import (
    AsyncIterator,
    List,
    Optional,
    Union,
)

from ._config import FileSystemConfig
from ._directory import DirEntry
from ._handle import AsyncFile
from ._metrics import FileSystemMetrics
from ._ops import FileStat
from ._pool import FileSystemPool
from ._security import validate_path


class FileSystem:
    """
    High-level async filesystem service.

    Provides a unified API for all file operations with shared
    configuration, pool, and metrics.  Designed for dependency
    injection — register as a singleton in Aquilia's DI container.

    Parameters
    ----------
    config
        Filesystem configuration.  Uses defaults if not provided.
    pool
        Custom thread pool.  A dedicated pool is created if not provided.
    metrics
        Metrics recorder.  A new instance is created if not provided.
    """

    __slots__ = ("_config", "_pool", "_metrics", "_owns_pool")

    def __init__(
        self,
        config: Optional[FileSystemConfig] = None,
        pool: Optional[FileSystemPool] = None,
        metrics: Optional[FileSystemMetrics] = None,
    ) -> None:
        self._config = config or FileSystemConfig()
        self._owns_pool = pool is None
        self._pool = pool or FileSystemPool(self._config)
        self._metrics = metrics or FileSystemMetrics()

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def config(self) -> FileSystemConfig:
        """Current filesystem configuration."""
        return self._config

    @property
    def pool(self) -> FileSystemPool:
        """The underlying thread pool."""
        return self._pool

    @property
    def metrics(self) -> FileSystemMetrics:
        """Operation metrics."""
        return self._metrics

    # ── File operations ─────────────────────────────────────────────────

    def open(
        self,
        path: Union[str, Path],
        mode: str = "r",
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ):
        """
        Open a file asynchronously.

        Returns an awaitable context manager yielding :class:`AsyncFile`.
        """
        from ._ops import async_open
        return async_open(
            path, mode, buffering, encoding, errors, newline,
            pool=self._pool, config=self._config,
            metrics=self._metrics, sandbox=sandbox,
        )

    async def read_file(
        self,
        path: Union[str, Path],
        *,
        encoding: Optional[str] = None,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> Union[str, bytes]:
        """Read entire file contents."""
        from ._ops import read_file
        return await read_file(
            path, encoding=encoding,
            pool=self._pool, config=self._config,
            metrics=self._metrics, sandbox=sandbox,
        )

    async def write_file(
        self,
        path: Union[str, Path],
        data: Union[str, bytes],
        *,
        encoding: str = "utf-8",
        atomic: Optional[bool] = None,
        mkdir: bool = False,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> int:
        """Write data to a file. Returns bytes written."""
        from ._ops import write_file
        return await write_file(
            path, data, encoding=encoding, atomic=atomic, mkdir=mkdir,
            pool=self._pool, config=self._config,
            metrics=self._metrics, sandbox=sandbox,
        )

    async def append_file(
        self,
        path: Union[str, Path],
        data: Union[str, bytes],
        *,
        encoding: str = "utf-8",
        sandbox: Optional[Union[str, Path]] = None,
    ) -> int:
        """Append data to a file. Returns bytes written."""
        from ._ops import append_file
        return await append_file(
            path, data, encoding=encoding,
            pool=self._pool, config=self._config,
            metrics=self._metrics, sandbox=sandbox,
        )

    async def copy_file(
        self,
        src: Union[str, Path],
        dst: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> str:
        """Copy a file. Returns destination path."""
        from ._ops import copy_file
        return await copy_file(
            src, dst,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def move_file(
        self,
        src: Union[str, Path],
        dst: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> str:
        """Move/rename a file. Returns destination path."""
        from ._ops import move_file
        return await move_file(
            src, dst,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def delete_file(
        self,
        path: Union[str, Path],
        *,
        missing_ok: bool = False,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Delete a file. Returns True if deleted."""
        from ._ops import delete_file
        return await delete_file(
            path, missing_ok=missing_ok,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def file_exists(
        self,
        path: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Check if a file exists."""
        from ._ops import file_exists
        return await file_exists(
            path, pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def file_stat(
        self,
        path: Union[str, Path],
        *,
        follow_symlinks: Optional[bool] = None,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> FileStat:
        """Get file status information."""
        from ._ops import file_stat
        return await file_stat(
            path, follow_symlinks=follow_symlinks,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    # ── Streaming ───────────────────────────────────────────────────────

    def stream_read(
        self,
        path: Union[str, Path],
        chunk_size: Optional[int] = None,
        offset: int = 0,
        end: Optional[int] = None,
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> AsyncIterator[bytes]:
        """Stream file contents in chunks."""
        from ._streaming import stream_read
        return stream_read(
            path, chunk_size=chunk_size, offset=offset, end=end,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def stream_copy(
        self,
        src: Union[str, Path],
        dst: Union[str, Path],
        chunk_size: Optional[int] = None,
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> int:
        """Stream-copy a file. Returns bytes copied."""
        from ._streaming import stream_copy
        return await stream_copy(
            src, dst, chunk_size=chunk_size,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    # ── Directory operations ────────────────────────────────────────────

    async def list_dir(
        self,
        path: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> List[str]:
        """List directory contents (names only)."""
        from ._directory import list_dir
        return await list_dir(
            path, pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def scan_dir(
        self,
        path: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> List[DirEntry]:
        """Scan directory with metadata (os.scandir)."""
        from ._directory import scan_dir
        return await scan_dir(
            path, pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def make_dir(
        self,
        path: Union[str, Path],
        *,
        parents: bool = False,
        exist_ok: bool = False,
        mode: int = 0o755,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> None:
        """Create a directory."""
        from ._directory import make_dir
        return await make_dir(
            path, parents=parents, exist_ok=exist_ok, mode=mode,
            pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def remove_dir(
        self,
        path: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> None:
        """Remove an empty directory."""
        from ._directory import remove_dir
        return await remove_dir(
            path, pool=self._pool, config=self._config, sandbox=sandbox,
        )

    async def remove_tree(
        self,
        path: Union[str, Path],
        *,
        sandbox: Optional[Union[str, Path]] = None,
    ) -> None:
        """Recursively remove a directory tree."""
        from ._directory import remove_tree
        return await remove_tree(
            path, pool=self._pool, config=self._config, sandbox=sandbox,
        )

    # ── Temporary files ─────────────────────────────────────────────────

    def tempfile(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmp-",
        dir: Optional[Union[str, Path]] = None,
        delete: bool = True,
    ):
        """Create an async temporary file context manager."""
        from ._tempfile import AsyncTemporaryFile
        return AsyncTemporaryFile(
            suffix=suffix, prefix=prefix, dir=dir,
            pool=self._pool, config=self._config, delete=delete,
        )

    def tempdir(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmpdir-",
        dir: Optional[Union[str, Path]] = None,
    ):
        """Create an async temporary directory context manager."""
        from ._tempfile import AsyncTemporaryDirectory
        return AsyncTemporaryDirectory(
            suffix=suffix, prefix=prefix, dir=dir,
            pool=self._pool, config=self._config,
        )

    # ── Locking ─────────────────────────────────────────────────────────

    def lock(
        self,
        path: Union[str, Path],
        *,
        timeout: float = -1,
        shared: bool = False,
    ):
        """
        Create an async file lock.

        Usage::

            async with fs.lock("/tmp/app.lock", timeout=5.0):
                ...  # exclusive access
        """
        from ._lock import AsyncFileLock
        return AsyncFileLock(
            path, timeout=timeout, shared=shared,
            pool=self._pool, config=self._config,
        )

    # ── Lifecycle ───────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Initialize the filesystem service (start thread pool)."""
        self._pool.initialize()

    async def shutdown(self, timeout: float = 5.0) -> None:
        """Shut down the filesystem service."""
        if self._owns_pool:
            await self._pool.shutdown(timeout=timeout)

    async def health_check(self) -> dict:
        """Return health status and metrics."""
        return {
            "status": "healthy" if self._pool._executor is not None else "not_initialized",
            "pool_active": self._pool._active_count,
            "pool_max_threads": self._config.effective_max_pool_threads(),
            **self._metrics.to_dict(),
        }

    def __repr__(self) -> str:
        return (
            f"<FileSystem pool_threads={self._config.effective_max_pool_threads()} "
            f"reads={self._metrics.total_reads} "
            f"writes={self._metrics.total_writes}>"
        )
