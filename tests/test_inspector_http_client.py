import time

import pytest

from aquilia.http import AsyncHTTPClient, MockTransport, create_response
from aquilia.inspector.http_hook import InspectorHTTPClientMiddleware
from aquilia.inspector.trace import Lane, RequestTrace, SpanStatus, _reset_current_trace, _set_current_trace


@pytest.mark.asyncio
async def test_http_client_middleware_records_span():
    # Instantiate client with mock transport and our middleware
    transport = MockTransport()
    transport.add_response(
        "GET",
        "https://example.com/api",
        create_response(status_code=200, body=b"OK"),
    )

    client = AsyncHTTPClient(transport=transport)
    client.middleware.add(InspectorHTTPClientMiddleware())

    trace = RequestTrace(
        trace_id="trace-http-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )

    token = _set_current_trace(trace)
    try:
        response = await client.get("https://example.com/api")
        assert response.status_code == 200

        # Verify trace has external_http span
        assert len(trace.spans) == 1
        span = trace.spans[0]
        assert span.lane == Lane.EXTERNAL_HTTP
        assert "GET https://example.com/api" in span.label
        assert span.status == SpanStatus.OK
        assert span.detail["status"] == 200
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_http_client_middleware_records_error_span():
    transport = MockTransport()
    transport.add_response(
        "POST",
        "https://example.com/fail",
        create_response(status_code=500, body=b"Error"),
    )

    client = AsyncHTTPClient(transport=transport)
    client.middleware.add(InspectorHTTPClientMiddleware())

    trace = RequestTrace(
        trace_id="trace-http-2",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )

    token = _set_current_trace(trace)
    try:
        response = await client.post("https://example.com/fail")
        assert response.status_code == 500

        assert len(trace.spans) == 1
        span = trace.spans[0]
        assert span.lane == Lane.EXTERNAL_HTTP
        assert span.status == SpanStatus.ERROR
        assert span.detail["status"] == 500
    finally:
        _reset_current_trace(token)
