"""Adversarial corpus: inputs designed to expose boundary-condition bugs.

The differential suite proves the codec doesn't diverge from stdlib on ordinary
inputs. This suite ensures it degrades gracefully on inputs that are *designed*
to break parsers — deeply nested structures, huge integers, malformed UTF-8,
surrogate pairs, control characters, and payloads that exercise memory
allocation and recursion limits.

Every test asserts one of three outcomes:
1. Parses successfully and produces the expected structure.
2. Rejects with a ValueError (malformed input).
3. Times out gracefully under a deadline (DoS mitigation).
"""

from __future__ import annotations

import json
import sys

import pytest

try:
    import aquilia._json as native_json

    JSON_NATIVE = hasattr(native_json, "loads")
    if not JSON_NATIVE:
        native_json = None
except (ImportError, AttributeError):
    JSON_NATIVE = False
    native_json = None

pytestmark = pytest.mark.skipif(not JSON_NATIVE, reason="native JSON engine not built")


# ── Deep nesting ─────────────────────────────────────────────────────────────


def test_deep_array_nesting() -> None:
    """100 levels of array nesting should parse without stack overflow."""
    depth = 100
    payload = b"[" * depth + b"1" + b"]" * depth
    result = native_json.loads(payload)
    # Unwrap to the bottom.
    for _ in range(depth):
        assert isinstance(result, list)
        assert len(result) == 1
        result = result[0]
    assert result == 1


def test_deep_object_nesting() -> None:
    """100 levels of object nesting should parse without stack overflow."""
    depth = 100
    payload = b'{"a":' * depth + b"1" + b"}" * depth
    result = native_json.loads(payload)
    for _ in range(depth):
        assert isinstance(result, dict)
        assert "a" in result
        result = result["a"]
    assert result == 1


def test_excessive_nesting_rejects() -> None:
    """Nesting beyond a safe threshold must reject, not crash or hang."""
    depth = 10000
    payload = b"[" * depth + b"1" + b"]" * depth
    with pytest.raises(ValueError, match="(?i)depth|nesting|recursion"):
        native_json.loads(payload)


# ── Large numbers ────────────────────────────────────────────────────────────


def test_huge_integer() -> None:
    """Python ints are unbounded; yyjson must not truncate."""
    huge = 10**100
    payload = str(huge).encode("utf-8")
    result = native_json.loads(payload)
    assert result == huge
    assert type(result) is int


def test_huge_negative_integer() -> None:
    huge = -(10**100)
    payload = str(huge).encode("utf-8")
    result = native_json.loads(payload)
    assert result == huge


def test_maxfloat() -> None:
    """Near max float must preserve precision."""
    val = sys.float_info.max
    payload = json.dumps(val).encode("utf-8")
    result = native_json.loads(payload)
    assert result == val


def test_minfloat() -> None:
    val = sys.float_info.min
    payload = json.dumps(val).encode("utf-8")
    result = native_json.loads(payload)
    assert result == val


# ── Unicode edge cases ───────────────────────────────────────────────────────


def test_all_ascii_printable() -> None:
    """ASCII 0x20-0x7E (excluding backslash and quote)."""
    chars = "".join(chr(i) for i in range(0x20, 0x7F) if chr(i) not in ('"', "\\"))
    payload = json.dumps(chars).encode("utf-8")
    result = native_json.loads(payload)
    assert result == chars


def test_unicode_bmp() -> None:
    """Characters from the Basic Multilingual Plane."""
    s = "Hello 世界 مرحبا שלום"
    payload = json.dumps(s).encode("utf-8")
    result = native_json.loads(payload)
    assert result == s


def test_unicode_astral_plane() -> None:
    """Characters beyond U+FFFF (emoji, etc.)."""
    s = "😀😁🚀🔥"
    payload = json.dumps(s).encode("utf-8")
    result = native_json.loads(payload)
    assert result == s


def test_escaped_unicode() -> None:
    """All forms of Unicode escapes must decode correctly."""
    payload = b'"\\u0041\\u00e9\\ud83d\\ude00"'  # A, é, 😀
    result = native_json.loads(payload)
    assert result == "Aé😀"


def test_null_byte_in_string() -> None:
    """U+0000 is valid in JSON strings."""
    payload = b'"before\\u0000after"'
    result = native_json.loads(payload)
    assert result == "before\x00after"


def test_control_characters_escaped() -> None:
    """Control characters (0x00-0x1F) must be escaped in valid JSON."""
    payload = b'"\\n\\t\\r\\b\\f"'
    result = native_json.loads(payload)
    assert result == "\n\t\r\b\f"


