"""
Executor behaviour that depends on the dialect.

Two things the executor must get right per backend:

* **The tracking table.** It is created before any migration runs, so its own
  DDL cannot go through the migration machinery -- it is rendered directly and
  must still be valid on each dialect (Oracle has no ``AUTOINCREMENT``, no
  ``SERIAL``, and no ``IF NOT EXISTS`` on ``CREATE TABLE``).
* **Ignorable DDL errors.** Re-running a migration that creates an index MySQL
  already has raises error 1061; dropping one it does not have raises 1091.
  Both are safely ignorable, and the decision belongs to the adapter, not the
  executor. Every other error must still fail the migration.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from aquilia.db.backends.mysql import MySQLAdapter
from aquilia.db.backends.sqlite import SQLiteAdapter
from aquilia.faults.domains import MigrationFault
from aquilia.models import fields
from aquilia.models.migration import (
    AddIndex,
    IndexState,
    MigrationExecutor,
    ProjectState,
    TableState,
)
from aquilia.models.migration.schema import ColumnState


def _mock_db(dialect: str, *, adapter: object | None = None) -> MagicMock:
    """A database that records SQL without executing it.

    ``_adapter`` is set explicitly rather than left to MagicMock: an
    auto-created attribute would answer ``should_ignore_ddl_error`` with a
    truthy Mock, making every error look ignorable.
    """
    db = MagicMock()
    db.dialect = dialect
    db._adapter = adapter
    db.execute = AsyncMock()
    db.fetch_all = AsyncMock(return_value=[])

    @asynccontextmanager
    async def transaction():
        yield

    db.transaction = transaction
    return db


# ── Tracking table ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("dialect", "expected", "forbidden"),
    [
        ("sqlite", "AUTOINCREMENT", "SERIAL"),
        ("postgresql", "SERIAL", "AUTOINCREMENT"),
        ("mysql", "AUTO_INCREMENT", "SERIAL"),
        ("oracle", "GENERATED ALWAYS AS IDENTITY", "AUTOINCREMENT"),
    ],
)
async def test_tracking_table_ddl_per_dialect(dialect, expected, forbidden):
    db = _mock_db(dialect)
    await MigrationExecutor(db).ensure_tracking_table()

    sql = db.execute.call_args[0][0]
    assert expected in sql
    assert forbidden not in sql
    assert "PRIMARY KEY" in sql
    for column in ("revision", "slug", "checksum", "applied_at"):
        assert column in sql


async def test_oracle_tracking_table_omits_if_not_exists():
    """Oracle has no ``CREATE TABLE IF NOT EXISTS``; emitting it is a syntax error."""
    db = _mock_db("oracle")
    await MigrationExecutor(db).ensure_tracking_table()
    assert "IF NOT EXISTS" not in db.execute.call_args[0][0]


async def test_tracking_table_name_is_quoted_per_dialect():
    mysql = _mock_db("mysql")
    await MigrationExecutor(mysql).ensure_tracking_table()
    assert "`aquilia_migrations`" in mysql.execute.call_args[0][0]

    postgres = _mock_db("postgresql")
    await MigrationExecutor(postgres).ensure_tracking_table()
    assert '"aquilia_migrations"' in postgres.execute.call_args[0][0]


# ── Ignorable DDL errors ────────────────────────────────────────────────────


def _mysql_error(code: int, message: str) -> Exception:
    """A chained exception shaped like the one aiomysql raises."""
    inner = Exception(code, message)
    outer = Exception("execute failed")
    outer.__cause__ = inner
    return outer


def _add_index_operation() -> tuple[list, ProjectState]:
    table = TableState.of(
        "Widget",
        "widgets",
        columns=[
            ColumnState.of("id", fields.AutoField(primary_key=True)),
            ColumnState.of("name", fields.CharField(max_length=50)),
        ],
    )
    state = ProjectState(tables={"Widget": table})
    operation = AddIndex(model="Widget", index=IndexState(name="idx_widgets_name", columns=("name",)))
    return [operation], state


async def test_mysql_duplicate_index_is_skipped():
    """Error 1061 means the index already exists -- the migration should proceed."""
    db = _mock_db("mysql", adapter=MySQLAdapter())
    attempts = 0

    async def execute(sql, params=None):
        nonlocal attempts
        if "INDEX" in sql.upper() and "CREATE" in sql.upper():
            attempts += 1
            raise _mysql_error(1061, "Duplicate key name 'idx_widgets_name'")

    db.execute = execute

    operations, state = _add_index_operation()
    result = await MigrationExecutor(db).apply_operations(operations, state, description="dup index")

    assert attempts == 1
    assert result.statements_skipped == 1
    assert result.statements_executed == 0


async def test_mysql_unknown_column_error_still_fails():
    """Only the ignorable codes are ignorable; 1054 must fail the migration."""
    db = _mock_db("mysql", adapter=MySQLAdapter())

    async def execute(sql, params=None):
        raise _mysql_error(1054, "Unknown column 'bad_col'")

    db.execute = execute

    operations, state = _add_index_operation()
    with pytest.raises(MigrationFault):
        await MigrationExecutor(db).apply_operations(operations, state, description="bad column")


async def test_sqlite_does_not_inherit_mysql_error_tolerance():
    """A 1061-shaped error on SQLite is meaningless and must not be swallowed."""
    db = _mock_db("sqlite", adapter=SQLiteAdapter())

    async def execute(sql, params=None):
        raise _mysql_error(1061, "Duplicate key name 'idx_widgets_name'")

    db.execute = execute

    operations, state = _add_index_operation()
    with pytest.raises(MigrationFault):
        await MigrationExecutor(db).apply_operations(operations, state, description="not mysql")
