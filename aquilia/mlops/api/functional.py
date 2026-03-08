"""
Functional Serving -- ``@serve`` decorator for minimal model definitions.

For rapid prototyping or simple models where a full class is overkill,
``@serve`` wraps a plain function into an ``AquiliaModel`` subclass
and registers it.

Usage::

    from aquilia.mlops import serve

    @serve(name="echo", version="v1")
    async def echo_model(inputs: dict) -> dict:
        return {"echo": inputs.get("text", "")}

    # Equivalent to:
    #
    # @model(name="echo", version="v1")
    # class EchoModel(AquiliaModel):
    #     async def predict(self, inputs: dict) -> dict:
    #         return {"echo": inputs.get("text", "")}
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

from .model_class import AquiliaModel, _get_global_registry

logger = logging.getLogger("aquilia.mlops.api.functional")


def serve(
    name: str,
    version: str = "v1",
    device: str = "auto",
    batch_size: int = 16,
    max_batch_latency_ms: float = 50.0,
    workers: int = 4,
    tags: Optional[List[str]] = None,
) -> Callable:
    """
    Decorator that wraps a function into a registered model.

    The function should accept a ``dict`` and return a ``dict``.
    It can be sync or async.

    Usage::

        @serve(name="add", version="v1")
        def add_model(inputs: dict) -> dict:
            return {"sum": inputs["a"] + inputs["b"]}

        @serve(name="async_echo")
        async def echo(inputs: dict) -> dict:
            return {"echo": inputs["text"]}
    """

    def decorator(fn: Callable) -> Callable:
        # Determine if the function is async
        is_async = inspect.iscoroutinefunction(fn)

        # Dynamically create an AquiliaModel subclass
        if is_async:
            class _FunctionalModel(AquiliaModel):
                async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                    result = await fn(inputs)
                    if not isinstance(result, dict):
                        return {"prediction": result}
                    return result
        else:
            class _FunctionalModel(AquiliaModel):
                async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                    result = fn(inputs)
                    if not isinstance(result, dict):
                        return {"prediction": result}
                    return result

        # Give the class a meaningful name
        _FunctionalModel.__name__ = f"_Serve_{fn.__name__}"
        _FunctionalModel.__qualname__ = f"_Serve_{fn.__name__}"

        # Store metadata
        _FunctionalModel.__mlops_model_name__ = name       # type: ignore[attr-defined]
        _FunctionalModel.__mlops_model_version__ = version  # type: ignore[attr-defined]

        # Register with global registry
        registry = _get_global_registry()
        registry.register_sync(
            name=name,
            model_class=_FunctionalModel,
            version=version,
            config={
                "device": device,
                "batch_size": batch_size,
                "max_batch_latency_ms": max_batch_latency_ms,
                "workers": workers,
            },
            tags=tags,
        )

        # Preserve the original function for direct calling
        fn.__mlops_model_class__ = _FunctionalModel  # type: ignore[attr-defined]
        fn.__mlops_model_name__ = name                # type: ignore[attr-defined]

        return fn

    return decorator
