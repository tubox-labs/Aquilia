"""
Tests for the new typed Integration configuration system.

These tests verify:
  1. Protocol compliance for all integration types
  2. Dataclass construction and defaults
  3. to_dict() round-trip correctness
  4. Validation (__post_init__) for constrained types
  5. AdminModules.with_() immutable partial override
  6. Legacy fluent method backward compat
  7. Workspace.integrate() accepting typed objects
  8. MiddlewareChain fluent API
  9. Factory classmethods (MailAuth, AdminModules, etc.)
  10. All integration types importable from aquilia top-level
"""

import pytest
from typing import Dict, Any


# ============================================================================
# 1. Top-level import smoke test
# ============================================================================


class TestIntegrationImports:
    """Verify every typed integration is importable from aquilia."""

    def test_import_from_aquilia(self):
        from aquilia import (
            IntegrationConfig,
            AuthIntegration,
            DatabaseIntegration,
            SessionIntegration,
            MailIntegration,
            MailAuth,
            SmtpProvider,
            SesProvider,
            SendGridProvider,
            ConsoleProvider,
            FileProvider,
            AdminIntegration,
            AdminModules,
            AdminAudit,
            AdminMonitoring,
            AdminSidebar,
            AdminContainers,
            AdminPods,
            AdminSecurity,
            MiddlewareChain,
            MiddlewareEntry,
            CacheIntegration,
            TasksIntegration,
            StorageIntegration,
            TemplatesIntegration,
            CorsIntegration,
            CspIntegration,
            RateLimitIntegration,
            CsrfIntegration,
            OpenAPIIntegration,
            I18nIntegration,
            MLOpsIntegration,
            VersioningIntegration,
            RenderIntegration,
            LoggingIntegration,
            StaticFilesIntegration,
            DiIntegration,
            RoutingIntegration,
            FaultHandlingIntegration,
            PatternsIntegration,
            RegistryIntegration,
            SerializersIntegration,
        )

        # All symbols resolve without error
        assert IntegrationConfig is not None

    def test_import_from_integrations_package(self):
        from aquilia.integrations import (
            IntegrationConfig,
            MailIntegration,
            AdminModules,
            CacheIntegration,
        )

        assert IntegrationConfig is not None

    def test_import_from_config_builders(self):
        from aquilia.config_builders import (
            MailIntegration,
            AdminModules,
            CacheIntegration,
            IntegrationConfig,
        )

        assert IntegrationConfig is not None


# ============================================================================
# 2. Protocol compliance
# ============================================================================


