"""
Version Manager — semantic versioning, promotion, and rollback.

Tracks version history per model and provides instant rollback
to previous versions.

Usage::

    vm = VersionManager(registry)
    await vm.promote("sentiment", from_version="v1", to_tag="production")
    await vm.rollback("sentiment")   # switches back to previous version
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .registry import ModelRegistry

logger = logging.getLogger("aquilia.mlops.orchestrator.versioning")


class VersionManager:
    """
    Version Management for ML models.

    Works alongside ``ModelRegistry`` to track version history,
    enable promotion (staging → production), and instant rollback.
    """

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry
        # model_name → list of previous active versions (stack)
        self._history: Dict[str, List[str]] = defaultdict(list)

    async def promote(
        self,
        name: str,
        from_version: str,
        to_tag: str = "active",
    ) -> bool:
        """
        Promote a model version to the active slot.

        Pushes the current active version onto the rollback stack.

        Args:
            name: Model name.
            from_version: Version to promote.
            to_tag: Ignored for now (always promotes to active).

        Returns:
            True if promotion succeeded.
        """
        entry = self._registry.get(name, from_version)
        if not entry:
            logger.warning(
                "Cannot promote %s:%s — not found in registry", name, from_version,
            )
            return False

        # Save current active for rollback
        current = self._registry.get_active_version(name)
        if current and current != from_version:
            self._history[name].append(current)

        ok = await self._registry.set_active_version(name, from_version)
        if ok:
            logger.info(
                "Promoted %s:%s to active (previous: %s)", name, from_version, current,
            )
        return ok

    async def rollback(self, name: str) -> Optional[str]:
        """
        Roll back to the previous active version.

        Pops the latest previous version from the history stack
        and sets it as active.

        Returns:
            The version rolled back to, or None if no history.
        """
        history = self._history.get(name, [])
        if not history:
            logger.warning("No rollback history for model %s", name)
            return None

        previous = history.pop()
        ok = await self._registry.set_active_version(name, previous)
        if ok:
            logger.info("Rolled back %s to version %s", name, previous)
            return previous
        return None

    def history(self, name: str) -> List[str]:
        """Return the version rollback history for a model."""
        return list(self._history.get(name, []))

    def can_rollback(self, name: str) -> bool:
        """Check if a rollback is available."""
        return bool(self._history.get(name))
