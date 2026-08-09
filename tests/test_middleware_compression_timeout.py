"""Tests for the compression and timeout middleware.

Both were minimal implementations that worked on the happy path and misbehaved
around the edges. These pin down the edges.
"""

from __future__ import annotations

import asyncio

import pytest

from aquilia.middleware.builtin.compression import (
    CompressionMiddleware,
    parse_accept_encoding,
)
from aquilia.middleware.builtin.timeout import TimeoutMiddleware
from aquilia.response import Response


def _request(path="/", headers=None, method="GET"):
    class _Req:
        def __init__(self):
            self.state: dict = {}
            self.scope: dict = {"headers": []}
            self.method = method
            self.path = path
            self._headers = {k.lower(): v for k, v in (headers or {}).items()}

        def header(self, name, default=None):
            return self._headers.get(name.lower(), default)

    return _Req()


def _ctx():
    class _Ctx:
        def __init__(self):
            self.state: dict = {}
            self.request_id = None

    return _Ctx()


def _text(body: str, content_type="text/plain", **headers) -> Response:
    return Response(content=body, headers={"content-type": content_type, **headers})


# ── Accept-Encoding parsing ──────────────────────────────────────────────────


class TestAcceptEncodingParsing:
    def test_plain_tokens(self):
        assert parse_accept_encoding("gzip, deflate") == {"gzip": 1.0, "deflate": 1.0}

    def test_quality_values(self):
        parsed = parse_accept_encoding("gzip;q=0.5, br;q=1.0")
        assert parsed == {"gzip": 0.5, "br": 1.0}

    def test_zero_quality_is_preserved_not_dropped(self):
        """q=0 means 'refuse'; conflating it with absent loses that."""
        assert parse_accept_encoding("gzip;q=0")["gzip"] == 0.0

    def test_malformed_quality_defaults_to_one(self):
        assert parse_accept_encoding("gzip;q=banana")["gzip"] == 1.0

    def test_empty_and_whitespace(self):
        assert parse_accept_encoding("") == {}
        assert parse_accept_encoding("  ,  ") == {}


class TestEncodingSelection:
    def test_gzip_when_only_gzip_offered(self):
        assert CompressionMiddleware().select_encoding("gzip") == "gzip"

    def test_explicit_refusal_is_honoured(self):
        """Substring matching read 'gzip;q=0' as acceptance and sent gzip."""
        assert CompressionMiddleware().select_encoding("gzip;q=0") is None

    def test_higher_quality_wins(self):
        assert CompressionMiddleware().select_encoding("br;q=0.1, gzip;q=0.9") == "gzip"

    def test_identity_only_selects_nothing(self):
        assert CompressionMiddleware().select_encoding("identity") is None

    def test_unknown_encoding_selects_nothing(self):
        assert CompressionMiddleware().select_encoding("exotic-codec") is None

    def test_empty_header_selects_nothing(self):
        assert CompressionMiddleware().select_encoding("") is None


# ── Eligibility ──────────────────────────────────────────────────────────────


class TestEligibility:
    def test_text_types_are_compressible(self):
        assert CompressionMiddleware().should_compress(_text("x", "text/html")) is True

    def test_json_is_compressible(self):
        assert CompressionMiddleware().should_compress(_text("{}", "application/json")) is True

    def test_already_compressed_types_are_skipped(self):
        mw = CompressionMiddleware()
        for ct in ("image/jpeg", "video/mp4", "application/zip", "image/png"):
            assert mw.should_compress(_text("x", ct)) is False, ct

    def test_already_encoded_response_is_not_recompressed(self):
        response = _text("x", "text/plain")
        response.headers["content-encoding"] = "gzip"
        assert CompressionMiddleware().should_compress(response) is False

    def test_no_transform_is_honoured(self):
        response = _text("x", "text/plain")
        response.headers["cache-control"] = "public, no-transform"
        assert CompressionMiddleware().should_compress(response) is False

    def test_bodiless_statuses_are_skipped(self):
        for status in (204, 304):
            response = Response(content="", status=status, headers={"content-type": "text/plain"})
            assert CompressionMiddleware().should_compress(response) is False, status

    def test_unknown_content_type_is_skipped(self):
        """Only text/* and the allow-list are compressed; anything else is
        assumed already-compressed or not worth the CPU."""
        assert CompressionMiddleware().should_compress(_text("x", "application/octet-stream")) is False

    def test_content_type_parameters_are_ignored(self):
        response = _text("x", "text/html; charset=utf-8")
        assert CompressionMiddleware().should_compress(response) is True


# ── End-to-end compression ───────────────────────────────────────────────────


