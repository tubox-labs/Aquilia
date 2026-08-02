"""
aquilia.devplatform.platform — AquiliaDevelopmentPlatform facade.

Central API surface exposed to plugins. Provides hook registration
for request lifecycle and exception events.

All hook callbacks are executed safely — exceptions inside hooks
are caught and logged so they cannot affect the request path.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord
from aquilia.devplatform.faults import WorkerFault, report_fault
from aquilia.devplatform.plugins.registry import PluginManager
from aquilia.typing.devplatform import Hook as _Hook


class AquiliaDevelopmentPlatform:
    """
    Facade object passed to every plugin during initialization.

    Exposes hook registration for:
      - request start/end events
      - exception interception

    All callable hooks are stored in lists and invoked with
    exception isolation so one bad plugin cannot crash the server.
    """

    def __init__(self, runtime: RuntimeStateStore) -> None:
        self._runtime = runtime
        self._plugin_manager = PluginManager()

        self._request_start_hooks: list[_Hook] = []
        self._request_end_hooks: list[_Hook] = []
        self._exception_hooks: list[_Hook] = []

    # ── Plugin management ─────────────────────────────────────────────────

    def load_plugins(self) -> None:
        """Discover and initialize all installed plugins."""
        self._plugin_manager.discover(self)

    def register_plugin_direct(self, plugin: Any) -> None:
        """Register a plugin instance directly (testing / first-party)."""
        self._plugin_manager.register_manual(plugin, self)

    def shutdown_plugins(self) -> None:
        """Call ``shutdown()`` on every loaded plugin (used at server teardown)."""
        self._plugin_manager.shutdown_all()

    def list_plugins(self) -> list[dict[str, str]]:
        """Return ``[{"name", "version"}, ...]`` for all loaded plugins."""
        return self._plugin_manager.list_plugins()

    # ── Hook registration ─────────────────────────────────────────────────

    def on_request_start(self, hook: _Hook) -> None:
        """Register a callback executed at the start of each request."""
        self._request_start_hooks.append(hook)

    def on_request_end(self, hook: _Hook) -> None:
        """Register a callback executed at the end of each request with the RequestRecord."""
        self._request_end_hooks.append(hook)
        # Also register with RuntimeStateStore so it fires on every committed record
        self._runtime.add_request_listener(self._make_safe_hook(hook))

    def on_exception(self, hook: Callable[[Exception, Any], None]) -> None:
        """Register a callback executed when an unhandled exception occurs."""
        self._exception_hooks.append(hook)

    # ── Hook dispatch helpers ─────────────────────────────────────────────

    def _make_safe_hook(self, hook: _Hook) -> _Hook:
        """Wrap a hook so a plugin failure cannot affect the request path."""

        def safe(record: RequestRecord) -> None:
            try:
                hook(record)
            except Exception as exc:
                fault = WorkerFault(
                    f"plugin hook {hook.__qualname__!r} raised: {exc}",
                    metadata={"hook": hook.__qualname__},
                )
                report_fault(fault, app=self._runtime.app)

        return safe

    def fire_request_start(self, scope: Any) -> None:
        """Invoke every registered request-start hook with the ASGI ``scope``.

        Hook failures are isolated and reported as a :class:`WorkerFault`;
        they never propagate into the request path.
        """
        for hook in self._request_start_hooks:
            try:
                hook(scope)
            except Exception as exc:
                fault = WorkerFault(
                    f"request_start hook {hook.__qualname__!r} raised: {exc}",
                    metadata={"hook": hook.__qualname__},
                )
                report_fault(fault, app=self._runtime.app)

    def fire_request_end(self, record: RequestRecord) -> None:
        """Invoke every registered request-end hook with the ``RequestRecord``.

        Hook failures are isolated and reported as a :class:`WorkerFault`.
        """
        for hook in self._request_end_hooks:
            try:
                hook(record)
            except Exception as exc:
                fault = WorkerFault(
                    f"request_end hook {hook.__qualname__!r} raised: {exc}",
                    metadata={"hook": hook.__qualname__},
                )
                report_fault(fault, app=self._runtime.app)

    def fire_exception(self, exc: Exception, context: Any = None) -> None:
        """Invoke every registered exception hook with ``(exc, context)``.

        Hook failures are isolated and reported as a :class:`WorkerFault`.
        """
        for hook in self._exception_hooks:
            try:
                hook(exc, context)
            except Exception as inner:
                fault = WorkerFault(
                    f"exception hook {hook.__qualname__!r} raised: {inner}",
                    metadata={"hook": hook.__qualname__},
                )
                report_fault(fault, app=self._runtime.app)

    # ── Runtime access ────────────────────────────────────────────────────

    def get_runtime(self) -> RuntimeStateStore:
        """Return the global :class:`RuntimeStateStore` singleton."""
        return self._runtime

    def register_request_hook(self, callback: Callable[[RequestRecord], None]) -> None:
        """Backward-compat alias for on_request_end."""
        self.on_request_end(callback)
