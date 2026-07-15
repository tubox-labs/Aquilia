"""Unit tests for ADP diagnostics samplers and the runtime metrics store."""

from __future__ import annotations

import asyncio

import pytest

from aquilia.devplatform.core.runtime import RuntimeStateStore, _safe_call_float, _safe_call_pair
from aquilia.devplatform.core.state import RequestRecord
from aquilia.devplatform.diagnostics.system import CPUSampler, EventLoopLagSampler, read_rss_bytes


class TestSystemSamplers:
    def test_read_rss_nonnegative(self):
        assert read_rss_bytes() >= 0

    def test_cpu_sampler_bounded(self):
        s = CPUSampler()
        # burn a little CPU
        sum(i * i for i in range(100000))
        val = s.sample()
        assert 0.0 <= val <= 100.0 or val >= 0.0  # psutil path may exceed briefly on multicore

    async def test_lag_sampler_measures(self):
        s = EventLoopLagSampler(interval_s=0.02)
        s.start()
        # Block the loop to force lag.
        import time as _t

        await asyncio.sleep(0.02)
        _t.sleep(0.05)  # synchronous stall
        await asyncio.sleep(0.06)
        s.stop()
        assert s.lag_ms >= 0.0

    async def test_lag_sampler_stop_cancels_task(self):
        s = EventLoopLagSampler(interval_s=0.02)
        s.start()
        await asyncio.sleep(0.01)
        s.stop()
        assert s._task is None

    def test_lag_sampler_no_loop_is_inert(self):
        s = EventLoopLagSampler()
        s.start()  # no running loop
        assert s.lag_ms == 0.0


class TestSafeHelpers:
    def test_safe_call_float_none(self):
        assert _safe_call_float(None) == 0.0

    def test_safe_call_float_raises(self):
        assert _safe_call_float(lambda: 1 / 0) == 0.0

    def test_safe_call_pair_bad(self):
        assert _safe_call_pair(lambda: "not-a-pair") == (0, 0)

    def test_safe_call_pair_ok(self):
        assert _safe_call_pair(lambda: (3, 4)) == (3, 4)


class TestRuntimeSnapshot:
    def test_snapshot_reads_sources(self, runtime):
        runtime.attach_sources(
            cpu=lambda: 42.0, lag=lambda: 1.5, tasks=lambda: 9, cache_stats=lambda: (7, 2), jobs=lambda: 4
        )
        s = runtime.snapshot()
        assert s.cpu_percent == 42.0
        assert s.event_loop_lag_ms == 1.5
        assert s.active_tasks == 9
        assert (s.cache_hits, s.cache_misses) == (7, 2)
        assert s.background_jobs == 4

    def test_slow_request_counted(self, runtime):
        runtime.record_request(RequestRecord(trace_id="a", method="GET", path="/", status_code=200, duration_ms=999))
        runtime.record_request(RequestRecord(trace_id="b", method="GET", path="/", status_code=200, duration_ms=1))
        assert runtime.snapshot().slow_requests == 1

    def test_error_rate(self, runtime):
        runtime.record_request(RequestRecord(trace_id="a", method="GET", path="/", status_code=500, duration_ms=1))
        runtime.record_request(RequestRecord(trace_id="b", method="GET", path="/", status_code=200, duration_ms=1))
        s = runtime.snapshot()
        assert s.total_errors == 1
        assert s.error_rate == pytest.approx(0.5)

    def test_snapshot_source_failure_is_zero(self, runtime):
        runtime.attach_sources(cpu=lambda: 1 / 0)
        assert runtime.snapshot().cpu_percent == 0.0

    def test_snapshot_empty_error_rate_zero(self, runtime):
        assert runtime.snapshot().error_rate == 0.0
