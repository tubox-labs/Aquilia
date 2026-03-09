"""
Tests for aquilia.sqlite — native async SQLite module.

Tests cover:
    1. SqlitePoolConfig validation
    2. PRAGMA building
    3. Row object (dict/attr/index access)
    4. StatementCache LRU
    5. ConnectionPool lifecycle (open/close)
    6. Read/write query execution
    7. Transaction commit / rollback
    8. Savepoint nesting
    9. Fault mapping (sqlite3 → aquilia.sqlite errors)
    10. Metrics recording
    11. Pool quick methods
    12. Introspection (tables, columns, indexes, foreign keys)
    13. SQLiteAdapter (DatabaseAdapter interface) backward compatibility
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from aquilia.sqlite import (
    AsyncConnection,
    CacheStats,
    ConnectionPool,
    PoolExhaustedError,
    Row,
    SqliteConnectionError,
    SqliteError,
    SqliteIntegrityError,
    SqliteMetrics,
    SqlitePoolConfig,
    SqliteQueryError,
    SqliteSchemaError,
    SqliteSecurityError,
    SqliteTimeoutError,
    StatementCache,
    TransactionContext,
    SavepointContext,
    build_pragmas,
    create_pool,
    map_sqlite_error,
    row_factory,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    """Return a path for a temporary SQLite database file."""
    return str(tmp_path / "test.db")


@pytest_asyncio.fixture
async def pool(tmp_db: str):
    """Create and yield an open pool, close after test."""
    p = await create_pool(
        SqlitePoolConfig(path=tmp_db, pool_size=3, pool_min_size=1)
    )
    yield p
    await p.close()


@pytest_asyncio.fixture
async def memory_pool():
    """Pool using :memory: database."""
    p = await create_pool(
        SqlitePoolConfig(path=":memory:", pool_size=1, pool_min_size=1)
    )
    yield p
    await p.close()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Config Validation
# ═══════════════════════════════════════════════════════════════════════════

class TestSqlitePoolConfig:
    def test_defaults(self):
        cfg = SqlitePoolConfig()
        assert cfg.journal_mode == "WAL"
        assert cfg.foreign_keys is True
        assert cfg.busy_timeout == 5000
        assert cfg.synchronous == "NORMAL"
        assert cfg.pool_size == 5
        assert cfg.statement_cache_size == 256

    def test_journal_mode_validation(self):
        SqlitePoolConfig(journal_mode="DELETE")  # ok
        with pytest.raises(ValueError, match="journal_mode"):
            SqlitePoolConfig(journal_mode="INVALID")

    def test_synchronous_validation(self):
        SqlitePoolConfig(synchronous="FULL")  # ok
        with pytest.raises(ValueError, match="synchronous"):
            SqlitePoolConfig(synchronous="BOGUS")

    def test_temp_store_validation(self):
        SqlitePoolConfig(temp_store="FILE")  # ok
        with pytest.raises(ValueError, match="temp_store"):
            SqlitePoolConfig(temp_store="DISK")

    def test_pool_size_validation(self):
        with pytest.raises(ValueError, match="pool_size"):
            SqlitePoolConfig(pool_size=0)

    def test_pool_min_exceeds_max(self):
        with pytest.raises(ValueError, match="pool_min_size"):
            SqlitePoolConfig(pool_size=2, pool_min_size=5)

    def test_from_url(self):
        cfg = SqlitePoolConfig.from_url("sqlite:///my.db")
        assert cfg.path == "my.db"

    def test_from_url_memory(self):
        cfg = SqlitePoolConfig.from_url("sqlite:///:memory:")
        assert cfg.path == ":memory:"
        assert cfg.is_memory

    def test_from_sqlite_config(self):
        from aquilia.db.configs import SqliteConfig
        base = SqliteConfig(path="data/app.db", busy_timeout=10000)
        cfg = SqlitePoolConfig.from_sqlite_config(base, synchronous="FULL")
        assert cfg.path == "data/app.db"
        assert cfg.busy_timeout == 10000
        assert cfg.synchronous == "FULL"


# ═══════════════════════════════════════════════════════════════════════════
# 2. PRAGMA Building
# ═══════════════════════════════════════════════════════════════════════════

class TestPragmaBuilder:
    def test_build_writer_pragmas(self):
        cfg = SqlitePoolConfig()
        pragmas = build_pragmas(cfg, readonly=False)
        texts = " ".join(pragmas)
        assert "journal_mode = WAL" in texts
        assert "busy_timeout = 5000" in texts
        assert "foreign_keys = ON" in texts
        assert "synchronous = NORMAL" in texts
        assert "query_only" not in texts

    def test_build_reader_pragmas(self):
        cfg = SqlitePoolConfig()
        pragmas = build_pragmas(cfg, readonly=True)
        texts = " ".join(pragmas)
        assert "query_only = 1" in texts
        # Readers should not set journal_mode or wal_autocheckpoint
        assert "journal_mode" not in texts
        assert "wal_autocheckpoint" not in texts


# ═══════════════════════════════════════════════════════════════════════════
# 3. Row Object
# ═══════════════════════════════════════════════════════════════════════════

class TestRow:
    def test_index_access(self):
        row = Row(("id", "name"), (1, "Alice"))
        assert row[0] == 1
        assert row[1] == "Alice"

    def test_key_access(self):
        row = Row(("id", "name"), (1, "Alice"))
        assert row["id"] == 1
        assert row["name"] == "Alice"

    def test_attr_access(self):
        row = Row(("id", "name"), (1, "Alice"))
        assert row.id == 1
        assert row.name == "Alice"

    def test_to_dict(self):
        row = Row(("id", "name"), (1, "Alice"))
        assert row.to_dict() == {"id": 1, "name": "Alice"}

    def test_keys_values_items(self):
        row = Row(("a", "b"), (10, 20))
        assert row.keys() == ("a", "b")
        assert row.values() == (10, 20)
        assert row.items() == (("a", 10), ("b", 20))

    def test_len_iter(self):
        row = Row(("x", "y", "z"), (1, 2, 3))
        assert len(row) == 3
        assert list(row) == [1, 2, 3]

    def test_contains(self):
        row = Row(("id",), (1,))
        assert "id" in row
        assert "name" not in row

    def test_get_with_default(self):
        row = Row(("id",), (1,))
        assert row.get("id") == 1
        assert row.get("missing", 42) == 42

    def test_immutable(self):
        row = Row(("id",), (1,))
        with pytest.raises(AttributeError, match="immutable"):
            row.id = 2  # type: ignore

    def test_missing_key(self):
        row = Row(("id",), (1,))
        with pytest.raises(KeyError):
            row["nope"]

    def test_missing_attr(self):
        row = Row(("id",), (1,))
        with pytest.raises(AttributeError):
            row.nope

    def test_equality(self):
        r1 = Row(("id",), (1,))
        r2 = Row(("id",), (1,))
        assert r1 == r2

    def test_repr(self):
        row = Row(("id", "name"), (1, "A"))
        assert "id=1" in repr(row)
        assert "name='A'" in repr(row)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Statement Cache
# ═══════════════════════════════════════════════════════════════════════════

class TestStatementCache:
    def test_miss_then_hit(self):
        cache = StatementCache(capacity=10)
        assert cache.touch("SELECT 1") is False  # miss
        assert cache.touch("SELECT 1") is True   # hit
        assert cache.stats.hits == 1
        assert cache.stats.misses == 1

    def test_eviction(self):
        cache = StatementCache(capacity=2)
        cache.touch("A")
        cache.touch("B")
        cache.touch("C")  # evicts A
        assert "A" not in cache
        assert "B" in cache
        assert "C" in cache
        assert cache.stats.evictions == 1

    def test_lru_order(self):
        cache = StatementCache(capacity=2)
        cache.touch("A")
        cache.touch("B")
        cache.touch("A")  # move A to front
        cache.touch("C")  # evicts B (LRU)
        assert "A" in cache
        assert "B" not in cache

    def test_clear(self):
        cache = StatementCache(capacity=10)
        cache.touch("X")
        cache.clear()
        assert len(cache) == 0

    def test_zero_capacity(self):
        cache = StatementCache(capacity=0)
        assert cache.touch("X") is False  # always miss
        assert cache.stats.misses == 1
        assert len(cache) == 0

    def test_hit_rate(self):
        cache = StatementCache(capacity=10)
        cache.touch("A")  # miss
        cache.touch("A")  # hit
        cache.touch("A")  # hit
        assert cache.stats.hit_rate == pytest.approx(2.0 / 3.0, abs=0.01)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Connection Pool Lifecycle
# ═══════════════════════════════════════════════════════════════════════════

class TestConnectionPoolLifecycle:
    @pytest.mark.asyncio
    async def test_open_close(self, tmp_db: str):
        pool = ConnectionPool(SqlitePoolConfig(path=tmp_db, pool_size=2, pool_min_size=1))
        await pool.open()
        assert pool.is_open
        assert pool.size >= 2  # 1 writer + at least 1 reader
        await pool.close()
        assert not pool.is_open

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_db: str):
        async with ConnectionPool(
            SqlitePoolConfig(path=tmp_db, pool_size=1, pool_min_size=1)
        ) as pool:
            assert pool.is_open
        assert not pool.is_open

    @pytest.mark.asyncio
    async def test_double_open(self, tmp_db: str):
        pool = ConnectionPool(SqlitePoolConfig(path=tmp_db))
        await pool.open()
        await pool.open()  # should be a no-op
        assert pool.is_open
        await pool.close()

    @pytest.mark.asyncio
    async def test_double_close(self, tmp_db: str):
        pool = ConnectionPool(SqlitePoolConfig(path=tmp_db))
        await pool.open()
        await pool.close()
        await pool.close()  # should be a no-op


# ═══════════════════════════════════════════════════════════════════════════
# 6. Query Execution
# ═══════════════════════════════════════════════════════════════════════════

class TestQueryExecution:
    @pytest.mark.asyncio
    async def test_create_and_insert(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await pool.execute("INSERT INTO t (val) VALUES (?)", ["hello"])
        rows = await pool.fetch_all("SELECT val FROM t")
        assert len(rows) == 1
        assert rows[0]["val"] == "hello"

    @pytest.mark.asyncio
    async def test_fetch_one(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await pool.execute("INSERT INTO t (val) VALUES (?)", ["world"])
        row = await pool.fetch_one("SELECT val FROM t WHERE id = 1")
        assert row is not None
        assert row["val"] == "world"

    @pytest.mark.asyncio
    async def test_fetch_one_none(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        row = await pool.fetch_one("SELECT * FROM t WHERE id = 999")
        assert row is None

    @pytest.mark.asyncio
    async def test_fetch_val(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await pool.execute("INSERT INTO t (val) VALUES (?)", ["x"])
        count = await pool.fetch_val("SELECT count(*) FROM t")
        assert count == 1

    @pytest.mark.asyncio
    async def test_execute_many(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await pool.execute_many(
            "INSERT INTO t (val) VALUES (?)",
            [["a"], ["b"], ["c"]],
        )
        rows = await pool.fetch_all("SELECT val FROM t ORDER BY val")
        assert [r["val"] for r in rows] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_row_types(self, pool: ConnectionPool):
        """Rows from pool.fetch_all should be Row objects."""
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await pool.execute("INSERT INTO t (val) VALUES (?)", ["test"])
        rows = await pool.fetch_all("SELECT * FROM t")
        assert len(rows) == 1
        row = rows[0]
        assert isinstance(row, Row)
        assert row.val == "test"
        assert row["val"] == "test"
        assert row[1] == "test"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Transactions
# ═══════════════════════════════════════════════════════════════════════════

class TestTransactions:
    @pytest.mark.asyncio
    async def test_commit(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        async with pool.acquire(readonly=False) as conn:
            async with conn.transaction(mode="IMMEDIATE"):
                await conn.execute("INSERT INTO t (val) VALUES (?)", ["committed"])
        rows = await pool.fetch_all("SELECT val FROM t")
        assert len(rows) == 1
        assert rows[0]["val"] == "committed"

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        with pytest.raises(RuntimeError, match="oops"):
            async with pool.acquire(readonly=False) as conn:
                async with conn.transaction():
                    await conn.execute("INSERT INTO t (val) VALUES (?)", ["bad"])
                    raise RuntimeError("oops")
        rows = await pool.fetch_all("SELECT * FROM t")
        assert len(rows) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. Savepoints
# ═══════════════════════════════════════════════════════════════════════════

class TestSavepoints:
    @pytest.mark.asyncio
    async def test_savepoint_release(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        async with pool.acquire(readonly=False) as conn:
            async with conn.transaction() as txn:
                await conn.execute("INSERT INTO t (val) VALUES (?)", ["outer"])
                async with txn.savepoint("sp1"):
                    await conn.execute("INSERT INTO t (val) VALUES (?)", ["inner"])
        rows = await pool.fetch_all("SELECT val FROM t ORDER BY val")
        assert [r["val"] for r in rows] == ["inner", "outer"]

    @pytest.mark.asyncio
    async def test_savepoint_rollback(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        async with pool.acquire(readonly=False) as conn:
            async with conn.transaction() as txn:
                await conn.execute("INSERT INTO t (val) VALUES (?)", ["keep"])
                with pytest.raises(ValueError, match="boom"):
                    async with txn.savepoint("sp1"):
                        await conn.execute("INSERT INTO t (val) VALUES (?)", ["discard"])
                        raise ValueError("boom")
        rows = await pool.fetch_all("SELECT val FROM t ORDER BY val")
        assert [r["val"] for r in rows] == ["keep"]

    @pytest.mark.asyncio
    async def test_invalid_savepoint_name(self, pool: ConnectionPool):
        async with pool.acquire(readonly=False) as conn:
            with pytest.raises(ValueError, match="Invalid savepoint"):
                await conn.savepoint("bad name!")


# ═══════════════════════════════════════════════════════════════════════════
# 9. Error Mapping
# ═══════════════════════════════════════════════════════════════════════════

class TestErrorMapping:
    def test_operational_locked(self):
        exc = sqlite3.OperationalError("database is locked")
        mapped = map_sqlite_error(exc, operation="execute")
        assert isinstance(mapped, SqliteConnectionError)

    def test_operational_no_such_table(self):
        exc = sqlite3.OperationalError("no such table: users")
        mapped = map_sqlite_error(exc, operation="fetch_all")
        assert isinstance(mapped, SqliteSchemaError)

    def test_integrity(self):
        exc = sqlite3.IntegrityError("UNIQUE constraint failed")
        mapped = map_sqlite_error(exc, operation="execute")
        assert isinstance(mapped, SqliteIntegrityError)

    def test_programming(self):
        exc = sqlite3.ProgrammingError("cannot operate on a closed cursor")
        mapped = map_sqlite_error(exc, operation="execute")
        assert isinstance(mapped, SqliteQueryError)

    def test_generic_database_error(self):
        exc = sqlite3.DatabaseError("some unknown error")
        mapped = map_sqlite_error(exc, operation="execute")
        assert isinstance(mapped, SqliteQueryError)

    def test_fallback(self):
        exc = ValueError("not a sqlite3 error")
        mapped = map_sqlite_error(exc, operation="execute")
        assert isinstance(mapped, SqliteError)


# ═══════════════════════════════════════════════════════════════════════════
# 10. Metrics
# ═══════════════════════════════════════════════════════════════════════════

class TestMetrics:
    @pytest.mark.asyncio
    async def test_query_metrics(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        await pool.execute("INSERT INTO t VALUES (1)")
        await pool.fetch_all("SELECT * FROM t")
        m = pool.metrics
        assert m.queries_total >= 3
        assert m.query_latency_ns > 0

    @pytest.mark.asyncio
    async def test_pool_size_metric(self, pool: ConnectionPool):
        assert pool.metrics.pool_size >= 2  # writer + min readers

    def test_snapshot(self):
        m = SqliteMetrics()
        m.record_query(1000, row_count=5)
        snap = m.snapshot()
        assert snap["queries_total"] == 1
        assert snap["query_rows_total"] == 5

    def test_reset(self):
        m = SqliteMetrics()
        m.record_query(1000)
        m.reset()
        assert m.queries_total == 0


# ═══════════════════════════════════════════════════════════════════════════
# 11. Pool Quick Methods
# ═══════════════════════════════════════════════════════════════════════════

class TestPoolQuickMethods:
    @pytest.mark.asyncio
    async def test_execute_returns_rowcount(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        rc = await pool.execute("INSERT INTO t (val) VALUES (?)", ["x"])
        assert rc == 1

    @pytest.mark.asyncio
    async def test_pool_closed_raises(self, tmp_db: str):
        pool = await create_pool(SqlitePoolConfig(path=tmp_db, pool_size=1, pool_min_size=1))
        await pool.close()
        with pytest.raises(SqliteConnectionError, match="closed"):
            await pool.execute("SELECT 1")


# ═══════════════════════════════════════════════════════════════════════════
# 12. Introspection
# ═══════════════════════════════════════════════════════════════════════════

class TestIntrospection:
    @pytest.mark.asyncio
    async def test_table_exists(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
        async with pool.acquire(readonly=True) as conn:
            assert await conn.table_exists("users") is True
            assert await conn.table_exists("nope") is False

    @pytest.mark.asyncio
    async def test_get_tables(self, pool: ConnectionPool):
        await pool.execute("CREATE TABLE alpha (id INTEGER PRIMARY KEY)")
        await pool.execute("CREATE TABLE beta (id INTEGER PRIMARY KEY)")
        async with pool.acquire(readonly=True) as conn:
            tables = await conn.get_tables()
            assert "alpha" in tables
            assert "beta" in tables

    @pytest.mark.asyncio
    async def test_get_columns(self, pool: ConnectionPool):
        await pool.execute(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INT)"
        )
        async with pool.acquire(readonly=True) as conn:
            cols = await conn.get_columns("t")
            names = [c["name"] for c in cols]
            assert "id" in names
            assert "name" in names
            assert "age" in names


# ═══════════════════════════════════════════════════════════════════════════
# 13. SQLiteAdapter Backward Compatibility
# ═══════════════════════════════════════════════════════════════════════════

class TestSQLiteAdapterCompat:
    @pytest.mark.asyncio
    async def test_adapter_connect_execute_disconnect(self, tmp_db: str):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        adapter = SQLiteAdapter()
        await adapter.connect(f"sqlite:///{tmp_db}")
        assert adapter.is_connected
        assert adapter.dialect == "sqlite"

        await adapter.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await adapter.execute("INSERT INTO t (val) VALUES (?)", ["hello"])

        rows = await adapter.fetch_all("SELECT val FROM t")
        assert len(rows) == 1
        assert rows[0]["val"] == "hello"

        row = await adapter.fetch_one("SELECT val FROM t WHERE id = 1")
        assert row is not None
        assert row["val"] == "hello"

        val = await adapter.fetch_val("SELECT count(*) FROM t")
        assert val == 1

        await adapter.disconnect()
        assert not adapter.is_connected

    @pytest.mark.asyncio
    async def test_adapter_transactions(self, tmp_db: str):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        adapter = SQLiteAdapter()
        await adapter.connect(f"sqlite:///{tmp_db}")

        await adapter.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")

        # Transaction commit
        await adapter.begin()
        await adapter.execute("INSERT INTO t (val) VALUES (?)", ["txn"])
        await adapter.commit()
        rows = await adapter.fetch_all("SELECT val FROM t")
        assert len(rows) == 1

        # Transaction rollback
        await adapter.begin()
        await adapter.execute("INSERT INTO t (val) VALUES (?)", ["rolled_back"])
        await adapter.rollback()
        rows = await adapter.fetch_all("SELECT val FROM t")
        assert len(rows) == 1  # still just 1 row

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_introspection(self, tmp_db: str):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        adapter = SQLiteAdapter()
        await adapter.connect(f"sqlite:///{tmp_db}")

        await adapter.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        assert await adapter.table_exists("users") is True
        assert await adapter.table_exists("orders") is False

        tables = await adapter.get_tables()
        assert "users" in tables

        cols = await adapter.get_columns("users")
        col_names = [c.name for c in cols]
        assert "id" in col_names
        assert "name" in col_names

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_savepoints(self, tmp_db: str):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        adapter = SQLiteAdapter()
        await adapter.connect(f"sqlite:///{tmp_db}")

        await adapter.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        await adapter.begin()
        await adapter.execute("INSERT INTO t (val) VALUES (?)", ["outer"])
        await adapter.savepoint("sp1")
        await adapter.execute("INSERT INTO t (val) VALUES (?)", ["inner"])
        await adapter.rollback_to_savepoint("sp1")
        await adapter.commit()

        rows = await adapter.fetch_all("SELECT val FROM t")
        assert len(rows) == 1
        assert rows[0]["val"] == "outer"

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_metrics(self, tmp_db: str):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        adapter = SQLiteAdapter()
        await adapter.connect(f"sqlite:///{tmp_db}")

        metrics = adapter.metrics
        assert metrics is not None
        assert metrics.pool_size >= 2  # writer + reader

        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_parse_url(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter

        assert SQLiteAdapter._parse_url("sqlite:///db.sqlite3") == "db.sqlite3"
        assert SQLiteAdapter._parse_url("sqlite:///:memory:") == ":memory:"
        assert SQLiteAdapter._parse_url("sqlite:///") == ":memory:"
