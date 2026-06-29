import pytest

from aquilia.inspector.stream import SSEStreamManager
from aquilia.inspector.trace import RequestTrace


@pytest.mark.asyncio
async def test_sse_stream_manager_fan_out():
    manager = SSEStreamManager()

    # Register clients
    q1 = manager.register_client()
    q2 = manager.register_client()

    assert len(manager._queues) == 2

    # Publish trace
    trace = RequestTrace(
        trace_id="t-stream-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=100.0,
        started_monotonic=200.0,
    )
    manager.publish_trace(trace)

    # Both queues should receive the trace dict
    data1 = q1.get_nowait()
    data2 = q2.get_nowait()
    assert data1["trace_id"] == "t-stream-1"
    assert data2["trace_id"] == "t-stream-1"

    # Unregister client
    manager.unregister_client(q1)
    assert len(manager._queues) == 1
    assert q1 not in manager._queues


@pytest.mark.asyncio
async def test_sse_stream_generator():
    manager = SSEStreamManager()
    q = manager.register_client()

    trace = RequestTrace(
        trace_id="t-stream-2",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=100.0,
        started_monotonic=200.0,
    )
    manager.publish_trace(trace)

    # Use the generator
    gen = manager.event_generator(q)
    # Get first item
    data = await anext(gen)
    assert data["trace_id"] == "t-stream-2"
