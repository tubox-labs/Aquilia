"""Per-middleware timing and call counters.

The second implementation of :class:`~aquilia.middleware.instrumentation.base.Instrument`,
and the proof that the seam works: tracing and metrics coexist without either
one touching the registry or the builder.

Deliberately backend-free. It accumulates into a plain dict that a metrics
exporter, a health endpoint, or a test can read. Wiring it to StatsD or
Prometheus is the application's job.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.middleware.core.descriptor import MiddlewareDescriptor
    from aquilia.middleware.core.types import Handler
    from aquilia.request import Request
    from aquilia.response import Response


@dataclass(slots=True)
class MiddlewareStats:
    """Running totals for one middleware."""

    calls: int = 0
    errors: int = 0
    total_ms: float = 0.0

    @property
    def mean_ms(self) -> float:
        return self.total_ms / self.calls if self.calls else 0.0


@dataclass(slots=True)
class MetricsInstrument:
    """Counts calls, errors, and cumulative time per middleware.

    Single-process and lock-free: increments happen on the event loop thread,
    so they are atomic with respect to each other under CPython.
    """

    stats: dict[str, MiddlewareStats] = field(default_factory=dict)

    def wrap(self, descriptor: MiddlewareDescriptor, link: Handler) -> Handler:
        entry = self.stats.setdefault(descriptor.name, MiddlewareStats())

        async def measured(request: Request, ctx: RequestCtx) -> Response:
            started = time.monotonic()
            try:
                return await link(request, ctx)
            except BaseException:
                entry.errors += 1
                raise
            finally:
                entry.calls += 1
                entry.total_ms += (time.monotonic() - started) * 1000.0

        measured.__name__ = f"measured_{descriptor.name}"
        return measured

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        """Point-in-time copy, safe to serialize."""
        return {
            name: {
                "calls": s.calls,
                "errors": s.errors,
                "total_ms": round(s.total_ms, 3),
                "mean_ms": round(s.mean_ms, 4),
            }
            for name, s in self.stats.items()
        }

    def reset(self) -> None:
        self.stats.clear()


__all__ = ["MetricsInstrument", "MiddlewareStats"]
