# Cache System Audit Fixes

This document details the fixes applied to the `aquilia.cache` subsystem in Aquilia v1.3.4, addressing findings from the Cache & Storage architectural audit.

All changes are backward compatible at the API level. Two changes alter runtime *behaviour* in ways that are corrections of clearly-wrong behaviour: generated cache keys change when `key_version` is set, and the HTTP response cache no longer serves identity-bearing responses from a shared entry. Both are described in detail below and in the [Migration Guide](migration.md).

## §A1 `key_version` Was a Dead Configuration Field (BUG)

**Previous Behavior:**
`CacheConfig.key_version` was documented as "Increment to mass-invalidate all keys" and was faithfully parsed from workspace configuration into `CacheConfig`, and exposed in `CacheConfig.to_dict()`. It never reached the key builder. Setting `key_version: 5` had zero effect on any generated key, so the documented mass-invalidation workflow silently did nothing.

**Root Cause:**
`CacheService.__init__` constructed its key builder as `DefaultKeyBuilder()` with no arguments. `DefaultKeyBuilder.__init__` defaults `version=0`, and `build()` only embeds a version segment when `version > 0`. The configured value was read but never passed.

**Fix:**
`CacheService` now builds its key builder from configuration:

```python
self._key_builder = build_key_builder(
    self._config.key_builder,
    version=self._config.key_version,
)
```

A new `build_key_builder(strategy, *, version)` factory selects between the colon-segment `DefaultKeyBuilder` and the SHA-256 `HashKeyBuilder`, and raises `ConfigInvalidFault` for an unknown strategy rather than silently falling back.

**User Impact:**
Bumping `key_version` now invalidates the entire keyspace, as documented. Because the default `CacheConfig.key_version` is `1`, generated keys gain a `v1:` segment on upgrade:

```text
# before
aq:users:user:123

# after
aq:v1:users:user:123
```

This is a one-time cold-cache effect on deploy — old entries are not read and expire naturally under their own TTL. Set `key_version: 0` to retain the previous unversioned key layout exactly.

## §A2 Two Independent Key Builders (ARCH)

**Previous Behavior:**
`aquilia/cache/decorators.py` held its own module-level `_key_builder = DefaultKeyBuilder()`, separate from the instance inside `CacheService` and permanently pinned at `version=0`. The decorator built a key with `from_args(namespace=...)`, which already prefixed the namespace, then passed that composite string as the `key` argument to `cache_service.get(cache_key, namespace=namespace)`, which prefixed the namespace a *second* time. The configured `key_prefix` and `key_version` were applied only by the service side and were invisible to the decorator's builder.

**Fix:**
The decorator no longer owns a builder. It computes only the *call signature* and lets `CacheService` apply namespace, prefix, and version exactly once:

```python
# aquilia/cache/decorators.py
cache_key = call_signature(func.__qualname__, args[skip:], kwargs)
```

`DefaultKeyBuilder.from_args` and `HashKeyBuilder.from_args` now both delegate to their own `build()`, so every code path produces one consistent layout. A `KeyBuilder` `Protocol` documents the contract for custom builders.

**User Impact:**
Decorator-generated keys are now identical in shape to manually-built keys and carry the configured prefix and version. The double namespace segment is gone. Keys change on upgrade; entries written by the old layout are unreachable and expire under their TTL.

## §A3 `@cached` Dropped the First Positional Argument (CRITICAL)

**Previous Behavior:**
A decorated plain function returned another call's cached value:

```python
@cached(ttl=60, namespace="users")
async def fetch(user_id: int):
    return {"id": user_id}

await fetch(1)   # {'id': 1}
await fetch(2)   # {'id': 1}   <-- wrong value, silently served
```

**Root Cause:**
The decorator decided whether to strip a bound `self` with `skip = 1 if args and hasattr(args[0], "__class__") else 0`. Every Python object has `__class__`, so the test was unconditionally true and the first positional argument was excluded from every generated key. All calls to a single-argument function collapsed onto one key.

**Fix:**
A new `_is_bound_call()` helper determines method-ness from the function's qualified name and the runtime type of the first argument, so `self` is stripped only for genuine methods:

```python
skip = 1 if _is_bound_call(func, args) else 0
```

**User Impact:**
This was a silent data-correctness bug — decorated functions returned wrong results, not errors. Any application using `@cached` or `@cache_aside` on a plain function with positional arguments was affected. No code changes are required; flush affected namespaces after upgrading if stale values may have been persisted to a distributed backend.

