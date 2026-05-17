# Admin Configuration

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/admin/__init__.py` | 358 | 0 | 0 | AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia. |
| `aquilia/admin/audit.py` | 839 | 5 | 0 | AquilAdmin -- Audit Trail. |
| `aquilia/admin/blueprints.py` | 182 | 0 | 0 | AquilAdmin -- Blueprints for Admin Models. |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `AdminConfigurationFault` | `aquilia/admin/faults.py` |  | Admin system misconfiguration or missing dependency. |
| `AdminSecurityPolicy` | `aquilia/admin/security.py` | `from_config`, `protect_response`, `extract_client_ip` | Central orchestrator for all admin security features. |
| `AdminConfig` | `aquilia/admin/site.py` | `is_module_enabled`, `is_action_allowed`, `is_metric_enabled`, `is_sidebar_section_visible`, `get_docker_host`, `get_container_refresh_interval`, `get_container_log_tail`, `is_container_action_allowed`, `is_container_capability_enabled`, `get_kube_namespace`, `get_pod_refresh_interval`, `get_pod_log_tail`, `is_pod_resource_enabled`, `is_pod_capability_enabled`, `to_dict`, `from_dict` | Immutable admin configuration parsed from ``Integration.admin()`` config dict. |
| `AdminCacheIntegration` | `aquilia/admin/subsystems.py` | `enabled`, `set_cache_service`, `get_model_list`, `set_model_list`, `invalidate_model`, `get_dashboard_stats`, `set_dashboard_stats`, `get_fragment`, `set_fragment` | Integrates Aquilia CacheService into admin operations. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
