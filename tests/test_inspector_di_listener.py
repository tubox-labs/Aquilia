import time

import pytest

from aquilia.di.core import Container
from aquilia.di.diagnostics import DIEvent, DIEventType
from aquilia.inspector.di_listener import InspectorDiagnosticListener
from aquilia.inspector.trace import Lane, RequestTrace, SpanStatus, _reset_current_trace, _set_current_trace


def test_listener_filters_events():
    listener = InspectorDiagnosticListener()
    trace = RequestTrace(
        trace_id="req-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _set_current_trace(trace)
    try:
        # Should ignore REGISTRATION event
        reg_event = DIEvent(
            type=DIEventType.REGISTRATION,
            provider_name="MyProvider",
            token="my_token",
        )
        listener.on_event(reg_event)
        assert len(trace.spans) == 0

        # Should record RESOLUTION_SUCCESS
        succ_event = DIEvent(
            type=DIEventType.RESOLUTION_SUCCESS,
            provider_name="MyProvider",
            token="my_token",
            duration=0.005,  # 5ms
        )
        listener.on_event(succ_event)
        assert len(trace.spans) == 1
        span = trace.spans[0]
        assert span.lane == Lane.DEPENDENCY
        assert span.label == "MyProvider"
        assert span.duration_ms == 5.0
        assert span.status == SpanStatus.OK

        # Should record RESOLUTION_FAILURE
        err = ValueError("resolution failed")
        fail_event = DIEvent(
            type=DIEventType.RESOLUTION_FAILURE,
            provider_name="MyProvider",
            token="my_token",
            duration=0.002,  # 2ms
            error=err,
        )
        listener.on_event(fail_event)
        assert len(trace.spans) == 2
        span2 = trace.spans[1]
        assert span2.status == SpanStatus.ERROR
        assert span2.detail["error"] == "resolution failed"
    finally:
        _reset_current_trace(token)


def test_listener_no_active_trace():
    listener = InspectorDiagnosticListener()
    # No current trace
    succ_event = DIEvent(
        type=DIEventType.RESOLUTION_SUCCESS,
        provider_name="MyProvider",
        token="my_token",
        duration=0.005,
    )
    # Should not raise exception
    listener.on_event(succ_event)


@pytest.mark.asyncio
async def test_listener_registered_on_app_container_sees_request_scope_events():
    container = Container(scope="app")
    listener = InspectorDiagnosticListener()
    container.add_diagnostic_listener(listener)

    # Create request scope child
    child = container.create_request_scope()

    # Verify diagnostics is shared
    assert child._diagnostics is container._diagnostics

    # Emit event on child container
    trace = RequestTrace(
        trace_id="req-2",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _set_current_trace(trace)
    try:
        child._diagnostics.emit(
            DIEventType.RESOLUTION_SUCCESS,
            provider_name="RequestScopedService",
            token="service_token",
            duration=0.003,
        )
        assert len(trace.spans) == 1
        assert trace.spans[0].label == "RequestScopedService"
    finally:
        _reset_current_trace(token)
