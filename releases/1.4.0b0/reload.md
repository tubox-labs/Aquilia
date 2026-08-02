# Hot Reload — v1.4.0b0

`aquilia/devplatform/reload/`: `watcher.py` (filesystem events) →
`analyzer.py` (`DependencyGraphAnalyzer`, `ReloadPlan`) → `executor.py`
(`ModuleReloadExecutor`) → `state_preservation.py` (`StateBridgeRegistry`).

## The Reverse-Dependency Bug

**Before this release**, reverse-dependency detection scanned each loaded
module's `__dict__` for values that happened to equal the target module name
by object identity — this essentially never matched anything, since Python
imports don't work that way.

**The AST-based rewrite** in `_static_import_targets()` parses each loaded
module's source with `ast.parse()`, walks `ast.Import`/`ast.ImportFrom`
nodes, and resolves relative imports via `importlib.util.resolve_name()`
against the importing module's actual `__package__`. Results are memoized
per `(file_path, mtime)` so an unchanged dependent isn't re-parsed on every
reload cycle.

**A second bug was found and fixed during that rewrite.** The first version
of `_imports_module()` matched a target as a "reverse dependency" whenever
`module_name.startswith(target + ".")` — intended to catch `from pkg import
submodule` patterns, but it also matched a bare `import aquilia` against
*every* `aquilia.*` submodule, since `"aquilia.devplatform.config".startswith("aquilia.")`
is trivially `True`. This inflated `ReloadPlan.affected_modules` with
unrelated modules on nearly every reload.

Verified with a real loaded-module pair:

```python
>>> import aquilia.devplatform.reload.analyzer as az
>>> import aquilia.devplatform.config
>>> az._get_reverse_deps('aquilia.devplatform.config')
# Before fix:
['aquilia.middleware', 'aquilia.auth.clearance', 'aquilia.asgi', 'aquilia.server',
 'aquilia.versioning.middleware', 'aquilia.admin.site',
 'aquilia.devplatform.core.lifespan', 'aquilia.devplatform.core.protocol',
 'aquilia.devplatform.devserver', 'aquilia.devplatform']
# After fix:
['aquilia.devplatform', 'aquilia.devplatform.core.lifespan',
 'aquilia.devplatform.core.protocol', 'aquilia.devplatform.devserver']
```

`aquilia.middleware` was flagged only because it contains a bare `import
aquilia` statement somewhere — it does not actually import
`aquilia.devplatform.config`. The fix: build fully-resolved candidate
targets at parse time (`base` for the imported module itself, plus
`f"{base}.{alias.name}"` for each `from X import name` clause, to still
catch the legitimate `from pkg import submodule` case) and match only by
**exact** name — no prefix matching in either direction.

```python
def _imports_module(import_targets: set[str], module_name: str) -> bool:
    return module_name in import_targets
```

## `AutoDiscoveryEngine` Integration

`DependencyGraphAnalyzer.__init__` lazily constructs an
`aquilia.discovery.engine.AutoDiscoveryEngine(modules_dir)` when a workspace
root with a `modules/` directory is resolvable (via an explicit constructor
argument or the `AQUILIA_WORKSPACE` env var).

`_diff_workspace_changes(changed_paths)`:
1. Maps each changed path under `modules/` to its top-level workspace module name.
2. Calls `AutoDiscoveryEngine.discover(module_name)` per affected module — this reuses the engine's own incremental mtime+SHA256 cache (`.aquilia/discovery_cache.surp`), so this diff doesn't re-scan unchanged files.
3. Aggregates `ComponentKind` counts (`controller`, `service`, `model`, ...) across the returned `ClassifiedComponent` list.
4. Produces a string like `"Discovery diff: 1 controller, 2 service"`, attached to `ReloadPlan.reason` (when the changed tier is `APP`) and `ReloadPlan.discovery_summary`.

This is best-effort: if no workspace root is resolvable, `modules/` doesn't
exist, or the engine fails to construct, `_diff_workspace_changes()` returns
`""` and the plan falls back to the generic tier-based reason string.

## Stability Tiers → Strategy

`_classify_tier(module_name)` checks path fragments against `_TIER_MAP` (first match wins, order matters):

```python
_TIER_MAP = [
    ("aquilary", StabilityTier.CORE),
    ("/di/", StabilityTier.CORE),
    ("patterns", StabilityTier.CORE),
    ("/db/", StabilityTier.FRAMEWORK),
    ("routing", StabilityTier.FRAMEWORK),
    ("middleware", StabilityTier.FRAMEWORK),
    ("controller", StabilityTier.APP),
    ("models", StabilityTier.APP),
    ("auth", StabilityTier.APP),
    ("sessions", StabilityTier.APP),
    ("debug", StabilityTier.LEAF),
    ("testing", StabilityTier.LEAF),
    ("devplatform", StabilityTier.LEAF),
]
```

Unmatched modules default to `APP` tier. `compute_strategy()` takes the
**minimum** tier value (i.e. most restrictive: `CORE` < `FRAMEWORK` < `APP` <
`LEAF`) across all changed files in the batch, so one `CORE`-tier file
anywhere in a batched change forces `FULL` for the whole batch.

| Max tier in batch | Strategy | Reason |
|---|---|---|
| `CORE` | `FULL` | "Core stability tier changed — full reload required" |
| `FRAMEWORK` | `PARTIAL` | "Framework tier changed — partial reload of dependents" |
| `APP` | `PARTIAL` | discovery diff summary, or generic fallback |
| `LEAF` | `HOT_PATCH` | "Leaf tier changed — hot-patch eligible" |
| (unresolvable path / not in `sys.modules`) | `FULL` | "Changed files not found in sys.modules — possible new module or config change" |

## `ModuleReloadExecutor` Strategies

`aquilia/devplatform/reload/executor.py`:

- **`FULL`** — `_graceful_shutdown_app()` calls `server.graceful_shutdown(timeout=self._shutdown_timeout)` (looked up as `self._runtime.app.server`), wrapped in `asyncio.wait_for(..., timeout=self._shutdown_timeout + 2.0)`, before `os.execv(sys.executable, [sys.executable] + sys.argv)`. **This is new in v1.4.0b0** — previously `_full_reload()` called `os.execv()` immediately, dropping in-flight requests and any unclosed DB pools/effects/tasks. If no `server` reference is found on `runtime.app`, a warning is logged and shutdown is skipped (`asyncio.sleep(0.1)` placeholder) rather than blocking reload indefinitely.
- **`PARTIAL`** — `StateBridgeRegistry.snapshot()` captures long-lived resources by key (`db_connection_pool`, `session_store`, `cache_backend`, `websocket_registry`), each affected module is `importlib.reload()`-ed, then `StateBridgeRegistry.restore()` re-binds the snapshotted resources into the newly-loaded service instances (`AquiliaDatabase.get_active()._pool`, `SessionStoreRegistry.set_active()`, `CacheService.set_backend()`). `_rebind_aquilia_runtime()` then clears and recompiles the controller router. Any `importlib.reload()` failure falls back to `FULL`.
- **`HOT_PATCH`** — swaps `__code__` on matching functions between the old and a freshly `exec`-ed module namespace, without re-importing. Falls back to `PARTIAL` on any failure (missing spec, `exec_module` error, etc.).

`shutdown_timeout` is threaded from `AquiliaDevelopmentConfig.timeout_graceful_shutdown` through `WorkspaceWatcher._handle_changes()` into `ModuleReloadExecutor.__init__`.
