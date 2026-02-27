"""
API Layer Tests — @model, @serve, AquiliaModel, RouteGenerator.
"""

import pytest
from typing import Any, Dict

from aquilia.mlops.api.model_class import AquiliaModel, model, set_global_registry
from aquilia.mlops.api.functional import serve
from aquilia.mlops.api.route_generator import RouteGenerator, RouteDefinition
from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.router import VersionRouter
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.engine.hooks import collect_hooks, on_load, on_unload, before_predict

from .conftest import MockModel


# ═══════════════════════════════════════════════════════════════════════
# AquiliaModel Base Class Tests
# ═══════════════════════════════════════════════════════════════════════

class TestAquiliaModel:
    """Test AquiliaModel base class."""

    @pytest.mark.asyncio
    async def test_default_preprocess_is_identity(self):
        m = AquiliaModel()
        result = await m.preprocess({"text": "hello"})
        assert result == {"text": "hello"}

    @pytest.mark.asyncio
    async def test_default_postprocess_is_identity(self):
        m = AquiliaModel()
        result = await m.postprocess({"sentiment": "positive"})
        assert result == {"sentiment": "positive"}

    @pytest.mark.asyncio
    async def test_predict_not_implemented(self):
        m = AquiliaModel()
        with pytest.raises(NotImplementedError, match="must implement predict"):
            await m.predict({"text": "hello"})

    @pytest.mark.asyncio
    async def test_default_health(self):
        m = AquiliaModel()
        health = await m.health()
        assert health == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_custom_model_predict(self):
        m = MockModel()
        result = await m.predict({"text": "hello"})
        assert "echo" in result
        assert m.predict_count == 1

    @pytest.mark.asyncio
    async def test_custom_model_preprocess(self):
        m = MockModel()
        result = await m.preprocess({"text": "hello"})
        assert result["_preprocessed"] is True


# ═══════════════════════════════════════════════════════════════════════
# @model Decorator Tests
# ═══════════════════════════════════════════════════════════════════════

