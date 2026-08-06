"""Differential parity tests for the Phase 2 Tier 3 native FieldPlan additions.

Covers nested Contracts (single and to-many), ``TextFacet.pattern``,
``DictFacet``, and ``BytesFacet``.

The property asserted is the one every tier asserts: a payload validated with
the native engine enabled must produce a byte-identical ``(sealed,
validated_data, errors)`` triple to the same payload validated with it disabled.

Nested Contracts are the highest-risk addition in the whole engine, because the
Python path (``sigil.run_nested_contract``) does more than run the child's
structural pass -- it instantiates the child, runs its ``@ward`` methods, and
calls its ``validate()`` hook. Both are user Python, which the engine may never
execute. The eligibility tests below pin that a child declaring either is
escaped, and the parity tests pin that the escape still lands on the same answer.
"""

from __future__ import annotations

from typing import Any

import pytest

from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import (
    BytesFacet,
    DictFacet,
    IntFacet,
    TextFacet,
)
from tests.dataengine.test_fieldplan_phase2_parity import assert_parity


def _compiled(contract_cls: type[Contract]):
    """Freshly compiled plan for a contract, bypassing the cache."""
    import aquilia.contracts._native_plan as native_plan

    native_plan._PLAN_CACHE.clear()
    return native_plan.field_plan_for(contract_cls)


def _require_native() -> None:
    from aquilia._dataengine_loader import DATAENGINE_NATIVE

    if not DATAENGINE_NATIVE:
        pytest.skip("native data engine not built")


# ---------------------------------------------------------------------------
# Nested Contracts
# ---------------------------------------------------------------------------


class Inner(Contract):
    a: int
    b: str


class Outer(Contract):
    inner: Inner
    n: int


class ManyOuter(Contract):
    items: list[Inner]
    label: str


class DeepInner(Contract):
    x: int


class DeepMiddle(Contract):
    deep: DeepInner
    m: str


class DeepOuter(Contract):
    middle: DeepMiddle
    o: int


@pytest.mark.parametrize(
    "payload",
    [
        {"inner": {"a": 1, "b": "x"}, "n": 5},
        {"inner": {"a": "12", "b": "x"}, "n": 5},  # child coerces
        {"inner": {"a": "notint", "b": "x"}, "n": 5},  # child rejects
        {"inner": {"a": 1}, "n": 5},  # child missing required
        {"inner": {"a": 1, "b": ""}, "n": 5},  # blank rejected by TextFacet
        {"inner": {}, "n": 5},
        {"inner": None, "n": 5},
        {"inner": "notadict", "n": 5},
        {"inner": [], "n": 5},
        {"n": 5},  # nested field absent
        {"inner": {"a": 1, "b": "x"}},  # sibling absent
        {},
        # An unknown key inside the child. Sigil does not reject unknown fields
        # (only Contract.is_sealed does, at the top level), so this must pass.
        {"inner": {"a": 1, "b": "x", "extra": 9}, "n": 5},
    ],
)
def test_nested_single_parity(payload: dict) -> None:
    assert_parity(Outer, payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"items": [{"a": 1, "b": "x"}], "label": "L"},
        {"items": [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}], "label": "L"},
        {"items": [], "label": "L"},
        {"items": [{"a": 1, "b": ""}], "label": "L"},  # one bad element
        {"items": [{"a": 1, "b": "x"}, {"a": "bad", "b": "y"}], "label": "L"},
        {"items": [{"a": 1, "b": "x"}, "notadict"], "label": "L"},
        {"items": "notalist", "label": "L"},
        {"items": None, "label": "L"},
        {"items": ({"a": 1, "b": "x"},), "label": "L"},  # tuple input
        {"label": "L"},
    ],
)
def test_nested_many_parity(payload: dict) -> None:
    assert_parity(ManyOuter, payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"middle": {"deep": {"x": 1}, "m": "s"}, "o": 2},
        {"middle": {"deep": {"x": "bad"}, "m": "s"}, "o": 2},
        {"middle": {"deep": {}, "m": "s"}, "o": 2},
        {"middle": {"m": "s"}, "o": 2},
        {"middle": {"deep": None, "m": "s"}, "o": 2},
    ],
)
def test_nested_three_levels_parity(payload: dict) -> None:
    """Recursion must compose: the middle plan runs the deep plan."""
    assert_parity(DeepOuter, payload)


def test_nested_compiles_fully_native() -> None:
    _require_native()
    for cls, covered in ((Outer, 2), (ManyOuter, 2), (DeepOuter, 2)):
        compiled = _compiled(cls)
        assert compiled is not None, f"{cls.__name__} produced no plan"
        assert not compiled.escaped, f"{cls.__name__} escaped {sorted(compiled.escaped)}"
        assert len(compiled.plan) == covered


# ---------------------------------------------------------------------------
# Nested eligibility gates -- the child must contain no user Python
# ---------------------------------------------------------------------------


