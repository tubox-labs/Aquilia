"""
Convenience Filesystem Operations — High-level async file I/O functions.

These are the primary replacements for ``aiofiles`` usage throughout
the Aquilia framework.  Each function validates paths, records metrics,
and delegates blocking I/O to the dedicated filesystem pool.

Usage::

    from aquilia.filesystem import (
        async_open, read_file, write_file, append_file,
        copy_file, move_file, delete_file, file_exists, file_stat,
    )

    data = await read_file("config.json")
    await write_file("output.txt", "hello world")
    await copy_file("src.dat", "dst.dat")
"""

from __future__ import annotations

import contextlib
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from ._config import FileSystemConfig
from ._errors import wrap_os_error
from ._handle import AsyncFile
from ._metrics import FileSystemMetrics
from ._pool import FileSystemPool
from ._security import validate_path

# ═══════════════════════════════════════════════════════════════════════════
# async_open — Drop-in replacement for aiofiles.open()
# ═══════════════════════════════════════════════════════════════════════════


class _AsyncOpenContext:
    """
    Context manager returned by :func:`async_open`.

    Supports both ``async with`` and direct ``await``::

        # As context manager
        async with async_open("file.txt", "r") as f:
            content = await f.read()

        # Direct await
        f = await async_open("file.txt", "r")
        try:
            content = await f.read()
        finally:
            await f.close()
    """

    __slots__ = (
        "_path",
        "_mode",
        "_buffering",
        "_encoding",
        "_errors_param",
        "_newline",
        "_pool",
        "_config",
        "_metrics",
        "_sandbox",
        "_handle",
    )

    def __init__(
        self,
        path: str | Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        pool: FileSystemPool | None = None,
        config: FileSystemConfig | None = None,
        metrics: FileSystemMetrics | None = None,
        sandbox: str | Path | None = None,
    ) -> None:
        self._path = path
        self._mode = mode
        self._buffering = buffering
        self._encoding = encoding
        self._errors_param = errors
        self._newline = newline
        self._pool = pool or _get_default_pool()
        self._config = config or FileSystemConfig()
        self._metrics = metrics
        self._sandbox = sandbox or self._config.sandbox_root
        self._handle: AsyncFile | None = None

    def __await__(self):
        return self._open().__await__()

    async def _open(self) -> AsyncFile:
        pool = self._pool
        config = self._config
        path = self._path

        # Validate unless we're creating a new file in a known location
        safe_path = validate_path(path, config=config, sandbox=self._sandbox, operation="open")
        str_path = str(safe_path)

        def _do_open():
            return open(
                str_path,
                mode=self._mode,
                buffering=self._buffering,
                encoding=self._encoding,
                errors=self._errors_param,
                newline=self._newline,
            )

        try:
            fp = await pool.run(_do_open)
        except Exception as exc:
            raise wrap_os_error(exc, "open", str_path) from exc

        self._handle = AsyncFile(
            fp=fp,
            pool=pool,
            name=str_path,
            mode=self._mode,
            write_buffer_size=config.write_buffer_size,
        )
        return self._handle

    async def __aenter__(self) -> AsyncFile:
        return await self._open()

    async def __aexit__(self, *exc: object) -> None:
        if self._handle:
            await self._handle.close()


def async_open(
    path: str | Path,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    *,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    metrics: FileSystemMetrics | None = None,
    sandbox: str | Path | None = None,
) -> _AsyncOpenContext:
    """
    Open a file asynchronously.

    Drop-in replacement for ``aiofiles.open()``.  Returns a context
    manager that yields an :class:`AsyncFile`.

    Parameters
    ----------
    path
        File path to open.
    mode
        File mode (``"r"``, ``"rb"``, ``"w"``, ``"wb"``, ``"a"``, etc.).
    buffering
        Buffering policy (same as built-in ``open``).
    encoding
        Text encoding (e.g., ``"utf-8"``).
    errors
        How encoding errors are handled.
    newline
        Newline translation mode.
    pool
        Filesystem pool. Uses default if not provided.
    config
        Filesystem configuration.
    metrics
        Metrics recorder.
    sandbox
        Sandbox root for path validation.

    Returns
    -------
    _AsyncOpenContext
        Awaitable context manager yielding :class:`AsyncFile`.

    Example
    -------
    ::

        async with async_open("data.txt", "r", encoding="utf-8") as f:
            content = await f.read()
    """
    return _AsyncOpenContext(
        path,
        mode,
        buffering,
        encoding,
        errors,
        newline,
        pool=pool,
        config=config,
        metrics=metrics,
        sandbox=sandbox,
    )


