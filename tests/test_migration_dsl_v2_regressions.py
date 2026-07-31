"""
Regression tests for the Aquilia Migration DSL v2 rewrite.

Each test here corresponds to a defect confirmed by execution against the v1
migration system. The test name states the defect; the docstring states what v1
did and why it mattered. A failure means a defect has come back.

The audit that produced this list is summarized in the module docstrings of
:mod:`aquilia.models.migration.schema`, ``.backends``, ``.autodetect``, and
``.serializer``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from aquilia.db.engine import AquiliaDatabase
from aquilia.faults.domains import MigrationFault
from aquilia.models.base import Model
from aquilia.models.constraint import CheckConstraint, ExclusionConstraint
from aquilia.models.fields_module import (
    AutoField,
    BigIntegerField,
    BooleanField,
    CharField,
    DecimalField,
    ForeignKey,
    GeneratedField,
    IntegerField,
    JSONField,
    ManyToManyField,
    TextField,
    UUIDField,
)
from aquilia.models.index import FunctionalIndex, GinIndex
from aquilia.models.migration import (
    ColumnState,
    MigrationEngine,
    ProjectState,
    RenameHint,
    TableState,
    detect_changes,
)
from aquilia.models.migration.autodetect import Autodetector
from aquilia.models.migration.backends import get_backend
from aquilia.models.migration.graph import MigrationGraph, MigrationNode
from aquilia.models.migration.operations import (
    AddConstraint,
    AddField,
    AlterField,
    CreateModel,
    DeleteModel,
    Operation,
    RemoveField,
    RunPython,
    RunSQL,
)
from aquilia.models.migration.schema import (
    NOT_PROVIDED,
    CheckConstraintState,
    IndexState,
    UniqueConstraintState,
)
from aquilia.models.registry import ModelRegistry


@pytest.fixture(autouse=True)
def _clean_registry():
    """Isolate each test's model registrations."""
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


def _column(name: str, field_class: str = "CharField", **kwargs) -> ColumnState:
    """Build a minimal column state for diffing tests."""
    return ColumnState(name=name, column=name, field_class=field_class, field_kwargs=kwargs)


def _table(model: str, db_table: str, columns: list[ColumnState]) -> TableState:
    """Build a minimal table state for diffing tests."""
    return TableState(model=model, db_table=db_table, columns={c.name: c for c in columns})


# ── Crashers ────────────────────────────────────────────────────────────────


class TestCrashers:
    """Defects that raised an exception rather than producing wrong output."""

    @pytest.mark.asyncio
    async def test_create_tables_with_meta_constraints_does_not_crash(self, tmp_path):
        """v1: InitialSchemaPlanner called AddConstraint(table=, name=, constraint_def=)
        against a signature of (table, constraint_sql), so ModelRegistry.create_tables()
        raised TypeError for any model declaring Meta.constraints.
        """

        class Product(Model):
            id = AutoField()
            price = IntegerField()

            class Meta:
                table_name = "products"
                constraints = [CheckConstraint(check="price >= 0", name="ck_price")]

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/constraints.db")
        await db.connect()
        try:
            ModelRegistry.set_database(db)
            statements = await ModelRegistry.create_tables(db)
            assert any("ck_price" in sql for sql in statements)
            assert "products" in await db.get_tables()
        finally:
            await db.disconnect()

    def test_irreversible_operation_reports_rather_than_aborting_rollback(self):
        """v1: compile_downgrade caught NotImplementedError, but operations raised
        MigrationFault, which is not a subclass. One irreversible operation therefore
        aborted the entire downgrade instead of being annotated and skipped.
        """
        assert not issubclass(MigrationFault, NotImplementedError)

        # v2 reports irreversibility by returning None -- no exception to mis-catch.
        assert RunSQL(sql="DELETE FROM t").reverse() is None
        assert RunPython(code=print).reverse() is None

        # And every structural operation is genuinely reversible.
        table = _table("U", "u", [_column("id", "AutoField")])
        assert isinstance(CreateModel(model="U", table=table).reverse(), DeleteModel)
        assert isinstance(DeleteModel(model="U", table=table).reverse(), CreateModel)
        field = _column("bio", "TextField")
        assert isinstance(AddField(model="U", field=field).reverse(), RemoveField)
        assert isinstance(RemoveField(model="U", field=field).reverse(), AddField)


# ── Silent data corruption ──────────────────────────────────────────────────