## §A4 Functions Returning `None` Were Never Cached (BUG)

**Previous Behavior:**
The store step was gated on `if result is not None and should_cache:`. A function whose legitimate result was `None` (a "known absent" lookup) recomputed on every call forever and never recorded a hit — exactly the negative-caching case that most benefits from a cache.

**Fix:**
`None` results are stored as a private sentinel and restored transparently on read. Suppressing negative caching is now an explicit opt-in via the existing `condition` parameter:

```python
# cache the negative result (new default)
@cached(ttl=60, namespace="lookups")
async def find_user(email: str) -> User | None: ...

# opt out: recompute on every miss
@cached(ttl=60, namespace="lookups", condition=lambda r: r is not None)
async def find_user(email: str) -> User | None: ...
```

**User Impact:**
Decorated functions returning `None` are now cached for their TTL. If your code depends on a `None` result being recomputed each call, add the `condition` shown above.

## §A5 LFU Eviction Was O(n), Not O(log n) (PERF)

**Previous Behavior:**
`MemoryBackend`'s module docstring advertised *"LFU: Min-heap + frequency counter with O(log n) eviction"*. The implementation did `min(self._freq_counter, key=...)` — a linear scan over every key on every eviction. No heap existed for LFU; the only heap in the file was TTL-only. Under an LFU policy with a large, consistently-full cache, every insert paid an O(n) cost.

**Fix:**
A real `(frequency, key)` min-heap now backs LFU. Superseded tuples are skipped on pop and compacted in bulk when the heap outgrows the live entry count, giving amortised O(log n) eviction:

```python
def _pop_least_frequent(self) -> str | None:
    while self._lfu_heap:
        freq, key = heappop(self._lfu_heap)
        if self._freq_counter.get(key) != freq:
            continue          # superseded by a later access
        return key
    return None
```

**User Impact:**
Faster evictions under LFU at scale. No API change. The docstring now matches the implementation.

## §A6 Unbounded TTL Heap Growth (BUG — Memory Leak)

**Previous Behavior:**
`MemoryBackend.set()` pushed a `(expires_at, key)` tuple onto `_ttl_heap` on every TTL'd write, and `_evict_key()` — the single cleanup path for all indices — never touched the heap. Overwriting the same TTL'd key (session refresh, rate-limit counters) grew the heap without bound relative to the store. The sweeper guarded against acting on stale tuples, so evictions stayed correct, but memory grew steadily in long-running processes and would not surface in short tests.

**Fix:**
Both heaps use lazy invalidation with bulk compaction. A tuple is live only if it still matches the stored entry's expiry (or, for LFU, the key's current frequency); the heap is rebuilt once it exceeds a small multiple of the live entry count. Two diagnostic properties, `ttl_heap_size` and `lfu_heap_size`, are exposed for tests and leak triage.

Measured on 2,000 repeated writes to a single TTL'd key:

| | Heap length | Store length |
|---|---|---|
| Before | 2,000 (unbounded) | 1 |
| After | ≤ 16 | 1 |

**User Impact:**
Memory is bounded for workloads that repeatedly rewrite the same TTL'd keys. No API change.

## §A7 Redis Docstring Claimed Lua Atomicity That Did Not Exist (BUG + DOCS)

**Previous Behavior:**
`RedisBackend`'s docstring advertised *"Lua scripts for atomic operations"* and *"Lua-based atomic increment/decrement"*. No `EVAL` or `register_script` call existed anywhere in the file. `increment()` was an `exists()` check followed by a separate `incrby()` — a check-then-act race in which two concurrent callers on a missing key can both observe "absent" and both return `None`.

**Fix:**
The claimed scripts now exist. `increment()` evaluates the existence check and the increment inside one script, so the decision is atomic and a missing key is never created:

```lua
if redis.call('EXISTS', KEYS[1]) == 0 then
  return nil
end
return redis.call('INCRBY', KEYS[1], ARGV[1])
```

Verified against a live Redis 7: 50 concurrent `increment` calls on a counter seeded at `10` produced 50 distinct results with a maximum of exactly `60`.

**User Impact:**
`increment`/`decrement` are race-free against concurrent callers and remain consistent with `MemoryBackend` semantics (absent keys return `None` and are not created).

## §A8 Redis Tag and Namespace Sets Grew Forever (BUG — Memory Leak)

**Previous Behavior:**
`set()` added each key to a Redis set per tag and per namespace. When the underlying key later expired through Redis's own TTL rather than an explicit `delete`, nothing removed its set membership. Any workload relying on natural expiry accumulated stale members indefinitely.

