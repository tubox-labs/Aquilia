# Migration Guide — 1.4.0b2 → 1.4.0b3

Aquilia v1.4.0b3 is backward-compatible for standard applications, but introduces breaking changes for internal CLI tools, custom health scripts, and CI/CD pipelines expecting legacy exit code behavior. Everything in the new vector database subsystem is additive — nothing existing changes when you do not adopt it.

---

## Quick assessment

| You have… | Action required |
|---|---|
| A standard `AquiliaServer` application | Bump the version. Nothing else. |
| CI running `aq validate` or `aq doctor` | **Yes** — exit codes are now enforced. See §1. |
| Imports from `aquilia.cli.parsers` | **Yes** — the package is removed. See §2. |
| Test fixtures instantiating `ControllerRouter` / `AquiliaServer` | Recommended — call `.clear()` / `.shutdown()`. See §3. |
| Hand-built `BootContext` objects | **Yes** — DI key renamed. See §4. |
| Custom `BaseSubsystem` subclasses | Review — `_timeout` is now enforced. See §5. |
| Code touching `AdminRateLimiter` privates | **Yes** — use `force_cleanup()`. See §6. |
| Aggressive `/health` polling | Review — the endpoint now runs live checks. See §7. |
| Interest in vector search | Opt-in. See §8. |

---

## 1. Exit Code Contract Changes

In v1.4.0b2 and earlier, `aq doctor` and `aq validate` returned exit code `0` even when findings contained errors. In v1.4.0b3, exit codes are strictly enforced:

- `ExitCode.OK` (`0`): Command succeeded without errors.
- `ExitCode.FAILED` (`1`): At least one `ERROR` or `FATAL` finding was discovered.
- `ExitCode.CONFIG` (`3`): Workspace file missing or unloadable.

### CI/CD Pipeline Migration

If your CI pipeline relies on `aq validate` or `aq doctor`, update scripts to handle non-zero exit codes:

```bash
# BEFORE (in CI pipeline)
aq validate
# Always returned 0, even on broken manifests

# AFTER (in CI pipeline)
aq validate
# Returns exit code 1 if manifest has errors, failing the build as intended.
```

---

## 2. Removed Legacy Parser Modules

The following internal CLI parser modules were removed:
- `aquilia/cli/discovery_cli.py`
- `aquilia/cli/parsers/__init__.py`
- `aquilia/cli/parsers/module.py`
- `aquilia/cli/parsers/workspace.py`

### Replacement

If you had custom scripts importing from `aquilia.cli.parsers`, migrate to `aquilia.cli.core.workspace`:

```python
# BEFORE
from aquilia.cli.parsers.workspace import WorkspaceManifest
manifest = WorkspaceManifest.from_file(Path("workspace.py"))

# AFTER
from aquilia.cli.core.workspace import load_workspace
ws = load_workspace(Path.cwd())
print(ws.module_names)
```

---

## 3. Router Teardown API

If you maintain custom test fixtures that manually instantiate `ControllerRouter` or `AquiliaServer`, invoke `.clear()` or `.shutdown()` during teardown:

```python
# BEFORE
router = ControllerRouter()
router.initialize()
# ... test logic ...
# router left in memory

# AFTER
router = ControllerRouter()
router.initialize()
try:
    # ... test logic ...
finally:
    router.clear()
```

---

## 4. `BootContext` DI Key Renamed

If you build a `BootContext` by hand — an embedder, an alternative runner, or a test — the DI container key changed.

```python
# BEFORE
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state["_di_registry"] = container    # read only by StorageSubsystem, and never set by anything

# AFTER — explicit container
from aquilia.subsystems import DI_CONTAINER_KEY
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state[DI_CONTAINER_KEY] = container

# AFTER — or let the runtime registry supply every app container
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)
```

`BootContext.di_containers()` resolves the explicit container first, then falls back to every container in `registry.di_containers`. It returns an empty list when neither is present, and subsystems treat that as "DI is not wired here" and skip registration with a debug log.

**Nothing can regress**, because `"_di_registry"` was never set by any code path — it was a dead branch. `AquiliaServer` applications are unaffected: the server does not drive `BootContext` subsystems.

