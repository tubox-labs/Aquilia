"""
Aquilia DB Backend -- Oracle adapter via python-oracledb.

Provides full async Oracle support with connection pooling,
proper transaction management, and introspection.

Uses Oracle 12c+ IDENTITY columns for auto-increment.

Requires oracledb:
    pip install oracledb
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from .base import (
    DatabaseAdapter,
    AdapterCapabilities,
    ColumnInfo,
)

logger = logging.getLogger("aquilia.db.backends.oracle")

__all__ = ["OracleAdapter"]

# Try importing Oracle driver
try:
    import oracledb
    _HAS_ORACLEDB = True
except ImportError:
    oracledb = None  # type: ignore
    _HAS_ORACLEDB = False

# Savepoint name validation
_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Oracle reserved word quoting
_ORACLE_RESERVED = frozenset({
    "ACCESS", "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "AUDIT",
    "BETWEEN", "BY", "CHAR", "CHECK", "CLUSTER", "COLUMN", "COMMENT",
    "COMPRESS", "CONNECT", "CREATE", "CURRENT", "DATE", "DECIMAL",
    "DEFAULT", "DELETE", "DESC", "DISTINCT", "DROP", "ELSE", "EXCLUSIVE",
    "EXISTS", "FILE", "FLOAT", "FOR", "FROM", "GRANT", "GROUP", "HAVING",
    "IDENTIFIED", "IMMEDIATE", "IN", "INCREMENT", "INDEX", "INITIAL",
    "INSERT", "INTEGER", "INTERSECT", "INTO", "IS", "LEVEL", "LIKE",
    "LOCK", "LONG", "MAXEXTENTS", "MINUS", "MLSLABEL", "MODE", "MODIFY",
    "NOAUDIT", "NOCOMPRESS", "NOT", "NOWAIT", "NULL", "NUMBER", "OF",
    "OFFLINE", "ON", "ONLINE", "OPTION", "OR", "ORDER", "PCTFREE",
    "PRIOR", "PUBLIC", "RAW", "RENAME", "RESOURCE", "REVOKE", "ROW",
    "ROWID", "ROWNUM", "ROWS", "SELECT", "SESSION", "SET", "SHARE",
    "SIZE", "SMALLINT", "START", "SUCCESSFUL", "SYNONYM", "SYSDATE",
    "TABLE", "THEN", "TO", "TRIGGER", "UID", "UNION", "UNIQUE", "UPDATE",
    "USER", "VALIDATE", "VALUES", "VARCHAR", "VARCHAR2", "VIEW",
    "WHENEVER", "WHERE", "WITH",
})


class OracleAdapter(DatabaseAdapter):
    """
    Oracle adapter using python-oracledb (async mode).

    Features:
    - Connection pool via oracledb.create_pool_async
    - Proper transaction management with a dedicated connection
    - Savepoint support with SQL injection prevention
    - Full introspection via ALL_TAB_COLUMNS / ALL_TABLES
    - Automatic ``?`` → ``:N`` placeholder conversion (string-literal safe)
    - Oracle 12c+ IDENTITY column support for auto-increment

    Requires:
        pip install oracledb
    """

    capabilities = AdapterCapabilities(
        supports_returning=True,    # Oracle supports RETURNING INTO
        supports_json_type=False,   # JSON support limited; use CLOB
        supports_arrays=False,
        supports_hstore=False,
        supports_citext=False,
        supports_upsert=True,       # MERGE statement
        supports_savepoints=True,
        supports_window_functions=True,
        supports_cte=True,          # Oracle 11g R2+
        param_style="named",       # :1, :2, ... (positional named)
        null_ordering=True,         # NULLS FIRST / NULLS LAST
        name="oracle",
    )

    def __init__(self):
        self._pool: Any = None
        self._txn_conn: Any = None  # Dedicated connection for active transaction
        self._connected = False
        self._in_transaction = False

    async def connect(self, url: str, **options) -> None:
        if self._connected:
            return

        if not _HAS_ORACLEDB:
            raise ImportError(
                "oracledb is required for Oracle support.\n"
                "Install: pip install oracledb"
            )

        conn_kwargs = _parse_oracle_url(url)
        conn_kwargs.update(options)

        min_size = conn_kwargs.pop("pool_min_size", 2)
        max_size = conn_kwargs.pop("pool_max_size", 10)

        # Enable thin mode by default (no Oracle Client required)
        oracledb.defaults.fetch_lobs = False

        self._pool = oracledb.create_pool_async(
            user=conn_kwargs.get("user"),
            password=conn_kwargs.get("password"),
            dsn=conn_kwargs.get("dsn"),
            min=min_size,
            max=max_size,
        )
        # Pool creation in async mode requires await
        self._pool = await self._pool
        self._connected = True
        logger.info(
            f"Oracle connected via oracledb: "
            f"{conn_kwargs.get('dsn', '?')}"
        )

    async def disconnect(self) -> None:
        if not self._connected:
            return
        # Release transaction connection if held
        if self._txn_conn is not None:
            try:
                await self._txn_conn.rollback()
            except Exception:
                pass
            try:
                await self._txn_conn.close()
            except Exception:
                pass
            self._txn_conn = None
            self._in_transaction = False
        if self._pool:
            await self._pool.close(force=True)
            self._pool = None
        self._connected = False
        logger.debug("Oracle disconnected")

    def adapt_sql(self, sql: str) -> str:
        """
        Convert ``?`` placeholders to ``:1, :2, ...`` for oracledb.

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
                result.append(f":{param_idx}")
            else:
                result.append(ch)
            i += 1
        return "".join(result)

    def _get_conn(self) -> Any:
        """Return the transaction connection if in txn, else None."""
        if self._in_transaction and self._txn_conn is not None:
            return self._txn_conn
        return None

    async def _execute_with_cursor(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        """Execute SQL and return cursor."""
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            cursor = conn.cursor()
            await cursor.execute(adapted_sql, params or [])
            return cursor
        else:
            conn = await self._pool.acquire()
            try:
                cursor = conn.cursor()
                await cursor.execute(adapted_sql, params or [])
                if not self._in_transaction:
                    await conn.commit()
                return cursor
            finally:
                if not self._in_transaction:
                    await self._pool.release(conn)

    async def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if not self._connected:
            raise RuntimeError("Not connected to Oracle")
        return await self._execute_with_cursor(sql, params)

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None:
        if not self._connected:
            raise RuntimeError("Not connected to Oracle")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()
        if conn is not None:
            cursor = conn.cursor()
            await cursor.executemany(adapted_sql, list(params_list))
        else:
            conn = await self._pool.acquire()
            try:
                cursor = conn.cursor()
                await cursor.executemany(adapted_sql, list(params_list))
                await conn.commit()
            finally:
                await self._pool.release(conn)

    async def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("Not connected to Oracle")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()

        async def _fetch(c: Any) -> List[Dict[str, Any]]:
            cursor = c.cursor()
            await cursor.execute(adapted_sql, params or [])
            columns = [col[0].lower() for col in cursor.description] if cursor.description else []
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

        if conn is not None:
            return await _fetch(conn)
        else:
            conn = await self._pool.acquire()
            try:
                return await _fetch(conn)
            finally:
                await self._pool.release(conn)

    async def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("Not connected to Oracle")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()

        async def _fetch(c: Any) -> Optional[Dict[str, Any]]:
            cursor = c.cursor()
            await cursor.execute(adapted_sql, params or [])
            columns = [col[0].lower() for col in cursor.description] if cursor.description else []
            row = await cursor.fetchone()
            if row is None:
                return None
            return dict(zip(columns, row))

        if conn is not None:
            return await _fetch(conn)
        else:
            conn = await self._pool.acquire()
            try:
                return await _fetch(conn)
            finally:
                await self._pool.release(conn)

    async def fetch_val(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if not self._connected:
            raise RuntimeError("Not connected to Oracle")
        adapted_sql = self.adapt_sql(sql)
        conn = self._get_conn()

        async def _fetch(c: Any) -> Any:
            cursor = c.cursor()
            await cursor.execute(adapted_sql, params or [])
            row = await cursor.fetchone()
            return row[0] if row else None

        if conn is not None:
            return await _fetch(conn)
        else:
            conn = await self._pool.acquire()
            try:
                return await _fetch(conn)
            finally:
                await self._pool.release(conn)

    # ── Transactions ─────────────────────────────────────────────────

    async def begin(self) -> None:
        """Acquire a dedicated connection and start a transaction."""
        if self._in_transaction:
            return
        self._txn_conn = await self._pool.acquire()
        # Oracle transactions are implicit -- any DML starts a transaction
        self._in_transaction = True

    async def commit(self) -> None:
        """Commit the transaction and release the connection."""
        if not self._in_transaction or self._txn_conn is None:
            return
        try:
            await self._txn_conn.commit()
        finally:
            self._in_transaction = False
            await self._pool.release(self._txn_conn)
            self._txn_conn = None

    async def rollback(self) -> None:
        """Rollback the transaction and release the connection."""
        if not self._in_transaction or self._txn_conn is None:
            return
        try:
            await self._txn_conn.rollback()
        finally:
            self._in_transaction = False
            await self._pool.release(self._txn_conn)
            self._txn_conn = None

    async def savepoint(self, name: str) -> None:
        """Create a savepoint (must be inside a transaction)."""
        if not _SP_NAME_RE.match(name):
            raise ValueError(f"Invalid savepoint name: {name!r}")
        conn = self._get_conn()
        if conn is None:
            raise RuntimeError("Cannot create savepoint outside a transaction")
        cursor = conn.cursor()
        await cursor.execute(f'SAVEPOINT {name}')

    async def release_savepoint(self, name: str) -> None:
        """Oracle does not support RELEASE SAVEPOINT -- no-op."""
        if not _SP_NAME_RE.match(name):
            raise ValueError(f"Invalid savepoint name: {name!r}")
        # Oracle does not have RELEASE SAVEPOINT -- this is a no-op
        pass

    async def rollback_to_savepoint(self, name: str) -> None:
        if not _SP_NAME_RE.match(name):
            raise ValueError(f"Invalid savepoint name: {name!r}")
        conn = self._get_conn()
        if conn is None:
            raise RuntimeError("Cannot rollback savepoint outside a transaction")
        cursor = conn.cursor()
        await cursor.execute(f'ROLLBACK TO SAVEPOINT {name}')

    # ── Introspection ────────────────────────────────────────────────

    async def table_exists(self, table_name: str) -> bool:
        row = await self.fetch_one(
            "SELECT COUNT(*) AS cnt FROM user_tables WHERE table_name = ?",
            [table_name.upper()],
        )
        return bool(row and row.get("cnt", 0) > 0)

    async def get_tables(self) -> List[str]:
        rows = await self.fetch_all(
            "SELECT table_name FROM user_tables ORDER BY table_name"
        )
        return [r["table_name"].lower() for r in rows]

    async def get_columns(self, table_name: str) -> List[ColumnInfo]:
        rows = await self.fetch_all(
            "SELECT column_name, data_type, nullable, data_default, "
            "data_length, data_precision, data_scale "
            "FROM user_tab_columns "
            "WHERE table_name = ? "
            "ORDER BY column_id",
            [table_name.upper()],
        )
        # Get primary key columns
        pk_rows = await self.fetch_all(
            "SELECT cols.column_name "
            "FROM user_constraints cons "
            "JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name "
            "WHERE cons.constraint_type = 'P' AND cons.table_name = ?",
            [table_name.upper()],
        )
        pk_columns = {r["column_name"].lower() for r in pk_rows}

        columns = []
        for row in rows:
            col_name = row["column_name"].lower()
            data_type = row["data_type"]
            if row.get("data_precision") and "NUMBER" in data_type:
                data_type = f"NUMBER({row['data_precision']},{row.get('data_scale', 0)})"
            columns.append(ColumnInfo(
                name=col_name,
                data_type=data_type,
                nullable=row["nullable"] == "Y",
                default=row.get("data_default"),
                primary_key=col_name in pk_columns,
                max_length=row.get("data_length"),
            ))
        return columns

    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index info for an Oracle table."""
        rows = await self.fetch_all(
            "SELECT i.index_name, i.uniqueness, ic.column_name "
            "FROM user_indexes i "
            "JOIN user_ind_columns ic ON i.index_name = ic.index_name "
            "WHERE i.table_name = ? "
            "ORDER BY i.index_name, ic.column_position",
            [table_name.upper()],
        )
        idx_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            name = row["index_name"].lower()
            if name not in idx_map:
                idx_map[name] = {
                    "name": name,
                    "unique": row["uniqueness"] == "UNIQUE",
                    "columns": [],
                }
            idx_map[name]["columns"].append(row["column_name"].lower())
        return list(idx_map.values())

    async def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key info for an Oracle table."""
        rows = await self.fetch_all(
            "SELECT a.column_name AS from_column, "
            "c_pk.table_name AS to_table, "
            "b.column_name AS to_column, "
            "c.delete_rule AS on_delete "
            "FROM user_cons_columns a "
            "JOIN user_constraints c ON a.constraint_name = c.constraint_name "
            "JOIN user_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name "
            "JOIN user_cons_columns b ON c_pk.constraint_name = b.constraint_name "
            "WHERE c.constraint_type = 'R' AND a.table_name = ?",
            [table_name.upper()],
        )
        return [
            {
                "from_column": r["from_column"].lower(),
                "to_table": r["to_table"].lower(),
                "to_column": r["to_column"].lower(),
                "on_delete": r.get("on_delete", "NO ACTION"),
            }
            for r in rows
        ]

    @property
    def is_connected(self) -> bool:
        return self._connected and self._pool is not None

    @property
    def dialect(self) -> str:
        return "oracle"

    def last_insert_id(self, cursor: Any) -> Optional[int]:
        """
        Oracle does not have lastrowid in the same way.
        Use RETURNING INTO clause or sequences instead.
        """
        if hasattr(cursor, "lastrowid") and cursor.lastrowid:
            return cursor.lastrowid
        return None


# ── URL parsing helper ──────────────────────────────────────────────

def _parse_oracle_url(url: str) -> Dict[str, Any]:
    """
    Parse an oracle:// URL into connection kwargs.

    Supported formats:
        oracle://user:password@host:port/service_name
        oracle://user:password@host/service_name
        oracle+thin://user:password@host:port/service_name
        oracle+thick://user:password@host:port/service_name

    Returns:
        Dict with 'user', 'password', 'dsn' keys.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 1521
    service = (parsed.path or "/").lstrip("/") or "ORCL"

    # Build DSN in Easy Connect format: host:port/service_name
    dsn = f"{host}:{port}/{service}"

    kwargs: Dict[str, Any] = {
        "dsn": dsn,
    }
    if parsed.username:
        kwargs["user"] = parsed.username
    if parsed.password:
        kwargs["password"] = parsed.password

    return kwargs