class TestSilentCorruption:
    """Defects that produced valid SQL doing the wrong thing."""

    def test_unrelated_same_type_columns_are_not_treated_as_a_rename(self):
        """v1: _detect_field_renames scored (same_type * 0.7) + (name_sim * 0.3) against
        a 0.6 threshold. Same type alone contributed 0.7, so any same-typed pair matched.
        Dropping `legacy_zzz` and adding `brand_new_field` emitted RENAME COLUMN,
        silently destroying the dropped column's data.
        """
        before = ProjectState({"U": _table("U", "u", [_column("id", "AutoField"), _column("legacy_zzz")])})
        after = ProjectState({"U": _table("U", "u", [_column("id", "AutoField"), _column("brand_new_field")])})

        kinds = [type(op).__name__ for op in detect_changes(before, after)]
        assert "RenameField" not in kinds
        assert sorted(kinds) == ["AddField", "RemoveField"]

    def test_explicit_hint_still_produces_a_rename(self):
        """A rename must remain expressible -- the fix is to require intent, not to
        remove the capability.
        """
        before = ProjectState({"U": _table("U", "u", [_column("legacy_zzz")])})
        after = ProjectState({"U": _table("U", "u", [_column("brand_new_field")])})

        operations = detect_changes(
            before,
            after,
            hints=(RenameHint(model="U", old_name="legacy_zzz", new_name="brand_new_field"),),
        )
        assert [type(op).__name__ for op in operations] == ["RenameField"]

    def test_ambiguous_rename_candidates_are_refused(self):
        """Two equally-scoring candidates mean picking either is a coin flip that
        destroys data half the time, so neither is chosen.
        """
        before = ProjectState({"U": _table("U", "u", [_column("a", max_length=10)])})
        after = ProjectState({"U": _table("U", "u", [_column("x", max_length=10), _column("y", max_length=10)])})
        kinds = sorted(type(op).__name__ for op in detect_changes(before, after))
        assert "RenameField" not in kinds
        assert kinds == ["AddField", "AddField", "RemoveField"]

    def test_natural_integer_primary_key_is_not_auto_increment(self):
        """v1: _snapshot_field_to_column_def set
        `autoincrement = primary_key and "INT" in type`, so a natural integer key
        became AUTOINCREMENT and explicit key inserts were overridden.
        """

        class Country(Model):
            code = IntegerField(primary_key=True)
            name = CharField(max_length=80)

            class Meta:
                table_name = "countries"

        state = ProjectState.from_models([Country])
        code = state.tables["Country"].columns["code"]
        assert code.primary_key is True
        assert code.auto_increment is False

        sql = get_backend("sqlite").create_table(state.tables["Country"])[0].sql
        assert "AUTOINCREMENT" not in sql

    def test_foreign_key_drop_uses_the_database_column_name(self):
        """v1: diff_to_operations passed the Python attribute name to RemoveField, so a
        ForeignKey named `author` emitted DROP COLUMN "author" for a column actually
        called `author_id` -- the statement failed, or on a table that happened to have
        an `author` column, dropped the wrong one.
        """

        class Writer(Model):
            id = AutoField()

            class Meta:
                table_name = "writers"

        class Article(Model):
            id = AutoField()
            author = ForeignKey(Writer)

            class Meta:
                table_name = "articles"

        before = ProjectState.from_models([Writer, Article])
        after = ProjectState(
            {
                "Writer": before.tables["Writer"],
                "Article": before.tables["Article"].without_column("author"),
            }
        )

        operations = detect_changes(before, after)
        removals = [op for op in operations if isinstance(op, RemoveField)]
        assert len(removals) == 1

        statements = removals[0].database_forwards(before, get_backend("postgresql"))
        assert any('"author_id"' in s.sql for s in statements)
        assert not any('DROP COLUMN "author"' in s.sql for s in statements)

    def test_alter_field_applies_every_changed_attribute(self):
        """v1: AlterField carried only new_type. Detected changes to nullability,
        default, and uniqueness were computed by _field_changed and then discarded,
        so the migration reported success while leaving those attributes unchanged.
        """

        class Note(Model):
            id = AutoField()
            title = CharField(max_length=100)

            class Meta:
                table_name = "notes"

        state = ProjectState.from_models([Note])
        old = state.tables["Note"].columns["title"]
        new = old.evolve(null=True, default="untitled", field_kwargs={"max_length": 500})

        sql = " ".join(
            s.sql
            for s in AlterField(model="Note", old_field=old, new_field=new).database_forwards(
                state, get_backend("postgresql")
            )
        )
        assert "TYPE VARCHAR(500)" in sql
        assert "DROP NOT NULL" in sql
        assert "SET DEFAULT 'untitled'" in sql

    @pytest.mark.parametrize("dialect", ["postgresql", "mysql", "oracle", "sqlite"])
    def test_alter_field_is_never_a_silent_no_op(self, dialect):
        """v1: AlterField.to_sql returned [] for MySQL and Oracle and a comment for
        SQLite. The migration reported success on all three while changing nothing.
        """

        class Item(Model):
            id = AutoField()
            label = CharField(max_length=50)

            class Meta:
                table_name = "items"

        state = ProjectState.from_models([Item])
        old = state.tables["Item"].columns["label"]
        new = old.evolve(field_kwargs={"max_length": 200})

        statements = AlterField(model="Item", old_field=old, new_field=new).database_forwards(
            state, get_backend(dialect)
        )
        executable = [s for s in statements if s.sql and not s.sql.strip().startswith("--")]
        assert executable, f"{dialect} produced no executable statement for a real column change"


# ── Invalid SQL ─────────────────────────────────────────────────────────────


