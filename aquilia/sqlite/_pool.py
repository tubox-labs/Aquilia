"""
Connection Pool — Async pool with N readers + 1 writer.

Manages a set of ``AsyncConnection`` wrappers.  Under WAL journal mode,
multiple readers can operate concurrently while writes are serialized
through a single dedicated writer connection.

Features:
    - Reader pool (deque-based, configurable min/max)
    - Dedicated writer with ``asyncio.Lock`` serialization
    - Per-connection PRAGMA application
    - Idle connection eviction
    - Health checks (execute ``SELECT 1``)
    - Quick methods (execute, fetch_all, etc.) that auto-acquire/release
    - Metrics integration
    - Graceful shutdown
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from collections import deque
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ._config import SqlitePoolConfig
from ._connection import AsyncConnection
from ._errors import (
    PoolExhaustedError,
    SqliteConnectionError,
    SqliteSecurityError,
)
from ._metrics import SqliteMetrics
from ._pragma import apply_pragmas, build_pragmas
from ._rows import Row, row_factory
from ._transaction import TransactionContext

logger = logging.getLogger("aquilia.sqlite.pool")

__all__ = ["ConnectionPool", "create_pool"]


class _AcquireContext:
    """Async context manager returned by :meth:`ConnectionPool.acquire`."""

    __slots__ = ("_pool", "_readonly", "_conn")

    def __init__(self, pool: ConnectionPool, *, readonly: bool) -> None:
        self._pool = pool
        self._readonly = readonly
        self._conn: AsyncConnection | None = None

    async def __aenter__(self) -> AsyncConnection:
        self._conn = await self._pool._acquire(readonly=self._readonly)
        return self._conn

    async def __aexit__(self, *exc: Any) -> None:
        if self._conn is not None:
            await self._pool._release(self._conn)
            self._conn = None


class ConnectionPool:
    """
    Async connection pool for SQLite.

    Manages *N* reader connections and one writer connection.  All
    connections share a ``ThreadPoolExecutor`` for dispatching blocking
    ``sqlite3`` calls.

    Usage::

        pool = await create_pool("sqlite:///db.sqlite3")
        async with pool.acquire(readonly=True) as conn:
            rows = await conn.fetch_all("SELECT * FROM users")
        await pool.close()

    Or as an async context manager::

        async with await create_pool(config) as pool:
            row = await pool.fetch_one("SELECT count(*) FROM users")
    """

    __slots__ = (
        "_config",
        "_executor",
        "_writer",
        "_writer_lock",
        "_readers",
        "_reader_semaphore",
        "_metrics",
        "_conn_counter",
        "_opened",
        "_closed",
    )

    def __init__(
        self,
        config: SqlitePoolConfig,
        metrics: SqliteMetrics | None = None,
    ) -> None:
        self._config = config
        self._metrics = metrics or SqliteMetrics()
        self._executor: ThreadPoolExecutor | None = None
        self._writer: AsyncConnection | None = None
        self._writer_lock = asyncio.Lock()
        self._readers: deque[AsyncConnection] = deque()
        self._reader_semaphore: asyncio.Semaphore | None = None
        self._conn_counter = 0
        self._opened = False
        self._closed = False

    # ── Lifecycle ────────────────────────────────────────────────────

    async def open(self) -> None:
        """
        Open the pool: create the executor, writer, and initial readers.
        """
        if self._opened:
            return

        self._validate_path()

        # Total connections: pool_size readers + 1 writer
        total = self._config.pool_size + 1
        self._executor = ThreadPoolExecutor(
            max_workers=total,
            thread_name_prefix="aquilia-sqlite",
        )

        # Open writer
        self._writer = await self._open_connection(readonly=False)

        # Open initial readers
        self._reader_semaphore = asyncio.Semaphore(self._config.pool_size)
        for _ in range(self._config.pool_min_size):
            reader = await self._open_connection(readonly=True)
            self._readers.append(reader)

        self._metrics.pool_size = 1 + len(self._readers)
        self._metrics.pool_idle = len(self._readers)
        self._opened = True

    async def close(self) -> None:
        """
        Close all connections and shut down the executor.
        """
        if self._closed:
            return
        self._closed = True

        # Close readers
        while self._readers:
            conn = self._readers.popleft()
            await conn.close()

        # Close writer
        if self._writer:
            await self._writer.close()
            self._writer = None

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

        self._metrics.pool_size = 0
        self._metrics.pool_idle = 0
        self._opened = False

    async def __aenter__(self) -> ConnectionPool:
        await self.open()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ── Acquire / Release ────────────────────────────────────────────

    def acquire(self, *, readonly: bool = False) -> _AcquireContext:
        """
        Acquire a connection from the pool.

        Returns an async context manager that releases the connection
        on exit.

        Args:
            readonly: If True, acquire a reader (default).
                      If False, acquire the writer.

        Usage::

            async with pool.acquire(readonly=True) as conn:
                rows = await conn.fetch_all("SELECT ...")
        """
        return _AcquireContext(self, readonly=readonly)

    async def _acquire(self, *, readonly: bool) -> AsyncConnection:
        """Internal: acquire a connection."""
        if self._closed:
            raise SqliteConnectionError("Pool is closed")
        if not self._opened:
            raise SqliteConnectionError("Pool is not open")

        if not readonly:
            # Writer: serialize with lock
            self._metrics.pool_waiting += 1
            try:
                await asyncio.wait_for(
                    self._writer_lock.acquire(),
                    timeout=self._config.pool_timeout,
                )
            except asyncio.TimeoutError:
                raise PoolExhaustedError("Timed out waiting for writer connection")
            finally:
                self._metrics.pool_waiting -= 1

            assert self._writer is not None
            return self._writer

        # Reader: try to get from deque
        assert self._reader_semaphore is not None
        self._metrics.pool_waiting += 1
        try:
            await asyncio.wait_for(
                self._reader_semaphore.acquire(),
                timeout=self._config.pool_timeout,
            )
        except asyncio.TimeoutError:
            raise PoolExhaustedError("Timed out waiting for reader connection")
        finally:
            self._metrics.pool_waiting -= 1

        if self._readers:
            conn = self._readers.popleft()
            self._metrics.pool_idle -= 1
            return conn

        # No idle reader available — open a new one
        conn = await self._open_connection(readonly=True)
        self._metrics.pool_size += 1
        return conn

    async def _release(self, conn: AsyncConnection) -> None:
        """Internal: release a connection back to the pool."""
        if conn.readonly:
            # Return to reader deque
            if not self._closed and not conn.closed:
                self._readers.append(conn)
                self._metrics.pool_idle += 1
            assert self._reader_semaphore is not None
            self._reader_semaphore.release()
        else:
            # Release writer lock
            self._writer_lock.release()

    # ── Quick methods (auto-acquire) ─────────────────────────────────

    async def execute(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> Any:
        """Execute a write statement (acquires writer automatically)."""
        async with self.acquire(readonly=False) as conn:
            return await conn.execute(sql, params)

    async def execute_many(
        self,
        sql: str,
        params_seq: Sequence[Sequence[Any]],
    ) -> int:
        """Execute with multiple param sets (acquires writer)."""
        async with self.acquire(readonly=False) as conn:
            return await conn.execute_many(sql, params_seq)

    async def fetch_all(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> list[Row]:
        """Fetch all rows (acquires reader)."""
        async with self.acquire(readonly=True) as conn:
            return await conn.fetch_all(sql, params)

    async def fetch_one(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> Row | None:
        """Fetch one row (acquires reader)."""
        async with self.acquire(readonly=True) as conn:
            return await conn.fetch_one(sql, params)

    async def fetch_val(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        *,
        column: int = 0,
    ) -> Any:
        """Fetch a scalar value (acquires reader)."""
        async with self.acquire(readonly=True) as conn:
            return await conn.fetch_val(sql, params, column=column)

    # ── Transaction shorthand ────────────────────────────────────────

    def transaction(self, *, mode: str = "DEFERRED") -> TransactionContext:
        """
        Create a transaction context manager using the writer connection.

        Note: The caller must use ``async with pool.acquire(readonly=False)``
        for explicit connection access.  This shorthand acquires the writer
        internally.

        Usage::

            async with pool.acquire(readonly=False) as conn:
                async with conn.transaction(mode="IMMEDIATE") as txn:
                    await conn.execute("INSERT ...")
        """
        if self._writer is None:
            raise SqliteConnectionError("Pool is not open")
        return TransactionContext(
            self._writer,
            mode=mode,
            metrics=self._metrics,
        )

    # ── Maintenance ──────────────────────────────────────────────────

    async def checkpoint(self, *, mode: str = "PASSIVE") -> None:
        """
        Force a WAL checkpoint.

        Args:
            mode: PASSIVE, FULL, RESTART, or TRUNCATE.
        """
        mode = mode.upper()
        if mode not in ("PASSIVE", "FULL", "RESTART", "TRUNCATE"):
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="sqlite.checkpoint_mode",
                reason=f"Invalid checkpoint mode: {mode!r}",
            )
        async with self.acquire(readonly=False) as conn:
            await conn.execute(f"PRAGMA wal_checkpoint({mode})")

    async def vacuum(self) -> None:
        """Run VACUUM on the database (requires exclusive access)."""
        async with self.acquire(readonly=False) as conn:
            await conn.execute_script("VACUUM")
            conn.clear_cache()

    # ── Properties ───────────────────────────────────────────────────

    @property
    def size(self) -> int:
        """Current total connections (readers + writer)."""
        return self._metrics.pool_size

    @property
    def idle(self) -> int:
        """Current idle reader connections."""
        return self._metrics.pool_idle

    @property
    def metrics(self) -> SqliteMetrics:
        """Pool metrics."""
        return self._metrics

    @property
    def is_open(self) -> bool:
        """Whether the pool is open."""
        return self._opened and not self._closed

    @property
    def config(self) -> SqlitePoolConfig:
        """Pool configuration."""
        return self._config

    # ── Private helpers ──────────────────────────────────────────────

    async def _open_connection(self, *, readonly: bool) -> AsyncConnection:
        """Create and configure a new connection."""
        assert self._executor is not None

        self._conn_counter += 1
        conn_id = self._conn_counter

        loop = asyncio.get_running_loop()

        def _create() -> sqlite3.Connection:
            # For :memory: databases, use shared cache URI so all
            # connections (readers + writer) share the same database.
            db_path = self._config.path
            uri = False
            if db_path == ":memory:" or db_path == "":
                db_path = "file::memory:?cache=shared"
                uri = True
            raw = sqlite3.connect(
                db_path,
                timeout=self._config.busy_timeout / 1000.0,
                check_same_thread=False,
                isolation_level=None,  # Manual transaction control
                cached_statements=self._config.statement_cache_size,
                uri=uri,
            )
            raw.row_factory = row_factory
            pragmas = build_pragmas(self._config, readonly=readonly)
            apply_pragmas(raw, pragmas)
            return raw

        try:
            raw = await loop.run_in_executor(self._executor, _create)
        except sqlite3.Error as exc:
            raise SqliteConnectionError(
                f"Failed to open connection: {exc}",
                original=exc,
            ) from exc

        conn = AsyncConnection(
            raw=raw,
            executor=self._executor,
            config=self._config,
            metrics=self._metrics,
            readonly=readonly,
            conn_id=conn_id,
        )
        return conn

    def _validate_path(self) -> None:
        """Validate the database path for security."""
        if self._config.path == ":memory:":
            return

        if not self._config.enforce_path_security:
            return

        path = os.path.abspath(self._config.path)

        if self._config.sandbox_root:
            sandbox = os.path.abspath(self._config.sandbox_root)
            if not path.startswith(sandbox + os.sep) and path != sandbox:
                raise SqliteSecurityError(f"Database path {path!r} is outside sandbox {sandbox!r}")

        # Ensure parent directory exists for file-based DBs
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# Module-level factory
# ═══════════════════════════════════════════════════════════════════════════


async def create_pool(
    url_or_config: str | SqlitePoolConfig | None = None,
    *,
    min_size: int | None = None,
    max_size: int | None = None,
    **kwargs: Any,
) -> ConnectionPool:
    """
    Create and open a connection pool.

    Args:
        url_or_config: A ``sqlite:///`` URL string, a ``SqlitePoolConfig``,
                       or None for defaults.
        min_size: Override ``pool_min_size``.
        max_size: Override ``pool_size`` (reader connections).
        **kwargs: Additional overrides passed to ``SqlitePoolConfig``.

    Returns:
        An opened ``ConnectionPool``.

    Usage::

        pool = await create_pool("sqlite:///db.sqlite3")
        rows = await pool.fetch_all("SELECT 1")
        await pool.close()
    """
    if isinstance(url_or_config, SqlitePoolConfig):
        config = url_or_config
    elif isinstance(url_or_config, str):
        config = SqlitePoolConfig.from_url(url_or_config, **kwargs)
    else:
        config = SqlitePoolConfig(**kwargs)

    if min_size is not None:
        config.pool_min_size = min_size
    if max_size is not None:
        config.pool_size = max_size

    pool = ConnectionPool(config)
    await pool.open()
    return pool
