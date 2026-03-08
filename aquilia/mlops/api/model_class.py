"""
AquiliaModel -- declarative base class and ``@model`` decorator.

The primary developer interface for defining ML models within Aquilia.

Usage::

    from aquilia.mlops import AquiliaModel, model

    @model(name="sentiment", version="v1")
    class SentimentModel(AquiliaModel):

        async def load(self, artifacts_dir: str, device: str):
            self.pipeline = load_pipeline(artifacts_dir, device)

        async def predict(self, inputs: dict) -> dict:
            return {"sentiment": self.pipeline(inputs["text"])}

        async def preprocess(self, inputs: dict) -> dict:
            return {"text": inputs["text"].strip().lower()}

        async def postprocess(self, outputs: dict) -> dict:
            outputs["confidence"] = round(outputs["confidence"], 4)
            return outputs

The ``@model`` decorator registers the class with the global
``ModelRegistry`` so that the ``RouteGenerator`` can auto-create
HTTP endpoints for it.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

logger = logging.getLogger("aquilia.mlops.api.model_class")

T = TypeVar("T", bound="AquiliaModel")

# Global registry reference -- set by the DI/lifecycle layer
_global_registry: Any = None


def _get_global_registry() -> Any:
    """Get the global model registry, creating a lazy one if needed."""
    global _global_registry
    if _global_registry is None:
        from ..orchestrator.registry import ModelRegistry
        _global_registry = ModelRegistry()
    return _global_registry


def set_global_registry(registry: Any) -> None:
    """Set the global model registry (called by DI providers)."""
    global _global_registry
    _global_registry = registry


class AquiliaModel:
    """
    Base class for Aquilia ML models.

    Subclass this and implement ``predict()`` at minimum.
    Override ``load()``, ``unload()``, ``preprocess()``,
    ``postprocess()``, ``health()``, and ``metrics()`` as needed.

    All methods can be sync or async -- the pipeline adapts automatically.
    """

    # ── Lifecycle ────────────────────────────────────────────────────

    async def load(self, artifacts_dir: str, device: str) -> None:
        """
        Load model weights / artifacts into memory.

        Called by ``ModelLoader`` when the model is first needed.

        Args:
            artifacts_dir: Path to the model artifacts directory.
            device: Compute device to load onto (e.g. "cpu", "cuda:0").
        """
        pass

    async def unload(self) -> None:
        """Release model resources. Called during shutdown or hot reload."""
        pass

    # ── Inference ────────────────────────────────────────────────────

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on preprocessed inputs.

        This is the core method every model MUST implement.

        Args:
            inputs: Preprocessed input dictionary.

        Returns:
            Output dictionary with predictions.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement predict()"
        )

    # ── Pre/Post Processing ──────────────────────────────────────────

    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw inputs before prediction.

        Default: identity (pass-through).
        """
        return inputs

    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform prediction outputs before returning to client.

        Default: identity (pass-through).
        """
        return outputs

    # ── Observability ────────────────────────────────────────────────

    async def health(self) -> Dict[str, Any]:
        """
        Custom health check.

        Override to add model-specific health indicators.
        Default returns ``{"status": "ok"}``.
        """
        return {"status": "ok"}

    async def metrics(self) -> Dict[str, float]:
        """
        Custom metrics.

        Override to expose model-specific metrics.
        Default returns empty dict.
        """
        return {}


# ── @model Decorator ─────────────────────────────────────────────────────

def model(
    name: str,
    version: str = "v1",
    device: str = "auto",
    batch_size: int = 16,
    max_batch_latency_ms: float = 50.0,
    warmup_requests: int = 0,
    workers: int = 4,
    timeout_ms: float = 30000.0,
    tags: Optional[List[str]] = None,
    supports_streaming: bool = False,
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator that registers an ``AquiliaModel`` subclass with the model registry.

    Usage::

        @model(name="sentiment", version="v1", device="cuda:0")
        class SentimentModel(AquiliaModel):
            async def predict(self, inputs: dict) -> dict:
                ...

    The decorated class is registered at import time so the
    ``RouteGenerator`` can auto-create endpoints for it.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        # Store metadata on the class for later retrieval
        cls.__mlops_model_name__ = name       # type: ignore[attr-defined]
        cls.__mlops_model_version__ = version  # type: ignore[attr-defined]
        cls.__mlops_model_config__ = {        # type: ignore[attr-defined]
            "device": device,
            "batch_size": batch_size,
            "max_batch_latency_ms": max_batch_latency_ms,
            "warmup_requests": warmup_requests,
            "workers": workers,
            "timeout_ms": timeout_ms,
        }

        # Register with the global registry
        registry = _get_global_registry()
        registry.register_sync(
            name=name,
            model_class=cls,
            version=version,
            config={
                "device": device,
                "batch_size": batch_size,
                "max_batch_latency_ms": max_batch_latency_ms,
                "warmup_requests": warmup_requests,
                "workers": workers,
                "timeout_ms": timeout_ms,
            },
            supports_streaming=supports_streaming,
            tags=tags,
        )

        return cls

    return decorator
