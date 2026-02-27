"""
Orchestrator Tests — ModelRegistry, VersionManager, VersionRouter, ModelLoader.
"""

import asyncio
import pytest

from aquilia.mlops.orchestrator.registry import ModelRegistry, ModelConfig, ModelEntry
from aquilia.mlops.orchestrator.versioning import VersionManager
from aquilia.mlops.orchestrator.router import VersionRouter
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.runtime.base import ModelState

from .conftest import MockModel, FailingModel


# ═══════════════════════════════════════════════════════════════════════
# ModelRegistry Tests
# ═══════════════════════════════════════════════════════════════════════

class TestModelRegistry:
    """Test in-memory model registry."""

    @pytest.mark.asyncio
    async def test_register_and_get(self, model_registry):
        entry = await model_registry.register("sentiment", MockModel, version="v1")
        assert entry.name == "sentiment"
        assert entry.version == "v1"

        retrieved = model_registry.get("sentiment")
        assert retrieved is not None
        assert retrieved.key == "sentiment:v1"

    @pytest.mark.asyncio
    async def test_register_sets_active_version(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        assert model_registry.get_active_version("sentiment") == "v1"

    @pytest.mark.asyncio
    async def test_multiple_versions(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2")

        versions = model_registry.list_versions("sentiment")
        assert "v1" in versions
        assert "v2" in versions
        assert model_registry.get_active_version("sentiment") == "v2"

    @pytest.mark.asyncio
    async def test_get_specific_version(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2")

        v1 = model_registry.get("sentiment", "v1")
        assert v1 is not None
        assert v1.version == "v1"

    @pytest.mark.asyncio
    async def test_list_models(self, model_registry):
        await model_registry.register("sentiment", MockModel)
        await model_registry.register("embedding", MockModel)

        models = model_registry.list_models()
        assert "sentiment" in models
        assert "embedding" in models

    @pytest.mark.asyncio
    async def test_has_model(self, model_registry):
        await model_registry.register("sentiment", MockModel)
        assert model_registry.has("sentiment")
        assert not model_registry.has("nonexistent")

    @pytest.mark.asyncio
    async def test_unregister(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2")

        result = await model_registry.unregister("sentiment", "v2")
        assert result is True
        assert model_registry.get_active_version("sentiment") == "v1"

    @pytest.mark.asyncio
    async def test_unregister_last_version(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        result = await model_registry.unregister("sentiment", "v1")
        assert result is True
        assert not model_registry.has("sentiment")

    @pytest.mark.asyncio
    async def test_update_state(self, model_registry):
        await model_registry.register("sentiment", MockModel)
        model_registry.update_state("sentiment", "v1", ModelState.LOADED)

        entry = model_registry.get("sentiment")
        assert entry.state == ModelState.LOADED

    def test_sync_register(self, model_registry):
        entry = model_registry.register_sync("echo", MockModel, version="v1")
        assert entry.name == "echo"
        assert model_registry.has("echo")

    @pytest.mark.asyncio
    async def test_summary(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("embedding", MockModel, version="v1")

        summary = model_registry.summary()
        assert summary["total_models"] == 2
        assert summary["total_versions"] == 2


# ═══════════════════════════════════════════════════════════════════════
# VersionManager Tests
# ═══════════════════════════════════════════════════════════════════════

class TestVersionManager:
    """Test version promotion and rollback."""

    @pytest.mark.asyncio
    async def test_promote_version(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        vm = VersionManager(model_registry)
        ok = await vm.promote("sentiment", "v2")
        assert ok is True
        assert model_registry.get_active_version("sentiment") == "v2"

    @pytest.mark.asyncio
    async def test_rollback(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        vm = VersionManager(model_registry)
        await vm.promote("sentiment", "v2")
        assert model_registry.get_active_version("sentiment") == "v2"

        rolled = await vm.rollback("sentiment")
        assert rolled == "v1"
        assert model_registry.get_active_version("sentiment") == "v1"

    @pytest.mark.asyncio
    async def test_rollback_no_history(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        vm = VersionManager(model_registry)

        result = await vm.rollback("sentiment")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_rollback(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        vm = VersionManager(model_registry)
        assert not vm.can_rollback("sentiment")

        await vm.promote("sentiment", "v2")
        assert vm.can_rollback("sentiment")

    @pytest.mark.asyncio
    async def test_promote_nonexistent(self, model_registry):
        vm = VersionManager(model_registry)
        ok = await vm.promote("nonexistent", "v1")
        assert ok is False


# ═══════════════════════════════════════════════════════════════════════
# VersionRouter Tests
# ═══════════════════════════════════════════════════════════════════════

class TestVersionRouter:
    """Test request routing to model versions."""

    @pytest.mark.asyncio
    async def test_default_routing(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        router = VersionRouter(model_registry)

        version = await router.route("sentiment")
        assert version == "v1"

    @pytest.mark.asyncio
    async def test_header_override(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)
        router = VersionRouter(model_registry)

        version = await router.route(
            "sentiment",
            headers={"x-model-version": "v2"},
        )
        assert version == "v2"

    @pytest.mark.asyncio
    async def test_invalid_header_version_falls_back(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        router = VersionRouter(model_registry)

        version = await router.route(
            "sentiment",
            headers={"x-model-version": "nonexistent"},
        )
        assert version == "v1"

    @pytest.mark.asyncio
    async def test_canary_routing(self, model_registry):
        """Canary routing should split traffic based on percentage."""
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        router = VersionRouter(model_registry)
        router.set_canary("sentiment", "v2", percentage=50.0)

        # Run many requests and check distribution
        versions = []
        for _ in range(200):
            v = await router.route("sentiment")
            versions.append(v)

        v1_count = versions.count("v1")
        v2_count = versions.count("v2")

        # With 50% canary, expect roughly 50/50
        # Allow wide margin for randomness
        assert v2_count > 30, f"Expected ~100 canary hits, got {v2_count}"
        assert v1_count > 30, f"Expected ~100 base hits, got {v1_count}"

    @pytest.mark.asyncio
    async def test_clear_canary(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        router = VersionRouter(model_registry)
        router.set_canary("sentiment", "v2", percentage=100)
        router.clear_canary("sentiment")

        version = await router.route("sentiment")
        assert version == "v1"

    @pytest.mark.asyncio
    async def test_route_nonexistent_model_raises(self, model_registry):
        router = VersionRouter(model_registry)
        with pytest.raises(KeyError, match="not registered"):
            await router.route("nonexistent")

    @pytest.mark.asyncio
    async def test_canary_100_percent(self, model_registry):
        await model_registry.register("sentiment", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v2", set_active=False)

        router = VersionRouter(model_registry)
        router.set_canary("sentiment", "v2", percentage=100)

        for _ in range(50):
            v = await router.route("sentiment")
            assert v == "v2"


# ═══════════════════════════════════════════════════════════════════════
# ModelLoader Tests
# ═══════════════════════════════════════════════════════════════════════

class TestModelLoader:
    """Test lazy loading, hot reload, and lifecycle management."""

    @pytest.mark.asyncio
    async def test_lazy_load(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)

        # Model should not be loaded yet
        assert not loader.is_loaded("echo", "v1")

        # ensure_loaded triggers lazy load
        loaded = await loader.ensure_loaded("echo", "v1")
        assert loaded is not None
        assert loaded.entry.state == ModelState.LOADED
        assert loader.is_loaded("echo", "v1")

    @pytest.mark.asyncio
    async def test_ensure_loaded_idempotent(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)

        loaded1 = await loader.ensure_loaded("echo", "v1")
        loaded2 = await loader.ensure_loaded("echo", "v1")
        assert loaded1 is loaded2

    @pytest.mark.asyncio
    async def test_load_calls_model_lifecycle(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)

        loaded = await loader.ensure_loaded("echo", "v1")
        assert loaded.instance.load_called is True

    @pytest.mark.asyncio
    async def test_unload(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)

        await loader.ensure_loaded("echo", "v1")
        assert loader.is_loaded("echo", "v1")

        result = await loader.unload("echo", "v1")
        assert result is True
        assert not loader.is_loaded("echo", "v1")

    @pytest.mark.asyncio
    async def test_unload_calls_model_lifecycle(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)

        loaded = await loader.ensure_loaded("echo", "v1")
        instance = loaded.instance
        await loader.unload("echo", "v1")
        assert instance.unload_called is True

    @pytest.mark.asyncio
    async def test_hot_reload(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        await model_registry.register("echo", MockModel, version="v2", set_active=False)

        loader = ModelLoader(model_registry)
        await loader.ensure_loaded("echo", "v1")

        new_loaded = await loader.hot_reload("echo", "v2")
        assert new_loaded.entry.version == "v2"
        assert not loader.is_loaded("echo", "v1")  # old unloaded
        assert loader.is_loaded("echo", "v2")  # new loaded
        assert model_registry.get_active_version("echo") == "v2"

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises(self, model_registry):
        loader = ModelLoader(model_registry)
        with pytest.raises(KeyError, match="not found"):
            await loader.ensure_loaded("nonexistent", "v1")

    @pytest.mark.asyncio
    async def test_unload_all(self, model_registry):
        await model_registry.register("model_a", MockModel, version="v1")
        await model_registry.register("model_b", MockModel, version="v1")

        loader = ModelLoader(model_registry)
        await loader.ensure_loaded("model_a", "v1")
        await loader.ensure_loaded("model_b", "v1")

        await loader.unload_all()
        assert len(loader.loaded_models()) == 0

    @pytest.mark.asyncio
    async def test_summary(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        loader = ModelLoader(model_registry)
        await loader.ensure_loaded("echo", "v1")

        summary = loader.summary()
        assert summary["loaded_count"] == 1
        assert "echo:v1" in summary["models"]


# ═══════════════════════════════════════════════════════════════════════
# ModelOrchestrator End-to-End Tests
# ═══════════════════════════════════════════════════════════════════════

class TestModelOrchestrator:
    """Test the full orchestra: route → load → pipeline → result."""

    @pytest.mark.asyncio
    async def test_predict_end_to_end(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        result = await orch.predict("echo", {"text": "hello"})
        assert result.request_id  # should have a UUID
        assert result.finish_reason == "stop"
        assert "echo" in result.outputs

    @pytest.mark.asyncio
    async def test_predict_batch(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        results = await orch.predict_batch(
            "echo",
            [{"text": "a"}, {"text": "b"}, {"text": "c"}],
        )
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_health_per_model(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        # Before loading
        health = await orch.get_health("echo")
        assert health["state"] == "unloaded"

        # After loading (via predict)
        await orch.predict("echo", {"text": "test"})
        health = await orch.get_health("echo")
        assert health["state"] == "loaded"

    @pytest.mark.asyncio
    async def test_health_aggregate(self, model_registry):
        await model_registry.register("model_a", MockModel, version="v1")
        await model_registry.register("model_b", MockModel, version="v1")

        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        health = await orch.get_health()
        assert health["models_registered"] == 2

    @pytest.mark.asyncio
    async def test_list_models(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        await model_registry.register("sentiment", MockModel, version="v1")

        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        models = await orch.list_models()
        assert len(models) == 2
        names = [m["name"] for m in models]
        assert "echo" in names
        assert "sentiment" in names

    @pytest.mark.asyncio
    async def test_predict_nonexistent_model(self, model_registry):
        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        with pytest.raises(KeyError, match="not registered"):
            await orch.predict("nonexistent", {"text": "test"})

    @pytest.mark.asyncio
    async def test_reload_model(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        await model_registry.register("echo", MockModel, version="v2", set_active=False)

        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        await orch.predict("echo", {"text": "test"})  # load v1
        result = await orch.reload_model("echo", "v2")
        assert result["version"] == "v2"
        assert result["state"] == "loaded"

    @pytest.mark.asyncio
    async def test_shutdown(self, model_registry):
        await model_registry.register("echo", MockModel, version="v1")
        router = VersionRouter(model_registry)
        loader = ModelLoader(model_registry)
        orch = ModelOrchestrator(model_registry, router, loader)

        await orch.predict("echo", {"text": "test"})
        await orch.shutdown()
        assert len(loader.loaded_models()) == 0
