"""
Inference Pipeline — async preprocess → batch/infer → postprocess pipeline.

Each inference request flows through this pipeline:

1. ``preprocess`` hooks (model-specific input transformation)
2. ``before_predict`` hooks (cross-cutting pre-inference)
3. Inference via batcher or direct runtime call
4. ``after_predict`` hooks (cross-cutting post-inference)
5. ``postprocess`` hooks (model-specific output transformation)

Every stage is wrapped with:
- Timing (per-stage latency recorded in metrics)
- Error handling (``on_error`` hooks called, fallback result returned)
- Async-safe execution

Usage::

    pipeline = InferencePipeline(
        runtime=my_runtime,
        hooks=hook_registry,
        metrics=metrics_collector,
        executor=inference_executor,
    )
    result = await pipeline.execute(request)
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .._types import (
    BatchRequest,
    InferenceRequest,
    InferenceResult,
)
from ..runtime.base import BaseRuntime, ModelState
from .hooks import HookRegistry

logger = logging.getLogger("aquilia.mlops.engine.pipeline")


@dataclass
class PipelineContext:
    """Per-request context flowing through the pipeline."""
    request_id: str
    model_name: str = ""
    model_version: str = ""
    trace_id: str = ""
    start_time: float = field(default_factory=time.monotonic)
    stage_timings: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InferencePipeline:
    """
    Async inference pipeline with hooks and metrics.

    Manages the full lifecycle of a single prediction request,
    calling hooks in order and recording metrics at each stage.
    """

    def __init__(
        self,
        runtime: BaseRuntime,
        hooks: Optional[HookRegistry] = None,
        metrics_collector: Any = None,
        executor: Any = None,  # InferenceExecutor
    ) -> None:
        self._runtime = runtime
        self._hooks = hooks or HookRegistry()
        self._metrics = metrics_collector
        self._executor = executor

    # ── Main Execute ─────────────────────────────────────────────────

    async def execute(
        self,
        request: InferenceRequest,
        model_name: str = "",
        model_version: str = "",
    ) -> InferenceResult:
        """
        Execute the full inference pipeline for a single request.

        Returns an ``InferenceResult`` regardless of success or failure.
        """
        ctx = PipelineContext(
            request_id=request.request_id,
            model_name=model_name,
            model_version=model_version,
            trace_id=str(uuid.uuid4())[:8],
        )

        try:
            # Stage 1: Preprocess
            inputs = await self._run_preprocess(request.inputs, ctx)

            # Stage 2: Before-predict hooks
            await self._run_hooks("before_predict", ctx, inputs=inputs)

            # Stage 3: Inference
            preprocessed_request = InferenceRequest(
                request_id=request.request_id,
                inputs=inputs,
                parameters=request.parameters,
                timestamp=request.timestamp,
                priority=request.priority,
                stream=request.stream,
                max_tokens=request.max_tokens,
                timeout_ms=request.timeout_ms,
            )
            result = await self._run_inference(preprocessed_request, ctx)

            # Stage 4: After-predict hooks
            await self._run_hooks("after_predict", ctx, result=result)

            # Stage 5: Postprocess
            result.outputs = await self._run_postprocess(result.outputs, ctx)

            # Record total latency
            total_ms = (time.monotonic() - ctx.start_time) * 1000
            result.latency_ms = total_ms
            result.metadata["stage_timings"] = ctx.stage_timings
            result.metadata["trace_id"] = ctx.trace_id

            # Record metrics
            if self._metrics:
                self._metrics.record_inference(
                    latency_ms=total_ms,
                    batch_size=1,
                    model_name=model_name,
                    token_count=result.token_count,
                    prompt_tokens=result.prompt_tokens,
                )

            return result

        except Exception as exc:
            return await self._handle_error(exc, request, ctx)

    # ── Pipeline Stages ──────────────────────────────────────────────

    async def _run_preprocess(
        self, inputs: Dict[str, Any], ctx: PipelineContext,
    ) -> Dict[str, Any]:
        """Run preprocess hooks, then runtime.preprocess()."""
        start = time.monotonic()

        # Model-class preprocess hooks
        for hook in self._hooks.preprocess:
            inputs = await self._call_hook(hook, inputs)

        # Runtime-level preprocess
        inputs = await self._runtime.preprocess(inputs)

        ctx.stage_timings["preprocess_ms"] = (time.monotonic() - start) * 1000
        return inputs

    async def _run_inference(
        self, request: InferenceRequest, ctx: PipelineContext,
    ) -> InferenceResult:
        """Run inference through the executor or directly."""
        start = time.monotonic()

        batch = BatchRequest(requests=[request], batch_id=ctx.trace_id)

        if self._executor and self._executor.is_running:
            # Offload blocking inference to thread pool
            results = await self._executor.submit(
                self._sync_infer_wrapper, batch,
            )
        else:
            results = await self._runtime.infer(batch)

        ctx.stage_timings["inference_ms"] = (time.monotonic() - start) * 1000

        if results:
            return results[0]

        return InferenceResult(
            request_id=request.request_id,
            outputs={},
            finish_reason="error",
            metadata={"error": "No results from runtime"},
        )

    def _sync_infer_wrapper(self, batch: BatchRequest) -> List[InferenceResult]:
        """Wrapper to run async infer in a sync context for the executor."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._runtime.infer(batch))
        finally:
            loop.close()

    async def _run_postprocess(
        self, outputs: Dict[str, Any], ctx: PipelineContext,
    ) -> Dict[str, Any]:
        """Run runtime.postprocess(), then postprocess hooks."""
        start = time.monotonic()

        # Runtime-level postprocess
        outputs = await self._runtime.postprocess(outputs)

        # Model-class postprocess hooks
        for hook in self._hooks.postprocess:
            outputs = await self._call_hook(hook, outputs)

        ctx.stage_timings["postprocess_ms"] = (time.monotonic() - start) * 1000
        return outputs

    # ── Hook Execution ───────────────────────────────────────────────

    async def _run_hooks(
        self,
        kind: str,
        ctx: PipelineContext,
        **kwargs: Any,
    ) -> None:
        """Run all hooks of a given kind."""
        hooks = self._hooks.get(kind)
        if not hooks:
            return

        start = time.monotonic()
        for hook in hooks:
            await self._call_hook(hook, **kwargs)
        ctx.stage_timings[f"{kind}_ms"] = (time.monotonic() - start) * 1000

    async def _call_hook(self, hook: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call a hook, handling both sync and async callables."""
        try:
            if inspect.iscoroutinefunction(hook):
                return await hook(*args, **kwargs)
            else:
                return hook(*args, **kwargs)
        except Exception:
            logger.exception("Hook %s raised an exception", getattr(hook, "__name__", hook))
            raise

    # ── Error Handling ───────────────────────────────────────────────

    async def _handle_error(
        self,
        exc: Exception,
        request: InferenceRequest,
        ctx: PipelineContext,
    ) -> InferenceResult:
        """Handle pipeline errors — call on_error hooks, return error result."""
        total_ms = (time.monotonic() - ctx.start_time) * 1000

        logger.error(
            "Pipeline error for request %s: %s", request.request_id, exc,
        )

        # Call on_error hooks
        error_result: Optional[Dict[str, Any]] = None
        for hook in self._hooks.on_error:
            try:
                result = await self._call_hook(hook, exc, request)
                if isinstance(result, dict):
                    error_result = result
            except Exception:
                logger.exception("on_error hook raised")

        # Record error in metrics
        if self._metrics:
            self._metrics.record_inference(
                latency_ms=total_ms,
                error=True,
                model_name=ctx.model_name,
            )

        return InferenceResult(
            request_id=request.request_id,
            outputs=error_result or {"error": str(exc)},
            latency_ms=total_ms,
            finish_reason="error",
            metadata={
                "error_type": type(exc).__name__,
                "stage_timings": ctx.stage_timings,
                "trace_id": ctx.trace_id,
            },
        )

    # ── Batch Execute ────────────────────────────────────────────────

    async def execute_batch(
        self,
        requests: List[InferenceRequest],
        model_name: str = "",
        model_version: str = "",
    ) -> List[InferenceResult]:
        """Execute the pipeline for multiple requests concurrently."""
        tasks = [
            self.execute(req, model_name, model_version)
            for req in requests
        ]
        return await asyncio.gather(*tasks)
