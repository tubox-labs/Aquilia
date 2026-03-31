"""
Comprehensive regression tests for CROUS request / response integration.

Covers:
- §1: Request — is_crous, accepts_crous, prefers_crous, best_response_format
- §2: Request — crous() payload parsing, model validation, error handling
- §3: Request — data() auto-detection (JSON vs CROUS)
- §4: Response — Response.crous() factory, fallback, compression, dedup
- §5: Response — Response.negotiated() content negotiation
- §6: Response — _detect_media_type CROUS magic detection
- §7: Decorator — requires_crous attribute tagging
- §8: Faults — InvalidCrous, CrousUnavailable
- §9: Round-trip — encode → request.crous() → Response.crous() → decode
- §10: Edge cases & regression guards
"""

import asyncio
import json
import pytest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import crous as _crous_mod

# ============================================================================
# Helpers
# ============================================================================


def _make_scope(
    method: str = "POST",
    path: str = "/",
    headers: Optional[Dict[str, str]] = None,
    content_type: Optional[str] = None,
) -> dict:
    """Build a minimal ASGI scope dict."""
    raw_headers = []
    if content_type:
        raw_headers.append((b"content-type", content_type.encode()))
    for name, value in (headers or {}).items():
        raw_headers.append((name.lower().encode(), value.encode()))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": raw_headers,
        "query_string": b"",
        "root_path": "",
        "scheme": "http",
    }


def _make_receive(body: bytes):
    """Return an async receive callable delivering *body* in one chunk."""
    called = False

    async def receive():
        nonlocal called
        if not called:
            called = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


def _make_request(
    body: bytes = b"",
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
    **extra_headers,
):
    """Build a Request with the given body, content-type, and accept."""
    from aquilia.request import Request

    headers = dict(extra_headers)
    if accept:
        headers["accept"] = accept
    scope = _make_scope(
        method="POST",
        headers=headers,
        content_type=content_type,
    )
    return Request(scope, _make_receive(body))


# ============================================================================
# §1 — Content-type & Accept detection
# ============================================================================


class TestIsCrous:
    """Request.is_crous() detection."""

    def test_application_x_crous(self):
        req = _make_request(content_type="application/x-crous")
        assert req.is_crous() is True

    def test_application_crous(self):
        req = _make_request(content_type="application/crous")
        assert req.is_crous() is True

    def test_application_vnd_crous(self):
        req = _make_request(content_type="application/vnd.crous")
        assert req.is_crous() is True

    def test_json_is_not_crous(self):
        req = _make_request(content_type="application/json")
        assert req.is_crous() is False

    def test_no_content_type_fallback_to_magic(self):
        body = _crous_mod.encode({"hello": "world"})
        req = _make_request(body=body)
        # Force body into cache so magic detection works
        req._body = body
        assert req.is_crous() is True

    def test_no_content_type_non_crous_body(self):
        req = _make_request(body=b'{"json": true}')
        req._body = b'{"json": true}'
        assert req.is_crous() is False


class TestAcceptsCrous:
    """Request.accepts_crous()."""

    def test_explicit_accept(self):
        req = _make_request(accept="application/x-crous")
        assert req.accepts_crous() is True

    def test_wildcard_accept(self):
        req = _make_request(accept="*/*")
        assert req.accepts_crous() is True

    def test_json_only(self):
        req = _make_request(accept="application/json")
        assert req.accepts_crous() is False

    def test_mixed_accept(self):
        req = _make_request(accept="application/json, application/x-crous")
        assert req.accepts_crous() is True

    def test_vnd_crous_accept(self):
        req = _make_request(accept="application/vnd.crous")
        assert req.accepts_crous() is True


