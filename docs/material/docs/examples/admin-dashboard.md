# Admin Dashboard

The Admin Dashboard example demonstrates Aquilia admin model registration, role-based
permission checks, audit-style service events, and admin workspace integration.

---

## What It Demonstrates

- `AdminIntegration` with `AdminModules` configuration
- `ModelAdmin` subclass with `@register()` decorator for model registration
- Role-based permission checks: staff can create/assign, viewers are read-only
- Audit-style service events for admin operations
- `AppManifest.models` for declaring persistent model schemas
- Dashboard endpoint returning ticket counts and permission-derived capability flags

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Enables `AdminIntegration` with audit, monitoring, and testing modules |
| `modules/adminops/manifest.py` | Declares controller, service, and model |
| `modules/adminops/controllers.py` | Dashboard endpoint with permission-derived data |
| `modules/adminops/services.py` | Ticket CRUD with role enforcement |
| `modules/adminops/admin.py` | `ModelAdmin` registration via `@register(SupportTicket)` |
| `modules/adminops/models.py` | `SupportTicket` model declaration |

## Workspace Configuration

```python
from aquilia.integrations import AdminIntegration, AdminModules

workspace.integrate(AdminIntegration(
    site_title="Operations Admin",
    modules=AdminModules(
        audit=True,
        monitoring=True,
        testing=True,
    ),
))
```

`AdminModules` controls which admin subsystem pages are available:

| Flag | Purpose |
| ---- | ------- |
| `audit` | Enable audit log viewer pages |
| `monitoring` | Enable health and metrics pages |
| `testing` | Enable test runner pages |
| `storage` | Enable file storage browser |
| `tasks` | Enable task queue management |

## Model Registration

```python
from aquilia.admin import ModelAdmin, register

@register(SupportTicket)
class SupportTicketAdmin(ModelAdmin):
    list_display = ["title", "status", "assignee", "created_at"]
    list_filter = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]
    actions = ["assign_to_staff", "resolve_closed"]
```

The `@register(Model)` decorator links the model to admin configuration. `ModelAdmin`
subclasses define:

| Attribute | Purpose |
| --------- | ------- |
| `list_display` | Columns shown in the admin list view |
| `list_filter` | Fields available for filtering |
| `search_fields` | Fields searched by the admin search bar |
| `ordering` | Default sort order (prefix with `-` for descending) |
| `actions` | Named admin actions available in the action dropdown |

## Permission Enforcement

The service layer enforces role-based permissions:

```python
class AdminOpsService:
    async def create_ticket(self, identity: Identity, data: dict) -> dict:
        if identity.role not in ("staff", "admin"):
            raise PermissionFault(detail="Only staff can create tickets")
        return await self._store.create(data)

    async def get_dashboard(self, identity: Identity) -> dict:
        counts = await self._store.counts_by_status()
        return {
            "tickets": counts,
            "can_create": identity.role in ("staff", "admin"),
            "can_assign": identity.role == "admin",
            "viewer": identity.role == "viewer",
        }
```

## Running

```bash
cd examples/admin_dashboard_app
python -m uvicorn runtime:app --reload --port 8061
```

```bash
# Dashboard with role-derived capabilities
curl http://127.0.0.1:8061/adminops/dashboard

# Run tests
python -m pytest examples/admin_dashboard_app -q
```

## What You'll Learn

- How to register models with `@register()` and `ModelAdmin`
- How to configure `AdminIntegration` with `AdminModules`
- How to enforce role-based permissions in admin services
- How to build dashboard endpoints with capability flags
- How to structure admin module code with models, admin config, and services