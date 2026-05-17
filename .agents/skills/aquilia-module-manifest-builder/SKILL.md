---
name: aquilia-module-manifest-builder
description: "Create, update, debug, and sync Aquilia module manifests. Use when working with module manifest.py files, AppManifest, services/controllers/models/tasks/socket_controllers, imports/exports, auto_discovery, or aq add module."
---

# Aquilia Module Manifest Builder

## Purpose
Create module-level configuration that matches Aquilia Manifest-First architecture.

## Trigger Conditions
Use for module creation, `AppManifest` setup, imports/exports, component registration, auto-discovery, `aq add module`, `aq manifest update`, or `aq discover --sync`.

## Inputs
- Module name, route prefix, fault domain, imports/exports.
- Component import paths for controllers, services, models, middleware, guards, pipes, interceptors, tasks, and socket controllers.
- Whether the module should be minimal, full, explicit, or auto-discovered.

## Execution Flow
1. Use `aq add module` when scaffolding; it mirrors `ModuleGenerator`.
2. In `manifest.py`, instantiate `AppManifest(name=..., version=..., controllers=[...], services=[...], base_path=...)`.
3. Add `models`, `socket_controllers`, `middleware`, `guards`, `pipes`, `interceptors`, `background_tasks`, `templates`, `faults`, `imports`, and `exports` only when needed.
4. Keep route prefix in `workspace.py` via `Module.route_prefix()`.
5. Run `aq validate` or inspect manifest import errors after changes.

## Constraints
- Component refs must use `module.path:ClassName` where required.
- Manifest `name` must be alphanumeric/underscore and `version` must be present.
- Manifest-level `DatabaseConfig` is deprecated and ignored at runtime.

## Implementation Anchors
`aquilia/manifest.py`, `aquilia/cli/generators/module.py`, `aquilia/cli/commands/add.py`, `aquilia/aquilary/core.py`, `aquilia/discovery/engine.py`, `examples/*/modules/*/manifest.py`.

## Examples
- Add `socket_controllers=["modules.chat.sockets:ChatSocket"]`.
- Export `OrdersService` so importing modules can use it.
- Disable `auto_discover` for explicit production manifests.

## Failure Handling
`ManifestValidationFault` points to structural issues. Missing components usually mean bad import paths or disabled discovery. Dependency cycles are found by the Aquilary dependency graph; inspect `imports` and `depends_on`.
