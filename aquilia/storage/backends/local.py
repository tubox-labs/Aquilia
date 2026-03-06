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

import asyncio
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    BinaryIO,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from ..base import (
    FileNotFoundError,
    PermissionError,
    StorageBackend,
    StorageFile,
    StorageFullError,
    StorageMetadata,
)
from ..configs import LocalConfig


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
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], StorageFile],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
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

        await asyncio.get_event_loop().run_in_executor(None, _write)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not full.exists():
            raise FileNotFoundError(
                f"File not found: {name}", backend="local", path=name
            )

        def _read() -> bytes:
            return full.read_bytes()

        data = await asyncio.get_event_loop().run_in_executor(None, _read)
        meta = await self.stat(name)
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        name = self._normalize_path(name)
        full = self._full_path(name)

        def _delete() -> None:
            if full.exists():
                full.unlink()

        await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def exists(self, name: str) -> bool:
        name = self._normalize_path(name)
        full = self._full_path(name)
        return await asyncio.get_event_loop().run_in_executor(None, full.exists)

    async def stat(self, name: str) -> StorageMetadata:
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not full.exists():
            raise FileNotFoundError(
                f"File not found: {name}", backend="local", path=name
            )

        def _stat() -> os.stat_result:
            return full.stat()

        st = await asyncio.get_event_loop().run_in_executor(None, _stat)

        return StorageMetadata(
            name=name,
            size=st.st_size,
            content_type=self.guess_content_type(name),
            last_modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            created_at=datetime.fromtimestamp(st.st_ctime, tz=timezone.utc),
        )

    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        target = self._root / path if path else self._root

        def _list() -> Tuple[List[str], List[str]]:
            dirs: List[str] = []
            files: List[str] = []
            if not target.exists():
                return dirs, files
            for entry in target.iterdir():
                if entry.is_dir():
                    dirs.append(entry.name)
                else:
                    files.append(entry.name)
            return dirs, files

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: Optional[int] = None) -> str:
        name = self._normalize_path(name)
        base = self._config.base_url.rstrip("/")
        return f"{base}/{name}"

    async def copy(self, src: str, dst: str) -> str:
        src_path = self._full_path(self._normalize_path(src))
        dst = self._normalize_path(dst)
        dst_path = self._full_path(dst)

        if not src_path.exists():
            raise FileNotFoundError(
                f"Source not found: {src}", backend="local", path=src
            )

        if self._config.create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)

        def _copy() -> None:
            shutil.copy2(str(src_path), str(dst_path))

        await asyncio.get_event_loop().run_in_executor(None, _copy)
        return dst

    # -- Internal ----------------------------------------------------------

    def _full_path(self, name: str) -> Path:
        """Resolve name to full path, ensuring it stays within root."""
        full = (self._root / name).resolve()
        if not str(full).startswith(str(self._root)):
            raise PermissionError(
                f"Path traversal blocked: {name}", backend="local", path=name
            )
        return full

    @staticmethod
    async def _read_content(
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], StorageFile],
    ) -> bytes:
        """Normalise any content type to bytes."""
        if isinstance(content, bytes):
            return content
        if isinstance(content, StorageFile):
            return await content.read()
        if hasattr(content, "read"):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, content.read)  # type: ignore
        # AsyncIterator
        parts: list[bytes] = []
        async for chunk in content:  # type: ignore
            parts.append(chunk)
        return b"".join(parts)
