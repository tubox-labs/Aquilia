"""
AquilaHTTP — HTTP Session.

Persistent HTTP session with shared cookies, headers,
and connection reuse.
"""

from __future__ import annotations

import logging
from typing import Any

from ._transport import HTTPTransport, create_transport
from .config import HTTPClientConfig, TimeoutConfig
from .cookies import CookieJar
from .interceptors import HTTPInterceptor
from .middleware import HTTPClientMiddleware
from .request import HTTPClientRequest, HTTPMethod, RequestBuilder
from .response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.session")


class HTTPSession:
    """
    Persistent HTTP session.

    Maintains cookies, default headers, and connection reuse
    across multiple requests.

    Example:
        ```python
        async with HTTPSession(base_url="https://api.example.com") as session:
            response = await session.get("/users")
            users = await response.json()

            response = await session.post("/users", json={"name": "John"})
            new_user = await response.json()
        ```
    """

    __slots__ = (
        "_config",
        "_transport",
        "_cookies",
        "_interceptors",
        "_middleware",
        "_closed",
    )

    def __init__(
        self,
        base_url: str | None = None,
        *,
        config: HTTPClientConfig | None = None,
        transport: HTTPTransport | None = None,
        cookies: CookieJar | None = None,
        interceptors: list[HTTPInterceptor] | None = None,
        middleware: list[HTTPClientMiddleware] | None = None,
    ):
        """
        Initialize HTTP session.

        Args:
            base_url: Base URL for all requests.
            config: HTTP client configuration.
            transport: Custom transport (defaults to aiohttp).
            cookies: Cookie jar for persistent cookies.
            interceptors: Request/response interceptors.
            middleware: Middleware stack.
        """
        # Build config
        if config:
            self._config = config
        else:
            self._config = HTTPClientConfig(base_url=base_url)

        if base_url and self._config.base_url != base_url:
            self._config = self._config.with_base_url(base_url)

        # Initialize components
        self._transport = transport
        self._cookies = cookies or CookieJar()
        self._interceptors = list(interceptors) if interceptors else []
        self._middleware = list(middleware) if middleware else []
        self._closed = False

    @property
    def config(self) -> HTTPClientConfig:
        """Get session configuration."""
        return self._config

    @property
    def cookies(self) -> CookieJar:
        """Get session cookie jar."""
        return self._cookies

    @property
    def base_url(self) -> str | None:
        """Get base URL."""
        return self._config.base_url

    def _get_transport(self) -> HTTPTransport:
        """Get or create transport."""
        if self._transport is None:
            self._transport = create_transport(self._config)
        return self._transport

    async def _send_with_interceptors(
        self,
        request: HTTPClientRequest,
    ) -> HTTPClientResponse:
        """Send request through interceptor chain."""
        transport = self._get_transport()

        # Build handler chain
        async def final_handler(req: HTTPClientRequest) -> HTTPClientResponse:
            return await transport.send(req)

        handler = final_handler

        # Apply interceptors in reverse order
        for interceptor in reversed(self._interceptors):
            current = handler

            async def make_interceptor(
                i: HTTPInterceptor = interceptor,
                h: Any = current,
            ) -> HTTPClientResponse:
                async def intercept_fn(r: HTTPClientRequest) -> HTTPClientResponse:
                    return await i.intercept(r, h)

                return intercept_fn

            handler = await make_interceptor()  # type: ignore

        return await handler(request)

    async def _send_with_middleware(
        self,
        request: HTTPClientRequest,
    ) -> HTTPClientResponse:
        """Send request through middleware stack."""

        async def final_handler(req: HTTPClientRequest) -> HTTPClientResponse:
            return await self._send_with_interceptors(req)

        if not self._middleware:
            return await final_handler(request)

        # Build middleware chain
        handler = final_handler
        for mw in reversed(self._middleware):
            current = handler

            async def make_middleware(
                middleware: HTTPClientMiddleware = mw,
                next_handler: Any = current,
            ) -> HTTPClientResponse:
                async def mw_fn(r: HTTPClientRequest) -> HTTPClientResponse:
                    return await middleware(r, next_handler)

                return mw_fn

            handler = await make_middleware()  # type: ignore

        return await handler(request)

    async def send(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """
        Send an HTTP request.

        Args:
            request: The request to send.

        Returns:
            The response.
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Add cookies to request
        cookie_header = self._cookies.get_header(request.url)
        if cookie_header:
            headers = dict(request.headers)
            existing = headers.get("Cookie", "")
            if existing:
                headers["Cookie"] = f"{existing}; {cookie_header}"
            else:
                headers["Cookie"] = cookie_header
            request = request.copy(headers=headers)

        # Send through middleware/interceptors
        response = await self._send_with_middleware(request)

        # Store cookies from response
        self._cookies.set_from_response(response.headers, request.url)

        # Handle redirects if enabled
        if self._config.follow_redirects and response.is_redirect:
            response = await self._follow_redirects(request, response)

        # Raise for status if configured
        if self._config.raise_for_status:
            response.raise_for_status()

        return response

    async def _follow_redirects(
        self,
        original_request: HTTPClientRequest,
        response: HTTPClientResponse,
    ) -> HTTPClientResponse:
        """Follow redirect responses."""
        from urllib.parse import urljoin

        from .faults import TooManyRedirectsFault

        history: list[HTTPClientResponse] = []
        current_response = response
        current_url = original_request.url

        for _ in range(self._config.max_redirects):
            if not current_response.is_redirect:
                current_response.history = history
                return current_response

            location = current_response.location
            if not location:
                current_response.history = history
                return current_response

            history.append(current_response)

            # Build redirect URL
            redirect_url = urljoin(current_url, location)

            # For 303 or POST redirects, switch to GET
            method = original_request.method
            body = original_request.body
            if current_response.status_code == 303 or (
                current_response.status_code in (301, 302) and method == HTTPMethod.POST
            ):
                method = HTTPMethod.GET
                body = None

            # Build new request
            redirect_request = original_request.copy(
                method=method,
                url=redirect_url,
                body=body,
            )

            current_url = redirect_url
            current_response = await self._send_with_middleware(redirect_request)

        raise TooManyRedirectsFault(
            f"Maximum redirects ({self._config.max_redirects}) exceeded",
            max_redirects=self._config.max_redirects,
            url=current_url,
        )

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
            **kwargs: Additional arguments for RequestBuilder.

        Returns:
            RequestBuilder instance.
        """
        return RequestBuilder(
            method,
            url,
            base_url=self._config.base_url,
            **kwargs,
        )

    async def _request(
        self,
        method: str | HTTPMethod,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict[str, Any] | str | bytes | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """Internal request method."""
        builder = self.request(method, url)

        if params:
            builder.params(params)
        if headers:
            builder.headers(headers)
        if json is not None:
            builder.json(json)
        if data is not None:
            if isinstance(data, (str, bytes)):
                builder.body(data if isinstance(data, bytes) else data.encode())
            else:
                builder.form(data)
        if timeout is not None:
            if isinstance(timeout, (int, float)):
                builder.timeout(total=timeout)
            else:
                builder.timeout(
                    total=timeout.total,
                    connect=timeout.connect,
                    read=timeout.read,
                )

        request = builder.build()
        return await self.send(request)

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """Send a GET request."""
        return await self._request(
            "GET",
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
        timeout: float | TimeoutConfig | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """Send a POST request."""
        return await self._request(
            "POST",
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
        """Send a PUT request."""
        return await self._request(
            "PUT",
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
        """Send a PATCH request."""
        return await self._request(
            "PATCH",
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
        """Send a DELETE request."""
        return await self._request(
            "DELETE",
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
        """Send a HEAD request."""
        return await self._request(
            "HEAD",
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
        """Send an OPTIONS request."""
        return await self._request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    async def close(self) -> None:
        """Close the session."""
        self._closed = True

        if self._transport:
            await self._transport.close()
            self._transport = None

        logger.debug("Session closed")

    async def __aenter__(self) -> HTTPSession:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *exc: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        return f"<HTTPSession base_url={self._config.base_url!r}>"
