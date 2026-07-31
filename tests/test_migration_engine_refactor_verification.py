"""
Verification suite for the migration engine's architectural invariants.

Pins the boundaries the design depends on:

1. ``ModelRegistry`` is not an execution authority -- it decides *what* to
   create and delegates *how* to the executor.
2. ``MigrationExecutor`` is the sole execution path for schema DDL.
3. Operations compile to typed :class:`Statement` objects, never to bare
   strings the caller has to interpret.
4. Initial schema creation is planned from models directly, with no synthetic
   empty-state diffing, and is recorded in ``aquilia_migrations``.
5. Backend adapters own dialect-specific error tolerance (MySQL 1061/1091).
6. A failing migration rolls back every statement that preceded it.
"""

import inspect
import sqlite3

import pytest

from aquilia.db.backends.mysql import MySQLAdapter
from aquilia.db.engine import AquiliaDatabase
from aquilia.faults.domains import MigrationFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, ForeignKey, IntegerField
from aquilia.models.migration import (
    MIGRATION_TABLE,
    CreateModel,
    MigrationExecutor,
    ProjectState,
    RunSQL,
    Statement,
    compile_operations,
    get_backend,
)


@pytest.fixture(autouse=True)
def reset_model_registry():
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


@pytest.mark.asyncio
async def test_model_registry_has_no_execution_authority():
    """ModelRegistry must not run DDL, manage transactions, or parse SQL text."""
    import aquilia.models.registry as reg_module

    source = inspect.getsource(reg_module)

    assert "for sql in statements:" not in source
    assert 'if sql.startswith("--"):' not in source
    assert 'dialect == "mysql" and _args' not in source

    assert "MigrationExecutor(" in source
    assert "await executor.apply_operations(" in source
    assert "await cls._drop_via_executor(" in source


@pytest.mark.asyncio
async def test_initial_schema_planned_directly_from_models():
    """State is built from models directly -- no fake migration, no empty-state diff."""

    class User(Model):
        username = CharField(max_length=50, unique=True)
        age = IntegerField(default=18)

    class Profile(Model):
        user = ForeignKey("User", on_delete="CASCADE")
        bio = CharField(max_length=200, null=True)

    state = ProjectState.from_models(ModelRegistry._topological_sort())

    assert {"User", "Profile"} <= set(state.tables)
    users = state.tables["User"]
    assert users.db_table == User._meta.table_name
    assert users.columns["username"].unique is True

    # The foreign key resolves to the *table* it targets, not just a model name.
    reference = state.tables["Profile"].columns["user"].reference
    assert reference is not None
    assert reference.model == "User"
    assert reference.table == User._meta.table_name
    assert reference.on_delete == "CASCADE"


@pytest.mark.asyncio
async def test_operations_compile_to_typed_statements():
    """Compilation yields Statement objects carrying execution metadata."""
    state = ProjectState()
    table = ProjectState.from_models([]).tables  # empty, for clarity
    assert table == {}

    class Thing(Model):
        title = CharField(max_length=100)

        class Meta:
            table_name = "typed_things"

    target = ProjectState.from_models([Thing])
    statements = compile_operations(
        [CreateModel(model="Thing", table=target.tables["Thing"])],
        state,
        get_backend("sqlite"),
    )

    assert len(statements) == 1
    statement = statements[0]
    assert isinstance(statement, Statement)
    assert "CREATE TABLE" in statement.sql
    assert statement.description
    assert statement.destructive is False
    assert statement.transactional is True


@pytest.mark.asyncio
async def test_mysql_adapter_encapsulates_error_tolerance():
    """Dialect-specific error tolerance belongs to the adapter, not the executor."""
    adapter = MySQLAdapter()

    class FakeException(Exception):
        def __init__(self, code):
            self.args = (code, "Duplicate key name")

    assert adapter.should_ignore_ddl_error(FakeException(1061)) is True
    assert adapter.should_ignore_ddl_error(FakeException(1091)) is True
    assert adapter.should_ignore_ddl_error(FakeException(1054)) is False


@pytest.mark.asyncio
async def test_migration_history_recorded_on_initial_schema(tmp_path):
    """Initial schema creation is recorded in aquilia_migrations like any migration."""

    class Order(Model):
        code = CharField(max_length=20)

    db_file = tmp_path / "initial_history.db"
    db = AquiliaDatabase(f"sqlite:///{db_file}")
    await db.connect()
    ModelRegistry.set_database(db)

    await ModelRegistry.create_tables(db)

    records = await MigrationExecutor(db).applied_records()
    assert any(record.revision == "0000_initial_schema" for record in records)
    # The record carries a checksum, which is what makes drift detectable.
    initial = next(record for record in records if record.revision == "0000_initial_schema")
    assert initial.checksum

    await db.disconnect()


@pytest.mark.asyncio
async def test_atomic_execution_rolls_back_on_failure(tmp_path):
    """A failing statement undoes every statement that preceded it in the batch."""

    class Good(Model):
        name = CharField(max_length=30)

        class Meta:
            table_name = "goods"

    db_file = tmp_path / "atomic_tx.db"
    db = AquiliaDatabase(f"sqlite:///{db_file}")
    await db.connect()

    state = ProjectState.from_models([Good])
    operations = [
        CreateModel(model="Good", table=state.tables["Good"]),
        RunSQL(sql="INVALID SQL SYNTAX THAT FAILS"),
    ]

    executor = MigrationExecutor(db)
    await executor.ensure_tracking_table()

    with pytest.raises(MigrationFault):
        await executor.apply_operations(operations, ProjectState(), description="failing batch")

    connection = sqlite3.connect(str(db_file))
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goods'").fetchall()
    connection.close()
    await db.disconnect()

    assert rows == [], "Every DDL statement in a failing batch must roll back."


@pytest.mark.asyncio
async def test_drop_tables_tears_down_schema(tmp_path):
    """Teardown goes through the executor and actually removes the tables."""
    db_file = tmp_path / "rollback_test.db"
    db = AquiliaDatabase(f"sqlite:///{db_file}")
    await db.connect()
    ModelRegistry.set_database(db)

    class Widget(Model):
        label = CharField(max_length=40)

    await ModelRegistry.create_tables(db)
    assert await MigrationExecutor(db).applied_revisions()

    dropped = await ModelRegistry.drop_tables(db)
    assert len(dropped) >= 1

    connection = sqlite3.connect(str(db_file))
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        [Widget._meta.table_name],
    ).fetchone()
    connection.close()
    await db.disconnect()

    assert row is None, "Widget table must be dropped after drop_tables()."


@pytest.mark.asyncio
async def test_tracking_table_name_is_shared_constant():
    """Everything that reads or writes migration history agrees on the table name."""
    assert MIGRATION_TABLE == "aquilia_migrations"

    db = AquiliaDatabase("sqlite:///:memory:")
    await db.connect()
    try:
        assert MigrationExecutor(db).table == MIGRATION_TABLE
    finally:
        await db.disconnect()
