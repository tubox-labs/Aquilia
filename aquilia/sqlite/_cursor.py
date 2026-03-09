"""
Async Cursor — Streaming row iteration over query results.

Wraps ``sqlite3.Cursor`` and dispatches ``fetchone`` / ``fetchmany``
to the thread pool, providing an ``__aiter__`` for streaming large
result sets without loading everything into memory.
"""

from __future__ import annotations

import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Any, AsyncIterator, Optional

from ._rows import Row

__all__ = ["AsyncCursor"]


class AsyncCursor:
    """
    Async wrapper around a ``sqlite3.Cursor``.

    Provides async iteration and explicit fetch methods.  The cursor
    is created by executing a query and can be used to stream rows
    lazily.

    Usage::

        cursor = await conn.cursor("SELECT * FROM users")
        async for row in cursor:
            print(row.name)
        await cursor.close()
    """

    __slots__ = ("_raw", "_executor", "_closed")

    def __init__(
        self,
        raw: sqlite3.Cursor,
        executor: ThreadPoolExecutor,
    ) -> None:
        self._raw = raw
        self._executor = executor
        self._closed = False

    async def _run(self, fn: Any, *args: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, fn, *args)

    async def fetch_one(self) -> Row | None:
        """Fetch the next row, or None if exhausted."""
        return await self._run(self._raw.fetchone)  # type: ignore[return-value]

    async def fetch_many(self, size: int = 100) -> list[Row]:
        """Fetch up to *size* rows."""
        return await self._run(self._raw.fetchmany, size)  # type: ignore[return-value]

    async def fetch_all(self) -> list[Row]:
        """Fetch all remaining rows."""
        return await self._run(self._raw.fetchall)  # type: ignore[return-value]

    async def close(self) -> None:
        """Close the cursor."""
        if not self._closed:
            try:
                await self._run(self._raw.close)
            except Exception:
                pass
            self._closed = True

    @property
    def description(self) -> tuple[Any, ...] | None:
        """Column descriptions from the last query."""
        return self._raw.description

    @property
    def rowcount(self) -> int:
        """Number of rows affected by the last operation."""
        return self._raw.rowcount

    @property
    def lastrowid(self) -> int | None:
        """Row ID of the last inserted row."""
        return self._raw.lastrowid

    # ── Async iteration ──────────────────────────────────────────────

    def __aiter__(self) -> AsyncIterator[Row]:
        return self

    async def __anext__(self) -> Row:
        row = await self.fetch_one()
        if row is None:
            raise StopAsyncIteration
        return row
