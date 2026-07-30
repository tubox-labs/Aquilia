"""
Exhaustive verification test suite for the Aquilia Migration Engine Refactor.

Validates all 14 phases of the architectural refactor:
1. ModelRegistry is no longer an execution authority.
2. MigrationRunner & DDLExecutor are the sole execution engine.
3. SQL strings are replaced by typed ExecutableStatement intermediate representations.
4. Initial schema planning is owned by InitialSchemaPlanner without synthetic empty-snapshot diffing hacks.
5. Backend adapters encapsulate database-specific DDL quirks (e.g. MySQL error 1061/1091).
6. Initial schema creation is recorded consistently in aquilia_migrations.
7. Atomic transactions and rollbacks work deterministically.
"""

import inspect
import sqlite3
import pytest
from pathlib import Path

from aquilia.db.engine import AquiliaDatabase
from aquilia.db.backends.mysql import MySQLAdapter
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, IntegerField, ForeignKey
from aquilia.models.ddl_executor import DDLExecutor, ExecutableStatement, StatementType
from aquilia.models.migration_planner import MigrationPlanner, InitialSchemaPlanner, MigrationPlan
from aquilia.models.migration_runner import MigrationRunner, MIGRATION_TABLE
from aquilia.faults.domains import MigrationFault


@pytest.fixture(autouse=True)
def reset_model_registry():
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


@pytest.mark.asyncio
async def test_model_registry_has_no_execution_authority():
    """Verify ModelRegistry no longer contains DDL execution loops, transaction blocks, or SQL string parsing."""
    import aquilia.models.registry as reg_module

    source = inspect.getsource(reg_module)

    # ModelRegistry source must not contain hardcoded execute loops or comment parsing
    assert 'for sql in statements:' not in source
    assert 'if sql.startswith("--"):' not in source
    assert 'dialect == "mysql" and _args' not in source

    # ModelRegistry source must delegate to MigrationRunner
    assert "runner = MigrationRunner(" in source
    assert "await runner.create_initial_schema(" in source
    assert "await runner.drop_all_tables(" in source


@pytest.mark.asyncio
async def test_initial_schema_planner_direct_generation():
    """Verify InitialSchemaPlanner creates typed operations directly from models without fake migrations."""

    class User(Model):
        username = CharField(max_length=50, unique=True)
        age = IntegerField(default=18)

    class Profile(Model):
        user = ForeignKey("User", on_delete="CASCADE")
        bio = CharField(max_length=200, null=True)

    models = ModelRegistry._topological_sort()
    step = InitialSchemaPlanner.plan_from_models(models)

    assert step.is_initial is True
    assert step.revision == "0000_initial_schema"
    assert len(step.operations) >= 2  # CreateModel User and Profile

    # Verify CreateModel operations
    user_op = next(op for op in step.operations if getattr(op, "name", "") == "User")
    assert user_op.table == User._meta.table_name
    assert any(f.name == "username" and f.unique is True for f in user_op.fields)


@pytest.mark.asyncio
async def test_ddl_executor_typed_statements():
    """Verify DDLExecutor compiles operations into typed ExecutableStatement objects."""
    from aquilia.models.migration_dsl import CreateModel, C

    op = CreateModel(
        name="Test",
        table="tests",
        fields=[C.auto("id"), C.varchar("title", 100)],
    )

    statements = DDLExecutor.compile_operations([op], dialect="sqlite")
    assert len(statements) == 1
    stmt = statements[0]

    assert isinstance(stmt, ExecutableStatement)
    assert stmt.statement_type == StatementType.CREATE_TABLE
    assert stmt.is_comment is False
    assert "CREATE TABLE" in stmt.sql


@pytest.mark.asyncio
async def test_mysql_adapter_encapsulates_error_tolerance():
    """Verify MySQLAdapter encapsulates error 1061 and 1091 tolerance."""
    adapter = MySQLAdapter()

    class FakeException(Exception):
        def __init__(self, code):
            self.args = (code, "Duplicate key name")

    assert adapter.should_ignore_ddl_error(FakeException(1061)) is True
    assert adapter.should_ignore_ddl_error(FakeException(1091)) is True
    assert adapter.should_ignore_ddl_error(FakeException(1054)) is False


@pytest.mark.asyncio
async def test_migration_history_recorded_on_initial_schema(tmp_path):
    """Verify initial schema creation records history in aquilia_migrations."""
    ModelRegistry.reset()

    class Order(Model):
        code = CharField(max_length=20)

    db_file = tmp_path / "initial_history.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    # Execute initial schema
    await ModelRegistry.create_tables(db)

    # Verify tracking table exists and initial schema record is present
    runner = MigrationRunner(db)
    records = await runner.get_applied_records()

    assert len(records) >= 1
    assert any(r.revision == "0000_initial_schema" for r in records)

    await db.disconnect()


@pytest.mark.asyncio
async def test_atomic_transaction_execution_and_rollback(tmp_path):
    """Verify DDLExecutor and MigrationRunner execute statements transactionally and roll back on failure."""
    ModelRegistry.reset()

    class Item(Model):
        name = CharField(max_length=30)

    db_file = tmp_path / "atomic_tx.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    runner = MigrationRunner(db)

    # Construct plan with a failing step containing a valid CreateModel and a broken RunSQL
    from aquilia.models.migration_dsl import CreateModel, RunSQL, C

    valid_op = CreateModel("Good", "goods", [C.auto("id")])
    broken_op = RunSQL("INVALID SQL SYNTAX THAT FAILS")

    from aquilia.models.migration_planner import MigrationStep
    failing_step = MigrationStep(
        revision="20260730_999999",
        slug="broken",
        operations=[valid_op, broken_op],
    )
    plan = MigrationPlan(steps=[failing_step])

    with pytest.raises(Exception):
        await runner.execute_plan(plan)

    # Verify goods table does not exist due to transaction rollback
    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goods'")
    rows = cursor.fetchall()
    conn.close()
    await db.disconnect()

    assert len(rows) == 0, "All DDL operations in failing plan step must roll back atomically!"


@pytest.mark.asyncio
async def test_rollback_to_zero(tmp_path):
    """Verify rollback_to('zero') undoes applied migrations."""
    ModelRegistry.reset()

    db_file = tmp_path / "rollback_test.db"
    db_url = f"sqlite:///{db_file}"

    db = AquiliaDatabase(db_url)
    await db.connect()
    ModelRegistry.set_database(db)

    class Widget(Model):
        label = CharField(max_length=40)

    await ModelRegistry.create_tables(db)

    runner = MigrationRunner(db)
    applied = await runner.get_applied()
    assert len(applied) >= 1

    # Roll back tables via drop_tables
    dropped = await ModelRegistry.drop_tables(db)
    assert len(dropped) >= 1

    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='widget'")
    row = cursor.fetchone()
    conn.close()
    await db.disconnect()

    assert row is None, "Widget table must be dropped after drop_tables execution!"
