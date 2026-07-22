"""get_or_create()/update_or_create() must warn that they are not atomic."""

from __future__ import annotations

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import AutoField, CharField


class CwUser(Model):
    table = "cw_user"
    id = AutoField(primary_key=True)
    email = CharField(max_length=100, unique=True)
    name = CharField(max_length=100, default="")


@pytest_asyncio.fixture
async def db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()
    ModelRegistry.register(CwUser)
    original = CwUser._db
    CwUser._db = database
    await database.execute(CwUser.generate_create_table_sql())

    yield database

    CwUser._db = original
    await database.disconnect()


async def test_get_or_create_warns(db):
    with pytest.warns(RuntimeWarning, match="not atomic"):
        await CwUser.get_or_create(email="a@test.com", defaults={"name": "Alice"})


async def test_update_or_create_warns(db):
    with pytest.warns(RuntimeWarning, match="not atomic"):
        await CwUser.update_or_create(email="a@test.com", defaults={"name": "Alice 2"})


async def test_find_or_create_does_not_warn(db, recwarn):
    await CwUser.find_or_create(email="b@test.com", defaults={"name": "Bob"})
    assert not any(issubclass(w.category, RuntimeWarning) for w in recwarn.list)
