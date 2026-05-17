# Admin Architecture

## Runtime Role

The built-in administration system for model management, audit views, permissions, security controls, task views, storage pages, mailer views, and operational screens.

The implementation is split across 21 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 20 |
| `typing` | 19 |
| `logging` | 13 |
| `aquilia` | 8 |
| `datetime` | 8 |
| `collections` | 6 |
| `contextlib` | 6 |
| `dataclasses` | 6 |
| `audit` | 4 |
| `enum` | 4 |
| `faults` | 3 |
| `hashlib` | 3 |
| `os` | 3 |
| `pathlib` | 3 |
| `permissions` | 3 |
| `site` | 3 |
| `controller` | 2 |
| `json` | 2 |
| `models` | 2 |
| `options` | 2 |
| `secrets` | 2 |
| `time` | 2 |
| `traceback` | 2 |
| `blueprints` | 1 |
| `contextvars` | 1 |
| `csv` | 1 |
| `decimal` | 1 |
| `di_providers` | 1 |
| `export` | 1 |
| `filters` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