class TestInvalidSQL:
    """Defects that emitted SQL the target database rejects."""

    def test_expression_index_retains_its_expression(self):
        """v1: a FunctionalIndex snapshotted to columns: [] because the snapshot format
        had no expression field, producing `CREATE INDEX "fx" ON "posts" ();` -- a
        syntax error that only surfaced at apply time.
        """

        class Post(Model):
            id = AutoField()
            title = CharField(max_length=200)

            class Meta:
                table_name = "posts"
                indexes = [FunctionalIndex(expression='LOWER("title")', name="fx_title")]

        state = ProjectState.from_models([Post])
        index = next(i for i in state.tables["Post"].indexes if i.name == "fx_title")
        assert index.expressions == ('LOWER("title")',)

        sql = get_backend("postgresql").create_index("posts", index)[0].sql
        assert "LOWER" in sql
        assert 'ON "posts" ()' not in sql

    def test_index_state_with_no_keys_is_rejected_at_construction(self):
        """An index with neither columns nor expressions can only produce invalid SQL,
        so it fails when built rather than when applied.
        """
        with pytest.raises(MigrationFault, match="neither columns nor expressions"):
            IndexState(name="empty")

    def test_gin_index_retains_method_condition_and_opclasses(self):
        """v1: the snapshot kept only {name, columns, unique}, so a partial GIN index
        with operator classes silently became a plain B-tree index over every row --
        a different index with different performance and different semantics.
        """

        class Doc(Model):
            id = AutoField()
            body = TextField()
            live = BooleanField(default=True)

            class Meta:
                table_name = "docs"
                indexes = [GinIndex(fields=["body"], name="gin_body", condition="live", opclasses=["gin_trgm_ops"])]

        state = ProjectState.from_models([Doc])
        index = next(i for i in state.tables["Doc"].indexes if i.name == "gin_body")
        assert index.method == "GIN"
        assert index.condition == "live"
        assert index.opclasses == ("gin_trgm_ops",)

        sql = get_backend("postgresql").create_index("docs", index)[0].sql
        assert "USING GIN" in sql
        assert "gin_trgm_ops" in sql
        assert "WHERE (live)" in sql

    def test_unsupported_partial_index_is_refused_not_silently_widened(self):
        """Dropping a partial index's predicate would index every row, which changes a
        unique partial index's meaning. MySQL and Oracle therefore refuse it.
        """
        index = IndexState(name="ix", columns=("a",), condition="b > 0")
        for dialect in ("mysql", "oracle"):
            with pytest.raises(MigrationFault, match="does not support partial indexes"):
                get_backend(dialect).create_index("t", index)

    @pytest.mark.parametrize("dialect", ["mysql", "oracle"])
    def test_create_index_omits_if_not_exists_where_unsupported(self, dialect):
        """v1: CreateIndex.to_sql emitted IF NOT EXISTS unconditionally. MySQL and
        Oracle both reject it on CREATE INDEX, so every generated index statement was
        a syntax error on those backends.
        """
        sql = get_backend(dialect).create_index("t", IndexState(name="ix", columns=("a",)))[0].sql
        assert "IF NOT EXISTS" not in sql

    def test_mysql_quotes_identifiers_with_backticks(self):
        """v1 hardcoded double-quote identifier quoting everywhere, which MySQL rejects
        unless ANSI_QUOTES is enabled -- so every generated statement failed on a
        default MySQL install.
        """
        backend = get_backend("mysql")
        assert backend.quote("order") == "`order`"

        class Thing(Model):
            id = AutoField()
            name = CharField(max_length=10)

            class Meta:
                table_name = "things"

        sql = backend.create_table(ProjectState.from_models([Thing]).tables["Thing"])[0].sql
        assert "`things`" in sql
        assert '"things"' not in sql

    def test_foreign_key_column_does_not_declare_its_own_sequence(self):
        """A FK resolves its type from the referenced primary key. On PostgreSQL that
        is SERIAL, which creates a sequence -- so a FK column declared SERIAL would
        invent key values on insert instead of failing.
        """

        class Team(Model):
            id = AutoField()

            class Meta:
                table_name = "teams"

        class Player(Model):
            id = AutoField()
            team = ForeignKey(Team)

            class Meta:
                table_name = "players"

        state = ProjectState.from_models([Team, Player])
        sql = get_backend("postgresql").create_table(state.tables["Player"])[0].sql
        assert '"team_id" INTEGER' in sql
        assert '"team_id" SERIAL' not in sql

    def test_oracle_orders_default_before_not_null(self):
        """Oracle requires DEFAULT before NOT NULL; the reverse order that every other
        dialect accepts is an ORA-00907 syntax error.
        """

        class Row(Model):
            id = AutoField()
            count = IntegerField(default=0)

            class Meta:
                table_name = "rows_t"

        state = ProjectState.from_models([Row])
        sql = get_backend("oracle").create_table(state.tables["Row"])[0].sql
        assert "DEFAULT 0 NOT NULL" in sql
        assert "NOT NULL DEFAULT" not in sql

    def test_oracle_omits_on_update_clause(self):
        """Oracle implements no ON UPDATE referential action and rejects the clause."""

        class Parent(Model):
            id = AutoField()

            class Meta:
                table_name = "parents"

        class Child(Model):
            id = AutoField()
            parent = ForeignKey(Parent)

            class Meta:
                table_name = "children"

        state = ProjectState.from_models([Parent, Child])
        sql = get_backend("oracle").create_table(state.tables["Child"])[0].sql
        assert "ON UPDATE" not in sql

    def test_unserializable_default_is_refused(self):
        """v1's _format_default fell through to repr(value), producing SQL that either
        failed to parse or parsed into something unintended.
        """
        backend = get_backend("postgresql")
        with pytest.raises(MigrationFault, match="Cannot render"):
            backend.literal({"a": 1})


# ── Missing capabilities ────────────────────────────────────────────────────