class TestProtocolCompliance:
    """Every typed integration must implement IntegrationConfig."""

    def _check_protocol(self, obj):
        from aquilia.integrations._protocol import IntegrationConfig

        assert isinstance(obj, IntegrationConfig), f"{type(obj).__name__} does not satisfy IntegrationConfig protocol"
        assert hasattr(obj, "_integration_type")
        assert hasattr(obj, "to_dict")
        d = obj.to_dict()
        assert isinstance(d, dict)
        assert "_integration_type" in d, f"{type(obj).__name__}.to_dict() missing _integration_type"
        return d

    def test_auth(self):
        from aquilia.integrations import AuthIntegration

        d = self._check_protocol(AuthIntegration())
        assert d["_integration_type"] == "auth"

    def test_database(self):
        from aquilia.integrations import DatabaseIntegration

        d = self._check_protocol(DatabaseIntegration())
        assert d["_integration_type"] == "database"

    def test_session(self):
        from aquilia.integrations import SessionIntegration

        d = self._check_protocol(SessionIntegration())
        assert d["_integration_type"] == "sessions"

    def test_mail(self):
        from aquilia.integrations import MailIntegration

        d = self._check_protocol(MailIntegration(default_from="a@b.com"))
        assert d["_integration_type"] == "mail"

    def test_admin(self):
        from aquilia.integrations import AdminIntegration

        d = self._check_protocol(AdminIntegration())
        assert d["_integration_type"] == "admin"

    def test_cache(self):
        from aquilia.integrations import CacheIntegration

        d = self._check_protocol(CacheIntegration())
        assert d["_integration_type"] == "cache"

    def test_tasks(self):
        from aquilia.integrations import TasksIntegration

        d = self._check_protocol(TasksIntegration())
        assert d["_integration_type"] == "tasks"

    def test_storage(self):
        from aquilia.integrations import StorageIntegration

        d = self._check_protocol(StorageIntegration())
        assert d["_integration_type"] == "storage"

    def test_templates(self):
        from aquilia.integrations import TemplatesIntegration

        d = self._check_protocol(TemplatesIntegration())
        assert d["_integration_type"] == "templates"

    def test_cors(self):
        from aquilia.integrations import CorsIntegration

        d = self._check_protocol(CorsIntegration())
        assert d["_integration_type"] == "cors"

    def test_csp(self):
        from aquilia.integrations import CspIntegration

        d = self._check_protocol(CspIntegration())
        assert d["_integration_type"] == "csp"

    def test_rate_limit(self):
        from aquilia.integrations import RateLimitIntegration

        d = self._check_protocol(RateLimitIntegration())
        assert d["_integration_type"] == "rate_limit"

    def test_csrf(self):
        from aquilia.integrations import CsrfIntegration

        d = self._check_protocol(CsrfIntegration())
        assert d["_integration_type"] == "csrf"

    def test_openapi(self):
        from aquilia.integrations import OpenAPIIntegration

        d = self._check_protocol(OpenAPIIntegration())
        assert d["_integration_type"] == "openapi"

    def test_i18n(self):
        from aquilia.integrations import I18nIntegration

        d = self._check_protocol(I18nIntegration())
        assert d["_integration_type"] == "i18n"

    def test_mlops(self):
        from aquilia.integrations import MLOpsIntegration

        d = self._check_protocol(MLOpsIntegration())
        assert d["_integration_type"] == "mlops"

    def test_versioning(self):
        from aquilia.integrations import VersioningIntegration

        d = self._check_protocol(VersioningIntegration())
        assert d["_integration_type"] == "versioning"

    def test_render(self):
        from aquilia.integrations import RenderIntegration

        d = self._check_protocol(RenderIntegration())
        assert d["_integration_type"] == "render"

    def test_logging(self):
        from aquilia.integrations import LoggingIntegration

        d = self._check_protocol(LoggingIntegration())
        assert d["_integration_type"] == "logging"

    def test_static_files(self):
        from aquilia.integrations import StaticFilesIntegration

        d = self._check_protocol(StaticFilesIntegration())
        assert d["_integration_type"] == "static_files"

    def test_di(self):
        from aquilia.integrations import DiIntegration

        d = self._check_protocol(DiIntegration())
        assert d["_integration_type"] == "dependency_injection"

    def test_routing(self):
        from aquilia.integrations import RoutingIntegration

        d = self._check_protocol(RoutingIntegration())
        assert d["_integration_type"] == "routing"

    def test_fault_handling(self):
        from aquilia.integrations import FaultHandlingIntegration

        d = self._check_protocol(FaultHandlingIntegration())
        assert d["_integration_type"] == "fault_handling"

    def test_patterns(self):
        from aquilia.integrations import PatternsIntegration

        d = self._check_protocol(PatternsIntegration())
        assert d["_integration_type"] == "patterns"

    def test_registry(self):
        from aquilia.integrations import RegistryIntegration

        d = self._check_protocol(RegistryIntegration())
        assert d["_integration_type"] == "registry"

    def test_serializers(self):
        from aquilia.integrations import SerializersIntegration

        d = self._check_protocol(SerializersIntegration())
        assert d["_integration_type"] == "serializers"


# ============================================================================
# 3. Dataclass construction & defaults
# ============================================================================


