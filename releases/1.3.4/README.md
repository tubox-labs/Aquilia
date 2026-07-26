# Aquilia v1.3.4 Release Notes — "Structural Integrity & Controller Expansion"

Aquilia v1.3.4 is a major architecture audit and feature release focusing on framework stability, registry correctness, controller integrity, workspace discovery robustness, and scalability. 

This release combines **Phase 1** (registry, workspace, config, and runtime audit fixes) with **Phase 2** (controller system audit fixes, strict resolved-import discovery mode, distributed throttle backends, and Resource / ViewSet CRUD controllers) and **Phase 3** (cache, storage, and filesystem audit fixes covering two critical path-traversal exposures, a cross-user response-cache leak, a silent `@cached` data-correctness bug, and unified subsystem lifecycle/health integration).

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
12. [Phase 2: DI String Token Unwrapping & RequestDAG Fixes](di_annotated_token_fix.md)
    - `Annotated[Any, Inject("token")]` string token unwrapping
    - Direct `Inject` instance token resolution
    - RequestDAG unified descriptor unwrapping
    - `@auto_inject` `include_extras=True` type hint preservation
    - Detailed docstrings across `Inject`, `Dep`, `RequestDAG`, and core DAG APIs
13. [Phase 3: Cache System Audit Fixes](cache_audit.md)
    - `@cached` dropping the first positional argument (CRITICAL)
    - HTTP response cache leaking across identities (CRITICAL / SECURITY)
    - Dead `key_version` config and duplicated key builders
    - Bounded memory heaps, real O(log n) LFU eviction
    - Redis Lua atomics, tag round-tripping, self-pruning tag sets
    - Cross-process stampede prevention via distributed locks
14. [Phase 3: Storage & Filesystem Audit Fixes](storage_filesystem_audit.md)
    - Streaming path bypassing sandbox validation (CRITICAL / SECURITY)
    - `LocalStorage` sibling-directory containment bypass (CRITICAL / SECURITY)
    - Directory operations raising `TypeError` on every call (CRITICAL)
    - True chunked streaming for local and S3 backends
    - S3 multipart upload and a dedicated bounded thread pool
15. [Phase 3: Subsystem Lifecycle & Health](subsystem_lifecycle.md)
    - Filesystem promoted to a first-class, DI-injectable subsystem
    - Real per-backend health probes replacing hardcoded `HEALTHY`
    - DI patch no longer breaking the `ProviderNotFoundError` contract

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

### DI Annotated String Token Injection
```python
from typing import Annotated, Any
from aquilia.di import Container, Inject

# Resolve string tokenized cross-module services cleanly from Annotated type hints
cross_app = await container.resolve_async(
    Annotated[Any, Inject("modules.auth.services:CrossAppService")]
)
```

### Identity-Safe Response Caching
```python
from aquilia.cache.middleware import CacheMiddleware

# Default: authenticated requests bypass the shared cache entirely
CacheMiddleware(cache_service, default_ttl=60)

# Opt in to per-identity caching -- requires the identity header in vary_headers
CacheMiddleware(
    cache_service,
    vary_headers=("Accept", "Cookie"),
    cache_authenticated=True,
)
```

### Cross-Process Stampede Prevention
```python
# workspace.py -- Redis-backed cache
Integration.cache(
    backend="redis",
    redis_url="redis://localhost:6379/0",
    distributed_stampede_lock=True,   # default; only one worker recomputes fleet-wide
    stampede_lock_ttl=30.0,
)
```

### Sandboxed Streaming
```python
# stream_read/stream_copy now honour the sandbox they always advertised
async for chunk in fs.stream_read(path, sandbox="/srv/uploads"):
    await sink.write(chunk)

# escaping the sandbox raises instead of silently succeeding
await fs.stream_copy("/etc/passwd", dst, sandbox="/srv/uploads")  # PathTraversalFault
```

### DI-Injectable Filesystem
```python
# workspace.py
Integration.filesystem(
    enabled=True,
    sandbox_root="/srv/uploads",
    allow_unsandboxed=False,
)
```

