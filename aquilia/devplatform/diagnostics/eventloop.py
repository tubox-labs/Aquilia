"""
aquilia.devplatform.diagnostics.eventloop — asyncio event loop health monitor.

Sets loop.slow_callback_duration to flag slow callbacks.
Tracks active, completed, and pending tasks to detect resource leaks.
Publishes slow-callback events to the RuntimeStateStore.
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from aquilia.devplatform.core._base import SingletonMixin

logger = logging.getLogger("aquilia.devplatform.diagnostics.eventloop")

_TOOK_RE = re.compile(r"took\s+([0-9]+\.?[0-9]*)\s+second")


def _parse_took_seconds(message: str) -> float:
    """Extract the duration from asyncio's ``... took N seconds`` slow-callback
    message. Returns ``0.0`` if the pattern is absent."""
    m = _TOOK_RE.search(message)
    if not m:
        return 0.0
    try:
        return float(m.group(1))
    except ValueError:
        return 0.0


@dataclass
class SlowCallbackRecord:
    """Record of a slow event loop callback."""

    handle_repr: str
    duration_s: float
    detected_at: float = field(default_factory=time.time)


class EventLoopMonitor(SingletonMixin):
    """
    Monitors the asyncio event loop for slow callbacks and task saturation.

    Singleton — obtain via EventLoopMonitor.get_instance().
    """

    _SLOW_THRESHOLD_S: float = 0.010  # 10ms — matches loop.slow_callback_duration

    def __init__(self) -> None:
        self._slow_callbacks: list[SlowCallbackRecord] = []
        self._lock = threading.Lock()
        self._original_slow_duration: float | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._monitor_task: asyncio.Task[Any] | None = None
        self._original_handler: Any = None
        self._our_handler: Any = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Install slow-callback detection on the given event loop."""
        if self._running:
            return
        self._loop = loop
        self._running = True

        # Lower the threshold for slow callback warnings
        self._original_slow_duration = loop.slow_callback_duration
        loop.slow_callback_duration = self._SLOW_THRESHOLD_S

        # Patch exception handler to capture slow-callback info. Keep a
        # reference to the prior handler so stop() can restore it exactly.
        original_handler = loop.get_exception_handler()
        self._original_handler = original_handler

        def adp_exception_handler(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
            msg = context.get("message", "")
            if "Executing" in msg and "took" in msg:
                # asyncio formats slow callbacks as
                #   "Executing <Handle ...> took 0.123 seconds"
                # so the duration is parsed out of the message text.
                rec = SlowCallbackRecord(
                    handle_repr=repr(context.get("handle", "unknown"))[:200],
                    duration_s=_parse_took_seconds(msg),
                )
                with self._lock:
                    self._slow_callbacks.append(rec)
                    if len(self._slow_callbacks) > 200:
                        self._slow_callbacks.pop(0)
                logger.warning("ADP slow callback detected: %s (%.1fms)", rec.handle_repr[:80], rec.duration_s * 1000)
            elif original_handler:
                original_handler(loop, context)
            else:
                loop.default_exception_handler(context)

        self._our_handler = adp_exception_handler
        loop.set_exception_handler(adp_exception_handler)
        logger.info("ADP event-loop monitor active (slow threshold=%dms)", int(self._SLOW_THRESHOLD_S * 1000))

    def stop(self) -> None:
        """Restore the original exception handler and slow-callback duration."""
        self._running = False
        loop = self._loop
        if loop is not None:
            # Restore slow_callback_duration.
            if self._original_slow_duration is not None:
                try:
                    loop.slow_callback_duration = self._original_slow_duration
                except Exception:
                    pass
            # Restore the exception handler ONLY if ours is still installed —
            # if something else replaced it after us, clobbering it would be
            # worse than leaving it. (asyncio has no handler stack.)
            try:
                if loop.get_exception_handler() is self._our_handler:
                    loop.set_exception_handler(self._original_handler)
            except Exception:
                pass
        self._original_slow_duration = None
        self._our_handler = None
        self._original_handler = None
        self._loop = None
        logger.info("ADP event-loop monitor stopped.")

    def get_slow_callbacks(self, limit: int = 50) -> list[SlowCallbackRecord]:
        with self._lock:
            return list(self._slow_callbacks[-limit:])

    def get_task_summary(self) -> dict[str, int]:
        """Return count of pending and running asyncio tasks."""
        try:
            all_tasks = asyncio.all_tasks(self._loop)
            done = sum(1 for t in all_tasks if t.done())
            pending = len(all_tasks) - done
            return {"total": len(all_tasks), "pending": pending, "done": done}
        except Exception:
            return {"total": 0, "pending": 0, "done": 0}