class TestDataclassConstruction:
    """Test that typed integrations construct with correct defaults."""

    def test_auth_defaults(self):
        from aquilia.integrations import AuthIntegration

        a = AuthIntegration()
        assert a.enabled is True
        assert a.access_token_ttl_minutes == 60
        assert a.refresh_token_ttl_days == 30
        assert a.algorithm == "HS256"
        assert a.store_type == "memory"

    def test_auth_custom(self):
        from aquilia.integrations import AuthIntegration

        a = AuthIntegration(access_token_ttl_minutes=120, algorithm="RS256")
        assert a.access_token_ttl_minutes == 120
        assert a.algorithm == "RS256"
        d = a.to_dict()
        assert d["tokens"]["access_token_ttl_minutes"] == 120
        assert d["tokens"]["algorithm"] == "RS256"

    def test_database_url(self):
        from aquilia.integrations import DatabaseIntegration

        db = DatabaseIntegration(url="sqlite:///test.db")
        assert db.url == "sqlite:///test.db"
        d = db.to_dict()
        assert d["url"] == "sqlite:///test.db"
        assert d["auto_create"] is True
        assert d["_integration_type"] == "database"

    def test_database_config_object(self):
        from aquilia.integrations import DatabaseIntegration

        class FakeConfig:
            def to_dict(self):
                return {"driver": "pg", "host": "localhost"}

        db = DatabaseIntegration(config=FakeConfig())
        d = db.to_dict()
        assert d["driver"] == "pg"
        assert d["_integration_type"] == "database"

    def test_session_defaults(self):
        from aquilia.integrations import SessionIntegration

        s = SessionIntegration()
        assert s.enabled is True

    def test_cache_defaults(self):
        from aquilia.integrations import CacheIntegration

        c = CacheIntegration()
        assert c.backend == "memory"
        assert c.max_size == 10000
        assert c.default_ttl == 300

    def test_tasks_defaults(self):
        from aquilia.integrations import TasksIntegration

        t = TasksIntegration()
        assert t.num_workers == 4
        assert t.backend == "memory"

    def test_storage_defaults(self):
        from aquilia.integrations import StorageIntegration

        s = StorageIntegration()
        assert s.default == "default"

    def test_cors_defaults(self):
        from aquilia.integrations import CorsIntegration

        c = CorsIntegration()
        assert c.enabled is True
        assert c.allow_origins == ["*"]

    def test_cors_custom(self):
        from aquilia.integrations import CorsIntegration

        c = CorsIntegration(
            allow_origins=["https://app.com"],
            allow_methods=["GET", "POST"],
            max_age=600,
        )
        d = c.to_dict()
        assert d["allow_origins"] == ["https://app.com"]
        assert d["allow_methods"] == ["GET", "POST"]
        assert d["max_age"] == 600

    def test_csp_defaults(self):
        from aquilia.integrations import CspIntegration

        c = CspIntegration()
        assert c.preset == "strict"
        assert c.nonce is True
        assert c.report_only is False

    def test_rate_limit_defaults(self):
        from aquilia.integrations import RateLimitIntegration

        r = RateLimitIntegration()
        assert r.limit == 100
        assert r.window == 60

    def test_csrf_defaults(self):
        from aquilia.integrations import CsrfIntegration

        c = CsrfIntegration()
        assert c.enabled is True

    def test_openapi_defaults(self):
        from aquilia.integrations import OpenAPIIntegration

        o = OpenAPIIntegration()
        assert o.title == "Aquilia API"
        assert o.version == "1.0.0"

    def test_i18n_defaults(self):
        from aquilia.integrations import I18nIntegration

        i = I18nIntegration()
        assert i.default_locale == "en"

    def test_mlops_defaults(self):
        from aquilia.integrations import MLOpsIntegration

        m = MLOpsIntegration()
        assert m.enabled is True
        assert m.registry_db == "registry.db"

    def test_versioning_defaults(self):
        from aquilia.integrations import VersioningIntegration

        v = VersioningIntegration()
        assert v.strategy == "header"
        assert v.header_name == "X-API-Version"

    def test_render_defaults(self):
        from aquilia.integrations import RenderIntegration

        r = RenderIntegration()
        assert r.enabled is True

    def test_logging_defaults(self):
        from aquilia.integrations import LoggingIntegration

        lg = LoggingIntegration()
        assert lg.level == "INFO"

    def test_static_files_defaults(self):
        from aquilia.integrations import StaticFilesIntegration

        s = StaticFilesIntegration()
        assert s.directories == {"/static": "static"}
        assert s.cache_max_age == 86400

    def test_di_defaults(self):
        from aquilia.integrations import DiIntegration

        d = DiIntegration()
        assert d.auto_wire is True

    def test_routing_defaults(self):
        from aquilia.integrations import RoutingIntegration

        r = RoutingIntegration()
        assert r.strict_matching is True

    def test_fault_handling_defaults(self):
        from aquilia.integrations import FaultHandlingIntegration

        f = FaultHandlingIntegration()
        assert f.default_strategy == "propagate"

    def test_patterns_defaults(self):
        from aquilia.integrations import PatternsIntegration

        p = PatternsIntegration()
        assert p.enabled is True

    def test_registry_defaults(self):
        from aquilia.integrations import RegistryIntegration

        r = RegistryIntegration()
        assert r.enabled is True

    def test_serializers_defaults(self):
        from aquilia.integrations import SerializersIntegration

        s = SerializersIntegration()
        assert s.enabled is True


# ============================================================================
# 4. Validation (__post_init__)
# ============================================================================


