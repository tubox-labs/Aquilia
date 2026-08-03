# Phase 7 — Testing Strategy

**Status:** design
**Baseline:** 189 existing test files. The engine must not require a single one to change.

---

## 1. The central test principle: dual-path parity

Every behavioural test runs **twice** — once with the native engine, once with the pure-Python fallback. Identical results are required. This is the single most important guarantee in the project: it makes the native engine deletable at any time.

```python
# tests/conftest.py — addition
import os
import pytest

def pytest_generate_tests(metafunc):
    """Parametrise any test requesting the `engine_mode` fixture over both paths."""
    if "engine_mode" in metafunc.fixturenames:
        metafunc.parametrize("engine_mode", ["native", "fallback"], indirect=True)

@pytest.fixture
def engine_mode(request, monkeypatch):
    from aquilia import _core_loader
    if request.param == "native":
        if not _core_loader._NATIVE:
            pytest.skip("native engine not built")
    else:
        monkeypatch.setattr(_core_loader, "_NATIVE", False)
        _core_loader.use_fallback()
    yield request.param
    _core_loader.reset()
```

The existing 189 files keep running unmodified against whichever path is active by default. A separate CI job runs the **entire** suite with `AQUILIA_ENGINE=0` (Phase 6 §9), which is the real parity gate — it needs no test changes at all.

---

## 2. Test layers

| Layer | Location | Runner | What it proves |
|---|---|---|---|
| C++ unit | `aquilia/_core/tests/*.cpp` | `ctest` | arena, interner, trie, resolver logic in isolation — no Python |
| Binding unit | `tests/engine/test_bindings.py` | pytest | types construct, refcounts balance, exceptions translate |
| Parity | `tests/engine/test_parity.py` | pytest | native and fallback produce identical results |
| Property | `tests/engine/test_properties.py` | pytest + Hypothesis | invariants over generated route tables and paths |
| Fuzz | `tests/engine/fuzz/` | libFuzzer | no crash/UB on arbitrary path bytes |
| Concurrency | `tests/engine/test_concurrency.py` | pytest-asyncio | frozen router safe under `asyncio.gather` |
| Memory | `tests/engine/test_memory.py` | pytest + tracemalloc | zero leak over 10k requests |
| Regression | existing 189 files | pytest | no behaviour change |
| Performance | `benchmarks/engine/` | pytest-benchmark | targets from Phases 3–5 met |

---

## 3. C++ unit tests

Pure C++, no Python linkage, so the core logic is testable in isolation and under sanitizers without an interpreter.

```cpp
// tests/test_router.cpp
TEST(Router, StaticMatchBeatsParam) {
    Interner in; RadixRouter r(in);
    r.add_route(GET, "/users/me", 1, NO_VERSION);
    r.add_route(GET, "/users/{id}", 2, NO_VERSION);
    r.freeze();
    EXPECT_EQ(r.match(GET, "/users/me").route_id, 1u);   // static wins
    EXPECT_EQ(r.match(GET, "/users/42").route_id, 2u);
}

TEST(Router, MissAllocatesNothing) {
    // asserted via a counting allocator installed for the test
}

TEST(Arena, ResetReusesBlocks) {
    Arena a; void* p1 = a.alloc(128); a.reset();
    EXPECT_EQ(a.alloc(128), p1);          // O(1) reset, same block
}

TEST(Interner, IdempotentAndStable) {
    Interner in;
    auto a = in.intern("users"); auto b = in.intern("users");
    EXPECT_EQ(a, b);
    EXPECT_EQ(in.get(a), "users");
}
```

Framework: **GoogleTest via CMake `FetchContent`**, test-only so it never enters the wheel. If offline, the tests degrade to a minimal assert-based harness (`AQUILIA_ENGINE_TESTS=minimal`).

---

## 4. Parity tests

The highest-value Python tests. They assert native and fallback agree on the *same* inputs, including edge cases.

```python
# tests/engine/test_parity.py
ROUTE_TABLE = [
    ("GET",  "/"),                    ("GET",  "/users"),
    ("GET",  "/users/{id}"),          ("GET",  "/users/{id}/posts/{pid}"),
    ("POST", "/users"),               ("GET",  "/files/{path:path}"),
    ("GET",  "/v1/items"),            ("GET",  "/items/{id:int}"),
]

PROBE_PATHS = [
    "/", "/users", "/users/", "/users/42", "/users/me",
    "/users/42/posts/7", "/files/a/b/c.txt", "/items/abc",   # int cast must fail
    "/nope", "", "//", "/users//42", "/USERS", "/users/42/",
    "/items/-1", "/items/999999999999999999999",             # overflow
]

def test_match_parity(native_router, fallback_router):
    for method in ("GET", "POST", "HEAD", "DELETE"):
        for path in PROBE_PATHS:
            n = native_router.match(method, path)
            f = fallback_router.match(method, path)
            assert n == f, f"divergence on {method} {path}: {n!r} != {f!r}"
```

Parity is also asserted for: DI resolution order, scope-clear behaviour, `RequestContext` attribute get/set including the `_extra` escape hatch, and binding-cache results.

---

## 5. Property-based tests

Hypothesis generates route tables and probe paths; invariants are checked rather than specific outputs.

