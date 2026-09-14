"""get_or_create()/update_or_create() concurrency contract.

Both methods must be atomic when the lookup fields are covered by a unique
constraint: concurrent callers produce exactly one row and no unique-violation
fault. A warning remains only for lookups with no unique constraint, where
atomicity is impossible by definition (there is no conflict target).
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models import UniqueConstraint
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import AutoField, CharField, IntegerField


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


async def test_get_or_create_is_atomic_and_silent_for_unique_lookup(db, recwarn):
    user, created = await CwUser.get_or_create(email="a@test.com", defaults={"name": "Alice"})

    assert created is True
    assert user.email == "a@test.com"
    assert not any(issubclass(w.category, RuntimeWarning) for w in recwarn.list)

    _, created_again = await CwUser.get_or_create(email="a@test.com", defaults={"name": "Ignored"})
    assert created_again is False


async def test_update_or_create_is_atomic_and_silent_for_unique_lookup(db, recwarn):
    user, created = await CwUser.update_or_create(email="a@test.com", defaults={"name": "Alice 2"})

    assert created is True
    assert user.name == "Alice 2"
    assert not any(issubclass(w.category, RuntimeWarning) for w in recwarn.list)

    updated, created_again = await CwUser.update_or_create(email="a@test.com", defaults={"name": "Alice 3"})
    assert created_again is False
    assert updated.name == "Alice 3"


async def test_non_unique_lookup_still_warns(db):
    class CwEvent(Model):
        table = "cw_event"
        id = AutoField(primary_key=True)
        kind = CharField(max_length=50, blank=True)
        payload = CharField(max_length=50, default="x", blank=True)

    ModelRegistry.register(CwEvent)
    original = CwEvent._db
    CwEvent._db = CwUser._db
    await CwUser._db.execute(CwEvent.generate_create_table_sql())
    try:
        with pytest.warns(RuntimeWarning, match="no unique constraint"):
            await CwEvent.get_or_create(kind="click")
        with pytest.warns(RuntimeWarning, match="no unique constraint"):
            await CwEvent.update_or_create(kind="click", defaults={"payload": "x"})
    finally:
        CwEvent._db = original


async def test_concurrent_get_or_create_produces_one_row(db):
    results = await asyncio.gather(
        *[CwUser.get_or_create(email="race@test.com", defaults={"name": f"n{i}"}) for i in range(10)],
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert not failures, failures
    assert sum(1 for _, created in results if created) == 1
    assert await CwUser.query().filter(email="race@test.com").count() == 1


async def test_concurrent_update_or_create_produces_one_row(db):
    results = await asyncio.gather(
        *[CwUser.update_or_create(email="race2@test.com", defaults={"name": f"n{i}"}) for i in range(10)],
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert not failures, failures
    assert sum(1 for _, created in results if created) == 1
    assert await CwUser.query().filter(email="race2@test.com").count() == 1
    # Every caller's UPDATE ran against the single surviving row; the final
    # name is one of the concurrent writers', not a crash or a duplicate.
    row = await CwUser.query().filter(email="race2@test.com").first()
    assert row.name.startswith("n")


async def test_concurrent_update_or_create_composite_unique(db):
    class CwMembership(Model):
        table = "cw_membership"
        id = AutoField(primary_key=True)
        user_id = IntegerField()
        group_id = IntegerField()
        role = CharField(max_length=20, default="member")

        class Meta:
            table_name = "cw_membership"
            constraints = [UniqueConstraint(fields=["user_id", "group_id"], name="uq_user_group")]

    ModelRegistry.register(CwMembership)
    CwMembership._db = CwUser._db
    await CwUser._db.execute(CwMembership.generate_create_table_sql())

    results = await asyncio.gather(
        *[CwMembership.update_or_create(user_id=7, group_id=9, defaults={"role": f"role{i}"}) for i in range(10)],
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert not failures, failures
    assert sum(1 for _, created in results if created) == 1
    assert await CwMembership.query().filter(user_id=7, group_id=9).count() == 1


async def test_find_or_create_does_not_warn(db, recwarn):
    await CwUser.find_or_create(email="b@test.com", defaults={"name": "Bob"})
    assert not any(issubclass(w.category, RuntimeWarning) for w in recwarn.list)