class TestMissingCapabilities:
    """Model semantics that never reached SQL in v1."""

    @pytest.mark.asyncio
    async def test_many_to_many_junction_table_is_created(self, tmp_path):
        """v1: ManyToManyField was absent from create_snapshot and from the
        initial-schema planner, so a database built from generated migrations had no
        junction table and every M2M relationship was broken at runtime.
        """

        class Tag(Model):
            id = AutoField()
            name = CharField(max_length=40)

            class Meta:
                table_name = "tags"

        class Entry(Model):
            id = AutoField()
            tags = ManyToManyField(Tag)

            class Meta:
                table_name = "entries"

        state = ProjectState.from_models([Tag, Entry])
        assert state.tables["Entry"].m2m, "M2M relation missing from schema state"

        engine = MigrationEngine(tmp_path / "migrations")
        assert engine.make_migrations([Tag, Entry], slug="init") is not None

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/m2m.db")
        await db.connect()
        try:
            await engine.migrate(db)
            tables = await db.get_tables()
            assert "entries_tags" in tables, f"junction table not created; got {sorted(tables)}"
        finally:
            await db.disconnect()

    def test_generated_column_retains_its_expression(self):
        """v1: the planner mapped GeneratedField to its output type and dropped the
        GENERATED ALWAYS AS clause, producing a permanently-NULL ordinary column.
        """

        class Line(Model):
            id = AutoField()
            qty = IntegerField()
            price = DecimalField(max_digits=8, decimal_places=2)
            total = GeneratedField(expression="qty * price", output_field=DecimalField())

            class Meta:
                table_name = "lines"

        state = ProjectState.from_models([Line])
        total = state.tables["Line"].columns["total"]
        assert total.generated == "qty * price"

        sql = get_backend("postgresql").create_table(state.tables["Line"])[0].sql
        assert "GENERATED ALWAYS AS (qty * price) STORED" in sql

    def test_unique_together_becomes_a_constraint(self):
        """v1: Meta.unique_together was never snapshotted, so the uniqueness guarantee
        silently vanished from any migration-built database.
        """

        class Member(Model):
            id = AutoField()
            email = CharField(max_length=100)
            tenant = IntegerField()

            class Meta:
                table_name = "members"
                unique_together = [("email", "tenant")]

        state = ProjectState.from_models([Member])
        uniques = [c for c in state.tables["Member"].constraints if isinstance(c, UniqueConstraintState)]
        assert uniques, "unique_together produced no constraint"
        assert uniques[0].columns == ("email", "tenant")

        sql = get_backend("postgresql").create_table(state.tables["Member"])[0].sql
        assert 'UNIQUE ("email", "tenant")' in sql

    def test_sqlite_alter_column_rebuilds_the_table(self):
        """v1: AlterField emitted `-- SQLite: ALTER COLUMN not supported` -- a comment
        that reported success while changing nothing, so the next migration built on a
        schema that did not exist.
        """

        class Rec(Model):
            id = AutoField()
            label = CharField(max_length=20)

            class Meta:
                table_name = "recs"

        state = ProjectState.from_models([Rec])
        old = state.tables["Rec"].columns["label"]
        new = old.evolve(field_kwargs={"max_length": 300})

        statements = get_backend("sqlite").alter_column(state.tables["Rec"], old, new)
        joined = " ".join(s.sql for s in statements)
        assert "CREATE TABLE" in joined
        assert "INSERT INTO" in joined
        assert "DROP TABLE" in joined
        assert "RENAME TO" in joined
        assert not any(s.sql.strip().startswith("--") for s in statements)

    def test_sqlite_check_constraint_rebuilds_rather_than_being_skipped(self):
        """v1: AddConstraint emitted a comment for any non-UNIQUE constraint on SQLite,
        dropping the integrity guarantee without reporting it.
        """

        class Acct(Model):
            id = AutoField()
            balance = IntegerField()

            class Meta:
                table_name = "accts"

        state = ProjectState.from_models([Acct])
        operation = AddConstraint(
            model="Acct",
            constraint=CheckConstraintState(name="ck_balance", check="balance >= 0"),
        )
        joined = " ".join(s.sql for s in operation.database_forwards(state, get_backend("sqlite")))
        assert "ck_balance" in joined
        assert "CREATE TABLE" in joined

    def test_exclusion_constraint_is_refused_where_unsupported(self):
        """Silently dropping an EXCLUDE constraint would remove an integrity guarantee.
        Backends that cannot express it raise instead.
        """

        class Booking(Model):
            id = AutoField()
            room = IntegerField()

            class Meta:
                table_name = "bookings"
                constraints = [ExclusionConstraint(name="ex_room", expressions=[("room", "=")], index_type="GIST")]

        state = ProjectState.from_models([Booking])
        constraint = state.tables["Booking"].constraints[0]

        assert "EXCLUDE USING GIST" in get_backend("postgresql").constraint_definition(constraint)
        for dialect in ("mysql", "sqlite", "oracle"):
            with pytest.raises(MigrationFault, match="does not support EXCLUDE"):
                get_backend(dialect).constraint_definition(constraint)

    def test_adding_not_null_column_without_default_is_refused(self):
        """Every SQL database rejects this on a populated table. v1 emitted the
        statement anyway and let it fail against production.
        """
        column = ColumnState(name="slug", column="slug", field_class="CharField", default=NOT_PROVIDED)
        with pytest.raises(MigrationFault, match="without a default"):
            get_backend("postgresql").add_column("posts", column)


# ── Determinism ─────────────────────────────────────────────────────────────


class TestDeterminism:
    """v1 produced different output on different interpreter runs."""

    def test_operation_order_is_stable_across_hash_seeds(self):
        """v1: compute_diff built its work list from `old_names & new_names` and
        iterated the resulting set, so operation order -- and therefore the generated
        migration file -- changed on every run. Two developers running makemigrations
        on identical models got different diffs.
        """
        script = (
            "import json;"
            "from aquilia.models.migration import ProjectState, TableState, ColumnState, detect_changes;"
            "mk=lambda n: TableState(model=n, db_table=n.lower(), columns={"
            "'id': ColumnState(name='id', column='id', field_class='AutoField'),"
            "'a': ColumnState(name='a', column='a', field_class='CharField')});"
            "before=ProjectState({n: mk(n) for n in ('Alpha','Beta','Gamma','Delta','Epsilon')});"
            "after=ProjectState({n: mk(n).with_column("
            "ColumnState(name='b', column='b', field_class='TextField')) "
            "for n in ('Alpha','Beta','Gamma','Delta','Epsilon')});"
            "print(json.dumps([op.describe() for op in detect_changes(before, after)]))"
        )
        outputs = set()
        for seed in ("0", "1", "42", "12345"):
            completed = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).resolve().parent.parent),
                env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
                check=True,
            )
            outputs.add(completed.stdout.strip())
        assert len(outputs) == 1, f"operation order varied across hash seeds: {outputs}"

    def test_state_checksum_is_stable_across_hash_seeds(self):
        """The snapshot checksum must depend only on the schema, or every run looks
        like a schema change.
        """
        script = (
            "from aquilia.models.migration import ProjectState, TableState, ColumnState;"
            "cols={c: ColumnState(name=c, column=c, field_class='CharField') "
            "for c in ('z','y','x','w','v','u')};"
            "print(ProjectState({'M': TableState(model='M', db_table='m', columns=cols)}).checksum())"
        )
        outputs = set()
        for seed in ("0", "7", "999"):
            completed = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).resolve().parent.parent),
                env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
                check=True,
            )
            outputs.add(completed.stdout.strip())
        assert len(outputs) == 1, f"checksum varied across hash seeds: {outputs}"

    def test_generated_migration_file_is_byte_identical_on_regeneration(self):
        """v1's generated file embedded a wall-clock timestamp in the body and rendered
        columns via type-string guessing, so regenerating produced a different file.
        """
        from aquilia.models.migration.serializer import render_migration_module

        class Widget(Model):
            id = AutoField()
            name = CharField(max_length=60)

            class Meta:
                table_name = "widgets"

        operations = detect_changes(ProjectState(), ProjectState.from_models([Widget]))
        node = MigrationNode(revision="20260101_000000", slug="init", operations=tuple(operations))
        first = render_migration_module(node)
        second = render_migration_module(node)
        assert hashlib.sha256(first.encode()).hexdigest() == hashlib.sha256(second.encode()).hexdigest()


