"""
IntegrationConfig protocol — the contract every integration type satisfies.

Any object that implements ``_integration_type`` (a string tag) and
``to_dict()`` (returning the config dict) is a valid integration and
can be passed to ``Workspace.integrate()``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IntegrationConfig(Protocol):
    """Protocol that all typed integration configs implement."""

    @property
    def _integration_type(self) -> str:
        """Unique tag identifying this integration kind (e.g. ``"mail"``)."""
        ...  # pragma: no cover

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the flat dict consumed by ``ConfigLoader``."""
        ...  # pragma: no cover