# ═══════════════════════════════════════════════════════════════════════════
# read_file / write_file — Whole-file operations
# ═══════════════════════════════════════════════════════════════════════════


async def read_file(
    path: str | Path,
    *,
    encoding: str | None = None,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    metrics: FileSystemMetrics | None = None,
    sandbox: str | Path | None = None,
) -> str | bytes:
    """
    Read the entire contents of a file.

    Returns ``str`` when *encoding* is specified, ``bytes`` otherwise.
    """
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="read")
    str_path = str(safe)

    def _read():
        if encoding:
            return safe.read_text(encoding=encoding)
        return safe.read_bytes()

    t0 = time.monotonic_ns()
    try:
        result = await _pool.run(_read)
    except Exception as exc:
        if metrics:
            metrics.record_error("read")
        raise wrap_os_error(exc, "read", str_path) from exc

    if metrics:
        elapsed = time.monotonic_ns() - t0
        size = len(result) if isinstance(result, (bytes, str)) else 0
        metrics.record_read(size, elapsed)

    return result


async def write_file(
    path: str | Path,
    data: str | bytes,
    *,
    encoding: str = "utf-8",
    atomic: bool | None = None,
    mkdir: bool = False,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    metrics: FileSystemMetrics | None = None,
    sandbox: str | Path | None = None,
) -> int:
    """
    Write data to a file.

    Parameters
    ----------
    path
        Destination file path.
    data
        Content to write (``str`` or ``bytes``).
    encoding
        Encoding for string data.
    atomic
        If ``True``, write to a temp file then ``os.replace()``.
        Defaults to config.atomic_writes.
    mkdir
        If ``True``, create parent directories.
    pool, config, metrics, sandbox
        Standard filesystem parameters.

    Returns
    -------
    int
        Number of bytes written.
    """
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    use_atomic = atomic if atomic is not None else _config.atomic_writes
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="write")
    str_path = str(safe)

    raw = data.encode(encoding) if isinstance(data, str) else data

    def _write():
        if mkdir:
            safe.parent.mkdir(parents=True, exist_ok=True)

        if use_atomic:
            import tempfile as _tf

            fd, tmp = _tf.mkstemp(dir=str(safe.parent), prefix=".aquilia-tmp-")
            try:
                os.write(fd, raw)
                if _config.fsync_on_write:
                    os.fsync(fd)
                os.close(fd)
                os.replace(tmp, str_path)
            except BaseException:
                os.close(fd) if not _is_fd_closed(fd) else None
                with contextlib.suppress(OSError):
                    os.unlink(tmp)
                raise
        else:
            with open(str_path, "wb") as f:
                f.write(raw)
                if _config.fsync_on_write:
                    os.fsync(f.fileno())
        return len(raw)

    t0 = time.monotonic_ns()
    try:
        n = await _pool.run(_write)
    except Exception as exc:
        if metrics:
            metrics.record_error("write")
        raise wrap_os_error(exc, "write", str_path) from exc

    if metrics:
        elapsed = time.monotonic_ns() - t0
        metrics.record_write(n, elapsed)
    return n


async def append_file(
    path: str | Path,
    data: str | bytes,
    *,
    encoding: str = "utf-8",
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    metrics: FileSystemMetrics | None = None,
    sandbox: str | Path | None = None,
) -> int:
    """Append data to a file.  Creates the file if it doesn't exist."""
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="append")
    str_path = str(safe)

    raw = data.encode(encoding) if isinstance(data, str) else data

    def _append():
        with open(str_path, "ab") as f:
            f.write(raw)
            if _config.fsync_on_write:
                os.fsync(f.fileno())
        return len(raw)

    t0 = time.monotonic_ns()
    try:
        n = await _pool.run(_append)
    except Exception as exc:
        if metrics:
            metrics.record_error("append")
        raise wrap_os_error(exc, "append", str_path) from exc

    if metrics:
        elapsed = time.monotonic_ns() - t0
        metrics.record_write(n, elapsed)
    return n


# ═══════════════════════════════════════════════════════════════════════════
# File management operations
# ═══════════════════════════════════════════════════════════════════════════


