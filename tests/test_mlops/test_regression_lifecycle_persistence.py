"""
Regression tests — Lifecycle hooks, Config builder, Model persistence, DType system.

Covers:
- Config builder syntax & fluent API (the unmatched ')' regression)
- Lifecycle hook string resolution (the 'on_startup' AttributeError regression)
- LifecycleCoordinator global + app-level hooks
- Model persistence manager save/load round-trip
- DType enum properties and conversions
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ═══════════════════════════════════════════════════════════════════════════
# 1. Config Builder Regression Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigBuilderRegression:
    """Regression: config_builders.py must be importable and complete."""

    def test_config_builders_importable(self):
        """The file must compile and import without SyntaxError."""
        import aquilia.config_builders  # noqa: F401

    def test_workspace_has_on_startup(self):
        """Workspace must expose on_startup (the original bug)."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        assert hasattr(ws, "on_startup")
        assert callable(ws.on_startup)

    def test_workspace_has_on_shutdown(self):
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        assert hasattr(ws, "on_shutdown")
        assert callable(ws.on_shutdown)

    def test_workspace_has_runtime(self):
        """Workspace.runtime() must exist (was broken by missing def)."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        assert hasattr(ws, "runtime")
        assert callable(ws.runtime)

    def test_on_startup_fluent_api(self):
        """on_startup must return self for chaining."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        result = ws.on_startup("my.module:func")
        assert result is ws

    def test_on_shutdown_fluent_api(self):
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        result = ws.on_shutdown("my.module:func")
        assert result is ws

    def test_runtime_fluent_api(self):
        """runtime() must return self for chaining."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        result = ws.runtime(mode="prod", port=9000)
        assert result is ws

    def test_workspace_mlops_auto_wires_hooks(self):
        """Calling .mlops() must auto-register lifecycle hooks."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        ws.mlops(enabled=True)
        assert ws._on_startup == "aquilia.mlops.engine.lifecycle:mlops_on_startup"
        assert ws._on_shutdown == "aquilia.mlops.engine.lifecycle:mlops_on_shutdown"

    def test_workspace_mlops_disabled_skips_hooks(self):
        """Calling .mlops(enabled=False) must NOT register hooks."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        ws.mlops(enabled=False)
        assert ws._on_startup is None
        assert ws._on_shutdown is None

    def test_workspace_mlops_does_not_overwrite_explicit_hooks(self):
        """If hooks are set first, .mlops() must NOT overwrite them."""
        from aquilia.config_builders import Workspace

        ws = Workspace("test-ws")
        ws.on_startup("custom.module:my_startup")
        ws.mlops(enabled=True)
        assert ws._on_startup == "custom.module:my_startup"

    def test_module_has_lifecycle_hooks(self):
        """Module builder must also support lifecycle hooks."""
        from aquilia.config_builders import Module

        m = Module("test-mod")
        assert hasattr(m, "on_startup")
        assert hasattr(m, "on_shutdown")

    def test_module_on_startup_fluent(self):
        from aquilia.config_builders import Module

        m = Module("test-mod")
        result = m.on_startup("my.module:func")
        assert result is m

    def test_full_workspace_chain(self):
        """A realistic fluent chain must not raise."""
        from aquilia.config_builders import Workspace, Module

        ws = (
            Workspace("my-app", version="1.0.0")
            .runtime(mode="dev", port=8000)
            .on_startup("app.lifecycle:on_start")
            .on_shutdown("app.lifecycle:on_stop")
            .mlops(enabled=True, blob_root="/tmp/store")
        )
        # mlops should NOT have overwritten explicit hooks
        assert ws._on_startup == "app.lifecycle:on_start"
        assert ws._on_shutdown == "app.lifecycle:on_stop"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Lifecycle Hook Resolution Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestLifecycleHookResolution:
    """Regression: string import paths must resolve to callables."""

    def test_resolve_colon_path(self):
        """'json:dumps' must resolve to json.dumps."""
        from aquilia.lifecycle import LifecycleCoordinator

        mock_runtime = MagicMock()
        mock_runtime.meta.app_contexts = []
        coord = LifecycleCoordinator(mock_runtime)

        resolved = coord._resolve_hook("json:dumps")
        assert resolved is json.dumps

    def test_resolve_dot_path(self):
        """'os.path.exists' must resolve to os.path.exists."""
        from aquilia.lifecycle import LifecycleCoordinator

        mock_runtime = MagicMock()
        mock_runtime.meta.app_contexts = []
        coord = LifecycleCoordinator(mock_runtime)

        resolved = coord._resolve_hook("os.path.exists")
        assert resolved is os.path.exists

    def test_resolve_callable_passthrough(self):
        """Already-callable hooks must pass through unchanged."""
        from aquilia.lifecycle import LifecycleCoordinator

        mock_runtime = MagicMock()
        mock_runtime.meta.app_contexts = []
        coord = LifecycleCoordinator(mock_runtime)

        my_func = lambda: None
        assert coord._resolve_hook(my_func) is my_func

    def test_resolve_none_returns_none(self):
        from aquilia.lifecycle import LifecycleCoordinator

        mock_runtime = MagicMock()
        mock_runtime.meta.app_contexts = []
        coord = LifecycleCoordinator(mock_runtime)

        assert coord._resolve_hook(None) is None

    def test_resolve_invalid_path_returns_none(self):
        from aquilia.lifecycle import LifecycleCoordinator

        mock_runtime = MagicMock()
        mock_runtime.meta.app_contexts = []
        coord = LifecycleCoordinator(mock_runtime)

        assert coord._resolve_hook("totally.fake.module:nope") is None


# ═══════════════════════════════════════════════════════════════════════════
# 3. LifecycleCoordinator Startup/Shutdown Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestLifecycleCoordinator:
    """Lifecycle coordinator must call hooks in the right order."""

    @pytest.mark.asyncio
    async def test_startup_calls_app_hooks(self):
        """App-level on_startup hooks must be called."""
        from aquilia.lifecycle import LifecycleCoordinator

        called = []

        async def my_hook(config, di):
            called.append("started")

        ctx = MagicMock()
        ctx.name = "test-app"
        ctx.on_startup = my_hook
        ctx.on_shutdown = None
        ctx.config_namespace = {}

        runtime = MagicMock()
        runtime.meta.app_contexts = [ctx]
        runtime.di_containers = {}

        coord = LifecycleCoordinator(runtime)
        await coord.startup()

        assert called == ["started"]
        assert "test-app" in coord.started_apps

    @pytest.mark.asyncio
    async def test_shutdown_calls_app_hooks_reverse(self):
        """App hooks must be called in reverse order on shutdown."""
        from aquilia.lifecycle import LifecycleCoordinator

        order = []

        async def hook_a(cfg, di):
            order.append("A")

        async def hook_b(cfg, di):
            order.append("B")

        ctx_a = MagicMock()
        ctx_a.name = "app-a"
        ctx_a.on_startup = hook_a
        ctx_a.on_shutdown = hook_a
        ctx_a.config_namespace = {}

        ctx_b = MagicMock()
        ctx_b.name = "app-b"
        ctx_b.on_startup = hook_b
        ctx_b.on_shutdown = hook_b
        ctx_b.config_namespace = {}

        runtime = MagicMock()
        runtime.meta.app_contexts = [ctx_a, ctx_b]
        runtime.di_containers = {}

        coord = LifecycleCoordinator(runtime)
        await coord.startup()
        assert order == ["A", "B"]

        order.clear()
        await coord.shutdown()
        # Reverse: B then A
        assert order == ["B", "A"]

    @pytest.mark.asyncio
    async def test_skip_none_hooks(self):
        """Apps with no hooks must still be tracked in started_apps."""
        from aquilia.lifecycle import LifecycleCoordinator

        ctx = MagicMock()
        ctx.name = "no-hooks"
        ctx.on_startup = None
        ctx.on_shutdown = None
        ctx.config_namespace = {}

        runtime = MagicMock()
        runtime.meta.app_contexts = [ctx]
        runtime.di_containers = {}

        coord = LifecycleCoordinator(runtime)
        await coord.startup()

        assert "no-hooks" in coord.started_apps

    @pytest.mark.asyncio
    async def test_startup_rollback_on_failure(self):
        """If a hook fails, already-started apps must be shut down."""
        from aquilia.lifecycle import LifecycleCoordinator, LifecycleError

        shutdown_called = []

        async def good_startup(cfg, di):
            pass

        async def good_shutdown(cfg, di):
            shutdown_called.append("shutdown")

        async def bad_startup(cfg, di):
            raise RuntimeError("boom")

        ctx_good = MagicMock()
        ctx_good.name = "good"
        ctx_good.on_startup = good_startup
        ctx_good.on_shutdown = good_shutdown
        ctx_good.config_namespace = {}

        ctx_bad = MagicMock()
        ctx_bad.name = "bad"
        ctx_bad.on_startup = bad_startup
        ctx_bad.on_shutdown = None
        ctx_bad.config_namespace = {}

        runtime = MagicMock()
        runtime.meta.app_contexts = [ctx_good, ctx_bad]
        runtime.di_containers = {}

        coord = LifecycleCoordinator(runtime)
        with pytest.raises(LifecycleError, match="Startup failed"):
            await coord.startup()

        # good_shutdown should have been called during rollback
        assert "shutdown" in shutdown_called

    @pytest.mark.asyncio
    async def test_sync_hooks_supported(self):
        """Non-async hooks must also work."""
        from aquilia.lifecycle import LifecycleCoordinator

        called = []

        def sync_hook(cfg, di):
            called.append("sync")

        ctx = MagicMock()
        ctx.name = "sync-app"
        ctx.on_startup = sync_hook
        ctx.on_shutdown = None
        ctx.config_namespace = {}

        runtime = MagicMock()
        runtime.meta.app_contexts = [ctx]
        runtime.di_containers = {}

        coord = LifecycleCoordinator(runtime)
        await coord.startup()
        assert called == ["sync"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. Model Persistence Manager Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestModelPersistenceManager:
    """Model persistence save/load round-trip tests."""

    @pytest.fixture(autouse=True)
    def _tmp_dir(self, tmp_path):
        self.root = tmp_path / "models"
        self.root.mkdir()

    def _make_manager(self):
        from aquilia.mlops.orchestrator.persistence import ModelPersistenceManager
        return ModelPersistenceManager(root_dir=str(self.root))

    @pytest.mark.asyncio
    async def test_save_load_roundtrip(self):
        """Save a bundle, then load it back."""
        from aquilia.mlops.orchestrator.persistence import (
            ModelPersistenceManager,
            ModelBundle,
        )

        mgr = self._make_manager()

        # Create a fake weights file
        weights = self.root / "weights.bin"
        weights.write_bytes(b"fake-weights-data")

        bundle = ModelBundle(
            name="test-model",
            version="v1",
            weights_path=weights,
            metadata={"accuracy": 0.95},
            framework="custom",
            dtype="float32",
        )

        model_dir = await mgr.save_bundle(bundle)
        assert (model_dir / "metadata.json").exists()

        # Verify metadata
        meta = json.loads((model_dir / "metadata.json").read_text())
        assert meta["name"] == "test-model"
        assert meta["version"] == "v1"
        assert meta["framework"] == "custom"
        assert meta["accuracy"] == 0.95

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises(self):
        """Loading a model that doesn't exist must raise FileNotFoundError."""
        mgr = self._make_manager()

        with pytest.raises(FileNotFoundError, match="not found in persistence"):
            await mgr.load_model("nonexistent", "v99")

    @pytest.mark.asyncio
    async def test_save_creates_directory_structure(self):
        """Save must create name/version directories."""
        from aquilia.mlops.orchestrator.persistence import ModelBundle

        mgr = self._make_manager()

        weights = self.root / "w.bin"
        weights.write_bytes(b"data")

        bundle = ModelBundle(
            name="my-model", version="v2",
            weights_path=weights,
            metadata={}, framework="custom", dtype="float32",
        )
        model_dir = await mgr.save_bundle(bundle)
        assert model_dir == self.root / "my-model" / "v2"
        assert model_dir.is_dir()

    def test_register_framework(self):
        """Custom frameworks must be registerable."""
        from aquilia.mlops.orchestrator.persistence import (
            ModelPersistenceManager,
            ModelLoader,
            ModelSaver,
        )

        class FakeLoader(ModelLoader):
            def load(self, path, **kw):
                return "loaded"

        class FakeSaver(ModelSaver):
            def save(self, model, path, **kw):
                pass

        mgr = self._make_manager()
        mgr.register_framework("fake", FakeLoader(), FakeSaver())

        assert "fake" in mgr._loaders
        assert "fake" in mgr._savers


