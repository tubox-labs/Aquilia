"""
AquilaVectorDB — Dedicated thread pool.

elips is a synchronous C++ extension. Every hot binding releases the GIL
(``place``, ``seek``, ``scan``, ``commit``, ``vacuum``, ``quantize``), so
offloading to threads yields real parallelism rather than merely non-blocking
syntax — which is what makes the async facade in :mod:`aquilia.vectordb.engine`
honest rather than cosmetic.

Structurally a sibling of :class:`aquilia.filesystem._pool.FileSystemPool`, and
separate from it for the same reason it is separate from the default executor:
a long ``rebuild_index()`` must not starve unrelated ``run_in_executor``
callers, and ``aquilia-vdb`` thread names make a stalled vector operation
identifiable in a stack dump.

Sizing
------

The default of 4 workers is not a throughput knob. elips is single-writer per
directory and takes a ``shared_mutex`` per vault, so writes serialize inside C++
however many threads submit them; a larger pool buys nothing for writes and adds
contention. Reads *do* parallelize (shared lock plus released GIL), and that is
what the 4 is for.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

logger = logging.getLogger("aquilia.vectordb.pool")

T = TypeVar("T")

#: Default worker count. See the sizing note in the module docstring.
DEFAULT_POOL_THREADS = 4


class VectorPool:
    """
    Dedicated thread pool for blocking elips operations.

    Created once at subsystem startup and shared by every vector engine for the
    lifetime of the application.

    Args:
        max_workers: Thread count. Defaults to :data:`DEFAULT_POOL_THREADS`.
    """

    __slots__ = ("_max_workers", "_executor", "_active_count", "_peak_active", "_submissions", "_initialized")

    def __init__(self, max_workers: int = DEFAULT_POOL_THREADS) -> None:
        self._max_workers = max(1, int(max_workers))
        self._executor: ThreadPoolExecutor | None = None
        self._active_count = 0
        self._peak_active = 0
        self._submissions = 0
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Whether the pool has been created."""
        return self._initialized

    @property
    def max_workers(self) -> int:
        """Configured thread count."""
        return self._max_workers

    @property
    def active_count(self) -> int:
        """Operations currently executing in the pool."""
        return self._active_count

    @property
    def peak_active(self) -> int:
        """High-water mark of concurrent operations."""
        return self._peak_active

    @property
    def submissions(self) -> int:
        """Total operations submitted since initialization."""
        return self._submissions

    def initialize(self) -> None:
        """
        Create the thread pool.

        Idempotent — repeat calls are no-ops, so tests and the subsystem may
        both call it without coordinating.
        """
        if self._initialized:
            return
        self._executor = ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="aquilia-vdb",
        )
        self._initialized = True

    async def run(self, fn: Callable[..., T], *args: Any) -> T:
        """
        Execute a blocking callable in the dedicated pool.

        The single primitive every elips call flows through.

        Args:
            fn: Blocking callable.
            *args: Positional arguments for ``fn``. Use ``functools.partial``
                for keyword arguments — ``run_in_executor`` takes none.

        Returns:
            Whatever ``fn`` returns.
        """
        if not self._initialized or self._executor is None:
            # Auto-initialize so direct engine use in tests needs no ceremony.
            self.initialize()

        loop = asyncio.get_running_loop()
        self._submissions += 1
        self._active_count += 1
        if self._active_count > self._peak_active:
            self._peak_active = self._active_count
        try:
            return await loop.run_in_executor(self._executor, fn, *args)
        finally:
            self._active_count -= 1

    async def shutdown(self, timeout: float = 10.0) -> None:
        """
        Drain and shut down the pool.

        Args:
            timeout: Seconds to wait for in-flight operations. On expiry the
                executor is torn down with ``cancel_futures=True``.

        Notes:
            The timeout defaults higher than the filesystem pool's because a
            vector ``compact()`` or ``rebuild_index()`` legitimately runs for
            seconds; cutting one short would leave the index mid-rewrite.
        """
        if not self._initialized or self._executor is None:
            return

        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                # shutdown(wait=True) blocks its calling thread, so it runs on
                # the default executor to keep the event loop responsive.
                loop.run_in_executor(None, self._executor.shutdown, True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Vector pool shutdown timed out after %.1fs, forcing", timeout)
            self._executor.shutdown(wait=False, cancel_futures=True)

        self._executor = None
        self._initialized = False

    def stats(self) -> dict[str, Any]:
        """Return pool counters for health and diagnostics."""
        return {
            "max_workers": self._max_workers,
            "active": self._active_count,
            "peak_active": self._peak_active,
            "submissions": self._submissions,
            "initialized": self._initialized,
        }

    def __repr__(self) -> str:
        state = "initialized" if self._initialized else "stopped"
        return f"<VectorPool {state} workers={self._max_workers} active={self._active_count}>"


__all__ = ["DEFAULT_POOL_THREADS", "VectorPool"]
