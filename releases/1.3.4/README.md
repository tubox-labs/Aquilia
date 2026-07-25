# Aquilia v1.3.4 Release Notes — "Structural Integrity & Controller Expansion"

Aquilia v1.3.4 is a major architecture audit and feature release focusing on framework stability, registry correctness, controller integrity, workspace discovery robustness, and scalability. 

This release combines **Phase 1** (registry, workspace, config, and runtime audit fixes) with **Phase 2** (controller system audit fixes, strict resolved-import discovery mode, distributed throttle backends, and Resource / ViewSet CRUD controllers).

---

## Table of Contents

1. [Phase 1: Round 1 Bugfixes](bugfixes_r1.md)
   - `Secret` positional-value disambiguation
   - `ManifestWriter` post-write AST validation
   - `DependencyGraph` recursive Tarjan & BFS algorithm stack overflows
   - O(n²) manifest registry lookup optimization
   - `AQUILIA_FAIL_FAST=1` startup failure bypass
2. [Phase 1: Round 2 Bugfixes](bugfixes_r2.md)
   - Discovery cache SHA-256 I/O optimization via mtime/size fast-path
   - `imports` field dependency graph inclusion & bidirectional manifest sync
   - Autodiscovery failure logging for broken modules
   - `surp` decode error propagation fix
   - Exec-based workspace discovery fallback
   - Two-phase static AST manifest loader
3. [Phase 1: Performance Improvements](performance.md)
   - Tarjan SCC iterative graph conversion
   - O(1) manifest index lookup
   - Discovery cache mtime/size I/O bypass
4. [Phase 1: Manifest System Changes](manifest_system.md)
   - Bidirectional `imports` and `depends_on` synchronization
   - Legacy field deprecations
5. [Phase 1: Workspace Discovery Enhancements](workspace_discovery.md)
   - Executive module discovery via `_load_workspace_from_exec()`
6. [Phase 1: CLI Updates](cli.md)
   - `aq validate --deprecated` flag
7. [Phase 2: Controller System Audit Fixes](controller_audit.md)
   - Lifecycle hook bypass on simple routes (CRITICAL)
   - Token generation during session-only auth (SECURITY)
   - Forward-reference type resolution in DI (BUG)
   - Dynamic segment route conflict detection (BUG)
   - Controller class-level cache flushing (ARCH)
   - Router URL generation O(1) performance (PERF)
8. [Phase 2: Strict Resolved-Import Discovery Mode](strict_discovery.md)
   - `StrictDiscoveryEngine` vs AST mode
   - Transitive inheritance and aliased imports
   - CLI usage (`aq discover --strict`)
9. [Phase 2: Distributed Throttle Backends](distributed_throttle.md)
   - `ThrottleBackend` protocol
   - `MemoryThrottleBackend` (sliding window, async-safe)
   - `RedisThrottleBackend` (distributed, fail-open)
   - New `Throttle` API and configuration
10. [Phase 2: Resource / ViewSet CRUD Controllers](resource_viewset.md)
    - Auto-generated CRUD routes
    - `@action` decorator for custom endpoints
    - `ReadOnlyResource`, `CRUDResource`, and Mixins
11. [Migration Guide](migration.md)
    - Complete migration guide for all Phase 1 & Phase 2 changes

---

## Quick Examples

### Explicit `Secret` API
```python
# Positional value is always literal; env lookup requires env=
db_pass = Secret(env="MY_DATABASE_PASS")  # explicit env-var
db_pass = Secret("literal-value")         # literal value, no env lookup
```

### Resource CRUD Controller
```python
from aquilia.controller.resource import CRUDResource, action

class UserResource(CRUDResource):
    # Auto-registers GET /, GET /{id:int}, POST /, PUT /{id:int}, PATCH /{id:int}, DELETE /{id:int}
    id_param = "id"
    id_type = "int"

    async def list(self, ctx):
        return {"users": []}

    async def retrieve(self, ctx, id: int):
        return {"id": id, "name": "Alice"}
        
    @action(methods=["POST"], detail=True)
    async def deactivate(self, ctx, id: int):
        return {"status": "deactivated"}
```

### Distributed Throttle (Redis)
```python
from aquilia.controller.throttle import Throttle

throttle = Throttle.with_redis(
    url="redis://localhost:6379",
    limit=100,
    window=60
)
```

### Strict Discovery Mode
```bash
# Discover dynamic, aliased, or re-exported classes using true MRO resolution
aq discover --strict
```

