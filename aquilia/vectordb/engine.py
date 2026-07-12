"""
Aquilia VectorDB engine -- async-safe wrapper around the synchronous Elips bindings.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .configs import ElipsConfig
from .faults import VectorEngineFault

if TYPE_CHECKING:
    import elips

logger = logging.getLogger("aquilia.vectordb.engine")

__all__ = ["ElipsEngine"]


class ElipsEngine:
    """
    Async-safe wrapper around the synchronous Elips Python bindings.

    Elips (like sqlite3) is fully synchronous. Every blocking call is
    dispatched to a thread pool via ``asyncio.to_thread()`` so it never
    blocks the event loop.

    Connection is lazy -- nothing connects until the first operation, or
    until ``await engine.connect()`` is called explicitly.
    """

    def __init__(self, config: ElipsConfig) -> None:
        self._config = config
        self._engine: elips.Engine | None = None
        self._lock = asyncio.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix="aquilia-vectordb",
        )

    async def connect(self) -> None:
        """Open the Elips database. Idempotent and thread-safe."""
        async with self._lock:
            if self._engine is not None:
                return
            import elips

            try:
                self._engine = await asyncio.to_thread(
                    elips.connect,
                    self._config.path,
                    **self._config.to_connect_kwargs(),
                )
                logger.info("Elips connected: %s", self._config.path)
            except Exception as exc:
                raise VectorEngineFault(reason=str(exc), path=self._config.path) from exc

    async def disconnect(self) -> None:
        """Close the Elips database."""
        async with self._lock:
            if self._engine is None:
                return
            await asyncio.to_thread(self._engine.close)
            self._engine = None
            logger.info("Elips disconnected: %s", self._config.path)

    @property
    def is_connected(self) -> bool:
        return self._engine is not None

    async def arena(self, vault_name: str) -> elips.Arena:
        """Return an Arena for *vault_name*, connecting lazily if needed.

        ``Engine.arena()`` is a pure-Python call with no I/O, so it's safe
        to call directly from async code without a thread.
        """
        await self.connect()
        return self._engine.arena(vault_name)

    async def run_sync(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Run a synchronous Elips call in the thread pool.

        Every Arena read/write call must go through this.

        Usage:
            key = await engine.run_sync(arena.write, vector=v, meta=m)
            rows = await engine.run_sync(arena.sweep, where=f, limit=10)
        """
        if kwargs:
            fn = functools.partial(fn, **kwargs)
        return await asyncio.to_thread(fn, *args)

    async def checkpoint(self) -> None:
        """Flush database state to durable storage."""
        if self._engine:
            await asyncio.to_thread(self._engine.checkpoint)

    async def compact(self) -> None:
        """Rebuild indexes and compact the persistent layout."""
        if self._engine:
            await asyncio.to_thread(self._engine.compact)

    async def __aenter__(self) -> ElipsEngine:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.disconnect()
