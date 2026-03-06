"""
Google Cloud Storage Backend.

Stores files in Google Cloud Storage buckets.
Requires ``google-cloud-storage`` (``pip install google-cloud-storage``).

Usage::

    from aquilia.storage.backends.gcs import GCSStorage
    from aquilia.storage.configs import GCSConfig

    storage = GCSStorage(GCSConfig(bucket="my-bucket", project="my-project"))
    await storage.initialize()
    name = await storage.save("data/report.csv", csv_bytes)
"""

from __future__ import annotations

import asyncio
import json
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
from ..configs import GCSConfig


class GCSStorage(StorageBackend):
    """
    Google Cloud Storage backend.

    Uses ``google-cloud-storage`` with I/O offloaded to executors
    for async compatibility.
    """

    __slots__ = ("_config", "_client", "_bucket")

    def __init__(self, config: GCSConfig) -> None:
        self._config = config
        self._client: Any = None
        self._bucket: Any = None

    @property
    def backend_name(self) -> str:
        return "gcs"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        try:
            from google.cloud import storage as gcs_lib
        except ImportError:
            raise BackendUnavailableError(
                "GCS backend requires 'google-cloud-storage'. "
                "Install: pip install google-cloud-storage",
                backend="gcs",
            )

        loop = asyncio.get_event_loop()

        def _connect() -> Any:
            kwargs: Dict[str, Any] = {}
            if self._config.project:
                kwargs["project"] = self._config.project
            if self._config.credentials_path:
                client = gcs_lib.Client.from_service_account_json(
                    self._config.credentials_path, **kwargs
                )
            elif self._config.credentials_json:
                info = json.loads(self._config.credentials_json)
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_info(info)
                client = gcs_lib.Client(credentials=creds, **kwargs)
            else:
                client = gcs_lib.Client(**kwargs)  # ADC
            return client

        self._client = await loop.run_in_executor(None, _connect)
        self._bucket = self._client.bucket(self._config.bucket)

    async def shutdown(self) -> None:
        if self._client:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._client.close)
            self._client = None
            self._bucket = None

    async def ping(self) -> bool:
        if not self._bucket:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._bucket.reload)
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
        self._ensure_bucket()
        name = self._normalize_path(name)

        if not overwrite and await self.exists(name):
            name = self.generate_filename(name)

        blob_name = self._blob_name(name)
        data = await self._read_content(content)
        ct = content_type or self.guess_content_type(name)

        loop = asyncio.get_event_loop()

        def _upload() -> None:
            blob = self._bucket.blob(blob_name)
            if metadata:
                blob.metadata = metadata
            blob.upload_from_string(data, content_type=ct)

        await loop.run_in_executor(None, _upload)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        self._ensure_bucket()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _download() -> tuple:
            blob = self._bucket.blob(blob_name)
            if not blob.exists():
                raise FileNotFoundError(
                    f"File not found: {name}", backend="gcs", path=name
                )
            blob.reload()
            data = blob.download_as_bytes()
            return data, blob

        try:
            data, blob = await loop.run_in_executor(None, _download)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(str(e), backend="gcs", path=name)

        meta = StorageMetadata(
            name=self._normalize_path(name),
            size=len(data),
            content_type=blob.content_type or "application/octet-stream",
            etag=blob.etag or "",
            last_modified=blob.updated,
            created_at=blob.time_created,
            metadata=blob.metadata or {},
        )
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        self._ensure_bucket()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _delete() -> None:
            blob = self._bucket.blob(blob_name)
            if blob.exists():
                blob.delete()

        try:
            await loop.run_in_executor(None, _delete)
        except Exception:
            pass

    async def exists(self, name: str) -> bool:
        self._ensure_bucket()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _exists() -> bool:
            return self._bucket.blob(blob_name).exists()

        return await loop.run_in_executor(None, _exists)

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_bucket()
        blob_name = self._blob_name(name)
        loop = asyncio.get_event_loop()

        def _stat() -> StorageMetadata:
            blob = self._bucket.blob(blob_name)
            if not blob.exists():
                raise FileNotFoundError(
                    f"File not found: {name}", backend="gcs", path=name
                )
            blob.reload()
            return StorageMetadata(
                name=self._normalize_path(name),
                size=blob.size or 0,
                content_type=blob.content_type or "application/octet-stream",
                etag=blob.etag or "",
                last_modified=blob.updated,
                created_at=blob.time_created,
                metadata=blob.metadata or {},
                storage_class=blob.storage_class or "",
            )

        return await loop.run_in_executor(None, _stat)

    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        self._ensure_bucket()
        prefix = self._blob_name(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        loop = asyncio.get_event_loop()

        def _list() -> Tuple[List[str], List[str]]:
            blobs = self._client.list_blobs(
                self._config.bucket, prefix=prefix, delimiter="/"
            )
            files: List[str] = []
            for blob in blobs:
                name = blob.name
                if name == prefix:
                    continue
                files.append(name.rsplit("/", 1)[-1])
            dirs: List[str] = [
                p.rstrip("/").rsplit("/", 1)[-1]
                for p in blobs.prefixes
            ]
            return dirs, files

        return await loop.run_in_executor(None, _list)

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: Optional[int] = None) -> str:
        self._ensure_bucket()
        blob_name = self._blob_name(name)
        expiry = expire or self._config.presigned_expiry
        loop = asyncio.get_event_loop()

        def _sign() -> str:
            blob = self._bucket.blob(blob_name)
            return blob.generate_signed_url(
                expiration=timedelta(seconds=expiry),
                method="GET",
            )

        return await loop.run_in_executor(None, _sign)

    # -- Internal ----------------------------------------------------------

    def _ensure_bucket(self) -> None:
        if self._bucket is None:
            raise BackendUnavailableError(
                "GCS bucket not initialized. Call initialize() first.",
                backend="gcs",
            )

    # _read_content inherited from StorageBackend
