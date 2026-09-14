"""
Migration-system regressions from the AniWave migration audit (2026-09-14).

Each test pins a defect the audit found while porting a real backend:

F-01 -- ``ArrayField.base_field`` was never serialized, so a generated
        migration contained ``fields.ArrayField()`` and could not even be
        imported in a clean process.
F-02 -- A foreign key's column type was resolved through the live model
        registry at apply time; ``aq db migrate`` never imports workspace
        models, so every FK column fell back to INTEGER and UUID-keyed
        targets produced un-appliable DDL.
F-13 -- ``makemigrations --dry-run`` discarded the computed operations and
        reported "No model changes detected" even with a full initial
        migration pending.
F-14 -- ``aq db diff`` introspection keyed columns by database name (vs the
        model's attribute name), reported constraint-backing indexes as
        drift, and could not reconstruct unique constraints -- 40 false
        changes for a schema that matched its models exactly.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from aquilia.db import AquiliaDatabase
from aquilia.models import Index, Model, UniqueConstraint
from aquilia.models.fields import (
    ArrayField,
    CharField,
    ForeignKey,
    IntegerField,
    TextField,
    UUIDField,
)
from aquilia.models.migration import MigrationEngine, load_migration_module
from aquilia.models.migration.autodetect import detect_changes
from aquilia.models.migration.schema import ProjectState, Reference

_POSTGRES_URL = os.environ.get("AQUILIA_TEST_POSTGRES_URL")
needs_postgres = pytest.mark.skipif(not _POSTGRES_URL, reason="set AQUILIA_TEST_POSTGRES_URL to run")


class AuditOwner(Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=100)

    class Meta:
        table_name = "audit_owners"


class AuditEvent(Model):
    id = UUIDField(primary_key=True)
    owner = ForeignKey("AuditOwner", on_delete="CASCADE")
    tags = ArrayField(TextField(), size=10)
    score = IntegerField(null=True)

    class Meta:
        table_name = "audit_events"
        indexes = [Index(fields=["score"])]
        constraints = [UniqueConstraint(fields=["owner", "score"], name="uq_owner_score")]


MODELS = [AuditOwner, AuditEvent]


@pytest.fixture
def generated(tmp_path):
    """Generate the initial migration for MODELS and return (path, source)."""
    engine = MigrationEngine(tmp_path / "migrations")
    path = engine.make_migrations(MODELS)
    assert path is not None and path.exists()
    return path, path.read_text(encoding="utf-8")


# ── F-01: ArrayField serialization ──────────────────────────────────────────


def test_array_field_deconstruct_includes_base_field_and_size():
    spec = ArrayField(TextField(), size=7).deconstruct()

    assert spec["base_field"]["type"] == "TextField"
    assert spec["size"] == 7


def test_array_field_without_size_omits_it():
    assert "size" not in ArrayField(TextField()).deconstruct()


def test_generated_file_carries_array_base_field(generated):
    _, code = generated

    assert "ArrayField()" not in code
    assert "ArrayField(base_field=fields.TextField(), size=10)" in code


def test_generated_migration_loads_and_renders_array_type(generated):
    """The file must import and resolve its SQL type without any model registered."""
    node = load_migration_module(generated[0])

    events = next(op for op in node.operations if op.model == "AuditEvent")
    tags = events.table.columns["tags"]
    assert tags.sql_type("postgresql") == "TEXT[]"
    assert tags.sql_type("sqlite") == "TEXT"


# ── F-02: self-contained FK column types ────────────────────────────────────


def test_reference_records_target_pk_field_class(generated):
    node = load_migration_module(generated[0])

    events = next(op for op in node.operations if op.model == "AuditEvent")
    reference = events.table.columns["owner"].reference
    assert reference is not None
    assert reference.to_field == "UUIDField"


def test_migration_file_is_self_contained_for_fk_types(generated):
    _, code = generated

    assert 'to_field="UUIDField"' in code


def test_fk_column_type_survives_clean_process(tmp_path, generated):
    """Loading the file in a process with NO models registered must render UUID.

    This is the exact condition of ``aq db migrate`` (it never imports the
    workspace models): before the fix, the FK column rendered INTEGER and the
    DDL failed on PostgreSQL with 'incompatible types: integer and uuid'.
    """
    child = tmp_path / "_clean_load.py"
    child.write_text(
        textwrap.dedent(
            """
            import sys
            from pathlib import Path

            from aquilia.models.migration import load_migration_module
            from aquilia.models.migration.backends import get_backend
            from aquilia.models.migration.executor import compile_operations
            from aquilia.models.migration.schema import ProjectState
            from aquilia.models.registry import ModelRegistry

            assert not ModelRegistry.all_models(), "registry must be clean"

            node = load_migration_module(Path(sys.argv[1]))
            backend = get_backend("postgresql")
            sql = "\\n".join(
                statement.sql
                for operation in node.operations
                for statement in compile_operations([operation], ProjectState(), backend)
            )
            assert '"owner_id" UUID' in sql, sql
            print("OK")
            """
        )
    )
    proc = subprocess.run([sys.executable, str(child), str(generated[0])], capture_output=True, text=True)

    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_integer_fk_still_renders_integer(tmp_path):
    """The to_field spec must not regress the ordinary integer-keyed case."""

    class IntOwner(Model):
        name = CharField(max_length=50)

        class Meta:
            table_name = "audit_int_owners"

    class IntItem(Model):
        owner = ForeignKey("IntOwner")

        class Meta:
            table_name = "audit_int_items"

    engine = MigrationEngine(tmp_path / "migrations")
    path = engine.make_migrations([IntOwner, IntItem])
    assert path is not None

    node = load_migration_module(path)
    item = next(op for op in node.operations if op.model == "IntItem")
    sql_type = item.table.columns["owner"].sql_type("postgresql")

    from aquilia.models.migration.backends import get_backend

    assert get_backend("postgresql")._storage_type(sql_type) == "BIGINT"


def test_reference_equality_ignores_to_field():
    """Snapshots written before ``to_field`` existed must not diff as changed."""
    legacy = Reference(model="User", table="users")
    modern = Reference(model="User", table="users", to_field="UUIDField")

    assert legacy == modern
    assert hash(legacy) == hash(modern)


def test_reference_round_trips_through_dict():
    reference = Reference(model="User", table="users", to_field="CharField", to_field_kwargs={"max_length": 36})

    rebuilt = Reference.from_dict(reference.to_dict())

    assert rebuilt.to_field == "CharField"
    assert rebuilt.to_field_kwargs == {"max_length": 36}
    assert rebuilt == reference


# ── F-13: honest dry-run ────────────────────────────────────────────────────


def test_dry_run_reports_pending_operations(tmp_path):
    engine = MigrationEngine(tmp_path / "migrations")

    node = engine.make_migrations(MODELS, dry_run=True)

    assert node is not None, "dry-run must distinguish 'pending' from 'no changes'"
    assert node.operations, "the initial migration must have operations"
    assert not (tmp_path / "migrations").exists(), "dry-run must not write files"


def test_dry_run_returns_none_when_in_sync(tmp_path):
    engine = MigrationEngine(tmp_path / "migrations")
    assert engine.make_migrations(MODELS) is not None

    assert engine.make_migrations(MODELS, dry_run=True) is None


# ── F-14: no false drift against an identical schema ────────────────────────


async def _assert_no_drift(db_url: str) -> None:
    engine = MigrationEngine("migrations")  # directory irrelevant; not reused
    import tempfile
    from pathlib import Path as _P

    with tempfile.TemporaryDirectory() as td:
        engine = MigrationEngine(_P(td) / "migrations")
        assert engine.make_migrations(MODELS) is not None
        db = AquiliaDatabase(db_url)
        await db.connect()
        try:
            await engine.migrate(db)
            live = await ProjectState.from_database(db, model_classes=MODELS)
        finally:
            await db.disconnect()

    target = ProjectState.from_models(MODELS)
    operations = detect_changes(live, target, infer_renames=False)
    assert operations == [], [op.describe() for op in operations]


@pytest.mark.asyncio
async def test_no_false_drift_on_sqlite(tmp_path):
    await _assert_no_drift(f"sqlite:///{tmp_path / 'audit_drift.db'}")


@needs_postgres
@pytest.mark.asyncio
async def test_no_false_drift_on_postgres():
    await _assert_no_drift(_POSTGRES_URL)


@pytest.mark.asyncio
async def test_real_drift_is_still_detected(tmp_path):
    """The reconciliation must not mask genuine schema differences."""

    class AuditEvent2(Model):
        id = UUIDField(primary_key=True)
        owner = ForeignKey("AuditOwner", on_delete="CASCADE")
        tags = ArrayField(TextField(), size=10)
        score = IntegerField(null=True)
        extra = TextField(null=True)

        class Meta:
            table_name = "audit_events"

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        engine = MigrationEngine(Path(td) / "migrations")
        assert engine.make_migrations(MODELS) is not None
        db = AquiliaDatabase(f"sqlite:///{tmp_path / 'audit_true.db'}")
        await db.connect()
        try:
            await engine.migrate(db)
            live = await ProjectState.from_database(db, model_classes=[AuditOwner, AuditEvent2])
        finally:
            await db.disconnect()

    target = ProjectState.from_models([AuditOwner, AuditEvent2])
    descriptions = [op.describe() for op in detect_changes(live, target, infer_renames=False)]

    assert any("Add field" in d and "extra" in d for d in descriptions)
    # The unique constraint and index disappeared from the model world.
    assert any("Remove constraint" in d for d in descriptions)
    assert any("Remove index" in d for d in descriptions)


def test_generated_source_is_valid_python(generated):
    ast.parse(generated[1])
