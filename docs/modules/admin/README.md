# Admin Documentation

This directory is the professional documentation set for `admin`. It is implementation-driven and aligned with the current source files under `aquilia/admin`.

## What This Covers

The built-in administration system for model management, audit views, permissions, security controls, task views, storage pages, mailer views, and operational screens.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 21
- Public classes: 92
- Configuration or dataclass-like types: 19
- Public functions: 53
- Constants detected: 16

## Fast Start

```python
from aquilia.admin import __version__, AdminAction, AdminAuditLog, AdminAPIKeyBlueprint, AdminAuditEntryBlueprint, AdminGroupBlueprint

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
