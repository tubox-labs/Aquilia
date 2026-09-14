"""
Aquilia DB Backend -- PostgreSQL adapter via asyncpg.

Provides full async PostgreSQL support with connection pooling,
proper transaction management, and introspection.

Requires asyncpg:
    pip install asyncpg
"""

from __future__ import annotations

import contextlib
import logging
import re
from collections.abc import Sequence
from typing import Any

from aquilia.db.backends.base import AdapterCapabilities, ColumnInfo, DatabaseAdapter
from aquilia.faults.domains import DatabaseConnectionFault, QueryFault

logger = logging.getLogger("aquilia.db.backends.postgres")

__all__ = ["PostgresAdapter"]

# Try importing async postgres driver
try:
    import asyncpg

    _HAS_ASYNCPG = True
except ImportError:
    asyncpg = None  # type: ignore
    _HAS_ASYNCPG = False

# Savepoint name validation
_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Pattern to detect INSERT statements (for RETURNING auto-injection)
_INSERT_RE = re.compile(r"^\s*INSERT\s+INTO\s+", re.IGNORECASE)

# Extract rowcount from asyncpg status strings like "INSERT 0 1", "UPDATE 3"
_STATUS_ROWCOUNT_RE = re.compile(r"(\d+)\s*$")

# The column list of an index definition: "... USING btree (col_a, col_b)"
_INDEXDEF_COLUMNS_RE = re.compile(r"\bUSING\s+\w+\s*\((.*)\)\s*$")


def _indexdef_columns(definition: str) -> list[str]:
    """Recover the key column names from a ``pg_get_indexdef`` string.

    Handles multi-part keys, quoted identifiers, ``COLLATE`` clauses, and
    ``ASC``/``DESC``/``NULLS`` options; a non-identifier part (an expression
    index like ``lower(email)``) is kept verbatim so it remains comparable.
    """
    match = _INDEXDEF_COLUMNS_RE.search(definition or "")
    if not match:
        return []
    body = match.group(1)

    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))

    columns = []
    for part in parts:
        part = part.strip()
        while True:
            upper = part.upper()
            for suffix in (" ASC", " DESC", " NULLS FIRST", " NULLS LAST"):
                if upper.endswith(suffix):
                    part = part[: -len(suffix)].strip()
                    break
            else:
                break
        part = re.sub(r"\s+COLLATE\s+\"?[\w.]+\"?", "", part, flags=re.IGNORECASE).strip()
        columns.append(part.strip('"'))
    return columns


class _PgCursorResult:
    """
    Thin cursor-like wrapper around asyncpg results so the ORM can
    access ``.lastrowid`` and ``.rowcount`` the same way it does for
    aquilia.sqlite / aiomysql cursors.
    """

    __slots__ = ("lastrowid", "rowcount")

    def __init__(self, lastrowid: int | None = None, rowcount: int = 0):
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    @classmethod
    def from_status(cls, status: str) -> _PgCursorResult:
        """Build from an asyncpg status string like ``'INSERT 0 1'``."""
        m = _STATUS_ROWCOUNT_RE.search(status)
        rc = int(m.group(1)) if m else 0
        return cls(lastrowid=None, rowcount=rc)


