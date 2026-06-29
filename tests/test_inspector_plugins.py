import time

import pytest

from aquilia.inspector.plugins import _CUSTOM_LANES, register_lane, span
from aquilia.inspector.trace import RequestTrace, SpanStatus, _reset_current_trace, _set_current_trace


def test_custom_lane_registration():
    register_lane("my-custom-lane", "My Custom Lane")
    assert _CUSTOM_LANES["my-custom-lane"] == "My Custom Lane"


def test_span_context_manager_happy_path():
    trace = RequestTrace(
        trace_id="t-plugin-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _set_current_trace(trace)
    try:
        with span(lane="my-custom-lane", label="custom-operation", detail={"some": "metadata"}):
            # simulate work
            time.sleep(0.005)

        assert len(trace.spans) == 1
        s = trace.spans[0]
        assert s.lane == "my-custom-lane"
        assert s.label == "custom-operation"
        assert s.status == SpanStatus.OK
        assert s.detail["some"] == "metadata"
        assert s.duration_ms >= 5.0
    finally:
        _reset_current_trace(token)


def test_span_context_manager_raises_exception():
    trace = RequestTrace(
        trace_id="t-plugin-2",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _set_current_trace(trace)
    try:
        with pytest.raises(ValueError, match="fail inside"), span(lane="custom", label="fail-operation"):
            raise ValueError("fail inside")

        assert len(trace.spans) == 1
        s = trace.spans[0]
        assert s.status == SpanStatus.ERROR
        assert s.detail["error"] == "fail inside"
    finally:
        _reset_current_trace(token)


def test_span_context_manager_no_active_trace():
    # Outside active trace, should simply yield and execute block
    called = False
    with span(lane="custom", label="noop"):
        called = True
    assert called