class TestValidation:
    """Test that constrained types reject invalid input."""

    def test_cache_invalid_backend(self):
        from aquilia.integrations import CacheIntegration

        with pytest.raises(ValueError, match="Invalid cache backend"):
            CacheIntegration(backend="mongodb")

    def test_cache_valid_backends(self):
        from aquilia.integrations import CacheIntegration

        for backend in ("memory", "redis", "composite", "null"):
            c = CacheIntegration(backend=backend)
            assert c.backend == backend

    def test_cache_invalid_eviction(self):
        from aquilia.integrations import CacheIntegration

        with pytest.raises(ValueError, match="Invalid eviction policy"):
            CacheIntegration(eviction_policy="clock")

    def test_cache_valid_eviction(self):
        from aquilia.integrations import CacheIntegration

        for policy in ("lru", "lfu", "ttl", "fifo", "random"):
            c = CacheIntegration(eviction_policy=policy)
            assert c.eviction_policy == policy

    def test_versioning_invalid_strategy(self):
        from aquilia.integrations import VersioningIntegration

        with pytest.raises(ValueError, match="Invalid versioning strategy"):
            VersioningIntegration(strategy="magic")

    def test_versioning_valid_strategies(self):
        from aquilia.integrations import VersioningIntegration

        for strat in ("url", "header", "query", "media_type", "channel", "composite"):
            v = VersioningIntegration(strategy=strat)
            assert v.strategy == strat

    def test_versioning_invalid_negotiation(self):
        from aquilia.integrations import VersioningIntegration

        with pytest.raises(ValueError, match="Invalid negotiation mode"):
            VersioningIntegration(negotiation_mode="guessing")

    def test_versioning_valid_negotiation(self):
        from aquilia.integrations import VersioningIntegration

        for mode in ("exact", "compatible", "best_match", "nearest", "latest"):
            v = VersioningIntegration(negotiation_mode=mode)
            assert v.negotiation_mode == mode


# ============================================================================
# 5. AdminModules
# ============================================================================


class TestAdminModules:
    """Test AdminModules dataclass, with_(), and factory classmethods."""

    def test_defaults(self):
        from aquilia.integrations import AdminModules

        m = AdminModules()
        assert m.dashboard is True
        assert m.orm is True
        assert m.monitoring is False
        assert m.audit is False
        assert m.containers is False

    def test_with_creates_copy(self):
        from aquilia.integrations import AdminModules

        m1 = AdminModules(monitoring=True)
        m2 = m1.with_(audit=True, containers=True)
        # Original unchanged
        assert m1.audit is False
        assert m1.containers is False
        # Copy has the overrides
        assert m2.monitoring is True
        assert m2.audit is True
        assert m2.containers is True

    def test_all_enabled(self):
        from aquilia.integrations import AdminModules

        m = AdminModules.all_enabled()
        assert m.dashboard is True
        assert m.monitoring is True
        assert m.audit is True
        assert m.containers is True
        assert m.pods is True
        assert m.tasks is True
        assert m.orm is True

    def test_all_disabled(self):
        from aquilia.integrations import AdminModules

        m = AdminModules.all_disabled()
        assert m.dashboard is False
        assert m.monitoring is False
        assert m.audit is False
        assert m.orm is False

    def test_to_dict(self):
        from aquilia.integrations import AdminModules

        m = AdminModules(monitoring=True)
        d = m.to_dict()
        assert d["monitoring"] is True
        assert d["dashboard"] is True
        assert d["audit"] is False

    def test_legacy_enable_disable(self):
        """Test backward-compatible fluent enable/disable methods."""
        from aquilia.integrations import AdminModules

        m = AdminModules()
        m.enable_monitoring()
        assert m.monitoring is True
        m.disable_monitoring()
        assert m.monitoring is False

    def test_legacy_enable_all(self):
        from aquilia.integrations import AdminModules

        m = AdminModules()
        m.enable_all()
        assert m.dashboard is True
        assert m.monitoring is True
        assert m.audit is True

    def test_legacy_disable_all(self):
        from aquilia.integrations import AdminModules

        m = AdminModules.all_enabled()
        m.disable_all()
        assert m.dashboard is False
        assert m.monitoring is False


