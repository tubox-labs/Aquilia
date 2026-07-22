"""Unit + live-DB tests for the new enterprise field types: MoneyField,
EncryptedField, PointField/GeometryField, GenericForeignKey."""

from __future__ import annotations

import decimal

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields import EncryptedField, EncryptedMixin, FieldValidationError, MoneyField
from aquilia.models.fields_module import AutoField, CharField, GenericForeignKey, GeometryField, PointField


# ── MoneyField ──────────────────────────────────────────────────────────────


def test_money_field_defaults():
    field = MoneyField()
    assert field.currency == "USD"
    assert field._field_type == "MONEY"


def test_money_field_precision_like_decimal():
    field = MoneyField(max_digits=8, decimal_places=2, currency="EUR")
    assert field.validate("19.99") == decimal.Decimal("19.99")
    assert field.to_db(decimal.Decimal("19.99")) == "19.99"
    with pytest.raises(FieldValidationError):
        field.validate("1234567.89")  # 9 significant digits > max_digits=8


def test_money_field_rejects_bad_currency_code():
    with pytest.raises(FieldValidationError):
        MoneyField(currency="dollars")


def test_money_field_deconstruct_includes_currency():
    field = MoneyField(currency="GBP")
    d = field.deconstruct()
    assert d["currency"] == "GBP"


# ── EncryptedField ──────────────────────────────────────────────────────────


def test_encrypted_field_round_trips_with_configured_key():
    EncryptedMixin.configure_encryption_key("test-key-material")
    try:
        field = EncryptedField()
        ciphertext = field.to_db("top secret")
        assert ciphertext != "top secret"
        assert field.to_python(ciphertext) == "top secret"
    finally:
        EncryptedMixin._encryption_backend = None
        EncryptedMixin._decryption_backend = None
        EncryptedMixin._fernet_instance = None


def test_encrypted_field_to_db_accepts_dialect_kwarg():
    """Regression: to_db(value, dialect=...) must not TypeError -- every real
    Model.save() call site passes dialect as a keyword argument."""
    field = EncryptedField()
    with pytest.warns(UserWarning):
        field.to_db("value", dialect="postgresql")


# ── PointField / GeometryField ───────────────────────────────────────────────


def test_point_field_accepts_valid_point():
    field = PointField()
    value = {"type": "Point", "coordinates": [-122.4194, 37.7749]}
    assert field.validate(value) == value


def test_point_field_rejects_non_point_geometry():
    field = PointField()
    with pytest.raises(FieldValidationError):
        field.validate({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]})


def test_point_field_rejects_wrong_coordinate_count():
    field = PointField()
    with pytest.raises(FieldValidationError):
        field.validate({"type": "Point", "coordinates": [1.0]})


def test_geometry_field_accepts_polygon():
    field = GeometryField()
    value = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    assert field.validate(value) == value


def test_geometry_field_rejects_unknown_type():
    field = GeometryField()
    with pytest.raises(FieldValidationError):
        field.validate({"type": "NotAShape", "coordinates": []})


def test_geometry_field_round_trips_through_json():
    field = GeometryField()
    value = {"type": "Point", "coordinates": [1, 2]}
    stored = field.to_db(value)
    assert field.to_python(stored) == value


# ── GenericForeignKey ─────────────────────────────────────────────────────


class GfkAuthor(Model):
    table = "gfk_author"
    id = AutoField(primary_key=True)
    name = CharField(max_length=50)


class GfkComment(Model):
    table = "gfk_comment"
    id = AutoField(primary_key=True)
    body = CharField(max_length=50, default="a comment")
    content_type = CharField(max_length=255, null=True)
    object_id = CharField(max_length=255, null=True)
    target = GenericForeignKey("content_type", "object_id")


@pytest_asyncio.fixture
async def gfk_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    originals = {}
    for model in (GfkAuthor, GfkComment):
        ModelRegistry.register(model)
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


async def test_generic_fk_attach_and_resolve(gfk_db):
    author = await GfkAuthor.create(name="Alice")
    comment = await GfkComment.create()

    GfkComment.target.attach(comment, author)
    await comment.save()

    reloaded = await GfkComment.get(pk=comment.pk)
    resolved = await GfkComment.target.resolve(reloaded)
    assert resolved is not None
    assert resolved.pk == author.pk
    assert resolved.name == "Alice"


async def test_generic_fk_resolve_none_when_unset(gfk_db):
    comment = await GfkComment.create()
    resolved = await GfkComment.target.resolve(comment)
    assert resolved is None
