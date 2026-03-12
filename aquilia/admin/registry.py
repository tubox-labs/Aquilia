"""
AquilAdmin -- Model Registration & Auto-Discovery.

Provides the @register decorator and autodiscover() function for
registering models with the admin site.

Auto-discovery:
    When autodiscover() is called (typically at startup), it scans
    ModelRegistry.all_models() and registers any model that doesn't
    already have an explicit ModelAdmin with the default ModelAdmin.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aquilia.models.base import Model

    from .site import AdminSite

logger = logging.getLogger("aquilia.admin.registry")

# Pending registrations (before AdminSite is created)
_pending_registrations: list[tuple] = []


def register(
    model_or_admin: Any = None,
    *,
    site: AdminSite | None = None,
) -> Callable:
    """
    Register a model or ModelAdmin with the admin site.

    Can be used as a class decorator or called directly.

    Usage (decorator on ModelAdmin):
        @register
        class UserAdmin(ModelAdmin):
            model = User
            list_display = ["id", "name", "email"]

    Usage (decorator with model):
        @register(User)
        class UserAdmin(ModelAdmin):
            list_display = ["id", "name"]

    Usage (direct call):
        register(User, UserAdmin)
    """
    from .options import ModelAdmin as _ModelAdmin

    def _do_register(admin_cls: type[_ModelAdmin], model_cls: type[Model] | None = None):
        """Actually register the admin class."""
        actual_model = model_cls or admin_cls.model
        if actual_model is None:
            from .faults import AdminRegistrationFault

            raise AdminRegistrationFault(
                reason="Must specify a model class either via the 'model' attribute or as a decorator argument.",
                model_name=admin_cls.__name__,
            )

        admin_instance = admin_cls(model=actual_model)

        if site is not None:
            site.register_admin(actual_model, admin_instance)
        else:
            # Try default site
            from .site import AdminSite

            default_site = AdminSite.default()
            if default_site._initialized:
                default_site.register_admin(actual_model, admin_instance)
            else:
                _pending_registrations.append((actual_model, admin_instance))

    # Handle various calling patterns
    if model_or_admin is None:
        # @register or @register()
        def decorator(cls):
            _do_register(cls)
            return cls

        return decorator

    if isinstance(model_or_admin, type):
        from .options import ModelAdmin as _ModelAdmin

        if issubclass(model_or_admin, _ModelAdmin):
            # @register applied to ModelAdmin class
            _do_register(model_or_admin)
            return model_or_admin
        else:
            # @register(UserModel) -- decorator factory
            def decorator(cls):
                _do_register(cls, model_or_admin)
                return cls

            return decorator

    from .faults import AdminRegistrationFault

    raise AdminRegistrationFault(
        reason=f"Invalid argument to @register: {model_or_admin!r}",
    )


def autodiscover() -> dict[str, type[Model]]:
    """
    Auto-discover and register all models from ModelRegistry.

    Scans ModelRegistry.all_models() and registers any model that
    doesn't already have an explicit ModelAdmin with the default.

    Also registers the built-in admin models (AdminUser, AdminGroup, etc.)
    with rich ModelAdmin configurations for admin management.

    Returns:
        Dictionary of model_name -> model_class that were auto-registered.
    """
    from aquilia.models.registry import ModelRegistry

    from .options import ModelAdmin
    from .site import AdminSite

    site = AdminSite.default()
    auto_registered: dict[str, type] = {}

    # ── Register built-in admin models with custom ModelAdmin configs ──
    _register_admin_models(site)

    all_models = ModelRegistry.all_models()
    for name, model_cls in all_models.items():
        # Skip abstract models
        if hasattr(model_cls, "_meta") and model_cls._meta.abstract:
            continue

        # Skip already registered
        if site.is_registered(model_cls):
            continue

        # Auto-register with default ModelAdmin
        admin_instance = ModelAdmin(model=model_cls)
        site.register_admin(model_cls, admin_instance)
        auto_registered[name] = model_cls

    return auto_registered


def _register_admin_models(site: AdminSite) -> None:
    """
    Register the built-in admin models with rich ModelAdmin subclasses.

    Only models with ``_HAS_ORM != False`` get a real registration.
    Legacy stubs (ContentType, AdminGroup, etc.) are skipped because
    they carry ``_HAS_ORM = False``.
    """
    from .models import _HAS_ORM
    from .options import ModelAdmin

    if not _HAS_ORM:
        return

    from .models import (
        AdminAPIKey,
        AdminAuditEntry,
        AdminPreference,
        AdminUser,
    )

    # ── AdminUser Admin ──
    if not site.is_registered(AdminUser):

        class AdminUserAdmin(ModelAdmin):
            list_display = [
                "id",
                "username",
                "email",
                "display_name",
                "role",
                "is_active",
                "login_count",
                "last_login_at",
            ]
            search_fields = ["username", "email", "display_name"]
            list_filter = ["role", "is_active"]
            ordering = ["-created_at"]
            readonly_fields = ["id", "password_hash", "created_at", "login_count", "last_login_at", "last_active_at"]
            exclude = ["password_hash"]
            icon = "user"
            verbose_name = "Admin User"
            verbose_name_plural = "Admin Users"

        site.register_admin(AdminUser, AdminUserAdmin(model=AdminUser))

    # ── AdminAuditEntry Admin ──
    if not site.is_registered(AdminAuditEntry):

        class AdminAuditEntryAdmin(ModelAdmin):
            list_display = [
                "id",
                "timestamp",
                "username",
                "action",
                "resource_type",
                "resource_id",
                "severity",
                "category",
            ]
            search_fields = ["username", "action", "resource_type", "summary"]
            list_filter = ["action", "severity", "category"]
            ordering = ["-timestamp"]
            readonly_fields = [
                "id",
                "timestamp",
                "user_id",
                "username",
                "ip_address",
                "user_agent",
                "action",
                "resource_type",
                "resource_id",
                "summary",
                "detail",
                "diff",
                "severity",
                "category",
            ]
            icon = "list"
            verbose_name = "Audit Entry"
            verbose_name_plural = "Audit Entries"

        site.register_admin(AdminAuditEntry, AdminAuditEntryAdmin(model=AdminAuditEntry))

    # ── AdminAPIKey Admin ──
    if not site.is_registered(AdminAPIKey):

        class AdminAPIKeyAdmin(ModelAdmin):
            list_display = ["id", "name", "prefix", "user_id", "is_active", "last_used_at", "expires_at", "created_at"]
            search_fields = ["name", "prefix"]
            list_filter = ["is_active"]
            ordering = ["-created_at"]
            readonly_fields = ["id", "key_hash", "prefix", "created_at", "last_used_at"]
            exclude = ["key_hash"]
            icon = "key"
            verbose_name = "API Key"
            verbose_name_plural = "API Keys"

        site.register_admin(AdminAPIKey, AdminAPIKeyAdmin(model=AdminAPIKey))

    # ── AdminPreference Admin ──
    if not site.is_registered(AdminPreference):

        class AdminPreferenceAdmin(ModelAdmin):
            list_display = ["id", "user_id", "namespace", "updated_at"]
            search_fields = ["namespace"]
            list_filter = ["namespace"]
            ordering = ["user_id", "namespace"]
            readonly_fields = ["id"]
            icon = "settings"
            verbose_name = "User Preference"
            verbose_name_plural = "User Preferences"

        site.register_admin(AdminPreference, AdminPreferenceAdmin(model=AdminPreference))


def flush_pending_registrations() -> int:
    """
    Flush any pending registrations to the default AdminSite.

    Called during AdminSite initialization.
    Returns count of flushed registrations.
    """
    from .site import AdminSite

    site = AdminSite.default()
    count = 0

    for model_cls, admin_instance in _pending_registrations:
        site.register_admin(model_cls, admin_instance)
        count += 1

    _pending_registrations.clear()
    return count
