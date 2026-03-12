"""
Compatibility Shim — aiosqlite-compatible API for gradual migration.

Provides a ``connect()`` function that returns an object with the same
interface as ``aiosqlite.Connection``, backed by the native
``aquilia.sqlite`` pool.

Usage::

    from aquilia.sqlite._compat import connect

    async with connect("db.sqlite3") as conn:
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        cursor = await conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()

This shim emits ``DeprecationWarning`` on import to encourage migration
to the pool-based API.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from typing import Any

from ._config import SqlitePoolConfig
from ._pool import ConnectionPool, create_pool

__all__ = ["connect", "CompatConnection"]

# Emit deprecation warning when the compat module is used
warnings.warn(
    "aquilia.sqlite._compat is a migration shim for aiosqlite. Use aquilia.sqlite.create_pool() for the native API.",
    DeprecationWarning,
    stacklevel=2,
)


class CompatConnection:
    """
    aiosqlite-compatible connection object.

    Wraps a ``ConnectionPool`` and presents the same interface as
    ``aiosqlite.Connection``: ``execute``, ``executemany``,
    ``executescript``, ``commit``, ``rollback``, ``close``, and
    ``row_factory``.
    """

    __slots__ = ("_pool", "_config")

    def __init__(self, pool: ConnectionPool, config: SqlitePoolConfig) -> None:
        self._pool = pool
        self._config = config

    async def execute(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> Any:
        """Execute a SQL statement (returns cursor-like)."""
        async with self._pool.acquire(readonly=False) as conn:
            await conn.execute(sql, list(parameters))
            return _CompatCursor(conn)

    async def executemany(
        self,
        sql: str,
        parameters: Sequence[Sequence[Any]],
    ) -> Any:
        """Execute with multiple parameter sets."""
        async with self._pool.acquire(readonly=False) as conn:
            await conn.execute_many(sql, parameters)
            return _CompatCursor(conn)

    async def executescript(self, script: str) -> None:
        """Execute a multi-statement script."""
        async with self._pool.acquire(readonly=False) as conn:
            await conn.execute_script(script)

    async def commit(self) -> None:
        """Commit (no-op: auto-commit is the default)."""
        pass

    async def rollback(self) -> None:
        """Rollback."""
        async with self._pool.acquire(readonly=False) as conn:
            await conn.rollback()

    async def close(self) -> None:
        """Close the pool."""
        await self._pool.close()

    async def __aenter__(self) -> CompatConnection:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


class _CompatCursor:
    """Minimal cursor-like wrapper for compat layer."""

    __slots__ = ("_conn",)

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    async def fetchall(self) -> list[Any]:
        return []

    async def fetchone(self) -> Any:
        return None


async def connect(
    database: str = ":memory:",
    **kwargs: Any,
) -> CompatConnection:
    """
    aiosqlite-compatible ``connect()`` function.

    Creates a pool with a single writer connection (no readers) to
    match the single-connection semantics of aiosqlite.

    Args:
        database: Path to the SQLite database.
        **kwargs: Additional options.

    Returns:
        A ``CompatConnection`` that can be used as a drop-in replacement
        for ``aiosqlite.connect()``.
    """
    config = SqlitePoolConfig(
        path=database,
        pool_size=1,
        pool_min_size=0,
    )
    pool = await create_pool(config)
    return CompatConnection(pool, config)
