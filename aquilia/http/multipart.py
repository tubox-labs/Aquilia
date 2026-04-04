"""
AquilaHTTP — Multipart Form Data.

Builder for multipart/form-data requests with file uploads.
"""

from __future__ import annotations

import mimetypes
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass
class FormField:
    """A form field in multipart data."""

    name: str
    value: str | bytes
    content_type: str | None = None
    filename: str | None = None


@dataclass
class FormFile:
    """A file field in multipart data."""

    name: str
    filename: str
    content: bytes | BinaryIO | AsyncIterator[bytes] | Path
    content_type: str | None = None
    content_length: int | None = None

    def __post_init__(self):
        # Auto-detect content type from filename
        if self.content_type is None:
            ct, _ = mimetypes.guess_type(self.filename)
            self.content_type = ct or "application/octet-stream"

        # Auto-detect content length
        if self.content_length is None:
            if isinstance(self.content, bytes):
                self.content_length = len(self.content)
            elif isinstance(self.content, Path):
                try:
                    self.content_length = self.content.stat().st_size
                except OSError:
                    pass


class MultipartFormData:
    """
    Builder for multipart/form-data requests.

    Example:
        ```python
        form = (
            MultipartFormData()
            .field("name", "John Doe")
            .field("email", "john@example.com")
            .file("avatar", "avatar.png", open("avatar.png", "rb"))
            .file_from_path("document", Path("document.pdf"))
        )

        request = (
            RequestBuilder("POST", "https://api.example.com/upload")
            .body(form.encode())
            .header("Content-Type", form.content_type)
            .build()
        )
        ```
    """

    __slots__ = ("_fields", "_files", "_boundary")

    def __init__(self, boundary: str | None = None):
        self._fields: list[FormField] = []
        self._files: list[FormFile] = []
        self._boundary = boundary or self._generate_boundary()

    @staticmethod
    def _generate_boundary() -> str:
        """Generate a unique boundary string."""
        return f"----AquilaHTTP{uuid.uuid4().hex}"

    @property
    def boundary(self) -> str:
        """Get the multipart boundary."""
        return self._boundary

    @property
    def content_type(self) -> str:
        """Get the Content-Type header value."""
        return f"multipart/form-data; boundary={self._boundary}"

    def field(
        self,
        name: str,
        value: str | bytes,
        content_type: str | None = None,
    ) -> MultipartFormData:
        """
        Add a form field.

        Args:
            name: Field name.
            value: Field value.
            content_type: Optional content type.

        Returns:
            Self for chaining.
        """
        self._fields.append(
            FormField(
                name=name,
                value=value,
                content_type=content_type,
            )
        )
        return self

    def file(
        self,
        name: str,
        filename: str,
        content: bytes | BinaryIO | AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> MultipartFormData:
        """
        Add a file field.

        Args:
            name: Field name.
            filename: File name.
            content: File content (bytes, file-like, or async iterator).
            content_type: Optional content type (auto-detected if None).

        Returns:
            Self for chaining.
        """
        self._files.append(
            FormFile(
                name=name,
                filename=filename,
                content=content,
                content_type=content_type,
            )
        )
        return self

    def file_from_path(
        self,
        name: str,
        path: Path | str,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> MultipartFormData:
        """
        Add a file field from a path.

        Args:
            name: Field name.
            path: Path to file.
            content_type: Optional content type.
            filename: Optional filename (defaults to path basename).

        Returns:
            Self for chaining.
        """
        path = Path(path)
        self._files.append(
            FormFile(
                name=name,
                filename=filename or path.name,
                content=path,
                content_type=content_type,
            )
        )
        return self

    def file_from_bytes(
        self,
        name: str,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> MultipartFormData:
        """
        Add a file field from bytes.

        Args:
            name: Field name.
            filename: File name.
            data: File content as bytes.
            content_type: Optional content type.

        Returns:
            Self for chaining.
        """
        return self.file(name, filename, data, content_type)

    def _encode_field(self, f: FormField) -> bytes:
        """Encode a form field to bytes."""
        parts = []

        # Content-Disposition header
        disposition = f'Content-Disposition: form-data; name="{f.name}"'
        if f.filename:
            disposition += f'; filename="{f.filename}"'
        parts.append(disposition.encode("utf-8"))

        # Content-Type header (optional)
        if f.content_type:
            parts.append(f"Content-Type: {f.content_type}".encode())

        # Empty line before content
        parts.append(b"")

        # Content
        if isinstance(f.value, bytes):
            parts.append(f.value)
        else:
            parts.append(f.value.encode("utf-8"))

        return b"\r\n".join(parts)

    async def _encode_file(self, f: FormFile) -> bytes:
        """Encode a file field to bytes."""
        parts = []

        # Content-Disposition header
        safe_filename = f.filename.replace('"', '\\"')
        disposition = f'Content-Disposition: form-data; name="{f.name}"; filename="{safe_filename}"'
        parts.append(disposition.encode("utf-8"))

        # Content-Type header
        parts.append(f"Content-Type: {f.content_type}".encode())

        # Empty line before content
        parts.append(b"")

        # Content
        content = await self._read_file_content(f)
        parts.append(content)

        return b"\r\n".join(parts)

    async def _read_file_content(self, f: FormFile) -> bytes:
        """Read file content from various sources."""
        import asyncio

        if isinstance(f.content, bytes):
            return f.content

        if isinstance(f.content, Path):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, f.content.read_bytes)

        if hasattr(f.content, "read"):
            # File-like object
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                f.content.read,  # type: ignore
            )

        # Async iterator
        chunks: list[bytes] = []
        async for chunk in f.content:  # type: ignore
            chunks.append(chunk)
        return b"".join(chunks)

    async def encode(self) -> bytes:
        """
        Encode all fields and files to multipart body.

        Returns:
            Complete multipart body as bytes.
        """
        parts: list[bytes] = []
        boundary = self._boundary.encode("utf-8")

        # Encode fields
        for f in self._fields:
            parts.append(b"--" + boundary)
            parts.append(self._encode_field(f))

        # Encode files
        for f in self._files:
            parts.append(b"--" + boundary)
            parts.append(await self._encode_file(f))

        # Final boundary
        parts.append(b"--" + boundary + b"--")
        parts.append(b"")  # Trailing CRLF

        return b"\r\n".join(parts)

    def encode_sync(self) -> bytes:
        """
        Synchronously encode fields and files.

        Only works if all file contents are bytes.

        Returns:
            Complete multipart body as bytes.
        """
        parts: list[bytes] = []
        boundary = self._boundary.encode("utf-8")

        # Encode fields
        for f in self._fields:
            parts.append(b"--" + boundary)
            parts.append(self._encode_field(f))

        # Encode files
        for f in self._files:
            if not isinstance(f.content, bytes):
                if isinstance(f.content, Path):
                    content = f.content.read_bytes()
                elif hasattr(f.content, "read"):
                    content = f.content.read()  # type: ignore
                else:
                    raise ValueError("Cannot synchronously encode async file content. Use encode() instead.")
            else:
                content = f.content

            # Build file part
            safe_filename = f.filename.replace('"', '\\"')
            file_parts = [
                f'Content-Disposition: form-data; name="{f.name}"; filename="{safe_filename}"'.encode(),
                f"Content-Type: {f.content_type}".encode(),
                b"",
                content,
            ]

            parts.append(b"--" + boundary)
            parts.append(b"\r\n".join(file_parts))

        # Final boundary
        parts.append(b"--" + boundary + b"--")
        parts.append(b"")

        return b"\r\n".join(parts)

    async def stream(self, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """
        Stream the multipart body in chunks.

        Useful for large files to avoid loading everything into memory.

        Args:
            chunk_size: Size of chunks to yield.

        Yields:
            Chunks of the multipart body.
        """
        boundary = self._boundary.encode("utf-8")

        # Stream fields
        for f in self._fields:
            yield b"--" + boundary + b"\r\n"
            yield self._encode_field(f) + b"\r\n"

        # Stream files
        for f in self._files:
            yield b"--" + boundary + b"\r\n"

            # Headers
            safe_filename = f.filename.replace('"', '\\"')
            headers = (
                f'Content-Disposition: form-data; name="{f.name}"; filename="{safe_filename}"\r\n'
                f"Content-Type: {f.content_type}\r\n"
                f"\r\n"
            ).encode()
            yield headers

            # Stream content
            async for chunk in self._stream_file_content(f, chunk_size):
                yield chunk

            yield b"\r\n"

        # Final boundary
        yield b"--" + boundary + b"--\r\n"

    async def _stream_file_content(
        self,
        f: FormFile,
        chunk_size: int,
    ) -> AsyncIterator[bytes]:
        """Stream file content in chunks."""
        import asyncio

        if isinstance(f.content, bytes):
            for i in range(0, len(f.content), chunk_size):
                yield f.content[i : i + chunk_size]
            return

        if isinstance(f.content, Path):
            loop = asyncio.get_running_loop()
            with open(f.content, "rb") as fp:
                while True:
                    chunk = await loop.run_in_executor(None, fp.read, chunk_size)
                    if not chunk:
                        break
                    yield chunk
            return

        if hasattr(f.content, "read"):
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(
                    None,
                    f.content.read,
                    chunk_size,  # type: ignore
                )
                if not chunk:
                    break
                yield chunk
            return

        # Async iterator
        async for chunk in f.content:  # type: ignore
            yield chunk

    def content_length(self) -> int | None:
        """
        Calculate total content length if possible.

        Returns:
            Total content length, or None if unknown (async content).
        """
        total = 0
        boundary_len = len(self._boundary.encode("utf-8"))

        for f in self._fields:
            # Boundary + CRLF
            total += 2 + boundary_len + 2

            # Headers
            header = f'Content-Disposition: form-data; name="{f.name}"'
            if f.filename:
                header += f'; filename="{f.filename}"'
            total += len(header.encode("utf-8")) + 2

            if f.content_type:
                total += len(f"Content-Type: {f.content_type}".encode()) + 2

            total += 2  # Empty line

            # Content + CRLF
            if isinstance(f.value, bytes):
                total += len(f.value)
            else:
                total += len(f.value.encode("utf-8"))
            total += 2

        for f in self._files:
            # Can only calculate if content length is known
            if f.content_length is None:
                return None

            # Boundary + CRLF
            total += 2 + boundary_len + 2

            # Headers
            safe_filename = f.filename.replace('"', '\\"')
            header = f'Content-Disposition: form-data; name="{f.name}"; filename="{safe_filename}"'
            total += len(header.encode("utf-8")) + 2
            total += len(f"Content-Type: {f.content_type}".encode()) + 2
            total += 2  # Empty line

            # Content + CRLF
            total += f.content_length
            total += 2

        # Final boundary
        total += 2 + boundary_len + 2 + 2

        return total
