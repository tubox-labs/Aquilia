# Admin Architecture

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/admin/__init__.py` | 358 | 0 | 0 | AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia. |
| `aquilia/admin/audit.py` | 839 | 5 | 0 | AquilAdmin -- Audit Trail. |
| `aquilia/admin/contracts.py` | 182 | 0 | 0 | AquilAdmin -- Contracts for Admin Models. |
| `aquilia/admin/controller.py` | 7124 | 1 | 0 | AquilAdmin -- Admin Controller. |
| `aquilia/admin/di_providers.py` | 124 | 0 | 5 | AquilAdmin -- DI Providers. |
| `aquilia/admin/error_tracker.py` | 554 | 3 | 1 | AquilAdmin — Error Tracker. |
| `aquilia/admin/export.py` | 366 | 6 | 0 | AquilAdmin -- Export System. |
| `aquilia/admin/faults.py` | 391 | 15 | 0 | AquilAdmin -- Structured Faults for Admin System. |
| `aquilia/admin/filters.py` | 335 | 9 | 1 | AquilAdmin -- Advanced Filter System. |
| `aquilia/admin/hooks.py` | 459 | 4 | 0 | AquilAdmin -- Lifecycle Hooks System. |
| `aquilia/admin/inlines.py` | 345 | 3 | 0 | AquilAdmin -- Inline Model Admin. |
| `aquilia/admin/models.py` | 1192 | 5 | 0 | Aquilia Admin — Data Models ============================ |
| `aquilia/admin/options.py` | 662 | 2 | 1 | AquilAdmin -- ModelAdmin Options. |
| `aquilia/admin/permissions.py` | 396 | 2 | 8 | AquilAdmin -- Admin Permission & Role System. |
| `aquilia/admin/query_inspector.py` | 361 | 3 | 1 | AquilAdmin — Live Query Inspector. |
| `aquilia/admin/registry.py` | 288 | 0 | 3 | AquilAdmin -- Model Registration & Auto-Discovery. |
| `aquilia/admin/security.py` | 1035 | 8 | 1 | AquilAdmin -- Security Hardening Module. |
| `aquilia/admin/site.py` | 7750 | 2 | 0 | AquilAdmin -- AdminSite (Central Registry). |
| `aquilia/admin/subsystems.py` | 1024 | 12 | 2 | AquilAdmin -- Subsystem Integration Module. |
| `aquilia/admin/templates.py` | 1774 | 0 | 28 | AquilAdmin -- Template Renderer. |
| `aquilia/admin/widgets.py` | 516 | 12 | 2 | AquilAdmin -- Dashboard Widget System. |

## Internal Shape

`admin` has 21 Python files, 92 public classes, 53 public module-level functions, and 22 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 8 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.audit` | 4 |
| `.faults` | 3 |
| `.models` | 3 |
| `.permissions` | 3 |
| `.site` | 3 |
| `.controller` | 2 |
| `.options` | 2 |
| `.contracts` | 1 |
| `.di_providers` | 1 |
| `.export` | 1 |
| `.filters` | 1 |
| `.hooks` | 1 |
| `.inlines` | 1 |
| `.registry` | 1 |
| `.security` | 1 |
| `.subsystems` | 1 |
| `.templates` | 1 |
| `.widgets` | 1 |
| `aquilia._version` | 1 |
| `aquilia.admin.permissions` | 1 |
| `aquilia.controller.base` | 1 |
| `aquilia.controller.decorators` | 1 |
| `aquilia.controller.pagination` | 1 |
| `aquilia.faults` | 1 |
| `aquilia.faults.core` | 1 |
| `aquilia.response` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 20 |
| `typing` | 19 |
| `logging` | 13 |
| `datetime` | 9 |
| `collections` | 6 |
| `contextlib` | 6 |
| `dataclasses` | 6 |
| `enum` | 4 |
| `hashlib` | 3 |
| `os` | 3 |
| `pathlib` | 3 |
| `json` | 2 |
| `secrets` | 2 |
| `time` | 2 |
| `traceback` | 2 |
| `contextvars` | 1 |
| `csv` | 1 |
| `decimal` | 1 |
| `hmac` | 1 |
| `html` | 1 |
| `io` | 1 |
| `re` | 1 |
| `uuid` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `SurpAuditStore` | `aquilia/admin/audit.py` | Thin persistence layer that stores/loads audit entries using the SURP binary format.  Falls back to no-op if ``surp`` is not installed. |
| `AdminController` | `aquilia/admin/controller.py` | Aquilia Admin Controller. |
| `ExportRegistry` | `aquilia/admin/export.py` | Registry of available export formats. |
| `AdminConfigurationFault` | `aquilia/admin/faults.py` | Admin system misconfiguration or missing dependency. |
| `AdminHooksMixin` | `aquilia/admin/hooks.py` | Mixin providing lifecycle hook methods for ModelAdmin. |
| `AdminSecurityPolicy` | `aquilia/admin/security.py` | Central orchestrator for all admin security features. |
| `AdminConfig` | `aquilia/admin/site.py` | Immutable admin configuration parsed from ``Integration.admin()`` config dict. |
| `AdminCacheIntegration` | `aquilia/admin/subsystems.py` | Integrates Aquilia CacheService into admin operations. |
| `AdminAuthGuard` | `aquilia/admin/subsystems.py` | Flow guard that verifies admin authentication. |
| `AdminPermGuard` | `aquilia/admin/subsystems.py` | Flow guard that checks model-level permissions. |
| `AdminCSRFGuard` | `aquilia/admin/subsystems.py` | Flow guard that validates CSRF tokens for POST/PUT/DELETE requests. |
| `AdminRateLimitGuard` | `aquilia/admin/subsystems.py` | Flow guard that enforces rate limits on admin requests. |
| `AdminAuditHook` | `aquilia/admin/subsystems.py` | Flow hook that logs admin actions to the audit trail. |
| `WidgetRegistry` | `aquilia/admin/widgets.py` | Registry for dashboard widgets. |

## Error Handling

Fault/error classes defined here:

`ErrorRecord`, `ErrorGroup`, `ErrorTracker`, `AdminFault`, `AdminAuthenticationFault`, `AdminAuthorizationFault`, `AdminSecurityFault`, `AdminCSRFViolationFault`, `AdminRateLimitFault`, `AdminModelNotFoundFault`, `AdminRecordNotFoundFault`, `AdminValidationFault`, `AdminActionFault`, `AdminConfigurationFault`, `AdminRegistrationFault`, `AdminInlineFault`, `AdminTemplateFault`, `AdminExportFault`