class WardChild(Contract):
    a: int

    @ward
    def always_ok(self, data: Any) -> None:
        """A ward that passes. Its *existence* is what must force the escape."""


class WardOuter(Contract):
    child: WardChild


class ValidateChild(Contract):
    a: int

    def validate(self, data: Any) -> Any:
        return data


class ValidateOuter(Contract):
    child: ValidateChild


class PartialChild(Contract):
    """One field escapes, so the child plan is partial and unusable as a sub-plan."""

    a: int
    checked: str = TextFacet(validators=[lambda v: None])


class PartialOuter(Contract):
    child: PartialChild


@pytest.mark.parametrize("contract_cls", [WardOuter, ValidateOuter, PartialOuter])
def test_nested_with_user_python_is_escaped(contract_cls: type[Contract]) -> None:
    """A child running any Python beyond its structural pass must not go native.

    ``run_nested_contract`` executes the child's wards and ``validate()`` hook.
    Neither can run in the engine, and a partial child plan has nowhere to
    report its escaped fields from through the parent's single native pass.
    """
    _require_native()
    compiled = _compiled(contract_cls)
    assert compiled is None or "child" in compiled.escaped


@pytest.mark.parametrize(
    "payload",
    [{"child": {"a": 1}}, {"child": {"a": "bad"}}, {"child": {}}, {}],
)
def test_ward_child_parity(payload: dict) -> None:
    """The escape must still agree with the all-Python path."""
    assert_parity(WardOuter, payload)


@pytest.mark.parametrize("payload", [{"child": {"a": 1}}, {"child": {"a": "bad"}}, {}])
def test_validate_child_parity(payload: dict) -> None:
    assert_parity(ValidateOuter, payload)


@pytest.mark.parametrize(
    "payload",
    [{"child": {"a": 1, "checked": "x"}}, {"child": {"a": "bad", "checked": "x"}}, {}],
)
def test_partial_child_parity(payload: dict) -> None:
    assert_parity(PartialOuter, payload)


# ---------------------------------------------------------------------------
# Self-reference: compiling it would not terminate
# ---------------------------------------------------------------------------


class SelfRef(Contract):
    label: str
    child: SelfRef = None


def test_self_referential_field_is_escaped() -> None:
    """A Contract nesting itself must escape that field, not recurse forever.

    The sibling scalars still compile -- the cycle guard is per field, so a
    self-referential Contract keeps native handling for everything else.
    """
    _require_native()
    compiled = _compiled(SelfRef)
    assert compiled is not None
    assert "child" in compiled.escaped
    assert len(compiled.plan) == 1  # `label` still native


@pytest.mark.parametrize(
    "payload",
    [
        {"label": "a"},
        {"label": "a", "child": {"label": "b"}},
        {"label": "a", "child": {"label": "b", "child": {"label": "c"}}},
        {"label": "a", "child": None},
        {"label": "a", "child": "notadict"},
    ],
)
def test_self_referential_parity(payload: dict) -> None:
    assert_parity(SelfRef, payload)


# ---------------------------------------------------------------------------
# TextFacet.pattern
# ---------------------------------------------------------------------------


class Patterned(Contract):
    code = TextFacet(pattern=r"^[A-Z]+$")


class PatternedBounded(Contract):
    code = TextFacet(pattern=r"[0-9]+", min_length=3, max_length=6)


@pytest.mark.parametrize(
    "value",
    ["ABC", "abc", "A", "", "ABC123", "  ABC  ", "ÀBC", 123, None],
)
def test_pattern_parity(value: Any) -> None:
    assert_parity(Patterned, {"code": value})


@pytest.mark.parametrize(
    "value",
    [
        "12345",
        "abc123",  # search(), not match(): an unanchored pattern hits anywhere
        "ab",  # too short -- length is checked before the pattern
        "abcdefg",  # too long
        "abcdef",
        "xyz",  # long enough, but no digit
    ],
)
def test_pattern_with_length_bounds_parity(value: Any) -> None:
    """Length is checked before the pattern, so the first violation must match."""
    assert_parity(PatternedBounded, {"code": value})


def test_pattern_compiles_natively() -> None:
    _require_native()
    for cls in (Patterned, PatternedBounded):
        compiled = _compiled(cls)
        assert compiled is not None and not compiled.escaped


def test_email_facet_still_escapes() -> None:
    """EmailFacet is a TextFacet *subclass* with its own seal override.

    Its regex lives on the class, not in ``self.pattern``, and its ``cast``
    lowercases. Pattern support must not accidentally pull it native.
    """
    _require_native()
    from aquilia.contracts.facets import EmailFacet

    class WithEmail(Contract):
        addr = EmailFacet()

    compiled = _compiled(WithEmail)
    assert compiled is None or "addr" in compiled.escaped


# ---------------------------------------------------------------------------
# DictFacet
# ---------------------------------------------------------------------------


