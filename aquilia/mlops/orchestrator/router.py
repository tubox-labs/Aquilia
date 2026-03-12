"""
Version Router -- routes inference requests to the correct model version.

Supports:
- Default routing → active version
- Canary routing: percentage-based traffic split
- Header-based routing: ``X-Model-Version`` header override
- A/B testing via request metadata

Usage::

    router = VersionRouter(registry)
    router.set_canary("sentiment", "v2", percentage=10)
    version = await router.route("sentiment", request_headers)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any

from .registry import ModelRegistry

logger = logging.getLogger("aquilia.mlops.orchestrator.router")


@dataclass
class CanaryConfig:
    """Active canary configuration for a model."""

    canary_version: str
    base_version: str
    percentage: float = 10.0  # 0–100


class VersionRouter:
    """
    Routes inference requests to the correct model version.

    Routing priority:
    1. Explicit header ``X-Model-Version``
    2. Active canary split
    3. Default (active version from registry)
    """

    VERSION_HEADER = "x-model-version"

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry
        self._canaries: dict[str, CanaryConfig] = {}

    # ── Routing ──────────────────────────────────────────────────────

    async def route(
        self,
        model_name: str,
        headers: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Resolve which model version should handle this request.

        Args:
            model_name: Name of the model.
            headers: HTTP headers (for header-based routing).
            metadata: Request metadata (for A/B testing).

        Returns:
            Version string to use for this request.

        Raises:
            KeyError: If the model is not registered.
        """
        # 1. Explicit header override
        if headers:
            explicit = headers.get(self.VERSION_HEADER)
            if explicit and self._registry.has(model_name, explicit):
                return explicit

        # 2. Canary split
        canary = self._canaries.get(model_name)
        if canary:
            if random.random() * 100 < canary.percentage:
                return canary.canary_version
            return canary.base_version

        # 3. Default -- active version
        active = self._registry.get_active_version(model_name)
        if active is None:
            from aquilia.faults.domains import ModelNotFoundFault

            raise ModelNotFoundFault(
                model=model_name,
                reason=f"Model '{model_name}' is not registered",
            )
        return active

    # ── Canary Management ────────────────────────────────────────────

    def set_canary(
        self,
        model_name: str,
        canary_version: str,
        percentage: float = 10.0,
        base_version: str | None = None,
    ) -> None:
        """
        Configure canary routing for a model.

        Args:
            model_name: Model name.
            canary_version: Version to send canary traffic to.
            percentage: Percentage of traffic for the canary (0–100).
            base_version: Base version (default: current active version).
        """
        base = base_version or self._registry.get_active_version(model_name)
        if base is None:
            from aquilia.faults.domains import ModelNotFoundFault

            raise ModelNotFoundFault(
                model=model_name,
                reason=f"Model '{model_name}' has no active version",
            )

        self._canaries[model_name] = CanaryConfig(
            canary_version=canary_version,
            base_version=base,
            percentage=max(0.0, min(100.0, percentage)),
        )

    def clear_canary(self, model_name: str) -> None:
        """Remove canary routing for a model."""
        self._canaries.pop(model_name, None)

    def get_canary(self, model_name: str) -> CanaryConfig | None:
        """Get the active canary config for a model."""
        return self._canaries.get(model_name)

    def has_canary(self, model_name: str) -> bool:
        """Check if a canary is active for a model."""
        return model_name in self._canaries

    def summary(self) -> dict[str, Any]:
        """Canary routing summary."""
        return {
            name: {
                "canary_version": cfg.canary_version,
                "base_version": cfg.base_version,
                "percentage": cfg.percentage,
            }
            for name, cfg in self._canaries.items()
        }
