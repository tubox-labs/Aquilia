import pytest

from aquilia.controller.base import RequestCtx
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.toolbar import ToolbarInjectionMiddleware
from aquilia.inspector.trace import RequestTrace, _reset_current_trace, _set_current_trace
from aquilia.request import Request
from aquilia.response import Response


def _get_body_str(response) -> str:
    content = response._content
    if isinstance(content, bytes):
        return content.decode("utf-8")
    return str(content)


@pytest.mark.asyncio
async def test_toolbar_injected_in_html():
    config = InspectorConfig(enabled=True, toolbar_enabled=True)
    middleware = ToolbarInjectionMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-1")

    trace = RequestTrace(
        trace_id="req-1",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    async def next_handler(req, context):
        return Response(
            content=b"<html><body><h1>Hello</h1></body></html>",
            headers={"content-type": "text/html; charset=utf-8"},
        )

    try:
        response = await middleware(request, ctx, next_handler)
        assert response.status == 200
        body = _get_body_str(response)
        assert "aq-tab" in body
        assert "aq-panel" in body
        assert "aq-toolbar-data" in body
        assert response.headers["content-length"] == str(len(response._content))
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_toolbar_not_injected_in_json():
    config = InspectorConfig(enabled=True, toolbar_enabled=True)
    middleware = ToolbarInjectionMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/api/users",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-2")

    trace = RequestTrace(
        trace_id="req-2",
        method="GET",
        path="/api/users",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    async def next_handler(req, context):
        return Response.json({"status": "ok"})

    try:
        response = await middleware(request, ctx, next_handler)
        body = _get_body_str(response)
        assert "aq-tab" not in body
        assert "aq-panel" not in body
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_toolbar_not_injected_in_redirect():
    config = InspectorConfig(enabled=True, toolbar_enabled=True)
    middleware = ToolbarInjectionMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/old-path",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-3")

    trace = RequestTrace(
        trace_id="req-3",
        method="GET",
        path="/old-path",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    async def next_handler(req, context):
        return Response(
            content=b"Redirecting...",
            status=302,
            headers={"content-type": "text/html", "location": "/new-path"},
        )

    try:
        response = await middleware(request, ctx, next_handler)
        body = _get_body_str(response)
        assert "aq-tab" not in body
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_toolbar_not_injected_if_disabled():
    config = InspectorConfig(enabled=True, toolbar_enabled=False)
    middleware = ToolbarInjectionMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-4")

    trace = RequestTrace(
        trace_id="req-4",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    async def next_handler(req, context):
        return Response(
            content=b"<html><body><h1>Hello</h1></body></html>",
            headers={"content-type": "text/html"},
        )

    try:
        response = await middleware(request, ctx, next_handler)
        body = _get_body_str(response)
        assert "aq-tab" not in body
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_toolbar_not_injected_no_body_tag():
    config = InspectorConfig(enabled=True, toolbar_enabled=True)
    middleware = ToolbarInjectionMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/index",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-5")

    trace = RequestTrace(
        trace_id="req-5",
        method="GET",
        path="/index",
        route_pattern=None,
        started_at=1.0,
        started_monotonic=1.0,
    )
    token = _set_current_trace(trace)

    async def next_handler(req, context):
        return Response(
            content=b"<h1>Hello</h1>",
            headers={"content-type": "text/html"},
        )

    try:
        response = await middleware(request, ctx, next_handler)
        body = _get_body_str(response)
        assert "aq-tab" not in body
    finally:
        _reset_current_trace(token)
