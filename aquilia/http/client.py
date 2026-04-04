"""
AquilaHTTP — Async HTTP Client.

Main HTTP client class providing a high-level API for making
HTTP requests with full async support.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from ._transport import HTTPTransport
from .config import HTTPClientConfig, TimeoutConfig
from .cookies import CookieJar
from .interceptors import HTTPInterceptor
from .middleware import HTTPClientMiddleware
from .multipart import MultipartFormData
from .request import HTTPClientRequest, HTTPMethod, RequestBuilder
from .response import HTTPClientResponse
from .session import HTTPSession

logger = logging.getLogger("aquilia.http.client")


class AsyncHTTPClient:
    """
    Async HTTP client.

    High-level client for making HTTP requests with support for:
    - Automatic connection pooling
    - Cookie management
    - Request/response interceptors
    - Middleware
    - Retry logic
    - Timeouts
    - Streaming

    Example:
        ```python
        async with AsyncHTTPClient() as client:
            # Simple GET
            response = await client.get("https://api.example.com/users")
            users = await response.json()

            # POST with JSON
            response = await client.post(
                "https://api.example.com/users",
                json={"name": "John", "email": "john@example.com"},
            )
            new_user = await response.json()

            # With headers and params
            response = await client.get(
                "https://api.example.com/search",
                params={"q": "python"},
                headers={"Accept": "application/json"},
            )

            # Streaming response
            async for chunk in response.iter_bytes():
                process(chunk)
        ```
    """

    __slots__ = ("_session",)

    def __init__(
        self,
        base_url: str | None = None,
        *,
        config: HTTPClientConfig | None = None,
        transport: HTTPTransport | None = None,
        cookies: CookieJar | None = None,
        interceptors: list[HTTPInterceptor] | None = None,
        middleware: list[HTTPClientMiddleware] | None = None,
        timeout: float | TimeoutConfig | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
        raise_for_status: bool = False,
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL prepended to all requests.
            config: Full HTTP client configuration.
            transport: Custom transport implementation.
            cookies: Cookie jar for persistent cookies.
            interceptors: Request/response interceptors.
            middleware: Middleware stack.
            timeout: Default request timeout.
            headers: Default headers for all requests.
            follow_redirects: Whether to follow redirects.
            raise_for_status: Raise exceptions for 4xx/5xx.
        """
        # Build config from parameters if not provided
        if config is None:
            config = HTTPClientConfig(
                base_url=base_url,
                default_headers=headers or {},
                follow_redirects=follow_redirects,
                raise_for_status=raise_for_status,
            )

            if timeout is not None:
                if isinstance(timeout, (int, float)):
                    config = config.with_timeout(total=timeout)
                else:
                    config = HTTPClientConfig(
                        base_url=base_url,
                        timeout=timeout,
                        default_headers=headers or {},
                        follow_redirects=follow_redirects,
                        raise_for_status=raise_for_status,
                    )

        # Create session
        self._session = HTTPSession(
            config=config,
            transport=transport,
            cookies=cookies,
            interceptors=interceptors,
            middleware=middleware,
        )

    @property
    def config(self) -> HTTPClientConfig:
        """Get client configuration."""
        return self._session.config

    @property
    def cookies(self) -> CookieJar:
        """Get cookie jar."""
        return self._session.cookies

    @property
    def base_url(self) -> str | None:
        """Get base URL."""
        return self._session.base_url

    def request(
        self,
        method: str | HTTPMethod,
        url: str,
        **kwargs: Any,
    ) -> RequestBuilder:
        """
        Create a request builder.

        Args:
            method: HTTP method.
            url: Request URL.
            **kwargs: Additional arguments.

        Returns:
            RequestBuilder for fluent configuration.
        """
        return self._session.request(method, url, **kwargs)

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """
        Send a pre-built request.

        Args:
            request: The request to send.

        Returns:
            The response.
        """
        return await self._session.send(request)

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a GET request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | str | bytes | None = None,
        files: MultipartFormData | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a POST request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            json: JSON body (auto-serialized).
            data: Form data or raw body.
            files: Multipart form data with files.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        if files is not None:
            # Handle multipart form data
            body = await files.encode()
            headers = headers or {}
            headers["Content-Type"] = files.content_type
            return await self._session.post(
                url,
                params=params,
                headers=headers,
                data=body,
                timeout=timeout,
                **kwargs,
            )

        return await self._session.post(
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            timeout=timeout,
            **kwargs,
        )

    async def put(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | str | bytes | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a PUT request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            json: JSON body (auto-serialized).
            data: Form data or raw body.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.put(
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            timeout=timeout,
            **kwargs,
        )

    async def patch(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | str | bytes | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a PATCH request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            json: JSON body (auto-serialized).
            data: Form data or raw body.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.patch(
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            timeout=timeout,
            **kwargs,
        )

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a DELETE request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.delete(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    async def head(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send a HEAD request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.head(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    async def options(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """
        Send an OPTIONS request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            timeout: Request timeout.
            **kwargs: Additional arguments.

        Returns:
            The response.
        """
        return await self._session.options(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    async def stream(
        self,
        method: str | HTTPMethod,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | str | bytes | None = None,
        chunk_size: int = 65536,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream a response body.

        Args:
            method: HTTP method.
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            json: JSON body.
            data: Form data or raw body.
            chunk_size: Size of chunks to yield.
            **kwargs: Additional arguments.

        Yields:
            Response body chunks.
        """
        builder = self.request(method, url)

        if params:
            builder.params(params)
        if headers:
            builder.headers(headers)
        if json is not None:
            builder.json(json)
        if data is not None:
            if isinstance(data, bytes):
                builder.body(data)
            elif isinstance(data, str):
                builder.body(data.encode())
            else:
                builder.form(data)

        request = builder.build()
        response = await self.send(request)

        async for chunk in response.iter_bytes(chunk_size):
            yield chunk

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._session.close()
        logger.debug("Client closed")

    async def __aenter__(self) -> AsyncHTTPClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *exc: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        return f"<AsyncHTTPClient base_url={self.base_url!r}>"


# Convenience function for quick one-off requests
async def request(
    method: str | HTTPMethod,
    url: str,
    **kwargs: Any,
) -> HTTPClientResponse:
    """
    Make a one-off HTTP request.

    Creates a temporary client for a single request.

    Args:
        method: HTTP method.
        url: Request URL.
        **kwargs: Arguments passed to the request method.

    Returns:
        The response.

    Example:
        ```python
        response = await request("GET", "https://api.example.com/users")
        users = await response.json()
        ```
    """
    async with AsyncHTTPClient() as client:
        if method.upper() == "GET":
            return await client.get(url, **kwargs)
        elif method.upper() == "POST":
            return await client.post(url, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(url, **kwargs)
        elif method.upper() == "PATCH":
            return await client.patch(url, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(url, **kwargs)
        elif method.upper() == "HEAD":
            return await client.head(url, **kwargs)
        elif method.upper() == "OPTIONS":
            return await client.options(url, **kwargs)
        else:
            builder = client.request(method, url)
            for key, value in kwargs.items():
                if hasattr(builder, key):
                    getattr(builder, key)(value)
            return await client.send(builder.build())


# Convenience functions
async def get(url: str, **kwargs: Any) -> HTTPClientResponse:
    """Make a GET request."""
    return await request("GET", url, **kwargs)


async def post(url: str, **kwargs: Any) -> HTTPClientResponse:
    """Make a POST request."""
    return await request("POST", url, **kwargs)


async def put(url: str, **kwargs: Any) -> HTTPClientResponse:
    """Make a PUT request."""
    return await request("PUT", url, **kwargs)


async def patch(url: str, **kwargs: Any) -> HTTPClientResponse:
    """Make a PATCH request."""
    return await request("PATCH", url, **kwargs)


async def delete(url: str, **kwargs: Any) -> HTTPClientResponse:
    """Make a DELETE request."""
    return await request("DELETE", url, **kwargs)
