"""
Transaction & Savepoint — Async context managers for transaction control.

Provides:
    - ``TransactionContext``: ``async with conn.transaction(mode="IMMEDIATE")``
    - ``SavepointContext``:   ``async with txn.savepoint("sp1")``

Both context managers handle commit/rollback automatically and support
cooperative cancellation (rollback on ``CancelledError``).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ._connection import AsyncConnection
    from ._metrics import SqliteMetrics

logger = logging.getLogger("aquilia.sqlite.transaction")

__all__ = ["TransactionContext", "SavepointContext"]


class TransactionContext:
    """
    Async context manager for a database transaction.

    Usage::

        async with conn.transaction(mode="IMMEDIATE") as txn:
            await conn.execute("INSERT INTO users (name) VALUES (?)", ["Alice"])
            async with txn.savepoint("sp1") as sp:
                await conn.execute("INSERT INTO logs (msg) VALUES (?)", ["created"])
            # savepoint released
        # transaction committed

    On exception (including ``CancelledError``), the transaction is rolled back.
    """

    __slots__ = ("_conn", "_mode", "_metrics", "_t0")

    def __init__(
        self,
        conn: AsyncConnection,
        mode: str = "DEFERRED",
        metrics: SqliteMetrics | None = None,
    ) -> None:
        self._conn = conn
        self._mode = mode
        self._metrics = metrics
        self._t0: int = 0

    async def __aenter__(self) -> TransactionContext:
        self._t0 = time.monotonic_ns()
        await self._conn.begin(mode=self._mode)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        elapsed = time.monotonic_ns() - self._t0

        if exc_type is not None:
            # Exception (including CancelledError) → rollback
            try:
                await self._conn.rollback()
            except Exception:
                logger.warning("Rollback failed during exception handling", exc_info=True)
            if self._metrics:
                self._metrics.record_transaction(elapsed, committed=False)
            return  # Re-raise the original exception

        try:
            await self._conn.commit()
            if self._metrics:
                self._metrics.record_transaction(elapsed, committed=True)
        except Exception:
            try:
                await self._conn.rollback()
            except Exception:
                logger.warning("Rollback after commit failure", exc_info=True)
            if self._metrics:
                self._metrics.record_transaction(elapsed, committed=False)
            raise

    def savepoint(self, name: str) -> SavepointContext:
        """Create a nested savepoint within this transaction."""
        return SavepointContext(self._conn, name, metrics=self._metrics)


class SavepointContext:
    """
    Async context manager for a savepoint.

    Usage::

        async with txn.savepoint("sp1") as sp:
            await conn.execute("INSERT ...")
        # savepoint released on success, rolled back on exception
    """

    __slots__ = ("_conn", "_name", "_metrics", "_t0")

    def __init__(
        self,
        conn: AsyncConnection,
        name: str,
        metrics: SqliteMetrics | None = None,
    ) -> None:
        self._conn = conn
        self._name = name
        self._metrics = metrics
        self._t0: int = 0

    async def __aenter__(self) -> SavepointContext:
        self._t0 = time.monotonic_ns()
        await self._conn.savepoint(self._name)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None:
            try:
                await self._conn.rollback_to_savepoint(self._name)
            except Exception:
                logger.warning(
                    "Rollback to savepoint %r failed", self._name,
                    exc_info=True,
                )
            return  # Re-raise original

        try:
            await self._conn.release_savepoint(self._name)
        except Exception:
            try:
                await self._conn.rollback_to_savepoint(self._name)
            except Exception:
                logger.warning(
                    "Rollback to savepoint %r after release failure",
                    self._name,
                    exc_info=True,
                )
            raise

    async def rollback(self) -> None:
        """Manually rollback to this savepoint."""
        await self._conn.rollback_to_savepoint(self._name)

    async def release(self) -> None:
        """Manually release (commit) this savepoint."""
        await self._conn.release_savepoint(self._name)
