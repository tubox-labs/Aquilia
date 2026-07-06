"""
Comprehensive regression tests for SURP request / response integration.

Covers:
- §1: Request — is_surp, accepts_surp, prefers_surp, best_response_format
- §2: Request — surp() payload parsing, model validation, error handling
- §3: Request — data() auto-detection (JSON vs SURP)
- §4: Response — Response.surp() factory, fallback, compression, dedup
- §5: Response — Response.negotiated() content negotiation
- §6: Response — _detect_media_type binary fallback
- §7: Decorator — requires_surp attribute tagging
- §8: Faults — InvalidSurp, SurpUnavailable
- §9: Round-trip — encode → request.surp() → Response.surp() → decode
- §10: Edge cases & regression guards
"""

import json
from typing import Any
from unittest.mock import patch

import pytest

_surp_mod = pytest.importorskip("surp")

# ============================================================================
# Helpers
# ============================================================================


def _make_scope(
    method: str = "POST",
    path: str = "/",
    headers: dict[str, str] | None = None,
    content_type: str | None = None,
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
    content_type: str | None = None,
    accept: str | None = None,
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


class TestIsSurp:
    """Request.is_surp() detection."""

    def test_application_x_surp(self):
        req = _make_request(content_type="application/x-surp")
        assert req.is_surp() is True

    def test_application_surp(self):
        req = _make_request(content_type="application/surp")
        assert req.is_surp() is True

    def test_application_vnd_surp(self):
        req = _make_request(content_type="application/vnd.surp")
        assert req.is_surp() is True

    def test_json_is_not_surp(self):
        req = _make_request(content_type="application/json")
        assert req.is_surp() is False

    def test_no_content_type_does_not_guess_binary_format(self):
        body = _surp_mod.encode({"hello": "world"})
        req = _make_request(body=body)
        req._body = body
        assert req.is_surp() is False

    def test_no_content_type_non_surp_body(self):
        req = _make_request(body=b'{"json": true}')
        req._body = b'{"json": true}'
        assert req.is_surp() is False


class TestAcceptsSurp:
    """Request.accepts_surp()."""

    def test_explicit_accept(self):
        req = _make_request(accept="application/x-surp")
        assert req.accepts_surp() is True

    def test_wildcard_accept(self):
        req = _make_request(accept="*/*")
        assert req.accepts_surp() is True

    def test_json_only(self):
        req = _make_request(accept="application/json")
        assert req.accepts_surp() is False

    def test_mixed_accept(self):
        req = _make_request(accept="application/json, application/x-surp")
        assert req.accepts_surp() is True

    def test_vnd_surp_accept(self):
        req = _make_request(accept="application/vnd.surp")
        assert req.accepts_surp() is True


class TestPrefersSurp:
    """Request.prefers_surp() quality-factor negotiation."""

    def test_surp_higher_quality(self):
        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.9")
        assert req.prefers_surp() is True

    def test_json_higher_quality(self):
        req = _make_request(accept="application/json;q=1.0, application/x-surp;q=0.5")
        assert req.prefers_surp() is False

    def test_surp_implicit_q1(self):
        req = _make_request(accept="application/x-surp, application/json;q=0.8")
        assert req.prefers_surp() is True

    def test_both_implicit_q1(self):
        # Equal quality — surp not *strictly* greater
        req = _make_request(accept="application/x-surp, application/json")
        assert req.prefers_surp() is False

    def test_wildcard_does_not_prefer(self):
        req = _make_request(accept="*/*")
        assert req.prefers_surp() is False

    def test_no_surp_in_accept(self):
        req = _make_request(accept="application/json")
        assert req.prefers_surp() is False

    def test_empty_accept(self):
        req = _make_request(accept="")
        assert req.prefers_surp() is False

    def test_no_accept_header(self):
        req = _make_request()
        assert req.prefers_surp() is False

    def test_surp_only(self):
        req = _make_request(accept="application/x-surp")
        # json_q=0.0, surp_q=1.0  →  True
        assert req.prefers_surp() is True

    def test_invalid_q_value(self):
        req = _make_request(accept="application/x-surp;q=abc, application/json")
        # q=abc → 0.0, json q=1.0  → False
        assert req.prefers_surp() is False


class TestBestResponseFormat:
    """Request.best_response_format() negotiation."""

    def test_surp_preferred(self):
        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.8")
        assert req.best_response_format() == "surp"

    def test_json_default(self):
        req = _make_request(accept="application/json")
        assert req.best_response_format() == "json"

    def test_no_accept(self):
        req = _make_request()
        assert req.best_response_format() == "json"

    def test_surp_unavailable_falls_back(self):
        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.8")
        with patch("aquilia.request._HAS_SURP", False):
            assert req.best_response_format() == "json"


# ============================================================================
# §2 — Request.surp() parsing
# ============================================================================


class TestRequestSurpParser:
    """Request.surp() payload decoding."""

    @pytest.mark.asyncio
    async def test_parse_dict(self):
        payload = _surp_mod.encode({"name": "Aquilia", "version": 2})
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result == {"name": "Aquilia", "version": 2}

    @pytest.mark.asyncio
    async def test_parse_list(self):
        payload = _surp_mod.encode([1, 2, 3])
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_parse_nested(self):
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        payload = _surp_mod.encode(data)
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result == data

    @pytest.mark.asyncio
    async def test_parse_scalar_string(self):
        payload = _surp_mod.encode("hello world")
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_parse_scalar_int(self):
        payload = _surp_mod.encode(42)
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result == 42

    @pytest.mark.asyncio
    async def test_parse_null(self):
        payload = _surp_mod.encode(None)
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_bool(self):
        payload = _surp_mod.encode(True)
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert result is True

    @pytest.mark.asyncio
    async def test_parse_float(self):
        payload = _surp_mod.encode(3.14)
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.surp()
        assert abs(result - 3.14) < 1e-9

    @pytest.mark.asyncio
    async def test_idempotent_caching(self):
        payload = _surp_mod.encode({"cached": True})
        req = _make_request(body=payload, content_type="application/x-surp")
        r1 = await req.surp()
        r2 = await req.surp()
        assert r1 is r2  # Same object reference

    @pytest.mark.asyncio
    async def test_invalid_payload_strict(self):
        from aquilia.request import InvalidSurp

        req = _make_request(body=b"NOT_SURP_DATA", content_type="application/x-surp")
        with pytest.raises(InvalidSurp):
            await req.surp(strict=True)

    @pytest.mark.asyncio
    async def test_invalid_payload_non_strict(self):
        from aquilia.request import InvalidSurp

        req = _make_request(body=b"garbage", content_type="application/x-surp")
        with pytest.raises(InvalidSurp):
            await req.surp(strict=False)

    @pytest.mark.asyncio
    async def test_empty_body(self):
        from aquilia.request import InvalidSurp

        req = _make_request(body=b"", content_type="application/x-surp")
        with pytest.raises(InvalidSurp, match="Empty"):
            await req.surp()

    @pytest.mark.asyncio
    async def test_payload_too_large(self):
        from aquilia.request import PayloadTooLarge

        payload = _surp_mod.encode({"big": "x" * 1000})
        req = _make_request(body=payload, content_type="application/x-surp")
        req.json_max_size = 10  # tiny limit
        with pytest.raises(PayloadTooLarge):
            await req.surp()

    @pytest.mark.asyncio
    async def test_surp_unavailable(self):
        from aquilia.request import SurpUnavailable

        payload = _surp_mod.encode({"test": 1})
        req = _make_request(body=payload, content_type="application/x-surp")
        with patch("aquilia.request._HAS_SURP", False), pytest.raises(SurpUnavailable):
            await req.surp()

    @pytest.mark.asyncio
    async def test_model_validation_dict(self):
        """Model validation with a callable (like a dataclass)."""
        from dataclasses import dataclass

        @dataclass
        class User:
            name: str
            age: int

        payload = _surp_mod.encode({"name": "Alice", "age": 30})
        req = _make_request(body=payload, content_type="application/x-surp")
        user = await req.surp(User)
        assert user.name == "Alice"
        assert user.age == 30


# ============================================================================
# §3 — Request.data() auto-detection
# ============================================================================


class TestRequestDataAutoDetect:
    """Request.data() routes to surp() or json() automatically."""

    @pytest.mark.asyncio
    async def test_auto_detect_surp(self):
        payload = _surp_mod.encode({"format": "surp"})
        req = _make_request(body=payload, content_type="application/x-surp")
        result = await req.data()
        assert result == {"format": "surp"}

    @pytest.mark.asyncio
    async def test_auto_detect_json(self):
        body = json.dumps({"format": "json"}).encode()
        req = _make_request(body=body, content_type="application/json")
        result = await req.data()
        assert result == {"format": "json"}

    @pytest.mark.asyncio
    async def test_data_without_surp_content_type_uses_json(self):
        from aquilia.request import InvalidJSON

        payload = _surp_mod.encode({"magic": True})
        req = _make_request(body=payload)
        req._body = payload
        with pytest.raises(InvalidJSON):
            await req.data()


# ============================================================================
# §4 — Response.surp() factory
# ============================================================================


class TestResponseSurp:
    """Response.surp() serialization."""

    def test_basic_dict(self):
        from aquilia.response import SURP_MEDIA_TYPE, Response

        resp = Response.surp({"key": "value"})
        assert resp.status == 200
        ct = resp._headers.get("content-type", "")
        assert SURP_MEDIA_TYPE in ct

        # Body should be valid SURP
        body = resp._content
        assert isinstance(body, bytes)
        decoded = _surp_mod.decode(body)
        assert decoded == {"key": "value"}

    def test_basic_list(self):
        from aquilia.response import Response

        resp = Response.surp([1, 2, 3])
        decoded = _surp_mod.decode(resp._content)
        assert decoded == [1, 2, 3]

    def test_status_code(self):
        from aquilia.response import Response

        resp = Response.surp({"ok": True}, status=201)
        assert resp.status == 201

    def test_extra_headers(self):
        from aquilia.response import Response

        resp = Response.surp({"ok": True}, headers={"x-custom": "yes"})
        assert resp._headers.get("x-custom") == "yes"

    def test_content_length_set(self):
        from aquilia.response import Response

        resp = Response.surp({"size": "check"})
        cl = resp._headers.get("content-length")
        assert cl is not None
        assert int(cl) == len(resp._content)

    def test_surp_version_header(self):
        from aquilia.response import Response

        resp = Response.surp({"version": True})
        assert resp._headers.get("x-surp-version") == "1"

    def test_nested_data(self):
        from aquilia.response import Response

        data = {
            "users": [
                {"id": 1, "name": "Alice", "roles": ["admin"]},
                {"id": 2, "name": "Bob", "roles": []},
            ],
            "total": 2,
        }
        resp = Response.surp(data)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == data

    def test_dedup_enabled_by_default(self):
        from aquilia.response import Response

        # With lots of repeated strings, dedup should produce smaller output
        data = {"items": [{"type": "widget"} for _ in range(100)]}
        resp_dedup = Response.surp(data, dedup=True)
        resp_no_dedup = Response.surp(data, dedup=False)
        # Dedup should be same or smaller
        assert len(resp_dedup._content) <= len(resp_no_dedup._content)

    def test_compression_none_explicit(self):
        from aquilia.response import Response

        data = {"big": "x" * 1000}
        resp = Response.surp(data, compression="none")
        decoded = _surp_mod.decode(resp._content)
        assert decoded == data

    def test_compression_unavailable_graceful(self):
        """When compression is requested but not available at decode time,
        the response itself is still valid SURP binary."""
        from aquilia.response import Response

        data = {"compressed": True}
        # Encoding with zstd succeeds (encode side works)
        resp = Response.surp(data, compression="zstd")
        # Content-type is still SURP
        ct = resp._headers.get("content-type", "")
        assert "surp" in ct

    def test_fallback_to_json_when_unavailable(self):
        from aquilia.response import Response

        with patch("aquilia.response._HAS_SURP", False):
            resp = Response.surp({"fallback": True})
            ct = resp._headers.get("content-type", "")
            assert "json" in ct

    def test_unicode_data(self):
        from aquilia.response import Response

        data = {"emoji": "🚀", "chinese": "你好", "arabic": "مرحبا"}
        resp = Response.surp(data)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == data

    def test_empty_dict(self):
        from aquilia.response import Response

        resp = Response.surp({})
        decoded = _surp_mod.decode(resp._content)
        assert decoded == {}

    def test_empty_list(self):
        from aquilia.response import Response

        resp = Response.surp([])
        decoded = _surp_mod.decode(resp._content)
        assert decoded == []

    def test_scalar_string(self):
        from aquilia.response import Response

        resp = Response.surp("hello")
        decoded = _surp_mod.decode(resp._content)
        assert decoded == "hello"

    def test_scalar_int(self):
        from aquilia.response import Response

        resp = Response.surp(42)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == 42

    def test_none_value(self):
        from aquilia.response import Response

        resp = Response.surp(None)
        decoded = _surp_mod.decode(resp._content)
        assert decoded is None

    def test_bool_value(self):
        from aquilia.response import Response

        resp = Response.surp(True)
        decoded = _surp_mod.decode(resp._content)
        assert decoded is True


# ============================================================================
# §5 — Response.negotiated() content negotiation
# ============================================================================


class TestResponseNegotiated:
    """Response.negotiated() selects SURP vs JSON."""

    def test_negotiated_surp_when_preferred(self):
        from aquilia.response import SURP_MEDIA_TYPE, Response

        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.8")
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert SURP_MEDIA_TYPE in ct

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

    def test_negotiated_with_requires_surp(self):
        from aquilia.response import SURP_MEDIA_TYPE, Response, requires_surp

        @requires_surp
        async def handler():
            pass

        req = _make_request(accept="application/x-surp, application/json")
        req.state["matched_handler"] = handler
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        assert SURP_MEDIA_TYPE in ct

    def test_negotiated_requires_surp_but_client_rejects(self):
        from aquilia.response import Response, requires_surp

        @requires_surp
        async def handler():
            pass

        req = _make_request(accept="application/json")
        req.state["matched_handler"] = handler
        resp = Response.negotiated({"data": 1}, req)
        ct = resp._headers.get("content-type", "")
        # Client doesn't accept SURP, so JSON
        assert "json" in ct

    def test_negotiated_fallback_when_surp_unavailable(self):
        from aquilia.response import Response

        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.8")
        with patch("aquilia.response._HAS_SURP", False):
            resp = Response.negotiated({"data": 1}, req)
            ct = resp._headers.get("content-type", "")
            assert "json" in ct

    def test_negotiated_status_preserved(self):
        from aquilia.response import Response

        req = _make_request(accept="application/x-surp;q=1.0, application/json;q=0.8")
        resp = Response.negotiated({"data": 1}, req, status=201)
        assert resp.status == 201


# ============================================================================
# §6 — _detect_media_type binary fallback
# ============================================================================


class TestDetectMediaType:
    """Response._detect_media_type handles binary payloads."""

    def test_surp_bytes_without_media_type_are_octet_stream(self):
        from aquilia.response import Response

        payload = _surp_mod.encode({"detect": True})
        resp = Response(content=payload)
        ct = resp._headers.get("content-type", "")
        assert ct == "application/octet-stream"

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
# §7 — requires_surp decorator
# ============================================================================


class TestRequiresSurpDecorator:
    """requires_surp sets __surp_response__."""

    def test_sets_attribute(self):
        from aquilia.response import requires_surp

        @requires_surp
        async def my_handler():
            pass

        assert my_handler.__surp_response__ is True

    def test_preserves_function(self):
        import inspect

        from aquilia.response import requires_surp

        @requires_surp
        async def my_handler():
            return 42

        assert inspect.iscoroutinefunction(my_handler)

    def test_stacks_with_other_decorators(self):
        """requires_surp can stack with @requires effects."""
        from aquilia.flow import requires
        from aquilia.response import requires_surp

        @requires_surp
        @requires("DBTx")
        async def handler():
            pass

        assert handler.__surp_response__ is True
        assert "DBTx" in handler.__flow_effects__

    def test_sync_function(self):
        from aquilia.response import requires_surp

        @requires_surp
        def sync_handler():
            pass

        assert sync_handler.__surp_response__ is True


# ============================================================================
# §8 — SURP-specific faults
# ============================================================================


class TestSurpFaults:
    """InvalidSurp and SurpUnavailable fault classes."""

    def test_invalid_surp_code(self):
        from aquilia.request import InvalidSurp

        fault = InvalidSurp("bad payload")
        assert fault.code == "INVALID_SURP"
        assert "bad payload" in fault.message

    def test_invalid_surp_default_message(self):
        from aquilia.request import InvalidSurp

        fault = InvalidSurp()
        assert fault.message == "Invalid SURP payload"

    def test_invalid_surp_metadata(self):
        from aquilia.request import InvalidSurp

        fault = InvalidSurp("fail", magic="deadbeef")
        assert fault.metadata.get("magic") == "deadbeef"

    def test_surp_unavailable_code(self):
        from aquilia.request import SurpUnavailable

        fault = SurpUnavailable()
        assert fault.code == "SURP_UNAVAILABLE"

    def test_surp_unavailable_not_public(self):
        from aquilia.request import SurpUnavailable

        fault = SurpUnavailable()
        # Not exposed to clients — internal error
        assert fault.public is False

    def test_invalid_surp_is_request_fault(self):
        from aquilia.request import InvalidSurp, RequestFault

        assert issubclass(InvalidSurp, RequestFault)

    def test_surp_unavailable_is_request_fault(self):
        from aquilia.request import RequestFault, SurpUnavailable

        assert issubclass(SurpUnavailable, RequestFault)


# ============================================================================
# §9 — Full round-trip
# ============================================================================


class TestSurpRoundTrip:
    """End-to-end: Python → SURP bytes → Request.surp() → Response.surp() → Python."""

    @pytest.mark.asyncio
    async def test_dict_round_trip(self):
        from aquilia.response import Response

        original = {"users": [{"id": 1, "name": "Alice"}], "total": 1}

        # Encode to wire bytes
        wire = _surp_mod.encode(original)

        # Parse on request side
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        assert parsed == original

        # Build response
        resp = Response.surp(parsed)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_nested_round_trip(self):
        from aquilia.response import Response

        original = {
            "config": {
                "database": {"host": "localhost", "port": 5432},
                "cache": {"ttl": 300, "enabled": True},
            },
            "features": ["auth", "i18n", "surp"],
        }

        wire = _surp_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        resp = Response.surp(parsed)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_unicode_round_trip(self):
        from aquilia.response import Response

        original = {"emoji": "🎉🚀✨", "japanese": "こんにちは", "rtl": "שלום"}

        wire = _surp_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        resp = Response.surp(parsed)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_large_payload_round_trip(self):
        from aquilia.response import Response

        original = {"items": [{"id": i, "value": f"item_{i}"} for i in range(500)]}

        wire = _surp_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-surp")
        req.json_max_size = 10_000_000  # Ensure large enough
        parsed = await req.surp()
        resp = Response.surp(parsed)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == original

    @pytest.mark.asyncio
    async def test_no_compression_round_trip(self):
        from aquilia.response import Response

        original = {"data": "y" * 500}

        wire = _surp_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        # Use dedup but no compression to ensure full round-trip
        resp = Response.surp(parsed, dedup=True, compression=None)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == original


# ============================================================================
# §10 — Edge cases & regression guards
# ============================================================================


class TestEdgeCases:
    """Boundary conditions and regression guards."""

    @pytest.mark.asyncio
    async def test_surp_then_json_separate_caches(self):
        """surp() and json() use separate caches."""
        surp_body = _surp_mod.encode({"source": "surp"})
        req = _make_request(body=surp_body, content_type="application/x-surp")
        surp_result = await req.surp()
        assert surp_result == {"source": "surp"}
        # JSON cache should still be None
        assert req._json is None

    def test_has_surp_function(self):
        from aquilia.response import has_surp

        assert has_surp() is True

    def test_has_surp_when_unavailable(self):
        from aquilia.response import has_surp

        with patch("aquilia.response._HAS_SURP", False):
            assert has_surp() is False

    def test_surp_media_type_constant(self):
        from aquilia.request import SURP_MEDIA_TYPE
        from aquilia.response import SURP_MEDIA_TYPE as RESP_SURP_MT

        assert SURP_MEDIA_TYPE == "application/x-surp"
        assert RESP_SURP_MT == "application/x-surp"

    @pytest.mark.asyncio
    async def test_binary_bytes_in_dict(self):
        """SURP supports bytes values natively."""
        from aquilia.response import Response

        original = {"binary": b"\x00\x01\x02\xff"}
        wire = _surp_mod.encode(original)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        assert parsed["binary"] == b"\x00\x01\x02\xff"

        resp = Response.surp(parsed)
        decoded = _surp_mod.decode(resp._content)
        assert decoded["binary"] == b"\x00\x01\x02\xff"

    def test_surp_media_types_frozenset(self):
        from aquilia.request import SURP_MEDIA_TYPES

        assert isinstance(SURP_MEDIA_TYPES, frozenset)
        assert len(SURP_MEDIA_TYPES) == 3

    @pytest.mark.asyncio
    async def test_deeply_nested_structure(self):
        """Deep nesting should encode/decode correctly."""

        data: Any = "leaf"
        for _ in range(20):
            data = {"nested": data}

        wire = _surp_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()

        # Traverse 20 levels
        node = parsed
        for _ in range(20):
            assert "nested" in node
            node = node["nested"]
        assert node == "leaf"

    def test_response_surp_invalid_compression_ignored(self):
        """Unknown compression name should not crash."""
        from aquilia.response import Response

        resp = Response.surp({"test": True}, compression="unknown_algo")
        # Should still produce valid SURP (no compression applied)
        decoded = _surp_mod.decode(resp._content)
        assert decoded == {"test": True}

    @pytest.mark.asyncio
    async def test_negative_integers(self):

        data = {"neg": -42, "zero": 0, "pos": 100}
        wire = _surp_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        assert parsed == data

    @pytest.mark.asyncio
    async def test_mixed_type_list(self):
        data = [1, "two", 3.0, True, None, {"nested": "yes"}]
        wire = _surp_mod.encode(data)
        req = _make_request(body=wire, content_type="application/x-surp")
        parsed = await req.surp()
        assert parsed == data

    def test_response_surp_preserves_insertion_order(self):
        from collections import OrderedDict

        from aquilia.response import Response

        data = OrderedDict([("z", 1), ("a", 2), ("m", 3)])
        resp = Response.surp(data)
        decoded = _surp_mod.decode(resp._content)
        assert list(decoded.keys()) == ["z", "a", "m"]


class TestModuleExports:
    """Verify SURP symbols are properly exported."""

    def test_response_exports(self):
        from aquilia.response import __all__

        assert "SURP_MEDIA_TYPE" in __all__
        assert "has_surp" in __all__
        assert "requires_surp" in __all__

    def test_request_importable(self):
        from aquilia.request import (
            SURP_MEDIA_TYPE,
            InvalidSurp,
            SurpUnavailable,
        )

        assert SURP_MEDIA_TYPE == "application/x-surp"
        assert InvalidSurp is not None
        assert SurpUnavailable is not None
