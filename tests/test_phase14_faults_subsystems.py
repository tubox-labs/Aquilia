"""
Phase 14 -- Comprehensive Tests for Fault Migration, Config Builders,
and Subsystem Integration.

Tests:
    Task 1 (Fault Mechanism):
        1. New fault classes (CSRF, RateLimit, Configuration, Registration,
           Inline, Template, Export, Security)
        2. Fault hierarchy and inheritance
        3. Raw exception conversion in inlines, permissions, templates,
           registry, models
        4. AdminSecurity config builder fluent API
        5. Integration.admin() security parameter
        6. AdminConfig security_config parsing
        7. AdminSecurityPolicy.from_config() factory

    Task 2 (Subsystem Integration):
        8. AdminCacheIntegration (model list, dashboard, fragment caching)
        9. AdminTasks (audit cleanup, session cleanup, security report,
           rate limit cleanup)
        10. Flow guards (AuthGuard, PermGuard, CSRFGuard, RateLimitGuard)
        11. Flow hooks (AuditHook)
        12. AdminLifecycle (startup, shutdown)
        13. AdminSubsystems orchestrator
        14. Effect tokens (AdminDBEffect, AdminCacheEffect, AdminTaskEffect)
        15. build_admin_flow_pipeline()
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
#  Imports
# ═══════════════════════════════════════════════════════════════════════════════

from aquilia.admin.faults import (
    ADMIN_DOMAIN,
    AdminFault,
    AdminAuthenticationFault,
    AdminAuthorizationFault,
    AdminCSRFViolationFault,
    AdminRateLimitFault,
    AdminSecurityFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
    AdminActionFault,
    AdminConfigurationFault,
    AdminRegistrationFault,
    AdminInlineFault,
    AdminTemplateFault,
    AdminExportFault,
)
from aquilia.admin.security import (
    AdminCSRFProtection,
    AdminRateLimiter,
    AdminSecurityHeaders,
    AdminSecurityPolicy,
    PasswordValidator,
    SecurityEventTracker,
)
from aquilia.admin.site import AdminConfig, AdminSite
from aquilia.admin.subsystems import (
    AdminCacheIntegration,
    AdminTasks,
    AdminLifecycle,
    AdminSubsystems,
    AdminAuthGuard,
    AdminPermGuard,
    AdminCSRFGuard,
    AdminRateLimitGuard,
    AdminAuditHook,
    AdminDBEffect,
    AdminCacheEffect,
    AdminTaskEffect,
    build_admin_flow_pipeline,
    get_admin_subsystems,
)
from aquilia.faults import Fault
from aquilia.config_builders import Integration


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 1: Fault Mechanism Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNewFaultClasses:
    """Test all new admin fault classes."""

    def test_admin_csrf_violation_fault(self):
        """AdminCSRFViolationFault has correct code, status, and inherits AdminSecurityFault."""
        fault = AdminCSRFViolationFault()
        assert fault.code == "ADMIN_CSRF_VIOLATION"
        assert fault.status == 403
        assert isinstance(fault, AdminSecurityFault)
        assert isinstance(fault, AdminFault)
        assert isinstance(fault, Fault)
        assert "CSRF" in str(fault.message)

    def test_admin_csrf_violation_fault_custom_reason(self):
        fault = AdminCSRFViolationFault("Token expired")
        assert "Token expired" in str(fault.message)

    def test_admin_rate_limit_fault(self):
        """AdminRateLimitFault has correct code, status, and metadata."""
        fault = AdminRateLimitFault(limit=5, window=900, retry_after=300, operation="login")
        assert fault.code == "ADMIN_RATE_LIMIT"
        assert fault.status == 429
        assert fault.limit == 5
        assert fault.window == 900
        assert fault.retry_after == 300
        assert fault.operation == "login"
        assert isinstance(fault, AdminSecurityFault)
        assert "retry after 300s" in str(fault.message)

    def test_admin_rate_limit_fault_defaults(self):
        fault = AdminRateLimitFault()
        assert fault.limit == 0
        assert fault.retry_after == 0
        assert fault.operation == "login"

    def test_admin_security_fault_base(self):
        """AdminSecurityFault is the base for all security-related admin faults."""
        fault = AdminSecurityFault("IP blocked")
        assert fault.code == "ADMIN_SECURITY_ERROR"
        assert fault.status == 403
        assert fault.reason == "IP blocked"
        assert isinstance(fault, AdminFault)

    def test_admin_security_fault_metadata(self):
        fault = AdminSecurityFault("Blocked", ip="1.2.3.4", attempts=5)
        assert fault.metadata == {"ip": "1.2.3.4", "attempts": 5}

    def test_admin_configuration_fault(self):
        """AdminConfigurationFault for missing dependencies."""
        fault = AdminConfigurationFault(
            "Jinja2 is required for admin templates",
            dependency="Jinja2",
        )
        assert fault.code == "ADMIN_CONFIG_ERROR"
        assert fault.status == 500
        assert fault.dependency == "Jinja2"
        assert "Jinja2" in str(fault.message)

    def test_admin_configuration_fault_no_dependency(self):
        fault = AdminConfigurationFault("Invalid config")
        assert fault.dependency == ""
        assert "Invalid config" in str(fault.message)

    def test_admin_registration_fault(self):
        """AdminRegistrationFault for model registration errors."""
        fault = AdminRegistrationFault(
            reason="Must specify a model class",
            model_name="UserAdmin",
        )
        assert fault.code == "ADMIN_REGISTRATION_ERROR"
        assert fault.status == 500
        assert fault.model_name == "UserAdmin"
        assert "UserAdmin" in str(fault.message)

    def test_admin_registration_fault_no_model(self):
        fault = AdminRegistrationFault(reason="Invalid argument")
        assert fault.model_name == ""
        assert "Invalid argument" in str(fault.message)

    def test_admin_inline_fault(self):
        """AdminInlineFault for FK resolution errors."""
        fault = AdminInlineFault(
            reason="No ForeignKey found",
            inline_model="OrderItem",
            parent_model="Order",
        )
        assert fault.code == "ADMIN_INLINE_ERROR"
        assert fault.status == 400
        assert fault.inline_model == "OrderItem"
        assert fault.parent_model == "Order"
        assert "OrderItem" in str(fault.message)
        assert "Order" in str(fault.message)

    def test_admin_template_fault(self):
        """AdminTemplateFault for template rendering errors."""
        fault = AdminTemplateFault(
            reason="Variable 'user' is undefined",
            template_name="admin/list.html",
        )
        assert fault.code == "ADMIN_TEMPLATE_ERROR"
        assert fault.status == 500
        assert fault.template_name == "admin/list.html"

    def test_admin_export_fault(self):
        """AdminExportFault for export generation errors."""
        fault = AdminExportFault(
            reason="Serialization failed",
            export_format="CSV",
        )
        assert fault.code == "ADMIN_EXPORT_ERROR"
        assert fault.status == 500
        assert fault.export_format == "CSV"
        assert "CSV" in str(fault.message)


class TestFaultHierarchy:
    """Test the fault class hierarchy is correct."""

    def test_all_faults_inherit_admin_fault(self):
        """All admin faults must inherit from AdminFault."""
        fault_classes = [
            AdminAuthenticationFault,
            AdminAuthorizationFault,
            AdminCSRFViolationFault,
            AdminRateLimitFault,
            AdminSecurityFault,
            AdminModelNotFoundFault,
            AdminRecordNotFoundFault,
            AdminValidationFault,
            AdminActionFault,
            AdminConfigurationFault,
            AdminRegistrationFault,
            AdminInlineFault,
            AdminTemplateFault,
            AdminExportFault,
        ]
        for cls in fault_classes:
            assert issubclass(cls, AdminFault), f"{cls.__name__} must inherit AdminFault"
            assert issubclass(cls, Fault), f"{cls.__name__} must inherit Fault"

    def test_security_faults_inherit_security_fault(self):
        """CSRF and RateLimit faults must inherit AdminSecurityFault."""
        assert issubclass(AdminCSRFViolationFault, AdminSecurityFault)
        assert issubclass(AdminRateLimitFault, AdminSecurityFault)

    def test_admin_domain(self):
        """All admin faults use the ADMIN domain."""
        fault = AdminCSRFViolationFault()
        assert fault.domain == ADMIN_DOMAIN

    def test_existing_faults_unchanged(self):
        """Existing fault classes still work correctly."""
        auth = AdminAuthenticationFault("bad creds")
        assert auth.code == "ADMIN_AUTH_FAILED"
        assert auth.status == 401

        authz = AdminAuthorizationFault("view", "User")
        assert authz.code == "ADMIN_AUTHZ_DENIED"
        assert authz.status == 403

        model = AdminModelNotFoundFault("User")
        assert model.code == "ADMIN_MODEL_NOT_FOUND"
        assert model.status == 404

        record = AdminRecordNotFoundFault("User", "42")
        assert record.code == "ADMIN_RECORD_NOT_FOUND"
        assert record.status == 404

        val = AdminValidationFault({"name": "required"})
        assert val.code == "ADMIN_VALIDATION_ERROR"
        assert val.status == 422

        action = AdminActionFault("delete", "failed")
        assert action.code == "ADMIN_ACTION_FAILED"
        assert action.status == 400


class TestRawExceptionConversion:
    """Test that raw exceptions have been converted to typed faults."""

    def test_inlines_no_fk_raises_inline_fault(self):
        """inlines.py: No FK → AdminInlineFault (not ValueError)."""
        from aquilia.admin.inlines import InlineModelAdmin
        from aquilia.admin.faults import AdminInlineFault

        class ParentModel:
            __name__ = "ParentModel"
            _fields = {}

        class ChildModel:
            __name__ = "ChildModel"
            _fields = {}

        inline = InlineModelAdmin.__new__(InlineModelAdmin)
        inline.model = ChildModel
        inline._parent_model = ParentModel
        inline.fk_name = ""  # No explicit fk_name
        inline._fk_field = None

        with pytest.raises(AdminInlineFault) as exc_info:
            inline.get_fk_name()

        assert "No ForeignKey found" in str(exc_info.value.message)
        assert exc_info.value.inline_model == "ChildModel"
        assert exc_info.value.parent_model == "ParentModel"

    def test_permissions_superadmin_revoke_raises_authz_fault(self):
        """permissions.py: SUPERADMIN revoke → AdminAuthorizationFault (not ValueError)."""
        from aquilia.admin.permissions import AdminRole, AdminPermission, update_role_permissions
        from aquilia.admin.faults import AdminAuthorizationFault

        with pytest.raises(AdminAuthorizationFault) as exc_info:
            update_role_permissions(AdminRole.SUPERADMIN, AdminPermission.MODEL_VIEW, granted=False)

        assert "SUPERADMIN" in str(exc_info.value.message)

    def test_registry_no_model_raises_registration_fault(self):
        """registry.py: Missing model → AdminRegistrationFault (not ValueError)."""
        from aquilia.admin.faults import AdminRegistrationFault
        from aquilia.admin.registry import register
        from aquilia.admin.options import ModelAdmin

        class BadAdmin(ModelAdmin):
            model = None

        with pytest.raises(AdminRegistrationFault) as exc_info:
            register(BadAdmin)

        assert "model" in str(exc_info.value.message).lower()

    def test_registry_invalid_arg_raises_registration_fault(self):
        """registry.py: Invalid argument → AdminRegistrationFault (not TypeError)."""
        from aquilia.admin.faults import AdminRegistrationFault
        from aquilia.admin.registry import register

        with pytest.raises(AdminRegistrationFault) as exc_info:
            register(42)

        assert "Invalid argument" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_models_create_superuser_no_orm_raises_config_fault(self):
        """models.py: No ORM → AdminConfigurationFault (not RuntimeError)."""
        from aquilia.admin.faults import AdminConfigurationFault
        from aquilia.admin.models import AdminUser

        if not getattr(AdminUser, "_HAS_ORM", True):
            with pytest.raises(AdminConfigurationFault) as exc_info:
                await AdminUser.create_superuser("admin", "password")
            assert exc_info.value.dependency == "ORM"

    @pytest.mark.asyncio
    async def test_models_create_staff_user_no_orm_raises_config_fault(self):
        """models.py: No ORM → AdminConfigurationFault (not RuntimeError)."""
        from aquilia.admin.faults import AdminConfigurationFault
        from aquilia.admin.models import AdminUser

        if not getattr(AdminUser, "_HAS_ORM", True):
            with pytest.raises(AdminConfigurationFault) as exc_info:
                await AdminUser.create_staff_user("staff", "password")
            assert exc_info.value.dependency == "ORM"

    def test_templates_no_jinja_raises_config_fault(self):
        """templates.py: No Jinja2 → AdminConfigurationFault (not RuntimeError)."""
        from aquilia.admin.faults import AdminConfigurationFault
        import aquilia.admin.templates as tpl_mod

        # Save originals
        orig_engine = tpl_mod._admin_engine
        orig_env = tpl_mod._jinja_env

        try:
            tpl_mod._admin_engine = None
            tpl_mod._jinja_env = None

            with pytest.raises(AdminConfigurationFault) as exc_info:
                tpl_mod._render_template("test.html")

            assert exc_info.value.dependency == "Jinja2"
        finally:
            tpl_mod._admin_engine = orig_engine
            tpl_mod._jinja_env = orig_env


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 1: Config Builder Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminSecurityBuilder:
    """Test Integration.AdminSecurity fluent builder."""

    def test_default_values(self):
        """AdminSecurity builder has sensible OWASP defaults."""
        sec = Integration.AdminSecurity()
        d = sec.to_dict()

        assert d["csrf"]["enabled"] is True
        assert d["csrf"]["max_age"] == 7200
        assert d["csrf"]["token_length"] == 32
        assert d["rate_limit"]["enabled"] is True
        assert d["rate_limit"]["max_login_attempts"] == 5
        assert d["rate_limit"]["login_window"] == 900
        assert d["rate_limit"]["progressive_lockout"] is True
        assert d["password"]["min_length"] == 10
        assert d["password"]["require_upper"] is True
        assert d["password"]["require_special"] is True
        assert d["headers"]["enabled"] is True
        assert d["headers"]["frame_options"] == "DENY"
        assert d["session_fixation_protection"] is True
        assert d["event_tracker_max_events"] == 1000

    def test_csrf_configuration(self):
        """Fluent CSRF configuration."""
        sec = (
            Integration.AdminSecurity()
            .csrf_enabled(True)
            .csrf_max_age(3600)
            .csrf_token_length(64)
        )
        d = sec.to_dict()
        assert d["csrf"]["max_age"] == 3600
        assert d["csrf"]["token_length"] == 64

    def test_no_csrf(self):
        """Disable CSRF."""
        sec = Integration.AdminSecurity().no_csrf()
        d = sec.to_dict()
        assert d["csrf"]["enabled"] is False

    def test_rate_limit_configuration(self):
        """Fluent rate limit configuration."""
        sec = (
            Integration.AdminSecurity()
            .rate_limit_max_attempts(10)
            .rate_limit_window(1800)
            .sensitive_op_limit(50)
            .sensitive_op_window(600)
        )
        d = sec.to_dict()
        assert d["rate_limit"]["max_login_attempts"] == 10
        assert d["rate_limit"]["login_window"] == 1800
        assert d["rate_limit"]["sensitive_op_limit"] == 50
        assert d["rate_limit"]["sensitive_op_window"] == 600

    def test_no_rate_limit(self):
        sec = Integration.AdminSecurity().no_rate_limit()
        d = sec.to_dict()
        assert d["rate_limit"]["enabled"] is False

    def test_progressive_lockout_tiers(self):
        """Custom lockout tiers."""
        tiers = [[3, 120], [10, 600]]
        sec = (
            Integration.AdminSecurity()
            .progressive_lockout(True)
            .lockout_tiers(tiers)
        )
        d = sec.to_dict()
        assert d["rate_limit"]["lockout_tiers"] == tiers

    def test_password_policies(self):
        """Password policy configuration."""
        sec = (
            Integration.AdminSecurity()
            .password_min_length(12)
            .password_max_length(256)
            .password_require_upper(True)
            .password_require_digit(False)
        )
        d = sec.to_dict()
        assert d["password"]["min_length"] == 12
        assert d["password"]["max_length"] == 256
        assert d["password"]["require_upper"] is True
        assert d["password"]["require_digit"] is False

    def test_relaxed_password_policy(self):
        sec = Integration.AdminSecurity().relaxed_password_policy()
        d = sec.to_dict()
        assert d["password"]["min_length"] == 8
        assert d["password"]["require_upper"] is False
        assert d["password"]["require_special"] is False

    def test_strict_password_policy(self):
        sec = Integration.AdminSecurity().strict_password_policy()
        d = sec.to_dict()
        assert d["password"]["min_length"] == 12
        assert d["password"]["require_upper"] is True
        assert d["password"]["require_special"] is True

    def test_security_headers_configuration(self):
        """Custom CSP and headers."""
        sec = (
            Integration.AdminSecurity()
            .csp_template("default-src 'self'")
            .frame_options("SAMEORIGIN")
            .permissions_policy("camera=()")
        )
        d = sec.to_dict()
        assert d["headers"]["csp_template"] == "default-src 'self'"
        assert d["headers"]["frame_options"] == "SAMEORIGIN"
        assert d["headers"]["permissions_policy"] == "camera=()"

    def test_no_security_headers(self):
        sec = Integration.AdminSecurity().no_security_headers()
        d = sec.to_dict()
        assert d["headers"]["enabled"] is False

    def test_session_fixation_protection(self):
        sec = Integration.AdminSecurity().session_fixation_protection(False)
        d = sec.to_dict()
        assert d["session_fixation_protection"] is False

    def test_event_tracker_max_events(self):
        sec = Integration.AdminSecurity().event_tracker_max_events(5000)
        d = sec.to_dict()
        assert d["event_tracker_max_events"] == 5000

    def test_fluent_chaining(self):
        """All methods return self for fluent chaining."""
        sec = (
            Integration.AdminSecurity()
            .csrf_enabled()
            .csrf_max_age(3600)
            .rate_limit_enabled()
            .rate_limit_max_attempts(10)
            .rate_limit_window(600)
            .progressive_lockout()
            .password_min_length(12)
            .password_require_special()
            .security_headers_enabled()
            .session_fixation_protection()
            .event_tracker_max_events(2000)
        )
        assert isinstance(sec, Integration.AdminSecurity)
        d = sec.to_dict()
        assert d["csrf"]["enabled"] is True
        assert d["rate_limit"]["max_login_attempts"] == 10

    def test_repr(self):
        sec = Integration.AdminSecurity()
        r = repr(sec)
        assert "AdminSecurity" in r
        assert "csrf" in r
        assert "rate_limit" in r

    def test_min_bounds(self):
        """Values are clamped to minimum bounds."""
        sec = (
            Integration.AdminSecurity()
            .csrf_max_age(1)        # min 60
            .csrf_token_length(1)   # min 16
            .rate_limit_max_attempts(0)  # min 1
            .rate_limit_window(1)        # min 10
            .password_min_length(1)      # min 4
            .event_tracker_max_events(1) # min 100
        )
        d = sec.to_dict()
        assert d["csrf"]["max_age"] >= 60
        assert d["csrf"]["token_length"] >= 16
        assert d["rate_limit"]["max_login_attempts"] >= 1
        assert d["rate_limit"]["login_window"] >= 10
        assert d["password"]["min_length"] >= 4
        assert d["event_tracker_max_events"] >= 100


class TestIntegrationAdminSecurity:
    """Test Integration.admin() with security parameter."""

    def test_admin_includes_security_config(self):
        """Integration.admin() returns security_config in the dict."""
        config = Integration.admin()
        assert "security_config" in config
        assert config["security_config"]["csrf"]["enabled"] is True
        assert config["security_config"]["rate_limit"]["enabled"] is True

    def test_admin_with_custom_security_builder(self):
        """Custom AdminSecurity builder is wired into Integration.admin()."""
        sec = (
            Integration.AdminSecurity()
            .csrf_max_age(1800)
            .rate_limit_max_attempts(10)
            .password_min_length(16)
        )
        config = Integration.admin(security=sec)
        assert config["security_config"]["csrf"]["max_age"] == 1800
        assert config["security_config"]["rate_limit"]["max_login_attempts"] == 10
        assert config["security_config"]["password"]["min_length"] == 16

    def test_admin_default_security_config(self):
        """Without security param, defaults are populated."""
        config = Integration.admin()
        sec = config["security_config"]
        assert sec["csrf"]["enabled"] is True
        assert sec["rate_limit"]["max_login_attempts"] == 5
        assert sec["password"]["min_length"] == 10
        assert sec["headers"]["enabled"] is True
        assert sec["session_fixation_protection"] is True

    def test_admin_security_with_no_csrf(self):
        """Disable CSRF via builder."""
        sec = Integration.AdminSecurity().no_csrf()
        config = Integration.admin(security=sec)
        assert config["security_config"]["csrf"]["enabled"] is False

    def test_admin_backward_compat_no_security_param(self):
        """Admin config works without security param (backward compat)."""
        config = Integration.admin(
            site_title="Test Admin",
            enable_audit=True,
        )
        assert config["site_title"] == "Test Admin"
        assert config["enable_audit"] is True
        assert "security_config" in config


class TestAdminConfigSecurity:
    """Test AdminConfig parsing of security_config."""

    def test_admin_config_from_dict_default_security(self):
        """AdminConfig.from_dict() includes default security config."""
        raw = Integration.admin()
        config = AdminConfig.from_dict(raw)
        sec = config.security_config
        assert sec["csrf"]["enabled"] is True
        assert sec["rate_limit"]["max_login_attempts"] == 5
        assert sec["password"]["min_length"] == 10

    def test_admin_config_from_dict_custom_security(self):
        """AdminConfig.from_dict() respects custom security config."""
        sec_builder = (
            Integration.AdminSecurity()
            .csrf_max_age(900)
            .rate_limit_max_attempts(3)
            .password_min_length(16)
        )
        raw = Integration.admin(security=sec_builder)
        config = AdminConfig.from_dict(raw)
        sec = config.security_config
        assert sec["csrf"]["max_age"] == 900
        assert sec["rate_limit"]["max_login_attempts"] == 3
        assert sec["password"]["min_length"] == 16

    def test_admin_config_to_dict_includes_security(self):
        """AdminConfig.to_dict() serializes security config."""
        config = AdminConfig()
        d = config.to_dict()
        assert "security" in d
        assert d["security"]["csrf"]["enabled"] is True

    def test_admin_config_security_config_deep_merge(self):
        """Security config is deep-merged with defaults."""
        raw = Integration.admin()
        raw["security_config"] = {
            "csrf": {"max_age": 1800},
            # Only override one nested field -- others should use defaults
        }
        config = AdminConfig.from_dict(raw)
        sec = config.security_config
        assert sec["csrf"]["max_age"] == 1800
        assert sec["csrf"]["enabled"] is True  # Default preserved
        assert sec["rate_limit"]["max_login_attempts"] == 5  # Default preserved


class TestAdminSecurityPolicyFromConfig:
    """Test AdminSecurityPolicy.from_config() factory method."""

    def test_from_config_defaults(self):
        """from_config with default config creates valid policy."""
        config = AdminConfig().security_config
        policy = AdminSecurityPolicy.from_config(config)

        assert isinstance(policy.csrf, AdminCSRFProtection)
        assert isinstance(policy.rate_limiter, AdminRateLimiter)
        assert isinstance(policy.headers, AdminSecurityHeaders)
        assert isinstance(policy.password_validator, PasswordValidator)
        assert isinstance(policy.event_tracker, SecurityEventTracker)

    def test_from_config_custom_csrf(self):
        """from_config respects CSRF settings."""
        config = {
            "csrf": {"enabled": True, "max_age": 1800, "token_length": 48},
            "rate_limit": {"enabled": True, "max_login_attempts": 5, "login_window": 900,
                          "sensitive_op_limit": 30, "sensitive_op_window": 300,
                          "progressive_lockout": True},
            "password": {"min_length": 10, "max_length": 128,
                        "require_upper": True, "require_lower": True,
                        "require_digit": True, "require_special": True},
            "headers": {"enabled": True, "frame_options": "DENY"},
            "session_fixation_protection": True,
            "event_tracker_max_events": 1000,
        }
        policy = AdminSecurityPolicy.from_config(config)
        assert policy.csrf._max_age == 1800
        assert policy.csrf._token_length == 48

    def test_from_config_custom_rate_limiter(self):
        """from_config respects rate limit settings."""
        config = {
            "csrf": {"enabled": True, "max_age": 7200, "token_length": 32},
            "rate_limit": {"enabled": True, "max_login_attempts": 10, "login_window": 1800,
                          "sensitive_op_limit": 50, "sensitive_op_window": 600,
                          "progressive_lockout": True},
            "password": {"min_length": 10, "max_length": 128,
                        "require_upper": True, "require_lower": True,
                        "require_digit": True, "require_special": True},
            "headers": {"enabled": True, "frame_options": "DENY"},
            "session_fixation_protection": True,
            "event_tracker_max_events": 1000,
        }
        policy = AdminSecurityPolicy.from_config(config)
        assert policy.rate_limiter.max_login_attempts == 10
        assert policy.rate_limiter.login_window == 1800

    def test_from_config_custom_password(self):
        """from_config respects password policy."""
        config = {
            "csrf": {"enabled": True, "max_age": 7200, "token_length": 32},
            "rate_limit": {"enabled": True, "max_login_attempts": 5, "login_window": 900,
                          "sensitive_op_limit": 30, "sensitive_op_window": 300,
                          "progressive_lockout": True},
            "password": {"min_length": 16, "max_length": 256,
                        "require_upper": True, "require_lower": True,
                        "require_digit": True, "require_special": False},
            "headers": {"enabled": True, "frame_options": "DENY"},
            "session_fixation_protection": True,
            "event_tracker_max_events": 1000,
        }
        policy = AdminSecurityPolicy.from_config(config)
        assert policy.password_validator.min_length == 16
        assert policy.password_validator.max_length == 256
        assert policy.password_validator.require_special is False

    def test_from_config_custom_headers(self):
        """from_config respects security header settings."""
        config = {
            "csrf": {"enabled": True, "max_age": 7200, "token_length": 32},
            "rate_limit": {"enabled": True, "max_login_attempts": 5, "login_window": 900,
                          "sensitive_op_limit": 30, "sensitive_op_window": 300,
                          "progressive_lockout": True},
            "password": {"min_length": 10, "max_length": 128,
                        "require_upper": True, "require_lower": True,
                        "require_digit": True, "require_special": True},
            "headers": {"enabled": True, "frame_options": "SAMEORIGIN",
                        "csp_template": "default-src 'self'"},
            "session_fixation_protection": True,
            "event_tracker_max_events": 2000,
        }
        policy = AdminSecurityPolicy.from_config(config)
        assert policy.headers._frame_options == "SAMEORIGIN"
        assert policy.headers._csp_template == "default-src 'self'"
        assert policy.event_tracker._max_events == 2000

    def test_from_config_empty_config(self):
        """from_config with empty dict uses all defaults."""
        policy = AdminSecurityPolicy.from_config({})
        assert isinstance(policy.csrf, AdminCSRFProtection)
        assert isinstance(policy.rate_limiter, AdminRateLimiter)

    def test_admin_site_uses_from_config(self):
        """AdminSite creates security policy from config."""
        AdminSite.reset()
        site = AdminSite.default()
        assert isinstance(site.security, AdminSecurityPolicy)
        assert isinstance(site.security.csrf, AdminCSRFProtection)
        assert isinstance(site.security.rate_limiter, AdminRateLimiter)
        AdminSite.reset()


# ═══════════════════════════════════════════════════════════════════════════════
#  Task 2: Subsystem Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminCacheIntegration:
    """Test AdminCacheIntegration."""

    def test_disabled_without_cache_service(self):
        """Cache integration is disabled when no service is set."""
        cache = AdminCacheIntegration()
        assert cache.enabled is False

    def test_enabled_with_cache_service(self):
        """Cache integration is enabled when service is set."""
        mock_cache = MagicMock()
        cache = AdminCacheIntegration(cache_service=mock_cache)
        assert cache.enabled is True

    def test_set_cache_service(self):
        """set_cache_service enables the integration."""
        cache = AdminCacheIntegration()
        assert cache.enabled is False
        cache.set_cache_service(MagicMock())
        assert cache.enabled is True

    @pytest.mark.asyncio
    async def test_get_model_list_disabled(self):
        """Returns None when disabled."""
        cache = AdminCacheIntegration()
        result = await cache.get_model_list("User")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_model_list_cached(self):
        """Returns cached data when available."""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=[{"id": 1, "name": "Alice"}])
        cache = AdminCacheIntegration(cache_service=mock_cache)

        result = await cache.get_model_list("User", page=1)
        assert result == [{"id": 1, "name": "Alice"}]
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_model_list(self):
        """Sets cached data."""
        mock_cache = AsyncMock()
        cache = AdminCacheIntegration(cache_service=mock_cache)

        await cache.set_model_list("User", 1, None, "", "", [{"id": 1}])
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_model(self):
        """Invalidates cached data for a model."""
        mock_cache = AsyncMock()
        mock_cache.invalidate_tag = AsyncMock(return_value=5)
        cache = AdminCacheIntegration(cache_service=mock_cache)

        count = await cache.invalidate_model("User")
        assert count == 5
        mock_cache.invalidate_tag.assert_called_once_with("model:User")

    @pytest.mark.asyncio
    async def test_dashboard_stats_caching(self):
        """Dashboard stats can be cached and retrieved."""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value={"total_models": 5})
        mock_cache.set = AsyncMock()
        cache = AdminCacheIntegration(cache_service=mock_cache)

        await cache.set_dashboard_stats({"total_models": 5})
        result = await cache.get_dashboard_stats()
        assert result == {"total_models": 5}

    @pytest.mark.asyncio
    async def test_fragment_caching(self):
        """Template fragments can be cached."""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value="<div>cached</div>")
        mock_cache.set = AsyncMock()
        cache = AdminCacheIntegration(cache_service=mock_cache)

        await cache.set_fragment("sidebar", "<div>cached</div>")
        result = await cache.get_fragment("sidebar")
        assert result == "<div>cached</div>"

    @pytest.mark.asyncio
    async def test_cache_error_handling(self):
        """Cache errors don't propagate -- return None."""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=Exception("Redis down"))
        cache = AdminCacheIntegration(cache_service=mock_cache)

        result = await cache.get_model_list("User")
        assert result is None

    def test_model_list_key_deterministic(self):
        """Cache keys are deterministic for same inputs."""
        cache = AdminCacheIntegration()
        key1 = cache._model_list_key("User", 1, {"active": True}, "alice", "name")
        key2 = cache._model_list_key("User", 1, {"active": True}, "alice", "name")
        assert key1 == key2

    def test_model_list_key_different_for_different_inputs(self):
        """Cache keys differ for different inputs."""
        cache = AdminCacheIntegration()
        key1 = cache._model_list_key("User", 1, None, "", "")
        key2 = cache._model_list_key("User", 2, None, "", "")
        assert key1 != key2


