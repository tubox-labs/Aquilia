import os
import tempfile

from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.store import MemoryTraceStore, SQLiteTraceStore
from aquilia.inspector.trace import RequestTrace


def test_memory_trace_store():
    config = InspectorConfig(max_traces=3)
    store = MemoryTraceStore(config)

    t1 = RequestTrace("req-1", "GET", "/1", None, 1.0, 1.0)
    t2 = RequestTrace("req-2", "GET", "/2", None, 2.0, 2.0)
    t3 = RequestTrace("req-3", "GET", "/3", None, 3.0, 3.0)
    t4 = RequestTrace("req-4", "GET", "/4", None, 4.0, 4.0)

    store.save(t1)
    store.save(t2)
    store.save(t3)

    assert store.get("req-1") == t1
    assert len(store.list_recent()) == 3

    # Add 4th trace, which should evict req-1
    store.save(t4)
    assert store.get("req-1") is None
    assert store.get("req-2") == t2
    assert store.get("req-4") == t4

    # Verify newest first in list_recent
    recent = store.list_recent()
    assert len(recent) == 3
    assert recent[0].trace_id == "req-4"
    assert recent[1].trace_id == "req-3"
    assert recent[2].trace_id == "req-2"

    store.clear()
    assert len(store.list_recent()) == 0


def test_sqlite_trace_store():
    fd, path = tempfile.mkstemp()
    os.close(fd)

    try:
        config = InspectorConfig(max_traces=3, store="sqlite", store_path=path)
        store = SQLiteTraceStore(config)

        t1 = RequestTrace("req-1", "GET", "/1", None, 1.0, 1.0)
        t2 = RequestTrace("req-2", "GET", "/2", None, 2.0, 2.0)
        t3 = RequestTrace("req-3", "GET", "/3", None, 3.0, 3.0)
        t4 = RequestTrace("req-4", "GET", "/4", None, 4.0, 4.0)

        store.save(t1)
        store.save(t2)
        store.save(t3)

        assert store.get("req-1").trace_id == "req-1"
        assert len(store.list_recent()) == 3

        # Add 4th trace, which should evict req-1
        store.save(t4)
        assert store.get("req-1") is None
        assert store.get("req-2").trace_id == "req-2"
        assert store.get("req-4").trace_id == "req-4"

        # Verify newest first in list_recent
        recent = store.list_recent()
        assert len(recent) == 3
        assert recent[0].trace_id == "req-4"
        assert recent[1].trace_id == "req-3"
        assert recent[2].trace_id == "req-2"

        store.clear()
        assert len(store.list_recent()) == 0
    finally:
        if os.path.exists(path):
            os.remove(path)
