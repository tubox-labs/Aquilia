"""
Shared fixtures for MLOps tests.

All tests run WITHOUT real ML frameworks (PyTorch, ONNX, etc.)
by using mock runtimes and model classes.
"""

import asyncio
import pytest
from typing import Any, Dict, List

from aquilia.mlops.runtime.base import BaseRuntime, ModelState
from aquilia.mlops._types import BatchRequest, InferenceRequest, InferenceResult
from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.router import VersionRouter
from aquilia.mlops.orchestrator.versioning import VersionManager
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.api.model_class import AquiliaModel
from aquilia.mlops.engine.hooks import HookRegistry
from aquilia.mlops.engine.pipeline import InferencePipeline
from aquilia.mlops.runtime.executor import InferenceExecutor
from aquilia.mlops.runtime.device_manager import DeviceManager


# ── Mock Runtime ─────────────────────────────────────────────────────────

class MockRuntime(BaseRuntime):
    """A mock runtime that returns predictable results without ML dependencies."""

    def __init__(self, fail_on_load: bool = False, fail_on_infer: bool = False):
        super().__init__()
        self._fail_on_load = fail_on_load
        self._fail_on_infer = fail_on_infer
        self._infer_calls: List[BatchRequest] = []

    async def prepare(self, manifest, model_dir):
        self._set_state(ModelState.PREPARED)
        self._manifest = manifest
        self._model_dir = model_dir

    async def load(self):
        self._set_state(ModelState.LOADING)
        if self._fail_on_load:
            self._last_error = "Simulated load failure"
            self._set_state(ModelState.FAILED)
            raise RuntimeError("Simulated load failure")
        self._set_state(ModelState.LOADED)

    async def infer(self, batch: BatchRequest) -> List[InferenceResult]:
        if self._state != ModelState.LOADED:
            raise RuntimeError(
                f"Model not loaded (state={self._state.value}). Call load() first."
            )
        if self._fail_on_infer:
            raise RuntimeError("Simulated inference failure")

        self._infer_calls.append(batch)
        results = []
        for req in batch.requests:
            self._total_infer_count += 1
            results.append(InferenceResult(
                request_id=req.request_id,
                outputs={"echo": req.inputs, "model": "mock"},
                latency_ms=1.0,
                finish_reason="stop",
            ))
        return results


# ── Mock Model Class ─────────────────────────────────────────────────────

class MockModel(AquiliaModel):
    """A mock AquiliaModel for testing."""

    def __init__(self):
        self.load_called = False
        self.unload_called = False
        self.predict_count = 0

    async def load(self, artifacts_dir: str, device: str):
        self.load_called = True
        self.device = device

    async def unload(self):
        self.unload_called = True

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.predict_count += 1
        return {"echo": inputs, "model": "mock"}

    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Add a marker that preprocess ran
        inputs["_preprocessed"] = True
        return inputs

    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        outputs["_postprocessed"] = True
        return outputs


class FailingModel(AquiliaModel):
    """A model that fails on predict for error testing."""

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        raise ValueError("Simulated prediction failure")


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_manifest():
    """Create a minimal ModelpackManifest for testing."""
    from aquilia.mlops._types import ModelpackManifest
    return ModelpackManifest(
        name="test-model",
        version="v1",
        framework="custom",
        entrypoint="model.py",
    )


@pytest.fixture
def mock_runtime():
    """Create a MockRuntime instance."""
    return MockRuntime()


@pytest.fixture
def failing_runtime():
    """Create a runtime that fails on load."""
    return MockRuntime(fail_on_load=True)


@pytest.fixture
def model_registry():
    """Create a fresh ModelRegistry."""
    return ModelRegistry()


@pytest.fixture
def executor():
    """Create an InferenceExecutor."""
    return InferenceExecutor(max_workers=2)


@pytest.fixture
def device_manager():
    """Create a DeviceManager."""
    return DeviceManager()
