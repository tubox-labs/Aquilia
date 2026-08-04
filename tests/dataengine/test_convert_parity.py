"""Conversion parity: native convert() must equal CPython's own conversion.

``docs/models-engine/07-testing-strategy.md`` §4 requires this be exhaustive
rather than sampled, and specifies the adversarial corpus each type must
include. Values must be `==` **and** the same `type()` -- a native `int` that
returned a `bool`, or a `Decimal` that lost its exponent, would pass a naive
equality check and still be a defect.

Every test here is skipped wholesale when the extension is absent, so a
pure-Python install still reports green rather than erroring.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import date, datetime, time
from decimal import Decimal

import pytest

from aquilia._dataengine_loader import DATAENGINE_NATIVE

pytestmark = pytest.mark.skipif(not DATAENGINE_NATIVE, reason="native data engine not built")

if DATAENGINE_NATIVE:
    from aquilia import _dataengine as de

    TC = de.TypeCode


# ---------------------------------------------------------------------------
# Int -- CPython ints are unbounded, so int64 overflow is a real failure mode
# ---------------------------------------------------------------------------

INT_INPUTS = [
    "0",
    "-0",
    "1",
    "-1",
    "42",
    "9223372036854775807",  # int64 max
    "9223372036854775808",  # int64 max + 1
    "-9223372036854775808",  # int64 min
    "-9223372036854775809",  # int64 min - 1
    "18446744073709551616",  # 2**64
    "123456789012345678901234567890",  # 30 digits, per 07 §4
    "+5",  # int() accepts a leading plus
    "1_000",  # int() accepts digit separators
    "  7  ",  # int() strips surrounding whitespace
    "١٢",  # Arabic-Indic digits; int() accepts any Unicode Nd
]


@pytest.mark.parametrize("raw", INT_INPUTS)
def test_int_parity(raw):
    want = int(raw)
    got = de.convert(TC.INT, raw)
    assert got == want
    assert type(got) is type(want)


def test_int_beyond_int64_is_not_wrapped():
    """A 30-digit id must survive. Silent int64 wrapping is the failure mode."""
    raw = "123456789012345678901234567890"
    assert de.convert(TC.INT, raw) == 123456789012345678901234567890


@pytest.mark.parametrize("raw", ["abc", "3.9", "", "0x10", "nan"])
def test_int_rejects_match_python(raw):
    with pytest.raises(ValueError):
        int(raw)
    with pytest.raises(ValueError):
        de.convert(TC.INT, raw)


def test_int_passthrough_preserves_identity():
    n = 12345
    assert de.convert(TC.INT, n) is n


# ---------------------------------------------------------------------------
# Float
# ---------------------------------------------------------------------------

FLOAT_INPUTS = ["0.0", "-0.0", "1.5", "-1.5", "1e308", "1e-308", "1E10", "inf", "-inf", "  2.5  "]


@pytest.mark.parametrize("raw", FLOAT_INPUTS)
def test_float_parity(raw):
    want = float(raw)
    got = de.convert(TC.FLOAT, raw)
    assert got == want
    assert type(got) is float
    # -0.0 == 0.0 is True, so sign has to be checked separately.
    assert math.copysign(1.0, got) == math.copysign(1.0, want)


def test_float_nan_parity():
    got = de.convert(TC.FLOAT, "nan")
    assert math.isnan(got)
    assert type(got) is float


# ---------------------------------------------------------------------------
# Decimal -- exponent is part of the value for money
# ---------------------------------------------------------------------------

DECIMAL_INPUTS = ["0", "-0", "1.10", "1.1", "19.99", "0.00", "1E+3", "1e-3", "-273.15", "123456789.123456789"]


@pytest.mark.parametrize("raw", DECIMAL_INPUTS)
def test_decimal_parity(raw):
    want = Decimal(raw)
    got = de.convert(TC.DECIMAL, raw)
    assert got == want
    assert type(got) is Decimal
    # The assertion that matters: Decimal("1.10") == Decimal("1.1") is True but
    # they are not interchangeable. as_tuple() is what catches a lost exponent.
    assert got.as_tuple() == want.as_tuple()


def test_decimal_preserves_trailing_zero_exponent():
    got = de.convert(TC.DECIMAL, "1.10")
    assert got.as_tuple() == Decimal("1.10").as_tuple()
    assert got.as_tuple() != Decimal("1.1").as_tuple()


# ---------------------------------------------------------------------------
# Date / DateTime / Time
# ---------------------------------------------------------------------------

DATE_INPUTS = ["2026-01-15", "0001-01-01", "9999-12-31", "2024-02-29"]  # leap day


@pytest.mark.parametrize("raw", DATE_INPUTS)
def test_date_parity(raw):
    want = date.fromisoformat(raw)
    got = de.convert(TC.DATE, raw)
    assert got == want
    assert type(got) is date


DATETIME_INPUTS = [
    "2026-01-15T10:30:00",
    "2026-01-15T10:30:00.123456",  # fractional seconds
    "2026-01-15T10:30:00+00:00",  # tz offset
    "2026-01-15T10:30:00-05:00",
    "0001-01-01T00:00:00",
    "9999-12-31T23:59:59",
]


@pytest.mark.parametrize("raw", DATETIME_INPUTS)
def test_datetime_parity(raw):
    want = datetime.fromisoformat(raw)
    got = de.convert(TC.DATETIME, raw)
    assert got == want
    assert type(got) is datetime
    assert got.tzinfo == want.tzinfo
    assert got.microsecond == want.microsecond


@pytest.mark.parametrize("raw", ["10:30:00", "00:00:00", "23:59:59.999999"])
def test_time_parity(raw):
    want = time.fromisoformat(raw)
    got = de.convert(TC.TIME, raw)
    assert got == want
    assert type(got) is time


# ---------------------------------------------------------------------------
# UUID -- the one natively-parsed conversion, so the corpus is widest here
# ---------------------------------------------------------------------------

UUID_ACCEPTED = [
    "550e8400-e29b-41d4-a716-446655440000",
    "550E8400-E29B-41D4-A716-446655440000",
    "550e8400-E29B-41d4-A716-446655440000",
    "550e8400e29b41d4a716446655440000",
    "{550e8400-e29b-41d4-a716-446655440000}",
    "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
    "00000000-0000-0000-0000-000000000000",
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
]

# Forms CPython accepts that the native parser deliberately refuses. convert()
# must still return the right answer by falling back to uuid.UUID.
UUID_FALLBACK = [
    "1234_678123456781234567812345678",  # int(hex,16) allows separators
    "+1234567812345678123456781234567",  # int() allows a sign
    " 50e8400e29b41d4a716446655440000",  # int() strips whitespace
]


@pytest.mark.parametrize("raw", UUID_ACCEPTED + UUID_FALLBACK)
def test_uuid_parity(raw):
    want = uuid.UUID(raw)
    got = de.convert(TC.UUID, raw)
    assert got == want
    assert type(got) is uuid.UUID
    assert got.int == want.int
    assert got.is_safe == want.is_safe
    assert str(got) == str(want)
    assert hash(got) == hash(want)


@pytest.mark.parametrize("raw", UUID_ACCEPTED)
def test_uuid_fast_path_is_actually_taken(raw):
    """Guard against a green suite that proves nothing: if the parser silently
    rejected everything, every parity test above would still pass via the
    uuid.UUID fallback."""
    assert de.uuid_from_string(raw) is not None


@pytest.mark.parametrize("raw", UUID_FALLBACK)
def test_uuid_unusual_forms_defer_to_python(raw):
    """These must NOT be parsed natively -- CPython's semantics differ, so
    handling them here would be a silent divergence."""
    assert de.uuid_from_string(raw) is None


@pytest.mark.parametrize(
    "raw",
    [
        "550e8400-e29b-41d4-a716-44665544000g",  # bad hex
        "550e8400-e29b-41d4-a716-4466554400",  # too short
        "not-a-uuid",
        "",
    ],
)
def test_uuid_invalid_raises_like_python(raw):
    with pytest.raises(ValueError):
        uuid.UUID(raw)
    with pytest.raises(ValueError):
        de.convert(TC.UUID, raw)


def test_uuid_all_versions_round_trip():
    for factory in (uuid.uuid1, uuid.uuid4):
        for _ in range(50):
            u = factory()
            got = de.convert(TC.UUID, str(u))
            assert got == u
            assert got.version == u.version
            assert got.variant == u.variant


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

JSON_INPUTS = [
    '{"k": "v"}',
    "{}",
    "[]",
    "[1, 2, 3]",
    '{"nested": {"deep": [1, {"x": null}]}}',
    '{"unicode": "caf\\u00e9"}',
    '{"big": 123456789012345678901234567890}',
    '{"dup": 1, "dup": 2}',  # last wins, same as json.loads
    '{"float": 1.5, "bool": true, "null": null}',
    '"bare string"',
    "123",
]


@pytest.mark.parametrize("raw", JSON_INPUTS)
def test_json_parity(raw):
    want = json.loads(raw)
    got = de.convert(TC.JSON, raw)
    assert got == want
    assert type(got) is type(want)


def test_json_invalid_raises():
    with pytest.raises(ValueError):
        de.convert(TC.JSON, "{not json}")


# ---------------------------------------------------------------------------
# Bool / Str / Bytes / Passthrough
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,want",
    [(1, True), (0, False), ("x", True), ("", False), ([], False), ([0], True), (None, False)],
)
def test_bool_parity(raw, want):
    got = de.convert(TC.BOOL, raw)
    assert got is want


def test_str_passthrough_preserves_identity():
    s = "hello"
    assert de.convert(TC.STR, s) is s


def test_str_converts_non_str():
    assert de.convert(TC.STR, 42) == "42"


@pytest.mark.parametrize("raw", [b"abc", "abc", b"", ""])
def test_bytes_parity(raw):
    got = de.convert(TC.BYTES, raw)
    assert got == (raw if isinstance(raw, bytes) else raw.encode())
    assert type(got) is bytes


def test_passthrough_returns_same_object():
    o = object()
    assert de.convert(TC.PASSTHROUGH, o) is o


def test_passthrough_handles_none():
    assert de.convert(TC.PASSTHROUGH, None) is None


# ---------------------------------------------------------------------------
# Refcount hygiene -- 07 §7 asserts on growth, not on absolute counts
# ---------------------------------------------------------------------------


def test_no_refcount_growth_over_repeated_conversion():
    import gc
    import sys

    s = "550e8400-e29b-41d4-a716-446655440000"
    de.convert(TC.UUID, s)  # warm any one-time caches
    gc.collect()
    before = sys.getrefcount(s)
    for _ in range(10_000):
        de.convert(TC.UUID, s)
    gc.collect()
    assert sys.getrefcount(s) == before


def test_no_object_growth_over_repeated_conversion():
    import gc

    gc.collect()
    before = len(gc.get_objects())
    for _ in range(10_000):
        de.convert(TC.DECIMAL, "19.99")
        de.convert(TC.UUID, "550e8400-e29b-41d4-a716-446655440000")
    gc.collect()
    assert len(gc.get_objects()) - before < 100
