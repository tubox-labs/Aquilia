import pytest

from aquilia.controller.base import RequestCtx
from aquilia.inspector.collector import get_collector, reset_global_collector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.middleware import InspectorMiddleware
from aquilia.request import Request
from aquilia.response import Response


@pytest.mark.asyncio
async def test_inspector_middleware_happy_path():
    reset_global_collector()
    config = InspectorConfig(capture_client_addr=True)
    collector = get_collector(config)
    middleware = InspectorMiddleware(config)

    # Mock request
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/test-path",
            "query_string": b"foo=bar",
            "headers": [
                (b"host", b"localhost"),
                (b"content-type", b"application/json"),
                (b"authorization", b"Bearer token123"),
            ],
            "client": ("127.0.0.1", 12345),
        },
        receive=None,
    )
    request._body = b'{"password": "secret", "user": "john"}'

    ctx = RequestCtx(request=request, request_id="req-1")

    async def next_handler(req, context):
        return Response.json({"status": "ok"}, status=200)

    response = await middleware(request, ctx, next_handler)
    assert response.status == 200

    # Verify trace
    traces = collector.list_recent()
    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == "req-1"
    assert trace.method == "POST"
    assert trace.path == "/test-path"
    assert trace.client_addr == "127.0.0.1"

    # Verify redaction before storage
    assert trace.request_headers["authorization"] == "***REDACTED***"
    assert "password" in trace.request_body_preview
    assert "secret" not in trace.request_body_preview
    assert "***REDACTED***" in trace.request_body_preview


@pytest.mark.asyncio
async def test_inspector_middleware_exception_path():
    reset_global_collector()
    config = InspectorConfig()
    collector = get_collector(config)
    middleware = InspectorMiddleware(config)

    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/error-path",
            "query_string": b"",
            "headers": [],
        },
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-2")

    async def next_handler(req, context):
        raise ValueError("Handler failed")

    with pytest.raises(ValueError, match="Handler failed"):
        await middleware(request, ctx, next_handler)

    # Verify trace got saved and contains exception details
    traces = collector.list_recent()
    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == "req-2"
    assert trace.exception is not None
    assert trace.exception.exception_type == "ValueError"
    assert trace.exception.message == "Handler failed"
