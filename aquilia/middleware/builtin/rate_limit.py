"""
Rate Limiting Middleware - Production-grade request rate limiting.

Implements multiple algorithms:
- Token Bucket:  Smooth burst-tolerant limiting with refill rate
- Sliding Window: Accurate per-window counting (no boundary spikes)
- Fixed Window:   Simple per-interval counters (lightweight)

Features:
- Per-client keying (IP, API key, user ID, or custom extractor)
- Multiple limit tiers (global, per-route, per-user)
- Retry-After header computation
- Configurable response format (JSON / plain)
- Memory-efficient storage with automatic expiration (O(1) amortized)
- Thread-safe via dict-level atomicity in CPython

All middleware follow the Aquilia async signature:
    async def __call__(self, request, ctx, next) -> Response
"""

from __future__ import annotations

import logging
import math
from collections.abc import Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Any,
)

from aquilia.faults.domains import RateLimitExceededFault
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.utils.throttling import (
    NEVER_REFILLS_RETRY_AFTER,
    BucketStore,
    SlidingWindowCounter,
    TokenBucket,
)

# Runtime import, not TYPE_CHECKING: _rate_limited_response constructs a Response
# when a limit trips. aquilia.response does not import middleware_ext, so this
# introduces no cycle.
from aquilia.response import Response

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request

Handler = Callable[["Request", "RequestCtx"], Awaitable["Response"]]

logger = logging.getLogger("aquilia.middleware.rate_limit")


# ─── Key extractors ──────────────────────────────────────────────────────────


def ip_key_extractor(request: Request) -> str:
    """Extract client IP as rate-limit key."""
    # Prefer forwarded IP (set by ProxyFixMiddleware)
    ip = request.state.get("client_ip")
    if ip:
        return f"ip:{ip}"
    # Fallback to ASGI scope
    if hasattr(request, "_scope") and isinstance(request._scope, dict):
        client = request._scope.get("client")
        if client:
            return f"ip:{client[0]}"
    return "ip:unknown"


def api_key_extractor(request: Request) -> str | None:
    """Extract API key from Authorization or X-API-Key header."""
    api_key = request.header("x-api-key")
    if api_key:
        return f"apikey:{api_key}"
    auth = request.header("authorization")
    if auth and auth.lower().startswith("bearer "):
        return f"bearer:{auth[7:][:32]}"  # Truncate for safety
    return None


def user_key_extractor(request: Request) -> str | None:
    """Extract user ID from request state (set by auth middleware)."""
    user_id = request.state.get("user_id")
    if user_id:
        return f"user:{user_id}"
    identity = request.state.get("identity")
    if identity and hasattr(identity, "id"):
        return f"user:{identity.id}"
    return None


# ─── Algorithms (shared with the WebSocket limiter) ──────────────────────────

# The algorithms live in aquilia.middleware.utils.throttling so HTTP and WebSocket limiters
# enforce identically. These private aliases keep the historical names importable.
_NEVER_REFILLS_RETRY_AFTER = NEVER_REFILLS_RETRY_AFTER
_TokenBucket = TokenBucket
_SlidingWindowCounter = SlidingWindowCounter
_BucketStore = BucketStore


# ─── Rate Limit Configuration ────────────────────────────────────────────────


class RateLimitRule:
    """
    A single rate-limit rule.

    Ecosystem Integration:
    - Configurable via Integration.rate_limit() config builder
    - RateLimitExceededFault raised through Aquilia fault system
    - Key extractors integrate with DI (user identity) and ProxyFixMiddleware (client IP)

    Attributes:
        limit: Maximum requests per window.
        window: Window size in seconds.
        algorithm: "token_bucket" or "sliding_window".
        key_func: Function to extract the rate-limit key from request.
                  Defaults to IP-based.
        burst: Extra burst capacity (token_bucket only). Defaults to limit.
        scope: Which paths this rule applies to ("*" = all).
        methods: HTTP methods this rule applies to (empty = all).
        requires_identity: Whether ``key_func`` needs an authenticated identity
                  on ``request.state``. Auto-detected for ``user_key_extractor``;
                  set explicitly for custom identity-based extractors. Rules with
                  this set must be registered *after* the auth middleware, or
                  they can never produce a key.
    """

    __slots__ = ("limit", "window", "algorithm", "key_func", "burst", "scope", "methods", "requires_identity")

    def __init__(
        self,
        limit: int = 100,
        window: float = 60.0,
        algorithm: str = "sliding_window",
        key_func: Callable[[Request], str | None] | None = None,
        burst: int | None = None,
        scope: str = "*",
        methods: list[str] | None = None,
        requires_identity: bool | None = None,
    ):
        self.limit = limit
        self.window = window
        self.algorithm = algorithm
        self.key_func = key_func or ip_key_extractor
        self.burst = burst
        self.scope = scope
        self.methods = methods or []
        # Auto-detect for the built-in extractor so the common config path
        # ("per_user": true) gets correct ordering without extra wiring.
        if requires_identity is None:
            requires_identity = self.key_func is user_key_extractor
        self.requires_identity = requires_identity

    def matches(self, request: Request) -> bool:
        """Check if this rule applies to the given request."""
        if self.methods and request.method not in self.methods:
            return False
        if self.scope == "*":
            return True
        return request.path.startswith(self.scope)


# ─── Rate Limit Middleware ────────────────────────────────────────────────────


