# Admin Troubleshooting

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq admin check`
- `aq admin createsuperuser`
- `aq admin createstaff`
- `aq admin listusers`
- `aq admin changepassword`
- `aq admin setup`
- `aq admin status`
- `aq admin audit`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
