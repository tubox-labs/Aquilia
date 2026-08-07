# Performance Improvements — v1.4.0b1

Aquilia v1.4.0b1 delivers an extraordinary leap in performance across the entire framework. Through the rigorous analysis performed in the `perf/json-orm-validation-engine` branch, severe Python-level bottlenecks were identified and eliminated in "Phase 0", followed by deep architectural rewrites in subsequent phases.

## Performance Overview Matrix

| Component | Metric | Before | After | Improvement |
|-----------|--------|--------|-------|-------------|
| **Validation Endpoint** | Requests Per Second (RPS) | 1,809 | 15,075 | **+733%** |
| **Validation Suite** | Total Execution Time | ~500s | ~200s | **2.5x faster** |
| **ORM Entity Fetch** | `get()` latency | 120.7 µs | 9.3 µs | **13x faster** |
| **Database Pool** | `acquire()` overhead | 43.0 µs | 0.18 µs | **238x faster** |
| **Database Engine** | Query Setup Overhead | 32.0 µs | 0 µs* | **-100% overhead** |
| **JSON Engine** | Small Payload Encode | Base | - | **8.5x faster** |
| **JSON Engine** | 100KB Payload Encode | Base | - | **3.9x faster** |
| **JSON Engine** | Small Payload Decode | Base | - | **4.8x faster** |
| **DI Container** | Resolve Setup | 66.8 ns | 22.9 ns | **~3x faster** |
| **Database** | General `db_queries` bench | Base | - | **+485%** |
| **Database** | Updates `db_updates` bench | Base | - | **+164%** |

*( * Overhead reduced to zero unless inspector is actively attached )*

---

## Phase 0: Hot-Path Correctness Fixes

Before a single line of C++ was introduced, fixing fundamental logical flaws in the Python engine yielded massive gains.

### 1. `validate_body` Double-Bind Fix
**The Bug:** The `@validate_body` decorator and the core Controller Engine were unaware of each other's state. When a request came in, the decorator parsed and validated the body, but the controller engine *also* attempted to extract and bind the `body` parameter. This resulted in duplicate parsing, duplicate validation, and a masked internal exception (`"got multiple values for keyword argument 'body'"`), which the framework gracefully but expensively handled on every request.
**The Fix:** `validate_body` now reads from a cached parse state on the request. The Controller engine checks for `request.validated_data` before attempting to bind `body`.
**Impact:** RPS jumped from 1,809 to 15,075 on validation-heavy endpoints.

### 2. `Response.json` String vs. Bytes Fix
**The Bug:** The JSON serialization path incorrectly coerced the output to a Python `str` instead of raw `bytes` when `orjson` wasn't available. The ASGI specification requires `bytes` for the HTTP body. Consequently, a 100KB payload was serialized to a string, and then explicitly `.encode('utf-8')` was called, effectively building the 100KB string twice in memory.
**The Fix:** The unified codec now guarantees a `bytes` return type. `Response.json` streams these bytes directly.
**Impact:** Large payload emission is roughly 4x faster and uses half the memory.

### 3. Iterative `_check_json_depth`
**The Bug:** To protect against billion-laughs style nested JSON attacks, `_check_json_depth` traversed dictionaries recursively. A maliciously deeply nested payload blew the Python call stack, turning a legitimate `400 Bad Request` into a `500 Internal Server Error`, triggering expensive exception reporting.
**The Fix:** The traversal was rewritten using an iterative stack approach.

### 4. Inspector Gating (`_notify_inspector`)
**The Bug:** Inside `db/engine.py`, the `_notify_inspector` function was calling `traceback.extract_stack()` on *every single query* to provide source-code mapping for the dev platform. This function call alone cost 32µs, accounting for 26% of total query execution time.
**The Fix:** The call is now strictly gated behind `_QUERY_INSPECTION`, which is unconditionally `False` in production mode.

### 5. Database Pool `acquire()` Fix
**The Bug:** In `sqlite/_pool.py`, retrieving a connection from the asyncio queue was wrapped in `asyncio.wait_for(..., timeout=X)`. `asyncio.wait_for` creates a new Task on every invocation, causing massive event-loop pressure.
**The Fix:** Removed the wrapper. The queue is managed deterministically. Overhead dropped from 43µs to 0.18µs.

---

## SQLite Inline Execution Engine (`sqlite/_inline.py`)

Python's standard `sqlite3` driver is blocking. Traditionally, async frameworks dispatch SQLite queries to a `ThreadPoolExecutor` to avoid blocking the asyncio event loop. However, thread-hopping in Python takes roughly 25-30µs. For a simple `SELECT * FROM users WHERE id = ?` (which SQLite executes in ~1.5µs), the thread hop is 20x slower than the query itself!

**The `InlinePolicy` API:**
Aquilia v1.4.0b1 introduces an intelligent execution policy. Fast, bounded queries (like primary key lookups or simple index seeks) are executed **inline** directly on the asyncio event loop.

```python
# db_config.py
inline_fast_queries = True
inline_max_duration_ms = 5.0
```

**The Demotion Mechanism:**
Safety is guaranteed. The engine measures the execution time of inline queries. If a query (e.g., a table scan) takes longer than `inline_max_duration_ms`, the engine logs a warning and **permanently demotes** that specific SQL statement to the thread pool for the lifetime of the application. The event loop is never accidentally starved by a slow query more than once.

**Impact:** ORM `get()` latency collapsed from 120.7µs down to 9.3µs.

---

## Core Architecture Enhancements

### Radix-Trie Router
The `aquilia/_core` extension replaces Python `re` regex routing with a native radix-trie. The trie allows O(K) lookup time (where K is the path depth). Furthermore, method eligibility (e.g., matching a `GET` vs a `POST` to the same path) is baked into the C++ traversal nodes, failing fast instead of propagating up the Python routing tree.

### ASGI Direct Cache Write
In the ASGI layer, the framework previously used `register_instance(Request, request)` for dependency injection scoping per-request. This was replaced with direct dictionary cache writes on the context object, stripping out method dispatch overhead.

### DI Meta Hoist & Slot Fields
The `Container.resolve_async()` hot path read `provider.meta` multiple times per dependency resolution. This property access was hoisted into a local variable, reducing 11 property reads down to 1 (saving ~19ns per call).

Similarly, `DISettings._strict_scopes` was a private field wrapped in a `@property` for validation. It has been converted to a plain public slot field `strict_scopes`, along with `scope_check_enabled`. Validation now occurs once during `__post_init__`. This reduced the DI setup overhead from 66.8ns to 22.9ns per resolve cycle.

---

## Summary
The combination of Phase 0 logical fixes, the SQLite inline engine, and C++ primitive replacements ensures Aquilia v1.4.0b1 is capable of handling enterprise-grade throughput with minimal hardware utilization.
