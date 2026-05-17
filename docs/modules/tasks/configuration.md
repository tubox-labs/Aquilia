# Tasks Configuration

Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

No public config-specific class was detected in this module. It is configured through workspace/module declarations, related integration objects, or direct Python APIs.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/tasks/__init__.py` | 82 | 0 | 0 | AquilaTasks — Industry-Grade Async Background Task Manager. |
| `aquilia/tasks/decorators.py` | 218 | 0 | 4 | AquilaTasks — Task Decorator. |
| `aquilia/tasks/engine.py` | 841 | 3 | 0 | AquilaTasks — Task Engine & Backends. |
| `aquilia/tasks/faults.py` | 130 | 5 | 0 | AquilaTasks — Fault Classes. |
| `aquilia/tasks/job.py` | 179 | 4 | 0 | AquilaTasks — Job Model. |
| `aquilia/tasks/schedule.py` | 254 | 2 | 2 | AquilaTasks — Schedule Definitions. |
| `aquilia/tasks/worker.py` | 98 | 1 | 0 | AquilaTasks — Worker. |

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
