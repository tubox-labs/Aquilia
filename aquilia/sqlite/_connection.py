"""
Async Connection — Thread-dispatched wrapper around ``sqlite3.Connection``.

Each ``AsyncConnection`` owns a ``sqlite3.Connection`` and dispatches all
blocking calls to a shared ``ThreadPoolExecutor`` via
``asyncio.loop.run_in_executor()``.

Features:
    - All query methods are async
    - Statement cache tracking (hit / miss counters)
    - Row factory integration (returns :class:`Row` objects)
    - Transaction and savepoint methods
    - Introspection helpers (table_exists, get_tables, etc.)
    - Cooperative cancellation on ``asyncio.CancelledError``
"""

from __future__ import annotations

import asyncio
import logging
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Sequence

from ._config import SqlitePoolConfig
from ._errors import (
    SqliteConnectionError,
    SqliteError,
    SqliteQueryError,
    map_sqlite_error,
)
from ._metrics import SqliteMetrics
from ._pragma import apply_pragmas, build_pragmas
from ._rows import Row, row_factory
from ._statement_cache import CacheStats, StatementCache
from ._transaction import TransactionContext, SavepointContext

logger = logging.getLogger("aquilia.sqlite.connection")

__all__ = ["AsyncConnection"]

# Savepoint name validation — prevent SQL injection
_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class AsyncConnection:
    """
    Async wrapper around a single ``sqlite3.Connection``.

    All blocking operations are dispatched to the provided executor.
    The connection is **not** thread-safe — each connection must only
    be used by one task at a time (enforced by the pool).

    Args:
        raw: The underlying ``sqlite3.Connection``.
        executor: Shared thread pool for dispatching blocking calls.
        config: Pool configuration (for echo, timeouts, etc.).
        metrics: Shared metrics collector.
        readonly: Whether this is a read-only connection.
        conn_id: Unique identifier for this connection (for logging).
    """

    __slots__ = (
        "_raw",
        "_executor",
        "_config",
        "_metrics",
        "_readonly",
        "_conn_id",
        "_cache",
        "_in_transaction",
        "_closed",
        "_created_at",
    )

    def __init__(
        self,
        raw: sqlite3.Connection,
        executor: ThreadPoolExecutor,
        config: SqlitePoolConfig,
        metrics: SqliteMetrics | None = None,
        readonly: bool = False,
        conn_id: int = 0,
    ) -> None:
        self._raw = raw
        self._executor = executor
        self._config = config
        self._metrics = metrics
        self._readonly = readonly
        self._conn_id = conn_id
        self._cache = StatementCache(capacity=config.statement_cache_size)
        self._in_transaction = False
        self._closed = False
        self._created_at = time.monotonic()

    # ── Internal: run blocking callable in thread pool ───────────────

    async def _run(self, fn: Any, *args: Any) -> Any:
        """Execute *fn* in the thread pool executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, fn, *args)

    # ── Query methods ────────────────────────────────────────────────

    async def execute(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
    ) -> "AsyncCursor":
        """
        Execute a single SQL statement.

        Args:
            sql: SQL text with ``?`` placeholders.
            params: Parameter sequence.

        Returns:
            :class:`AsyncCursor` wrapping the raw ``sqlite3.Cursor``.
            Callers can read ``.lastrowid`` for INSERT statements and
            ``.rowcount`` for UPDATE / DELETE.
        """
        from ._cursor import AsyncCursor  # local import avoids circular dependency

        params = params or []
        self._log_sql(sql, params)

        t0 = time.monotonic_ns()
        cached = self._cache.touch(sql)
        if self._metrics:
            self._metrics.record_cache_access(hit=cached)

        try:
            raw_cursor = await self._run(self._raw.execute, sql, params)
            if self._config.auto_commit and not self._in_transaction:
                await self._run(self._raw.commit)
            elapsed = time.monotonic_ns() - t0
            if self._metrics:
                self._metrics.record_query(elapsed)
            return AsyncCursor(raw_cursor, self._executor)
        except sqlite3.Error as exc:
            if self._metrics:
                self._metrics.record_query_error()
            raise map_sqlite_error(exc, operation="execute", sql=sql) from exc

    async def execute_many(
        self,
        sql: str,
        params_seq: Sequence[Sequence[Any]],
    ) -> int:
        """
        Execute a statement with multiple parameter sets.

        Args:
            sql: SQL text with ``?`` placeholders.
            params_seq: Sequence of parameter sequences.

        Returns:
            Total number of rows affected.
        """
        self._log_sql(sql, f"({len(params_seq)} param sets)")

        t0 = time.monotonic_ns()
        self._cache.touch(sql)

        try:
            cursor = await self._run(self._raw.executemany, sql, params_seq)
            if self._config.auto_commit and not self._in_transaction:
                await self._run(self._raw.commit)
            elapsed = time.monotonic_ns() - t0
            if self._metrics:
                self._metrics.record_query(elapsed)
            return cursor.rowcount
        except sqlite3.Error as exc:
            if self._metrics:
                self._metrics.record_query_error()
            raise map_sqlite_error(exc, operation="execute_many", sql=sql) from exc

    async def execute_script(self, script: str) -> None:
        """
        Execute a multi-statement SQL script.

        Note: This commits any pending transaction first and does not
        use parameter binding.

        Args:
            script: Multi-statement SQL text.
        """
        self._log_sql(script[:200], None)
        try:
            await self._run(self._raw.executescript, script)
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="execute_script") from exc

    async def fetch_all(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
    ) -> list[Row]:
        """
        Execute and return all rows.

        Args:
            sql: SQL text.
            params: Parameter sequence.

        Returns:
            List of :class:`Row` objects.
        """
        params = params or []
        self._log_sql(sql, params)

        t0 = time.monotonic_ns()
        cached = self._cache.touch(sql)
        if self._metrics:
            self._metrics.record_cache_access(hit=cached)

        try:
            cursor = await self._run(self._raw.execute, sql, params)
            rows = await self._run(cursor.fetchall)
            elapsed = time.monotonic_ns() - t0
            if self._metrics:
                self._metrics.record_query(elapsed, row_count=len(rows))
            return rows  # type: ignore[return-value]
        except sqlite3.Error as exc:
            if self._metrics:
                self._metrics.record_query_error()
            raise map_sqlite_error(exc, operation="fetch_all", sql=sql) from exc

    async def fetch_one(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
    ) -> Row | None:
        """
        Execute and return the first row, or None.

        Args:
            sql: SQL text.
            params: Parameter sequence.

        Returns:
            A :class:`Row` or None.
        """
        params = params or []
        self._log_sql(sql, params)

        t0 = time.monotonic_ns()
        cached = self._cache.touch(sql)
        if self._metrics:
            self._metrics.record_cache_access(hit=cached)

        try:
            cursor = await self._run(self._raw.execute, sql, params)
            row = await self._run(cursor.fetchone)
            elapsed = time.monotonic_ns() - t0
            if self._metrics:
                self._metrics.record_query(elapsed, row_count=1 if row else 0)
            return row  # type: ignore[return-value]
        except sqlite3.Error as exc:
            if self._metrics:
                self._metrics.record_query_error()
            raise map_sqlite_error(exc, operation="fetch_one", sql=sql) from exc

    async def fetch_val(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
        *,
        column: int = 0,
    ) -> Any:
        """
        Execute and return a single scalar value.

        Args:
            sql: SQL text.
            params: Parameter sequence.
            column: Column index to extract (default 0).

        Returns:
            The scalar value, or None if no rows.
        """
        row = await self.fetch_one(sql, params)
        if row is None:
            return None
        return row[column]

    # ── Transaction methods ──────────────────────────────────────────

    async def begin(self, *, mode: str = "DEFERRED") -> None:
        """
        Start a transaction.

        Args:
            mode: Transaction mode — DEFERRED, IMMEDIATE, or EXCLUSIVE.
        """
        mode = mode.upper()
        if mode not in ("DEFERRED", "IMMEDIATE", "EXCLUSIVE"):
            from aquilia.faults.domains import ConfigInvalidFault
            raise ConfigInvalidFault(
                key="sqlite.transaction_mode",
                reason=f"Invalid transaction mode: {mode!r}",
            )

        try:
            await self._run(self._raw.execute, f"BEGIN {mode}")
            self._in_transaction = True
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="begin") from exc

    async def commit(self) -> None:
        """Commit the current transaction."""
        try:
            await self._run(self._raw.commit)
            self._in_transaction = False
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="commit") from exc

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            await self._run(self._raw.rollback)
            self._in_transaction = False
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="rollback") from exc

    async def savepoint(self, name: str) -> None:
        """
        Create a savepoint.

        Args:
            name: Savepoint name (alphanumeric + underscore only).
        """
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        try:
            await self._run(self._raw.execute, f'SAVEPOINT "{name}"')
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="savepoint") from exc

    async def release_savepoint(self, name: str) -> None:
        """Release (commit) a savepoint."""
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        try:
            await self._run(self._raw.execute, f'RELEASE SAVEPOINT "{name}"')
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="release_savepoint") from exc

    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a savepoint."""
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        try:
            await self._run(self._raw.execute, f'ROLLBACK TO SAVEPOINT "{name}"')
        except sqlite3.Error as exc:
            raise map_sqlite_error(exc, operation="rollback_to_savepoint") from exc

    # ── Transaction context managers ─────────────────────────────────

    def transaction(self, *, mode: str = "DEFERRED") -> TransactionContext:
        """
        Return a transaction context manager.

        Usage::

            async with conn.transaction(mode="IMMEDIATE") as txn:
                await conn.execute("INSERT ...")
        """
        return TransactionContext(self, mode=mode, metrics=self._metrics)

    def savepoint_ctx(self, name: str) -> SavepointContext:
        """
        Return a savepoint context manager.

        Usage::

            async with conn.savepoint_ctx("sp1") as sp:
                await conn.execute("INSERT ...")
        """
        return SavepointContext(self, name, metrics=self._metrics)

    # ── Introspection ────────────────────────────────────────────────

    async def table_exists(self, name: str) -> bool:
        """Check if a table exists."""
        row = await self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [name],
        )
        return row is not None

    async def get_tables(self) -> list[str]:
        """List all user table names."""
        rows = await self.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in rows]

    async def get_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Get column info for a table (PRAGMA table_info)."""
        rows = await self.fetch_all(f'PRAGMA table_info("{table_name}")')
        columns = []
        for row in rows:
            columns.append({
                "name": row["name"],
                "type": row["type"],
                "nullable": not row["notnull"],
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            })
        return columns

    async def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Get index info for a table."""
        rows = await self.fetch_all(f'PRAGMA index_list("{table_name}")')
        indexes = []
        for row in rows:
            idx_name = row["name"]
            idx_info = await self.fetch_all(f'PRAGMA index_info("{idx_name}")')
            columns = [i["name"] for i in idx_info]
            indexes.append({
                "name": idx_name,
                "unique": bool(row["unique"]),
                "columns": columns,
            })
        return indexes

    async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Get foreign key info for a table."""
        rows = await self.fetch_all(f'PRAGMA foreign_key_list("{table_name}")')
        fks = []
        for row in rows:
            fks.append({
                "from_column": row["from"],
                "to_table": row["table"],
                "to_column": row["to"],
            })
        return fks

    # ── Backup ───────────────────────────────────────────────────────

    async def backup(
        self,
        target: str | AsyncConnection,
        *,
        pages: int = -1,
    ) -> None:
        """
        Online backup to another database.

        Uses ``sqlite3.Connection.backup()`` (available Python ≥ 3.7).

        Args:
            target: File path or another ``AsyncConnection``.
            pages: Pages per step (-1 = all at once).
        """
        if isinstance(target, AsyncConnection):
            target_raw = target._raw
        else:
            target_raw = sqlite3.connect(target)

        try:
            await self._run(self._raw.backup, target_raw, pages=pages)
        finally:
            if isinstance(target, str):
                target_raw.close()

    # ── Cache ────────────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Clear the statement cache."""
        self._cache.clear()

    @property
    def cache_stats(self) -> CacheStats:
        """Statement cache statistics."""
        return self._cache.stats

    # ── Connection lifecycle ─────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying sqlite3 connection."""
        if self._closed:
            return
        try:
            await self._run(self._raw.close)
        except Exception:
            pass
        finally:
            self._closed = True

    # ── Properties ───────────────────────────────────────────────────

    @property
    def readonly(self) -> bool:
        """Whether this is a read-only connection."""
        return self._readonly

    @property
    def in_transaction(self) -> bool:
        """Whether a transaction is active."""
        return self._in_transaction

    @property
    def closed(self) -> bool:
        """Whether the connection has been closed."""
        return self._closed

    @property
    def conn_id(self) -> int:
        """Unique connection identifier."""
        return self._conn_id

    @property
    def age(self) -> float:
        """Seconds since this connection was created."""
        return time.monotonic() - self._created_at

    @property
    def path(self) -> str:
        """Database file path."""
        return self._config.path

    # ── Private helpers ──────────────────────────────────────────────

    def _log_sql(self, sql: str, params: Any) -> None:
        """Log SQL if echo is enabled."""
        if self._config.echo:
            logger.info("[conn-%d] %s  params=%s", self._conn_id, sql, params)
