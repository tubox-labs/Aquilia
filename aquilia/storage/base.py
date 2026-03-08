"""
Storage Base -- Abstract backend contract and core types.

Defines the StorageBackend ABC, StorageFile async wrapper, metadata,
and structured error hierarchy.  Every backend inherits from
StorageBackend and implements the async contract.

Design principles (async-first, fsspec-aligned):
    - Async-native: every I/O method is ``async``
    - Streaming: ``save`` and ``open`` accept/return async iterators
    - Metadata-rich: ``stat`` returns typed StorageMetadata
    - Idempotent deletes: ``delete`` never raises on missing files
    - URL generation: ``url`` returns public/signed URLs
    - Health: ``ping`` returns True if the backend is reachable
"""

from __future__ import annotations

import os
import hashlib
import mimetypes
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import (
    Any,
    AsyncIterator,
    BinaryIO,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
    runtime_checkable,
)


# ═══════════════════════════════════════════════════════════════════════════
# Errors — Fault-based storage error hierarchy
# ═══════════════════════════════════════════════════════════════════════════

from aquilia.faults.core import Fault, FaultDomain, Severity

STORAGE_DOMAIN = FaultDomain.custom("storage", "File storage faults")


class StorageError(Fault):
    """Base fault for all storage operations."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        self.backend_name_str = backend
        self.path = path
        super().__init__(
            code=kwargs.pop("code", "STORAGE_ERROR"),
            message=message,
            domain=STORAGE_DOMAIN,
            severity=kwargs.pop("severity", Severity.ERROR),
            retryable=kwargs.pop("retryable", True),
            public=kwargs.pop("public", False),
            metadata={"backend": backend, "path": path, **kwargs.pop("metadata", {})},
            **kwargs,
        )


class FileNotFoundError(StorageError):
    """Raised when a file does not exist in the storage backend."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_FILE_NOT_FOUND",
            severity=Severity.WARN,
            retryable=False,
            **kwargs,
        )


class PermissionError(StorageError):
    """Raised when the caller lacks permission for the operation."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_PERMISSION_DENIED",
            severity=Severity.ERROR,
            retryable=False,
            **kwargs,
        )


class StorageFullError(StorageError):
    """Raised when the storage quota is exceeded."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_FULL",
            severity=Severity.ERROR,
            retryable=False,
            **kwargs,
        )


class BackendUnavailableError(StorageError):
    """Raised when the storage backend is unreachable or not configured."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_BACKEND_UNAVAILABLE",
            severity=Severity.FATAL,
            retryable=True,
            **kwargs,
        )


class StorageIOFault(StorageError):
    """Raised on I/O operation errors (closed file, wrong mode)."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_IO_ERROR",
            severity=Severity.ERROR,
            retryable=False,
            **kwargs,
        )


class StorageConfigFault(StorageError):
    """Raised on storage configuration / registry errors."""

    def __init__(self, message: str, backend: str = "", path: str = "", **kwargs):
        super().__init__(
            message,
            backend=backend,
            path=path,
            code="STORAGE_CONFIG_ERROR",
            severity=Severity.FATAL,
            retryable=False,
            **kwargs,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Metadata
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class StorageMetadata:
    """
    Immutable metadata for a stored file.

    Returned by ``StorageBackend.stat()`` and attached to ``StorageFile``.
    """
    name: str                                           # Relative path/key
    size: int = 0                                       # Bytes
    content_type: str = "application/octet-stream"      # MIME type
    etag: str = ""                                      # Content hash / ETag
    last_modified: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)  # Custom headers/tags
    storage_class: str = ""                             # e.g. STANDARD, GLACIER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "content_type": self.content_type,
            "etag": self.etag,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": dict(self.metadata),
            "storage_class": self.storage_class,
        }


# ═══════════════════════════════════════════════════════════════════════════
# StorageFile -- async file wrapper
# ═══════════════════════════════════════════════════════════════════════════

