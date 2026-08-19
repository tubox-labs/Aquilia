from __future__ import annotations

import asyncio
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from aquilia.cli.__main__ import cli
from aquilia.cli.commands.model_cmds import (
    cmd_check,
    cmd_diff,
    cmd_flush,
    cmd_history,
    cmd_makemigrations,
    cmd_migrate,
    cmd_reset,
    cmd_rollback,
    cmd_seed,
)
from aquilia.db import AquiliaDatabase
from aquilia.models.base import Model
from aquilia.models.fields_module import CharField, IntegerField


# Define a simple test model class
class CliTestProduct(Model):
    name = CharField(max_length=100)
    price = IntegerField()

    class Meta:
        table_name = "cli_test_products"


@pytest.fixture
def temp_workspace():
    # Setup temp path inside workspace to respect sandbox constraints
    temp_dir = Path.cwd() / "test_temp_db_cli"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    migrations_dir = temp_dir / "migrations"
    db_file = temp_dir / "test.db"
    db_url = f"sqlite:///{db_file}"

    yield temp_dir, migrations_dir, db_url

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_db_cli_enhanced_workflow(temp_workspace):
    temp_dir, migrations_dir, db_url = temp_workspace

    # ── 1. Makemigrations and Migrate ───────────────────────────────────────
    # Generate migrations for CliTestProduct
    # We monkeypatch model discovery to return only our CliTestProduct
    import aquilia.cli.commands.model_cmds as model_cmds

    original_discover = model_cmds._discover_models
    model_cmds._discover_models = lambda **kwargs: [CliTestProduct]

    try:
        generated = cmd_makemigrations(
            app=None,
            migrations_dir=str(migrations_dir),
            verbose=True,
        )
        assert len(generated) == 1
        migration_path = generated[0]
        assert migration_path.exists()

        # Apply migration
        applied = cmd_migrate(
            migrations_dir=str(migrations_dir),
            database_url=db_url,
            plan=False,
        )
        assert len(applied) == 1

        # ── 2. Test History Command ─────────────────────────────────────────────
        history = cmd_history(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            verbose=True,
        )
        assert len(history) == 1
        assert history[0]["revision"] is not None
        assert history[0]["slug"] is not None
        assert history[0]["checksum"] is not None

        # ── 3. Test Check Command (Passed) ──────────────────────────────────────
        check_passed = cmd_check(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            verbose=True,
        )
        assert check_passed is True

        # ── 4. Test Check Command (Integrity Mismatch) ──────────────────────────
        # Tamper with the migration file content
        migration_content = migration_path.read_text(encoding="utf-8")
        migration_path.write_text(migration_content + "\n# Tampered", encoding="utf-8")

        check_failed = cmd_check(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            verbose=True,
        )
        assert check_failed is False

        # Restore migration content
        migration_path.write_text(migration_content, encoding="utf-8")

        # ── 5. Test Diff Command ────────────────────────────────────────────────
        in_sync = cmd_diff(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            compare="models",
            verbose=True,
        )
        assert in_sync is True

        # ── 6. Test Seed Command ────────────────────────────────────────────────
        # Create seeds.py in temp_dir
        seed_file = temp_dir / "seeds.py"
        seed_content = (
            "async def seed(db):\n"
            "    await db.execute(\n"
            '        \'INSERT INTO "cli_test_products" ("name", "price") VALUES (?, ?)\',\n'
            "        ['Widget', 100]\n"
            "    )\n"
        )
        seed_file.write_text(seed_content, encoding="utf-8")

        cmd_seed(
            database_url=db_url,
            seed_file=str(seed_file),
            verbose=True,
        )

        # Verify seeding worked
        async def verify_seeding():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                rows = await db.fetch_all('SELECT * FROM "cli_test_products"')
                assert len(rows) == 1
                assert rows[0]["name"] == "Widget"
                assert rows[0]["price"] == 100
            finally:
                await db.disconnect()

        asyncio.run(verify_seeding())

        # ── 7. Test Flush Command ───────────────────────────────────────────────
        cmd_flush(
            database_url=db_url,
            verbose=True,
            yes=True,
        )

        # Verify flushing worked (rows = 0)
        async def verify_flushing():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                rows = await db.fetch_all('SELECT * FROM "cli_test_products"')
                assert len(rows) == 0
                tables = await db.get_tables()
                assert "cli_test_products" in tables
            finally:
                await db.disconnect()

        asyncio.run(verify_flushing())

        # ── 8. Test Rollback Command ────────────────────────────────────────────
        # Seed again
        async def seed_again():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                await db.execute('INSERT INTO "cli_test_products" ("name", "price") VALUES (?, ?)', ["Widget", 100])
            finally:
                await db.disconnect()

        asyncio.run(seed_again())

        # Rollback migration
        rolled_back = cmd_rollback(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            target="zero",
            fake=False,
            plan=False,
        )
        assert len(rolled_back) == 1

        # Verify rollback dropped the table
        async def verify_rollback():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                tables = await db.get_tables()
                assert "cli_test_products" not in tables
            finally:
                await db.disconnect()

        asyncio.run(verify_rollback())

        # ── 9. Test Reset Command ───────────────────────────────────────────────
        # Run migrations again first
        cmd_migrate(
            migrations_dir=str(migrations_dir),
            database_url=db_url,
            plan=False,
        )

        # Add a product
        async def add_product():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                await db.execute('INSERT INTO "cli_test_products" ("name", "price") VALUES (?, ?)', ["Gadget", 200])
            finally:
                await db.disconnect()

        asyncio.run(add_product())

        # Reset
        cmd_reset(
            database_url=db_url,
            migrations_dir=str(migrations_dir),
            verbose=True,
            yes=True,
        )

        # Reset drops all tables and runs migrations. Table should exist, but rows should be 0.
        async def verify_reset():
            db = AquiliaDatabase(db_url)
            await db.connect()
            try:
                tables = await db.get_tables()
                assert "cli_test_products" in tables
                rows = await db.fetch_all('SELECT * FROM "cli_test_products"')
                assert len(rows) == 0
            finally:
                await db.disconnect()

        asyncio.run(verify_reset())

    finally:
        model_cmds._discover_models = original_discover