class TestModelDecorator:
    """Test @model class decorator."""

    def test_decorator_attaches_metadata(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @model(name="test_deco", version="v1", device="cuda:0")
        class TestModel(AquiliaModel):
            async def predict(self, inputs):
                return {"ok": True}

        assert hasattr(TestModel, "__mlops_model_name__")
        assert TestModel.__mlops_model_name__ == "test_deco"
        assert TestModel.__mlops_model_version__ == "v1"

    def test_decorator_registers_in_registry(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @model(name="test_reg", version="v2")
        class RegModel(AquiliaModel):
            async def predict(self, inputs):
                return {"ok": True}

        assert registry.has("test_reg")
        assert registry.get_active_version("test_reg") == "v2"

    def test_decorator_preserves_class(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @model(name="preserved", version="v1")
        class OriginalModel(AquiliaModel):
            async def predict(self, inputs):
                return {"ok": True}

        assert OriginalModel.__name__ == "OriginalModel"


# ═══════════════════════════════════════════════════════════════════════
# @serve Functional Decorator Tests
# ═══════════════════════════════════════════════════════════════════════

class TestServeDecorator:
    """Test @serve functional decorator."""

    def test_serve_registers_model(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @serve(name="func_echo", version="v1")
        async def echo(inputs: dict) -> dict:
            return {"echo": inputs["text"]}

        assert registry.has("func_echo")

    def test_serve_preserves_function(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @serve(name="func_preserved", version="v1")
        async def my_func(inputs: dict) -> dict:
            return {"ok": True}

        assert callable(my_func)
        assert my_func.__name__ == "my_func"

    def test_serve_sync_function(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @serve(name="func_sync", version="v1")
        def sync_model(inputs: dict) -> dict:
            return {"sum": inputs.get("a", 0) + inputs.get("b", 0)}

        assert registry.has("func_sync")

    @pytest.mark.asyncio
    async def test_serve_model_can_predict(self):
        registry = ModelRegistry()
        set_global_registry(registry)

        @serve(name="func_pred", version="v1")
        async def pred_model(inputs: dict) -> dict:
            return {"result": inputs["x"] * 2}

        # Get the model class and instantiate
        entry = registry.get("func_pred")
        instance = entry.model_class()
        result = await instance.predict({"x": 5})
        assert result == {"result": 10}


# ═══════════════════════════════════════════════════════════════════════
# Hook Collection Tests
# ═══════════════════════════════════════════════════════════════════════

class TestHookCollection:
    """Test hook decorator collection from model instances."""

    def test_collect_hooks_from_instance(self):

        class HookedModel(AquiliaModel):
            @on_load
            async def my_on_load(self):
                pass

            @on_unload
            async def my_on_unload(self):
                pass

            @before_predict
            async def my_before(self):
                pass

            async def predict(self, inputs):
                return inputs

        instance = HookedModel()
        hooks = collect_hooks(instance)

        assert len(hooks.on_load) == 1
        assert len(hooks.on_unload) == 1
        assert len(hooks.before_predict) == 1

    def test_no_hooks_is_empty(self):
        instance = MockModel()
        hooks = collect_hooks(instance)
        # MockModel has no hook decorators
        assert not hooks.has("on_load")
        assert not hooks.has("on_unload")

    def test_hook_summary(self):
        class SomeModel(AquiliaModel):
            @on_load
            async def load_hook(self):
                pass

            async def predict(self, inputs):
                return inputs

        hooks = collect_hooks(SomeModel())
        summary = hooks.summary()
        assert summary["on_load"] == 1
        assert summary["on_unload"] == 0


# ═══════════════════════════════════════════════════════════════════════
# RouteGenerator Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRouteGenerator:
    """Test auto-generated route definitions."""

    @pytest.mark.asyncio
    async def test_generates_global_routes(self):
        registry = ModelRegistry()
        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry)

        routes = gen.generate()
        paths = [r.path for r in routes]

        assert "/mlops/models" in paths
        assert "/mlops/health" in paths
        assert "/mlops/metrics" in paths

    @pytest.mark.asyncio
    async def test_generates_per_model_routes(self):
        registry = ModelRegistry()
        await registry.register("sentiment", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry)

        routes = gen.generate()
        paths = [r.path for r in routes]

        assert "/mlops/models/sentiment/predict" in paths
        assert "/mlops/models/sentiment/health" in paths
        assert "/mlops/models/sentiment/metrics" in paths

    @pytest.mark.asyncio
    async def test_streaming_route_only_when_supported(self):
        registry = ModelRegistry()
        await registry.register("no_stream", MockModel, version="v1", supports_streaming=False)
        await registry.register("has_stream", MockModel, version="v1", supports_streaming=True)

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry)

        routes = gen.generate()
        paths = [r.path for r in routes]

        assert "/mlops/models/has_stream/stream" in paths
        assert "/mlops/models/no_stream/stream" not in paths

    @pytest.mark.asyncio
    async def test_route_table(self):
        registry = ModelRegistry()
        await registry.register("echo", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry)

        table = gen.route_table()
        assert len(table) > 0
        assert all(
            "method" in entry and "path" in entry
            for entry in table
        )

    @pytest.mark.asyncio
    async def test_custom_prefix(self):
        registry = ModelRegistry()
        await registry.register("echo", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry, prefix="/api/ml")

        routes = gen.generate()
        paths = [r.path for r in routes]

        assert "/api/ml/models/echo/predict" in paths
        assert "/api/ml/health" in paths

    @pytest.mark.asyncio
    async def test_predict_handler_works(self):
        registry = ModelRegistry()
        await registry.register("echo", MockModel, version="v1")

        router = VersionRouter(registry)
        loader = ModelLoader(registry)
        orch = ModelOrchestrator(registry, router, loader)
        gen = RouteGenerator(orch, registry)

        routes = gen.generate()
        predict_route = next(r for r in routes if r.path.endswith("/predict"))

        # Call the handler directly
        result = await predict_route.handler({"inputs": {"text": "hello"}})
        assert "outputs" in result
        assert "request_id" in result
