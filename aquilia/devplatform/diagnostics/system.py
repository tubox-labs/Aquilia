"""
aquilia.devplatform.diagnostics.system — process & event-loop health sampling.

Provides cheap, dependency-optional samplers the dashboard reads each frame:

  * CPU% and RSS via ``psutil`` when installed, degrading to ``resource`` /
    ``/proc/self/statm`` and finally to ``0`` — never raising, never requiring
    an optional dependency.
  * Event-loop lag via an :class:`EventLoopLagSampler` background asyncio task
    that measures the drift between an intended and actual wake-up time. Lag is
    the single best signal that the loop is blocked by synchronous work.

All samplers are best-effort observers: a failure yields a zero/None reading,
not an exception, so the dashboard render loop can never crash on telemetry.
"""

from __future__ import annotations

import asyncio
import os
import time


def read_rss_bytes() -> int:
    """Return current process RSS in bytes, or ``0`` if unobtainable."""
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        pass
    # Linux /proc fallback: statm pages * page size.
    try:
        with open("/proc/self/statm", encoding="ascii") as fh:
            pages = int(fh.readline().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
    except Exception:
        pass
    # POSIX resource fallback (ru_maxrss: KiB on Linux, bytes on macOS).
    try:
        import resource
        import sys

        maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(maxrss if sys.platform == "darwin" else maxrss * 1024)
    except Exception:
        return 0


class CPUSampler:
    """Stateful CPU-percent sampler.

    ``psutil`` is preferred (true per-interval CPU%). Without it we approximate
    from :func:`os.times` process-time deltas across successive reads, divided
    by wall-clock delta and CPU count. Both paths return ``0.0`` on failure.
    """

    def __init__(self) -> None:
        self._proc = None
        try:
            import psutil

            self._proc = psutil.Process()
            # Prime psutil's internal interval baseline.
            self._proc.cpu_percent(None)
        except Exception:
            self._proc = None
        self._last_wall = time.monotonic()
        self._last_cpu = self._process_cpu_seconds()

    @staticmethod
    def _process_cpu_seconds() -> float:
        try:
            t = os.times()
            return float(t.user + t.system + t.children_user + t.children_system)
        except Exception:
            return 0.0

    def sample(self) -> float:
        """Return CPU% since the previous call (0.0 on the first/failed call)."""
        if self._proc is not None:
            try:
                return float(self._proc.cpu_percent(None))
            except Exception:
                return 0.0
        now = time.monotonic()
        cpu = self._process_cpu_seconds()
        wall_delta = now - self._last_wall
        cpu_delta = cpu - self._last_cpu
        self._last_wall = now
        self._last_cpu = cpu
        if wall_delta <= 0:
            return 0.0
        ncpu = os.cpu_count() or 1
        return max(0.0, min(100.0, (cpu_delta / wall_delta) * 100.0 / ncpu))


class EventLoopLagSampler:
    """Background task that measures event-loop scheduling lag.

    Sleeps for a fixed interval and records how much later than intended it
    actually woke up. Sustained lag means the loop is starved by synchronous
    work. Exposes an exponential moving average via :attr:`lag_ms`.
    """

    def __init__(self, interval_s: float = 0.25, ema_alpha: float = 0.3) -> None:
        self._interval = interval_s
        self._alpha = ema_alpha
        self._lag_ms: float = 0.0
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def lag_ms(self) -> float:
        return self._lag_ms

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            self._task = asyncio.get_running_loop().create_task(self._run(), name="adp-loop-lag")
        except RuntimeError:
            # No running loop — sampler stays inert (lag_ms == 0.0).
            self._running = False

    async def _run(self) -> None:
        while self._running:
            start = time.monotonic()
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            actual = time.monotonic() - start
            lag = max(0.0, (actual - self._interval)) * 1000.0
            self._lag_ms = self._alpha * lag + (1 - self._alpha) * self._lag_ms

    def stop(self) -> None:
        self._running = False
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None
