"""
End-to-end tests: spawn a real ADP dev-server subprocess and exercise the full
transport, lifespan, startup banner, request handling, and graceful shutdown.

These are the highest-fidelity tests in the suite. They are marked ``e2e`` and
``slow`` and can be deselected with ``-m 'not e2e'`` on constrained CI runners.
"""

from __future__ import annotations

import http.client
import signal

import pytest

from .conftest import free_port, wait_for_port

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def _get(host: str, port: int, path: str = "/"):
    conn = http.client.HTTPConnection(host, port, timeout=5)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


class TestEndToEnd:
    def test_server_boots_and_serves(self, dev_server_process):
        port = free_port()
        proc = dev_server_process(port=port)
        proc.start()
        try:
            assert wait_for_port("127.0.0.1", port, timeout=15), "server never opened port"
            status, body = _get("127.0.0.1", port, "/")
            assert status == 200
            assert body == b"hello"
        finally:
            out = proc.stop(signal.SIGINT)
        # Startup banner present, and no emoji flood.
        assert "Aquilia Native Development Platform" in out
        for glyph in "⚡✅◆↻ℹ⚠":
            assert glyph not in out

    def test_startup_banner_fields(self, dev_server_process):
        port = free_port()
        proc = dev_server_process(port=port)
        proc.start()
        try:
            assert wait_for_port("127.0.0.1", port, timeout=15)
        finally:
            out = proc.stop(signal.SIGINT)
        for field in ("App", "Environment", "Transport", "WebSocket", "Reload", "Process"):
            assert field in out

    def test_clean_stdout_no_request_log_flood(self, dev_server_process):
        port = free_port()
        proc = dev_server_process(port=port)
        proc.start()
        try:
            assert wait_for_port("127.0.0.1", port, timeout=15)
            for _ in range(10):
                _get("127.0.0.1", port, "/")
        finally:
            out = proc.stop(signal.SIGINT)
        # The dashboard default must not dump per-request access logs to stdout.
        assert "GET / 200" not in out
        assert out.count("GET /") <= 1

    def test_sigint_graceful_shutdown(self, dev_server_process):
        port = free_port()
        proc = dev_server_process(port=port)
        proc.start()
        try:
            assert wait_for_port("127.0.0.1", port, timeout=15)
        finally:
            out = proc.stop(signal.SIGINT)
        # Process exited (communicate returned) with a non-hanging shutdown.
        assert proc.proc.returncode is not None

    def test_sigterm_also_shuts_down(self, dev_server_process):
        port = free_port()
        proc = dev_server_process(port=port)
        proc.start()
        try:
            assert wait_for_port("127.0.0.1", port, timeout=15)
        finally:
            proc.stop(signal.SIGTERM)
        assert proc.proc.returncode is not None
