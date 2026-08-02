"""Regression tests for the devplatform PortManager.

Core bug being guarded: the old CLI probe bound without SO_REUSEADDR while the
real server binds with reuse_address=True, so a just-terminated server's
TIME_WAIT port looked occupied and the CLI hopped 8000 -> 8001. PortManager
probes with the same options, so TIME_WAIT is reclaimed and only a genuine
live listener causes a switch.
"""

from __future__ import annotations

import os
import socket

import pytest

from aquilia.devplatform.portmanager import PortDecision, PortManager


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_free_port_reclaimed_no_switch():
    port = _free_port()
    d = PortManager().resolve("127.0.0.1", port)
    assert isinstance(d, PortDecision)
    assert d.port == port
    assert d.reclaimed and not d.switched


def test_live_listener_switches():
    port = _free_port()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", port))
    listener.listen(1)
    try:
        d = PortManager().resolve("127.0.0.1", port)
        assert d.switched
        assert d.port != port
        assert "actively in use" in d.reason
    finally:
        listener.close()


def test_time_wait_reclaims_same_port():
    """The bug: a TIME_WAIT socket must NOT force a port switch.

    We create a real client/server pair, close the server side while a
    connection is established, and immediately ask PortManager to resolve the
    same port. Because it probes with SO_REUSEADDR (matching the real server),
    it must return the *same* port, not increment.
    """
    port = _free_port()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", port))
    server.listen(1)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    conn, _ = server.accept()

    # Close server-side listener + connection to leave the port lingering.
    conn.close()
    server.close()
    client.close()

    d = PortManager().resolve("127.0.0.1", port)
    assert d.port == port, "TIME_WAIT port must be reclaimed, not switched"
    assert not d.switched


def _fd_count() -> int:
    try:
        return len(os.listdir(f"/proc/{os.getpid()}/fd"))
    except OSError:
        try:
            return len(os.listdir("/dev/fd"))
        except OSError:
            pytest.skip("no fd introspection available")


def test_no_fd_leak_under_repeated_resolve():
    port = _free_port()
    mgr = PortManager()
    # Warm up so lazy allocations don't skew the baseline.
    mgr.resolve("127.0.0.1", port)
    before = _fd_count()
    for _ in range(200):
        d = mgr.resolve("127.0.0.1", port)
        assert d.port == port  # stable, no drift
    after = _fd_count()
    assert after <= before + 1, f"fd leak: {before} -> {after}"
