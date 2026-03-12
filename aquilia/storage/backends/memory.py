"""
In-Memory Storage Backend.

Stores files entirely in memory.  Ideal for tests, ephemeral caches,
and CI environments where no filesystem or cloud access is available.

Usage::

    from aquilia.storage.backends.memory import MemoryStorage
    from aquilia.storage.configs import MemoryConfig

    storage = MemoryStorage(MemoryConfig())
    name = await storage.save("test.txt", b"hello world")
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import (
    BinaryIO,
)

from ..base import (
    FileNotFoundError,
    StorageBackend,
    StorageFile,
    StorageFullError,
    StorageMetadata,
)
from ..configs import MemoryConfig


class MemoryStorage(StorageBackend):
    """
    In-memory storage backend.

    All data lives in ``_store`` (a plain dict).  Thread-safe for
    single-event-loop asyncio usage.
    """

    __slots__ = ("_config", "_store", "_meta")

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._config = config or MemoryConfig()
        self._store: dict[str, bytes] = {}
        self._meta: dict[str, StorageMetadata] = {}

    @property
    def backend_name(self) -> str:
        return "memory"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        pass  # Nothing to initialise

    async def shutdown(self) -> None:
        self._store.clear()
        self._meta.clear()

    async def ping(self) -> bool:
        return True

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

        if not overwrite and name in self._store:
            name = self.generate_filename(name)

        data = await self._read_content(content)

        # Quota check
        if self._config.max_size > 0:
            total = sum(len(v) for v in self._store.values()) + len(data)
            if total > self._config.max_size:
                raise StorageFullError(
                    f"Memory storage quota exceeded ({self._config.max_size} bytes)",
                    backend="memory",
                    path=name,
                )

        now = datetime.now(timezone.utc)
        self._store[name] = data
        self._meta[name] = StorageMetadata(
            name=name,
            size=len(data),
            content_type=content_type or self.guess_content_type(name),
            last_modified=now,
            created_at=now,
            metadata=metadata or {},
        )
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        name = self._normalize_path(name)
        if name not in self._store:
            raise FileNotFoundError(f"File not found: {name}", backend="memory", path=name)
        return StorageFile(
            name=name,
            mode=mode,
            content=self._store[name],
            meta=self._meta.get(name),
        )

    async def delete(self, name: str) -> None:
        name = self._normalize_path(name)
        self._store.pop(name, None)
        self._meta.pop(name, None)

    async def exists(self, name: str) -> bool:
        return self._normalize_path(name) in self._store

    async def stat(self, name: str) -> StorageMetadata:
        name = self._normalize_path(name)
        if name not in self._meta:
            raise FileNotFoundError(f"File not found: {name}", backend="memory", path=name)
        return self._meta[name]

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        prefix = (path.rstrip("/") + "/") if path else ""
        dirs: set[str] = set()
        files: list[str] = []

        for key in self._store:
            if not key.startswith(prefix):
                continue
            relative = key[len(prefix) :]
            if "/" in relative:
                dirs.add(relative.split("/")[0])
            else:
                files.append(relative)

        return sorted(dirs), sorted(files)

    async def size(self, name: str) -> int:
        name = self._normalize_path(name)
        if name not in self._store:
            raise FileNotFoundError(f"File not found: {name}", backend="memory", path=name)
        return len(self._store[name])

    async def url(self, name: str, expire: int | None = None) -> str:
        name = self._normalize_path(name)
        return f"memory:///{name}"

    # -- Internal ----------------------------------------------------------

    # _read_content inherited from StorageBackend
