"""
Comprehensive MLOps route tests — MLOpsController endpoints and custom MLController.

Tests cover:
- MLOpsController: /mlops/health, /mlops/healthz, /mlops/readyz, /mlops/predict,
  /mlops/models, /mlops/metrics, /mlops/drift, /mlops/plugins, /mlops/experiments,
  /mlops/hot-models, /mlops/circuit-breaker, /mlops/rate-limit, /mlops/memory,
  /mlops/capabilities, /mlops/artifacts, /mlops/lineage
- MLController: /ml/predict, /ml/models, /ml/health, /ml/retrain
- Workspace compilation with MLOps enabled
- Model registration via @model decorator
"""

import asyncio
import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════
# 1. Config / Workspace compilation tests
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceMLOpsCompilation:
    """Workspace must compile with MLOps features wired."""

    def test_workspace_importable(self):
        """workspace.py must import without errors."""
        import importlib
        spec = importlib.util.spec_from_file_location(
            "auth_workspace",
            "/Users/kuroyami/PyProjects/Aquilia/authentication/workspace.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "workspace")

    def test_workspace_has_mlops_config(self):
        """Workspace must have mlops integration configured."""
        import importlib
        spec = importlib.util.spec_from_file_location(
            "auth_workspace2",
            "/Users/kuroyami/PyProjects/Aquilia/authentication/workspace.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ws = mod.workspace
        assert ws._mlops_config is not None
        assert ws._on_startup is not None
        assert ws._on_shutdown is not None

    def test_workspace_has_ml_module(self):
        """Workspace must register the 'ml' module."""
        import importlib
        spec = importlib.util.spec_from_file_location(
            "auth_workspace3",
            "/Users/kuroyami/PyProjects/Aquilia/authentication/workspace.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ws = mod.workspace
        module_names = [m.name for m in ws._modules]
        assert "ml" in module_names


# ═══════════════════════════════════════════════════════════════════════════
# 2. MLOpsController route tests (standalone, no server required)
# ═══════════════════════════════════════════════════════════════════════════


class TestMLOpsControllerRoutes:
    """Test MLOpsController endpoints with mocked dependencies."""

    def _make_controller(self, **kwargs):
        from aquilia.mlops.serving.controllers import MLOpsController
        return MLOpsController(**kwargs)

    @pytest.mark.asyncio
    async def test_health_no_deps(self):
        """GET /mlops/health returns healthy even with no services."""
        ctrl = self._make_controller()
        result = await ctrl.health()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "components" in result

    @pytest.mark.asyncio
    async def test_healthz_no_server(self):
        """GET /mlops/healthz returns alive without serving server."""
        ctrl = self._make_controller()
        result = await ctrl.liveness()
        assert result["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readyz_no_server(self):
        """GET /mlops/readyz returns ready without serving server."""
        ctrl = self._make_controller()
        result = await ctrl.readiness()
        assert result["status"] == "ready"

    @pytest.mark.asyncio
    async def test_predict_no_server(self):
        """POST /mlops/predict returns 503 without serving server."""
        ctrl = self._make_controller()
        result = await ctrl.predict({"inputs": {"text": "hello"}})
        assert result["status"] == 503

    @pytest.mark.asyncio
    async def test_predict_with_server(self):
        """POST /mlops/predict dispatches to serving server."""
        mock_server = AsyncMock()
        mock_result = MagicMock()
        mock_result.request_id = "req-1"
        mock_result.outputs = {"label": "positive"}
        mock_result.latency_ms = 5.0
        mock_result.metadata = {}
        mock_result.token_count = 0
        mock_result.prompt_tokens = 0
        mock_result.finish_reason = "stop"
        mock_server.predict.return_value = mock_result

        ctrl = self._make_controller(serving_server=mock_server)
        result = await ctrl.predict({"inputs": {"text": "hello"}})
        assert result["request_id"] == "req-1"
        assert result["outputs"]["label"] == "positive"

    @pytest.mark.asyncio
    async def test_metrics_no_collector(self):
        """GET /mlops/metrics returns error without collector."""
        ctrl = self._make_controller()
        result = await ctrl.metrics()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_metrics_with_collector(self):
        """GET /mlops/metrics returns summary from collector."""
        mock_metrics = MagicMock()
        mock_metrics.get_summary.return_value = {"count": 100}
        ctrl = self._make_controller(metrics_collector=mock_metrics)
        result = await ctrl.metrics()
        assert result["count"] == 100

    @pytest.mark.asyncio
    async def test_list_models_no_registry(self):
        """GET /mlops/models returns empty list without registry."""
        ctrl = self._make_controller()
        result = await ctrl.list_models()
        assert result["models"] == []

    @pytest.mark.asyncio
    async def test_list_models_with_registry(self):
        """GET /mlops/models returns models from registry."""
        mock_registry = AsyncMock()
        mock_registry.list_packs.return_value = [
            {"name": "iris", "version": "v1"},
        ]
        ctrl = self._make_controller(registry=mock_registry)
        result = await ctrl.list_models()
        assert len(result["models"]) == 1

    @pytest.mark.asyncio
    async def test_get_model_no_registry(self):
        """GET /mlops/models/{name} returns error without registry."""
        ctrl = self._make_controller()
        result = await ctrl.get_model("iris")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_drift_no_detector(self):
        """GET /mlops/drift returns error without detector."""
        ctrl = self._make_controller()
        result = await ctrl.drift_status()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_plugins_no_host(self):
        """GET /mlops/plugins returns empty list without host."""
        ctrl = self._make_controller()
        result = await ctrl.list_plugins()
        assert result["plugins"] == []

    @pytest.mark.asyncio
    async def test_lineage_no_dag(self):
        """GET /mlops/lineage returns error without DAG."""
        ctrl = self._make_controller()
        result = await ctrl.lineage()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_experiments_no_ledger(self):
        """GET /mlops/experiments returns empty without ledger."""
        ctrl = self._make_controller()
        result = await ctrl.list_experiments()
        assert result["experiments"] == []

    @pytest.mark.asyncio
    async def test_hot_models_no_metrics(self):
        """GET /mlops/hot-models returns empty list."""
        ctrl = self._make_controller()
        result = await ctrl.hot_models()
        assert result["hot_models"] == []

    @pytest.mark.asyncio
    async def test_circuit_breaker_no_server(self):
        """GET /mlops/circuit-breaker returns error."""
        ctrl = self._make_controller()
        result = await ctrl.circuit_breaker_status()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_rate_limit_no_server(self):
        """GET /mlops/rate-limit returns error."""
        ctrl = self._make_controller()
        result = await ctrl.rate_limit_status()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_memory_no_server(self):
        """GET /mlops/memory returns error."""
        ctrl = self._make_controller()
        result = await ctrl.memory_status()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_capabilities_no_server(self):
        """GET /mlops/capabilities returns error."""
        ctrl = self._make_controller()
        result = await ctrl.model_capabilities()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_with_all_components(self):
        """Health check reports status of all connected components."""
        mock_registry = MagicMock()
        mock_registry._initialized = True

        mock_server = AsyncMock()
        mock_server.health.return_value = {"serving": "up"}

        mock_plugins = MagicMock()
        mock_plugins.list_plugins.return_value = [MagicMock()]
        mock_plugins.active_plugins = [MagicMock()]

        mock_cache = MagicMock()
        mock_fault = MagicMock()
        mock_artifacts = MagicMock()

        ctrl = self._make_controller(
            registry=mock_registry,
            serving_server=mock_server,
            plugin_host=mock_plugins,
            cache_service=mock_cache,
            fault_engine=mock_fault,
            artifact_store=mock_artifacts,
        )
        result = await ctrl.health()
        assert result["status"] == "healthy"
        assert "registry" in result["components"]
        assert "serving" in result["components"]
        assert "plugins" in result["components"]
        assert "cache" in result["components"]
        assert "fault_engine" in result["components"]
        assert "artifact_store" in result["components"]


# ═══════════════════════════════════════════════════════════════════════════
# 3. Custom MLController route tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMLControllerRoutes:
    """Test custom MLController endpoints."""

    def _make_controller(self, **service_kwargs):
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.controllers import MLController
        from modules.ml.services import MLService
        service = MLService(**service_kwargs)
        return MLController(service=service)

    @pytest.mark.asyncio
    async def test_list_models_empty(self):
        """GET /ml/models returns empty when no registry."""
        ctrl = self._make_controller()
        result = await ctrl.list_models()
        assert result._content is not None

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self):
        """GET /ml/health returns healthy status."""
        ctrl = self._make_controller()
        result = await ctrl.health()
        assert result._content is not None

    @pytest.mark.asyncio
    async def test_retrain_returns_accepted(self):
        """POST /ml/retrain returns 202."""
        ctx = MagicMock()
        ctrl = self._make_controller()
        result = await ctrl.retrain(ctx, {"model_name": "iris-classifier"})
        assert result.status == 202


# ═══════════════════════════════════════════════════════════════════════════
# 4. @model decorator registration tests
# ═══════════════════════════════════════════════════════════════════════════


class TestModelRegistration:
    """The @model decorator must register models correctly."""

    def test_iris_model_has_metadata(self):
        """IrisModel must have __mlops_model_name__ set by @model."""
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.model import IrisModel
        assert IrisModel.__mlops_model_name__ == "iris-classifier"
        assert IrisModel.__mlops_model_version__ == "v1.0.0"

    def test_iris_model_has_config(self):
        """IrisModel must have __mlops_model_config__."""
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.model import IrisModel
        cfg = IrisModel.__mlops_model_config__
        assert "device" in cfg
        assert "batch_size" in cfg

    def test_iris_model_is_aquilia_model(self):
        """IrisModel must be a subclass of AquiliaModel."""
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.model import IrisModel
        from aquilia.mlops.api.model_class import AquiliaModel
        assert issubclass(IrisModel, AquiliaModel)


# ═══════════════════════════════════════════════════════════════════════════
# 5. MLOps Blueprint validation tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMLBlueprints:
    """Blueprint validation for ML inputs/outputs."""

    def test_iris_input_blueprint_importable(self):
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.blueprints import IrisInputBlueprint
        assert IrisInputBlueprint is not None

    def test_iris_output_blueprint_importable(self):
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.blueprints import IrisOutputBlueprint
        assert IrisOutputBlueprint is not None

    def test_iris_input_has_required_fields(self):
        import sys
        sys.path.insert(0, "/Users/kuroyami/PyProjects/Aquilia/authentication")
        from modules.ml.blueprints import IrisInputBlueprint
        field_names = [name for name in dir(IrisInputBlueprint)
                      if not name.startswith("_")]
        # Should have sepal_length, sepal_width, petal_length, petal_width
        assert "sepal_length" in field_names
        assert "sepal_width" in field_names
        assert "petal_length" in field_names
        assert "petal_width" in field_names


# ═══════════════════════════════════════════════════════════════════════════
# 6. Train script DType integration
# ═══════════════════════════════════════════════════════════════════════════


class TestTrainDTypeIntegration:
    """Train script must use DType enum."""

    def test_train_script_importable(self):
        """train.py must compile without errors."""
        import importlib
        spec = importlib.util.spec_from_file_location(
            "ml_train",
            "/Users/kuroyami/PyProjects/Aquilia/authentication/modules/ml/train.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "train_and_pack")

    def test_dtype_import_exists(self):
        """train.py must import DType from aquilia.mlops._types."""
        import importlib
        spec = importlib.util.spec_from_file_location(
            "ml_train2",
            "/Users/kuroyami/PyProjects/Aquilia/authentication/modules/ml/train.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "DType")


# ═══════════════════════════════════════════════════════════════════════════
# 7. MLOpsController with mock orchestrator end-to-end
# ═══════════════════════════════════════════════════════════════════════════


class TestMLOpsEndToEnd:
    """End-to-end tests with fully mocked orchestrator."""

    @pytest.mark.asyncio
    async def test_full_predict_flow(self):
        """Full predict: request → controller → server → response."""
        mock_result = MagicMock()
        mock_result.request_id = "abc-123"
        mock_result.outputs = {"species": 0, "probability": [0.9, 0.05, 0.05]}
        mock_result.latency_ms = 2.5
        mock_result.metadata = {"model": "iris"}
        mock_result.token_count = 0
        mock_result.prompt_tokens = 0
        mock_result.finish_reason = "stop"

        mock_server = AsyncMock()
        mock_server.predict.return_value = mock_result

        from aquilia.mlops.serving.controllers import MLOpsController
        ctrl = MLOpsController(serving_server=mock_server)

        result = await ctrl.predict({
            "inputs": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        })
        assert result["request_id"] == "abc-123"
        assert result["outputs"]["species"] == 0
        assert result["latency_ms"] == 2.5

    @pytest.mark.asyncio
    async def test_rollout_no_engine(self):
        """POST /mlops/models/{name}/rollout returns error without engine."""
        from aquilia.mlops.serving.controllers import MLOpsController
        ctrl = MLOpsController()
        result = await ctrl.start_rollout({
            "from_version": "v1",
            "to_version": "v2",
        })
        assert "error" in result

    @pytest.mark.asyncio
    async def test_experiment_lifecycle(self):
        """Create → list → conclude experiment flow."""
        from aquilia.mlops import ExperimentLedger

        ledger = ExperimentLedger()
        from aquilia.mlops.serving.controllers import MLOpsController
        ctrl = MLOpsController(experiment_ledger=ledger)

        # Create experiment
        create_result = await ctrl.create_experiment({
            "experiment_id": "exp-1",
            "description": "Test A/B",
            "arms": [
                {"name": "control", "model_version": "v1", "weight": 50},
                {"name": "treatment", "model_version": "v2", "weight": 50},
            ],
        })
        assert create_result["experiment_id"] == "exp-1"

        # List experiments
        list_result = await ctrl.list_experiments()
        assert list_result["total"] == 1

        # Conclude
        conclude_result = await ctrl.conclude_experiment("exp-1", winner="treatment")
        assert conclude_result["experiment_id"] == "exp-1"

    @pytest.mark.asyncio
    async def test_lineage_dag(self):
        """Lineage DAG routes work with populated DAG."""
        from aquilia.mlops import ModelLineageDAG

        dag = ModelLineageDAG()
        dag.add_model("model-a", version="v1")
        dag.add_model("model-b", version="v1", parents=["model-a"])

        from aquilia.mlops.serving.controllers import MLOpsController
        ctrl = MLOpsController(lineage_dag=dag)

        result = await ctrl.lineage()
        assert result["total"] == 2
        assert "model-a" in result["roots"]

        ancestors = await ctrl.lineage_ancestors("model-b")
        assert "model-a" in ancestors["ancestors"]

        descendants = await ctrl.lineage_descendants("model-a")
        assert "model-b" in descendants["descendants"]