class TestPrefersCrous:
    """Request.prefers_crous() quality-factor negotiation."""

    def test_crous_higher_quality(self):
        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.9")
        assert req.prefers_crous() is True

    def test_json_higher_quality(self):
        req = _make_request(accept="application/json;q=1.0, application/x-crous;q=0.5")
        assert req.prefers_crous() is False

    def test_crous_implicit_q1(self):
        req = _make_request(accept="application/x-crous, application/json;q=0.8")
        assert req.prefers_crous() is True

    def test_both_implicit_q1(self):
        # Equal quality — crous not *strictly* greater
        req = _make_request(accept="application/x-crous, application/json")
        assert req.prefers_crous() is False

    def test_wildcard_does_not_prefer(self):
        req = _make_request(accept="*/*")
        assert req.prefers_crous() is False

    def test_no_crous_in_accept(self):
        req = _make_request(accept="application/json")
        assert req.prefers_crous() is False

    def test_empty_accept(self):
        req = _make_request(accept="")
        assert req.prefers_crous() is False

    def test_no_accept_header(self):
        req = _make_request()
        assert req.prefers_crous() is False

    def test_crous_only(self):
        req = _make_request(accept="application/x-crous")
        # json_q=0.0, crous_q=1.0  →  True
        assert req.prefers_crous() is True

    def test_invalid_q_value(self):
        req = _make_request(accept="application/x-crous;q=abc, application/json")
        # q=abc → 0.0, json q=1.0  → False
        assert req.prefers_crous() is False


class TestBestResponseFormat:
    """Request.best_response_format() negotiation."""

    def test_crous_preferred(self):
        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.8")
        assert req.best_response_format() == "crous"

    def test_json_default(self):
        req = _make_request(accept="application/json")
        assert req.best_response_format() == "json"

    def test_no_accept(self):
        req = _make_request()
        assert req.best_response_format() == "json"

    def test_crous_unavailable_falls_back(self):
        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.8")
        with patch("aquilia.request._HAS_CROUS", False):
            assert req.best_response_format() == "json"


# ============================================================================
# §2 — Request.crous() parsing
# ============================================================================


class TestRequestCrousParser:
    """Request.crous() payload decoding."""

    @pytest.mark.asyncio
    async def test_parse_dict(self):
        payload = _crous_mod.encode({"name": "Aquilia", "version": 2})
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result == {"name": "Aquilia", "version": 2}

    @pytest.mark.asyncio
    async def test_parse_list(self):
        payload = _crous_mod.encode([1, 2, 3])
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_parse_nested(self):
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        payload = _crous_mod.encode(data)
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result == data

    @pytest.mark.asyncio
    async def test_parse_scalar_string(self):
        payload = _crous_mod.encode("hello world")
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_parse_scalar_int(self):
        payload = _crous_mod.encode(42)
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result == 42

    @pytest.mark.asyncio
    async def test_parse_null(self):
        payload = _crous_mod.encode(None)
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_bool(self):
        payload = _crous_mod.encode(True)
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert result is True

    @pytest.mark.asyncio
    async def test_parse_float(self):
        payload = _crous_mod.encode(3.14)
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.crous()
        assert abs(result - 3.14) < 1e-9

    @pytest.mark.asyncio
    async def test_idempotent_caching(self):
        payload = _crous_mod.encode({"cached": True})
        req = _make_request(body=payload, content_type="application/x-crous")
        r1 = await req.crous()
        r2 = await req.crous()
        assert r1 is r2  # Same object reference

    @pytest.mark.asyncio
    async def test_invalid_magic_strict(self):
        from aquilia.request import InvalidCrous

        req = _make_request(body=b"NOT_CROUS_DATA", content_type="application/x-crous")
        with pytest.raises(InvalidCrous):
            await req.crous(strict=True)

    @pytest.mark.asyncio
    async def test_invalid_magic_non_strict(self):
        # Non-strict skips magic check; crous.decode on garbage
        # may return empty list or unexpected data rather than raising.
        req = _make_request(body=b"garbage", content_type="application/x-crous")
        result = await req.crous(strict=False)
        # crous.decode(b"garbage") returns [] — parsed but meaningless
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_body(self):
        from aquilia.request import InvalidCrous

        req = _make_request(body=b"", content_type="application/x-crous")
        with pytest.raises(InvalidCrous, match="Empty"):
            await req.crous()

    @pytest.mark.asyncio
    async def test_payload_too_large(self):
        from aquilia.request import PayloadTooLarge

        payload = _crous_mod.encode({"big": "x" * 1000})
        req = _make_request(body=payload, content_type="application/x-crous")
        req.json_max_size = 10  # tiny limit
        with pytest.raises(PayloadTooLarge):
            await req.crous()

    @pytest.mark.asyncio
    async def test_crous_unavailable(self):
        from aquilia.request import CrousUnavailable

        payload = _crous_mod.encode({"test": 1})
        req = _make_request(body=payload, content_type="application/x-crous")
        with patch("aquilia.request._HAS_CROUS", False):
            with pytest.raises(CrousUnavailable):
                await req.crous()

    @pytest.mark.asyncio
    async def test_model_validation_dict(self):
        """Model validation with a callable (like a dataclass)."""
        from dataclasses import dataclass

        @dataclass
        class User:
            name: str
            age: int

        payload = _crous_mod.encode({"name": "Alice", "age": 30})
        req = _make_request(body=payload, content_type="application/x-crous")
        user = await req.crous(User)
        assert user.name == "Alice"
        assert user.age == 30


