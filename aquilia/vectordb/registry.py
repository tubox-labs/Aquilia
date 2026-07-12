"""
Aquilia VectorDB registry -- global registry for all VectorModel subclasses.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import VectorModel
    from .engine import ElipsEngine

logger = logging.getLogger("aquilia.vectordb.registry")

__all__ = ["VectorModelRegistry"]


class VectorModelRegistry:
    """
    Global registry for all ``VectorModel`` subclasses.

    Mirrors ``aquilia.models.registry.ModelRegistry``.
    """

    _models: dict[str, type[VectorModel]] = {}
    _engine: ElipsEngine | None = None

    @classmethod
    def register(cls, model_cls: type[VectorModel]) -> None:
        """Register a concrete ``VectorModel`` subclass by its ``__name__``."""
        name = model_cls.__name__
        if name in cls._models and cls._models[name] is not model_cls:
            from .faults import VectorModelRegistrationFault

            raise VectorModelRegistrationFault(name, "A different model with this name is already registered")
        cls._models[name] = model_cls
        if cls._engine is not None:
            model_cls._engine = cls._engine

    @classmethod
    def get(cls, name: str) -> type[VectorModel] | None:
        """Look up a registered model class by its ``__name__``, or ``None`` if not found."""
        return cls._models.get(name)

    @classmethod
    def all_models(cls) -> dict[str, type[VectorModel]]:
        """Return a shallow copy of ``{model_name: model_cls}`` for every registered model."""
        return dict(cls._models)

    @classmethod
    def set_engine(cls, engine: ElipsEngine) -> None:
        """Bind *engine* as the default for every currently-registered (and future) model."""
        cls._engine = engine
        for model_cls in cls._models.values():
            model_cls._engine = engine

    @classmethod
    def get_engine(cls) -> ElipsEngine | None:
        """Return the registry-wide default engine, or ``None`` if unset."""
        return cls._engine

    @classmethod
    async def connect_all(cls) -> None:
        """Explicitly connect the registered engine. Optional -- engines connect lazily on first use."""
        if cls._engine is None:
            from .faults import VectorEngineFault

            raise VectorEngineFault(reason="No engine configured", path="(none)")
        await cls._engine.connect()

    @classmethod
    async def disconnect_all(cls) -> None:
        """Disconnect the registered engine, if any."""
        if cls._engine is not None:
            await cls._engine.disconnect()

    @classmethod
    async def checkpoint(cls) -> None:
        """Flush the registered engine's database to durable storage."""
        if cls._engine is not None:
            await cls._engine.checkpoint()

    @classmethod
    async def compact(cls) -> None:
        """Rebuild indexes and compact the registered engine's storage."""
        if cls._engine is not None:
            await cls._engine.compact()

    @classmethod
    def reset(cls) -> None:
        """Clear all registered models and the default engine. Testing only."""
        cls._models.clear()
        cls._engine = None
        logger.debug("VectorModelRegistry reset")
