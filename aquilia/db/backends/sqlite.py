"""
Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module.

This is the default backend. It uses the native ``aquilia.sqlite``
connection pool (built on stdlib ``sqlite3``) and implements the full
``DatabaseAdapter`` interface including introspection.

Built on the native aquilia.sqlite module with:
- Connection pooling (N readers + 1 writer)
- Prepared statement caching
- Full PRAGMA hardening (busy_timeout, synchronous, etc.)
- Observable metrics
- Cooperative cancellation
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from .base import (
    DatabaseAdapter,
    AdapterCapabilities,
    ColumnInfo,
    TableInfo,
)

from aquilia.sqlite import (
    ConnectionPool,
    SqlitePoolConfig,
    SqliteMetrics,
    create_pool,
    SqliteError,
    SqliteConnectionError,
    Row,
)

logger = logging.getLogger("aquilia.db.backends.sqlite")

__all__ = ["SQLiteAdapter"]

# Savepoint name validation -- prevent SQL injection
_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class SQLiteAdapter(DatabaseAdapter):
    """
    SQLite adapter using the native ``aquilia.sqlite`` connection pool.

    Features:
    - Connection pooling (WAL-mode concurrent readers + serialized writer)
    - Full PRAGMA hardening (busy_timeout, synchronous=NORMAL, etc.)
    - Prepared statement caching per connection
    - Foreign key enforcement
    - Full introspection support
    - Savepoint-based nested transactions
    - SQL injection prevention on savepoint names
    - Observable metrics (queries, cache hits, pool utilization)
    """

    capabilities = AdapterCapabilities(
        supports_returning=False,
        supports_json_type=False,
        supports_arrays=False,
        supports_hstore=False,
        supports_citext=False,
        supports_upsert=True,
        supports_savepoints=True,
        supports_window_functions=True,
        supports_cte=True,
        param_style="qmark",
        null_ordering=False,
        name="sqlite",
    )

    def __init__(self) -> None:
        self._pool: Optional[ConnectionPool] = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._in_transaction = False
        self._writer_conn: Any = None  # held during transaction

    async def connect(self, url: str, **options) -> None:
        if self._connected:
            return
        async with self._lock:
            if self._connected:
                return
            db_path = self._parse_url(url)
            config = SqlitePoolConfig(
                path=db_path,
                journal_mode=options.get("journal_mode", "WAL"),
                foreign_keys=options.get("foreign_keys", True),
                busy_timeout=options.get("busy_timeout", 5000),
                synchronous=options.get("synchronous", "NORMAL"),
                pool_size=options.get("pool_size", 5),
                pool_min_size=options.get("pool_min_size", 2),
                statement_cache_size=options.get("statement_cache_size", 256),
                echo=options.get("echo", False),
            )
            self._pool = await create_pool(config)
            self._connected = True

    async def disconnect(self) -> None:
        if not self._connected:
            return
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
            self._connected = False

    async def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        params = params or []
        if self._in_transaction and self._writer_conn is not None:
            return await self._writer_conn.execute(sql, params)
        # Auto-commit mode: use pool quick method (acquires writer)
        return await self._pool.execute(sql, params)

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        if self._in_transaction and self._writer_conn is not None:
            await self._writer_conn.execute_many(sql, params_list)
            return
        await self._pool.execute_many(sql, params_list)

    async def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        params = params or []
        if self._in_transaction and self._writer_conn is not None:
            rows = await self._writer_conn.fetch_all(sql, params)
        else:
            rows = await self._pool.fetch_all(sql, params)
        # Convert Row objects to dicts for backward compatibility
        result = []
        for row in rows:
            if isinstance(row, Row):
                result.append(row.to_dict())
            elif hasattr(row, "keys"):
                result.append(dict(row))
            else:
                result.append(row)  # type: ignore[arg-type]
        return result

    async def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        params = params or []
        if self._in_transaction and self._writer_conn is not None:
            row = await self._writer_conn.fetch_one(sql, params)
        else:
            row = await self._pool.fetch_one(sql, params)
        if row is None:
            return None
        if isinstance(row, Row):
            return row.to_dict()
        if hasattr(row, "keys"):
            return dict(row)
        return None

    async def fetch_val(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        params = params or []
        if self._in_transaction and self._writer_conn is not None:
            return await self._writer_conn.fetch_val(sql, params)
        return await self._pool.fetch_val(sql, params)

    # ── Transactions ─────────────────────────────────────────────────

    async def begin(self) -> None:
        if not self._connected or self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault
            raise DatabaseConnectionFault(backend="sqlite", reason="Not connected")
        # Acquire the writer connection and hold it for the transaction
        self._writer_conn = await self._pool._acquire(readonly=False)
        await self._writer_conn.begin(mode="DEFERRED")
        self._in_transaction = True

    async def commit(self) -> None:
        if self._writer_conn is not None:
            await self._writer_conn.commit()
            await self._pool._release(self._writer_conn)  # type: ignore[union-attr]
            self._writer_conn = None
        self._in_transaction = False

    async def rollback(self) -> None:
        if self._writer_conn is not None:
            await self._writer_conn.rollback()
            await self._pool._release(self._writer_conn)  # type: ignore[union-attr]
            self._writer_conn = None
        self._in_transaction = False

    async def savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        if self._writer_conn is not None:
            await self._writer_conn.savepoint(name)
        elif self._pool is not None:
            async with self._pool.acquire(readonly=False) as conn:
                await conn.savepoint(name)

    async def release_savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        if self._writer_conn is not None:
            await self._writer_conn.release_savepoint(name)
        elif self._pool is not None:
            async with self._pool.acquire(readonly=False) as conn:
                await conn.release_savepoint(name)

    async def rollback_to_savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            from aquilia.faults.domains import QueryFault
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        if self._writer_conn is not None:
            await self._writer_conn.rollback_to_savepoint(name)
        elif self._pool is not None:
            async with self._pool.acquire(readonly=False) as conn:
                await conn.rollback_to_savepoint(name)

    # ── Introspection ────────────────────────────────────────────────

    async def table_exists(self, table_name: str) -> bool:
        row = await self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table_name],
        )
        return row is not None

    async def get_tables(self) -> List[str]:
        rows = await self.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [r["name"] for r in rows]

    async def get_columns(self, table_name: str) -> List[ColumnInfo]:
        rows = await self.fetch_all(f'PRAGMA table_info("{table_name}")')
        columns = []
        for row in rows:
            columns.append(ColumnInfo(
                name=row["name"],
                data_type=row["type"],
                nullable=not row["notnull"],
                default=row["dflt_value"],
                primary_key=bool(row["pk"]),
            ))
        return columns

    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
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

    async def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key info for a table."""
        rows = await self.fetch_all(f'PRAGMA foreign_key_list("{table_name}")')
        fks = []
        for row in rows:
            fks.append({
                "from_column": row["from"],
                "to_table": row["table"],
                "to_column": row["to"],
                "on_delete": row.get("on_delete", "NO ACTION"),
                "on_update": row.get("on_update", "NO ACTION"),
            })
        return fks

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def dialect(self) -> str:
        return "sqlite"

    @property
    def pool(self) -> Optional[ConnectionPool]:
        """Access the underlying connection pool (for advanced usage)."""
        return self._pool

    @property
    def metrics(self) -> Optional[SqliteMetrics]:
        """Access pool metrics."""
        if self._pool:
            return self._pool.metrics
        return None

    @staticmethod
    def _parse_url(url: str) -> str:
        """Extract file path from sqlite URL."""
        for prefix in ("sqlite:///", "sqlite://"):
            if url.startswith(prefix):
                path = url[len(prefix):]
                return path or ":memory:"
        return url.replace("sqlite:", "").lstrip("/") or ":memory:"
