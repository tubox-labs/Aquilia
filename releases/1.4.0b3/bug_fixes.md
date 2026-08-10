# Bug Fixes & Refactorings — v1.4.0b3

Aquilia v1.4.0b3 resolves several critical bugs across the CLI framework, route introspection engine, subsystem boot layer, admin lifecycle, native C++ bindings, and docsite build infrastructure.

Regression coverage for the subsystem and admin fixes: `tests/test_subsystem_boot_contract.py`.

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

## 5. `StorageRegistry` Was Never Registered Into DI

### Previous Behavior
A host that booted `StorageSubsystem` through `BootContext` got working storage backends, but `StorageRegistry` was not resolvable from DI. Constructor injection of `StorageRegistry` failed with a resolution error.

### Root Cause
`StorageSubsystem._register_di()` read `ctx.shared_state.get("_di_registry")` — a key **nothing in the codebase ever sets**. The branch was permanently dead and failed silently, since the guard was `if registry_obj and hasattr(registry_obj, "register")`. `EffectSubsystem` used a different key (`"container"`), so the two subsystems could never both be wired by the same host. Neither consulted `BootContext.registry`, so the normal case — a context carrying a `RuntimeRegistry` — registered nothing.

### New Behavior
`BootContext.di_containers()` is the single resolution path: `shared_state[DI_CONTAINER_KEY]` first, then every container in `registry.di_containers`. Both subsystems call it, and both register into **all** app containers rather than one — matching how `AquiliaServer` registers app-scoped values.

### User Impact
`AquiliaServer` applications are unaffected (the server does not use this path). Embedders and tests that build a `BootContext` now get `StorageRegistry` and the effect registry actually wired. Anyone who set `"_di_registry"` should rename it to `DI_CONTAINER_KEY`; it never worked, so nothing can regress.

