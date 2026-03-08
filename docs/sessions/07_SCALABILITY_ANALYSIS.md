# Session Scalability Analysis

## Current Architecture

### MemoryStore
- **Complexity:** O(1) load/save/delete via `OrderedDict`
- **LRU Eviction:** O(1) via `OrderedDict.popitem(last=False)`
- **Principal Index:** O(1) lookup via `dict[str, set[str]]`
- **Concurrency:** Single `asyncio.Lock` (process-level)
- **Max Sessions:** Configurable (default 10,000)
- **Memory:** ~2 KB per session (ID + data + metadata)

### FileStore
- **Complexity:** O(1) load/save/delete (direct file access)
- **Principal Lookup:** O(n) full directory scan
- **Concurrency:** Single `asyncio.Lock`
- **Atomic Writes:** temp file + rename
- **I/O:** Blocking (not ideal for async)

### SessionEngine
- **Per-Request Cost:** 1 transport extract + 1 store load + 1 policy check + 1 store save + 1 transport inject
- **Rotation Cost:** +1 store delete + 1 new ID generation
- **Concurrency Check:** 1 `count_by_principal` + optional evictions

## Scaling Bottlenecks

### 1. Single-Process Lock Contention
The `asyncio.Lock` in MemoryStore serializes all session operations. Under high
concurrency (10K+ concurrent requests), this becomes a bottleneck.

**Mitigation:** Use sharded locks (partition by session ID hash) or lock-free
data structures.

### 2. FileStore Blocking I/O
`Path.read_text()` and `Path.write_text()` are blocking calls that tie up the
async event loop.

**Mitigation:** Use `asyncio.to_thread()` or `aiofiles` for non-blocking I/O.

### 3. No Distributed Store
MemoryStore is process-local. Multi-process/multi-node deployments cannot share
session state.

**Mitigation:** Implement RedisStore using `aioredis` or `redis-py` with async
support.

### 4. O(n) Cleanup
`cleanup_expired()` iterates all sessions to find expired ones.

**Mitigation:** Use a sorted index by `expires_at` for O(log n) cleanup, or
lazy expiration (check on access).

## Scaling Recommendations

### Short-term (v1.x)
1. Implement `RedisStore` with connection pooling
2. Replace FileStore blocking I/O with `asyncio.to_thread()`
3. Add sharded locks to MemoryStore (16 shards)

### Medium-term (v2.x)
1. Add sorted TTL index for O(log n) expired session cleanup
2. Implement session data compression (zstd)
3. Add batch operations (load_many, save_many)

### Long-term (v3.x)
1. Implement distributed session store with consistent hashing
2. Add session replication for HA
3. Implement write-behind caching (eventual consistency mode)

## Performance Characteristics

| Operation | MemoryStore | FileStore | RedisStore (proposed) |
|---|---|---|---|
| Load | O(1) ~1μs | O(1) ~100μs | O(1) ~200μs |
| Save | O(1) ~1μs | O(1) ~500μs | O(1) ~200μs |
| Delete | O(1) ~1μs | O(1) ~100μs | O(1) ~200μs |
| List by Principal | O(k) ~1μs | O(n) ~10ms | O(k) ~500μs |
| Cleanup Expired | O(n) | O(n) | O(n) with SCAN |
| Max Sessions | ~50K (RAM) | ~1M (disk) | ~10M+ (Redis) |