# ============================================================================
# §3 — Request.data() auto-detection
# ============================================================================


class TestRequestDataAutoDetect:
    """Request.data() routes to crous() or json() automatically."""

    @pytest.mark.asyncio
    async def test_auto_detect_crous(self):
        payload = _crous_mod.encode({"format": "crous"})
        req = _make_request(body=payload, content_type="application/x-crous")
        result = await req.data()
        assert result == {"format": "crous"}

    @pytest.mark.asyncio
    async def test_auto_detect_json(self):
        body = json.dumps({"format": "json"}).encode()
        req = _make_request(body=body, content_type="application/json")
        result = await req.data()
        assert result == {"format": "json"}

    @pytest.mark.asyncio
    async def test_auto_detect_crous_by_magic(self):
        payload = _crous_mod.encode({"magic": True})
        req = _make_request(body=payload)
        # Pre-cache body so magic detection fires
        req._body = payload
        result = await req.data()
        assert result == {"magic": True}


# ============================================================================
# §4 — Response.crous() factory
# ============================================================================


class TestResponseCrous:
    """Response.crous() serialization."""

    def test_basic_dict(self):
        from aquilia.response import Response, CROUS_MEDIA_TYPE

        resp = Response.crous({"key": "value"})
        assert resp.status == 200
        ct = resp._headers.get("content-type", "")
        assert CROUS_MEDIA_TYPE in ct

        # Body should be valid CROUS
        body = resp._content
        assert isinstance(body, bytes)
        assert body[:7] == b"CROUSv1"
        decoded = _crous_mod.decode(body)
        assert decoded == {"key": "value"}

    def test_basic_list(self):
        from aquilia.response import Response

        resp = Response.crous([1, 2, 3])
        decoded = _crous_mod.decode(resp._content)
        assert decoded == [1, 2, 3]

    def test_status_code(self):
        from aquilia.response import Response

        resp = Response.crous({"ok": True}, status=201)
        assert resp.status == 201

    def test_extra_headers(self):
        from aquilia.response import Response

        resp = Response.crous({"ok": True}, headers={"x-custom": "yes"})
        assert resp._headers.get("x-custom") == "yes"

    def test_content_length_set(self):
        from aquilia.response import Response

        resp = Response.crous({"size": "check"})
        cl = resp._headers.get("content-length")
        assert cl is not None
        assert int(cl) == len(resp._content)

    def test_crous_version_header(self):
        from aquilia.response import Response

        resp = Response.crous({"version": True})
        assert resp._headers.get("x-crous-version") == "1"

    def test_nested_data(self):
        from aquilia.response import Response

        data = {
            "users": [
                {"id": 1, "name": "Alice", "roles": ["admin"]},
                {"id": 2, "name": "Bob", "roles": []},
            ],
            "total": 2,
        }
        resp = Response.crous(data)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == data

    def test_dedup_enabled_by_default(self):
        from aquilia.response import Response

        # With lots of repeated strings, dedup should produce smaller output
        data = {"items": [{"type": "widget"} for _ in range(100)]}
        resp_dedup = Response.crous(data, dedup=True)
        resp_no_dedup = Response.crous(data, dedup=False)
        # Dedup should be same or smaller
        assert len(resp_dedup._content) <= len(resp_no_dedup._content)

    def test_compression_none_explicit(self):
        from aquilia.response import Response

        data = {"big": "x" * 1000}
        resp = Response.crous(data, compression="none")
        assert resp._content[:7] == b"CROUSv1"
        decoded = _crous_mod.decode(resp._content)
        assert decoded == data

    def test_compression_unavailable_graceful(self):
        """When compression is requested but not available at decode time,
        the response itself is still valid CROUS binary."""
        from aquilia.response import Response

        data = {"compressed": True}
        # Encoding with zstd succeeds (encode side works)
        resp = Response.crous(data, compression="zstd")
        assert resp._content[:7] == b"CROUSv1"
        # Content-type is still CROUS
        ct = resp._headers.get("content-type", "")
        assert "crous" in ct

    def test_fallback_to_json_when_unavailable(self):
        from aquilia.response import Response

        with patch("aquilia.response._HAS_CROUS", False):
            resp = Response.crous({"fallback": True})
            ct = resp._headers.get("content-type", "")
            assert "json" in ct

    def test_unicode_data(self):
        from aquilia.response import Response

        data = {"emoji": "🚀", "chinese": "你好", "arabic": "مرحبا"}
        resp = Response.crous(data)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == data

    def test_empty_dict(self):
        from aquilia.response import Response

        resp = Response.crous({})
        decoded = _crous_mod.decode(resp._content)
        assert decoded == {}

    def test_empty_list(self):
        from aquilia.response import Response

        resp = Response.crous([])
        decoded = _crous_mod.decode(resp._content)
        assert decoded == []

    def test_scalar_string(self):
        from aquilia.response import Response

        resp = Response.crous("hello")
        decoded = _crous_mod.decode(resp._content)
        assert decoded == "hello"

    def test_scalar_int(self):
        from aquilia.response import Response

        resp = Response.crous(42)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == 42

    def test_none_value(self):
        from aquilia.response import Response

        resp = Response.crous(None)
        decoded = _crous_mod.decode(resp._content)
        assert decoded is None

    def test_bool_value(self):
        from aquilia.response import Response

        resp = Response.crous(True)
        decoded = _crous_mod.decode(resp._content)
        assert decoded is True


