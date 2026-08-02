"""
aquilia.devplatform.core.runtime — Thread-safe global RuntimeStateStore singleton.

Holds live server metrics: active connections, request counters, event-loop
health, WebSocket registry, DB pool stats, and the rolling request history.

All counters use threading.Lock for thread safety. asyncio tasks update
counters directly from the event loop; Inspector's collector reads these
values without additional locking (eventual-consistency display is fine for
a live debugging surface).
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.core.state import RequestRecord
from aquilia.devplatform.faults import WorkerFault, report_fault


def _safe_call_float(fn: Any) -> float:
    """Invoke an optional telemetry callable, returning ``0.0`` on any failure."""
    if fn is None:
        return 0.0
    try:
        return float(fn())
    except Exception:
        return 0.0


def _safe_call_pair(fn: Any) -> tuple[int, int]:
    """Invoke an optional ``() -> (int, int)`` callable, ``(0, 0)`` on failure."""
    if fn is None:
        return (0, 0)
    try:
        a, b = fn()
        return (int(a), int(b))
    except Exception:
        return (0, 0)


def _safe_rss() -> int:
    """Best-effort process RSS in bytes; ``0`` if the sampler is unavailable."""
    try:
        from aquilia.devplatform.diagnostics.system import read_rss_bytes

        return read_rss_bytes()
    except Exception:
        return 0


@dataclass
class ServerMetrics:
    """Point-in-time snapshot of server health metrics."""

    active_connections: int = 0
    active_websockets: int = 0
    total_requests: int = 0
    total_errors: int = 0
    uptime_s: float = 0.0
    rps_1s: float = 0.0  # requests per second (rolling 1-second window)
    avg_latency_ms: float = 0.0  # exponential moving average
    worker_pid: int = field(default_factory=os.getpid)
    db_pool_active: int = 0
    db_pool_limit: int = 0
    # Extended dashboard telemetry (best-effort; 0 when unavailable)
    cpu_percent: float = 0.0
    rss_bytes: int = 0
    event_loop_lag_ms: float = 0.0
    active_tasks: int = 0
    slow_requests: int = 0  # requests slower than the slow threshold
    error_rate: float = 0.0  # total_errors / total_requests
    background_jobs: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class RuntimeStateStore(SingletonMixin):
    """
    Thread-safe global state store for the ADP.

    Singleton — obtain via RuntimeStateStore.get_instance().
    All fields updated atomically via _lock.
    Consumers (Inspector) read without lock for perf;
    minor inconsistencies in display are acceptable.
    """

    def __init__(self, max_history: int = 500) -> None:
        self._lock = threading.Lock()
        self._max_history = max_history
        self.app: Any = None

        # Counters
        self.active_connections: int = 0
        self.active_websockets: int = 0
        self.total_requests: int = 0
        self.total_errors: int = 0

        # Timing
        self._started_at: float = time.monotonic()

        # Rolling request history (circular)
        self._request_history: deque[RequestRecord] = deque(maxlen=max_history)

        # RPS tracking — timestamps of recent requests in last 1s
        self._recent_request_times: deque[float] = deque(maxlen=10_000)

        # Latency EMA (alpha=0.1, updates with each completed request)
        self._latency_ema_ms: float = 0.0
        self._ema_alpha: float = 0.1

        # Slow-request counter (requests exceeding _slow_threshold_ms)
        self._slow_requests: int = 0
        self._slow_threshold_ms: float = 500.0

        # DB pool snapshot (set by db listener)
        self.db_pool_active: int = 0
        self.db_pool_limit: int = 0

        # Shutdown flag
        self._shutting_down: bool = False

        # Registered request listeners (hooks for plugins)
        self._request_listeners: list[Any] = []

        # External telemetry samplers (attached by the lifespan/UI layer).
        # Each is an optional zero-arg callable returning a float/int; failures
        # are swallowed so telemetry can never break a snapshot read.
        self._cpu_source: Any = None
        self._lag_source: Any = None
        self._task_count_source: Any = None
        self._cache_stats_source: Any = None
        self._job_count_source: Any = None

    def attach_sources(
        self,
        *,
        cpu: Any = None,
        lag: Any = None,
        tasks: Any = None,
        cache_stats: Any = None,
        jobs: Any = None,
    ) -> None:
        """Attach best-effort telemetry callables consumed by :meth:`snapshot`.

        Each argument is a zero-arg callable (or ``None`` to leave unchanged):
        ``cpu`` → float %, ``lag`` → float ms, ``tasks`` → int, ``cache_stats``
        → ``(hits, misses)`` tuple, ``jobs`` → int. Kept as loose callables so
        the runtime store never hard-depends on the diagnostics or task
        subsystems.
        """
        with self._lock:
            if cpu is not None:
                self._cpu_source = cpu
            if lag is not None:
                self._lag_source = lag
            if tasks is not None:
                self._task_count_source = tasks
            if cache_stats is not None:
                self._cache_stats_source = cache_stats
            if jobs is not None:
                self._job_count_source = jobs

    # ── Connection counters ────────────────────────────────────────────────

    def connection_opened(self) -> None:
        """Increment the active HTTP connection counter."""
        with self._lock:
            self.active_connections += 1

    def connection_closed(self) -> None:
        """Decrement the active HTTP connection counter (floored at 0)."""
        with self._lock:
            self.active_connections = max(0, self.active_connections - 1)

    def websocket_opened(self) -> None:
        """Increment the active WebSocket connection counter."""
        with self._lock:
            self.active_websockets += 1

    def websocket_closed(self) -> None:
        """Decrement the active WebSocket connection counter (floored at 0)."""
        with self._lock:
            self.active_websockets = max(0, self.active_websockets - 1)

    # ── Request lifecycle ──────────────────────────────────────────────────

    def record_request(self, record: RequestRecord) -> None:
        """Commit a completed request record and update all derived counters."""
        now = time.monotonic()
        with self._lock:
            self.total_requests += 1
            if record.status_code >= 500:
                self.total_errors += 1
            if record.duration_ms >= self._slow_threshold_ms:
                self._slow_requests += 1

            # RPS window
            self._recent_request_times.append(now)

            # Latency EMA
            if self._latency_ema_ms == 0.0:
                self._latency_ema_ms = record.duration_ms
            else:
                self._latency_ema_ms = (
                    self._ema_alpha * record.duration_ms + (1 - self._ema_alpha) * self._latency_ema_ms
                )

            self._request_history.append(record)

        # Notify listeners outside lock to avoid deadlocks
        for listener in list(self._request_listeners):
            try:
                listener(record)
            except Exception as exc:
                fault = WorkerFault(
                    f"request listener {getattr(listener, '__qualname__', listener)!r} raised: {exc}",
                    metadata={"trace_id": record.trace_id},
                )
                report_fault(fault, app=self.app)

    # ── Metrics snapshot ────────────────────────────────��──────────────────

    def snapshot(self) -> ServerMetrics:
        """Return a fully lock-guarded point-in-time metrics snapshot.

        All counter reads happen under ``_lock`` so a snapshot can never see a
        torn/partially-updated state while another thread mutates counters.
        Optional telemetry sources (CPU, event-loop lag, task/cache/job counts)
        are captured into locals under the lock, then invoked *outside* it —
        each is best-effort and any failure yields a zero reading rather than
        propagating.
        """
        now = time.monotonic()
        with self._lock:
            cutoff = now - 1.0
            rps = sum(1 for t in self._recent_request_times if t >= cutoff)
            active_connections = self.active_connections
            active_websockets = self.active_websockets
            total_requests = self.total_requests
            total_errors = self.total_errors
            latency = self._latency_ema_ms
            slow = self._slow_requests
            db_active = self.db_pool_active
            db_limit = self.db_pool_limit
            started_at = self._started_at
            cpu_src = self._cpu_source
            lag_src = self._lag_source
            task_src = self._task_count_source
            cache_src = self._cache_stats_source
            job_src = self._job_count_source

        cpu = _safe_call_float(cpu_src)
        lag = _safe_call_float(lag_src)
        tasks = int(_safe_call_float(task_src))
        jobs = int(_safe_call_float(job_src))
        cache_hits, cache_misses = _safe_call_pair(cache_src)
        error_rate = (total_errors / total_requests) if total_requests else 0.0

        return ServerMetrics(
            active_connections=active_connections,
            active_websockets=active_websockets,
            total_requests=total_requests,
            total_errors=total_errors,
            uptime_s=now - started_at,
            rps_1s=float(rps),
            avg_latency_ms=latency,
            db_pool_active=db_active,
            db_pool_limit=db_limit,
            cpu_percent=cpu,
            rss_bytes=_safe_rss(),
            event_loop_lag_ms=lag,
            active_tasks=tasks,
            slow_requests=slow,
            error_rate=error_rate,
            background_jobs=jobs,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )

    # ── Request history ────────────────────────────────────────────────────

    def get_recent_requests(self, limit: int = 50) -> list[RequestRecord]:
        with self._lock:
            history = list(self._request_history)
        return history[-limit:]

    def get_request(self, trace_id: str) -> RequestRecord | None:
        with self._lock:
            for record in self._request_history:
                if record.trace_id == trace_id:
                    return record
        return None

    # ── Listeners ─────────────────────────────────────────────────────────

    def add_request_listener(self, listener: Any) -> None:
        """Register a callback fired with each committed ``RequestRecord``."""
        self._request_listeners.append(listener)

    def remove_request_listener(self, listener: Any) -> None:
        """Remove a previously registered request listener (no-op if absent)."""
        if listener in self._request_listeners:
            self._request_listeners.remove(listener)

    # ── Shutdown ───────────────────────────────────────────────────────────

    def set_shutting_down(self) -> None:
        """Mark the server as shutting down (checked by the hot-reload watcher)."""
        self._shutting_down = True

    @property
    def is_shutting_down(self) -> bool:
        """Whether a graceful shutdown is in progress."""
        return self._shutting_down

    @property
    def uptime_s(self) -> float:
        """Seconds elapsed since this store was created (server start)."""
        return time.monotonic() - self._started_at
