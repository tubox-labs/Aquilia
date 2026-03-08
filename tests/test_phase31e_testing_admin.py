"""
Phase 31e — Testing Admin Page.

Comprehensive tests for the new Testing Framework admin page:
- AdminConfig.modules includes "testing" (default False)
- AdminModules builder: enable_testing() / disable_testing()
- Integration.admin(enable_testing=True) flat syntax
- AdminConfig.is_module_enabled("testing")
- AdminConfig.from_dict() round-trip
- get_testing_data() structure & correctness
- render_testing_page() produces HTML with Chart.js
- Controller routes: /testing/, /testing/api/
- Sidebar link presence
- Template file exists and extends base.html
- Testing framework components importable
- Chart canvas IDs present in template output
- enable_all() includes testing
- Workspace to_dict round-trip
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest


# ════════════════════════════════════════════════════════════════════════════
# 1. ADMIN CONFIG — MODULE REGISTRATION
# ════════════════════════════════════════════════════════════════════════════


class TestAdminConfigTestingModule:
    """AdminConfig must include 'testing' in its modules dict."""

    def test_admin_config_has_testing_key(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        assert "testing" in cfg.modules

    def test_admin_config_testing_disabled_by_default(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        assert cfg.modules["testing"] is False

    def test_admin_config_is_module_enabled_testing_false(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        assert cfg.is_module_enabled("testing") is False

    def test_admin_config_is_module_enabled_testing_true(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig(modules={
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": False, "admin_users": True,
            "profile": True, "audit": False,
            "containers": False, "pods": False,
            "query_inspector": False, "tasks": False, "errors": False,
            "testing": True,
        })
        assert cfg.is_module_enabled("testing") is True

    def test_admin_config_from_dict_testing_default_false(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({})
        assert cfg.is_module_enabled("testing") is False

    def test_admin_config_from_dict_testing_enabled(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({"modules": {"testing": True}})
        assert cfg.is_module_enabled("testing") is True

    def test_admin_config_from_dict_testing_disabled_explicit(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({"modules": {"testing": False}})
        assert cfg.is_module_enabled("testing") is False

    def test_admin_config_from_dict_preserves_other_modules(self):
        """Enabling testing shouldn't break other modules."""
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({"modules": {"testing": True, "tasks": True}})
        assert cfg.is_module_enabled("testing") is True
        assert cfg.is_module_enabled("tasks") is True
        assert cfg.is_module_enabled("dashboard") is True
        assert cfg.is_module_enabled("monitoring") is False

    def test_admin_config_frozen(self):
        """AdminConfig is frozen dataclass — immutable."""
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        with pytest.raises(Exception):  # FrozenInstanceError
            cfg.modules = {}


# ════════════════════════════════════════════════════════════════════════════
# 2. ADMIN MODULES BUILDER
# ════════════════════════════════════════════════════════════════════════════


