"""
AquilaHTTP — Transport Layer.

Native async HTTP transport using Python's asyncio and ssl modules.
No external dependencies required.
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import logging
import re
import ssl
import time
import zlib
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from .config import HTTPClientConfig, TimeoutConfig
from .faults import (
    CertificateVerifyFault,
    ConnectionClosedFault,
    ConnectionFault,
    ConnectTimeoutFault,
    InvalidResponseFault,
    ReadTimeoutFault,
    TLSFault,
    TransportFault,
)
from .request import HTTPClientRequest
from .response import HTTPClientResponse, create_response

logger = logging.getLogger("aquilia.http.transport")


# HTTP/1.1 constants
CRLF = b"\r\n"
HTTP_VERSION = b"HTTP/1.1"
DEFAULT_PORT_HTTP = 80
DEFAULT_PORT_HTTPS = 443
MAX_LINE_LENGTH = 65536
MAX_HEADERS = 100
CHUNK_SIZE = 65536


@dataclass
class RawResponse:
    """Raw HTTP response data."""

    http_version: str
    status_code: int
    reason: str
    headers: dict[str, str]
    body: bytes = b""
    stream: AsyncIterator[bytes] | None = None


@dataclass
class ConnectionInfo:
    """Information about a connection."""

    host: str
    port: int
    ssl: bool
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)

    @property
    def age(self) -> float:
        return time.monotonic() - self.created_at

    def is_alive(self) -> bool:
        """Check if connection is still alive."""
        return not self.writer.is_closing()

    async def close(self) -> None:
        """Close the connection."""
        if not self.writer.is_closing():
            self.writer.close()
            try:
                await asyncio.wait_for(self.writer.wait_closed(), timeout=1.0)
            except (asyncio.TimeoutError, Exception):
                pass


class ConnectionPool:
    """
    Simple connection pool for HTTP keep-alive.

    Manages reusable TCP connections per host.
    """

    __slots__ = (
        "_connections",
        "_max_connections",
        "_max_per_host",
        "_keepalive_expiry",
        "_lock",
    )

    def __init__(
        self,
        max_connections: int = 100,
        max_per_host: int = 10,
        keepalive_expiry: float = 60.0,
    ):
        self._connections: dict[str, list[ConnectionInfo]] = {}
        self._max_connections = max_connections
        self._max_per_host = max_per_host
        self._keepalive_expiry = keepalive_expiry
        self._lock = asyncio.Lock()

    def _make_key(self, host: str, port: int, ssl: bool) -> str:
        return f"{'https' if ssl else 'http'}://{host}:{port}"

    async def get_connection(
        self,
        host: str,
        port: int,
        use_ssl: bool,
    ) -> ConnectionInfo | None:
        """Get an existing connection from the pool."""
        key = self._make_key(host, port, use_ssl)

        async with self._lock:
            connections = self._connections.get(key, [])

            # Find a live connection
            while connections:
                conn = connections.pop(0)

                # Check if expired
                if conn.age > self._keepalive_expiry:
                    await conn.close()
                    continue

                # Check if still alive
                if conn.is_alive():
                    conn.last_used = time.monotonic()
                    return conn
                else:
                    await conn.close()

            return None

    async def put_connection(self, conn: ConnectionInfo) -> bool:
        """Return a connection to the pool."""
        key = self._make_key(conn.host, conn.port, conn.ssl)

        async with self._lock:
            if key not in self._connections:
                self._connections[key] = []

            connections = self._connections[key]

            # Check limits
            if len(connections) >= self._max_per_host:
                await conn.close()
                return False

            # Check total connections
            total = sum(len(c) for c in self._connections.values())
            if total >= self._max_connections:
                await conn.close()
                return False

            connections.append(conn)
            return True

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for connections in self._connections.values():
                for conn in connections:
                    await conn.close()
            self._connections.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired connections."""
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


