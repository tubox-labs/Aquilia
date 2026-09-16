"""
AquilaHTTP — HTTP Session.

Persistent HTTP session with shared cookies, headers,
and connection reuse.
"""

from __future__ import annotations

import logging
from typing import Any

from aquilia.http._transport import HTTPTransport, create_transport
from aquilia.http.config import HTTPClientConfig, TimeoutConfig
from aquilia.http.cookies import CookieJar
from aquilia.http.interceptors import HTTPInterceptor
from aquilia.http.middleware import HTTPClientMiddleware
from aquilia.http.request import HTTPClientRequest, HTTPMethod, RequestBuilder
from aquilia.http.response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.session")

# A redirect response body larger than this is aborted instead of drained:
# reading megabytes of unwanted body just to reuse a connection is a bad
# trade (N-05).
_REDIRECT_DRAIN_LIMIT = 64 * 1024


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
        # ``is None`` check, not truthiness: an empty CookieJar is falsy
        # (it defines __len__) and must not be silently replaced.
        self._cookies = cookies if cookies is not None else CookieJar()
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
        from aquilia.http.middleware import RetryMiddleware
        from aquilia.http.retry import create_retry_strategy

        transport = self._get_transport()

        # Build handler chain
        async def final_handler(req: HTTPClientRequest) -> HTTPClientResponse:
            return await transport.send(req)

        handler = final_handler

        # Auto-retry sits INNERMOST -- wrapping only the transport call,
        # inside any user middleware -- and only when a retry policy is
        # actually configured (the client-level default is no retries).
        if self._config.retry.max_attempts > 0:
            retry_middleware = RetryMiddleware(create_retry_strategy(self._config.retry))
            # Bind the current handler explicitly: the closure below must
            # not see the rebound ``handler`` name (late binding would
            # make retry wrap itself).
            inner = handler

            async def retry_handler(req: HTTPClientRequest) -> HTTPClientResponse:
                return await retry_middleware(req, inner)

            handler = retry_handler

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

        # Merge config default headers under the per-request headers
        # (per-request wins). This is where constructor headers finally
        # reach the wire -- before, they were stored but never sent
        # (NEW-3). Applies to every send path: direct send(), builder
        # requests, and each redirect hop (via copy()).
        if self._config.default_headers:
            request = request.copy(headers=self._config.merge_headers(request.headers))

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

        # Handle redirects if enabled. A per-request override
        # (request.follow_redirects) wins over the session default
        # (F-HTTP-05).
        follow = request.follow_redirects if request.follow_redirects is not None else self._config.follow_redirects
        if follow and response.is_redirect:
            response = await self._follow_redirects(request, response)

        # Store cookies from response: feed the raw field lines, not the
        # collapsed dict -- duplicate Set-Cookie headers must each reach
        # the jar (F-HTTP-06). Done after redirect handling so the
        # final response's cookies are stored too; each redirect hop
        # stores its own cookies inside _follow_redirects.
        self._cookies.set_from_response(response.raw_headers, request.url)

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

        from aquilia.http.faults import TooManyRedirectsFault

        history: list[HTTPClientResponse] = []
        current_response = response
        current_request = original_request
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
            method = current_request.method
            body = current_request.body
            if current_response.status_code == 303 or (
                current_response.status_code in (301, 302) and method == HTTPMethod.POST
            ):
                method = HTTPMethod.GET
                body = None

            # Build new request: hop ≥ 2 must re-evaluate the per-request
            # follow_redirects override too (copy carries it through).
            redirect_request = current_request.copy(
                method=method,
                url=redirect_url,
                body=body,
            )

            # Drain or close the intermediate response so its connection
            # does not leak: drain when little is left, otherwise abort.
            await self._release_redirect_response(current_response)

            current_url = redirect_url
            current_request = redirect_request
            # Every hop runs through the same send path as a first
            # request: cookies are attached from the jar, middleware and
            # interceptors apply, and the hop's own Set-Cookie lines are
            # stored (NEW-2).
            current_response = await self._send_with_middleware(redirect_request)
            self._cookies.set_from_response(current_response.raw_headers, redirect_request.url)

        raise TooManyRedirectsFault(
            f"Maximum redirects ({self._config.max_redirects}) exceeded",
            max_redirects=self._config.max_redirects,
            url=current_url,
        )

    async def _release_redirect_response(self, response: HTTPClientResponse) -> None:
        """Release an intermediate redirect response's connection.

        A redirect body is worthless to the caller, but its connection
        is still owned by the response: drain it when only a little
        remains (so the connection can be reused), otherwise abort it
        (N-05 -- never block the redirect on a large unwanted body).
        """
        remaining = response.content_length
        if remaining is not None and remaining <= _REDIRECT_DRAIN_LIMIT:
            try:
                await response.read()
                return
            except Exception:
                pass
        await response.close()

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
        follow_redirects: bool | None = None,
        **kwargs: Any,
    ) -> HTTPClientResponse:
        """Internal request method."""
        if kwargs:
            # Silently dropping a kwarg the caller believes in is a bug
            # factory -- fail loudly instead.
            raise TypeError(f"Unexpected keyword argument(s): {', '.join(sorted(kwargs))}")

        builder = self.request(method, url)

        # Default params from config sit under per-request params
        # (per-request wins on key conflicts).
        if self._config.default_params or params:
            builder.params(self._config.merge_params(params))
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
        if follow_redirects is not None:
            builder.follow_redirects(follow_redirects)

        request = builder.build()
        return await self.send(request)

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
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
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
            **kwargs,
        )

    async def put(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
            **kwargs,
        )

    async def patch(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
            **kwargs,
        )

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
            **kwargs,
        )

    async def head(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
            **kwargs,
        )

    async def options(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool | None = None,
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
            follow_redirects=follow_redirects,
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
