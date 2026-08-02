"""
aquilia.devplatform.devserver — AquiliaDevelopmentServer.

Top-level server object. Wires together:
  - ADPProtocolHandler (connection instrumentation)
  - ASGILifespanManager (ADP startup/shutdown hooks)
  - AquiliaDevelopmentPlatform (plugin facade)
  - RuntimeStateStore (global metrics singleton)

Provides an asyncio-native serve() method using a low-level TCP acceptor
so no external ASGI runner is required during development.

Startup sequence:
  1. Parse/validate config
  2. Instantiate RuntimeState
  3. Initialize telemetry (via ASGILifespanManager -> lifespan.startup)
  4. Register core listeners
  5. Initialize hot reload
  6. Bootstrap main lifespan (Aquilia app)
  7. Listen for network socket (UDS > inherited FD > TCP host:port)

``aq run`` / ``aq dev`` CLI commands instantiate this class.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import logging
import os
import signal
import socket
import stat
import sys
from collections.abc import Callable
from typing import Any

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.h11_transport import H11Connection
from aquilia.devplatform.core.lifespan import ASGILifespanManager
from aquilia.devplatform.core.protocol import ADPProtocolHandler
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord
from aquilia.devplatform.core.websocket_transport import serve_websocket
from aquilia.devplatform.faults import StartupFault, report_fault
from aquilia.devplatform.platform import AquiliaDevelopmentPlatform

logger = logging.getLogger("aquilia.devplatform.devserver")


class AquiliaDevelopmentServer:
    """
    Framework-aware ASGI development server for Aquilia.

    Wraps the application with instrumentation, lifespan management,
    and exposes a simple start/stop API.

    .. warning::
        Development use only. This server exists for the inner dev loop —
        hot-reload, Inspector tracing, per-request diagnostics — and has
        not been hardened for internet-facing production traffic. Deploy
        production apps with uvicorn or another mature ASGI server
        (hypercorn, daphne). ``aq run`` enforces this automatically:
        production mode always uses uvicorn.

    Usage::

        config = AquiliaDevelopmentConfig(port=8000)
        server = AquiliaDevelopmentServer(config)
        await server.start(aquilia_app)
    """

    def __init__(self, config: AquiliaDevelopmentConfig) -> None:
        self.config = config
        self._runtime = RuntimeStateStore.get_instance()
        self._platform = AquiliaDevelopmentPlatform(self._runtime)
        self._active_connections: int = 0
        self._server: asyncio.Server | None = None
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._wrapped_app: Any = None
        self._lifespan_task: asyncio.Task | None = None
        self._signalled: bool = False
        self._shutdown_event_lifespan: asyncio.Event = asyncio.Event()
        self._lifespan_shutdown_complete: asyncio.Event = asyncio.Event()

    # ── Public API ─────────────────────────────────────────────────────────

    async def start(self, app: Any) -> None:
        """
        Start the development server.

        Wraps the Aquilia application with ADP instrumentation,
        boots the plugin registry, and opens the TCP listener socket.
        """
        self._configure_logging()

        logger.info(
            "Aquilia Dev Platform starting on http://%s:%d",
            self.config.host,
            self.config.port,
        )
        logger.warning(
            "The Aquilia Native Development Platform is a DEVELOPMENT server. "
            "Do not use it for production traffic — deploy with uvicorn or "
            "another production-grade ASGI server (hypercorn, daphne)."
        )

        # Wrap app with lifespan manager then protocol handler
        lifespan_app = ASGILifespanManager(app, self.config, self._runtime)
        self._wrapped_app = ADPProtocolHandler(lifespan_app, self.config, self._runtime)

        # Load plugins
        self._platform.load_plugins()

        # Run ASGI lifespan startup (triggers ADP subsystems via ASGILifespanManager)
        await self._run_lifespan_startup(app)

        # Bind socket: UDS > inherited FD > TCP host:port, in that priority order
        try:
            if self.config.uds:
                self._prepare_uds_path(self.config.uds)
                self._server = await asyncio.start_unix_server(self._accept_connection, path=self.config.uds)
                os.chmod(self.config.uds, 0o600)
                logger.info("Listening on unix:%s (PID %d)", self.config.uds, os.getpid())
            elif self.config.fd is not None:
                sock = socket.socket(fileno=self.config.fd)
                self._server = await asyncio.start_server(self._accept_connection, sock=sock)
                logger.info("Listening on inherited fd=%d (PID %d)", self.config.fd, os.getpid())
            else:
                self._server = await asyncio.start_server(
                    self._accept_connection,
                    host=self.config.host,
                    port=self.config.port,
                    reuse_address=True,
                    reuse_port=self._supports_reuse_port(),
                )
                logger.info("Listening on http://%s:%d (PID %d)", self.config.host, self.config.port, os.getpid())
        except OSError as exc:
            wsa_eacces = getattr(errno, "WSAEACCES", 10013)
            if (
                exc.errno in (errno.EADDRINUSE, wsa_eacces)
                or getattr(exc, "winerror", None) == 10013
                or isinstance(exc, PermissionError)
            ):
                report_fault(
                    StartupFault(
                        f"port {self.config.port} already in use (EADDRINUSE)",
                        metadata={"port": self.config.port},
                    )
                )
                sys.exit(1)
            report_fault(StartupFault(f"socket bind failed: {exc}"))
            raise

        # Register SIGINT / SIGTERM for graceful shutdown.
        # add_signal_handler is POSIX-only; silently skip on Windows.
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._on_signal)
            except (NotImplementedError, RuntimeError):
                pass

        async with self._server:
            try:
                await self._server.serve_forever()
            except asyncio.CancelledError:
                pass
            finally:
                await self.stop()

    @staticmethod
    def _prepare_uds_path(path: str) -> None:
        """
        Prepare a UNIX domain socket path for binding.

        If a file already exists at ``path``: unlink it if it's a stale
        socket (from a crashed previous process) so binding doesn't fail
        with ``EADDRINUSE``; refuse to clobber it if it's anything else
        (regular file, directory, etc.) — that would silently destroy
        unrelated data.
        """
        try:
            st = os.stat(path)
        except FileNotFoundError:
            return
        if stat.S_ISSOCK(st.st_mode):
            os.unlink(path)
        else:
            raise StartupFault(f"refusing to bind UDS at {path!r}: existing non-socket file would be clobbered")

    async def stop(self) -> None:
        """
        Gracefully shut down the server.

        1. Stop accepting new connections.
        2. Wait for in-flight requests to drain.
        3. Cancel the long-running lifespan task.
        4. Run lifespan shutdown hooks.
        5. Shut down plugins.
        """
        if self._shutdown_event.is_set():
            return  # already stopped — idempotent
        logger.info("ADP: initiating graceful shutdown…")
        self._runtime.set_shutting_down()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        # Drain in-flight requests
        timeout = self.config.timeout_graceful_shutdown
        try:
            await asyncio.wait_for(self._drain_connections(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Drain timeout after %.1fs — forcing shutdown.", timeout)

        # Trigger lifespan shutdown event
        self._shutdown_event_lifespan.set()

        # Wait for lifespan shutdown to complete
        if self._lifespan_task and not self._lifespan_task.done():
            try:
                await asyncio.wait_for(self._lifespan_shutdown_complete.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Lifespan shutdown timed out after 10s — forcing cancel.")
                self._lifespan_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await self._lifespan_task

        self._platform.shutdown_plugins()
        self._shutdown_event.set()
        logger.info("ADP: shutdown complete.")

    def _on_signal(self) -> None:
        """Signal handler — idempotently initiate graceful shutdown.

        Runs synchronously in the loop's signal-handler context. Closing the
        server is idempotent, and the ``_signalled`` guard means a second
        SIGINT/SIGTERM (or SIGINT then SIGTERM) does not double-close or spawn a
        second shutdown coroutine. ``serve_forever`` unblocks once the server is
        closed, and the ``finally`` in :meth:`start` runs the full ``stop()``.
        """
        if self._signalled:
            return
        self._signalled = True
        if self._server:
            self._server.close()

    async def _graceful_stop(self) -> None:
        """Backward-compatible alias for the signal path (idempotent close)."""
        self._on_signal()

    def get_runtime(self) -> RuntimeStateStore:
        """Return the global :class:`RuntimeStateStore` singleton."""
        return self._runtime

    def get_platform(self) -> AquiliaDevelopmentPlatform:
        """Return the :class:`AquiliaDevelopmentPlatform` plugin facade."""
        return self._platform

    def register_request_listener(self, listener: Callable[[RequestRecord], None]) -> None:
        """Register a callback fired with each committed ``RequestRecord``."""
        self._runtime.add_request_listener(listener)

    def get_recent_requests(self, limit: int = 50) -> list[RequestRecord]:
        """Return up to ``limit`` most recent committed request records."""
        return self._runtime.get_recent_requests(limit)

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _accept_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Low-level TCP/UDS connection handler.

        Drives HTTP/1.1 through h11 (real state machine: keep-alive, chunked
        transfer-encoding, pipelining) via H11Connection. A WebSocket upgrade
        request hands the raw socket off to the native RFC 6455 transport.
        """
        self._active_connections += 1
        try:
            ws_hook = None
            if self.config.ws != "none":
                ws_hook = lambda conn, request: serve_websocket(conn, request, self._wrapped_app)  # noqa: E731

            server_addr = (self.config.host, self.config.port)
            conn = H11Connection(reader, writer, self._wrapped_app, server_addr, ws_upgrade_hook=ws_hook)
            await conn.run()
        finally:
            self._active_connections -= 1
            try:
                writer.close()
            except Exception:
                pass

    async def _run_lifespan_startup(self, app: Any) -> None:
        """
        Trigger the ASGI lifespan startup event so the Aquilia app boots
        and ADP subsystems initialize before accepting HTTP connections.
        """
        startup_complete = asyncio.Event()
        startup_failed = asyncio.Event()

        startup_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal startup_sent
            if not startup_sent:
                startup_sent = True
                return {"type": "lifespan.startup"}
            await self._shutdown_event_lifespan.wait()
            return {"type": "lifespan.shutdown"}

        async def send(message: dict[str, Any]) -> None:
            if message["type"] in ("lifespan.startup.complete", "lifespan.startup.failed"):
                if message["type"] == "lifespan.startup.complete":
                    startup_complete.set()
                else:
                    startup_failed.set()
            elif message["type"] in ("lifespan.shutdown.complete", "lifespan.shutdown.failed"):
                self._lifespan_shutdown_complete.set()

        scope = {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}
        # Store the task so stop() can cancel it cleanly instead of letting
        # the event loop destroy it as pending on SIGINT.
        self._lifespan_task = asyncio.create_task(
            self._wrapped_app(scope, receive, send),
            name="adp-lifespan",
        )
        # Wait briefly for startup hooks to complete
        try:
            await asyncio.wait_for(startup_complete.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            report_fault(StartupFault("ASGI lifespan startup timed out after 30s — continuing anyway"), app=app)

    async def _drain_connections(self) -> None:
        """Wait for active_connections to reach zero."""
        while self._active_connections > 0:
            await asyncio.sleep(0.05)

    @staticmethod
    def _supports_reuse_port() -> bool:
        return hasattr(socket, "SO_REUSEPORT")

    def _configure_logging(self) -> None:
        """
        Route the ``aquilia`` logger tree through the ADP log router.

        Rather than attaching a raw ``StreamHandler`` (which floods the
        terminal and fights the dashboard TUI for the screen), the dev server
        installs the single :class:`~aquilia.devplatform.logging.ADPLogRouter`
        handler. In DASHBOARD/INSPECTOR/SILENT modes records are captured into
        the Inspector ring buffer without touching stdout; VERBOSE/DEBUG mirror
        them to the console. The mode is derived from ``config.log_level``:
        DEBUG → DEBUG mode, otherwise DASHBOARD (clean default).

        Scoped to the ``aquilia`` tree (plus root, for third-party capture)
        rather than ``logging.basicConfig()`` so an embedding host application's
        own logging configuration is preserved.
        """
        from aquilia.devplatform.logging import LogMode, get_router

        mode = LogMode.DEBUG if self.config.log_level == "DEBUG" else LogMode.DASHBOARD
        get_router().install(mode=mode)

    # ── Uvicorn integration helper ─────────────────────────────────────────

    @staticmethod
    async def serve_with_uvicorn(
        app: Any,
        config: AquiliaDevelopmentConfig,
    ) -> None:
        """
        Recommended alternative: run the wrapped ADP app via uvicorn.

        This leverages uvicorn's mature HTTP/1.1 + HTTP/2 + WebSocket handling
        while still injecting ADP instrumentation via the protocol wrapper.

        Usage in CLI::

            server = AquiliaDevelopmentServer(config)
            await AquiliaDevelopmentServer.serve_with_uvicorn(app, config)
        """
        try:
            import uvicorn

            runtime = RuntimeStateStore.get_instance()
            platform = AquiliaDevelopmentPlatform(runtime)
            platform.load_plugins()

            lifespan_app = ASGILifespanManager(app, config, runtime)
            adp_app = ADPProtocolHandler(lifespan_app, config, runtime)

            uv_config = uvicorn.Config(
                adp_app,
                host=config.host,
                port=config.port,
                log_level=config.log_level.lower(),
                reload=False,  # ADP handles its own hot-reload
            )
            server = uvicorn.Server(uv_config)
            await server.serve()
        except ImportError:
            raise RuntimeError(
                "uvicorn not installed. Install with: pip install uvicorn\n"
                "Or use AquiliaDevelopmentServer.start() for the built-in transport."
            )
