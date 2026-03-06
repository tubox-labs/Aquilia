"""
Azure Blob Storage Backend.

Stores files in Azure Blob Storage containers.
Requires ``azure-storage-blob`` (``pip install azure-storage-blob``).

Usage::

    from aquilia.storage.backends.azure import AzureBlobStorage
    from aquilia.storage.configs import AzureBlobConfig

    storage = AzureBlobStorage(AzureBlobConfig(
        container="media",
        connection_string="DefaultEndpointsProtocol=https;..."
    ))
    await storage.initialize()
    name = await storage.save("images/logo.png", png_bytes)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
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
    StorageBackend,
    StorageError,
    StorageFile,
    StorageMetadata,
)
from ..configs import AzureBlobConfig


class AzureBlobStorage(StorageBackend):
    """
    Azure Blob Storage backend.

    Uses ``azure-storage-blob`` with I/O offloaded to executors.
    """

    __slots__ = ("_config", "_service_client", "_container_client")

    def __init__(self, config: AzureBlobConfig) -> None:
        self._config = config
        self._service_client: Any = None
        self._container_client: Any = None

    @property
    def backend_name(self) -> str:
        return "azure"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise BackendUnavailableError(
                "Azure backend requires 'azure-storage-blob'. "
                "Install: pip install azure-storage-blob",
                backend="azure",
            )

        loop = asyncio.get_event_loop()

        def _connect() -> Any:
            if self._config.connection_string:
                client = BlobServiceClient.from_connection_string(
                    self._config.connection_string
                )
            elif self._config.account_name:
                account_url = f"https://{self._config.account_name}.blob.core.windows.net"
                if self._config.account_key:
                    from azure.storage.blob import BlobServiceClient as BSC
                    client = BSC(
                        account_url=account_url,
                        credential=self._config.account_key,
                    )
                elif self._config.sas_token:
                    client = BlobServiceClient(
                        account_url=account_url,
                        credential=self._config.sas_token,
                    )
                else:
                    # Attempt DefaultAzureCredential
                    try:
                        from azure.identity import DefaultAzureCredential
                        credential = DefaultAzureCredential()
                    except ImportError:
                        raise BackendUnavailableError(
                            "Azure identity requires 'azure-identity'. "
                            "Install: pip install azure-identity",
                            backend="azure",
                        )
                    client = BlobServiceClient(
                        account_url=account_url,
                        credential=credential,
                    )
            else:
                raise BackendUnavailableError(
                    "Azure config must provide connection_string or account_name",
                    backend="azure",
                )
            return client

        self._service_client = await loop.run_in_executor(None, _connect)
        self._container_client = self._service_client.get_container_client(
            self._config.container
        )

    async def shutdown(self) -> None:
        if self._service_client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._service_client.close)
            except Exception:
                pass
            self._service_client = None
            self._container_client = None

    async def ping(self) -> bool:
        if not self._container_client:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._container_client.get_container_properties
            )
            return True
        except Exception:
            return False

    # -- Core operations ---------------------------------------------------

    def _blob_name(self, name: str) -> str:
        name = self._normalize_path(name)
        if self._config.prefix:
            return f"{self._config.prefix.strip('/')}/{name}"
        return name

    def _unblob(self, blob_name: str) -> str:
        if self._config.prefix:
            prefix = self._config.prefix.strip("/") + "/"
            if blob_name.startswith(prefix):
                return blob_name[len(prefix):]
        return blob_name

    async def save(
        self,
        name: str,
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], StorageFile],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False,
    ) -> str:
        self._ensure_container()
        name = self._normalize_path(name)

        if not overwrite and await self.exists(name):
            name = self.generate_filename(name)

        blob_name = self._blob_name(name)
        data = await self._read_content(content)
        ct = content_type or self.guess_content_type(name)

        loop = asyncio.get_event_loop()

        def _upload() -> None:
            from azure.storage.blob import ContentSettings
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                data,
                overwrite=self._config.overwrite or overwrite,
                content_settings=ContentSettings(content_type=ct),
                metadata=metadata,
            )

        await loop.run_in_executor(None, _upload)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        self._ensure_container()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _download() -> tuple:
            blob_client = self._container_client.get_blob_client(blob_name)
            try:
                download = blob_client.download_blob()
                data = download.readall()
                props = blob_client.get_blob_properties()
                return data, props
            except Exception as e:
                if "BlobNotFound" in str(e) or "404" in str(e):
                    raise FileNotFoundError(
                        f"File not found: {name}", backend="azure", path=name
                    )
                raise

        try:
            data, props = await loop.run_in_executor(None, _download)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(str(e), backend="azure", path=name)

        meta = StorageMetadata(
            name=self._normalize_path(name),
            size=props.size,
            content_type=(
                props.content_settings.content_type
                if props.content_settings
                else "application/octet-stream"
            ),
            etag=props.etag or "",
            last_modified=props.last_modified,
            created_at=props.creation_time,
            metadata=props.metadata or {},
        )
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        self._ensure_container()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _delete() -> None:
            blob_client = self._container_client.get_blob_client(blob_name)
            try:
                blob_client.delete_blob()
            except Exception:
                pass

        await loop.run_in_executor(None, _delete)

    async def exists(self, name: str) -> bool:
        self._ensure_container()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _exists() -> bool:
            blob_client = self._container_client.get_blob_client(blob_name)
            try:
                blob_client.get_blob_properties()
                return True
            except Exception:
                return False

        return await loop.run_in_executor(None, _exists)

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_container()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _stat() -> StorageMetadata:
            blob_client = self._container_client.get_blob_client(blob_name)
            try:
                props = blob_client.get_blob_properties()
            except Exception:
                raise FileNotFoundError(
                    f"File not found: {name}", backend="azure", path=name
                )
            return StorageMetadata(
                name=self._normalize_path(name),
                size=props.size,
                content_type=(
                    props.content_settings.content_type
                    if props.content_settings
                    else "application/octet-stream"
                ),
                etag=props.etag or "",
                last_modified=props.last_modified,
                created_at=props.creation_time,
                metadata=props.metadata or {},
            )

        return await loop.run_in_executor(None, _stat)

    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        self._ensure_container()
        prefix = self._blob_name(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        loop = asyncio.get_event_loop()

        def _list() -> Tuple[List[str], List[str]]:
            dirs: set = set()
            files: List[str] = []

            blobs = self._container_client.walk_blobs(
                name_starts_with=prefix, delimiter="/"
            )
            for item in blobs:
                if hasattr(item, "prefix"):
                    # Virtual directory
                    d = item.prefix.rstrip("/").rsplit("/", 1)[-1]
                    dirs.add(d)
                else:
                    f = item.name.rsplit("/", 1)[-1]
                    files.append(f)
            return sorted(dirs), files

        return await loop.run_in_executor(None, _list)

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: Optional[int] = None) -> str:
        self._ensure_container()
        blob_name = self._blob_name(name)

        if self._config.custom_domain:
            return f"https://{self._config.custom_domain}/{self._config.container}/{blob_name}"

        if self._config.account_name:
            base = f"https://{self._config.account_name}.blob.core.windows.net"
            return f"{base}/{self._config.container}/{blob_name}"

        return f"/{self._config.container}/{blob_name}"

    # -- Internal ----------------------------------------------------------

    def _ensure_container(self) -> None:
        if self._container_client is None:
            raise BackendUnavailableError(
                "Azure container not initialized. Call initialize() first.",
                backend="azure",
            )

    # _read_content inherited from StorageBackend