Full detail: [subsystem_boot_contract.md](subsystem_boot_contract.md#1-bootcontextdi_containers--one-di-resolution-path).

---

## 5. `BaseSubsystem._timeout` Is Now Enforced

`initialize()` now wraps `_do_initialize` in `asyncio.wait_for(..., timeout=self._timeout)`. The declared default has always been 30 seconds; it was simply never read.

Two things to check in a custom subsystem:

**Cancellation safety.** `wait_for` cancels the coroutine on timeout. If `_do_initialize` acquires a resource before its first `await`, release it in a `finally`:

```python
async def _do_initialize(self, ctx: BootContext) -> None:
    handle = acquire_something()
    try:
        await self._connect(handle)
    except asyncio.CancelledError:
        handle.close()
        raise
```

**Legitimately unbounded init.** Set `_timeout = 0` (or negative) to disable the bound rather than picking an arbitrarily large number:

```python
class IndexRebuildSubsystem(BaseSubsystem):
    _name = "index-rebuild"
    _timeout = 0        # operator-supervised; no meaningful upper bound
```

A timeout is not an exception — it returns `HealthStatus(status=UNHEALTHY, message="Initialization timed out after 30s")`, so a host that treats `UNHEALTHY + required` as fatal stops the boot and one that does not carries on degraded.

Related: `required` may be computed during `_do_initialize` (`VectorDBSubsystem` raises it when stores are declared). Read it **after** `initialize()` returns:

```python
# WRONG — reads the class default
if subsystem.required: ...
status = await subsystem.initialize(ctx)

# RIGHT
status = await subsystem.initialize(ctx)
if status.status is SubsystemStatus.UNHEALTHY and subsystem.required:
    raise RuntimeError(status.message)
```

---

## 6. `AdminRateLimiter` Cleanup

Replace private-state manipulation with the new public method:

```python
# BEFORE
limiter._last_cleanup = 0
limiter._maybe_cleanup()
cleaned = before - len(limiter._login_records)

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
```

`_maybe_cleanup()` remains for the periodic path and is unchanged. `force_cleanup()` never clears an active lockout — only records past their `lockout_until` with no recent attempts are removed. Releasing a locked-out principal is still `clear_login_attempts()`.

If you configure admin, its lifecycle now runs automatically (audit flush, rate-limit sweep, DI wiring for `CacheService` and `TaskManager`). If you previously called `AdminLifecycle.on_startup()` yourself as a workaround, you can remove it — `on_startup` is idempotent, so leaving it is also safe.

Full detail: [admin_lifecycle.md](admin_lifecycle.md).

---

## 7. `/health` Runs Live Checks

`ASGIAdapter`'s `/health` handler now calls `await registry.run_checks()` before rendering, so a dependency that died after boot is no longer masked by the boot-time snapshot.

**Response shape is unchanged.** Values may now differ from the boot snapshot — that is the point.

**Cost.** One check invocation per registered subsystem per request. `StorageSubsystem` and `VectorDBSubsystem` register live checks; for storage that is a backend liveness probe, for vectordb it is `VectorRegistry.health()` across configured stores. `run_checks()` is a no-op when nothing registered a check, so apps without those subsystems pay nothing.

If a load balancer polls `/health` aggressively and you would rather it not touch the backends, point it at a cheaper endpoint and reserve `/health` for real health assessment.

---

## 8. Adopting the Vector Database (opt-in)

Nothing here is required. An install without `elips`, or a workspace without a `vectordb` block, behaves exactly as it did in v1.4.0b2.

```bash
pip install 'aquilia[vectordb]'
```

> **Python 3.10:** `elips 1.1.0` publishes no cp310 wheels, so the extra carries `python_version >= '3.11'`. On 3.10 it installs nothing and `aquilia.vectordb` degrades exactly as on any install without the driver — `VectorNotInstalledFault` at first use. Without the marker, `aquilia[full]` would be unresolvable on 3.10 rather than simply omitting vector support.

**Step 1 — declare stores** in `workspace.py`:

```python
from aquilia.workspace import Workspace

workspace = (
    Workspace("myapp")
    .vectordb(
        path="./.aquilia/vectors",
        stores={"default": {"dimension": 384, "metric": "cosine"}},
    )
)
```

or in `aquilia.config.py`:

```python
class BaseEnv(AquilaConfig):
    class vectordb(AquilaConfig.VectorDB):
        enabled   = True
        dimension = 384
```

**Step 2 — declare models** in `modules/<app>/vector_models.py` (or a `vector_models/` package). The directory is separate from `models/` deliberately: importing a vector model imports `aquilia.vectordb`, and scanning `models/` for them would drag the optional dependency into every app that has SQL models.

```python
from aquilia.vectordb import VectorModel, KeyField, TextField, VectorField, Field

class Document(VectorModel):
    key:    str         = KeyField(prefix="doc_")
    body:   str         = TextField(embed=True, min_length=1)
    vector: list[float] = VectorField(dimension=384)
    source: str         = Field(default="web", indexed=True)

    class Meta:
        collection = "documents"
        store = "default"
```

**Step 3 — optionally declare them explicitly** in the module manifest:

```python
manifest = AppManifest(
    name="blog",
    version="1.0.0",
    vector_models=["modules.blog.vector_models"],
)
```

Discovery finds them either way. A manifest-declared ref that fails to import or resolve is a **hard fault** (`ModelRegistrationFault`); a discovery-scanned file that fails is logged and skipped. An explicit declaration is a promise, and a silently-missing model would surface later as an empty search rather than an error.

**Step 4 — verify**:

```bash
aq vectordb status     # driver installed? stores read correctly?
aq vectordb models     # slot routing as intended?
aq doctor              # includes the new vectordb.driver check
```

### Deployment constraints

- **elips is single-writer per directory.** With `workers > 1`, every worker after the first fails to acquire the lock — a startup fault, not a degradation. Give each worker its own store path, or set `read_only=True` on the shared store so workers search without the writer lock (writes then raise).
- **Set `auto_create=False` in production** so a missing store fails the boot instead of serving an empty index.
- **`VectorDBSubsystem` is not driven by `AquiliaServer`.** Like every `BootContext` subsystem, it is initialized by the host. See [vectordb.md](vectordb.md#wiring-the-store-lifecycle) for a module lifecycle-hook example. The `aq vectordb` commands need none of this — they configure and shut down `VectorRegistry` themselves.

### What is *not* a migration

Changing `dimension`, `metric`, or the embedder on an existing store. elips persists that identity on disk and refuses a reopen that disagrees, and vectors from two embedding models occupy incompatible spaces — mixing them makes distances meaningless while still returning a confident-looking ranked list. Use `aq vectordb reembed --model <M> --to-embedder <URI>`, which refuses an in-place dimension change and names the store to reconfigure.

Full detail: [vectordb.md](vectordb.md) · [vectordb_cli.md](vectordb_cli.md)

---

## Upgrade Checklist

- [ ] Upgrade `aquilia` to `1.4.0b3` in `pyproject.toml` or `requirements.txt`.
- [ ] Run `aq doctor` to perform a full health audit of your workspace.
- [ ] Remove any imports from `aquilia.cli.parsers`.
- [ ] Verify that CI/CD workflows handle non-zero exit codes from `aq validate`.
- [ ] Ensure test fixtures call `server.shutdown()` or `router.clear()` to prevent nanobind leak warnings.
- [ ] Rename `shared_state["_di_registry"]` to `shared_state[DI_CONTAINER_KEY]` in any hand-built `BootContext`.
- [ ] Confirm custom `BaseSubsystem` subclasses are cancellation-safe, or set `_timeout = 0`.
- [ ] Replace `AdminRateLimiter` private-state pokes with `force_cleanup()`.
- [ ] If `/health` is polled by a load balancer, budget for live check invocations.
- [ ] If adopting vector search: install `aquilia[vectordb]`, declare stores and models, verify with `aq vectordb status` / `aq vectordb models`.

---

## Deprecated Features

None in this release.

## Removed Features

- `aquilia/cli/discovery_cli.py`
- `aquilia/cli/parsers/` (`__init__.py`, `module.py`, `workspace.py`)

Both were internal CLI helpers with no documented public API. See §2 for the replacement.

---

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12+ |
| Python (with `vectordb` extra) | **3.11** | 3.12+ |
| OS | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |
| SQLite | 3.35.0 | 3.42.0+ |
| `elips` (optional) | 1.1.0 | 1.1.0+ |

---

## Related documentation

- [README.md](README.md) — release overview and highlights
- [vectordb.md](vectordb.md) · [vectordb_cli.md](vectordb_cli.md) — the new vector subsystem
- [subsystem_boot_contract.md](subsystem_boot_contract.md) — `BootContext`, timeouts, live health
- [admin_lifecycle.md](admin_lifecycle.md) — admin startup/shutdown and rate limiter
- [cli_modernization.md](cli_modernization.md) · [checks_engine.md](checks_engine.md) — CLI architecture
- [bug_fixes.md](bug_fixes.md) — every defect fixed in this release
