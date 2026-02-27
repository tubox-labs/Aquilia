"""
Failure Mode Tests — bad input, runtime failure, device failure, timeouts.
"""

import asyncio
import pytest

from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.router import VersionRouter
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.runtime.base import ModelState, InvalidStateTransition
from aquilia.mlops._types import ModelpackManifest

from .conftest import MockRuntime, MockModel, FailingModel


# ═══════════════════════════════════════════════════════════════════════
# Bad Input Tests
# ═══════════════════════════════════════════════════════════════════════

class TestBadInput:
    """Test behavior with invalid or malformed inputs."""

    @pytest.mark.asyncio
    async def test_empty_inputs(self):
        registry = ModelRegistry()
        await registry.register("echo", MockModel, version="v1")
        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        # Empty dict should still work (model just echoes it)
        result = await orch.predict("echo", {})
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_model_not_found_raises(self):
        registry = ModelRegistry()
        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        with pytest.raises(KeyError, match="not registered"):
            await orch.predict("nonexistent", {"text": "test"})

    @pytest.mark.asyncio
    async def test_nonexistent_health(self):
        registry = ModelRegistry()
        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        health = await orch.get_health("nonexistent")
        assert "error" in health or health.get("status") == "not_found"


# ═══════════════════════════════════════════════════════════════════════
# Runtime Failure Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRuntimeFailure:
    """Test runtime load and inference failures."""

    @pytest.mark.asyncio
    async def test_load_failure_sets_failed_state(self):
        runtime = MockRuntime(fail_on_load=True)
        manifest = ModelpackManifest(
            name="fail", version="v1", framework="custom", entrypoint="model.py",
        )
        await runtime.prepare(manifest, "/tmp")

        with pytest.raises(RuntimeError):
            await runtime.load()
        assert runtime.state == ModelState.FAILED
        assert runtime.last_error is not None

    @pytest.mark.asyncio
    async def test_infer_on_unloaded_runtime_raises(self):
        runtime = MockRuntime()
        from aquilia.mlops._types import BatchRequest, InferenceRequest

        batch = BatchRequest(requests=[
            InferenceRequest(request_id="r1", inputs={"text": "hello"}),
        ])

        with pytest.raises(RuntimeError, match="not loaded"):
            await runtime.infer(batch)

    @pytest.mark.asyncio
    async def test_failing_model_returns_error_result(self):
        """A model that raises in predict() should return an error result, not crash."""
        registry = ModelRegistry()
        await registry.register("failing", FailingModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        result = await orch.predict("failing", {"text": "test"})
        # The pipeline should catch the error and return an error result
        assert result.finish_reason == "error" or "error" in result.outputs

    @pytest.mark.asyncio
    async def test_runtime_retry_after_failure(self):
        """After a load failure, a retry should succeed."""
        runtime = MockRuntime(fail_on_load=True)
        manifest = ModelpackManifest(
            name="retry", version="v1", framework="custom", entrypoint="model.py",
        )
        await runtime.prepare(manifest, "/tmp")

        with pytest.raises(RuntimeError):
            await runtime.load()
        assert runtime.state == ModelState.FAILED

        # Fix and retry
        runtime._fail_on_load = False
        await runtime.load()
        assert runtime.state == ModelState.LOADED


# ═══════════════════════════════════════════════════════════════════════
# State Machine Violation Tests
# ═══════════════════════════════════════════════════════════════════════

class TestStateViolations:
    """Test that invalid state transitions are caught."""

    def test_unloaded_to_loaded_is_invalid(self):
        runtime = MockRuntime()
        with pytest.raises(InvalidStateTransition):
            runtime._set_state(ModelState.LOADED)

    def test_unloaded_to_loading_is_invalid(self):
        runtime = MockRuntime()
        with pytest.raises(InvalidStateTransition):
            runtime._set_state(ModelState.LOADING)

    def test_loaded_to_prepared_is_invalid(self):
        runtime = MockRuntime()
        runtime._state = ModelState.LOADED

        with pytest.raises(InvalidStateTransition):
            runtime._set_state(ModelState.PREPARED)

    def test_error_message_is_descriptive(self):
        runtime = MockRuntime()
        try:
            runtime._set_state(ModelState.LOADED)
        except InvalidStateTransition as e:
            assert "unloaded" in str(e).lower()
            assert "loaded" in str(e).lower()
            assert "allowed" in str(e).lower()


# ═══════════════════════════════════════════════════════════════════════
# Device Fallback Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDeviceFallback:
    """Test device selection fallback behavior."""

    @pytest.mark.asyncio
    async def test_unavailable_device_falls_back(self):
        from aquilia.mlops.runtime.device_manager import DeviceManager
        dm = DeviceManager()
        await dm.initialize()

        # Request a device that doesn't exist
        device = await dm.select_device("cuda:99")
        # Should fall back to something available
        assert device in ["cpu", "mps"] or device.startswith("cuda:")

    @pytest.mark.asyncio
    async def test_auto_always_returns_something(self):
        from aquilia.mlops.runtime.device_manager import DeviceManager
        dm = DeviceManager()
        await dm.initialize()

        device = await dm.select_device("auto")
        assert device is not None
        assert len(device) > 0

    @pytest.mark.asyncio
    async def test_cpu_always_works(self):
        from aquilia.mlops.runtime.device_manager import DeviceManager
        dm = DeviceManager()
        await dm.initialize()

        device = await dm.select_device("cpu")
        assert device == "cpu"


# ═══════════════════════════════════════════════════════════════════════
# Executor Failure Tests
# ═══════════════════════════════════════════════════════════════════════

class TestExecutorFailures:
    """Test executor edge cases and failures."""

    @pytest.mark.asyncio
    async def test_submit_before_start_raises(self):
        from aquilia.mlops.runtime.executor import InferenceExecutor
        executor = InferenceExecutor(max_workers=2)

        with pytest.raises(RuntimeError, match="not started"):
            await executor.submit(lambda: 42)

    @pytest.mark.asyncio
    async def test_exception_propagation(self):
        from aquilia.mlops.runtime.executor import InferenceExecutor

        async with InferenceExecutor(max_workers=2) as executor:
            def bad():
                raise ValueError("intentional error")

            with pytest.raises(ValueError, match="intentional error"):
                await executor.submit(bad)

    @pytest.mark.asyncio
    async def test_failed_tasks_tracked_in_metrics(self):
        from aquilia.mlops.runtime.executor import InferenceExecutor

        async with InferenceExecutor(max_workers=2) as executor:
            for _ in range(5):
                try:
                    await executor.submit(lambda: 1 / 0)
                except ZeroDivisionError:
                    pass

            metrics = executor.metrics()
            assert metrics["total_failed"] == 5
            assert metrics["total_completed"] == 0
