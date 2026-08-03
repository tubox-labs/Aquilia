# Phase 5 — Native Routing Engine Specification

**Status:** design
**Targets:** Phase 2 finding B5 (`_version_matches` imports, 0.42 µs) and the residual 0.79 µs static / 1.17 µs dynamic match cost

---

## 1. Scope decision — algorithm vs constant factor

Phase 2 measured router scaling directly (evidence E5):

| routes | static match | dynamic match | miss |
|---|---|---|---|
| 15 | 832 ns | 1,228 ns | 284 ns |
| 150 | 840 ns | 1,239 ns | 291 ns |
| 750 | 865 ns | 1,248 ns | 288 ns |
| 3,000 | 858 ns | 1,300 ns | 299 ns |

**200× the route count costs +3% lookup time.** The existing three-tier design (static hash map → segment trie → regex fallback, `router.py:230`) is already asymptotically correct. The Phase-brief instruction to "benchmark multiple routing algorithms before selecting one" has been answered by measurement: **algorithm choice is not the bottleneck and switching algorithms cannot help.**

Decomposition of the 782 ns static match (evidence E2):

| Component | Cost | Share |
|---|---|---|
| raw `dict.get` on the static map | 22.8 ns | 3.0% |
| `_version_matches(route, None)` | 492 ns | **64%** |
| remainder (call frames, normalisation, dataclass construction) | ~267 ns | 33% |

The dominant cost is `_version_matches` (`router.py:361`), and 421 ns of that 492 ns is **two `from aquilia.versioning.core import ...` statements executed per call** (evidence E1: 421 ns for two imports, ~205 ns each).

**Conclusion: the native router's job is to eliminate constant-factor Python overhead — call frames, per-call imports, and per-match object allocation — not to change the matching algorithm.** The radix trie is retained because it is already the right structure.

---

## 2. Data structure

Radix trie over interned segment ids, flattened into contiguous arrays for cache locality.

```cpp
struct Node {
    uint32_t first_child;   // index into nodes_, 0 = none
    uint32_t child_count;
    uint32_t segment_id;    // interned literal; PARAM_SENTINEL for a param edge
    uint32_t param_name_id; // interned param name, when segment_id == PARAM_SENTINEL
    uint32_t route_id;      // terminal payload; NO_ROUTE if not terminal
    uint8_t  param_kind;    // 0 none, 1 str, 2 int, 3 uuid, 4 path(catch-all)
};

class RadixRouter {
    Interner& interner_;
    std::vector<Node> nodes_;                          // flattened trie, breadth-ordered
    std::array<std::vector<uint32_t>, N_METHODS> roots_;
    // Tier 1: exact-path hash map per method, keyed by interned whole-path id
    std::array<std::unordered_map<uint32_t, uint32_t>, N_METHODS> static_;
    bool frozen_ = false;
};
```

**Why a flattened array rather than pointer-linked nodes:** children of a node are contiguous, so a segment scan is a linear walk over adjacent cache lines. Typical fan-out is small (2–8), so linear scan beats hashing per node.

**HTTP methods are a fixed-size array, not a map.** There are nine methods; `roots_[method_idx]` is an array index, replacing the `self._tries.get(method)` dict lookup.

---

## 3. Matching algorithm

```
match(method, path) -> (route_id, params) | miss

1. method_idx = method_to_index(method)          O(1), perfect hash on first byte + length
2. path_id = interner_.lookup(path)              O(1), no insert
   if path_id valid and static_[method_idx] has path_id:
       return (route_id, {})                     ← Tier 1, no allocation
3. walk segments of path without allocating:
       for each segment [begin,end) delimited by '/':
           seg_id = interner_.lookup(segment)
           child = find_static_child(node, seg_id)     linear scan, integer compare
           if !child: child = param_child(node)
                      record (param_name_id, begin, end)   ← indices, not strings
           if !child: return miss
4. if node.route_id == NO_ROUTE: return miss
5. materialise params dict ONCE, only on success
```

Two properties matter for the constant factor:

- **No string allocation during the walk.** Segments are `string_view`s into the original path buffer. Param values are recorded as `(offset, length)` pairs in a small stack array and only converted to Python `str`/`int` objects after a match succeeds. On a miss, zero Python objects are allocated — the current implementation allocates a list from `path.strip("/").split("/")` (74 ns) before it can fail.
- **Integer comparison instead of string comparison.** Interned segment ids reduce `seg == "users"` to `seg_id == 42`.

Complexity: **O(k)** where k = path depth, with a k-independent Tier-1 fast path for static routes. Identical asymptotics to the current implementation, materially lower constants.

---

## 4. Typed parameter extraction

`param_kind` drives inline conversion without regex:

| kind | validation | conversion |
|---|---|---|
| `str` | none | `PyUnicode_FromStringAndSize` |
| `int` | all-digits scan (with optional `-`) | `strtoll` → `PyLong_FromLongLong` |
| `uuid` | 36-char shape + hex-digit scan | `PyUnicode` (Python constructs UUID if annotated) |
| `path` | none (catch-all, consumes remainder) | `PyUnicode` |

Failed validation returns miss immediately, matching the current `except (ValueError, TypeError): return None` behaviour at `router.py:496`.

**Regex routes are not natively matched.** Patterns the trie cannot represent (arbitrary regex constraints) fall through to the existing Python Tier-3 regex list (`router.py:286`), exactly as `_trie_insert` already returns `False` for them (`router.py:209`). This preserves full behavioural compatibility for complex patterns at no correctness risk.

---

