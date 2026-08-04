"""Tests for the native JSON engine and the codec entry point.

Structure
---------
Every test here runs against whichever backend :mod:`aquilia.json` selected, so
the file is meaningful on a pure-Python install too. Tests that require the
native extension are marked with ``requires_native``.

The differential tests are the important ones. A JSON codec has an external
specification and an obvious reference implementation, so "does it agree with
the stdlib on hundreds of thousands of generated values" is a far stronger
statement than any hand-written case list -- and it is what caught the two real
bugs in this engine: a wrong SWAR identity that corrupted non-ASCII strings, and
silent precision loss on integers above 2**64.
"""

from __future__ import annotations

import json as stdlib
import math
import random
import struct

import pytest

from aquilia.json import JSONDecodeError, JSONEncodeError, backend, dumps, loads, native

requires_native = pytest.mark.skipif(not native, reason="native aquilia._json not built")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def _random_value(rng: random.Random, depth: int = 0):
    """Build an arbitrary JSON-representable Python value.

    Excludes lone surrogates: they are not encodable UTF-8, and both this codec
    and the stdlib raise ``UnicodeEncodeError`` on them (verified separately in
    :func:`test_lone_surrogate_matches_stdlib`).
    """
    if depth > 4:
        return rng.choice([None, True, False, 0, -1, 1.5, "s", ""])
    kind = rng.randint(0, 9)
    if kind == 0:
        return {f"k{i}": _random_value(rng, depth + 1) for i in range(rng.randint(0, 5))}
    if kind == 1:
        return [_random_value(rng, depth + 1) for _ in range(rng.randint(0, 5))]
    if kind == 2:
        return rng.randint(-(2**63), 2**63 - 1)
    if kind == 3:
        return rng.random() * 10 ** rng.randint(-8, 8)
    if kind == 4:
        return "".join(
            chr(rng.choice([rng.randint(1, 0xD7FF), rng.randint(0xE000, 0xFFFF), rng.randint(0x10000, 0x10FFFF)]))
            for _ in range(rng.randint(0, 12))
        )
    if kind == 5:
        return rng.choice([None, True, False])
    if kind == 6:
        return "".join(chr(rng.randint(0, 0x7F)) for _ in range(rng.randint(0, 20)))
    if kind == 7:
        return {}
    if kind == 8:
        # Beyond int64/uint64: the case where a naive decoder silently degrades
        # to a double and loses digits.
        return rng.randint(-(10**40), 10**40)
    return []


# ---------------------------------------------------------------------------
# Differential vs the standard library
# ---------------------------------------------------------------------------


class TestDifferential:
    def test_encode_agrees_with_stdlib(self):
        rng = random.Random(20260805)
        checked = 0
        for _ in range(20000):
            value = _random_value(rng)
            try:
                expected = stdlib.dumps(value, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError, UnicodeEncodeError):
                continue
            checked += 1
            produced = dumps(value)
            # Semantic rather than byte comparison: key order is preserved by
            # both, but float formatting may legitimately differ in form while
            # denoting the same value.
            assert stdlib.loads(produced) == stdlib.loads(expected), value
        assert checked > 15000, f"generator produced too few valid cases ({checked})"

    def test_decode_agrees_with_stdlib(self):
        rng = random.Random(52608202)
        checked = 0
        for _ in range(20000):
            value = _random_value(rng)
            try:
                text = stdlib.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError, UnicodeEncodeError):
                continue
            checked += 1
            assert loads(text.encode()) == stdlib.loads(text), text[:200]
        assert checked > 15000

    def test_roundtrip_is_identity(self):
        rng = random.Random(11)
        for _ in range(20000):
            value = _random_value(rng)
            try:
                dumped = dumps(value)
            except (JSONEncodeError, UnicodeEncodeError):
                continue
            assert loads(dumped) == value, value

    def test_ascii_output_is_byte_identical_to_stdlib(self):
        """Where no float or non-ASCII formatting is involved, agreement should
        be exact, not merely semantic."""
        rng = random.Random(777)
        checked = 0
        for _ in range(10000):
            value = _random_value(rng)
            try:
                expected = stdlib.dumps(value, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError, UnicodeEncodeError):
                continue
            if not expected.isascii() or any(c in expected for c in ".e"):
                continue
            checked += 1
            assert dumps(value).decode() == expected
        assert checked > 500


# ---------------------------------------------------------------------------
# Floats -- the part most likely to be subtly wrong
# ---------------------------------------------------------------------------


