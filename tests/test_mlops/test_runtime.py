"""
Runtime Layer Tests — ModelState FSM, DeviceManager, InferenceExecutor.
"""

import asyncio
import pytest
import time

from aquilia.mlops.runtime.base import (
    BaseRuntime,
    ModelState,
    InvalidStateTransition,
    _TRANSITIONS,
)
from aquilia.mlops.runtime.executor import InferenceExecutor, PoolKind
from aquilia.mlops.runtime.device_manager import DeviceManager, DeviceKind
from aquilia.mlops._types import ModelpackManifest

from .conftest import MockRuntime


# ═══════════════════════════════════════════════════════════════════════
# ModelState FSM Tests
# ═══════════════════════════════════════════════════════════════════════

class TestModelState:
    """Test model state machine transitions."""

    def test_initial_state_is_unloaded(self):
        runtime = MockRuntime()
        assert runtime.state == ModelState.UNLOADED

    @pytest.mark.asyncio
    async def test_valid_lifecycle_transitions(self):
        """UNLOADED → PREPARED → LOADING → LOADED → UNLOADING → UNLOADED"""
        runtime = MockRuntime()
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )

        assert runtime.state == ModelState.UNLOADED

        await runtime.prepare(manifest, "/tmp/model")
        assert runtime.state == ModelState.PREPARED

        await runtime.load()
        assert runtime.state == ModelState.LOADED

        await runtime.unload()
        assert runtime.state == ModelState.UNLOADED

    @pytest.mark.asyncio
    async def test_failed_state_on_load_error(self):
        """LOADING → FAILED when load() raises."""
        runtime = MockRuntime(fail_on_load=True)
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )

        await runtime.prepare(manifest, "/tmp/model")
        assert runtime.state == ModelState.PREPARED

        with pytest.raises(RuntimeError, match="Simulated load failure"):
            await runtime.load()
        assert runtime.state == ModelState.FAILED

    @pytest.mark.asyncio
    async def test_retry_from_failed_state(self):
        """FAILED → LOADING → LOADED (retry)."""
        runtime = MockRuntime(fail_on_load=True)
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )

        await runtime.prepare(manifest, "/tmp/model")
        with pytest.raises(RuntimeError):
            await runtime.load()
        assert runtime.state == ModelState.FAILED

        # Fix the failure and retry
        runtime._fail_on_load = False
        await runtime.load()
        assert runtime.state == ModelState.LOADED

    def test_invalid_transition_raises(self):
        """Direct UNLOADED → LOADED should fail."""
        runtime = MockRuntime()
        with pytest.raises(InvalidStateTransition) as exc_info:
            runtime._set_state(ModelState.LOADED)
        assert exc_info.value.current == ModelState.UNLOADED
        assert exc_info.value.target == ModelState.LOADED

    def test_invalid_transition_unloaded_to_loading(self):
        """UNLOADED → LOADING (must go through PREPARED first)."""
        runtime = MockRuntime()
        with pytest.raises(InvalidStateTransition):
            runtime._set_state(ModelState.LOADING)

    def test_all_transitions_are_documented(self):
        """Every ModelState value should appear in _TRANSITIONS."""
        for state in ModelState:
            assert state in _TRANSITIONS, f"Missing transition for {state}"

    @pytest.mark.asyncio
    async def test_is_loaded_property(self):
        """is_loaded should reflect ModelState.LOADED."""
        runtime = MockRuntime()
        assert not runtime.is_loaded

        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        await runtime.prepare(manifest, "/tmp/model")
        assert not runtime.is_loaded

        await runtime.load()
        assert runtime.is_loaded

        await runtime.unload()
        assert not runtime.is_loaded


# ═══════════════════════════════════════════════════════════════════════
# DeviceManager Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDeviceManager:
    """Test device detection and selection."""

    @pytest.mark.asyncio
    async def test_initialize_detects_cpu(self):
        dm = DeviceManager()
        await dm.initialize()
        assert "cpu" in [d.name for d in dm.list_devices()]

    @pytest.mark.asyncio
    async def test_cpu_always_available(self):
        dm = DeviceManager()
        await dm.initialize()
        cpu = dm.get_device("cpu")
        assert cpu is not None
        assert cpu.is_available
        assert cpu.kind == DeviceKind.CPU

    @pytest.mark.asyncio
    async def test_select_device_auto_fallback(self):
        """Auto selection should fall back to CPU when no GPU."""
        dm = DeviceManager()
        await dm.initialize()
        device = await dm.select_device("auto")
        # Should be cpu if no GPU, or cuda/mps if available
        assert device in ["cpu", "mps"] or device.startswith("cuda:")

    @pytest.mark.asyncio
    async def test_select_unknown_device_falls_back(self):
        dm = DeviceManager()
        await dm.initialize()
        device = await dm.select_device("nonexistent_device")
        # Should fall back to auto selection
        assert device in ["cpu", "mps"] or device.startswith("cuda:")

    @pytest.mark.asyncio
    async def test_device_locking(self):
        """Device lock prevents concurrent access."""
        dm = DeviceManager()
        await dm.initialize()

        acquired = []

        async def acquire_and_hold(device_name, delay):
            async with dm.acquire(device_name):
                acquired.append(("entered", device_name))
                await asyncio.sleep(delay)
                acquired.append(("exited", device_name))

        # Start two tasks with the same device lock
        t1 = asyncio.create_task(acquire_and_hold("cpu", 0.05))
        await asyncio.sleep(0.01)  # Let t1 acquire first
        t2 = asyncio.create_task(acquire_and_hold("cpu", 0.01))

        await asyncio.gather(t1, t2)

        # t1 should enter then exit before t2 enters
        assert acquired[0] == ("entered", "cpu")
        assert acquired[1] == ("exited", "cpu")
        assert acquired[2] == ("entered", "cpu")
        assert acquired[3] == ("exited", "cpu")

    @pytest.mark.asyncio
    async def test_summary(self):
        dm = DeviceManager()
        await dm.initialize()
        summary = dm.summary()
        assert "default_device" in summary
        assert "devices" in summary
        assert "cpu" in summary["devices"]

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        dm = DeviceManager()
        await dm.initialize()
        devices_1 = len(dm.list_devices())
        await dm.initialize()
        devices_2 = len(dm.list_devices())
        assert devices_1 == devices_2


