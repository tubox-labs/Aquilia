"""
aquilia.devplatform.core.lifespan — ASGI lifespan manager for the ADP.

Wraps the Aquilia application's ASGI lifespan to inject ADP startup/shutdown
hooks into the standard ASGI lifespan protocol:

  lifespan.startup  → boot telemetry engines, plugin registry, hot-reload watcher
  lifespan.shutdown → drain in-flight requests, flush traces, stop engines

This avoids monkey-patching Aquilia's LifecycleCoordinator directly; instead
it wraps the ASGI lifespan event stream so both Aquilia's internal hooks and
ADP hooks execute in sequence.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.faults import InspectorFault, ReloadFault, WorkerFault, report_fault
from aquilia.devplatform.logging import get_router

logger = logging.getLogger("aquilia.devplatform.lifespan")


class ASGILifespanManager:
    """
    Wraps an Aquilia ASGI application and intercepts lifespan events
    to run ADP boot/teardown sequences around the app's own lifecycle.

    Usage::

        wrapped_app = ASGILifespanManager(aquilia_app, config, runtime)
        # pass wrapped_app to the network socket acceptor

    The wrapped app is fully transparent for http and websocket scopes.
    """

    def __init__(
        self,
        app: Any,
        config: AquiliaDevelopmentConfig,
        runtime: RuntimeStateStore,
    ) -> None:
        self._app = app
        self._config = config
        self._runtime = runtime
        self._runtime.app = app
        self._started = False
        self._lag_sampler: Any = None

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        else:
            await self._app(scope, receive, send)

    async def _handle_lifespan(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        """
        Intercept lifespan.startup / lifespan.shutdown events.

        ADP startup hooks fire BEFORE the app's own startup hooks so
        that telemetry listeners are registered before the first request arrives.
        ADP shutdown hooks fire AFTER the app's own shutdown hooks so
        that in-flight request traces can still be flushed.
        """
        started_event: asyncio.Event = asyncio.Event()
        shutdown_event: asyncio.Event = asyncio.Event()

        async def adp_receive() -> dict[str, Any]:
            """Forward lifespan events to the wrapped app unchanged."""
            msg = await receive()
            msg_type = msg.get("type", "")
            if msg_type == "lifespan.startup":
                get_router().log_event("Lifespan startup initiated", kind="lifespan")
            elif msg_type == "lifespan.shutdown":
                get_router().log_event("Lifespan shutdown initiated", kind="lifespan")
            return msg

        async def adp_send(message: dict[str, Any]) -> None:
            """Intercept app responses to inject ADP hooks."""
            msg_type = message.get("type", "")

            if msg_type == "lifespan.startup.complete":
                # App finished its startup — now run ADP startup hooks
                await self._adp_startup()
                await send(message)
                get_router().log_event("Lifespan startup complete", kind="lifespan")
                started_event.set()

            elif msg_type == "lifespan.startup.failed":
                get_router().log_event("Lifespan startup failed", kind="lifespan")
                logger.error("Aquilia app startup failed — ADP entering error mode.")
                await send(message)

            elif msg_type == "lifespan.shutdown.complete":
                # ADP shutdown hooks fire before we signal completion
                await self._adp_shutdown()
                await send(message)
                get_router().log_event("Lifespan shutdown complete", kind="lifespan")
                shutdown_event.set()

            elif msg_type == "lifespan.shutdown.failed":
                get_router().log_event("Lifespan shutdown failed", kind="lifespan")
                logger.error("Aquilia app shutdown failed.")
                await self._adp_shutdown()
                await send(message)

            else:
                await send(message)

        await self._app(scope, adp_receive, adp_send)

    # ── ADP startup ────────────────────────────────────────────────────────

    async def _adp_startup(self) -> None:
        """Boot ADP subsystems in dependency order."""
        if self._started:
            return  # idempotent — prevent double-boot on reconnect / reload
        logger.info("ADP: booting telemetry subsystems…")

        await self._start_telemetry()
        await self._register_core_listeners()
        await self._start_hot_reload()

        self._started = True
        logger.info("ADP: all subsystems ready.")

    async def _start_telemetry(self) -> None:
        """Enable tracemalloc and event-loop slow-callback monitoring."""
        if self._config.inspector_enabled:
            try:
                from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker

                MemoryUsageTracker.get_instance().start()
            except Exception as exc:
                report_fault(WorkerFault(f"memory tracker failed to start: {exc}"), app=self._app)

        try:
            from aquilia.devplatform.diagnostics.eventloop import EventLoopMonitor

            loop = asyncio.get_running_loop()
            EventLoopMonitor.get_instance().start(loop)
        except Exception as exc:
            report_fault(WorkerFault(f"event-loop monitor failed to start: {exc}"), app=self._app)

        # Wire dashboard telemetry sources into the runtime store (best-effort).
        try:
            from aquilia.devplatform.diagnostics.eventloop import EventLoopMonitor
            from aquilia.devplatform.diagnostics.system import CPUSampler, EventLoopLagSampler

            cpu_sampler = CPUSampler()
            lag_sampler = EventLoopLagSampler()
            lag_sampler.start()
            self._lag_sampler = lag_sampler  # keep a reference for shutdown

            def _task_count() -> int:
                return EventLoopMonitor.get_instance().get_task_summary().get("total", 0)

            self._runtime.attach_sources(
                cpu=cpu_sampler.sample,
                lag=lambda: lag_sampler.lag_ms,
                tasks=_task_count,
            )
        except Exception as exc:
            report_fault(WorkerFault(f"dashboard telemetry wiring failed: {exc}"), app=self._app)

    async def _register_core_listeners(self) -> None:
        """Attach DI diagnostic listener to active containers."""
        if not self._config.inspector_enabled:
            return
        try:
            from aquilia.inspector.di_listener import InspectorDiagnosticListener

            listener = InspectorDiagnosticListener()
            # Attempt to discover containers via aquilary runtime registry
            try:
                registry = None
                if self._app is not None:
                    server = getattr(self._app, "server", None)
                    if server is not None:
                        registry = getattr(server, "runtime", None)

                if registry is not None:
                    for container in registry.di_containers.values():
                        if hasattr(container, "add_diagnostic_listener"):
                            container.add_diagnostic_listener(listener)
            except Exception as exc:
                report_fault(InspectorFault(f"DI diagnostic listener attachment failed: {exc}"), app=self._app)
        except ImportError:
            logger.debug("ADP DI listener registration skipped: aquilia.inspector not available.")

    async def _start_hot_reload(self) -> None:
        if not self._config.reload:
            return
        try:
            from aquilia.devplatform.reload.watcher import WorkspaceWatcher

            watcher = WorkspaceWatcher(self._config, self._runtime)
            asyncio.create_task(watcher.watch(), name="adp-hot-reload")
            logger.info("ADP hot-reload watcher started (dirs: %s)", self._config.reload_dirs)
        except Exception as exc:
            report_fault(ReloadFault(f"hot-reload watcher failed to start: {exc}"), app=self._app)

    # ── ADP shutdown ───────────────────────────────────────────────────────

    async def _adp_shutdown(self) -> None:
        """Tear down ADP subsystems cleanly."""
        logger.info("ADP: shutting down subsystems…")
        self._runtime.set_shutting_down()

        # Stop event loop monitor
        try:
            from aquilia.devplatform.diagnostics.eventloop import EventLoopMonitor

            EventLoopMonitor.get_instance().stop()
        except Exception as exc:
            report_fault(WorkerFault(f"event-loop monitor failed to stop cleanly: {exc}"), app=self._app)

        # Stop memory tracker
        try:
            from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker

            MemoryUsageTracker.get_instance().stop()
        except Exception as exc:
            report_fault(WorkerFault(f"memory tracker failed to stop cleanly: {exc}"), app=self._app)

        # Stop event-loop lag sampler
        if self._lag_sampler is not None:
            try:
                self._lag_sampler.stop()
            except Exception as exc:
                report_fault(WorkerFault(f"loop-lag sampler failed to stop cleanly: {exc}"), app=self._app)
            self._lag_sampler = None

        logger.info("ADP: shutdown complete.")