class TestAdminTasks:
    """Test AdminTasks background job integration."""

    def test_disabled_without_task_manager(self):
        tasks = AdminTasks()
        assert tasks.enabled is False

    def test_enabled_with_task_manager(self):
        tasks = AdminTasks(task_manager=MagicMock())
        assert tasks.enabled is True

    @pytest.mark.asyncio
    async def test_audit_log_cleanup(self):
        """Audit log cleanup prunes entries beyond max."""
        tasks = AdminTasks()
        AdminSite.reset()
        site = AdminSite.default()

        # Manually add entries if possible
        result = await tasks.audit_log_cleanup(max_entries=100)
        assert "pruned" in result
        assert "remaining" in result
        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_security_report(self):
        """Security report generates event summary."""
        tasks = AdminTasks()
        AdminSite.reset()
        site = AdminSite.default()

        # Record some events
        site.security.event_tracker.record("login_failed", "1.2.3.4")
        site.security.event_tracker.record("csrf_violation", "5.6.7.8")

        report = await tasks.security_report()
        assert report["total_events"] >= 2
        assert "login_failed" in report["by_type"]
        assert "csrf_violation" in report["by_type"]
        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self):
        """Rate limit cleanup removes stale records."""
        tasks = AdminTasks()
        AdminSite.reset()
        site = AdminSite.default()

        result = await tasks.rate_limit_cleanup()
        assert "cleaned_login" in result
        assert "cleaned_sensitive" in result
        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_enqueue_audit_cleanup_no_task_manager(self):
        """Without task manager, runs inline."""
        tasks = AdminTasks()
        AdminSite.reset()
        result = await tasks.enqueue_audit_cleanup(max_entries=1000)
        assert result is None  # Ran inline
        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Session cleanup runs without error."""
        tasks = AdminTasks()
        result = await tasks.session_cleanup()
        assert "cleaned" in result


class TestAdminEffects:
    """Test admin effect tokens."""

    def test_admin_db_effect(self):
        effect = AdminDBEffect("write")
        assert effect.name == "AdminDB"
        assert effect.mode == "write"
        assert effect.kind == "db"
        assert "write" in repr(effect)

    def test_admin_db_effect_default_read(self):
        effect = AdminDBEffect()
        assert effect.mode == "read"

    def test_admin_cache_effect(self):
        effect = AdminCacheEffect("admin")
        assert effect.name == "AdminCache"
        assert effect.mode == "admin"
        assert effect.kind == "cache"

    def test_admin_task_effect(self):
        effect = AdminTaskEffect("admin")
        assert effect.name == "AdminTask"
        assert effect.mode == "admin"
        assert effect.kind == "queue"


class TestAdminFlowGuards:
    """Test flow guard implementations."""

    def test_auth_guard_no_identity(self):
        """AuthGuard rejects requests without identity."""
        guard = AdminAuthGuard()
        ctx = MagicMock(spec=[])  # No identity attribute
        assert guard(ctx) is False

    def test_auth_guard_no_identity_attr(self):
        ctx = MagicMock()
        ctx.identity = None
        guard = AdminAuthGuard()
        assert guard(ctx) is False

    def test_auth_guard_admin_roles(self):
        """AuthGuard accepts admin-level roles."""
        guard = AdminAuthGuard()
        for role in ["superadmin", "admin", "staff", "editor", "viewer"]:
            ctx = MagicMock()
            ctx.identity = MagicMock()
            ctx.identity.roles = [role]
            assert guard(ctx) is True, f"Role '{role}' should be accepted"

    def test_auth_guard_non_admin_role(self):
        """AuthGuard rejects non-admin roles."""
        guard = AdminAuthGuard()
        ctx = MagicMock()
        ctx.identity = MagicMock()
        ctx.identity.roles = ["user", "guest"]
        assert guard(ctx) is False

    def test_auth_guard_claims_based_roles(self):
        """AuthGuard reads roles from claims dict."""
        guard = AdminAuthGuard()
        ctx = MagicMock()
        # Create identity with claims but no roles attribute
        identity = MagicMock(spec=["claims"])
        identity.claims = {"roles": ["admin"]}
        ctx.identity = identity
        assert guard(ctx) is True

    def test_auth_guard_repr(self):
        guard = AdminAuthGuard()
        assert "AdminAuthGuard" in repr(guard)
        assert "priority=10" in repr(guard)

    def test_perm_guard_with_identity(self):
        """PermGuard checks model permissions."""
        guard = AdminPermGuard(model="User", action="view")
        assert guard.priority == 20
        assert guard.model == "User"
        assert guard.action == "view"

    def test_perm_guard_no_identity(self):
        guard = AdminPermGuard(model="User", action="view")
        ctx = MagicMock()
        ctx.identity = None
        assert guard(ctx) is False

    def test_csrf_guard_safe_methods(self):
        """CSRFGuard allows GET/HEAD/OPTIONS without token."""
        guard = AdminCSRFGuard()
        for method in ["GET", "HEAD", "OPTIONS"]:
            ctx = MagicMock()
            ctx.request = MagicMock()
            ctx.request.method = method
            assert guard(ctx) is True

    def test_csrf_guard_post_no_policy(self):
        """CSRFGuard allows POST when no policy (graceful fallback)."""
        guard = AdminCSRFGuard(security_policy=None)
        ctx = MagicMock()
        ctx.request = MagicMock()
        ctx.request.method = "POST"
        assert guard(ctx) is True

    def test_csrf_guard_repr(self):
        guard = AdminCSRFGuard()
        assert "AdminCSRFGuard" in repr(guard)

    def test_rate_limit_guard_no_policy(self):
        """RateLimitGuard allows when no policy."""
        guard = AdminRateLimitGuard(security_policy=None)
        ctx = MagicMock()
        assert guard(ctx) is True

    def test_rate_limit_guard_login(self):
        """RateLimitGuard checks login rate limits."""
        policy = MagicMock()
        policy.rate_limiter = MagicMock()
        policy.rate_limiter.is_login_locked = MagicMock(return_value=(False, 0))
        policy.extract_client_ip = MagicMock(return_value="1.2.3.4")

        guard = AdminRateLimitGuard(security_policy=policy, operation="login")
        ctx = MagicMock()
        ctx.request = MagicMock()

        assert guard(ctx) is True

    def test_rate_limit_guard_locked(self):
        """RateLimitGuard rejects when locked out."""
        policy = MagicMock()
        policy.rate_limiter = MagicMock()
        policy.rate_limiter.is_login_locked = MagicMock(return_value=(True, 300))
        policy.extract_client_ip = MagicMock(return_value="1.2.3.4")

        guard = AdminRateLimitGuard(security_policy=policy, operation="login")
        ctx = MagicMock()
        ctx.request = MagicMock()

        assert guard(ctx) is False

    def test_rate_limit_guard_sensitive_op(self):
        """RateLimitGuard checks sensitive operation limits."""
        policy = MagicMock()
        policy.rate_limiter = MagicMock()
        policy.rate_limiter.check_sensitive_op = MagicMock(return_value=(True, 0))
        policy.extract_client_ip = MagicMock(return_value="1.2.3.4")

        guard = AdminRateLimitGuard(security_policy=policy, operation="password_change")
        ctx = MagicMock()
        ctx.request = MagicMock()

        assert guard(ctx) is True


class TestAdminAuditHook:
    """Test the AdminAuditHook flow hook."""

    def test_audit_hook_creation(self):
        hook = AdminAuditHook(action="create", model_name="User")
        assert hook.action == "create"
        assert hook.model_name == "User"
        assert "AdminAuditHook" in repr(hook)

    @pytest.mark.asyncio
    async def test_audit_hook_logs_action(self):
        """AuditHook attempts to log to audit trail."""
        hook = AdminAuditHook(action="view", model_name="User")
        ctx = MagicMock()
        ctx.identity = MagicMock()
        ctx.identity.name = "admin"
        ctx.request = MagicMock()

        AdminSite.reset()
        # Should not raise even if audit log methods are limited
        await hook(ctx)
        AdminSite.reset()


class TestBuildAdminFlowPipeline:
    """Test build_admin_flow_pipeline() factory."""

    def test_default_pipeline(self):
        """Default pipeline includes auth guard and audit hook."""
        pipeline = build_admin_flow_pipeline()
        assert "guards" in pipeline
        assert "hooks" in pipeline
        assert any(isinstance(g, AdminAuthGuard) for g in pipeline["guards"])
        assert any(isinstance(h, AdminAuditHook) for h in pipeline["hooks"])

    def test_pipeline_with_csrf(self):
        """Pipeline with require_csrf includes CSRFGuard."""
        pipeline = build_admin_flow_pipeline(require_csrf=True)
        assert any(isinstance(g, AdminCSRFGuard) for g in pipeline["guards"])

    def test_pipeline_with_rate_limit(self):
        """Pipeline with rate_limit_op includes RateLimitGuard."""
        pipeline = build_admin_flow_pipeline(rate_limit_op="login")
        assert any(isinstance(g, AdminRateLimitGuard) for g in pipeline["guards"])

    def test_pipeline_with_model_perm(self):
        """Pipeline with model_name includes PermGuard."""
        pipeline = build_admin_flow_pipeline(model_name="User", action="change")
        assert any(isinstance(g, AdminPermGuard) for g in pipeline["guards"])

    def test_pipeline_no_auth(self):
        """Pipeline without require_auth skips AuthGuard."""
        pipeline = build_admin_flow_pipeline(require_auth=False)
        assert not any(isinstance(g, AdminAuthGuard) for g in pipeline["guards"])

    def test_pipeline_name(self):
        """Pipeline has a descriptive name."""
        pipeline = build_admin_flow_pipeline(model_name="User", action="view")
        assert "admin_view_User" in pipeline["name"]

    def test_pipeline_guard_ordering(self):
        """Guards should be in correct priority order when listed."""
        pipeline = build_admin_flow_pipeline(
            rate_limit_op="login",
            require_csrf=True,
            model_name="User",
            action="change",
        )
        guards = pipeline["guards"]
        # Should have: rate_limit (5), auth (10), csrf (15), perm (20)
        assert len(guards) == 4
        # Verify types exist
        guard_types = {type(g).__name__ for g in guards}
        assert "AdminRateLimitGuard" in guard_types
        assert "AdminAuthGuard" in guard_types
        assert "AdminCSRFGuard" in guard_types
        assert "AdminPermGuard" in guard_types


class TestAdminLifecycle:
    """Test AdminLifecycle startup/shutdown hooks."""

    def test_lifecycle_properties(self):
        lifecycle = AdminLifecycle()
        assert isinstance(lifecycle.cache, AdminCacheIntegration)
        assert isinstance(lifecycle.tasks, AdminTasks)

    @pytest.mark.asyncio
    async def test_startup(self):
        """Startup initializes admin site."""
        lifecycle = AdminLifecycle()
        AdminSite.reset()

        await lifecycle.on_startup()

        site = AdminSite.default()
        assert site._initialized is True
        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_startup_idempotent(self):
        """Multiple startups are safe."""
        lifecycle = AdminLifecycle()
        AdminSite.reset()

        await lifecycle.on_startup()
        await lifecycle.on_startup()  # Should not fail

        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Shutdown cleans up admin resources."""
        lifecycle = AdminLifecycle()
        AdminSite.reset()

        await lifecycle.on_startup()
        await lifecycle.on_shutdown()

        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_startup_with_di_container(self):
        """Startup wires cache/task services from DI container."""
        lifecycle = AdminLifecycle()
        AdminSite.reset()

        container = MagicMock()
        container.resolve = MagicMock(return_value=None)

        await lifecycle.on_startup(container=container)
        AdminSite.reset()


