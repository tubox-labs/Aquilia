"""
aquilia.devplatform.plugins.protocol — Plugin interface protocol.

Plugins implement AquiliaDevelopmentPlugin to register hooks into the ADP.
Runtime-checkable so isinstance() works without subclassing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from aquilia.devplatform.platform import AquiliaDevelopmentPlatform


@runtime_checkable
class AquiliaDevelopmentPlugin(Protocol):
    """
    Formal protocol for ADP plugins.

    Third-party packages implement this protocol and declare an entry point
    under the ``aquilia_dev.plugins`` group to be auto-discovered.

    Entry point format in pyproject.toml::

        [project.entry-points."aquilia_dev.plugins"]
        my_plugin = "my_package.plugin:MyPlugin"

    The class must be default-constructable (no required constructor args).
    """

    @property
    def name(self) -> str:
        """Unique plugin identifier (e.g. 'aquilia_sql')."""
        ...

    @property
    def version(self) -> str:
        """SemVer string (e.g. '1.0.0')."""
        ...

    def initialize(self, adp: AquiliaDevelopmentPlatform) -> None:
        """
        Initialize the plugin and register hooks via the ADP platform facade.

        Called once during server startup after all ADP subsystems are ready.
        Must not block — use asyncio.create_task() for any async work.
        """
        ...

    def shutdown(self) -> None:
        """
        Clean up plugin resources on server shutdown.

        Called synchronously during the shutdown sequence.
        Must not raise — wrap all cleanup in try/except.
        """
        ...
