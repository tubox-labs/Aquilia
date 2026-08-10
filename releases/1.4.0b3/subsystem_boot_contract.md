# Subsystem Boot Contract — v1.4.0b3

The `aquilia.subsystems` package gained a documented, enforced contract. Five defects found in the 2026-08-09 subsystem audit are fixed here, and the package's role relative to `AquiliaServer` is now stated explicitly instead of implied.

Regression coverage: `tests/test_subsystem_boot_contract.py`.

---

## Overview

| Change | Kind |
|---|---|
| `BootContext.di_containers()` + `DI_CONTAINER_KEY` | New API — single DI resolution path |
| `_timeout` actually enforced in `BaseSubsystem.initialize()` | Behavioural fix |
| `BootContext` population contract documented | Documentation |
| `StorageSubsystem` DI registration repaired | Bug fix |
| `EffectSubsystem` DI registration repaired | Bug fix |
| `EffectSubsystem.health_check()` constructs a valid `HealthStatus` | Bug fix |
| `StorageSubsystem` / `VectorDBSubsystem` register a **live** health check | Bug fix |
| `required` computed-after-`initialize()` contract documented | Documentation |
| `aquilia.subsystems` package role documented; no `SubsystemOrchestrator` | Documentation |

---

## Who drives subsystems

Previously the package docstring said "the server orchestrates subsystems in priority order". It does not. `AquiliaServer` boots storage, cache, tasks, mail and effects through its own ordered `_setup_*` methods, and that is the production path.

`aquilia.subsystems` is the entry point for hosts that drive subsystems **themselves** — embedders, alternative runners, and tests — where there is no `AquiliaServer` to own the sequence. Both paths share the same underlying registries (`StorageRegistry`, `VectorRegistry`, `EffectRegistry`), so behaviour does not diverge; only the orchestration does.

There is deliberately **no `SubsystemOrchestrator`**. Adding one would create a second production boot sequence to keep in sync with the server's. A host that wants ordered boot composes it directly:

```python
from aquilia.health import SubsystemStatus
from aquilia.subsystems import BootContext, EffectSubsystem, StorageSubsystem

subsystems = sorted([StorageSubsystem(), EffectSubsystem()], key=lambda s: s.priority)
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)

for sub in subsystems:
    status = await sub.initialize(ctx)
    ctx.health.register(sub.name, status)
    # `required` is only final after initialize() — see below.
    if status.status is SubsystemStatus.UNHEALTHY and sub.required:
        raise RuntimeError(f"required subsystem {sub.name} failed: {status.message}")

# ... shutdown in reverse priority order
for sub in reversed(subsystems):
    await sub.shutdown()
```

---

## 1. `BootContext.di_containers()` — one DI resolution path

### Previous API

Each subsystem invented its own `shared_state` key and its own resolution rule.

```python
# StorageSubsystem._register_di  — BEFORE
registry_obj = ctx.shared_state.get("_di_registry")
if registry_obj and hasattr(registry_obj, "register"):
    provider = ValueProvider(value=self._registry, token=StorageRegistry, scope="app")
    registry_obj.register(provider)
```

```python
# EffectSubsystem._register_with_di  — BEFORE
container = ctx.shared_state.get("container")
if container:
    self._registry.register_with_container(container)
```

**Why it worked (and why it did not).** `"_di_registry"` is a key **nothing in the codebase ever sets**. `StorageRegistry` was therefore never registered into DI — the branch was permanently dead, silently. `EffectSubsystem` used a different key, `"container"`, so a host that populated one got exactly one of the two subsystems wired. Neither consulted `BootContext.registry`, so a context built with a `RuntimeRegistry` — the normal case — registered nothing at all.

### New API

```python
DI_CONTAINER_KEY = "container"

@dataclass
class BootContext:
    def di_containers(self) -> list[Any]:
        """Return every DI container a subsystem should register itself into."""
        explicit = self.shared_state.get(DI_CONTAINER_KEY)
        if explicit is not None and hasattr(explicit, "register"):
            return [explicit]

        containers = getattr(self.registry, "di_containers", None)
        if isinstance(containers, dict):
            return [c for c in containers.values() if hasattr(c, "register")]
        if isinstance(containers, (list, tuple)):
            return [c for c in containers if hasattr(c, "register")]
        return []
```

```python
# StorageSubsystem._register_di  — AFTER
containers = ctx.di_containers()
if not containers:
    self._logger.debug("No DI container in boot context -- skipping StorageRegistry registration")
    return

for container in containers:
    container.register(ValueProvider(value=self._registry, token=StorageRegistry, scope="app"))
```

