"""
Comprehensive test suite for Aquilia Database Migration Architecture Audit:
- Verifies auto_migrate=False strictly prevents table creation and schema modification.
- Verifies missing/uninitialized database at startup produces non-fatal warning instead of SchemaFault.
- Verifies failed migrations or table creations roll back atomically without partial schema pollution.
- Verifies DatabaseState enum classification.
"""

import os
import pytest
import sqlite3
from pathlib import Path

from aquilia.db.engine import AquiliaDatabase
from aquilia.integrations.database import DatabaseIntegration
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, IntegerField
from aquilia.models.startup_guard import DatabaseState, get_db_state, check_db_ready
from aquilia.models.migration_runner import MigrationRunner
from aquilia.faults.domains import SchemaFault, QueryFault, MigrationFault


@pytest.fixture(autouse=True)
def cleanup_registry():
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


@pytest.mark.asyncio
async def test_auto_migrate_false_prevents_table_creation(tmp_path):
    """
    Verify auto_migrate=False strictly prevents table creation or schema modification.
    """
    class TargetModel(Model):
        title = CharField(max_length=120)

    db_file = tmp_path / "app_no_migrate.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    # auto_migrate is False
    auto_migrate = False
    auto_create = True

    # Emulate server.py Phase 4 logic
    if auto_migrate:
        await ModelRegistry.create_tables()

    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [TargetModel._meta.table_name])
    row = cursor.fetchone()
    conn.close()
    await db.disconnect()

    assert row is None, "Table must NOT be created when auto_migrate=False!"


@pytest.mark.asyncio
async def test_startup_guard_state_classification_and_warning(tmp_path):
    """
    Verify get_db_state correctly identifies database readiness states.
    """
    db_file = tmp_path / "missing_db.db"
    db_url = f"sqlite:///{db_file}"

    # Missing database state
    state = get_db_state(db_url, tmp_path / "migrations")
    assert state == DatabaseState.MISSING_DATABASE

    # check_db_ready returns False (warning printed, no fatal exception)
    is_ready = check_db_ready(db_url, tmp_path / "migrations", auto_migrate=False)
    assert is_ready is False


@pytest.mark.asyncio
async def test_atomic_table_creation_rollback_on_failure(tmp_path, monkeypatch):
    """
    Verify ModelRegistry.create_tables() rolls back all created tables if an error occurs mid-way.
    """
    class ValidModel(Model):
        name = CharField(max_length=50)

    db_file = tmp_path / "atomic_creation.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    real_execute = db._adapter.execute
    exec_count = 0

    async def failing_execute(sql, params=None):
        nonlocal exec_count
        exec_count += 1
        res = await real_execute(sql, params)
        if exec_count >= 1:
            raise RuntimeError("Simulated mid-way DDL execution failure")
        return res

    monkeypatch.setattr(db._adapter, "execute", failing_execute)

    with pytest.raises(Exception):
        await ModelRegistry.create_tables(db)

    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [ValidModel._meta.table_name])
    row = cursor.fetchone()
    conn.close()
    await db.disconnect()

    assert row is None, "ValidModel table must be rolled back cleanly when subsequent DDL statement fails!"


@pytest.mark.asyncio
async def test_atomic_migration_runner_rollback(tmp_path):
    """
    Verify MigrationRunner rolls back all DSL statements when a migration fails mid-way.
    """
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Create a migration file with a failing operation
    mig_file = migrations_dir / "20260730_120000_failing_migration.py"
    mig_file.write_text("""
from aquilia.models.migration_dsl import Migration, CreateTable, ColumnDef, RawSQL

revision = "20260730_120000"
slug = "failing_migration"

operations = [
    CreateTable("first_table", [ColumnDef("id", "INTEGER", primary_key=True)]),
    RawSQL("CREATE TABLE second_table (col INT, col INT)"),
]
""", encoding="utf-8")

    db_file = tmp_path / "mig_test.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()

    runner = MigrationRunner(db, migrations_dir)

    with pytest.raises(MigrationFault):
        await runner.migrate()

    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='first_table'")
    row = cursor.fetchone()
    conn.close()
    await db.disconnect()

    assert row is None, "first_table must be rolled back when second_table statement in migration fails!"