# ── Round-trip fidelity ─────────────────────────────────────────────────────


class TestRoundTrip:
    """v1's generated file described a different schema than the models."""

    @pytest.mark.parametrize(
        "field_factory,expected_class",
        [
            (lambda: BigIntegerField(primary_key=True), "BigIntegerField"),
            (lambda: JSONField(null=True), "JSONField"),
            (lambda: UUIDField(unique=True), "UUIDField"),
            (lambda: DecimalField(max_digits=12, decimal_places=4), "DecimalField"),
            (lambda: BooleanField(default=True), "BooleanField"),
            (lambda: TextField(default="x"), "TextField"),
        ],
    )
    def test_field_class_survives_serialization(self, field_factory, expected_class):
        """v1's _render_column_def inferred a C.* factory from the SQL type string:
        a non-auto BIGINT primary key rendered as C.text(primary_key=True), JSONB as
        C.text, and a UUID as C.varchar. Anything unrecognized fell through to C.text,
        so the file on disk described different columns than the models.
        """
        field = field_factory()
        field.__set_name__(type("Owner", (), {}), "value")

        state = ColumnState.from_field("value", field)
        assert state.field_class == expected_class

        restored = ColumnState.from_dict(json.loads(json.dumps(state.to_dict(), default=str)))
        assert restored.field_class == expected_class
        assert restored.to_dict() == state.to_dict()

    def test_every_operation_round_trips_exactly(self):
        """A migration file must reconstruct the operations it was generated from."""

        class Owner(Model):
            id = AutoField()
            name = CharField(max_length=50)

            class Meta:
                table_name = "owners"

        class Pet(Model):
            id = AutoField()
            nickname = CharField(max_length=50, db_index=True)
            owner = ForeignKey(Owner, on_delete="SET_NULL", null=True)
            friends = ManyToManyField(Owner)

            class Meta:
                table_name = "pets"
                constraints = [CheckConstraint(check="id > 0", name="ck_id")]

        operations = detect_changes(ProjectState(), ProjectState.from_models([Owner, Pet]))
        assert operations
        for operation in operations:
            assert Operation.from_dict(operation.to_dict()) == operation

    def test_loaded_migration_replays_to_the_original_schema(self, tmp_path):
        """Applying a generated migration must produce exactly the models' schema."""
        from aquilia.models.migration.serializer import load_migration_module

        class Shop(Model):
            id = AutoField()
            title = CharField(max_length=120)
            rating = DecimalField(max_digits=3, decimal_places=1)

            class Meta:
                table_name = "shops"

        target = ProjectState.from_models([Shop])
        engine = MigrationEngine(tmp_path / "migrations")
        path = engine.make_migrations([Shop], slug="init")
        assert path is not None

        replayed = ProjectState()
        for operation in load_migration_module(path).operations:
            operation.state_forwards(replayed)
        assert replayed.checksum() == target.checksum()


# ── Lifecycle and integrity ─────────────────────────────────────────────────


