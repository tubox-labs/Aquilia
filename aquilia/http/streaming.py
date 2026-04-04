"""
AquilaHTTP — Streaming Support.

Async streaming utilities for request and response bodies.
Supports chunked encoding, progress tracking, and backpressure.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO


@dataclass
class StreamProgress:
    """Progress information for streaming operations."""

    bytes_transferred: int
    total_bytes: int | None
    elapsed: float

    @property
    def percentage(self) -> float | None:
        """Calculate progress percentage (0-100)."""
        if self.total_bytes is None or self.total_bytes == 0:
            return None
        return (self.bytes_transferred / self.total_bytes) * 100

    @property
    def bytes_per_second(self) -> float:
        """Calculate transfer rate."""
        if self.elapsed == 0:
            return 0.0
        return self.bytes_transferred / self.elapsed

    @property
    def eta_seconds(self) -> float | None:
        """Estimate remaining time in seconds."""
        if self.total_bytes is None:
            return None
        remaining = self.total_bytes - self.bytes_transferred
        rate = self.bytes_per_second
        if rate == 0:
            return None
        return remaining / rate


ProgressCallback = Callable[[StreamProgress], Coroutine[Any, Any, None]] | Callable[[StreamProgress], None]


class StreamingBody:
    """
    Streaming request body wrapper.

    Provides async iteration over bytes with optional progress tracking.
    """

    __slots__ = ("_source", "_chunk_size", "_total_size", "_on_progress")

    def __init__(
        self,
        source: bytes | AsyncIterator[bytes] | BinaryIO | Path,
        *,
        chunk_size: int = 65536,
        total_size: int | None = None,
        on_progress: ProgressCallback | None = None,
    ):
        """
        Initialize streaming body.

        Args:
            source: Data source (bytes, async iterator, file, or path).
            chunk_size: Size of chunks to yield.
            total_size: Total size in bytes (for progress tracking).
            on_progress: Callback for progress updates.
        """
        self._source = source
        self._chunk_size = chunk_size
        self._total_size = total_size
        self._on_progress = on_progress

    @property
    def content_length(self) -> int | None:
        """Get content length if known."""
        if self._total_size is not None:
            return self._total_size

        if isinstance(self._source, bytes):
            return len(self._source)

        if isinstance(self._source, Path):
            try:
                return self._source.stat().st_size
            except OSError:
                return None

        return None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate over chunks."""
        import time

        start_time = time.monotonic()
        bytes_sent = 0

        async for chunk in self._iter_source():
            bytes_sent += len(chunk)
            yield chunk

            if self._on_progress:
                elapsed = time.monotonic() - start_time
                progress = StreamProgress(
                    bytes_transferred=bytes_sent,
                    total_bytes=self._total_size,
                    elapsed=elapsed,
                )
                result = self._on_progress(progress)
                if asyncio.iscoroutine(result):
                    await result

    async def _iter_source(self) -> AsyncIterator[bytes]:
        """Iterate over the underlying source."""
        if isinstance(self._source, bytes):
            for i in range(0, len(self._source), self._chunk_size):
                yield self._source[i : i + self._chunk_size]

        elif isinstance(self._source, Path):
            async for chunk in stream_file(self._source, chunk_size=self._chunk_size):
                yield chunk

        elif hasattr(self._source, "read"):
            # File-like object - read in executor
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(
                    None,
                    self._source.read,
                    self._chunk_size,  # type: ignore
                )
                if not chunk:
                    break
                yield chunk

        else:
            # Assume async iterator
            async for chunk in self._source:  # type: ignore
                yield chunk


async def stream_file(
    path: Path | str,
    *,
    chunk_size: int = 65536,
) -> AsyncIterator[bytes]:
    """
    Stream a file asynchronously.

    Args:
        path: Path to file.
        chunk_size: Size of chunks to yield.

    Yields:
        File chunks.
    """
    path = Path(path)
    loop = asyncio.get_running_loop()

    def _read_chunks() -> bytes:
        with open(path, "rb") as f:
            return f.read(chunk_size)

    # Open file and read chunks in executor
    with open(path, "rb") as f:
        while True:
            chunk = await loop.run_in_executor(None, f.read, chunk_size)
            if not chunk:
                break
            yield chunk


async def stream_bytes(
    data: bytes,
    chunk_size: int = 65536,
) -> AsyncIterator[bytes]:
    """
    Stream bytes in chunks.

    Args:
        data: Bytes to stream.
        chunk_size: Size of chunks to yield.

    Yields:
        Data chunks.
    """
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]
        # Allow other tasks to run
        await asyncio.sleep(0)


