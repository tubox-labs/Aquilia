"""Hardening tests for ADP diagnostics: event-loop monitor + memory tracker."""

from __future__ import annotations

import asyncio
import tracemalloc

import pytest

from aquilia.devplatform.diagnostics.eventloop import EventLoopMonitor, _parse_took_seconds
from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker


class TestParseTook:
    def test_parses_seconds(self):
        assert _parse_took_seconds("Executing <Handle x> took 0.250 seconds") == 0.250

    def test_absent_returns_zero(self):
        assert _parse_took_seconds("some other message") == 0.0

    def test_garbage_returns_zero(self):
        assert _parse_took_seconds("took abc seconds") == 0.0


class TestEventLoopMonitor:
    async def test_start_stop_restores_handler(self):
        loop = asyncio.get_running_loop()

        sentinel_calls = []

        def original(loop, ctx):
            sentinel_calls.append(ctx)

        loop.set_exception_handler(original)

        mon = EventLoopMonitor.get_instance()
        mon.start(loop)
        assert loop.get_exception_handler() is not original  # ours installed
        mon.stop()
        assert loop.get_exception_handler() is original  # restored exactly
        loop.set_exception_handler(None)

    async def test_stop_leaves_foreign_handler_untouched(self):
        loop = asyncio.get_running_loop()
        mon = EventLoopMonitor.get_instance()
        mon.start(loop)

        # Something else replaces the handler after us.
        def foreign(loop, ctx):
            pass

        loop.set_exception_handler(foreign)
        mon.stop()
        # We must NOT clobber the foreign handler.
        assert loop.get_exception_handler() is foreign
        loop.set_exception_handler(None)

    async def test_slow_callback_recorded(self):
        loop = asyncio.get_running_loop()
        mon = EventLoopMonitor.get_instance()
        mon.start(loop)
        loop.call_exception_handler({"message": "Executing <Handle cb> took 0.030 seconds", "handle": "cb"})
        cbs = mon.get_slow_callbacks()
        assert cbs and cbs[-1].duration_s == pytest.approx(0.030)
        mon.stop()

    async def test_double_start_idempotent(self):
        loop = asyncio.get_running_loop()
        mon = EventLoopMonitor.get_instance()
        mon.start(loop)
        h1 = loop.get_exception_handler()
        mon.start(loop)  # no-op
        assert loop.get_exception_handler() is h1
        mon.stop()
        loop.set_exception_handler(None)


class TestMemoryTracker:
    def test_start_stop_balance_when_owner(self):
        assert not tracemalloc.is_tracing()
        t = MemoryUsageTracker.get_instance()
        t.start()
        assert tracemalloc.is_tracing()
        t.stop()
        assert not tracemalloc.is_tracing()

    def test_does_not_stop_foreign_tracemalloc(self):
        tracemalloc.start()  # started by someone else
        try:
            t = MemoryUsageTracker.get_instance()
            t.start()  # should observe already-tracing, not own it
            t.stop()
            assert tracemalloc.is_tracing()  # left intact
        finally:
            tracemalloc.stop()

    def test_stop_joins_thread(self):
        t = MemoryUsageTracker.get_instance()
        t.start()
        thread = t._thread
        t.stop()
        assert thread is not None
        assert not thread.is_alive()

    def test_double_stop_safe(self):
        t = MemoryUsageTracker.get_instance()
        t.start()
        t.stop()
        t.stop()  # must not raise
