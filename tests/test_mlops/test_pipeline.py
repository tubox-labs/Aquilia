"""
Pipeline & Batching Tests — InferencePipeline execution and hook ordering.
"""

import asyncio
import pytest

from aquilia.mlops.engine.pipeline import InferencePipeline, PipelineContext
from aquilia.mlops.engine.hooks import (
    HookRegistry,
    collect_hooks,
    before_predict,
    after_predict,
    on_error,
    preprocess as preprocess_hook,
    postprocess as postprocess_hook,
)
from aquilia.mlops._types import InferenceRequest, InferenceResult, BatchRequest
from aquilia.mlops.api.model_class import AquiliaModel
from aquilia.mlops.runtime.base import ModelState

from .conftest import MockRuntime, MockModel


# ═══════════════════════════════════════════════════════════════════════
# InferencePipeline Tests
# ═══════════════════════════════════════════════════════════════════════

class TestInferencePipeline:
    """Test the async inference pipeline."""

    @pytest.fixture
    def loaded_runtime(self):
        """A runtime in LOADED state."""
        import asyncio
        rt = MockRuntime()
        from aquilia.mlops._types import ModelpackManifest
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        loop = asyncio.new_event_loop()
        loop.run_until_complete(rt.prepare(manifest, "/tmp"))
        loop.run_until_complete(rt.load())
        loop.close()
        return rt

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, loaded_runtime):
        pipeline = InferencePipeline(runtime=loaded_runtime)
        request = InferenceRequest(request_id="r1", inputs={"text": "hello"})

        result = await pipeline.execute(request, model_name="test")
        assert result.request_id == "r1"
        assert result.finish_reason == "stop"
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_stage_timings_recorded(self, loaded_runtime):
        pipeline = InferencePipeline(runtime=loaded_runtime)
        request = InferenceRequest(request_id="r1", inputs={"text": "hello"})

        result = await pipeline.execute(request)
        assert "stage_timings" in result.metadata
        timings = result.metadata["stage_timings"]
        assert "preprocess_ms" in timings
        assert "inference_ms" in timings
        assert "postprocess_ms" in timings

    @pytest.mark.asyncio
    async def test_trace_id_assigned(self, loaded_runtime):
        pipeline = InferencePipeline(runtime=loaded_runtime)
        request = InferenceRequest(request_id="r1", inputs={"text": "hello"})

        result = await pipeline.execute(request)
        assert "trace_id" in result.metadata

    @pytest.mark.asyncio
    async def test_batch_execute(self, loaded_runtime):
        pipeline = InferencePipeline(runtime=loaded_runtime)
        requests = [
            InferenceRequest(request_id=f"r{i}", inputs={"i": i})
            for i in range(5)
        ]

        results = await pipeline.execute_batch(requests)
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.request_id == f"r{i}"


# ═══════════════════════════════════════════════════════════════════════
# Pipeline Hook Ordering Tests
# ═══════════════════════════════════════════════════════════════════════

class TestPipelineHooks:
    """Test that hooks are called in the correct order."""

    @pytest.mark.asyncio
    async def test_hooks_called_in_order(self):
        """Hooks should fire: preprocess → before_predict → infer → after_predict → postprocess."""
        call_log = []

        class HookedModel(AquiliaModel):
            @preprocess_hook
            async def my_preprocess(self, inputs):
                call_log.append("preprocess")
                return inputs

            @before_predict
            async def my_before(self, **kwargs):
                call_log.append("before_predict")

            @after_predict
            async def my_after(self, **kwargs):
                call_log.append("after_predict")

            @postprocess_hook
            async def my_postprocess(self, outputs):
                call_log.append("postprocess")
                return outputs

            async def predict(self, inputs):
                return {"ok": True}

        instance = HookedModel()
        hooks = collect_hooks(instance)

        rt = MockRuntime()
        from aquilia.mlops._types import ModelpackManifest
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        await rt.prepare(manifest, "/tmp")
        await rt.load()

        pipeline = InferencePipeline(runtime=rt, hooks=hooks)
        request = InferenceRequest(request_id="r1", inputs={"text": "hello"})
        await pipeline.execute(request)

        assert call_log == ["preprocess", "before_predict", "after_predict", "postprocess"]

    @pytest.mark.asyncio
    async def test_on_error_hook_called(self):
        """on_error hook should fire when the pipeline encounters an error."""
        error_log = []

        class ErrorModel(AquiliaModel):
            @on_error
            async def my_error_handler(self, exc, request):
                error_log.append(str(exc))
                return {"handled": True}

            async def predict(self, inputs):
                return inputs

        instance = ErrorModel()
        hooks = collect_hooks(instance)

        # Use a runtime that fails on infer
        rt = MockRuntime(fail_on_infer=True)
        from aquilia.mlops._types import ModelpackManifest
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        await rt.prepare(manifest, "/tmp")
        await rt.load()

        pipeline = InferencePipeline(runtime=rt, hooks=hooks)
        request = InferenceRequest(request_id="r1", inputs={"text": "hello"})

        result = await pipeline.execute(request)
        assert result.finish_reason == "error"
        assert len(error_log) == 1
        assert "Simulated inference failure" in error_log[0]


