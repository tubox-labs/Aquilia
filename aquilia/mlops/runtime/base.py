"""
Runtime base -- abstract interface for inference backends.

Provides ``BaseRuntime`` (standard) and ``BaseStreamingRuntime``
(for LLM/SLM with token-by-token streaming), both governed by
a ``ModelState`` finite-state machine.

State transitions::

    UNLOADED ──prepare()──▸ PREPARED ──load()──▸ LOADING ──(ok)──▸ LOADED
                                                   │
                                                 (fail)
                                                   │
                                                   ▾
                                                 FAILED ──load()──▸ LOADING  (retry)

    LOADED ──unload()──▸ UNLOADING ──(done)──▸ UNLOADED

Adding a new runtime backend (TensorRT, vLLM, custom) requires only
implementing the abstract methods.  No API-layer changes needed.
"""

from __future__ import annotations

import abc
import logging
import time
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

from .._types import (
    BatchRequest,
    InferenceRequest,
    InferenceResult,
    ModelpackManifest,
    StreamChunk,
    TokenUsage,
)

logger = logging.getLogger("aquilia.mlops.runtime")


# ── Model State FSM ──────────────────────────────────────────────────────

class ModelState(str, Enum):
    """
    Lifecycle states for a model runtime.

    The state machine enforces valid transitions and gives the orchestrator
    and health-check endpoints a clear view of model readiness.
    """
    UNLOADED = "unloaded"
    PREPARED = "prepared"      # artifacts downloaded / validated
    LOADING = "loading"        # model being loaded into memory / device
    LOADED = "loaded"          # ready for inference
    FAILED = "failed"          # load or inference caused a fatal error
    UNLOADING = "unloading"    # graceful shutdown in progress


# Legal transitions: (from_state) → {to_states}
_TRANSITIONS: Dict[ModelState, set] = {
    ModelState.UNLOADED:  {ModelState.PREPARED},
    ModelState.PREPARED:  {ModelState.LOADING, ModelState.UNLOADED},
    ModelState.LOADING:   {ModelState.LOADED, ModelState.FAILED},
    ModelState.LOADED:    {ModelState.UNLOADING, ModelState.FAILED},
    ModelState.FAILED:    {ModelState.LOADING, ModelState.UNLOADED},
    ModelState.UNLOADING: {ModelState.UNLOADED},
}


class InvalidStateTransition(RuntimeError):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, current: ModelState, target: ModelState) -> None:
        super().__init__(
            f"Invalid state transition: {current.value} → {target.value}. "
            f"Allowed targets from {current.value}: "
            f"{', '.join(s.value for s in _TRANSITIONS.get(current, set()))}"
        )
        self.current = current
        self.target = target


# ── Base Runtime ─────────────────────────────────────────────────────────

