"""Validation parity: the native path must agree with Sigil.validate exactly.

The design makes one half of this trivial and the other half essential:

* On **failure**, the native plan returns None and the payload is re-validated
  by Python, so error messages are byte-identical by construction rather than by
  careful reimplementation. (This is a deliberate departure from
  ``docs/models-engine/05`` §3.7, which proposed caching resolved message
  strings at compile time -- unsound, because ``contract_message`` resolves
  through a request-scoped i18n ContextVar, so the same key yields different
  text per locale.)

* On **success**, the validated dict must match Python's exactly -- same keys,
  same values, same types. That is what these tests pin.

Every test asserts against ``Sigil.validate`` rather than against a hardcoded
expectation, so the Python path stays the reference implementation.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE
from aquilia.contracts import Contract
from aquilia.contracts._native_plan import field_plan_for
from aquilia.contracts.facets import TextFacet

pytestmark = pytest.mark.skipif(not DATAENGINE_NATIVE, reason="native data engine not built")


class Wide(Contract):
    name: str
    count: int
    ratio: float
    active: bool
    created: datetime
    start: date
    at: time
    ident: uuid.UUID


class Optionals(Contract):
    required_field: str
    optional_null: str | None = None
    with_default: str = "fallback"


class Bounded(Contract):
    qty: int = 0
    label: str = TextFacet(default="x", min_length=2, max_length=8)


def _assert_parity(contract_cls, payload):
    """Native and Python must agree, whichever path each takes."""
    compiled = field_plan_for(contract_cls)
    assert compiled is not None, "contract should be eligible for this test to mean anything"

    py_errors, py_validated = contract_cls._sigil.validate(payload)
    native = compiled.plan.execute(payload)

    if native is None:
        # Deferred: Python owns the outcome. Nothing to compare, but the reason
        # must be a real one -- either an error, or a value the plan declined.
        return py_errors, py_validated

    # The plan may have escaped some fields to Python. Merge both results.
    if compiled.escaped:
        escaped_errors, escaped_validated = contract_cls._sigil.validate(
            payload, _only=compiled.escaped
        )
        if escaped_errors:
            # Escaped field failed; no native dict to compare.
            return py_errors, py_validated
        native.update(escaped_validated)

    assert not py_errors, f"native accepted a payload Python rejected: {py_errors}"
    assert native == py_validated
    for key, value in native.items():
        assert type(value) is type(py_validated[key]), key
    return py_errors, py_validated


# ---------------------------------------------------------------------------
# Success-path parity
# ---------------------------------------------------------------------------

WIDE_PAYLOAD = {
    "name": "alice",
    "count": 42,
    "ratio": 1.5,
    "active": True,
    "created": "2026-01-15T10:30:00",
    "start": "2026-01-15",
    "at": "10:30:00",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
}


def test_wide_payload_parity():
    _assert_parity(Wide, WIDE_PAYLOAD)


def test_wide_payload_takes_native_path():
    """If this ever returns None the parity test above proves nothing."""
    assert field_plan_for(Wide).plan.execute(WIDE_PAYLOAD) is not None


@pytest.mark.parametrize(
    "override",
    [
        {"count": 0},
        {"count": -1},
        {"count": 3.0},  # integral float is accepted
        {"count": "42"},  # numeric string
        {"count": 123456789012345678901234567890},  # unbounded int
        {"ratio": 0.0},
        {"ratio": "2.5"},
        {"ratio": 3},  # int -> float
        {"active": False},
        {"created": "2026-01-15T10:30:00.123456"},
        {"created": "2026-01-15T10:30:00+00:00"},
        {"start": "2024-02-29"},  # leap day
        {"ident": "550E8400-E29B-41D4-A716-446655440000"},
        {"ident": "{550e8400-e29b-41d4-a716-446655440000}"},
        {"ident": "urn:uuid:550e8400-e29b-41d4-a716-446655440000"},
        {"name": "x"},
        {"name": "unicode: café ☕"},
        {"name": "a" * 5000},
    ],
)
def test_wide_payload_variants_parity(override):
    _assert_parity(Wide, {**WIDE_PAYLOAD, **override})


# ---------------------------------------------------------------------------
# Missing vs explicit None -- 05 §3.4 / §3.5, different resolution paths
# ---------------------------------------------------------------------------


class SkipVsNull(Contract):
    # required=False, allow_null=False, no default. This is the shape where the
    # missing/None distinction is actually observable: a missing key is skipped
    # silently, while an explicit None is a "not_null" error. With allow_null=True
    # or a default present, both paths converge on None and the distinction
    # disappears -- an earlier version of this test used such a shape and proved
    # nothing.
    req: str
    opt: str = TextFacet(required=False)


def test_missing_is_skipped_but_explicit_none_errors():
    """05 §3.5: a missing key and an explicit None follow different paths."""
    missing = SkipVsNull(data={"req": "x"})
    assert missing.is_sealed(), missing.errors
    assert "opt" not in missing.validated_data

    explicit = SkipVsNull(data={"req": "x", "opt": None})
    assert not explicit.is_sealed()
    py_errors, _ = SkipVsNull._sigil.validate({"req": "x", "opt": None})
    assert explicit.errors == py_errors


def test_missing_optional_matches_python_exactly():
    _assert_parity(SkipVsNull, {"req": "x"})


def test_nullable_without_default_still_yields_none():
    """When allow_null is set, a missing key resolves to None -- and the native
    path must agree rather than skipping the key."""

    class Nullable(Contract):
        req: str
        maybe: str = TextFacet(required=False, allow_null=True)

    _assert_parity(Nullable, {"req": "x"})
    plan = field_plan_for(Nullable).plan
    assert plan.execute({"req": "x"}) == {"req": "x", "maybe": None}


def test_default_is_used_when_key_absent():
    c = Optionals(data={"required_field": "x"})
    assert c.is_sealed(), c.errors
    assert c.validated_data["with_default"] == "fallback"


def test_default_wins_over_required():
    """05 §3.4: default is consulted BEFORE required, so a field that is both
    required and defaulted uses the default rather than erroring."""
    c = Bounded(data={})
    assert c.is_sealed(), c.errors
    assert c.validated_data["qty"] == 0


def test_explicit_none_on_non_nullable_errors_identically():
    payload = {"required_field": None}
    c = Optionals(data=payload)
    assert not c.is_sealed()
    py_errors, _ = Optionals._sigil.validate(payload)
    assert c.errors == py_errors


# ---------------------------------------------------------------------------
# Failure-path parity -- errors always come from Python, so they must match
# ---------------------------------------------------------------------------

FAILING_PAYLOADS = [
    {},
    {"name": "alice"},
    {**WIDE_PAYLOAD, "count": "abc"},
    {**WIDE_PAYLOAD, "count": True},
    {**WIDE_PAYLOAD, "count": 3.9},
    {**WIDE_PAYLOAD, "ratio": "not-a-float"},
    {**WIDE_PAYLOAD, "created": "not-a-datetime"},
    {**WIDE_PAYLOAD, "ident": "not-a-uuid"},
    {**WIDE_PAYLOAD, "name": None},
    {**WIDE_PAYLOAD, "name": ""},
]


@pytest.mark.parametrize("payload", FAILING_PAYLOADS)
def test_error_messages_are_byte_identical(payload):
    """Messages appear in HTTP 422 bodies, so they are public API. Equivalent is
    not sufficient -- identical is required."""
    c = Wide(data=dict(payload))
    sealed = c.is_sealed()
    py_errors, _ = Wide._sigil.validate(dict(payload))
    assert sealed == (not py_errors)
    assert c.errors == py_errors


@pytest.mark.parametrize("payload", FAILING_PAYLOADS)
def test_failing_payloads_defer_to_python(payload):
    plan = field_plan_for(Wide).plan
    py_errors, _ = Wide._sigil.validate(dict(payload))
    if py_errors:
        assert plan.execute(dict(payload)) is None


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("label", ["ab", "abcdefgh", "abcd"])
def test_length_bounds_accepted(label):
    _assert_parity(Bounded, {"qty": 1, "label": label})


@pytest.mark.parametrize("label", ["a", "abcdefghi"])
def test_length_bounds_rejected_identically(label):
    payload = {"qty": 1, "label": label}
    c = Bounded(data=dict(payload))
    py_errors, _ = Bounded._sigil.validate(dict(payload))
    assert not c.is_sealed()
    assert c.errors == py_errors


def test_length_is_code_points_not_bytes():
    """A multi-byte character counts as one, matching len()."""
    payload = {"qty": 1, "label": "café"}  # 4 code points, 5 UTF-8 bytes
    c = Bounded(data=payload)
    assert c.is_sealed(), c.errors


# ---------------------------------------------------------------------------
# Extra keys and never-raises
# ---------------------------------------------------------------------------


def test_extra_keys_ignored_by_default():
    _assert_parity(Wide, {**WIDE_PAYLOAD, "unexpected": "ignored"})


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"name": []},
        {"name": {}},
        {"count": object()},
        {"ratio": [1, 2]},
        {"ident": 12345},
        {"created": -1},
    ],
)
def test_never_raises(payload):
    """Sigil.validate's documented contract is 'never raises'. The native path
    must uphold it: a conversion failure is a fallback, never an exception."""
    plan = field_plan_for(Wide).plan
    plan.execute(dict(payload))  # must not raise
    Wide(data=dict(payload)).is_sealed()  # must not raise


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


def test_no_object_growth_over_repeated_validation():
    import gc

    plan = field_plan_for(Wide).plan
    for _ in range(100):
        plan.execute(dict(WIDE_PAYLOAD))
    gc.collect()
    before = len(gc.get_objects())
    for _ in range(10_000):
        plan.execute(dict(WIDE_PAYLOAD))
    gc.collect()
    assert len(gc.get_objects()) - before < 100


def test_payload_refcount_is_balanced():
    import gc
    import sys

    plan = field_plan_for(Wide).plan
    name = "alice"
    payload = {**WIDE_PAYLOAD, "name": name}
    plan.execute(payload)
    gc.collect()
    before = sys.getrefcount(name)
    for _ in range(10_000):
        plan.execute(payload)
    gc.collect()
    assert sys.getrefcount(name) == before
