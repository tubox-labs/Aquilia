"""
Inference Executor -- offloads blocking inference to thread/process pools.

Aquilia is async-native.  Model inference (PyTorch ``forward()``,
scikit-learn ``predict()``, ONNX ``run()`` …) is typically CPU/GPU-bound
and must not run on the asyncio event loop.

The ``InferenceExecutor`` wraps a ``concurrent.futures`` pool and exposes
an async ``submit()`` that runs any callable off-loop, returning a
coroutine the caller can ``await``.

Features:
- Configurable pool type (thread or process) and worker count
- Graceful shutdown with drain timeout
- Active-task counter for health/metrics
- Device-aware worker allocation when paired with ``DeviceManager``
- Async context manager support

Usage::

    executor = InferenceExecutor(max_workers=4)
    await executor.start()

    result = await executor.submit(model.forward, input_tensor)

    await executor.shutdown()
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger("aquilia.mlops.runtime.executor")

T = TypeVar("T")


class PoolKind(str, Enum):
    """Executor pool types."""
    THREAD = "thread"
    PROCESS = "process"


class InferenceExecutor:
    """
    Async-compatible executor for CPU/GPU-bound inference work.

    Wraps ``ThreadPoolExecutor`` (default) or ``ProcessPoolExecutor``
    and provides an ``await``-able ``submit()`` that keeps the event
    loop responsive.
    """

    __slots__ = (
        "_pool",
        "_pool_kind",
        "_max_workers",
        "_active",
        "_total_submitted",
        "_total_completed",
        "_total_failed",
        "_total_time_ms",
        "_started",
        "_shutdown_event",
        "_lock",
    )

    def __init__(
        self,
        max_workers: int = 4,
        pool_kind: PoolKind = PoolKind.THREAD,
    ) -> None:
        self._pool_kind = pool_kind
        self._max_workers = max(1, max_workers)
        self._pool: Optional[concurrent.futures.Executor] = None
        self._active: int = 0
        self._total_submitted: int = 0
        self._total_completed: int = 0
        self._total_failed: int = 0
        self._total_time_ms: float = 0.0
        self._started: bool = False
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        """Create the underlying executor pool."""
        if self._started:
            return

        if self._pool_kind == PoolKind.PROCESS:
            self._pool = concurrent.futures.ProcessPoolExecutor(
                max_workers=self._max_workers,
            )
        else:
            self._pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="aq-infer",
            )

        self._started = True

    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shut down the executor.

        Waits up to ``timeout`` seconds for in-flight tasks to complete,
        then forcefully shuts down.
        """
        if not self._started or self._pool is None:
            return

        self._shutdown_event.set()

        # Wait for active tasks to drain
        deadline = time.monotonic() + timeout
        while self._active > 0 and time.monotonic() < deadline:
            await asyncio.sleep(0.05)

        cancel = self._active > 0
        self._pool.shutdown(wait=not cancel, cancel_futures=cancel)
        self._pool = None
        self._started = False

        if cancel:
            logger.warning(
                "InferenceExecutor force-shutdown with %d active tasks", self._active,
            )
        else:
            pass

    # ── Submission ───────────────────────────────────────────────────

    async def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Submit a blocking callable and return its result asynchronously.

        The callable runs inside the thread/process pool while the event
        loop remains responsive.

        Raises:
            RuntimeError: If the executor is not started or is shutting down.
            Exception: Re-raises any exception from ``fn``.
        """
        if not self._started or self._pool is None:
            raise RuntimeError("InferenceExecutor not started; call start() first")

        if self._shutdown_event.is_set():
            raise RuntimeError("InferenceExecutor is shutting down")

        loop = asyncio.get_running_loop()

        with self._lock:
            self._active += 1
            self._total_submitted += 1

        start = time.monotonic()
        try:
            if kwargs:
                # concurrent.futures doesn't support kwargs directly
                result = await loop.run_in_executor(
                    self._pool,
                    lambda: fn(*args, **kwargs),
                )
            else:
                result = await loop.run_in_executor(self._pool, fn, *args)

            elapsed = (time.monotonic() - start) * 1000
            with self._lock:
                self._total_completed += 1
                self._total_time_ms += elapsed

            return result

        except Exception:
            with self._lock:
                self._total_failed += 1
            raise

        finally:
            with self._lock:
                self._active -= 1

    # ── Context Manager ──────────────────────────────────────────────

    async def __aenter__(self) -> "InferenceExecutor":
        await self.start()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.shutdown()

    # ── Observability ────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._started and not self._shutdown_event.is_set()

    @property
    def active_tasks(self) -> int:
        return self._active

    @property
    def max_workers(self) -> int:
        return self._max_workers

    def metrics(self) -> dict:
        """Return executor metrics for health/monitoring endpoints."""
        avg_ms = (
            self._total_time_ms / self._total_completed
            if self._total_completed > 0 else 0.0
        )
        return {
            "pool_kind": self._pool_kind.value,
            "max_workers": self._max_workers,
            "active_tasks": self._active,
            "total_submitted": self._total_submitted,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
            "avg_execution_ms": round(avg_ms, 2),
            "is_running": self.is_running,
        }
