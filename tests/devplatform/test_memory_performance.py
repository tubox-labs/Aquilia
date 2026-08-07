"""Memory + performance tests for the ADP (bounded buffers, startup budget)."""

from __future__ import annotations

import gc
import time
import weakref

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.protocol import ADPProtocolHandler
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord
from aquilia.devplatform.logging import ADPLogRouter, LogMode, get_router

from .conftest import drive_http, make_asgi_echo


class TestBoundedMemory:
    def test_request_history_bounded(self):
        RuntimeStateStore.reset_instance()
        rt = RuntimeStateStore(max_history=100)
        for i in range(10000):
            rt.record_request(RequestRecord(trace_id=str(i), method="GET", path="/", status_code=200, duration_ms=1.0))
        assert len(rt.get_recent_requests(100000)) <= 100

    def test_log_ring_bounded(self):
        ADPLogRouter.reset_instance()
        r = get_router()
        r.install(mode=LogMode.DASHBOARD, ring_size=200)
        for i in range(10000):
            r.log_event(f"m{i}")
        assert len(r.events()) == 200
        r.uninstall()
        ADPLogRouter.reset_instance()

    def test_old_records_released(self):
        RuntimeStateStore.reset_instance()
        rt = RuntimeStateStore(max_history=10)
        first = RequestRecord(trace_id="first", method="GET", path="/", status_code=200, duration_ms=1.0)
        ref = weakref.ref(first)
        rt.record_request(first)
        del first
        for i in range(50):
            rt.record_request(RequestRecord(trace_id=str(i), method="GET", path="/", status_code=200, duration_ms=1.0))
        gc.collect()
        # Evicted from the bounded deque → collectable.
        assert ref() is None


@pytest.mark.slow
class TestPerformance:
    def test_request_overhead_reasonable(self):
        RuntimeStateStore.reset_instance()
        rt = RuntimeStateStore.get_instance()
        cfg = AquiliaDevelopmentConfig(port=8000, reload=False, n_plus_one_detection=False)
        handler = ADPProtocolHandler(make_asgi_echo(200, b"x"), cfg, rt)

        import asyncio

        async def run():
            start = time.perf_counter()
            for _ in range(2000):
                await drive_http(handler, "GET", "/")
            return time.perf_counter() - start

        elapsed = asyncio.run(run())
        # Loose ceiling: 2000 instrumented requests should be well under 5s.
        assert elapsed < 5.0

    def test_snapshot_cheap(self):
        import os

        is_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
        budget = 30.0 if is_ci else 15.0

        RuntimeStateStore.reset_instance()
        rt = RuntimeStateStore.get_instance()
        start = time.perf_counter()
        for _ in range(10000):
            rt.snapshot()
        assert time.perf_counter() - start < budget
