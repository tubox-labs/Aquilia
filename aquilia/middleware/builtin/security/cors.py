"""CORS — cross-origin resource sharing (RFC 6454 / 7231 / Fetch Standard).

Origin matching supports exact strings, wildcard subdomains, and compiled
regexes, with an LRU cache so a hot origin is matched once rather than per
request.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from re import Pattern
from typing import TYPE_CHECKING

from aquilia.faults.domains import CORSViolationFault
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class _OriginMatcher:
    """
    Efficient origin matching with support for:
    - Exact strings
    - Wildcard "*"
    - Glob patterns  (e.g. "*.example.com")
    - Compiled regex patterns

    Uses an LRU cache to avoid re-evaluating expensive regex on every request.
    """

    __slots__ = ("_allow_all", "_exact", "_regex_patterns", "_cache", "_cache_limit")

    def __init__(
        self,
        origins: list[str | Pattern],
        cache_size: int = 512,
    ):
        self._allow_all = False
        self._exact: set[str] = set()
        self._regex_patterns: list[Pattern] = []
        self._cache: OrderedDict[str, bool] = OrderedDict()
        self._cache_limit = cache_size

        for origin in origins:
            if isinstance(origin, str):
                if origin == "*":
                    self._allow_all = True
                elif "*" in origin:
                    # Convert glob to regex: *.example.com → ^[^.]+\.example\.com$
                    escaped = re.escape(origin).replace(r"\*", "[^.]+")
                    self._regex_patterns.append(re.compile(f"^{escaped}$", re.IGNORECASE))
                else:
                    self._exact.add(origin.lower())
            else:
                # Pre-compiled regex
                self._regex_patterns.append(origin)

    def matches(self, origin: str) -> bool:
        if self._allow_all:
            return True

        origin_lower = origin.lower()

        # Check cache
        cached = self._cache.get(origin_lower)
        if cached is not None:
            self._cache.move_to_end(origin_lower)
            return cached

        result = self._evaluate(origin_lower)

        # Update LRU cache
        self._cache[origin_lower] = result
        if len(self._cache) > self._cache_limit:
            self._cache.popitem(last=False)

        return result

    def _evaluate(self, origin: str) -> bool:
        if origin in self._exact:
            return True
        return any(pattern.match(origin) for pattern in self._regex_patterns)

    @property
    def is_wildcard(self) -> bool:
        return self._allow_all


class CORSMiddleware(Middleware):
    """
    Full-featured CORS middleware following the Fetch Standard.

    Features:
    - Efficient LRU-cached origin matching (exact, glob, regex)
    - Separate preflight and simple-request handling
    - Vary header management (prevents cache poisoning)
    - Credential support with proper origin reflection
    - Expose-headers control
    - Per-route opt-out via request.state["cors_skip"]

    Args:
        allow_origins: Allowed origins (strings, globs, or compiled regex).
        allow_methods: Methods for Access-Control-Allow-Methods.
        allow_headers: Headers for Access-Control-Allow-Headers.
        expose_headers: Headers for Access-Control-Expose-Headers.
        allow_credentials: Allow credentials (cookies, Authorization).
        max_age: Preflight cache duration (seconds).
        allow_origin_regex: Convenience regex string.
    """

    def __init__(
        self,
        allow_origins: list[str | Pattern] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
        allow_origin_regex: str | None = None,
    ):
        origins = list(allow_origins or ["*"])
        if allow_origin_regex:
            origins.append(re.compile(allow_origin_regex))

        self._matcher = _OriginMatcher(origins)
        self._allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "HEAD",
            "OPTIONS",
        ]
        self._allow_headers = allow_headers or [
            "accept",
            "accept-language",
            "content-language",
            "content-type",
            "authorization",
            "x-requested-with",
            "x-request-id",
        ]
        self._expose_headers = expose_headers or []
        self._allow_credentials = allow_credentials
        self._max_age = max_age

        # Pre-compute header values
        self._methods_str = ", ".join(self._allow_methods)
        self._headers_str = ", ".join(self._allow_headers)
        self._expose_str = ", ".join(self._expose_headers) if self._expose_headers else ""

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        origin = request.header("origin")

        # No origin → not a CORS request
        if not origin:
            response = await next_handler(request, ctx)
            # Still add Vary so caches don't serve stale responses
            response.headers.setdefault("vary", "Origin")
            return response

        # Skip if route opted out
        if request.state.get("cors_skip"):
            return await next_handler(request, ctx)

        allowed = self._matcher.matches(origin)

        # Preflight
        if request.method == "OPTIONS":
            resp = self._preflight(origin, request, allowed)
            if not allowed:
                resp._fault = CORSViolationFault(origin=origin)
            return resp

        # Actual request
        response = await next_handler(request, ctx)
        self._apply_cors_headers(response, origin, allowed)
        if not allowed:
            response._fault = CORSViolationFault(origin=origin)
        return response

    def _preflight(self, origin: str, request: Request, allowed: bool) -> Response:
        headers: dict[str, str] = {}

        if allowed:
            self._set_origin_header(headers, origin)
            headers["access-control-allow-methods"] = self._methods_str
            headers["access-control-allow-headers"] = self._headers_str
            headers["access-control-max-age"] = str(self._max_age)

            if self._allow_credentials:
                headers["access-control-allow-credentials"] = "true"

        headers["vary"] = "Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        headers["content-length"] = "0"

        from aquilia.response import Response

        return Response(b"", status=204, headers=headers)

    def _apply_cors_headers(self, response: Response, origin: str, allowed: bool) -> None:
        if allowed:
            self._set_origin_header(response.headers, origin)

            if self._allow_credentials:
                response.headers["access-control-allow-credentials"] = "true"

            if self._expose_str:
                response.headers["access-control-expose-headers"] = self._expose_str

        # Always set Vary to prevent cache poisoning
        existing_vary = response.headers.get("vary", "")
        if "Origin" not in existing_vary:
            new_vary = f"{existing_vary}, Origin" if existing_vary else "Origin"
            response.headers["vary"] = new_vary

    def _set_origin_header(self, headers: dict, origin: str) -> None:
        """Set Access-Control-Allow-Origin.  Reflects origin when credentials
        are enabled (wildcard forbidden with credentials)."""
        if self._allow_credentials or not self._matcher.is_wildcard:
            headers["access-control-allow-origin"] = origin
        else:
            headers["access-control-allow-origin"] = "*"


__all__ = ["CORSMiddleware"]
