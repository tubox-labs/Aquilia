"""Eligibility: what compiles natively, what escapes to Python, and proof both happen.

``docs/models-engine/07-testing-strategy.md`` §5 makes the point that drives
this file: the Phase 9 router shipped with a test asserting the native tier was
*actually being used*, because an eligibility bug that rejected everything would
leave the whole parity suite green while the engine sat idle. Both directions
are failures:

* a plan that compiles when it should not -> silent divergence from Python
* a plan that never compiles -> a green suite proving nothing

Eligibility is decided **per field**. A field the plan cannot represent is
escaped -- named in ``CompiledPlan.escaped`` and validated by the ordinary
``Sigil.validate`` loop -- rather than sinking the whole contract. So this file
asserts three things: eligible fields compile, ineligible fields escape, and a
contract whose fields *all* escape produces no plan at all (a plan that covers
nothing is strictly worse than no plan).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE
from aquilia.contracts import Contract, ward
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
    compiled = field_plan_for(SimpleScalars)
    assert compiled is not None
    assert len(compiled.plan) == 4
    assert not compiled.escaped


def test_mixed_scalar_contract_is_eligible():
    compiled = field_plan_for(MixedScalars)
    assert compiled is not None
    assert not compiled.escaped


def test_eligible_plan_actually_executes():
    compiled = field_plan_for(SimpleScalars)
    out = compiled.plan.execute({"name": "alice", "count": 1, "ratio": 1.5, "active": True})
    assert out == {"name": "alice", "count": 1, "ratio": 1.5, "active": True}


def test_plan_is_cached_per_class():
    """One plan per contract -- the Sigil is immutable after class build."""
    assert field_plan_for(SimpleScalars) is field_plan_for(SimpleScalars)


# ---------------------------------------------------------------------------
# Wholly ineligible -- every field escapes, so there is no plan worth having
# ---------------------------------------------------------------------------


class WithValidator(Contract):
    name: str = TextFacet(validators=[lambda v: None])


class WithPattern(Contract):
    code: str = TextFacet(pattern=r"^[A-Z]+$")


class WithCallableDefault(Contract):
    # Sigil.validate calls `facet.default() if callable(facet.default)`, so a
    # callable default is user code on the validation path.
    tags: str = TextFacet(default=lambda: "x")


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
        pytest.param(WithCallableDefault, id="callable-default"),
    ],
)
def test_single_ineligible_field_yields_no_plan(contract):
    """One field, and it escapes -> nothing left to run natively.

    A plan covering zero fields would still cost a failed lookup per field and a
    second validate() call, so it is worse than no plan.
    """
    assert field_plan_for(contract) is None


def test_decimal_is_representable_since_tier2():
    """DecimalFacet was a documented v1 exclusion; Tier 2 lifted it.

    The exclusion existed because ``DecimalFacet.seal`` enforces ``max_digits``
    and ``decimal_places``, which need exponent-aware inspection. Those are now
    read off ``Decimal.as_tuple()`` natively -- the same source the Python code
    reads -- so the field compiles rather than escaping.
    """
    compiled = field_plan_for(WithDecimal)
    assert compiled is not None
    assert not compiled.escaped
    assert len(compiled.plan) == 1


def test_pattern_is_representable_since_tier3():
    """A regex pattern was a v1 exclusion; Tier 3 lifted it.

    The native seal calls the *compiled* ``re.Pattern.search`` -- C code in
    ``_sre``, so a builtin call rather than user Python. Reimplementing a regex
    engine natively was never on the table; borrowing CPython's is exact.
    """
    compiled = field_plan_for(WithPattern)
    assert compiled is not None
    assert not compiled.escaped
    assert len(compiled.plan) == 1


def test_plain_nested_contract_is_representable_since_tier3():
    """A nested Contract with no wards and no validate() override compiles.

    ``run_nested_contract`` reduces to the child's structural pass in that case,
    which is exactly what a recursively compiled sub-plan reproduces.
    """
    compiled = field_plan_for(WithNested)
    assert compiled is not None
    assert not compiled.escaped
    assert len(compiled.plan) == 1


def test_custom_facet_subclass_escapes():
    """type(facet) is X, not isinstance: a subclass may override cast/seal, and
    running base semantics against it would be a silent divergence."""

    class MyText(TextFacet):
        def cast(self, value):  # noqa: ANN001, ANN201
            return str(value).upper()

    class WithCustomFacet(Contract):
        name: str = MyText()

    assert field_plan_for(WithCustomFacet) is None


# ---------------------------------------------------------------------------
# Per-field escape -- one exotic field must not sink its siblings
# ---------------------------------------------------------------------------


class NestedSibling(Contract):
    """The case that made the native path dead in production.

    Nested objects are the normal shape of a real API payload. Under the old
    all-or-nothing rule this contract compiled to None and all four scalars were
    validated in Python. Since Tier 3 the nested field compiles too, so this now
    covers all four -- kept as the regression guard for that.
    """

    name: str
    count: int
    ratio: float
    inner: Inner


class WardedInner(Contract):
    """A nested child whose ward is user Python, so it cannot go native."""

    x: int

    @ward
    def always_ok(self, data):  # noqa: ANN001, ANN201
        """Passes. Its *existence* is what forces the parent field to escape."""


class WardedNestedSibling(Contract):
    name: str
    count: int
    ratio: float
    inner: WardedInner


class ValidatorSibling(Contract):
    name: str
    checked: str = TextFacet(validators=[lambda v: None])


class ComputedSibling(Contract):
    name: str
    label: str = Computed(lambda self: "x")


@pytest.mark.parametrize(
    ("contract", "escaped", "covered"),
    [
        pytest.param(WardedNestedSibling, {"inner"}, 3, id="nested-with-ward"),
        pytest.param(ValidatorSibling, {"checked"}, 1, id="validator"),
        pytest.param(ComputedSibling, {"label"}, 1, id="computed"),
        pytest.param(WithValidator, None, None, id="control-all-escaped"),
    ],
)
def test_ineligible_field_escapes_without_sinking_siblings(contract, escaped, covered):
    compiled = field_plan_for(contract)
    if escaped is None:
        assert compiled is None
        return
    assert compiled is not None
    assert set(compiled.escaped) == escaped
    assert len(compiled.plan) == covered


def test_plain_nested_sibling_now_covers_everything():
    """The contract that motivated per-field escape is now fully native.

    Kept alongside the escape test so the two cases stay visibly distinct: a
    *plain* nested child compiles, a nested child carrying user Python does not.
    """
    compiled = field_plan_for(NestedSibling)
    assert compiled is not None
    assert not compiled.escaped
    assert len(compiled.plan) == 4


def test_escaped_and_covered_fields_are_disjoint():
    """core.py merges the two dicts assuming disjointness; prove it holds."""
    compiled = field_plan_for(NestedSibling)
    # The plan does not expose its field names, but the counts must add up to
    # the contract's full field set with no overlap.
    total = len(NestedSibling._sigil.fields)
    assert len(compiled.plan) + len(compiled.escaped) == total


def test_contract_with_escaped_field_validates_end_to_end():
    """The whole point: native for the scalars, Python for the nested field,
    one correct result."""
    c = NestedSibling(data={"name": "a", "count": 1, "ratio": 1.5, "inner": {"x": 7}})
    assert c.is_sealed(), c.errors
    assert c.validated_data["name"] == "a"
    assert c.validated_data["count"] == 1
    assert c.validated_data["inner"]["x"] == 7


def test_escaped_field_error_is_still_reported():
    """An escaped field's failure must surface, not be silently dropped by the
    native path having already 'succeeded' on the fields it covers."""
    c = NestedSibling(data={"name": "a", "count": 1, "ratio": 1.5, "inner": {"x": "not-an-int"}})
    assert not c.is_sealed()
    assert "inner" in c.errors


def test_escaped_required_field_missing_is_reported():
    c = NestedSibling(data={"name": "a", "count": 1, "ratio": 1.5})
    assert not c.is_sealed()
    assert "inner" in c.errors


# ---------------------------------------------------------------------------
# Per-call eligibility -- a compiled plan still defers on the wrong shape
# ---------------------------------------------------------------------------


def test_non_dict_payload_falls_back():
    """MultiDict/FormData need alternate-key handling that lives in Python."""

    class DictSubclass(dict):
        pass

    compiled = field_plan_for(SimpleScalars)
    payload = DictSubclass(name="a", count=1, ratio=1.0, active=True)
    assert compiled.plan.execute(payload) is None


def test_failing_field_falls_back_to_python():
    """Any failure aborts the payload so Python produces the real error --
    which is what keeps messages byte-identical and localised."""
    compiled = field_plan_for(SimpleScalars)
    assert compiled.plan.execute({"name": "a", "count": "not-an-int", "ratio": 1.0, "active": True}) is None


def test_missing_required_falls_back():
    compiled = field_plan_for(SimpleScalars)
    assert compiled.plan.execute({"name": "a"}) is None


def test_partial_mode_uses_python_path():
    """partial=True is excluded from v1: PATCH semantics skip required checks."""
    c = SimpleScalars(data={"name": "a"}, partial=True)
    assert c.is_sealed(), c.errors
    assert "count" not in c.validated_data


def test_int_facet_rejections_fall_back():
    """Every counter-intuitive IntFacet row (05 §3.1) must defer, not decide."""
    compiled = field_plan_for(SimpleScalars)
    base = {"name": "a", "ratio": 1.0, "active": True}
    for bad in (True, False, 3.9, float("nan"), float("inf"), "3.9", Decimal("3.9")):
        assert compiled.plan.execute({**base, "count": bad}) is None, bad


def test_int_facet_accepts_integral_float():
    compiled = field_plan_for(SimpleScalars)
    out = compiled.plan.execute({"name": "a", "count": 3.0, "ratio": 1.0, "active": True})
    assert out["count"] == 3
    assert type(out["count"]) is int


def test_text_trim_defers_when_stripping_needed():
    """trim defaults to True, so a value needing a strip must go to Python."""
    compiled = field_plan_for(SimpleScalars)
    assert compiled.plan.execute({"name": "  alice  ", "count": 1, "ratio": 1.0, "active": True}) is None


def test_text_blank_defers():
    """TextFacet.seal rejects "" unless allow_blank."""
    compiled = field_plan_for(SimpleScalars)
    assert compiled.plan.execute({"name": "", "count": 1, "ratio": 1.0, "active": True}) is None
