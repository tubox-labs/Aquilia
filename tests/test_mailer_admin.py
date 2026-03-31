"""
Phase 22 — Comprehensive Mailer Admin Page Tests.

Exhaustive regression tests for the Mailer admin integration:

 1. AdminConfig — module registration, defaults, from_dict round-trips
 2. AdminModules builder — enable_mailer/disable_mailer, chaining, enable_all
 3. Integration.admin() flat syntax — enable_mailer=True/False
 4. Workspace to_dict round-trip
 5. AdminPermission — MAILER_VIEW, MAILER_MANAGE, role mapping
 6. AdminSite.get_mailer_data() — structure, defaults, wired service
 7. render_mailer_page() — produces HTML, template variables, fallback
 8. AdminController mailer routes — method existence, async, source checks
 9. Sidebar link presence
10. Template file — exists, extends base.html, block content, block extra_js
11. server.py route wiring — mailer routes always registered
12. Disabled-page behaviour — module off → styled disabled page (not 404)
13. Mail subsystem imports — envelope, service, providers, faults
14. Config builders — _mailer in __slots__, to_dict, enable/disable return self
15. Send-test controller logic — email validation, priority mapping, body generation
16. Health-check controller logic — provider iteration, overall status
17. Security tab data — DKIM, TLS, PII, allowed domains
18. Edge cases — empty providers, no service, partial config
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ════════════════════════════════════════════════════════════════════════════
# 1. ADMIN CONFIG — MODULE REGISTRATION
# ════════════════════════════════════════════════════════════════════════════


class TestAdminConfigMailerModule:
    """AdminConfig must include 'mailer' in its modules dict."""

    def test_admin_config_has_mailer_key(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert "mailer" in cfg.modules

    def test_admin_config_mailer_disabled_by_default(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert cfg.modules["mailer"] is False

    def test_admin_config_is_module_enabled_mailer_false(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert cfg.is_module_enabled("mailer") is False

    def test_admin_config_is_module_enabled_mailer_true(self):
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
                "mlops": False,
                "storage": False,
                "mailer": True,
            }
        )
        assert cfg.is_module_enabled("mailer") is True

    def test_admin_config_from_dict_mailer_default_false(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({})
        assert cfg.is_module_enabled("mailer") is False

    def test_admin_config_from_dict_mailer_enabled(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mailer": True}})
        assert cfg.is_module_enabled("mailer") is True

    def test_admin_config_from_dict_mailer_disabled_explicit(self):
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mailer": False}})
        assert cfg.is_module_enabled("mailer") is False

    def test_admin_config_from_dict_preserves_other_modules(self):
        """Enabling mailer shouldn't break other modules."""
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig.from_dict({"modules": {"mailer": True, "tasks": True}})
        assert cfg.is_module_enabled("mailer") is True
        assert cfg.is_module_enabled("tasks") is True
        assert cfg.is_module_enabled("dashboard") is True
        assert cfg.is_module_enabled("monitoring") is False

    def test_admin_config_frozen(self):
        """AdminConfig is frozen dataclass — immutable."""
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        with pytest.raises(Exception):
            cfg.modules = {}

    def test_admin_config_mailer_not_in_default_enabled_set(self):
        """Mailer should not be enabled by default (opt-in only)."""
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        default_enabled = [k for k, v in cfg.modules.items() if v]
        assert "mailer" not in default_enabled


# ════════════════════════════════════════════════════════════════════════════
# 2. ADMIN MODULES BUILDER
# ════════════════════════════════════════════════════════════════════════════


