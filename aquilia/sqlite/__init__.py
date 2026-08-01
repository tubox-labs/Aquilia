"""
``aquilia.sqlite`` — Native async SQLite module for the Aquilia framework.

Zero-dependency (stdlib ``sqlite3`` only) replacement for ``aiosqlite``.
Provides connection pooling, prepared statement caching, transaction
management, introspection, observability, and DI integration.

Quick start::

    from aquilia.sqlite import create_pool

    pool = await create_pool("sqlite:///db.sqlite3")

    # Quick queries (auto-acquire/release)
    rows = await pool.fetch_all("SELECT * FROM users WHERE active = ?", [True])
    await pool.execute("INSERT INTO users (name) VALUES (?)", ["Alice"])

    # Explicit connection
    async with pool.acquire(readonly=False) as conn:
        async with conn.transaction(mode="IMMEDIATE") as txn:
            await conn.execute("INSERT INTO logs (msg) VALUES (?)", ["created"])
            async with txn.savepoint("sp1"):
                await conn.execute("UPDATE users SET active = 0 WHERE id = ?", [42])

    await pool.close()

Architecture:
    - ``ConnectionPool``: N reader connections + 1 writer connection
    - ``AsyncConnection``: Thread-dispatched wrapper around ``sqlite3.Connection``
    - ``AsyncCursor``: Streaming row iteration
    - ``Row``: Dict-like row with attribute access
    - ``TransactionContext`` / ``SavepointContext``: Async context managers
    - ``StatementCache``: Per-connection LRU tracking
    - ``SqliteMetrics``: Observable counters
    - ``SqliteService``: DI-integrated lifecycle management
"""

from __future__ import annotations

# ── Backup ───────────────────────────────────────────────────────────
from aquilia.sqlite._backup import backup_database

# ── Configuration ────────────────────────────────────────────────────
from aquilia.sqlite._config import SqlitePoolConfig

# ── Connection & cursor ──────────────────────────────────────────────
from aquilia.sqlite._connection import AsyncConnection
from aquilia.sqlite._cursor import AsyncCursor

# ── Errors ───────────────────────────────────────────────────────────
from aquilia.sqlite._errors import (
    PoolExhaustedError,
    SqliteConnectionError,
    SqliteError,
    SqliteIntegrityError,
    SqliteQueryError,
    SqliteSchemaError,
    SqliteSecurityError,
    SqliteTimeoutError,
    map_sqlite_error,
    to_aquilia_fault,
)

# ── Metrics ──────────────────────────────────────────────────────────
from aquilia.sqlite._metrics import SqliteMetrics

# ── Core pool API ────────────────────────────────────────────────────
from aquilia.sqlite._pool import ConnectionPool, create_pool

# ── PRAGMA builder ───────────────────────────────────────────────────
from aquilia.sqlite._pragma import apply_pragmas, build_pragmas

# ── Rows ─────────────────────────────────────────────────────────────
from aquilia.sqlite._rows import Row, row_factory

# ── DI service ───────────────────────────────────────────────────────
from aquilia.sqlite._service import SqliteService

# ── Statement cache ──────────────────────────────────────────────────
from aquilia.sqlite._statement_cache import CacheStats, StatementCache

# ── Transaction ──────────────────────────────────────────────────────
from aquilia.sqlite._transaction import SavepointContext, TransactionContext

__all__ = [
    # Pool
    "ConnectionPool",
    "create_pool",
    # Connection / Cursor
    "AsyncConnection",
    "AsyncCursor",
    # Rows
    "Row",
    "row_factory",
    # Transaction
    "TransactionContext",
    "SavepointContext",
    # Config
    "SqlitePoolConfig",
    # Statement cache
    "StatementCache",
    "CacheStats",
    # Metrics
    "SqliteMetrics",
    # Errors
    "SqliteError",
    "SqliteConnectionError",
    "PoolExhaustedError",
    "SqliteQueryError",
    "SqliteIntegrityError",
    "SqliteSchemaError",
    "SqliteTimeoutError",
    "SqliteSecurityError",
    "map_sqlite_error",
    "to_aquilia_fault",
    # PRAGMA
    "build_pragmas",
    "apply_pragmas",
    # Backup
    "backup_database",
    # DI Service
    "SqliteService",
]
