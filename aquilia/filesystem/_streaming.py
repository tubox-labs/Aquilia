"""
Streaming Pipeline — High-performance async file streaming.

Provides chunked reading, writing, and file-to-file copying with
configurable chunk sizes and memory-efficient data flow.

Key classes:
    - ``AsyncFileStream``: Chunked async iterator for reading
    - ``AsyncWriteStream``: Buffered async writer
    - ``stream_copy``: Streaming file-to-file copy

Design notes:
    - Memory usage is bounded to ``chunk_size`` (default 64KB)
    - No intermediate full-file materialisation
    - Backpressure is implicit via ``await`` at each chunk
    - Every path is validated through ``_security.validate_path`` before
      the descriptor is opened, so the streaming path enforces exactly the
      same sandbox containment guarantees as ``_ops`` (SEC-FS-03).
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

from aquilia.filesystem._config import FileSystemConfig
from aquilia.filesystem._errors import wrap_os_error
from aquilia.filesystem._path import _get_default_pool as _get
from aquilia.filesystem._pool import FileSystemPool
from aquilia.filesystem._security import validate_path
from aquilia.typing import PathLike


class AsyncFileStream:
    """
    Chunked async iterator for streaming file reads.

    The path is validated and canonicalised at construction time through
    :func:`aquilia.filesystem.validate_path`, giving the streaming path the
    same sandbox containment guarantees as the whole-file helpers in
    ``_ops`` (SEC-FS-03).

    Args:
        path: File path to stream.
        chunk_size: Size of each chunk in bytes.
        pool: Thread pool to use.  Uses the shared default pool if ``None``.
        offset: Start reading from this byte offset.
        end: Stop reading at this byte offset (exclusive).  ``None`` = EOF.
        config: Filesystem config supplying limits and ``sandbox_root``.
        sandbox: Sandbox root override.  Takes precedence over
            ``config.sandbox_root``.

    Raises:
        PathTraversalFault: If the resolved path escapes the sandbox.
        PathTooLongFault: If the resolved path exceeds the length limit.
        PermissionDeniedFault: If the path contains null bytes.

    Usage::

        stream = AsyncFileStream(
            "/srv/uploads/large.bin",
            chunk_size=1024 * 1024,
            sandbox="/srv/uploads",
        )
        async for chunk in stream:
            process(chunk)

    Memory usage is bounded to ``chunk_size`` regardless of file size.
    """

    __slots__ = ("_path", "_chunk_size", "_pool", "_offset", "_end")

    def __init__(
        self,
        path: PathLike,
        *,
        chunk_size: int = 65_536,
        pool: FileSystemPool | None = None,
        offset: int = 0,
        end: int | None = None,
        config: FileSystemConfig | None = None,
        sandbox: PathLike | None = None,
    ) -> None:
        cfg = config or FileSystemConfig()
        self._path = validate_path(
            path,
            config=cfg,
            sandbox=sandbox or cfg.sandbox_root,
            operation="stream_read",
        )
        self._chunk_size = chunk_size
        self._pool = pool or _get_default_pool()
        self._offset = offset
        self._end = end

    @property
    def path(self) -> Path:
        """Resolved, sandbox-validated path being streamed."""
        return self._path

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._stream()

    async def _stream(self) -> AsyncIterator[bytes]:
        """Internal streaming implementation."""

        def _open():
            return open(self._path, "rb")

        try:
            fp = await self._pool.run(_open)
        except Exception as exc:
            raise wrap_os_error(exc, "stream_read", str(self._path)) from exc

        try:
            if self._offset > 0:
                await self._pool.run(fp.seek, self._offset)

            remaining = None
            if self._end is not None:
                remaining = self._end - self._offset

            while True:
                read_size = self._chunk_size
                if remaining is not None:
                    if remaining <= 0:
                        break
                    read_size = min(read_size, remaining)

                try:
                    chunk = await self._pool.run(fp.read, read_size)
                except Exception as exc:
                    raise wrap_os_error(exc, "stream_read", str(self._path)) from exc

                if not chunk:
                    break

                if remaining is not None:
                    remaining -= len(chunk)

                yield chunk
        finally:
            with contextlib.suppress(Exception):
                await self._pool.run(fp.close)


class AsyncWriteStream:
    """
    Buffered async writer for streaming file writes.

    Accumulates data in a buffer and flushes to disk when the buffer
    exceeds the configured threshold.  The destination path is validated
    and canonicalised at construction time through
    :func:`aquilia.filesystem.validate_path` (SEC-FS-03).

    Args:
        path: Destination file path.
        buffer_size: Flush threshold in bytes.
        pool: Thread pool to use.  Uses the shared default pool if ``None``.
        config: Filesystem config supplying limits and ``sandbox_root``.
        sandbox: Sandbox root override.  Takes precedence over
            ``config.sandbox_root``.

    Raises:
        PathTraversalFault: If the resolved path escapes the sandbox.
        PathTooLongFault: If the resolved path exceeds the length limit.
        PermissionDeniedFault: If the path contains null bytes.

    Usage::

        async with AsyncWriteStream("/srv/out/data.bin", sandbox="/srv/out") as writer:
            await writer.write(chunk1)
            await writer.write(chunk2)
        # File is flushed and closed on context exit
    """

    __slots__ = (
        "_path",
        "_buffer",
        "_buffer_size",
        "_pool",
        "_fp",
        "_total_written",
    )

    def __init__(
        self,
        path: PathLike,
        *,
        buffer_size: int = 65_536,
        pool: FileSystemPool | None = None,
        config: FileSystemConfig | None = None,
        sandbox: PathLike | None = None,
    ) -> None:
        cfg = config or FileSystemConfig()
        self._path = validate_path(
            path,
            config=cfg,
            sandbox=sandbox or cfg.sandbox_root,
            operation="stream_write",
        )
        self._buffer = bytearray()
        self._buffer_size = buffer_size
        self._pool = pool or _get_default_pool()
        self._fp = None
        self._total_written = 0

    @property
    def path(self) -> Path:
        """Resolved, sandbox-validated destination path."""
        return self._path

    @property
    def total_written(self) -> int:
        """Total bytes written so far."""
        return self._total_written

    async def write(self, data: bytes) -> int:
        """
        Write data to the stream.

        Data is buffered and flushed when the buffer threshold is reached.

        Args:
            data: Bytes to write.

        Returns:
            Number of bytes accepted.
        """
        self._buffer.extend(data)
        self._total_written += len(data)

        if len(self._buffer) >= self._buffer_size:
            await self._flush()

        return len(data)

    async def flush(self) -> None:
        """Force-flush the buffer to disk."""
        await self._flush()
        if self._fp:
            await self._pool.run(self._fp.flush)

    async def close(self) -> None:
        """Flush remaining data and close the file."""
        await self._flush()
        if self._fp:
            with contextlib.suppress(Exception):
                await self._pool.run(self._fp.close)
            self._fp = None

    async def __aenter__(self) -> AsyncWriteStream:
        await self._ensure_open()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _ensure_open(self) -> None:
        """Open the file if not already open."""
        if self._fp is None:
            # Ensure parent directory exists
            parent = self._path.parent
            if not parent.exists():

                def _mkdirs():
                    parent.mkdir(parents=True, exist_ok=True)

                await self._pool.run(_mkdirs)

            def _open():
                return open(self._path, "wb")

            try:
                self._fp = await self._pool.run(_open)
            except Exception as exc:
                raise wrap_os_error(exc, "stream_write", str(self._path)) from exc

    async def _flush(self) -> None:
        """Flush buffer contents to disk."""
        if not self._buffer:
            return

        await self._ensure_open()

        buf = bytes(self._buffer)
        self._buffer.clear()

        try:
            await self._pool.run(self._fp.write, buf)
        except Exception as exc:
            raise wrap_os_error(exc, "stream_write", str(self._path)) from exc


async def stream_copy(
    src: PathLike,
    dst: PathLike,
    *,
    chunk_size: int = 65_536,
    pool: FileSystemPool | None = None,
    config: FileSystemConfig | None = None,
    sandbox: PathLike | None = None,
) -> int:
    """
    Copy a file via streaming.

    Memory usage is bounded to ``chunk_size`` regardless of file size.
    Creates parent directories for ``dst`` if needed.  Both paths are
    sandbox-validated before any descriptor is opened (SEC-FS-03).

    Args:
        src: Source file path.
        dst: Destination file path.
        chunk_size: Size of each transfer chunk.
        pool: Thread pool to use.
        config: Filesystem config supplying limits and ``sandbox_root``.
        sandbox: Sandbox root override applied to both paths.

    Returns:
        Total bytes copied.

    Raises:
        PathTraversalFault: If either path escapes the sandbox.
        FileSystemFault: On read/write failure.

    Usage::

        copied = await stream_copy(
            "/srv/uploads/in.bin",
            "/srv/uploads/out.bin",
            sandbox="/srv/uploads",
        )
    """
    total = 0
    stream = AsyncFileStream(
        src,
        chunk_size=chunk_size,
        pool=pool,
        config=config,
        sandbox=sandbox,
    )

    async with AsyncWriteStream(
        dst,
        buffer_size=chunk_size,
        pool=pool,
        config=config,
        sandbox=sandbox,
    ) as writer:
        async for chunk in stream:
            await writer.write(chunk)
            total += len(chunk)

    return total


async def stream_read(
    path: PathLike,
    *,
    chunk_size: int = 65_536,
    pool: FileSystemPool | None = None,
    offset: int = 0,
    end: int | None = None,
    config: FileSystemConfig | None = None,
    sandbox: PathLike | None = None,
) -> AsyncIterator[bytes]:
    """
    Stream a file in chunks.

    Convenience wrapper around :class:`AsyncFileStream`.  The path is
    sandbox-validated before the file is opened (SEC-FS-03).

    Args:
        path: File path to stream.
        chunk_size: Size of each chunk.
        pool: Thread pool to use.
        offset: Start byte offset.
        end: End byte offset (exclusive).
        config: Filesystem config supplying limits and ``sandbox_root``.
        sandbox: Sandbox root override.

    Yields:
        Chunks of bytes, each at most ``chunk_size`` long.

    Raises:
        PathTraversalFault: If the resolved path escapes the sandbox.
        FileSystemFault: On read failure.

    Usage::

        async for chunk in stream_read("/srv/uploads/a.bin", sandbox="/srv/uploads"):
            await response.write(chunk)
    """
    stream = AsyncFileStream(
        path,
        chunk_size=chunk_size,
        pool=pool,
        offset=offset,
        end=end,
        config=config,
        sandbox=sandbox,
    )
    async for chunk in stream:
        yield chunk


def _get_default_pool() -> FileSystemPool:
    """Get the default filesystem pool (lazy singleton)."""

    return _get()
