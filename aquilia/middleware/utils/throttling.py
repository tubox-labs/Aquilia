"""Rate-limiting algorithms — transport-agnostic leaf module.

The token bucket and sliding-window counter here are pure accounting: they know
about time and counts, nothing about HTTP requests, WebSocket messages, or
Aquilia's fault system. Both the HTTP rate-limit middleware
(:mod:`aquilia.middleware.builtin.rate_limit`) and the WebSocket one
(``aquilia.sockets.middleware.builtin.rate_limit``) call into these, so the two
transports cannot drift in enforcement behaviour.

Import nothing from the rest of the framework here — the value of this module is
that any subsystem can use it without dragging a middleware stack along.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

# Retry-After (seconds) reported for a bucket whose refill rate is zero, i.e.
# one that will never hand out another token on its own.
NEVER_REFILLS_RETRY_AFTER = 3600


class TokenBucket:
    """
    Classic token bucket with lazy refill.

    Attributes:
        capacity: Maximum tokens in bucket.
        refill_rate: Tokens added per second.
        tokens: Current token count.
        last_refill: Timestamp of last refill.
    """

    __slots__ = ("capacity", "refill_rate", "tokens", "last_refill")

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Try to consume tokens.

        Returns:
            (allowed, retry_after_seconds)
        """
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0.0

        # How long until enough tokens are available. A zero refill rate means
        # the bucket never refills (a "block once drained" rule), so report a
        # finite-but-large retry rather than dividing by zero.
        if self.refill_rate <= 0:
            return False, float(NEVER_REFILLS_RETRY_AFTER)
        deficit = tokens - self.tokens
        retry_after = deficit / self.refill_rate
        return False, retry_after

    @property
    def remaining(self) -> int:
        return int(self.tokens)


class SlidingWindowCounter:
    """
    Sliding window counter using two adjacent fixed windows.

    More accurate than fixed windows (no boundary spike) while using
    only O(1) space per key.

    Algorithm:
        weighted_count = prev_count * overlap_ratio + current_count

    Attributes:
        window_size: Window duration in seconds.
        max_requests: Maximum requests per window.
    """

    __slots__ = ("window_size", "max_requests", "_prev_count", "_curr_count", "_prev_start", "_curr_start")

    def __init__(self, window_size: float, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        now = time.monotonic()
        self._curr_start = now
        self._curr_count = 0
        self._prev_start = now - window_size
        self._prev_count = 0

    def consume(self) -> tuple[bool, float]:
        """
        Try to record a request.

        Returns:
            (allowed, retry_after_seconds)
        """
        now = time.monotonic()
        self._advance_windows(now)

        # Calculate weighted count
        elapsed_in_window = now - self._curr_start
        weight = max(0.0, 1.0 - elapsed_in_window / self.window_size)
        weighted = self._prev_count * weight + self._curr_count

        if weighted >= self.max_requests:
            # Estimate when the window will roll enough to allow a request
            retry = self.window_size - elapsed_in_window
            return False, max(0.1, retry)

        self._curr_count += 1
        return True, 0.0

    def _advance_windows(self, now: float) -> None:
        window_end = self._curr_start + self.window_size
        if now >= window_end:
            # How many full windows have passed
            windows_passed = int((now - self._curr_start) / self.window_size)
            if windows_passed >= 2:
                # Both windows expired
                self._prev_count = 0
                self._curr_count = 0
                self._prev_start = now - self.window_size
                self._curr_start = now
            else:
                # Rotate once
                self._prev_count = self._curr_count
                self._prev_start = self._curr_start
                self._curr_count = 0
                self._curr_start = window_end

    @property
    def remaining(self) -> int:
        now = time.monotonic()
        elapsed = now - self._curr_start
        weight = max(0.0, 1.0 - elapsed / self.window_size)
        used = int(self._prev_count * weight + self._curr_count)
        return max(0, self.max_requests - used)

    @property
    def reset_time(self) -> float:
        return self._curr_start + self.window_size


class BucketStore:
    """
    In-memory store for rate-limit buckets with periodic cleanup.

    Entries that haven't been accessed for longer than the idle TTL are evicted
    on a lazy schedule to bound memory growth. Without this, any keying scheme
    with unbounded cardinality (client IP, connection id) leaks for the lifetime
    of the process.

    State is per-process. Under multiple workers each process keeps its own
    buckets, so an effective limit is ``limit × workers`` for any key that is not
    pinned to one worker. A distributed limiter is out of scope here.
    """

    def __init__(self, cleanup_interval: float = 60.0):
        self._buckets: dict[str, Any] = {}
        self._last_access: dict[str, float] = {}
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.monotonic()

    def get_or_create(self, key: str, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        self._last_access[key] = now

        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = factory()
            self._buckets[key] = bucket

        # Lazy cleanup
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup(now)

        return bucket

    def discard(self, key: str) -> None:
        """Drop a bucket immediately.

        Callers that know when a key dies for good — a WebSocket disconnect, say
        — can release the entry now instead of waiting out the idle TTL.
        """
        self._buckets.pop(key, None)
        self._last_access.pop(key, None)

    def _cleanup(self, now: float) -> None:
        self._last_cleanup = now
        # Default 5 minute TTL for idle buckets
        ttl = max(self._cleanup_interval * 5, 300)
        expired = [k for k, t in self._last_access.items() if now - t > ttl]
        for k in expired:
            self._buckets.pop(k, None)
            self._last_access.pop(k, None)


__all__ = [
    "TokenBucket",
    "SlidingWindowCounter",
    "BucketStore",
    "NEVER_REFILLS_RETRY_AFTER",
]
