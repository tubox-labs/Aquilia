"""Tests for the rich, aligned LogEvent formatter (streaming + Inspector)."""

from __future__ import annotations

import logging
import re
import time

from aquilia.devplatform.logging import LogEvent

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _req(method="GET", path="/", status=200, dur=25.4, exc=None):
    return LogEvent(
        timestamp=time.time(),
        level_no=logging.INFO,
        level_name="INFO",
        logger_name="aquilia.devplatform.request",
        message=f"{method} {path} {status} {dur:.1f}ms",
        kind="request",
        meta={"method": method, "path": path, "status": status, "duration_ms": dur, "exception_type": exc},
    )


class TestFormatLine:
    def test_plain_request_has_kind_and_parts(self):
        out = _req("GET", "/admin/", 200, 25.4).format_line(color=False)
        assert "REQ" in out
        assert "GET" in out and "/admin/" in out and "200" in out and "25.4ms" in out

    def test_color_request_wraps_ansi(self):
        out = _req("POST", "/x", 401, 121.3).format_line(color=True)
        assert "\x1b[" in out
        assert _ANSI.sub("", out).endswith("121.3ms")

    def test_disconnect_tag_rendered(self):
        out = _req("GET", "/stream/", 200, 1966.6, exc="ClientDisconnectError").format_line(color=False)
        assert "[ClientDisconnectError]" in out

    def test_non_request_keeps_message(self):
        ev = LogEvent(
            timestamp=time.time(),
            level_no=logging.DEBUG,
            level_name="DEBUG",
            logger_name="aquilia.devplatform.h11_transport",
            message="Client disconnected during GET /",
            kind="log",
        )
        out = ev.format_line(color=False)
        assert "LOG" in out and "Client disconnected during GET /" in out

    def test_status_color_differs_by_class(self):
        ok = _req(status=200).format_line(color=True)
        server_err = _req(status=503).format_line(color=True)
        # 2xx green (\x1b[92m) vs 5xx red (\x1b[91m) — different status colouring.
        assert "\x1b[92m" in ok
        assert "\x1b[91m" in server_err