def test_lone_surrogate_rejects() -> None:
    """A lone high or low surrogate is invalid."""
    with pytest.raises(ValueError):
        native_json.loads(b'"\\ud800"')  # lone high surrogate
    with pytest.raises(ValueError):
        native_json.loads(b'"\\udc00"')  # lone low surrogate


def test_invalid_utf8_rejects() -> None:
    """Malformed UTF-8 must reject, not silently truncate or mojibake."""
    with pytest.raises(ValueError):
        native_json.loads(b'"\xff\xfe"')  # invalid UTF-8 bytes


# ── Large payloads ───────────────────────────────────────────────────────────


def test_large_array() -> None:
    """10,000-element array should parse without choking."""
    arr = list(range(10000))
    payload = json.dumps(arr).encode("utf-8")
    result = native_json.loads(payload)
    assert result == arr


def test_large_object() -> None:
    """1,000-key object should parse."""
    obj = {f"key_{i}": i for i in range(1000)}
    payload = json.dumps(obj).encode("utf-8")
    result = native_json.loads(payload)
    assert result == obj


def test_huge_string() -> None:
    """1MB string should not overflow the buffer."""
    s = "a" * (1024 * 1024)
    payload = json.dumps(s).encode("utf-8")
    result = native_json.loads(payload)
    assert result == s


# ── Encode edge cases ────────────────────────────────────────────────────────


def test_encode_control_characters() -> None:
    """Control characters must be escaped in output."""
    s = "\x00\x01\x1f"
    encoded = native_json.dumps(s)
    # Re-parse to confirm it's valid JSON.
    result = json.loads(encoded)
    assert result == s


def test_encode_backslash_quote() -> None:
    """Backslash and quote must be escaped."""
    s = 'He said: "It\'s a \\ character."'
    encoded = native_json.dumps(s)
    result = json.loads(encoded)
    assert result == s


def test_encode_unicode_outside_bmp() -> None:
    """Emoji and other astral-plane characters must encode correctly."""
    s = "😀🚀"
    encoded = native_json.dumps(s)
    result = json.loads(encoded)
    assert result == s


def test_encode_huge_dict() -> None:
    """Large dict should encode without overflowing the buffer."""
    obj = {f"field_{i}": i for i in range(5000)}
    encoded = native_json.dumps(obj)
    result = json.loads(encoded)
    assert result == obj


def test_encode_deeply_nested() -> None:
    """Deep nesting should encode without stack overflow."""
    obj: dict | int = 1
    for _ in range(100):
        obj = {"x": obj}
    encoded = native_json.dumps(obj)
    result = json.loads(encoded)
    assert result == obj


# ── Malformed input rejection ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "payload",
    [
        b"\xfe\xff",  # invalid UTF-8 BOM
        b"\x00",  # bare null byte
        b'{"a":1, "a":2',  # unclosed object
        b"[1, 2, 3",  # unclosed array
        b'{"a": }',  # missing value
        b"[1, , 3]",  # missing value
        b'{"a": 1, "b": 2,}',  # trailing comma in object
        b"[1, 2,]",  # trailing comma in array
        b'"unterminated',  # unterminated string
        b"tru",  # truncated keyword
        b"nul",
        b"fals",
        b"NaN",  # not valid JSON
        b"Infinity",
        b"-Infinity",
        b"0x10",  # hex literal
        b"012",  # octal literal
        b"+1",  # leading plus
    ],
)
def test_malformed_input_rejects(payload: bytes) -> None:
    """Every malformed payload must raise ValueError, not crash or hang."""
    with pytest.raises(ValueError):
        native_json.loads(payload)


# ── Memory and DoS mitigation ────────────────────────────────────────────────


def test_repeated_keys_in_object() -> None:
    """Duplicate keys: last value wins, no crash."""
    payload = b'{"a": 1, "a": 2, "a": 3}'
    result = native_json.loads(payload)
    assert result == {"a": 3}


def test_empty_structures() -> None:
    """Empty array and empty object are valid."""
    assert native_json.loads(b"[]") == []
    assert native_json.loads(b"{}") == {}


def test_whitespace_tolerance() -> None:
    """Leading, trailing, and internal whitespace must be ignored."""
    assert native_json.loads(b"  \n\t  [  1  ,  2  ]  \n  ") == [1, 2]
    assert native_json.loads(b'  {  "a"  :  1  }  ') == {"a": 1}
