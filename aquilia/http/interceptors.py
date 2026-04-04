"""
AquilaHTTP — Interceptors.

Request/response interceptors for cross-cutting concerns
like logging, authentication, metrics, and caching.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .request import HTTPClientRequest
from .response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.interceptors")


class HTTPInterceptor(ABC):
    """
    Base class for HTTP interceptors.

    Interceptors can modify requests before sending and
    responses after receiving.
    """

    @abstractmethod
    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        """
        Intercept and optionally modify request/response.

        Args:
            request: The outgoing request.
            next_handler: The next handler in the chain.

        Returns:
            The response (possibly modified).
        """
        ...


class InterceptorChain:
    """
    Chain of interceptors.

    Executes interceptors in order, with each interceptor
    wrapping the next.
    """

    __slots__ = ("_interceptors", "_handler")

    def __init__(
        self,
        interceptors: list[HTTPInterceptor] | None = None,
        handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]] | None = None,
    ):
        self._interceptors = list(interceptors) if interceptors else []
        self._handler = handler

    def add(self, interceptor: HTTPInterceptor) -> InterceptorChain:
        """Add an interceptor to the chain."""
        self._interceptors.append(interceptor)
        return self

    def set_handler(
        self,
        handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> InterceptorChain:
        """Set the final handler."""
        self._handler = handler
        return self

    async def execute(self, request: HTTPClientRequest) -> HTTPClientResponse:
        """Execute the interceptor chain."""
        if self._handler is None:
            raise RuntimeError("InterceptorChain requires a handler")

        # Build chain from inside out
        handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]] = self._handler

        for interceptor in reversed(self._interceptors):
            current_handler = handler

            async def make_next(
                interceptor: HTTPInterceptor = interceptor,
                next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]] = current_handler,
            ) -> Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]:
                async def next_fn(req: HTTPClientRequest) -> HTTPClientResponse:
                    return await interceptor.intercept(req, next_handler)

                return next_fn

            handler = await make_next()

        return await handler(request)

    def __len__(self) -> int:
        return len(self._interceptors)


# ============================================================================
# Built-in Interceptors
# ============================================================================


class LoggingInterceptor(HTTPInterceptor):
    """
    Logs request and response details.

    Configurable log level and detail.
    """

    __slots__ = ("_logger", "_log_headers", "_log_body")

    def __init__(
        self,
        logger_name: str = "aquilia.http",
        log_headers: bool = False,
        log_body: bool = False,
    ):
        self._logger = logging.getLogger(logger_name)
        self._log_headers = log_headers
        self._log_body = log_body

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        start_time = time.monotonic()

        # Log request
        self._logger.info(f"→ {request.method.value} {request.url}")
        if self._log_headers:
            for name, value in request.headers.items():
                self._logger.debug(f"  {name}: {value}")

        try:
            response = await next_handler(request)

            # Log response
            elapsed = time.monotonic() - start_time
            self._logger.info(f"← {response.status_code} {response.reason} ({elapsed:.3f}s)")
            if self._log_headers:
                for name, value in response.headers.items():
                    self._logger.debug(f"  {name}: {value}")

            return response

        except Exception as e:
            elapsed = time.monotonic() - start_time
            self._logger.error(f"✗ {type(e).__name__}: {e} ({elapsed:.3f}s)")
            raise


class HeaderInterceptor(HTTPInterceptor):
    """
    Adds default headers to all requests.
    """

    __slots__ = ("_headers",)

    def __init__(self, headers: dict[str, str]):
        self._headers = headers

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        # Add headers that aren't already set
        new_headers = dict(request.headers)
        for name, value in self._headers.items():
            if name not in new_headers:
                new_headers[name] = value

        modified = request.copy(headers=new_headers)
        return await next_handler(modified)


class UserAgentInterceptor(HTTPInterceptor):
    """
    Sets User-Agent header.
    """

    __slots__ = ("_user_agent",)

    def __init__(self, user_agent: str = "Aquilia-HTTP/1.0"):
        self._user_agent = user_agent

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        if "User-Agent" not in request.headers:
            new_headers = dict(request.headers)
            new_headers["User-Agent"] = self._user_agent
            request = request.copy(headers=new_headers)

        return await next_handler(request)


class AcceptInterceptor(HTTPInterceptor):
    """
    Sets Accept header for content negotiation.
    """

    __slots__ = ("_accept",)

    def __init__(self, accept: str = "application/json"):
        self._accept = accept

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        if "Accept" not in request.headers:
            new_headers = dict(request.headers)
            new_headers["Accept"] = self._accept
            request = request.copy(headers=new_headers)

        return await next_handler(request)


@dataclass
class RequestMetrics:
    """Metrics collected for a request."""

    method: str
    url: str
    status_code: int
    elapsed: float
    request_size: int
    response_size: int | None
    error: str | None = None


class MetricsInterceptor(HTTPInterceptor):
    """
    Collects request metrics.

    Calls a callback with metrics for each request.
    """

    __slots__ = ("_callback",)

    def __init__(
        self,
        callback: Callable[[RequestMetrics], Awaitable[None]] | Callable[[RequestMetrics], None],
    ):
        self._callback = callback

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        start_time = time.monotonic()
        error_msg: str | None = None
        status_code = 0
        response_size: int | None = None

        # Calculate request size
        request_size = 0
        if isinstance(request.body, bytes):
            request_size = len(request.body)
        elif request.content_length:
            request_size = request.content_length

        try:
            response = await next_handler(request)
            status_code = response.status_code
            response_size = response.content_length
            return response

        except Exception as e:
            error_msg = str(e)
            raise

        finally:
            elapsed = time.monotonic() - start_time
            metrics = RequestMetrics(
                method=request.method.value,
                url=request.url,
                status_code=status_code,
                elapsed=elapsed,
                request_size=request_size,
                response_size=response_size,
                error=error_msg,
            )

            import asyncio

            result = self._callback(metrics)
            if asyncio.iscoroutine(result):
                await result


class TimeoutInterceptor(HTTPInterceptor):
    """
    Enforces timeout on requests.

    Wraps the request in an asyncio timeout.
    """

    __slots__ = ("_timeout",)

    def __init__(self, timeout: float):
        self._timeout = timeout

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        import asyncio

        from .faults import RequestTimeoutFault

        try:
            return await asyncio.wait_for(
                next_handler(request),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise RequestTimeoutFault(
                f"Request timed out after {self._timeout}s",
                timeout=self._timeout,
                url=request.url,
            )


class RedirectInterceptor(HTTPInterceptor):
    """
    Handles HTTP redirects.

    Follows redirect responses automatically.
    """

    __slots__ = ("_max_redirects", "_follow_redirects")

    def __init__(
        self,
        max_redirects: int = 10,
        follow_redirects: bool = True,
    ):
        self._max_redirects = max_redirects
        self._follow_redirects = follow_redirects

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        from urllib.parse import urljoin

        from .faults import TooManyRedirectsFault
        from .request import HTTPMethod

        if not self._follow_redirects:
            return await next_handler(request)

        redirect_chain: list[str] = [request.url]
        current_request = request
        history: list[HTTPClientResponse] = []

        for _ in range(self._max_redirects + 1):
            response = await next_handler(current_request)

            if not response.is_redirect:
                # Add history to final response
                response.history = history
                return response

            location = response.location
            if not location:
                return response

            # Build redirect URL
            redirect_url = urljoin(current_request.url, location)
            redirect_chain.append(redirect_url)

            # Check for redirect loop
            if redirect_chain.count(redirect_url) > 1:
                raise TooManyRedirectsFault(
                    f"Redirect loop detected: {redirect_url}",
                    max_redirects=self._max_redirects,
                    url=redirect_url,
                    redirect_chain=redirect_chain,
                )

            # Record in history
            history.append(response)

            # For 303 or POST redirects, switch to GET
            method = current_request.method
            body = current_request.body
            if response.status_code == 303 or (response.status_code in (301, 302) and method == HTTPMethod.POST):
                method = HTTPMethod.GET
                body = None

            # Build new request
            current_request = current_request.copy(
                method=method,
                url=redirect_url,
                body=body,
            )

        raise TooManyRedirectsFault(
            f"Maximum redirects ({self._max_redirects}) exceeded",
            max_redirects=self._max_redirects,
            url=current_request.url,
            redirect_chain=redirect_chain,
        )


class CacheInterceptor(HTTPInterceptor):
    """
    HTTP response caching interceptor.

    Caches GET responses based on Cache-Control headers.
    """

    __slots__ = ("_cache", "_max_age")

    def __init__(
        self,
        cache: dict[str, tuple[HTTPClientResponse, float]] | None = None,
        max_age: float = 300.0,
    ):
        self._cache: dict[str, tuple[HTTPClientResponse, float]] = cache or {}
        self._max_age = max_age

    def _cache_key(self, request: HTTPClientRequest) -> str:
        """Generate cache key from request."""
        return f"{request.method.value}:{request.url}"

    def _is_cacheable(self, response: HTTPClientResponse) -> bool:
        """Check if response is cacheable."""
        if not response.is_success:
            return False

        cache_control = response.get_header("Cache-Control", "")
        if "no-store" in cache_control or "no-cache" in cache_control:
            return False

        return True

    def _get_max_age(self, response: HTTPClientResponse) -> float:
        """Extract max-age from response."""
        cache_control = response.get_header("Cache-Control", "")
        for part in cache_control.split(","):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    return float(part[8:])
                except ValueError:
                    pass
        return self._max_age

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        from .request import HTTPMethod

        # Only cache GET requests
        if request.method != HTTPMethod.GET:
            return await next_handler(request)

        key = self._cache_key(request)

        # Check cache
        if key in self._cache:
            response, expiry = self._cache[key]
            if time.monotonic() < expiry:
                logger.debug(f"Cache hit: {request.url}")
                return response
            else:
                del self._cache[key]

        # Make request
        response = await next_handler(request)

        # Cache if cacheable
        if self._is_cacheable(response):
            max_age = self._get_max_age(response)
            expiry = time.monotonic() + max_age
            # Need to read body to cache it
            body = await response.read()
            # Create a new response with cached body
            from .response import create_response

            cached = create_response(
                status_code=response.status_code,
                headers=response.headers,
                body=body,
                url=response.url,
                http_version=response.http_version,
                elapsed=response.elapsed,
            )
            self._cache[key] = (cached, expiry)
            logger.debug(f"Cached: {request.url} (max-age={max_age}s)")
            return cached

        return response