# ============================================================================
# §5 — Response.negotiated() content negotiation
# ============================================================================


class TestResponseNegotiated:
    """Response.negotiated() selects CROUS vs JSON."""

    def test_negotiated_crous_when_preferred(self):
        from aquilia.response import Response, CROUS_MEDIA_TYPE

        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.8")
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert CROUS_MEDIA_TYPE in ct

    def test_negotiated_json_when_preferred(self):
        from aquilia.response import Response

        req = _make_request(accept="application/json")
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert "json" in ct

    def test_negotiated_json_default(self):
        from aquilia.response import Response

        req = _make_request()
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert "json" in ct

    def test_negotiated_with_requires_crous(self):
        from aquilia.response import Response, CROUS_MEDIA_TYPE, requires_crous

        @requires_crous
        async def handler():
            pass

        req = _make_request(accept="application/x-crous, application/json")
        req.state["matched_handler"] = handler
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert CROUS_MEDIA_TYPE in ct

    def test_negotiated_requires_crous_but_client_rejects(self):
        from aquilia.response import Response, requires_crous

        @requires_crous
        async def handler():
            pass

        req = _make_request(accept="application/json")
        req.state["matched_handler"] = handler
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        # Client doesn't accept CROUS, so JSON
        assert "json" in ct

    def test_negotiated_fallback_when_crous_unavailable(self):
        from aquilia.response import Response

        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.8")
        with patch("aquilia.response._HAS_CROUS", False):
            resp = Response.negotiated({"data": 1}, req)
            ct = resp._headers.get("content-type", "")
            assert "json" in ct

    def test_negotiated_status_preserved(self):
        from aquilia.response import Response

        req = _make_request(accept="application/x-crous;q=1.0, application/json;q=0.8")
        resp = Response.negotiated({"data": 1}, req, status=201)
        assert resp.status == 201


# ============================================================================
# §6 — _detect_media_type CROUS magic
# ============================================================================


class TestDetectMediaType:
    """Response._detect_media_type auto-detects CROUS binary."""

    def test_crous_bytes(self):
        from aquilia.response import Response, CROUS_MEDIA_TYPE

        payload = _crous_mod.encode({"detect": True})
        resp = Response(content=payload)
        ct = resp._headers.get("content-type", "")
        assert CROUS_MEDIA_TYPE in ct

    def test_plain_bytes(self):
        from aquilia.response import Response

        resp = Response(content=b"plain binary")
        ct = resp._headers.get("content-type", "")
        assert ct == "application/octet-stream"

    def test_short_bytes_no_crash(self):
        from aquilia.response import Response

        resp = Response(content=b"CRO")
        ct = resp._headers.get("content-type", "")
        assert ct == "application/octet-stream"

    def test_empty_bytes(self):
        from aquilia.response import Response

        resp = Response(content=b"")
        ct = resp._headers.get("content-type", "")
        assert ct == "application/octet-stream"