**Fix:**
Tag and namespace sets are pruned opportunistically by a Lua script that returns only live members and `SREM`s the rest in the same round trip. `delete_by_tags`, `clear(namespace)`, and `keys(namespace=...)` all read through it, so ordinary use keeps the sets bounded.

**User Impact:**
Tag and namespace sets no longer grow without bound. Verified against live Redis: after an entry expired naturally, both the live-member list and the set cardinality were `0`.

## §A9 Redis `get()` Always Returned Empty Tags (BUG)

**Previous Behavior:**
The `CacheEntry` reconstructed by `RedisBackend.get()` carried no tags and a default namespace, because neither was fetched back on read. Code written and tested against `MemoryBackend` that inspected `entry.tags` silently misbehaved in production against Redis.

**Fix:**
`set()` mirrors tags and namespace into a sidecar hash carrying the entry's own TTL, so it expires with the entry rather than leaking. `get()` pipelines the value, TTL, and sidecar in one round trip and restores `tags` and `namespace`. `delete`, `clear`, and `delete_by_tags` remove the sidecar alongside the entry, and `keys()` filters internal `_meta:`, `_tags:`, and `_ns:` keys out of results.

**User Impact:**
`entry.tags` and `entry.namespace` behave identically across `MemoryBackend` and `RedisBackend`.

## §A10 Composite Fire-and-Forget L2 Writes Could Be Dropped (BUG)

**Previous Behavior:**
In async-L2-write mode, `CompositeBackend` scheduled the L2 write with `asyncio.ensure_future(...)` and discarded the returned task. Untracked tasks may be garbage-collected before completion, and `shutdown()` had no way to await them, so a shutdown racing an in-flight write could silently lose it — on the code path whose entire purpose is L2 durability.

**Fix:**
Scheduled writes are held in a set until their done-callback fires, and `shutdown()` drains them:

```python
def _schedule_l2(self, coro):
    task = asyncio.ensure_future(coro)
    self._pending.add(task)
    task.add_done_callback(self._pending.discard)
```

A public `drain(timeout=5.0)` method and a `pending_writes` property are available for explicit control and diagnostics.

**User Impact:**
Async L2 writes survive shutdown. Verified against live Redis: 25 async writes followed immediately by `shutdown()` produced 25 durable L2 entries, with tags intact. Previously this workload lost writes once the connection pool was saturated.

## §A11 Pickle Serializer Was Unreachable Through Configuration (BUG)

**Previous Behavior:**
`PickleCacheSerializer` correctly required a `secret_key` to HMAC-sign payloads — good security design. But `create_cache_backend()` called `get_serializer(config.serializer)` with no key, and no `secret_key` field existed anywhere in `CacheConfig`. Configuring `serializer: "pickle"` therefore always raised, making a documented option unreachable through any standard configuration flow.

**Fix:**
A `serializer_secret_key` field was added to `CacheConfig` and is parsed by `build_cache_config()`. Requesting pickle without it raises an actionable `ConfigInvalidFault` naming the exact key to set:

```python
CacheIntegration(
    backend="redis",
    serializer="pickle",
    serializer_secret_key=env("AQUILIA_CACHE_SIGNING_KEY"),
)
```

**User Impact:**
Pickle is reachable through configuration, and still refuses to run unsigned. JSON remains the default and is unaffected.

## §A12 Stampede Protection Did Not Cross Process Boundaries (SCALE)

**Previous Behavior:**
`get_or_set` implemented a correct single-flight guard using an in-memory map and asyncio locks. Each process had its own map, so N Gunicorn workers or N Kubernetes pods sharing one Redis still produced N concurrent recomputations on expiry — precisely the thundering herd the feature exists to prevent, at the boundary where it matters most.

**Fix:**
The `CacheBackend` contract gained an optional distributed lock, advertised by `supports_distributed_lock` and implemented in `RedisBackend` with `SET NX PX` plus a token-checked Lua release:

```lua
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
```

The lock is leased, so a crashed holder cannot deadlock the fleet, and the token check prevents a holder whose lease already expired from deleting a lock another worker has since acquired. The winner of the local single-flight race additionally takes the cross-process lock; losers wait briefly for the winner's value and fall back to computing independently rather than stalling the request.

New configuration: `distributed_stampede_lock` (default `true`), `stampede_lock_ttl` (default `30.0`), `stampede_poll_interval` (default `0.05`).

