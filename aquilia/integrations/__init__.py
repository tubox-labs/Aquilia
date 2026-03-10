"""
Aquilia Integrations — Typed, validated configuration objects.

This package replaces the monolithic ``Integration`` class with a
composable set of typed dataclasses.  Each integration is a frozen
dataclass with ``__post_init__`` validation, IDE autocompletion,
and a ``.to_dict()`` method that produces the config dict consumed
by ``ConfigLoader`` / ``server.py``.

Quick start::

    from aquilia.integrations import (
        MailIntegration, MailAuth, SmtpProvider,
        DatabaseIntegration,
        AdminIntegration, AdminModules,
        CacheIntegration,
        VersioningIntegration,
    )

    workspace = (
        Workspace("myapp")
        .integrate(DatabaseIntegration(url="sqlite:///app.db"))
        .integrate(MailIntegration(
            default_from="noreply@app.com",
            auth=MailAuth.plain("user", password_env="SMTP_PASS"),
            providers=[SmtpProvider(host="smtp.app.com")],
        ))
        .integrate(AdminIntegration(
            site_title="My Admin",
            modules=AdminModules(monitoring=True, audit=True),
        ))
    )

Backward compatibility
----------------------
The legacy ``Integration`` class in ``config_builders.py`` still works.
Its static methods now delegate to these typed classes, so old code
(``Integration.mail(...)``, ``Integration.admin(...)``, etc.) keeps
working without changes.
"""

# ── Protocol ──────────────────────────────────────────────────────────
from aquilia.integrations._protocol import IntegrationConfig

# ── Auth ──────────────────────────────────────────────────────────────
from aquilia.integrations.auth import AuthIntegration

# ── Database ──────────────────────────────────────────────────────────
from aquilia.integrations.database import DatabaseIntegration

# ── Sessions ──────────────────────────────────────────────────────────
from aquilia.integrations.sessions import SessionIntegration

# ── Mail ──────────────────────────────────────────────────────────────
from aquilia.integrations.mail import (
    MailIntegration,
    MailAuth,
    SmtpProvider,
    SesProvider,
    SendGridProvider,
    ConsoleProvider,
    FileProvider,
)

# ── Admin ─────────────────────────────────────────────────────────────
from aquilia.integrations.admin import (
    AdminIntegration,
    AdminModules,
    AdminAudit,
    AdminMonitoring,
    AdminSidebar,
    AdminContainers,
    AdminPods,
    AdminSecurity,
)

# ── Middleware ────────────────────────────────────────────────────────
from aquilia.integrations.mw import (
    MiddlewareChain,
    MiddlewareEntry,
)

# ── Cache ─────────────────────────────────────────────────────────────
from aquilia.integrations.cache import CacheIntegration

# ── Tasks ─────────────────────────────────────────────────────────────
from aquilia.integrations.tasks import TasksIntegration

# ── Storage ───────────────────────────────────────────────────────────
from aquilia.integrations.storage import StorageIntegration

# ── Templates ─────────────────────────────────────────────────────────
from aquilia.integrations.templates import TemplatesIntegration

# ── Security (CORS / CSP / Rate-Limit / CSRF) ────────────────────────
from aquilia.integrations.security import (
    CorsIntegration,
    CspIntegration,
    RateLimitIntegration,
    CsrfIntegration,
)

# ── OpenAPI ───────────────────────────────────────────────────────────
from aquilia.integrations.openapi import OpenAPIIntegration

# ── I18n ──────────────────────────────────────────────────────────────
from aquilia.integrations.i18n import I18nIntegration

# ── MLOps ─────────────────────────────────────────────────────────────
from aquilia.integrations.mlops import MLOpsIntegration

# ── Versioning ────────────────────────────────────────────────────────
from aquilia.integrations.versioning_cfg import VersioningIntegration

# ── Render ────────────────────────────────────────────────────────────
from aquilia.integrations.render import RenderIntegration

# ── Logging ───────────────────────────────────────────────────────────
from aquilia.integrations.logging_cfg import LoggingIntegration

# ── Static Files ──────────────────────────────────────────────────────
from aquilia.integrations.static import StaticFilesIntegration

# ── Misc simple integrations ─────────────────────────────────────────
from aquilia.integrations.simple import (
    DiIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    RegistryIntegration,
    SerializersIntegration,
)


__all__ = [
    # Protocol
    "IntegrationConfig",
    # Core
    "AuthIntegration",
    "DatabaseIntegration",
    "SessionIntegration",
    # Mail
    "MailIntegration",
    "MailAuth",
    "SmtpProvider",
    "SesProvider",
    "SendGridProvider",
    "ConsoleProvider",
    "FileProvider",
    # Admin
    "AdminIntegration",
    "AdminModules",
    "AdminAudit",
    "AdminMonitoring",
    "AdminSidebar",
    "AdminContainers",
    "AdminPods",
    "AdminSecurity",
    # Middleware
    "MiddlewareChain",
    "MiddlewareEntry",
    # Subsystems
    "CacheIntegration",
    "TasksIntegration",
    "StorageIntegration",
    "TemplatesIntegration",
    # Security
    "CorsIntegration",
    "CspIntegration",
    "RateLimitIntegration",
    "CsrfIntegration",
    # Docs
    "OpenAPIIntegration",
    # i18n
    "I18nIntegration",
    # ML
    "MLOpsIntegration",
    # Versioning
    "VersioningIntegration",
    # Deployment
    "RenderIntegration",
    # Observability
    "LoggingIntegration",
    "StaticFilesIntegration",
    # Simple
    "DiIntegration",
    "RoutingIntegration",
    "FaultHandlingIntegration",
    "PatternsIntegration",
    "RegistryIntegration",
    "SerializersIntegration",
]
