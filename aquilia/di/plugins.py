"""
DI plugin system — extend provider discovery and registry construction.

Aquilia auto-discovers providers by convention (``*Service``/``*Controller``
naming, ``__di_scope__`` markers). That covers the common case but is not
extensible: there is no hook for a third-party package to contribute providers,
rewrite metadata, or run validation as the registry is built.

:class:`DIPlugin` is that hook. Register plugins with :func:`register_plugin`;
they run at well-defined points during :meth:`Registry.from_manifests`. Plugins
are honoured only when ``DISettings.enable_plugins`` is on.

Lifecycle hooks (all optional, all no-ops by default):

* :meth:`DIPlugin.on_registry_build` — after providers load, before graph build.
  Contribute or mutate providers here.
* :meth:`DIPlugin.on_provider_registered` — per provider, as each is registered
  into a container.
* :meth:`DIPlugin.on_container_built` — after an app container is fully built.

Example — a plugin that auto-registers every ``*Repository`` it can import::

    from aquilia.di.plugins import DIPlugin, register_plugin

    class RepositoryPlugin(DIPlugin):
        name = "repository-autoreg"

        def on_registry_build(self, registry):
            registry.add_provider(ClassProvider(UserRepository, scope="app"))

    register_plugin(RepositoryPlugin())
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..faults.domains import DIFault

if TYPE_CHECKING:
    from .core import Container, Provider, Registry


class DIPlugin:
    """Base class for DI plugins.

    Subclass and override the hooks you need. Give each plugin a stable
    :attr:`name` (used for de-duplication and diagnostics). All hooks are
    optional; the base implementations do nothing.

    Attributes:
        name: Stable plugin identifier.
    """

    #: Stable identifier for this plugin (override in subclasses).
    name: str = "di-plugin"

    def on_registry_build(self, registry: Registry) -> None:
        """Called after providers load, before the dependency graph is built.

        Use :meth:`Registry.add_provider` to contribute providers, or inspect
        ``registry._providers`` to rewrite metadata.
        """

    def on_provider_registered(self, container: Container, provider: Provider) -> None:
        """Called as each provider is registered into a container."""

    def on_container_built(self, container: Container) -> None:
        """Called after an app container has been fully built."""


# ── Process-global plugin registry ────────────────────────────────────

_plugins: list[DIPlugin] = []


def register_plugin(plugin: DIPlugin) -> None:
    """Register a :class:`DIPlugin` for the process.

    Idempotent by :attr:`DIPlugin.name` — re-registering a plugin with the
    same name replaces the previous instance.

    Args:
        plugin: The plugin instance to register.

    Raises:
        DIFault: If *plugin* is not a :class:`DIPlugin`.

    Example::

        register_plugin(MyPlugin())
    """
    if not isinstance(plugin, DIPlugin):
        raise DIFault(
            code="DI_INVALID_PLUGIN",
            message=f"Expected a DIPlugin instance, got {type(plugin).__name__}.",
            metadata={"got": type(plugin).__name__},
        )
    # Replace any existing plugin with the same name.
    for i, existing in enumerate(_plugins):
        if existing.name == plugin.name:
            _plugins[i] = plugin
            return
    _plugins.append(plugin)


def unregister_plugin(name: str) -> bool:
    """Remove a registered plugin by name. Returns whether one was removed."""
    for i, existing in enumerate(_plugins):
        if existing.name == name:
            del _plugins[i]
            return True
    return False


def get_plugins() -> list[DIPlugin]:
    """Return the active plugins (empty when plugins are disabled in settings).

    Example::

        for plugin in get_plugins():
            plugin.on_registry_build(registry)
    """
    from .settings import get_di_settings

    if not get_di_settings().enable_plugins:
        return []
    return list(_plugins)


def clear_plugins() -> None:
    """Remove all registered plugins. Intended for test teardown."""
    _plugins.clear()


def run_registry_build(registry: Registry) -> None:
    """Invoke ``on_registry_build`` for every active plugin (best-effort)."""
    for plugin in get_plugins():
        try:
            plugin.on_registry_build(registry)
        except Exception as exc:  # plugins must never crash the boot
            import logging as _log

            _log.getLogger("aquilia.di").warning("Plugin %r on_registry_build failed: %s", plugin.name, exc)


def run_container_built(container: Container) -> None:
    """Invoke ``on_container_built`` for every active plugin (best-effort)."""
    for plugin in get_plugins():
        try:
            plugin.on_container_built(container)
        except Exception as exc:
            import logging as _log

            _log.getLogger("aquilia.di").warning("Plugin %r on_container_built failed: %s", plugin.name, exc)


def _notify_provider_registered(container: Container, provider: Provider) -> None:
    """Invoke ``on_provider_registered`` for every active plugin (best-effort)."""
    for plugin in get_plugins():
        try:
            plugin.on_provider_registered(container, provider)
        except Exception as exc:
            import logging as _log

            _log.getLogger("aquilia.di").warning("Plugin %r on_provider_registered failed: %s", plugin.name, exc)


# Re-export as a public helper name too.
notify_provider_registered = _notify_provider_registered


def install_plugin_metadata(target: Any, **metadata: Any) -> Any:
    """Attach arbitrary DI metadata to a class/factory for plugin consumption.

    A tiny convenience so plugins can annotate targets during discovery.

    Example::

        install_plugin_metadata(UserService, team="identity", tier="core")
    """
    existing = getattr(target, "__di_plugin_meta__", None)
    merged = dict(existing) if isinstance(existing, dict) else {}
    merged.update(metadata)
    target.__di_plugin_meta__ = merged
    return target
