"""
Production-scale stress tests for the migration system.

These are correctness-under-load checks, not micro-benchmarks: they assert that
behaviour holds at sizes where an accidental O(n^2) or a hash-ordered
collection would show up, and they bound wall-clock loosely enough not to be
flaky on a busy machine.

What is covered:

* Wide tables (1,000 columns) and large schemas (300 models).
* Deep foreign-key chains, which exercise dependency ordering.
* Cyclic references, which must be broken rather than hang or overflow.
* Repeated generation, which must be byte-identical (determinism).
* Repeated apply and rollback against a real SQLite database.
* Graph ordering over a wide dependency DAG.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from aquilia.db import AquiliaDatabase
from aquilia.faults.domains import MigrationConflictFault
from aquilia.models import fields
from aquilia.models.migration import (
    CreateModel,
    MigrationEngine,
    MigrationGraph,
    MigrationNode,
    ProjectState,
    Reference,
    compile_operations,
    detect_changes,
    get_backend,
    load_migration_module,
    render_migration_module,
)
from aquilia.models.migration.schema import ColumnState, TableState

DIALECTS = ("sqlite", "postgresql", "mysql", "oracle")


def _wide_table(model: str, table: str, column_count: int) -> TableState:
    columns = [ColumnState.of("id", fields.AutoField(primary_key=True))]
    columns += [ColumnState.of(f"field_{i}", fields.CharField(max_length=100)) for i in range(column_count)]
    return TableState.of(model, table, columns=columns)


def _chain(depth: int) -> ProjectState:
    """A -> B -> C -> ... chain of foreign keys, `depth` tables long."""
    tables = {}
    for i in range(depth):
        columns = [ColumnState.of("id", fields.AutoField(primary_key=True))]
        if i > 0:
            columns.append(
                ColumnState.of(
                    "parent",
                    fields.ForeignKey(f"Model{i - 1}"),
                    column="parent_id",
                    reference=Reference(model=f"Model{i - 1}", table=f"table_{i - 1}", column="id"),
                )
            )
        tables[f"Model{i}"] = TableState.of(f"Model{i}", f"table_{i}", columns=columns)
    return ProjectState(tables=tables)


# ── Scale ───────────────────────────────────────────────────────────────────


def test_thousand_column_table_compiles_on_every_dialect():
    table = _wide_table("Wide", "wide", 1_000)
    assert len(table.columns) == 1_001

    for dialect in DIALECTS:
        started = time.perf_counter()
        statements = compile_operations(
            [CreateModel(model="Wide", table=table)], ProjectState(), get_backend(dialect)
        )
        elapsed = time.perf_counter() - started

        assert statements
        assert "field_999" in statements[0].sql
        assert elapsed < 10.0, f"{dialect} took {elapsed:.1f}s for 1000 columns"


def test_three_hundred_model_schema_diffs_and_renders():
    after = ProjectState(
        tables={f"Model{i}": _wide_table(f"Model{i}", f"table_{i}", 8) for i in range(300)},
    )

    started = time.perf_counter()
    operations = detect_changes(ProjectState(), after)
    assert len(operations) == 300
    assert time.perf_counter() - started < 20.0

    node = MigrationNode(revision="0001", slug="bulk", operations=tuple(operations))
    source = render_migration_module(node)
    assert source.count("CreateModel(") == 300


def test_deep_foreign_key_chain_orders_parents_first():
    state = _chain(150)
    operations = detect_changes(ProjectState(), state)

    order = [operation.model for operation in operations]
    assert len(order) == 150
    position = {model: index for index, model in enumerate(order)}
    for i in range(1, 150):
        assert position[f"Model{i - 1}"] < position[f"Model{i}"], f"Model{i} created before its parent"


def test_wide_schema_applies_to_sqlite(tmp_path):
    """A 120-table schema must actually create on a real database."""
    state = _chain(120)
    operations = detect_changes(ProjectState(), state)

    async def run():
        db = AquiliaDatabase(f"sqlite:///{tmp_path / 'wide.db'}")
        await db.connect()
        try:
            from aquilia.models.migration import MigrationExecutor

            executor = MigrationExecutor(db)
            await executor.ensure_tracking_table()
            result = await executor.apply_operations(operations, ProjectState(), description="wide")
            assert result.statements_executed >= 120
            assert len(await db.get_tables()) >= 120
        finally:
            await db.disconnect()

    import asyncio

    asyncio.run(run())


# ── Cycles ──────────────────────────────────────────────────────────────────


def test_mutually_referencing_models_do_not_hang():
    """A -> B and B -> A must resolve by deferring one key, not loop forever."""
    a = TableState.of(
        "Alpha",
        "alpha",
        columns=[
            ColumnState.of("id", fields.AutoField(primary_key=True)),
            ColumnState.of(
                "beta",
                fields.ForeignKey("Beta", null=True),
                column="beta_id",
                reference=Reference(model="Beta", table="beta", column="id"),
            ),
        ],
    )
    b = TableState.of(
        "Beta",
        "beta",
        columns=[
            ColumnState.of("id", fields.AutoField(primary_key=True)),
            ColumnState.of(
                "alpha",
                fields.ForeignKey("Alpha", null=True),
                column="alpha_id",
                reference=Reference(model="Alpha", table="alpha", column="id"),
            ),
        ],
    )

    started = time.perf_counter()
    operations = detect_changes(ProjectState(), ProjectState(tables={"Alpha": a, "Beta": b}))
    assert time.perf_counter() - started < 5.0
    # Two creations plus the deferred key that closes the cycle.
    assert [type(operation).__name__ for operation in operations] == [
        "CreateModel",
        "CreateModel",
        "AddConstraint",
    ]

    # The first table created must not carry an inline REFERENCES to a table
    # that does not exist yet; that key arrives as a separate ALTER TABLE.
    statements = compile_operations(operations, ProjectState(), get_backend("postgresql"))
    assert "REFERENCES" not in statements[0].sql
    assert any("ADD CONSTRAINT" in statement.sql for statement in statements)


def test_cyclic_migration_graph_is_rejected():
    """A dependency cycle between migrations is an error, not a hang."""
    graph = MigrationGraph()
    graph.add(MigrationNode(revision="0001", slug="a", operations=(), dependencies=("0002",)))
    graph.add(MigrationNode(revision="0002", slug="b", operations=(), dependencies=("0001",)))

    with pytest.raises(MigrationConflictFault):
        graph.order()


def test_large_graph_orders_quickly():
    graph = MigrationGraph()
    for i in range(500):
        graph.add(
            MigrationNode(
                revision=f"{i:04d}",
                slug=f"m{i}",
                operations=(),
                dependencies=(f"{i - 1:04d}",) if i else (),
            )
        )

    started = time.perf_counter()
    order = graph.order()
    assert time.perf_counter() - started < 5.0
    assert len(order) == 500
    assert order[0] == "0000"
    assert order[-1] == "0499"


# ── Determinism ─────────────────────────────────────────────────────────────


def test_repeated_rendering_is_byte_identical():
    """Same state in, same bytes out -- what makes "no changes" trustworthy."""
    state = _chain(40)
    operations = detect_changes(ProjectState(), state)
    node = MigrationNode(revision="0001", slug="chain", operations=tuple(operations))

    renders = {render_migration_module(node) for _ in range(5)}
    assert len(renders) == 1


def test_repeated_generation_detects_no_changes(tmp_path):
    """Generating twice from unchanged state must produce nothing the second time."""
    engine = MigrationEngine(tmp_path / "migrations")
    state = _chain(30)

    node = MigrationNode(
        revision="20260101_000000",
        slug="initial",
        operations=tuple(detect_changes(ProjectState(), state)),
    )
    path = engine.migrations_dir
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{node.name}.py").write_text(render_migration_module(node), encoding="utf-8")
    engine.save_snapshot(state)

    # The snapshot now equals the state, so a diff against it is empty.
    assert detect_changes(engine.load_snapshot(), state) == []


def test_round_trip_survives_a_large_migration(tmp_path):
    """Load-then-render must reproduce the file for a non-trivial migration."""
    operations = detect_changes(ProjectState(), _chain(60))
    node = MigrationNode(revision="20260101_000000", slug="big", operations=tuple(operations))

    path = Path(tmp_path) / f"{node.name}.py"
    source = render_migration_module(node)
    path.write_text(source, encoding="utf-8")

    reloaded = render_migration_module(load_migration_module(path))
    assert reloaded.split("TEMPLATE_VERSION")[1] == source.split("TEMPLATE_VERSION")[1]


# ── Apply / rollback cycles ─────────────────────────────────────────────────


def test_repeated_apply_and_rollback_cycles(tmp_path):
    """Applying and rolling back repeatedly must leave no residue."""
    import asyncio

    engine = MigrationEngine(tmp_path / "migrations")
    engine.migrations_dir.mkdir(parents=True, exist_ok=True)

    state = _chain(25)
    node = MigrationNode(
        revision="20260101_000000",
        slug="cycle",
        operations=tuple(detect_changes(ProjectState(), state)),
    )
    (engine.migrations_dir / f"{node.name}.py").write_text(render_migration_module(node), encoding="utf-8")

    async def run():
        db = AquiliaDatabase(f"sqlite:///{tmp_path / 'cycle.db'}")
        await db.connect()
        try:
            for _ in range(3):
                await engine.migrate(db)
                status = await engine.status(db)
                assert status.is_current
                assert len(await db.get_tables()) >= 25

                await engine.migrate(db, target="zero")
                remaining = {t for t in await db.get_tables() if not t.startswith("aquilia_")}
                assert remaining == set(), f"tables survived rollback: {sorted(remaining)}"
        finally:
            await db.disconnect()

    asyncio.run(run())
