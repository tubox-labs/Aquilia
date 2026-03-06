"""
Amazon S3 / S3-Compatible Storage Backend.

Supports Amazon S3, MinIO, DigitalOcean Spaces, Backblaze B2,
Cloudflare R2, and any S3-compatible object store.

Requires ``boto3`` (``pip install boto3``).

Usage::

    from aquilia.storage.backends.s3 import S3Storage
    from aquilia.storage.configs import S3Config

    storage = S3Storage(S3Config(bucket="my-bucket", region="us-east-1"))
    await storage.initialize()
    name = await storage.save("reports/q4.pdf", pdf_bytes)
"""

from __future__ import annotations

import asyncio
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
    StorageBackend,
    StorageError,
    StorageFile,
    StorageMetadata,
)
from ..configs import S3Config


class S3Storage(StorageBackend):
    """
    Amazon S3 / S3-compatible storage backend.

    Uses ``boto3`` under the hood.  All I/O is offloaded to a
    thread executor to stay async-friendly.
    """

    __slots__ = ("_config", "_client", "_resource")

    def __init__(self, config: S3Config) -> None:
        self._config = config
        self._client: Any = None
        self._resource: Any = None

    @property
    def backend_name(self) -> str:
        return "s3"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        try:
            import boto3
            from botocore.config import Config as BotoConfig
        except ImportError:
            raise BackendUnavailableError(
                "S3 backend requires 'boto3'. Install: pip install boto3",
                backend="s3",
            )

        kwargs: Dict[str, Any] = {
            "region_name": self._config.region,
        }
        if self._config.access_key:
            kwargs["aws_access_key_id"] = self._config.access_key
        if self._config.secret_key:
            kwargs["aws_secret_access_key"] = self._config.secret_key
        if self._config.session_token:
            kwargs["aws_session_token"] = self._config.session_token
        if self._config.endpoint_url:
            kwargs["endpoint_url"] = self._config.endpoint_url

        boto_config = BotoConfig(
            signature_version=self._config.signature_version,
            s3={"addressing_style": self._config.addressing_style},
        )
        kwargs["config"] = boto_config

        loop = asyncio.get_event_loop()
        self._client = await loop.run_in_executor(
            None, lambda: boto3.client("s3", **kwargs)
        )
        self._resource = await loop.run_in_executor(
            None, lambda: boto3.resource("s3", **kwargs)
        )

    async def shutdown(self) -> None:
        if self._client:
            self._client = None
        if self._resource:
            self._resource = None

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.head_bucket(Bucket=self._config.bucket),
            )
            return True
        except Exception:
            return False

    # -- Core operations ---------------------------------------------------

    def _key(self, name: str) -> str:
        """Prefix-qualified S3 key."""
        name = self._normalize_path(name)
        if self._config.prefix:
            return f"{self._config.prefix.strip('/')}/{name}"
        return name

    def _unkey(self, key: str) -> str:
        """Strip prefix from S3 key."""
        if self._config.prefix:
            prefix = self._config.prefix.strip("/") + "/"
            if key.startswith(prefix):
                return key[len(prefix):]
        return key

    async def save(
        self,
        name: str,
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], StorageFile],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False,
    ) -> str:
        self._ensure_client()
        name = self._normalize_path(name)

        if not overwrite and await self.exists(name):
            name = self.generate_filename(name)

        key = self._key(name)
        data = await self._read_content(content)
        ct = content_type or self.guess_content_type(name)

        put_kwargs: Dict[str, Any] = {
            "Bucket": self._config.bucket,
            "Key": key,
            "Body": data,
            "ContentType": ct,
        }
        if metadata:
            put_kwargs["Metadata"] = metadata
        if self._config.default_acl:
            put_kwargs["ACL"] = self._config.default_acl
        if self._config.storage_class:
            put_kwargs["StorageClass"] = self._config.storage_class

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._client.put_object(**put_kwargs)
        )
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        self._ensure_client()
        key = self._key(name)

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.get_object(
                    Bucket=self._config.bucket, Key=key
                ),
            )
        except Exception as e:
            if "NoSuchKey" in str(type(e).__name__) or "404" in str(e):
                raise FileNotFoundError(
                    f"File not found: {name}", backend="s3", path=name
                )
            raise StorageError(str(e), backend="s3", path=name)

        data = await loop.run_in_executor(None, lambda: response["Body"].read())
        meta = StorageMetadata(
            name=self._normalize_path(name),
            size=response.get("ContentLength", len(data)),
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=response.get("ETag", "").strip('"'),
            last_modified=response.get("LastModified"),
            metadata=response.get("Metadata", {}),
            storage_class=response.get("StorageClass", ""),
        )
        return StorageFile(name=name, mode=mode, content=data, meta=meta)

    async def delete(self, name: str) -> None:
        self._ensure_client()
        key = self._key(name)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self._client.delete_object(
                    Bucket=self._config.bucket, Key=key
                ),
            )
        except Exception:
            pass  # Idempotent delete

    async def exists(self, name: str) -> bool:
        self._ensure_client()
        key = self._key(name)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self._client.head_object(
                    Bucket=self._config.bucket, Key=key
                ),
            )
            return True
        except Exception:
            return False

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_client()
        key = self._key(name)
        loop = asyncio.get_event_loop()
        try:
            head = await loop.run_in_executor(
                None,
                lambda: self._client.head_object(
                    Bucket=self._config.bucket, Key=key
                ),
            )
        except Exception:
            raise FileNotFoundError(
                f"File not found: {name}", backend="s3", path=name
            )

        return StorageMetadata(
            name=self._normalize_path(name),
            size=head.get("ContentLength", 0),
            content_type=head.get("ContentType", "application/octet-stream"),
            etag=head.get("ETag", "").strip('"'),
            last_modified=head.get("LastModified"),
            metadata=head.get("Metadata", {}),
            storage_class=head.get("StorageClass", ""),
        )

    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        self._ensure_client()
        prefix = self._key(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.list_objects_v2(
                Bucket=self._config.bucket,
                Prefix=prefix,
                Delimiter="/",
            ),
        )

        dirs: List[str] = []
        files: List[str] = []

        for cp in response.get("CommonPrefixes", []):
            d = cp["Prefix"].rstrip("/")
            d = d.rsplit("/", 1)[-1]
            dirs.append(d)

        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key == prefix:
                continue
            f = key.rsplit("/", 1)[-1]
            files.append(f)

        return dirs, files

    async def size(self, name: str) -> int:
        meta = await self.stat(name)
        return meta.size

    async def url(self, name: str, expire: Optional[int] = None) -> str:
        self._ensure_client()
        key = self._key(name)
        expiry = expire or self._config.presigned_expiry

        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(
            None,
            lambda: self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._config.bucket, "Key": key},
                ExpiresIn=expiry,
            ),
        )
        return url

    # -- Internal ----------------------------------------------------------

    def _ensure_client(self) -> None:
        if self._client is None:
            raise BackendUnavailableError(
                "S3 client not initialized. Call initialize() first.",
                backend="s3",
            )

    # _read_content inherited from StorageBackend
