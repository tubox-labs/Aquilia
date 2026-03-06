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
import os
import stat as stat_module
from datetime import datetime, timezone
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
    BackendUnavailableError,
    FileNotFoundError,
    PermissionError,
    StorageBackend,
    StorageError,
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
                pkey = paramiko.RSAKey.from_private_key_file(
                    key_path, password=self._config.key_passphrase
                )
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
                try:
                    self._sftp.close()
                except Exception:
                    pass
            if self._transport:
                try:
                    self._transport.close()
                except Exception:
                    pass

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
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], StorageFile],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
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
            except IOError:
                raise FileNotFoundError(
                    f"File not found: {name}", backend="sftp", path=name
                )
            return buf.getvalue()

        data = await loop.run_in_executor(None, _download)
        meta = await self.stat(name)
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _delete() -> None:
            try:
                self._sftp.remove(remote)
            except IOError:
                pass

        await loop.run_in_executor(None, _delete)

    async def exists(self, name: str) -> bool:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _exists() -> bool:
            try:
                self._sftp.stat(remote)
                return True
            except IOError:
                return False

        return await loop.run_in_executor(None, _exists)

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_sftp()
        remote = self._remote_path(name)
        loop = asyncio.get_event_loop()

        def _stat() -> StorageMetadata:
            try:
                attrs = self._sftp.stat(remote)
            except IOError:
                raise FileNotFoundError(
                    f"File not found: {name}", backend="sftp", path=name
                )
            return StorageMetadata(
                name=self._normalize_path(name),
                size=attrs.st_size or 0,
                content_type=self.guess_content_type(name),
                last_modified=(
                    datetime.fromtimestamp(attrs.st_mtime, tz=timezone.utc)
                    if attrs.st_mtime
                    else None
                ),
                created_at=(
                    datetime.fromtimestamp(attrs.st_atime, tz=timezone.utc)
                    if attrs.st_atime
                    else None
                ),
            )

        return await loop.run_in_executor(None, _stat)

    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        self._ensure_sftp()
        remote = self._remote_path(path) if path else self._config.root
        loop = asyncio.get_event_loop()

        def _list() -> Tuple[List[str], List[str]]:
            dirs: List[str] = []
            files: List[str] = []
            try:
                entries = self._sftp.listdir_attr(remote)
            except IOError:
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

    async def url(self, name: str, expire: Optional[int] = None) -> str:
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
            except IOError:
                try:
                    self._sftp.mkdir(current)
                except IOError:
                    pass

    # _read_content inherited from StorageBackend
