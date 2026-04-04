"""
AquilaHTTP — Middleware.

Composable middleware chain for HTTP client requests.
Similar to server-side middleware but for outgoing requests.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from .request import HTTPClientRequest
from .response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.middleware")

# Type alias for middleware handler
MiddlewareHandler = Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]


class HTTPClientMiddleware(ABC):
    """
    Base class for HTTP client middleware.

    Middleware wraps the request/response cycle and can:
    - Modify requests before sending
    - Modify responses after receiving
    - Short-circuit the chain
    - Add error handling
    """

    @abstractmethod
    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        """
        Process the request.

        Args:
            request: The outgoing request.
            call_next: Calls the next middleware in the chain.

        Returns:
            The response.
        """
        ...


class MiddlewareStack:
    """
    Stack of middleware that processes requests.

    Middleware is executed in order for requests and
    reverse order for responses (onion model).
    """

    __slots__ = ("_middleware", "_handler")

    def __init__(self):
        self._middleware: list[HTTPClientMiddleware] = []
        self._handler: MiddlewareHandler | None = None

    def add(self, middleware: HTTPClientMiddleware) -> MiddlewareStack:
        """Add middleware to the stack."""
        self._middleware.append(middleware)
        return self

    def add_many(self, middleware: list[HTTPClientMiddleware]) -> MiddlewareStack:
        """Add multiple middleware to the stack."""
        self._middleware.extend(middleware)
        return self

    def set_handler(self, handler: MiddlewareHandler) -> MiddlewareStack:
        """Set the final request handler."""
        self._handler = handler
        return self

    def build(self) -> MiddlewareHandler:
        """
        Build the middleware chain.

        Returns:
            A single handler that executes all middleware.
        """
        if self._handler is None:
            raise RuntimeError("MiddlewareStack requires a handler")

        handler = self._handler

        # Build chain from inside out
        for middleware in reversed(self._middleware):
            current_handler = handler

            async def make_chain(
                mw: HTTPClientMiddleware = middleware,
                next_handler: MiddlewareHandler = current_handler,
            ) -> MiddlewareHandler:
                async def chained(request: HTTPClientRequest) -> HTTPClientResponse:
                    return await mw(request, next_handler)

                return chained

            import asyncio

            handler = asyncio.get_event_loop().run_until_complete(make_chain())

        return handler

    async def execute(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """Execute the middleware chain."""
        if self._handler is None:
            raise RuntimeError("MiddlewareStack requires a handler")

        # Build chain dynamically
        async def build_and_execute() -> HTTPClientResponse:
            handler = self._handler

            for middleware in reversed(self._middleware):
                current = handler

                async def wrapped(
                    req: HTTPClientRequest,
                    mw: HTTPClientMiddleware = middleware,
                    next_h: MiddlewareHandler = current,  # type: ignore
                ) -> HTTPClientResponse:
                    return await mw(req, next_h)

                handler = wrapped

            return await handler(request)  # type: ignore

        return await build_and_execute()


# ============================================================================
# Built-in Middleware
# ============================================================================


class LoggingMiddleware(HTTPClientMiddleware):
    """
    Logs requests and responses.
    """

    __slots__ = ("_logger", "_log_body")

    def __init__(
        self,
        logger_name: str = "aquilia.http.client",
        log_body: bool = False,
    ):
        self._logger = logging.getLogger(logger_name)
        self._log_body = log_body

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        import time

        start = time.monotonic()
        self._logger.info(f"→ {request.method.value} {request.url}")

        try:
            response = await call_next(request)
            elapsed = time.monotonic() - start
            self._logger.info(f"← {response.status_code} {response.reason} ({elapsed:.3f}s)")
            return response
        except Exception as e:
            elapsed = time.monotonic() - start
            self._logger.error(f"✗ {type(e).__name__}: {e} ({elapsed:.3f}s)")
            raise


class HeadersMiddleware(HTTPClientMiddleware):
    """
    Adds default headers to all requests.
    """

    __slots__ = ("_headers",)

    def __init__(self, headers: dict[str, str]):
        self._headers = headers

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        new_headers = dict(self._headers)
        new_headers.update(request.headers)
        request = request.copy(headers=new_headers)
        return await call_next(request)


class TimeoutMiddleware(HTTPClientMiddleware):
    """
    Enforces timeout on requests.
    """

    __slots__ = ("_timeout",)

    def __init__(self, timeout: float):
        self._timeout = timeout

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        import asyncio

        from .faults import RequestTimeoutFault

        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise RequestTimeoutFault(
                f"Request timed out after {self._timeout}s",
                timeout=self._timeout,
                url=request.url,
            )


class ErrorHandlingMiddleware(HTTPClientMiddleware):
    """
    Handles errors and converts them to faults.
    """

    __slots__ = ("_raise_for_status",)

    def __init__(self, raise_for_status: bool = True):
        self._raise_for_status = raise_for_status

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        try:
            response = await call_next(request)

            if self._raise_for_status:
                response.raise_for_status()

            return response

        except Exception:
            raise


class RetryMiddleware(HTTPClientMiddleware):
    """
    Retries failed requests.
    """

    __slots__ = ("_strategy",)

    def __init__(self, strategy: Any = None):  # RetryStrategy
        from .retry import ExponentialBackoff

        self._strategy = strategy or ExponentialBackoff()

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        from .retry import RetryExecutor

        executor = RetryExecutor(self._strategy)
        return await executor.execute(call_next, request)


class CompressionMiddleware(HTTPClientMiddleware):
    """
    Handles request/response compression.
    """

    __slots__ = ("_accept_encoding",)

    def __init__(
        self,
        accept_encoding: str = "gzip, deflate",
    ):
        self._accept_encoding = accept_encoding

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        # Add Accept-Encoding header
        if "Accept-Encoding" not in request.headers:
            new_headers = dict(request.headers)
            new_headers["Accept-Encoding"] = self._accept_encoding
            request = request.copy(headers=new_headers)

        response = await call_next(request)

        # Note: Actual decompression is typically handled by
        # the transport layer (aiohttp)

        return response


class CacheMiddleware(HTTPClientMiddleware):
    """
    Caches GET responses.
    """

    __slots__ = ("_cache", "_max_age")

    def __init__(
        self,
        cache: dict[str, tuple[HTTPClientResponse, float]] | None = None,
        max_age: float = 300.0,
    ):
        self._cache: dict[str, tuple[HTTPClientResponse, float]] = cache or {}
        self._max_age = max_age

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        import time

        from .request import HTTPMethod

        # Only cache GET requests
        if request.method != HTTPMethod.GET:
            return await call_next(request)

        key = f"{request.method.value}:{request.url}"

        # Check cache
        if key in self._cache:
            response, expiry = self._cache[key]
            if time.monotonic() < expiry:
                return response
            else:
                del self._cache[key]

        # Make request
        response = await call_next(request)

        # Cache successful responses
        if response.is_success:
            expiry = time.monotonic() + self._max_age
            self._cache[key] = (response, expiry)

        return response


class BaseURLMiddleware(HTTPClientMiddleware):
    """
    Prepends base URL to relative URLs.
    """

    __slots__ = ("_base_url",)

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        from urllib.parse import urljoin, urlparse

        parsed = urlparse(request.url)

        # If URL has no scheme, prepend base URL
        if not parsed.scheme:
            new_url = urljoin(self._base_url + "/", request.url.lstrip("/"))
            request = request.copy(url=new_url)

        return await call_next(request)


class CookieMiddleware(HTTPClientMiddleware):
    """
    Manages cookies automatically.
    """

    __slots__ = ("_jar",)

    def __init__(self, jar: Any = None):  # CookieJar
        from .cookies import CookieJar

        self._jar = jar or CookieJar()

    @property
    def jar(self) -> Any:
        return self._jar

    async def __call__(
        self,
        request: HTTPClientRequest,
        call_next: MiddlewareHandler,
    ) -> HTTPClientResponse:
        # Add cookies to request
        cookie_header = self._jar.get_header(request.url)
        if cookie_header:
            new_headers = dict(request.headers)
            existing = new_headers.get("Cookie", "")
            if existing:
                new_headers["Cookie"] = f"{existing}; {cookie_header}"
            else:
                new_headers["Cookie"] = cookie_header
            request = request.copy(headers=new_headers)

        response = await call_next(request)

        # Store cookies from response
        self._jar.set_from_response(response.headers, request.url)

        return response


def create_middleware_stack(
    *,
    base_url: str | None = None,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
    enable_logging: bool = False,
    enable_retry: bool = False,
    enable_cache: bool = False,
    enable_cookies: bool = False,
    raise_for_status: bool = False,
) -> list[HTTPClientMiddleware]:
    """
    Create a standard middleware stack.

    Args:
        base_url: Base URL to prepend.
        timeout: Request timeout.
        headers: Default headers.
        enable_logging: Enable request/response logging.
        enable_retry: Enable automatic retries.
        enable_cache: Enable response caching.
        enable_cookies: Enable cookie management.
        raise_for_status: Raise exceptions for 4xx/5xx.

    Returns:
        List of middleware in execution order.
    """
    middleware: list[HTTPClientMiddleware] = []

    if enable_logging:
        middleware.append(LoggingMiddleware())

    if timeout:
        middleware.append(TimeoutMiddleware(timeout))

    if base_url:
        middleware.append(BaseURLMiddleware(base_url))

    if headers:
        middleware.append(HeadersMiddleware(headers))

    if enable_cookies:
        middleware.append(CookieMiddleware())

    if enable_cache:
        middleware.append(CacheMiddleware())

    if enable_retry:
        middleware.append(RetryMiddleware())

    if raise_for_status:
        middleware.append(ErrorHandlingMiddleware(raise_for_status=True))

    return middleware
