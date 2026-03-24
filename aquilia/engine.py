"""
Engine -- Core runtime primitives for the Aquilia request lifecycle.

This module provides:
- ``RequestCtx``  : The per-request execution context (DI, state, timing).
- ``LifecycleHook``: Typed enum for startup / shutdown / request hooks.
- ``EngineMetrics``: Lightweight counters for in-flight requests and latency.

The controller-layer ``RequestCtx`` (in ``aquilia.controller.base``) extends
this with HTTP-specific accessors (path, method, json, form, render).
This engine-level version is used by middleware, the ASGI adapter, and any
subsystem that needs DI resolution without a full HTTP request object.

Performance (v3 — scalability):
- ``os.urandom(16).hex()`` replaces ``uuid.uuid4().hex`` (~4× faster).
- Metrics tracking moved out of ``__init__`` to avoid double-counting
  when the ASGI adapter also calls ``request_started()``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
)

if TYPE_CHECKING:
    from .typing.container import RequestContainer

from .typing.container import CleanupCallback

logger = logging.getLogger("aquilia.engine")

# Pre-bind for hot-path speed
_urandom = os.urandom


# ---------------------------------------------------------------------------
# Lifecycle hook enum
# ---------------------------------------------------------------------------


class LifecycleHook(Enum):
    """Named lifecycle points that subsystems can subscribe to."""

    BEFORE_REQUEST = auto()
    AFTER_REQUEST = auto()
    ON_ERROR = auto()
    ON_STARTUP = auto()
    ON_SHUTDOWN = auto()


# ---------------------------------------------------------------------------
# Engine-level metrics (lock-free via asyncio-safe counters)
# ---------------------------------------------------------------------------


class EngineMetrics:
    """
    Lightweight in-process metrics for the Aquilia engine.

    Tracks:
    - Total requests processed
    - Currently in-flight requests
    - Total errors
    - Cumulative latency (for mean calculation)

    All counters are ``int`` / ``float`` and only mutated from the
    async event-loop, so no locking is required.
    """

    __slots__ = (
        "total_requests",
        "inflight",
        "total_errors",
        "_cumulative_latency_ms",
    )

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.inflight: int = 0
        self.total_errors: int = 0
        self._cumulative_latency_ms: float = 0.0

    # -- mutation helpers --------------------------------------------------

    def request_started(self) -> None:
        self.total_requests += 1
        self.inflight += 1

    def request_finished(self, latency_ms: float) -> None:
        self.inflight -= 1
        self._cumulative_latency_ms += latency_ms

    def request_errored(self) -> None:
        self.total_errors += 1

    # -- read helpers ------------------------------------------------------

    @property
    def mean_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self._cumulative_latency_ms / self.total_requests

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of current metrics."""
        return {
            "total_requests": self.total_requests,
            "inflight": self.inflight,
            "total_errors": self.total_errors,
            "mean_latency_ms": round(self.mean_latency_ms, 3),
        }

    def __repr__(self) -> str:
        return f"<EngineMetrics requests={self.total_requests} inflight={self.inflight} errors={self.total_errors}>"


# ---------------------------------------------------------------------------
# Singleton metrics instance -- shared by all RequestCtx in the process
# ---------------------------------------------------------------------------

_engine_metrics = EngineMetrics()


def get_engine_metrics() -> EngineMetrics:
    """Return the process-level engine metrics singleton."""
    return _engine_metrics


# ---------------------------------------------------------------------------
# RequestCtx -- per-request execution context
# ---------------------------------------------------------------------------


