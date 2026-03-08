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
- Inlines: Edit related models on the same page (TabularInline, StackedInline)
- Filters: Rich filter API with DateRange, NumericRange, Boolean, Related filters
- Widgets: Dashboard cards/metrics system (Count, Stat, Chart, Table, Progress)
- Export: Multi-format export (CSV, JSON, XML) with field selection
- Hooks: Lifecycle hooks (save_model, delete_model, get_queryset, before/after)
- Mixins: SoftDeleteMixin, VersioningMixin, TimestampMixin for common patterns
- History: Per-record change log timeline view
- Batch Update: Update a field across multiple records at once

Architecture:
    AdminSite (singleton)
        ├── ModelAdmin (per-model config)
        │   ├── list_display, list_filter, search_fields
        │   ├── fieldsets, readonly_fields, ordering
        │   ├── actions (bulk operations)
        │   ├── inlines (TabularInline, StackedInline)
        │   ├── export_formats, export_fields
        │   ├── save_as, save_on_top
        │   └── permissions (has_view/add/change/delete_permission)
        ├── AdminHooksMixin (lifecycle hooks)
        │   ├── get_queryset, get_object
        │   ├── clean_form, before_save, save_model, save_related, after_save
        │   ├── before_delete, delete_model, after_delete
        │   ├── log_addition, log_change, log_deletion
        │   └── response_add, response_change, response_delete
        ├── InlineModelAdmin (related model editing)
        │   ├── TabularInline (compact table layout)
        │   └── StackedInline (full form layout)
        ├── ListFilter (filter classes)
        │   ├── SimpleFilter, BooleanFilter, ChoiceFilter
        │   ├── DateRangeFilter, NumericRangeFilter
        │   ├── RelatedModelFilter, AllValuesFilter, EmptyFieldFilter
        │   └── resolve_filter() (auto-detection)
        ├── AdminWidget (dashboard widgets)
        │   ├── CountWidget, StatWidget, ChartWidget
        │   ├── TableWidget, ListWidget, ProgressWidget
        │   ├── RecentActivityWidget, CustomHTMLWidget
        │   └── WidgetRegistry
        ├── Exporter (export system)
        │   ├── CSVExporter, JSONExporter, XMLExporter
        │   └── ExportRegistry
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
        │   ├── GET  /admin/{app}/{model}/{pk}/history → Change history
        │   ├── POST /admin/{app}/{model}/action  → Bulk action
        │   ├── POST /admin/{app}/{model}/batch-update → Batch update
        │   ├── GET  /admin/{app}/{model}/filter-meta → Filter metadata API
        │   └── GET  /admin/audit/           → Audit log
        ├── AdminPermission (RBAC integration)
        └── AdminAudit (action logging)

Usage:
    from aquilia.admin import AdminSite, ModelAdmin, register
    from aquilia.admin import TabularInline, StackedInline
    from aquilia.admin import DateRangeFilter, AdminHooksMixin

    # Option 1: Decorator
    @register
    class UserAdmin(ModelAdmin, AdminHooksMixin):
        model = User
        list_display = ["id", "name", "email", "active", "created_at"]
        list_filter = ["active", ("created_at", DateRangeFilter)]
        search_fields = ["name", "email"]
        ordering = ["-created_at"]
        save_as = True
        inlines = [ProfileInline]

        def save_model(self, request, obj, form_data, change):
            if not change:
                obj.created_by = request.identity.username
            super().save_model(request, obj, form_data, change)

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
from .inlines import InlineModelAdmin, TabularInline, StackedInline
from .filters import (
    ListFilter, SimpleFilter, BooleanFilter, ChoiceFilter,
    DateRangeFilter, NumericRangeFilter, AllValuesFilter,
    RelatedModelFilter, EmptyFieldFilter, resolve_filter,
)
from .widgets import (
    AdminWidget, CountWidget, StatWidget, ChartWidget,
    RecentActivityWidget, TableWidget, ListWidget,
    ProgressWidget, CustomHTMLWidget, WidgetRegistry,
    WidgetSize, WidgetPosition, get_widget_registry, register_widget,
)
from .export import (
    Exporter, CSVExporter, JSONExporter, XMLExporter,
    ExportFormat, ExportRegistry,
)
from .hooks import (
    AdminHooksMixin, SoftDeleteMixin, VersioningMixin, TimestampMixin,
)
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
from .security import (
    AdminCSRFProtection,
    AdminRateLimiter,
    AdminSecurityHeaders,
    AdminSecurityPolicy,
    PasswordValidator,
    PasswordStrength,
    SecurityEventTracker,
    SecurityEvent,
    register_security_providers,
)
from .subsystems import (
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
from .di_providers import register_admin_providers

__all__ = [
    # Core
    "AdminSite",
    "AdminConfig",
    "ModelAdmin",
    
    # Registration
    "register",
    "autodiscover",
    
    # Inlines
    "InlineModelAdmin",
    "TabularInline",
    "StackedInline",
    
    # Filters
    "ListFilter",
    "SimpleFilter",
    "BooleanFilter",
    "ChoiceFilter",
    "DateRangeFilter",
    "NumericRangeFilter",
    "AllValuesFilter",
    "RelatedModelFilter",
    "EmptyFieldFilter",
    "resolve_filter",
    
    # Widgets
    "AdminWidget",
    "CountWidget",
    "StatWidget",
    "ChartWidget",
    "RecentActivityWidget",
    "TableWidget",
    "ListWidget",
    "ProgressWidget",
    "CustomHTMLWidget",
    "WidgetRegistry",
    "WidgetSize",
    "WidgetPosition",
    "get_widget_registry",
    "register_widget",
    
    # Export
    "Exporter",
    "CSVExporter",
    "JSONExporter",
    "XMLExporter",
    "ExportFormat",
    "ExportRegistry",
    
    # Hooks / Mixins
    "AdminHooksMixin",
    "SoftDeleteMixin",
    "VersioningMixin",
    "TimestampMixin",
    
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
    "AdminCSRFViolationFault",
    "AdminRateLimitFault",
    "AdminSecurityFault",
    "AdminModelNotFoundFault",
    "AdminRecordNotFoundFault",
    "AdminValidationFault",
    "AdminActionFault",
    "AdminConfigurationFault",
    "AdminRegistrationFault",
    "AdminInlineFault",
    "AdminTemplateFault",
    "AdminExportFault",
    
    # DI
    "register_admin_providers",
    
    # Security
    "AdminCSRFProtection",
    "AdminRateLimiter",
    "AdminSecurityHeaders",
    "AdminSecurityPolicy",
    "PasswordValidator",
    "PasswordStrength",
    "SecurityEventTracker",
    "SecurityEvent",
    "register_security_providers",
    
    # Subsystems
    "AdminSubsystems",
    "AdminCacheIntegration",
    "AdminTasks",
    "AdminLifecycle",
    "AdminAuthGuard",
    "AdminPermGuard",
    "AdminCSRFGuard",
    "AdminRateLimitGuard",
    "AdminAuditHook",
    "AdminDBEffect",
    "AdminCacheEffect",
    "AdminTaskEffect",
    "build_admin_flow_pipeline",
    "get_admin_subsystems",
]
