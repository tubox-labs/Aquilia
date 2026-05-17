---
name: aquilia-workspace-bootstrap
description: "Create and adjust Aquilia workspaces using the real Workspace, Module, AquilaConfig, runtime, and aq init/add flows. Use for workspace.py, project bootstrap, env config, module pointers, and starter project structure."
---

# Aquilia Workspace Bootstrap

## Purpose
Create or repair Aquilia `workspace.py` and starter project structure using the Python-native builder API.

## Trigger Conditions
Use when the user asks to create a project, edit workspace runtime settings, add modules, configure integrations, set env config, or debug `aq init workspace` / `aq add module` output.

## Inputs
- Workspace name, root path, runtime mode/host/port/reload.
- Module names with route prefixes, imports, exports, and tags.
- Required integrations: database, cache, sessions, auth, templates, storage, tasks, i18n, OpenAPI, admin, mail, MLOps, or provider settings.

## Execution Flow
1. Prefer `aq init workspace <name>` for new projects when CLI use is acceptable; otherwise mirror `WorkspaceGenerator` output.
2. Define `workspace.py` with `Workspace(...).runtime(...).module(Module(...).route_prefix(...)).integrate(...)`.
3. Keep component declarations out of `workspace.py`; `Module` is an orchestration pointer.
4. Use `AquilaConfig`, `Env`, and `Secret` for Python-native environment config.
5. Cross-check real examples such as `examples/multi_module_native_app/workspace.py`.

## Constraints
- Do not recommend YAML as canonical config; `ConfigLoader` and `pyconfig.py` make Python-native config canonical.
- Do not use deprecated `Module.register_*` methods for new code.
- If auth is enabled, sessions are required by `AquiliaServer._setup_middleware()`.

## Implementation Anchors
`aquilia/config_builders.py`, `aquilia/pyconfig.py`, `aquilia/config.py`, `aquilia/cli/generators/workspace.py`, `aquilia/cli/commands/init.py`, `examples/*/workspace.py`.

## Examples
- "Create a workspace with accounts, catalog, orders, and realtime modules."
- "Move controller declarations out of workspace.py into module manifests."
- "Add memory cache, local storage, templates, and OpenAPI."

## Failure Handling
If `workspace.py` is missing, runtime raises `FileNotFoundError`; create it or set `AQUILIA_WORKSPACE`. If route prefixes are wrong, remember `Module.route_prefix()` wins over manifest `route_prefix`. If discovery fails, inspect `modules/<name>/manifest.py` imports and sys.path.