class TestAdminSubclasses:
    """Test AdminAudit, AdminMonitoring, AdminSidebar, etc."""

    def test_admin_audit_defaults(self):
        from aquilia.integrations import AdminAudit

        a = AdminAudit()
        assert a.enabled is False
        assert a.max_entries == 10_000

    def test_admin_audit_to_dict(self):
        from aquilia.integrations import AdminAudit

        a = AdminAudit(max_entries=5000, log_views=False)
        d = a.to_dict()
        assert d["max_entries"] == 5000
        assert d["log_views"] is False

    def test_admin_monitoring_defaults(self):
        from aquilia.integrations import AdminMonitoring

        m = AdminMonitoring()
        assert m.enabled is False
        assert m.refresh_interval == 30

    def test_admin_sidebar_defaults(self):
        from aquilia.integrations import AdminSidebar

        s = AdminSidebar()
        assert s.overview is True
        assert s.data is True

    def test_admin_containers_defaults(self):
        from aquilia.integrations import AdminContainers

        c = AdminContainers()
        assert c.docker_host is None
        assert c.log_tail == 200

    def test_admin_pods_defaults(self):
        from aquilia.integrations import AdminPods

        p = AdminPods()
        assert p.namespace == "default"
        assert p.refresh_interval == 15

    def test_admin_security_defaults(self):
        from aquilia.integrations import AdminSecurity

        s = AdminSecurity()
        assert s.csrf_enabled is True
        assert s.rate_limit_enabled is True
        assert s.password_min_length == 10

    def test_admin_integration_full(self):
        from aquilia.integrations import (
            AdminIntegration,
            AdminModules,
            AdminAudit,
            AdminMonitoring,
            AdminSecurity,
        )

        admin = AdminIntegration(
            site_title="My Admin",
            modules=AdminModules(monitoring=True),
            audit=AdminAudit(max_entries=5000),
            monitoring=AdminMonitoring(enabled=True, refresh_interval=15),
            security=AdminSecurity(rate_limit_max_attempts=10),
        )
        d = admin.to_dict()
        assert d["_integration_type"] == "admin"
        assert d["site_title"] == "My Admin"
        assert d["modules"]["monitoring"] is True
        assert d["audit_config"]["max_entries"] == 5000
        assert d["monitoring_config"]["refresh_interval"] == 15
        assert d["security_config"]["rate_limit"]["max_login_attempts"] == 10


# ============================================================================
# 6. Mail system
# ============================================================================


class TestMailIntegration:
    """Test MailAuth factory classmethods and MailIntegration composition."""

    def test_mail_auth_plain(self):
        from aquilia.integrations import MailAuth

        auth = MailAuth.plain("user@mail.com", password_env="MAIL_PASS")
        assert auth.method == "plain"
        assert auth.username == "user@mail.com"
        assert auth.password_env == "MAIL_PASS"
        d = auth.to_dict()
        assert d["method"] == "plain"
        assert d["username"] == "user@mail.com"

    def test_mail_auth_api_key(self):
        from aquilia.integrations import MailAuth

        auth = MailAuth.api_key(env="SENDGRID_KEY")
        assert auth.method == "api_key"
        assert auth.api_key_env == "SENDGRID_KEY"

    def test_mail_auth_aws_ses(self):
        from aquilia.integrations import MailAuth

        auth = MailAuth.aws_ses(
            access_key_id="AKIA...",
            secret_access_key_env="AWS_SECRET",
            region="us-east-1",
        )
        assert auth.method == "aws_ses"
        assert auth.aws_region == "us-east-1"

    def test_mail_auth_oauth2(self):
        from aquilia.integrations import MailAuth

        auth = MailAuth.oauth2(
            client_id="abc",
            client_secret_env="SECRET",
            token_url="https://oauth2.example.com/token",
        )
        assert auth.method == "oauth2"
        assert auth.client_id == "abc"

    def test_mail_auth_anonymous(self):
        from aquilia.integrations import MailAuth

        auth = MailAuth.anonymous()
        assert auth.method == "none"

    def test_smtp_provider(self):
        from aquilia.integrations import SmtpProvider

        p = SmtpProvider(host="smtp.app.com", port=587, use_tls=True)
        d = p.to_dict()
        assert d["type"] == "smtp"
        assert d["host"] == "smtp.app.com"
        assert d["port"] == 587

    def test_ses_provider(self):
        from aquilia.integrations import SesProvider

        p = SesProvider(region="eu-west-1")
        d = p.to_dict()
        assert d["type"] == "ses"
        assert d["region"] == "eu-west-1"

    def test_sendgrid_provider(self):
        from aquilia.integrations import SendGridProvider, MailAuth

        p = SendGridProvider(auth=MailAuth.api_key(env="SG_KEY"))
        d = p.to_dict()
        assert d["type"] == "sendgrid"
        assert d["auth"]["method"] == "api_key"

    def test_console_provider(self):
        from aquilia.integrations import ConsoleProvider

        p = ConsoleProvider()
        d = p.to_dict()
        assert d["type"] == "console"

    def test_file_provider(self):
        from aquilia.integrations import FileProvider

        p = FileProvider(output_dir="/tmp/mail")
        d = p.to_dict()
        assert d["type"] == "file"
        assert d["output_dir"] == "/tmp/mail"

    def test_mail_integration_composition(self):
        from aquilia.integrations import MailIntegration, MailAuth, SmtpProvider

        mail = MailIntegration(
            default_from="noreply@app.com",
            auth=MailAuth.plain("user", password_env="PASS"),
            providers=[SmtpProvider(host="smtp.app.com")],
        )
        d = mail.to_dict()
        assert d["_integration_type"] == "mail"
        assert d["default_from"] == "noreply@app.com"
        assert d["auth"]["method"] == "plain"
        assert len(d["providers"]) == 1
        assert d["providers"][0]["type"] == "smtp"


