# Admin Documentation

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

## Coverage Snapshot

- Source files: 21
- Source lines: 26075
- Public classes: 92
- Public module functions: 53
- Constants/module flags: 22
- Public exports in `__all__`: 116

## Source Files Read

- `aquilia/admin/__init__.py`: AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia.
- `aquilia/admin/audit.py`: AquilAdmin -- Audit Trail.
- `aquilia/admin/contracts.py`: AquilAdmin -- Contracts for Admin Models.
- `aquilia/admin/controller.py`: AquilAdmin -- Admin Controller.
- `aquilia/admin/di_providers.py`: AquilAdmin -- DI Providers.
- `aquilia/admin/error_tracker.py`: AquilAdmin — Error Tracker.
- `aquilia/admin/export.py`: AquilAdmin -- Export System.
- `aquilia/admin/faults.py`: AquilAdmin -- Structured Faults for Admin System.
- `aquilia/admin/filters.py`: AquilAdmin -- Advanced Filter System.
- `aquilia/admin/hooks.py`: AquilAdmin -- Lifecycle Hooks System.
- `aquilia/admin/inlines.py`: AquilAdmin -- Inline Model Admin.
- `aquilia/admin/models.py`: Aquilia Admin — Data Models ============================
- `aquilia/admin/options.py`: AquilAdmin -- ModelAdmin Options.
- `aquilia/admin/permissions.py`: AquilAdmin -- Admin Permission & Role System.
- `aquilia/admin/query_inspector.py`: AquilAdmin — Live Query Inspector.
- `aquilia/admin/registry.py`: AquilAdmin -- Model Registration & Auto-Discovery.
- `aquilia/admin/security.py`: AquilAdmin -- Security Hardening Module.
- `aquilia/admin/site.py`: AquilAdmin -- AdminSite (Central Registry).
- `aquilia/admin/subsystems.py`: AquilAdmin -- Subsystem Integration Module.
- `aquilia/admin/templates.py`: AquilAdmin -- Template Renderer.
- `aquilia/admin/widgets.py`: AquilAdmin -- Dashboard Widget System.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