# ═══════════════════════════════════════════════════════════════════════════
# 5. DType System Regression Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDTypeRegression:
    """DType enum must expose correct properties and conversions."""

    def test_dtype_importable(self):
        from aquilia.mlops._types import DType
        assert hasattr(DType, "FLOAT32")

    def test_floating_types(self):
        from aquilia.mlops._types import DType

        for dt in (DType.FLOAT64, DType.FLOAT32, DType.FLOAT16, DType.BFLOAT16):
            assert dt.is_floating, f"{dt} should be floating"
            assert not dt.is_integer, f"{dt} should not be integer"

    def test_integer_types(self):
        from aquilia.mlops._types import DType

        for dt in (DType.INT64, DType.INT32, DType.INT16, DType.INT8, DType.UINT8):
            assert dt.is_integer, f"{dt} should be integer"
            assert not dt.is_floating, f"{dt} should not be floating"

    def test_bool_is_neither(self):
        from aquilia.mlops._types import DType

        assert not DType.BOOL.is_floating
        assert not DType.BOOL.is_integer

    def test_itemsize(self):
        from aquilia.mlops._types import DType

        assert DType.FLOAT64.itemsize == 8
        assert DType.FLOAT32.itemsize == 4
        assert DType.FLOAT16.itemsize == 2
        assert DType.INT8.itemsize == 1

    def test_string_value(self):
        from aquilia.mlops._types import DType

        assert DType.FLOAT32.value == "float32"
        assert DType.INT64.value == "int64"

    def test_tensorspec_uses_dtype(self):
        """TensorSpec.dtype must accept DType enum values."""
        from aquilia.mlops._types import DType, TensorSpec

        spec = TensorSpec(name="input", dtype=DType.FLOAT32, shape=[None, 64])
        assert spec.dtype == DType.FLOAT32
        assert spec.dtype.is_floating


# ═══════════════════════════════════════════════════════════════════════════
# 6. AppContext Hook Resolution Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestAppContextHookResolution:
    """RuntimeRegistry must resolve string hooks to callables."""

    def test_resolve_lifecycle_hooks_method_exists(self):
        """RuntimeRegistry must have _resolve_lifecycle_hooks."""
        from aquilia.aquilary.core import RuntimeRegistry
        assert hasattr(RuntimeRegistry, "_resolve_lifecycle_hooks")

    def test_string_hook_resolved_to_callable(self):
        """A string hook must become a callable after resolution."""
        from aquilia.aquilary.core import AppContext

        ctx = AppContext(
            name="test",
            version="1.0",
            manifest=None,
            config_namespace={},
            on_startup="json:dumps",
            on_shutdown="os.path.exists",
        )
        # Before resolution, hooks are strings
        assert isinstance(ctx.on_startup, str)
        assert isinstance(ctx.on_shutdown, str)