# ============================================================================
# 7. Middleware chain
# ============================================================================


class TestMiddlewareChain:
    """Test the MiddlewareChain fluent builder."""

    def test_empty_chain(self):
        from aquilia.integrations import MiddlewareChain

        chain = MiddlewareChain()
        assert chain.to_list() == []

    def test_use_appends(self):
        from aquilia.integrations import MiddlewareChain

        chain = (
            MiddlewareChain()
            .use("aquilia.middleware.ExceptionMiddleware", priority=1)
            .use("aquilia.middleware.LoggingMiddleware", priority=10)
        )
        lst = chain.to_list()
        assert len(lst) == 2
        assert lst[0]["path"] == "aquilia.middleware.ExceptionMiddleware"
        assert lst[0]["priority"] == 1
        assert lst[1]["path"] == "aquilia.middleware.LoggingMiddleware"

    def test_middleware_entry_to_dict(self):
        from aquilia.integrations import MiddlewareEntry

        e = MiddlewareEntry(
            path="aquilia.middleware.CORSMiddleware",
            priority=5,
            scope="api",
        )
        d = e.to_dict()
        assert d["path"] == "aquilia.middleware.CORSMiddleware"
        assert d["priority"] == 5
        assert d["scope"] == "api"

    def test_chain_classmethod(self):
        from aquilia.integrations import MiddlewareChain

        chain = MiddlewareChain.chain()
        assert isinstance(chain, MiddlewareChain)
        assert len(chain) == 0

    def test_presets_exist(self):
        from aquilia.integrations import MiddlewareChain

        for preset in ("defaults", "production", "minimal"):
            if hasattr(MiddlewareChain, preset):
                result = getattr(MiddlewareChain, preset)()
                assert isinstance(result, MiddlewareChain)


# ============================================================================
# 8. Workspace.integrate() with typed objects
# ============================================================================


class TestWorkspaceTypedIntegrate:
    """Test Workspace.integrate() accepting IntegrationConfig objects."""

    def test_integrate_cache(self):
        from aquilia import Workspace, CacheIntegration

        ws = Workspace("test").integrate(CacheIntegration(backend="redis", max_size=500))
        d = ws.to_dict()
        assert d["integrations"]["cache"]["backend"] == "redis"
        assert d["integrations"]["cache"]["max_size"] == 500

    def test_integrate_mail(self):
        from aquilia import Workspace, MailIntegration, SmtpProvider

        ws = Workspace("test").integrate(
            MailIntegration(
                default_from="hi@app.com",
                providers=[SmtpProvider(host="smtp.app.com")],
            )
        )
        d = ws.to_dict()
        assert d["integrations"]["mail"]["default_from"] == "hi@app.com"

    def test_integrate_cors(self):
        from aquilia import Workspace, CorsIntegration

        ws = Workspace("test").integrate(
            CorsIntegration(
                allow_origins=["https://app.com"],
                max_age=600,
            )
        )
        d = ws.to_dict()
        assert d["security"]["cors"]["allow_origins"] == ["https://app.com"]

    def test_integrate_admin(self):
        from aquilia import Workspace, AdminIntegration, AdminModules

        ws = Workspace("test").integrate(
            AdminIntegration(
                site_title="Test Admin",
                modules=AdminModules(monitoring=True),
            )
        )
        d = ws.to_dict()
        assert d["integrations"]["admin"]["site_title"] == "Test Admin"

    def test_integrate_versioning(self):
        from aquilia import Workspace, VersioningIntegration

        ws = Workspace("test").integrate(
            VersioningIntegration(
                strategy="url",
                versions=["v1", "v2"],
                default_version="v1",
            )
        )
        d = ws.to_dict()
        vconf = d["integrations"]["versioning"]
        assert vconf["strategy"] == "url"
        assert vconf["versions"] == ["v1", "v2"]

    def test_integrate_multiple_typed(self):
        from aquilia import (
            Workspace,
            CacheIntegration,
            I18nIntegration,
            TasksIntegration,
        )

        ws = (
            Workspace("test")
            .integrate(CacheIntegration(backend="redis"))
            .integrate(I18nIntegration(default_locale="fr"))
            .integrate(TasksIntegration(num_workers=8))
        )
        d = ws.to_dict()
        assert d["integrations"]["cache"]["backend"] == "redis"
        assert d["integrations"]["i18n"]["default_locale"] == "fr"
        assert d["integrations"]["tasks"]["num_workers"] == 8

    def test_integrate_legacy_dict_still_works(self):
        from aquilia import Workspace, Integration

        ws = Workspace("test").integrate(Integration.cache(backend="memory", max_size=2000))
        d = ws.to_dict()
        assert d["integrations"]["cache"]["backend"] == "memory"
        assert d["integrations"]["cache"]["max_size"] == 2000

    def test_integrate_mixed_typed_and_legacy(self):
        from aquilia import Workspace, Integration, CacheIntegration, I18nIntegration

        ws = (
            Workspace("test")
            .integrate(CacheIntegration(backend="redis"))  # new
            .integrate(Integration.tasks(num_workers=4))  # legacy
            .integrate(I18nIntegration(default_locale="de"))  # new
        )
        d = ws.to_dict()
        assert d["integrations"]["cache"]["backend"] == "redis"
        assert d["integrations"]["tasks"]["num_workers"] == 4
        assert d["integrations"]["i18n"]["default_locale"] == "de"


