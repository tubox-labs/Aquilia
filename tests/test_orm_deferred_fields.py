"""
Regression tests for only()/defer() deferred-field access.

Previously, a field excluded via only()/defer() was either left to leak the
raw class-level Field metadata object (the actual pre-fix behavior) or, if
naively "fixed" to default to None, would be indistinguishable from a real
database NULL -- both are silent data-integrity hazards. Accessing an
excluded field must now raise DeferredFieldAccessFault, while internal
call sites using getattr(obj, name, default) (e.g. dirty-field tracking,
to_dict serialization) must keep degrading to *default* instead of
propagating, and instances that were never partially loaded must incur
zero extra overhead (class is left untouched).
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import DeferredFieldAccessFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, IntegerField


class Article(Model):
    id = IntegerField(primary_key=True)
    title = CharField(max_length=100)
    body = CharField(max_length=1000, null=True)


@pytest_asyncio.fixture
async def db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()
    await database.execute(Article.generate_create_table_sql())
    await database.execute(
        "INSERT INTO article (id, title, body) VALUES (1, ?, ?)",
        ["Hello", "Full body text"],
    )
    original_db = Article._db
    Article._db = database
    yield database
    Article._db = original_db
    await database.disconnect()


class TestDeferredFieldAccessRaises:
    @pytest.mark.asyncio
    async def test_direct_access_to_deferred_field_raises(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        assert article.title == "Hello"
        with pytest.raises(DeferredFieldAccessFault):
            _ = article.body

    @pytest.mark.asyncio
    async def test_defer_excludes_named_field(self, db):
        article = await Article.objects.defer("body").filter(id=1).first()
        assert article.title == "Hello"
        with pytest.raises(DeferredFieldAccessFault):
            _ = article.body

    @pytest.mark.asyncio
    async def test_fully_loaded_instance_never_raises(self, db):
        article = await Article.objects.filter(id=1).first()
        assert article.body == "Full body text"


class TestDeferredFieldGetattrDefaultDegrades:
    @pytest.mark.asyncio
    async def test_getattr_with_default_returns_default(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        # getattr(obj, name, default) must NOT raise -- dirty-field
        # tracking and other defensive internal call sites rely on this.
        assert getattr(article, "body", "SENTINEL") == "SENTINEL"

    @pytest.mark.asyncio
    async def test_to_dict_does_not_raise_on_deferred_field(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        result = article.to_dict()
        assert result["title"] == "Hello"
        assert result["body"] is None  # serializes safely, does not raise

    @pytest.mark.asyncio
    async def test_get_dirty_fields_does_not_raise_and_ignores_untouched_deferred(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        dirty = article.get_dirty_fields()
        assert "body" not in dirty


class TestSaveDoesNotClobberDeferredFields:
    @pytest.mark.asyncio
    async def test_save_preserves_untouched_deferred_field(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        article.title = "Updated title"
        await article.save()

        fresh = await Article.objects.filter(id=1).first()
        assert fresh.title == "Updated title"
        assert fresh.body == "Full body text"  # must NOT have been nulled out


class TestRefreshClearsDeferredGuard:
    @pytest.mark.asyncio
    async def test_partial_refresh_of_deferred_field_clears_guard(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        await article.refresh(fields=["body"])
        assert article.body == "Full body text"
        assert type(article) is Article  # class swapped back once fully loaded

    @pytest.mark.asyncio
    async def test_full_refresh_clears_deferred_guard(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        assert type(article) is not Article  # guard variant while deferred
        await article.refresh()
        assert article.body == "Full body text"
        assert type(article) is Article


class TestDeferredGuardIsolation:
    @pytest.mark.asyncio
    async def test_guard_variant_not_registered_in_model_registry(self, db):
        before = len(ModelRegistry.all_models())
        await Article.objects.only("id").filter(id=1).first()
        await Article.objects.only("id").filter(id=1).first()
        after = len(ModelRegistry.all_models())
        assert before == after

    @pytest.mark.asyncio
    async def test_guard_variant_keeps_correct_table_name(self, db):
        article = await Article.objects.only("id", "title").filter(id=1).first()
        assert article._table_name == "article"

    @pytest.mark.asyncio
    async def test_guard_class_is_cached_not_recreated(self, db):
        a1 = await Article.objects.only("id").filter(id=1).first()
        a2 = await Article.objects.only("id").filter(id=1).first()
        assert type(a1) is type(a2)