See [subsystem_boot_contract.md](subsystem_boot_contract.md#1-bootcontextdi_containers--one-di-resolution-path).

---

## 6. `BaseSubsystem._timeout` Was Declared But Never Enforced

### Previous Behavior
`BaseSubsystem` declared `_timeout: float = 30.0` and its docstring promised "timeout-protected initialization". A subsystem blocking on an unreachable dependency — an S3 endpoint behind a dropped route, a vector store whose lock holder never exits — hung the boot indefinitely, with no log line and no health status.

### Root Cause
Nothing read the value. `initialize()` awaited `self._do_initialize(ctx)` unbounded.

### New Behavior
`_do_initialize` is wrapped in `asyncio.wait_for(..., timeout=self._timeout)`. A timeout produces `UNHEALTHY` with `Initialization timed out after 30s` and an `ERROR` log line, so a host that treats `UNHEALTHY + required` as fatal stops the boot. A non-positive `_timeout` disables the bound deliberately, for a subsystem whose init legitimately has no upper limit.

### User Impact
A misconfigured optional subsystem can no longer wedge a deployment in "starting" forever. Custom `BaseSubsystem` subclasses must be cancellation-safe in `_do_initialize` — `wait_for` cancels the coroutine — or opt out with `_timeout = 0`.

---

## 7. `EffectSubsystem.health_check()` Always Raised `TypeError`

### Previous Behavior
Calling `EffectSubsystem.health_check()` reported the effect registry as unhealthy with a confusing message, regardless of its actual state.

### Root Cause
The method constructed `HealthStatus(..., metadata=health)`. `HealthStatus` (`aquilia/health.py`) has no `metadata` field — its fields are `name`, `status`, `latency_ms`, `message`, `details`, `checked_at`. Every call raised `TypeError: __init__() got an unexpected keyword argument 'metadata'`, which the caller's broad `except Exception` converted into an unhealthy status.

```python
# BEFORE
return HealthStatus(name=self._name, status=..., metadata=health)

# AFTER
return HealthStatus(name=self._name, status=..., details=health)
```

The import also moved to module scope and to `aquilia.health` directly rather than through the `aquilia.subsystems.base` re-export, and the return type is now annotated.

### User Impact
`/health` and any host calling `health_check()` now report the effect registry's real state.

---

## 8. `/health` Served a Boot-Time Snapshot

### Previous Behavior
A storage backend that went offline an hour after boot kept reporting `HEALTHY` until the process restarted.

### Root Cause
`StorageSubsystem._register_health()` published one `storage.<alias>` status per backend at boot and stopped. `HealthRegistry.register_check()` existed but nothing used it, and `ASGIAdapter`'s `/health` handler read `registry.to_dict()` — a pure snapshot read with no refresh.

### New Behavior
`StorageSubsystem` and `VectorDBSubsystem` register a live aggregate check (`health.register_check(self._name, self.health_check)`) alongside the per-alias snapshot, and `ASGIAdapter` calls `await registry.run_checks()` before rendering. Per-alias entries remain a boot snapshot (they describe what was configured); the aggregate entries are live.

### User Impact
`/health` can detect a dead dependency without a restart. The cost is one check invocation per registered subsystem per request — `run_checks()` is a no-op when nothing registered a check, so apps without storage or vectordb pay nothing. A check that raises is caught and recorded as `UNHEALTHY` rather than failing the endpoint.

---

## 9. Admin Lifecycle Hooks Were Never Invoked

### Previous Behavior
Configuring the admin dashboard produced working routes and nothing else. Buffered audit entries were lost on every restart, `AdminRateLimiter` records grew for the process lifetime, `AdminTasks.enqueue_*` silently ran inline, admin's cache integration ran unbacked, and admin security DI providers were absent.

### Root Cause
`AquiliaServer._wire_admin_integration()` registered routes and stopped there. `AdminLifecycle.on_startup()` / `on_shutdown()` were implemented and tested in isolation but called by nothing — there was no `LifecycleCoordinator` entry for admin and no admin step in the server's startup sequence. The symptom was invisible: routes worked, and the missing upkeep showed only as slow memory growth and an audit log that reset on deploy.

### New Behavior
`AquiliaServer.startup()` gained Step 3.25 — after DI containers exist, before the task manager starts — gated on `config["integrations"]["admin"]`, with a mirror in `shutdown()`. Failure is non-fatal: a warning is logged, `_admin_subsystems` stays `None`, admin routes still serve, and only background upkeep is off.

### User Impact
Audit logs flush on graceful shutdown; the rate limiter is swept; `TaskManager` and `CacheService` are resolved from DI. Applications that do not configure admin are unaffected. No migration is required.

See [admin_lifecycle.md](admin_lifecycle.md#1-admin-lifecycle-hooks-never-ran).

---

## 10. `AdminTasks.rate_limit_cleanup()` No-Opped on Freshly Booted Hosts

### Previous Behavior
`rate_limit_cleanup()` returned `{"cleaned_login": 0, "cleaned_sensitive": 0}` and removed nothing, for the first hour of a host's uptime — indistinguishable from "there was nothing stale to clean".

### Root Cause
The task set `limiter._last_cleanup = 0` and called `_maybe_cleanup()`, expecting the interval guard to fall through. But that guard is `time.monotonic() - self._last_cleanup < self.cleanup_interval`, and `time.monotonic()` is **not** wall-clock — on Linux it is time since boot. On a host up for less than `cleanup_interval` (default 3600s), `time.monotonic()` is itself below 3600, so `now - 0 < 3600` held and the sweep returned immediately. Fresh containers, which restart constantly, spent a disproportionate share of their life inside that window.

The surrounding `max(0, before - after)` length arithmetic hid the same fragility from the other end: it cannot distinguish "nothing was stale" from "the sweep never ran", and would go negative if a concurrent request added a record between the two reads.

### New Behavior
The sweep is factored out of the interval check into `_sweep(now)`, which returns exact `(login, sensitive)` removal counts, and exposed as `AdminRateLimiter.force_cleanup()`:

```python
# BEFORE
before_login = len(limiter._login_records)
limiter._last_cleanup = 0
limiter._maybe_cleanup()
cleaned_login = max(0, before_login - len(limiter._login_records))

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
```

### User Impact
The cleanup task works on a freshly booted host and reports accurate counts. An active lockout is still never cleared — `_sweep` only removes records past their `lockout_until` with no recent attempts — so `force_cleanup()` cannot be used to release a locked-out principal. That remains `clear_login_attempts()`.

See [admin_lifecycle.md](admin_lifecycle.md#2-adminratelimiterforce_cleanup--public-sweep-api).

---

## 11. Workspace Integration Detection Reported Phantom Integrations

### Previous Behavior
`aq doctor` reported subsystem findings for integrations a workspace had never declared. A workspace with no `templates` integration could emit `AQ_TEMPLATE_DIR_MISSING`, and the storage/cache/mail probes fired against nothing.

### Root Cause
`aquilia.cli.checks.subsystems._integration()` resolved an integration by attribute lookup: `getattr(workspace_obj, name)`. But `Workspace` exposes builder **methods** named `storage`, `vectordb`, `i18n`, `tasks` and `templates`. `getattr` returned the bound method — truthy — so every workspace looked like it had declared every one of those subsystems.

### New Behavior
`_integration()` treats `Workspace._integrations` as authoritative, since it holds exactly what `integrate()` and the builder methods recorded. Attribute lookup remains only as a fallback for non-`Workspace` objects, and it now skips callables:

```python
declared = getattr(obj, "_integrations", None)
if isinstance(declared, dict):
    found = declared.get(name)
    if found is not None:
        return found

for attr in (name, f"{name}_integration", f"_{name}"):
    found = getattr(obj, attr, None)
    if found is not None and not callable(found):
        return found
return None
```

### User Impact
`aq doctor` and `aq validate` no longer emit findings for undeclared subsystems. Since findings at `WARN` do not affect the exit code, this changes report noise rather than CI outcomes — except where a phantom integration produced an `ERROR`.

---

## 12. `aqdocx` TS2657 JSX Build Error in `MiddlewareOverview.tsx`

### Previous Behavior
Running `tsc -b` on the `aqdocx` documentation site failed with:
```
TS2657: JSX expressions must have one parent element
```

### Root Cause
The v1.4.0b2 restructure banner `<div>` and the architecture diagram `<div>` were placed as direct children inside `return()` without a parent fragment, causing TypeScript build failures during static site generation.

### New Behavior
Restored single-root returns and positioned the v1.4.0b2 restructure banner inside `MiddlewareOverview.tsx` after the header section. `tsc -b` builds cleanly.

---

## Related documentation

- [subsystem_boot_contract.md](subsystem_boot_contract.md) — full detail on fixes 5–8
- [admin_lifecycle.md](admin_lifecycle.md) — full detail on fixes 9–10
- [vectordb.md](vectordb.md) — the new vector subsystem
- [checks_engine.md](checks_engine.md) — the check registry fix 11 lives in
- [migration.md](migration.md) — upgrade steps and compatibility matrix
