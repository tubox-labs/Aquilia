"""
Async Temporary Files — Secure temporary file and directory management.

Provides async context managers for creating temporary files and
directories with automatic cleanup.

Usage::

    from aquilia.filesystem import async_tempfile, async_tempdir

    async with async_tempfile(suffix=".json") as tmp:
        await tmp.write(b'{"key": "value"}')
        await tmp.flush()
        # tmp.name is the path to the temp file

    async with async_tempdir(prefix="aquilia-") as tmpdir:
        # tmpdir is an AsyncPath to the temp directory
        await (tmpdir / "data.txt").write_text("hello")
    # Directory and contents are deleted on exit
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union

from ._config import FileSystemConfig
from ._errors import wrap_os_error
from ._handle import AsyncFile
from ._pool import FileSystemPool


class AsyncTemporaryFile:
    """
    Async temporary file with automatic cleanup.

    Creates a named temporary file that is deleted when the context
    manager exits.  The file is open for writing by default.

    Usage::

        async with AsyncTemporaryFile(suffix=".dat") as tmp:
            await tmp.write(data)
            path = tmp.name  # Use the path for something
        # File is deleted here
    """

    __slots__ = (
        "_suffix",
        "_prefix",
        "_dir",
        "_pool",
        "_config",
        "_handle",
        "_path",
        "_delete",
    )

    def __init__(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmp-",
        dir: Optional[Union[str, Path]] = None,
        pool: Optional[FileSystemPool] = None,
        config: Optional[FileSystemConfig] = None,
        delete: bool = True,
    ) -> None:
        self._suffix = suffix
        self._prefix = prefix
        self._dir = str(dir) if dir else None
        self._pool = pool or _get_default_pool()
        self._config = config or FileSystemConfig()
        self._handle: Optional[AsyncFile] = None
        self._path: Optional[str] = None
        self._delete = delete

        # Use configured temp dir if not explicitly provided
        if self._dir is None and self._config.temp_dir:
            self._dir = self._config.temp_dir

    @property
    def name(self) -> str:
        """The temporary file path."""
        return self._path or ""

    async def __aenter__(self) -> AsyncFile:
        """Create and open the temporary file."""
        def _create():
            fd, path = tempfile.mkstemp(
                suffix=self._suffix,
                prefix=self._prefix,
                dir=self._dir,
            )
            # Convert FD to a Python file object
            fp = os.fdopen(fd, "w+b")
            return fp, path

        try:
            fp, self._path = await self._pool.run(_create)
        except Exception as exc:
            raise wrap_os_error(exc, "create_tempfile", self._dir or "<tempdir>") from exc

        self._handle = AsyncFile(
            fp=fp,
            pool=self._pool,
            name=self._path,
            mode="w+b",
            write_buffer_size=self._config.write_buffer_size,
        )
        return self._handle

    async def __aexit__(self, *exc: object) -> None:
        """Close and delete the temporary file."""
        if self._handle:
            await self._handle.close()

        if self._delete and self._path:
            try:
                await self._pool.run(os.unlink, self._path)
            except FileNotFoundError:
                pass
            except Exception:
                pass  # Best-effort cleanup


class AsyncTemporaryDirectory:
    """
    Async temporary directory with automatic cleanup.

    Creates a temporary directory that is recursively deleted when
    the context manager exits.

    Usage::

        async with AsyncTemporaryDirectory(prefix="build-") as tmpdir:
            # tmpdir is an AsyncPath
            await (tmpdir / "output.txt").write_text("result")
        # Directory and all contents deleted here
    """

    __slots__ = ("_suffix", "_prefix", "_dir", "_pool", "_config", "_path")

    def __init__(
        self,
        *,
        suffix: str = "",
        prefix: str = "aquilia-tmpdir-",
        dir: Optional[Union[str, Path]] = None,
        pool: Optional[FileSystemPool] = None,
        config: Optional[FileSystemConfig] = None,
    ) -> None:
        self._suffix = suffix
        self._prefix = prefix
        self._dir = str(dir) if dir else None
        self._pool = pool or _get_default_pool()
        self._config = config or FileSystemConfig()
        self._path: Optional[str] = None

        if self._dir is None and self._config.temp_dir:
            self._dir = self._config.temp_dir

    @property
    def name(self) -> str:
        """The temporary directory path."""
        return self._path or ""

    async def __aenter__(self):
        """Create the temporary directory.  Returns an ``AsyncPath``."""
        from ._path import AsyncPath

        def _create():
            return tempfile.mkdtemp(
                suffix=self._suffix,
                prefix=self._prefix,
                dir=self._dir,
            )

        try:
            self._path = await self._pool.run(_create)
        except Exception as exc:
            raise wrap_os_error(exc, "create_tempdir", self._dir or "<tempdir>") from exc

        return AsyncPath(self._path, pool=self._pool, config=self._config)

    async def __aexit__(self, *exc: object) -> None:
        """Recursively delete the temporary directory."""
        if self._path:
            try:
                await self._pool.run(shutil.rmtree, self._path, True)
            except Exception:
                pass  # Best-effort cleanup


# ═══════════════════════════════════════════════════════════════════════════
# Convenience aliases
# ═══════════════════════════════════════════════════════════════════════════

async_tempfile = AsyncTemporaryFile
async_tempdir = AsyncTemporaryDirectory


def _get_default_pool() -> FileSystemPool:
    """Get the default filesystem pool (lazy singleton)."""
    from ._path import _get_default_pool as _get
    return _get()
