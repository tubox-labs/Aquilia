"""
AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia.

A comprehensive admin dashboard built with
modern architecture: automatic model detection from ModelRegistry,
role-based access control, audit logging, and deep integration with
Aquilia's ORM, Auth, Sessions, DI, Controller, Cache, and Templates.

Key Features:
- Auto-detection: Models registered via ModelRegistry are auto-discovered
- Zero-config: Works out of the box with sensible defaults
- ModelAdmin: Declarative configuration per model
- AdminSite: Central registry with dashboard, CRUD, search, filters
- RBAC: Role/permission management using Aquilia Auth
- Audit Trail: Every admin action logged via AuditTrail
- Session-based: Admin authentication via Aquilia Sessions
- DI-integrated: All admin services are injectable
- Template-rendered: HTML dashboard via Aquilia TemplateEngine
- CLI-integrated: `aq admin` commands for setup and management
- Theme: Matches aqdocx dark/light mode with Aquilia green accent

Architecture:
    AdminSite (singleton)
        ├── ModelAdmin (per-model config)
        │   ├── list_display, list_filter, search_fields
        │   ├── fieldsets, readonly_fields, ordering
        │   ├── actions (bulk operations)
        │   └── permissions (has_view/add/change/delete_permission)
        ├── AdminController (at /admin)
        │   ├── GET  /admin/                 → Dashboard
        │   ├── GET  /admin/login            → Login page
        │   ├── POST /admin/login            → Authenticate
        │   ├── POST /admin/logout           → Logout
        │   ├── GET  /admin/{app}/{model}/   → List view
        │   ├── GET  /admin/{app}/{model}/add     → Add form
        │   ├── POST /admin/{app}/{model}/add     → Create record
        │   ├── GET  /admin/{app}/{model}/{pk}    → Edit form
        │   ├── POST /admin/{app}/{model}/{pk}    → Update record
        │   ├── POST /admin/{app}/{model}/{pk}/delete → Delete record
        │   ├── POST /admin/{app}/{model}/action  → Bulk action
        │   └── GET  /admin/audit/           → Audit log
        ├── AdminPermission (RBAC integration)
        └── AdminAudit (action logging)

Usage:
    from aquilia.admin import AdminSite, ModelAdmin, register

    # Option 1: Decorator
    @register
    class UserAdmin(ModelAdmin):
        model = User
        list_display = ["id", "name", "email", "active", "created_at"]
        list_filter = ["active", "created_at"]
        search_fields = ["name", "email"]
        ordering = ["-created_at"]

    # Option 2: Manual registration
    admin_site = AdminSite.default()
    admin_site.register(User, UserAdmin)

    # Option 3: Zero-config (auto-detected from ModelRegistry)
    # All models are auto-registered with default ModelAdmin
"""

__version__ = "1.0.0"

from .site import AdminSite, AdminConfig
from .options import ModelAdmin
from .registry import register, autodiscover
from .permissions import AdminPermission, AdminRole
from .audit import AdminAuditLog, AdminAction
from .controller import AdminController
from .models import (
    AdminUser,
    AdminGroup,
    AdminPermission as AdminPermissionModel,
    ContentType,
    AdminLogEntry,
    AdminSession,
)
from .blueprints import (
    AdminUserBlueprint,
    AdminGroupBlueprint,
    AdminPermissionBlueprint,
    ContentTypeBlueprint,
    AdminLogEntryBlueprint,
    AdminSessionBlueprint,
)
from .faults import (
    AdminFault,
    AdminAuthenticationFault,
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
    AdminActionFault,
)
from .di_providers import register_admin_providers

__all__ = [
    # Core
    "AdminSite",
    "AdminConfig",
    "ModelAdmin",
    
    # Registration
    "register",
    "autodiscover",
    
    # Permissions
    "AdminPermission",
    "AdminRole",
    
    # Audit
    "AdminAuditLog",
    "AdminAction",
    
    # Controller
    "AdminController",
    
    # Models
    "AdminUser",
    "AdminGroup",
    "AdminPermissionModel",
    "ContentType",
    "AdminLogEntry",
    "AdminSession",
    
    # Blueprints
    "AdminUserBlueprint",
    "AdminGroupBlueprint",
    "AdminPermissionBlueprint",
    "ContentTypeBlueprint",
    "AdminLogEntryBlueprint",
    "AdminSessionBlueprint",
    
    # Faults
    "AdminFault",
    "AdminAuthenticationFault",
    "AdminAuthorizationFault",
    "AdminModelNotFoundFault",
    "AdminRecordNotFoundFault",
    "AdminValidationFault",
    "AdminActionFault",
    
    # DI
    "register_admin_providers",
]