# ============================================================================
# 9. to_dict() output format matches legacy Integration static methods
# ============================================================================


class TestToDictCompatibility:
    """Verify typed to_dict() produces compatible structure with legacy Integration methods."""

    def test_cache_compat(self):
        from aquilia import Integration
        from aquilia.integrations import CacheIntegration

        legacy = Integration.cache(backend="redis", max_size=500)
        typed = CacheIntegration(backend="redis", max_size=500).to_dict()
        assert typed["backend"] == legacy["backend"]
        assert typed["max_size"] == legacy["max_size"]
        assert typed["_integration_type"] == legacy["_integration_type"]

    def test_i18n_compat(self):
        from aquilia import Integration
        from aquilia.integrations import I18nIntegration

        legacy = Integration.i18n(default_locale="fr", available_locales=["fr", "en"])
        typed = I18nIntegration(default_locale="fr", available_locales=["fr", "en"]).to_dict()
        assert typed["default_locale"] == legacy["default_locale"]
        assert typed["available_locales"] == legacy["available_locales"]

    def test_tasks_compat(self):
        from aquilia import Integration
        from aquilia.integrations import TasksIntegration

        legacy = Integration.tasks(num_workers=8, backend="redis")
        typed = TasksIntegration(num_workers=8, backend="redis").to_dict()
        assert typed["num_workers"] == legacy["num_workers"]
        assert typed["backend"] == legacy["backend"]

    def test_cors_compat(self):
        from aquilia import Integration
        from aquilia.integrations import CorsIntegration

        legacy = Integration.cors(
            allow_origins=["https://app.com"],
            max_age=600,
        )
        typed = CorsIntegration(
            allow_origins=["https://app.com"],
            max_age=600,
        ).to_dict()
        assert typed["allow_origins"] == legacy["allow_origins"]
        assert typed["max_age"] == legacy["max_age"]

    def test_openapi_compat(self):
        from aquilia import Integration
        from aquilia.integrations import OpenAPIIntegration

        legacy = Integration.openapi(title="My API", version="2.0.0")
        typed = OpenAPIIntegration(title="My API", version="2.0.0").to_dict()
        assert typed["title"] == legacy["title"]
        assert typed["version"] == legacy["version"]


# ============================================================================
# 10. Templates builder
# ============================================================================


class TestTemplatesIntegration:
    """Test TemplatesIntegration and its builder."""

    def test_defaults(self):
        from aquilia.integrations import TemplatesIntegration

        t = TemplatesIntegration()
        assert t.search_paths == ["templates"]

    def test_custom_search_paths(self):
        from aquilia.integrations import TemplatesIntegration

        t = TemplatesIntegration(
            search_paths=["views", "layouts"],
            cache="filesystem",
            sandbox=False,
        )
        d = t.to_dict()
        assert d["search_paths"] == ["views", "layouts"]
        assert d["cache"] == "filesystem"
        assert d["sandbox"] is False

    def test_builder_api(self):
        from aquilia.integrations import TemplatesIntegration

        builder = TemplatesIntegration.builder()
        builder.source("custom_templates").cached("filesystem").secure()
        assert builder["search_paths"] == ["custom_templates"]
        assert builder["cache"] == "filesystem"


# ============================================================================
# 11. Simple integrations
# ============================================================================