def test_db_migrate_imports_workspace_enum_fields(tmp_path, monkeypatch):
    """The installed CLI can deserialize EnumFields from workspace modules.

    A console-script launch does not guarantee that the workspace working
    directory appears on ``sys.path``. Generated migrations nevertheless store
    durable enum references such as ``modules.users.models.UserStatus``, so the
    migration loader must make the owning workspace importable before executing
    the migration module.
    """
    workspace_root = tmp_path / "enum_workspace"
    users_module = workspace_root / "modules" / "users"
    migrations_dir = workspace_root / "migrations"
    users_module.mkdir(parents=True)
    migrations_dir.mkdir()

    (workspace_root / "workspace.py").write_text(
        '"""Regression workspace for migration import resolution."""\n',
        encoding="utf-8",
    )
    (users_module / "models.py").write_text(
        'from enum import Enum\n\nclass UserStatus(Enum):\n    ACTIVE = "active"\n',
        encoding="utf-8",
    )
    (migrations_dir / "20260819_093002_user.py").write_text(
        '"""Create the user table with a workspace EnumField."""\n\n'
        "from aquilia.models import fields\n"
        "from aquilia.models.migration.operations import CreateModel, Operation\n"
        "from aquilia.models.migration.schema import ColumnState, TableState\n\n"
        "class Meta:\n"
        '    """Migration metadata read by the migration runner."""\n\n'
        '    revision = "20260819_093002"\n'
        '    slug = "user"\n'
        "    dependencies = []\n"
        "    replaces = []\n"
        "    atomic = True\n\n"
        "operations: list[Operation] = [\n"
        "    CreateModel(\n"
        '        model="User",\n'
        "        table=TableState.of(\n"
        '            "User",\n'
        '            "users",\n'
        "            columns=[\n"
        "                ColumnState.of(\n"
        '                    "status",\n'
        "                    fields.EnumField(\n"
        '                        enum_class="modules.users.models.UserStatus",\n'
        "                    ),\n"
        "                ),\n"
        '                ColumnState.of("id", fields.BigAutoField()),\n'
        "            ],\n"
        "        ),\n"
        "    ),\n"
        "]\n",
        encoding="utf-8",
    )

    resolved_root = str(workspace_root.resolve())
    monkeypatch.chdir(workspace_root)
    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if entry not in {"", resolved_root}])
    for module_name in list(sys.modules):
        if module_name == "modules" or module_name.startswith("modules."):
            monkeypatch.delitem(sys.modules, module_name, raising=False)

    database_path = workspace_root / "db.sqlite3"
    result = CliRunner().invoke(
        cli,
        [
            "db",
            "migrate",
            "--migrations-dir",
            str(migrations_dir),
            "--database-url",
            f"sqlite:///{database_path}",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Applied 1 migration(s)" in result.output
    with sqlite3.connect(database_path) as connection:
        table = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'").fetchone()
    assert table == ("users",)
