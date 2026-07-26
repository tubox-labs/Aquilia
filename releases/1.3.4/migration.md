# Migration Guide — Aquilia v1.3.4

Aquilia v1.3.4 is a **backwards-compatible** bug-fix and feature-expansion release. No existing APIs have been removed or broken. All manifests and configurations from 1.3.3 continue to work without modification.

This guide outlines recommended migrations to take advantage of new features, explicit API patterns, and security enhancements.

---

## Upgrading

Upgrade your environment using pip:

```bash
pip install aquilia==1.3.4
```

---

## Secret API Changes

The `Secret` class now enforces strict separation between literal values and environment variable lookups.

**1.3.3 Behavior:** 
`Secret("API_KEY")` ambiguously tried to look up the `API_KEY` environment variable because the string was all caps.

**1.3.4 Behavior:**
Positional arguments are strictly treated as literal values. If you want to pull a secret from the environment, you must use the `env` keyword argument.

**Migration Steps:**
If you see a `DeprecationWarning: ALL_CAPS positional argument treated as literal`, update your code:

```python
# Change this:
my_key = Secret("STRIPE_KEY")

# To this:
my_key = Secret(env="STRIPE_KEY")
```

---

## `imports` vs `depends_on`

The `depends_on` field in `AppManifest` is officially deprecated in favor of `imports`. 

**Migration Steps:**
Both fields work identically in 1.3.4 due to internal bidirectional synchronization. However, you should update your manifests to the v2 API pattern:

```python
# Change this:
manifest = AppManifest(name="app", depends_on=["other"])

# To this:
manifest = AppManifest(name="app", imports=["other"])
```
Use `aq validate --deprecated` to find all instances of `depends_on` in your codebase.

---

## AQUILIA_FAIL_FAST Environment Variable

By default, Aquilia catches startup exceptions to allow local development servers to boot and serve 500-error stubs. If you prefer your server to immediately crash and exit on a bad boot (highly recommended for CI/CD and Production), opt-in using the new environment variable.

**Migration Steps:**
No action is required to maintain 1.3.3 behavior. To enable fail-fast, add the following to your environment:

```bash
export AQUILIA_FAIL_FAST=1
```

---

## Authentication Provisioning (`issue_tokens`)

**Status:** Recommended Migration (Security Hardening)

If you are using `AuthManager.authenticate_password()` in a flow that only relies on session cookies and does not require JWTs, you should explicitly disable token generation. Previously, JWTs were minted unconditionally.

```python
# Before
identity = await auth_manager.authenticate_password(username, password)

# After (if you only need session auth)
identity = await auth_manager.authenticate_password(username, password, issue_tokens=False)
```

---

## Distributed Throttle Backend Migration

**Status:** Optional Migration

If your application runs across multiple workers or processes and you are using the legacy `Throttle` object, rate limits were previously tracked independently per worker in memory. You can upgrade to a distributed Redis backend with a single line change.

```python
# Before (Single-process memory only)
from aquilia.controller.throttle import Throttle
throttle = Throttle(limit=100, window=60)

# After (Distributed via Redis)
throttle = Throttle.with_redis(
    url="redis://localhost:6379/0",
    limit=100,
    window=60
)
```
Existing instances of `Throttle(limit, window)` will continue to operate exactly as they did before, using the memory tracker.

---

## Strict Discovery Mode

**Status:** Optional Migration

If your `AutoDiscoveryEngine` or Aquilia CLI fails to detect controllers or models because they are imported via aliases, re-exported through `__all__`, or rely on deep transitive inheritance across multiple files, switch to strict mode.

```bash
# In your terminal
aq discover --strict
```

Or programmatically:
```python
engine.discover(strict=True)
```
*Note: Strict mode physically imports your application modules. Ensure your module-level code is side-effect free.*

---

## Resource / ViewSet Adoption

**Status:** Optional Adoption

For standard CRUD endpoints, you can significantly reduce boilerplate by swapping plain `Controller` instances for `Resource` subclasses.

```python
# Before
class PostController(Controller):
    @route(["GET"], "/")
    async def list_posts(self, ctx): ...
    
    @route(["GET"], "/{id:int}")
    async def get_post(self, ctx, id: int): ...

# After
from aquilia.controller.resource import ReadOnlyResource

class PostResource(ReadOnlyResource):
    async def list(self, ctx): ...
    async def retrieve(self, ctx, id: int): ...
```
All existing Aquilia decorators and pipeline definitions apply seamlessly to `Resource` classes.

