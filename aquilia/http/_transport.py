"""
HTTP Transport Layer

Native async HTTP/1.1 using asyncio + ssl. No deps.
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import logging
import re
import socket
import ssl
import time
import zlib
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urlparse

from aquilia.http.config import HTTPClientConfig
from aquilia.http.faults import (
    CertificateVerifyFault,
    ConnectionClosedFault,
    ConnectionFault,
    ConnectionPoolExhaustedFault,
    ConnectTimeoutFault,
    DecodingFault,
    InvalidHeaderFault,
    InvalidResponseFault,
    InvalidURLFault,
    ProxyFault,
    ReadTimeoutFault,
    RequestBuildFault,
    RequestTimeoutFault,
    ResponseSizeExceededFault,
    TLSFault,
    TransportFault,
)
from aquilia.http.request import HTTPClientRequest, HTTPMethod
from aquilia.http.response import HTTPClientResponse, create_response

logger = logging.getLogger("aquilia.http.transport")

# limits
CRLF = b"\r\n"
HTTP_VERSION = b"HTTP/1.1"
DEFAULT_PORT_HTTP = 80
DEFAULT_PORT_HTTPS = 443
MAX_LINE_LENGTH = 65536
MAX_HEADERS = 100
CHUNK_SIZE = 65536

# Body framing modes, derived from the request method and response headers.
FRAMING_NONE = "none"
FRAMING_CONTENT_LENGTH = "content-length"
FRAMING_CHUNKED = "chunked"
FRAMING_UNTIL_CLOSE = "until-close"

# A single chunk larger than this is a framing error, not a payload.
MAX_CHUNK_SIZE = 16 * 1024 * 1024

_CHUNK_SIZE_RE = re.compile(r"^[0-9a-fA-F]{1,8}$")


def _host_matches_no_proxy(host: str, no_proxy: str | None) -> bool:
    """Match *host* against a comma-separated no_proxy list.

    Entries match exactly, as a domain suffix (``example.com`` matches
    ``api.example.com``), with a leading dot, or globally via ``*``.
    """
    if not no_proxy:
        return False
    host = host.lower()
    for entry in no_proxy.split(","):
        entry = entry.strip().lower()
        if not entry:
            continue
        if entry == "*":
            return True
        if entry.startswith("."):
            if host == entry[1:] or host.endswith(entry):
                return True
        elif host == entry or host.endswith("." + entry):
            return True
    return False


def _proxy_authorization(proxy_parsed) -> str | None:
    """Basic Proxy-Authorization credentials from the proxy URL userinfo."""
    if proxy_parsed.username is None and proxy_parsed.password is None:
        return None
    creds = f"{proxy_parsed.username or ''}:{proxy_parsed.password or ''}"
    return base64.b64encode(creds.encode()).decode()


@dataclass
class RawResponse:
    """Raw response before processing."""

    http_version: str
    status_code: int
    reason: str
    headers: dict[str, str]
    body: bytes = b""
    stream: AsyncIterator[bytes] | None = None


@dataclass
class ConnectionInfo:
    """Tracks a pooled connection."""

    host: str
    port: int
    ssl: bool
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)
    # Explicit pool key override. A proxied connection's endpoint is the
    # proxy, but its identity is the (target, proxy) pair -- two targets
    # through one proxy must never share a tunnel.
    pool_key: str | None = None
    # Set by ``ConnectionPool.acquire`` while the connection is checked
    # out: the in-flight slot it occupies is released by
    # ``put_connection``/``discard_connection`` when it returns to the
    # pool (or is closed). ``None`` while it sits idle in the pool.
    slot_key: str | None = None

    @property
    def age(self) -> float:
        return time.monotonic() - self.created_at

    def is_alive(self) -> bool:
        return not self.writer.is_closing()

    async def close(self) -> None:
        if not self.writer.is_closing():
            self.writer.close()
            try:
                await asyncio.wait_for(self.writer.wait_closed(), timeout=1.0)
            except (asyncio.TimeoutError, Exception):
                pass


class ConnectionPool:
    """Keep-alive connection pool. Reuses TCP connections per host.

    Every checked-out connection occupies one in-flight slot: a
    per-host semaphore (``max_per_host``) and a global semaphore
    (``max_connections``). ``acquire`` takes a slot first (waiting up
    to the pool timeout, then raising
    ``ConnectionPoolExhaustedFault``), then reuses an idle pooled
    connection or opens a new one under the slot. The slot is
    released synchronously when the connection is returned -- so the
    abort path in the transport (which must never await) can free it.
    """

    __slots__ = (
        "_connections",
        "_max_connections",
        "_max_per_host",
        "_max_keepalive",
        "_keepalive_expiry",
        "_lock",
        "_closed",
        "_global_semaphore",
        "_host_semaphores",
    )

    def __init__(
        self,
        max_connections: int = 100,
        max_per_host: int = 10,
        keepalive_expiry: float = 60.0,
        max_keepalive_connections: int | None = None,
    ):
        self._connections: dict[str, list[ConnectionInfo]] = {}
        self._max_connections = max_connections
        self._max_per_host = max_per_host
        self._max_keepalive = max_keepalive_connections
        self._keepalive_expiry = keepalive_expiry
        self._lock = asyncio.Lock()
        self._closed = False
        self._global_semaphore = asyncio.Semaphore(max_connections)
        self._host_semaphores: dict[str, asyncio.Semaphore] = {}

    def _make_key(self, host: str, port: int, ssl: bool) -> str:
        return f"{'https' if ssl else 'http'}://{host}:{port}"

    @staticmethod
    def _conn_key(conn: ConnectionInfo) -> str:
        """A connection's pool identity: its explicit proxy-aware key, or
        the plain endpoint key."""
        return conn.pool_key or f"{'https' if conn.ssl else 'http'}://{conn.host}:{conn.port}"

    async def get_connection(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        *,
        key: str | None = None,
    ) -> ConnectionInfo | None:
        """Grab a live idle connection if one exists."""
        key = key or self._make_key(host, port, use_ssl)

        async with self._lock:
            connections = self._connections.get(key, [])

            while connections:
                conn = connections.pop(0)

                if conn.age > self._keepalive_expiry:
                    await conn.close()
                    continue

                if conn.is_alive():
                    conn.last_used = time.monotonic()
                    return conn
                else:
                    await conn.close()

            return None

    async def _take_slot(self, key: str, timeout: float | None) -> None:
        """Acquire the global then per-host in-flight slots.

        Fixed order (global before host) so concurrent tasks can never
        deadlock holding one another's second slot. The wait is fully
        event-driven (semaphore), bounded by the pool timeout.
        """
        host_sem = self._host_semaphores.get(key)
        if host_sem is None:
            host_sem = asyncio.Semaphore(self._max_per_host)
            self._host_semaphores[key] = host_sem

        if timeout is not None and timeout > 0:
            try:
                await asyncio.wait_for(self._global_semaphore.acquire(), timeout)
            except asyncio.TimeoutError as e:
                raise ConnectionPoolExhaustedFault(
                    f"Timed out after {timeout:.2f}s waiting for a pool slot",
                    pool_size=self._max_connections,
                ) from e
            try:
                await asyncio.wait_for(host_sem.acquire(), timeout)
            except asyncio.TimeoutError as e:
                self._global_semaphore.release()
                raise ConnectionPoolExhaustedFault(
                    f"Timed out after {timeout:.2f}s waiting for a connection to {key}",
                    pool_size=self._max_per_host,
                ) from e
        else:
            await self._global_semaphore.acquire()
            await host_sem.acquire()

    def _release_slot(self, key: str) -> None:
        self._host_semaphores[key].release()
        self._global_semaphore.release()

    def _release_slots(self, conn: ConnectionInfo) -> None:
        """Free a connection's in-flight slot. Sync by design: the
        transport's abort path must release slots without awaiting,
        because a second cancellation must not interrupt cleanup."""
        key = conn.slot_key
        if key is None:
            return
        conn.slot_key = None
        self._release_slot(key)

    async def acquire(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        *,
        timeout: float | None = None,
        connect: Any = None,
        key: str | None = None,
    ) -> ConnectionInfo:
        """Acquire a connection: an idle pooled one if available, else a
        new one opened under an in-flight slot.

        Waits (event-driven) for a slot for at most ``timeout`` seconds
        before raising ``ConnectionPoolExhaustedFault``. ``key``
        overrides the pool identity (proxy-aware connections share the
        endpoint with the proxy but not the identity).
        """
        if self._closed:
            raise ConnectionClosedFault("Connection pool is closed")

        key = key or self._make_key(host, port, use_ssl)
        await self._take_slot(key, timeout)

        try:
            # Another task may have pooled a connection while we waited
            # for the slot -- prefer reuse over opening a new socket.
            conn = await self.get_connection(host, port, use_ssl, key=key)
            if conn is not None:
                conn.slot_key = key
                return conn

            if connect is None:
                self._release_slot(key)
                raise ConnectionClosedFault(
                    f"No pooled connection to {key} and no connector available"
                )

            conn = await connect()
        except BaseException:
            self._release_slot(key)
            raise

        conn.slot_key = key
        return conn

    def discard_connection(self, conn: ConnectionInfo) -> None:
        """Abandon a connection without pooling it (sync, cancellation-safe)."""
        self._release_slots(conn)

    async def put_connection(self, conn: ConnectionInfo) -> bool:
        """Return connection to pool if we have room.

        A closed pool takes ownership of nothing: the connection is closed
        instead, so a response finishing its body after the client was shut
        down cannot resurrect an open connection inside a dead pool.

        The connection's in-flight slot is always released here -- pooled
        or not -- so waiters in ``acquire`` can proceed.
        """
        pooled = False
        async with self._lock:
            if not self._closed:
                key = self._conn_key(conn)
                connections = self._connections.setdefault(key, [])

                within_idle_cap = self._max_keepalive is None or len(connections) < self._max_keepalive

                if within_idle_cap and len(connections) < self._max_per_host:
                    total_idle = sum(len(c) for c in self._connections.values())
                    if total_idle < self._max_connections:
                        connections.append(conn)
                        conn.last_used = time.monotonic()
                        pooled = True

        if not pooled:
            await conn.close()

        self._release_slots(conn)
        return pooled

    async def close_all(self) -> None:
        async with self._lock:
            self._closed = True
            for connections in self._connections.values():
                for conn in connections:
                    await conn.close()
            self._connections.clear()

    async def cleanup_expired(self) -> int:
        """Prune dead/expired connections."""
        removed = 0

        async with self._lock:
            for key in list(self._connections.keys()):
                connections = self._connections[key]
                alive = []

                for conn in connections:
                    if conn.age > self._keepalive_expiry or not conn.is_alive():
                        await conn.close()
                        removed += 1
                    else:
                        alive.append(conn)

                if alive:
                    self._connections[key] = alive
                else:
                    del self._connections[key]

        return removed


class _StreamDecompressor:
    """Streaming gzip/deflate decoder for response bodies.

    Fed chunk by chunk instead of buffering the whole body: multi-member
    gzip streams (a gzip body is a sequence of members) roll into a fresh
    decompressor, and the zlib-vs-raw deflate ambiguity is resolved on
    the first bytes. The ``limit`` argument bounds the output of each
    call so a compressed bomb cannot expand into unbounded memory.
    """

    __slots__ = ("_encoding", "_decompressor", "_pending", "_started", "_zlib_wrapped")

    def __init__(self, encoding: str):
        self._encoding = encoding
        self._pending = b""
        self._started = False
        # deflate: some servers send raw deflate despite the name; try the
        # zlib-wrapped format first and fall back on the first bytes.
        self._zlib_wrapped = encoding == "deflate"
        if encoding == "gzip":
            self._decompressor: zlib.Decompress | None = zlib.decompressobj(16 + zlib.MAX_WBITS)
        elif encoding == "deflate":
            self._decompressor = zlib.decompressobj()
        else:
            self._decompressor = None

    def _new_decompressor(self) -> zlib.Decompress:
        if self._encoding == "deflate":
            if self._zlib_wrapped:
                return zlib.decompressobj()
            return zlib.decompressobj(-zlib.MAX_WBITS)
        return zlib.decompressobj(16 + zlib.MAX_WBITS)

    def decompress(self, data: bytes, limit: int | None) -> bytes:
        """Decompress *data*, returning at most *limit* bytes.

        Input that could not be processed (the output limit was hit)
        stays buffered inside and is returned by the next call.
        """
        d = self._decompressor
        if d is None:
            return data

        out = bytearray()
        pending = self._pending + data
        self._pending = b""

        while True:
            if d.eof:
                # End of a gzip member: whatever is left starts the next.
                unused = d.unused_data
                if not unused:
                    break
                # unused_data IS the remainder of the input -- the member
                # consumed its prefix -- so it replaces pending outright;
                # prepending would replay already-decompressed members forever.
                pending = unused
                d = self._new_decompressor()
                self._decompressor = d

            try:
                if limit is None:
                    piece = d.decompress(pending)
                else:
                    max_length = limit - len(out)
                    if max_length <= 0:
                        break
                    piece = d.decompress(pending, max_length)
            except zlib.error:
                if self._encoding == "deflate" and not self._started and self._zlib_wrapped:
                    # Raw deflate despite the name -- retry unwrapped.
                    self._zlib_wrapped = False
                    d = zlib.decompressobj(-zlib.MAX_WBITS)
                    self._decompressor = d
                    continue
                raise

            self._started = True
            out += piece

            if d.eof:
                continue  # open the next member, if any

            pending = d.unconsumed_tail
            if not pending or not piece or (limit is not None and len(out) >= limit):
                break

        self._pending = pending
        return bytes(out)


class _BodyReader:
    """Framing-aware incremental HTTP/1.1 response body reader.

    The body is yielded chunk by chunk as it arrives, decompressed on
    the fly, and the framing is validated strictly: a short
    content-length read or a malformed chunk size is a fault, never a
    silently truncated payload.

    ``completed_cleanly`` is the pool's release gate -- a connection
    whose body was not framed to completion must never be reused, or the
    next request reads leftover bytes.
    """

    __slots__ = (
        "_reader",
        "_framing",
        "_length",
        "_encoding",
        "_decompressor",
        "_read_timeout",
        "_deadline",
        "_max_size",
        "_produced",
        "_extensions",
        "_url",
        "completed_cleanly",
    )

    def __init__(
        self,
        reader: asyncio.StreamReader,
        framing: str,
        *,
        content_length: int = 0,
        content_encoding: str = "",
        read_timeout: float | None = None,
        deadline: float | None = None,
        max_size: int | None = None,
        extensions: dict[str, Any] | None = None,
        url: str = "",
    ):
        self._reader = reader
        self._framing = framing
        self._length = content_length
        self._encoding = content_encoding
        self._decompressor = _StreamDecompressor(content_encoding) if content_encoding in ("gzip", "deflate") else None
        self._read_timeout = read_timeout
        self._deadline = deadline
        self._max_size = max_size
        self._produced = 0
        self._extensions = extensions if extensions is not None else {}
        self._url = url
        self.completed_cleanly = False

    def _next_timeout(self) -> tuple[float, type[ReadTimeoutFault] | type[RequestTimeoutFault]] | None:
        """Effective timeout for the next read: read timeout vs deadline."""
        best: tuple[float, type[ReadTimeoutFault] | type[RequestTimeoutFault]] | None = None
        if self._read_timeout is not None and self._read_timeout > 0:
            best = (self._read_timeout, ReadTimeoutFault)
        if self._deadline is not None:
            remaining = self._deadline - time.monotonic()
            if best is None or remaining < best[0]:
                # A total deadline now bounds the whole body (D-6).
                best = (max(remaining, 0.0), RequestTimeoutFault)
        return best

    async def _read(self, n: int) -> bytes:
        timeout_pair = self._next_timeout()
        if timeout_pair is None:
            return await self._reader.read(n)

        timeout, fault_cls = timeout_pair
        try:
            return await asyncio.wait_for(self._reader.read(n), timeout=timeout)
        except asyncio.TimeoutError as e:
            raise fault_cls(
                f"{'Read' if fault_cls is ReadTimeoutFault else 'Request'} timed out after {timeout:.2f}s",
                timeout=timeout,
                url=self._url,
            ) from e

    async def _read_line(self) -> bytes:
        timeout_pair = self._next_timeout()
        if timeout_pair is None:
            try:
                return await self._reader.readline()
            except (ValueError, asyncio.LimitOverrunError) as e:
                raise InvalidResponseFault(f"Response line exceeds {MAX_LINE_LENGTH} byte limit: {e}") from e

        timeout, fault_cls = timeout_pair
        try:
            return await asyncio.wait_for(self._reader.readline(), timeout=timeout)
        except asyncio.TimeoutError as e:
            raise fault_cls(
                f"{'Read' if fault_cls is ReadTimeoutFault else 'Request'} timed out after {timeout:.2f}s",
                timeout=timeout,
                url=self._url,
            ) from e
        except (ValueError, asyncio.LimitOverrunError) as e:
            raise InvalidResponseFault(f"Response line exceeds {MAX_LINE_LENGTH} byte limit: {e}") from e

    def _decode(self, chunk: bytes) -> list[bytes]:
        """Decompress a chunk and enforce the response size budget."""
        if self._decompressor is None:
            pieces = [chunk] if chunk else []
        else:
            try:
                if self._max_size is not None:
                    # One byte over the remaining budget: the overshoot
                    # itself proves the limit was passed.
                    piece = self._decompressor.decompress(chunk, self._max_size - self._produced + 1)
                else:
                    piece = self._decompressor.decompress(chunk, None)
            except zlib.error as e:
                # A corrupt body must not masquerade as the payload.
                raise DecodingFault(
                    f"Failed to decompress {self._encoding} body: {e}",
                    encoding=self._encoding,
                ) from e
            pieces = [piece] if piece else []

        for piece in pieces:
            self._produced += len(piece)

        if self._max_size is not None and self._produced > self._max_size:
            raise ResponseSizeExceededFault(
                f"Response body exceeded {self._max_size} bytes",
                url=self._url,
                max_size=self._max_size,
                bytes_read=self._produced,
            )

        return pieces

    async def __aiter__(self) -> AsyncIterator[bytes]:
        if self._framing == FRAMING_NONE:
            # HEAD responses and 1xx/204/304 carry no body regardless of
            # what the headers claim; the framing is complete immediately.
            self.completed_cleanly = True
            return

        if self._framing == FRAMING_CHUNKED:
            # Loop until the 0-size terminator returns from inside.
            while True:
                size_line = await self._read_line()
                size_str = size_line.strip().decode("latin-1")

                # chunk extensions (rare but possible)
                if ";" in size_str:
                    size_str = size_str.split(";", 1)[0]

                if not _CHUNK_SIZE_RE.match(size_str):
                    raise InvalidResponseFault(f"Invalid chunk size: {size_str!r}")

                chunk_size = int(size_str, 16)

                if chunk_size == 0:
                    # Trailer section: field lines until a blank line.
                    trailers: list[tuple[str, str]] = []
                    while True:
                        line = (await self._read_line()).strip()
                        if not line:
                            break
                        line_str = line.decode("latin-1")
                        if ":" in line_str:
                            name, value = line_str.split(":", 1)
                            trailers.append((name.strip(), value.strip()))
                    if trailers:
                        self._extensions["http.response.trailers"] = trailers
                    self.completed_cleanly = True
                    return

                if chunk_size > MAX_CHUNK_SIZE:
                    raise InvalidResponseFault(
                        f"Chunk size {chunk_size} exceeds {MAX_CHUNK_SIZE} byte limit"
                    )

                remaining = chunk_size
                while remaining > 0:
                    chunk = await self._read(min(CHUNK_SIZE, remaining))
                    if not chunk:
                        raise ConnectionClosedFault(
                            f"Connection closed inside chunk ({remaining} bytes outstanding)",
                            url=self._url,
                        )
                    remaining -= len(chunk)
                    for piece in self._decode(chunk):
                        yield piece

                crlf = await self._read_line()
                if crlf.strip():
                    raise InvalidResponseFault(f"Missing CRLF after chunk: {crlf[:32]!r}")

        elif self._framing == FRAMING_CONTENT_LENGTH:
            remaining = self._length
            while remaining > 0:
                chunk = await self._read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    # A short read is a dead connection, not a partial
                    # body: half a payload must not look like success.
                    raise ConnectionClosedFault(
                        f"Connection closed with {remaining} of {self._length} body bytes unread",
                        url=self._url,
                    )
                remaining -= len(chunk)
                for piece in self._decode(chunk):
                    yield piece
            self.completed_cleanly = True
            return

        else:
            # Read until close (HTTP/1.0 style): EOF completes the body,
            # a stall is a timeout, never a silent end of stream.
            while True:
                chunk = await self._read(CHUNK_SIZE)
                if not chunk:
                    break
                for piece in self._decode(chunk):
                    yield piece
            self.completed_cleanly = True
            return


class HTTPTransport(ABC):
    """Base transport interface."""

    @abstractmethod
    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse: ...
    @abstractmethod
    async def close(self) -> None: ...

    async def __aenter__(self) -> HTTPTransport:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


class NativeTransport(HTTPTransport):
    """
    Pure asyncio HTTP/1.1 transport.

    - keep-alive + connection pooling
    - TLS/SSL
    - chunked encoding
    - gzip/deflate
    - timeouts
    """

    __slots__ = ("_config", "_pool", "_closed")

    def __init__(self, config: HTTPClientConfig | None = None):
        self._config = config or HTTPClientConfig()
        self._pool = ConnectionPool(
            max_connections=self._config.pool.max_connections,
            max_per_host=self._config.pool.max_connections_per_host,
            keepalive_expiry=self._config.pool.keepalive_expiry,
            max_keepalive_connections=self._config.pool.max_keepalive_connections,
        )
        self._closed = False

    def _create_ssl_context(self) -> ssl.SSLContext | None:
        tls = self._config.tls

        if not tls.verify:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        if tls.ssl_context:
            return tls.ssl_context

        ctx = ssl.create_default_context()

        if tls.ca_bundle:
            ctx.load_verify_locations(tls.ca_bundle)
        elif tls.verify:
            try:
                import certifi

                ctx.load_verify_locations(certifi.where())
            except (ImportError, OSError, ssl.SSLError):
                # Fall back to system trust store when certifi is unavailable.
                pass

        if tls.cert_file:
            ctx.load_cert_chain(certfile=tls.cert_file, keyfile=tls.key_file)

        if tls.minimum_version:
            version_map = {
                "TLSv1.2": ssl.TLSVersion.TLSv1_2,
                "TLSv1.3": ssl.TLSVersion.TLSv1_3,
            }
            if tls.minimum_version in version_map:
                ctx.minimum_version = version_map[tls.minimum_version]

        return ctx

    async def _resolve_addresses(
        self,
        host: str,
        port: int,
        timeout: float | None,
    ) -> list[tuple[int, str, int]]:
        loop = asyncio.get_running_loop()

        try:
            addr_info = await asyncio.wait_for(
                loop.getaddrinfo(
                    host,
                    port,
                    type=socket.SOCK_STREAM,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError as e:
            raise ConnectTimeoutFault(
                f"DNS resolution for {host}:{port} timed out after {timeout or 0:.2f}s",
                timeout=timeout or 0,
                url=f"{host}:{port}",
            ) from e
        except OSError as e:
            raise ConnectionFault(
                f"DNS resolution failed for {host}:{port}: {e}",
                host=host,
                port=port,
                cause=str(e),
            ) from e

        addresses: list[tuple[int, str, int]] = []
        seen: set[tuple[int, str, int]] = set()

        for family, _socktype, _proto, _canonname, sockaddr in addr_info:
            if family not in (socket.AF_INET, socket.AF_INET6):
                continue

            resolved_host = str(sockaddr[0])
            resolved_port = int(sockaddr[1])
            key = (family, resolved_host, resolved_port)

            if key in seen:
                continue

            seen.add(key)
            addresses.append(key)

        if not addresses:
            raise ConnectionFault(
                f"No connectable addresses resolved for {host}:{port}",
                host=host,
                port=port,
            )

        return addresses

    async def _connect(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: float | None = None,
    ) -> ConnectionInfo:
        connect_timeout = timeout or self._config.timeout.connect or 10.0

        ssl_context: ssl.SSLContext | None = None
        if use_ssl:
            ssl_context = self._create_ssl_context()

        addresses = await self._resolve_addresses(host, port, connect_timeout)
        last_os_error: OSError | None = None
        timeout_attempts = 0

        for family, resolved_host, resolved_port in addresses:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        host=resolved_host,
                        port=resolved_port,
                        ssl=ssl_context,
                        family=family,
                        server_hostname=host if use_ssl else None,
                        ssl_handshake_timeout=connect_timeout if use_ssl else None,
                        limit=MAX_LINE_LENGTH,
                    ),
                    timeout=connect_timeout,
                )

                return ConnectionInfo(
                    host=host,
                    port=port,
                    ssl=use_ssl,
                    reader=reader,
                    writer=writer,
                )

            except asyncio.TimeoutError:
                timeout_attempts += 1
                continue

            except ssl.SSLCertVerificationError as e:
                raise CertificateVerifyFault(
                    f"Cert verify failed for {host}: {e}",
                    url=f"https://{host}:{port}",
                    reason=str(e),
                ) from e

            except ssl.SSLError as e:
                raise TLSFault(
                    f"SSL error connecting to {host}: {e}",
                    url=f"https://{host}:{port}",
                    reason=str(e),
                ) from e

            except OSError as e:
                last_os_error = e
                continue

        if timeout_attempts > 0 and timeout_attempts == len(addresses):
            raise ConnectTimeoutFault(
                f"Connection to {host}:{port} timed out after {connect_timeout:.2f}s",
                timeout=connect_timeout,
                url=f"{'https' if use_ssl else 'http'}://{host}:{port}",
            )

        if last_os_error is not None:
            raise ConnectionFault(
                f"Connection failed to {host}:{port}: {last_os_error}",
                host=host,
                port=port,
                cause=str(last_os_error),
            ) from last_os_error

        raise ConnectionFault(
            f"Connection failed to {host}:{port}",
            host=host,
            port=port,
            cause="No address succeeded",
        )

    async def _get_connection(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: float | None = None,
    ) -> ConnectionInfo:
        # try pool first
        conn = await self._pool.get_connection(host, port, use_ssl)
        if conn:
            return conn
        return await self._connect(host, port, use_ssl, timeout)

    def _select_proxy(self, scheme: str, host: str) -> str | None:
        """Pick the proxy URL for a request, honoring no_proxy."""
        proxy = self._config.proxy
        if proxy is None:
            return None
        url = proxy.https_proxy if scheme == "https" else proxy.http_proxy
        if not url:
            return None
        if _host_matches_no_proxy(host, proxy.no_proxy):
            return None
        return url

    async def _connect_via_proxy(
        self,
        host: str,
        port: int,
        proxy_url: str,
        use_ssl: bool,
        timeout: float | None,
        pool_key: str,
    ) -> ConnectionInfo:
        """Open a connection to the target through an HTTP proxy.

        Plain HTTP targets are requested in absolute form over the
        proxy connection; HTTPS targets get a CONNECT tunnel, and the
        TLS handshake inside the tunnel verifies the TARGET host --
        never the proxy.
        """
        proxy_parsed = urlparse(proxy_url)
        proxy_host = proxy_parsed.hostname or ""
        proxy_port = proxy_parsed.port or (DEFAULT_PORT_HTTPS if proxy_parsed.scheme == "https" else DEFAULT_PORT_HTTP)
        proxy_tls = proxy_parsed.scheme == "https"
        auth = _proxy_authorization(proxy_parsed)

        connect_timeout = timeout or self._config.timeout.connect or 10.0
        ssl_context = self._create_ssl_context() if proxy_tls else None

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                host=proxy_host,
                port=proxy_port,
                ssl=ssl_context,
                ssl_handshake_timeout=connect_timeout if proxy_tls else None,
                limit=MAX_LINE_LENGTH,
            ),
            timeout=connect_timeout,
        )

        try:
            if use_ssl:
                # CONNECT tunnel to the target.
                lines = [f"CONNECT {host}:{port} HTTP/1.1", f"Host: {host}:{port}"]
                if auth:
                    lines.append(f"Proxy-Authorization: Basic {auth}")
                writer.write(("\r\n".join(lines) + "\r\n\r\n").encode("latin-1"))
                await asyncio.wait_for(writer.drain(), timeout=connect_timeout)

                status_line = (await asyncio.wait_for(reader.readline(), timeout=connect_timeout)).decode("latin-1")
                parts = status_line.split(maxsplit=2)
                if len(parts) < 2 or not parts[1].isdigit() or not 200 <= int(parts[1]) < 300:
                    writer.close()
                    raise ProxyFault(
                        f"Proxy refused CONNECT tunnel: {status_line.strip()}",
                        proxy_url=proxy_url,
                        url=f"https://{host}:{port}",
                    )

                # Drain the CONNECT response headers.
                while True:
                    line = await asyncio.wait_for(reader.readline(), timeout=connect_timeout)
                    if line in (b"\r\n", b"\n", b""):
                        break

                # TLS upgrade inside the tunnel. server_hostname is the
                # TARGET host: the certificate presented must belong to
                # the origin, not to the proxy relaying it.
                loop = asyncio.get_running_loop()
                transport = writer.transport
                protocol = transport.get_protocol()
                tls_transport = await asyncio.wait_for(
                    loop.start_tls(
                        transport,
                        protocol,
                        self._create_ssl_context(),
                        server_hostname=host,
                        ssl_handshake_timeout=connect_timeout,
                    ),
                    timeout=connect_timeout,
                )
                writer = asyncio.StreamWriter(tls_transport, protocol, reader, loop)

            return ConnectionInfo(
                host=proxy_host,
                port=proxy_port,
                ssl=use_ssl,
                reader=reader,
                writer=writer,
                pool_key=pool_key,
            )
        except ProxyFault:
            raise
        except asyncio.TimeoutError as e:
            writer.close()
            raise ConnectTimeoutFault(
                f"Proxy connection to {proxy_url} timed out after {connect_timeout:.2f}s",
                timeout=connect_timeout,
                url=proxy_url,
            ) from e
        except ssl.SSLError as e:
            writer.close()
            raise TLSFault(f"TLS error via proxy {proxy_url}: {e}", url=proxy_url, reason=str(e)) from e
        except OSError as e:
            writer.close()
            raise ConnectionFault(
                f"Proxy connection to {proxy_url} failed: {e}",
                url=proxy_url,
                host=proxy_host,
                port=proxy_port,
                cause=str(e),
            ) from e

    def _build_request_bytes(
        self,
        request: HTTPClientRequest,
        *,
        absolute_form: bool = False,
        proxy_authorization: str | None = None,
    ) -> bytes:
        parsed = urlparse(request.url)

        # URL credentials are rejected, never honored: silently dropping
        # them would send an unauthenticated request while the caller
        # believes auth was applied.
        if parsed.username is not None or parsed.password is not None:
            raise InvalidURLFault(
                f"URL credentials are not supported; pass auth= instead: {request.url}",
                url=request.url,
            )

        # Percent-encode the path so raw spaces or control characters
        # cannot smuggle extra lines onto the wire. "/" and existing "%"
        # escapes survive untouched, so already-encoded URLs are no-ops.
        path = quote(parsed.path or "/", safe="/%")
        if parsed.query:
            query = quote(parsed.query, safe="=&%+?/:@,;$")
            path = f"{path}?{query}"

        # Plain HTTP through a proxy uses the absolute-form request
        # target (RFC 9110 §7.1) so the proxy knows where to forward.
        if absolute_form:
            request_target = request.url
        else:
            request_target = path
        lines = [f"{request.method.value} {request_target} HTTP/1.1"]

        headers = dict(request.headers)

        # Host header
        if "Host" not in headers:
            hostname = parsed.hostname or ""
            if ":" in hostname:
                # IPv6 literal: ``urlparse`` strips the brackets, the wire
                # format requires them back.
                hostname = f"[{hostname}]"
            if parsed.port and parsed.port not in (80, 443):
                headers["Host"] = f"{hostname}:{parsed.port}"
            else:
                headers["Host"] = hostname or parsed.netloc

        # defaults
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._config.user_agent
        if "Accept" not in headers:
            headers["Accept"] = "*/*"
        if "Accept-Encoding" not in headers:
            # Derived from the configured algorithms, not hardcoded: the
            # client must only advertise what its config says it accepts.
            headers["Accept-Encoding"] = (
                ", ".join(algo.value for algo in self._config.compression) or "gzip, deflate"
            )
        if "Connection" not in headers:
            headers["Connection"] = "keep-alive"

        # body length
        if request.body is not None and isinstance(request.body, bytes):
            headers["Content-Length"] = str(len(request.body))

        # Streaming bodies: either the caller pinned an explicit
        # Content-Length (honored byte-exactly by _write_streaming_body)
        # or the body travels chunked.
        if request.is_streaming():
            has_explicit_length = any(
                name.lower() == "content-length" for name in headers
            )
            if not has_explicit_length and "Transfer-Encoding" not in headers:
                headers["Transfer-Encoding"] = "chunked"

        # basic auth
        if request.auth:
            creds = f"{request.auth[0]}:{request.auth[1]}"
            encoded = base64.b64encode(creds.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        # Proxy credentials from the proxy URL userinfo travel as
        # Proxy-Authorization, separate from end-to-end Authorization.
        if proxy_authorization is not None and "Proxy-Authorization" not in headers:
            headers["Proxy-Authorization"] = f"Basic {proxy_authorization}"

        for name, value in headers.items():
            lines.append(f"{name}: {value}")

        lines.append("")
        lines.append("")

        # Header values travel as latin-1 on the wire. Requests built
        # through RequestBuilder are validated up front; this guard is the
        # backstop for requests constructed directly with a raw dict.
        try:
            request_bytes = "\r\n".join(lines).encode("latin-1")
        except UnicodeEncodeError as e:
            raise InvalidHeaderFault(
                f"Request head contains characters not encodable as latin-1: {e}",
            ) from e

        if request.body is not None and isinstance(request.body, bytes):
            request_bytes += request.body

        return request_bytes

    async def _read_line(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> bytes:
        read_timeout = timeout or self._config.timeout.read or self._config.timeout.total or 30.0

        try:
            line = await asyncio.wait_for(reader.readline(), timeout=read_timeout)
            if len(line) > MAX_LINE_LENGTH:
                raise InvalidResponseFault(f"Line too long: {len(line)} bytes")
            return line

        except asyncio.TimeoutError as e:
            raise ReadTimeoutFault(f"Read timed out after {read_timeout:.2f}s", timeout=read_timeout) from e
        except (ValueError, asyncio.LimitOverrunError) as e:
            # readline() raises these when a line exceeds the stream limit.
            raise InvalidResponseFault(f"Response line exceeds {MAX_LINE_LENGTH} byte limit: {e}") from e

    async def _read_response_head(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> tuple[str, int, str, list[tuple[str, str]]]:
        """Read the status line and header block.

        Returns the raw ``(name, value)`` field lines in arrival order.
        Multi-value headers (notably repeated ``Set-Cookie``) are preserved
        as separate entries -- collapsing them into a dict here is lossy,
        since ``Set-Cookie`` must not be combined (RFC 9110 §5.2) and a
        cookie jar that only ever sees the last line silently loses
        sessions.
        """
        status_line = await self._read_line(reader, timeout)
        if not status_line:
            raise ConnectionClosedFault("Connection closed while reading response")

        status_line = status_line.strip().decode("latin-1")

        # HTTP/1.1 200 OK
        match = re.match(r"HTTP/(\d\.\d)\s+(\d{3})\s*(.*)", status_line)
        if not match:
            raise InvalidResponseFault(f"Invalid status line: {status_line}")

        http_version = match.group(1)
        status_code = int(match.group(2))
        reason = match.group(3)

        headers: list[tuple[str, str]] = []
        header_count = 0

        while True:
            line = await self._read_line(reader, timeout)
            line = line.strip()

            if not line:
                break

            header_count += 1
            if header_count > MAX_HEADERS:
                raise InvalidResponseFault(f"Too many headers: {header_count}")

            line_str = line.decode("latin-1")
            if ":" not in line_str:
                raise InvalidResponseFault(f"Invalid header: {line_str}")

            name, value = line_str.split(":", 1)
            headers.append((name.strip(), value.strip()))

        return http_version, status_code, reason, headers

    def _decompress_body(self, body: bytes, encoding: str) -> bytes:
        encoding = encoding.lower()

        if encoding == "gzip":
            try:
                return gzip.decompress(body)
            except Exception as e:
                # A corrupt body must not masquerade as the payload (N-13):
                # silently passing it through hides the corruption.
                raise DecodingFault(
                    f"Failed to decompress gzip body: {e}",
                    encoding="gzip",
                ) from e

        elif encoding == "deflate":
            try:
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                try:
                    return zlib.decompress(body)
                except Exception as e:
                    raise DecodingFault(
                        f"Failed to decompress deflate body: {e}",
                        encoding="deflate",
                    ) from e

        return body

    @staticmethod
    def _body_framing(
        request: HTTPClientRequest,
        status_code: int,
        raw_headers: list[tuple[str, str]],
        headers_lower: dict[str, str],
    ) -> tuple[str, int]:
        """Pick the body framing mode and declared length for a response."""
        # HEAD responses and 1xx/204/304 carry no body regardless of
        # what the headers claim.
        if request.method == HTTPMethod.HEAD or status_code < 200 or status_code in (204, 304):
            return FRAMING_NONE, 0

        transfer_encoding = headers_lower.get("transfer-encoding", "").lower()
        tokens = [token.strip() for token in transfer_encoding.split(",") if token.strip()]
        if "chunked" in tokens:
            return FRAMING_CHUNKED, 0

        content_length_values = [value.strip() for name, value in raw_headers if name.lower() == "content-length"]
        if content_length_values:
            # Disagreement between repeated Content-Length fields is a
            # request-smuggling vector, not something to average out.
            if len(set(content_length_values)) > 1:
                raise InvalidResponseFault(f"Conflicting Content-Length values: {content_length_values}")
            try:
                length = int(content_length_values[0])
            except ValueError:
                raise InvalidResponseFault(f"Invalid Content-Length: {content_length_values[0]!r}") from None
            if length < 0:
                raise InvalidResponseFault(f"Negative Content-Length: {length}")
            return FRAMING_CONTENT_LENGTH, length

        return FRAMING_UNTIL_CLOSE, 0

    async def _write_streaming_body(
        self,
        conn: ConnectionInfo,
        request: HTTPClientRequest,
        write_timeout: float,
    ) -> None:
        """Write a streaming (AsyncIterator) request body.

        An explicit user-supplied Content-Length is honored
        byte-exactly -- under- or over-shooting it is a
        RequestBuildFault, not a silently malformed request. Without
        one, the body travels chunked via ChunkedEncoder. Any failure
        propagates: the caller (send) closes the connection on error
        instead of pooling a half-written socket.
        """
        from aquilia.http.streaming import ChunkedEncoder

        body = request.body
        assert body is not None  # guarded by is_streaming()

        cl_values = [v for k, v in request.headers.items() if k.lower() == "content-length"]
        explicit_length: int | None = None
        if cl_values:
            try:
                explicit_length = int(cl_values[0])
            except ValueError:
                raise RequestBuildFault(
                    f"Invalid Content-Length for streaming body: {cl_values[0]!r}",
                    url=request.url,
                ) from None
            if explicit_length < 0:
                raise RequestBuildFault(
                    f"Negative Content-Length for streaming body: {explicit_length}",
                    url=request.url,
                )

        written = 0
        try:
            if explicit_length is not None:
                async for chunk in body:
                    data = bytes(chunk)
                    written += len(data)
                    if written > explicit_length:
                        raise RequestBuildFault(
                            f"Streaming body exceeded its Content-Length "
                            f"{explicit_length}: at least {written} bytes",
                            url=request.url,
                        )
                    conn.writer.write(data)
                    await asyncio.wait_for(conn.writer.drain(), timeout=write_timeout)
                if written != explicit_length:
                    raise RequestBuildFault(
                        f"Streaming body produced {written} bytes but "
                        f"Content-Length is {explicit_length}",
                        url=request.url,
                    )
            else:
                async for piece in ChunkedEncoder(body):
                    conn.writer.write(piece)
                    await asyncio.wait_for(conn.writer.drain(), timeout=write_timeout)
        except RequestBuildFault:
            raise
        except asyncio.TimeoutError as e:
            raise ReadTimeoutFault(
                f"Write timed out after {write_timeout:.2f}s streaming request body",
                timeout=write_timeout,
                url=request.url,
            ) from e
        except (ConnectionError, OSError) as e:
            raise ConnectionFault(
                f"Connection error streaming request body: {e}",
                url=request.url,
                host=conn.host,
                port=conn.port,
                cause=str(e),
            ) from e

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        if self._closed:
            raise ConnectionClosedFault("Transport is closed")

        parsed = urlparse(request.url)
        use_ssl = parsed.scheme == "https"
        host = parsed.hostname or ""
        port = parsed.port or (DEFAULT_PORT_HTTPS if use_ssl else DEFAULT_PORT_HTTP)

        timeout_config = request.timeout or self._config.timeout
        total_timeout = timeout_config.total
        connect_timeout = timeout_config.connect
        read_timeout = timeout_config.read or timeout_config.total
        pool_timeout = timeout_config.pool

        start_time = time.monotonic()
        # The total deadline covers connect + write + head + the entire
        # body read (D-6): every stage below is bounded by the time left,
        # and the body reader keeps enforcing it per chunk.
        deadline = (start_time + total_timeout) if total_timeout and total_timeout > 0 else None

        def _bounded(value: float | None) -> float | None:
            """Min of a stage timeout and the remaining total deadline."""
            if deadline is None:
                return value
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return 0.0
            if value is None:
                return remaining
            return min(value, remaining)

        conn: ConnectionInfo | None = None
        keep_connection = True
        response_created = False

        # Per-request proxy selection: the proxy depends on the target's
        # scheme and host (no_proxy can exempt either).
        proxy_url = self._select_proxy(parsed.scheme, host)
        proxy_auth: str | None = None
        if proxy_url is not None:
            proxy_parsed = urlparse(proxy_url)
            proxy_auth = _proxy_authorization(proxy_parsed)
            proxy_host = proxy_parsed.hostname or ""
            proxy_port = proxy_parsed.port or (
                DEFAULT_PORT_HTTPS if proxy_parsed.scheme == "https" else DEFAULT_PORT_HTTP
            )
            # Pool identity is (target, proxy): the endpoint is shared
            # with the proxy, the tunnel is not.
            pool_key = f"{self._pool._make_key(host, port, use_ssl)}|via {proxy_url}"
            acquire_host, acquire_port = proxy_host, proxy_port
        else:
            pool_key = None
            acquire_host, acquire_port = host, port

        try:
            effective_connect = _bounded(connect_timeout)
            if effective_connect is not None and effective_connect <= 0:
                raise RequestTimeoutFault(
                    f"Request timed out after {total_timeout:.2f}s",
                    timeout=total_timeout,
                    url=request.url,
                )

            if proxy_url is not None:

                def open_via_proxy() -> ConnectionInfo:
                    return self._connect_via_proxy(
                        host, port, proxy_url, use_ssl, effective_connect, pool_key
                    )

                conn = await self._pool.acquire(
                    acquire_host,
                    acquire_port,
                    use_ssl,
                    timeout=_bounded(pool_timeout),
                    connect=open_via_proxy,
                    key=pool_key,
                )
            else:
                conn = await self._pool.acquire(
                    acquire_host,
                    acquire_port,
                    use_ssl,
                    timeout=_bounded(pool_timeout),
                    connect=lambda: self._connect(host, port, use_ssl, effective_connect),
                )

            request_bytes = self._build_request_bytes(
                request,
                absolute_form=proxy_url is not None and not use_ssl,
                proxy_authorization=proxy_auth,
            )
            conn.writer.write(request_bytes)
            write_timeout = _bounded(timeout_config.write or 30.0)
            try:
                await asyncio.wait_for(conn.writer.drain(), timeout=write_timeout or 30.0)
            except asyncio.TimeoutError as e:
                if deadline is not None and deadline - time.monotonic() <= 0:
                    raise RequestTimeoutFault(
                        f"Request timed out after {total_timeout:.2f}s",
                        timeout=total_timeout,
                        url=request.url,
                    ) from e
                raise

            # Streaming request bodies are written before the response
            # head is read; a failure mid-body closes the connection,
            # never pools it (F-HTTP-08: the stream must not be
            # silently dropped).
            if request.is_streaming():
                await self._write_streaming_body(conn, request, write_timeout or 30.0)

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RequestTimeoutFault(
                        f"Request timed out after {total_timeout:.2f}s",
                        timeout=total_timeout,
                        url=request.url,
                    )
                try:
                    http_version, status_code, reason, raw_headers = await asyncio.wait_for(
                        self._read_response_head(conn.reader, read_timeout),
                        timeout=remaining,
                    )
                except asyncio.TimeoutError as e:
                    raise RequestTimeoutFault(
                        f"Request timed out after {total_timeout:.2f}s",
                        timeout=total_timeout,
                        url=request.url,
                    ) from e
            else:
                http_version, status_code, reason, raw_headers = await self._read_response_head(
                    conn.reader, read_timeout
                )

            elapsed = time.monotonic() - start_time

            # Header field names are case-insensitive; the pool decision must
            # not depend on the server's casing.
            headers_lower = {name.lower(): value for name, value in raw_headers}
            connection_header = headers_lower.get("connection", "").lower()
            if connection_header == "close" or http_version == "1.0":
                keep_connection = False

            framing, content_length = self._body_framing(request, status_code, raw_headers, headers_lower)
            extensions: dict[str, Any] = {}
            body_reader = _BodyReader(
                conn.reader,
                framing,
                content_length=content_length,
                content_encoding=headers_lower.get("content-encoding", "").lower(),
                read_timeout=read_timeout,
                deadline=deadline,
                max_size=self._config.max_response_size,
                extensions=extensions,
                url=request.url,
            )

            async def body_stream() -> AsyncIterator[bytes]:
                # Ownership of ``conn`` transfers from the transport to this
                # response: the pool must never hold a connection whose body
                # has not been read, or a later request can be served the
                # leftover bytes -- and closing the client recycles the
                # connection under an in-flight reader. The connection goes
                # back to the pool (or is closed) exactly once, when the
                # body is fully consumed or the stream is closed.
                try:
                    async for chunk in body_reader:
                        yield chunk
                finally:
                    if body_reader.completed_cleanly and keep_connection and conn.is_alive():
                        try:
                            await self._pool.put_connection(conn)
                        except (asyncio.CancelledError, Exception):
                            # A second cancellation during cleanup must not
                            # interrupt the release: fall back to a sync
                            # close so the socket never leaks.
                            conn.writer.close()
                            self._pool.discard_connection(conn)
                    else:
                        # Abort path: sync close only -- a cancelled body
                        # read can be re-cancelled while awaiting close.
                        conn.writer.close()
                        self._pool.discard_connection(conn)

            response_created = True
            return create_response(
                status_code=status_code,
                headers=raw_headers,
                stream=body_stream(),
                url=request.url,
                http_version=http_version,
                elapsed=elapsed,
                request_url=request.url,
                extensions=extensions,
            )

        except (
            ConnectionFault,
            ConnectionPoolExhaustedFault,
            TLSFault,
            ConnectTimeoutFault,
            ReadTimeoutFault,
            RequestTimeoutFault,
            RequestBuildFault,
        ):
            keep_connection = False
            raise

        except asyncio.TimeoutError as e:
            keep_connection = False
            elapsed = time.monotonic() - start_time
            if elapsed < (connect_timeout or 10.0):
                raise ConnectTimeoutFault(
                    f"Connection timed out after {elapsed:.2f}s",
                    timeout=connect_timeout or 0,
                    url=request.url,
                ) from e
            raise ReadTimeoutFault(
                f"Read timed out after {elapsed:.2f}s",
                timeout=read_timeout or 0,
                url=request.url,
            ) from e

        except ssl.SSLError as e:
            keep_connection = False
            raise TLSFault(f"SSL error: {e}", url=request.url, reason=str(e)) from e

        except OSError as e:
            keep_connection = False
            raise ConnectionFault(
                f"Connection error: {e}",
                url=request.url,
                host=host,
                port=port,
                cause=str(e),
            ) from e

        except Exception as e:
            keep_connection = False
            raise TransportFault(f"Transport error: {e}", url=request.url, cause=str(e)) from e

        finally:
            # Release the connection here only when no response took
            # ownership of it (an error was raised before the body stream
            # was created). A created response releases it itself once its
            # body has been consumed.
            if conn and not response_created:
                if keep_connection and conn.is_alive():
                    try:
                        await self._pool.put_connection(conn)
                    except (asyncio.CancelledError, Exception):
                        conn.writer.close()
                        self._pool.discard_connection(conn)
                else:
                    # Sync close only: this path can run while the task is
                    # being cancelled, and a second cancellation must not
                    # interrupt the cleanup.
                    conn.writer.close()
                    self._pool.discard_connection(conn)

    async def close(self) -> None:
        self._closed = True
        await self._pool.close_all()


class MockTransport(HTTPTransport):
    """Mock transport for tests. Returns predefined responses."""

    __slots__ = ("_responses", "_requests", "_default_response")

    def __init__(self, default_response: HTTPClientResponse | None = None):
        self._responses: dict[str, HTTPClientResponse] = {}
        self._requests: list[HTTPClientRequest] = []
        self._default_response = default_response or create_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=b"{}",
        )

    def add_response(self, method: str, url: str, response: HTTPClientResponse) -> None:
        key = f"{method.upper()}:{url}"
        self._responses[key] = response

    def add_json_response(
        self,
        method: str,
        url: str,
        data: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        import json

        body = json.dumps(data).encode("utf-8")
        response = create_response(
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body=body,
            url=url,
        )
        self.add_response(method, url, response)

    @property
    def requests(self) -> list[HTTPClientRequest]:
        return self._requests

    def clear(self) -> None:
        self._requests.clear()

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        self._requests.append(request)

        key = f"{request.method.value}:{request.url}"
        if key in self._responses:
            return self._responses[key]

        # pattern matching with wildcards
        for pattern, response in self._responses.items():
            method, url = pattern.split(":", 1)
            if method == request.method.value and "*" in url:
                import fnmatch

                if fnmatch.fnmatch(request.url, url):
                    return response

        return self._default_response

    async def close(self) -> None:
        pass


def create_transport(config: HTTPClientConfig | None = None) -> HTTPTransport:
    """Create native HTTP transport."""
    return NativeTransport(config)