class PostgresAdapter(DatabaseAdapter):
    """
    PostgreSQL adapter using asyncpg with connection pooling.

    Features:
    - Connection pool via asyncpg.create_pool
    - Proper transaction management with a dedicated connection
    - Savepoint support with SQL injection prevention
    - Full introspection via information_schema
    - Automatic ``?`` → ``$N`` placeholder conversion (string-literal safe)

    Requires:
        pip install asyncpg
    """

    capabilities = AdapterCapabilities(
        supports_returning=True,
        supports_json_type=True,
        supports_arrays=True,
        supports_hstore=True,
        supports_citext=True,
        supports_upsert=True,
        supports_savepoints=True,
        supports_window_functions=True,
        supports_cte=True,
        param_style="numeric",  # $1, $2, ...
        null_ordering=True,
        name="postgresql",
    )

    def __init__(self):
        self._pool: Any = None
        self._txn_conn: Any = None  # Dedicated connection for active transaction
        self._txn_obj: Any = None  # asyncpg Transaction object
        self._connected = False
        self._in_transaction = False

    async def connect(self, url: str, **options) -> None:
        if self._connected:
            return

        if not _HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for the PostgreSQL backend. Install it with: pip install aquilia[postgres]"
            )

        min_size = options.pop("pool_min_size", 2)
        max_size = options.pop("pool_max_size", 10)
        self._pool = await asyncpg.create_pool(url, min_size=min_size, max_size=max_size, **options)
        self._connected = True

    async def disconnect(self) -> None:
        if not self._connected:
            return
        # Release transaction connection if held
        if self._txn_conn is not None:
            try:
                if self._txn_obj is not None:
                    await self._txn_obj.rollback()
            except Exception:
                pass
            with contextlib.suppress(Exception):
                await self._txn_conn.close()
            self._txn_conn = None
            self._txn_obj = None
            self._in_transaction = False
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._connected = False

    def adapt_sql(self, sql: str) -> str:
        """
        Convert ``?`` placeholders to ``$1, $2, ...`` for asyncpg.

        String-literal safe -- skips ``?`` inside single-quoted strings.
        """
        result: list[str] = []
        param_idx = 0
        in_string = False
        i = 0
        while i < len(sql):
            ch = sql[i]
            if ch == "'" and not in_string:
                in_string = True
                result.append(ch)
            elif ch == "'" and in_string:
                # Check for escaped quote ''
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    result.append("''")
                    i += 2
                    continue
                in_string = False
                result.append(ch)
            elif ch == "?" and not in_string:
                param_idx += 1
                result.append(f"${param_idx}")
            else:
                result.append(ch)
            i += 1
        return "".join(result)

    def _get_conn(self) -> Any:
        """Return the transaction connection if in txn, else raise."""
        if self._in_transaction and self._txn_conn is not None:
            return self._txn_conn
        return None

    async def execute(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        if not self._connected:
            raise DatabaseConnectionFault(backend="postgresql", reason="Not connected to PostgreSQL")
        adapted_sql = self.adapt_sql(sql)
        args = params or []

        # INSERT: auto-append RETURNING "id" so we can expose lastrowid.
        is_insert = _INSERT_RE.match(adapted_sql) is not None
        appended_returning = is_insert and "RETURNING" not in adapted_sql.upper()
        if appended_returning:
            adapted_sql += ' RETURNING "id"'

        conn = self._get_conn()

        async def _fetchrow(query: str):
            if conn is not None:
                return await conn.fetchrow(query, *args)
            async with self._pool.acquire() as c:
                return await c.fetchrow(query, *args)

        async def _execute_plain(query: str) -> str:
            if conn is not None:
                return await conn.execute(query, *args)
            async with self._pool.acquire() as c:
                return await c.execute(query, *args)

        if is_insert:
            try:
                row = await _fetchrow(adapted_sql)
            except Exception as exc:
                # The auto-appended RETURNING "id" assumes a column named
                # "id"; tables without one (a composite primary key, a
                # custom PK name) must still insert. The clause exists only
                # to expose lastrowid, so drop it and fall back to a plain
                # execute.
                if _HAS_ASYNCPG and isinstance(exc, asyncpg.exceptions.UndefinedColumnError) and appended_returning:
                    # Drop only the clause we appended; the rest of
                    # adapted_sql is already dialect-correct.
                    status = await _execute_plain(adapted_sql[: -len(' RETURNING "id"')])
                    return _PgCursorResult.from_status(status)
                raise
            lastrowid = row["id"] if row and "id" in row else None
            # A RETURNING row means exactly one row was inserted; no row
            # means the statement inserted nothing (the conflict path of
            # INSERT ... ON CONFLICT DO NOTHING). Hardcoding 1 here made
            # every conflicted upsert report itself as created.
            rowcount = 1 if row is not None else 0
            return _PgCursorResult(lastrowid=lastrowid, rowcount=rowcount)

        # Non-INSERT (DDL, UPDATE, DELETE, etc.)
        if conn is not None:
            status = await conn.execute(adapted_sql, *args)
        else:
            async with self._pool.acquire() as c:
                status = await c.execute(adapted_sql, *args)
        return _PgCursorResult.from_status(status)

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None:
        if not self._connected:
            raise DatabaseConnectionFault(backend="postgresql", reason="Not connected to PostgreSQL")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            await conn.executemany(adapted_sql, params_list)
        else:
            async with self._pool.acquire() as c:
                await c.executemany(adapted_sql, params_list)

    async def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        if not self._connected:
            raise DatabaseConnectionFault(backend="postgresql", reason="Not connected to PostgreSQL")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            rows = await conn.fetch(adapted_sql, *(params or []))
        else:
            async with self._pool.acquire() as c:
                rows = await c.fetch(adapted_sql, *(params or []))
        return [dict(row) for row in rows]

    async def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
        if not self._connected:
            raise DatabaseConnectionFault(backend="postgresql", reason="Not connected to PostgreSQL")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            row = await conn.fetchrow(adapted_sql, *(params or []))
        else:
            async with self._pool.acquire() as c:
                row = await c.fetchrow(adapted_sql, *(params or []))
        if row is None:
            return None
        return dict(row)

    async def fetch_val(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        if not self._connected:
            raise DatabaseConnectionFault(backend="postgresql", reason="Not connected to PostgreSQL")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            return await conn.fetchval(adapted_sql, *(params or []))
        async with self._pool.acquire() as c:
            return await c.fetchval(adapted_sql, *(params or []))

    # ── Transactions ─────────────────────────────────────────────────

    async def begin(self, isolation: str | None = None, readonly: bool = False) -> None:
        """Acquire a dedicated connection and start a transaction.

        ``isolation``/``readonly`` are passed straight to asyncpg's own
        ``Connection.transaction()``, which sets them as part of the same
        ``BEGIN`` statement -- unlike a separate ``SET TRANSACTION ...``
        issued beforehand, this can't land on a different connection than
        the one the transaction actually runs on.
        """
        if self._in_transaction:
            return
        self._txn_conn = await self._pool.acquire()
        kwargs: dict[str, Any] = {"readonly": readonly}
        if isolation:
            kwargs["isolation"] = isolation.strip().lower().replace(" ", "_")
        self._txn_obj = self._txn_conn.transaction(**kwargs)
        await self._txn_obj.start()
        self._in_transaction = True

    async def commit(self) -> None:
        """Commit the transaction and release the connection."""
        if not self._in_transaction or self._txn_obj is None:
            return
        try:
            await self._txn_obj.commit()
        finally:
            self._in_transaction = False
            await self._pool.release(self._txn_conn)
            self._txn_conn = None
            self._txn_obj = None

    async def rollback(self) -> None:
        """Rollback the transaction and release the connection."""
        if not self._in_transaction or self._txn_obj is None:
            return
        try:
            await self._txn_obj.rollback()
        finally:
            self._in_transaction = False
            await self._pool.release(self._txn_conn)
            self._txn_conn = None
            self._txn_obj = None

    async def savepoint(self, name: str) -> None:
        """Create a savepoint (must be inside a transaction)."""
        if not _SP_NAME_RE.match(name):
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        conn = self._get_conn()
        if conn is None:
            raise QueryFault(message="Cannot create savepoint outside a transaction")
        await conn.execute(f'SAVEPOINT "{name}"')

    async def release_savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        conn = self._get_conn()
        if conn is None:
            raise QueryFault(message="Cannot release savepoint outside a transaction")
        await conn.execute(f'RELEASE SAVEPOINT "{name}"')

    async def rollback_to_savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            raise QueryFault(message=f"Invalid savepoint name: {name!r}")
        conn = self._get_conn()
        if conn is None:
            raise QueryFault(message="Cannot rollback savepoint outside a transaction")
        await conn.execute(f'ROLLBACK TO SAVEPOINT "{name}"')

    # ── Introspection ────────────────────────────────────────────────

    async def table_exists(self, table_name: str) -> bool:
        row = await self.fetch_one(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=?) AS e",
            [table_name],
        )
        return bool(row and row.get("e"))

    async def get_tables(self) -> list[str]:
        rows = await self.fetch_all(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
        )
        return [r["table_name"] for r in rows]

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        # The primary-key membership is fetched separately: introspection
        # consumers (schema drift, `aq db diff`) read ColumnInfo.primary_key,
        # and leaving it False marked every PostgreSQL primary key as
        # changed on the next diff. Array columns get their full type
        # ("text[]") the same way: information_schema reports only 'ARRAY',
        # which cannot be compared against a model's element type.
        pk_rows = await self.fetch_all(
            "SELECT kcu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "ON kcu.constraint_name = tc.constraint_name "
            "AND kcu.constraint_schema = tc.constraint_schema "
            "WHERE tc.table_schema = 'public' AND tc.table_name = ? "
            "AND tc.constraint_type = 'PRIMARY KEY'",
            [table_name],
        )
        pk_columns = {row["column_name"] for row in pk_rows}

        rows = await self.fetch_all(
            "SELECT column_name, data_type, is_nullable, column_default, "
            "character_maximum_length "
            "FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=? "
            "ORDER BY ordinal_position",
            [table_name],
        )
        if any(row["data_type"] == "ARRAY" for row in rows):
            array_types = {
                row["attname"]: row["full_type"]
                for row in await self.fetch_all(
                    "SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS full_type "
                    "FROM pg_attribute a "
                    "JOIN pg_class t ON a.attrelid = t.oid "
                    "JOIN pg_namespace n ON n.oid = t.relnamespace "
                    "WHERE n.nspname = 'public' AND t.relname = ? "
                    "AND a.attnum > 0 AND NOT a.attisdropped",
                    [table_name],
                )
            }
        else:
            array_types = {}

        columns = []
        for row in rows:
            columns.append(
                ColumnInfo(
                    name=row["column_name"],
                    data_type=array_types.get(row["column_name"], row["data_type"]),
                    nullable=row["is_nullable"] == "YES",
                    default=row.get("column_default"),
                    max_length=row.get("character_maximum_length"),
                    primary_key=row["column_name"] in pk_columns,
                )
            )
        return columns

    async def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Get index info for a PostgreSQL table.

        Column names are recovered from ``pg_get_indexdef`` so drift
        comparison can match an index against the model's declaration, and
        each entry carries ``constraint_backed`` -- ``True`` when the index
        exists only to back a PRIMARY KEY / UNIQUE constraint. Those indexes
        are implied by the constraint rather than independently declared, so
        reporting them as plain indexes made every model-declared index and
        constraint look like drift.
        """
        rows = await self.fetch_all(
            "SELECT i.relname AS indexname, "
            "pg_get_indexdef(i.oid) AS indexdef, "
            "ix.indisunique AS is_unique, "
            "ix.indisprimary AS is_primary, "
            "EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = i.oid) AS constraint_backed "
            "FROM pg_class t "
            "JOIN pg_namespace n ON n.oid = t.relnamespace "
            "JOIN pg_index ix ON ix.indrelid = t.oid "
            "JOIN pg_class i ON i.oid = ix.indexrelid "
            "WHERE n.nspname = 'public' AND t.relname = ? "
            "ORDER BY i.relname",
            [table_name],
        )
        indexes = []
        for row in rows:
            indexes.append(
                {
                    "name": row["indexname"],
                    "definition": row["indexdef"],
                    "unique": bool(row["is_unique"]),
                    "columns": _indexdef_columns(row["indexdef"]),
                    "constraint_backed": bool(row["constraint_backed"]),
                    "primary": bool(row["is_primary"]),
                }
            )
        return indexes

    async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Get foreign key info for a PostgreSQL table."""
        rows = await self.fetch_all(
            "SELECT kcu.column_name AS from_column, "
            "ccu.table_name AS to_table, "
            "ccu.column_name AS to_column, "
            "rc.delete_rule AS on_delete, "
            "rc.update_rule AS on_update "
            "FROM information_schema.key_column_usage kcu "
            "JOIN information_schema.referential_constraints rc "
            "ON kcu.constraint_name = rc.constraint_name "
            "JOIN information_schema.constraint_column_usage ccu "
            "ON rc.unique_constraint_name = ccu.constraint_name "
            "WHERE kcu.table_schema = 'public' AND kcu.table_name = ?",
            [table_name],
        )
        return [dict(r) for r in rows]

    @property
    def is_connected(self) -> bool:
        return self._connected and self._pool is not None

    @property
    def dialect(self) -> str:
        return "postgresql"


def _mask_url(url: str) -> str:
    """Mask password in URL for logging."""
    if "@" in url:
        parts = url.split("@", 1)
        pre = parts[0]
        if ":" in pre:
            scheme_user = pre.rsplit(":", 1)[0]
            return f"{scheme_user}:***@{parts[1]}"
    return url