# ============================================================================
# §7 — requires_crous decorator
# ============================================================================


class TestRequiresCrousDecorator:
    """requires_crous sets __crous_response__."""

    def test_sets_attribute(self):
        from aquilia.response import requires_crous

        @requires_crous
        async def my_handler():
            pass

        assert my_handler.__crous_response__ is True

    def test_preserves_function(self):
        from aquilia.response import requires_crous
        import inspect

        @requires_crous
        async def my_handler():
            return 42

        assert inspect.iscoroutinefunction(my_handler)

    def test_stacks_with_other_decorators(self):
        """requires_crous can stack with @requires effects."""
        from aquilia.response import requires_crous
        from aquilia.flow import requires

        @requires_crous
        @requires("DBTx")
        async def handler():
            pass

        assert handler.__crous_response__ is True
        assert "DBTx" in handler.__flow_effects__

    def test_sync_function(self):
        from aquilia.response import requires_crous

        @requires_crous
        def sync_handler():
            pass

        assert sync_handler.__crous_response__ is True


# ============================================================================
# §8 — CROUS-specific faults
# ============================================================================


class TestCrousFaults:
    """InvalidCrous and CrousUnavailable fault classes."""

    def test_invalid_crous_code(self):
        from aquilia.request import InvalidCrous

        fault = InvalidCrous("bad payload")
        assert fault.code == "INVALID_CROUS"
        assert "bad payload" in fault.message

    def test_invalid_crous_default_message(self):
        from aquilia.request import InvalidCrous

        fault = InvalidCrous()
        assert fault.message == "Invalid CROUS payload"

    def test_invalid_crous_metadata(self):
        from aquilia.request import InvalidCrous

        fault = InvalidCrous("fail", magic="deadbeef")
        assert fault.metadata.get("magic") == "deadbeef"

    def test_crous_unavailable_code(self):
        from aquilia.request import CrousUnavailable

        fault = CrousUnavailable()
        assert fault.code == "CROUS_UNAVAILABLE"

    def test_crous_unavailable_not_public(self):
        from aquilia.request import CrousUnavailable

        fault = CrousUnavailable()
        # Not exposed to clients — internal error
        assert fault.public is False

    def test_invalid_crous_is_request_fault(self):
        from aquilia.request import InvalidCrous, RequestFault

        assert issubclass(InvalidCrous, RequestFault)

    def test_crous_unavailable_is_request_fault(self):
        from aquilia.request import CrousUnavailable, RequestFault

        assert issubclass(CrousUnavailable, RequestFault)


# ============================================================================
# §9 — Full round-trip
# ============================================================================


class TestCrousRoundTrip:
    """End-to-end: Python → CROUS bytes → Request.crous() → Response.crous() → Python."""

    @pytest.mark.asyncio
    async def test_dict_round_trip(self):
        from aquilia.response import Response

        original = {"users": [{"id": 1, "name": "Alice"}], "total": 1}

        # Encode to wire bytes
        wire = _crous_mod.encode(original)

        # Parse on request side
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        assert parsed == original

        # Build response
        resp = Response.crous(parsed)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_nested_round_trip(self):
        from aquilia.response import Response

        original = {
            "config": {
                "database": {"host": "localhost", "port": 5432},
                "cache": {"ttl": 300, "enabled": True},
            },
            "features": ["auth", "i18n", "crous"],
        }

        wire = _crous_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        resp = Response.crous(parsed)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_unicode_round_trip(self):
        from aquilia.response import Response

        original = {"emoji": "🎉🚀✨", "japanese": "こんにちは", "rtl": "שלום"}

        wire = _crous_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        resp = Response.crous(parsed)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_large_payload_round_trip(self):
        from aquilia.response import Response

        original = {"items": [{"id": i, "value": f"item_{i}"} for i in range(500)]}

        wire = _crous_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-crous")
        req.json_max_size = 10_000_000  # Ensure large enough
        parsed = await req.crous()
        resp = Response.crous(parsed)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_no_compression_round_trip(self):
        from aquilia.response import Response

        original = {"data": "y" * 500}

        wire = _crous_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        # Use dedup but no compression to ensure full round-trip
        resp = Response.crous(parsed, dedup=True, compression=None)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == original


# ============================================================================
# §10 — Edge cases & regression guards
# ============================================================================


