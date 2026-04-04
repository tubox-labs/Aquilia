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
from urllib.parse import urlparse

from .config import HTTPClientConfig
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

# limits
CRLF = b"\r\n"
HTTP_VERSION = b"HTTP/1.1"
DEFAULT_PORT_HTTP = 80
DEFAULT_PORT_HTTPS = 443
MAX_LINE_LENGTH = 65536
MAX_HEADERS = 100
CHUNK_SIZE = 65536


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
    """Keep-alive connection pool. Reuses TCP connections per host."""

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
        """Grab a live connection if one exists."""
        key = self._make_key(host, port, use_ssl)

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

    async def put_connection(self, conn: ConnectionInfo) -> bool:
        """Return connection to pool if we have room."""
        key = self._make_key(conn.host, conn.port, conn.ssl)

        async with self._lock:
            if key not in self._connections:
                self._connections[key] = []

            connections = self._connections[key]

            if len(connections) >= self._max_per_host:
                await conn.close()
                return False

            total = sum(len(c) for c in self._connections.values())
            if total >= self._max_connections:
                await conn.close()
                return False

            connections.append(conn)
            return True

    async def close_all(self) -> None:
        async with self._lock:
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

    def _build_request_bytes(self, request: HTTPClientRequest) -> bytes:
        parsed = urlparse(request.url)

        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        lines = [f"{request.method.value} {path} HTTP/1.1"]

        headers = dict(request.headers)

        # Host header
        if "Host" not in headers:
            if parsed.port and parsed.port not in (80, 443):
                headers["Host"] = f"{parsed.hostname}:{parsed.port}"
            else:
                headers["Host"] = parsed.hostname or parsed.netloc

        # defaults
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._config.user_agent
        if "Accept" not in headers:
            headers["Accept"] = "*/*"
        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip, deflate"
        if "Connection" not in headers:
            headers["Connection"] = "keep-alive"

        # body length
        if request.body is not None and isinstance(request.body, bytes):
            headers["Content-Length"] = str(len(request.body))

        # basic auth
        if request.auth:
            creds = f"{request.auth[0]}:{request.auth[1]}"
            encoded = base64.b64encode(creds.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        for name, value in headers.items():
            lines.append(f"{name}: {value}")

        lines.append("")
        lines.append("")

        request_bytes = "\r\n".join(lines).encode("latin-1")

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

    async def _read_response_head(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> tuple[str, int, str, dict[str, str]]:
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
                raise InvalidResponseFault(f"Invalid header: {line_str}")

            name, value = line_str.split(":", 1)
            headers[name.strip()] = value.strip()

        return http_version, status_code, reason, headers

    async def _read_body_content_length(
        self,
        reader: asyncio.StreamReader,
        length: int,
        timeout: float | None = None,
    ) -> bytes:
        read_timeout = timeout or self._config.timeout.read or self._config.timeout.total or 30.0

        try:
            return await asyncio.wait_for(reader.readexactly(length), timeout=read_timeout)
        except asyncio.IncompleteReadError as e:
            return e.partial
        except asyncio.TimeoutError as e:
            raise ReadTimeoutFault(f"Read timed out after {read_timeout:.2f}s", timeout=read_timeout) from e

    async def _read_body_chunked(
        self,
        reader: asyncio.StreamReader,
        timeout: float | None = None,
    ) -> bytes:
        body_parts: list[bytes] = []

        while True:
            size_line = await self._read_line(reader, timeout)
            size_str = size_line.strip().decode("ascii")

            # chunk extensions (rare but possible)
            if ";" in size_str:
                size_str = size_str.split(";")[0]

            try:
                chunk_size = int(size_str, 16)
            except ValueError:
                raise InvalidResponseFault(f"Invalid chunk size: {size_str}")

            if chunk_size == 0:
                await self._read_line(reader, timeout)  # trailing CRLF
                break

            chunk_data = await self._read_body_content_length(reader, chunk_size, timeout)
            body_parts.append(chunk_data)
            await self._read_line(reader, timeout)  # CRLF after chunk

        return b"".join(body_parts)

    def _decompress_body(self, body: bytes, encoding: str) -> bytes:
        encoding = encoding.lower()

        if encoding == "gzip":
            try:
                return gzip.decompress(body)
            except Exception as e:
                logger.warning(f"gzip decompress failed: {e}")
                return body

        elif encoding == "deflate":
            try:
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                try:
                    return zlib.decompress(body)
                except Exception as e:
                    logger.warning(f"deflate decompress failed: {e}")
                    return body

        return body

    async def _create_body_stream(
        self,
        reader: asyncio.StreamReader,
        headers: dict[str, str],
        timeout: float | None = None,
    ) -> AsyncIterator[bytes]:
        transfer_encoding = headers.get("Transfer-Encoding", "").lower()
        content_length = headers.get("Content-Length")
        content_encoding = headers.get("Content-Encoding", "")

        if transfer_encoding == "chunked":
            body = await self._read_body_chunked(reader, timeout)
            if content_encoding:
                body = self._decompress_body(body, content_encoding)
            yield body

        elif content_length:
            length = int(content_length)
            if length > 0:
                body = await self._read_body_content_length(reader, length, timeout)
                if content_encoding:
                    body = self._decompress_body(body, content_encoding)
                yield body

        else:
            # read until close (HTTP/1.0 style)
            chunks: list[bytes] = []
            try:
                while True:
                    chunk = await asyncio.wait_for(reader.read(CHUNK_SIZE), timeout=timeout or 30.0)
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
        if self._closed:
            raise ConnectionClosedFault("Transport is closed")

        parsed = urlparse(request.url)
        use_ssl = parsed.scheme == "https"
        host = parsed.hostname or ""
        port = parsed.port or (DEFAULT_PORT_HTTPS if use_ssl else DEFAULT_PORT_HTTP)

        timeout_config = request.timeout or self._config.timeout
        connect_timeout = timeout_config.connect
        read_timeout = timeout_config.read or timeout_config.total

        start_time = time.monotonic()
        conn: ConnectionInfo | None = None
        keep_connection = True

        try:
            conn = await self._get_connection(host, port, use_ssl, connect_timeout)

            request_bytes = self._build_request_bytes(request)
            conn.writer.write(request_bytes)
            await asyncio.wait_for(conn.writer.drain(), timeout=timeout_config.write or 30.0)

            http_version, status_code, reason, headers = await self._read_response_head(conn.reader, read_timeout)

            elapsed = time.monotonic() - start_time

            connection_header = headers.get("Connection", "").lower()
            if connection_header == "close" or http_version == "1.0":
                keep_connection = False

            async def body_stream() -> AsyncIterator[bytes]:
                async for chunk in self._create_body_stream(conn.reader, headers, read_timeout):
                    yield chunk

            return create_response(
                status_code=status_code,
                headers=headers,
                stream=body_stream(),
                url=request.url,
                http_version=http_version,
                elapsed=elapsed,
                request_url=request.url,
            )

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
            if conn:
                if keep_connection and conn.is_alive():
                    await self._pool.put_connection(conn)
                else:
                    await conn.close()

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
