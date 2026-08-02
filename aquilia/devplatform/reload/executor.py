"""
aquilia.devplatform.reload.executor — Module reload dispatcher.

Given a ReloadPlan from DependencyGraphAnalyzer, performs the actual reload:
  - FULL: os.execv() — replaces current process with fresh Python
  - PARTIAL: importlib.reload() on each affected module in dependency order,
             then re-registers routes/DI bindings in the Aquilia runtime
  - HOT_PATCH: replaces function __code__ objects in-place (opt-in)

The StateBridgeRegistry is consulted before reload to snapshot long-lived
resource references, and called after to re-bind them to reloaded services.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys

from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.faults import ReloadFault, report_fault
from aquilia.devplatform.reload.analyzer import ReloadPlan, ReloadStrategy
from aquilia.devplatform.reload.state_preservation import StateBridgeRegistry

logger = logging.getLogger("aquilia.devplatform.reload.executor")

_DEFAULT_SHUTDOWN_TIMEOUT = 5.0


class ModuleReloadExecutor:
    """
    Executes a ReloadPlan produced by DependencyGraphAnalyzer.
    """

    def __init__(
        self,
        plan: ReloadPlan,
        runtime: RuntimeStateStore,
        shutdown_timeout: float = _DEFAULT_SHUTDOWN_TIMEOUT,
    ) -> None:
        self._plan = plan
        self._runtime = runtime
        self._shutdown_timeout = shutdown_timeout

    async def execute(self) -> None:
        if self._plan.strategy == ReloadStrategy.NOOP:
            logger.debug("Reload skipped: %s", self._plan.reason)
            return

        logger.info(
            "Executing reload: strategy=%s reason=%s modules=%s",
            self._plan.strategy.value,
            self._plan.reason,
            self._plan.changed_modules,
        )

        if self._plan.strategy == ReloadStrategy.FULL:
            await self._full_reload()
        elif self._plan.strategy == ReloadStrategy.PARTIAL:
            await self._partial_reload()
        elif self._plan.strategy == ReloadStrategy.HOT_PATCH:
            await self._hot_patch()

    async def _full_reload(self) -> None:
        """
        Replace the current process with a fresh Python interpreter.

        Runs the Aquilia app's graceful shutdown (drain in-flight requests,
        close DB pools/effects/tasks) before execv — skipping this would
        drop live connections and leak unclosed resources across reload.
        Bounded by ``shutdown_timeout`` so a hung shutdown can't wedge reload.

        Before ``execv`` we also restore the terminal (exit any alternate-screen
        buffer, undo cbreak mode) and stop the diagnostic trackers. ``execv``
        replaces the process image in place, so anything not unwound here — a
        raw-mode TTY, tracemalloc, a running snapshot thread — would leak into,
        or corrupt, the freshly-started process's terminal.
        """
        logger.warning("Full reload triggered — restarting process.")
        await self._graceful_shutdown_app()
        self._pre_execv_cleanup()
        # execv replaces current process image
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @staticmethod
    def _pre_execv_cleanup() -> None:
        """Best-effort teardown of terminal + diagnostics state before execv."""
        # Restore the terminal: leave alt-screen, show cursor. cbreak restore is
        # owned by the UI's atexit hook, but execv bypasses atexit — so emit the
        # sequences directly and also flush.
        try:
            import sys as _sys

            if _sys.stdout.isatty():
                _sys.stdout.write("\033[?25h\033[?1049l")
                _sys.stdout.flush()
        except Exception:
            pass
        # Stop diagnostics so tracemalloc and the snapshot thread don't carry
        # into (or race with) the replacement process.
        for mod, cls in (
            ("aquilia.devplatform.diagnostics.memory", "MemoryUsageTracker"),
            ("aquilia.devplatform.diagnostics.eventloop", "EventLoopMonitor"),
        ):
            try:
                import importlib

                inst = getattr(importlib.import_module(mod), cls).get_instance()
                inst.stop()
            except Exception:
                pass

    async def _graceful_shutdown_app(self) -> None:
        """Best-effort graceful shutdown of the wrapped Aquilia server before reload/exit."""
        import asyncio

        app = self._runtime.app
        server = getattr(app, "server", None)
        if server is None or not hasattr(server, "graceful_shutdown"):
            logger.warning(
                "Full reload: no AquiliaServer reference found — skipping graceful "
                "shutdown, in-flight requests may be dropped."
            )
            await asyncio.sleep(0.1)
            return

        try:
            await asyncio.wait_for(
                server.graceful_shutdown(timeout=self._shutdown_timeout),
                timeout=self._shutdown_timeout + 2.0,
            )
            logger.info("Full reload: graceful shutdown complete.")
        except asyncio.TimeoutError:
            report_fault(
                ReloadFault(
                    f"graceful shutdown exceeded {self._shutdown_timeout:.1f}s before full reload — forcing restart"
                ),
                app=self._runtime.app,
            )
        except Exception as exc:
            report_fault(
                ReloadFault(f"graceful shutdown failed before full reload ({exc}) — forcing restart"),
                app=self._runtime.app,
            )

    async def _partial_reload(self) -> None:
        """Reload affected modules in-place, re-bind state references."""
        bridge = StateBridgeRegistry.get_instance()

        # Snapshot resources before reload
        snapshot = bridge.snapshot()

        failed_modules: list[str] = []
        for mod_name in self._plan.affected_modules:
            mod = sys.modules.get(mod_name)
            if mod is None:
                continue
            try:
                importlib.reload(mod)
                logger.debug("Reloaded module: %s", mod_name)
            except Exception as exc:
                logger.error("Failed to reload %s: %s", mod_name, exc)
                failed_modules.append(mod_name)

        if failed_modules:
            logger.warning(
                "Partial reload had failures: %s — falling back to full reload",
                failed_modules,
            )
            await self._full_reload()
            return

        # Restore resource references
        bridge.restore(snapshot)

        # Attempt to re-register routes in Aquilia's runtime
        await self._rebind_aquilia_runtime()

        logger.info("Partial reload complete.")

    async def _hot_patch(self) -> None:
        """
        Swap function bytecode (__code__) for changed modules without re-importing.

        Only works for function-level changes with no class-level modifications.
        Falls back to partial reload if bytecode swap fails.
        """
        fallback_needed = False
        for mod_name in self._plan.changed_modules:
            mod = sys.modules.get(mod_name)
            if mod is None:
                continue
            try:
                # Re-import the module source into a temporary namespace
                spec = importlib.util.find_spec(mod_name)
                if spec is None or spec.origin is None:
                    fallback_needed = True
                    break

                new_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(new_mod)  # type: ignore[union-attr]

                # Swap __code__ for each function defined in both
                patched = 0
                for name in dir(new_mod):
                    new_obj = getattr(new_mod, name, None)
                    old_obj = getattr(mod, name, None)
                    if (
                        callable(new_obj)
                        and callable(old_obj)
                        and hasattr(new_obj, "__code__")
                        and hasattr(old_obj, "__code__")
                    ):
                        old_obj.__code__ = new_obj.__code__
                        patched += 1

                logger.debug("Hot-patched %d functions in %s", patched, mod_name)

            except Exception as exc:
                report_fault(
                    ReloadFault(
                        f"hot-patch failed for {mod_name} ({exc}) — falling back to partial reload",
                        metadata={"module": mod_name},
                    ),
                    app=self._runtime.app,
                )
                fallback_needed = True
                break

        if fallback_needed:
            await self._partial_reload()

    async def _rebind_aquilia_runtime(self) -> None:
        """
        Re-register routes and DI bindings after a partial reload.
        Best-effort — if this fails, a full reload is recommended.
        """
        try:
            app = self._runtime.app
            if app is None:
                logger.warning("Route recompilation failed: app reference not registered on state store.")
                return

            server = getattr(app, "server", None)
            if server is None:
                logger.warning("Route recompilation failed: server instance not found on app.")
                return

            # 1. Clear the router fast paths and compiled routes
            router = getattr(server, "controller_router", None)
            if router is not None:
                router.compiled_controllers.clear()
                router.routes_by_method.clear()
                router._static_routes.clear()
                router._dynamic_routes.clear()
                router._tries.clear()
                router._initialized = False

            # 2. Reset compilation state of the registry and run route compilation
            registry = getattr(server, "runtime", None)
            if registry is not None:
                registry._compiled = False
                registry.compile_routes()

            # 3. Reload and recompile controllers on the server
            if hasattr(server, "_load_controllers"):
                await server._load_controllers()

            # 4. Explicitly re-initialize fast-path matching structures
            if router is not None:
                router.initialize()

            logger.info("Routes and controllers recompiled after partial reload.")
        except Exception as exc:
            report_fault(ReloadFault(f"route recompilation after partial reload failed: {exc}"), app=self._runtime.app)