**User Impact:**
Verified against live Redis with six independent backends acting as six processes: **one** loader invocation total, all six workers returning the winner's value. Backends without distributed lock support are unaffected and continue to coalesce per-process.

## §A13 HTTP Response Cache Leaked Across Identities (CRITICAL — SECURITY)

**Previous Behavior:**
`CacheMiddleware` defaulted `vary_headers` to `("Accept", "Accept-Encoding")`. The cache key was built from method, path, query string, and those headers only — **`Cookie` and `Authorization` were excluded unless the integrator added them explicitly.** With the middleware attached at `scope="global"`, the first authenticated user to hit a path had their response cached and served to every subsequent visitor of that path until the TTL expired. This is the cache-poisoning class behind numerous real-world CDN data-leak incidents, and the safe configuration was not the default.

**Fix:**
Two safeguards, neither of which can be disabled implicitly:

1. A request carrying `Cookie` or `Authorization` bypasses the cache entirely unless that header is listed in `vary_headers` **and** `cache_authenticated=True` is passed.
2. A response that sets `Set-Cookie` is never stored.

Both paths mark the response `X-Cache: PRIVATE`. Deliberate per-identity caching remains available:

```python
CacheMiddleware(
    cache_service,
    vary_headers=("Accept", "Cookie"),
    cache_authenticated=True,
)
```

**User Impact:**
Anonymous responses cache exactly as before. Authenticated responses stop being shared. Verified end-to-end through the real `Request`/`Response` pipeline: two users with different session cookies each received their own body, and anonymous traffic still produced `MISS` then `HIT`.

## §A14 Response Bodies Were Cached Empty (BUG)

**Previous Behavior:**
`CacheMiddleware` read `response.content` to build the ETag and the cached payload. `Response` exposed no `content` attribute, so the guarded read fell through to `b""`. Every stored entry had an empty body and an ETag computed over empty bytes, meaning a cache *hit* served a blank response.

**Root Cause:**
The attribute was renamed to a private `_content` on `Response` without updating the middleware, and the `hasattr` guard converted the resulting `AttributeError` into a silent empty default.

**Fix:**
`Response` gained a documented public `content` property and a `body()` method that returns encoded bytes, or `None` for streaming and awaitable content that cannot be materialised without consuming the stream. The middleware treats `None` as "not cacheable" and returns the response untouched, rather than storing an empty placeholder.

**User Impact:**
The HTTP response cache serves real bodies. Streaming responses are correctly skipped instead of being cached as blanks.

## §A15 Cache Middleware Header Casing (BUG)

**Previous Behavior:**
`Response` normalises header keys to lowercase when constructed, but direct `response.headers["X-Cache"] = ...` assignment bypassed that normalisation. `X-Cache`, `ETag`, and `Cache-Control` were written mixed-case on the miss path and lowercase on the replay path, so lookups by either spelling missed roughly half the time. The `Cache-Control` no-store/private check and the `X-Cache-TTL` route override read mixed-case names against a lowercase mapping and never matched.

**Fix:**
All writes go through `Response.set_header()`, which normalises. A `_response_header()` helper performs case-insensitive reads, so `Cache-Control: private`, `Set-Cookie`, and `X-Cache-TTL` are honoured regardless of the spelling the handler used.

**User Impact:**
`Cache-Control: no-store` and `private` are respected, and the `X-Cache-TTL` per-route override works. Header names are consistently lowercase, matching the framework-wide `Response` contract.

## §A16 Server Wiring Passed Invalid Arguments (BUG)

**Previous Behavior:**
`Server._setup_cache()` constructed the middleware with `CacheMiddleware(cache_service=svc, ttl=..., namespace=...)`. `CacheMiddleware` accepts no `ttl` parameter. The resulting `TypeError` was swallowed by the surrounding `except Exception`, logged as a non-fatal init failure, and the response cache was silently never installed even when explicitly enabled. Configured `cacheable_methods`, `vary_headers`, and `stale_while_revalidate` were also ignored.

**Fix:**
The call now uses the correct parameter names and threads every configured value through, falling back to the parsed `CacheConfig` defaults. `set_default_cache_service()` is also invoked during setup, so `@cached` on standalone functions resolves the configured service instead of silently no-opping.

**User Impact:**
Enabling the response cache in workspace configuration actually installs it, with all configured options applied.

## Related Documentation

- [Storage & Filesystem Audit Fixes](storage_filesystem_audit.md)
- [Subsystem Lifecycle & Health](subsystem_lifecycle.md)
- [Migration Guide](migration.md)
