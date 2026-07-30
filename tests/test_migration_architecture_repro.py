"""
Reproduction tests for Aquilia Database Migration Subsystem Issues:
- Bug 1: auto_migrate=False Still Executes Migrations / Table Creation
- Bug 2: Database Not Ready Should Be Warning, Not Fatal Error (Raises SchemaFault)
- Bug 3: Failed Migration / Schema Creation Leaves Partial Schema
"""

import os
import pytest
import sqlite3
from pathlib import Path

from aquilia.db.engine import AquiliaDatabase
from aquilia.integrations.database import DatabaseIntegration
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, IntegerField
from aquilia.faults.domains import SchemaFault, QueryFault, MigrationFault


@pytest.fixture(autouse=True)
def cleanup_registry():
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


@pytest.mark.asyncio
async def test_repro_bug_1_auto_migrate_false_creates_tables(tmp_path):
    """
    Bug 1 Repro: Setting auto_migrate=False in DatabaseIntegration still causes
    tables to be created on startup because auto_create defaults to True.
    """
    class DummyUser(Model):
        name = CharField(max_length=100)
        age = IntegerField(default=18)

    db_file = tmp_path / "bug1.db"
    db_url = f"sqlite:///{db_file}"

    integration = DatabaseIntegration(
        url=db_url,
        auto_migrate=False,
    )
    
    cfg = integration.to_dict()
    assert cfg["auto_migrate"] is False
    assert cfg["auto_create"] is True

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    # Server startup currently checks: if auto_create: await ModelRegistry.create_tables()
    # even when auto_migrate=False!
    auto_create = cfg["auto_create"]
    if auto_create:
        await ModelRegistry.create_tables()

    table_name = DummyUser._meta.table_name
    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table_name])
    row = cursor.fetchone()
    conn.close()
    await db.disconnect()

    # Table WAS created despite auto_migrate=False!
    assert row is not None, f"Bug 1 reproduced: auto_migrate=False still created table '{table_name}'!"


@pytest.mark.asyncio
async def test_repro_bug_2_db_not_ready_raises_schema_fault(tmp_path):
    """
    Bug 2 Repro: When db file does not exist and auto_migrate=False,
    server startup currently raises SchemaFault instead of logging a warning and continuing.
    """
    db_file = tmp_path / "nonexistent.db"
    db_url = f"sqlite:///{db_file}"

    from aquilia.models.startup_guard import check_db_ready

    db_ready = check_db_ready(
        db_url=db_url,
        migrations_dir=tmp_path / "migrations",
        auto_migrate=False,
        auto_create=False,
    )

    assert db_ready is False

    # Current server.py behavior when db_ready is False and auto_create is False:
    with pytest.raises(SchemaFault) as exc_info:
        if not db_ready:
            raise SchemaFault(
                table="(startup)",
                reason="Database is not ready. There are unapplied migrations or the database is missing.",
            )

    assert "Database is not ready" in str(exc_info.value)


@pytest.mark.asyncio
async def test_repro_bug_3_partial_schema_on_failed_creation(tmp_path):
    """
    Bug 3 Repro: If table creation / migration encounters an error midway,
    previously created tables remain committed on disk (partial schema).
    """
    db_file = tmp_path / "partial.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    # Table 1 statement
    await db.execute("CREATE TABLE table_one (id INTEGER PRIMARY KEY, name TEXT)")

    # Table 2 statement with duplicate column error -> fails
    with pytest.raises((QueryFault, SchemaFault, Exception)):
        await db.execute("CREATE TABLE table_two (id INT, id INT)")

    await db.disconnect()

    # Inspect database file -- table_one still exists because statements are executed without a single atomic transaction wrapper!
    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='table_one'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None, "Bug 3 reproduced: partial schema changes persisted after failure!"