class TestCompressionBehaviour:
    async def test_large_body_is_compressed(self):
        mw = CompressionMiddleware(minimum_size=10)
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip"}),
            _ctx(),
            _text("hello " * 500),
        )
        assert response.headers["content-encoding"] == "gzip"
        assert response.headers["vary"] == "Accept-Encoding"
        assert int(response.headers["content-length"]) == len(response._content)

    async def test_small_body_is_not_compressed_but_still_varies(self):
        """Vary must be set whenever compression was *considered*, or a shared
        cache can serve a compressed body to a client that cannot decode it."""
        mw = CompressionMiddleware(minimum_size=10_000)
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip"}),
            _ctx(),
            _text("small"),
        )
        assert "content-encoding" not in response.headers
        assert response.headers["vary"] == "Accept-Encoding"

    async def test_incompressible_body_is_left_alone(self):
        """Random bytes grow under gzip; sending the larger body is a loss."""
        import os

        mw = CompressionMiddleware(minimum_size=10)
        payload = os.urandom(2048).hex()[:64]
        response = _text(payload, "text/plain")
        # Force the grow-check by making the body tiny but above the threshold.
        result = await mw.after(_request(headers={"accept-encoding": "gzip"}), _ctx(), response)
        if "content-encoding" in result.headers:
            assert len(result._content) < len(payload.encode())

    async def test_client_refusing_gzip_gets_plain_body(self):
        mw = CompressionMiddleware(minimum_size=10)
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip;q=0"}),
            _ctx(),
            _text("hello " * 500),
        )
        assert "content-encoding" not in response.headers

    async def test_no_accept_encoding_header(self):
        mw = CompressionMiddleware(minimum_size=10)
        response = await mw.after(_request(), _ctx(), _text("hello " * 500))
        assert "content-encoding" not in response.headers

    async def test_strong_etag_is_weakened(self):
        """A strong ETag identifies bytes; compressed bytes differ (RFC 9110)."""
        mw = CompressionMiddleware(minimum_size=10)
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip"}),
            _ctx(),
            _text("hello " * 500, etag='"abc123"'),
        )
        assert response.headers["etag"] == 'W/"abc123"'

    async def test_weak_etag_is_left_alone(self):
        mw = CompressionMiddleware(minimum_size=10)
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip"}),
            _ctx(),
            _text("hello " * 500, etag='W/"abc123"'),
        )
        assert response.headers["etag"] == 'W/"abc123"'

    async def test_compressed_body_round_trips(self):
        import gzip

        mw = CompressionMiddleware(minimum_size=10)
        original = "round trip " * 200
        response = await mw.after(
            _request(headers={"accept-encoding": "gzip"}),
            _ctx(),
            _text(original),
        )
        assert gzip.decompress(response._content).decode() == original


# ── Timeout ──────────────────────────────────────────────────────────────────


class TestTimeoutResolution:
    def test_default_applies_everywhere(self):
        assert TimeoutMiddleware(5.0).resolve_timeout(_request("/anything")) == 5.0

    def test_per_path_override(self):
        mw = TimeoutMiddleware(5.0, per_path={"/api/export": 120.0})
        assert mw.resolve_timeout(_request("/api/export/csv")) == 120.0
        assert mw.resolve_timeout(_request("/api/users")) == 5.0

    def test_longest_prefix_wins(self):
        mw = TimeoutMiddleware(5.0, per_path={"/api": 10.0, "/api/export": 120.0})
        assert mw.resolve_timeout(_request("/api/export/csv")) == 120.0
        assert mw.resolve_timeout(_request("/api/users")) == 10.0

    def test_exempt_paths_return_none(self):
        mw = TimeoutMiddleware(5.0, exempt=("/events", "/ws"))
        assert mw.resolve_timeout(_request("/events/stream")) is None
        assert mw.resolve_timeout(_request("/api")) == 5.0

    def test_resolver_takes_precedence_over_per_path(self):
        mw = TimeoutMiddleware(5.0, per_path={"/api": 10.0}, resolver=lambda r: 99.0)
        assert mw.resolve_timeout(_request("/api/x")) == 99.0

    def test_resolver_returning_none_falls_through(self):
        mw = TimeoutMiddleware(5.0, per_path={"/api": 10.0}, resolver=lambda r: None)
        assert mw.resolve_timeout(_request("/api/x")) == 10.0


class TestTimeoutBehaviour:
    async def test_fast_handler_passes_through(self):
        async def fast(request, ctx):
            return Response.json({"ok": True})

        response = await TimeoutMiddleware(1.0).handle(_request(), _ctx(), fast)
        assert response.status == 200

    async def test_slow_handler_raises_request_timeout_fault(self):
        from aquilia.faults.domains import RequestTimeoutFault

        async def slow(request, ctx):
            await asyncio.sleep(5)

        with pytest.raises(RequestTimeoutFault) as exc:
            await TimeoutMiddleware(0.05).handle(_request(), _ctx(), slow)
        assert exc.value.status == 408

    async def test_exempt_path_is_never_timed_out(self):
        async def slow(request, ctx):
            await asyncio.sleep(0.1)
            return Response.json({"ok": True})

        mw = TimeoutMiddleware(0.01, exempt=("/events",))
        response = await mw.handle(_request("/events/stream"), _ctx(), slow)
        assert response.status == 200

    async def test_deadline_is_published_to_the_handler(self):
        seen: dict = {}

        async def handler(request, ctx):
            seen["budget"] = request.state.get("timeout_budget")
            seen["deadline"] = request.state.get("deadline")
            return Response.json({"ok": True})

        await TimeoutMiddleware(7.5).handle(_request(), _ctx(), handler)
        assert seen["budget"] == 7.5
        assert seen["deadline"] > 0

    async def test_cancellation_propagates_as_cancellation(self):
        """A client disconnect must not be reported as a 408."""

        async def cancelled(request, ctx):
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await TimeoutMiddleware(10.0).handle(_request(), _ctx(), cancelled)

    async def test_handler_exceptions_are_not_swallowed(self):
        async def boom(request, ctx):
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await TimeoutMiddleware(10.0).handle(_request(), _ctx(), boom)
