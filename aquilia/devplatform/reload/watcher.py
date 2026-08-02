"""
aquilia.devplatform.reload.watcher — Filesystem watcher for hot-reload.

Uses `watchfiles` for efficient cross-platform file change detection.
Debounces rapid sequences of events (50ms window) to batch simultaneous
saves from code formatters or IDEs into a single reload cycle.

Calls the DependencyGraphAnalyzer and ModuleReloadExecutor on each batch.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.faults import ReloadFault, report_fault

logger = logging.getLogger("aquilia.devplatform.reload.watcher")

_DEBOUNCE_MS = 50  # ms — bundle simultaneous saves


class WorkspaceWatcher:
    """
    Watches configured directories for file changes and triggers module reloads.

    Requires the `watchfiles` package (optional dependency). If it is not
    installed, hot-reload is disabled entirely for the session — file
    changes are not polled or detected by any fallback mechanism; a warning
    is logged once and ``watch()`` returns.
    """

    def __init__(
        self,
        config: AquiliaDevelopmentConfig,
        runtime: RuntimeStateStore,
    ) -> None:
        self._config = config
        self._runtime = runtime
        self._watch_dirs = [str(d) for d in config.reload_dirs]
        self._watch_roots = [Path(d).resolve() for d in config.reload_dirs]
        self._excludes = config.reload_excludes
        self._running = False

    async def watch(self) -> None:
        """Start watching. Runs indefinitely until cancelled or shutdown."""
        monitor_task: asyncio.Task | None = None
        try:
            from watchfiles import awatch

            self._running = True
            logger.info("Hot-reload watcher active: %s", self._watch_dirs)

            # Create a stop event that will be set when the server shuts down.
            stop_event = asyncio.Event()

            async def _monitor_shutdown() -> None:
                """Poll runtime shutdown flag and signal the awatch stop event."""
                while not self._runtime.is_shutting_down:
                    await asyncio.sleep(0.1)
                stop_event.set()

            monitor_task = asyncio.create_task(_monitor_shutdown(), name="adp-reload-shutdown-check")

            async for changes in awatch(
                *self._watch_dirs,
                stop_event=stop_event,
                debounce=_DEBOUNCE_MS,
            ):
                if self._runtime.is_shutting_down:
                    break
                changed_paths = {Path(path) for _, path in changes}
                filtered = self._filter_paths(changed_paths)
                if filtered:
                    await self._handle_changes(filtered)

        except ImportError:
            logger.warning("watchfiles not installed — hot-reload disabled. Install with: pip install watchfiles")
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            # Cancel the shutdown-monitor helper so it never outlives watch().
            if monitor_task is not None and not monitor_task.done():
                monitor_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await monitor_task
            logger.info("Hot-reload watcher stopped.")

    def _filter_paths(self, paths: set[Path]) -> set[Path]:
        """Remove excluded, non-workspace, and noise paths.

        Only ``.py`` source files survive: the reload analyzer maps changed
        paths to Python modules (``analyzer._path_to_module_name`` returns
        ``None`` for anything else), so a changed non-``.py`` file can never
        produce a meaningful reload — it only forces a blind FULL restart.
        Runtime-written artifacts under the workspace (``.aquilia/audit.surp``
        and ``discovery_cache.surp`` from serving ``/admin/``, sqlite files,
        uploaded media/avatars, logs) are therefore dropped here, which is the
        root fix for reloads firing when no source changed.

        Resolves each path (dereferencing symlinks) before checking it falls
        within one of the configured watch roots, so a symlink pointing
        outside the workspace — or a relative ``..`` component slipping in
        via an exclude pattern mismatch — cannot smuggle an out-of-workspace
        path into the reload pipeline.
        """
        filtered: set[Path] = set()
        for path in paths:
            resolved = path.resolve()
            # Source files are the only thing the analyzer can act on.
            if resolved.suffix != ".py":
                continue
            if not self._is_within_workspace(resolved):
                continue
            path_str = str(resolved)
            excluded = False
            for pattern in self._excludes:
                if resolved.match(pattern) or pattern in path_str:
                    excluded = True
                    break
            # Also skip common noise: __pycache__, .pyc, .git
            if not excluded and "__pycache__" not in path_str and not path_str.endswith(".pyc"):
                filtered.add(resolved)
        return filtered

    def _is_within_workspace(self, resolved_path: Path) -> bool:
        """Return True if ``resolved_path`` falls under one of the watch roots."""
        return any(resolved_path.is_relative_to(root) for root in self._watch_roots)

    async def _handle_changes(self, changed_paths: set[Path]) -> None:
        """Analyze changes and dispatch reload."""
        logger.info("File change detected: %s", [str(p) for p in changed_paths])
        try:
            from aquilia.devplatform.reload.analyzer import DependencyGraphAnalyzer
            from aquilia.devplatform.reload.executor import ModuleReloadExecutor

            analyzer = DependencyGraphAnalyzer()
            strategy = analyzer.compute_strategy(changed_paths)

            executor = ModuleReloadExecutor(
                strategy, self._runtime, shutdown_timeout=self._config.timeout_graceful_shutdown
            )
            await executor.execute()

        except Exception as exc:
            report_fault(ReloadFault(str(exc), metadata={"changed_paths": [str(p) for p in changed_paths]}))
