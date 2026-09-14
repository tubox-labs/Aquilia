"""
``CompositePrimaryKey`` wiring -- F-03 of the AniWave migration audit.

``CompositePrimaryKey`` was exported and documented (``Meta.primary_key =
CompositePrimaryKey(fields=[...])``) but nothing read it: the metaclass
injected a surrogate ``id = BigAutoField()`` anyway and the migration system
never emitted the table-level ``PRIMARY KEY``. These tests pin the full
wiring: declaration validation, DDL, migrations, identity CRUD, and drift.
"""

from __future__ import annotations

import pytest

from aquilia.faults.domains import ConfigInvalidFault, QueryFault
from aquilia.models import Model
from aquilia.models.fields import CharField, IntegerField
from aquilia.models.fields.composite import CompositePrimaryKey
from aquilia.models.migration import MigrationEngine
from aquilia.models.migration.autodetect import detect_changes
from aquilia.models.migration.schema import ProjectState


class Membership(Model):
    user_id = IntegerField()
    group_id = IntegerField()
    role = CharField(max_length=50)

    class Meta:
        table_name = "cpk_memberships"
        primary_key = CompositePrimaryKey(fields=["user_id", "group_id"])


def test_no_surrogate_id_is_injected():
    assert "id" not in Membership._fields
    assert Membership._pk_composite == ("user_id", "group_id")
    assert Membership._pk_attr == "user_id"


def test_create_table_sql_uses_table_level_primary_key():
    ddl = Membership.generate_create_table_sql("sqlite")

    assert 'PRIMARY KEY ("user_id", "group_id")' in ddl
    assert "AUTOINCREMENT" not in ddl
    assert '"id"' not in ddl


def test_single_field_composite_pk_is_rejected():
    with pytest.raises(ConfigInvalidFault):

        class Broken(Model):
            a = IntegerField()

            class Meta:
                table_name = "cpk_broken"
                primary_key = CompositePrimaryKey(fields=["a"])


def test_unknown_field_names_are_rejected():
    with pytest.raises(ConfigInvalidFault):

        class Broken(Model):
            a = IntegerField()

            class Meta:
                table_name = "cpk_broken2"
                primary_key = CompositePrimaryKey(fields=["a", "nope"])


def test_mixing_composite_and_field_pk_is_rejected():
    with pytest.raises(ConfigInvalidFault):

        class Broken(Model):
            a = IntegerField(primary_key=True)
            b = IntegerField()

            class Meta:
                table_name = "cpk_broken3"
                primary_key = CompositePrimaryKey(fields=["a", "b"])


def test_non_composite_pk_meta_value_is_rejected():
    with pytest.raises(ConfigInvalidFault):

        class Broken(Model):
            a = IntegerField()
            b = IntegerField()

            class Meta:
                table_name = "cpk_broken4"
                primary_key = ["a", "b"]


@pytest.mark.asyncio
async def test_composite_pk_crud_and_migrations(tmp_path):
    engine = MigrationEngine(tmp_path / "migrations")
    path = engine.make_migrations([Membership])
    assert path is not None

    code = path.read_text(encoding="utf-8")
    assert "PrimaryKeyConstraintState" in code
    assert 'ColumnState.of("id"' not in code

    from aquilia.db import set_database
    from aquilia.db.engine import configure_database

    db = configure_database(f"sqlite:///{tmp_path / 'cpk.db'}", alias="default")
    await db.connect()
    set_database(db)
    original_db = Membership._db
    Membership._db = db
    try:
        await db.execute("DROP TABLE IF EXISTS cpk_memberships")
        await engine.migrate(db)

        member = Membership(user_id=1, group_id=2, role="admin")
        await member.save()
        assert member.pk == (1, 2)

        fetched = await Membership.get(pk=(1, 2))
        assert fetched is not None and fetched.role == "admin"

        fetched.role = "owner"
        await fetched.save()
        assert (await Membership.get(pk=(1, 2))).role == "owner"

        await fetched.refresh()
        assert fetched.role == "owner"

        with pytest.raises(QueryFault):
            await Membership(user_id=1, group_id=2, role="dup").save()

        assert await Membership.query().count() == 1
        assert (await fetched.delete_instance()) == 1
        assert await Membership.query().count() == 0

        # An identical schema must not report drift, including the composite
        # key itself (introspected as pk columns + constraint, declared as
        # plain columns + constraint).
        live = await ProjectState.from_database(db, model_classes=[Membership])
        target = ProjectState.from_models([Membership])
        assert detect_changes(live, target, infer_renames=False) == []
    finally:
        Membership._db = original_db
        await db.disconnect()
        set_database(None)  # type: ignore[arg-type]


def test_pk_setter_accepts_sequence_for_composite():
    member = Membership(user_id=1, group_id=2, role="x")

    member.pk = (3, 4)

    assert member.pk == (3, 4)
    with pytest.raises(QueryFault):
        member.pk = (3,)
