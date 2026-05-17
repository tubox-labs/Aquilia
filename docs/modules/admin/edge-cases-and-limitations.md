# Admin Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `AdminFault` | `aquilia/admin/faults.py` | Base fault for all admin operations. |
| `AdminAuthenticationFault` | `aquilia/admin/faults.py` | Admin authentication failed. |
| `AdminAuthorizationFault` | `aquilia/admin/faults.py` | Admin authorization failed -- insufficient permissions. |
| `AdminSecurityFault` | `aquilia/admin/faults.py` | Base fault for admin security violations. |
| `AdminCSRFViolationFault` | `aquilia/admin/faults.py` | CSRF token validation failed. |
| `AdminRateLimitFault` | `aquilia/admin/faults.py` | Rate limit exceeded for admin operation. |
| `AdminModelNotFoundFault` | `aquilia/admin/faults.py` | Requested model is not registered with admin. |
| `AdminRecordNotFoundFault` | `aquilia/admin/faults.py` | Record not found in database. |
| `AdminValidationFault` | `aquilia/admin/faults.py` | Validation error when creating/updating records. |
| `AdminActionFault` | `aquilia/admin/faults.py` | Bulk action execution failed. |
| `AdminConfigurationFault` | `aquilia/admin/faults.py` | Admin system misconfiguration or missing dependency. |
| `AdminRegistrationFault` | `aquilia/admin/faults.py` | Model registration error. |
| `AdminInlineFault` | `aquilia/admin/faults.py` | Inline model configuration error. |
| `AdminTemplateFault` | `aquilia/admin/faults.py` | Template rendering error. |
| `AdminExportFault` | `aquilia/admin/faults.py` | Export generation error. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/admin/__init__.py`: AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia.
- `aquilia/admin/audit.py`: AquilAdmin -- Audit Trail.
- `aquilia/admin/blueprints.py`: AquilAdmin -- Blueprints for Admin Models.
- `aquilia/admin/controller.py`: AquilAdmin -- Admin Controller.
- `aquilia/admin/di_providers.py`: AquilAdmin -- DI Providers.
- `aquilia/admin/error_tracker.py`: AquilAdmin - Error Tracker.
- `aquilia/admin/export.py`: AquilAdmin -- Export System.
- `aquilia/admin/faults.py`: AquilAdmin -- Structured Faults for Admin System.
- `aquilia/admin/filters.py`: AquilAdmin -- Advanced Filter System.
- `aquilia/admin/hooks.py`: AquilAdmin -- Lifecycle Hooks System.
- `aquilia/admin/inlines.py`: AquilAdmin -- Inline Model Admin.
- `aquilia/admin/models.py`: Aquilia Admin - Data Models
- `aquilia/admin/options.py`: AquilAdmin -- ModelAdmin Options.
- `aquilia/admin/permissions.py`: AquilAdmin -- Admin Permission & Role System.
- `aquilia/admin/query_inspector.py`: AquilAdmin - Live Query Inspector.
- `aquilia/admin/registry.py`: AquilAdmin -- Model Registration & Auto-Discovery.
- `aquilia/admin/security.py`: AquilAdmin -- Security Hardening Module.
- `aquilia/admin/site.py`: AquilAdmin -- AdminSite (Central Registry).
- `aquilia/admin/subsystems.py`: AquilAdmin -- Subsystem Integration Module.
- `aquilia/admin/templates.py`: AquilAdmin -- Template Renderer.
- `aquilia/admin/widgets.py`: AquilAdmin -- Dashboard Widget System.