async def copy_file(
    src: str | Path,
    dst: str | Path,
    *,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
) -> str:
    """
    Copy a file from *src* to *dst*.

    Preserves metadata.  Returns the destination path.
    """
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    _sb = sandbox or _config.sandbox_root
    safe_src = validate_path(src, config=_config, sandbox=_sb, operation="copy_src")
    safe_dst = validate_path(dst, config=_config, sandbox=_sb, operation="copy_dst")

    def _copy():
        return str(shutil.copy2(str(safe_src), str(safe_dst)))

    try:
        return await _pool.run(_copy)
    except Exception as exc:
        raise wrap_os_error(exc, "copy", str(safe_src)) from exc


async def move_file(
    src: str | Path,
    dst: str | Path,
    *,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
) -> str:
    """
    Move (rename) a file from *src* to *dst*.

    Uses ``os.replace`` for atomic moves on the same filesystem,
    falling back to ``shutil.move`` for cross-device moves.
    """
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    _sb = sandbox or _config.sandbox_root
    safe_src = validate_path(src, config=_config, sandbox=_sb, operation="move_src")
    safe_dst = validate_path(dst, config=_config, sandbox=_sb, operation="move_dst")

    def _move():
        try:
            os.replace(str(safe_src), str(safe_dst))
        except OSError:
            shutil.move(str(safe_src), str(safe_dst))
        return str(safe_dst)

    try:
        return await _pool.run(_move)
    except Exception as exc:
        raise wrap_os_error(exc, "move", str(safe_src)) from exc


async def delete_file(
    path: str | Path,
    *,
    missing_ok: bool = False,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
) -> bool:
    """
    Delete a file.

    Returns ``True`` if the file was deleted, ``False`` if it didn't
    exist (only when *missing_ok* is ``True``).
    """
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="delete")

    def _delete():
        try:
            os.unlink(str(safe))
            return True
        except FileNotFoundError:
            if missing_ok:
                return False
            raise

    try:
        return await _pool.run(_delete)
    except Exception as exc:
        raise wrap_os_error(exc, "delete", str(safe)) from exc


async def file_exists(
    path: str | Path,
    *,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
) -> bool:
    """Check if a file exists."""
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="exists")
    return await _pool.run(safe.exists)


@dataclass(frozen=True, slots=True)
class FileStat:
    """File status information."""

    size: int
    mode: int
    uid: int
    gid: int
    atime_ns: int
    mtime_ns: int
    ctime_ns: int
    is_file: bool
    is_dir: bool
    is_symlink: bool

    @property
    def atime(self) -> float:
        return self.atime_ns / 1_000_000_000

    @property
    def mtime(self) -> float:
        return self.mtime_ns / 1_000_000_000

    @property
    def ctime(self) -> float:
        return self.ctime_ns / 1_000_000_000


async def file_stat(
    path: str | Path,
    *,
    follow_symlinks: bool | None = None,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
) -> FileStat:
    """Get file status (stat) information."""
    _pool = pool or _get_default_pool()
    _config = config or FileSystemConfig()
    _follow = follow_symlinks if follow_symlinks is not None else _config.follow_symlinks
    safe = validate_path(path, config=_config, sandbox=sandbox or _config.sandbox_root, operation="stat")

    def _stat():
        st = os.stat(str(safe)) if _follow else os.lstat(str(safe))
        p = Path(str(safe))
        return FileStat(
            size=st.st_size,
            mode=st.st_mode,
            uid=st.st_uid,
            gid=st.st_gid,
            atime_ns=st.st_atime_ns,
            mtime_ns=st.st_mtime_ns,
            ctime_ns=st.st_ctime_ns,
            is_file=p.is_file(),
            is_dir=p.is_dir(),
            is_symlink=p.is_symlink(),
        )

    try:
        return await _pool.run(_stat)
    except Exception as exc:
        raise wrap_os_error(exc, "stat", str(safe)) from exc


# ═══════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════


def _is_fd_closed(fd: int) -> bool:
    """Check if a file descriptor is already closed."""
    try:
        os.fstat(fd)
        return False
    except OSError:
        return True


def _get_default_pool() -> FileSystemPool:
    """Get the default filesystem pool (lazy singleton)."""
    from ._path import _get_default_pool as _get

    return _get()