class HTTPTransport(ABC):
    """
    Abstract HTTP transport.

    Defines the interface for sending HTTP requests.
    """

    @abstractmethod
    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """
        Send an HTTP request.

        Args:
            request: The request to send.

        Returns:
            The response.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the transport and release resources."""
        ...

    async def __aenter__(self) -> HTTPTransport:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


class NativeTransport(HTTPTransport):
    """
    Native async HTTP/1.1 transport.

    Uses Python's asyncio for networking with no external dependencies.
    Supports:
    - HTTP/1.1 with keep-alive
    - TLS/SSL
    - Chunked transfer encoding
    - Gzip/deflate decompression
    - Connection pooling
    - Timeouts
    """

    __slots__ = ("_config", "_pool", "_closed")

    def __init__(self, config: HTTPClientConfig | None = None):
        self._config = config or HTTPClientConfig()
        self._pool = ConnectionPool(
            max_connections=self._config.pool.max_connections,
            max_per_host=self._config.pool.max_connections_per_host,
            keepalive_expiry=self._config.pool.keepalive_expiry,
        )
        self._closed = False

    def _create_ssl_context(self) -> ssl.SSLContext | None:
        """Create SSL context from config."""
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

        if tls.cert_file:
            ctx.load_cert_chain(
                certfile=tls.cert_file,
                keyfile=tls.key_file,
            )

        if tls.minimum_version:
            version_map = {
                "TLSv1.2": ssl.TLSVersion.TLSv1_2,
                "TLSv1.3": ssl.TLSVersion.TLSv1_3,
            }
            if tls.minimum_version in version_map:
                ctx.minimum_version = version_map[tls.minimum_version]

        return ctx

    async def _connect(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: float | None = None,
    ) -> ConnectionInfo:
        """Establish a new connection."""
        connect_timeout = timeout or self._config.timeout.connect or 10.0

        ssl_context: ssl.SSLContext | None = None
        if use_ssl:
            ssl_context = self._create_ssl_context()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host=host,
                    port=port,
                    ssl=ssl_context,
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

        except asyncio.TimeoutError as e:
            raise ConnectTimeoutFault(
                f"Connection to {host}:{port} timed out after {connect_timeout:.2f}s",
                timeout=connect_timeout,
                url=f"{'https' if use_ssl else 'http'}://{host}:{port}",
            ) from e

        except ssl.SSLCertVerificationError as e:
            raise CertificateVerifyFault(
                f"Certificate verification failed for {host}: {e}",
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
            raise ConnectionFault(
                f"Connection failed to {host}:{port}: {e}",
                host=host,
                port=port,
                cause=str(e),
            ) from e

    async def _get_connection(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: float | None = None,
    ) -> ConnectionInfo:
        """Get a connection from pool or create new one."""
        # Try to get from pool first
        conn = await self._pool.get_connection(host, port, use_ssl)
        if conn:
            return conn

        # Create new connection
        return await self._connect(host, port, use_ssl, timeout)

    def _build_request_bytes(self, request: HTTPClientRequest) -> bytes:
        """Build HTTP/1.1 request bytes."""
        parsed = urlparse(request.url)

        # Build request line
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        lines = [f"{request.method.value} {path} HTTP/1.1"]

        # Build headers
        headers = dict(request.headers)

        # Ensure Host header
        if "Host" not in headers:
            host = parsed.netloc
            if parsed.port and parsed.port not in (80, 443):
                headers["Host"] = f"{parsed.hostname}:{parsed.port}"
            else:
                headers["Host"] = parsed.hostname or host

        # Add default headers
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._config.user_agent

        if "Accept" not in headers:
            headers["Accept"] = "*/*"

        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip, deflate"

        if "Connection" not in headers:
            headers["Connection"] = "keep-alive"

        # Content-Length for body
        if request.body is not None and isinstance(request.body, bytes):
            headers["Content-Length"] = str(len(request.body))

        # Basic auth
        if request.auth:
            credentials = f"{request.auth[0]}:{request.auth[1]}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        # Add headers to request
        for name, value in headers.items():
            lines.append(f"{name}: {value}")

        # End of headers
        lines.append("")
        lines.append("")

        request_bytes = "\r\n".join(lines).encode("latin-1")

        # Add body
        if request.body is not None and isinstance(request.body, bytes):
            request_bytes += request.body

        return request_bytes

    async def _read_line(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> bytes:
        """Read a line from the stream with timeout."""
        read_timeout = timeout or self._config.timeout.read or self._config.timeout.total or 30.0

        try:
            line = await asyncio.wait_for(
                reader.readline(),
                timeout=read_timeout,
            )

            if len(line) > MAX_LINE_LENGTH:
                raise InvalidResponseFault(
                    f"Response line too long: {len(line)} bytes",
                )

            return line

        except asyncio.TimeoutError as e:
            raise ReadTimeoutFault(
                f"Read timed out after {read_timeout:.2f}s",
                timeout=read_timeout,
            ) from e

    async def _read_response_head(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> tuple[str, int, str, dict[str, str]]:
        """Read and parse HTTP response status line and headers."""
        # Read status line
        status_line = await self._read_line(reader, timeout)
        if not status_line:
            raise ConnectionClosedFault("Connection closed while reading response")

        status_line = status_line.strip().decode("latin-1")

        # Parse status line: HTTP/1.1 200 OK
        match = re.match(r"HTTP/(\d\.\d)\s+(\d{3})\s*(.*)", status_line)
        if not match:
            raise InvalidResponseFault(f"Invalid status line: {status_line}")

        http_version = match.group(1)
        status_code = int(match.group(2))
        reason = match.group(3)

        # Read headers
        headers: dict[str, str] = {}
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
                raise InvalidResponseFault(f"Invalid header line: {line_str}")

            name, value = line_str.split(":", 1)
            headers[name.strip()] = value.strip()

        return http_version, status_code, reason, headers

    async def _read_body_content_length(
        self,
        reader: asyncio.StreamReader,
        length: int,
        timeout: float | None = None,
    ) -> bytes:
        """Read exact number of bytes from stream."""
        read_timeout = timeout or self._config.timeout.read or self._config.timeout.total or 30.0

        try:
            data = await asyncio.wait_for(
                reader.readexactly(length),
                timeout=read_timeout,
            )
            return data
        except asyncio.IncompleteReadError as e:
            return e.partial
        except asyncio.TimeoutError as e:
            raise ReadTimeoutFault(
                f"Read timed out after {read_timeout:.2f}s",
                timeout=read_timeout,
            ) from e

    async def _read_body_chunked(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> bytes:
        """Read chunked transfer encoding body."""
        body_parts: list[bytes] = []

        while True:
            # Read chunk size line
            size_line = await self._read_line(reader, timeout)
            size_str = size_line.strip().decode("ascii")

            # Handle chunk extensions (rare)
            if ";" in size_str:
                size_str = size_str.split(";")[0]

            try:
                chunk_size = int(size_str, 16)
            except ValueError:
                raise InvalidResponseFault(f"Invalid chunk size: {size_str}")

            if chunk_size == 0:
                # Final chunk - read trailing CRLF
                await self._read_line(reader, timeout)
                break

            # Read chunk data
            chunk_data = await self._read_body_content_length(reader, chunk_size, timeout)
            body_parts.append(chunk_data)

            # Read trailing CRLF after chunk
            await self._read_line(reader, timeout)

        return b"".join(body_parts)

    def _decompress_body(self, body: bytes, encoding: str) -> bytes:
        """Decompress response body if needed."""
        encoding = encoding.lower()

        if encoding == "gzip":
            try:
                return gzip.decompress(body)
            except Exception as e:
                logger.warning(f"Failed to decompress gzip: {e}")
                return body

        elif encoding == "deflate":
            try:
                # Try raw deflate first
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                try:
                    # Try zlib format
                    return zlib.decompress(body)
                except Exception as e:
                    logger.warning(f"Failed to decompress deflate: {e}")
                    return body

        return body

    async def _create_body_stream(
        self,
        reader: asyncio.StreamReader,
        headers: dict[str, str],
        timeout: float | None = None,
    ) -> AsyncIterator[bytes]:
        """Create async iterator for streaming response body."""
        transfer_encoding = headers.get("Transfer-Encoding", "").lower()
        content_length = headers.get("Content-Length")
        content_encoding = headers.get("Content-Encoding", "")

        if transfer_encoding == "chunked":
            # Read chunked body
            body = await self._read_body_chunked(reader, timeout)

            # Decompress if needed
            if content_encoding:
                body = self._decompress_body(body, content_encoding)

            yield body

        elif content_length:
            length = int(content_length)
            if length > 0:
                body = await self._read_body_content_length(reader, length, timeout)

                # Decompress if needed
                if content_encoding:
                    body = self._decompress_body(body, content_encoding)

                yield body

        else:
            # Read until connection closes (HTTP/1.0 style)
            chunks: list[bytes] = []
            try:
                while True:
                    chunk = await asyncio.wait_for(
                        reader.read(CHUNK_SIZE),
                        timeout=timeout or 30.0,
                    )
                    if not chunk:
                        break
                    chunks.append(chunk)
            except asyncio.TimeoutError:
                pass

            body = b"".join(chunks)
            if content_encoding:
                body = self._decompress_body(body, content_encoding)

            yield body

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """Send an HTTP request using native async sockets."""
        if self._closed:
            raise ConnectionClosedFault("Transport is closed")

        parsed = urlparse(request.url)
        use_ssl = parsed.scheme == "https"
        host = parsed.hostname or ""
        port = parsed.port or (DEFAULT_PORT_HTTPS if use_ssl else DEFAULT_PORT_HTTP)

        # Determine timeouts
        timeout_config = request.timeout or self._config.timeout
        connect_timeout = timeout_config.connect
        read_timeout = timeout_config.read or timeout_config.total

        start_time = time.monotonic()
        conn: ConnectionInfo | None = None
        keep_connection = True

        try:
            # Get or create connection
            conn = await self._get_connection(host, port, use_ssl, connect_timeout)

            # Build and send request
            request_bytes = self._build_request_bytes(request)

            conn.writer.write(request_bytes)
            await asyncio.wait_for(
                conn.writer.drain(),
                timeout=timeout_config.write or 30.0,
            )

            # Read response head
            http_version, status_code, reason, headers = await self._read_response_head(
                conn.reader,
                read_timeout,
            )

            elapsed = time.monotonic() - start_time

            # Check for Connection: close
            connection_header = headers.get("Connection", "").lower()
            if connection_header == "close" or http_version == "1.0":
                keep_connection = False

            # Create response with body stream
            async def body_stream() -> AsyncIterator[bytes]:
                async for chunk in self._create_body_stream(conn.reader, headers, read_timeout):
                    yield chunk

            response = create_response(
                status_code=status_code,
                headers=headers,
                stream=body_stream(),
                url=request.url,
                http_version=http_version,
                elapsed=elapsed,
                request_url=request.url,
            )

            return response

        except (ConnectionFault, TLSFault, ConnectTimeoutFault, ReadTimeoutFault):
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
            raise TLSFault(
                f"SSL error: {e}",
                url=request.url,
                reason=str(e),
            ) from e

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
            raise TransportFault(
                f"Transport error: {e}",
                url=request.url,
                cause=str(e),
            ) from e

        finally:
            if conn:
                if keep_connection and conn.is_alive():
                    # Return to pool for reuse
                    await self._pool.put_connection(conn)
                else:
                    await conn.close()

    async def close(self) -> None:
        """Close the transport and all connections."""
        self._closed = True
        await self._pool.close_all()
        logger.debug("Native transport closed")


class MockTransport(HTTPTransport):
    """
    Mock transport for testing.

    Returns predefined responses for requests.
    """

    __slots__ = ("_responses", "_requests", "_default_response")

    def __init__(
        self,
        default_response: HTTPClientResponse | None = None,
    ):
        self._responses: dict[str, HTTPClientResponse] = {}
        self._requests: list[HTTPClientRequest] = []
        self._default_response = default_response or create_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=b"{}",
        )

    def add_response(
        self,
        method: str,
        url: str,
        response: HTTPClientResponse,
    ) -> None:
        """Add a predefined response for a request."""
        key = f"{method.upper()}:{url}"
        self._responses[key] = response

    def add_json_response(
        self,
        method: str,
        url: str,
        data: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        """Add a JSON response."""
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
        """Get all recorded requests."""
        return self._requests

    def clear(self) -> None:
        """Clear recorded requests."""
        self._requests.clear()

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """Return predefined response or default."""
        self._requests.append(request)

        key = f"{request.method.value}:{request.url}"
        if key in self._responses:
            return self._responses[key]

        # Try pattern matching
        for pattern, response in self._responses.items():
            method, url = pattern.split(":", 1)
            if method == request.method.value:
                if "*" in url:
                    import fnmatch

                    if fnmatch.fnmatch(request.url, url):
                        return response

        return self._default_response

    async def close(self) -> None:
        """No-op for mock transport."""
        pass


# Keep AIOHTTPTransport for backward compatibility, but make it optional
AIOHTTPTransport: type | None = None

try:
    import aiohttp
    from aiohttp import (
        ClientConnectorCertificateError,
        ClientConnectorError,
        ClientConnectorSSLError,
        ClientSession,
        ClientTimeout,
        TCPConnector,
    )

    AIOHTTP_AVAILABLE = True

    class _AIOHTTPTransport(HTTPTransport):
        """
        aiohttp-based HTTP transport (optional).

        Uses aiohttp for the underlying HTTP implementation.
        Only available if aiohttp is installed.
        """

        __slots__ = ("_config", "_session", "_connector", "_closed")

        def __init__(self, config: HTTPClientConfig | None = None):
            self._config = config or HTTPClientConfig()
            self._session: ClientSession | None = None
            self._connector: TCPConnector | None = None
            self._closed = False

        def _create_ssl_context(self) -> ssl.SSLContext | bool:
            """Create SSL context from config."""
            tls = self._config.tls

            if not tls.verify:
                return False

            if tls.ssl_context:
                return tls.ssl_context

            ctx = ssl.create_default_context()

            if tls.ca_bundle:
                ctx.load_verify_locations(tls.ca_bundle)

            if tls.cert_file:
                ctx.load_cert_chain(
                    certfile=tls.cert_file,
                    keyfile=tls.key_file,
                )

            if tls.minimum_version:
                version_map = {
                    "TLSv1.2": ssl.TLSVersion.TLSv1_2,
                    "TLSv1.3": ssl.TLSVersion.TLSv1_3,
                }
                if tls.minimum_version in version_map:
                    ctx.minimum_version = version_map[tls.minimum_version]

            return ctx

        def _create_timeout(
            self,
            override: TimeoutConfig | None = None,
        ) -> ClientTimeout:
            """Create aiohttp timeout from config."""
            cfg = override or self._config.timeout

            return ClientTimeout(
                total=cfg.total,
                connect=cfg.connect,
                sock_read=cfg.read,
            )

        async def _get_session(self) -> ClientSession:
            """Get or create the aiohttp session."""
            if self._session is None or self._session.closed:
                # Create connector
                ssl_context = self._create_ssl_context()

                self._connector = TCPConnector(
                    limit=self._config.pool.max_connections,
                    limit_per_host=self._config.pool.max_connections_per_host,
                    keepalive_timeout=self._config.pool.keepalive_expiry,
                    ssl=ssl_context,
                    enable_cleanup_closed=True,
                )

                # Default headers
                headers = dict(self._config.default_headers)
                if "User-Agent" not in headers:
                    headers["User-Agent"] = self._config.user_agent

                # Create session
                self._session = ClientSession(
                    connector=self._connector,
                    timeout=self._create_timeout(),
                    headers=headers,
                    raise_for_status=False,
                )

            return self._session

        async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
            """Send an HTTP request using aiohttp."""
            if self._closed:
                raise ConnectionClosedFault("Transport is closed")

            session = await self._get_session()
            start_time = time.monotonic()

            # Prepare request kwargs
            kwargs: dict[str, Any] = {
                "method": request.method.value,
                "url": request.url,
                "headers": request.headers,
                "allow_redirects": False,
            }

            # Add body
            if request.body is not None:
                if isinstance(request.body, bytes):
                    kwargs["data"] = request.body
                else:
                    kwargs["data"] = request.body

            # Add timeout override
            if request.timeout:
                kwargs["timeout"] = self._create_timeout(request.timeout)

            # Add basic auth
            if request.auth:
                kwargs["auth"] = aiohttp.BasicAuth(
                    request.auth[0],
                    request.auth[1],
                )

            try:
                async with session.request(**kwargs) as aio_response:
                    elapsed = time.monotonic() - start_time

                    headers = dict(aio_response.headers)

                    async def body_stream() -> AsyncIterator[bytes]:
                        async for chunk in aio_response.content.iter_any():
                            yield chunk

                    return create_response(
                        status_code=aio_response.status,
                        headers=headers,
                        stream=body_stream(),
                        url=str(aio_response.url),
                        http_version=f"{aio_response.version.major}.{aio_response.version.minor}",
                        elapsed=elapsed,
                        request_url=request.url,
                    )

            except asyncio.TimeoutError as e:
                elapsed = time.monotonic() - start_time
                if elapsed < (self._config.timeout.connect or 10.0):
                    raise ConnectTimeoutFault(
                        f"Connection timed out after {elapsed:.2f}s",
                        timeout=self._config.timeout.connect or 0,
                        url=request.url,
                    ) from e
                raise ReadTimeoutFault(
                    f"Read timed out after {elapsed:.2f}s",
                    timeout=self._config.timeout.total or 0,
                    url=request.url,
                ) from e

            except ClientConnectorCertificateError as e:
                raise CertificateVerifyFault(
                    f"Certificate verification failed: {e}",
                    url=request.url,
                    reason=str(e),
                ) from e

            except ClientConnectorSSLError as e:
                raise TLSFault(
                    f"SSL error: {e}",
                    url=request.url,
                    reason=str(e),
                ) from e

            except ClientConnectorError as e:
                parsed = urlparse(request.url)
                raise ConnectionFault(
                    f"Connection failed: {e}",
                    url=request.url,
                    host=parsed.hostname or "",
                    port=parsed.port,
                    cause=str(e),
                ) from e

            except aiohttp.ClientError as e:
                raise TransportFault(
                    f"Transport error: {e}",
                    url=request.url,
                    cause=str(e),
                ) from e

        async def close(self) -> None:
            """Close the transport."""
            self._closed = True

            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

            if self._connector and not self._connector.closed:
                await self._connector.close()
                self._connector = None

            logger.debug("AIOHTTPTransport closed")

    AIOHTTPTransport = _AIOHTTPTransport

except ImportError:
    AIOHTTP_AVAILABLE = False


def create_transport(
    config: HTTPClientConfig | None = None,
    prefer_aiohttp: bool = False,
) -> HTTPTransport:
    """
    Create the appropriate transport.

    By default, uses the native transport. Set prefer_aiohttp=True
    to use aiohttp if available.

    Args:
        config: HTTP client configuration.
        prefer_aiohttp: Prefer aiohttp transport if available.

    Returns:
        HTTP transport instance.
    """
    if prefer_aiohttp and AIOHTTP_AVAILABLE and AIOHTTPTransport is not None:
        return AIOHTTPTransport(config)

    return NativeTransport(config)
