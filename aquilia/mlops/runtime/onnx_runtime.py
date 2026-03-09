"""
ONNX Runtime adapter -- high-performance inference via onnxruntime.

Requires ``onnxruntime`` or ``onnxruntime-gpu`` (optional dependency).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .._types import BatchRequest, InferenceResult, ModelpackManifest
from .base import BaseRuntime, ModelState

logger = logging.getLogger("aquilia.mlops.runtime.onnx")


class ONNXRuntimeAdapter(BaseRuntime):
    """
    ONNX Runtime inference adapter.

    Uses ``onnxruntime.InferenceSession`` for high-performance CPU/GPU inference.
    """

    def __init__(
        self,
        providers: Optional[List[str]] = None,
        session_options: Optional[Any] = None,
    ):
        super().__init__()
        self._session: Any = None
        self._providers = providers
        self._session_options = session_options
        self._inference_count: int = 0
        self._total_latency_ms: float = 0.0

    async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None:
        self._set_state(ModelState.PREPARED)
        self._manifest = manifest
        self._model_dir = model_dir

    async def load(self) -> None:
        if not self._manifest:
            from aquilia.faults.domains import ConfigMissingFault
            raise ConfigMissingFault(key="mlops.runtime.manifest")

        self._set_state(ModelState.LOADING)

        try:
            import onnxruntime as ort
        except ImportError:
            self._set_state(ModelState.FAILED)
            raise ImportError(
                "onnxruntime required. Install with: pip install onnxruntime"
            )

        start = time.monotonic()

        model_path = Path(self._model_dir) / "model" / self._manifest.entrypoint
        if not model_path.exists():
            model_path = Path(self._model_dir) / self._manifest.entrypoint

        if not model_path.exists():
            self._set_state(ModelState.FAILED)
            raise FileNotFoundError(f"ONNX model not found: {model_path}")

        try:
            providers = self._providers or ort.get_available_providers()
            sess_opts = self._session_options or ort.SessionOptions()

            self._session = ort.InferenceSession(
                str(model_path), sess_options=sess_opts, providers=providers
            )
        except Exception:
            self._set_state(ModelState.FAILED)
            raise

        self._set_state(ModelState.LOADED)
        self._load_time_ms = (time.monotonic() - start) * 1000

    async def infer(self, batch: BatchRequest) -> List[InferenceResult]:
        if not self._session:
            from aquilia.faults.domains import ConfigMissingFault
            raise ConfigMissingFault(key="mlops.runtime.session")

        results: List[InferenceResult] = []
        input_names = [inp.name for inp in self._session.get_inputs()]
        output_names = [out.name for out in self._session.get_outputs()]

        for req in batch.requests:
            start = time.monotonic()

            # Build feed dict
            feed: Dict[str, Any] = {}
            for name in input_names:
                if name in req.inputs:
                    val = req.inputs[name]
                    if not isinstance(val, np.ndarray):
                        val = np.array(val)
                    feed[name] = val

            raw_outputs = self._session.run(output_names, feed)
            outputs = {
                name: out.tolist() if isinstance(out, np.ndarray) else out
                for name, out in zip(output_names, raw_outputs)
            }

            latency = (time.monotonic() - start) * 1000
            self._inference_count += 1
            self._total_latency_ms += latency

            results.append(InferenceResult(
                request_id=req.request_id,
                outputs=outputs,
                latency_ms=latency,
            ))

        return results

    async def metrics(self) -> Dict[str, float]:
        base = await super().metrics()
        avg = self._total_latency_ms / max(self._inference_count, 1)
        base.update({
            "inference_count": float(self._inference_count),
            "avg_latency_ms": avg,
        })
        return base

    async def unload(self) -> None:
        self._session = None
        await super().unload()
