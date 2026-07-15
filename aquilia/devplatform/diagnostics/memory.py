"""
aquilia.devplatform.diagnostics.memory — tracemalloc-based memory tracker.

Captures RSS and allocation deltas per request and at configured intervals.
Flags potential memory leaks when allocations grow consistently over snapshots.
"""

from __future__ import annotations

import logging
import threading
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any

from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.faults import WorkerFault, report_fault

logger = logging.getLogger("aquilia.devplatform.diagnostics.memory")


@dataclass
class MemorySnapshot:
    """Point-in-time allocation snapshot."""

    timestamp: float
    rss_bytes: int
    top_allocations: list[dict[str, Any]] = field(default_factory=list)
    tracemalloc_current: int = 0
    tracemalloc_peak: int = 0


class MemoryUsageTracker(SingletonMixin):
    """
    Singleton memory tracker using tracemalloc.

    Periodically captures allocation snapshots and compares them to detect
    sustained growth patterns that indicate memory leaks.
    """

    def __init__(
        self,
        snapshot_interval_s: float = 30.0,
        top_n: int = 20,
        leak_growth_threshold: int = 3,
    ) -> None:
        self._snapshot_interval_s = snapshot_interval_s
        self._top_n = top_n
        self._leak_growth_threshold = leak_growth_threshold
        self._snapshots: list[MemorySnapshot] = []
        self._lock = threading.Lock()
        self._running = False
        self._owns_tracemalloc = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Enable tracemalloc and start the background snapshot thread.

        If tracemalloc was already tracing when we started (e.g. another
        subsystem or the user enabled it), we record that so :meth:`stop` won't
        yank it out from under them — we only stop tracemalloc if we started it.
        """
        if self._running:
            return
        self._owns_tracemalloc = not tracemalloc.is_tracing()
        if self._owns_tracemalloc:
            tracemalloc.start(10)
        self._running = True
        self._thread = threading.Thread(
            target=self._snapshot_loop,
            name="adp-memory-tracker",
            daemon=True,
        )
        self._thread.start()
        logger.info("ADP memory tracker started (interval=%ss)", self._snapshot_interval_s)

    def stop(self) -> None:
        """Stop the snapshot thread and disable tracemalloc if we started it."""
        if not self._running:
            return
        self._running = False
        thread = self._thread
        self._thread = None
        # Join the snapshot thread so no snapshot runs after stop() returns.
        # It sleeps up to interval seconds, so bound the wait generously but
        # finitely and never join ourselves.
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=min(self._snapshot_interval_s + 1.0, 5.0))
        if self._owns_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
        self._owns_tracemalloc = False
        logger.info("ADP memory tracker stopped.")

    def _snapshot_loop(self) -> None:
        # Sleep in short slices so stop() can join the thread promptly instead
        # of waiting a whole snapshot interval (which may be tens of seconds).
        while self._running:
            waited = 0.0
            while waited < self._snapshot_interval_s and self._running:
                slice_s = min(0.25, self._snapshot_interval_s - waited)
                time.sleep(slice_s)
                waited += slice_s
            if self._running:
                self._take_snapshot()

    def _take_snapshot(self) -> None:
        try:
            snap = tracemalloc.take_snapshot()
            current, peak = tracemalloc.get_traced_memory()

            top_stats = snap.statistics("lineno")
            top_allocs = []
            for stat in top_stats[: self._top_n]:
                top_allocs.append(
                    {
                        "filename": stat.traceback[0].filename if stat.traceback else "?",
                        "lineno": stat.traceback[0].lineno if stat.traceback else 0,
                        "size_bytes": stat.size,
                        "count": stat.count,
                    }
                )

            rss = self._get_rss()
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                rss_bytes=rss,
                top_allocations=top_allocs,
                tracemalloc_current=current,
                tracemalloc_peak=peak,
            )

            with self._lock:
                self._snapshots.append(snapshot)
                # Keep last 60 snapshots (30-min window at 30s interval)
                if len(self._snapshots) > 60:
                    self._snapshots.pop(0)

            self._check_for_leaks()

        except Exception as exc:
            report_fault(WorkerFault(f"memory snapshot failed: {exc}"))

    def _get_rss(self) -> int:
        try:
            import psutil

            return psutil.Process().memory_info().rss
        except ImportError:
            return 0

    def _check_for_leaks(self) -> None:
        """Warn if RSS has grown monotonically over recent snapshots."""
        with self._lock:
            if len(self._snapshots) < self._leak_growth_threshold + 1:
                return
            recent = self._snapshots[-self._leak_growth_threshold - 1 :]
        rss_values = [s.rss_bytes for s in recent]
        if all(rss_values[i] < rss_values[i + 1] for i in range(len(rss_values) - 1)):
            growth_mb = (rss_values[-1] - rss_values[0]) / 1024 / 1024
            logger.warning(
                "ADP potential memory leak detected: RSS grew %.2f MB over %d snapshots.",
                growth_mb,
                len(recent),
            )

    def get_latest_snapshot(self) -> MemorySnapshot | None:
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_rss_delta(self, before_rss: int) -> int:
        """Return current RSS minus a baseline captured before the request."""
        return self._get_rss() - before_rss

    def capture_rss(self) -> int:
        return self._get_rss()
