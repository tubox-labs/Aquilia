"""Differential parity tests for the Phase 2 native FieldPlan additions.

Every test here asserts the same property: **a payload validated with the native
engine enabled produces byte-identical results to the same payload validated
with it disabled.** Not "both reject it" -- the same ``is_sealed()`` verdict, the
same ``validated_data``, and the same ``errors`` mapping, including message text.

Why differential rather than expected-value tests
-------------------------------------------------
The native plan is an optimisation whose only contract is *indistinguishability*
from ``Sigil.validate``. Asserting a hand-written expected value would encode a
second opinion about what Python does, and when the two disagreed the test would
not say which was wrong. Comparing the two paths directly makes Python the
reference implementation by construction, which is exactly the safety property
``_native_plan.py`` claims.

The engine is toggled by re-importing the loader under a patched environment
variable, because ``DATAENGINE_NATIVE`` is resolved once at import time.
"""

from __future__ import annotations

import datetime
import importlib
import os
import uuid
from decimal import Decimal
from typing import Any

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.facets import (
    BoolFacet,
    ChoiceFacet,
    DateFacet,
    FloatFacet,
    IntFacet,
    ListFacet,
    LiteralFacet,
    TextFacet,
    UUIDFacet,
)


def _validate_with_engine(contract_cls: type[Contract], payload: dict, *, native: bool) -> tuple:
    """Validate ``payload`` with the native engine forced on or off.

    Returns:
        ``(sealed, validated, errors)`` -- the full observable outcome, so a
        divergence in any one of them fails the comparison.

    Notes:
        The plan cache is keyed by contract class and is populated on first use,
        so it must be cleared between the two runs. Otherwise the second run
        would reuse the first run's decision and both halves of the comparison
        would exercise the same path.
    """
    import aquilia._dataengine_loader as loader
    import aquilia.contracts._native_plan as native_plan

    prior = os.environ.get("AQUILIA_DATAENGINE")
    os.environ["AQUILIA_DATAENGINE"] = "1" if native else "0"
    try:
        importlib.reload(loader)
        importlib.reload(native_plan)
        # Sigil holds its own reference to field_plan_for, captured at import.
        import aquilia.contracts.core as core_mod
        import aquilia.contracts.sigil as sigil_mod

        sigil_mod.field_plan_for = native_plan.field_plan_for
        core_mod.field_plan_for = native_plan.field_plan_for
        native_plan._PLAN_CACHE.clear()

        bp = contract_cls(data=payload)
        sealed = bp.is_sealed()
        validated = dict(bp.validated_data) if bp.validated_data is not None else None
        errors = {k: list(v) if isinstance(v, list) else v for k, v in bp.errors.items()}
        return sealed, validated, errors
    finally:
        if prior is None:
            os.environ.pop("AQUILIA_DATAENGINE", None)
        else:
            os.environ["AQUILIA_DATAENGINE"] = prior
        importlib.reload(loader)
        importlib.reload(native_plan)
        import aquilia.contracts.core as core_mod
        import aquilia.contracts.sigil as sigil_mod

        sigil_mod.field_plan_for = native_plan.field_plan_for
        core_mod.field_plan_for = native_plan.field_plan_for
        native_plan._PLAN_CACHE.clear()


def _same(a: Any, b: Any) -> bool:
    """Structural equality that treats two NaNs as equal.

    ``Decimal("NaN") == Decimal("NaN")`` is False by IEEE-754, and the same holds
    for ``float("nan")``. A plain ``==`` on the result tuples would therefore
    report a divergence for a value both paths produced identically. Comparing
    NaN by *representation* is the right test here: the question is whether the
    two paths are distinguishable, and two NaNs of the same type are not.
    """
    if type(a) is not type(b):
        return a == b

    if isinstance(a, (dict,)):
        if a.keys() != b.keys():
            return False
        return all(_same(a[k], b[k]) for k in a)

    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))

    if isinstance(a, (set, frozenset)):
        return a == b

    if isinstance(a, float):
        # NaN != NaN, so fall back to identity of representation.
        return a == b or (a != a and b != b)

    if isinstance(a, Decimal):
        return a == b or (a.is_nan() and b.is_nan())

    return a == b


def assert_parity(contract_cls: type[Contract], payload: dict) -> None:
    """Fail unless the native and Python paths agree on every observable."""
    native = _validate_with_engine(contract_cls, payload, native=True)
    python = _validate_with_engine(contract_cls, payload, native=False)
    assert _same(native, python), (
        f"native/python divergence for {contract_cls.__name__} on {payload!r}\n"
        f"  native: sealed={native[0]} validated={native[1]} errors={native[2]}\n"
        f"  python: sealed={python[0]} validated={python[1]} errors={python[2]}"
    )


