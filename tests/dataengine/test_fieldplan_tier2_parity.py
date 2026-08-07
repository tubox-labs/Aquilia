"""Differential parity tests for the Phase 2 Tier 2 native FieldPlan additions.

Covers EnumFacet, SetFacet, TupleFacet, DecimalFacet precision limits, and
DurationFacet. The property asserted is the same one Tier 1 asserts: a payload
validated with the native engine enabled must produce a byte-identical verdict,
``validated_data``, and ``errors`` mapping to the same payload validated with it
disabled.

See :mod:`tests.dataengine.test_fieldplan_phase2_parity` for why the tests are
written differentially rather than against hand-written expected values.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from enum import Enum, IntEnum, StrEnum
from typing import Any

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.facets import (
    BoolFacet,
    DateFacet,
    DecimalFacet,
    DurationFacet,
    EnumFacet,
    FloatFacet,
    IntFacet,
    ListFacet,
    SetFacet,
    TextFacet,
    TupleFacet,
    UUIDFacet,
)
from tests.dataengine.test_fieldplan_phase2_parity import assert_parity

# ---------------------------------------------------------------------------
# Enum fixtures
# ---------------------------------------------------------------------------


class Colour(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Priority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Flavour(StrEnum):
    SWEET = "sweet"
    SOUR = "sour"


class NameCollides(Enum):
    """A member whose *name* is another member's *value*.

    Pins the lookup order: ``EnumFacet.cast`` tries by value before by name, so
    ``"B"`` must resolve to ``A`` (value ``"B"``), not to ``B``.
    """

    A = "B"
    B = "c"


class CustomMissing(Enum):
    """An Enum with a ``_missing_`` hook -- must never compile natively."""

    X = "x"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        return cls.X


# ---------------------------------------------------------------------------
# EnumFacet
# ---------------------------------------------------------------------------


class ColourContract(Contract):
    colour = EnumFacet(enum_class=Colour)


class PriorityContract(Contract):
    priority = EnumFacet(enum_class=Priority)


class FlavourContract(Contract):
    flavour = EnumFacet(enum_class=Flavour)


class CollisionContract(Contract):
    pick = EnumFacet(enum_class=NameCollides)


@pytest.mark.parametrize(
    "value",
    [
        "red",
        "green",
        "blue",
        "RED",  # by name
        "GREEN",
        "purple",  # neither value nor name
        "",
        None,
        1,
        True,
        Colour.RED,  # already a member
        [],  # unhashable
    ],
)
def test_enum_value_and_name_parity(value: Any) -> None:
    assert_parity(ColourContract, {"colour": value})


@pytest.mark.parametrize(
    "value",
    [
        1,
        2,
        3,
        0,
        99,
        "1",  # IntEnum coerces via int() -- native defers, Python accepts
        "HIGH",  # by name
        True,  # == 1, so the value map finds HIGH
        False,
        1.0,  # == 1
        Priority.LOW,
    ],
)
def test_int_enum_parity(value: Any) -> None:
    """IntEnum coercion is the subtle case.

    ``EnumFacet.cast`` calls ``int(value)`` before the lookup when the Enum
    subclasses ``int``, so ``"1"`` resolves to ``Priority.HIGH``. The native path
    does not reproduce that coercion and defers instead -- these cases prove the
    deferral still lands on the same answer.
    """
    assert_parity(PriorityContract, {"priority": value})


@pytest.mark.parametrize("value", ["sweet", "sour", "SWEET", "salty", 1, None])
def test_str_enum_parity(value: Any) -> None:
    assert_parity(FlavourContract, {"flavour": value})


@pytest.mark.parametrize("value", ["B", "c", "A", "b"])
def test_enum_name_value_collision_parity(value: Any) -> None:
    """Value lookup must win over name lookup, exactly as Python orders them."""
    assert_parity(CollisionContract, {"pick": value})


def test_custom_missing_enum_is_escaped() -> None:
    """An Enum with a ``_missing_`` override runs Python on a lookup miss.

    ``EnumMeta.__call__`` invokes that hook, and it can return any member for an
    otherwise-unmapped value. The native path replaces the call with a dict
    lookup, so such a class must never compile.
    """
    from aquilia.contracts._native_plan import field_plan_for

    class CustomMissingContract(Contract):
        x = EnumFacet(enum_class=CustomMissing)

    compiled = field_plan_for(CustomMissingContract)
    assert compiled is None or "x" in compiled.escaped


@pytest.mark.parametrize("value", ["x", "X", "anything-else", 42])
def test_custom_missing_enum_parity(value: Any) -> None:
    """The escape must still agree with the all-Python path."""

    class CustomMissingContract(Contract):
        x = EnumFacet(enum_class=CustomMissing)

    assert_parity(CustomMissingContract, {"x": value})


class NullableEnumContract(Contract):
    colour = EnumFacet(enum_class=Colour, allow_null=True)
    fallback = EnumFacet(enum_class=Colour, default=Colour.RED)


@pytest.mark.parametrize(
    "payload",
    [{}, {"colour": None}, {"colour": "red"}, {"colour": "bad"}, {"fallback": "green"}, {"fallback": None}],
)
def test_enum_nullability_parity(payload: dict) -> None:
    assert_parity(NullableEnumContract, payload)


# ---------------------------------------------------------------------------
# SetFacet
# ---------------------------------------------------------------------------


class IntSetContract(Contract):
    values = SetFacet(child=IntFacet())


class BoundedSetContract(Contract):
    tags = SetFacet(child=TextFacet(), min_items=2, max_items=4)


@pytest.mark.parametrize(
    "value",
    [
        [],
        [1],
        [1, 2, 3],
        [1, 1, 1],  # dedupes to one element
        ["1", 1],  # distinct raw, equal after cast
        [1, True],  # equal raw -- Python dedupes before casting
        [1, "notanint"],
        [1, None],
        (1, 2),  # tuple input
        {1, 2},  # set input -- non-deterministic order, must defer
        "notacollection",
        None,
    ],
)
def test_int_set_parity(value: Any) -> None:
    """Python dedupes the *raw* values then casts; the native path casts then
    dedupes. These cases pin that the two orders cannot disagree for the element
    types the plan accepts."""
    assert_parity(IntSetContract, {"values": value})


@pytest.mark.parametrize(
    "value",
    [
        [],
        ["a"],
        ["a", "b"],
        ["a", "b", "c", "d"],
        ["a", "b", "c", "d", "e"],
        ["a", "a"],  # dedupes below min_items
        ["a", "a", "b"],  # dedupes to exactly min_items
    ],
)
def test_bounded_set_parity(value: Any) -> None:
    """Item counts are judged *after* dedup, which is what facets.py does."""
    assert_parity(BoundedSetContract, {"tags": value})


# ---------------------------------------------------------------------------
# TupleFacet
# ---------------------------------------------------------------------------


class StrTupleContract(Contract):
    parts = TupleFacet(child=TextFacet())


class BoundedTupleContract(Contract):
    pair = TupleFacet(child=IntFacet(), min_items=2, max_items=2)


@pytest.mark.parametrize(
    "value",
    [
        [],
        ["a"],
        ["a", "b", "c"],
        ("a", "b"),
        ["a", ""],  # blank rejected by TextFacet.seal
        ["a", 1],
        {"a", "b"},  # set input -- ordering is unobservable, must defer
        None,
        "notacollection",
    ],
)
def test_str_tuple_parity(value: Any) -> None:
    assert_parity(StrTupleContract, {"parts": value})


@pytest.mark.parametrize("value", [[1, 2], [1], [1, 2, 3], [], ["1", "2"], [1, "x"]])
def test_bounded_tuple_parity(value: Any) -> None:
    assert_parity(BoundedTupleContract, {"pair": value})


# ---------------------------------------------------------------------------
# DecimalFacet
# ---------------------------------------------------------------------------


class PlainDecimalContract(Contract):
    amount = DecimalFacet()


class PreciseDecimalContract(Contract):
    price = DecimalFacet(max_digits=5, decimal_places=2)


class BoundedDecimalContract(Contract):
    rate = DecimalFacet(min_value=0, max_value=100, decimal_places=3)


@pytest.mark.parametrize(
    "value",
    [
        "19.99",
        "0",
        "-5",
        "1E+3",
        "0.001",
        "1e-7",
        123,
        "notanumber",
        "",
        "NaN",  # parses, but is not finite
        "Infinity",
        "-Infinity",
        0.1,  # float: Decimal(str(0.1)) == Decimal("0.1")
        True,  # bool is an int subclass
        None,
        Decimal("2.5"),
    ],
)
def test_plain_decimal_parity(value: Any) -> None:
    assert_parity(PlainDecimalContract, {"amount": value})


@pytest.mark.parametrize(
    "value",
    [
        "19.99",  # 4 digits, 2 places -- passes
        "12345",  # 5 digits, 0 places -- passes
        "123456",  # 6 digits -- exceeds max_digits
        "1.234",  # 3 places -- exceeds decimal_places
        "0.001",  # 1 significant digit, 3 places -- places violated
        "999.99",
        "1000.00",  # 6 digits
        "-19.99",
        "0.00",
    ],
)
def test_precise_decimal_parity(value: Any) -> None:
    """``max_digits`` counts *significant* digits from ``Decimal.as_tuple()``.

    ``Decimal("0.001")`` has one significant digit and three decimal places,
    which is surprising but is exactly what facets.py counts.
    """
    assert_parity(PreciseDecimalContract, {"price": value})


@pytest.mark.parametrize("value", ["0", "50.5", "100", "100.001", "-0.001", "99.999", "99.9999"])
def test_bounded_decimal_parity(value: Any) -> None:
    """Bounds are applied before precision, matching DecimalFacet.seal order."""
    assert_parity(BoundedDecimalContract, {"rate": value})


# ---------------------------------------------------------------------------
# DurationFacet
# ---------------------------------------------------------------------------


class DurationContract(Contract):
    span = DurationFacet()


@pytest.mark.parametrize(
    "value",
    [
        0,
        90,
        1.5,
        -30,
        "90",  # numeric string -- native defers, Python parses
        "01:30:00",  # HH:MM:SS -- native defers
        "-01:30:00",
        "+90",
        "notaduration",
        "",
        True,  # isinstance(True, int) -- Python yields timedelta(seconds=1)
        False,
        None,
        datetime.timedelta(seconds=5),
        float("nan"),
        float("inf"),
    ],
)
def test_duration_parity(value: Any) -> None:
    assert_parity(DurationContract, {"span": value})


# ---------------------------------------------------------------------------
# Anti-vacuity guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "contract_name",
    [
        "ColourContract",
        "PriorityContract",
        "FlavourContract",
        "CollisionContract",
        "IntSetContract",
        "BoundedSetContract",
        "StrTupleContract",
        "BoundedTupleContract",
        "PlainDecimalContract",
        "PreciseDecimalContract",
        "BoundedDecimalContract",
        "DurationContract",
    ],
)
def test_tier2_contracts_actually_compile_natively(contract_name: str) -> None:
    """Every Tier 2 feature must reach the native path, or the parity tests lie.

    A parity test that compares Python against Python passes unconditionally. If
    a compiler change starts escaping one of these fields, the corresponding
    parity tests would keep passing while silently testing nothing.
    """
    from aquilia._dataengine_loader import DATAENGINE_NATIVE

    if not DATAENGINE_NATIVE:
        pytest.skip("native data engine not built")

    import aquilia.contracts._native_plan as native_plan

    contract_cls = globals()[contract_name]
    native_plan._PLAN_CACHE.clear()
    compiled = native_plan.field_plan_for(contract_cls)

    assert compiled is not None, f"{contract_name} produced no native plan"
    assert len(compiled.plan) >= 1, f"{contract_name} plan covers no fields"
    assert not compiled.escaped, f"{contract_name} escaped {sorted(compiled.escaped)} to Python"


# ---------------------------------------------------------------------------
# Mixed Tier 1 + Tier 2 contract
# ---------------------------------------------------------------------------


class KitchenSinkContract(Contract):
    name = TextFacet(min_length=2, max_length=20)
    count = IntFacet(min_value=0, multiple_of=5)
    colour = EnumFacet(enum_class=Colour)
    price = DecimalFacet(max_digits=6, decimal_places=2)
    tags = SetFacet(child=TextFacet(), max_items=3)
    coords = TupleFacet(child=FloatFacet())
    ids = ListFacet(child=UUIDFacet())
    when = DateFacet()
    span = DurationFacet()
    active = BoolFacet()


_VALID = {
    "name": "Widget",
    "count": 10,
    "colour": "red",
    "price": "19.99",
    "tags": ["a", "b"],
    "coords": [1.0, 2.5],
    "ids": ["123e4567-e89b-12d3-a456-426614174000"],
    "when": "2026-01-15",
    "span": 90,
    "active": True,
}


@pytest.mark.parametrize(
    "override",
    [
        {},
        {"name": "W"},  # too short
        {"count": 7},  # not a multiple of 5
        {"colour": "purple"},
        {"price": "1234567.89"},  # too many digits
        {"price": "1.234"},  # too many places
        {"tags": ["a", "b", "c", "d"]},  # too many items
        {"tags": ["a", "a", "a"]},  # dedupes to one
        {"coords": [1.0, "x"]},
        {"ids": ["not-a-uuid"]},
        {"when": "2026-02-30"},
        {"span": "01:30:00"},
        {"active": "yes"},
        {"colour": None},
    ],
)
def test_kitchen_sink_parity(override: dict) -> None:
    """Ten facets across both tiers in one contract, one field perturbed."""
    assert_parity(KitchenSinkContract, {**_VALID, **override})


def test_kitchen_sink_compiles_fully_native() -> None:
    from aquilia._dataengine_loader import DATAENGINE_NATIVE

    if not DATAENGINE_NATIVE:
        pytest.skip("native data engine not built")

    import aquilia.contracts._native_plan as native_plan

    native_plan._PLAN_CACHE.clear()
    compiled = native_plan.field_plan_for(KitchenSinkContract)
    assert compiled is not None
    assert not compiled.escaped, f"escaped {sorted(compiled.escaped)}"
    assert len(compiled.plan) == 10
