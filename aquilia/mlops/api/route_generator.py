"""
Route Generator -- auto-generate Aquilia controller endpoints per model.

Scans the ``ModelRegistry`` and generates HTTP endpoints for each
registered model:

Per model:
- ``POST /mlops/models/{name}/predict``  -- sync inference
- ``POST /mlops/models/{name}/stream``   -- streaming (if supported)
- ``GET  /mlops/models/{name}/health``   -- per-model health
- ``GET  /mlops/models/{name}/metrics``  -- per-model metrics

Global:
- ``GET  /mlops/health``   -- aggregate health
- ``GET  /mlops/metrics``  -- aggregate metrics
- ``GET  /mlops/models``   -- list all models

Usage::

    gen = RouteGenerator(orchestrator, registry)
    route_definitions = gen.generate()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aquilia.mlops.api.route_generator")


@dataclass
class RouteDefinition:
    """A generated route definition ready for controller compilation."""
    method: str           # "GET" or "POST"
    path: str             # e.g. "/mlops/models/sentiment/predict"
    handler: Callable     # async handler function
    model_name: str = ""  # which model this route serves (empty = global)
    description: str = ""


class RouteGenerator:
    """
    Generates HTTP route definitions from registered models.

    These definitions can be used by the ``MLOpsController`` or compiled
    into Aquilia controllers dynamically.
    """

    def __init__(
        self,
        orchestrator: Any,   # ModelOrchestrator
        registry: Any,       # ModelRegistry
        prefix: str = "/mlops",
    ) -> None:
        self._orchestrator = orchestrator
        self._registry = registry
        self._prefix = prefix

    def generate(self) -> List[RouteDefinition]:
        """
        Generate all route definitions for all registered models.

        Returns a flat list of ``RouteDefinition`` objects.
        """
        routes: List[RouteDefinition] = []

        # Global routes
        routes.extend(self._generate_global_routes())

        # Per-model routes
        for model_name in self._registry.list_models():
            routes.extend(self._generate_model_routes(model_name))

        return routes

    # ── Global Routes ────────────────────────────────────────────────

    def _generate_global_routes(self) -> List[RouteDefinition]:
        """Generate global MLOps routes."""
        orch = self._orchestrator

        async def list_models_handler(ctx: Any = None) -> Dict[str, Any]:
            models = await orch.list_models()
            return {"models": models}

        async def global_health_handler(ctx: Any = None) -> Dict[str, Any]:
            return await orch.get_health()

        async def global_metrics_handler(ctx: Any = None) -> Dict[str, Any]:
            return await orch.get_metrics()

        return [
            RouteDefinition(
                method="GET",
                path=f"{self._prefix}/models",
                handler=list_models_handler,
                description="List all registered models",
            ),
            RouteDefinition(
                method="GET",
                path=f"{self._prefix}/health",
                handler=global_health_handler,
                description="Aggregate health check",
            ),
            RouteDefinition(
                method="GET",
                path=f"{self._prefix}/metrics",
                handler=global_metrics_handler,
                description="Aggregate metrics",
            ),
        ]

    # ── Per-Model Routes ─────────────────────────────────────────────

    def _generate_model_routes(self, model_name: str) -> List[RouteDefinition]:
        """Generate routes for a specific model."""
        orch = self._orchestrator
        entry = self._registry.get(model_name)
        if entry is None:
            return []

        routes: List[RouteDefinition] = []
        base = f"{self._prefix}/models/{model_name}"

        # POST /predict
        async def predict_handler(
            body: Dict[str, Any],
            ctx: Any = None,
            _name: str = model_name,
        ) -> Dict[str, Any]:
            headers = {}
            if ctx and hasattr(ctx, "headers"):
                headers = dict(ctx.headers) if ctx.headers else {}

            inputs = body.get("inputs", body.get("input", body))
            parameters = body.get("parameters", {})

            result = await orch.predict(
                model_name=_name,
                inputs=inputs,
                parameters=parameters,
                headers=headers,
            )
            return {
                "request_id": result.request_id,
                "outputs": result.outputs,
                "latency_ms": round(result.latency_ms, 2),
                "metadata": result.metadata,
            }

        routes.append(RouteDefinition(
            method="POST",
            path=f"{base}/predict",
            handler=predict_handler,
            model_name=model_name,
            description=f"Run prediction on {model_name}",
        ))

        # GET /health
        async def health_handler(
            ctx: Any = None,
            _name: str = model_name,
        ) -> Dict[str, Any]:
            return await orch.get_health(_name)

        routes.append(RouteDefinition(
            method="GET",
            path=f"{base}/health",
            handler=health_handler,
            model_name=model_name,
            description=f"Health check for {model_name}",
        ))

        # GET /metrics
        async def metrics_handler(
            ctx: Any = None,
            _name: str = model_name,
        ) -> Dict[str, Any]:
            return await orch.get_metrics(_name)

        routes.append(RouteDefinition(
            method="GET",
            path=f"{base}/metrics",
            handler=metrics_handler,
            model_name=model_name,
            description=f"Metrics for {model_name}",
        ))

        # POST /stream (only if model supports streaming)
        if entry.supports_streaming:
            async def stream_handler(
                body: Dict[str, Any],
                ctx: Any = None,
                _name: str = model_name,
            ) -> Any:
                inputs = body.get("inputs", body.get("input", body))
                parameters = body.get("parameters", {})

                # Return async generator for streaming response
                async def generate():
                    async for chunk in orch.stream_predict(
                        model_name=_name,
                        inputs=inputs,
                        parameters=parameters,
                    ):
                        yield {
                            "token": chunk.token,
                            "token_id": chunk.token_id,
                            "is_finished": chunk.is_finished,
                            "finish_reason": chunk.finish_reason,
                            "cumulative_tokens": chunk.cumulative_tokens,
                        }

                return generate()

            routes.append(RouteDefinition(
                method="POST",
                path=f"{base}/stream",
                handler=stream_handler,
                model_name=model_name,
                description=f"Streaming inference for {model_name}",
            ))

        return routes

    def route_table(self) -> List[Dict[str, str]]:
        """Return a human-readable route table."""
        routes = self.generate()
        return [
            {
                "method": r.method,
                "path": r.path,
                "model": r.model_name or "(global)",
                "description": r.description,
            }
            for r in routes
        ]
