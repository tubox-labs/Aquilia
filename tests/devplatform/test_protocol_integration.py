"""Integration tests: ADP protocol handler ↔ runtime store ↔ Inspector."""

from __future__ import annotations

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.protocol import ADPProtocolHandler, redact_body_preview
from aquilia.devplatform.logging import LogMode, get_router

from .conftest import drive_http, make_asgi_boom, make_asgi_echo


@pytest.fixture
def cfg():
    return AquiliaDevelopmentConfig(host="127.0.0.1", port=8000, reload=False, n_plus_one_detection=False)


class TestProtocolInstrumentation:
    async def test_records_successful_request(self, cfg, runtime):
        handler = ADPProtocolHandler(make_asgi_echo(200, b"hi"), cfg, runtime)
        status, _, body = await drive_http(handler, "GET", "/x")
        assert status == 200 and body == b"hi"
        s = runtime.snapshot()
        assert s.total_requests == 1 and s.total_errors == 0

    async def test_counts_500_as_error(self, cfg, runtime):
        handler = ADPProtocolHandler(make_asgi_echo(503, b"err"), cfg, runtime)
        await drive_http(handler, "GET", "/e")
        assert runtime.snapshot().total_errors == 1

    async def test_exception_propagates_and_records(self, cfg, runtime):
        handler = ADPProtocolHandler(make_asgi_boom(), cfg, runtime)
        with pytest.raises(RuntimeError):
            await drive_http(handler, "GET", "/boom")
        # connection counter returns to zero even on exception
        assert runtime.snapshot().active_connections == 0

    async def test_request_emitted_to_inspector(self, cfg, runtime):
        get_router().install(mode=LogMode.INSPECTOR)
        handler = ADPProtocolHandler(make_asgi_echo(200, b"ok"), cfg, runtime)
        await drive_http(handler, "POST", "/submit")
        reqs = get_router().events(kind="request")
        assert reqs and "POST /submit 200" in reqs[-1].message

    async def test_connection_counter_balanced(self, cfg, runtime):
        handler = ADPProtocolHandler(make_asgi_echo(), cfg, runtime)
        for _ in range(5):
            await drive_http(handler, "GET", "/")
        assert runtime.snapshot().active_connections == 0


class TestRedaction:
    def test_bearer_scrubbed(self):
        out = redact_body_preview(b'{"token": "Bearer abc123secret"}')
        assert "abc123secret" not in out and "REDACTED" in out

    def test_empty_none(self):
        assert redact_body_preview(b"") is None

    def test_capped(self):
        out = redact_body_preview(b"y" * 5000, limit=50)
        assert len(out) <= 52
