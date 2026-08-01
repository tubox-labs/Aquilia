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

from collections.abc import AsyncIterator
from pathlib import Path

from aquilia.filesystem._config import FileSystemConfig
from aquilia.filesystem._directory import (
    DirEntry,
    copy_tree,
    list_dir,
    make_dir,
    remove_dir,
    remove_tree,
    scan_dir,
    walk,
)
from aquilia.filesystem._lock import AsyncFileLock
from aquilia.filesystem._metrics import FileSystemMetrics
from aquilia.filesystem._ops import (
    FileStat,
    append_file,
    async_open,
    copy_file,
    delete_file,
    file_exists,
    file_stat,
    move_file,
    read_file,
    write_file,
)
from aquilia.filesystem._pool import FileSystemPool
from aquilia.filesystem._streaming import stream_copy, stream_read
from aquilia.filesystem._tempfile import AsyncTemporaryDirectory, AsyncTemporaryFile


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
        config: FileSystemConfig | None = None,
        pool: FileSystemPool | None = None,
        metrics: FileSystemMetrics | None = None,
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
        path: str | Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        *,
        sandbox: str | Path | None = None,
    ):
        """
        Open a file asynchronously.

        Returns an awaitable context manager yielding :class:`AsyncFile`.
        """

        return async_open(
            path,
            mode,
            buffering,
            encoding,
            errors,
            newline,
            pool=self._pool,
            config=self._config,
            metrics=self._metrics,
            sandbox=sandbox,
        )

    async def read_file(
        self,
        path: str | Path,
        *,
        encoding: str | None = None,
        sandbox: str | Path | None = None,
    ) -> str | bytes:
        """Read entire file contents."""

        return await read_file(
            path,
            encoding=encoding,
            pool=self._pool,
            config=self._config,
            metrics=self._metrics,
            sandbox=sandbox,
        )

    async def write_file(
        self,
        path: str | Path,
        data: str | bytes,
        *,
        encoding: str = "utf-8",
        atomic: bool | None = None,
        mkdir: bool = False,
        sandbox: str | Path | None = None,
    ) -> int:
        """Write data to a file. Returns bytes written."""

        return await write_file(
            path,
            data,
            encoding=encoding,
            atomic=atomic,
            mkdir=mkdir,
            pool=self._pool,
            config=self._config,
            metrics=self._metrics,
            sandbox=sandbox,
        )

    async def append_file(
        self,
        path: str | Path,
        data: str | bytes,
        *,
        encoding: str = "utf-8",
        sandbox: str | Path | None = None,
    ) -> int:
        """Append data to a file. Returns bytes written."""

        return await append_file(
            path,
            data,
            encoding=encoding,
            pool=self._pool,
            config=self._config,
            metrics=self._metrics,
            sandbox=sandbox,
        )

    async def copy_file(
        self,
        src: str | Path,
        dst: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> str:
        """Copy a file. Returns destination path."""

        return await copy_file(
            src,
            dst,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def move_file(
        self,
        src: str | Path,
        dst: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> str:
        """Move/rename a file. Returns destination path."""

        return await move_file(
            src,
            dst,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def delete_file(
        self,
        path: str | Path,
        *,
        missing_ok: bool = False,
        sandbox: str | Path | None = None,
    ) -> bool:
        """Delete a file. Returns True if deleted."""

        return await delete_file(
            path,
            missing_ok=missing_ok,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def file_exists(
        self,
        path: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> bool:
        """Check if a file exists."""

        return await file_exists(
            path,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def file_stat(
        self,
        path: str | Path,
        *,
        follow_symlinks: bool | None = None,
        sandbox: str | Path | None = None,
    ) -> FileStat:
        """Get file status information."""

        return await file_stat(
            path,
            follow_symlinks=follow_symlinks,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    # ── Streaming ───────────────────────────────────────────────────────

    def stream_read(
        self,
        path: str | Path,
        chunk_size: int | None = None,
        offset: int = 0,
        end: int | None = None,
        *,
        sandbox: str | Path | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Stream file contents in chunks.

        Args:
            path: File to read.
            chunk_size: Bytes per chunk; falls back to
                ``config.default_chunk_size`` when omitted.
            offset: Start byte offset.
            end: End byte offset (exclusive).
            sandbox: Sandbox root override.

        Returns:
            Async iterator over byte chunks.

        Raises:
            PathTraversalFault: If the resolved path escapes the sandbox.

        Usage::

            async for chunk in fs.stream_read(path, sandbox=uploads_root):
                ...
        """

        return stream_read(
            path,
            chunk_size=chunk_size or self._config.default_chunk_size,
            offset=offset,
            end=end,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def stream_copy(
        self,
        src: str | Path,
        dst: str | Path,
        chunk_size: int | None = None,
        *,
        sandbox: str | Path | None = None,
    ) -> int:
        """
        Stream-copy a file.

        Args:
            src: Source path.
            dst: Destination path.
            chunk_size: Bytes per chunk; falls back to
                ``config.default_chunk_size`` when omitted.
            sandbox: Sandbox root override applied to both paths.

        Returns:
            Number of bytes copied.

        Raises:
            PathTraversalFault: If either path escapes the sandbox.

        Usage::

            copied = await fs.stream_copy(src, dst, sandbox=uploads_root)
        """

        return await stream_copy(
            src,
            dst,
            chunk_size=chunk_size or self._config.default_chunk_size,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    # ── Directory operations ────────────────────────────────────────────

    async def list_dir(
        self,
        path: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> list[str]:
        """List directory contents (names only)."""

        return await list_dir(
            path,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def scan_dir(
        self,
        path: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> list[DirEntry]:
        """Scan directory with metadata (os.scandir)."""

        return await scan_dir(
            path,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def make_dir(
        self,
        path: str | Path,
        *,
        parents: bool = False,
        exist_ok: bool = False,
        mode: int = 0o755,
        sandbox: str | Path | None = None,
    ) -> None:
        """Create a directory."""

        return await make_dir(
            path,
            parents=parents,
            exist_ok=exist_ok,
            mode=mode,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def remove_dir(
        self,
        path: str | Path,
        *,
        sandbox: str | Path | None = None,
    ) -> None:
        """Remove an empty directory."""

        return await remove_dir(
            path,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def remove_tree(
        self,
        path: str | Path,
        *,
        ignore_errors: bool = False,
        sandbox: str | Path | None = None,
    ) -> None:
        """Recursively remove a directory tree."""

        return await remove_tree(
            path,
            ignore_errors=ignore_errors,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    async def copy_tree(
        self,
        src: str | Path,
        dst: str | Path,
        *,
        symlinks: bool = False,
        dirs_exist_ok: bool = False,
        sandbox: str | Path | None = None,
    ) -> str:
        """
        Recursively copy a directory tree.

        Args:
            src: Source directory.
            dst: Destination directory.
            symlinks: Copy symlinks as symlinks rather than following them.
            dirs_exist_ok: Do not raise if destination directories exist.
            sandbox: Sandbox root override applied to both paths.

        Returns:
            Destination path as a string.

        Raises:
            PathTraversalFault: If either path escapes the sandbox.

        Usage::

            await fs.copy_tree("/srv/a", "/srv/b", sandbox="/srv")
        """

        return await copy_tree(
            src,
            dst,
            symlinks=symlinks,
            dirs_exist_ok=dirs_exist_ok,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    def walk(
        self,
        top: str | Path,
        *,
        topdown: bool = True,
        followlinks: bool = False,
        sandbox: str | Path | None = None,
    ) -> AsyncIterator[tuple[str, list[str], list[str]]]:
        """
        Recursively walk a directory tree.

        Args:
            top: Root directory to walk.
            topdown: Yield a directory before its subdirectories.
            followlinks: Follow symbolic links while walking.
            sandbox: Sandbox root override.

        Returns:
            Async iterator of ``(dirpath, dirnames, filenames)`` tuples.

        Raises:
            PathTraversalFault: If the resolved root escapes the sandbox.

        Usage::

            async for dirpath, dirs, files in fs.walk("/srv", sandbox="/srv"):
                ...
        """

        return walk(
            top,
            topdown=topdown,
            followlinks=followlinks,
            pool=self._pool,
            config=self._config,
            sandbox=sandbox,
        )

    # ── Temporary files ─────────────────────────────────────────────────

    def tempfile(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmp-",
        dir: str | Path | None = None,
        delete: bool = True,
    ):
        """Create an async temporary file context manager."""

        return AsyncTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            pool=self._pool,
            config=self._config,
            delete=delete,
        )

    def tempdir(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmpdir-",
        dir: str | Path | None = None,
    ):
        """Create an async temporary directory context manager."""

        return AsyncTemporaryDirectory(
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            pool=self._pool,
            config=self._config,
        )

    # ── Locking ─────────────────────────────────────────────────────────

    def lock(
        self,
        path: str | Path,
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

        return AsyncFileLock(
            path,
            timeout=timeout,
            shared=shared,
            pool=self._pool,
            config=self._config,
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
