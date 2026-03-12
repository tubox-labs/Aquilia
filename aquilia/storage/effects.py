"""
Storage Effect Provider -- Bridges storage into the Aquilia Effect system.

Integrates ``StorageRegistry`` as an ``EffectProvider`` for
``EffectKind.STORAGE``, so that handlers can declare
``@requires(Effect("storage"))`` and automatically receive
a ``StorageBackend`` instance.

Usage (in handlers)::

    from aquilia.effects import Effect, EffectKind

    @requires(Effect("storage", kind=EffectKind.STORAGE))
    async def upload_handler(req, storage: StorageBackend):
        name = await storage.save("uploads/file.pdf", req.body)
        return {"saved": name}
"""

from __future__ import annotations

import logging
from typing import Any

from ..effects import EffectKind, EffectProvider
from .base import StorageConfigFault

logger = logging.getLogger("aquilia.storage.effects")


class StorageEffectProvider(EffectProvider):
    """
    Effect provider that yields ``StorageBackend`` instances
    from the ``StorageRegistry``.

    ``acquire(mode)`` returns the backend for the given alias
    (mode='alias_name') or the default backend if mode is None.
    """

    def __init__(self, registry: Any = None) -> None:
        """
        Args:
            registry: A ``StorageRegistry`` instance (set at boot or later).
        """
        self._registry = registry

    @property
    def kind(self) -> EffectKind:
        return EffectKind.STORAGE

    def set_registry(self, registry: Any) -> None:
        """Inject registry after construction (for deferred wiring)."""
        self._registry = registry

    async def initialize(self) -> None:
        """No-op -- backends are initialised by StorageSubsystem."""
        pass

    async def acquire(self, mode: str | None = None) -> Any:
        """
        Acquire a storage backend.

        Args:
            mode: Backend alias (e.g. 'cdn', 's3'). If None, returns default.

        Returns:
            StorageBackend instance.
        """
        if not self._registry:
            raise StorageConfigFault("StorageEffectProvider has no registry")

        if mode:
            return self._registry[mode]
        return self._registry.default

    async def release(self, resource: Any, success: bool = True) -> None:
        """No-op -- storage backends are stateless per request."""
        pass

    async def finalize(self) -> None:
        """No-op -- shutdown handled by StorageSubsystem."""
        pass