class TestFloats:
    def test_random_bit_patterns_round_trip_exactly(self):
        """Every finite double must survive encode->decode unchanged.

        Generated from raw bit patterns rather than arithmetic so the corpus
        includes subnormals, values near the exponent limits, and every
        significand shape -- the inputs where a shortest-representation
        algorithm goes wrong.
        """
        rng = random.Random(4)
        checked = 0
        for _ in range(50000):
            (value,) = struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))
            if not math.isfinite(value):
                continue
            checked += 1
            decoded = loads(dumps(value))
            assert decoded == value
            # repr equality catches a value that compares equal but was written
            # with more digits than necessary.
            assert repr(decoded) == repr(value)
        assert checked > 40000

    @pytest.mark.parametrize(
        "value",
        [
            0.0,
            -0.0,
            1.0,
            -1.0,
            0.1,
            0.5,
            1 / 3,
            2**53,
            -(2**53),
            2.0**53 + 2.0,
            1e16,
            1e17,
            1e22,
            1e23,
            1e-300,
            1e300,
            5e-324,  # smallest subnormal
            1.7976931348623157e308,  # DBL_MAX
            math.pi,
            math.e,
        ],
    )
    def test_notable_values(self, value):
        decoded = loads(dumps(value))
        assert decoded == value
        assert repr(decoded) == repr(value)

    def test_negative_zero_keeps_its_sign(self):
        """The integral-value fast path must not swallow the sign: (int64)-0.0
        is 0, which would print "0.0"."""
        assert math.copysign(1, loads(dumps(-0.0))) == -1
        assert dumps(-0.0) == b"-0.0"

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_non_finite_is_rejected(self, value):
        """JSON has no representation for these. Emitting a bare `NaN` token
        produces output only some parsers accept, so it is an error instead."""
        with pytest.raises(JSONEncodeError):
            dumps(value)


# ---------------------------------------------------------------------------
# Integers
# ---------------------------------------------------------------------------


class TestIntegers:
    @pytest.mark.parametrize(
        "value",
        [0, 1, -1, 2**31, 2**32, 2**63 - 1, -(2**63), 2**63, 2**64, 2**64 + 1, 2**128, -(2**128)],
    )
    def test_boundaries_are_exact(self, value):
        """Above 2**63 the int64 path overflows and above 2**64 the uint64 path
        does too; both must reach the arbitrary-precision fallback rather than
        degrading to a double."""
        assert loads(dumps(value)) == value

    def test_decoded_bignum_keeps_every_digit(self):
        """The defect this pins: a 30-digit id decoded as
        1.2345678901234568e+29 is silent data corruption."""
        raw = b'{"id":123456789012345678901234567890}'
        assert loads(raw)["id"] == 123456789012345678901234567890
        assert isinstance(loads(raw)["id"], int)

    def test_bool_is_not_encoded_as_int(self):
        """bool subclasses int in CPython, so an int-first dispatch emits 1/0."""
        assert dumps(True) == b"true"
        assert dumps(False) == b"false"
        assert dumps([True, 1, False, 0]) == b"[true,1,false,0]"


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------


class TestStrings:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", b'""'),
            ("plain", b'"plain"'),
            ('q"uote', b'"q\\"uote"'),
            ("back\\slash", b'"back\\\\slash"'),
            ("new\nline", b'"new\\nline"'),
            ("tab\there", b'"tab\\there"'),
            ("ret\rurn", b'"ret\\rurn"'),
            ("\x08\x0c", b'"\\b\\f"'),
            ("\x00", b'"\\u0000"'),
            ("\x1f", b'"\\u001f"'),
        ],
    )
    def test_escapes(self, value, expected):
        assert dumps(value) == expected

    def test_del_is_not_escaped(self):
        """0x7F is legal unescaped per RFC 8259."""
        assert dumps("\x7f") == b'"\x7f"'

    def test_utf8_passes_through_raw(self):
        for value in ("é", "→", "😀", "日本語", "Ω≈ç√"):
            assert dumps(value).decode() == f'"{value}"'
            assert loads(dumps(value)) == value

    def test_every_bmp_codepoint_round_trips(self):
        """Exhaustive over the BMP minus the surrogate range. This is the test
        that would have caught the bad SWAR identity, which mis-flagged every
        byte >= 0x80 as a control character."""
        chunk = []
        for cp in range(1, 0x10000):
            if 0xD800 <= cp <= 0xDFFF:
                continue
            chunk.append(chr(cp))
            if len(chunk) == 1000:
                value = "".join(chunk)
                assert loads(dumps(value)) == value
                chunk = []
        if chunk:
            value = "".join(chunk)
            assert loads(dumps(value)) == value

    def test_lone_surrogate_matches_stdlib(self):
        """Both codecs refuse: a lone surrogate is not encodable UTF-8."""
        with pytest.raises((JSONEncodeError, UnicodeEncodeError)):
            dumps({"k": "\ud800"})
        with pytest.raises(UnicodeEncodeError):
            stdlib.dumps({"k": "\ud800"}, ensure_ascii=False).encode()

    def test_long_string(self):
        value = "x" * 1_000_000
        assert loads(dumps(value)) == value

    def test_escape_at_every_offset(self):
        """Exercises both the word-at-a-time loop and the scalar tail."""
        for pos in range(40):
            value = "a" * 40
            value = value[:pos] + '"' + value[pos + 1 :]
            assert loads(dumps(value)) == value


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------


