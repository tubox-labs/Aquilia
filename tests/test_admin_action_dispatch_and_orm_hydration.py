"""
Regression tests for three related v1.2.5 bugs:

1. ModelAdmin bulk actions (e.g. "delete_selected") crashed with
   ``TypeError: ..._action_delete_selected() takes 3 positional arguments
   but 4 were given`` -- built-in actions were registered as bound methods
   (``func=self._action_x``) while ``AdminSite.execute_action()`` invokes
   ``action_desc.func(model_admin, request, queryset)`` per the unbound
   contract documented on ``AdminActionDescriptor``.

2. That same bulk-delete path called ``queryset.delete()`` (a raw bulk
   DELETE), bypassing ``on_delete`` cascade handling entirely -- deleting a
   parent row referenced by a CASCADE child left the child orphaned instead
   of being cascade-deleted.

3. ``Model.objects.select_related(...).filter(...).first()`` (and ``.one()``)
   returned the FK's raw stored value instead of a hydrated related-model
   instance, because only ``all()`` applied select_related's column-splitting
   step.

None of these were caught by the existing admin test suite, which mocks
``AdminSite.execute_action()`` rather than exercising the real dispatch path.
"""

from __future__ import annotations

import pytest_asyncio

from aquilia.admin.options import ModelAdmin
from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.deletion import CASCADE
from aquilia.models.fields_module import AutoField, CharField, ForeignKey


class DispatchFixAuthor(Model):
    # Deliberately unique names -- ModelRegistry / reverse-FK cache is a
    # process-wide singleton shared with every other test module.
    table = "dispatchfix_author"
    id = AutoField(primary_key=True)
    name = CharField(max_length=50)


class DispatchFixBook(Model):
    table = "dispatchfix_book"
    id = AutoField(primary_key=True)
    title = CharField(max_length=100)
    author = ForeignKey(DispatchFixAuthor, on_delete=CASCADE)


@pytest_asyncio.fixture
async def seeded_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    for model in (DispatchFixAuthor, DispatchFixBook):
        ModelRegistry.register(model)
        model._reverse_fk_cache = None

    originals = {}
    for model in (DispatchFixAuthor, DispatchFixBook):
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    await database.execute("INSERT INTO dispatchfix_author (id, name) VALUES (1, 'Alice')")
    await database.execute("INSERT INTO dispatchfix_author (id, name) VALUES (2, 'Bob')")
    await database.execute("INSERT INTO dispatchfix_book (id, title, author_id) VALUES (1, 'Book A', 1)")

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


class TestAdminActionDispatch:
    """Fix 1: built-in actions must dispatch without a positional-arg crash."""

    async def test_delete_selected_dispatches_without_crashing(self, seeded_db):
        admin = ModelAdmin(model=DispatchFixAuthor)
        action_desc = admin.get_actions()["delete_selected"]

        qs = DispatchFixAuthor.objects.filter(id=2)
        # This is exactly how AdminSite.execute_action() invokes it --
        # previously raised TypeError: ...takes 3 positional arguments
        # but 4 were given.
        result = await action_desc.func(admin, None, qs)

        assert "Deleted 1 record" in result
        assert await DispatchFixAuthor.objects.filter(id=2).exists() is False

    async def test_duplicate_selected_dispatches_without_crashing(self, seeded_db):
        admin = ModelAdmin(model=DispatchFixAuthor)
        action_desc = admin.get_actions()["duplicate_selected"]

        qs = DispatchFixAuthor.objects.filter(id=1)
        result = await action_desc.func(admin, None, qs)

        assert "Duplicated 1 record" in result


class TestAdminBulkDeleteCascade:
    """Fix 2: bulk delete_selected must honor relational on_delete policies."""

    async def test_delete_selected_cascades_to_related_rows(self, seeded_db):
        admin = ModelAdmin(model=DispatchFixAuthor)
        action_desc = admin.get_actions()["delete_selected"]

        assert await DispatchFixBook.objects.filter(author_id=1).exists() is True

        qs = DispatchFixAuthor.objects.filter(id=1)
        await action_desc.func(admin, None, qs)

        assert await DispatchFixAuthor.objects.filter(id=1).exists() is False
        # CASCADE child must be gone too -- previously left orphaned because
        # queryset.delete() bypasses on_delete handling entirely.
        assert await DispatchFixBook.objects.filter(author_id=1).exists() is False


class TestSelectRelatedHydration:
    """Fix 3: select_related must be honored by first()/one(), not just all()."""

    async def test_first_hydrates_related_instance(self, seeded_db):
        book = await DispatchFixBook.objects.select_related("author").filter(title="Book A").first()

        assert book is not None
        assert isinstance(book.author, DispatchFixAuthor)
        assert book.author.name == "Alice"

    async def test_one_hydrates_related_instance(self, seeded_db):
        book = await DispatchFixBook.objects.select_related("author").filter(title="Book A").one()

        assert isinstance(book.author, DispatchFixAuthor)
        assert book.author.name == "Alice"