---

# Phase 3 — Cache, Storage & Filesystem

Phase 3 preserves every public API. Three behaviours change in ways that are corrections of clearly-wrong behaviour, so review the "Action required" notes below before deploying.

## 1. Cache keys change shape (action: expect one cold cache)

**Status:** Automatic — no code change

`CacheConfig.key_version` now actually reaches the key builder (it previously did nothing), and decorator-generated keys no longer embed the namespace twice. Because `key_version` defaults to `1`, generated keys gain a version segment:

```text
# before
aq:users:user:123

# after
aq:v1:users:user:123
```

Old entries become unreachable and expire under their own TTL. This is a one-time cold-cache effect on deploy, not data loss. To keep the previous layout exactly:

```python
Integration.cache(key_version=0)
```

To mass-invalidate the cache at any future deploy, increment the value — which now works as documented.

## 2. `@cached` returns correct values again (action: flush stale entries)

**Status:** Automatic — no code change

A decorated function's first positional argument was excluded from its cache key, so every call collapsed onto one entry:

```python
@cached(ttl=60, namespace="users")
async def fetch(user_id: int):
    return {"id": user_id}

await fetch(1)   # {'id': 1}
await fetch(2)   # {'id': 1}   <-- before: wrong value served silently
await fetch(2)   # {'id': 2}   <-- after: correct
```

**Action required:** if you use `@cached` or `@cache_aside` on plain functions with a distributed backend, flush the affected namespaces after upgrading so persisted wrong values are not served:

```python
await cache.invalidate_namespace("users")
```

## 3. `None` results are now cached (action: opt out if you relied on recomputation)

**Status:** Behaviour change — opt-out available

Functions returning `None` were never cached and recomputed forever. They are now cached for their TTL. To restore the previous behaviour on a specific function:

```python
@cached(ttl=60, namespace="lookups", condition=lambda r: r is not None)
async def find_user(email: str) -> User | None: ...
```

## 4. Authenticated responses are no longer shared (action: opt in if intended)

**Status:** Security fix — opt-in available

`CacheMiddleware` previously cached a response keyed only on method, path, query, and `Accept`/`Accept-Encoding`. The first authenticated visitor's response was served to everyone else hitting that path. Now a request carrying `Cookie` or `Authorization` bypasses the cache, and a response setting `Set-Cookie` is never stored; both are marked `X-Cache: PRIVATE`.

If you deliberately want per-identity caching, opt in **and** vary on the identity header:

```python
CacheMiddleware(
    cache_service,
    vary_headers=("Accept", "Cookie"),
    cache_authenticated=True,
)
```

Anonymous traffic caches exactly as before. Expect a hit-rate drop on authenticated routes — that drop is the leak closing.

## 5. Response cache actually installs and stores real bodies

**Status:** Automatic — no code change

`Server._setup_cache()` passed an invalid `ttl=` argument to `CacheMiddleware`; the resulting `TypeError` was swallowed and the middleware was silently never installed. Separately, the middleware read a nonexistent `Response.content`, so any entry it did store had an empty body.

If you had `middleware.enabled: true` configured and saw no caching, it will now take effect — including your configured `cacheable_methods`, `vary_headers`, and `stale_while_revalidate`. Verify your TTLs are what you intend before deploying.

## 6. Streaming and directory operations enforce the sandbox (action: review call sites)

**Status:** Security fix — may raise where it previously did not

`stream_read`, `stream_copy`, and every `FileSystem` directory method now honour `sandbox=`. Code that streamed or listed outside its declared sandbox previously succeeded silently and now raises `PathTraversalFault`:

```python
# before: silently succeeded, full traversal exposure
async for chunk in fs.stream_read("/etc/passwd", sandbox="/srv/uploads"):
    ...

# after: PathTraversalFault
```

A raise here means the traversal was already happening unchecked. Additionally, `FileSystem.list_dir`, `scan_dir`, `make_dir`, `remove_dir`, and `remove_tree` previously raised `TypeError` on every call and are now functional.