## 5. Version filtering (B5, 492 ns → ~0 ns)

`_version_matches` runs per candidate and costs 492 ns, 64% of a static match, mostly from two per-call imports. Root cause is a deliberate cycle-break — but `aquilia.versioning.core` is a **leaf** relative to `aquilia.controller`, so hoisting is safe (verified against the SCC analysis in Phase 1 §6).

Native design: **version constraints are resolved to integers at freeze time.**

```cpp
struct VersionConstraint {
    uint8_t kind;      // 0 neutral/none, 1 exact-list, 2 range, 3 bound
    uint32_t list_off; // offset into a shared version-id pool
    uint16_t list_len;
    uint32_t min_id, max_id;
};
```

Version strings are interned to dense ids at startup. A match check becomes an integer comparison or a short scan over a contiguous id list — no imports, no `getattr`, no string parsing.

The **unversioned fast path** (the overwhelmingly common case) is a single branch: if the route's constraint kind is `0` and the request's resolved version id is `NONE`, match immediately. This is the case Phase 2 measured, and it goes from 492 ns to ~2 ns.

Semantics preserved exactly per `router.py:361-468`: `VERSION_MISSING` handling, neutral routes, explicit version lists, ranges, structural `bound_version`, and controller-level fallback. All of it is precomputed rather than re-derived per request.

---

## 6. Route conflict detection

The current implementation raises `RoutingFault("ROUTE_CONFLICT")` when multiple routes match one path+version (`router.py:269`, `:350`, `:515`). This check runs **per request** and requires collecting all matching candidates into a list before deciding.

Native design moves conflict detection to **freeze time**. During `freeze()`, the router walks the trie and asserts each terminal node has at most one route per (method, version-constraint) pair with overlapping constraints. Conflicts raise at startup, where they belong — a route table conflict is a static property of the application, not a per-request condition.

The hot path then returns the single `route_id` directly with no candidate list allocation. This removes a list allocation and a loop from every dynamic match.

**Behavioural note:** this converts a runtime 500 into a startup failure. That is strictly better (fail fast, before serving traffic) but is a behaviour change, so it is gated: the Python layer keeps its runtime check active when `AQUILIA_ENGINE_STRICT_ROUTES=0`, and existing conflict tests are run against both paths.

---

## 7. Reverse routing (`url_for`)

`url_for` (`router.py:645`) is not on the request hot path — it runs during template rendering and response construction. It already uses an O(1) `_name_index`. Native cost would be dominated by the Python string formatting it must return.

**Decision: `url_for` stays in Python.** The native router exposes `route_path(route_id) -> str` so the Python layer can keep its existing substitution logic. One micro-fix is warranted regardless: `router.py:687` executes `import re` and `re.compile` **inside the parameter loop** for typed patterns — that compile should be hoisted and cached (this is a Python-side fix, recorded in the roadmap).

---

## 8. Middleware, groups, nested routers, prefixes

These are all **registration-time** concerns, resolved before `freeze()`:

- **Route groups / nested routers / prefixes:** the Python compiler already flattens prefixes into `route.full_path` at compile time (`controller/compiler.py:81`). The native router only ever sees fully-qualified paths. No native work needed.
- **Middleware:** `MiddlewareStack` builds and caches its chain once (`middleware.py:170`) and is not per-route. Untouched.
- **Prefix optimisation:** the trie provides this structurally — shared prefixes share nodes.

---

## 9. Mutation and lifecycle

```
construct → add_route(method, path, route_id, constraint)* → freeze() → match()*
```

`freeze()` builds the flattened arrays, interns all segments, precomputes version constraints, and runs conflict detection. It is one-way; `add_route` after freeze raises `RuntimeError`.

This matches Phase 1 §2: the route table is only final **after `lifespan.startup`**, so the engine is constructed and frozen there — never at import time.

Post-freeze the router is immutable, so `match()` is lock-free and callable from any thread without synchronisation, fixing the free-threading hazard noted in Phase 1 §8.

**Hot reload:** dev-mode reload discards the router and builds a new one. Because `route_id`s are dense indices into a Python-side array, the Python layer swaps both atomically. This also removes the `id(route)`-keyed cache hazard flagged in Phase 1 §7 — ids are stable dense integers, not memory addresses.

---

## 10. Complexity summary

| Operation | Current | Native | Note |
|---|---|---|---|
| static match | O(1), 782 ns | O(1), ~150 ns | Tier-1 hash, no version imports |
| dynamic match | O(k), 1,173 ns | O(k), ~250 ns | no per-segment allocation |
| miss | O(k), 298 ns | O(k), ~80 ns | zero Python allocation |
| `get_allowed_methods` | O(methods × tiers) | O(methods), array indexed | miss path only |
| registration | O(k) per route | O(k) per route | startup only |
| freeze | — | O(nodes) | startup only, adds conflict detection |

---

## 11. Acceptance criteria

| Criterion | Target |
|---|---|
| Static match | ≤ 200 ns (from 782 ns) |
| Dynamic match, 1 param | ≤ 300 ns (from 1,173 ns) |
| Miss | ≤ 100 ns (from 298 ns) |
| Scaling to 3,000 routes | ≤ +5% vs 15 routes |
| Zero allocation on miss | verified by `tracemalloc` delta ≈ 0 |
| Regex-pattern routes | fall through to Python Tier 3, all tests pass |
| Version semantics | 100% of `tests/test_versioning*` pass |
| Conflict detection | existing conflict tests pass on both paths |
| Fallback parity | identical match results with `_NATIVE=False` |