class TestEdgeCases:
    """Boundary conditions and regression guards."""

    @pytest.mark.asyncio
    async def test_crous_then_json_separate_caches(self):
        """crous() and json() use separate caches."""
        crous_body = _crous_mod.encode({"source": "crous"})
        req = _make_request(body=crous_body, content_type="application/x-crous")
        crous_result = await req.crous()
        assert crous_result == {"source": "crous"}
        # JSON cache should still be None
        assert req._json is None

    def test_has_crous_function(self):
        from aquilia.response import has_crous

        assert has_crous() is True

    def test_has_crous_when_unavailable(self):
        from aquilia.response import has_crous

        with patch("aquilia.response._HAS_CROUS", False):
            assert has_crous() is False

    def test_crous_media_type_constant(self):
        from aquilia.request import CROUS_MEDIA_TYPE
        from aquilia.response import CROUS_MEDIA_TYPE as RESP_CROUS_MT

        assert CROUS_MEDIA_TYPE == "application/x-crous"
        assert RESP_CROUS_MT == "application/x-crous"

    def test_crous_magic_constant(self):
        from aquilia.request import CROUS_MAGIC
        from aquilia.response import CROUS_MAGIC as RESP_MAGIC

        assert CROUS_MAGIC == b"CROUSv1"
        assert RESP_MAGIC == b"CROUSv1"

    @pytest.mark.asyncio
    async def test_binary_bytes_in_dict(self):
        """CROUS supports bytes values natively."""
        from aquilia.response import Response

        original = {"binary": b"\x00\x01\x02\xff"}
        wire = _crous_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        assert parsed["binary"] == b"\x00\x01\x02\xff"

        resp = Response.crous(parsed)
        decoded = _crous_mod.decode(resp._content)
        assert decoded["binary"] == b"\x00\x01\x02\xff"

    def test_crous_media_types_frozenset(self):
        from aquilia.request import CROUS_MEDIA_TYPES

        assert isinstance(CROUS_MEDIA_TYPES, frozenset)
        assert len(CROUS_MEDIA_TYPES) == 3

    @pytest.mark.asyncio
    async def test_deeply_nested_structure(self):
        """Deep nesting should encode/decode correctly."""
        from aquilia.response import Response

        data: Any = "leaf"
        for _ in range(20):
            data = {"nested": data}

        wire = _crous_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()

        # Traverse 20 levels
        node = parsed
        for _ in range(20):
            assert "nested" in node
            node = node["nested"]
        assert node == "leaf"

    def test_response_crous_invalid_compression_ignored(self):
        """Unknown compression name should not crash."""
        from aquilia.response import Response

        resp = Response.crous({"test": True}, compression="unknown_algo")
        # Should still produce valid CROUS (no compression applied)
        decoded = _crous_mod.decode(resp._content)
        assert decoded == {"test": True}

    @pytest.mark.asyncio
    async def test_negative_integers(self):
        from aquilia.response import Response

        data = {"neg": -42, "zero": 0, "pos": 100}
        wire = _crous_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        assert parsed == data

    @pytest.mark.asyncio
    async def test_mixed_type_list(self):
        data = [1, "two", 3.0, True, None, {"nested": "yes"}]
        wire = _crous_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-crous")
        parsed = await req.crous()
        assert parsed == data

    def test_response_crous_preserves_insertion_order(self):
        from aquilia.response import Response
        from collections import OrderedDict

        data = OrderedDict([("z", 1), ("a", 2), ("m", 3)])
        resp = Response.crous(data)
        decoded = _crous_mod.decode(resp._content)
        assert list(decoded.keys()) == ["z", "a", "m"]


class TestModuleExports:
    """Verify CROUS symbols are properly exported."""

    def test_response_exports(self):
        from aquilia.response import __all__

        assert "CROUS_MEDIA_TYPE" in __all__
        assert "CROUS_MAGIC" in __all__
        assert "has_crous" in __all__
        assert "requires_crous" in __all__

    def test_request_importable(self):
        from aquilia.request import (
            CROUS_MEDIA_TYPE,
            CROUS_MEDIA_TYPES,
            CROUS_MAGIC,
            InvalidCrous,
            CrousUnavailable,
        )

        assert CROUS_MEDIA_TYPE == "application/x-crous"
        assert InvalidCrous is not None
        assert CrousUnavailable is not None
