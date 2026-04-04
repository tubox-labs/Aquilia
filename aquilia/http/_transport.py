"""
AquilaHTTP — Transport Layer.

Low-level HTTP transport abstraction using aiohttp.
Handles connection management, SSL, and raw request/response.
"""

from __future__ import annotations

import asyncio
import logging
import ssl
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlparse

from .config import HTTPClientConfig, TimeoutConfig
from .faults import (
    CertificateVerifyFault,
    ConnectionClosedFault,
    ConnectionFault,
    ConnectTimeoutFault,
    ReadTimeoutFault,
    TLSFault,
    TransportFault,
)
from .request import HTTPClientRequest
from .response import HTTPClientResponse, create_response

logger = logging.getLogger("aquilia.http.transport")

# Try to import aiohttp
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
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None  # type: ignore


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


class AIOHTTPTransport(HTTPTransport):
    """
    aiohttp-based HTTP transport.

    Uses aiohttp for the underlying HTTP implementation.
    """

    __slots__ = ("_config", "_session", "_connector", "_closed")

    def __init__(self, config: HTTPClientConfig | None = None):
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for AIOHTTPTransport. Install it with: pip install aiohttp")

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
            "allow_redirects": False,  # We handle redirects ourselves
        }

        # Add body
        if request.body is not None:
            if isinstance(request.body, bytes):
                kwargs["data"] = request.body
            else:
                # Streaming body
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

                # Read headers
                headers = dict(aio_response.headers)

                # Create response with stream
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

        logger.debug("Transport closed")


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


def create_transport(config: HTTPClientConfig | None = None) -> HTTPTransport:
    """
    Create the appropriate transport based on available libraries.

    Args:
        config: HTTP client configuration.

    Returns:
        HTTP transport instance.
    """
    if AIOHTTP_AVAILABLE:
        return AIOHTTPTransport(config)

    raise ImportError("No HTTP transport available. Install aiohttp: pip install aiohttp")
