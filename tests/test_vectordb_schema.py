"""
Vector model schema tests — annotation routing, codecs, and validation.

These exercise the declaration layer only, so they run without ``elips``
installed: nothing here opens a store.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated

import pytest

from aquilia.vectordb import (
    Choices,
    Dimension,
    Key,
    MaxLength,
    MinLength,
    MinValue,
    Payload,
    Score,
    Text,
    VectorModel,
)
from aquilia.vectordb.codecs import decode_value, encode_value, resolve_codec
from aquilia.vectordb.faults import VectorSchemaFault, VectorValidationFault


class Colour(Enum):
    RED = "red"
    BLUE = "blue"


class Priority(Enum):
    LOW = 1
    HIGH = 2


# ── Slot routing ─────────────────────────────────────────────────────────────


class Doc(VectorModel):
    key: Annotated[str, Key()]
    vector: Annotated[list[float], Dimension(8)]
    body: Annotated[str, Text(), MinLength(1), MaxLength(64)]
    views: Annotated[int, Payload(indexed=True), MinValue(0)]
    slug: Annotated[str, Payload(name="url_slug")]
    tag: str | None
    score: Annotated[float, Score()]

    class Meta:
        collection = "docs"


def test_slots_route_to_the_right_positions():
    schema = Doc._vfields
    assert schema.key_attr == "key"
    assert schema.text_attr == "body"
    assert schema.vector_attr == "vector"
    assert schema.score_attr == "score"
    assert schema.dimension == 8


def test_payloads_collected_with_storage_keys():
    schema = Doc._vfields
    assert set(schema.payloads) == {"body", "views", "slug", "tag"}
    assert schema.payloads["slug"].key == "url_slug"
    assert schema.payload_keys["url_slug"].attribute == "slug"


def test_indexed_and_optional_flags():
    schema = Doc._vfields
    assert schema.payloads["views"].indexed is True
    assert schema.payloads["slug"].indexed is False
    assert schema.payloads["tag"].optional is True
    assert schema.payloads["views"].optional is False


def test_score_is_not_written():
    """The score slot is query output, never stored."""
    written = {spec.attribute for spec in Doc._vfields.written_payloads}
    assert "score" not in written


def test_meta_defaults_from_class_name():
    class Untitled(VectorModel):
        key: Annotated[str, Key()]
        body: Annotated[str, Text()]

    assert Untitled._voptions.collection == "untitled"
    assert Untitled._voptions.store == "default"


def test_dimension_marker_and_meta_must_agree():
    with pytest.raises(VectorSchemaFault) as exc:

        class Conflict(VectorModel):
            key: Annotated[str, Key()]
            vector: Annotated[list[float], Dimension(8)]

            class Meta:
                dimension = 16

    assert exc.value.code == "VECTOR_SCHEMA_INVALID"


def test_duplicate_slot_rejected():
    with pytest.raises(VectorSchemaFault):

        class TwoKeys(VectorModel):
            key: Annotated[str, Key()]
            other: Annotated[str, Key()]
            body: Annotated[str, Text()]


def test_model_without_key_rejected():
    with pytest.raises(VectorSchemaFault):

        class NoKey(VectorModel):
            body: Annotated[str, Text()]


def test_model_with_no_vector_or_text_rejected():
    """A model with nothing to index could never be written."""
    with pytest.raises(VectorSchemaFault):

        class Inert(VectorModel):
            key: Annotated[str, Key()]
            count: Annotated[int, Payload()]


def test_unroutable_type_rejected():
    """Nested payloads have no faithful elips encoding, so they fail loudly."""
    with pytest.raises(VectorSchemaFault):

        class Nested(VectorModel):
            key: Annotated[str, Key()]
            body: Annotated[str, Text()]
            data: Annotated[dict, Payload()]


def test_abstract_model_is_not_registered():
    from aquilia.vectordb.registry import VectorRegistry

    class Base(VectorModel):
        key: Annotated[str, Key()]
        body: Annotated[str, Text()]

        class Meta:
            abstract = True

    assert VectorRegistry.get("Base") is None


def test_subclass_does_not_inherit_abstract_or_collection():
    class Base(VectorModel):
        key: Annotated[str, Key()]
        body: Annotated[str, Text()]

        class Meta:
            abstract = True
            store = "shared"

    class Child(Base):
        extra: Annotated[int, Payload()]

    assert Child._voptions.abstract is False
    assert Child._voptions.collection == "child"
    # Non-excluded options still inherit.
    assert Child._voptions.store == "shared"
    # Parent payloads carry over.
    assert "body" in Child._vfields.payloads
    assert "extra" in Child._vfields.payloads


# ── Instances ────────────────────────────────────────────────────────────────


def test_unknown_attribute_rejected():
    with pytest.raises(VectorValidationFault) as exc:
        Doc(nope=1)
    assert "nope" in exc.value.errors


def test_validate_collects_every_error():
    doc = Doc(key="k", body="", views=-5, vector=[0.0] * 8)
    with pytest.raises(VectorValidationFault) as exc:
        doc.validate()
    assert set(exc.value.errors) == {"body", "views"}


def test_validate_rejects_wrong_dimension():
    doc = Doc(key="k", body="hi", views=1, vector=[0.0, 1.0])
    with pytest.raises(VectorValidationFault) as exc:
        doc.validate()
    assert "vector" in exc.value.errors


def test_key_property_reads_the_key_slot():
    doc = Doc(key="abc", body="hi", views=0, vector=[0.0] * 8)
    assert doc.key == "abc"
    doc.key = "xyz"
    assert doc.key == "xyz"


def test_to_dict_excludes_vector_by_default():
    doc = Doc(key="k", body="hi", views=3, vector=[0.5] * 8)
    assert "vector" not in doc.to_dict()
    assert doc.to_dict(include_vector=True)["vector"] == [0.5] * 8


def test_choices_constraint():
    class Tagged(VectorModel):
        key: Annotated[str, Key()]
        body: Annotated[str, Text()]
        state: Annotated[str, Payload(), Choices("draft", "live")]

    Tagged(key="k", body="x", state="live").validate()

    with pytest.raises(VectorValidationFault):
        Tagged(key="k", body="x", state="nope").validate()


# ── Codecs ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    [True, 3, 2.5, "text"],
)
def test_scalar_codecs_round_trip(value):
    encoded = encode_value(value, type(value))
    assert decode_value(encoded, type(value)) == value


def test_datetime_encodes_to_orderable_float():
    early = datetime(2020, 1, 1, tzinfo=timezone.utc)
    late = datetime(2024, 1, 1, tzinfo=timezone.utc)

    enc_early = encode_value(early, datetime)
    enc_late = encode_value(late, datetime)

    assert isinstance(enc_early, float)
    assert enc_early < enc_late  # ordering survives, so range filters work
    assert decode_value(enc_early, datetime) == early


def test_naive_datetime_is_treated_as_utc():
    naive = datetime(2024, 6, 1, 12, 0, 0)
    decoded = decode_value(encode_value(naive, datetime), datetime)
    assert decoded == naive.replace(tzinfo=timezone.utc)


def test_date_round_trips():
    value = date(2024, 3, 15)
    assert decode_value(encode_value(value, date), date) == value


def test_decimal_is_exact_but_not_orderable():
    value = Decimal("10.05")
    codec = resolve_codec(Decimal)
    assert codec.orderable is False
    assert decode_value(encode_value(value, Decimal), Decimal) == value


def test_uuid_round_trips():
    value = uuid.uuid4()
    assert decode_value(encode_value(value, uuid.UUID), uuid.UUID) == value


def test_str_enum_round_trips():
    assert decode_value(encode_value(Colour.RED, Colour), Colour) is Colour.RED


def test_int_enum_is_orderable():
    codec = resolve_codec(Priority)
    assert codec.orderable is True
    assert decode_value(encode_value(Priority.HIGH, Priority), Priority) is Priority.HIGH


def test_unsupported_type_has_no_codec():
    assert resolve_codec(dict) is None
    assert resolve_codec(list) is None


def test_decode_of_corrupt_value_returns_it_unchanged():
    """A read must not fail because one record predates a type change."""
    assert decode_value("not-a-uuid", uuid.UUID) == "not-a-uuid"