class TestKeys:
    def test_string_keys(self):
        assert dumps({"a": 1}) == b'{"a":1}'

    def test_non_string_keys_are_stringified_like_stdlib(self):
        for key in (1, 1.5, True, False, None):
            produced = loads(dumps({key: "v"}))
            expected = stdlib.loads(stdlib.dumps({key: "v"}))
            assert produced == expected

    def test_unsupported_key_type_raises(self):
        with pytest.raises(JSONEncodeError):
            dumps({(1, 2): "v"})

    def test_nested_object_keys_are_not_lost(self):
        """Regression: while iterating a nested container the parent's key was
        being overwritten, so `{"a": {"b": 1}, "c": 2}` lost "a"."""
        value = {"a": {"b": 1}, "c": 2, "d": {"e": {"f": [1, 2]}}, "g": 3}
        assert loads(dumps(value)) == value


# ---------------------------------------------------------------------------
# Malformed and adversarial input
# ---------------------------------------------------------------------------


class TestMalformedInput:
    @pytest.mark.parametrize(
        "raw",
        [
            b"",
            b"{",
            b"[",
            b'{"a":',
            b"[1,2",
            b'{"a":1,}',
            b"[1,]",
            b"{'a':1}",
            b'{"a":1 /* c */}',
            b'{"a":01}',
            b'{"a":+1}',
            b'{"a":1.}',
            b'{"a":.1}',
            b'{"a":--1}',
            b"tru",
            b"nul",
            b'{"a" 1}',
            b'{"a":1}{"b":2}',
            b"\xff\xfe",
            b'{"a":"unterminated',
        ],
    )
    def test_rejected(self, raw):
        with pytest.raises(JSONDecodeError):
            loads(raw)

    def test_truncation_at_every_offset(self):
        """Every prefix of a valid document is either valid or a clean error --
        never a crash."""
        full = stdlib.dumps({"a": [1, 2, {"b": "text", "c": [True, None, 1.5]}], "d": {"e": {}}}).encode()
        for cut in range(1, len(full)):
            try:
                loads(full[:cut])
            except JSONDecodeError:
                pass

    def test_duplicate_keys_take_the_last_value(self):
        """Matches json.loads and every other mainstream parser."""
        assert loads(b'{"a":1,"a":2}') == {"a": 2}
        assert loads(b'{"a":1,"a":2}') == stdlib.loads('{"a":1,"a":2}')

    def test_deep_nesting_is_an_error_not_a_crash(self):
        """The explicit work stack turns what would be a C-stack overflow into a
        catchable error. A recursive implementation segfaults or raises
        RecursionError here; both are worse than a 400."""
        payload = b"[" * 100_000 + b"]" * 100_000
        with pytest.raises(JSONDecodeError):
            loads(payload)

    def test_deep_nesting_on_encode_is_an_error_not_a_crash(self):
        value: list = []
        current = value
        for _ in range(100_000):
            nxt: list = []
            current.append(nxt)
            current = nxt
        with pytest.raises(JSONEncodeError):
            dumps(value)

    def test_recursive_structure_is_rejected(self):
        value: list = []
        value.append(value)
        with pytest.raises((JSONEncodeError, RecursionError, ValueError)):
            dumps(value)

    def test_nesting_within_the_limit_still_works(self):
        depth = 100
        payload = b"[" * depth + b"1" + b"]" * depth
        result = loads(payload)
        for _ in range(depth):
            assert isinstance(result, list)
            result = result[0]
        assert result == 1

    def test_wrong_input_type(self):
        for bad in (None, 1, 1.5, object(), [], {}):
            with pytest.raises((JSONDecodeError, TypeError)):
                loads(bad)


# ---------------------------------------------------------------------------
# Input container types
# ---------------------------------------------------------------------------


class TestInputTypes:
    def test_bytes(self):
        assert loads(b'{"a":1}') == {"a": 1}

    def test_str(self):
        assert loads('{"a":1}') == {"a": 1}

    def test_bytearray(self):
        assert loads(bytearray(b'{"a":1}')) == {"a": 1}

    def test_memoryview(self):
        assert loads(memoryview(b'{"a":1}')) == {"a": 1}

    def test_decoded_objects_do_not_alias_the_input_buffer(self):
        """A mutable input must not be able to change an already-decoded string
        after the fact."""
        buf = bytearray(b'{"key":"value"}')
        decoded = loads(buf)
        buf[0:1] = b"X"
        assert decoded == {"key": "value"}