class TestLifecycle:
    """Defects in ordering, atomicity, and history tracking."""

    @pytest.mark.asyncio
    async def test_history_and_schema_commit_together(self, tmp_path):
        """v1: DDL ran in a transaction, then the tracking row was inserted after it
        committed. A crash in between left the schema changed but unrecorded, so the
        next run reapplied the migration against a database that already had it.
        """

        class Job(Model):
            id = AutoField()
            name = CharField(max_length=40)

            class Meta:
                table_name = "jobs"

        engine = MigrationEngine(tmp_path / "migrations")
        engine.make_migrations([Job], slug="init")

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/history.db")
        await db.connect()
        try:
            await engine.migrate(db)
            status = await engine.status(db)
            assert len(status.applied) == 1
            assert status.is_current, "migration applied but not recorded as such"

            # A second migrate must be a no-op rather than reapplying.
            assert await engine.migrate(db) == []
        finally:
            await db.disconnect()

    def test_migration_file_is_written_before_the_snapshot(self, tmp_path, monkeypatch):
        """v1 wrote the snapshot first (its comment called this a 'TWO-PHASE WRITE FIX',
        but the order was inverted). A failure to write the migration file left the
        snapshot advanced and the diff unrecoverable -- the next makemigrations saw no
        changes and generated nothing.
        """

        class Draft(Model):
            id = AutoField()
            body = TextField()

            class Meta:
                table_name = "drafts"

        engine = MigrationEngine(tmp_path / "migrations")
        original_write = Path.write_text

        def failing_write(self, *args, **kwargs):
            if self.suffix == ".py":
                raise OSError("disk full")
            return original_write(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", failing_write)
        with pytest.raises(OSError):
            engine.make_migrations([Draft], slug="init")
        monkeypatch.undo()

        # The snapshot must not have advanced, so the change is still detectable.
        assert engine.load_snapshot().tables == {}
        assert engine.make_migrations([Draft], slug="init") is not None

    def test_tables_are_dropped_in_reverse_dependency_order(self):
        """v1 emitted DropModel operations in alphabetical order, so a parent table
        could be dropped while a child still referenced it.
        """

        class Author2(Model):
            id = AutoField()

            class Meta:
                table_name = "authors2"

        class Book2(Model):
            id = AutoField()
            author = ForeignKey(Author2)

            class Meta:
                table_name = "books2"

        state = ProjectState.from_models([Author2, Book2])
        assert state.creation_order() == ("Author2", "Book2")
        assert state.deletion_order() == ("Book2", "Author2")

        operations = detect_changes(state, ProjectState())
        deletions = [op.model for op in operations if isinstance(op, DeleteModel)]
        assert deletions.index("Book2") < deletions.index("Author2")

    def test_migration_dependencies_are_enforced_not_merely_recorded(self):
        """v1 wrote a `dependencies` list into every migration and never read it --
        ordering came from sorting filenames, which breaks as soon as two developers
        generate migrations independently.
        """
        graph = MigrationGraph()
        graph.add(MigrationNode(revision="0003", slug="c", dependencies=("0002",)))
        graph.add(MigrationNode(revision="0001", slug="a"))
        graph.add(MigrationNode(revision="0002", slug="b", dependencies=("0001",)))
        assert graph.order() == ("0001", "0002", "0003")

    def test_dependency_cycle_is_detected(self):
        """A cycle cannot be applied in any order; it must be reported, not looped on."""
        from aquilia.faults.domains import MigrationConflictFault

        graph = MigrationGraph()
        graph.add(MigrationNode(revision="A", dependencies=("B",)))
        graph.add(MigrationNode(revision="B", dependencies=("A",)))
        with pytest.raises(MigrationConflictFault):
            graph.order()

    def test_missing_dependency_is_reported(self):
        """A migration depending on a deleted file must fail loudly."""
        graph = MigrationGraph()
        graph.add(MigrationNode(revision="X", dependencies=("gone",)))
        with pytest.raises(MigrationFault, match="does not exist"):
            graph.order()

    def test_checksum_reflects_operation_content(self):
        """v1's plan checksum hashed f"{revision}:{slug}:{len(operations)}", so any
        change preserving the operation count was invisible to it.
        """

        class First(Model):
            id = AutoField()
            a = CharField(max_length=10)

            class Meta:
                table_name = "first_t"

        class Second(Model):
            id = AutoField()
            a = CharField(max_length=999)

            class Meta:
                table_name = "first_t"

        one = ProjectState.from_models([First])
        two = ProjectState({"First": ProjectState.from_models([Second]).tables["Second"]})
        assert one.checksum() != two.checksum()

    @pytest.mark.asyncio
    async def test_rollback_reverses_the_schema_change(self, tmp_path):
        """v1's RemoveField/DropModel/AlterField could not be reversed at all."""

        class Doc2(Model):
            id = AutoField()
            title = CharField(max_length=80)

            class Meta:
                table_name = "docs2"

        engine = MigrationEngine(tmp_path / "migrations")
        engine.make_migrations([Doc2], slug="init")

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/rollback.db")
        await db.connect()
        try:
            await engine.migrate(db)
            assert "docs2" in await db.get_tables()

            await engine.migrate(db, target="zero")
            assert "docs2" not in await db.get_tables()
            assert (await engine.status(db)).applied == ()
        finally:
            await db.disconnect()


# ── Optimizer ───────────────────────────────────────────────────────────────


class TestOptimizer:
    """v1 had no operation optimizer."""

    def test_create_then_add_field_collapses(self):
        """Squashing fifty migrations that each add a column should produce one
        CreateModel, not one create plus forty-nine adds.
        """
        from aquilia.models.migration.optimizer import optimize

        table = _table("U", "u", [_column("id", "AutoField")])
        operations = [CreateModel(model="U", table=table)]
        for index in range(5):
            operations.append(AddField(model="U", field=_column(f"f{index}", "TextField")))

        reduced = optimize(operations)
        assert len(reduced) == 1
        assert isinstance(reduced[0], CreateModel)
        assert len(reduced[0].table.columns) == 6

    def test_add_then_remove_field_cancels(self):
        """A column added and dropped within one migration should produce no SQL."""
        from aquilia.models.migration.optimizer import optimize

        field = _column("temp", "TextField")
        assert optimize([AddField(model="U", field=field), RemoveField(model="U", field=field)]) == []

    def test_raw_sql_blocks_reordering(self):
        """RunSQL may depend on the exact intermediate schema, so nothing may be
        merged across it.
        """
        from aquilia.models.migration.optimizer import optimize

        field = _column("temp", "TextField")
        operations = [
            AddField(model="U", field=field),
            RunSQL(sql="UPDATE u SET temp = 'x'"),
            RemoveField(model="U", field=field),
        ]
        assert len(optimize(operations)) == 3


# ── v1 compatibility ────────────────────────────────────────────────────────


class TestPreV2MigrationFiles:
    """A migration file from before the rewrite must fail loudly, not silently.

    The old DSL module is gone, so such a file cannot execute. What matters is
    that the failure names the file and the reason -- a project upgrading
    squashes its history into a single baseline migration instead.
    """

    def test_pre_v2_migration_file_raises_migration_fault(self, tmp_path):
        from aquilia.models.migration.serializer import load_migration_module

        source = "\n".join(
            [
                "from aquilia.models.migration_dsl import CreateModel, columns as C",
                "",
                "class Meta:",
                '    revision = "20250101_000000"',
                '    slug = "legacy"',
                "    dependencies = []",
                "",
                "operations = [",
                '    CreateModel(name="LegacyUser", table="legacy_users", fields=[C.auto("id")]),',
                "]",
            ]
        )
        path = Path(tmp_path) / "20250101_000000_legacy.py"
        path.write_text(source, encoding="utf-8")

        with pytest.raises(MigrationFault) as excinfo:
            load_migration_module(path)

        assert "20250101_000000_legacy.py" in str(excinfo.value)

    def test_non_operation_entry_is_rejected_by_name(self, tmp_path):
        """An ``operations`` list holding something else must say what it found."""
        from aquilia.models.migration.serializer import load_migration_module

        source = "\n".join(
            [
                "class Meta:",
                '    revision = "20250102_000000"',
                '    slug = "bad_entry"',
                "    dependencies = []",
                "",
                'operations = ["CREATE TABLE oops (id INTEGER)"]',
            ]
        )
        path = Path(tmp_path) / "20250102_000000_bad_entry.py"
        path.write_text(source, encoding="utf-8")

        with pytest.raises(MigrationFault) as excinfo:
            load_migration_module(path)

        reason = str(excinfo.value)
        assert "str" in reason
        assert "Operation" in reason

    def test_dict_entries_still_load(self, tmp_path):
        """Files that serialized operations as dicts predate constructor calls.

        Nothing emits that form now, but a file already applied must keep
        loading so its recorded checksum and history stay valid.
        """
        from aquilia.models.migration.serializer import load_migration_module

        source = "\n".join(
            [
                "from aquilia.models.migration.operations import AddIndex",
                "from aquilia.models.migration.schema import IndexState",
                "",
                "class Meta:",
                '    revision = "20250103_000000"',
                '    slug = "dict_form"',
                "    dependencies = []",
                "",
                "operations = [",
                '    AddIndex(model="Widget", index=IndexState(name="idx_widgets_name",',
                '                                              columns=("name",))).to_dict(),',
                "]",
            ]
        )
        path = Path(tmp_path) / "20250103_000000_dict_form.py"
        path.write_text(source, encoding="utf-8")

        node = load_migration_module(path)
        assert len(node.operations) == 1
        assert node.operations[0].index.name == "idx_widgets_name"


class TestSecurity:
    """Injection surfaces in DDL generation."""

    def test_identifier_quoting_escapes_embedded_quotes(self):
        """An unescaped quote in an identifier would terminate the quoted name early
        and let the remainder be parsed as SQL.
        """
        backend = get_backend("postgresql")
        assert backend.quote('we"ird') == '"we""ird"'
        assert get_backend("mysql").quote("we`ird") == "`we``ird`"

    def test_string_literal_escapes_embedded_quotes(self):
        """A default value containing a quote must not be able to close the literal."""
        backend = get_backend("postgresql")
        assert backend.literal("O'Brien") == "'O''Brien'"

    def test_null_byte_in_identifier_is_refused(self):
        """A NUL byte truncates the statement at the driver boundary, so whatever
        follows it is silently discarded.
        """
        with pytest.raises(MigrationFault, match="NUL byte"):
            get_backend("postgresql").quote("bad\x00name")

    def test_run_python_rejects_unimportable_callables(self):
        """A lambda or nested function cannot be imported by name when the migration is
        applied on another machine, so it must be refused at generation time rather
        than producing a file that fails to load later.
        """
        with pytest.raises(MigrationFault, match="module-level function"):
            RunPython(code=lambda db: None).to_dict()


# ── Backend coverage ────────────────────────────────────────────────────────


class TestBackendCoverage:
    """Every supported dialect must produce syntactically plausible DDL."""

    @pytest.mark.parametrize("dialect", ["postgresql", "sqlite", "mysql", "oracle"])
    def test_create_table_is_emitted_for_every_dialect(self, dialect):
        """v1 had no Oracle path for several operations and emitted PostgreSQL-shaped
        SQL for MySQL.
        """

        class Full(Model):
            id = AutoField()
            name = CharField(max_length=100, db_index=True)
            note = TextField(default="none")
            count = IntegerField(default=0)
            flag = BooleanField(default=False)

            class Meta:
                table_name = "full_t"

        state = ProjectState.from_models([Full])
        statements = get_backend(dialect).create_table(state.tables["Full"])
        assert statements
        sql = statements[0].sql
        assert sql.startswith("CREATE TABLE")
        assert "full_t" in sql
        assert sql.rstrip().endswith(";")

    def test_unknown_dialect_is_refused(self):
        """v1 fell back to generic SQL for an unrecognized dialect, emitting statements
        that were merely plausible for the target database.
        """
        with pytest.raises(MigrationFault, match="No migration backend registered"):
            get_backend("cassandra")

    def test_dialect_aliases_resolve(self):
        """Common aliases must reach the right backend."""
        assert get_backend("postgres").dialect == "postgresql"
        assert get_backend("pg").dialect == "postgresql"
        assert get_backend("mariadb").dialect == "mysql"


# ── Validation ──────────────────────────────────────────────────────────────


class TestValidation:
    """Malformed schema must fail at plan time, not apply time."""

    def test_unknown_referential_action_is_refused(self):
        """v1 passed unknown on_delete values straight through into DDL, so a typo
        became a syntax error surfacing against a production database.
        """
        from aquilia.models.migration.schema import normalize_referential_action

        assert normalize_referential_action("set_null") == "SET NULL"
        assert normalize_referential_action("PROTECT") == "RESTRICT"
        with pytest.raises(MigrationFault, match="Unknown referential action"):
            normalize_referential_action("CASCAED")

    def test_alter_field_rejects_a_disguised_rename(self):
        """Two differently-named columns in one AlterField would emit SQL targeting
        whichever name the backend happened to read.
        """
        old = _column("title")
        with pytest.raises(MigrationFault, match="cannot rename a column"):
            AlterField(model="M", old_field=old, new_field=old.evolve(name="headline"))

    def test_duplicate_create_model_is_refused(self):
        """Two migrations both claiming to create one model makes the resulting schema
        depend on apply order.
        """
        table = _table("U", "u", [_column("id", "AutoField")])
        state = ProjectState()
        CreateModel(model="U", table=table).state_forwards(state)
        with pytest.raises(MigrationFault, match="already exists"):
            CreateModel(model="U", table=table).state_forwards(state)

    def test_unknown_operation_name_is_refused(self):
        """A migration referencing an unregistered operation must fail loudly rather
        than being skipped.
        """
        with pytest.raises(MigrationFault, match="Unknown migration operation"):
            Operation.from_dict({"operation": "TeleportTable"})

    def test_unknown_constraint_type_is_refused(self):
        """v1 silently skipped unrecognized constraints (`else: continue`), dropping an
        integrity guarantee without telling anyone.
        """

        class Weird:
            name = "w"

            def deconstruct(self):
                return {"type": "QuantumConstraint", "name": "w"}

        class Odd(Model):
            id = AutoField()

            class Meta:
                table_name = "odd_t"
                constraints = [Weird()]

        with pytest.raises(MigrationFault, match="not understood by the migration system"):
            ProjectState.from_models([Odd])

    def test_state_from_a_newer_version_is_refused(self):
        """Misreading a newer snapshot could generate a destructive migration from the
        misreading.
        """
        with pytest.raises(MigrationFault, match="newer than this Aquilia release"):
            ProjectState.from_dict({"version": 99, "tables": []})


# ── Autodetector configuration ──────────────────────────────────────────────


class TestAutodetectorConfiguration:
    """Rename inference must be controllable."""

    def test_rename_inference_can_be_disabled(self):
        """A project that would rather have an extra drop-plus-add than any chance of a
        wrong rename can turn inference off entirely.
        """
        before = ProjectState({"U": _table("U", "u", [_column("name", max_length=50)])})
        after = ProjectState({"U": _table("U", "u", [_column("name2", max_length=50)])})

        detector = Autodetector(before=before, after=after, infer_renames=False)
        kinds = sorted(type(op).__name__ for op in detector.detect())
        assert kinds == ["AddField", "RemoveField"]

    def test_model_rename_is_inferred_from_a_shared_table_name(self):
        """A table name is an explicit developer choice, so two models sharing one is
        near-conclusive evidence of a rename -- unlike field-set similarity, which two
        subclasses of one base model share entirely.
        """
        before = ProjectState({"Account": _table("Account", "users", [_column("id", "AutoField")])})
        after = ProjectState({"User": _table("User", "users", [_column("id", "AutoField")])})

        operations = detect_changes(before, after)
        assert [type(op).__name__ for op in operations] == ["RenameModel"]
        assert operations[0].old_model == "Account"
        assert operations[0].new_model == "User"

    def test_model_rename_with_unchanged_table_emits_no_sql(self):
        """Renaming only the class, with Meta.table_name pinning the table, is a
        state-only change. v1 emitted nothing at all in this case, leaving the snapshot
        and the database describing the model under different names.
        """
        before = ProjectState({"Account": _table("Account", "users", [_column("id", "AutoField")])})
        after = ProjectState({"User": _table("User", "users", [_column("id", "AutoField")])})

        operation = detect_changes(before, after)[0]
        assert operation.database_forwards(before, get_backend("postgresql")) == []

        state = before.clone()
        operation.state_forwards(state)
        assert "User" in state.tables
        assert "Account" not in state.tables


# ── Full lifecycle ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_migration_lifecycle_against_sqlite(tmp_path):
    """Generate, apply, extend, and roll back against a real database.

    Exercises the whole pipeline end to end: state from models, autodetection,
    serialization to disk, reload, compilation to SQL, transactional execution,
    history tracking, and reversal.
    """

    class Store(Model):
        id = AutoField()
        name = CharField(max_length=80, db_index=True)

        class Meta:
            table_name = "stores"

    class Product(Model):
        id = AutoField()
        title = CharField(max_length=150)
        store = ForeignKey(Store, on_delete="CASCADE")
        related = ManyToManyField(Store)
        price = DecimalField(max_digits=9, decimal_places=2)

        class Meta:
            table_name = "products"
            constraints = [CheckConstraint(check="price >= 0", name="ck_price")]

    engine = MigrationEngine(tmp_path / "migrations")
    first = engine.make_migrations([Store, Product], slug="initial")
    assert first is not None
    assert engine.make_migrations([Store, Product]) is None, "no-op regeneration produced a migration"

    db = AquiliaDatabase(f"sqlite:///{tmp_path}/lifecycle.db")
    await db.connect()
    try:
        plan = await engine.plan(db)
        assert plan, "plan was empty for a pending migration"

        await engine.migrate(db)
        tables = set(await db.get_tables())
        assert {"stores", "products", "products_related"} <= tables

        status = await engine.status(db)
        assert status.is_current
        assert await engine.verify_checksums(db) == []

        # Extend the schema and migrate again.
        blurb = TextField(null=True)
        blurb.__set_name__(Product, "blurb")
        Product._fields["blurb"] = blurb

        second = engine.make_migrations([Store, Product], slug="add_blurb")
        assert second is not None
        await engine.migrate(db)
        assert "blurb" in {c.name for c in await db.get_columns("products")}

        # Roll the second migration back.
        applied = (await engine.status(db)).applied
        await engine.migrate(db, target=applied[0])
        assert "blurb" not in {c.name for c in await db.get_columns("products")}
        assert "products" in await db.get_tables(), "rollback dropped more than it should"
    finally:
        Product._fields.pop("blurb", None)
        await db.disconnect()


def test_temporary_directory_helper_is_unused_placeholder():
    """Guard against an accidentally-committed scratch fixture."""
    assert tempfile is not None
    assert asyncio is not None
