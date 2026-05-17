---
name: aquilia-runtime-lifecycle-debugger
description: "Debug Aquilia runtime startup, discovery, bootstrap, ASGI lifespan, server startup/shutdown, health, route registration, and lifecycle hook behavior. Use for AquiliaRuntime, AquiliaServer, entrypoint, and production boot issues."
---

# Aquilia Runtime Lifecycle Debugger

## Purpose
Diagnose runtime phase failures and lifecycle behavior from `AquiliaRuntime`, `AquiliaServer`, `ASGIAdapter`, and `LifecycleCoordinator`.

## Trigger Conditions
Use for startup failures, missing `workspace.py`, missing manifests, route registration gaps, lifespan errors, health endpoint behavior, startup/shutdown hooks, and production entrypoint issues.

## Inputs
- Workspace root and `AQUILIA_WORKSPACE`/`AQUILIA_ENV` values.
- Error logs or phase where boot fails.
- List of modules expected to load.

## Execution Flow
1. Trace phases: `CREATED -> CONFIGURING -> DISCOVERING -> BOOTSTRAPPING -> READY -> RUNNING`.
2. Confirm `workspace.py` exists and module names are discoverable by `AquiliaRuntime._extract_module_names()`.
3. Inspect imports of `modules.<name>.manifest` and dynamic discovery of `modules/*/manifest.py`.
4. Check `AquiliaServer` setup for Aquilary, RuntimeRegistry, DI, middleware, controller compiler/router, sockets, templates, auth/sessions, and health registry.
5. For request issues, trace `ASGIAdapter.handle_http()` route matching and middleware chain caching.

## Constraints
- Do not bypass `AquiliaRuntime` with generated `runtime/app.py`; runtime.py is the consolidated bootstrap path.
- Do not mutate env values silently; report `AQUILIA_WORKSPACE` and mode assumptions.
- Lifespan startup/shutdown should go through server coordinator paths.

## Implementation Anchors
`aquilia/runtime.py`, `aquilia/entrypoint.py`, `aquilia/server.py`, `aquilia/asgi.py`, `aquilia/lifecycle.py`, `aquilia/health.py`, `tests/test_runtime.py`.

## Examples
- "Why does uvicorn aquilia.entrypoint:app return a 503?"
- "My module manifest imports but routes do not show up."
- "Debug a startup hook that rolls back app startup."

## Failure Handling
`FileNotFoundError` means workspace path resolution failed. Import errors in `DISCOVERING` point to module manifest imports. Lifecycle failures transition to `ERROR` and trigger rollback; inspect the hook and dependency order.