# ---------------------------------------------------------------------------
# default= hook
# ---------------------------------------------------------------------------


class TestDefaultHook:
    def test_sets_become_lists(self):
        assert loads(dumps({"s": {1, 2, 3}}))["s"] == [1, 2, 3]

    def test_tuples_become_arrays(self):
        assert loads(dumps((1, 2, 3))) == [1, 2, 3]

    def test_datetime_uses_isoformat(self):
        from datetime import date, datetime

        assert loads(dumps(datetime(2026, 8, 5, 12, 30))) == "2026-08-05T12:30:00"
        assert loads(dumps(date(2026, 8, 5))) == "2026-08-05"

    def test_unserialisable_object_raises(self):
        class Opaque:
            __slots__ = ()

        # The module-level default_serializer stringifies unknown objects rather
        # than failing, matching the previous framework behaviour.
        assert isinstance(loads(dumps(Opaque())), str)

    def test_custom_default_is_called(self):
        calls = []

        def hook(obj):
            calls.append(obj)
            return "replaced"

        class Opaque:
            __slots__ = ()

        value = Opaque()
        assert loads(dumps(value, default=hook)) == "replaced"
        assert calls == [value]

    def test_raising_default_propagates(self):
        def hook(obj):
            raise RuntimeError("boom")

        class Opaque:
            __slots__ = ()

        with pytest.raises(RuntimeError, match="boom"):
            dumps(Opaque(), default=hook)

    def test_default_returning_unserialisable_does_not_recurse_forever(self):
        """A hook that keeps returning unsupported objects must terminate: the
        replacement is encoded with the hook disabled."""

        class Opaque:
            __slots__ = ()

        def hook(obj):
            return Opaque()

        with pytest.raises((JSONEncodeError, TypeError)):
            dumps(Opaque(), default=hook)


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


class TestStructures:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ({}, b"{}"),
            ([], b"[]"),
            ((), b"[]"),
            (None, b"null"),
            ([[]], b"[[]]"),
            ([{}], b"[{}]"),
            ({"a": {}}, b'{"a":{}}'),
            ({"a": []}, b'{"a":[]}'),
            ([1, [2, [3, [4]]]], b"[1,[2,[3,[4]]]]"),
        ],
    )
    def test_shapes(self, value, expected):
        assert dumps(value) == expected

    def test_key_order_is_preserved(self):
        value = {"z": 1, "a": 2, "m": 3, "b": 4}
        assert dumps(value) == b'{"z":1,"a":2,"m":3,"b":4}'
        assert list(loads(dumps(value))) == ["z", "a", "m", "b"]

    def test_large_flat_list(self):
        value = list(range(100_000))
        assert loads(dumps(value)) == value

    def test_large_flat_dict(self):
        value = {f"key{i}": i for i in range(100_000)}
        assert loads(dumps(value)) == value

    def test_wide_row_payload(self):
        """The shape an ORM response actually has."""
        value = [{"id": i, "name": f"row-{i}", "score": i * 1.5, "ok": i % 2 == 0} for i in range(5000)]
        assert loads(dumps(value)) == value


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


class TestEntryPoint:
    def test_dumps_returns_bytes(self):
        assert isinstance(dumps({"a": 1}), bytes)

    def test_backend_name(self):
        assert backend() in {"aquilia._json", "stdlib"}

    def test_backend_matches_native_flag(self):
        assert (backend() == "aquilia._json") is native

    def test_decode_error_is_a_value_error(self):
        assert issubclass(JSONDecodeError, ValueError)

    def test_encode_error_is_a_type_error(self):
        assert issubclass(JSONEncodeError, TypeError)

    @requires_native
    def test_native_module_exposes_the_expected_surface(self):
        from aquilia import _json

        assert callable(_json.dumps)
        assert callable(_json.loads)
        assert callable(_json.noop)


@requires_native
class TestBufferReuse:
    def test_repeated_encodes_are_stable(self):
        """The thread-local buffer pool is reused across calls; a stale length or
        an uncleared buffer would show up as output from a previous call."""
        payloads = [{"a": 1}, {"b": "x" * 1000}, list(range(100)), {}, {"c": [1, 2, 3]}]
        expected = [dumps(p) for p in payloads]
        for _ in range(1000):
            for payload, want in zip(payloads, expected):
                assert dumps(payload) == want

    def test_concurrent_encoding_is_safe(self):
        """The pool is thread-local, so concurrent encoders must not interfere."""
        import threading

        errors: list[Exception] = []

        def worker(seed: int) -> None:
            try:
                rng = random.Random(seed)
                for _ in range(500):
                    value = _random_value(rng)
                    try:
                        assert loads(dumps(value)) == value
                    except (JSONEncodeError, UnicodeEncodeError):
                        pass
            except Exception as exc:  # pragma: no cover - only on failure
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