class TypedDictC(Contract):
    meta = DictFacet(value_facet=IntFacet())


class PlainDictC(Contract):
    meta = DictFacet()


class BoundedDictC(Contract):
    meta = DictFacet(max_keys=3)


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"a": 1},
        {"a": 1, "b": 2},
        {"a": "2"},  # coerced by the value facet
        {"a": "notint"},
        {"a": None},
        {"a": True},  # bool rejected by IntFacet
        {1: 2},  # non-str key
        '{"a": 1}',  # JSON string -- Python parses it, native defers
        "notadict",
        [],
        None,
    ],
)
def test_typed_dict_parity(value: Any) -> None:
    assert_parity(TypedDictC, {"meta": value})


@pytest.mark.parametrize(
    "value",
    [{}, {"a": 1}, {"a": "anything"}, {"a": [1, 2]}, {"a": None}, {1: 2}, "notadict", None],
)
def test_plain_dict_parity(value: Any) -> None:
    """With no value_facet, Python stores values untouched -- anything is valid."""
    assert_parity(PlainDictC, {"meta": value})


@pytest.mark.parametrize(
    "value",
    [{}, {"a": 1}, {"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 2, "c": 3, "d": 4}],
)
def test_bounded_dict_parity(value: Any) -> None:
    assert_parity(BoundedDictC, {"meta": value})


def test_dict_compiles_natively() -> None:
    _require_native()
    for cls in (TypedDictC, PlainDictC, BoundedDictC):
        compiled = _compiled(cls)
        assert compiled is not None and not compiled.escaped


def test_dict_result_is_a_fresh_object() -> None:
    """DictFacet.cast builds a new dict; mutating the payload after must not
    be observable in the validated data."""
    payload_inner = {"a": 1}
    bp = TypedDictC(data={"meta": payload_inner})
    assert bp.is_sealed()
    payload_inner["b"] = 2
    assert bp.validated_data["meta"] == {"a": 1}


# ---------------------------------------------------------------------------
# BytesFacet
# ---------------------------------------------------------------------------


class BytesC(Contract):
    blob = BytesFacet()


class BoundedBytesC(Contract):
    blob = BytesFacet(min_length=2, max_length=8)


class HexBytesC(Contract):
    blob = BytesFacet(encoding="hex")


@pytest.mark.parametrize(
    "value",
    [
        b"abc",
        b"",
        bytearray(b"abc"),
        memoryview(b"abc"),
        "aGVsbG8=",  # valid base64 -- native defers, Python decodes
        "not base64!",
        "",
        123,
        None,
    ],
)
def test_bytes_parity(value: Any) -> None:
    assert_parity(BytesC, {"blob": value})


@pytest.mark.parametrize(
    "value",
    [b"ab", b"a", b"", b"abcdefgh", b"abcdefghi", bytearray(b"abcd"), "aGVsbG8="],
)
def test_bounded_bytes_parity(value: Any) -> None:
    """Bounds count *decoded* bytes."""
    assert_parity(BoundedBytesC, {"blob": value})


@pytest.mark.parametrize("value", [b"abc", "616263", "zzz", ""])
def test_hex_bytes_parity(value: Any) -> None:
    """The encoding only affects the str branch, which always defers."""
    assert_parity(HexBytesC, {"blob": value})


def test_bytes_compiles_natively() -> None:
    _require_native()
    for cls in (BytesC, BoundedBytesC, HexBytesC):
        compiled = _compiled(cls)
        assert compiled is not None and not compiled.escaped


# ---------------------------------------------------------------------------
# Everything at once
# ---------------------------------------------------------------------------


class Tier3Sink(Contract):
    inner: Inner
    rows: list[Inner]
    code = TextFacet(pattern=r"^[A-Z]{2,}$")
    meta = DictFacet(value_facet=IntFacet(), max_keys=4)
    blob = BytesFacet(min_length=1)
    n: int


_VALID = {
    "inner": {"a": 1, "b": "x"},
    "rows": [{"a": 2, "b": "y"}],
    "code": "AB",
    "meta": {"k": 1},
    "blob": b"z",
    "n": 7,
}


@pytest.mark.parametrize(
    "override",
    [
        {},
        {"inner": {"a": "bad", "b": "x"}},
        {"inner": None},
        {"rows": [{"a": 1, "b": ""}]},
        {"rows": []},
        {"code": "a"},
        {"meta": {"k": "bad"}},
        {"meta": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}},
        {"blob": b""},
        {"n": "notint"},
    ],
)
def test_tier3_sink_parity(override: dict) -> None:
    assert_parity(Tier3Sink, {**_VALID, **override})


def test_tier3_sink_compiles_fully_native() -> None:
    _require_native()
    compiled = _compiled(Tier3Sink)
    assert compiled is not None
    assert not compiled.escaped, f"escaped {sorted(compiled.escaped)}"
    assert len(compiled.plan) == 6
