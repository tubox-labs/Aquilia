"""
SFTP / SSH Storage Backend.

Stores files on a remote server over SFTP.
Requires ``paramiko`` (``pip install paramiko``).

Usage::

    from aquilia.storage.backends.sftp import SFTPStorage
    from aquilia.storage.configs import SFTPConfig

    storage = SFTPStorage(SFTPConfig(
        host="files.example.com", username="deploy", key_path="~/.ssh/id_rsa"
    ))
    await storage.initialize()
    name = await storage.save("releases/v2.0.tar.gz", archive_bytes)
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import stat as stat_module
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import (
    Any,
    BinaryIO,
)

from ..base import (
    BackendUnavailableError,
    FileNotFoundError,
    StorageBackend,
    StorageFile,
    StorageMetadata,
)
from ..configs import SFTPConfig


class SFTPStorage(StorageBackend):
    """
    SFTP storage backend.

    Uses ``paramiko`` for SSH/SFTP transport.
    All I/O is offloaded to a thread executor.
    """

    __slots__ = ("_config", "_transport", "_sftp")

    def __init__(self, config: SFTPConfig) -> None:
        self._config = config
        self._transport: Any = None
        self._sftp: Any = None

    @property
    def backend_name(self) -> str:
        return "sftp"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        try:
            import paramiko
        except ImportError:
            raise BackendUnavailableError(
                "SFTP backend requires 'paramiko'. Install: pip install paramiko",
                backend="sftp",
            )

        loop = asyncio.get_event_loop()

        def _connect() -> tuple:
            transport = paramiko.Transport((self._config.host, self._config.port))

            if self._config.key_path:
                key_path = os.path.expanduser(self._config.key_path)
                pkey = paramiko.RSAKey.from_private_key_file(key_path, password=self._config.key_passphrase)
                transport.connect(username=self._config.username, pkey=pkey)
            elif self._config.password:
                transport.connect(
                    username=self._config.username,
                    password=self._config.password,
                )
            else:
                raise BackendUnavailableError(
                    "SFTP config requires either key_path or password",
                    backend="sftp",
                )

            sftp = paramiko.SFTPClient.from_transport(transport)
            return transport, sftp

        self._transport, self._sftp = await loop.run_in_executor(None, _connect)

    async def shutdown(self) -> None:
        loop = asyncio.get_event_loop()

        def _close() -> None:
            if self._sftp:
                with contextlib.suppress(Exception):
                    self._sftp.close()
            if self._transport:
                with contextlib.suppress(Exception):
                    self._transport.close()

        await loop.run_in_executor(None, _close)
        self._sftp = None
        self._transport = None

    async def ping(self) -> bool:
        if not self._transport:
            return False
        return self._transport.is_active()

    # -- Core operations ---------------------------------------------------

    def _remote_path(self, name: str) -> str:
        name = self._normalize_path(name)
        root = self._config.root.rstrip("/")
        return f"{root}/{name}"

    async def save(
        self,
        name: str,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        overwrite: bool = False,
    ) -> str:
        self._ensure_sftp()
        name = self._normalize_path(name)

        if not overwrite and await self.exists(name):
            name = self.generate_filename(name)

        remote = self._remote_path(name)
        data = await self._read_content(content)

        loop = asyncio.get_event_loop()

        def _upload() -> None:
            # Ensure parent directories
            parent = os.path.dirname(remote)
            self._mkdir_p(parent)

            import io

            buf = io.BytesIO(data)
            self._sftp.putfo(buf, remote)

        await loop.run_in_executor(None, _upload)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _download() -> bytes:
            import io

            buf = io.BytesIO()
            try:
                self._sftp.getfo(remote, buf)
            except OSError:
                raise FileNotFoundError(f"File not found: {name}", backend="sftp", path=name)
            return buf.getvalue()

        data = await loop.run_in_executor(None, _download)
        meta = await self.stat(name)
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _delete() -> None:
            with contextlib.suppress(OSError):
                self._sftp.remove(remote)

        await loop.run_in_executor(None, _delete)

    async def exists(self, name: str) -> bool:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _exists() -> bool:
            try:
                self._sftp.stat(remote)
                return True
            except OSError:
                return False

        return await loop.run_in_executor(None, _exists)

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _stat() -> StorageMetadata:
            try:
                attrs = self._sftp.stat(remote)
            except OSError:
                raise FileNotFoundError(f"File not found: {name}", backend="sftp", path=name)
            return StorageMetadata(
                name=self._normalize_path(name),
                size=attrs.st_size or 0,
                content_type=self.guess_content_type(name),
                last_modified=(datetime.fromtimestamp(attrs.st_mtime, tz=timezone.utc) if attrs.st_mtime else None),
                created_at=(datetime.fromtimestamp(attrs.st_atime, tz=timezone.utc) if attrs.st_atime else None),
            )

        return await loop.run_in_executor(None, _stat)

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        self._ensure_sftp()
        remote = self._remote_path(path) if path else self._config.root
        loop = asyncio.get_event_loop()

        def _list() -> tuple[list[str], list[str]]:
            dirs: list[str] = []
            files: list[str] = []
            try:
                entries = self._sftp.listdir_attr(remote)
            except OSError:
                return dirs, files
            for entry in entries:
                if stat_module.S_ISDIR(entry.st_mode or 0):
                    dirs.append(entry.filename)
                else:
                    files.append(entry.filename)
            return dirs, files

        return await loop.run_in_executor(None, _list)

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: int | None = None) -> str:
        name = self._normalize_path(name)
        if self._config.base_url:
            base = self._config.base_url.rstrip("/")
            return f"{base}/{name}"
        return f"sftp://{self._config.host}:{self._config.port}{self._remote_path(name)}"

    # -- Internal ----------------------------------------------------------

    def _ensure_sftp(self) -> None:
        if self._sftp is None:
            raise BackendUnavailableError(
                "SFTP client not initialized. Call initialize() first.",
                backend="sftp",
            )

    def _mkdir_p(self, remote_dir: str) -> None:
        """Recursively create remote directories."""
        parts = remote_dir.split("/")
        current = ""
        for part in parts:
            if not part:
                current = "/"
                continue
            current = f"{current}/{part}" if current != "/" else f"/{part}"
            try:
                self._sftp.stat(current)
            except OSError:
                with contextlib.suppress(OSError):
                    self._sftp.mkdir(current)

    # _read_content inherited from StorageBackend
