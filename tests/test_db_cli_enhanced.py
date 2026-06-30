from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

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
            use_dsl=True,
            migration_format="surp",
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
