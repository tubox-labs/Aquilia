import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from aquilia.controller.base import RequestCtx
from aquilia.db.engine import AquiliaDatabase
from aquilia.inspector.collector import get_collector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.middleware import InspectorMiddleware
from aquilia.inspector.toolbar import ToolbarInjectionMiddleware
from aquilia.inspector.trace import Lane, RequestTrace, _reset_current_trace, _set_current_trace
from aquilia.request import Request
from aquilia.response import Response


@pytest.mark.asyncio
async def test_slow_query_explain_plan():
    # Setup test trace
    trace = RequestTrace(
        trace_id="req-explain",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    try:
        # Mock database adapter
        mock_adapter = MagicMock()
        mock_adapter.dialect = "sqlite"
        mock_adapter.execute = AsyncMock(return_value=MagicMock(rowcount=1))
        # explain response
        mock_explain_row = MagicMock()
        mock_explain_row.__str__ = MagicMock(return_value="SCAN TABLE users")
        mock_adapter.fetch_all = AsyncMock(return_value=[mock_explain_row])

        db = AquiliaDatabase(url="sqlite:///:memory:", adapter=mock_adapter)
        db._adapter = mock_adapter

        # Run slow SELECT query (duration >= 50ms) to trigger explain plan
        db._notify_inspector("SELECT * FROM users", [], 60.0, 1, "User", db=db)

        # Wait a tiny bit for background task to resolve explain
        await asyncio.sleep(0.05)

        db_spans = [s for s in trace.spans if s.lane == Lane.DATABASE]
        assert len(db_spans) == 1
        span = db_spans[0]
        assert span.detail["explain_plan"] == "SCAN TABLE users"
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_cprofile_request_profiling():
    config = InspectorConfig(enabled=True)
    middleware = InspectorMiddleware(config)

    # 1. Without profile header/param
    request_normal = Request(
        scope={"type": "http", "method": "GET", "path": "/index", "headers": [], "query_string": b""},
        receive=None,
    )
    ctx_normal = RequestCtx(request=request_normal, request_id="req-normal")

    async def handler(req, context):
        return Response(b"ok")

    await middleware(request_normal, ctx_normal, handler)

    from aquilia.inspector.collector import get_collector

    trace_normal = get_collector(config).get("req-normal")
    assert trace_normal.profile_stats is None

    # 2. With profile query param
    request_param = Request(
        scope={"type": "http", "method": "GET", "path": "/index", "headers": [], "query_string": b"profile=true"},
        receive=None,
    )
    ctx_param = RequestCtx(request=request_param, request_id="req-profile-param")

    await middleware(request_param, ctx_param, handler)
    trace_param = get_collector(config).get("req-profile-param")
    assert trace_param.profile_stats is not None
    assert "function calls" in trace_param.profile_stats

    # 3. With profile header
    request_header = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [(b"x-profile", b"true")],
            "query_string": b"",
        },
        receive=None,
    )
    ctx_header = RequestCtx(request=request_header, request_id="req-profile-header")

    await middleware(request_header, ctx_header, handler)
    trace_header = get_collector(config).get("req-profile-header")
    assert trace_header.profile_stats is not None
    assert "function calls" in trace_header.profile_stats


@pytest.mark.asyncio
async def test_redirect_folding_in_toolbar():
    config = InspectorConfig(enabled=True)
    injection_middleware = ToolbarInjectionMiddleware(config)
    collector = get_collector(config)

    # First request: Redirect (302)
    trace_redir = RequestTrace("req-redir", "POST", "/login", None, 1.0, 1.0)
    trace_redir.finished_monotonic = 1.05
    collector.commit(trace_redir)

    token = _set_current_trace(trace_redir)
    try:
        req_redir = Request(
            scope={"type": "http", "method": "POST", "path": "/login", "headers": []},
            receive=None,
        )
        ctx_redir = RequestCtx(request=req_redir, request_id="req-redir")

        async def handler_redir(req, context):
            return Response(b"Redirecting...", status=302)

        res_redir = await injection_middleware(req_redir, ctx_redir, handler_redir)
        # Check redirect cookie is set
        cookie_header = res_redir.headers.get("set-cookie", "")
        assert "aq_redirect_traces=req-redir" in cookie_header
    finally:
        _reset_current_trace(token)

    # Second request: Landing Page (200 HTML)
    trace_landing = RequestTrace("req-landing", "GET", "/dashboard", None, 2.0, 2.0)
    trace_landing.finished_monotonic = 2.05
    collector.commit(trace_landing)

    token = _set_current_trace(trace_landing)
    try:
        req_landing = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/dashboard",
                "headers": [(b"cookie", b"aq_redirect_traces=req-redir")],
            },
            receive=None,
        )
        ctx_landing = RequestCtx(request=req_landing, request_id="req-landing")

        async def handler_landing(req, context):
            return Response(
                b"<html><body><h1>Dashboard</h1></body></html>", status=200, headers={"content-type": "text/html"}
            )

        res_landing = await injection_middleware(req_landing, ctx_landing, handler_landing)
        assert res_landing.status == 200

        # Check aq-toolbar-data payload in response body contains the redirect history
        body = res_landing._content.decode()
        assert "aq-toolbar-data" in body

        # Parse payload
        tag_idx = body.find('id="aq-toolbar-data"')
        start_idx = body.find(">", tag_idx) + 1
        end_idx = body.find("</script>", start_idx)
        payload_str = body[start_idx:end_idx]
        payload = json.loads(payload_str)

        assert payload["trace"]["trace_id"] == "req-landing"
        assert len(payload["redirect_history"]) == 1
        assert payload["redirect_history"][0]["trace_id"] == "req-redir"
        assert payload["redirect_history"][0]["path"] == "/login"
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_opentelemetry_correlation():
    # Mock opentelemetry trace get_current_span
    mock_span = MagicMock()
    mock_span.get_span_context = MagicMock(
        return_value=MagicMock(is_valid=True, trace_id=12345678901234567890123456789012, span_id=9876543210123456)
    )

    # Patch sys.modules to mock opentelemetry trace
    import sys
    from types import ModuleType

    otel_mock = ModuleType("opentelemetry")
    otel_mock.trace = MagicMock()
    otel_mock.trace.get_current_span = MagicMock(return_value=mock_span)
    sys.modules["opentelemetry"] = otel_mock

    config = InspectorConfig(enabled=True)
    middleware = InspectorMiddleware(config)

    request = Request(
        scope={"type": "http", "method": "GET", "path": "/index", "headers": []},
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-otel")

    async def next_handler(req, context):
        return Response(b"ok")

    await middleware(request, ctx, next_handler)

    from aquilia.inspector.collector import get_collector

    trace = get_collector(config).get("req-otel")
    assert trace is not None
    assert trace.otel_trace_id == f"{12345678901234567890123456789012:032x}"
    assert trace.otel_span_id == f"{9876543210123456:016x}"

    # Clean up sys.modules
    del sys.modules["opentelemetry"]