class TestAdminModulesMailerBuilder:
    """AdminModules builder must have enable/disable_mailer methods."""

    def test_enable_mailer(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_mailer()
        d = mods.to_dict()
        assert d["mailer"] is True

    def test_disable_mailer(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_mailer().disable_mailer()
        d = mods.to_dict()
        assert d["mailer"] is False

    def test_mailer_disabled_by_default(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert d["mailer"] is False

    def test_enable_mailer_returns_self(self):
        """Fluent API — enable_mailer returns self for chaining."""
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        result = mods.enable_mailer()
        assert result is mods

    def test_disable_mailer_returns_self(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        result = mods.disable_mailer()
        assert result is mods

    def test_chaining_with_other_modules(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_tasks().enable_errors().enable_mailer()
        d = mods.to_dict()
        assert d["tasks"] is True
        assert d["errors"] is True
        assert d["mailer"] is True

    def test_enable_all_includes_mailer(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_all()
        d = mods.to_dict()
        assert d["mailer"] is True

    def test_disable_all_includes_mailer(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_all().disable_all()
        d = mods.to_dict()
        assert d["mailer"] is False

    def test_mailer_key_in_to_dict(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert "mailer" in d

    def test_repr_includes_mailer_when_enabled(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_mailer()
        r = repr(mods)
        assert "mailer" in r

    def test_repr_excludes_mailer_when_disabled(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        r = repr(mods)
        assert "mailer" not in r

    def test_slots_contains_mailer(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        assert "_mailer" in mods.__slots__

    def test_enable_mailer_with_storage(self):
        """enable_mailer + enable_storage together."""
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_storage().enable_mailer()
        d = mods.to_dict()
        assert d["mailer"] is True
        assert d["storage"] is True

    def test_enable_mailer_with_mlops(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules().enable_mlops().enable_mailer()
        d = mods.to_dict()
        assert d["mailer"] is True
        assert d["mlops"] is True


# ════════════════════════════════════════════════════════════════════════════
# 3. INTEGRATION.ADMIN() FLAT SYNTAX
# ════════════════════════════════════════════════════════════════════════════


class TestIntegrationAdminFlatMailer:
    """Integration.admin(enable_mailer=True) flat param."""

    def test_flat_enable_mailer(self):
        from aquilia.config_builders import Integration

        cfg = Integration.admin(enable_mailer=True)
        assert cfg["modules"]["mailer"] is True

    def test_flat_enable_mailer_default_false(self):
        from aquilia.config_builders import Integration

        cfg = Integration.admin()
        assert cfg["modules"]["mailer"] is False

    def test_flat_enable_mailer_with_other_modules(self):
        from aquilia.config_builders import Integration

        cfg = Integration.admin(
            enable_mailer=True,
            enable_tasks=True,
            enable_storage=True,
        )
        assert cfg["modules"]["mailer"] is True
        assert cfg["modules"]["tasks"] is True
        assert cfg["modules"]["storage"] is True

    def test_flat_enable_mailer_preserved_in_admin_config(self):
        """Round-trip: flat syntax → AdminConfig."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig

        raw = Integration.admin(enable_mailer=True)
        cfg = AdminConfig.from_dict(raw)
        assert cfg.is_module_enabled("mailer") is True

    def test_flat_enable_mailer_false_preserved_in_admin_config(self):
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig

        raw = Integration.admin(enable_mailer=False)
        cfg = AdminConfig.from_dict(raw)
        assert cfg.is_module_enabled("mailer") is False

    def test_flat_enable_mailer_not_in_default_config(self):
        from aquilia.config_builders import Integration

        cfg = Integration.admin()
        assert cfg["modules"]["mailer"] is False


# ════════════════════════════════════════════════════════════════════════════
# 4. WORKSPACE TO_DICT ROUND-TRIP
# ════════════════════════════════════════════════════════════════════════════


class TestWorkspaceMailerRoundTrip:
    """Workspace serialisation includes mailer module."""

    def test_workspace_admin_mailer_enabled(self):
        from aquilia.config_builders import Workspace, Integration

        ws = Workspace("test").integrate(Integration.admin(enable_mailer=True))
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["mailer"] is True

    def test_workspace_admin_mailer_disabled(self):
        from aquilia.config_builders import Workspace, Integration

        ws = Workspace("test").integrate(Integration.admin())
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["mailer"] is False

    def test_workspace_admin_modules_builder_mailer(self):
        from aquilia.config_builders import Workspace, Integration

        mods = Integration.AdminModules().enable_mailer()
        ws = Workspace("test").integrate(Integration.admin(modules=mods))
        d = ws.to_dict()
        assert d["integrations"]["admin"]["modules"]["mailer"] is True


# ════════════════════════════════════════════════════════════════════════════
# 5. ADMIN PERMISSIONS — MAILER
# ════════════════════════════════════════════════════════════════════════════


class TestAdminPermissionsMailer:
    """MAILER_VIEW and MAILER_MANAGE exist and are in correct roles."""

    def test_mailer_view_exists(self):
        from aquilia.admin.permissions import AdminPermission

        assert hasattr(AdminPermission, "MAILER_VIEW")

    def test_mailer_manage_exists(self):
        from aquilia.admin.permissions import AdminPermission

        assert hasattr(AdminPermission, "MAILER_MANAGE")

    def test_mailer_view_value(self):
        from aquilia.admin.permissions import AdminPermission

        assert AdminPermission.MAILER_VIEW.value == "admin.mailer.view"

    def test_mailer_manage_value(self):
        from aquilia.admin.permissions import AdminPermission

        assert AdminPermission.MAILER_MANAGE.value == "admin.mailer.manage"

    def test_viewer_role_has_mailer_view(self):
        from aquilia.admin.permissions import ROLE_PERMISSIONS, AdminRole, AdminPermission

        assert AdminPermission.MAILER_VIEW in ROLE_PERMISSIONS[AdminRole.VIEWER]

    def test_viewer_role_no_mailer_manage(self):
        from aquilia.admin.permissions import ROLE_PERMISSIONS, AdminRole, AdminPermission

        assert AdminPermission.MAILER_MANAGE not in ROLE_PERMISSIONS[AdminRole.VIEWER]

    def test_staff_role_has_mailer_view(self):
        from aquilia.admin.permissions import ROLE_PERMISSIONS, AdminRole, AdminPermission

        assert AdminPermission.MAILER_VIEW in ROLE_PERMISSIONS[AdminRole.STAFF]

    def test_staff_role_has_mailer_manage(self):
        from aquilia.admin.permissions import ROLE_PERMISSIONS, AdminRole, AdminPermission

        assert AdminPermission.MAILER_MANAGE in ROLE_PERMISSIONS[AdminRole.STAFF]

    def test_admin_role_has_mailer_view(self):
        """Superadmin role should inherit at least MAILER_VIEW."""
        from aquilia.admin.permissions import ROLE_PERMISSIONS, AdminRole, AdminPermission

        admin_perms = ROLE_PERMISSIONS.get(AdminRole.SUPERADMIN, set())
        # Superadmin might use FULL_ACCESS or explicit perms
        has_perm = AdminPermission.MAILER_VIEW in admin_perms or AdminPermission.FULL_ACCESS in admin_perms
        assert has_perm

    def test_mailer_permissions_are_enum_members(self):
        from aquilia.admin.permissions import AdminPermission

        assert isinstance(AdminPermission.MAILER_VIEW, AdminPermission)
        assert isinstance(AdminPermission.MAILER_MANAGE, AdminPermission)

    def test_mailer_view_is_string_based(self):
        from aquilia.admin.permissions import AdminPermission

        assert isinstance(AdminPermission.MAILER_VIEW.value, str)
        assert "mailer" in AdminPermission.MAILER_VIEW.value


# ════════════════════════════════════════════════════════════════════════════
# 6. GET_MAILER_DATA() — DATA STRUCTURE
# ════════════════════════════════════════════════════════════════════════════


class TestGetMailerData:
    """AdminSite.get_mailer_data() returns comprehensive mail subsystem info."""

    def _make_site(self):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        site._mail_service = None
        return site

    def test_returns_dict(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert isinstance(data, dict)

    def test_has_available_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "available" in data

    def test_no_service_available_false(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert data["available"] is False

    def test_no_service_enabled_false(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert data["enabled"] is False

    def test_has_providers_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_has_provider_count(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "provider_count" in data
        assert data["provider_count"] == 0

    def test_has_active_provider_count(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "active_provider_count" in data
        assert data["active_provider_count"] == 0

    def test_has_default_from(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "default_from" in data
        assert isinstance(data["default_from"], str)

    def test_has_retry_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "retry" in data
        assert isinstance(data["retry"], dict)

    def test_has_rate_limit_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "rate_limit" in data
        assert isinstance(data["rate_limit"], dict)

    def test_has_security_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "security" in data
        assert isinstance(data["security"], dict)

    def test_has_templates_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "templates" in data
        assert isinstance(data["templates"], dict)

    def test_has_queue_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "queue" in data
        assert isinstance(data["queue"], dict)

    def test_has_stats_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "stats" in data
        assert isinstance(data["stats"], dict)

    def test_stats_has_total_sent(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "total_sent" in data["stats"]

    def test_stats_has_total_failed(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "total_failed" in data["stats"]

    def test_stats_has_total_queued(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "total_queued" in data["stats"]

    def test_stats_has_total_bounced(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "total_bounced" in data["stats"]

    def test_has_is_healthy_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "is_healthy" in data
        assert data["is_healthy"] is False

    def test_has_preview_mode(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "preview_mode" in data

    def test_has_console_backend(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "console_backend" in data

    def test_has_metrics_enabled(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "metrics_enabled" in data

    def test_has_tracing_enabled(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "tracing_enabled" in data

    def test_has_config_key(self):
        site = self._make_site()
        data = site.get_mailer_data()
        assert "config" in data


class TestGetMailerDataWithService:
    """get_mailer_data() with a mocked MailService."""

    def _make_site_with_service(self):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None

        # Mock MailConfig
        config = MagicMock()
        config.enabled = True
        config.default_from = "test@example.com"
        config.default_reply_to = "reply@example.com"
        config.subject_prefix = "[TEST] "
        config.preview_mode = False
        config.console_backend = True
        config.metrics_enabled = True
        config.tracing_enabled = False

        # Mock provider config
        provider = MagicMock()
        provider.name = "dev-console"
        provider.type = "console"
        provider.enabled = True
        provider.priority = 50
        provider.rate_limit_per_min = 600
        provider.host = None
        provider.port = None
        provider.use_tls = False
        provider.use_ssl = False
        provider.timeout = 30.0
        config.providers = [provider]

        # Mock retry
        retry = MagicMock()
        retry.max_attempts = 3
        retry.base_delay = 2.0
        retry.max_delay = 120.0
        retry.jitter = True
        config.retry = retry

        # Mock rate_limit
        rl = MagicMock()
        rl.global_per_minute = 500
        rl.per_domain_per_minute = 50
        rl.per_provider_per_minute = None
        config.rate_limit = rl

        # Mock security
        sec = MagicMock()
        sec.dkim_enabled = False
        sec.dkim_domain = None
        sec.dkim_selector = "aquilia"
        sec.require_tls = True
        sec.pii_redaction_enabled = True
        sec.allowed_from_domains = ["example.com"]
        config.security = sec

        # Mock templates
        tmpl = MagicMock()
        tmpl.template_dirs = ["mail_templates"]
        tmpl.auto_escape = True
        tmpl.cache_compiled = True
        tmpl.strict_mode = False
        config.templates = tmpl

        # Mock queue
        queue = MagicMock()
        queue.batch_size = 25
        queue.poll_interval = 2.0
        queue.dedupe_window_seconds = 1800
        queue.retention_days = 14
        config.queue = queue

        config.to_dict.return_value = {"enabled": True, "default_from": "test@example.com"}

        # Mock MailService
        svc = MagicMock()
        svc.config = config
        svc.is_healthy.return_value = True
        svc.get_provider_names.return_value = ["dev-console"]

        site._mail_service = svc
        return site, svc

    def test_available_true(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["available"] is True

    def test_enabled_true(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["enabled"] is True

    def test_default_from_matches(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["default_from"] == "test@example.com"

    def test_default_reply_to_matches(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["default_reply_to"] == "reply@example.com"

    def test_subject_prefix_matches(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["subject_prefix"] == "[TEST] "

    def test_console_backend_true(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["console_backend"] is True

    def test_is_healthy_true(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["is_healthy"] is True

    def test_provider_count(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["provider_count"] == 1

    def test_active_provider_count(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["active_provider_count"] == 1

    def test_provider_name(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["providers"][0]["name"] == "dev-console"

    def test_provider_type(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["providers"][0]["type"] == "console"

    def test_provider_type_display(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "Console (Dev)"

    def test_provider_status_active(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["providers"][0]["status"] == "active"

    def test_retry_config(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["retry"]["max_attempts"] == 3
        assert data["retry"]["base_delay"] == 2.0
        assert data["retry"]["jitter"] is True

    def test_rate_limit_config(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["rate_limit"]["global_per_minute"] == 500
        assert data["rate_limit"]["per_domain_per_minute"] == 50

    def test_security_config(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["security"]["require_tls"] is True
        assert data["security"]["pii_redaction_enabled"] is True
        assert "example.com" in data["security"]["allowed_from_domains"]

    def test_template_config(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["templates"]["auto_escape"] is True
        assert data["templates"]["cache_compiled"] is True

    def test_queue_config(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert data["queue"]["batch_size"] == 25
        assert data["queue"]["retention_days"] == 14

    def test_config_dict(self):
        site, _ = self._make_site_with_service()
        data = site.get_mailer_data()
        assert isinstance(data["config"], dict)
        assert data["config"]["enabled"] is True


# ════════════════════════════════════════════════════════════════════════════
# 7. RENDER_MAILER_PAGE() — TEMPLATE RENDERING
# ════════════════════════════════════════════════════════════════════════════


class TestRenderMailerPage:
    """render_mailer_page() produces HTML with correct template variables."""

    def _sample_data(self, available=True, enabled=True):
        return {
            "available": available,
            "enabled": enabled,
            "config": {"enabled": enabled},
            "providers": [
                {
                    "name": "smtp-primary",
                    "type": "smtp",
                    "type_display": "SMTP",
                    "enabled": True,
                    "active": True,
                    "priority": 10,
                    "rate_limit_per_min": 1000,
                    "host": "smtp.example.com",
                    "port": 587,
                    "use_tls": True,
                    "use_ssl": False,
                    "timeout": 30.0,
                    "status": "active",
                }
            ],
            "provider_count": 1,
            "active_provider_count": 1,
            "default_from": "noreply@example.com",
            "default_reply_to": "reply@example.com",
            "subject_prefix": "[APP] ",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": True,
            "tracing_enabled": False,
            "retry": {"max_attempts": 5, "base_delay": 1.0, "max_delay": 3600, "jitter": True},
            "rate_limit": {"global_per_minute": 1000, "per_domain_per_minute": 100, "per_provider_per_minute": None},
            "security": {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_selector": "aquilia",
                "require_tls": True,
                "pii_redaction_enabled": False,
                "allowed_from_domains": ["example.com"],
            },
            "templates": {
                "template_dirs": ["mail_templates"],
                "auto_escape": True,
                "cache_compiled": True,
                "strict_mode": False,
            },
            "queue": {"batch_size": 50, "poll_interval": 1.0, "dedupe_window_seconds": 3600, "retention_days": 30},
            "is_healthy": True,
            "stats": {"total_sent": 42, "total_failed": 3, "total_queued": 5, "total_bounced": 1},
        }

    def test_returns_html_string(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert isinstance(html, str)
        assert len(html) > 100

    def test_contains_mailer_heading(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Mailer" in html

    def test_contains_provider_name(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "smtp-primary" in html

    def test_contains_default_from(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "noreply@example.com" in html

    def test_contains_send_test_button(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Send Test Email" in html

    def test_contains_health_check_button(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Health Check" in html

    def test_contains_tabs(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "switchTab" in html
        assert "tab-overview" in html
        assert "tab-providers" in html
        assert "tab-config" in html
        assert "tab-security" in html
        assert "tab-send-test" in html
        assert "tab-health" in html

    def test_contains_retry_config(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Retry" in html or "retry" in html

    def test_contains_rate_limit(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Rate Limit" in html or "rate_limit" in html or "Rate" in html

    def test_contains_dkim_section(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "DKIM" in html

    def test_contains_security_checklist(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Security Best Practices" in html or "security" in html.lower()

    def test_unavailable_state(self):
        """When mail is not available, show not-configured page."""
        from aquilia.admin.templates import render_mailer_page

        data = self._sample_data(available=False, enabled=False)
        data["available"] = False
        html = render_mailer_page(data)
        assert "Not Configured" in html or "not configured" in html.lower() or "Disabled" in html

    def test_contains_priority_select(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "critical" in html.lower()
        assert "normal" in html.lower()

    def test_contains_api_reference(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "send_mail" in html or "asend_mail" in html

    def test_contains_ats_reference(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "ATS" in html or "Template" in html

    def test_contains_subject_prefix(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "[APP]" in html

    def test_contains_provider_type_display(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "SMTP" in html

    def test_stat_values_in_html(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        # The stats (42 sent, 3 failed, etc.) should appear
        assert "42" in html  # total_sent
        assert "3" in html  # total_failed

    def test_healthy_status_shown(self):
        from aquilia.admin.templates import render_mailer_page

        html = render_mailer_page(self._sample_data())
        assert "Healthy" in html or "healthy" in html


class TestRenderMailerPageSignature:
    """render_mailer_page function signature."""

    def test_has_render_mailer_page(self):
        from aquilia.admin.templates import render_mailer_page

        assert callable(render_mailer_page)

    def test_signature_params(self):
        from aquilia.admin.templates import render_mailer_page

        sig = inspect.signature(render_mailer_page)
        param_names = list(sig.parameters.keys())
        assert "mailer_data" in param_names
        assert "app_list" in param_names
        assert "identity_name" in param_names

    def test_default_identity_name(self):
        from aquilia.admin.templates import render_mailer_page

        sig = inspect.signature(render_mailer_page)
        assert sig.parameters["identity_name"].default == "Admin"


# ════════════════════════════════════════════════════════════════════════════
# 8. ADMIN CONTROLLER MAILER ROUTES
# ════════════════════════════════════════════════════════════════════════════


class TestAdminControllerMailerRoutes:
    """AdminController has mailer routes compiled correctly."""

    def test_controller_has_mailer_view_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mailer_view")

    def test_controller_has_mailer_api_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mailer_api")

    def test_controller_has_mailer_send_test_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mailer_send_test")

    def test_controller_has_mailer_health_check_method(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "mailer_health_check")

    def test_mailer_view_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mailer_view)

    def test_mailer_api_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mailer_api)

    def test_mailer_send_test_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mailer_send_test)

    def test_mailer_health_check_is_async(self):
        from aquilia.admin.controller import AdminController

        assert inspect.iscoroutinefunction(AdminController.mailer_health_check)

    def test_controller_imports_render_mailer_page(self):
        """render_mailer_page is imported in controller module."""
        import aquilia.admin.controller as ctrl_mod

        assert hasattr(ctrl_mod, "render_mailer_page")

    def test_mailer_view_source_has_identity_check(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "_require_identity" in source

    def test_mailer_view_checks_module_enabled(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "is_module_enabled" in source
        assert '"mailer"' in source or "'mailer'" in source

    def test_mailer_view_returns_disabled_page(self):
        """When module is disabled, mailer_view returns disabled response."""
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "_module_disabled_response" in source

    def test_mailer_api_checks_module_enabled(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_api)
        assert "is_module_enabled" in source

    def test_mailer_view_calls_get_mailer_data(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "get_mailer_data" in source

    def test_mailer_api_calls_get_mailer_data(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_api)
        assert "get_mailer_data" in source

    def test_mailer_view_calls_render_mailer_page(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "render_mailer_page" in source

    def test_send_test_checks_permission(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "MAILER_MANAGE" in source

    def test_send_test_validates_email(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "email" in source.lower()
        # Should have email regex or validation
        assert "match" in source or "validate" in source.lower()

    def test_send_test_supports_priority(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "priority" in source
        assert "critical" in source or "CRITICAL" in source

    def test_send_test_uses_email_multi_alternatives(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "EmailMultiAlternatives" in source

    def test_health_check_iterates_providers(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "provider" in source.lower()
        assert "health_check" in source

    def test_health_check_returns_overall_healthy(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "overall_healthy" in source

    def test_mailer_view_audit_logs(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "audit_log" in source

    def test_send_test_audit_logs(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "audit_log" in source


# ════════════════════════════════════════════════════════════════════════════
# 9. SIDEBAR LINK
# ════════════════════════════════════════════════════════════════════════════


class TestSidebarMailerLink:
    """Sidebar HTML includes the mailer link."""

    def test_sidebar_template_exists(self):
        sidebar_path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "partials", "sidebar_v2.html")
        assert os.path.isfile(sidebar_path)

    def test_sidebar_contains_mailer_link(self):
        sidebar_path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "partials", "sidebar_v2.html")
        with open(sidebar_path, encoding="utf-8") as f:
            content = f.read()
        assert "mailer" in content.lower()

    def test_sidebar_mailer_has_icon(self):
        sidebar_path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "partials", "sidebar_v2.html")
        with open(sidebar_path, encoding="utf-8") as f:
            content = f.read()
        assert "icon-mail" in content

    def test_sidebar_mailer_href(self):
        sidebar_path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "partials", "sidebar_v2.html")
        with open(sidebar_path, encoding="utf-8") as f:
            content = f.read()
        assert "mailer/" in content

    def test_sidebar_mailer_label(self):
        sidebar_path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "partials", "sidebar_v2.html")
        with open(sidebar_path, encoding="utf-8") as f:
            content = f.read()
        assert "Mailer" in content


# ════════════════════════════════════════════════════════════════════════════
# 10. TEMPLATE FILE
# ════════════════════════════════════════════════════════════════════════════


class TestMailerTemplateFile:
    """mailer.html template exists and is well-formed."""

    def test_template_exists(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        assert os.path.isfile(path)

    def test_template_extends_base(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert '{% extends "base.html" %}' in content

    def test_template_has_block_content(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "{% block content %}" in content

    def test_template_has_block_extra_js(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "{% block extra_js %}" in content

    def test_template_no_script_tags_in_extra_js(self):
        """base.html wraps extra_js in <script> — no <script> in child."""
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Find the extra_js block content
        start = content.find("{% block extra_js %}")
        end = content.find("{% endblock %}", start)
        if start != -1 and end != -1:
            js_block = content[start:end]
            assert "<script" not in js_block

    def test_template_has_sendTestEmail_function(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "sendTestEmail" in content

    def test_template_has_runHealthCheck_function(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "runHealthCheck" in content

    def test_template_has_switchTab_function(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "switchTab" in content

    def test_template_has_overview_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-overview" in content

    def test_template_has_providers_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-providers" in content

    def test_template_has_config_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-config" in content

    def test_template_has_security_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-security" in content

    def test_template_has_templates_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-templates" in content

    def test_template_has_send_test_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-send-test" in content

    def test_template_has_health_tab(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "tab-health" in content

    def test_template_has_toast_notification(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "mailerToast" in content

    def test_template_has_test_history_table(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "testHistoryTable" in content or "testHistoryBody" in content

    def test_template_has_not_configured_state(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "Not Configured" in content or "not_configured" in content.lower()

    def test_template_references_dark_theme(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "var(--bg-card)" in content or "var(--text-primary)" in content

    def test_template_has_send_test_form_fields(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "testTo" in content
        assert "testSubject" in content
        assert "testPriority" in content

    def test_template_has_provider_type_icons(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "icon-server" in content  # SMTP
        assert "icon-cloud" in content  # SES
        assert "icon-terminal" in content  # Console

    def test_template_nonzero_size(self):
        path = os.path.join(REPO_ROOT, "aquilia", "admin", "templates", "mailer.html")
        size = os.path.getsize(path)
        assert size > 5000  # Should be a substantial template


# ════════════════════════════════════════════════════════════════════════════
# 11. SERVER.PY ROUTE WIRING
# ════════════════════════════════════════════════════════════════════════════


class TestServerMailerRouteWiring:
    """Mailer routes are registered in _wire_admin_integration (server.py)."""

    def test_server_module_has_wire_admin_integration(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "_wire_admin_integration" in src

    def test_server_registers_mailer_view_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mailer_view" in src
        assert "/mailer/" in src

    def test_server_registers_mailer_api_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mailer_api" in src
        assert "/mailer/api/" in src

    def test_server_registers_mailer_send_test_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mailer_send_test" in src
        assert "/mailer/send-test/" in src

    def test_server_registers_mailer_health_check_route(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "mailer_health_check" in src
        assert "/mailer/health-check/" in src

    def test_mailer_view_uses_get_method(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "mailer_view" in line and "url_prefix" in line:
                assert '"GET"' in line or "'GET'" in line

    def test_mailer_api_uses_get_method(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "mailer_api" in line and "url_prefix" in line:
                assert '"GET"' in line or "'GET'" in line

    def test_mailer_send_test_uses_post_method(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "mailer_send_test" in line and "url_prefix" in line:
                assert '"POST"' in line or "'POST'" in line

    def test_mailer_health_check_uses_post_method(self):
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        lines = src.splitlines()
        for line in lines:
            if "mailer_health_check" in line and "url_prefix" in line:
                assert '"POST"' in line or "'POST'" in line

    def test_mailer_routes_always_registered(self):
        """Mailer routes must NOT be behind if _mod('mailer') guard.

        They should be always-registered (like containers/pods) so the
        controller can show the disabled page instead of 404.
        """
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        # Find the mailer_view route registration
        mailer_view_idx = src.find('"mailer_view"')
        assert mailer_view_idx > 0, "mailer_view not found in server.py"

        # Walk backwards to find the nearest _mod() call
        preceding = src[max(0, mailer_view_idx - 500) : mailer_view_idx]
        # There should NOT be _mod("mailer") guarding these routes
        assert '_mod("mailer")' not in preceding or "always registered" in preceding.lower()

    def test_mailer_routes_before_model_crud(self):
        """Mailer routes should appear before the <model:str> catch-all routes."""
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        mailer_pos = src.find('"mailer_view"')
        # Find the first actual route using <model:str> (skip comments)
        model_crud_pos = src.find('f"{url_prefix}/<model:str>/')
        assert mailer_pos > 0, "mailer_view not found in server source"
        assert model_crud_pos > 0, "model CRUD routes not found in server source"
        assert mailer_pos < model_crud_pos, "Mailer routes must come before model CRUD catch-all"

    def test_mailer_routes_after_mlops_routes(self):
        """Mailer routes should be placed after MLOps routes."""
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        mlops_pos = src.find("mlops_view")
        mailer_pos = src.find("mailer_view")
        assert mlops_pos > 0
        assert mailer_pos > 0
        assert mailer_pos > mlops_pos


# ════════════════════════════════════════════════════════════════════════════
# 12. DISABLED PAGE BEHAVIOUR
# ════════════════════════════════════════════════════════════════════════════


class TestMailerDisabledPage:
    """When mailer module is off, controller returns styled disabled page."""

    def test_mailer_view_calls_module_disabled_response(self):
        """mailer_view uses _module_disabled_response when module is off."""
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        assert "_module_disabled_response" in source
        assert '"Mailer"' in source or "'Mailer'" in source

    def test_mailer_api_returns_404_when_disabled(self):
        """mailer_api returns JSON 404 when module is off."""
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_api)
        assert "mailer disabled" in source or "404" in source

    def test_send_test_returns_404_when_disabled(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "mailer disabled" in source or "404" in source

    def test_module_disabled_response_method_exists(self):
        from aquilia.admin.controller import AdminController

        assert hasattr(AdminController, "_module_disabled_response")

    def test_disabled_page_not_404_model_not_found(self):
        """The disabled page should NOT be ADMIN_MODEL_NOT_FOUND.

        This was the original bug: without always-registered routes,
        /mailer/ was caught by <model:str> and raised ADMIN_MODEL_NOT_FOUND.
        Now with routes always registered, the controller itself handles it.
        """
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_view)
        # Should have is_module_enabled check and _module_disabled_response
        assert "is_module_enabled" in source
        assert "_module_disabled_response" in source
        # Should NOT reference ADMIN_MODEL_NOT_FOUND
        assert "ADMIN_MODEL_NOT_FOUND" not in source


# ════════════════════════════════════════════════════════════════════════════
# 13. MAIL SUBSYSTEM IMPORTS
# ════════════════════════════════════════════════════════════════════════════


class TestMailSubsystemImports:
    """Mail subsystem components are importable."""

    def test_import_mail_init(self):
        import aquilia.mail

        assert aquilia.mail is not None

    def test_import_mail_service(self):
        from aquilia.mail.service import MailService

        assert MailService is not None

    def test_import_mail_config(self):
        from aquilia.mail.config import MailConfig

        assert MailConfig is not None

    def test_import_mail_envelope(self):
        from aquilia.mail.envelope import MailEnvelope

        assert MailEnvelope is not None

    def test_import_mail_message(self):
        from aquilia.mail.message import EmailMessage

        assert EmailMessage is not None

    def test_import_mail_multi_alternatives(self):
        from aquilia.mail.message import EmailMultiAlternatives

        assert EmailMultiAlternatives is not None

    def test_import_mail_providers_protocol(self):
        from aquilia.mail.providers import IMailProvider

        assert IMailProvider is not None

    def test_import_mail_faults(self):
        from aquilia.mail.faults import MailFault

        assert MailFault is not None

    def test_import_mail_send_fault(self):
        from aquilia.mail.faults import MailSendFault

        assert MailSendFault is not None

    def test_import_mail_config_fault(self):
        from aquilia.mail.faults import MailConfigFault

        assert MailConfigFault is not None

    def test_import_mail_template_fault(self):
        from aquilia.mail.faults import MailTemplateFault

        assert MailTemplateFault is not None

    def test_import_smtp_provider(self):
        from aquilia.mail.providers.smtp import SMTPProvider

        assert SMTPProvider is not None

    def test_import_console_provider(self):
        from aquilia.mail.providers.console import ConsoleProvider

        assert ConsoleProvider is not None

    def test_import_di_providers(self):
        from aquilia.mail.di_providers import register_mail_providers

        assert callable(register_mail_providers)

    def test_import_template_message(self):
        from aquilia.mail.message import TemplateMessage

        assert TemplateMessage is not None

    def test_mail_envelope_has_status(self):
        from aquilia.mail.envelope import EnvelopeStatus

        assert hasattr(EnvelopeStatus, "QUEUED")
        assert hasattr(EnvelopeStatus, "SENT")
        assert hasattr(EnvelopeStatus, "FAILED")

    def test_mail_envelope_has_priority(self):
        from aquilia.mail.envelope import Priority

        assert hasattr(Priority, "CRITICAL")
        assert hasattr(Priority, "HIGH")
        assert hasattr(Priority, "NORMAL")
        assert hasattr(Priority, "LOW")
        assert hasattr(Priority, "BULK")

    def test_priority_values_ordered(self):
        from aquilia.mail.envelope import Priority

        assert Priority.CRITICAL.value < Priority.HIGH.value
        assert Priority.HIGH.value < Priority.NORMAL.value
        assert Priority.NORMAL.value < Priority.LOW.value
        assert Priority.LOW.value < Priority.BULK.value


# ════════════════════════════════════════════════════════════════════════════
# 14. CONFIG BUILDERS DETAIL
# ════════════════════════════════════════════════════════════════════════════


class TestConfigBuildersMailerDetail:
    """Detailed checks on config_builders mailer integration."""

    def test_admin_modules_has_mailer_slot(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        assert "_mailer" in mods.__slots__

    def test_admin_modules_mailer_initial_value(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        assert mods._mailer is False

    def test_to_dict_has_mailer_key(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert "mailer" in d

    def test_to_dict_mailer_false_by_default(self):
        from aquilia.config_builders import Integration

        d = Integration.AdminModules().to_dict()
        assert d["mailer"] is False

    def test_to_dict_mailer_true_after_enable(self):
        from aquilia.config_builders import Integration

        d = Integration.AdminModules().enable_mailer().to_dict()
        assert d["mailer"] is True

    def test_enable_mailer_method_exists(self):
        from aquilia.config_builders import Integration

        assert hasattr(Integration.AdminModules, "enable_mailer")

    def test_disable_mailer_method_exists(self):
        from aquilia.config_builders import Integration

        assert hasattr(Integration.AdminModules, "disable_mailer")

    def test_enable_mailer_is_callable(self):
        from aquilia.config_builders import Integration

        assert callable(getattr(Integration.AdminModules, "enable_mailer"))

    def test_disable_mailer_is_callable(self):
        from aquilia.config_builders import Integration

        assert callable(getattr(Integration.AdminModules, "disable_mailer"))

    def test_legacy_admin_flat_pop_enable_mailer(self):
        """Integration.admin(enable_mailer=True) uses kwargs.pop."""
        from aquilia.config_builders import Integration

        cfg = Integration.admin(enable_mailer=True)
        assert cfg["modules"]["mailer"] is True

    def test_legacy_admin_flat_no_leftover_kwarg(self):
        """enable_mailer should be popped, not left as unknown kwarg."""
        from aquilia.config_builders import Integration

        # Should not raise on unknown kwargs
        cfg = Integration.admin(enable_mailer=True)
        assert isinstance(cfg, dict)


# ════════════════════════════════════════════════════════════════════════════
# 15. SEND-TEST CONTROLLER LOGIC
# ════════════════════════════════════════════════════════════════════════════


class TestSendTestControllerLogic:
    """Deep inspection of send-test endpoint logic."""

    def test_validates_email_with_regex(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "re.compile" in source or "email_re" in source

    def test_priority_map_has_all_levels(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "critical" in source
        assert "high" in source
        assert "normal" in source
        assert "low" in source
        assert "bulk" in source

    def test_default_body_generated_if_empty(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "Aquilia Test Email" in source or "test email" in source.lower()

    def test_html_body_includes_branding(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        # Should have the branded HTML template
        assert "Aquilia" in source
        assert "html" in source.lower()

    def test_returns_json_response(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "application/json" in source

    def test_returns_envelope_id(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "envelope_id" in source

    def test_returns_success_flag(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert '"success"' in source or "'success'" in source

    def test_returns_error_on_failure(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert '"error"' in source or "'error'" in source

    def test_handles_missing_mail_service(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "MailService not available" in source or "not available" in source.lower()

    def test_supports_from_email_override(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "from_email" in source

    def test_supports_reply_to(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_send_test)
        assert "reply_to" in source


# ════════════════════════════════════════════════════════════════════════════
# 16. HEALTH-CHECK CONTROLLER LOGIC
# ════════════════════════════════════════════════════════════════════════════


class TestHealthCheckControllerLogic:
    """Deep inspection of health-check endpoint logic."""

    def test_checks_mailer_view_permission(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "MAILER_VIEW" in source

    def test_returns_overall_healthy(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "overall_healthy" in source

    def test_returns_checked_count(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "checked_count" in source

    def test_returns_provider_results(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert '"providers"' in source or "'providers'" in source

    def test_handles_provider_exceptions(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "except" in source

    def test_returns_json(self):
        from aquilia.admin.controller import AdminController

        source = inspect.getsource(AdminController.mailer_health_check)
        assert "application/json" in source


# ════════════════════════════════════════════════════════════════════════════
# 17. SECURITY TAB DATA
# ════════════════════════════════════════════════════════════════════════════


class TestSecurityTabData:
    """Security-related data flows correctly through the pipeline."""

    def test_security_dict_structure(self):
        """get_mailer_data security dict has expected keys when service is wired."""
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None

        svc = MagicMock()
        config = MagicMock()
        config.enabled = True
        config.providers = []
        config.default_from = "test@test.com"
        config.default_reply_to = None
        config.subject_prefix = ""
        config.preview_mode = False
        config.console_backend = False
        config.metrics_enabled = False
        config.tracing_enabled = False

        sec = MagicMock()
        sec.dkim_enabled = True
        sec.dkim_domain = "example.com"
        sec.dkim_selector = "mail"
        sec.require_tls = True
        sec.pii_redaction_enabled = True
        sec.allowed_from_domains = ["example.com", "test.com"]
        config.security = sec

        config.retry = None
        config.rate_limit = None
        config.templates = None
        config.queue = None
        config.to_dict.return_value = {}

        svc.config = config
        svc.is_healthy.return_value = True
        svc.get_provider_names.return_value = []

        site._mail_service = svc
        data = site.get_mailer_data()

        assert data["security"]["dkim_enabled"] is True
        assert data["security"]["dkim_domain"] == "example.com"
        assert data["security"]["dkim_selector"] == "mail"
        assert data["security"]["require_tls"] is True
        assert data["security"]["pii_redaction_enabled"] is True
        assert "example.com" in data["security"]["allowed_from_domains"]
        assert "test.com" in data["security"]["allowed_from_domains"]

    def test_template_shows_dkim_enabled(self):
        from aquilia.admin.templates import render_mailer_page

        data = {
            "available": True,
            "enabled": True,
            "config": {},
            "providers": [],
            "provider_count": 0,
            "active_provider_count": 0,
            "default_from": "a@b.com",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": False,
            "tracing_enabled": False,
            "is_healthy": True,
            "retry": {},
            "rate_limit": {},
            "queue": {},
            "templates": {},
            "security": {
                "dkim_enabled": True,
                "dkim_domain": "x.com",
                "dkim_selector": "s1",
                "require_tls": True,
                "pii_redaction_enabled": False,
                "allowed_from_domains": ["x.com"],
            },
            "stats": {"total_sent": 0, "total_failed": 0, "total_queued": 0, "total_bounced": 0},
        }
        html = render_mailer_page(data)
        assert "DKIM" in html
        assert "x.com" in html


# ════════════════════════════════════════════════════════════════════════════
# 18. EDGE CASES
# ════════════════════════════════════════════════════════════════════════════


class TestMailerEdgeCases:
    """Edge cases and defensive behaviour."""

    def test_get_mailer_data_no_mail_service_attr(self):
        """Site without _mail_service attribute still returns safe dict."""
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        # Do NOT set _mail_service
        data = site.get_mailer_data()
        assert data["available"] is False

    def test_get_mailer_data_service_none(self):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        site._mail_service = None
        data = site.get_mailer_data()
        assert data["available"] is False

    def test_get_mailer_data_config_none(self):
        """Service exists but config is None."""
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        svc = MagicMock()
        svc.config = None
        site._mail_service = svc
        data = site.get_mailer_data()
        assert data["available"] is True
        assert data["enabled"] is False

    def test_render_empty_providers_list(self):
        from aquilia.admin.templates import render_mailer_page

        data = {
            "available": True,
            "enabled": True,
            "config": {},
            "providers": [],
            "provider_count": 0,
            "active_provider_count": 0,
            "default_from": "a@b.com",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": False,
            "tracing_enabled": False,
            "is_healthy": False,
            "retry": {},
            "rate_limit": {},
            "security": {},
            "templates": {},
            "queue": {},
            "stats": {"total_sent": 0, "total_failed": 0, "total_queued": 0, "total_bounced": 0},
        }
        html = render_mailer_page(data)
        assert isinstance(html, str)
        assert "No Providers Configured" in html or "No" in html

    def test_render_with_multiple_providers(self):
        from aquilia.admin.templates import render_mailer_page

        data = {
            "available": True,
            "enabled": True,
            "config": {},
            "providers": [
                {
                    "name": "primary",
                    "type": "smtp",
                    "type_display": "SMTP",
                    "enabled": True,
                    "active": True,
                    "priority": 10,
                    "rate_limit_per_min": 1000,
                    "host": "smtp.a.com",
                    "port": 587,
                    "use_tls": True,
                    "use_ssl": False,
                    "timeout": 30,
                    "status": "active",
                },
                {
                    "name": "fallback",
                    "type": "ses",
                    "type_display": "AWS SES",
                    "enabled": True,
                    "active": False,
                    "priority": 50,
                    "rate_limit_per_min": 500,
                    "host": None,
                    "port": None,
                    "use_tls": False,
                    "use_ssl": False,
                    "timeout": 60,
                    "status": "inactive",
                },
            ],
            "provider_count": 2,
            "active_provider_count": 1,
            "default_from": "a@b.com",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": True,
            "tracing_enabled": True,
            "is_healthy": True,
            "retry": {"max_attempts": 3, "base_delay": 1, "max_delay": 60, "jitter": True},
            "rate_limit": {"global_per_minute": 500, "per_domain_per_minute": 50, "per_provider_per_minute": None},
            "security": {
                "dkim_enabled": False,
                "dkim_domain": None,
                "dkim_selector": "aquilia",
                "require_tls": True,
                "pii_redaction_enabled": False,
                "allowed_from_domains": [],
            },
            "templates": {"template_dirs": ["tmpl"], "auto_escape": True, "cache_compiled": True, "strict_mode": False},
            "queue": {"batch_size": 25, "poll_interval": 2, "dedupe_window_seconds": 1800, "retention_days": 7},
            "stats": {"total_sent": 100, "total_failed": 5, "total_queued": 10, "total_bounced": 2},
        }
        html = render_mailer_page(data)
        assert "primary" in html
        assert "fallback" in html
        assert "SMTP" in html
        assert "AWS SES" in html

    def test_render_preview_mode_shown(self):
        from aquilia.admin.templates import render_mailer_page

        data = {
            "available": True,
            "enabled": True,
            "config": {},
            "providers": [],
            "provider_count": 0,
            "active_provider_count": 0,
            "default_from": "a@b.com",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": True,
            "console_backend": False,
            "metrics_enabled": False,
            "tracing_enabled": False,
            "is_healthy": True,
            "retry": {},
            "rate_limit": {},
            "security": {},
            "templates": {},
            "queue": {},
            "stats": {"total_sent": 0, "total_failed": 0, "total_queued": 0, "total_bounced": 0},
        }
        html = render_mailer_page(data)
        assert "Preview" in html or "preview" in html

    def test_set_mail_service_method_exists(self):
        from aquilia.admin.site import AdminSite

        assert hasattr(AdminSite, "set_mail_service")

    def test_set_mail_service_stores_reference(self):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None
        mock_svc = MagicMock()
        site.set_mail_service(mock_svc)
        assert site._mail_service is mock_svc

    def test_server_wires_mail_service(self):
        """server.py should call site.set_mail_service()."""
        import aquilia.server as srv_mod

        src = inspect.getsource(srv_mod)
        assert "set_mail_service" in src

    def test_admin_config_unknown_module_returns_false(self):
        """is_module_enabled with unknown key returns False."""
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig()
        assert cfg.is_module_enabled("nonexistent_module") is False

    def test_render_mailer_page_with_minimal_data(self):
        """Should not crash with minimal data."""
        from aquilia.admin.templates import render_mailer_page

        data = {
            "available": False,
            "enabled": False,
            "config": {},
            "providers": [],
            "provider_count": 0,
            "active_provider_count": 0,
            "default_from": "",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": False,
            "tracing_enabled": False,
            "is_healthy": False,
            "retry": {},
            "rate_limit": {},
            "security": {},
            "templates": {},
            "queue": {},
            "stats": {"total_sent": 0, "total_failed": 0, "total_queued": 0, "total_bounced": 0},
        }
        html = render_mailer_page(data)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_config_builder_mailer_survives_enable_all_disable_all(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        mods.enable_all()
        assert mods.to_dict()["mailer"] is True
        mods.disable_all()
        assert mods.to_dict()["mailer"] is False
        mods.enable_mailer()
        assert mods.to_dict()["mailer"] is True

    def test_multiple_enable_disable_cycles(self):
        from aquilia.config_builders import Integration

        mods = Integration.AdminModules()
        for _ in range(5):
            mods.enable_mailer()
            assert mods._mailer is True
            mods.disable_mailer()
            assert mods._mailer is False

    def test_workspace_roundtrip_full(self):
        """Full Workspace → to_dict → AdminConfig.from_dict round-trip."""
        from aquilia.config_builders import Workspace, Integration
        from aquilia.admin.site import AdminConfig

        ws = Workspace("test").integrate(
            Integration.admin(modules=Integration.AdminModules().enable_mailer().enable_storage().enable_tasks())
        )
        d = ws.to_dict()
        cfg = AdminConfig.from_dict(d["integrations"]["admin"])
        assert cfg.is_module_enabled("mailer") is True
        assert cfg.is_module_enabled("storage") is True
        assert cfg.is_module_enabled("tasks") is True
        assert cfg.is_module_enabled("mlops") is False


# ════════════════════════════════════════════════════════════════════════════
# 19. PROVIDER TYPE DISPLAY MAPPING
# ════════════════════════════════════════════════════════════════════════════


class TestProviderTypeDisplayMapping:
    """The type_display mapping in get_mailer_data covers all provider types."""

    def _make_site_with_provider_type(self, ptype):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None

        config = MagicMock()
        config.enabled = True
        config.default_from = "a@b.com"
        config.default_reply_to = None
        config.subject_prefix = ""
        config.preview_mode = False
        config.console_backend = False
        config.metrics_enabled = False
        config.tracing_enabled = False
        config.retry = None
        config.rate_limit = None
        config.security = None
        config.templates = None
        config.queue = None
        config.to_dict.return_value = {}

        provider = MagicMock()
        provider.name = f"{ptype}-test"
        provider.type = ptype
        provider.enabled = True
        provider.priority = 50
        provider.rate_limit_per_min = 600
        provider.host = "host"
        provider.port = 587
        provider.use_tls = True
        provider.use_ssl = False
        provider.timeout = 30
        config.providers = [provider]

        svc = MagicMock()
        svc.config = config
        svc.is_healthy.return_value = True
        svc.get_provider_names.return_value = [f"{ptype}-test"]

        site._mail_service = svc
        return site

    def test_smtp_display(self):
        site = self._make_site_with_provider_type("smtp")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "SMTP"

    def test_ses_display(self):
        site = self._make_site_with_provider_type("ses")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "AWS SES"

    def test_sendgrid_display(self):
        site = self._make_site_with_provider_type("sendgrid")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "SendGrid"

    def test_console_display(self):
        site = self._make_site_with_provider_type("console")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "Console (Dev)"

    def test_file_display(self):
        site = self._make_site_with_provider_type("file")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "File (Dev)"

    def test_unknown_type_title_cased(self):
        site = self._make_site_with_provider_type("custom_provider")
        data = site.get_mailer_data()
        assert data["providers"][0]["type_display"] == "Custom_Provider"


# ════════════════════════════════════════════════════════════════════════════
# 20. MAIL FAULT HIERARCHY
# ════════════════════════════════════════════════════════════════════════════


class TestMailFaultHierarchy:
    """Mail fault classes are properly structured."""

    def test_mail_fault_base(self):
        from aquilia.mail.faults import MailFault

        assert issubclass(MailFault, Exception)

    def test_send_fault_inherits_mail_fault(self):
        from aquilia.mail.faults import MailSendFault, MailFault

        assert issubclass(MailSendFault, MailFault)

    def test_config_fault_inherits_mail_fault(self):
        from aquilia.mail.faults import MailConfigFault, MailFault

        assert issubclass(MailConfigFault, MailFault)

    def test_template_fault_inherits_mail_fault(self):
        from aquilia.mail.faults import MailTemplateFault, MailFault

        assert issubclass(MailTemplateFault, MailFault)

    def test_suppressed_fault_exists(self):
        from aquilia.mail.faults import MailSuppressedFault

        assert MailSuppressedFault is not None

    def test_rate_limit_fault_exists(self):
        from aquilia.mail.faults import MailRateLimitFault

        assert MailRateLimitFault is not None

    def test_validation_fault_exists(self):
        from aquilia.mail.faults import MailValidationFault

        assert MailValidationFault is not None


# ════════════════════════════════════════════════════════════════════════════
# 21. SMOKE: FULL RENDERING PIPELINE
# ════════════════════════════════════════════════════════════════════════════


class TestFullRenderingPipelineSmoke:
    """End-to-end: site.get_mailer_data() → render_mailer_page() → HTML."""

    def _make_wired_site(self):
        from aquilia.admin.site import AdminSite

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._app_order = []
        site._site_title = "Test"
        site._initialised = True
        site._admin_config = None

        config = MagicMock()
        config.enabled = True
        config.default_from = "smoke@test.com"
        config.default_reply_to = None
        config.subject_prefix = "[SMOKE] "
        config.preview_mode = False
        config.console_backend = True
        config.metrics_enabled = True
        config.tracing_enabled = True

        provider = MagicMock()
        provider.name = "console"
        provider.type = "console"
        provider.enabled = True
        provider.priority = 50
        provider.rate_limit_per_min = 9999
        provider.host = None
        provider.port = None
        provider.use_tls = False
        provider.use_ssl = False
        provider.timeout = 10
        config.providers = [provider]

        config.retry = MagicMock(max_attempts=3, base_delay=1, max_delay=60, jitter=True)
        config.rate_limit = MagicMock(global_per_minute=100, per_domain_per_minute=10, per_provider_per_minute=None)
        config.security = MagicMock(
            dkim_enabled=False,
            dkim_domain=None,
            dkim_selector="aquilia",
            require_tls=True,
            pii_redaction_enabled=False,
            allowed_from_domains=[],
        )
        config.templates = MagicMock(template_dirs=["tmpl"], auto_escape=True, cache_compiled=True, strict_mode=False)
        config.queue = MagicMock(batch_size=10, poll_interval=0.5, dedupe_window_seconds=600, retention_days=7)
        config.to_dict.return_value = {"enabled": True}

        svc = MagicMock()
        svc.config = config
        svc.is_healthy.return_value = True
        svc.get_provider_names.return_value = ["console"]

        site._mail_service = svc
        return site

    def test_full_pipeline_produces_html(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert isinstance(html, str)
        assert len(html) > 1000

    def test_full_pipeline_has_provider_name(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert "console" in html

    def test_full_pipeline_has_subject_prefix(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert "[SMOKE]" in html

    def test_full_pipeline_has_send_test(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert "Send Test Email" in html

    def test_full_pipeline_has_health_check(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert "Health Check" in html

    def test_full_pipeline_has_javascript(self):
        from aquilia.admin.templates import render_mailer_page

        site = self._make_wired_site()
        data = site.get_mailer_data()
        html = render_mailer_page(data)
        assert "sendTestEmail" in html
        assert "runHealthCheck" in html
        assert "switchTab" in html
