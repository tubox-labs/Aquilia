"""
Regression tests for ForeignKey hard-coding an integer primary key.

Previously ForeignKey.validate()/sql_type() (and schema_snapshot.py's
_field_to_sql_type(), used by makemigrations) assumed every related model
uses an integer primary key, and no field ever unwrapped a related Model
instance to its .pk before validating/persisting it. Assigning a related
instance directly (the natural, common pattern -- e.g.
`Verification(user=some_user_instance)`) or pointing a ForeignKey at a
UUID/str-keyed model raised FieldValidationError("Expected integer FK,
got <TypeName>") on the very first .save()/full_clean() call.

OneToOneField.__init__ also silently dropped related_name/on_delete/
on_update/db_constraint kwargs (it re-declared ForeignKey's signature
without them), so passing those to OneToOneField(...) was a no-op.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, FieldValidationError, ForeignKey, OneToOneField, UUIDField
from aquilia.models.schema_snapshot import _field_to_sql_type


class FkUuidAuthor(Model):
    # Deliberately unique names -- ModelRegistry is a process-wide singleton
    # shared with every other test module.
    table = "fkuuid_author"
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=50)


class FkUuidPost(Model):
    table = "fkuuid_post"
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    author = ForeignKey("FkUuidAuthor")
    title = CharField(max_length=50)


@pytest_asyncio.fixture
async def seeded_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    for model in (FkUuidAuthor, FkUuidPost):
        ModelRegistry.register(model)

    originals = {}
    for model in (FkUuidAuthor, FkUuidPost):
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


class TestForeignKeyAcceptsRelatedInstance:
    @pytest.mark.asyncio
    async def test_save_with_model_instance_assigned_to_fk(self, seeded_db):
        author = FkUuidAuthor(name="Ada")
        await author.save()

        post = FkUuidPost(author=author, title="Hello")
        await post.save()

        fetched = await FkUuidPost.objects.filter(id=post.id).first()
        assert fetched is not None
        assert str(fetched.author) == str(author.pk)

    @pytest.mark.asyncio
    async def test_validate_accepts_uuid_pk_value(self, seeded_db):
        author = FkUuidAuthor(name="Grace")
        await author.save()

        field = FkUuidPost._fields["author"]
        # Raw UUID pk value (not an instance) must also validate cleanly.
        assert field.validate(author.pk) == author.pk

    @pytest.mark.asyncio
    async def test_validate_rejects_none_without_null(self, seeded_db):
        field = FkUuidPost._fields["author"]

        with pytest.raises(FieldValidationError):
            field.validate(None)


class TestForeignKeySqlTypeMatchesRelatedPk:
    @pytest.mark.asyncio
    async def test_sql_type_resolves_to_related_pk_type(self, seeded_db):
        field = FkUuidPost._fields["author"]
        assert field.sql_type() == FkUuidAuthor._fields[FkUuidAuthor._pk_attr].sql_type()
        assert field.sql_type() != "INTEGER"

    @pytest.mark.asyncio
    async def test_schema_snapshot_field_to_sql_type_resolves_related_pk(self, seeded_db):
        field = FkUuidPost._fields["author"]
        assert _field_to_sql_type(field) == _field_to_sql_type(FkUuidAuthor._fields[FkUuidAuthor._pk_attr])
        assert _field_to_sql_type(field) != "INTEGER"


class TestOneToOneFieldForwardsKwargs:
    def test_related_name_and_on_delete_are_retained(self):
        field = OneToOneField("FkUuidAuthor", related_name="profile", on_delete="SET_NULL", db_constraint=False)
        assert field.related_name == "profile"
        assert field.on_delete == "SET_NULL"
        assert field.db_constraint is False
        # unique still defaults to True for O2O even with explicit kwargs passed.
        assert field.unique is True