async def collect_stream(stream: AsyncIterator[bytes]) -> bytes:
    """
    Collect all bytes from an async iterator.

    Args:
        stream: Async byte iterator.

    Returns:
        Complete bytes.
    """
    chunks: list[bytes] = []
    async for chunk in stream:
        chunks.append(chunk)
    return b"".join(chunks)


async def stream_with_limit(
    stream: AsyncIterator[bytes],
    max_bytes: int,
) -> AsyncIterator[bytes]:
    """
    Stream with a byte limit.

    Args:
        stream: Source stream.
        max_bytes: Maximum bytes to yield.

    Yields:
        Data chunks up to the limit.

    Raises:
        ValueError: If stream exceeds max_bytes.
    """
    total = 0
    async for chunk in stream:
        if total + len(chunk) > max_bytes:
            remaining = max_bytes - total
            if remaining > 0:
                yield chunk[:remaining]
            raise ValueError(f"Stream exceeded {max_bytes} bytes limit")
        total += len(chunk)
        yield chunk


class BufferedStream:
    """
    Buffered async stream reader.

    Provides line-by-line reading with buffering.
    """

    __slots__ = ("_stream", "_buffer", "_encoding")

    def __init__(
        self,
        stream: AsyncIterator[bytes],
        encoding: str = "utf-8",
    ):
        self._stream = stream
        self._buffer = b""
        self._encoding = encoding

    async def readline(self) -> str:
        """Read a single line."""
        while b"\n" not in self._buffer:
            try:
                chunk = await self._stream.__anext__()
                self._buffer += chunk
            except StopAsyncIteration:
                # End of stream - return remaining buffer
                line = self._buffer.decode(self._encoding)
                self._buffer = b""
                return line

        idx = self._buffer.index(b"\n")
        line = self._buffer[: idx + 1].decode(self._encoding)
        self._buffer = self._buffer[idx + 1 :]
        return line

    async def readlines(self) -> list[str]:
        """Read all lines."""
        lines: list[str] = []
        while True:
            line = await self.readline()
            if not line:
                break
            lines.append(line)
        return lines

    async def read(self, n: int = -1) -> bytes:
        """Read up to n bytes (or all if n=-1)."""
        if n == -1:
            # Read all remaining
            async for chunk in self._stream:
                self._buffer += chunk
            result = self._buffer
            self._buffer = b""
            return result

        while len(self._buffer) < n:
            try:
                chunk = await self._stream.__anext__()
                self._buffer += chunk
            except StopAsyncIteration:
                break

        result = self._buffer[:n]
        self._buffer = self._buffer[n:]
        return result


class ChunkedEncoder:
    """
    HTTP chunked transfer encoding encoder.

    Wraps a stream to produce chunked encoding format.
    """

    __slots__ = ("_stream",)

    def __init__(self, stream: AsyncIterator[bytes]):
        self._stream = stream

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate with chunked encoding."""
        async for chunk in self._stream:
            if chunk:
                # Chunk format: size\r\n data\r\n
                size = f"{len(chunk):x}\r\n".encode("ascii")
                yield size + chunk + b"\r\n"

        # Final chunk
        yield b"0\r\n\r\n"


class ChunkedDecoder:
    """
    HTTP chunked transfer encoding decoder.

    Decodes a chunked-encoded stream.
    """

    __slots__ = ("_stream", "_buffer")

    def __init__(self, stream: AsyncIterator[bytes]):
        self._stream = stream
        self._buffer = b""

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate decoding chunks."""
        async for raw in self._stream:
            self._buffer += raw

            while True:
                # Find chunk size line
                if b"\r\n" not in self._buffer:
                    break

                size_end = self._buffer.index(b"\r\n")
                size_line = self._buffer[:size_end].decode("ascii").strip()

                # Handle chunk extensions
                if ";" in size_line:
                    size_line = size_line.split(";")[0]

                try:
                    chunk_size = int(size_line, 16)
                except ValueError:
                    break

                # End of chunked data
                if chunk_size == 0:
                    return

                # Wait for full chunk
                needed = size_end + 2 + chunk_size + 2
                if len(self._buffer) < needed:
                    break

                # Extract chunk data
                chunk_start = size_end + 2
                chunk_data = self._buffer[chunk_start : chunk_start + chunk_size]
                self._buffer = self._buffer[needed:]

                yield chunk_data
