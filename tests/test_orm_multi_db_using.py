"""
Regression tests for ``Q.using(alias)`` / ``Manager.using(alias)`` /
``Model.using(alias)`` multi-database routing.

Previously ``using()`` recorded the alias on ``_db_alias`` but never
resolved it to an actual ``AquiliaDatabase`` connection -- every query
silently executed against the default database regardless of the alias
passed in. These tests pin down that ``using()`` now actually routes to
the aliased connection, and that an unknown alias fails loudly instead
of silently falling back to the default.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import DatabaseConnectionFault
from aquilia.models.base import Model
from aquilia.models.fields_module import CharField, IntegerField


class Widget(Model):
    id = IntegerField(primary_key=True)
    name = CharField(max_length=50)


@pytest_asyncio.fixture
async def two_databases():
    """Two independent in-memory SQLite databases: 'default' and 'replica'.

    Pins Widget._db explicitly instead of relying on the process-wide
    ModelRegistry fallback, since other test modules sharing this process
    may call ModelRegistry.set_database() and clobber it for every
    registered model, including Widget.
    """
    default_db = configure_database("sqlite:///:memory:", alias="default")
    replica_db = configure_database("sqlite:///:memory:", alias="replica")
    await default_db.connect()
    await replica_db.connect()

    await default_db.execute(Widget.generate_create_table_sql())
    await replica_db.execute(Widget.generate_create_table_sql())

    original_db = Widget._db
    Widget._db = default_db

    yield default_db, replica_db

    Widget._db = original_db
    await default_db.disconnect()
    await replica_db.disconnect()


class TestUsingRoutesToAliasedDatabase:
    @pytest.mark.asyncio
    async def test_using_queries_the_aliased_connection(self, two_databases):
        default_db, replica_db = two_databases
        await default_db.execute("INSERT INTO widget (id, name) VALUES (1, ?)", ["from-default"])
        await replica_db.execute("INSERT INTO widget (id, name) VALUES (1, ?)", ["from-replica"])

        default_row = await Widget.objects.filter(id=1).first()
        replica_row = await Widget.objects.using("replica").filter(id=1).first()

        assert default_row.name == "from-default"
        assert replica_row.name == "from-replica"

    @pytest.mark.asyncio
    async def test_model_classmethod_using_routes_correctly(self, two_databases):
        default_db, replica_db = two_databases
        await default_db.execute("INSERT INTO widget (id, name) VALUES (2, ?)", ["default-cls"])
        await replica_db.execute("INSERT INTO widget (id, name) VALUES (2, ?)", ["replica-cls"])

        row = await Widget.using("replica").filter(id=2).first()
        assert row.name == "replica-cls"

    @pytest.mark.asyncio
    async def test_writes_via_using_land_on_aliased_db_only(self, two_databases):
        default_db, replica_db = two_databases
        await replica_db.execute("INSERT INTO widget (id, name) VALUES (3, ?)", ["seed"])

        await Widget.objects.using("replica").filter(id=3).update(name="updated-on-replica")

        replica_row = await replica_db.fetch_one("SELECT name FROM widget WHERE id = 3")
        default_row = await default_db.fetch_one("SELECT name FROM widget WHERE id = 3")
        assert replica_row["name"] == "updated-on-replica"
        assert default_row is None  # row never existed on default

    @pytest.mark.asyncio
    async def test_unknown_alias_raises_instead_of_silent_default(self, two_databases):
        with pytest.raises(DatabaseConnectionFault):
            await Widget.objects.using("nonexistent-alias").filter(id=1).first()

    @pytest.mark.asyncio
    async def test_using_without_alias_arg_still_uses_default(self, two_databases):
        default_db, _replica_db = two_databases
        await default_db.execute("INSERT INTO widget (id, name) VALUES (4, ?)", ["plain-default"])
        row = await Widget.objects.filter(id=4).first()
        assert row.name == "plain-default"