# ---------------------------------------------------------------------------
# Anti-vacuity guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "contract_name",
    [
        "ChoiceContract",
        "IntChoiceContract",
        "LiteralContract",
        "MultipleContract",
        "BoundedListContract",
        "UuidListContract",
        "DateListContract",
    ],
)
def test_phase2_contracts_actually_compile_natively(contract_name: str) -> None:
    """Every Phase 2 feature must reach the native path, or the parity tests lie.

    A parity test that compares Python against Python passes unconditionally and
    proves nothing. If a compiler change starts escaping one of these fields, the
    corresponding parity tests would keep passing while silently testing nothing
    -- so the coverage claim is asserted here explicitly.
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
# ChoiceFacet / LiteralFacet
# ---------------------------------------------------------------------------


class ChoiceContract(Contract):
    status = ChoiceFacet(choices=["pending", "active", "done"])


class IntChoiceContract(Contract):
    level = ChoiceFacet(choices=[1, 2, 3])


class LiteralContract(Contract):
    kind = LiteralFacet("user")


@pytest.mark.parametrize(
    "value",
    [
        "pending",
        "active",
        "done",
        "PENDING",  # case-sensitive: must be rejected by both
        "unknown",
        "",
        1,
        None,
        True,
        [],  # unhashable -- `in` raises, both paths must agree
        {},
    ],
)
def test_choice_parity(value: Any) -> None:
    assert_parity(ChoiceContract, {"status": value})


@pytest.mark.parametrize("value", [1, 2, 3, 0, 4, True, False, "1", 1.0, None])
def test_int_choice_parity(value: Any) -> None:
    """``1 == True`` and ``1 == 1.0`` in Python, so set membership accepts them.

    This is the case a naive native implementation gets wrong: comparing by
    identity or by type would reject ``True`` where Python's ``in`` accepts it.
    """
    assert_parity(IntChoiceContract, {"level": value})


@pytest.mark.parametrize("value", ["user", "admin", "", None, 0])
def test_literal_parity(value: Any) -> None:
    assert_parity(LiteralContract, {"kind": value})


def test_choice_missing_key() -> None:
    assert_parity(ChoiceContract, {})


# ---------------------------------------------------------------------------
# multiple_of
# ---------------------------------------------------------------------------


class MultipleContract(Contract):
    count = IntFacet(multiple_of=5)


class NegativeMultipleContract(Contract):
    offset = IntFacet(multiple_of=3, min_value=-100)


@pytest.mark.parametrize("value", [0, 5, 10, 100, 7, 3, -5, -7, 1, "10", "7", 5.0, 7.5, True])
def test_multiple_of_parity(value: Any) -> None:
    assert_parity(MultipleContract, {"count": value})


@pytest.mark.parametrize("value", [-9, -6, -3, 0, 3, -1, -2, -4])
def test_multiple_of_negative_parity(value: Any) -> None:
    """Python's ``%`` takes the divisor's sign; C's takes the dividend's.

    ``-7 % 5`` is ``3`` in Python and ``-2`` in C. A native modulo written with
    the C operator would accept and reject different negative values, so these
    cases pin the behaviour.
    """
    assert_parity(NegativeMultipleContract, {"offset": value})


def test_float_multiple_of_is_escaped() -> None:
    """FloatFacet.multiple_of uses an epsilon test and must not go native."""
    from aquilia.contracts._native_plan import field_plan_for

    class FloatMultipleContract(Contract):
        ratio = FloatFacet(multiple_of=0.1)

    compiled = field_plan_for(FloatMultipleContract)
    # Either no plan at all, or the field is escaped -- never natively handled.
    assert compiled is None or "ratio" in compiled.escaped


@pytest.mark.parametrize("value", [0.1, 0.3, 0.30000000000000004, 1.0, 0.15])
def test_float_multiple_of_parity(value: Any) -> None:
    class FloatMultipleContract(Contract):
        ratio = FloatFacet(multiple_of=0.1)

    assert_parity(FloatMultipleContract, {"ratio": value})


# ---------------------------------------------------------------------------
# List item bounds
# ---------------------------------------------------------------------------


class BoundedListContract(Contract):
    tags = ListFacet(child=TextFacet(), min_items=2, max_items=4)


class MinOnlyListContract(Contract):
    items = ListFacet(child=IntFacet(), min_items=1)


@pytest.mark.parametrize(
    "value",
    [
        [],
        ["a"],
        ["a", "b"],
        ["a", "b", "c"],
        ["a", "b", "c", "d"],
        ["a", "b", "c", "d", "e"],
        ["a", ""],  # blank element -- TextFacet.seal rejects it
        ["a", 1],  # int coerces to str in Python
        ["a", None],
        "notalist",
        None,
    ],
)
def test_list_bounds_parity(value: Any) -> None:
    assert_parity(BoundedListContract, {"tags": value})


@pytest.mark.parametrize("value", [[], [1], [1, 2, 3], ["1"], [1.5], [True]])
def test_list_min_only_parity(value: Any) -> None:
    assert_parity(MinOnlyListContract, {"items": value})


# ---------------------------------------------------------------------------
# List of UUID / date
# ---------------------------------------------------------------------------


class UuidListContract(Contract):
    ids = ListFacet(child=UUIDFacet())


class DateListContract(Contract):
    days = ListFacet(child=DateFacet())


@pytest.mark.parametrize(
    "value",
    [
        [],
        ["123e4567-e89b-12d3-a456-426614174000"],
        ["123e4567-e89b-12d3-a456-426614174000", "00000000-0000-0000-0000-000000000000"],
        ["not-a-uuid"],
        ["123e4567e89b12d3a456426614174000"],  # no hyphens: uuid.UUID accepts
        [uuid.uuid4()],
        [None],
        [123],
    ],
)
def test_list_uuid_parity(value: Any) -> None:
    assert_parity(UuidListContract, {"ids": value})


@pytest.mark.parametrize(
    "value",
    [
        [],
        ["2026-01-15"],
        ["2026-01-15", "2020-12-31"],
        ["2026-02-30"],  # invalid calendar date
        ["not-a-date"],
        [datetime.date(2026, 1, 15)],
        [datetime.datetime(2026, 1, 15, 10, 30)],  # datetime -> date in Python
        [None],
    ],
)
def test_list_date_parity(value: Any) -> None:
    assert_parity(DateListContract, {"days": value})


# ---------------------------------------------------------------------------
# Child-constraint escape
# ---------------------------------------------------------------------------


def test_constrained_child_is_escaped() -> None:
    """A list child carrying its own constraints must not be natively handled.

    ``cast_list_of`` runs only the element cast, never the child's ``seal``, so a
    child with ``min_length`` would have that constraint silently dropped.
    """
    from aquilia.contracts._native_plan import field_plan_for

    class ConstrainedChildContract(Contract):
        codes = ListFacet(child=TextFacet(min_length=3))

    compiled = field_plan_for(ConstrainedChildContract)
    assert compiled is None or "codes" in compiled.escaped


@pytest.mark.parametrize("value", [["abc"], ["ab"], ["abcd", "xy"], []])
def test_constrained_child_parity(value: Any) -> None:
    """The escape must still produce the same answer as the all-Python path."""

    class ConstrainedChildContract(Contract):
        codes = ListFacet(child=TextFacet(min_length=3))

    assert_parity(ConstrainedChildContract, {"codes": value})


# ---------------------------------------------------------------------------
# Mixed contracts: native and escaped fields side by side
# ---------------------------------------------------------------------------


class MixedContract(Contract):
    name = TextFacet(min_length=2, max_length=20)
    age = IntFacet(min_value=0, max_value=150, multiple_of=1)
    status = ChoiceFacet(choices=["on", "off"])
    tags = ListFacet(child=TextFacet(), min_items=1, max_items=3)
    active = BoolFacet()
    ratio = FloatFacet(multiple_of=0.5)  # escaped: float multiple_of


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Ada", "age": 36, "status": "on", "tags": ["x"], "active": True, "ratio": 1.0},
        {"name": "A", "age": 36, "status": "on", "tags": ["x"], "active": True, "ratio": 1.0},
        {"name": "Ada", "age": -1, "status": "on", "tags": ["x"], "active": True, "ratio": 1.0},
        {"name": "Ada", "age": 36, "status": "bad", "tags": ["x"], "active": True, "ratio": 1.0},
        {"name": "Ada", "age": 36, "status": "on", "tags": [], "active": True, "ratio": 1.0},
        {"name": "Ada", "age": 36, "status": "on", "tags": ["x"], "active": "yes", "ratio": 1.0},
        {"name": "Ada", "age": 36, "status": "on", "tags": ["x"], "active": True, "ratio": 0.3},
        {},
    ],
)
def test_mixed_contract_parity(payload: dict) -> None:
    assert_parity(MixedContract, payload)


# ---------------------------------------------------------------------------
# Defaults and nullability interaction
# ---------------------------------------------------------------------------


class DefaultedChoiceContract(Contract):
    status = ChoiceFacet(choices=["a", "b"], default="a")
    level = ChoiceFacet(choices=[1, 2], allow_null=True)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "b"},
        {"status": None},
        {"level": None},
        {"level": 1},
        {"status": "b", "level": 2},
        {"status": "z", "level": 9},
    ],
)
def test_defaulted_choice_parity(payload: dict) -> None:
    assert_parity(DefaultedChoiceContract, payload)