# ═══════════════════════════════════════════════════════════════════════
# InferenceExecutor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestInferenceExecutor:
    """Test thread/process pool executor."""

    @pytest.mark.asyncio
    async def test_submit_runs_off_event_loop(self):
        """Blocking function should run in thread pool."""
        async with InferenceExecutor(max_workers=2) as executor:
            import threading
            main_thread = threading.current_thread().ident

            def get_thread_id():
                return threading.current_thread().ident

            worker_thread = await executor.submit(get_thread_id)
            assert worker_thread != main_thread

    @pytest.mark.asyncio
    async def test_submit_returns_result(self):
        async with InferenceExecutor(max_workers=2) as executor:
            result = await executor.submit(lambda: 42)
            assert result == 42

    @pytest.mark.asyncio
    async def test_submit_with_args(self):
        async with InferenceExecutor(max_workers=2) as executor:
            result = await executor.submit(lambda x, y: x + y, 3, 4)
            assert result == 7

    @pytest.mark.asyncio
    async def test_submit_with_kwargs(self):
        async with InferenceExecutor(max_workers=2) as executor:
            def add(a, b=10):
                return a + b
            result = await executor.submit(add, 5, b=20)
            assert result == 25

    @pytest.mark.asyncio
    async def test_submit_propagates_exception(self):
        async with InferenceExecutor(max_workers=2) as executor:
            def fail():
                raise ValueError("test error")

            with pytest.raises(ValueError, match="test error"):
                await executor.submit(fail)

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        async with InferenceExecutor(max_workers=2) as executor:
            await executor.submit(lambda: 1)
            await executor.submit(lambda: 2)

            metrics = executor.metrics()
            assert metrics["total_submitted"] == 2
            assert metrics["total_completed"] == 2
            assert metrics["total_failed"] == 0
            assert metrics["is_running"] is True

    @pytest.mark.asyncio
    async def test_failed_task_tracking(self):
        async with InferenceExecutor(max_workers=2) as executor:
            try:
                await executor.submit(lambda: 1 / 0)
            except ZeroDivisionError:
                pass

            metrics = executor.metrics()
            assert metrics["total_failed"] == 1

    @pytest.mark.asyncio
    async def test_not_started_raises(self):
        executor = InferenceExecutor(max_workers=2)
        with pytest.raises(RuntimeError, match="not started"):
            await executor.submit(lambda: 1)

    @pytest.mark.asyncio
    async def test_concurrent_submissions(self):
        async with InferenceExecutor(max_workers=4) as executor:
            tasks = [
                executor.submit(time.sleep, 0.01)
                for _ in range(10)
            ]
            await asyncio.gather(*tasks)

            metrics = executor.metrics()
            assert metrics["total_completed"] == 10

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        executor = InferenceExecutor(max_workers=2)
        await executor.start()
        assert executor.is_running

        await executor.shutdown()
        assert not executor.is_running


# ═══════════════════════════════════════════════════════════════════════
# Runtime Health & Metrics Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRuntimeHealth:
    """Test runtime health and metrics reporting."""

    @pytest.mark.asyncio
    async def test_health_reports_state(self):
        runtime = MockRuntime()
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        await runtime.prepare(manifest, "/tmp/model")
        await runtime.load()

        health = await runtime.health()
        assert health["status"] == "loaded"
        assert health["model"] == "test"
        assert health["version"] == "v1"

    @pytest.mark.asyncio
    async def test_metrics_after_inference(self):
        runtime = MockRuntime()
        manifest = ModelpackManifest(
            name="test", version="v1", framework="custom", entrypoint="model.py",
        )
        await runtime.prepare(manifest, "/tmp/model")
        await runtime.load()

        from aquilia.mlops._types import BatchRequest, InferenceRequest
        batch = BatchRequest(requests=[
            InferenceRequest(request_id="r1", inputs={"text": "hello"}),
        ])
        await runtime.infer(batch)

        metrics = await runtime.metrics()
        assert metrics["total_infer_count"] == 1.0
        assert metrics["state"] == 1.0  # LOADED

    @pytest.mark.asyncio
    async def test_unloaded_health(self):
        runtime = MockRuntime()
        health = await runtime.health()
        assert health["status"] == "unloaded"