```python
# tests/engine/test_properties.py
@given(routes=route_tables(), path=paths())
def test_invariants(routes, path):
    r = build_native(routes)
    m = r.match("GET", path)

    # I1: a match implies the matched pattern actually accepts the path
    if m.matched:
        assert pattern_accepts(routes[m.route_id], path)

    # I2: native and fallback never disagree
    assert m == build_fallback(routes).match("GET", path)

    # I3: static routes always beat parametric ones
    # I4: matching is deterministic across repeated calls
    assert m == r.match("GET", path)

    # I5: no match ever allocates a param not present in the pattern
    assert set(m.params) <= pattern_params(routes[m.route_id]) if m.matched else True
```

Generators deliberately include: empty segments, unicode, `%`-encodings, very deep paths (200 segments), 4 KB segments, trailing/duplicate slashes, and paths differing only by case.

---

## 6. Fuzz testing

```cpp
// tests/fuzz/fuzz_router.cpp — libFuzzer entry point
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    static RadixRouter* r = build_fixed_table();   // frozen once
    std::string path(reinterpret_cast<const char*>(data), size);
    r->match(GET, path);                           // must never crash or UB
    return 0;
}
```

Also fuzzed: `Interner::intern` with arbitrary bytes (including embedded NULs and invalid UTF-8), and `Arena::alloc` with adversarial size/alignment sequences.

Run under ASAN+UBSAN. CI budget: 60 s per target per PR; a nightly job runs 30 min per target. A crash reproducer is committed as a regression test.

**Invalid UTF-8 is explicitly in scope** — ASGI servers can deliver arbitrary bytes in the path, so the matcher must be byte-safe and never assume valid UTF-8.

---

## 7. Concurrency and thread-safety

```python
# tests/engine/test_concurrency.py
async def test_frozen_router_concurrent_match():
    router = build_and_freeze(500)
    async def worker():
        for _ in range(1000):
            assert router.match("GET", "/users/42").route_id == EXPECTED
    await asyncio.gather(*(worker() for _ in range(64)))

async def test_request_scope_isolation():
    """Concurrent requests must not observe each other's request-scoped state."""
    async def one(i):
        ctx = RequestContext()
        ctx.bind_request(FakeRequest(i))
        await asyncio.sleep(0)               # force interleaving
        assert ctx.request.id == i
    await asyncio.gather(*(one(i) for i in range(256)))
```

Plus a C++ test that spawns `std::thread`s against a frozen router (TSAN-clean), proving the post-freeze lock-free claim from Phase 5 §9 — and directly addressing the free-threading hazard identified in Phase 1 §8.

---

## 8. Memory correctness

| Check | Method | Gate |
|---|---|---|
| Leaks | ASAN `LeakSanitizer` | zero leaks |
| UB | UBSAN | zero reports |
| Refcounts | `sys.gettotalrefcount()` delta over 10k requests (debug build) | ≤ 0 net growth |
| Python-level growth | `tracemalloc` snapshot delta | < 1 KB over 10k requests |
| Arena reuse | block count stable after warmup | no unbounded growth |
| Interner growth | bounded after freeze | no post-freeze inserts |

```python
def test_no_refcount_growth():
    warm(1000)
    before = sys.gettotalrefcount()          # requires a debug build
    drive_requests(10_000)
    assert sys.gettotalrefcount() - before < 100
```

---

## 9. Soak and stress

| Test | Duration | Assertion |
|---|---|---|
| Sustained load | 30 min, 5k req/s | RSS flat after warmup; p99 does not drift |
| Route churn | 10k freeze/discard cycles | no growth (validates hot-reload path) |
| Large table | 50k routes | match still ≤ +5% vs 15 routes |
| Deep paths | 200-segment paths | no stack overflow (iterative walk, not recursive) |
| Pathological trie | 10k routes sharing a 50-segment prefix | no quadratic blowup |

Marked `@pytest.mark.slow`, excluded from PR runs, executed nightly — matching the existing `slow` marker convention in `pyproject.toml`.

---

## 10. Performance regression gates

```python
# tests/engine/test_perf_gates.py
GATES_NS = {
    "route_match_static":   200,
    "route_match_dynamic":  300,
    "route_match_miss":     100,
    "di_resolve_cached":    200,
    "ctx_acquire_reset":    100,
}

@pytest.mark.perf
@pytest.mark.parametrize("name,budget", GATES_NS.items())
def test_within_budget(name, budget):
    measured = run_benchmark(name)
    assert measured <= budget * 1.25, f"{name}: {measured:.0f} ns > {budget} ns (+25% tol)"
```

25% tolerance absorbs CI noise while still catching real regressions. The end-to-end gate (`≤ 7 µs/request`) runs on a dedicated non-virtualised runner because shared CI is too noisy for a 16 µs measurement.

---

## 11. Coverage targets

| Component | Target | Tool |
|---|---|---|
| C++ core (`src/*.cpp`) | ≥ 95% line, ≥ 90% branch | `gcov`/`llvm-cov` |
| Bindings (`module.cpp`) | 100% line | every entry point exercised |
| Fallback (`_core_fallback.py`) | ≥ 95% | `pytest-cov` |
| Integration glue in `aquilia/` | ≥ 90% | `pytest-cov` |

Coverage is reported per-PR; a drop below target blocks merge. `module.cpp` demands 100% because an unexercised binding is an untested ABI boundary.

---

## 12. What is explicitly NOT tested natively

Per Phases 4 and 5, these stay in Python and keep their existing tests unchanged:

- DI graph compilation and Tarjan cycle detection (startup-only)
- The three runtime cycle guards (ContextVar-based)
- Scope-violation policy enforcement
- Plugin hooks and diagnostic event streams
- `url_for` / reverse routing
- Regex-pattern route matching (Tier 3)

Their existing tests are the regression gate: if native work breaks them, the change is wrong.
