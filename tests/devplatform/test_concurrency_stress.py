"""Concurrency + stress tests for ADP shared state."""

from __future__ import annotations

import threading
import time

import pytest

from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord


class TestSingletonConcurrency:
    def test_parallel_get_instance_same_object(self):
        class S(SingletonMixin):
            def __init__(self):
                self.marker = object()

        results = []
        barrier = threading.Barrier(16)

        def worker():
            barrier.wait()
            results.append(S.get_instance())

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert len({id(r) for r in results}) == 1


class TestRuntimeConcurrency:
    def test_parallel_record_request_no_loss(self, runtime):
        n_threads, per = 8, 500

        def worker(tid):
            for i in range(per):
                runtime.record_request(
                    RequestRecord(trace_id=f"{tid}-{i}", method="GET", path="/", status_code=200, duration_ms=1.0)
                )

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert runtime.snapshot().total_requests == n_threads * per

    def test_parallel_connection_counters_balanced(self, runtime):
        def worker():
            for _ in range(1000):
                runtime.connection_opened()
                runtime.connection_closed()

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert runtime.snapshot().active_connections == 0

    def test_snapshot_during_mutation_never_torn(self, runtime):
        stop = threading.Event()

        def mutator():
            i = 0
            while not stop.is_set():
                runtime.record_request(
                    RequestRecord(trace_id=str(i), method="GET", path="/", status_code=200, duration_ms=1.0)
                )
                i += 1
                time.sleep(0)

        m = threading.Thread(target=mutator, daemon=True)
        m.start()
        try:
            for _ in range(200):
                s = runtime.snapshot()
                # invariants: counts are consistent, error_rate in [0,1]
                assert s.total_requests >= 0
                assert 0.0 <= s.error_rate <= 1.0
        finally:
            stop.set()
            m.join(timeout=5)


@pytest.mark.slow
class TestStress:
    def test_high_request_volume(self, runtime):
        for i in range(50000):
            runtime.record_request(
                RequestRecord(
                    trace_id=str(i),
                    method="GET",
                    path="/",
                    status_code=200 if i % 10 else 500,
                    duration_ms=float(i % 1000),
                )
            )
        s = runtime.snapshot()
        assert s.total_requests == 50000
        assert s.total_errors == 5000