### Large-Object Storage Streaming
```python
# Bounded memory: multipart on upload, chunked StreamingBody on download
async with await storage.open("archive.tar") as f:
    async for chunk in f:
        await sink.write(chunk)
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
| `di/core.py` | DI | Phase 2 | `Container._unwrap_token()` for `Annotated[Any, Inject("token")]` and `Inject` objects, docstrings |
| `di/dep.py` | DI | Phase 2 | `_unpack_annotation()` respects `Inject.token`, detailed `Dep` docstring |
| `di/decorators.py` | DI | Phase 2 | `@auto_inject` uses `include_extras=True`, detailed `Inject`/`inject` docstrings |
| `di/request_dag.py` | DI | Phase 2 | `RequestDAG` adapter unification & detailed docstring overhaul |
| `tests/test_di_annotated_inject_fix.py` | DI / Testing | Phase 2 | 9 brutal regression tests for DI Annotated string token resolution |
| `cache/service.py` | Cache | Phase 3 | Config-driven key builder, cross-process stampede lock, `key_builder`/`key_prefix` accessors |
| `cache/key_builder.py` | Cache | Phase 3 | `KeyBuilder` protocol, shared `call_signature()`, `build_key_builder()` factory |
| `cache/decorators.py` | Cache | Phase 3 | First-positional-argument key fix, `None` result caching, shared key layout |
| `cache/middleware.py` | Cache | Phase 3 | Identity-aware caching, `Set-Cookie` refusal, real body capture, header casing, tracked refresh tasks |
| `cache/backends/memory.py` | Cache | Phase 3 | Real LFU min-heap, bounded TTL/LFU heaps with lazy invalidation |
| `cache/backends/redis.py` | Cache | Phase 3 | Lua atomics, tag/namespace sidecar round-trip, self-pruning sets, distributed lock |
| `cache/backends/composite.py` | Cache | Phase 3 | Tracked async L2 writes, `drain()`, shutdown durability |
| `cache/core.py` | Cache | Phase 3 | `key_builder`, `serializer_secret_key`, distributed-stampede config; lock contract on `CacheBackend` |
| `cache/di_providers.py` | Cache | Phase 3 | Reachable pickle serializer wiring with actionable fault |
| `filesystem/_streaming.py` | Filesystem | Phase 3 | Sandbox validation on all streaming entry points |
| `filesystem/_directory.py` | Filesystem | Phase 3 | `config`/`sandbox` support and validation on every directory operation |
| `filesystem/_security.py` | Filesystem | Phase 3 | `allow_unsandboxed` enforcement, documented symlink semantics |
| `filesystem/_config.py` | Filesystem | Phase 3 | `allow_unsandboxed` field with fail-loudly validation |
| `filesystem/_service.py` | Filesystem | Phase 3 | `copy_tree`/`walk` exposure, chunk-size defaults, corrected forwarding |
| `storage/backends/local.py` | Storage | Phase 3 | Shared `validate_path` containment, full streaming read/write/copy |
| `storage/backends/s3.py` | Storage | Phase 3 | Multipart upload, `StreamingBody` iteration, dedicated executor |
| `storage/executor.py` | Storage | Phase 3 | New dedicated bounded thread pool for all cloud backends |
| `storage/registry.py` | Storage | Phase 3 | Criticality-aware initialization, logged shutdown, documented trust boundary |
| `response.py` | HTTP | Phase 3 | Public `content` property and `body()` accessor |
| `server.py` | Runtime | Phase 3 | Corrected cache middleware wiring, `_setup_filesystem()`, real per-backend health |
| `faults/integrations/di.py` | DI | Phase 3 | Preserves `ProviderNotFoundError` type; idempotent patch |
| `tests/test_cache_storage_filesystem_audit.py` | Testing | Phase 3 | 59 regression tests pinning every Phase 3 finding |

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
| DI `Annotated[Any, Inject("token")]` string token resolution | DI | Added `Container._unwrap_token()` to unwrap Annotated aliases & Inject markers. |
| `RequestDAG` unification & docstrings | DI | Unified descriptor unwrapping and completed comprehensive docstrings across Inject, Dep, RequestDAG. |
| `@cached` returned wrong values | Cache | First positional argument was excluded from every key, collapsing distinct calls onto one entry. |
| Response cache served other users' data | Cache | Identity-bearing requests bypass the shared cache; `Set-Cookie` responses are never stored. |
| Response cache stored empty bodies | Cache | Middleware read a nonexistent `Response.content`; new public `content`/`body()` accessors added. |
| Dead `key_version` config | Cache | Config value now reaches the key builder, so mass invalidation works as documented. |
| Duplicated key builders | Cache | Decorator and service share one layout; namespace embedded exactly once. |
| `None` never cached | Cache | Negative results are cached via a sentinel; opt out with `condition`. |
| O(n) LFU eviction | Cache | Real `(frequency, key)` min-heap with lazy invalidation. |
| Unbounded memory heaps | Cache | TTL and LFU heaps compact against live entries; 2,000 rewrites now bound the heap to ≤ 16. |
| Redis check-then-act race | Cache | `increment` runs existence check and `INCRBY` in one Lua script. |
| Redis tag sets grew forever | Cache | Lua pruning removes members whose keys expired naturally. |
| Redis `get()` lost tags | Cache | TTL-matched sidecar restores `tags` and `namespace`, matching MemoryBackend. |
| Dropped async L2 writes | Cache | Composite tracks scheduled tasks and drains them on shutdown. |
| Unreachable pickle serializer | Cache | `serializer_secret_key` config makes signed pickle configurable. |
| Per-process stampede only | Cache | Redis `SET NX PX` lock with token-checked release coalesces across processes. |
| Streaming bypassed the sandbox | Filesystem | `sandbox=` on `stream_read`/`stream_copy` was accepted and ignored; now enforced. |
| Directory ops raised `TypeError` | Filesystem | Every `FileSystem` directory method was unusable; now working and sandboxed. |
| Opt-in sandboxing | Filesystem | `allow_unsandboxed=False` makes a missing sandbox root a loud configuration error. |
| Prefix-match containment bypass | Storage | `LocalStorage` now delegates to the framework's single canonical `validate_path`. |
| Full-file buffering | Storage | Local and S3 backends stream in chunks instead of materialising whole objects. |
| No S3 multipart | Storage | Uploads above the threshold use multipart, lifting the 5 GB single-request limit. |
| Shared default executor | Storage | Dedicated bounded `aquilia-storage` pool replaces `run_in_executor(None, ...)`. |
| All-or-nothing registry boot | Storage | Optional backend failures degrade; only a failing default backend is fatal. |
| Hardcoded health status | Runtime | Cache, storage, and filesystem health are now really probed, per backend. |
| Filesystem needed manual wiring | Runtime | `Integration.filesystem()` registers a DI-injectable `FileSystem` with managed lifecycle. |
| DI patch broke exception contract | DI | `ProviderNotFoundError` type is preserved and enriched instead of replaced. |
