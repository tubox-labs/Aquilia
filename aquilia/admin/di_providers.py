"""
AquilAdmin -- DI Providers.

Dependency injection providers for admin subsystem components.
Registers AdminSite, AdminController, and AdminAuditLog as
injectable services so other parts of the application can depend
on admin functionality without importing singletons directly.

Usage with DI container::

    from aquilia.di import Container
    from aquilia.admin.di_providers import register_admin_providers

    container = Container()
    register_admin_providers(container)

    # Later, resolve the admin site:
    site = container.resolve(AdminSite)

Usage with DI decorators (auto-registered)::

    from aquilia.admin.di_providers import AdminSiteProvider

    class MyService:
        def __init__(self, admin_site: AdminSite):
            self.admin = admin_site
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from .site import AdminSite
from .audit import AdminAuditLog, ModelBackedAuditLog
from .controller import AdminController

if TYPE_CHECKING:
    from aquilia.di.core import Container

logger = logging.getLogger("aquilia.admin.di")


# ── Provider functions ───────────────────────────────────────────────────────


def provide_admin_site() -> AdminSite:
    """Provide the default AdminSite singleton."""
    return AdminSite.default()


def provide_admin_controller(site: Optional[AdminSite] = None) -> AdminController:
    """Provide an AdminController bound to the given or default site."""
    return AdminController(site=site or AdminSite.default())


def provide_audit_log(site: Optional[AdminSite] = None) -> AdminAuditLog:
    """Provide the audit log from the current AdminSite."""
    s = site or AdminSite.default()
    return s.audit_log


def provide_model_backed_audit_log() -> ModelBackedAuditLog:
    """Provide a ModelBackedAuditLog instance."""
    return ModelBackedAuditLog()


# ── Container registration ───────────────────────────────────────────────────


def register_admin_providers(container: "Container") -> None:
    """
    Register all admin DI providers with the given container.

    This enables resolution of:
    - ``AdminSite`` -- the singleton admin registry
    - ``AdminController`` -- the admin route controller
    - ``AdminAuditLog`` -- the audit log instance
    - ``ModelBackedAuditLog`` -- DB-backed audit log

    Call this during application bootstrap, typically in the
    ``Integration.admin()`` setup or workspace configuration.
    """
    try:
        from aquilia.di.providers import FactoryProvider, ValueProvider
        from aquilia.di.scopes import Scope

        # AdminSite is a singleton
        container.register(
            AdminSite,
            ValueProvider(AdminSite.default()),
        )

        # AdminController -- one per app scope
        container.register(
            AdminController,
            FactoryProvider(provide_admin_controller, scope=Scope.APP),
        )

        # AuditLog -- singleton from site
        container.register(
            AdminAuditLog,
            FactoryProvider(provide_audit_log, scope=Scope.SINGLETON),
        )

        # ModelBackedAuditLog -- singleton
        container.register(
            ModelBackedAuditLog,
            FactoryProvider(provide_model_backed_audit_log, scope=Scope.SINGLETON),
        )

        logger.debug("Registered admin DI providers: AdminSite, AdminController, AdminAuditLog")

    except ImportError:
        logger.debug("DI system not available -- skipping admin provider registration")
    except Exception as exc:
        logger.debug("Failed to register admin DI providers: %s", exc)


__all__ = [
    "register_admin_providers",
    "provide_admin_site",
    "provide_admin_controller",
    "provide_audit_log",
    "provide_model_backed_audit_log",
]
