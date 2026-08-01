"""
AquilaCache -- HTTP response caching middleware.

Integrates with Aquilia's middleware stack to provide:
- Automatic response caching for GET/HEAD requests
- ETag generation and validation
- Cache-Control header management
- Vary header support
- Namespace isolation per route pattern
- Stale-while-revalidate support
- Cache bypass via X-Cache-Bypass header
- Route-level TTL overrides via response headers
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from typing import TYPE_CHECKING, Any

from aquilia.middleware import Middleware
from aquilia.response import Response

if TYPE_CHECKING:
    from aquilia.cache.service import CacheService
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request

logger = logging.getLogger("aquilia.cache.middleware")


class CacheMiddleware(Middleware):
    """
    HTTP response caching middleware.

    Caches response bodies for cacheable requests and serves them
    directly on subsequent identical requests, bypassing the handler.

    Features:
    - Only caches GET/HEAD by default
    - Respects Cache-Control: no-cache, no-store
    - Generates and validates ETags
    - Handles Vary headers
    - Stale-while-revalidate: serve stale content while refreshing
    - X-Cache-Bypass header to skip cache for debugging
    - X-Cache-TTL response header for route-level TTL overrides
    - Integrates with CacheService for backend flexibility

    Security:
        The cache is **shared**, so any response that varies per identity
        must not be stored under an identity-independent key.  Two
        safeguards enforce this and neither can be disabled implicitly:

        1. A request carrying an identity signal (``Cookie`` or
           ``Authorization``) is only served from / stored in the cache when
           that header is listed in ``vary_headers``; otherwise the request
           bypasses the cache entirely.
        2. A response that sets ``Set-Cookie`` (or is marked ``private`` /
           ``no-store``) is never stored.

        Pass ``cache_authenticated=True`` together with the relevant
        ``vary_headers`` to deliberately cache per-identity responses.

    Args:
        cache_service: Backing cache service.
        default_ttl: TTL in seconds applied when a route sets no override.
        cacheable_methods: HTTP methods eligible for caching.
        vary_headers: Request headers folded into the cache key.
        namespace: Cache namespace for stored responses.
        stale_while_revalidate: Seconds a stale entry may still be served
            while a background refresh runs.
        cache_authenticated: Allow caching of identity-bearing requests when
            the corresponding header is present in ``vary_headers``.

    Usage::

        server.middleware_stack.add(
            CacheMiddleware(cache_service, default_ttl=60),
            scope="global",
            priority=25,
            name="response_cache",
        )

        # Deliberately cache per-session responses:
        CacheMiddleware(
            cache_service,
            vary_headers=("Accept", "Cookie"),
            cache_authenticated=True,
        )
    """

    #: Request headers that identify a caller and therefore partition the cache.
    IDENTITY_HEADERS: tuple[str, ...] = ("cookie", "authorization")

    def __init__(
        self,
        cache_service: CacheService,
        default_ttl: int = 60,
        cacheable_methods: tuple[str, ...] = ("GET", "HEAD"),
        vary_headers: tuple[str, ...] = ("Accept", "Accept-Encoding"),
        namespace: str = "http_response",
        stale_while_revalidate: int = 0,
        cache_authenticated: bool = False,
    ):
        self._cache = cache_service
        self._default_ttl = default_ttl
        self._cacheable_methods = cacheable_methods
        self._vary_headers = vary_headers
        self._namespace = namespace
        self._stale_while_revalidate = stale_while_revalidate
        self._cache_authenticated = cache_authenticated
        self._varied_identity = frozenset(h.lower() for h in vary_headers) & frozenset(self.IDENTITY_HEADERS)
        self._refresh_tasks: set[asyncio.Task[None]] = set()

        if cache_authenticated and not self._varied_identity:
            logger.warning(
                "CacheMiddleware(cache_authenticated=True) has no identity header in "
                "vary_headers; authenticated requests will still bypass the cache. "
                "Add 'Cookie' and/or 'Authorization' to vary_headers."
            )

    def _identity_blocks_cache(self, request: Request) -> bool:
        """
        Report whether this request's identity signals make caching unsafe.

        A request is unsafe when it carries an identity header that is not
        folded into the cache key, since the resulting entry would be served
        to other callers.

        Args:
            request: Inbound request.

        Returns:
            True if the request must bypass the cache.
        """
        getter = getattr(getattr(request, "headers", None), "get", None)
        if getter is None:
            return False

        for header in self.IDENTITY_HEADERS:
            if not getter(header, ""):
                continue
            if self._cache_authenticated and header in self._varied_identity:
                continue
            return True
        return False

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Any,
    ) -> Response:
        """Middleware handler."""
        # Only cache allowed methods
        if request.method not in self._cacheable_methods:
            return await next_handler(request, ctx)

        # Never let an identity-bearing request populate or read a shared entry
        # unless its identity header is part of the cache key.
        if self._identity_blocks_cache(request):
            response = await next_handler(request, ctx)
            if hasattr(response, "headers"):
                response.set_header("X-Cache", "PRIVATE")
            return response

        # Check for cache bypass header (requires valid secret token)
        bypass = ""
        if hasattr(request, "headers") and hasattr(request.headers, "get"):
            bypass = request.headers.get("x-cache-bypass", "") or ""
        if bypass:
            bypass_secret = os.environ.get("AQUILIA_CACHE_BYPASS_SECRET", "")
            if bypass_secret and hmac.compare_digest(bypass.strip(), bypass_secret):
                response = await next_handler(request, ctx)
                response.set_header("X-Cache", "BYPASS")
                return response
            else:
                # Ignore invalid bypass attempts silently — treat as normal request
                logger.warning("Rejected X-Cache-Bypass: invalid or missing secret.")

        # Respect no-cache/no-store directives
        cache_control = ""
        if hasattr(request, "headers") and hasattr(request.headers, "get"):
            cache_control = request.headers.get("cache-control", "") or ""

        if "no-store" in cache_control:
            return await next_handler(request, ctx)

        # Build cache key from request
        cache_key = self._build_request_key(request)

        # Check for cached response
        cached_data = await self._cache.get(cache_key, namespace=self._namespace)

        if cached_data and isinstance(cached_data, dict):
            # Check if stale
            cached_at = cached_data.get("cached_at", 0)
            ttl_used = cached_data.get("ttl", self._default_ttl)
            age = time.time() - cached_at
            is_stale = age > ttl_used

            # Check ETag with If-None-Match
            etag = cached_data.get("etag", "")
            if_none_match = ""
            if hasattr(request, "headers") and hasattr(request.headers, "get"):
                if_none_match = request.headers.get("if-none-match", "") or ""

            if if_none_match and if_none_match == etag:
                return Response(content=b"", status=304, headers={"ETag": etag})

            # Handle no-cache: must revalidate but can serve stale during revalidation
            if "no-cache" in cache_control:
                # Must revalidate -- go to handler
                pass
            elif is_stale and self._stale_while_revalidate > 0:
                # Stale-while-revalidate: serve stale, refresh in background
                stale_age = age - ttl_used
                if stale_age <= self._stale_while_revalidate:
                    # Serve stale content
                    headers = cached_data.get("headers", {})
                    headers["X-Cache"] = "STALE"
                    headers["ETag"] = etag
                    headers["Age"] = str(int(age))

                    # Trigger background refresh
                    self._spawn_refresh(request, ctx, next_handler, cache_key)

                    return Response(
                        content=cached_data.get("body", b""),
                        status=cached_data.get("status", 200),
                        headers=headers,
                    )
            elif not is_stale:
                # Fresh -- serve from cache
                headers = cached_data.get("headers", {})
                headers["X-Cache"] = "HIT"
                headers["ETag"] = etag
                headers["Age"] = str(int(age))

                return Response(
                    content=cached_data.get("body", b""),
                    status=cached_data.get("status", 200),
                    headers=headers,
                )

        # Cache miss -- call handler
        response = await next_handler(request, ctx)

        # Only cache successful responses
        if response.status < 200 or response.status >= 400:
            return response

        # Check response-level cache control
        resp_cache_control = self._response_header(response, "cache-control")
        if "no-store" in resp_cache_control or "private" in resp_cache_control:
            return response

        # A response that establishes a session is per-caller by definition.
        if self._response_header(response, "set-cookie"):
            response.set_header("X-Cache", "PRIVATE")
            return response

        # Determine TTL (route-level override via X-Cache-TTL header)
        ttl = self._default_ttl
        custom_ttl = self._response_header(response, "x-cache-ttl")
        if custom_ttl.isdigit():
            ttl = int(custom_ttl)

        # Generate ETag. A body that cannot be materialised (streaming or
        # awaitable content) is not cacheable -- caching an empty placeholder
        # would serve blank responses on every subsequent hit.
        body = response.body() if hasattr(response, "body") else None
        if body is None:
            return response
        etag = self._generate_etag(body)

        # Store in cache
        cache_data = {
            "body": body,
            "status": response.status,
            "headers": dict(response.headers) if hasattr(response, "headers") else {},
            "etag": etag,
            "cached_at": time.time(),
            "ttl": ttl,
        }

        await self._cache.set(
            cache_key,
            cache_data,
            ttl=ttl + self._stale_while_revalidate,  # Keep longer for stale serving
            namespace=self._namespace,
        )

        # Add cache headers to response
        response.set_header("X-Cache", "MISS")
        response.set_header("ETag", etag)
        cache_control_value = f"max-age={ttl}"
        if self._stale_while_revalidate > 0:
            cache_control_value += f", stale-while-revalidate={self._stale_while_revalidate}"
        response.set_header("Cache-Control", cache_control_value)

        return response

    @staticmethod
    def _response_header(response: Response, name: str) -> str:
        """
        Read a response header case-insensitively.

        Args:
            response: Response to inspect.
            name: Header name, lowercase.

        Returns:
            The header value, or an empty string when absent.

        Note:
            ``Response.headers`` normalises keys to lowercase, so a lookup by
            the canonical mixed-case spelling silently misses.
        """
        headers = getattr(response, "headers", None)
        if not headers:
            return ""
        value = headers.get(name) or headers.get(name.title()) or ""
        if isinstance(value, list):
            return ";".join(value)
        return str(value)

    def _spawn_refresh(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Any,
        cache_key: str,
    ) -> None:
        """
        Schedule a stale-while-revalidate refresh, retaining a strong reference.

        Args:
            request: The request to replay against the handler.
            ctx: Request context for the replay.
            next_handler: Downstream handler.
            cache_key: Key whose entry should be refreshed.

        Returns:
            ``None``.

        Note:
            The task is held in ``_refresh_tasks`` until completion so the
            event loop cannot garbage-collect it mid-flight.
        """
        task = asyncio.ensure_future(self._background_refresh(request, ctx, next_handler, cache_key))
        self._refresh_tasks.add(task)
        task.add_done_callback(self._refresh_tasks.discard)

    async def drain(self, timeout: float = 5.0) -> None:
        """
        Await any in-flight background refreshes.

        Args:
            timeout: Maximum seconds to wait before cancelling stragglers.

        Returns:
            ``None``.

        Usage::

            await cache_middleware.drain()
        """
        if not self._refresh_tasks:
            return
        pending = tuple(self._refresh_tasks)
        done, still_pending = await asyncio.wait(pending, timeout=timeout)
        for task in still_pending:
            task.cancel()

    async def _background_refresh(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Any,
        cache_key: str,
    ) -> None:
        """Refresh cache entry in background (stale-while-revalidate)."""
        try:
            response = await next_handler(request, ctx)
            if 200 <= response.status < 400:
                body = response.body() if hasattr(response, "body") else None
                if body is None:
                    return

                etag = self._generate_etag(body)
                cache_data = {
                    "body": body,
                    "status": response.status,
                    "headers": dict(response.headers) if hasattr(response, "headers") else {},
                    "etag": etag,
                    "cached_at": time.time(),
                    "ttl": self._default_ttl,
                }
                await self._cache.set(
                    cache_key,
                    cache_data,
                    ttl=self._default_ttl + self._stale_while_revalidate,
                    namespace=self._namespace,
                )
        except Exception as e:
            logger.warning(f"Background cache refresh failed: {e}")

    def _build_request_key(self, request: Request) -> str:
        """Build a cache key from request attributes."""
        parts = [request.method, request.path]

        # Include query string
        if hasattr(request, "query_string") and request.query_string:
            parts.append(str(request.query_string))

        # Include Vary headers
        for header in self._vary_headers:
            if hasattr(request, "headers") and hasattr(request.headers, "get"):
                val = request.headers.get(header, "")
                if val:
                    parts.append(f"{header}={val}")

        return ":".join(parts)

    def _generate_etag(self, body: bytes) -> str:
        """Generate ETag from response body using SHA-256."""
        digest = hashlib.sha256(body).hexdigest()[:32]
        return f'W/"{digest}"'