class RequestCtx:
    """
    Per-request execution context.

    Provides:
    - DI container scoped to the current request
    - Unique ``request_id`` for tracing / correlation
    - Arbitrary ``state`` dict for middleware data-passing
    - High-resolution timing (``started_at``, ``elapsed_ms``)
    - ``_cleanup_callbacks`` for deterministic resource teardown
    - Engine-level metrics tracking (in-flight, latency)

    Usage::

        ctx = RequestCtx(container=request_container)
        service = await ctx.resolve("UserService")
        ctx.state["tenant"] = "acme"
        ...
        await ctx.dispose()  # runs cleanup callbacks + container shutdown
    """

    __slots__ = (
        "container",
        "request_id",
        "state",
        "started_at",
        "_cleanup_callbacks",
        "_disposed",
        "_metrics",
    )

    def __init__(
        self,
        container: RequestContainer,
        request_id: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> None:
        self.container = container
        self.request_id = request_id or _urandom(16).hex()
        self.state: dict[str, Any] = state if state is not None else {}
        self.started_at: float = time.monotonic()
        self._cleanup_callbacks: list[CleanupCallback] = []
        self._disposed: bool = False
        self._metrics: EngineMetrics = _engine_metrics

        # NOTE (v3): metrics.request_started() is NO LONGER called here.
        # The ASGI adapter is the single source of truth for request counting
        # to prevent double-counting when both engine-ctx and ASGI adapter
        # track metrics.  Callers that use engine.RequestCtx directly
        # (outside the ASGI path) should call _metrics.request_started()
        # explicitly if they want in-flight tracking.

    # -- DI resolution -----------------------------------------------------

    async def resolve(self, name: str, optional: bool = False) -> Any:
        """Resolve a dependency from the request-scoped container.

        Args:
            name: Service name or type to resolve.
            optional: If ``True``, return ``None`` instead of raising when
                      the dependency is not registered.
        """
        return await self.container.resolve_async(name, optional=optional)

    def resolve_sync(self, name: str, optional: bool = False) -> Any:
        """Synchronous resolution -- only for sync-safe providers."""
        if hasattr(self.container, "resolve"):
            return self.container.resolve(name, optional=optional)
        from .faults.domains import DIResolutionFault

        raise DIResolutionFault(
            provider=name,
            reason="Synchronous resolution is not supported by this container.",
        )

    # -- State helpers -----------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Shorthand for ``ctx.state.get(key, default)``."""
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Shorthand for ``ctx.state[key] = value``."""
        self.state[key] = value

    # -- Timing ------------------------------------------------------------

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds elapsed since this context was created."""
        return (time.monotonic() - self.started_at) * 1000.0

    # -- Cleanup / disposal ------------------------------------------------

    def add_cleanup(self, callback: CleanupCallback) -> None:
        """Register an async or sync callable to run on ``dispose()``.

        Callbacks execute in LIFO order (last registered runs first).
        """
        self._cleanup_callbacks.append(callback)

    async def dispose(self) -> None:
        """Dispose of the request context.

        1. Runs cleanup callbacks in reverse registration order.
        2. Shuts down the request-scoped DI container.
        3. Records latency in engine metrics.

        Safe to call multiple times -- subsequent calls are no-ops.
        """
        if self._disposed:
            return
        self._disposed = True

        # 1. Cleanup callbacks (LIFO)
        for cb in reversed(self._cleanup_callbacks):
            try:
                result = cb()
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result
            except Exception as exc:
                logger.warning(
                    "Cleanup callback error [request_id=%s]: %s",
                    self.request_id,
                    exc,
                )

        # 2. Container shutdown
        if self.container and hasattr(self.container, "shutdown"):
            try:
                await self.container.shutdown()
            except Exception as exc:
                logger.warning(
                    "Container shutdown error [request_id=%s]: %s",
                    self.request_id,
                    exc,
                )

        # 3. Metrics
        self._metrics.request_finished(self.elapsed_ms)

    # -- Context manager ---------------------------------------------------

    async def __aenter__(self) -> RequestCtx:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self._metrics.request_errored()
        await self.dispose()

    # -- Repr --------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<RequestCtx id={self.request_id!r} elapsed={self.elapsed_ms:.1f}ms disposed={self._disposed}>"
