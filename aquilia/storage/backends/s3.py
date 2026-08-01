"""
Amazon S3 / S3-Compatible Storage Backend.

Supports Amazon S3, MinIO, DigitalOcean Spaces, Backblaze B2,
Cloudflare R2, and any S3-compatible object store.

Requires ``boto3`` (``pip install boto3``).

Design notes:
    - Every blocking SDK call runs on the dedicated storage thread pool
      (:mod:`aquilia.storage.executor`), not the interpreter's shared default
      executor, so storage traffic is bounded and separately sizable.
    - ``open`` streams the object body in chunks; nothing larger than one
      chunk is held in memory unless the caller explicitly calls ``read()``.
    - ``save`` uses multipart upload for payloads above
      ``S3Config.multipart_threshold``, lifting the 5 GB single-request limit
      and keeping memory bounded to one part.

Usage::

    from aquilia.storage.backends.s3 import S3Storage
    from aquilia.storage.configs import S3Config

    storage = S3Storage(S3Config(bucket="my-bucket", region="us-east-1"))
    await storage.initialize()
    name = await storage.save("reports/q4.pdf", pdf_bytes)

    async with await storage.open(name) as f:
        async for chunk in f:
            ...
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import (
    Any,
    BinaryIO,
)

from aquilia.storage.base import (
    BackendUnavailableError,
    FileNotFoundError,
    StorageBackend,
    StorageError,
    StorageFile,
    StorageMetadata,
)
from aquilia.storage.configs import S3Config
from aquilia.storage.executor import run_blocking

#: S3 requires every part except the last to be at least 5 MiB.
_MIN_PART_SIZE = 5 * 1024 * 1024


class S3Storage(StorageBackend):
    """
    Amazon S3 / S3-compatible storage backend.

    Uses ``boto3`` under the hood.  All I/O is offloaded to the dedicated
    storage thread executor to stay async-friendly.

    Args:
        config: Bucket, credentials, and transfer tuning.

    Usage::

        storage = S3Storage(S3Config(bucket="assets", region="eu-west-1"))
        await storage.initialize()
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

        kwargs: dict[str, Any] = {
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

        self._client = await run_blocking(lambda: boto3.client("s3", **kwargs))
        self._resource = await run_blocking(lambda: boto3.resource("s3", **kwargs))

    async def shutdown(self) -> None:
        if self._client:
            self._client = None
        if self._resource:
            self._resource = None

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            await run_blocking(lambda: self._client.head_bucket(Bucket=self._config.bucket))
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
                return key[len(prefix) :]
        return key

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
        Upload ``content`` under ``name``.

        Payloads at or above ``config.multipart_threshold`` are uploaded with
        S3 multipart, so objects larger than the 5 GB single-request limit
        succeed and peak memory stays near one part size.

        Args:
            name: Relative object key (excluding ``config.prefix``).
            content: Bytes, file-like object, async iterator, or ``StorageFile``.
            content_type: MIME type; guessed from *name* when omitted.
            metadata: Custom object metadata.
            overwrite: Replace an existing object instead of generating a new key.

        Returns:
            The key the object was stored under.

        Raises:
            BackendUnavailableError: If ``initialize`` has not been called.
            StorageError: If the upload fails.
        """
        self._ensure_client()
        name = self._normalize_path(name)

        if not overwrite and await self.exists(name):
            name = self.generate_filename(name)

        key = self._key(name)
        ct = content_type or self.guess_content_type(name)
        extra = self._object_kwargs(ct, metadata)

        threshold = max(_MIN_PART_SIZE, self._config.multipart_threshold)
        head, stream = await self._peek(content, threshold)

        if stream is None:
            await run_blocking(
                lambda: self._client.put_object(
                    Bucket=self._config.bucket,
                    Key=key,
                    Body=head,
                    **extra,
                )
            )
            return name

        await self._multipart_upload(key, head, stream, extra)
        return name

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        """
        Open an object for streaming reads.

        The returned :class:`StorageFile` wraps a lazy chunk iterator over the
        S3 ``StreamingBody``; the object is never fully materialised unless the
        caller invokes ``read()``.

        Args:
            name: Relative object key.
            mode: Open mode recorded on the returned file.

        Returns:
            A streaming ``StorageFile``.

        Raises:
            FileNotFoundError: If the object does not exist.
            StorageError: On any other S3 error.
        """
        self._ensure_client()
        key = self._key(name)

        try:
            response = await run_blocking(lambda: self._client.get_object(Bucket=self._config.bucket, Key=key))
        except Exception as e:
            if "NoSuchKey" in str(type(e).__name__) or "404" in str(e):
                raise FileNotFoundError(f"File not found: {name}", backend="s3", path=name)
            raise StorageError(str(e), backend="s3", path=name)

        meta = StorageMetadata(
            name=self._normalize_path(name),
            size=response.get("ContentLength", 0),
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=response.get("ETag", "").strip('"'),
            last_modified=response.get("LastModified"),
            metadata=response.get("Metadata", {}),
            storage_class=response.get("StorageClass", ""),
        )
        return StorageFile(
            name=name,
            mode=mode,
            meta=meta,
            chunks=self._iter_body(response["Body"]),
        )

    async def delete(self, name: str) -> None:
        self._ensure_client()
        key = self._key(name)
        try:
            await run_blocking(lambda: self._client.delete_object(Bucket=self._config.bucket, Key=key))
        except Exception:
            pass  # Idempotent delete

    async def exists(self, name: str) -> bool:
        self._ensure_client()
        key = self._key(name)
        try:
            await run_blocking(lambda: self._client.head_object(Bucket=self._config.bucket, Key=key))
            return True
        except Exception:
            return False

    async def stat(self, name: str) -> StorageMetadata:
        self._ensure_client()
        key = self._key(name)
        try:
            head = await run_blocking(lambda: self._client.head_object(Bucket=self._config.bucket, Key=key))
        except Exception:
            raise FileNotFoundError(f"File not found: {name}", backend="s3", path=name)

        return StorageMetadata(
            name=self._normalize_path(name),
            size=head.get("ContentLength", 0),
            content_type=head.get("ContentType", "application/octet-stream"),
            etag=head.get("ETag", "").strip('"'),
            last_modified=head.get("LastModified"),
            metadata=head.get("Metadata", {}),
            storage_class=head.get("StorageClass", ""),
        )

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        self._ensure_client()
        prefix = self._key(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        response = await run_blocking(
            lambda: self._client.list_objects_v2(
                Bucket=self._config.bucket,
                Prefix=prefix,
                Delimiter="/",
            )
        )

        dirs: list[str] = []
        files: list[str] = []

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

    async def url(self, name: str, expire: int | None = None) -> str:
        self._ensure_client()
        key = self._key(name)
        expiry = expire or self._config.presigned_expiry

        return await run_blocking(
            lambda: self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._config.bucket, "Key": key},
                ExpiresIn=expiry,
            )
        )

    # -- Internal ----------------------------------------------------------

    def _object_kwargs(self, content_type: str, metadata: dict[str, str] | None) -> dict[str, Any]:
        """
        Build the shared object-creation arguments for put/multipart uploads.

        Args:
            content_type: Resolved MIME type.
            metadata: Custom object metadata, if any.

        Returns:
            Keyword arguments accepted by both ``put_object`` and
            ``create_multipart_upload``.
        """
        kwargs: dict[str, Any] = {"ContentType": content_type}
        if metadata:
            kwargs["Metadata"] = metadata
        if self._config.default_acl:
            kwargs["ACL"] = self._config.default_acl
        if self._config.storage_class:
            kwargs["StorageClass"] = self._config.storage_class
        return kwargs

    async def _peek(
        self,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
        threshold: int,
    ) -> tuple[bytes, AsyncIterator[bytes] | None]:
        """
        Buffer up to *threshold* bytes to decide between single-part and multipart.

        Args:
            content: Any supported content form.
            threshold: Byte count above which multipart is used.

        Returns:
            ``(head, rest)``.  When ``rest`` is ``None`` the whole payload fits
            in ``head`` and a single ``put_object`` suffices; otherwise ``head``
            is the first part and ``rest`` yields the remaining chunks.
        """
        chunks = self._iter_content(content)
        buffered = bytearray()

        async for chunk in chunks:
            buffered.extend(chunk)
            if len(buffered) >= threshold:
                return bytes(buffered), chunks

        return bytes(buffered), None

    async def _multipart_upload(
        self,
        key: str,
        head: bytes,
        rest: AsyncIterator[bytes],
        extra: dict[str, Any],
    ) -> None:
        """
        Upload an object in parts, aborting cleanly on failure.

        Args:
            key: Fully-qualified S3 key.
            head: Already-buffered leading bytes (at least one full part).
            rest: Iterator yielding the remaining chunks.
            extra: Object-creation arguments from :meth:`_object_kwargs`.

        Returns:
            ``None``.

        Raises:
            StorageError: If any part fails; the multipart upload is aborted
                first so no incomplete upload is billed or left dangling.
        """
        bucket = self._config.bucket
        part_size = max(_MIN_PART_SIZE, self._config.multipart_chunk_size)

        created = await run_blocking(lambda: self._client.create_multipart_upload(Bucket=bucket, Key=key, **extra))
        upload_id = created["UploadId"]
        parts: list[dict[str, Any]] = []

        async def _upload_part(body: bytes) -> None:
            number = len(parts) + 1
            result = await run_blocking(
                lambda: self._client.upload_part(
                    Bucket=bucket,
                    Key=key,
                    PartNumber=number,
                    UploadId=upload_id,
                    Body=body,
                )
            )
            parts.append({"PartNumber": number, "ETag": result["ETag"]})

        try:
            buffer = bytearray(head)
            async for chunk in rest:
                buffer.extend(chunk)
                while len(buffer) >= part_size:
                    await _upload_part(bytes(buffer[:part_size]))
                    del buffer[:part_size]

            while len(buffer) > part_size:
                await _upload_part(bytes(buffer[:part_size]))
                del buffer[:part_size]
            if buffer or not parts:
                await _upload_part(bytes(buffer))

            await run_blocking(
                lambda: self._client.complete_multipart_upload(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            )
        except Exception as e:
            try:
                await run_blocking(
                    lambda: self._client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
                )
            except Exception:
                pass
            raise StorageError(f"Multipart upload failed: {e}", backend="s3", path=key) from e

    async def _iter_content(
        self,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
    ) -> AsyncIterator[bytes]:
        """
        Normalise any supported content form into a chunk stream.

        Args:
            content: Bytes, ``StorageFile``, sync file-like, or async iterator.

        Yields:
            Successive byte chunks.
        """
        chunk_size = max(_MIN_PART_SIZE, self._config.multipart_chunk_size)

        if isinstance(content, bytes):
            for i in range(0, len(content), chunk_size):
                yield content[i : i + chunk_size]
            return
        if isinstance(content, StorageFile):
            async for chunk in content:
                yield chunk
            return
        if hasattr(content, "read"):
            while True:
                chunk = await run_blocking(content.read, chunk_size)  # type: ignore[union-attr]
                if not chunk:
                    break
                yield chunk
            return
        async for chunk in content:  # type: ignore[union-attr]
            yield chunk

    @staticmethod
    async def _iter_body(body: Any, chunk_size: int = 65_536) -> AsyncIterator[bytes]:
        """
        Stream an S3 ``StreamingBody`` without materialising the whole object.

        Args:
            body: The ``Body`` handle from ``get_object``.
            chunk_size: Bytes to request per read.

        Yields:
            Successive byte chunks.
        """
        try:
            while True:
                chunk = await run_blocking(body.read, chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            close = getattr(body, "close", None)
            if close is not None:
                try:
                    await run_blocking(close)
                except Exception:
                    pass

    def _ensure_client(self) -> None:
        if self._client is None:
            raise BackendUnavailableError(
                "S3 client not initialized. Call initialize() first.",
                backend="s3",
            )

    # _read_content inherited from StorageBackend
