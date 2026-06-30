import pytest

from aquilia.controller.base import RequestCtx
from aquilia.inspector.collector import get_collector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.middleware import InspectorMiddleware
from aquilia.request import Request
from aquilia.response import Response


def test_sampling_rate_default_is_one():
    config = InspectorConfig()
    assert config.sampling_rate == 1.0


@pytest.mark.asyncio
async def test_sampling_rate_zero_skips_tracing():
    config = InspectorConfig(enabled=True, sampling_rate=0.0)
    middleware = InspectorMiddleware(config)
    collector = get_collector(config)

    request = Request(
        scope={"type": "http", "method": "GET", "path": "/index", "headers": [], "query_string": b""},
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-sample-skip")

    async def handler(req, context):
        return Response(b"ok")

    await middleware(request, ctx, handler)

    trace = collector.get("req-sample-skip")
    assert trace is None


@pytest.mark.asyncio
async def test_sampling_rate_one_traces_all():
    config = InspectorConfig(enabled=True, sampling_rate=1.0)
    middleware = InspectorMiddleware(config)
    collector = get_collector(config)

    request = Request(
        scope={"type": "http", "method": "GET", "path": "/index", "headers": [], "query_string": b""},
        receive=None,
    )
    ctx = RequestCtx(request=request, request_id="req-sample-traced")

    async def handler(req, context):
        return Response(b"ok")

    await middleware(request, ctx, handler)

    trace = collector.get("req-sample-traced")
    assert trace is not None
    assert trace.trace_id == "req-sample-traced"
