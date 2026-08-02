"""
aquilia.devplatform.plugins.registry — Plugin discovery and lifecycle manager.

Scans installed packages for entry points under the ``aquilia_dev.plugins``
group, loads and initializes each plugin, and manages their lifecycle.

Errors during plugin initialization are caught and logged — they do NOT
crash the server. Errors inside plugin hooks are also silenced to protect
the request path.
"""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING, Any

from aquilia.devplatform.faults import WorkerFault, report_fault
from aquilia.devplatform.plugins.protocol import AquiliaDevelopmentPlugin

if TYPE_CHECKING:
    from aquilia.devplatform.platform import AquiliaDevelopmentPlatform

logger = logging.getLogger("aquilia.devplatform.plugins.registry")

_ENTRY_POINT_GROUP = "aquilia_dev.plugins"


class PluginManager:
    """
    Discovers, loads, and manages the lifecycle of ADP plugins.

    Usage::

        manager = PluginManager()
        manager.discover(platform)  # loads all installed plugins
        # ... server running ...
        manager.shutdown_all()      # on server teardown
    """

    def __init__(self) -> None:
        self._plugins: list[AquiliaDevelopmentPlugin] = []

    def discover(self, platform: AquiliaDevelopmentPlatform) -> None:
        """
        Scan importlib entry points for plugins and initialize each.

        All exceptions are caught per-plugin so one bad plugin does not
        prevent others from loading.
        """
        entry_points = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
        for ep in entry_points:
            self._load_plugin(ep, platform)

        if self._plugins:
            logger.info(
                "ADP plugin registry: %d plugin(s) loaded: %s",
                len(self._plugins),
                [p.name for p in self._plugins],
            )
        else:
            logger.debug("ADP plugin registry: no plugins found under group '%s'.", _ENTRY_POINT_GROUP)

    def _load_plugin(
        self,
        ep: importlib.metadata.EntryPoint,
        platform: AquiliaDevelopmentPlatform,
    ) -> None:
        """Load, instantiate, and initialize a single plugin entry point."""
        try:
            plugin_cls = ep.load()
            plugin: Any = plugin_cls()

            if not isinstance(plugin, AquiliaDevelopmentPlugin):
                logger.warning(
                    "Plugin '%s' does not implement AquiliaDevelopmentPlugin protocol — skipped.",
                    ep.name,
                )
                return

            plugin.initialize(platform)
            self._plugins.append(plugin)
            logger.info("Plugin loaded: %s v%s", plugin.name, plugin.version)

        except Exception as exc:
            report_fault(
                WorkerFault(f"failed to load plugin {ep.name!r}: {exc} — skipping", metadata={"plugin": ep.name})
            )

    def register_manual(
        self,
        plugin: AquiliaDevelopmentPlugin,
        platform: AquiliaDevelopmentPlatform,
    ) -> None:
        """Register a plugin instance directly (for testing or first-party use)."""
        try:
            plugin.initialize(platform)
            self._plugins.append(plugin)
            logger.info("Plugin manually registered: %s", plugin.name)
        except Exception as exc:
            report_fault(
                WorkerFault(
                    f"manual plugin registration failed for {plugin.name!r}: {exc}", metadata={"plugin": plugin.name}
                )
            )

    def shutdown_all(self) -> None:
        """Call shutdown() on all registered plugins."""
        for plugin in self._plugins:
            try:
                plugin.shutdown()
            except Exception as exc:
                report_fault(
                    WorkerFault(f"plugin shutdown error ({plugin.name}): {exc}", metadata={"plugin": plugin.name})
                )
        logger.debug("All plugins shut down.")

    def list_plugins(self) -> list[dict[str, str]]:
        """Return summary of loaded plugins."""
        return [{"name": p.name, "version": p.version} for p in self._plugins]