### Why it is better

- **One key, one rule.** Subsystems must not invent their own `shared_state` key; they call `di_containers()`. A misspelled key can no longer silently disable registration.
- **Explicit container wins.** An embedder can target one container without constructing a `RuntimeRegistry`.
- **All containers, not one.** `registry.di_containers` holds one container per app. Returning all of them matches how `AquiliaServer` registers app-scoped values — into every container, not the first one. Registering into only one made the registry resolvable from some apps and not others.
- **Duck-typed, defensively.** Entries without a `register` attribute are filtered out, so a malformed registry degrades to "DI is not wired here" rather than raising mid-boot.

### Behavioural changes

| Context shape | Before | After |
|---|---|---|
| `shared_state["container"]` set | Effects wired; storage not | Both wired into that container |
| `shared_state["_di_registry"]` set | Nothing (key read only by storage, and never set by anything) | Ignored — not a well-known key |
| `registry=RuntimeRegistry(...)` with app containers | Nothing wired | Both wired into **every** app container |
| Neither | Silent no-op | Debug log, then skip |

### Migration

If you built a `BootContext` by hand and set `"_di_registry"`, rename it:

```python
# BEFORE
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state["_di_registry"] = container   # never actually worked

# AFTER
from aquilia.subsystems import DI_CONTAINER_KEY
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state[DI_CONTAINER_KEY] = container

# or, when you already have a RuntimeRegistry:
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)
```

No application code is affected: `AquiliaServer` does not use this path, and the key it replaces never worked.

---

## 2. `_timeout` is now enforced

### Previous behaviour

`BaseSubsystem` declared `_timeout: float = 30.0` and documented "timeout-protected initialization". Nothing read the value.

```python
# BEFORE
async def initialize(self, ctx: BootContext) -> HealthStatus:
    start = time.monotonic()
    try:
        await self._do_initialize(ctx)      # unbounded
        ...
```

A subsystem blocking on an unreachable dependency — an S3 endpoint behind a dropped route, a vector store whose lock holder never exits — hung the boot forever, with no log line and no health status.

### New behaviour

```python
# AFTER
if self._timeout and self._timeout > 0:
    await asyncio.wait_for(self._do_initialize(ctx), timeout=self._timeout)
else:
    await self._do_initialize(ctx)
```

```python
except asyncio.TimeoutError:
    elapsed = (time.monotonic() - start) * 1000
    message = f"Initialization timed out after {self._timeout:g}s"
    self._logger.error("%s %s", self._name, message)
    return HealthStatus(
        name=self._name,
        status=SubsystemStatus.UNHEALTHY,
        latency_ms=elapsed,
        message=message,
    )
```

A timeout degrades to `UNHEALTHY` with a named cause, exactly like any other initialization failure. A host that treats `UNHEALTHY + required` as fatal stops the boot; one that does not carries on degraded.

### Edge cases

- **`_timeout = 0` or negative disables the bound.** Deliberate: a subsystem whose init legitimately has no upper bound (a long index rebuild under operator supervision) can opt out rather than pick an arbitrary large number.
- **`asyncio.wait_for` cancels the coroutine.** `_do_initialize` must be cancellation-safe. Every in-tree subsystem is; a custom subsystem that acquires a resource before its first `await` should release it in a `finally`.
- **Per-subsystem values.** `VectorDBSubsystem` sets `_timeout = 60.0` because opening a store rebuilds its index — slower than a socket connect. The base default stays 30s.

### User impact

A misconfigured optional subsystem can no longer wedge a deployment in "starting" forever. Existing subsystems that initialize quickly are unaffected — the wrapper adds one `wait_for` frame.

---

## 3. `required` is computed, not static

`_required` is a class attribute, but `VectorDBSubsystem` raises it to `True` inside `_do_initialize` when stores are declared. `BaseSubsystem` now documents the resulting contract:

> `required` may be computed from configuration during `_do_initialize`. Read it **after** `initialize()` returns, never before — beforehand it only holds the class default.

```python
# WRONG — reads the class default, always False for vectordb
if subsystem.required:
    ...
status = await subsystem.initialize(ctx)

# RIGHT
status = await subsystem.initialize(ctx)
if status.status is SubsystemStatus.UNHEALTHY and subsystem.required:
    raise RuntimeError(...)
```

