"""ForeignKey raw-id accessor -- F-25 of the AniWave migration audit.

``filter(user_id=...)`` and ``create(user_id=...)`` accept the column
spelling, but reading it back was ``AttributeError``: the relation lives at
``instance.user`` (a descriptor) and nothing exposed ``instance.user_id``.
The raw column value is now a property beside the relation descriptor.
"""

from __future__ import annotations

import uuid

import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, ForeignKey, UUIDField


class FkUser(Model):
    table = "fk25_users"
    id = UUIDField(primary_key=True)
    name = CharField(max_length=50)

    class Meta:
        table_name = "fk25_users"


class FkSession(Model):
    table = "fk25_sessions"
    id = UUIDField(primary_key=True)
    user = ForeignKey("FkUser", on_delete="CASCADE")

    class Meta:
        table_name = "fk25_sessions"


@pytest_asyncio.fixture
async def db(tmp_path):
    database = configure_database(f"sqlite:///{tmp_path / 'fk25.db'}", alias="default")
    await database.connect()
    originals = {model: model._db for model in (FkUser, FkSession)}
    for model in (FkUser, FkSession):
        ModelRegistry.register(model)
        model._db = database
        await database.execute(model.generate_create_table_sql())
    yield database
    for model, original in originals.items():
        model._db = original
    await database.disconnect()


async def test_raw_id_attribute_reads_stored_key(db):
    user = await FkUser.create(id=uuid.uuid4(), name="alice")
    session = await FkSession.create(id=uuid.uuid4(), user=user)

    loaded = await FkSession.query().first()

    assert str(loaded.user_id) == str(user.id)
    assert str(loaded.user.pk) == str(user.id)


async def test_raw_id_attribute_writes(db):
    first = await FkUser.create(id=uuid.uuid4(), name="first")
    second = await FkUser.create(id=uuid.uuid4(), name="second")
    session = await FkSession.create(id=uuid.uuid4(), user=first)

    session.user_id = second.id
    await session.save()

    reloaded = await FkSession.query().first()
    assert str(reloaded.user_id) == str(second.id)


async def test_create_accepts_column_name_kwarg(db):
    user = await FkUser.create(id=uuid.uuid4(), name="x")

    session = await FkSession.create(id=uuid.uuid4(), user_id=user.id)

    assert str(session.user_id) == str(user.id)


async def test_filter_by_column_name_still_works(db):
    user = await FkUser.create(id=uuid.uuid4(), name="y")
    await FkSession.create(id=uuid.uuid4(), user=user)
    await FkSession.create(id=uuid.uuid4(), user=await FkUser.create(id=uuid.uuid4(), name="z"))

    sessions = await FkSession.query().filter(user_id=user.id).all()

    assert len(sessions) == 1
    assert str(sessions[0].user_id) == str(user.id)


async def test_relation_descriptor_still_works(db):
    user = await FkUser.create(id=uuid.uuid4(), name="w")
    session = await FkSession.create(id=uuid.uuid4(), user=user)

    hydrated = await session.related("user")

    assert hydrated is not None and hydrated.name == "w"
