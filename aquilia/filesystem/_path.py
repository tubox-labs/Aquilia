"""
Async Path — Async equivalent of ``pathlib.Path``.

Wraps ``pathlib.Path`` and delegates all I/O-performing methods to the
dedicated filesystem thread pool.  Non-I/O operations (name, parent,
suffix, ``/`` operator, etc.) remain synchronous for zero overhead.

Usage::

    from aquilia.filesystem import AsyncPath

    path = AsyncPath("/app/data/config.json")

    # Sync (no I/O):
    print(path.name)      # "config.json"
    print(path.parent)    # AsyncPath("/app/data")
    print(path.suffix)    # ".json"

    # Async (I/O):
    exists = await path.exists()
    data = await path.read_bytes()
    await path.write_text("hello")
    await (path.parent / "subdir").mkdir(parents=True, exist_ok=True)

    # Async iteration:
    async for child in path.parent.iterdir():
        print(child.name)
"""

from __future__ import annotations

import os
import stat as stat_module
from pathlib import Path, PurePosixPath
from typing import (
    Any,
    AsyncIterator,
    Optional,
    Union,
)

from ._config import FileSystemConfig
from ._errors import wrap_os_error
from ._handle import AsyncFile
from ._pool import FileSystemPool


class AsyncPath:
    """
    Async filesystem path with I/O delegation to the thread pool.

    The underlying ``pathlib.Path`` is used for path arithmetic.
    All methods that touch the filesystem are ``async``.
    """

    __slots__ = ("_path", "_pool", "_config")

    def __init__(
        self,
        *args: Union[str, Path, "AsyncPath"],
        pool: Optional[FileSystemPool] = None,
        config: Optional[FileSystemConfig] = None,
    ) -> None:
        parts = []
        for a in args:
            if isinstance(a, AsyncPath):
                parts.append(str(a._path))
            elif isinstance(a, Path):
                parts.append(str(a))
            else:
                parts.append(a)
        self._path = Path(*parts) if parts else Path(".")
        self._pool = pool or _get_default_pool()
        self._config = config

    # ── Sync Properties (no I/O) ─────────────────────────────────────────

    @property
    def name(self) -> str:
        """The final component of the path."""
        return self._path.name

    @property
    def stem(self) -> str:
        """The final component without suffix."""
        return self._path.stem

    @property
    def suffix(self) -> str:
        """The file extension."""
        return self._path.suffix

    @property
    def suffixes(self) -> list[str]:
        """All file extensions."""
        return self._path.suffixes

    @property
    def parent(self) -> "AsyncPath":
        """The parent directory."""
        return AsyncPath(self._path.parent, pool=self._pool, config=self._config)

    @property
    def parents(self) -> tuple["AsyncPath", ...]:
        """All ancestor directories."""
        return tuple(
            AsyncPath(p, pool=self._pool, config=self._config)
            for p in self._path.parents
        )

    @property
    def parts(self) -> tuple[str, ...]:
        """Path components as a tuple."""
        return self._path.parts

    @property
    def anchor(self) -> str:
        """The drive + root (e.g. '/' or 'C:\\')."""
        return self._path.anchor

    @property
    def drive(self) -> str:
        """The drive letter (Windows) or empty string."""
        return self._path.drive

    @property
    def root(self) -> str:
        """The root of the path."""
        return self._path.root

    def is_absolute(self) -> bool:
        """Whether the path is absolute."""
        return self._path.is_absolute()

    def is_relative_to(self, other: Union[str, Path, "AsyncPath"]) -> bool:
        """Whether this path is relative to another."""
        other_path = _to_path(other)
        return self._path.is_relative_to(other_path)

    @property
    def path(self) -> Path:
        """Access the underlying ``pathlib.Path``."""
        return self._path

    # ── Path Arithmetic (no I/O) ─────────────────────────────────────────

    def __truediv__(self, other: Union[str, Path, "AsyncPath"]) -> "AsyncPath":
        """Join paths with ``/`` operator."""
        other_str = str(_to_path(other)) if not isinstance(other, str) else other
        return AsyncPath(
            self._path / other_str,
            pool=self._pool,
            config=self._config,
        )

    def __rtruediv__(self, other: Union[str, Path]) -> "AsyncPath":
        return AsyncPath(
            Path(str(other)) / self._path,
            pool=self._pool,
            config=self._config,
        )

    def with_name(self, name: str) -> "AsyncPath":
        """Return a new path with the filename changed."""
        return AsyncPath(self._path.with_name(name), pool=self._pool, config=self._config)

    def with_stem(self, stem: str) -> "AsyncPath":
        """Return a new path with the stem changed."""
        return AsyncPath(self._path.with_stem(stem), pool=self._pool, config=self._config)

    def with_suffix(self, suffix: str) -> "AsyncPath":
        """Return a new path with the suffix changed."""
        return AsyncPath(self._path.with_suffix(suffix), pool=self._pool, config=self._config)

    def relative_to(self, other: Union[str, Path, "AsyncPath"]) -> "AsyncPath":
        """Return a relative version of this path."""
        other_path = _to_path(other)
        return AsyncPath(
            self._path.relative_to(other_path),
            pool=self._pool,
            config=self._config,
        )

    def resolve(self) -> "AsyncPath":
        """
        Resolve the path to an absolute canonical path.

        Note: ``os.path.realpath`` is fast and usually cached by the OS,
        so this is kept synchronous for ergonomics.
        """
        return AsyncPath(
            Path(os.path.realpath(str(self._path))),
            pool=self._pool,
            config=self._config,
        )

    def joinpath(self, *others: Union[str, Path, "AsyncPath"]) -> "AsyncPath":
        """Join one or more path components."""
        parts = [str(_to_path(o)) if not isinstance(o, str) else o for o in others]
        return AsyncPath(
            self._path.joinpath(*parts),
            pool=self._pool,
            config=self._config,
        )

    # ── Async Queries (I/O) ──────────────────────────────────────────────

    async def exists(self) -> bool:
        """Check whether the path exists on disk."""
        try:
            return await self._pool.run(self._path.exists)
        except OSError:
            return False

    async def is_file(self) -> bool:
        """Check whether the path is a regular file."""
        try:
            return await self._pool.run(self._path.is_file)
        except OSError:
            return False

    async def is_dir(self) -> bool:
        """Check whether the path is a directory."""
        try:
            return await self._pool.run(self._path.is_dir)
        except OSError:
            return False

    async def is_symlink(self) -> bool:
        """Check whether the path is a symbolic link."""
        try:
            return await self._pool.run(self._path.is_symlink)
        except OSError:
            return False

    async def stat(self) -> os.stat_result:
        """Get file status (size, permissions, timestamps, etc.)."""
        try:
            return await self._pool.run(self._path.stat)
        except Exception as exc:
            raise wrap_os_error(exc, "stat", str(self._path)) from exc

    async def lstat(self) -> os.stat_result:
        """Like ``stat()`` but don't follow symlinks."""
        try:
            return await self._pool.run(self._path.lstat)
        except Exception as exc:
            raise wrap_os_error(exc, "lstat", str(self._path)) from exc

    # ── Async Reading (I/O) ──────────────────────────────────────────────

    async def read_bytes(self) -> bytes:
        """Read the entire file as bytes."""
        try:
            return await self._pool.run(self._path.read_bytes)
        except Exception as exc:
            raise wrap_os_error(exc, "read_bytes", str(self._path)) from exc

    async def read_text(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        """Read the entire file as text."""
        def _read() -> str:
            return self._path.read_text(encoding=encoding, errors=errors)
        try:
            return await self._pool.run(_read)
        except Exception as exc:
            raise wrap_os_error(exc, "read_text", str(self._path)) from exc

    async def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> AsyncFile:
        """
        Open the file and return an ``AsyncFile`` handle.

        Usage::

            async with await path.open("r") as f:
                content = await f.read()
        """
        if encoding is None and "b" not in mode:
            encoding = "utf-8"

        def _open() -> Any:
            return self._path.open(
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )

        try:
            fp = await self._pool.run(_open)
        except Exception as exc:
            raise wrap_os_error(exc, "open", str(self._path)) from exc

        config = self._config or FileSystemConfig()
        return AsyncFile(
            fp=fp,
            pool=self._pool,
            name=str(self._path),
            mode=mode,
            write_buffer_size=config.write_buffer_size,
        )

    # ── Async Writing (I/O) ──────────────────────────────────────────────

    async def write_bytes(self, data: bytes) -> int:
        """Write bytes to the file (creates or overwrites)."""
        try:
            return await self._pool.run(self._path.write_bytes, data)
        except Exception as exc:
            raise wrap_os_error(exc, "write_bytes", str(self._path)) from exc

    async def write_text(
        self,
        data: str,
        encoding: str = "utf-8",
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> int:
        """Write text to the file (creates or overwrites)."""
        def _write() -> int:
            return self._path.write_text(
                data, encoding=encoding, errors=errors, newline=newline,
            )
        try:
            return await self._pool.run(_write)
        except Exception as exc:
            raise wrap_os_error(exc, "write_text", str(self._path)) from exc

    # ── Async Manipulation (I/O) ─────────────────────────────────────────

    async def mkdir(
        self,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        """Create a directory."""
        def _mkdir() -> None:
            self._path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
        try:
            await self._pool.run(_mkdir)
        except Exception as exc:
            raise wrap_os_error(exc, "mkdir", str(self._path)) from exc

    async def rmdir(self) -> None:
        """Remove an empty directory."""
        try:
            await self._pool.run(self._path.rmdir)
        except Exception as exc:
            raise wrap_os_error(exc, "rmdir", str(self._path)) from exc

    async def unlink(self, missing_ok: bool = False) -> None:
        """Remove a file or symbolic link."""
        def _unlink() -> None:
            self._path.unlink(missing_ok=missing_ok)
        try:
            await self._pool.run(_unlink)
        except Exception as exc:
            raise wrap_os_error(exc, "unlink", str(self._path)) from exc

    async def rename(self, target: Union[str, Path, "AsyncPath"]) -> "AsyncPath":
        """Rename/move the file or directory."""
        target_path = _to_path(target)
        def _rename() -> Path:
            return self._path.rename(target_path)
        try:
            result = await self._pool.run(_rename)
            return AsyncPath(result, pool=self._pool, config=self._config)
        except Exception as exc:
            raise wrap_os_error(exc, "rename", str(self._path)) from exc

    async def replace(self, target: Union[str, Path, "AsyncPath"]) -> "AsyncPath":
        """Atomically rename, replacing the target if it exists."""
        target_path = _to_path(target)
        def _replace() -> Path:
            return self._path.replace(target_path)
        try:
            result = await self._pool.run(_replace)
            return AsyncPath(result, pool=self._pool, config=self._config)
        except Exception as exc:
            raise wrap_os_error(exc, "replace", str(self._path)) from exc

    async def touch(self, mode: int = 0o666, exist_ok: bool = True) -> None:
        """Create the file (or update its access/modification times)."""
        def _touch() -> None:
            self._path.touch(mode=mode, exist_ok=exist_ok)
        try:
            await self._pool.run(_touch)
        except Exception as exc:
            raise wrap_os_error(exc, "touch", str(self._path)) from exc

    async def chmod(self, mode: int) -> None:
        """Change file permissions."""
        try:
            await self._pool.run(self._path.chmod, mode)
        except Exception as exc:
            raise wrap_os_error(exc, "chmod", str(self._path)) from exc

    # ── Async Iteration (I/O) ────────────────────────────────────────────

    async def iterdir(self) -> AsyncIterator["AsyncPath"]:
        """
        Iterate over directory contents.

        Yields ``AsyncPath`` objects for each entry.
        """
        def _iterdir() -> list[Path]:
            return list(self._path.iterdir())
        try:
            entries = await self._pool.run(_iterdir)
        except Exception as exc:
            raise wrap_os_error(exc, "iterdir", str(self._path)) from exc

        for entry in entries:
            yield AsyncPath(entry, pool=self._pool, config=self._config)

    async def glob(self, pattern: str) -> AsyncIterator["AsyncPath"]:
        """
        Glob for matching paths.

        Args:
            pattern: Glob pattern (e.g. ``"*.txt"``, ``"**/*.py"``).

        Yields:
            Matching ``AsyncPath`` objects.
        """
        def _glob() -> list[Path]:
            return list(self._path.glob(pattern))
        try:
            matches = await self._pool.run(_glob)
        except Exception as exc:
            raise wrap_os_error(exc, "glob", str(self._path)) from exc

        for match in matches:
            yield AsyncPath(match, pool=self._pool, config=self._config)

    async def rglob(self, pattern: str) -> AsyncIterator["AsyncPath"]:
        """
        Recursive glob for matching paths.

        Equivalent to ``glob("**/" + pattern)``.
        """
        def _rglob() -> list[Path]:
            return list(self._path.rglob(pattern))
        try:
            matches = await self._pool.run(_rglob)
        except Exception as exc:
            raise wrap_os_error(exc, "rglob", str(self._path)) from exc

        for match in matches:
            yield AsyncPath(match, pool=self._pool, config=self._config)

    # ── Dunder Methods ───────────────────────────────────────────────────

    def __str__(self) -> str:
        return str(self._path)

    def __repr__(self) -> str:
        return f"AsyncPath({str(self._path)!r})"

    def __fspath__(self) -> str:
        return str(self._path)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, AsyncPath):
            return self._path == other._path
        if isinstance(other, Path):
            return self._path == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._path)

    def __bool__(self) -> bool:
        return True


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _to_path(obj: Union[str, Path, "AsyncPath"]) -> Path:
    """Convert various path-like types to ``pathlib.Path``."""
    if isinstance(obj, AsyncPath):
        return obj._path
    if isinstance(obj, Path):
        return obj
    return Path(obj)


def _get_default_pool() -> FileSystemPool:
    """Get or create the default filesystem pool (lazy singleton)."""
    global _default_pool
    if _default_pool is None:
        _default_pool = FileSystemPool()
        _default_pool.initialize()
    return _default_pool


_default_pool: Optional[FileSystemPool] = None
