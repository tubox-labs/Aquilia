import time

from aquilia.inspector.trace import ExceptionNode, Lane, RequestTrace, ResponseSummary, SpanStatus


def test_request_trace_duration_and_dict():
    t = RequestTrace(
        trace_id="t1",
        method="GET",
        path="/users/42",
        route_pattern="/users/{id}",
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )

    time.sleep(0.01)
    t.finished_monotonic = time.monotonic()

    # Check duration calculation (should be around 10ms+)
    assert t.duration_ms >= 5.0

    # Add spans
    t.add_span(Lane.DATABASE, "SELECT * FROM users WHERE id = 42", 2.0, 5.0)
    assert len(t.spans) == 1
    assert t.spans[0].lane == Lane.DATABASE
    assert t.spans[0].label == "SELECT * FROM users WHERE id = 42"
    assert t.spans[0].start_offset_ms == 2.0
    assert t.spans[0].duration_ms == 5.0
    assert t.spans[0].status == SpanStatus.OK

    # Exception node
    t.exception = ExceptionNode(
        exception_type="ValueError",
        message="Invalid ID",
        fault_code="INVALID_VALUE",
        fault_domain="user",
        fingerprint="err-12345",
        stack_frames=[
            {"filename": "views.py", "lineno": 12, "name": "get_user"},
        ],
    )

    # Response summary
    t.response = ResponseSummary(
        status=400, size_bytes=105, content_type="application/json", preview='{"error": "Invalid ID"}'
    )

    d = t.to_dict()
    assert d["trace_id"] == "t1"
    assert d["method"] == "GET"
    assert d["path"] == "/users/42"
    assert len(d["spans"]) == 1
    assert d["spans"][0]["label"] == "SELECT * FROM users WHERE id = 42"
    assert d["exception"]["exception_type"] == "ValueError"
    assert d["response"]["status"] == 400
