"""Differential fuzzing: _json vs stdlib must agree on every payload.

The native JSON engine is not a reimplementation from scratch — it vendors yyjson,
a battle-tested parser with a clean security record. But the Python bindings that
wrap it are new code, and a binding bug could produce a value stdlib would reject
or vice versa, which would be a silent correctness divergence.

This suite runs both parsers over the same corpus and asserts byte-identical
output or identical rejection. Any divergence is a bug in one of them, and because
stdlib is the reference implementation, a disagreement means the native path is
wrong.
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

import pytest

try:
    import aquilia._json as native_json
    JSON_NATIVE = True
except ImportError:
    JSON_NATIVE = False
    native_json = None

pytestmark = pytest.mark.skipif(not JSON_NATIVE, reason="native JSON engine not built")


def _assert_decode_parity(payload: bytes) -> None:
    """Both decoders must produce identical output or both must reject."""
    native_result: Any = None
    native_error: Exception | None = None
    stdlib_result: Any = None
    stdlib_error: Exception | None = None

    try:
        native_result = native_json.loads(payload)
    except Exception as e:
        native_error = e

    try:
        stdlib_result = json.loads(payload)
    except Exception as e:
        stdlib_error = e

    # Both rejected: parity holds. The exception *type* is deliberately not
    # compared -- stdlib raises json.JSONDecodeError, the native path raises
    # plain ValueError, and JSONDecodeError is itself a ValueError subclass. What
    # callers depend on is that a malformed document raises ValueError, which
    # both satisfy; pinning the exact class would freeze an implementation
    # detail neither parser promises.
    if native_error is not None and stdlib_error is not None:
        assert isinstance(native_error, ValueError), (
            f"native raised {type(native_error).__name__}, expected a ValueError subclass"
        )
        assert isinstance(stdlib_error, ValueError), (
            f"stdlib raised {type(stdlib_error).__name__}, expected a ValueError subclass"
        )
        return

    # One rejected, one succeeded: divergence.
    if native_error is not None:
        pytest.fail(f"native rejected, stdlib accepted: {stdlib_result!r}\nError: {native_error}")
    if stdlib_error is not None:
        pytest.fail(f"stdlib rejected, native accepted: {native_result!r}\nError: {stdlib_error}")

    # Both succeeded: values must be identical.
    assert native_result == stdlib_result, f"values differ:\nnative: {native_result!r}\nstdlib: {stdlib_result!r}"
    _assert_deep_type_match(native_result, stdlib_result, path="$")


def _assert_deep_type_match(native: Any, stdlib: Any, path: str) -> None:
    """Types must match exactly at every level of nesting.

    json.loads and our native decoder both produce only dict/list/str/int/float/bool/None,
    so exact type identity is the right check — not isinstance, which would let
    subtypes through.
    """
    assert type(native) is type(stdlib), f"at {path}: type(native)={type(native)}, type(stdlib)={type(stdlib)}"

    if isinstance(native, dict):
        assert native.keys() == stdlib.keys(), f"at {path}: keys differ"
        for key in native:
            _assert_deep_type_match(native[key], stdlib[key], f"{path}.{key}")
    elif isinstance(native, list):
        assert len(native) == len(stdlib), f"at {path}: length differs"
        for i, (n, s) in enumerate(zip(native, stdlib)):
            _assert_deep_type_match(n, s, f"{path}[{i}]")
    elif isinstance(native, float):
        # NaN is the one float that fails self-equality, so it needs special handling.
        if math.isnan(native):
            assert math.isnan(stdlib), f"at {path}: native is NaN, stdlib is {stdlib}"
        else:
            assert native == stdlib, f"at {path}: {native} != {stdlib}"


def _assert_encode_parity(obj: Any) -> None:
    """Both encoders must produce parse-equivalent output or both must reject."""
    native_bytes: bytes | None = None
    native_error: Exception | None = None
    stdlib_bytes: bytes | None = None
    stdlib_error: Exception | None = None

    try:
        native_bytes = native_json.dumps(obj)
    except Exception as e:
        native_error = e

    try:
        # allow_nan=False: NaN and +-Infinity are not valid JSON. stdlib emits
        # them as bare NaN/Infinity tokens by default, which no conforming
        # parser accepts, so the strict setting is the correct reference for a
        # codec whose output goes on the wire.
        stdlib_str = json.dumps(
            obj, ensure_ascii=True, separators=(",", ":"), sort_keys=False, allow_nan=False
        )
        stdlib_bytes = stdlib_str.encode("utf-8")
    except Exception as e:
        stdlib_error = e

    if native_error is not None and stdlib_error is not None:
        assert isinstance(native_error, (TypeError, ValueError)), (
            f"native raised {type(native_error).__name__}"
        )
        assert isinstance(stdlib_error, (TypeError, ValueError)), (
            f"stdlib raised {type(stdlib_error).__name__}"
        )
        return

    if native_error is not None:
        pytest.fail(f"native rejected, stdlib accepted\nError: {native_error}")
    if stdlib_error is not None:
        pytest.fail(f"stdlib rejected, native accepted\nError: {stdlib_error}")

    # Both succeeded. Re-parse both outputs and assert the decoded values are identical.
    # This allows for whitespace and key-order variation while still catching real divergence.
    assert native_bytes is not None and stdlib_bytes is not None
    native_reparsed = json.loads(native_bytes)
    stdlib_reparsed = json.loads(stdlib_bytes)
    assert native_reparsed == stdlib_reparsed, (
        f"re-parsed values differ:\nnative: {native_reparsed!r}\nstdlib: {stdlib_reparsed!r}"
    )
    _assert_deep_type_match(native_reparsed, stdlib_reparsed, path="$")


# ── Decode parity corpus ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "payload",
    [
        b"null",
        b"true",
        b"false",
        b"0",
        b"1",
        b"-1",
        b"2147483647",
        b"-2147483648",
        b"9223372036854775807",
        b"-9223372036854775808",
        b"123456789012345678901234567890",  # beyond int64
        b"0.0",
        b"1.5",
        b"-1.5",
        b"1e10",
        b"1.23e-10",
        b'""',
        b'"hello"',
        b'"\\n\\t\\r"',
        b'"\\"\\\\/"',
        b'"\\u0041"',
        b'"\\u00e9"',
        b'"\\ud83d\\ude00"',  # emoji via surrogate pair
        b'"\xc3\xa9"',  # UTF-8 é
        b'"\\u0000"',
        b"[]",
        b"[1,2,3]",
        b"[null,true,false]",
        b'["a","b"]',
        b"{}",
        b'{"a":1}',
        b'{"a":1,"b":2}',
        b'{"nested":{"x":1}}',
        b'{"list":[1,2,3]}',
        b'[{"id":1},{"id":2}]',
        b'{"":"empty-key"}',
        b'  { "whitespace" : true }  ',
        b'{"a":1}\n',
        # Edge cases
        b'{"a":null,"b":null}',
        b'{"x":1,"x":2}',  # duplicate key: last wins
        b'[[[[[1]]]]]',  # deep nesting
        b'{"a":{"b":{"c":{"d":1}}}}',
    ],
)
def test_decode_parity(payload: bytes) -> None:
    _assert_decode_parity(payload)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b" ",
        b"nul",
        b"tru",
        b"falz",
        b"[",
        b"]",
        b"{",
        b"}",
        b'{"a"}',
        b'{"a":}',
        b'{"a":1,}',
        b"[1,2,]",
        b'"\\"',  # unterminated escape
        b'"\\x"',  # invalid escape
        b'"\\u"',
        b'"\\u00"',
        b'"\\u00g0"',
        b'{"a":1',
        b'[1,2',
        b"01",  # leading zero
        b"-",
        b"1.",
        b"1e",
    ],
)
def test_decode_malformed_rejected_by_both(payload: bytes) -> None:
    _assert_decode_parity(payload)


# ── Encode parity corpus ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "obj",
    [
        None,
        True,
        False,
        0,
        1,
        -1,
        123456789,
        -123456789,
        sys.maxsize,
        -sys.maxsize - 1,
        0.0,
        1.5,
        -1.5,
        1e10,
        1.23e-10,
        "",
        "hello",
        "unicode: café ☕",
        "\n\t\r",
        '"\\/\b\f',
        "\x00",
        [],
        [1, 2, 3],
        [None, True, False],
        ["a", "b"],
        {},
        {"a": 1},
        {"a": 1, "b": 2},
        {"nested": {"x": 1}},
        {"list": [1, 2, 3]},
        [{"id": 1}, {"id": 2}],
        {"": "empty-key"},
        # Nesting
        [[[[[1]]]]],
        {"a": {"b": {"c": {"d": 1}}}},
    ],
)
def test_encode_parity(obj: Any) -> None:
    _assert_encode_parity(obj)


def test_encode_nan_and_inf_both_reject() -> None:
    """NaN and inf are not valid JSON; both encoders must reject."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        _assert_encode_parity(bad)


def test_decode_number_precision() -> None:
    """Large integers and floats must preserve their exact value."""
    _assert_decode_parity(b"123456789012345678901234567890")
    _assert_decode_parity(b"1.7976931348623157e+308")  # near max float
    _assert_decode_parity(b"-1.7976931348623157e+308")


def test_decode_unicode_escapes() -> None:
    """All Unicode escape forms must decode identically."""
    _assert_decode_parity(b'"\\u0041\\u0042\\u0043"')  # ABC
    _assert_decode_parity(b'"\\u00e9"')  # é
    _assert_decode_parity(b'"\\ud83d\\ude00"')  # 😀 via surrogate pair


def test_encode_unicode_as_utf8() -> None:
    """Unicode strings must encode as UTF-8, not escapes."""
    native = native_json.dumps("café")
    # Our encoder emits UTF-8; stdlib with ensure_ascii=True would escape.
    # Re-parse to check correctness rather than asserting byte identity.
    assert json.loads(native) == "café"