## 7. Optional: fail loudly when no sandbox is configured

**Status:** Optional adoption

```python
# before -- containment silently disabled when sandbox_root is unset
FileSystemConfig()

# after -- a missing sandbox_root is a loud configuration error
FileSystemConfig(sandbox_root="/srv/uploads", allow_unsandboxed=False)
```

`allow_unsandboxed` defaults to `True`, so existing configurations are unaffected.

## 8. Optional: register the filesystem through configuration

**Status:** Optional adoption

```python
# Before -- manual construction and registration in application code
fs = FileSystem(FileSystemConfig(sandbox_root="/srv/uploads"))
container.register_singleton(FileSystem, fs)
await fs.initialize()

# After -- workspace.py
Integration.filesystem(
    enabled=True,
    sandbox_root="/srv/uploads",
    allow_unsandboxed=False,
)
```

The server then registers `FileSystem` in every DI container and manages the thread pool lifecycle. Manual registration continues to work; the subsystem is disabled by default.

## 9. Optional: enable cross-process stampede prevention

**Status:** Enabled by default on supporting backends

Stampede protection was previously per-process, so N workers still produced N recomputations. On Redis it now takes a leased, token-checked distributed lock:

```python
Integration.cache(
    backend="redis",
    redis_url="redis://localhost:6379/0",
    distributed_stampede_lock=True,   # default
    stampede_lock_ttl=30.0,
    stampede_poll_interval=0.05,
)
```

Set `distributed_stampede_lock=False` to restore per-process-only coalescing. Backends without lock support are unaffected.

## 10. Optional: signed pickle serializer is now reachable

**Status:** Optional adoption

Configuring `serializer: "pickle"` previously always raised, because no secret key could be supplied through configuration:

```python
Integration.cache(
    backend="redis",
    serializer="pickle",
    serializer_secret_key=env("AQUILIA_CACHE_SIGNING_KEY"),
)
```

Omitting the key raises an actionable `ConfigInvalidFault` naming the exact setting. JSON remains the default.

## 11. Optional: tune S3 multipart and the storage thread pool

**Status:** Optional adoption

```python
Integration.storage(backends=[{
    "alias": "cdn",
    "backend": "s3",
    "bucket": "assets",
    "multipart_threshold": 8 * 1024 * 1024,    # switch to multipart above this
    "multipart_chunk_size": 8 * 1024 * 1024,   # S3 minimum part size is 5 MiB
}])
```

```bash
# Size the dedicated storage thread pool (default: min(32, cpu_count + 4))
export AQUILIA_STORAGE_MAX_WORKERS=16
```

Objects above 5 GB now upload successfully; previously they were rejected outright.

## 12. `ProviderNotFoundError` handlers work again

**Status:** Automatic — no code change

Constructing a server applied a DI patch that re-raised `ProviderNotFoundFault` in place of `ProviderNotFoundError`, silently breaking every existing handler in the process:

```python
try:
    svc = container.resolve("optional.service")
except ProviderNotFoundError:
    svc = None          # before: stopped catching once any server booted
```

The original exception type is now preserved and enriched with resolution metadata. Handlers catching either `ProviderNotFoundError` or `ProviderNotFoundFault` both work, since the raised error is a `DIFault`.

---

## Phase 3 Upgrade Checklist

- [ ] Expect one cold cache after deploy, or set `key_version=0` to keep the old key layout.
- [ ] Flush namespaces used by `@cached` on plain functions if wrong values may have been persisted.
- [ ] Add `condition=lambda r: r is not None` where you relied on `None` recomputation.
- [ ] Decide per route whether authenticated responses should be cached; opt in with `cache_authenticated=True` plus the identity header in `vary_headers`.
- [ ] Verify response-cache TTLs — the middleware now actually installs if you enabled it.
- [ ] Review `stream_read`/`stream_copy`/directory call sites for paths outside their declared sandbox.
- [ ] Consider `allow_unsandboxed=False` for applications resolving user-supplied paths.
- [ ] Consider registering `FileSystem` through `Integration.filesystem()`.
- [ ] Confirm Redis reachability if relying on the distributed stampede lock.
- [ ] Set `AQUILIA_STORAGE_MAX_WORKERS` if your deployment is storage-I/O heavy.
