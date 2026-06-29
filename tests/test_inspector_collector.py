import time

from aquilia.inspector.collector import InspectorCollector, get_collector, reset_global_collector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.trace import RequestTrace


def test_collector_singleton():
    reset_global_collector()
    cfg1 = InspectorConfig(max_traces=10)
    cfg2 = InspectorConfig(max_traces=10)

    col1 = get_collector(cfg1)
    col2 = get_collector(cfg2)
    assert col1 is col2
    assert isinstance(col1, InspectorCollector)


def make_trace(trace_id: str, path: str, method: str) -> RequestTrace:
    return RequestTrace(
        trace_id=trace_id,
        method=method,
        path=path,
        route_pattern=path,
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )


def test_collector_crud_and_eviction():
    reset_global_collector()
    cfg = InspectorConfig(max_traces=3)
    col = get_collector(cfg)

    col.clear()

    t1 = make_trace(trace_id="t1", path="/p1", method="GET")
    t2 = make_trace(trace_id="t2", path="/p2", method="POST")
    t3 = make_trace(trace_id="t3", path="/p3", method="PUT")
    t4 = make_trace(trace_id="t4", path="/p4", method="DELETE")

    col.commit(t1)
    col.commit(t2)
    col.commit(t3)

    assert len(col.list_recent()) == 3
    assert col.get("t1") is t1
    assert col.get("t3") is t3

    # Adding 4th trace should evict t1 (FIFO)
    col.commit(t4)
    assert len(col.list_recent()) == 3
    assert col.get("t1") is None
    assert col.get("t2") is t2
    assert col.get("t4") is t4
