"""
Filesystem Thread Pool — Dedicated executor for blocking file I/O.

Isolates file operations from the default asyncio executor to prevent
thread starvation under high I/O load.  Inspired by Tokio's dedicated
blocking pool and Node.js libuv's configurable thread pool.

Design:
    - ``ThreadPoolExecutor`` with ``thread_name_prefix="aquilia-fs"``
    - Configurable min/max threads via ``FileSystemConfig``
    - Graceful shutdown with configurable drain timeout
    - Metrics integration for pool utilization tracking

Usage::

    pool = FileSystemPool(config)
    pool.initialize()

    data = await pool.run(Path.read_bytes, some_path)

    await pool.shutdown()
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

from ._config import FileSystemConfig
from ._metrics import FileSystemMetrics

logger = logging.getLogger("aquilia.filesystem.pool")

T = TypeVar("T")


class FileSystemPool:
    """
    Dedicated thread pool for filesystem operations.

    Wraps ``concurrent.futures.ThreadPoolExecutor`` with:
    - Lifecycle management (initialize/shutdown)
    - Automatic loop resolution
    - Metrics tracking
    - Named threads for debugging

    This pool is created once during server startup and shared by all
    filesystem operations for the lifetime of the application.
    """

    __slots__ = (
        "_config",
        "_executor",
        "_metrics",
        "_active_count",
        "_initialized",
    )

    def __init__(
        self,
        config: FileSystemConfig | None = None,
        metrics: FileSystemMetrics | None = None,
    ) -> None:
        self._config = config or FileSystemConfig()
        self._executor: ThreadPoolExecutor | None = None
        self._metrics = metrics
        self._active_count = 0
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Whether the pool has been initialized."""
        return self._initialized

    @property
    def active_count(self) -> int:
        """Number of currently active pool operations."""
        return self._active_count

    def initialize(self) -> None:
        """
        Create the thread pool.

        Called during server startup.  Safe to call multiple times
        (subsequent calls are no-ops).
        """
        if self._initialized:
            return

        max_workers = self._config.effective_max_pool_threads()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="aquilia-fs",
        )
        self._initialized = True

    async def run(self, fn: Callable[..., T], *args: Any) -> T:
        """
        Execute a blocking function in the dedicated pool.

        This is the core primitive.  All file I/O ultimately flows
        through this method.

        Args:
            fn: A blocking callable (e.g. ``Path.read_bytes``).
            *args: Arguments passed to ``fn``.

        Returns:
            The result of ``fn(*args)``.

        Raises:
            RuntimeError: If the pool is not initialized.
        """
        if not self._initialized or self._executor is None:
            # Auto-initialize for convenience (e.g. in tests)
            self.initialize()

        loop = asyncio.get_running_loop()

        # Track metrics
        if self._metrics:
            self._metrics.pool_submissions += 1

        self._active_count += 1
        if self._metrics and self._active_count > self._metrics.pool_peak_active:
            self._metrics.pool_peak_active = self._active_count

        try:
            result = await loop.run_in_executor(self._executor, fn, *args)
            return result
        finally:
            self._active_count -= 1

    async def shutdown(self, timeout: float = 5.0) -> None:
        """
        Drain and shut down the thread pool.

        Called during server shutdown.  Waits for in-flight operations
        to complete up to ``timeout`` seconds, then cancels remaining.

        Args:
            timeout: Maximum seconds to wait for drain.
        """
        if not self._initialized or self._executor is None:
            return

        # ThreadPoolExecutor.shutdown(wait=True) blocks the calling thread,
        # so we run it in a thread to keep the event loop responsive.
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,  # Use default pool for shutdown call
                    self._executor.shutdown,
                    True,  # wait=True
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "FileSystem pool shutdown timed out after %.1fs, forcing",
                timeout,
            )
            self._executor.shutdown(wait=False, cancel_futures=True)

        self._executor = None
        self._initialized = False
