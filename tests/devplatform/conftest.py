"""
Shared fixtures for the ADP test suite.

Provides singleton resets (the ADP leans heavily on process-wide singletons
that must not bleed between tests), an in-process ASGI app + protocol driver,
a loopback-socket server harness, and a real-``aq run`` subprocess harness for
the end-to-end tests.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.runtime import RuntimeStateStore

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Singleton hygiene ───────────────────────────────────────────────────────


def _reset_all_singletons() -> None:
    """Reset every ADP process-wide singleton to a pristine state."""
    from aquilia.devplatform.core.runtime import RuntimeStateStore
    from aquilia.devplatform.diagnostics.eventloop import EventLoopMonitor
    from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker
    from aquilia.devplatform.logging import ADPLogRouter
    from aquilia.devplatform.reload.state_preservation import StateBridgeRegistry

    for cls in (RuntimeStateStore, EventLoopMonitor, MemoryUsageTracker, StateBridgeRegistry, ADPLogRouter):
        with contextlib.suppress(Exception):
            cls.reset_instance()

    # WebSocketTracker + SQLQueryAnalyzer live in submodules that may not import
    # cleanly in every environment — reset defensively.
    with contextlib.suppress(Exception):
        from aquilia.devplatform.core.websocket import WebSocketTracker

        WebSocketTracker.reset_instance()
    with contextlib.suppress(Exception):
        from aquilia.devplatform.diagnostics.sql import SQLQueryAnalyzer

        SQLQueryAnalyzer.reset_instance()


@pytest.fixture(autouse=True)
def clean_singletons():
    """Auto-reset ADP singletons before and after every test."""
    _reset_all_singletons()
    yield
    # Make sure any tracker started during the test is stopped, then reset.
    with contextlib.suppress(Exception):
        from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker

        MemoryUsageTracker.get_instance().stop()
    _reset_all_singletons()


@pytest.fixture
def runtime() -> RuntimeStateStore:
    RuntimeStateStore.reset_instance()
    return RuntimeStateStore.get_instance()


@pytest.fixture
def config() -> AquiliaDevelopmentConfig:
    return AquiliaDevelopmentConfig(host="127.0.0.1", port=0, reload=False)


# ── In-process ASGI helpers ─────────────────────────────────────────────────


def make_asgi_echo(status: int = 200, body: bytes = b"ok"):
    """Return a minimal ASGI app that answers HTTP requests with ``body``."""

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return
        if scope["type"] == "http":
            await receive()
            await send({"type": "http.response.start", "status": status, "headers": []})
            await send({"type": "http.response.body", "body": body})

    return app


def make_asgi_boom():
    """An ASGI app whose HTTP handler raises, to exercise the exception path."""

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            return
        raise RuntimeError("intentional handler explosion")

    return app


async def drive_http(handler, method: str = "GET", path: str = "/", body: bytes = b""):
    """Drive one HTTP request through an ASGI callable, capturing the response.

    Returns ``(status, headers, body)``.
    """
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
    }
    sent: list[dict] = []
    received = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        return received.pop(0) if received else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await handler(scope, receive, send)
    status = next((m["status"] for m in sent if m["type"] == "http.response.start"), None)
    headers = next((m.get("headers", []) for m in sent if m["type"] == "http.response.start"), [])
    resp_body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, headers, resp_body


# ── Free-port helper ────────────────────────────────────────────────────────


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    """Poll until ``host:port`` accepts a TCP connection, or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.1)
    return False


# ── Temp workspace factory ──────────────────────────────────────────────────


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a minimal Aquilia workspace that boots a trivial ASGI app.

    The generated ``main.py`` exposes ``app`` directly (bypassing full manifest
    discovery) so the subprocess E2E tests exercise the ADP transport, UI, and
    lifecycle without depending on a fully-populated module tree.
    """
    (tmp_path / "main.py").write_text(
        "async def app(scope, receive, send):\n"
        "    if scope['type'] == 'lifespan':\n"
        "        while True:\n"
        "            m = await receive()\n"
        "            if m['type'] == 'lifespan.startup':\n"
        "                await send({'type': 'lifespan.startup.complete'})\n"
        "            elif m['type'] == 'lifespan.shutdown':\n"
        "                await send({'type': 'lifespan.shutdown.complete'})\n"
        "                return\n"
        "    elif scope['type'] == 'http':\n"
        "        await receive()\n"
        "        await send({'type': 'http.response.start', 'status': 200, 'headers': []})\n"
        "        await send({'type': 'http.response.body', 'body': b'hello'})\n",
        encoding="utf-8",
    )
    return tmp_path


# ── Subprocess `aq run` harness ─────────────────────────────────────────────


class DevServerProcess:
    """Spawns a real ADP dev server via ``python -m aquilia.devplatform`` shim.

    Uses a tiny runner script rather than the full ``aq`` CLI so the E2E tests
    stay hermetic (no workspace validation, manifest discovery, or generator
    machinery) while still exercising the genuine ADP transport, lifespan, UI
    construction, signal handling, and shutdown in a separate process.
    """

    def __init__(self, workspace: Path, port: int, http: str = "h11"):
        self.workspace = workspace
        self.port = port
        self.http = http
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        runner = self.workspace / "_run_adp.py"
        runner.write_text(
            "import asyncio, sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).parent))\n"
            f"sys.path.insert(0, {str(_REPO_ROOT)!r})\n"
            "from main import app\n"
            "from aquilia.devplatform.config import AquiliaDevelopmentConfig\n"
            "from aquilia.devplatform.devserver import AquiliaDevelopmentServer\n"
            "from aquilia.devplatform.ui import ADPTerminalUI\n"
            "async def _main():\n"
            f"    cfg = AquiliaDevelopmentConfig(host='127.0.0.1', port={self.port}, reload=False, http={self.http!r})\n"
            "    srv = AquiliaDevelopmentServer(cfg)\n"
            "    ui = ADPTerminalUI(cfg, runtime=srv.get_runtime(), mode='dev')\n"
            "    ui.render_header()\n"
            "    ui.start()\n"
            "    try:\n"
            "        await srv.start(app)\n"
            "    finally:\n"
            "        ui.stop()\n"
            "asyncio.run(_main())\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["AQUILIA_WORKSPACE"] = str(self.workspace)
        env["AQUILIA_ENV"] = "dev"
        self.proc = subprocess.Popen(
            [sys.executable, str(runner)],
            cwd=str(self.workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
        )

    def stop(self, sig: int | None = None) -> str:
        import signal as _signal

        if self.proc is None:
            return ""
        if self.proc.poll() is None:
            self.proc.send_signal(sig if sig is not None else _signal.SIGINT)
        try:
            out, _ = self.proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            out, _ = self.proc.communicate()
        return out or ""

    def __enter__(self) -> DevServerProcess:
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            with contextlib.suppress(Exception):
                self.proc.communicate(timeout=5)


@pytest.fixture
def dev_server_process(temp_workspace: Path):
    """Factory fixture yielding a :class:`DevServerProcess` builder."""
    created: list[DevServerProcess] = []

    def _make(port: int | None = None, http: str = "h11") -> DevServerProcess:
        p = DevServerProcess(temp_workspace, port or free_port(), http=http)
        created.append(p)
        return p

    yield _make

    for p in created:
        with contextlib.suppress(Exception):
            if p.proc and p.proc.poll() is None:
                p.proc.kill()
                p.proc.communicate(timeout=5)


# Silence "event loop is closed" noise on some platforms after subprocess tests.
@pytest.fixture(scope="session", autouse=True)
def _session_guard():
    yield
    with contextlib.suppress(Exception):
        asyncio.get_event_loop().close()