### Fail-Fast Startup
```bash
AQUILIA_FAIL_FAST=1 uvicorn entrypoint:app
```

---

## Complete Overview of Changes

### Files Changed Across Release
| File | Subsystem | Phase | Description |
|------|-----------|-------|-------------|
| `pyconfig.py` | Config | Phase 1 | Explicit `Secret` API, positional value strictness |
| `discovery/engine.py` | Workspace / Discovery | Phase 1 & 2 | AST validation, mtime/size cache fast-path, `StrictClassifier`, `StrictDiscoveryEngine` |
| `aquilary/graph.py` | Registry | Phase 1 | Iterative Tarjan implementation, depth-limit removal |
| `aquilary/core.py` | Registry | Phase 1 | O(n) manifest lookups, proper exception handling, bidirectional manifest sync |
| `entrypoint.py` | Runtime | Phase 1 | `AQUILIA_FAIL_FAST` support |
| `manifest.py` | Registry | Phase 1 | Bidirectional sync for `imports` and `depends_on` |
| `runtime.py` | Runtime | Phase 1 | Exec-based workspace module discovery |
| `aquilary/loader.py` | Registry | Phase 1 | Two-phase static AST manifest extraction |
| `cli/__main__.py` | CLI | Phase 1 & 2 | `aq validate --deprecated`, `aq discover --strict` |
| `controller/base.py` | Controller | Phase 2 | `Throttle` backend support, cache flushing, docstring additions |
| `controller/engine.py` | Controller | Phase 2 | Lifecycle hook fix on simple routes, async `_check_throttle` |
| `controller/router.py` | Controller | Phase 2 | O(1) `url_for()` routing index |
| `controller/compiler.py` | Controller | Phase 2 | Dynamic segment type-castor route conflict resolution |
| `controller/resource.py` | Controller | Phase 2 | `Resource[T]`, `CRUDResource`, `ReadOnlyResource`, `@action` |
| `controller/throttle.py` | Controller | Phase 2 | `ThrottleBackend`, `MemoryThrottleBackend`, `RedisThrottleBackend`, factory |
| `auth/manager.py` | Auth | Phase 2 | `issue_tokens=False` parameter on `authenticate_password()` |

---

## Summary of Fixes & Features

| Issue / Feature | Subsystem | Details |
|-----------------|-----------|---------|
| `Secret` lookup ambiguity | Config | Positional args always treated as literal values; `env=` required for env vars. |
| `ManifestWriter` corruption | Registry | Post-write `ast.parse()` validation prevents saving invalid Python. |
| Tarjan stack overflow | Registry | Converted Tarjan SCC & BFS graph algorithms to explicit iterative stacks. |
| O(n²) manifest lookups | Registry | Pre-indexed `{name: manifest}` dictionary eliminates linear scans. |
| Silent startup failures | Runtime | `AQUILIA_FAIL_FAST=1` bypasses 500 error stubs. |
| Slow discovery cache | Discovery | mtime + size fast-path bypasses SHA-256 hashing on unchanged files. |
| `imports` ignored in graph | Registry | Graph builder checks `imports` & populates `depends_on` bidirectionally. |
| Silent autodiscovery errors | Registry | Emits `logger.warning(..., exc_info=True)` for failed module scans. |
| Exec-based workspace discovery | Runtime | Executes `workspace.py` directly instead of brittle regex parsing. |
| Static AST manifest loader | Registry | Two-phase AST parsing prevents unwanted import-time side effects. |
| Simple route lifecycle hook bypass | Controller | `_has_lifecycle_hooks` check prevents skipping `on_request`/`on_response`. |
| Unwanted token minting | Auth | `issue_tokens=False` parameter prevents token generation in session flows. |
| Forward-ref type resolution | Controller | Parameter matcher uses exact match instead of substring matching. |
| Dynamic route conflicts | Controller | Differing parameter types (`int` vs `str`) are no longer flagged as conflicts. |
| Cache memory leaks | Controller | Added `clear_caches()` classmethods to flush `id()`-keyed caches. |
| O(n·m) `url_for()` scan | Controller | Pre-indexed `_name_index` makes URL lookups O(1). |
| Strict discovery mode | Discovery | Runtime import-based discovery (`aq discover --strict`) resolves true MRO. |
| Distributed throttling | Controller | Pluggable Redis and Memory rate limiting backends. |
| Resource / ViewSet controllers | Controller | Declarative CRUD controller abstractions (`Resource[T]`). |