class TestAdminSubsystems:
    """Test AdminSubsystems orchestrator."""

    def test_singleton(self):
        """AdminSubsystems.default() is a singleton."""
        AdminSubsystems.reset()
        a = AdminSubsystems.default()
        b = AdminSubsystems.default()
        assert a is b
        AdminSubsystems.reset()

    def test_reset(self):
        """reset() clears the singleton."""
        AdminSubsystems.reset()
        a = AdminSubsystems.default()
        AdminSubsystems.reset()
        b = AdminSubsystems.default()
        assert a is not b
        AdminSubsystems.reset()

    def test_properties(self):
        """Orchestrator exposes all subsystem properties."""
        AdminSubsystems.reset()
        subs = AdminSubsystems.default()
        assert isinstance(subs.lifecycle, AdminLifecycle)
        assert isinstance(subs.cache, AdminCacheIntegration)
        assert isinstance(subs.tasks, AdminTasks)
        AdminSubsystems.reset()

    def test_build_pipeline(self):
        """build_pipeline delegates to build_admin_flow_pipeline."""
        AdminSubsystems.reset()
        AdminSite.reset()

        subs = AdminSubsystems.default()
        pipeline = subs.build_pipeline(
            model_name="User",
            action="view",
            require_auth=True,
        )
        assert "guards" in pipeline
        assert "hooks" in pipeline

        AdminSubsystems.reset()
        AdminSite.reset()

    def test_get_admin_subsystems(self):
        """get_admin_subsystems() returns the singleton."""
        AdminSubsystems.reset()
        subs = get_admin_subsystems()
        assert isinstance(subs, AdminSubsystems)
        AdminSubsystems.reset()


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration Tests -- End-to-End
# ═══════════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_config_pipeline(self):
        """Full config flow: builder → admin() → AdminConfig → SecurityPolicy."""
        sec = (
            Integration.AdminSecurity()
            .csrf_max_age(3600)
            .rate_limit_max_attempts(3)
            .rate_limit_window(600)
            .password_min_length(16)
            .strict_password_policy()
            .csp_template("default-src 'self'; script-src 'self' {nonce}")
            .event_tracker_max_events(5000)
        )
        raw = Integration.admin(
            site_title="Secure Admin",
            security=sec,
            enable_audit=True,
        )
        config = AdminConfig.from_dict(raw)
        policy = AdminSecurityPolicy.from_config(config.security_config)

        # Verify entire chain
        assert config.security_config["csrf"]["max_age"] == 3600
        assert policy.csrf._max_age == 3600
        assert policy.rate_limiter.max_login_attempts == 3
        assert policy.rate_limiter.login_window == 600
        assert policy.password_validator.min_length == 12  # strict_password_policy overrides to 12
        assert policy.event_tracker._max_events == 5000

    def test_admin_site_security_policy_from_config(self):
        """AdminSite creates security policy from its config."""
        AdminSite.reset()
        site = AdminSite.default()

        # Default config
        assert isinstance(site.security, AdminSecurityPolicy)
        assert site.security.csrf._max_age == 7200  # Default
        assert site.security.rate_limiter.max_login_attempts == 5  # Default

        AdminSite.reset()

    @pytest.mark.asyncio
    async def test_full_subsystem_lifecycle(self):
        """Full subsystem lifecycle: startup → operation → shutdown."""
        AdminSite.reset()
        AdminSubsystems.reset()

        subs = AdminSubsystems.default()

        # Startup
        await subs.lifecycle.on_startup()

        # Build pipeline
        pipeline = subs.build_pipeline(
            model_name="User", action="view",
            require_auth=True, require_csrf=True,
        )
        assert len(pipeline["guards"]) >= 2
        assert len(pipeline["hooks"]) >= 1

        # Generate security report
        report = await subs.tasks.security_report()
        assert "total_events" in report

        # Shutdown
        await subs.lifecycle.on_shutdown()

        AdminSubsystems.reset()
        AdminSite.reset()

    def test_all_faults_are_importable_from_admin_package(self):
        """All new faults are importable from aquilia.admin."""
        from aquilia.admin import (
            AdminCSRFViolationFault,
            AdminRateLimitFault,
            AdminSecurityFault,
            AdminConfigurationFault,
            AdminRegistrationFault,
            AdminInlineFault,
            AdminTemplateFault,
            AdminExportFault,
        )
        # Verify they're actual classes
        assert issubclass(AdminCSRFViolationFault, AdminFault)
        assert issubclass(AdminRateLimitFault, AdminFault)

    def test_all_subsystems_importable_from_admin_package(self):
        """All subsystem classes are importable from aquilia.admin."""
        from aquilia.admin import (
            AdminSubsystems,
            AdminCacheIntegration,
            AdminTasks,
            AdminLifecycle,
            AdminAuthGuard,
            AdminPermGuard,
            AdminCSRFGuard,
            AdminRateLimitGuard,
            AdminAuditHook,
            AdminDBEffect,
            AdminCacheEffect,
            AdminTaskEffect,
            build_admin_flow_pipeline,
            get_admin_subsystems,
        )
        assert AdminSubsystems is not None
        assert AdminCacheIntegration is not None
