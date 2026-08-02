"""Unit tests for the ADP terminal UI (rendering, modes, emoji-free output)."""

from __future__ import annotations

import io
import sys

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.logging import LogMode, get_router
from aquilia.devplatform.ui import ADPTerminalUI, _fmt_bytes, _fmt_duration

_EMOJI = "⚡✅◆↻ℹ⚠★☆✓✗●▶◀►◄"


@pytest.fixture
def ui(runtime):
    cfg = AquiliaDevelopmentConfig(host="127.0.0.1", port=8000, reload=True)
    return ADPTerminalUI(cfg, runtime=runtime, mode="dev")


def _capture(fn) -> str:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = old
    return buf.getvalue()


class TestBannerContent:
    def test_banner_has_required_fields(self, ui):
        out = _capture(ui.render_header)
        for field in ("App", "Environment", "Transport", "WebSocket", "Reload", "Process", "Startup", "Workspace"):
            assert field in out

    def test_banner_no_emoji(self, ui):
        out = _capture(ui.render_header)
        for g in _EMOJI:
            assert g not in out


class TestFrames:
    def test_dashboard_frame_no_emoji_and_metrics(self, ui):
        frame = ui._build_dashboard_frame()
        for g in _EMOJI:
            assert g not in frame
        for label in (
            "CPU",
            "Memory",
            "Loop lag",
            "Requests",
            "RPS",
            "Errors",
            "Connections",
            "WebSockets",
            "Tasks",
            "Cache",
            "Bg jobs",
        ):
            assert label in frame

    def test_inspector_frame_shows_events(self, ui):
        get_router().install(mode=LogMode.INSPECTOR)
        get_router().log_event("GET / 200 1.2ms", kind="request")
        frame = ui._build_inspector_frame()
        assert "Inspector" in frame
        assert "GET / 200" in frame
        for g in _EMOJI:
            assert g not in frame

    def test_dashboard_without_runtime(self):
        cfg = AquiliaDevelopmentConfig(port=8000)
        ui = ADPTerminalUI(cfg, runtime=None, mode="dev")
        frame = ui._build_dashboard_frame()
        assert "unavailable" in frame

    def test_inspector_line_levels(self, ui):
        get_router().install(mode=LogMode.INSPECTOR)
        get_router().log_event("boom", level=40, kind="log")  # ERROR
        frame = ui._build_inspector_frame()
        assert "ERROR" in frame


class TestModeSwitching:
    def test_mode_starts_at_startup(self, ui):
        assert ui.ui_mode == "startup"

    def test_enter_mode_noop_without_tty(self, ui, monkeypatch):
        # stdout is not a tty in the test harness → enter_mode is a no-op.
        ui._enter_mode("dashboard")
        assert ui.ui_mode == "startup"

    def test_set_ui_mode_threadsafe(self, ui):
        ui._set_ui_mode("dashboard")
        assert ui.ui_mode == "dashboard"


class TestKeyHandling:
    def test_reload_key_invokes_callback(self, runtime):
        called = []
        cfg = AquiliaDevelopmentConfig(port=8000)
        ui = ADPTerminalUI(cfg, runtime=runtime, mode="dev", on_reload=lambda: called.append(1))
        get_router().install(mode=LogMode.DASHBOARD)
        ui._handle_key("r")
        assert called == [1]

    def test_quit_key_invokes_callback(self, runtime):
        called = []
        cfg = AquiliaDevelopmentConfig(port=8000)
        ui = ADPTerminalUI(cfg, runtime=runtime, mode="dev", on_quit=lambda: called.append(1))
        ui._handle_key("q")
        assert called == [1]

    def test_reload_callback_failure_isolated(self, runtime):
        cfg = AquiliaDevelopmentConfig(port=8000)

        def boom():
            raise RuntimeError("reload fail")

        ui = ADPTerminalUI(cfg, runtime=runtime, mode="dev", on_reload=boom)
        get_router().install(mode=LogMode.DASHBOARD)
        ui._handle_key("r")  # must not raise


class TestTerminalRestore:
    def test_stop_is_safe_without_start(self, ui):
        ui.stop()  # no threads started — must not raise

    def test_emergency_restore_idempotent(self, ui):
        ui._emergency_restore()
        ui._emergency_restore()


class TestFormatters:
    def test_fmt_bytes(self):
        assert _fmt_bytes(0) == "—"
        assert _fmt_bytes(512).endswith("B")
        assert "MB" in _fmt_bytes(5 * 1024 * 1024)

    def test_fmt_duration(self):
        assert _fmt_duration(5).endswith("s")
        assert "m" in _fmt_duration(90)
        assert "h" in _fmt_duration(3700)


class TestStartupStreamer:
    """Requests must stream to stdout in the startup view (not only Inspector)."""

    def _emit_request(self, level=20, status=200, path="/admin/"):

        get_router().log_event(
            "x",
            level=level,
            kind="request",
            logger_name="aquilia.devplatform.request",
            meta={"method": "GET", "path": path, "status": status, "duration_ms": 25.4, "exception_type": None},
        )

    def test_request_streams_in_startup(self, ui):
        ui._running = True
        ui._start_stream()
        try:
            out = _capture(lambda: self._emit_request(path="/admin/"))
        finally:
            ui._stop_stream()
        assert "GET" in out and "/admin/" in out and "200" in out

    def test_debug_noise_suppressed(self, ui):
        import logging

        ui._running = True
        ui._start_stream()
        try:
            out = _capture(
                lambda: get_router().log_event(
                    "chatter", level=logging.DEBUG, kind="log", logger_name="aquilia.devplatform.h11_transport"
                )
            )
        finally:
            ui._stop_stream()
        assert out == ""

    def test_warning_shown(self, ui):
        import logging

        ui._running = True
        ui._start_stream()
        try:
            out = _capture(
                lambda: get_router().log_event(
                    "login_failed", level=logging.WARNING, kind="log", logger_name="aquilia.admin.security"
                )
            )
        finally:
            ui._stop_stream()
        assert "login_failed" in out

    def test_suppressed_in_fullscreen_mode(self, ui):
        ui._running = True
        ui._start_stream()
        ui._set_ui_mode("dashboard")
        try:
            out = _capture(lambda: self._emit_request())
        finally:
            ui._stop_stream()
        assert out == ""
