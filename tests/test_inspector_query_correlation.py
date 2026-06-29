import asyncio
import random

import pytest

from aquilia.admin.query_inspector import QueryInspector
from aquilia.inspector.trace import RequestTrace, _reset_current_trace, _set_current_trace


def test_query_inspector_auto_fills_request_id():
    inspector = QueryInspector()
    trace = RequestTrace(
        trace_id="trace-123",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=100.0,
        started_monotonic=200.0,
    )

    token = _set_current_trace(trace)
    try:
        record = inspector.record(sql="SELECT * FROM users", duration_ms=5.0)
        assert record.request_id == "trace-123"
        # Verify it went to self._request_queries
        assert len(inspector._request_queries["trace-123"]) == 1
    finally:
        _reset_current_trace(token)


@pytest.mark.asyncio
async def test_query_inspector_concurrent_partitioning():
    inspector = QueryInspector()

    async def simulate_request(trace_id: str, num_queries: int):
        trace = RequestTrace(
            trace_id=trace_id,
            method="GET",
            path="/",
            route_pattern=None,
            started_at=100.0,
            started_monotonic=200.0,
        )
        token = _set_current_trace(trace)
        try:
            for i in range(num_queries):
                inspector.record(sql=f"SELECT * FROM table_{trace_id}_{i}", duration_ms=1.0)
                await asyncio.sleep(random.uniform(0.001, 0.005))
        finally:
            _reset_current_trace(token)

    # Launch 50 concurrent simulated requests
    tasks = [simulate_request(f"req-{i}", i % 5 + 1) for i in range(50)]
    await asyncio.gather(*tasks)

    # Verify each request got only its own queries
    for i in range(50):
        req_id = f"req-{i}"
        expected_len = i % 5 + 1
        queries = inspector._request_queries[req_id]
        assert len(queries) == expected_len
        for q in queries:
            assert q.request_id == req_id
            assert req_id in q.sql


def test_n_plus_one_detection():
    # n1_threshold is usually 5 by default, let's instantiate with 3
    inspector = QueryInspector(n1_threshold=3)

    # When request_id is empty, N+1 detection should not group them together
    for _ in range(5):
        inspector.record(sql="SELECT * FROM books WHERE id = ?", model="Book")

    # Check that without request_id, they were not tracked in _request_queries
    assert len(inspector.detect_n_plus_one()) == 0

    # Now do it with request_id auto-filled
    trace = RequestTrace(
        trace_id="req-n1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=100.0,
        started_monotonic=200.0,
    )
    token = _set_current_trace(trace)
    try:
        for _ in range(3):
            inspector.record(sql="SELECT * FROM books WHERE id = ?", model="Book")

        detections = inspector.detect_n_plus_one("req-n1")
        assert len(detections) == 1
        assert detections[0].count == 3
        assert detections[0].model == "Book"
    finally:
        _reset_current_trace(token)
