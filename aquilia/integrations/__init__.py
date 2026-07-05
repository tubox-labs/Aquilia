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
The ``Integration`` class (``aquilia/integrations/integration.py``) provides
backward-compatible static builder methods that delegate to the typed
dataclasses.  Prefer the typed dataclasses directly for new code.
"""

# ── Protocol ──────────────────────────────────────────────────────────
# ── Legacy Integration (backward compat) ───────────────────────────────
from aquilia.integrations.integration import Integration as Integration
from aquilia.integrations._protocol import IntegrationConfig

# ── Admin ─────────────────────────────────────────────────────────────
from aquilia.integrations.admin import (
    AdminAudit,
    AdminContainers,
    AdminIntegration,
    AdminModules,
    AdminMonitoring,
    AdminPods,
    AdminSecurity,
    AdminSidebar,
)

# ── Auth ──────────────────────────────────────────────────────────────
from aquilia.integrations.auth import AuthIntegration

# ── Cache ─────────────────────────────────────────────────────────────
from aquilia.integrations.cache import CacheIntegration

# ── Database ──────────────────────────────────────────────────────────
from aquilia.integrations.database import DatabaseIntegration

# ── I18n ──────────────────────────────────────────────────────────────
from aquilia.integrations.i18n import I18nIntegration

# ── Logging ───────────────────────────────────────────────────────────
from aquilia.integrations.logging_cfg import LoggingIntegration

# ── Mail ──────────────────────────────────────────────────────────────
from aquilia.integrations.mail import (
    ConsoleProvider,
    FileProvider,
    MailAuth,
    MailIntegration,
    SendGridProvider,
    SesProvider,
    SmtpProvider,
)

# ── Middleware ────────────────────────────────────────────────────────
from aquilia.integrations.mw import (
    MiddlewareChain,
    MiddlewareEntry,
)

# ── OpenAPI ───────────────────────────────────────────────────────────
from aquilia.integrations.openapi import OpenAPIIntegration

# ── Render ────────────────────────────────────────────────────────────
from aquilia.integrations.render import RenderIntegration

# ── Security (CORS / CSP / Rate-Limit / CSRF) ────────────────────────
from aquilia.integrations.security import (
    CorsIntegration,
    CspIntegration,
    CsrfIntegration,
    RateLimitIntegration,
)

# ── Sessions ──────────────────────────────────────────────────────────
from aquilia.integrations.sessions import SessionIntegration

# ── Misc simple integrations ─────────────────────────────────────────
from aquilia.integrations.simple import (
    DiIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    RegistryIntegration,
    RoutingIntegration,
    SerializersIntegration,
)

# ── Static Files ──────────────────────────────────────────────────────
from aquilia.integrations.static import StaticFilesIntegration

# ── Storage ───────────────────────────────────────────────────────────
from aquilia.integrations.storage import StorageIntegration

# ── Tasks ─────────────────────────────────────────────────────────────
from aquilia.integrations.tasks import TasksIntegration

# ── Templates ─────────────────────────────────────────────────────────
from aquilia.integrations.templates import TemplatesIntegration

# ── Versioning ────────────────────────────────────────────────────────
from aquilia.integrations.versioning_cfg import VersioningIntegration

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
    # Integration (typed wrapper — delegates to typed dataclasses)
    "Integration",
]
