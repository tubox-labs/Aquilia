"""Unit tests for the ADP logging pipeline (ADPLogRouter / LogMode / LogEvent)."""

from __future__ import annotations

import io
import logging
import sys
import threading

import pytest

from aquilia.devplatform.logging import ADPLogRouter, LogEvent, LogMode, get_router


@pytest.fixture
def router():
    ADPLogRouter.reset_instance()
    r = get_router()
    yield r
    r.uninstall()
    ADPLogRouter.reset_instance()


class TestLogMode:
    def test_stdout_gating(self):
        assert LogMode.DASHBOARD.writes_stdout is False
        assert LogMode.INSPECTOR.writes_stdout is False
        assert LogMode.SILENT.writes_stdout is False
        assert LogMode.VERBOSE.writes_stdout is True
        assert LogMode.DEBUG.writes_stdout is True

    def test_stdout_level(self):
        assert LogMode.DEBUG.stdout_level == logging.DEBUG
        assert LogMode.VERBOSE.stdout_level == logging.INFO


class TestRouterCapture:
    def test_dashboard_captures_without_stdout(self, router, capsys):
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.t",))
        logging.getLogger("aquilia.t").info("silent-capture")
        out = capsys.readouterr().out
        assert "silent-capture" not in out
        assert any(e.message == "silent-capture" for e in router.events())

    def test_verbose_writes_stdout(self, router):
        router.install(mode=LogMode.VERBOSE, logger_names=("aquilia.t",))
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            logging.getLogger("aquilia.t").warning("loud")
        finally:
            sys.stdout = old
        assert "loud" in buf.getvalue()

    def test_debug_mode_shows_debug(self, router):
        router.install(mode=LogMode.DEBUG, logger_names=("aquilia.t",))
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            logging.getLogger("aquilia.t").debug("dbg")
        finally:
            sys.stdout = old
        assert "dbg" in buf.getvalue()

    def test_verbose_suppresses_debug(self, router):
        router.install(mode=LogMode.VERBOSE, logger_names=("aquilia.t",))
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            logging.getLogger("aquilia.t").debug("hidden-dbg")
        finally:
            sys.stdout = old
        assert "hidden-dbg" not in buf.getvalue()
        # ...but it is still captured for the Inspector.
        assert any(e.message == "hidden-dbg" for e in router.events())


class TestRingBuffer:
    def test_bounded(self, router):
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.t",), ring_size=5)
        lg = logging.getLogger("aquilia.t")
        for i in range(20):
            lg.info("m%d", i)
        evs = router.events()
        assert len(evs) == 5
        assert evs[-1].message == "m19"

    def test_filter_by_kind(self, router):
        router.install(mode=LogMode.DASHBOARD)
        router.log_event("a request", kind="request")
        router.log_event("a reload", kind="reload")
        reqs = router.events(kind="request")
        assert len(reqs) == 1 and reqs[0].message == "a request"

    def test_clear(self, router):
        router.install(mode=LogMode.DASHBOARD)
        router.log_event("x")
        router.clear()
        assert router.events() == []


class TestSubscribers:
    def test_subscribe_and_unsubscribe(self, router):
        router.install(mode=LogMode.DASHBOARD)
        got: list[str] = []
        unsub = router.subscribe(lambda e: got.append(e.message))
        router.log_event("first")
        unsub()
        router.log_event("second")
        assert got == ["first"]

    def test_bad_subscriber_isolated(self, router):
        router.install(mode=LogMode.DASHBOARD)
        seen: list[str] = []

        def boom(e):
            raise ValueError("nope")

        router.subscribe(boom)
        router.subscribe(lambda e: seen.append(e.message))
        router.log_event("survives")  # must not raise
        assert seen == ["survives"]


class TestInstallHygiene:
    def test_strips_prior_stream_handlers(self, router):
        lg = logging.getLogger("aquilia.stripme")
        pre = logging.StreamHandler()
        lg.addHandler(pre)
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.stripme",))
        assert pre not in lg.handlers

    def test_idempotent_install(self, router):
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.t",))
        n1 = len(logging.getLogger("aquilia.t").handlers)
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.t",))
        n2 = len(logging.getLogger("aquilia.t").handlers)
        assert n1 == n2

    def test_uninstall_detaches(self, router):
        router.install(mode=LogMode.DASHBOARD, logger_names=("aquilia.t",))
        router.uninstall()
        assert router._handler not in logging.getLogger("aquilia.t").handlers


class TestLogEvent:
    def test_format_line_plain(self):
        ev = LogEvent(timestamp=0.0, level_no=logging.INFO, level_name="INFO", logger_name="aquilia.x", message="hi")
        line = ev.format_line(color=False)
        assert "INFO" in line and "x" in line and "hi" in line
        assert "\033[" not in line


class TestConcurrency:
    def test_concurrent_emit_no_loss(self, router):
        router.install(mode=LogMode.DASHBOARD, ring_size=100000)

        def worker(n):
            for i in range(500):
                router.log_event(f"{n}-{i}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(router.events()) == 8 * 500