class TestAdminModulesTestingBuilder:
    """AdminModules builder must have enable/disable_testing methods."""

    def test_enable_testing(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_testing()
        d = mods.to_dict()
        assert d["testing"] is True

    def test_disable_testing(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_testing().disable_testing()
        d = mods.to_dict()
        assert d["testing"] is False

    def test_testing_disabled_by_default(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert d["testing"] is False

    def test_enable_testing_returns_self(self):
        """Fluent API — enable_testing returns self for chaining."""
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        result = mods.enable_testing()
        assert result is mods

    def test_disable_testing_returns_self(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        result = mods.disable_testing()
        assert result is mods

    def test_chaining_with_other_modules(self):
        from aquilia.config_builders import Integration
        mods = (
            Integration.AdminModules()
            .enable_tasks()
            .enable_errors()
            .enable_testing()
        )
        d = mods.to_dict()
        assert d["tasks"] is True
        assert d["errors"] is True
        assert d["testing"] is True

    def test_enable_all_includes_testing(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_all()
        d = mods.to_dict()
        assert d["testing"] is True

    def test_disable_all_includes_testing(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_all().disable_all()
        d = mods.to_dict()
        assert d["testing"] is False

    def test_testing_key_in_to_dict(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert "testing" in d

    def test_repr_includes_testing_when_enabled(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_testing()
        r = repr(mods)
        assert "testing" in r

    def test_repr_excludes_testing_when_disabled(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        r = repr(mods)
        assert "testing" not in r

    def test_slots_contains_testing(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        assert "_testing" in mods.__slots__


# ════════════════════════════════════════════════════════════════════════════
# 3. INTEGRATION.ADMIN() FLAT SYNTAX
# ════════════════════════════════════════════════════════════════════════════


class TestIntegrationAdminFlat:
    """Integration.admin(enable_testing=True) flat param."""

    def test_flat_enable_testing(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(enable_testing=True)
        assert cfg["modules"]["testing"] is True

    def test_flat_enable_testing_default_false(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin()
        assert cfg["modules"]["testing"] is False

    def test_flat_enable_testing_with_other_modules(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            enable_testing=True,
            enable_tasks=True,
            enable_errors=True,
        )
        assert cfg["modules"]["testing"] is True
        assert cfg["modules"]["tasks"] is True
        assert cfg["modules"]["errors"] is True

    def test_flat_enable_testing_preserved_in_admin_config(self):
        """Round-trip: flat syntax → AdminConfig."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig
        raw = Integration.admin(enable_testing=True)
        cfg = AdminConfig.from_dict(raw)
        assert cfg.is_module_enabled("testing") is True


# ════════════════════════════════════════════════════════════════════════════
# 4. WORKSPACE TO_DICT ROUND-TRIP
# ════════════════════════════════════════════════════════════════════════════


class TestWorkspaceTestingRoundTrip:
    """Workspace serialisation includes testing module."""

    def test_workspace_admin_testing_enabled(self):
        from aquilia.config_builders import Workspace, Integration
        ws = Workspace("test").integrate(Integration.admin(enable_testing=True))
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["testing"] is True

    def test_workspace_admin_testing_disabled(self):
        from aquilia.config_builders import Workspace, Integration
        ws = Workspace("test").integrate(Integration.admin())
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["testing"] is False

    def test_workspace_admin_modules_builder_testing(self):
        from aquilia.config_builders import Workspace, Integration
        mods = Integration.AdminModules().enable_testing()
        ws = Workspace("test").integrate(
            Integration.admin(modules=mods)
        )
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["testing"] is True


# ════════════════════════════════════════════════════════════════════════════
# 5. GET_TESTING_DATA() — DATA STRUCTURE
# ════════════════════════════════════════════════════════════════════════════


class TestGetTestingData:
    """AdminSite.get_testing_data() returns comprehensive testing info."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_returns_dict(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert isinstance(data, dict)

    def test_has_available_key(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "available" in data

    def test_available_is_true(self):
        """Framework is installed — available should be True."""
        site = self._make_site()
        data = site.get_testing_data()
        assert data["available"] is True

    def test_has_framework_version(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "framework_version" in data
        assert data["framework_version"] == "1.0.0"

    def test_has_test_classes(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "test_classes" in data
        assert isinstance(data["test_classes"], list)
        assert len(data["test_classes"]) >= 4

    def test_test_classes_contain_expected_names(self):
        site = self._make_site()
        data = site.get_testing_data()
        names = [tc["name"] for tc in data["test_classes"]]
        assert "SimpleTestCase" in names
        assert "AquiliaTestCase" in names
        assert "TransactionTestCase" in names
        assert "LiveServerTestCase" in names

    def test_test_class_has_description(self):
        site = self._make_site()
        data = site.get_testing_data()
        for tc in data["test_classes"]:
            assert "description" in tc
            assert len(tc["description"]) > 0

    def test_test_class_has_category(self):
        site = self._make_site()
        data = site.get_testing_data()
        categories = [tc["category"] for tc in data["test_classes"]]
        assert "unit" in categories
        assert "integration" in categories
        assert "database" in categories
        assert "e2e" in categories

    def test_test_class_has_features(self):
        site = self._make_site()
        data = site.get_testing_data()
        for tc in data["test_classes"]:
            assert "features" in tc
            assert isinstance(tc["features"], list)
            assert len(tc["features"]) > 0

    def test_has_client_info(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "client" in data
        assert "http" in data["client"]
        assert "websocket" in data["client"]

    def test_client_http_has_methods(self):
        site = self._make_site()
        data = site.get_testing_data()
        http = data["client"]["http"]
        assert "methods" in http
        for m in ["get", "post", "put", "patch", "delete"]:
            assert m in http["methods"]

    def test_client_http_has_features(self):
        site = self._make_site()
        data = site.get_testing_data()
        http = data["client"]["http"]
        assert "features" in http
        assert "in_process_asgi" in http["features"]

    def test_has_assertions(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "assertions" in data
        assert isinstance(data["assertions"], list)
        assert len(data["assertions"]) > 0

    def test_total_assertions_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_assertions"] > 0

    def test_assertion_categories_have_http_status(self):
        site = self._make_site()
        data = site.get_testing_data()
        cats = [a["category"] for a in data["assertions"]]
        assert "HTTP Status" in cats

    def test_assertion_each_has_methods_and_count(self):
        site = self._make_site()
        data = site.get_testing_data()
        for a in data["assertions"]:
            assert "category" in a
            assert "methods" in a
            assert "count" in a
            assert a["count"] == len(a["methods"])

    def test_has_fixtures(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "fixtures" in data
        assert isinstance(data["fixtures"], list)

    def test_total_fixtures_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_fixtures"] > 0

    def test_fixture_entries_have_name(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["fixtures"]:
            assert "name" in f
            assert isinstance(f["name"], str)

    def test_has_mock_infra(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "mock_infra" in data
        assert isinstance(data["mock_infra"], list)
        assert len(data["mock_infra"]) > 0

    def test_total_mocks_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_mocks"] > 0

    def test_mock_infra_has_expected_components(self):
        site = self._make_site()
        data = site.get_testing_data()
        names = [m["name"] for m in data["mock_infra"]]
        assert "MockFaultEngine" in names
        assert "MockCacheBackend" in names
        assert "TestContainer" in names

    def test_mock_infra_entries_have_features(self):
        site = self._make_site()
        data = site.get_testing_data()
        for m in data["mock_infra"]:
            assert "name" in m
            assert "module" in m
            assert "description" in m
            assert "features" in m
            assert isinstance(m["features"], list)

    def test_has_utilities(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "utilities" in data
        assert isinstance(data["utilities"], list)

    def test_total_utilities_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_utilities"] > 0

    def test_utility_names(self):
        site = self._make_site()
        data = site.get_testing_data()
        names = [u["name"] for u in data["utilities"]]
        assert "make_test_scope" in names
        assert "make_test_request" in names

    def test_has_test_files(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "test_files" in data
        assert isinstance(data["test_files"], list)

    def test_total_test_files_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_test_files"] > 0

    def test_test_file_entries_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "name" in f
            assert "lines" in f
            assert "test_count" in f
            assert "class_count" in f
            assert f["name"].startswith("test_")
            assert f["name"].endswith(".py")

    def test_has_component_coverage(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "component_coverage" in data
        assert isinstance(data["component_coverage"], list)
        assert len(data["component_coverage"]) > 0

    def test_component_coverage_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        for c in data["component_coverage"]:
            assert "name" in c
            assert "module" in c
            assert "status" in c

    def test_total_components_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["total_components"] > 0

    def test_covered_components_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["covered_components"] > 0

    def test_has_summary(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "summary" in data
        assert isinstance(data["summary"], dict)

    def test_summary_keys(self):
        site = self._make_site()
        data = site.get_testing_data()
        summary = data["summary"]
        expected_keys = [
            "total_test_cases", "total_assertions", "total_fixtures",
            "total_mocks", "total_utilities", "total_test_files",
            "total_test_functions", "total_test_classes", "total_lines",
            "total_components", "covered_components",
        ]
        for k in expected_keys:
            assert k in summary, f"Missing key: {k}"

    def test_summary_total_test_functions_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["total_test_functions"] > 0

    def test_summary_total_lines_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["total_lines"] > 0

    def test_has_charts(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "charts" in data
        assert isinstance(data["charts"], dict)

    def test_charts_keys(self):
        site = self._make_site()
        data = site.get_testing_data()
        charts = data["charts"]
        expected_chart_keys = [
            "test_distribution", "test_categories",
            "assertion_categories", "mock_infrastructure",
            "lines_of_code", "component_coverage",
            "async_sync", "test_density",
            "imports_usage", "assertions_per_file",
        ]
        for k in expected_chart_keys:
            assert k in charts, f"Missing chart key: {k}"

    def test_chart_data_has_labels_and_values(self):
        site = self._make_site()
        data = site.get_testing_data()
        for key, chart in data["charts"].items():
            assert "labels" in chart, f"Chart '{key}' missing labels"
            assert "values" in chart, f"Chart '{key}' missing values"
            assert isinstance(chart["labels"], list)
            assert isinstance(chart["values"], list)

    def test_chart_test_distribution_has_files(self):
        site = self._make_site()
        data = site.get_testing_data()
        dist = data["charts"]["test_distribution"]
        assert len(dist["labels"]) > 0
        assert len(dist["values"]) > 0
        assert len(dist["labels"]) == len(dist["values"])

    def test_chart_component_coverage_all_100(self):
        """All components should be 'covered' → all values 100."""
        site = self._make_site()
        data = site.get_testing_data()
        cov = data["charts"]["component_coverage"]
        for v in cov["values"]:
            assert v == 100

    def test_chart_assertion_categories_match_assertions(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart_labels = data["charts"]["assertion_categories"]["labels"]
        assertion_cats = [a["category"] for a in data["assertions"]]
        assert chart_labels == assertion_cats

    def test_chart_mock_infra_match_mock_list(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart_labels = data["charts"]["mock_infrastructure"]["labels"]
        mock_names = [m["name"] for m in data["mock_infra"]]
        assert chart_labels == mock_names


# ════════════════════════════════════════════════════════════════════════════
# 6. RENDER_TESTING_PAGE() — HTML OUTPUT
# ════════════════════════════════════════════════════════════════════════════


class TestRenderTestingPage:
    """render_testing_page() produces correct HTML."""

    def _testing_data(self, **overrides):
        """Build minimal testing_data dict for render calls."""
        base = {
            "available": True,
            "framework_version": "1.0.0",
            "test_classes": [
                {"name": "AquiliaTestCase", "description": "Full test", "base": "IsolatedAsyncioTestCase",
                 "features": ["auto_server"], "category": "integration"},
            ],
            "client": {
                "http": {"name": "TestClient", "methods": ["get", "post"], "features": ["in_process_asgi"]},
                "websocket": {"name": "WebSocketTestClient", "features": ["connect"]},
            },
            "assertions": [
                {"category": "HTTP Status", "methods": ["assert_status_200"], "count": 1},
            ],
            "total_assertions": 1,
            "fixtures": [{"name": "test_client", "async": True}],
            "total_fixtures": 1,
            "mock_infra": [
                {"name": "MockFaultEngine", "module": "faults", "description": "Capture faults",
                 "features": ["emit_capture"]},
            ],
            "total_mocks": 1,
            "utilities": [{"name": "make_test_scope", "description": "Build ASGI scope"}],
            "total_utilities": 1,
            "test_files": [
                {"name": "test_example.py", "directory": "tests", "path": "/test_example.py",
                 "lines": 100, "test_count": 10, "class_count": 2},
            ],
            "total_test_files": 1,
            "component_coverage": [
                {"name": "Server", "module": "server", "status": "covered"},
            ],
            "total_components": 1,
            "covered_components": 1,
            "summary": {
                "total_test_cases": 4, "total_assertions": 1, "total_fixtures": 1,
                "total_mocks": 1, "total_utilities": 1, "total_test_files": 1,
                "total_test_functions": 10, "total_test_classes": 2, "total_lines": 100,
                "total_components": 1, "covered_components": 1,
            },
            "charts": {
                "test_distribution": {"labels": ["example"], "values": [10]},
                "test_categories": {"labels": ["Unit", "Integration"], "values": [3, 7]},
                "assertion_categories": {"labels": ["HTTP Status"], "values": [1]},
                "mock_infrastructure": {"labels": ["MockFaultEngine"], "values": [1]},
                "lines_of_code": {"labels": ["example"], "values": [100]},
                "component_coverage": {"labels": ["Server"], "values": [100]},
            },
        }
        base.update(overrides)
        return base

    def test_render_testing_page_returns_string(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert isinstance(html, str)

    def test_render_testing_page_contains_html(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "<html" in html or "<!DOCTYPE" in html or "Testing" in html

    def test_render_testing_page_includes_chart_js_cdn(self):
        """Output includes Chart.js CDN script."""
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "chart.js" in html.lower() or "Chart" in html

    def test_render_testing_page_includes_title(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "Testing Framework" in html

    def test_render_testing_page_includes_test_class_names(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "AquiliaTestCase" in html

    def test_render_testing_page_includes_framework_version(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "1.0.0" in html

    def test_render_testing_page_chart_canvas_elements(self):
        """All expected chart canvas IDs present."""
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "chartTestDistribution" in html
        assert "chartCoverage" in html
        assert "chartAssertions" in html
        assert "chartMockInfra" in html
        assert "chartLOC" in html

    def test_render_testing_page_active_page_is_testing(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        # The active_page="testing" is passed to the template
        assert "testing" in html.lower()

    def test_render_testing_page_shows_available_status(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data(available=True))
        assert "Available" in html

    def test_render_testing_page_shows_mock_infra_name(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "MockFaultEngine" in html

    def test_render_testing_page_shows_fixture_name(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "test_client" in html

    def test_render_testing_page_shows_utility_name(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "make_test_scope" in html

    def test_render_testing_page_shows_test_file(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "test_example.py" in html

    def test_render_testing_page_shows_assertion_category(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "HTTP Status" in html

    def test_render_testing_page_shows_component_coverage(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "Server" in html

    def test_render_testing_page_identity_name(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(
            testing_data=self._testing_data(),
            identity_name="TestAdmin",
        )
        assert "TestAdmin" in html

    def test_render_testing_page_custom_url_prefix(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(
            testing_data=self._testing_data(),
            url_prefix="/custom-admin",
        )
        # url_prefix is passed to template context
        assert "/custom-admin" in html or "custom-admin" in html


# ════════════════════════════════════════════════════════════════════════════
# 7. CONTROLLER ROUTES
# ════════════════════════════════════════════════════════════════════════════


class TestAdminControllerTestingRoutes:
    """AdminController has testing routes compiled correctly."""

    def test_controller_has_testing_view_method(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "testing_view")

    def test_controller_has_testing_api_method(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "testing_api")

    def test_testing_view_is_async(self):
        from aquilia.admin.controller import AdminController
        assert inspect.iscoroutinefunction(AdminController.testing_view)

    def test_testing_api_is_async(self):
        from aquilia.admin.controller import AdminController
        assert inspect.iscoroutinefunction(AdminController.testing_api)

    def test_controller_imports_render_testing_page(self):
        """render_testing_page is imported in controller module."""
        import aquilia.admin.controller as ctrl_mod
        assert hasattr(ctrl_mod, "render_testing_page")

    def test_testing_view_route_metadata(self):
        """testing_view should have route metadata for /testing/."""
        from aquilia.admin.controller import AdminController
        method = AdminController.testing_view
        # Routes are decorated with @GET("/testing/") → has __route_path__ or similar
        route_attrs = [a for a in dir(method) if "route" in a.lower() or "path" in a.lower()]
        # Also check via source inspection
        source = inspect.getsource(method)
        assert "testing" in source

    def test_testing_api_route_metadata(self):
        from aquilia.admin.controller import AdminController
        method = AdminController.testing_api
        source = inspect.getsource(method)
        assert "testing" in source
        assert "json" in source.lower() or "JSON" in source

    def test_testing_view_checks_identity(self):
        """testing_view must call _require_identity for auth."""
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_view)
        assert "_require_identity" in source

    def test_testing_api_checks_identity(self):
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_api)
        assert "_require_identity" in source

    def test_testing_view_checks_module_enabled(self):
        """testing_view must check is_module_enabled('testing')."""
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_view)
        assert "is_module_enabled" in source
        assert '"testing"' in source or "'testing'" in source

    def test_testing_api_checks_module_enabled(self):
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_api)
        assert "is_module_enabled" in source

    def test_testing_view_calls_get_testing_data(self):
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_view)
        assert "get_testing_data" in source

    def test_testing_api_calls_get_testing_data(self):
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_api)
        assert "get_testing_data" in source

    def test_testing_view_calls_render_testing_page(self):
        from aquilia.admin.controller import AdminController
        source = inspect.getsource(AdminController.testing_view)
        assert "render_testing_page" in source


# ════════════════════════════════════════════════════════════════════════════
# 8. SIDEBAR LINK
# ════════════════════════════════════════════════════════════════════════════


class TestSidebarTestingLink:
    """Sidebar HTML includes the testing link."""

    def test_sidebar_template_exists(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        assert os.path.isfile(sidebar_path)

    def test_sidebar_contains_testing_link(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        with open(sidebar_path) as f:
            content = f.read()
        assert "/testing/" in content

    def test_sidebar_testing_label(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        with open(sidebar_path) as f:
            content = f.read()
        assert "Testing" in content

    def test_sidebar_testing_icon(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        with open(sidebar_path) as f:
            content = f.read()
        assert "icon-check-circle" in content

    def test_sidebar_testing_active_page_check(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        with open(sidebar_path) as f:
            content = f.read()
        assert "active_page == 'testing'" in content

    def test_sidebar_testing_data_label(self):
        sidebar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "partials", "sidebar_v2.html",
        )
        with open(sidebar_path) as f:
            content = f.read()
        # Should have searchable data-sidebar-label
        assert "data-sidebar-label" in content
        # Find the testing link's data-sidebar-label
        import re
        labels = re.findall(r'data-sidebar-label="([^"]*testing[^"]*)"', content)
        assert len(labels) > 0


# ════════════════════════════════════════════════════════════════════════════
# 9. TEMPLATE FILE
# ════════════════════════════════════════════════════════════════════════════


class TestTestingTemplateFile:
    """testing.html template file structure and content."""

    def _template_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "testing.html",
        )

    def test_template_file_exists(self):
        assert os.path.isfile(self._template_path())

    def test_template_extends_base(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert '{% extends "base.html" %}' in content

    def test_template_has_title_block(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "{% block title %}" in content
        assert "Testing Framework" in content

    def test_template_has_content_block(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "{% block content %}" in content

    def test_template_includes_chart_js_cdn(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "chart.js" in content.lower()
        assert "cdn.jsdelivr.net" in content

    def test_template_has_chart_canvas_elements(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "chartTestDistribution" in content
        assert "chartCoverage" in content
        assert "chartAssertions" in content
        assert "chartMockInfra" in content
        assert "chartLOC" in content

    def test_template_has_status_bar(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "Available" in content

    def test_template_has_icon(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "icon-check-circle" in content

    def test_template_uses_framework_version(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "framework_version" in content

    def test_template_iterates_test_classes(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "test_classes" in content

    def test_template_iterates_mock_infra(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "mock_infra" in content

    def test_template_iterates_fixtures(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "fixtures" in content

    def test_template_iterates_test_files(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "test_files" in content

    def test_template_has_javascript_section(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "<script" in content or "{% block extra_js %}" in content

    def test_template_creates_chart_instances(self):
        with open(self._template_path()) as f:
            content = f.read()
        assert "new Chart(" in content


# ════════════════════════════════════════════════════════════════════════════
# 10. TESTING FRAMEWORK IMPORTS
# ════════════════════════════════════════════════════════════════════════════


class TestTestingFrameworkImports:
    """Verify all testing framework components are importable."""

    def test_import_aquilia_test_case(self):
        from aquilia.testing.cases import AquiliaTestCase
        assert AquiliaTestCase is not None

    def test_import_transaction_test_case(self):
        from aquilia.testing.cases import TransactionTestCase
        assert TransactionTestCase is not None

    def test_import_live_server_test_case(self):
        from aquilia.testing.cases import LiveServerTestCase
        assert LiveServerTestCase is not None

    def test_import_simple_test_case(self):
        from aquilia.testing.cases import SimpleTestCase
        assert SimpleTestCase is not None

    def test_import_test_client(self):
        from aquilia.testing.client import TestClient
        assert TestClient is not None

    def test_import_websocket_test_client(self):
        from aquilia.testing.client import WebSocketTestClient
        assert WebSocketTestClient is not None

    def test_import_aquilia_assertions(self):
        from aquilia.testing.assertions import AquiliaAssertions
        assert AquiliaAssertions is not None

    def test_import_mock_fault_engine(self):
        from aquilia.testing.faults import MockFaultEngine
        assert MockFaultEngine is not None

    def test_import_mock_effect_registry(self):
        from aquilia.testing.effects import MockEffectRegistry
        assert MockEffectRegistry is not None

    def test_import_mock_cache_backend(self):
        from aquilia.testing.cache import MockCacheBackend
        assert MockCacheBackend is not None

    def test_import_test_container(self):
        from aquilia.testing.di import TestContainer
        assert TestContainer is not None

    def test_import_mail_test_mixin(self):
        from aquilia.testing.mail import MailTestMixin
        assert MailTestMixin is not None

    def test_import_test_identity_factory(self):
        from aquilia.testing.auth import TestIdentityFactory
        assert TestIdentityFactory is not None

    def test_import_identity_builder(self):
        from aquilia.testing.auth import IdentityBuilder
        assert IdentityBuilder is not None

    def test_import_test_config(self):
        from aquilia.testing.config import TestConfig
        assert TestConfig is not None

    def test_import_test_server(self):
        from aquilia.testing.server import TestServer
        assert TestServer is not None

    def test_import_make_test_scope(self):
        from aquilia.testing.utils import make_test_scope
        assert callable(make_test_scope)

    def test_import_make_test_request(self):
        from aquilia.testing.utils import make_test_request
        assert callable(make_test_request)

    def test_import_make_upload_file(self):
        from aquilia.testing.utils import make_upload_file
        assert callable(make_upload_file)


# ════════════════════════════════════════════════════════════════════════════
# 11. TEMPLATES.PY — FUNCTION SIGNATURE
# ════════════════════════════════════════════════════════════════════════════


class TestRenderTestingPageSignature:
    """render_testing_page function exists and has correct signature."""

    def test_function_exists(self):
        from aquilia.admin.templates import render_testing_page
        assert callable(render_testing_page)

    def test_first_param_is_testing_data(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        params = list(sig.parameters.keys())
        assert params[0] == "testing_data"

    def test_has_app_list_param(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert "app_list" in sig.parameters

    def test_has_identity_name_param(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert "identity_name" in sig.parameters

    def test_has_site_title_param(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert "site_title" in sig.parameters

    def test_has_url_prefix_param(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert "url_prefix" in sig.parameters

    def test_default_identity_name(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert sig.parameters["identity_name"].default == "Admin"

    def test_default_url_prefix(self):
        from aquilia.admin.templates import render_testing_page
        sig = inspect.signature(render_testing_page)
        assert sig.parameters["url_prefix"].default == "/admin"


# ════════════════════════════════════════════════════════════════════════════
# 12. GET_TESTING_DATA — EDGE CASES
# ════════════════════════════════════════════════════════════════════════════


class TestGetTestingDataEdgeCases:
    """Edge cases and robustness of get_testing_data."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_data_is_json_serializable(self):
        """Entire testing data structure must be JSON-serializable."""
        site = self._make_site()
        data = site.get_testing_data()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert isinstance(deserialized, dict)

    def test_chart_labels_and_values_same_length(self):
        site = self._make_site()
        data = site.get_testing_data()
        for key, chart in data["charts"].items():
            assert len(chart["labels"]) == len(chart["values"]), \
                f"Chart '{key}': labels({len(chart['labels'])}) != values({len(chart['values'])})"

    def test_summary_consistency(self):
        """Summary totals should match actual data lengths."""
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["total_test_files"] == len(data["test_files"])
        assert data["summary"]["total_mocks"] == len(data["mock_infra"])
        assert data["summary"]["total_components"] == len(data["component_coverage"])

    def test_test_files_have_positive_lines(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert f["lines"] > 0, f"File {f['name']} has 0 lines"

    def test_mock_infra_feature_counts_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        for m in data["mock_infra"]:
            assert len(m["features"]) > 0, f"Mock {m['name']} has no features"

    def test_multiple_calls_idempotent(self):
        """Calling get_testing_data() twice gives same structure."""
        site = self._make_site()
        d1 = site.get_testing_data()
        d2 = site.get_testing_data()
        assert d1.keys() == d2.keys()
        assert d1["summary"] == d2["summary"]
        assert len(d1["test_files"]) == len(d2["test_files"])

    def test_component_coverage_all_covered(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["covered_components"] == data["total_components"]

    def test_no_duplicate_test_files(self):
        site = self._make_site()
        data = site.get_testing_data()
        names = [f["name"] for f in data["test_files"]]
        assert len(names) == len(set(names)), "Duplicate test file names found"

    def test_no_duplicate_mock_infra_names(self):
        site = self._make_site()
        data = site.get_testing_data()
        names = [m["name"] for m in data["mock_infra"]]
        assert len(names) == len(set(names)), "Duplicate mock names found"


# ════════════════════════════════════════════════════════════════════════════
# 13. INTEGRATION SMOKE TEST
# ════════════════════════════════════════════════════════════════════════════


class TestTestingAdminIntegration:
    """End-to-end integration: config → data → render."""

    def test_full_pipeline(self):
        """Config enables testing → data gathered → HTML rendered."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig, AdminSite
        from aquilia.admin.templates import render_testing_page

        # 1. Config
        raw = Integration.admin(enable_testing=True)
        cfg = AdminConfig.from_dict(raw)
        assert cfg.is_module_enabled("testing")

        # 2. Data
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = cfg
        data = site.get_testing_data()
        assert data["available"] is True

        # 3. Render
        html = render_testing_page(testing_data=data)
        assert "Testing Framework" in html
        assert "chartTestDistribution" in html

    def test_disabled_module_config(self):
        """When testing module is disabled, config reports False."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig

        raw = Integration.admin()
        cfg = AdminConfig.from_dict(raw)
        assert not cfg.is_module_enabled("testing")

    def test_workspace_full_config(self):
        """Full workspace config with testing enabled round-trips."""
        from aquilia.config_builders import Workspace, Integration

        ws = (
            Workspace("myapp")
            .integrate(Integration.admin(
                enable_testing=True,
                enable_tasks=True,
                enable_errors=True,
                enable_query_inspector=True,
            ))
        )
        d = ws.to_dict()
        mods = d["integrations"]["admin"]["modules"]
        assert mods["testing"] is True
        assert mods["tasks"] is True
        assert mods["errors"] is True
        assert mods["query_inspector"] is True

    def test_admin_modules_builder_all_devtools(self):
        """AdminModules builder enables all devtools including testing."""
        from aquilia.config_builders import Integration

        mods = (
            Integration.AdminModules()
            .enable_query_inspector()
            .enable_tasks()
            .enable_errors()
            .enable_testing()
        )
        d = mods.to_dict()
        assert d["query_inspector"] is True
        assert d["tasks"] is True
        assert d["errors"] is True
        assert d["testing"] is True

    def test_render_with_real_data(self):
        """Render testing page with real data from get_testing_data."""
        from aquilia.admin.site import AdminSite
        from aquilia.admin.templates import render_testing_page

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Aquilia Admin"
        site._initialised = True
        site._admin_config = None

        data = site.get_testing_data()
        html = render_testing_page(testing_data=data)

        # Should contain real test file names from the project
        assert "test_" in html
        # Should have chart instances
        assert "Chart" in html or "chart" in html.lower()
        # Should be non-trivial HTML
        assert len(html) > 1000


# ════════════════════════════════════════════════════════════════════════════
# 14. PHASE 31f — ENHANCED TESTING DASHBOARD
# Server route wiring · Disabled page · Enhanced metrics · New charts
# Search/filter · Code snippets · Count-up animations · Imports heatmap
# ════════════════════════════════════════════════════════════════════════════


class TestPhase31fServerRouteWiring:
    """Testing routes are registered in _wire_admin_integration (server.py)."""

    def test_server_module_has_wire_admin_integration(self):
        import aquilia.server as srv_mod
        src = inspect.getsource(srv_mod)
        assert "_wire_admin_integration" in src

    def test_server_registers_testing_view_route(self):
        import aquilia.server as srv_mod
        src = inspect.getsource(srv_mod)
        assert "testing_view" in src
        assert "/testing/" in src

    def test_server_registers_testing_api_route(self):
        import aquilia.server as srv_mod
        src = inspect.getsource(srv_mod)
        assert "testing_api" in src
        assert "/testing/api/" in src

    def test_testing_routes_use_get_method(self):
        import aquilia.server as srv_mod
        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "testing_view" in line and "admin_routes" in line:
                assert '"GET"' in line or "'GET'" in line
            if "testing_api" in line and "admin_routes" in line:
                assert '"GET"' in line or "'GET'" in line

    def test_testing_routes_after_errors_routes(self):
        """Testing routes should be placed after errors routes."""
        import aquilia.server as srv_mod
        src = inspect.getsource(srv_mod)
        errors_pos = src.find("errors_view")
        testing_pos = src.find("testing_view")
        assert errors_pos > 0
        assert testing_pos > 0
        assert testing_pos > errors_pos


class TestPhase31fDisabledPage:
    """Testing Framework appears in _config_hints for disabled page."""

    def test_config_hints_has_testing_framework(self):
        from aquilia.admin.controller import AdminController
        src = inspect.getsource(AdminController)
        assert '"Testing Framework"' in src or "'Testing Framework'" in src

    def test_config_hints_testing_builder_hint(self):
        from aquilia.admin.controller import AdminController
        src = inspect.getsource(AdminController)
        assert "enable_testing()" in src

    def test_config_hints_testing_flat_hint(self):
        from aquilia.admin.controller import AdminController
        src = inspect.getsource(AdminController)
        assert "enable_testing=True" in src

    def test_config_hints_testing_icon(self):
        from aquilia.admin.controller import AdminController
        src = inspect.getsource(AdminController)
        assert "check-circle" in src

    def test_testing_view_returns_disabled_page_when_off(self):
        """testing_view calls _module_disabled_response when testing not enabled."""
        from aquilia.admin.controller import AdminController
        src = inspect.getsource(AdminController.testing_view)
        assert "_module_disabled_response" in src
        assert '"Testing Framework"' in src or "'Testing Framework'" in src


class TestPhase31fEnhancedSummary:
    """Summary includes Phase 31f enhanced metrics."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_summary_has_total_assert_stmts(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "total_assert_stmts" in data["summary"]
        assert isinstance(data["summary"]["total_assert_stmts"], int)

    def test_summary_total_assert_stmts_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["total_assert_stmts"] > 0

    def test_summary_has_avg_tests_per_file(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "avg_tests_per_file" in data["summary"]
        assert isinstance(data["summary"]["avg_tests_per_file"], (int, float))

    def test_summary_avg_tests_per_file_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["avg_tests_per_file"] > 0

    def test_summary_has_avg_loc_per_test(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "avg_loc_per_test" in data["summary"]
        assert isinstance(data["summary"]["avg_loc_per_test"], (int, float))

    def test_summary_avg_loc_per_test_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert data["summary"]["avg_loc_per_test"] > 0

    def test_summary_has_avg_density(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "avg_density" in data["summary"]
        assert isinstance(data["summary"]["avg_density"], (int, float))

    def test_summary_has_total_async_tests(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "total_async_tests" in data["summary"]
        assert isinstance(data["summary"]["total_async_tests"], int)

    def test_summary_has_total_sync_tests(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "total_sync_tests" in data["summary"]
        assert isinstance(data["summary"]["total_sync_tests"], int)

    def test_summary_async_plus_sync_equals_total(self):
        site = self._make_site()
        data = site.get_testing_data()
        s = data["summary"]
        assert s["total_async_tests"] + s["total_sync_tests"] == s["total_test_functions"]

    def test_summary_has_category_breakdown(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "category_breakdown" in data["summary"]
        assert isinstance(data["summary"]["category_breakdown"], dict)

    def test_summary_category_breakdown_has_expected_keys(self):
        site = self._make_site()
        data = site.get_testing_data()
        cb = data["summary"]["category_breakdown"]
        for key in ("unit", "integration", "database", "e2e", "other"):
            assert key in cb, f"Missing category: {key}"

    def test_summary_category_breakdown_values_non_negative(self):
        site = self._make_site()
        data = site.get_testing_data()
        for k, v in data["summary"]["category_breakdown"].items():
            assert v >= 0, f"Category {k} has negative value: {v}"

    def test_summary_category_breakdown_sum_equals_files(self):
        site = self._make_site()
        data = site.get_testing_data()
        total_cats = sum(data["summary"]["category_breakdown"].values())
        assert total_cats == len(data["test_files"])

    def test_summary_has_imports_usage(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "imports_usage" in data["summary"]
        assert isinstance(data["summary"]["imports_usage"], dict)


class TestPhase31fEnhancedTestFileFields:
    """Test file entries include Phase 31f enhanced fields."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_test_file_has_category(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "category" in f, f"File {f['name']} missing category"
            assert f["category"] in ("unit", "integration", "database", "e2e", "other")

    def test_test_file_has_assert_count(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "assert_count" in f, f"File {f['name']} missing assert_count"
            assert isinstance(f["assert_count"], int)
            assert f["assert_count"] >= 0

    def test_test_file_has_density(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "density" in f, f"File {f['name']} missing density"
            assert isinstance(f["density"], (int, float))
            assert f["density"] >= 0

    def test_test_file_has_async_tests(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "async_tests" in f, f"File {f['name']} missing async_tests"
            assert isinstance(f["async_tests"], int)

    def test_test_file_has_sync_tests(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "sync_tests" in f, f"File {f['name']} missing sync_tests"
            assert isinstance(f["sync_tests"], int)

    def test_test_file_async_plus_sync_equals_count(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert f["async_tests"] + f["sync_tests"] == f["test_count"], \
                f"File {f['name']}: async({f['async_tests']}) + sync({f['sync_tests']}) != count({f['test_count']})"

    def test_test_file_has_imports(self):
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            assert "imports" in f, f"File {f['name']} missing imports"
            assert isinstance(f["imports"], list)

    def test_density_calculation_correct(self):
        """Density = (test_count / lines) * 100."""
        site = self._make_site()
        data = site.get_testing_data()
        for f in data["test_files"]:
            if f["lines"] > 0:
                expected = round((f["test_count"] / f["lines"]) * 100, 2)
                assert abs(f["density"] - expected) < 0.1, \
                    f"File {f['name']}: density {f['density']} != expected {expected}"


class TestPhase31fNewChartKeys:
    """Charts dict includes Phase 31f new chart types."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_charts_has_async_sync(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "async_sync" in data["charts"]

    def test_charts_async_sync_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["async_sync"]
        assert "labels" in chart
        assert "values" in chart
        assert chart["labels"] == ["Async", "Sync"]
        assert len(chart["values"]) == 2

    def test_charts_async_sync_values_match_summary(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["async_sync"]
        assert chart["values"][0] == data["summary"]["total_async_tests"]
        assert chart["values"][1] == data["summary"]["total_sync_tests"]

    def test_charts_has_test_density(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "test_density" in data["charts"]

    def test_charts_test_density_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["test_density"]
        assert "labels" in chart
        assert "values" in chart
        assert len(chart["labels"]) == len(chart["values"])
        assert len(chart["labels"]) > 0

    def test_charts_has_imports_usage(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "imports_usage" in data["charts"]

    def test_charts_imports_usage_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["imports_usage"]
        assert "labels" in chart
        assert "values" in chart
        assert len(chart["labels"]) == len(chart["values"])

    def test_charts_has_assertions_per_file(self):
        site = self._make_site()
        data = site.get_testing_data()
        assert "assertions_per_file" in data["charts"]

    def test_charts_assertions_per_file_structure(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["assertions_per_file"]
        assert "labels" in chart
        assert "values" in chart
        assert len(chart["labels"]) == len(chart["values"])

    def test_charts_test_categories_from_category_counts(self):
        """test_categories chart uses actual per-file category counts."""
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["test_categories"]
        # Total values should match total test files
        assert sum(chart["values"]) == len(data["test_files"])

    def test_all_chart_labels_values_same_length(self):
        site = self._make_site()
        data = site.get_testing_data()
        for key, chart in data["charts"].items():
            assert len(chart["labels"]) == len(chart["values"]), \
                f"Chart '{key}': labels({len(chart['labels'])}) != values({len(chart['values'])})"

    def test_all_charts_json_serializable(self):
        site = self._make_site()
        data = site.get_testing_data()
        serialized = json.dumps(data["charts"])
        assert isinstance(serialized, str)


class TestPhase31fTemplateEnhancements:
    """Template includes Phase 31f enhanced elements."""

    def _template_path(self):
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "aquilia", "admin", "templates", "testing.html",
        )

    def _read_template(self):
        with open(self._template_path()) as f:
            return f.read()

    def test_template_has_categories_chart_canvas(self):
        assert "chartCategories" in self._read_template()

    def test_template_has_async_sync_chart_canvas(self):
        assert "chartAsyncSync" in self._read_template()

    def test_template_has_density_chart_canvas(self):
        assert "chartDensity" in self._read_template()

    def test_template_has_imports_chart_canvas(self):
        assert "chartImports" in self._read_template()

    def test_template_has_asserts_per_file_canvas(self):
        assert "chartAssertsPerFile" in self._read_template()

    def test_template_has_search_input(self):
        assert "testFileSearch" in self._read_template()

    def test_template_has_category_filter(self):
        assert "testCategoryFilter" in self._read_template()

    def test_template_has_snippet_panel(self):
        assert "snippet-panel" in self._read_template()

    def test_template_has_snippet_tabs(self):
        content = self._read_template()
        assert "snippet-tab" in content
        assert "snip-unit" in content
        assert "snip-integration" in content
        assert "snip-client" in content
        assert "snip-mock" in content
        assert "snip-fixture" in content

    def test_template_has_copy_btn(self):
        assert "copy-btn" in self._read_template()

    def test_template_has_count_up_animation(self):
        content = self._read_template()
        assert "data-count" in content
        assert "countPulse" in content or "count-done" in content

    def test_template_has_density_bar(self):
        assert "density-bar" in self._read_template()

    def test_template_has_density_fill(self):
        assert "density-fill" in self._read_template()

    def test_template_has_category_badges(self):
        content = self._read_template()
        assert "cat-badge" in content
        assert "cat-unit" in content
        assert "cat-integration" in content
        assert "cat-database" in content
        assert "cat-e2e" in content

    def test_template_has_enhanced_status_bar(self):
        content = self._read_template()
        assert "total_assert_stmts" in content or "assert stmts" in content.lower()
        assert "total_async_tests" in content or "async" in content.lower()

    def test_template_has_imports_heatmap_section(self):
        assert "imports_usage" in self._read_template()

    def test_template_has_data_category_attribute(self):
        """Test file rows have data-category for JS filtering."""
        assert "data-category" in self._read_template()

    def test_template_has_data_name_attribute(self):
        """Test file rows have data-name for JS search."""
        assert "data-name" in self._read_template()

    def test_template_has_filter_files_function(self):
        assert "filterFiles" in self._read_template()

    def test_template_has_no_results_indicator(self):
        assert "testFileNoResults" in self._read_template()

    def test_template_file_table_has_assert_column(self):
        content = self._read_template()
        assert "Asserts" in content or "assert_count" in content

    def test_template_file_table_has_density_column(self):
        content = self._read_template()
        assert "Density" in content or "density" in content

    def test_template_file_table_has_async_column(self):
        content = self._read_template()
        assert "async_tests" in content or "Async" in content

    def test_template_enhanced_metric_cards(self):
        """Second row of metric cards for Phase 31f."""
        content = self._read_template()
        assert "Assert Statements" in content
        assert "Avg Tests / File" in content or "avg_tests_per_file" in content
        assert "Avg LOC / Test" in content or "avg_loc_per_test" in content
        assert "Avg Density" in content or "avg_density" in content


class TestPhase31fRenderWithEnhancedData:
    """render_testing_page works with Phase 31f enhanced data."""

    def _testing_data(self, **overrides):
        base = {
            "available": True,
            "framework_version": "1.0.0",
            "test_classes": [
                {"name": "AquiliaTestCase", "description": "Full test", "base": "IsolatedAsyncioTestCase",
                 "features": ["auto_server"], "category": "integration"},
            ],
            "client": {
                "http": {"name": "TestClient", "methods": ["get", "post"], "features": ["in_process_asgi"]},
                "websocket": {"name": "WebSocketTestClient", "features": ["connect"]},
            },
            "assertions": [
                {"category": "HTTP Status", "methods": ["assert_status_200"], "count": 1},
            ],
            "total_assertions": 1,
            "fixtures": [{"name": "test_client", "async": True}],
            "total_fixtures": 1,
            "mock_infra": [
                {"name": "MockFaultEngine", "module": "faults", "description": "Capture faults",
                 "features": ["emit_capture"]},
            ],
            "total_mocks": 1,
            "utilities": [{"name": "make_test_scope", "description": "Build ASGI scope"}],
            "total_utilities": 1,
            "test_files": [
                {"name": "test_example.py", "directory": "tests", "path": "/test_example.py",
                 "lines": 100, "test_count": 10, "class_count": 2,
                 "category": "unit", "assert_count": 25, "density": 10.0,
                 "async_tests": 3, "sync_tests": 7, "imports": ["AquiliaTestCase"]},
            ],
            "total_test_files": 1,
            "component_coverage": [
                {"name": "Server", "module": "server", "status": "covered"},
            ],
            "total_components": 1,
            "covered_components": 1,
            "summary": {
                "total_test_cases": 4, "total_assertions": 1, "total_fixtures": 1,
                "total_mocks": 1, "total_utilities": 1, "total_test_files": 1,
                "total_test_functions": 10, "total_test_classes": 2, "total_lines": 100,
                "total_components": 1, "covered_components": 1,
                "total_assert_stmts": 25, "avg_tests_per_file": 10.0,
                "avg_loc_per_test": 10.0, "avg_density": 10.0,
                "total_async_tests": 3, "total_sync_tests": 7,
                "category_breakdown": {"unit": 1, "integration": 0, "database": 0, "e2e": 0, "other": 0},
                "imports_usage": {"AquiliaTestCase": 1},
            },
            "charts": {
                "test_distribution": {"labels": ["example"], "values": [10]},
                "test_categories": {"labels": ["Unit"], "values": [1]},
                "assertion_categories": {"labels": ["HTTP Status"], "values": [1]},
                "mock_infrastructure": {"labels": ["MockFaultEngine"], "values": [1]},
                "lines_of_code": {"labels": ["example"], "values": [100]},
                "component_coverage": {"labels": ["Server"], "values": [100]},
                "async_sync": {"labels": ["Async", "Sync"], "values": [3, 7]},
                "test_density": {"labels": ["example"], "values": [10.0]},
                "imports_usage": {"labels": ["AquiliaTestCase"], "values": [1]},
                "assertions_per_file": {"labels": ["example"], "values": [25]},
            },
        }
        base.update(overrides)
        return base

    def test_render_returns_string(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert isinstance(html, str)

    def test_render_contains_new_chart_canvases(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "chartCategories" in html
        assert "chartAsyncSync" in html
        assert "chartDensity" in html
        assert "chartImports" in html
        assert "chartAssertsPerFile" in html

    def test_render_contains_enhanced_metrics(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "Assert Statements" in html
        assert "Avg Tests / File" in html
        assert "Avg Density" in html

    def test_render_contains_category_badge(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "cat-badge" in html
        assert "cat-unit" in html

    def test_render_contains_search_elements(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "testFileSearch" in html
        assert "testCategoryFilter" in html

    def test_render_contains_snippet_panel(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "Quick Setup" in html
        assert "snippet-panel" in html

    def test_render_contains_density_bar(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "density-bar" in html

    def test_render_contains_status_bar_with_asserts(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "25" in html  # total_assert_stmts
        assert "assert stmts" in html.lower() or "assert" in html.lower()

    def test_render_contains_async_sync_in_status(self):
        from aquilia.admin.templates import render_testing_page
        html = render_testing_page(testing_data=self._testing_data())
        assert "3 async" in html or "3 async" in html.lower()

    def test_render_with_real_data_enhanced(self):
        """Render with real data includes all Phase 31f enhancements."""
        from aquilia.admin.site import AdminSite
        from aquilia.admin.templates import render_testing_page

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Aquilia Admin"
        site._initialised = True
        site._admin_config = None

        data = site.get_testing_data()
        html = render_testing_page(testing_data=data)

        assert "chartCategories" in html
        assert "chartAsyncSync" in html
        assert "chartDensity" in html
        assert "chartImports" in html
        assert "snippet-panel" in html
        assert "testFileSearch" in html
        assert "Assert Statements" in html
        assert len(html) > 2000


class TestPhase31fEdgeCases:
    """Edge cases for Phase 31f enhanced data."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        return site

    def test_density_values_non_negative(self):
        site = self._make_site()
        data = site.get_testing_data()
        for v in data["charts"]["test_density"]["values"]:
            assert v >= 0

    def test_assert_counts_non_negative(self):
        site = self._make_site()
        data = site.get_testing_data()
        for v in data["charts"]["assertions_per_file"]["values"]:
            assert v >= 0

    def test_imports_usage_values_positive(self):
        site = self._make_site()
        data = site.get_testing_data()
        for v in data["charts"]["imports_usage"]["values"]:
            assert v > 0

    def test_async_sync_sum_equals_total(self):
        site = self._make_site()
        data = site.get_testing_data()
        chart = data["charts"]["async_sync"]
        assert chart["values"][0] + chart["values"][1] == data["summary"]["total_test_functions"]

    def test_categories_from_actual_files(self):
        """Category breakdown should reflect actual file categorisation."""
        site = self._make_site()
        data = site.get_testing_data()
        # Each test file has a category, summing categories should match file count
        expected_total = len(data["test_files"])
        cat_total = sum(data["summary"]["category_breakdown"].values())
        assert cat_total == expected_total

    def test_enhanced_data_json_serializable(self):
        site = self._make_site()
        data = site.get_testing_data()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert "charts" in parsed
        assert "async_sync" in parsed["charts"]
        assert "test_density" in parsed["charts"]

    def test_enhanced_data_idempotent(self):
        site = self._make_site()
        d1 = site.get_testing_data()
        d2 = site.get_testing_data()
        assert d1["summary"]["total_assert_stmts"] == d2["summary"]["total_assert_stmts"]
        assert d1["summary"]["total_async_tests"] == d2["summary"]["total_async_tests"]
        assert d1["summary"]["category_breakdown"] == d2["summary"]["category_breakdown"]
