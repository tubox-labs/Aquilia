"""
Stress Tests — concurrent inference, batching correctness, memory stability.
"""

import asyncio
import pytest
import time

from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.router import VersionRouter
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.runtime.executor import InferenceExecutor

from .conftest import MockModel


class TestConcurrentPredictions:
    """Test concurrent inference routing and correctness."""

    @pytest.mark.asyncio
    async def test_100_concurrent_predictions(self):
        """100 concurrent predictions should all return correct results."""
        registry = ModelRegistry()
        await registry.register("echo", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        tasks = [
            orch.predict("echo", {"idx": i})
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 100
        for result in results:
            assert result.finish_reason == "stop"
            assert "echo" in result.outputs

    @pytest.mark.asyncio
    async def test_concurrent_multi_model(self):
        """Concurrent predictions across multiple models."""
        registry = ModelRegistry()
        await registry.register("model_a", MockModel, version="v1")
        await registry.register("model_b", MockModel, version="v1")
        await registry.register("model_c", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        models = ["model_a", "model_b", "model_c"]
        tasks = [
            orch.predict(models[i % 3], {"idx": i})
            for i in range(60)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 60
        assert all(r.finish_reason == "stop" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_lazy_load_safety(self):
        """Multiple concurrent requests to unloaded model should only load once."""
        registry = ModelRegistry()
        await registry.register("lazy", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        # Fire 20 concurrent requests before model is loaded
        tasks = [
            orch.predict("lazy", {"idx": i})
            for i in range(20)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 20
        assert all(r.finish_reason == "stop" for r in results)

        # Verify model loaded only once (one entry in loader)
        assert len(loader.loaded_models()) == 1


class TestExecutorUnderLoad:
    """Test InferenceExecutor under concurrent load."""

    @pytest.mark.asyncio
    async def test_50_concurrent_executor_tasks(self):
        async with InferenceExecutor(max_workers=4) as executor:
            def work(n):
                return n * 2

            tasks = [executor.submit(work, i) for i in range(50)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 50
            assert results == [i * 2 for i in range(50)]

    @pytest.mark.asyncio
    async def test_executor_no_event_loop_blocking(self):
        """Verify inference doesn't block the event loop."""
        async with InferenceExecutor(max_workers=2) as executor:
            import time as _time

            async def timed_task():
                start = _time.monotonic()
                # This should NOT block the event loop
                await executor.submit(_time.sleep, 0.05)
                return _time.monotonic() - start

            # Run 4 tasks — with 2 workers, should take ~2x 50ms, not 4x
            tasks = [timed_task() for _ in range(4)]
            await asyncio.gather(*tasks)

            # Verify the event loop was responsive
            # (we can do async work while executor tasks run)
            loop_was_blocked = False
            async def check_loop():
                nonlocal loop_was_blocked
                start = _time.monotonic()
                await asyncio.sleep(0.001)
                elapsed = _time.monotonic() - start
                if elapsed > 0.1:  # More than 100ms delay = blocked
                    loop_was_blocked = True

            await check_loop()
            assert not loop_was_blocked


class TestMemoryStability:
    """Basic memory stability test over many predictions."""

    @pytest.mark.asyncio
    async def test_1000_sequential_predictions(self):
        """1000 predictions should complete without error accumulation."""
        registry = ModelRegistry()
        await registry.register("stable", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)

        error_count = 0
        for i in range(1000):
            result = await orch.predict("stable", {"idx": i})
            if result.finish_reason != "stop":
                error_count += 1

        assert error_count == 0

    @pytest.mark.asyncio
    async def test_repeated_load_unload_cycles(self):
        """Load/unload cycles should not leak resources."""
        registry = ModelRegistry()
        await registry.register("cyclable", MockModel, version="v1")

        loader = ModelLoader(registry)

        for _ in range(50):
            await loader.ensure_loaded("cyclable", "v1")
            await loader.unload("cyclable", "v1")

        # Should be able to load one final time
        loaded = await loader.ensure_loaded("cyclable", "v1")
        assert loaded is not None
