"""
Phase 31 — MLOps Admin Page Tests.

Comprehensive tests for the MLOps admin page:
- AdminConfig.modules includes "mlops" (default False)
- AdminModules builder: enable_mlops() / disable_mlops()
- Integration.admin(enable_mlops=True) flat syntax
- AdminConfig.is_module_enabled("mlops")
- AdminConfig.from_dict() round-trip
- get_mlops_data() structure & correctness
- set_mlops_services() stores references
- render_mlops_page() produces HTML with Chart.js
- Controller routes: /mlops/, /mlops/api/
- Template file exists and extends base.html
- Chart canvas IDs present in template
- Config hints for disabled page
- Server route wiring
- Drawer elements
- Code snippet tabs
- Capabilities reference panel
"""

from __future__ import annotations

import inspect
import json
import os
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest


# ════════════════════════════════════════════════════════════════════════════
# 1. ADMIN CONFIG — MODULE REGISTRATION
# ════════════════════════════════════════════════════════════════════════════


class TestAdminConfigMlopsModule:
    """AdminConfig must include 'mlops' in its modules dict."""

    def test_admin_config_has_mlops_key(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert "mlops" in cfg.modules

    def test_admin_config_mlops_disabled_by_default(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert cfg.modules["mlops"] is False

    def test_admin_config_is_module_enabled_mlops_false(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert cfg.is_module_enabled("mlops") is False

    def test_admin_config_is_module_enabled_mlops_true(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(
            modules={
                "dashboard": True,
                "orm": True,
                "build": True,
                "migrations": True,
                "config": True,
                "workspace": True,
                "permissions": True,
                "monitoring": False,
                "admin_users": True,
                "profile": True,
                "audit": False,
                "containers": False,
                "pods": False,
                "query_inspector": False,
                "tasks": False,
                "errors": False,
                "testing": False,
                "mlops": True,
            }
        )
        assert cfg.is_module_enabled("mlops") is True

    def test_admin_config_from_dict_mlops_default_false(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({})
        assert cfg.is_module_enabled("mlops") is False

    def test_admin_config_from_dict_mlops_enabled(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        assert cfg.is_module_enabled("mlops") is True

    def test_admin_config_from_dict_mlops_disabled_explicit(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": False}})
        assert cfg.is_module_enabled("mlops") is False

    def test_admin_config_from_dict_preserves_other_modules(self):
        """Enabling mlops shouldn't break other modules."""
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True, "tasks": True}})
        assert cfg.is_module_enabled("mlops") is True
        assert cfg.is_module_enabled("tasks") is True
        assert cfg.is_module_enabled("dashboard") is True
        assert cfg.is_module_enabled("monitoring") is False


# ════════════════════════════════════════════════════════════════════════════
# 2. GET_MLOPS_DATA
# ════════════════════════════════════════════════════════════════════════════


class TestGetMlopsData:
    """get_mlops_data() returns correct structure."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_get_mlops_data_returns_dict(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data, dict)

    def test_get_mlops_data_has_available_key(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "available" in data

    def test_get_mlops_data_has_models_key(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "models" in data

    def test_get_mlops_data_has_total_models(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_models" in data

    def test_get_mlops_data_has_total_inferences(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_inferences" in data

    def test_get_mlops_data_has_total_errors(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_errors" in data

    def test_get_mlops_data_has_total_tokens(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_tokens" in data

    def test_get_mlops_data_has_total_stream_requests(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_stream_requests" in data

    def test_get_mlops_data_has_metrics(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "metrics" in data

    def test_get_mlops_data_has_latency(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "latency" in data

    def test_get_mlops_data_has_throughput(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "throughput" in data

    def test_get_mlops_data_has_hot_models(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "hot_models" in data

    def test_get_mlops_data_has_drift(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "drift" in data

    def test_get_mlops_data_has_circuit_breaker(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "circuit_breaker" in data

    def test_get_mlops_data_has_rate_limiter(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "rate_limiter" in data

    def test_get_mlops_data_has_memory(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "memory" in data

    def test_get_mlops_data_has_plugins(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "plugins" in data

    def test_get_mlops_data_has_total_plugins(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_plugins" in data

    def test_get_mlops_data_has_experiments(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "experiments" in data

    def test_get_mlops_data_has_total_experiments(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_experiments" in data

    def test_get_mlops_data_has_active_experiments(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "active_experiments" in data

    def test_get_mlops_data_has_lineage(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "lineage" in data

    def test_get_mlops_data_has_lineage_nodes(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "lineage_nodes" in data

    def test_get_mlops_data_has_rollouts(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "rollouts" in data

    def test_get_mlops_data_has_total_rollouts(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "total_rollouts" in data

    def test_get_mlops_data_has_active_rollouts(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "active_rollouts" in data

    def test_get_mlops_data_has_charts(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "charts" in data

    def test_get_mlops_data_charts_has_model_states(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "model_states" in data["charts"]

    def test_get_mlops_data_charts_has_frameworks(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "frameworks" in data["charts"]

    def test_get_mlops_data_charts_has_plugin_states(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "plugin_states" in data["charts"]

    def test_get_mlops_data_charts_has_experiment_statuses(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "experiment_statuses" in data["charts"]

    def test_get_mlops_data_charts_has_rollout_phases(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "rollout_phases" in data["charts"]

    def test_get_mlops_data_has_enum_lists(self):
        """Capability enum lists must be present."""
        site = self._make_site()
        data = site.get_mlops_data()
        for key in [
            "frameworks",
            "runtime_kinds",
            "model_types",
            "device_types",
            "batching_strategies",
            "rollout_strategies",
            "drift_methods",
            "quantize_presets",
            "export_targets",
            "inference_modes",
        ]:
            assert key in data, f"Missing enum key: {key}"
            assert isinstance(data[key], list), f"{key} should be a list"
            assert len(data[key]) > 0, f"{key} should not be empty"

    def test_get_mlops_data_frameworks_includes_pytorch(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "pytorch" in data["frameworks"]

    def test_get_mlops_data_device_types_includes_cpu(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "cpu" in data["device_types"]

    def test_get_mlops_data_models_default_empty(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert data["models"] == []
        assert data["total_models"] == 0

    def test_get_mlops_data_plugins_default_empty(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert data["plugins"] == []
        assert data["total_plugins"] == 0

    def test_get_mlops_data_experiments_default_empty(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert data["experiments"] == []
        assert data["total_experiments"] == 0

    def test_get_mlops_data_rollouts_default_empty(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert data["rollouts"] == []
        assert data["total_rollouts"] == 0

    def test_get_mlops_data_serializable(self):
        """All data must be JSON-serializable."""
        site = self._make_site()
        data = site.get_mlops_data()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert isinstance(parsed, dict)


# ════════════════════════════════════════════════════════════════════════════
# 3. SET_MLOPS_SERVICES
# ════════════════════════════════════════════════════════════════════════════


class TestSetMlopsServices:
    """set_mlops_services() stores service references on the site."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_set_mlops_services_exists(self):
        from aquilia.admin.site import AdminSite

        assert hasattr(AdminSite, "set_mlops_services")

    def test_set_mlops_services_stores_registry(self):
        site = self._make_site()
        mock_registry = MagicMock()
        site.set_mlops_services(registry=mock_registry)
        assert site._mlops_registry is mock_registry

    def test_set_mlops_services_stores_metrics_collector(self):
        site = self._make_site()
        mock_metrics = MagicMock()
        site.set_mlops_services(metrics_collector=mock_metrics)
        assert site._mlops_metrics is mock_metrics

    def test_set_mlops_services_stores_drift_detector(self):
        site = self._make_site()
        mock_drift = MagicMock()
        site.set_mlops_services(drift_detector=mock_drift)
        assert site._mlops_drift is mock_drift

    def test_set_mlops_services_stores_circuit_breaker(self):
        site = self._make_site()
        mock_cb = MagicMock()
        site.set_mlops_services(circuit_breaker=mock_cb)
        assert site._mlops_circuit_breaker is mock_cb

    def test_set_mlops_services_stores_rate_limiter(self):
        site = self._make_site()
        mock_rl = MagicMock()
        site.set_mlops_services(rate_limiter=mock_rl)
        assert site._mlops_rate_limiter is mock_rl

    def test_set_mlops_services_stores_memory_tracker(self):
        site = self._make_site()
        mock_mem = MagicMock()
        site.set_mlops_services(memory_tracker=mock_mem)
        assert site._mlops_memory_tracker is mock_mem

    def test_set_mlops_services_stores_plugin_host(self):
        site = self._make_site()
        mock_ph = MagicMock()
        site.set_mlops_services(plugin_host=mock_ph)
        assert site._mlops_plugins is mock_ph

    def test_set_mlops_services_stores_experiment_ledger(self):
        site = self._make_site()
        mock_el = MagicMock()
        site.set_mlops_services(experiment_ledger=mock_el)
        assert site._mlops_experiments is mock_el

    def test_set_mlops_services_stores_lineage_dag(self):
        site = self._make_site()
        mock_ld = MagicMock()
        site.set_mlops_services(lineage_dag=mock_ld)
        assert site._mlops_lineage is mock_ld

    def test_set_mlops_services_stores_rollout_engine(self):
        site = self._make_site()
        mock_re = MagicMock()
        site.set_mlops_services(rollout_engine=mock_re)
        assert site._mlops_rollout is mock_re


# ════════════════════════════════════════════════════════════════════════════
# 4. RENDER_MLOPS_PAGE
# ════════════════════════════════════════════════════════════════════════════


class TestRenderMlopsPage:
    """render_mlops_page() produces correct HTML."""

    def _mlops_data(self, **overrides):
        """Build minimal mlops_data dict for render calls."""
        base = {
            "available": True,
            "models": [
                {
                    "name": "sentiment",
                    "version": "1.0.0",
                    "state": "loaded",
                    "framework": "pytorch",
                    "model_type": "classifier",
                },
            ],
            "total_models": 1,
            "total_inferences": 1500,
            "total_errors": 3,
            "total_tokens": 50000,
            "total_stream_requests": 200,
            "total_prompt_tokens": 12000,
            "metrics": {},
            "latency": {"p50": 12.5, "p95": 45.2, "p99": 120.1, "ewma": 15.3},
            "throughput": {"ewma": 42.7, "ttft_ewma": 8.2},
            "hot_models": [{"name": "sentiment", "score": 1500}],
            "drift": {"method": "psi", "threshold": 0.2, "has_reference": True},
            "circuit_breaker": {
                "state": "closed",
                "total_requests": 100,
                "total_failures": 2,
                "total_trips": 0,
                "total_successes": 98,
            },
            "rate_limiter": {"total_allowed": 950, "total_rejected": 50, "tokens_available": 8.5, "capacity": 10},
            "memory": {
                "current_bytes": 104857600,
                "soft_limit": 209715200,
                "hard_limit": 419430400,
                "tracked_models": 3,
                "evictions": 0,
            },
            "plugins": [
                {"name": "custom-logger", "version": "0.1.0", "state": "activated", "error": ""},
            ],
            "total_plugins": 1,
            "experiments": [
                {
                    "id": "exp-1",
                    "name": "ab-test-v2",
                    "status": "active",
                    "variants": ["control", "treatment"],
                    "total_assignments": 500,
                },
            ],
            "total_experiments": 1,
            "active_experiments": 1,
            "lineage": {"model-a": {"parents": []}, "model-b": {"parents": ["model-a"]}},
            "lineage_nodes": 2,
            "rollouts": [
                {
                    "id": "rollout-abc123",
                    "from_version": "1.0.0",
                    "to_version": "2.0.0",
                    "strategy": "canary",
                    "phase": "in_progress",
                    "percentage": 25,
                    "steps": 2,
                    "error": "",
                },
            ],
            "total_rollouts": 1,
            "active_rollouts": 1,
            "frameworks": ["pytorch", "tensorflow", "onnx", "jax", "sklearn"],
            "runtime_kinds": ["python", "onnx", "triton"],
            "model_types": ["classifier", "regressor", "generative"],
            "device_types": ["cpu", "cuda", "mps"],
            "batching_strategies": ["none", "fixed", "adaptive"],
            "rollout_strategies": ["canary", "ab", "blue_green", "rolling", "shadow"],
            "drift_methods": ["psi", "ks_test", "distribution"],
            "quantize_presets": ["int8", "fp16", "int4"],
            "export_targets": ["tflite", "coreml", "onnx"],
            "inference_modes": ["sync", "async", "streaming", "batch"],
            "charts": {
                "model_states": {"loaded": 1},
                "frameworks": {"pytorch": 1},
                "plugin_states": {"activated": 1},
                "experiment_statuses": {"active": 1},
                "rollout_phases": {"in_progress": 1},
            },
        }
        base.update(overrides)
        return base

    def test_render_mlops_page_returns_string(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert isinstance(html, str)

    def test_render_mlops_page_contains_html(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "<html" in html or "<!DOCTYPE" in html or "MLOps" in html

    def test_render_mlops_page_includes_chart_js_cdn(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "chart.js" in html.lower() or "Chart" in html

    def test_render_mlops_page_includes_title(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "MLOps" in html

    def test_render_mlops_page_includes_model_name(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "sentiment" in html

    def test_render_mlops_page_includes_version(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "1.0.0" in html

    def test_render_mlops_page_includes_framework(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "pytorch" in html

    def test_render_mlops_page_includes_inferences_count(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "1,500" in html or "1500" in html

    def test_render_mlops_page_includes_latency_p50(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "12.5" in html

    def test_render_mlops_page_includes_circuit_breaker_state(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "CLOSED" in html or "closed" in html

    def test_render_mlops_page_includes_drift_method(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "psi" in html

    def test_render_mlops_page_includes_plugin_name(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "custom-logger" in html

    def test_render_mlops_page_includes_experiment_name(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "ab-test-v2" in html

    def test_render_mlops_page_includes_rollout_strategy(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "canary" in html

    def test_render_mlops_page_includes_hot_models(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "Hot Models" in html or "hot_models" in html or "Most Requested" in html

    def test_render_mlops_page_shows_available_status(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(available=True))
        assert "Available" in html

    def test_render_mlops_page_shows_not_configured_when_unavailable(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(available=False))
        assert "Not Configured" in html

    def test_render_mlops_page_chart_canvas_elements(self):
        """All expected chart canvas IDs present."""
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "chart-model-states" in html
        assert "chart-frameworks" in html
        assert "chart-plugin-states" in html
        assert "chart-rollout-phases" in html

    def test_render_mlops_page_has_drawer(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "aq-drawer" in html
        assert "aq-drawer-overlay" in html

    def test_render_mlops_page_has_snippet_tabs(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "snippet-tab" in html
        assert "snippet-content" in html

    def test_render_mlops_page_has_code_block_container(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "code-block-container" in html

    def test_render_mlops_page_has_python_highlighter(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert 'data-aq-highlight="python"' in html

    def test_render_mlops_page_has_capabilities_panel(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data())
        assert "Capabilities Reference" in html or "cap-tab" in html

    def test_render_mlops_page_empty_models(self):
        """No models — should show empty state."""
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(models=[], total_models=0))
        assert "No models registered" in html

    def test_render_mlops_page_empty_rollouts(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(rollouts=[], total_rollouts=0, active_rollouts=0))
        assert "No rollouts active" in html

    def test_render_mlops_page_empty_experiments(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(experiments=[], total_experiments=0, active_experiments=0))
        assert "No experiments configured" in html

    def test_render_mlops_page_empty_plugins(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data(plugins=[], total_plugins=0))
        assert "No plugins loaded" in html


# ════════════════════════════════════════════════════════════════════════════
# 5. RENDER MLOPS PAGE SIGNATURE
# ════════════════════════════════════════════════════════════════════════════


class TestRenderMlopsPageSignature:
    """render_mlops_page() function signature is correct."""

    def test_render_mlops_page_importable(self):
        from aquilia.admin.templates import render_mlops_page

        assert callable(render_mlops_page)

    def test_render_mlops_page_accepts_mlops_data(self):
        from aquilia.admin.templates import render_mlops_page

        sig = inspect.signature(render_mlops_page)
        assert "mlops_data" in sig.parameters

    def test_render_mlops_page_accepts_app_list(self):
        from aquilia.admin.templates import render_mlops_page

        sig = inspect.signature(render_mlops_page)
        assert "app_list" in sig.parameters

    def test_render_mlops_page_accepts_identity_name(self):
        from aquilia.admin.templates import render_mlops_page

        sig = inspect.signature(render_mlops_page)
        assert "identity_name" in sig.parameters

    def test_render_mlops_page_accepts_identity_avatar(self):
        from aquilia.admin.templates import render_mlops_page

        sig = inspect.signature(render_mlops_page)
        assert "identity_avatar" in sig.parameters


# ════════════════════════════════════════════════════════════════════════════
# 6. CONTROLLER ROUTES
# ════════════════════════════════════════════════════════════════════════════


class TestAdminControllerMlopsRoutes:
    """AdminController has mlops routes compiled correctly."""

    def test_controller_has_mlops_view_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mlops_view")

    def test_controller_has_mlops_api_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mlops_api")

    def test_mlops_view_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mlops_view)

    def test_mlops_api_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mlops_api)

    def test_controller_imports_render_mlops_page(self):
        """render_mlops_page is imported in controller module."""
        import aquilia.admin.controller as ctrl_mod

        assert hasattr(ctrl_mod, "render_mlops_page")

    def test_mlops_view_route_metadata(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "mlops" in source

    def test_mlops_api_route_metadata(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_api)
        assert "mlops" in source
        assert "json" in source.lower() or "JSON" in source

    def test_mlops_view_checks_identity(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "_require_identity" in source

    def test_mlops_api_checks_identity(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_api)
        assert "_require_identity" in source

    def test_mlops_view_checks_module_enabled(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "is_module_enabled" in source
        assert '"mlops"' in source or "'mlops'" in source

    def test_mlops_api_checks_module_enabled(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_api)
        assert "is_module_enabled" in source

    def test_mlops_view_calls_get_mlops_data(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "get_mlops_data" in source

    def test_mlops_api_calls_get_mlops_data(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_api)
        assert "get_mlops_data" in source

    def test_mlops_view_calls_render_mlops_page(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "render_mlops_page" in source

    def test_mlops_view_returns_disabled_page_when_off(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mlops_view)
        assert "_module_disabled_response" in source
        assert '"MLOps"' in source or "'MLOps'" in source


# ════════════════════════════════════════════════════════════════════════════
# 7. TEMPLATE FILE
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsTemplateFile:
    """mlops.html template file structure and content."""

    def _template_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia",
            "admin",
            "templates",
            "mlops.html",
        )

    def test_template_file_exists(self):
        assert os.path.isfile(self._template_path())

    def test_template_extends_base(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert '{% extends "base.html" %}' in content

    def test_template_has_title_block(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "{% block title %}" in content
        assert "MLOps" in content

    def test_template_has_content_block(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "{% block content %}" in content

    def test_template_includes_chart_js_cdn(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "chart.js" in content.lower()
        assert "cdn.jsdelivr.net" in content

    def test_template_has_chart_canvas_elements(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "chart-model-states" in content
        assert "chart-frameworks" in content
        assert "chart-plugin-states" in content
        assert "chart-rollout-phases" in content

    def test_template_has_status_bar(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Available" in content

    def test_template_has_icon(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "icon-cpu" in content

    def test_template_iterates_models(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "models" in content
        assert "model.name" in content or "model" in content

    def test_template_iterates_plugins(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "plugins" in content
        assert "plugin.name" in content or "plugin" in content

    def test_template_iterates_rollouts(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "rollouts" in content

    def test_template_iterates_experiments(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "experiments" in content

    def test_template_has_javascript_section(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "{% block extra_js %}" in content

    def test_template_creates_chart_instances(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "new Chart(" in content

    def test_template_has_slide_out_drawer(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "aq-drawer-overlay" in content
        assert "aq-drawer" in content
        assert "openDrawer" in content
        assert "closeDrawer" in content

    def test_template_drawer_has_escape_key(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Escape" in content

    def test_template_has_model_drawer_handler(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "openModelDrawer" in content

    def test_template_has_rollout_drawer_handler(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "openRolloutDrawer" in content

    def test_template_has_snippet_panel(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snippet-panel" in content
        assert "snippet-tab" in content
        assert "snippet-content" in content

    def test_template_has_code_block_containers(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "code-block-container" in content
        assert "code-block-header" in content
        assert "code-block-body" in content

    def test_template_has_python_highlighter(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert 'data-aq-highlight="python"' in content

    def test_template_has_copy_snippet_function(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "copySnippet" in content

    def test_template_has_capabilities_tabs(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "cap-tab" in content
        assert "cap-panel" in content
        assert "cap-frameworks" in content
        assert "cap-devices" in content

    def test_template_has_circuit_breaker_panel(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Circuit Breaker" in content
        assert "cb-closed" in content or "cb-indicator" in content

    def test_template_has_rate_limiter_panel(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Rate Limiter" in content

    def test_template_has_memory_tracker_panel(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Memory Tracker" in content

    def test_template_has_drift_detection_section(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Drift" in content

    def test_template_has_hot_models_section(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Hot Models" in content or "Most Requested" in content

    def test_template_has_model_lineage_section(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "Lineage" in content

    def test_template_has_auto_refresh_polling(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "POLL_INTERVAL" in content or "setInterval" in content

    def test_template_snippet_tabs_model(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snip-model" in content

    def test_template_snippet_tabs_serve(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snip-serve" in content

    def test_template_snippet_tabs_pipeline(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snip-pipeline" in content

    def test_template_snippet_tabs_rollout(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snip-rollout" in content

    def test_template_snippet_tabs_config(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "snip-config" in content

    def test_template_model_search_input(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "modelSearch" in content

    def test_template_count_up_animation(self):
        with open(self._template_path(), encoding="utf-8") as f:
            content = f.read()
        assert "data-count" in content
        assert "requestAnimationFrame" in content


# ════════════════════════════════════════════════════════════════════════════
# 8. SERVER ROUTE WIRING
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsServerRouteWiring:
    """MLOps routes are registered in _wire_admin_integration (server.py)."""

    def test_server_module_has_wire_admin_integration(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "_wire_admin_integration" in src

    def test_server_registers_mlops_view_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mlops_view" in src
        assert "/mlops/" in src

    def test_server_registers_mlops_api_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mlops_api" in src
        assert "/mlops/api/" in src

    def test_mlops_routes_use_get_method(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "mlops_view" in line and "admin_routes" in line:
                assert '"GET"' in line or "'GET'" in line
            if "mlops_api" in line and "admin_routes" in line:
                assert '"GET"' in line or "'GET'" in line

    def test_mlops_routes_after_testing_routes(self):
        """MLOps routes should be placed after testing routes."""
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        testing_pos = src.find("testing_view")
        mlops_pos = src.find("mlops_view")
        assert testing_pos > 0
        assert mlops_pos > 0
        assert mlops_pos > testing_pos


# ════════════════════════════════════════════════════════════════════════════
# 9. DISABLED PAGE CONFIG HINTS
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsDisabledPage:
    """MLOps appears in _config_hints for disabled page."""

    def test_config_hints_has_mlops(self):
        from aquilia.admin.controller import AdminController

        src = inspect.getsource(AdminController)
        assert '"MLOps"' in src or "'MLOps'" in src

    def test_config_hints_mlops_builder_hint(self):
        from aquilia.admin.controller import AdminController

        src = inspect.getsource(AdminController)
        assert "enable_mlops()" in src

    def test_config_hints_mlops_flat_hint(self):
        from aquilia.admin.controller import AdminController

        src = inspect.getsource(AdminController)
        assert "enable_mlops=True" in src

    def test_config_hints_mlops_icon(self):
        from aquilia.admin.controller import AdminController

        src = inspect.getsource(AdminController)
        assert "cpu" in src

    def test_config_hints_mlops_description(self):
        from aquilia.admin.controller import AdminController

        src = inspect.getsource(AdminController)
        assert "model registry" in src.lower() or "inference" in src.lower()


# ════════════════════════════════════════════════════════════════════════════
# 10. MLOPS IMPORTS
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsImports:
    """Critical MLOps subsystem types are importable."""

    def test_import_framework_enum(self):
        from aquilia.mlops import Framework

        assert hasattr(Framework, "PYTORCH")

    def test_import_runtime_kind_enum(self):
        from aquilia.mlops import RuntimeKind

        assert hasattr(RuntimeKind, "PYTHON")

    def test_import_model_type_enum(self):
        from aquilia.mlops import ModelType

        assert hasattr(ModelType, "CLASSICAL_ML")

    def test_import_device_type_enum(self):
        from aquilia.mlops import DeviceType

        assert hasattr(DeviceType, "CPU")

    def test_import_batching_strategy_enum(self):
        from aquilia.mlops import BatchingStrategy

        assert hasattr(BatchingStrategy, "SIZE")

    def test_import_rollout_strategy_enum(self):
        from aquilia.mlops import RolloutStrategy

        assert hasattr(RolloutStrategy, "CANARY")

    def test_import_drift_method_enum(self):
        from aquilia.mlops import DriftMethod

        assert hasattr(DriftMethod, "PSI")

    def test_import_quantize_preset_enum(self):
        from aquilia.mlops import QuantizePreset

        assert hasattr(QuantizePreset, "INT8")

    def test_import_export_target_enum(self):
        from aquilia.mlops import ExportTarget

        assert hasattr(ExportTarget, "TFLITE")

    def test_import_inference_mode_enum(self):
        from aquilia.mlops import InferenceMode

        assert hasattr(InferenceMode, "SYNC")

    def test_import_circuit_breaker(self):
        from aquilia.mlops import CircuitBreaker

        assert CircuitBreaker is not None

    def test_import_token_bucket_rate_limiter(self):
        from aquilia.mlops import TokenBucketRateLimiter

        assert TokenBucketRateLimiter is not None

    def test_import_memory_tracker(self):
        from aquilia.mlops import MemoryTracker

        assert MemoryTracker is not None

    def test_import_model_lineage_dag(self):
        from aquilia.mlops import ModelLineageDAG

        assert ModelLineageDAG is not None

    def test_import_experiment_ledger(self):
        from aquilia.mlops import ExperimentLedger

        assert ExperimentLedger is not None

    def test_import_metrics_collector(self):
        from aquilia.mlops import MetricsCollector

        assert MetricsCollector is not None

    def test_import_drift_detector(self):
        from aquilia.mlops import DriftDetector

        assert DriftDetector is not None

    def test_import_plugin_host(self):
        from aquilia.mlops import PluginHost

        assert PluginHost is not None

    def test_import_model_orchestrator(self):
        from aquilia.mlops import ModelOrchestrator

        assert ModelOrchestrator is not None

    def test_import_model_registry(self):
        from aquilia.mlops import ModelRegistry

        assert ModelRegistry is not None


# ════════════════════════════════════════════════════════════════════════════
# 11. EDGE CASES
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsDataEdgeCases:
    """Edge cases for get_mlops_data()."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_no_mlops_services_set_returns_empty_collections(self):
        """Without set_mlops_services(), data has empty collections."""
        site = self._make_site()
        data = site.get_mlops_data()
        assert data["models"] == []
        assert data["plugins"] == []
        assert data["experiments"] == []
        assert data["rollouts"] == []
        assert data["hot_models"] == []

    def test_broken_registry_graceful(self):
        """A failing registry doesn't crash get_mlops_data()."""
        site = self._make_site()
        mock_registry = MagicMock()
        mock_registry.list_models.side_effect = RuntimeError("broken")
        site._mlops_registry = mock_registry
        data = site.get_mlops_data()
        assert data["models"] == []

    def test_broken_metrics_graceful(self):
        """A failing metrics collector doesn't crash get_mlops_data()."""
        site = self._make_site()
        mock_metrics = MagicMock()
        mock_metrics.get_summary.side_effect = RuntimeError("broken")
        site._mlops_metrics = mock_metrics
        data = site.get_mlops_data()
        assert data["total_inferences"] == 0

    def test_broken_plugin_host_graceful(self):
        site = self._make_site()
        mock_ph = MagicMock()
        mock_ph.list_plugins.side_effect = RuntimeError("broken")
        site._mlops_plugins = mock_ph
        data = site.get_mlops_data()
        assert data["plugins"] == []

    def test_broken_rollout_engine_graceful(self):
        site = self._make_site()
        mock_re = MagicMock()
        mock_re.list_rollouts.side_effect = RuntimeError("broken")
        site._mlops_rollout = mock_re
        data = site.get_mlops_data()
        assert data["rollouts"] == []

    def test_charts_model_states_aggregation(self):
        """Charts correctly aggregate model states."""
        site = self._make_site()
        mock_registry = MagicMock()
        mock_registry.list_models.return_value = ["a", "b", "c"]
        entry_a = MagicMock()
        entry_a.to_dict.return_value = {"name": "a", "state": "loaded", "framework": "pytorch"}
        entry_b = MagicMock()
        entry_b.to_dict.return_value = {"name": "b", "state": "loaded", "framework": "tensorflow"}
        entry_c = MagicMock()
        entry_c.to_dict.return_value = {"name": "c", "state": "failed", "framework": "pytorch"}
        mock_registry.get.side_effect = lambda n: {"a": entry_a, "b": entry_b, "c": entry_c}[n]
        site._mlops_registry = mock_registry
        data = site.get_mlops_data()
        assert data["charts"]["model_states"]["loaded"] == 2
        assert data["charts"]["model_states"]["failed"] == 1
        assert data["charts"]["frameworks"]["pytorch"] == 2
        assert data["charts"]["frameworks"]["tensorflow"] == 1

    def test_active_rollouts_count(self):
        """active_rollouts counts only in_progress rollouts."""
        site = self._make_site()
        mock_re = MagicMock()
        r1 = MagicMock()
        r1.id = "r1"
        r1.config.from_version = "1.0"
        r1.config.to_version = "2.0"
        r1.config.strategy.value = "canary"
        r1.phase.value = "in_progress"
        r1.current_percentage = 50
        r1.steps_completed = 3
        r1.error = None
        r2 = MagicMock()
        r2.id = "r2"
        r2.config.from_version = "2.0"
        r2.config.to_version = "3.0"
        r2.config.strategy.value = "rolling"
        r2.phase.value = "completed"
        r2.current_percentage = 100
        r2.steps_completed = 5
        r2.error = None
        mock_re.list_rollouts.return_value = [r1, r2]
        site._mlops_rollout = mock_re
        data = site.get_mlops_data()
        assert data["total_rollouts"] == 2
        assert data["active_rollouts"] == 1


# ════════════════════════════════════════════════════════════════════════════
# 12. FULL RENDER INTEGRATION
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsRenderIntegration:
    """Full integration: get_mlops_data → render_mlops_page."""

    def _make_site_with_services(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True

        # Mock a registry with one model
        mock_registry = MagicMock()
        mock_registry.list_models.return_value = ["test-model"]
        entry = MagicMock()
        entry.to_dict.return_value = {
            "name": "test-model",
            "version": "1.0.0",
            "state": "loaded",
            "framework": "pytorch",
            "model_type": "classifier",
        }
        mock_registry.get.return_value = entry
        site._mlops_registry = mock_registry

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.get_summary.return_value = {
            "aquilia_inference_total": 42,
            "aquilia_inference_errors_total": 1,
            "aquilia_tokens_generated_total": 1000,
            "aquilia_stream_requests_total": 10,
            "aquilia_prompt_tokens_total": 500,
        }
        mock_metrics.hot_models.return_value = [("test-model", 42)]
        mock_metrics.percentile.return_value = 10.0
        mock_metrics.ewma.return_value = 5.0
        site._mlops_metrics = mock_metrics

        return site

    def test_full_integration_produces_html(self):
        from aquilia.admin.templates import render_mlops_page

        site = self._make_site_with_services()
        data = site.get_mlops_data()
        html = render_mlops_page(mlops_data=data)
        assert isinstance(html, str)
        assert len(html) > 1000  # Should be substantial HTML

    def test_full_integration_contains_model_name(self):
        from aquilia.admin.templates import render_mlops_page

        site = self._make_site_with_services()
        data = site.get_mlops_data()
        html = render_mlops_page(mlops_data=data)
        assert "test-model" in html

    def test_full_integration_contains_inference_count(self):
        from aquilia.admin.templates import render_mlops_page

        site = self._make_site_with_services()
        data = site.get_mlops_data()
        html = render_mlops_page(mlops_data=data)
        assert "42" in html

    def test_full_integration_json_serializable_data(self):
        """Data from get_mlops_data should be JSON serializable."""
        site = self._make_site_with_services()
        data = site.get_mlops_data()
        result = json.dumps(data, default=str)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["total_models"] == 1
        assert parsed["total_inferences"] == 42


# ════════════════════════════════════════════════════════════════════════════
# 13. MLOps v2 — AUTOSCALER DATA
# ════════════════════════════════════════════════════════════════════════════


class TestGetMlopsDataAutoscaler:
    """get_mlops_data() autoscaler section."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_autoscaler_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "autoscaler" in data

    def test_autoscaler_default_empty_dict(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["autoscaler"], dict)

    def test_autoscaler_with_mock_service(self):
        site = self._make_site()
        mock_as = MagicMock()
        mock_as.policy = MagicMock()
        mock_as.policy.min_replicas = 1
        mock_as.policy.max_replicas = 8
        mock_as.policy.target_concurrency = 50
        mock_as.policy.target_latency_p95_ms = 200.0
        mock_as.policy.target_gpu_utilization = 0.75
        mock_as.policy.target_tokens_per_second = None
        mock_as.policy.cooldown_seconds = 60
        mock_as._current_replicas = 3
        mock_as.window_stats = {
            "window_rps": 12.5,
            "avg_latency": 45.2,
            "error_rate": 0.01,
            "samples": 100,
        }
        # evaluate() returns a ScalingDecision
        mock_decision = MagicMock()
        mock_decision.current_replicas = 3
        mock_decision.desired_replicas = 4
        mock_decision.reason = "high concurrency"
        mock_as.evaluate.return_value = mock_decision
        site._mlops_autoscaler = mock_as
        data = site.get_mlops_data()
        assert data["autoscaler"]["policy"]["min_replicas"] == 1
        assert data["autoscaler"]["policy"]["max_replicas"] == 8
        assert data["autoscaler"]["current_replicas"] == 3
        assert data["autoscaler"]["window_stats"]["window_rps"] == 12.5

    def test_broken_autoscaler_graceful(self):
        site = self._make_site()
        mock_as = MagicMock()
        mock_as.policy = MagicMock(side_effect=RuntimeError("broken"))
        type(mock_as).policy = property(lambda self: (_ for _ in ()).throw(RuntimeError("broken")))
        site._mlops_autoscaler = mock_as
        data = site.get_mlops_data()
        assert isinstance(data["autoscaler"], dict)


# ════════════════════════════════════════════════════════════════════════════
# 14. MLOps v2 — RBAC DATA
# ════════════════════════════════════════════════════════════════════════════


class TestGetMlopsDataRBAC:
    """get_mlops_data() rbac section."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_rbac_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "rbac" in data

    def test_rbac_default_empty_dict(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["rbac"], dict)

    def test_permissions_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "permissions" in data

    def test_permissions_is_list(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["permissions"], list)


# ════════════════════════════════════════════════════════════════════════════
# 15. MLOps v2 — BATCH QUEUE + LRU CACHE DATA
# ════════════════════════════════════════════════════════════════════════════


class TestGetMlopsDataQueueCache:
    """get_mlops_data() batch_queue and lru_cache sections."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_batch_queue_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "batch_queue" in data

    def test_lru_cache_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "lru_cache" in data

    def test_batch_queue_default_empty_dict(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["batch_queue"], dict)

    def test_lru_cache_default_empty_dict(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["lru_cache"], dict)

    def test_batch_queue_with_mock(self):
        site = self._make_site()
        mock_bq = MagicMock()
        mock_bq.stats = {
            "size": 5,
            "capacity": 100,
            "enqueued": 50,
            "dequeued": 45,
            "dropped": 0,
            "pending_tokens": 128,
        }
        site._mlops_batch_queue = mock_bq
        data = site.get_mlops_data()
        assert data["batch_queue"]["size"] == 5
        assert data["batch_queue"]["capacity"] == 100

    def test_lru_cache_with_mock(self):
        site = self._make_site()
        mock_lru = MagicMock()
        mock_lru.stats = {
            "capacity": 50,
            "size": 12,
            "hits": 200,
            "misses": 30,
            "hit_rate": 0.87,
        }
        site._mlops_lru_cache = mock_lru
        data = site.get_mlops_data()
        assert data["lru_cache"]["capacity"] == 50
        assert data["lru_cache"]["hit_rate"] == 0.87


# ════════════════════════════════════════════════════════════════════════════
# 16. MLOps v2 — PER-MODEL METRICS + PROMETHEUS
# ════════════════════════════════════════════════════════════════════════════


class TestGetMlopsDataPerModelMetrics:
    """get_mlops_data() per_model_metrics and prometheus_text sections."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_per_model_metrics_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "per_model_metrics" in data

    def test_per_model_metrics_default_empty_list(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["per_model_metrics"], list)

    def test_prometheus_text_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "prometheus_text" in data

    def test_prometheus_text_default_empty_string(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["prometheus_text"], str)

    def test_dtypes_key_present(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "dtypes" in data

    def test_dtypes_is_list(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert isinstance(data["dtypes"], list)

    def test_charts_has_memory_allocations(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "memory_allocations" in data["charts"]

    def test_charts_has_experiment_statuses(self):
        site = self._make_site()
        data = site.get_mlops_data()
        assert "experiment_statuses" in data["charts"]


# ════════════════════════════════════════════════════════════════════════════
# 17. MLOps v2 — SET_MLOPS_SERVICES EXTENDED PARAMS
# ════════════════════════════════════════════════════════════════════════════


class TestSetMlopsServicesV2:
    """set_mlops_services() v2 — new params for autoscaler, rbac, batch_queue, lru_cache."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite, AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mlops": True}})
        site = AdminSite.__new__(AdminSite)
        site.admin_config = cfg
        site._models = {}
        site._registry = {}
        site._admin_identities = {}
        site._initialized = True
        return site

    def test_set_mlops_services_accepts_autoscaler(self):
        from aquilia.admin.site import AdminSite

        sig = inspect.signature(AdminSite.set_mlops_services)
        assert "autoscaler" in sig.parameters

    def test_set_mlops_services_accepts_rbac_manager(self):
        from aquilia.admin.site import AdminSite

        sig = inspect.signature(AdminSite.set_mlops_services)
        assert "rbac_manager" in sig.parameters

    def test_set_mlops_services_accepts_batch_queue(self):
        from aquilia.admin.site import AdminSite

        sig = inspect.signature(AdminSite.set_mlops_services)
        assert "batch_queue" in sig.parameters

    def test_set_mlops_services_accepts_lru_cache(self):
        from aquilia.admin.site import AdminSite

        sig = inspect.signature(AdminSite.set_mlops_services)
        assert "lru_cache" in sig.parameters

    def test_set_mlops_services_stores_autoscaler(self):
        site = self._make_site()
        mock_as = MagicMock()
        site.set_mlops_services(autoscaler=mock_as)
        assert site._mlops_autoscaler is mock_as

    def test_set_mlops_services_stores_rbac_manager(self):
        site = self._make_site()
        mock_rbac = MagicMock()
        site.set_mlops_services(rbac_manager=mock_rbac)
        assert site._mlops_rbac is mock_rbac

    def test_set_mlops_services_stores_batch_queue(self):
        site = self._make_site()
        mock_bq = MagicMock()
        site.set_mlops_services(batch_queue=mock_bq)
        assert site._mlops_batch_queue is mock_bq

    def test_set_mlops_services_stores_lru_cache(self):
        site = self._make_site()
        mock_lru = MagicMock()
        site.set_mlops_services(lru_cache=mock_lru)
        assert site._mlops_lru_cache is mock_lru


# ════════════════════════════════════════════════════════════════════════════
# 18. MLOps v2 — TEMPLATE V2 SECTIONS
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsTemplateV2Sections:
    """mlops.html v2 template sections — autoscaler, RBAC, queue, cache, etc."""

    def _template_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia",
            "admin",
            "templates",
            "mlops.html",
        )

    def _read_template(self):
        with open(self._template_path(), encoding="utf-8") as f:
            return f.read()

    def test_template_has_autoscaler_section(self):
        content = self._read_template()
        assert "Autoscaler" in content

    def test_template_has_scaling_policy_heading(self):
        content = self._read_template()
        assert "Scaling Policy" in content

    def test_template_has_autoscaler_variable(self):
        content = self._read_template()
        assert "autoscaler" in content

    def test_template_has_rbac_section(self):
        content = self._read_template()
        assert "RBAC" in content or "Role-Based Access Control" in content

    def test_template_has_rbac_roles_table(self):
        content = self._read_template()
        assert "rbac.roles" in content

    def test_template_has_batch_queue_section(self):
        content = self._read_template()
        assert "Batch Queue" in content or "batch_queue" in content

    def test_template_has_lru_cache_section(self):
        content = self._read_template()
        assert "LRU" in content

    def test_template_has_per_model_metrics_section(self):
        content = self._read_template()
        assert "Per-Model Metrics" in content or "per_model_metrics" in content

    def test_template_has_prometheus_section(self):
        content = self._read_template()
        assert "Prometheus" in content

    def test_template_has_prometheus_copy_function(self):
        content = self._read_template()
        assert "copyPrometheusText" in content

    def test_template_has_experiment_statuses_chart(self):
        content = self._read_template()
        assert "chart-experiment-statuses" in content

    def test_template_has_memory_allocations_chart(self):
        content = self._read_template()
        assert "chart-memory-allocations" in content

    def test_template_has_dtypes_tab(self):
        content = self._read_template()
        assert "cap-dtypes" in content

    def test_template_has_permissions_tab(self):
        content = self._read_template()
        assert "cap-permissions" in content

    def test_template_has_drift_snippet(self):
        content = self._read_template()
        assert "snip-drift" in content

    def test_template_has_autoscaler_snippet(self):
        content = self._read_template()
        assert "snip-autoscaler" in content

    def test_template_has_rbac_snippet(self):
        content = self._read_template()
        assert "snip-rbac" in content

    def test_template_has_experiment_winner_column(self):
        content = self._read_template()
        assert "Winner" in content or "winner" in content

    def test_template_has_window_metrics(self):
        content = self._read_template()
        assert "Window" in content or "window" in content

    def test_template_has_last_decision_display(self):
        content = self._read_template()
        assert "Last Decision" in content or "last_decision" in content


# ════════════════════════════════════════════════════════════════════════════
# 19. MLOps v2 — RENDER PAGE WITH V2 DATA
# ════════════════════════════════════════════════════════════════════════════


class TestRenderMlopsPageV2:
    """render_mlops_page() produces HTML with v2 sections."""

    def _mlops_data_v2(self):
        return {
            "available": True,
            "models": [],
            "total_models": 0,
            "total_inferences": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "total_stream_requests": 0,
            "total_prompt_tokens": 0,
            "metrics": {},
            "latency": {},
            "throughput": {},
            "hot_models": [],
            "drift": {},
            "circuit_breaker": {},
            "rate_limiter": {},
            "memory": {},
            "plugins": [],
            "total_plugins": 0,
            "experiments": [],
            "total_experiments": 0,
            "active_experiments": 0,
            "lineage": {},
            "lineage_nodes": 0,
            "rollouts": [],
            "total_rollouts": 0,
            "active_rollouts": 0,
            "frameworks": ["pytorch"],
            "runtime_kinds": ["python"],
            "model_types": ["classifier"],
            "device_types": ["cpu"],
            "batching_strategies": ["none"],
            "rollout_strategies": ["canary"],
            "drift_methods": ["psi"],
            "quantize_presets": ["int8"],
            "export_targets": ["onnx"],
            "inference_modes": ["sync"],
            "autoscaler": {
                "policy": {
                    "min_replicas": 1,
                    "max_replicas": 10,
                    "target_concurrency": 50,
                    "target_latency_p95_ms": 200.0,
                    "cooldown_seconds": 60,
                },
                "current_replicas": 3,
                "window_stats": {
                    "window_rps": 15.0,
                    "avg_latency": 42.0,
                    "error_rate": 0.02,
                    "samples": 100,
                },
                "last_decision": {
                    "current": 3,
                    "desired": 4,
                    "reason": "high load",
                },
            },
            "rbac": {
                "roles": [
                    {"name": "ADMIN", "permissions": ["pack:read", "pack:write"], "user_count": 2},
                    {"name": "VIEWER", "permissions": ["pack:read"], "user_count": 5},
                ],
                "total_users": 7,
                "user_assignments": [
                    {"user": "alice", "role": "ADMIN"},
                ],
            },
            "batch_queue": {
                "size": 5,
                "capacity": 100,
                "enqueued": 50,
                "dequeued": 45,
                "dropped": 0,
                "pending_tokens": 128,
            },
            "lru_cache": {
                "capacity": 50,
                "size": 12,
                "hits": 200,
                "misses": 30,
                "hit_rate": 0.87,
            },
            "per_model_metrics": [
                {
                    "model": "sentiment",
                    "inferences": 100,
                    "errors": 2,
                    "avg_latency": 12.5,
                    "p95_latency": 45.0,
                    "tokens": 5000,
                    "error_rate": 0.02,
                },
            ],
            "prometheus_text": "# HELP aquilia_inference_total\naquillia_inference_total 100\n",
            "dtypes": ["float32", "float16", "int8"],
            "permissions": ["pack:read", "pack:write", "registry:admin"],
            "charts": {
                "model_states": {},
                "frameworks": {},
                "plugin_states": {},
                "experiment_statuses": {"active": 1},
                "rollout_phases": {},
                "memory_allocations": {"sentiment": 102.4},
            },
        }

    def test_render_v2_includes_autoscaler(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Autoscaler" in html
        assert "Scaling Policy" in html

    def test_render_v2_includes_rbac(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "RBAC" in html or "Role-Based Access Control" in html
        assert "ADMIN" in html
        assert "VIEWER" in html

    def test_render_v2_includes_batch_queue(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Batch Queue" in html

    def test_render_v2_includes_lru_cache(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "LRU" in html

    def test_render_v2_includes_per_model_metrics(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Per-Model Metrics" in html
        assert "sentiment" in html

    def test_render_v2_includes_prometheus(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Prometheus" in html
        assert "aquilia_inference_total" in html

    def test_render_v2_includes_dtypes_tab(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "DTypes" in html
        assert "float32" in html

    def test_render_v2_includes_permissions_tab(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Permissions" in html
        assert "pack:read" in html

    def test_render_v2_includes_new_chart_canvases(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "chart-experiment-statuses" in html
        assert "chart-memory-allocations" in html

    def test_render_v2_includes_new_snippet_tabs(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "snip-drift" in html
        assert "snip-autoscaler" in html
        assert "snip-rbac" in html

    def test_render_v2_includes_scaling_decision(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "scale_up" in html
        assert "high load" in html
        assert "4" in html  # desired replicas

    def test_render_v2_includes_window_stats(self):
        from aquilia.admin.templates import render_mlops_page

        html = render_mlops_page(mlops_data=self._mlops_data_v2())
        assert "Window" in html

    def test_render_v2_serializable(self):
        data = self._mlops_data_v2()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed["autoscaler"]["current_replicas"] == 3


# ════════════════════════════════════════════════════════════════════════════
# 20. MLOps v2 — SIDEBAR ENTRY
# ════════════════════════════════════════════════════════════════════════════


class TestMlopsSidebarEntry:
    """Sidebar has MLOps link under AI / ML section."""

    def _sidebar_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia",
            "admin",
            "templates",
            "partials",
            "sidebar_v2.html",
        )

    def test_sidebar_has_mlops_link(self):
        with open(self._sidebar_path(), encoding="utf-8") as f:
            content = f.read()
        assert "/admin/mlops/" in content or "mlops" in content

    def test_sidebar_has_ai_ml_section(self):
        with open(self._sidebar_path(), encoding="utf-8") as f:
            content = f.read()
        assert "AI / ML" in content

    def test_sidebar_mlops_icon(self):
        with open(self._sidebar_path(), encoding="utf-8") as f:
            content = f.read()
        assert "icon-cpu" in content

    def test_sidebar_mlops_active_page_check(self):
        with open(self._sidebar_path(), encoding="utf-8") as f:
            content = f.read()
        assert "mlops" in content
        assert "active_page" in content