class RateLimitMiddleware(Middleware):
    """
    Multi-algorithm rate limiting middleware.

    Supports layered rules evaluated in order.  The first rule whose
    ``matches()`` returns True and whose bucket is exhausted will
    trigger a 429 response.

    Standard rate-limit headers (draft-ietf-httpapi-ratelimit-headers):
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset
    - Retry-After

    Args:
        rules: List of RateLimitRule to evaluate.
        default_limit: Fallback limit if no rules provided.
        default_window: Fallback window (seconds).
        response_format: "json" or "plain" for 429 body.
        include_headers: Include rate-limit headers on all responses.
        exempt_paths: Paths to skip rate limiting (e.g. health checks).
    """

    def __init__(
        self,
        rules: list[RateLimitRule] | None = None,
        default_limit: int = 100,
        default_window: float = 60.0,
        response_format: str = "json",
        include_headers: bool = True,
        exempt_paths: list[str] | None = None,
    ):
        if rules:
            self._rules = rules
        else:
            self._rules = [
                RateLimitRule(limit=default_limit, window=default_window),
            ]

        self._response_format = response_format
        self._include_headers = include_headers
        self._exempt_paths: set = set(exempt_paths or ["/health", "/healthz", "/ready"])
        self._store = _BucketStore()
        self._warned_missing_identity = False

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        # Skip exempt paths
        if request.path in self._exempt_paths:
            return await next_handler(request, ctx)

        # Skip if route opted out
        if request.state.get("rate_limit_skip"):
            return await next_handler(request, ctx)

        # Evaluate rules
        for rule in self._rules:
            if not rule.matches(request):
                continue

            key = rule.key_func(request)
            if key is None:
                if rule.requires_identity and not self._warned_missing_identity:
                    # Ordering bug, not a normal miss: an identity rule that never
                    # sees an identity silently disables itself on every request.
                    self._warned_missing_identity = True
                    logger.warning(
                        "Rate-limit rule requires an authenticated identity but none was found on "
                        "request.state. The rate-limit middleware is most likely registered before "
                        "the auth middleware, which disables this rule entirely. Register it at a "
                        "priority greater than the auth middleware's (default 15)."
                    )
                continue  # Rule doesn't apply (e.g. no user ID)

            # Scope the key to the rule
            bucket_key = f"{rule.scope}:{key}"

            # Get or create bucket
            bucket = self._store.get_or_create(
                bucket_key,
                lambda: self._create_bucket(rule),
            )

            allowed, retry_after = bucket.consume()

            if not allowed:
                return self._rate_limited_response(rule, bucket, retry_after)

            # Add rate-limit headers for the first matching rule
            if self._include_headers:
                request.state["_ratelimit_rule"] = rule
                request.state["_ratelimit_bucket"] = bucket

        # Proceed to handler
        response = await next_handler(request, ctx)

        # Attach rate-limit headers
        if self._include_headers:
            rule = request.state.get("_ratelimit_rule")
            bucket = request.state.get("_ratelimit_bucket")
            if rule and bucket:
                self._apply_headers(response, rule, bucket)

        return response

    def _create_bucket(self, rule: RateLimitRule) -> Any:
        if rule.algorithm == "token_bucket":
            capacity = rule.burst if rule.burst is not None else rule.limit
            refill_rate = rule.limit / rule.window
            return _TokenBucket(capacity=capacity, refill_rate=refill_rate)
        else:
            return _SlidingWindowCounter(
                window_size=rule.window,
                max_requests=rule.limit,
            )

    def _rate_limited_response(self, rule: RateLimitRule, bucket: Any, retry_after: float) -> Response:
        # Create a RateLimitExceededFault for ecosystem integration.
        # The fault is attached to the response but NOT raised -- the middleware
        # returns a 429 response directly to avoid interrupting the pipeline.
        fault = RateLimitExceededFault(
            limit=rule.limit,
            window=rule.window,
            retry_after=retry_after,
        )

        headers = {
            "retry-after": str(int(math.ceil(retry_after))),
            "x-ratelimit-limit": str(rule.limit),
            "x-ratelimit-remaining": "0",
            "x-fault-code": fault.code,
        }

        if hasattr(bucket, "reset_time"):
            headers["x-ratelimit-reset"] = str(int(bucket.reset_time))

        if self._response_format == "json":
            resp = Response.json(
                {
                    "error": "Too Many Requests",
                    "code": fault.code,
                    "message": fault.message,
                    "retry_after": int(math.ceil(retry_after)),
                },
                status=429,
                headers=headers,
            )
        else:
            resp = Response(
                b"Rate limit exceeded",
                status=429,
                headers={**headers, "content-type": "text/plain"},
            )

        # Attach fault to response for observability / fault-engine integration
        resp._fault = fault
        return resp

    def _apply_headers(self, response: Response, rule: RateLimitRule, bucket: Any) -> None:
        remaining = bucket.remaining if hasattr(bucket, "remaining") else 0
        response.headers["x-ratelimit-limit"] = str(rule.limit)
        response.headers["x-ratelimit-remaining"] = str(max(0, remaining))
        if hasattr(bucket, "reset_time"):
            response.headers["x-ratelimit-reset"] = str(int(bucket.reset_time))


__all__ = [
    "RateLimitMiddleware",
    "RateLimitRule",
    "ip_key_extractor",
    "api_key_extractor",
    "user_key_extractor",
]
