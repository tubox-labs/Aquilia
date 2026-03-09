"""
Async File Handle — Core I/O primitive for the Aquilia filesystem module.

Provides an ``AsyncFile`` class that wraps a native Python file object
with async method delegation via the dedicated thread pool.

Features:
    - Full read/write/seek/tell/close support
    - Write buffering for small writes (configurable)
    - Async context manager
    - Async iterator (line-by-line or chunk-by-chunk)
    - Mode validation (read/write/append/binary/text)
    - Automatic resource cleanup

Design notes:
    - Each ``AsyncFile`` owns exactly one OS file descriptor
    - The file descriptor is opened in the pool thread and all
      subsequent I/O is delegated to the same pool
    - Write buffering uses ``bytearray`` for zero-copy extend
    - ``__slots__`` for memory efficiency
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Iterable,
    Optional,
    Union,
)

from ._config import FileSystemConfig
from ._errors import FileClosedFault, wrap_os_error
from ._pool import FileSystemPool


class AsyncFile:
    """
    Async file handle with buffered I/O.

    Wraps a native Python file object and delegates all blocking
    operations to the dedicated filesystem thread pool.

    Usage::

        async with await async_open("data.txt", "r") as f:
            content = await f.read()

        # Or via the module function:
        from aquilia.filesystem import async_open
        async with async_open("log.txt", "a") as f:
            await f.write("entry\\n")
    """

    __slots__ = (
        "_fp",
        "_pool",
        "_name",
        "_mode",
        "_closed",
        "_write_buffer",
        "_write_buffer_size",
        "_encoding",
        "_binary",
    )

    def __init__(
        self,
        fp: Any,  # io.IOBase
        pool: FileSystemPool,
        name: str = "",
        mode: str = "r",
        write_buffer_size: int = 65_536,
    ) -> None:
        self._fp = fp
        self._pool = pool
        self._name = name or getattr(fp, "name", "")
        self._mode = mode
        self._closed = False
        self._binary = "b" in mode
        self._encoding = getattr(fp, "encoding", "utf-8") if not self._binary else None

        # Write buffering
        self._write_buffer: bytearray | None = None
        self._write_buffer_size = write_buffer_size
        if any(c in mode for c in ("w", "a", "x", "+")):
            self._write_buffer = bytearray()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """The file path/name."""
        return self._name

    @property
    def mode(self) -> str:
        """The mode the file was opened with."""
        return self._mode

    @property
    def closed(self) -> bool:
        """Whether the file has been closed."""
        return self._closed

    @property
    def encoding(self) -> Optional[str]:
        """Text encoding (None for binary files)."""
        return self._encoding

    # ── Reading ──────────────────────────────────────────────────────────

    async def read(self, size: int = -1) -> Union[bytes, str]:
        """
        Read up to ``size`` bytes/characters.

        Args:
            size: Number of bytes/chars to read.  ``-1`` reads all.

        Returns:
            ``bytes`` for binary mode, ``str`` for text mode.
        """
        self._check_closed("read")
        try:
            if size == -1:
                return await self._pool.run(self._fp.read)
            return await self._pool.run(self._fp.read, size)
        except Exception as exc:
            raise wrap_os_error(exc, "read", self._name) from exc

    async def readline(self) -> Union[bytes, str]:
        """Read a single line."""
        self._check_closed("readline")
        try:
            return await self._pool.run(self._fp.readline)
        except Exception as exc:
            raise wrap_os_error(exc, "readline", self._name) from exc

    async def readlines(self) -> list[Union[bytes, str]]:
        """Read all lines into a list."""
        self._check_closed("readlines")
        try:
            return await self._pool.run(self._fp.readlines)
        except Exception as exc:
            raise wrap_os_error(exc, "readlines", self._name) from exc

    async def readinto(self, buffer: bytearray) -> int:
        """
        Read bytes into a pre-allocated buffer (binary mode only).

        Uses ``memoryview`` for zero-copy.

        Args:
            buffer: Writable buffer to fill.

        Returns:
            Number of bytes read.
        """
        self._check_closed("readinto")
        if not self._binary:
            raise TypeError("readinto() requires binary mode")
        try:
            return await self._pool.run(self._fp.readinto, buffer)
        except Exception as exc:
            raise wrap_os_error(exc, "readinto", self._name) from exc

    # ── Writing ──────────────────────────────────────────────────────────

    async def write(self, data: Union[bytes, str]) -> int:
        """
        Write data to the file.

        If write buffering is enabled, small writes are accumulated
        in an internal buffer and flushed when the threshold is reached.

        Args:
            data: Bytes (binary mode) or string (text mode) to write.

        Returns:
            Number of bytes/characters written.
        """
        self._check_closed("write")

        if self._write_buffer is not None and self._write_buffer_size > 0:
            # Buffered write path
            if isinstance(data, str):
                raw = data.encode(self._encoding or "utf-8")
            else:
                raw = data
            self._write_buffer.extend(raw)
            written = len(data)

            if len(self._write_buffer) >= self._write_buffer_size:
                await self._flush_buffer()
            return written
        else:
            # Unbuffered / direct write
            try:
                return await self._pool.run(self._fp.write, data)
            except Exception as exc:
                raise wrap_os_error(exc, "write", self._name) from exc

    async def writelines(self, lines: Iterable[Union[bytes, str]]) -> None:
        """Write an iterable of lines."""
        self._check_closed("writelines")
        for line in lines:
            await self.write(line)

    async def flush(self) -> None:
        """
        Flush write buffer and OS buffers.

        Ensures all buffered data reaches the OS file descriptor.
        """
        self._check_closed("flush")
        await self._flush_buffer()
        try:
            await self._pool.run(self._fp.flush)
        except Exception as exc:
            raise wrap_os_error(exc, "flush", self._name) from exc

    async def truncate(self, size: Optional[int] = None) -> int:
        """Truncate the file to at most ``size`` bytes."""
        self._check_closed("truncate")
        await self._flush_buffer()
        try:
            if size is None:
                return await self._pool.run(self._fp.truncate)
            return await self._pool.run(self._fp.truncate, size)
        except Exception as exc:
            raise wrap_os_error(exc, "truncate", self._name) from exc

    # ── Positioning ──────────────────────────────────────────────────────

    async def seek(self, offset: int, whence: int = 0) -> int:
        """
        Move the file position.

        Flushes write buffer before seeking.

        Args:
            offset: Position offset.
            whence: 0 = absolute, 1 = relative, 2 = from end.

        Returns:
            New absolute position.
        """
        self._check_closed("seek")
        await self._flush_buffer()
        try:
            return await self._pool.run(self._fp.seek, offset, whence)
        except Exception as exc:
            raise wrap_os_error(exc, "seek", self._name) from exc

    async def tell(self) -> int:
        """Return the current file position."""
        self._check_closed("tell")
        try:
            return await self._pool.run(self._fp.tell)
        except Exception as exc:
            raise wrap_os_error(exc, "tell", self._name) from exc

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def close(self) -> None:
        """
        Flush buffers and close the underlying file descriptor.

        Safe to call multiple times.
        """
        if self._closed:
            return

        self._closed = True

        # Flush any remaining write buffer
        if self._write_buffer:
            try:
                buf = bytes(self._write_buffer)
                self._write_buffer.clear()
                if self._binary:
                    await self._pool.run(self._fp.write, buf)
                else:
                    text = buf.decode(self._encoding or "utf-8")
                    await self._pool.run(self._fp.write, text)
            except Exception:
                pass  # Best-effort on close

        try:
            await self._pool.run(self._fp.close)
        except Exception:
            pass  # Best-effort on close

    async def __aenter__(self) -> "AsyncFile":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ── Async Iteration ──────────────────────────────────────────────────

    def __aiter__(self) -> AsyncIterator[Union[bytes, str]]:
        """Iterate over lines (text mode) or chunks (binary mode)."""
        return self._aiter_impl()

    async def _aiter_impl(self) -> AsyncIterator[Union[bytes, str]]:
        """Internal async iterator."""
        while True:
            line = await self.readline()
            if not line:
                break
            yield line

    async def chunks(self, chunk_size: int = 65_536) -> AsyncIterator[bytes]:
        """
        Iterate over the file in fixed-size chunks.

        Useful for streaming large binary files.

        Args:
            chunk_size: Size of each chunk in bytes.

        Yields:
            Chunks of bytes.
        """
        self._check_closed("chunks")
        while True:
            chunk = await self.read(chunk_size)
            if not chunk:
                break
            yield chunk  # type: ignore[misc]

    # ── Internal ─────────────────────────────────────────────────────────

    def _check_closed(self, operation: str) -> None:
        """Raise ``FileClosedFault`` if the file is closed."""
        if self._closed:
            raise FileClosedFault(operation=operation, path=self._name)

    async def _flush_buffer(self) -> None:
        """Flush the internal write buffer to the OS file descriptor."""
        if self._write_buffer:
            buf = bytes(self._write_buffer)
            self._write_buffer.clear()
            try:
                if self._binary:
                    await self._pool.run(self._fp.write, buf)
                else:
                    text = buf.decode(self._encoding or "utf-8")
                    await self._pool.run(self._fp.write, text)
            except Exception as exc:
                raise wrap_os_error(exc, "write", self._name) from exc

    def __del__(self) -> None:
        """Best-effort cleanup on garbage collection."""
        if not self._closed and self._fp and not getattr(self._fp, "closed", True):
            try:
                self._fp.close()
            except Exception:
                pass

    def __repr__(self) -> str:
        state = "closed" if self._closed else "open"
        return f"<AsyncFile name={self._name!r} mode={self._mode!r} {state}>"
