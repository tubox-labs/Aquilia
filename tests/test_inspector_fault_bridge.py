import time

from aquilia.faults.core import Fault
from aquilia.faults.engine import FaultEngine
from aquilia.inspector.fault_bridge import get_fault_listener
from aquilia.inspector.trace import Lane, RequestTrace, SpanStatus, _reset_current_trace, _set_current_trace


class DummyFault(Fault):
    pass


def test_fault_bridge_populates_trace():
    engine = FaultEngine()
    listener = get_fault_listener(None)
    engine.on_fault(listener)

    trace = RequestTrace(
        trace_id="trace-fault-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )

    token = _set_current_trace(trace)
    try:
        # Process a fault
        exc = ValueError("something failed")
        # Run process synchronously
        import asyncio

        asyncio.run(engine.process(exc, app="my-app", route="/my-route", request_id="trace-fault-1"))

        # Verify trace exception is populated
        assert trace.exception is not None
        assert trace.exception.exception_type == "ValueError"
        assert "something failed" in trace.exception.message

        # Verify Exception span is added
        assert len(trace.spans) == 1
        span = trace.spans[0]
        assert span.lane == Lane.EXCEPTION
        assert span.status == SpanStatus.ERROR
        assert span.duration_ms == 0.0
    finally:
        _reset_current_trace(token)


def test_fault_bridge_no_active_trace():
    engine = FaultEngine()
    listener = get_fault_listener(None)
    engine.on_fault(listener)

    # Process without active trace, should not raise
    exc = ValueError("no trace error")
    import asyncio

    asyncio.run(engine.process(exc, app="my-app", route="/my-route"))
