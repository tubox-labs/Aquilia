"""
Integration — typed integration configuration builder.

Provides a unified Integration class with typed static methods that delegate
to the new typed dataclass Integration objects. This replaces the legacy
monolithic _legacy.py implementation with a clean, maintainable design.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from aquilia.mail.auth import MailAuth as _MailAuthImpl
from aquilia.integrations.mail import SmtpProvider as _SmtpProvider
from aquilia.integrations.mail import SesProvider as _SesProvider
from aquilia.integrations.mail import SendGridProvider as _SendGridProvider
from aquilia.integrations.mail import ConsoleProvider as _ConsoleProvider
from aquilia.integrations.mail import FileProvider as _FileProvider


def _build_integration(cls: type, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Helper to instantiate a dataclass with only its declared fields and update with extras."""
    cls_fields = {f.name for f in dataclasses.fields(cls)}
    constructor_kwargs = {}
    extra_kwargs = {}
    for k, v in kwargs.items():
        if k in cls_fields:
            constructor_kwargs[k] = v
        else:
            extra_kwargs[k] = v
    obj = cls(*args, **constructor_kwargs)
    res = obj.to_dict()
    res.update(extra_kwargs)
    return res


class Integration:
    """Typed integration configuration builders.

    Each static method returns a typed integration dict compatible with
    Workspace.integrate(). Methods delegate to the appropriate typed
    dataclass implementation.

    For new code, prefer importing typed classes directly:
        from aquilia.integrations import MailIntegration, DatabaseIntegration, etc.
    """

    from aquilia.integrations.admin import (
        AdminModules,
        AdminAudit,
        AdminMonitoring,
        AdminSidebar,
        AdminSecurity,
    )

    # ── Mail auth and provider builders ──────────────────────────────
    MailAuth = _MailAuthImpl

    class MailProvider:
        """Typed mail provider builders."""
        SMTP = _SmtpProvider
        SES = _SesProvider
        SendGrid = _SendGridProvider
        Console = _ConsoleProvider
        File = _FileProvider

    # ── Integration static methods ────────────────────────────────────

    @staticmethod
    def mail(
        default_from: str = "noreply@localhost",
        default_reply_to: str | None = None,
        subject_prefix: str = "",
        providers: list | None = None,
        auth: Any | None = None,
        console_backend: bool = False,
        preview_mode: bool = False,
        template_dirs: list[str] | None = None,
        retry_max_attempts: int = 5,
        retry_base_delay: float = 1.0,
        rate_limit_global: int = 1000,
        rate_limit_per_domain: int = 100,
        dkim_enabled: bool = False,
        dkim_domain: str | None = None,
        dkim_selector: str = "aquilia",
        require_tls: bool = True,
        pii_redaction: bool = False,
        metrics_enabled: bool = True,
        tracing_enabled: bool = False,
        enabled: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Configure mail subsystem. Returns config dict for Workspace.integrate()."""
        from aquilia.integrations.mail import MailIntegration

        kwargs.update({
            "default_from": default_from,
            "default_reply_to": default_reply_to,
            "subject_prefix": subject_prefix,
            "providers": providers or [],
            "auth": auth,
            "console_backend": console_backend,
            "preview_mode": preview_mode,
            "template_dirs": template_dirs or ["mail_templates"],
            "retry_max_attempts": retry_max_attempts,
            "retry_base_delay": retry_base_delay,
            "rate_limit_global": rate_limit_global,
            "rate_limit_per_domain": rate_limit_per_domain,
            "dkim_enabled": dkim_enabled,
            "dkim_domain": dkim_domain,
            "dkim_selector": dkim_selector,
            "require_tls": require_tls,
            "pii_redaction": pii_redaction,
            "metrics_enabled": metrics_enabled,
            "tracing_enabled": tracing_enabled,
            "enabled": enabled,
        })
        return _build_integration(MailIntegration, **kwargs)

    @staticmethod
    def database(
        url: str = "sqlite:///db.sqlite3",
        auto_create: bool = True,
        scan_dirs: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Configure database integration."""
        from aquilia.integrations.database import DatabaseIntegration
        kwargs.update({
            "url": url,
            "auto_create": auto_create,
            "scan_dirs": scan_dirs or ["."],
        })
        return _build_integration(DatabaseIntegration, **kwargs)

    @staticmethod
    def cache(
        backend: str = "memory",
        default_ttl: int = 300,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Configure cache integration."""
        from aquilia.integrations.cache import CacheIntegration
        kwargs.update({
            "backend": backend,
            "default_ttl": default_ttl,
        })
        return _build_integration(CacheIntegration, **kwargs)

    @staticmethod
    def di(auto_wire: bool = True, **kwargs: Any) -> dict[str, Any]:
        """Configure dependency injection."""
        from aquilia.integrations.simple import DiIntegration
        kwargs.update({"auto_wire": auto_wire})
        return _build_integration(DiIntegration, **kwargs)

    @staticmethod
    def routing(strict_matching: bool = True, **kwargs: Any) -> dict[str, Any]:
        """Configure routing."""
        from aquilia.integrations.simple import RoutingIntegration
        kwargs.update({"strict_matching": strict_matching})
        return _build_integration(RoutingIntegration, **kwargs)

    @staticmethod
    def fault_handling(default_strategy: str = "propagate", **kwargs: Any) -> dict[str, Any]:
        """Configure fault handling."""
        from aquilia.integrations.simple import FaultHandlingIntegration
        kwargs.update({"default_strategy": default_strategy})
        return _build_integration(FaultHandlingIntegration, **kwargs)

    @staticmethod
    def tasks(
        backend: str = "memory",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Configure background tasks."""
        from aquilia.integrations.tasks import TasksIntegration
        kwargs.update({"backend": backend})
        return _build_integration(TasksIntegration, **kwargs)

    @staticmethod
    def storage(**kwargs: Any) -> dict[str, Any]:
        """Configure storage."""
        from aquilia.integrations.storage import StorageIntegration
        return _build_integration(StorageIntegration, **kwargs)

    @staticmethod
    def templates(**kwargs: Any) -> dict[str, Any]:
        """Configure templates."""
        from aquilia.integrations.templates import TemplatesIntegration
        return _build_integration(TemplatesIntegration, **kwargs)

    @staticmethod
    def cors(**kwargs: Any) -> dict[str, Any]:
        """Configure CORS."""
        from aquilia.integrations.security import CorsIntegration
        return _build_integration(CorsIntegration, **kwargs)

    @staticmethod
    def csp(**kwargs: Any) -> dict[str, Any]:
        """Configure CSP."""
        from aquilia.integrations.security import CspIntegration
        return _build_integration(CspIntegration, **kwargs)

    @staticmethod
    def rate_limit(**kwargs: Any) -> dict[str, Any]:
        """Configure rate limiting."""
        from aquilia.integrations.security import RateLimitIntegration
        return _build_integration(RateLimitIntegration, **kwargs)

    @staticmethod
    def csrf(**kwargs: Any) -> dict[str, Any]:
        """Configure CSRF protection."""
        from aquilia.integrations.security import CsrfIntegration
        return _build_integration(CsrfIntegration, **kwargs)

    @staticmethod
    def static_files(**kwargs: Any) -> dict[str, Any]:
        """Configure static file serving."""
        from aquilia.integrations.static import StaticFilesIntegration
        return _build_integration(StaticFilesIntegration, **kwargs)

    @staticmethod
    def openapi(**kwargs: Any) -> dict[str, Any]:
        """Configure OpenAPI/Swagger."""
        from aquilia.integrations.openapi import OpenAPIIntegration
        return _build_integration(OpenAPIIntegration, **kwargs)

    @staticmethod
    def i18n(**kwargs: Any) -> dict[str, Any]:
        """Configure internationalization."""
        from aquilia.integrations.i18n import I18nIntegration
        return _build_integration(I18nIntegration, **kwargs)

    @staticmethod
    def admin(**kwargs: Any) -> dict[str, Any]:
        """Configure admin panel."""
        from aquilia.integrations.admin import (
            AdminIntegration,
            AdminModules,
            AdminAudit,
            AdminMonitoring,
            AdminSidebar,
        )

        # 1. Parse modules
        modules = kwargs.get("modules")
        has_explicit_modules = modules is not None
        if modules is None:
            modules = AdminModules()
        else:
            # Clone if it is already an instance to avoid mutation
            modules = AdminModules(**modules.to_dict())

        if not has_explicit_modules:
            # Support enable/disable flat properties for modules
            module_fields = {f.name for f in dataclasses.fields(AdminModules)}
            for name in list(module_fields):
                # Check for enable_<name>
                enable_key = f"enable_{name}"
                if enable_key in kwargs:
                    setattr(modules, name, bool(kwargs.pop(enable_key)))
                # Check for disable_<name>
                disable_key = f"disable_{name}"
                if disable_key in kwargs:
                    setattr(modules, name, not bool(kwargs.pop(disable_key)))
                # Check for direct <name>
                if name in kwargs and name not in ("audit", "monitoring", "sidebar", "containers", "pods", "security"):
                    setattr(modules, name, bool(kwargs.pop(name)))

        # 2. Parse audit
        audit = kwargs.get("audit")
        has_explicit_audit = audit is not None
        if audit is None:
            audit = AdminAudit()
        else:
            audit = AdminAudit(**audit.to_dict())

        # If modules.audit is True, audit should also be enabled
        if modules.audit:
            audit.enabled = True

        if not has_explicit_audit and not has_explicit_modules:
            if "enable_audit" in kwargs:
                val = bool(kwargs.pop("enable_audit"))
                audit.enabled = val
                modules.audit = val
            if "audit_max_entries" in kwargs:
                audit.max_entries = kwargs.pop("audit_max_entries")
            if "audit_log_logins" in kwargs:
                audit.log_logins = bool(kwargs.pop("audit_log_logins"))
            if "audit_log_views" in kwargs:
                audit.log_views = bool(kwargs.pop("audit_log_views"))
            if "audit_log_searches" in kwargs:
                audit.log_searches = bool(kwargs.pop("audit_log_searches"))
            if "audit_excluded_actions" in kwargs:
                audit.excluded_actions = list(kwargs.pop("audit_excluded_actions"))
        else:
            # Clean up potential flat parameters so they don't get passed to AdminIntegration constructor
            kwargs.pop("enable_audit", None)
            kwargs.pop("audit_max_entries", None)
            kwargs.pop("audit_log_logins", None)
            kwargs.pop("audit_log_views", None)
            kwargs.pop("audit_log_searches", None)
            kwargs.pop("audit_excluded_actions", None)

        # 3. Parse monitoring
        monitoring = kwargs.get("monitoring")
        has_explicit_monitoring = monitoring is not None
        if monitoring is None:
            monitoring = AdminMonitoring()
        else:
            monitoring = AdminMonitoring(**monitoring.to_dict())

        # If modules.monitoring is True, monitoring should also be enabled
        if modules.monitoring:
            monitoring.enabled = True

        if not has_explicit_monitoring and not has_explicit_modules:
            if "enable_monitoring" in kwargs:
                val = bool(kwargs.pop("enable_monitoring"))
                monitoring.enabled = val
                modules.monitoring = val
            if "monitoring_metrics" in kwargs:
                monitoring.metrics = list(kwargs.pop("monitoring_metrics"))
            if "monitoring_refresh_interval" in kwargs:
                monitoring.refresh_interval = int(kwargs.pop("monitoring_refresh_interval"))
        else:
            # Clean up potential flat parameters
            kwargs.pop("enable_monitoring", None)
            kwargs.pop("monitoring_metrics", None)
            kwargs.pop("monitoring_refresh_interval", None)

        # 4. Parse sidebar
        sidebar = kwargs.get("sidebar")
        if sidebar is None:
            sidebar = AdminSidebar()
            if "sidebar_sections" in kwargs:
                sections = kwargs.pop("sidebar_sections")
                if isinstance(sections, dict):
                    for k, v in sections.items():
                        if hasattr(sidebar, k):
                            setattr(sidebar, k, bool(v))
        else:
            sidebar = AdminSidebar(**sidebar.to_dict())
            kwargs.pop("sidebar_sections", None)

        # Update kwargs with the parsed sub-config objects
        kwargs["modules"] = modules
        kwargs["audit"] = audit
        kwargs["monitoring"] = monitoring
        kwargs["sidebar"] = sidebar

        return _build_integration(AdminIntegration, **kwargs)

    @staticmethod
    def versioning(**kwargs: Any) -> dict[str, Any]:
        """Configure API versioning."""
        from aquilia.integrations.versioning_cfg import VersioningIntegration
        return _build_integration(VersioningIntegration, **kwargs)

    @staticmethod
    def logging(**kwargs: Any) -> dict[str, Any]:
        """Configure logging."""
        from aquilia.integrations.logging_cfg import LoggingIntegration
        return _build_integration(LoggingIntegration, **kwargs)

    @staticmethod
    def render(**kwargs: Any) -> dict[str, Any]:
        """Configure deployment provider."""
        from aquilia.integrations.render import RenderIntegration
        return _build_integration(RenderIntegration, **kwargs)

    @staticmethod
    def auth(**kwargs: Any) -> dict[str, Any]:
        """Configure authentication."""
        from aquilia.integrations.auth import AuthIntegration
        return _build_integration(AuthIntegration, **kwargs)

    @staticmethod
    def sessions(**kwargs: Any) -> dict[str, Any]:
        """Configure sessions."""
        from aquilia.integrations.sessions import SessionIntegration
        return _build_integration(SessionIntegration, **kwargs)

    @staticmethod
    def middleware_chain(entries: list | None = None, **kwargs: Any) -> dict[str, Any]:
        """Configure middleware chain."""
        from aquilia.integrations.mw import MiddlewareChain
        kwargs.update({"entries": entries or []})
        return _build_integration(MiddlewareChain, **kwargs)

    @staticmethod
    def patterns(**kwargs: Any) -> dict[str, Any]:
        """Configure patterns."""
        from aquilia.integrations.simple import PatternsIntegration
        return _build_integration(PatternsIntegration, **kwargs)

    @staticmethod
    def serializers(**kwargs: Any) -> dict[str, Any]:
        """Configure serializers."""
        from aquilia.integrations.simple import SerializersIntegration
        return _build_integration(SerializersIntegration, **kwargs)