class TestSimpleIntegrations:
    """Test the simple one-field integrations."""

    def test_di_custom(self):
        from aquilia.integrations import DiIntegration

        d = DiIntegration(auto_wire=False)
        out = d.to_dict()
        assert out["auto_wire"] is False

    def test_routing_custom(self):
        from aquilia.integrations import RoutingIntegration

        r = RoutingIntegration(strict_matching=False)
        out = r.to_dict()
        assert out["strict_matching"] is False

    def test_fault_handling_custom(self):
        from aquilia.integrations import FaultHandlingIntegration

        f = FaultHandlingIntegration(default_strategy="retry")
        out = f.to_dict()
        assert out["default_strategy"] == "retry"


# ============================================================================
# 12. Edge cases
# ============================================================================


class TestEdgeCases:
    """Edge case and regression tests."""

    def test_integration_type_preserved_in_dict(self):
        """Every to_dict() must include _integration_type."""
        from aquilia.integrations import (
            AuthIntegration,
            DatabaseIntegration,
            MailIntegration,
            CacheIntegration,
            TasksIntegration,
            StorageIntegration,
            CorsIntegration,
            CspIntegration,
            RateLimitIntegration,
            CsrfIntegration,
            OpenAPIIntegration,
            I18nIntegration,
            MLOpsIntegration,
            VersioningIntegration,
            RenderIntegration,
            LoggingIntegration,
            StaticFilesIntegration,
            DiIntegration,
            RoutingIntegration,
            FaultHandlingIntegration,
            PatternsIntegration,
            RegistryIntegration,
            SerializersIntegration,
            TemplatesIntegration,
        )

        for cls, kwargs in [
            (AuthIntegration, {}),
            (DatabaseIntegration, {}),
            (MailIntegration, {"default_from": "a@b.com"}),
            (CacheIntegration, {}),
            (TasksIntegration, {}),
            (StorageIntegration, {}),
            (CorsIntegration, {}),
            (CspIntegration, {}),
            (RateLimitIntegration, {}),
            (CsrfIntegration, {}),
            (OpenAPIIntegration, {}),
            (I18nIntegration, {}),
            (MLOpsIntegration, {}),
            (VersioningIntegration, {}),
            (RenderIntegration, {}),
            (LoggingIntegration, {}),
            (StaticFilesIntegration, {}),
            (DiIntegration, {}),
            (RoutingIntegration, {}),
            (FaultHandlingIntegration, {}),
            (PatternsIntegration, {}),
            (RegistryIntegration, {}),
            (SerializersIntegration, {}),
            (TemplatesIntegration, {}),
        ]:
            obj = cls(**kwargs)
            d = obj.to_dict()
            assert "_integration_type" in d, f"{cls.__name__} missing _integration_type"
            assert isinstance(d["_integration_type"], str)

    def test_admin_modules_immutability_via_with(self):
        """with_() must not mutate the original."""
        from aquilia.integrations import AdminModules

        orig = AdminModules(monitoring=True)
        copy = orig.with_(monitoring=False, audit=True)
        assert orig.monitoring is True
        assert orig.audit is False
        assert copy.monitoring is False
        assert copy.audit is True

    def test_workspace_to_dict_roundtrip(self):
        """Full workspace with typed integrations produces valid config dict."""
        from aquilia import Workspace
        from aquilia.integrations import (
            CacheIntegration,
            I18nIntegration,
            VersioningIntegration,
            CorsIntegration,
        )

        ws = (
            Workspace("roundtrip-test", version="1.0.0")
            .integrate(CacheIntegration(backend="redis", max_size=2000))
            .integrate(I18nIntegration(default_locale="ja", available_locales=["ja", "en"]))
            .integrate(
                VersioningIntegration(
                    strategy="url",
                    versions=["v1", "v2"],
                    default_version="v1",
                )
            )
            .integrate(CorsIntegration(allow_origins=["https://myapp.com"]))
        )
        d = ws.to_dict()
        assert d["workspace"]["name"] == "roundtrip-test"
        assert d["integrations"]["cache"]["backend"] == "redis"
        assert d["integrations"]["i18n"]["default_locale"] == "ja"
        assert d["integrations"]["versioning"]["strategy"] == "url"
        assert d["security"]["cors"]["allow_origins"] == ["https://myapp.com"]

    def test_mail_requires_default_from(self):
        """MailIntegration works with default_from."""
        from aquilia.integrations import MailIntegration

        m = MailIntegration(default_from="a@b.com")
        d = m.to_dict()
        assert d["default_from"] == "a@b.com"
