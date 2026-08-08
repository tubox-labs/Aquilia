"""SocketMetricsMiddleware — in-process counters and latency percentiles.

Deliberately dependency-free: counters in a dict, latencies in a bounded deque.
No Prometheus client, no push gateway. ``snapshot()`` returns a plain dict that an
exporter, a health endpoint, or the admin dashboard can read.
"""

from __future__ import annotations

import logging
import time
from collections import Counter, deque
from typing import TYPE_CHECKING, Any

from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import ConnectHandler, MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope

    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.metrics")

DEFAULT_LATENCY_WINDOW = 1000


class SocketMetricsMiddleware(SocketMiddleware):
    """
    Counts connections and messages, and tracks per-event latency.

    Registered at **priority 6** — inside logging, outside the security tier, so
    latency covers validation, rate limiting, auth, and the handler.

    Latency is kept in a fixed-size ring per event, so memory is bounded by
    ``latency_window x distinct events`` regardless of traffic. Percentiles are
    computed over that window, which makes them recent-history percentiles rather
    than all-time ones.

    ``ponytail: per-process counters, no aggregation across workers. Point
    snapshot() at a real metrics backend if you need fleet-wide numbers.``

    Args:
        latency_window: Samples retained per event.
        track_events: Optional whitelist of events to time. Unlisted events are
            still counted, just not timed — useful when one high-volume event
            would otherwise dominate the rings.
    """

    def __init__(
        self,
        *,
        latency_window: int = DEFAULT_LATENCY_WINDOW,
        track_events: list[str] | None = None,
    ):
        self.latency_window = latency_window
        self.track_events = set(track_events) if track_events else None

        self.connections_opened = 0
        self.connections_closed = 0
        self.messages_total = 0
        self.errors_total = 0
        self.events: Counter[str] = Counter()
        self.disconnect_reasons: Counter[str] = Counter()
        self._latencies: dict[str, deque[float]] = {}

    @property
    def connections_active(self) -> int:
        return self.connections_opened - self.connections_closed

    async def on_connect(self, ctx: SocketCtx, next_handler: ConnectHandler) -> None:
        self.connections_opened += 1
        try:
            await next_handler(ctx)
        except Exception:
            # A rejected handshake never disconnects, so without this the opened
            # counter would drift permanently above closed.
            self.connections_closed += 1
            self.errors_total += 1
            raise

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        self.messages_total += 1
        self.events[envelope.event] += 1

        t0 = time.monotonic()
        try:
            return await next_handler(envelope, ctx)
        except Exception:
            self.errors_total += 1
            raise
        finally:
            # Timed in `finally` so a failed message contributes to latency too;
            # excluding failures makes a chain that fails slowly look healthy.
            if self.track_events is None or envelope.event in self.track_events:
                self._record(envelope.event, (time.monotonic() - t0) * 1000.0)

    async def on_disconnect(self, ctx: SocketCtx, reason: str | None) -> None:
        self.connections_closed += 1
        self.disconnect_reasons[reason or "unknown"] += 1

    def _record(self, event: str, duration_ms: float) -> None:
        ring = self._latencies.get(event)
        if ring is None:
            ring = deque(maxlen=self.latency_window)
            self._latencies[event] = ring
        ring.append(duration_ms)

    def snapshot(self) -> dict[str, Any]:
        """Current metrics as a plain dict."""
        return {
            "connections": {
                "opened": self.connections_opened,
                "closed": self.connections_closed,
                "active": self.connections_active,
            },
            "messages": {
                "total": self.messages_total,
                "errors": self.errors_total,
                "by_event": dict(self.events),
            },
            "disconnect_reasons": dict(self.disconnect_reasons),
            "latency_ms": {event: self._percentiles(ring) for event, ring in self._latencies.items()},
        }

    @staticmethod
    def _percentiles(samples: deque[float]) -> dict[str, float]:
        if not samples:
            return {}
        ordered = sorted(samples)
        n = len(ordered)

        def pct(p: float) -> float:
            # Nearest-rank; index clamped so p=1.0 lands on the last element.
            return round(ordered[min(int(p * n), n - 1)], 3)

        return {
            "count": n,
            "p50": pct(0.50),
            "p95": pct(0.95),
            "p99": pct(0.99),
            "max": round(ordered[-1], 3),
        }

    def reset(self) -> None:
        """Zero every counter. Intended for tests and manual dev inspection."""
        self.connections_opened = 0
        self.connections_closed = 0
        self.messages_total = 0
        self.errors_total = 0
        self.events.clear()
        self.disconnect_reasons.clear()
        self._latencies.clear()


__all__ = ["SocketMetricsMiddleware", "DEFAULT_LATENCY_WINDOW"]