class BaseRuntime(abc.ABC):
    """
    Abstract runtime for model inference.

    Every runtime adapter must implement ``prepare``, ``load``, and ``infer``.
    Optional overrides: ``preprocess``, ``postprocess``, ``health``,
    ``metrics``, ``memory_info``.

    The ``_state`` attribute tracks the model lifecycle via ``ModelState``.
    Subclasses must call ``_set_state()`` to move through legal transitions.
    """

    def __init__(self) -> None:
        self._manifest: Optional[ModelpackManifest] = None
        self._model_dir: str = ""
        self._state: ModelState = ModelState.UNLOADED
        self._load_time_ms: float = 0.0
        self._device: str = "cpu"
        self._total_infer_count: int = 0
        self._total_infer_time_ms: float = 0.0
        self._last_error: Optional[str] = None

    # ── State Machine ────────────────────────────────────────────────

    @property
    def state(self) -> ModelState:
        """Current model lifecycle state."""
        return self._state

    @property
    def is_loaded(self) -> bool:
        """Backward-compatible loaded check."""
        return self._state == ModelState.LOADED

    def _set_state(self, target: ModelState) -> None:
        """
        Transition to ``target`` state.

        Raises ``InvalidStateTransition`` if the transition is not legal.
        """
        allowed = _TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise InvalidStateTransition(self._state, target)
        old = self._state
        self._state = target

    # ── Properties ───────────────────────────────────────────────────

    @property
    def manifest(self) -> Optional[ModelpackManifest]:
        return self._manifest

    @property
    def device(self) -> str:
        return self._device

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    # ── Abstract Interface ───────────────────────────────────────────

    @abc.abstractmethod
    async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None:
        """
        Prepare runtime with model artifacts (download, validate).

        Must transition state: UNLOADED → PREPARED.
        """

    @abc.abstractmethod
    async def load(self) -> None:
        """
        Load model into memory / accelerator.

        Must transition state: PREPARED|FAILED → LOADING → LOADED (or FAILED).
        """

    @abc.abstractmethod
    async def infer(self, batch: BatchRequest) -> List[InferenceResult]:
        """Run inference on a batch of requests."""

    # ── Optional Overrides ───────────────────────────────────────────

    async def preprocess(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw request inputs before inference.

        Override in subclasses for model-specific preprocessing.
        Default is identity (pass-through).
        """
        return raw_input

    async def postprocess(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw model outputs before returning to the client.

        Override in subclasses for model-specific postprocessing.
        Default is identity (pass-through).
        """
        return raw_output

    async def health(self) -> Dict[str, Any]:
        """Health check."""
        return {
            "status": self._state.value,
            "model": self._manifest.name if self._manifest else None,
            "version": self._manifest.version if self._manifest else None,
            "load_time_ms": self._load_time_ms,
            "device": self._device,
            "last_error": self._last_error,
        }

    async def metrics(self) -> Dict[str, float]:
        """Collect runtime-specific metrics."""
        avg = (
            self._total_infer_time_ms / self._total_infer_count
            if self._total_infer_count > 0 else 0.0
        )
        return {
            "state": float(self._state == ModelState.LOADED),
            "load_time_ms": self._load_time_ms,
            "total_infer_count": float(self._total_infer_count),
            "avg_infer_ms": avg,
        }

    async def unload(self) -> None:
        """Unload model and free resources."""
        if self._state == ModelState.UNLOADED:
            return
        self._set_state(ModelState.UNLOADING)
        self._manifest = None
        self._set_state(ModelState.UNLOADED)

    async def memory_info(self) -> Dict[str, Any]:
        """Return memory / device usage info (override in subclasses)."""
        return {"device": self._device, "state": self._state.value}

    def _detect_device(self) -> str:
        """Auto-detect best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"


# ── Streaming Runtime ────────────────────────────────────────────────────

class BaseStreamingRuntime(BaseRuntime):
    """
    Abstract runtime that adds streaming inference for LLM/SLM models.

    Subclasses must implement ``stream_infer`` in addition to ``infer``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._total_tokens_generated: int = 0
        self._total_prompt_tokens: int = 0
        self._total_stream_requests: int = 0

    @abc.abstractmethod
    async def stream_infer(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        """Stream tokens one at a time. Must be an async generator."""
        yield  # type: ignore[misc]

    async def token_usage(self) -> TokenUsage:
        """Return lifetime token usage statistics."""
        return TokenUsage(
            prompt_tokens=self._total_prompt_tokens,
            completion_tokens=self._total_tokens_generated,
            total_tokens=self._total_prompt_tokens + self._total_tokens_generated,
        )

    async def metrics(self) -> Dict[str, float]:
        """Extended metrics including token stats."""
        base = await super().metrics()
        base.update({
            "total_tokens_generated": float(self._total_tokens_generated),
            "total_prompt_tokens": float(self._total_prompt_tokens),
            "total_stream_requests": float(self._total_stream_requests),
        })
        return base


# ── Runtime Selection ────────────────────────────────────────────────────

def select_runtime(
    manifest: ModelpackManifest,
    preferred: Optional[str] = None,
    gpu_available: bool = False,
) -> BaseRuntime:
    """
    Select the best runtime for the given manifest.

    Selection logic:
    1. If ``preferred`` is specified, use that.
    2. If manifest is LLM/SLM → HuggingFace streaming runtime.
    3. If ONNX file exists → ONNXRuntimeAdapter.
    4. If Triton available + GPU → TritonAdapter.
    5. Fallback → PythonRuntime.
    """
    from .python_runtime import PythonRuntime

    if preferred == "onnxruntime":
        from .onnx_runtime import ONNXRuntimeAdapter
        return ONNXRuntimeAdapter()

    if preferred == "triton":
        from .triton_adapter import TritonAdapter
        return TritonAdapter()

    if preferred == "torchserve":
        from .torchserve_exporter import TorchServeExporter
        return TorchServeExporter()

    if preferred == "bentoml":
        from .bento_exporter import BentoExporter
        return BentoExporter()

    if preferred in ("huggingface", "vllm", "llamacpp", "ctransformers"):
        return PythonRuntime()  # PythonRuntime handles LLM frameworks

    # Auto-detect LLM models
    if manifest.is_llm:
        return PythonRuntime()

    # Auto-detect ONNX
    if manifest.entrypoint.endswith(".onnx"):
        try:
            from .onnx_runtime import ONNXRuntimeAdapter
            return ONNXRuntimeAdapter()
        except ImportError:
            pass

    if gpu_available:
        try:
            from .triton_adapter import TritonAdapter
            return TritonAdapter()
        except ImportError:
            pass

    return PythonRuntime()