An orchestrator that checks `required` first would treat a declared-but-unopenable vector store as optional and boot into a state where every search returns an empty list.

---

## 4. `EffectSubsystem.health_check()` constructed an invalid `HealthStatus`

### Previous behaviour

```python
# BEFORE
async def health_check(self):
    from aquilia.subsystems.base import HealthStatus, SubsystemStatus   # re-export
    ...
    return HealthStatus(
        name=self._name,
        status=...,
        metadata=health,        # <- no such field
    )
```

### Root cause

`HealthStatus` (`aquilia/health.py`) has fields `name`, `status`, `latency_ms`, `message`, `details`, `checked_at`. There is no `metadata`. Every call raised `TypeError: __init__() got an unexpected keyword argument 'metadata'`, which the caller's `except Exception` turned into an unhealthy status with a confusing message — so the effect subsystem reported unhealthy whenever it was asked, regardless of actual state.

### New behaviour

```python
# AFTER
from aquilia.health import HealthStatus, SubsystemStatus   # module-level, canonical import

async def health_check(self) -> HealthStatus:
    ...
    return HealthStatus(
        name=self._name,
        status=...,
        details=health,
    )
```

The import moved to module scope and to `aquilia.health` directly, and the return type is annotated. `details` is the field that `HealthStatus` actually carries.

### User impact

`/health` and any host calling `EffectSubsystem.health_check()` now report the effect registry's real state. Previously the effect entry was permanently unhealthy once checked.

---

## 5. `/health` reflects live state, not the boot snapshot

### Previous behaviour

`StorageSubsystem._register_health()` published one `storage.<alias>` status per backend at boot and stopped there. `HealthRegistry.register_check()` existed but nothing used it, and `ASGIAdapter`'s `/health` handler read `registry.to_dict()` — a pure snapshot read.

A backend that went offline an hour after boot kept reporting `HEALTHY` until the process restarted.

### New behaviour

Both `StorageSubsystem` and `VectorDBSubsystem` now register a live aggregate check alongside the per-alias snapshot:

```python
# StorageSubsystem._register_health / VectorDBSubsystem._register_health
health.register_check(self._name, self.health_check)
```

and `ASGIAdapter` refreshes before rendering:

```python
# Refresh any subsystem that registered a live check, so a dependency that
# died after boot is not masked by the boot-time snapshot.
await registry.run_checks()
health_report = registry.to_dict()
```

### Behavioural changes

- The per-alias `storage.<alias>` / `vectordb.<alias>` entries remain a **boot-time snapshot** — they name what was configured and how it looked at open.
- The aggregate `storage` / `vectordb` entries are now **live** and re-evaluated on each `/health` request.
- `run_checks()` is a **no-op when nothing registered a check**, so an app with no storage or vector subsystem pays nothing.

### Performance implications

`/health` now costs one check invocation per registered subsystem per request. For storage that is a backend liveness probe; for vectordb it is `VectorRegistry.health()` across configured stores. If `/health` is polled aggressively by a load balancer, that cost is real and proportional to the number of registered checks — the trade is a health endpoint that can actually detect a dead dependency.

### Edge cases

- A check that raises is caught by `HealthRegistry.run_checks()` and recorded as `UNHEALTHY` with the exception message, so one broken probe cannot fail the whole endpoint.
- `latency_ms` on a live-checked entry is the check's own duration, not the boot duration.

---

## Compatibility notes

| Surface | Compatibility |
|---|---|
| `AquiliaServer` applications | Unaffected — the server does not drive `BootContext` subsystems |
| `BootContext(...)` constructor | Unchanged; all new fields optional, `di_containers()` is additive |
| `shared_state["_di_registry"]` | No longer read. It never worked, so nothing can regress |
| `shared_state["container"]` | Still honoured, now via `DI_CONTAINER_KEY` |
| Custom `BaseSubsystem` subclasses | Must be cancellation-safe in `_do_initialize`; set `_timeout = 0` to opt out |
| `EffectSubsystem.health_check()` | Signature unchanged; now returns instead of raising |
| `/health` response body | Same shape; values may now differ from the boot snapshot |

---

## Related documentation

- [`vectordb.md`](vectordb.md) — `VectorDBSubsystem`, which exercises the computed-`required` and 60s-timeout paths
- [`admin_lifecycle.md`](admin_lifecycle.md) — the server-side lifecycle fix in the same audit
- [`bug_fixes.md`](bug_fixes.md) — the full defect list
- [`migration.md`](migration.md) — upgrade steps
