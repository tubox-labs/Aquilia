"""
Model Orchestrator -- top-level façade for ML inference.

The orchestrator ties together:
- ``ModelRegistry``  -- knows what models exist
- ``VersionRouter``  -- picks the right version per request
- ``ModelLoader``    -- lazy-loads models on first request
- ``InferencePipeline`` -- runs preprocess → infer → postprocess

This is the single entry point the API layer calls.  It knows nothing
about HTTP, controllers, or routing -- only model identity and inference.

Usage::

    orch = ModelOrchestrator(registry, router, loader)
    result = await orch.predict("sentiment", {"text": "great product"})
    health = await orch.get_health("sentiment")
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from .._types import (
    InferenceRequest,
    InferenceResult,
    StreamChunk,
)
from ..runtime.base import ModelState
from .registry import ModelRegistry
from .router import VersionRouter
from .loader import ModelLoader

logger = logging.getLogger("aquilia.mlops.orchestrator")


class ModelOrchestrator:
    """
    Top-level inference façade.

    Every prediction flows through:
    ``route(model_name) → ensure_loaded(name, version) → pipeline.execute(request)``
    """

    def __init__(
        self,
        registry: ModelRegistry,
        router: VersionRouter,
        loader: ModelLoader,
    ) -> None:
        self._registry = registry
        self._router = router
        self._loader = loader

    # ── Inference ────────────────────────────────────────────────────

    async def predict(
        self,
        model_name: str,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_id: str = "",
    ) -> InferenceResult:
        """
        Run a prediction through the full orchestrated pipeline.

        1. Resolve version (canary / header / active)
        2. Lazy-load the model if not yet loaded
        3. Execute the inference pipeline
        4. Return the result
        """
        import uuid

        if not request_id:
            request_id = str(uuid.uuid4())

        # Step 1: Route to the correct version
        version = await self._router.route(model_name, headers=headers)

        # Step 2: Ensure the model is loaded
        loaded = await self._loader.ensure_loaded(model_name, version)

        # Step 3: Build the inference request
        request = InferenceRequest(
            request_id=request_id,
            inputs=inputs,
            parameters=parameters or {},
        )

        # Step 4: Execute the pipeline
        result = await loaded.pipeline.execute(
            request,
            model_name=model_name,
            model_version=version,
        )

        return result

    async def predict_batch(
        self,
        model_name: str,
        batch_inputs: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[InferenceResult]:
        """Run batch predictions."""
        import uuid

        version = await self._router.route(model_name, headers=headers)
        loaded = await self._loader.ensure_loaded(model_name, version)

        requests = [
            InferenceRequest(
                request_id=str(uuid.uuid4()),
                inputs=inp,
                parameters=parameters or {},
            )
            for inp in batch_inputs
        ]

        return await loaded.pipeline.execute_batch(
            requests,
            model_name=model_name,
            model_version=version,
        )

    async def stream_predict(
        self,
        model_name: str,
        inputs: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_id: str = "",
    ) -> AsyncIterator[StreamChunk]:
        """Stream inference for LLM models."""
        import uuid
        from ..runtime.base import BaseStreamingRuntime

        if not request_id:
            request_id = str(uuid.uuid4())

        version = await self._router.route(model_name, headers=headers)
        loaded = await self._loader.ensure_loaded(model_name, version)

        # Check if the runtime supports streaming
        runtime = loaded.pipeline._runtime
        if not isinstance(runtime, BaseStreamingRuntime):
            raise RuntimeError(
                f"Model '{model_name}:{version}' does not support streaming inference"
            )

        request = InferenceRequest(
            request_id=request_id,
            inputs=inputs,
            parameters=parameters or {},
            stream=True,
        )

        async for chunk in runtime.stream_infer(request):
            yield chunk

    # ── Health & Metrics ─────────────────────────────────────────────

    async def get_health(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get health status for one model or all models.

        Returns per-model state, load time, and device info.
        """
        if model_name:
            entry = self._registry.get(model_name)
            if entry is None:
                return {"error": f"Model '{model_name}' not found", "status": "not_found"}

            loaded = self._loader.get_loaded(model_name, entry.version)
            return {
                "model": model_name,
                "version": entry.version,
                "state": entry.state.value,
                "load_time_ms": loaded.load_time_ms if loaded else 0.0,
                "config": {
                    "device": entry.config.device,
                    "batch_size": entry.config.batch_size,
                },
            }

        # Aggregate health
        models = {}
        for name in self._registry.list_models():
            entry = self._registry.get(name)
            if entry:
                models[name] = {
                    "version": entry.version,
                    "state": entry.state.value,
                }

        loaded_count = len(self._loader.loaded_models())
        total = len(self._registry.list_models())

        return {
            "status": "healthy" if loaded_count > 0 or total == 0 else "degraded",
            "models_registered": total,
            "models_loaded": loaded_count,
            "models": models,
        }

    async def get_metrics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for one model or all models."""
        if model_name:
            entry = self._registry.get(model_name)
            if entry is None:
                return {"error": f"Model '{model_name}' not found"}

            loaded = self._loader.get_loaded(model_name, entry.version)
            if loaded:
                runtime = loaded.pipeline._runtime
                return await runtime.metrics()
            return {"state": entry.state.value, "loaded": False}

        # Aggregate metrics
        result = {
            "registry": self._registry.summary(),
            "loader": self._loader.summary(),
            "router": self._router.summary(),
        }
        return result

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models with their status."""
        models = []
        for entry in self._registry.list_entries():
            models.append(entry.to_dict())
        return models

    # ── Management ───────────────────────────────────────────────────

    async def reload_model(self, model_name: str, version: str) -> Dict[str, Any]:
        """Hot-reload a model to a specific version."""
        loaded = await self._loader.hot_reload(model_name, version)
        return {
            "model": model_name,
            "version": version,
            "state": loaded.entry.state.value,
            "load_time_ms": loaded.load_time_ms,
        }

    async def unload_model(self, model_name: str, version: Optional[str] = None) -> bool:
        """Unload a specific model version."""
        if version is None:
            version = self._registry.get_active_version(model_name)
            if version is None:
                return False
        return await self._loader.unload(model_name, version)

    async def shutdown(self) -> None:
        """Graceful shutdown -- unload all models."""
        await self._loader.unload_all()
        logger.info("ModelOrchestrator shutdown complete")