class StorageFile:
    """
    Async file wrapper returned by ``StorageBackend.open()``.

    Supports:
    - ``await sf.read(size)`` — read N bytes (or all)
    - ``async for chunk in sf`` — stream in chunks
    - ``await sf.write(data)`` — write bytes (for writable files)
    - ``await sf.close()`` — release resources
    - ``async with storage.open(name) as f: ...`` — context manager
    """

    __slots__ = ("name", "mode", "meta", "_content", "_pos", "_closed", "_chunks")

    def __init__(
        self,
        name: str,
        mode: str = "rb",
        content: Optional[bytes] = None,
        meta: Optional[StorageMetadata] = None,
        chunks: Optional[AsyncIterator[bytes]] = None,
    ):
        self.name = name
        self.mode = mode
        self.meta = meta
        self._content = content
        self._pos = 0
        self._closed = False
        self._chunks = chunks

    async def read(self, size: int = -1) -> bytes:
        """Read bytes from the file."""
        if self._closed:
            raise StorageIOFault("I/O operation on closed StorageFile", path=self.name)

        # If we have chunked content, materialise it
        if self._content is None and self._chunks is not None:
            parts: list[bytes] = []
            async for chunk in self._chunks:
                parts.append(chunk)
            self._content = b"".join(parts)
            self._chunks = None

        if self._content is None:
            return b""

        if size == -1:
            data = self._content[self._pos:]
            self._pos = len(self._content)
            return data

        data = self._content[self._pos:self._pos + size]
        self._pos += len(data)
        return data

    async def write(self, data: bytes) -> int:
        """Write bytes (for writable files)."""
        if self._closed:
            raise StorageIOFault("I/O operation on closed StorageFile", path=self.name)
        if "w" not in self.mode and "a" not in self.mode:
            raise StorageIOFault("StorageFile not opened for writing", path=self.name)

        if self._content is None:
            self._content = data
        else:
            self._content += data
        return len(data)

    async def seek(self, pos: int) -> None:
        """Seek to byte position (clamped to valid range)."""
        if pos < 0:
            pos = 0
        self._pos = pos

    async def tell(self) -> int:
        """Return current byte position."""
        return self._pos

    @property
    def content(self) -> Optional[bytes]:
        """Return raw content bytes (or None if not materialised)."""
        return self._content

    async def close(self) -> None:
        """Release resources."""
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def size(self) -> int:
        if self._content is not None:
            return len(self._content)
        if self.meta:
            return self.meta.size
        return 0

    async def __aenter__(self) -> "StorageFile":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._iter_chunks()

    async def _iter_chunks(self, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """Yield content in chunks for streaming."""
        if self._chunks is not None:
            async for chunk in self._chunks:
                yield chunk
            return

        if self._content is not None:
            for i in range(0, len(self._content), chunk_size):
                yield self._content[i:i + chunk_size]


# ═══════════════════════════════════════════════════════════════════════════
# StorageBackend -- abstract base class
# ═══════════════════════════════════════════════════════════════════════════

class StorageBackend(ABC):
    """
    Abstract storage backend.

    Every backend implements this async contract.  The interface is
    fully async with richer metadata semantics.

    Lifecycle:
        1. ``__init__``   — configure (no I/O)
        2. ``initialize`` — connect / create directories (async)
        3. ``save/open/delete/...`` — normal operations
        4. ``shutdown``   — disconnect / flush (async)
    """

    # -- Identity ----------------------------------------------------------

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable backend identifier (e.g. 'local', 's3')."""
        ...

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        """
        Async initialization (create dirs, connect to remote, etc.).
        Called by StorageSubsystem during server startup.
        """
        pass

    async def shutdown(self) -> None:
        """
        Graceful shutdown (close connections, flush buffers).
        Called by StorageSubsystem during server shutdown.
        """
        pass

    async def ping(self) -> bool:
        """
        Health check — return True if the backend is reachable.
        Used by HealthRegistry for storage health monitoring.
        """
        return True

    # -- Core operations ---------------------------------------------------

    @abstractmethod
    async def save(
        self,
        name: str,
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], "StorageFile"],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False,
    ) -> str:
        """
        Save content under ``name``.

        Returns the actual stored name (may differ if conflicts are resolved).

        Args:
            name: Relative path/key for the file.
            content: File content (bytes, file-like, async iterator, or StorageFile).
            content_type: MIME type (auto-detected from name if None).
            metadata: Custom metadata/tags to attach.
            overwrite: If True, replace existing file silently.

        Returns:
            The actual name the file was saved as.

        Raises:
            StorageError: On write failure.
        """
        ...

    @abstractmethod
    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        """
        Open a file for reading.

        Returns a ``StorageFile`` that supports async read/stream.

        Args:
            name: Relative path/key.
            mode: Open mode (default ``"rb"``).

        Returns:
            StorageFile instance.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, name: str) -> None:
        """
        Delete a file.  Idempotent — does NOT raise if missing.

        Args:
            name: Relative path/key.
        """
        ...

    @abstractmethod
    async def exists(self, name: str) -> bool:
        """
        Check if a file exists.

        Args:
            name: Relative path/key.

        Returns:
            True if the file exists.
        """
        ...

    @abstractmethod
    async def stat(self, name: str) -> StorageMetadata:
        """
        Return metadata for a file.

        Args:
            name: Relative path/key.

        Returns:
            StorageMetadata with size, content_type, etag, timestamps.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    @abstractmethod
    async def listdir(self, path: str = "") -> Tuple[List[str], List[str]]:
        """
        List contents of a directory/prefix.

        Returns:
            (directories, files) tuple, each a list of names.
        """
        ...

    @abstractmethod
    async def size(self, name: str) -> int:
        """Return file size in bytes."""
        ...

    @abstractmethod
    async def url(self, name: str, expire: Optional[int] = None) -> str:
        """
        Return a URL for accessing the file.

        Args:
            name: Relative path/key.
            expire: For signed URLs, expiry in seconds.

        Returns:
            Public or pre-signed URL string.

        Raises:
            NotImplementedError: If the backend has no URL scheme.
        """
        ...

    # -- Convenience (default implementations) -----------------------------

    async def copy(self, src: str, dst: str) -> str:
        """Copy a file within the same backend."""
        async with await self.open(src) as f:
            data = await f.read()
        return await self.save(dst, data, overwrite=True)

    async def move(self, src: str, dst: str) -> str:
        """Move a file within the same backend."""
        result = await self.copy(src, dst)
        await self.delete(src)
        return result

    def generate_filename(self, filename: str) -> str:
        """
        Generate a safe, unique filename.

        Sanitises the input and prepends a short UUID prefix to
        prevent collisions.
        """
        safe = self.get_valid_name(filename)
        root, ext = os.path.splitext(safe)
        uid = uuid.uuid4().hex[:8]
        return f"{root}_{uid}{ext}"

    @staticmethod
    def get_valid_name(name: str) -> str:
        """
        Return a filesystem-safe filename.

        Strips path components, removes null bytes and dangerous
        characters, and limits total length.
        """
        name = os.path.basename(name)
        name = name.replace("\x00", "")
        unsafe = '<>:"|?*\\'
        for ch in unsafe:
            name = name.replace(ch, "_")
        root, ext = os.path.splitext(name)
        if len(root) > 200:
            root = root[:200]
        return (root + ext) or "unnamed"

    @staticmethod
    def guess_content_type(name: str) -> str:
        """Guess MIME type from filename."""
        ct, _ = mimetypes.guess_type(name)
        return ct or "application/octet-stream"

    @staticmethod
    def _normalize_path(name: str) -> str:
        """
        Normalise slashes, strip leading slash, and reject dangerous paths.

        Security hardening:
        - Rejects null bytes (\\x00)
        - Rejects path traversal (.. segments)
        - Enforces maximum path length (1024 chars)
        """
        if "\x00" in name:
            raise PermissionError(
                f"Null byte in storage path: {name!r}",
                path=name,
            )
        normalized = str(PurePosixPath(name)).lstrip("/")
        # Reject any remaining '..' segments after normalisation
        parts = normalized.split("/")
        if ".." in parts:
            raise PermissionError(
                f"Path traversal blocked: {name!r}",
                path=name,
            )
        if len(normalized) > 1024:
            raise PermissionError(
                f"Path too long ({len(normalized)} chars, max 1024): {name!r}",
                path=name,
            )
        return normalized

    @staticmethod
    async def _read_content(
        content: Union[bytes, BinaryIO, AsyncIterator[bytes], "StorageFile"],
    ) -> bytes:
        """Normalise any content type to raw bytes.

        Handles ``bytes``, ``StorageFile``, sync file-like objects
        (via executor), and async iterators.
        """
        if isinstance(content, bytes):
            return content
        if isinstance(content, StorageFile):
            return await content.read()
        if hasattr(content, "read"):
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, content.read)  # type: ignore
        # AsyncIterator[bytes]
        parts: list[bytes] = []
        async for chunk in content:  # type: ignore
            parts.append(chunk)
        return b"".join(parts)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} backend={self.backend_name!r}>"
