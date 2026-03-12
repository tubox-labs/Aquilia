"""
Local Filesystem Storage Backend.

Stores files on the local filesystem.  Supports auto-directory creation,
configurable permissions, and file-based URL serving.

Usage::

    from aquilia.storage.backends.local import LocalStorage
    from aquilia.storage.configs import LocalConfig

    storage = LocalStorage(LocalConfig(root="/var/uploads"))
    await storage.initialize()
    name = await storage.save("photos/avatar.png", image_bytes)
"""

from __future__ import annotations

import os
import shutil
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    BinaryIO,
)

from ...filesystem._config import FileSystemConfig as _FsConfig
from ...filesystem._pool import FileSystemPool as _FsPool
from ..base import (
    FileNotFoundError,
    PermissionError,
    StorageBackend,
    StorageFile,
    StorageMetadata,
)
from ..configs import LocalConfig

# Lazy-initialised shared pool for all LocalStorage instances
_pool: _FsPool | None = None


def _get_pool() -> _FsPool:
    global _pool
    if _pool is None:
        _pool = _FsPool(_FsConfig())
        _pool.initialize()
    return _pool


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Files are stored under ``config.root`` with optional
    ``base_url`` for serving via HTTP.
    """

    __slots__ = ("_config", "_root")

    def __init__(self, config: LocalConfig) -> None:
        self._config = config
        self._root = Path(config.root).resolve()

    @property
    def backend_name(self) -> str:
        return "local"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        if self._config.create_dirs:
            self._root.mkdir(parents=True, exist_ok=True)

    async def ping(self) -> bool:
        return self._root.exists() and self._root.is_dir()

    # -- Core operations ---------------------------------------------------

    async def save(
        self,
        name: str,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        overwrite: bool = False,
    ) -> str:
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not overwrite and full.exists():
            name = self.generate_filename(name)
            full = self._full_path(name)

        # Ensure parent directories
        if self._config.create_dirs:
            full.parent.mkdir(parents=True, exist_ok=True)

        data = await self._read_content(content)

        def _write() -> None:
            full.write_bytes(data)
            if self._config.permissions:
                os.chmod(full, self._config.permissions)

        await _get_pool().run(_write)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not full.exists():
            raise FileNotFoundError(f"File not found: {name}", backend="local", path=name)

        def _read() -> bytes:
            return full.read_bytes()

        data = await _get_pool().run(_read)
        meta = await self.stat(name)
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        name = self._normalize_path(name)
        full = self._full_path(name)

        def _delete() -> None:
            if full.exists():
                full.unlink()

        await _get_pool().run(_delete)

    async def exists(self, name: str) -> bool:
        name = self._normalize_path(name)
        full = self._full_path(name)
        return await _get_pool().run(full.exists)

    async def stat(self, name: str) -> StorageMetadata:
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not full.exists():
            raise FileNotFoundError(f"File not found: {name}", backend="local", path=name)

        def _stat() -> os.stat_result:
            return full.stat()

        st = await _get_pool().run(_stat)

        return StorageMetadata(
            name=name,
            size=st.st_size,
            content_type=self.guess_content_type(name),
            last_modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            created_at=datetime.fromtimestamp(st.st_ctime, tz=timezone.utc),
        )

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        target = self._root / path if path else self._root

        def _list() -> tuple[list[str], list[str]]:
            dirs: list[str] = []
            files: list[str] = []
            if not target.exists():
                return dirs, files
            for entry in target.iterdir():
                if entry.is_dir():
                    dirs.append(entry.name)
                else:
                    files.append(entry.name)
            return dirs, files

        return await _get_pool().run(_list)

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: int | None = None) -> str:
        name = self._normalize_path(name)
        base = self._config.base_url.rstrip("/")
        return f"{base}/{name}"

    async def copy(self, src: str, dst: str) -> str:
        src_path = self._full_path(self._normalize_path(src))
        dst = self._normalize_path(dst)
        dst_path = self._full_path(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src}", backend="local", path=src)

        if self._config.create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)

        def _copy() -> None:
            shutil.copy2(str(src_path), str(dst_path))

        await _get_pool().run(_copy)
        return dst

    # -- Internal ----------------------------------------------------------

    def _full_path(self, name: str) -> Path:
        """Resolve name to full path, ensuring it stays within root."""
        full = (self._root / name).resolve()
        if not str(full).startswith(str(self._root)):
            raise PermissionError(f"Path traversal blocked: {name}", backend="local", path=name)
        return full

    # _read_content inherited from StorageBackend
