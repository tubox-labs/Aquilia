"""
AquilAdmin — Model Registration & Auto-Discovery.

Provides the @register decorator and autodiscover() function for
registering models with the admin site.

Auto-discovery:
    When autodiscover() is called (typically at startup), it scans
    ModelRegistry.all_models() and registers any model that doesn't
    already have an explicit ModelAdmin with the default ModelAdmin.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from .options import ModelAdmin
    from .site import AdminSite

logger = logging.getLogger("aquilia.admin.registry")

# Pending registrations (before AdminSite is created)
_pending_registrations: List[tuple] = []


def register(
    model_or_admin: Any = None,
    *,
    site: Optional[AdminSite] = None,
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

    def _do_register(admin_cls: Type[_ModelAdmin], model_cls: Optional[Type[Model]] = None):
        """Actually register the admin class."""
        actual_model = model_cls or admin_cls.model
        if actual_model is None:
            raise ValueError(
                f"ModelAdmin {admin_cls.__name__} must specify a model class "
                "either via the 'model' attribute or as a decorator argument."
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
            # @register(UserModel) — decorator factory
            def decorator(cls):
                _do_register(cls, model_or_admin)
                return cls
            return decorator

    raise TypeError(f"Invalid argument to @register: {model_or_admin!r}")


def autodiscover() -> Dict[str, Type[Model]]:
    """
    Auto-discover and register all models from ModelRegistry.

    Scans ModelRegistry.all_models() and registers any model that
    doesn't already have an explicit ModelAdmin with the default.

    Also registers the built-in admin models (AdminUser, AdminGroup, etc.)
    with rich ModelAdmin configurations for Django-admin-like management.

    Returns:
        Dictionary of model_name -> model_class that were auto-registered.
    """
    from .site import AdminSite
    from .options import ModelAdmin
    from aquilia.models.registry import ModelRegistry

    site = AdminSite.default()
    auto_registered: Dict[str, type] = {}

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
        logger.debug("Auto-registered model: %s", name)

    logger.info(
        "Admin autodiscover complete: %d models auto-registered, %d total",
        len(auto_registered),
        len(site._registry),
    )

    return auto_registered


def _register_admin_models(site: "AdminSite") -> None:
    """
    Register the built-in admin models (AdminUser, AdminGroup, etc.)
    with rich ModelAdmin subclasses for Django-admin-like data management.

    These models store real data in database tables — ContentType tracks
    registered models, AdminUser stores staff accounts, AdminLogEntry
    provides an immutable audit trail, etc.
    """
    from .options import ModelAdmin
    from .models import _HAS_ORM

    if not _HAS_ORM:
        return

    from .models import (
        ContentType,
        AdminPermission as AdminPermissionModel,
        AdminGroup,
        AdminUser,
        AdminLogEntry,
        AdminSession,
    )

    # ── ContentType Admin ──
    if not site.is_registered(ContentType):
        class ContentTypeAdmin(ModelAdmin):
            list_display = ["id", "app_label", "model"]
            search_fields = ["app_label", "model"]
            ordering = ["app_label", "model"]
            readonly_fields = ["id"]
            icon = "🏷️"
            verbose_name = "Content Type"
            verbose_name_plural = "Content Types"
        site.register_admin(ContentType, ContentTypeAdmin(model=ContentType))

    # ── AdminPermission Admin ──
    if not site.is_registered(AdminPermissionModel):
        class AdminPermissionAdmin(ModelAdmin):
            list_display = ["id", "codename", "name", "content_type"]
            search_fields = ["name", "codename"]
            ordering = ["codename"]
            readonly_fields = ["id"]
            icon = "🔑"
            verbose_name = "Permission"
            verbose_name_plural = "Permissions"
        site.register_admin(AdminPermissionModel, AdminPermissionAdmin(model=AdminPermissionModel))

    # ── AdminGroup Admin ──
    if not site.is_registered(AdminGroup):
        class AdminGroupAdmin(ModelAdmin):
            list_display = ["id", "name"]
            search_fields = ["name"]
            ordering = ["name"]
            readonly_fields = ["id"]
            icon = "👥"
            verbose_name = "Group"
            verbose_name_plural = "Groups"
        site.register_admin(AdminGroup, AdminGroupAdmin(model=AdminGroup))

    # ── AdminUser Admin ──
    if not site.is_registered(AdminUser):
        class AdminUserAdmin(ModelAdmin):
            list_display = ["id", "username", "email", "is_superuser", "is_staff", "is_active", "date_joined"]
            search_fields = ["username", "email", "first_name", "last_name"]
            list_filter = ["is_superuser", "is_staff", "is_active"]
            ordering = ["-date_joined"]
            readonly_fields = ["id", "password_hash", "date_joined", "last_login"]
            exclude = ["password_hash"]
            icon = "👤"
            verbose_name = "Admin User"
            verbose_name_plural = "Admin Users"
        site.register_admin(AdminUser, AdminUserAdmin(model=AdminUser))

    # ── AdminLogEntry Admin ──
    if not site.is_registered(AdminLogEntry):
        class AdminLogEntryAdmin(ModelAdmin):
            list_display = ["id", "action_time", "user", "content_type", "object_repr", "action_flag"]
            search_fields = ["object_repr", "change_message"]
            list_filter = ["action_flag", "action_time"]
            ordering = ["-action_time"]
            readonly_fields = ["id", "action_time", "user", "content_type", "object_id", "object_repr", "action_flag", "change_message"]
            icon = "📋"
            verbose_name = "Log Entry"
            verbose_name_plural = "Log Entries"
        site.register_admin(AdminLogEntry, AdminLogEntryAdmin(model=AdminLogEntry))

    # ── AdminSession Admin ──
    if not site.is_registered(AdminSession):
        class AdminSessionAdmin(ModelAdmin):
            list_display = ["id", "session_key", "expire_date"]
            search_fields = ["session_key"]
            ordering = ["-expire_date"]
            readonly_fields = ["id", "session_key"]
            icon = "🔐"
            verbose_name = "Session"
            verbose_name_plural = "Sessions"
        site.register_admin(AdminSession, AdminSessionAdmin(model=AdminSession))

    logger.debug("Registered built-in admin models (ContentType, Permission, Group, User, LogEntry, Session)")


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
