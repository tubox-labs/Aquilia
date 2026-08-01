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

from aquilia.faults.domains import DIFault

if TYPE_CHECKING:
    from aquilia.di.core import Container, Provider, Registry


class DIPlugin:
    """
    Extensible lifecycle base class for DI container compilation and registration plugins.

    Args:
        None (Base class instantiation).

    Returns:
        A :class:`DIPlugin` instance.

    Note:
        Subclass and override lifecycle hooks (``on_registry_build``, ``on_provider_registered``,
        ``on_container_built``). Plugins are active when ``DISettings.enable_plugins`` is enabled.

    Usage::

        from aquilia.di.plugins import DIPlugin, register_plugin

        class CustomAutoRegistrationPlugin(DIPlugin):
            name = "custom-autoreg"

            def on_registry_build(self, registry):
                registry.add_provider(ClassProvider(AuditService, scope="app"))

        register_plugin(CustomAutoRegistrationPlugin())
    """

    #: Stable identifier for this plugin (override in subclasses).
    name: str = "di-plugin"

    def on_registry_build(self, registry: Registry) -> None:
        """Called after providers load, before the dependency graph is built."""

    def on_provider_registered(self, container: Container, provider: Provider) -> None:
        """Called as each provider is registered into a container."""

    def on_container_built(self, container: Container) -> None:
        """Called after an app container has been fully built."""


# ── Process-global plugin registry ────────────────────────────────────

_plugins: list[DIPlugin] = []


def register_plugin(plugin: DIPlugin) -> None:
    """
    Register a :class:`DIPlugin` instance in the global process registry.

    Args:
        plugin: The :class:`DIPlugin` instance to register.

    Returns:
        None.

    Note:
        Idempotent by :attr:`DIPlugin.name`. Re-registering a plugin with an existing name replaces it.

    Usage::

        register_plugin(MyCustomPlugin())
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
    """
    Unregister a plugin by its unique string name.

    Args:
        name: The string identifier of the plugin to remove.

    Returns:
        ``True`` if a matching plugin was found and removed, ``False`` otherwise.

    Note:
        Useful for test fixture cleanup and dynamic plugin unloading.

    Usage::

        was_removed = unregister_plugin("custom-autoreg")
    """
    for i, existing in enumerate(_plugins):
        if existing.name == name:
            del _plugins[i]
            return True
    return False


def get_plugins() -> list[DIPlugin]:
    """
    Retrieve all currently registered active DI plugins.

    Args:
        None.

    Returns:
        A list of active :class:`DIPlugin` instances (empty if ``DISettings.enable_plugins`` is False).

    Note:
        Returns a shallow copy of the active process plugin list.

    Usage::

        active_plugins = get_plugins()
    """
    from aquilia.di.settings import get_di_settings

    if not get_di_settings().enable_plugins:
        return []
    return list(_plugins)


def clear_plugins() -> None:
    """
    Clear all registered plugins from the process global registry.

    Args:
        None.

    Returns:
        None.

    Note:
        Intended for testing teardown to restore process isolation.

    Usage::

        clear_plugins()
    """
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
