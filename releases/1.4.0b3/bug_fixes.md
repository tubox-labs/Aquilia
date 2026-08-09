# Bug Fixes & Refactorings — v1.4.0b3

Aquilia v1.4.0b3 resolves several critical bugs across the CLI framework, route introspection engine, native C++ bindings, and docsite build infrastructure.

---

## 1. `aq doctor` and `aq validate` Exited With `0` on Broken Workspaces

### Previous Behavior
Running `aq doctor` or `aq validate` on a workspace with missing databases, unloadable manifests, or broken imports printed red warning/error banners but still exited with process exit code `0`. CI/CD pipelines relying on these commands failed to block broken builds.

### Root Cause
Command bodies caught exceptions and printed banners, but concluded execution without calling `sys.exit()` or returning a non-zero exit code. `doctor.py` and `validate.py` had separate, uncoordinated exit code paths.

### New Behavior
All health checks are now managed by `aquilia.cli.checks`. Process exit codes are calculated by `exit_code_for()`:
- Workspaces with missing files, broken imports, or `ERROR`/`FATAL` findings exit with status `1` (`ExitCode.FAILED`).
- Non-existent workspaces exit with status `3` (`ExitCode.CONFIG`).

### User Impact
CI/CD test suites running `aq validate` or `aq doctor` now accurately catch configuration errors and halt failing pipeline runs.

---

## 2. `aq inspect routes` Displayed Controller Count Instead of Endpoint Count

### Previous Behavior
A module containing a single `UserController` with 5 endpoint methods (`GET /users`, `POST /users`, `GET /users/:id`, `PUT /users/:id`, `DELETE /users/:id`) reported "1 route".

### Root Cause
Legacy inspection logic counted `len(manifest.controllers)` as `route_count`, confusing controller class instances with individual HTTP route handlers.

### New Behavior
`aquilia.cli.introspect.routes` calls `ControllerCompiler` (the same compiler used by `AquiliaServer` at boot) and sums individual compiled `RouteInfo` objects.

```bash
$ aq inspect routes
  Route Inspection
  ======================================================================

  users
     UserController  (prefix: /users)
       GET      /users                                 -> index
       POST     /users                                 -> create
       GET      /users/:id                             -> show
       PUT      /users/:id                             -> update
       DELETE   /users/:id                             -> delete

  ----------------------------------------------------------------------
  Total routes: 5
  Modules:      1
```

---

## 3. Inspection Probed Non-Existent Controller Attributes

### Previous Behavior
`aq inspect routes` attempted to extract routes statically by probing `__controller_routes__`, `__route__`, and `_route_meta`. Every controller failed inspection and printed:
```
!  UserController: routes could not be extracted statically
```

### Root Cause
None of those attributes existed on controller classes. The actual attribute used by the framework is `__route_metadata__`, and proper compilation requires `ControllerCompiler`.

### New Behavior
`extract_routes()` passes the controller class directly to `ControllerCompiler().compile_controller()`, respecting module-level `route_prefix` settings and starter controllers (`.starter("name")`).

---

## 4. Nanobind Leak Warnings on Server/Router Shutdown

### Previous Behavior
Stopping the dev server or running unit tests produced nanobind memory leak warnings on process exit:
```
nanobind: leaked 1 instance of type 'aquilia._core.Router'!
```

### Root Cause
`ControllerRouter` retained a reference to `_native` (`aquilia._core.Router`), and neither `AquiliaServer.shutdown()` nor `ASGIAdapter.shutdown()` cleared router instances during shutdown.

### New Behavior
Added `ControllerRouter.clear()`, which resets `_native = None`, `_native_methods.clear()`, and `_native_routes.clear()`. `AquiliaServer.shutdown()` and `ASGIAdapter.shutdown()` invoke `clear()`, releasing native memory cleanly.

---

## 5. `aqdocx` TS2657 JSX Build Error in `MiddlewareOverview.tsx`

### Previous Behavior
Running `tsc -b` on the `aqdocx` documentation site failed with:
```
TS2657: JSX expressions must have one parent element
```

### Root Cause
The v1.4.0b2 restructure banner `<div>` and the architecture diagram `<div>` were placed as direct children inside `return()` without a parent fragment, causing TypeScript build failures during static site generation.

### New Behavior
Restored single-root returns and positioned the v1.4.0b2 restructure banner inside `MiddlewareOverview.tsx` after the header section. `tsc -b` builds cleanly.
