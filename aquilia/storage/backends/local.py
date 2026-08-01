"""
Local Filesystem Storage Backend.

Stores files on the local filesystem.  Supports auto-directory creation,
configurable permissions, and file-based URL serving.

Path containment is delegated to :func:`aquilia.filesystem.validate_path`,
the single canonical implementation used by the whole framework: paths are
canonicalised with ``os.path.realpath`` and checked component-wise against
the configured root, so a sibling directory such as ``/var/data-private``
can never satisfy a root of ``/var/data``.

Reads and writes stream through :mod:`aquilia.filesystem._streaming`, so
neither ``open`` nor ``save`` materialises a whole file in memory.

Usage::

    from aquilia.storage.backends.local import LocalStorage
    from aquilia.storage.configs import LocalConfig

    storage = LocalStorage(LocalConfig(root="/var/uploads"))
    await storage.initialize()
    name = await storage.save("photos/avatar.png", image_bytes)

    async with await storage.open(name) as f:
        async for chunk in f:
            ...
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    BinaryIO,
)

from aquilia.filesystem._config import FileSystemConfig as _FsConfig
from aquilia.filesystem._errors import PathTraversalFault as _PathTraversalFault
from aquilia.filesystem._pool import FileSystemPool as _FsPool
from aquilia.filesystem._security import validate_path as _validate_path
from aquilia.filesystem._streaming import AsyncFileStream as _AsyncFileStream
from aquilia.filesystem._streaming import AsyncWriteStream as _AsyncWriteStream
from aquilia.filesystem._streaming import stream_copy as _stream_copy
from aquilia.storage.base import FileNotFoundError, PermissionError, StorageBackend, StorageFile, StorageMetadata
from aquilia.storage.configs import LocalConfig
from aquilia.typing import PathLike

# Lazy-initialised shared pool for all LocalStorage instances
_pool: _FsPool | None = None

# Chunk size for streaming reads/writes (64 KiB)
_CHUNK_SIZE = 65_536


def _get_pool() -> _FsPool:
    """
    Return the process-wide filesystem thread pool, creating it on first use.

    Returns:
        The shared, initialised :class:`FileSystemPool`.
    """
    global _pool
    if _pool is None:
        _pool = _FsPool(_FsConfig())
        _pool.initialize()
    return _pool


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Files are stored under ``config.root`` with optional
    ``base_url`` for serving via HTTP.  ``config.root`` acts as a hard
    sandbox: every resolved path is checked for containment before any
    I/O is performed.

    Args:
        config: Backend configuration (root, base URL, permissions).

    Usage::

        storage = LocalStorage(LocalConfig(root="/var/uploads"))
        await storage.initialize()
        await storage.save("a/b.txt", b"data")
    """

    __slots__ = ("_config", "_root", "_fs_config")

    def __init__(self, config: LocalConfig) -> None:
        self._config = config
        self._root = Path(config.root).resolve()
        self._fs_config = _FsConfig(sandbox_root=str(self._root))

    @property
    def backend_name(self) -> str:
        return "local"

    @property
    def root(self) -> Path:
        """Resolved sandbox root for this backend."""
        return self._root

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
        """
        Write ``content`` under ``name``, streaming it to disk in chunks.

        Args:
            name: Relative path/key for the file.
            content: Bytes, file-like object, async iterator, or ``StorageFile``.
            content_type: Ignored by this backend (derived from the name on read).
            metadata: Ignored by this backend (no sidecar metadata store).
            overwrite: Replace an existing file instead of generating a new name.

        Returns:
            The name the file was actually stored under.

        Raises:
            PermissionError: If ``name`` escapes the configured root.
        """
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not overwrite and full.exists():
            name = self.generate_filename(name)
            full = self._full_path(name)

        # Ensure parent directories
        if self._config.create_dirs:
            await _get_pool().run(lambda: full.parent.mkdir(parents=True, exist_ok=True))

        async with _AsyncWriteStream(
            full,
            buffer_size=_CHUNK_SIZE,
            pool=_get_pool(),
            config=self._fs_config,
        ) as writer:
            async for chunk in self._iter_content(content):
                await writer.write(chunk)

        if self._config.permissions:
            await _get_pool().run(os.chmod, full, self._config.permissions)

        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        """
        Open a stored file for streaming reads.

        The returned :class:`StorageFile` is backed by a lazy chunk iterator;
        content is only materialised if the caller invokes ``read()``.
        Iterating with ``async for`` keeps memory bounded to one chunk.

        Args:
            name: Relative path/key.
            mode: Open mode, recorded on the returned file.

        Returns:
            A streaming ``StorageFile``.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If ``name`` escapes the configured root.
        """
        name = self._normalize_path(name)
        full = self._full_path(name)

        if not await _get_pool().run(full.exists):
            raise FileNotFoundError(f"File not found: {name}", backend="local", path=name)

        meta = await self.stat(name)
        stream = _AsyncFileStream(
            full,
            chunk_size=_CHUNK_SIZE,
            pool=_get_pool(),
            config=self._fs_config,
        )
        return StorageFile(name=name, mode=mode, meta=meta, chunks=stream.__aiter__())

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

        def _stat() -> os.stat_result | None:
            try:
                return full.stat()
            except OSError:
                return None

        st = await _get_pool().run(_stat)
        if st is None:
            raise FileNotFoundError(f"File not found: {name}", backend="local", path=name)

        return StorageMetadata(
            name=name,
            size=st.st_size,
            content_type=self.guess_content_type(name),
            last_modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            created_at=datetime.fromtimestamp(st.st_ctime, tz=timezone.utc),
        )

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        target = self._full_path(self._normalize_path(path)) if path else self._root

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
        """
        Copy a stored file, streaming it chunk-by-chunk.

        Args:
            src: Source relative path/key.
            dst: Destination relative path/key.

        Returns:
            The normalised destination name.

        Raises:
            FileNotFoundError: If the source does not exist.
            PermissionError: If either name escapes the configured root.
        """
        src_path = self._full_path(self._normalize_path(src))
        dst = self._normalize_path(dst)
        dst_path = self._full_path(dst)

        if not await _get_pool().run(src_path.exists):
            raise FileNotFoundError(f"Source not found: {src}", backend="local", path=src)

        if self._config.create_dirs:
            await _get_pool().run(lambda: dst_path.parent.mkdir(parents=True, exist_ok=True))

        await _stream_copy(
            src_path,
            dst_path,
            chunk_size=_CHUNK_SIZE,
            pool=_get_pool(),
            config=self._fs_config,
        )
        return dst

    # -- Internal ----------------------------------------------------------

    @staticmethod
    async def _iter_content(
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
    ) -> AsyncIterator[bytes]:
        """
        Yield ``content`` as a chunk stream without materialising it whole.

        Args:
            content: Bytes, ``StorageFile``, sync file-like, or async iterator.

        Yields:
            Successive byte chunks.
        """
        if isinstance(content, bytes):
            for i in range(0, len(content), _CHUNK_SIZE):
                yield content[i : i + _CHUNK_SIZE]
            return
        if isinstance(content, StorageFile):
            async for chunk in content:
                yield chunk
            return
        if hasattr(content, "read"):
            pool = _get_pool()
            while True:
                chunk = await pool.run(content.read, _CHUNK_SIZE)  # type: ignore[union-attr]
                if not chunk:
                    break
                yield chunk
            return
        async for chunk in content:  # type: ignore[union-attr]
            yield chunk

    def _full_path(self, name: PathLike) -> Path:
        """
        Resolve ``name`` against the root, enforcing sandbox containment.

        Delegates to the framework's canonical
        :func:`aquilia.filesystem.validate_path`, which resolves symlinks and
        compares path *components* rather than string prefixes.

        Args:
            name: Already-normalised relative path.

        Returns:
            The absolute, validated path inside the root.

        Raises:
            PermissionError: If the resolved path lies outside the root.
        """
        try:
            return _validate_path(
                self._root / name,
                config=self._fs_config,
                sandbox=self._root,
                operation="storage.local",
            )
        except _PathTraversalFault as exc:
            raise PermissionError(
                f"Path traversal blocked: {name}",
                backend="local",
                path=str(name),
            ) from exc

    # _read_content inherited from StorageBackend
