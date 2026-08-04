"""Eligibility: ineligible contracts must actually fall back.

``docs/models-engine/07-testing-strategy.md`` §5 makes the point that drives
this file: the Phase 9 router shipped with a test asserting the native tier was
*actually being used*, because an eligibility bug that rejected everything would
leave the whole parity suite green while the engine sat idle. Both directions
are failures:

* a plan that compiles when it should not -> silent divergence from Python
* a plan that never compiles -> a green suite proving nothing

So this file asserts both, and the "actually used" test is not optional.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE
from aquilia.contracts import Contract
from aquilia.contracts._native_plan import field_plan_for
from aquilia.contracts.facets import Computed, TextFacet

pytestmark = pytest.mark.skipif(not DATAENGINE_NATIVE, reason="native data engine not built")


# ---------------------------------------------------------------------------
# Eligible -- the native path must actually be taken
# ---------------------------------------------------------------------------


class SimpleScalars(Contract):
    name: str
    count: int
    ratio: float
    active: bool


class MixedScalars(Contract):
    name: str
    count: int
    created: datetime
    start: date
    ident: uuid.UUID


def test_simple_contract_is_eligible():
    """Guard against a green suite that proves nothing."""
    plan = field_plan_for(SimpleScalars)
    assert plan is not None
    assert len(plan) == 4


def test_mixed_scalar_contract_is_eligible():
    plan = field_plan_for(MixedScalars)
    assert plan is not None


def test_eligible_plan_actually_executes():
    plan = field_plan_for(SimpleScalars)
    out = plan.execute({"name": "alice", "count": 1, "ratio": 1.5, "active": True})
    assert out == {"name": "alice", "count": 1, "ratio": 1.5, "active": True}


def test_plan_is_cached_per_class():
    """One plan per contract -- the Sigil is immutable after class build."""
    assert field_plan_for(SimpleScalars) is field_plan_for(SimpleScalars)


# ---------------------------------------------------------------------------
# Ineligible -- each of these must compile to None
# ---------------------------------------------------------------------------


class WithValidator(Contract):
    name: str = TextFacet(validators=[lambda v: None])


class WithPattern(Contract):
    code: str = TextFacet(pattern=r"^[A-Z]+$")


class WithCallableDefault(Contract):
    # Sigil.validate calls `facet.default() if callable(facet.default)`, so a
    # callable default is user code on the validation path.
    tags: str = TextFacet(default=lambda: "x")


class WithComputed(Contract):
    name: str
    label: str = Computed(lambda self: "x")


class WithDecimal(Contract):
    price: Decimal


class Inner(Contract):
    x: int


class WithNested(Contract):
    inner: Inner


@pytest.mark.parametrize(
    "contract",
    [
        pytest.param(WithValidator, id="validator"),
        pytest.param(WithPattern, id="pattern"),
        pytest.param(WithCallableDefault, id="callable-default"),
        pytest.param(WithComputed, id="computed"),
        pytest.param(WithDecimal, id="decimal-v1-exclusion"),
        pytest.param(WithNested, id="nested-contract"),
    ],
)
def test_ineligible_contracts_compile_to_none(contract):
    assert field_plan_for(contract) is None


def test_custom_facet_subclass_is_ineligible():
    """type(facet) is X, not isinstance: a subclass may override cast/seal, and
    running base semantics against it would be a silent divergence."""

    class MyText(TextFacet):
        def cast(self, value):  # noqa: ANN001, ANN201
            return str(value).upper()

    class WithCustomFacet(Contract):
        name: str = MyText()

    assert field_plan_for(WithCustomFacet) is None


# ---------------------------------------------------------------------------
# Per-call eligibility -- a compiled plan still defers on the wrong shape
# ---------------------------------------------------------------------------


def test_non_dict_payload_falls_back():
    """MultiDict/FormData need alternate-key handling that lives in Python."""

    class DictSubclass(dict):
        pass

    plan = field_plan_for(SimpleScalars)
    payload = DictSubclass(name="a", count=1, ratio=1.0, active=True)
    assert plan.execute(payload) is None


def test_failing_field_falls_back_to_python():
    """Any failure aborts the payload so Python produces the real error --
    which is what keeps messages byte-identical and localised."""
    plan = field_plan_for(SimpleScalars)
    assert plan.execute({"name": "a", "count": "not-an-int", "ratio": 1.0, "active": True}) is None


def test_missing_required_falls_back():
    plan = field_plan_for(SimpleScalars)
    assert plan.execute({"name": "a"}) is None


def test_partial_mode_uses_python_path():
    """partial=True is excluded from v1: PATCH semantics skip required checks."""
    c = SimpleScalars(data={"name": "a"}, partial=True)
    assert c.is_sealed(), c.errors
    assert "count" not in c.validated_data


def test_int_facet_rejections_fall_back():
    """Every counter-intuitive IntFacet row (05 §3.1) must defer, not decide."""
    plan = field_plan_for(SimpleScalars)
    base = {"name": "a", "ratio": 1.0, "active": True}
    for bad in (True, False, 3.9, float("nan"), float("inf"), "3.9", Decimal("3.9")):
        assert plan.execute({**base, "count": bad}) is None, bad


def test_int_facet_accepts_integral_float():
    plan = field_plan_for(SimpleScalars)
    out = plan.execute({"name": "a", "count": 3.0, "ratio": 1.0, "active": True})
    assert out["count"] == 3
    assert type(out["count"]) is int


def test_text_trim_defers_when_stripping_needed():
    """trim defaults to True, so a value needing a strip must go to Python."""
    plan = field_plan_for(SimpleScalars)
    assert plan.execute({"name": "  alice  ", "count": 1, "ratio": 1.0, "active": True}) is None


def test_text_blank_defers():
    """TextFacet.seal rejects "" unless allow_blank."""
    plan = field_plan_for(SimpleScalars)
    assert plan.execute({"name": "", "count": 1, "ratio": 1.0, "active": True}) is None
