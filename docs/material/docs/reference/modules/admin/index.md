# Admin Module

> `aquilia.admin` — Auto-discovering admin dashboard

The Admin module provides an auto-discovering, model-driven admin dashboard for managing application data. It detects registered models, generates CRUD interfaces, handles authentication/authorization, and supports custom actions.

## When to Use

Use the Admin module when you need:

- A ready-to-use admin dashboard for managing database records
- Role-based access control for admin operations
- Audit logging for administrative actions
- Custom admin actions on model records
- Auto-generated list/detail/create/edit forms

## Key Classes

| Class | Purpose |
|---|---|
| `AdminSite` | Central admin registry — the dashboard root |
| `ModelAdmin` | Per-model admin configuration and CRUD handlers |
| `AdminController` | HTTP controller serving admin views |
| `AdminUser` | Admin user model with authentication |
| `AdminRole` | Role-based authorization model |
| `AdminPermission` | Fine-grained permission model |
| `AdminAuditLog` | Audit trail for admin actions |
| `AdminAction` | Custom bulk/model actions |
| `AdminSession` | Admin session management |

## Quick Example

```python
from aquilia.admin import AdminSite, ModelAdmin, register

# Register a model with the admin site
class UserAdmin(ModelAdmin):
    list_display = ["id", "email", "name", "created_at"]
    search_fields = ["email", "name"]
    list_filter = ["status", "role"]
    ordering = ["-created_at"]

admin_site = AdminSite()
admin_site.register(User, UserAdmin)
```

```python
# Auto-discover admin registrations in admin.py files
from aquilia.admin import autodiscover

autodiscover()
```

## Import Path

```python
from aquilia.admin import (
    AdminSite,
    ModelAdmin,
    AdminController,
    AdminUser,
    AdminRole,
    AdminPermission,
    AdminAuditLog,
    AdminAction,
    AdminSession,
    register,
    autodiscover,
)
```

## Related Modules

- [models](../models/index.md) — Models registered with admin
- [auth](../auth/index.md) — Authentication and authorization
- [controller](../controller/index.md) — HTTP controller routing
- [blueprints](../blueprints/index.md) — Validation for admin forms