# ═══════════════════════════════════════════════════════════════════════
# Manifest Config Tests
# ═══════════════════════════════════════════════════════════════════════

class TestManifestConfig:
    """Test manifest configuration parsing and validation."""

    def test_parse_minimal_config(self):
        from aquilia.mlops.manifest.config import parse_mlops_config

        config = {"enabled": True}
        result = parse_mlops_config(config)
        assert result.enabled is True
        assert len(result.models) == 0

    def test_parse_with_models(self):
        from aquilia.mlops.manifest.config import parse_mlops_config

        config = {
            "enabled": True,
            "default_device": "cpu",
            "models": {
                "sentiment": {
                    "class": "myapp.models.SentimentModel",
                    "version": "v1",
                    "device": "cuda:0",
                    "batch_size": 32,
                },
            },
        }
        result = parse_mlops_config(config)
        assert len(result.models) == 1
        assert result.models[0].name == "sentiment"
        assert result.models[0].device == "cuda:0"
        assert result.models[0].batch_size == 32

    def test_parse_inherits_defaults(self):
        from aquilia.mlops.manifest.config import parse_mlops_config

        config = {
            "default_workers": 8,
            "default_batch_size": 64,
            "models": {
                "echo": {
                    "class": "myapp.EchoModel",
                },
            },
        }
        result = parse_mlops_config(config)
        assert result.models[0].workers == 8
        assert result.models[0].batch_size == 64

    def test_validation_rejects_bad_class_path(self):
        from aquilia.mlops.manifest.config import parse_mlops_config
        from aquilia.mlops.manifest.schema import validate_manifest_config

        config = {
            "models": {
                "bad": {
                    "class": "NoDots",
                    "version": "v1",
                },
            },
        }
        result = parse_mlops_config(config)
        errors = validate_manifest_config(result)
        assert len(errors) > 0
        assert any("dotted path" in e for e in errors)

    def test_validation_rejects_zero_batch_size(self):
        from aquilia.mlops.manifest.config import parse_mlops_config
        from aquilia.mlops.manifest.schema import validate_manifest_config

        config = {
            "models": {
                "bad": {
                    "class": "myapp.Model",
                    "batch_size": 0,
                },
            },
        }
        result = parse_mlops_config(config)
        errors = validate_manifest_config(result)
        assert any("batch_size" in e for e in errors)

    def test_validation_passes_good_config(self):
        from aquilia.mlops.manifest.config import parse_mlops_config
        from aquilia.mlops.manifest.schema import validate_manifest_config

        config = {
            "models": {
                "echo": {
                    "class": "myapp.models.EchoModel",
                    "version": "v1",
                    "device": "cpu",
                    "batch_size": 16,
                    "workers": 4,
                },
            },
        }
        result = parse_mlops_config(config)
        errors = validate_manifest_config(result)
        assert len(errors) == 0

    def test_validation_rejects_duplicate_entries(self):
        from aquilia.mlops.manifest.config import MLOpsManifestConfig, ModelManifestEntry
        from aquilia.mlops.manifest.schema import validate_manifest_config

        cfg = MLOpsManifestConfig(models=[
            ModelManifestEntry(name="dup", version="v1", class_path="a.B"),
            ModelManifestEntry(name="dup", version="v1", class_path="c.D"),
        ])
        errors = validate_manifest_config(cfg)
        assert any("duplicate" in e.lower() for e in errors)
