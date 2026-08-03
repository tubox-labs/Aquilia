# Phase 9 — Implementation Plan

**Status:** design
**Prerequisite:** Phase 8 Python fixes must land and be re-benchmarked before native work begins.

---

## 1. Sequencing rationale

The Phase 8 fixes are worth ~60% end-to-end gain with ~35 lines of Python. They must land first because:

1. They change the hot-path profile. After P1 (`register_instance`) and P3 (pool removal), the dominant costs shift. The native engine must target the *post-fix* hot spots.
2. They reduce the native engine's scope. `RequestContext` no longer needs to replace a pool — it replaces a plain constructor call. The bar is lower and the design is simpler.
3. They establish the new baseline that Phase 9 success criteria are measured against.

---

## 2. Implementation phases

### Phase 9A — Python fixes (Phase 8 rollout)

Implement fixes P1–P7 in the order specified in `docs/engine/08-python-fixes.md`. Each fix is a separate commit. After all seven:

```
python benchmarks/engine/profile_baseline.py --json benchmarks/engine/post_fixes.json
python benchmarks/engine/e2e_attribution.py
```

Commit `post_fixes.json`. This is the new baseline. If the measured gains differ materially from the Phase 8 §9 projections, update the Phase 9 success criteria before proceeding.

**Exit gate:** full request ≤ 8 µs (from 16.49 µs). If not met, investigate before proceeding.

---

### Phase 9B — Build system

Add `scikit-build-core` to `pyproject.toml` and create the `CMakeLists.txt` skeleton. The extension does not exist yet — this phase just proves the build system works.

```
aquilia/_core/
  CMakeLists.txt
  src/
    module.cpp          ← NB_MODULE(_core, m) { }  (empty)
  tests/
    CMakeLists.txt
    test_stub.cpp       ← TEST(Stub, Builds) { EXPECT_TRUE(true); }
```

Gate: `uv pip install -e .` succeeds; `python -c "from aquilia._core_loader import _NATIVE; print(_NATIVE)"` prints `True`; `ctest` passes.

---

### Phase 9C — Arena and interner

Implement `arena.hpp/cpp` and `interner.hpp` with full C++ unit tests. No Python bindings yet.

```cpp
// tests/test_arena.cpp
TEST(Arena, AllocAligns)
TEST(Arena, ResetReusesBlocks)
TEST(Arena, LargeAlloc)
TEST(Arena, ZeroSizeAlloc)

// tests/test_interner.cpp
TEST(Interner, IdempotentIntern)
TEST(Interner, DifferentStrings)
TEST(Interner, EmptyString)
TEST(Interner, LargeVolume)
TEST(Interner, NullBytes)
```

Gate: `ctest` passes under ASAN+UBSAN.

---

### Phase 9D — Native router

Implement `router.hpp/cpp` with C++ unit tests, then add nanobind bindings in `module.cpp`.

**C++ tests first:**
```cpp
TEST(Router, StaticMatchBeatsParam)
TEST(Router, DynamicIntParam)
TEST(Router, DynamicIntParamInvalid)
TEST(Router, MissAllocatesNothing)
TEST(Router, ScalingTo3000Routes)
TEST(Router, FreezeIsOneWay)
TEST(Router, ConflictDetectedAtFreeze)
TEST(Router, VersionNeutralMatchesAll)
TEST(Router, VersionExactList)
```

**Python parity test:**
```python
# tests/engine/test_router_parity.py
@pytest.mark.parametrize("engine_mode", ["native", "fallback"])
def test_match_parity(engine_mode, ...):
    ...
```

**Integration:** replace `ControllerRouter.match_sync` with a delegation to the native router when `_NATIVE` is true. The Python router remains the source of truth for registration; the native router is built from it at `freeze()` time.

Gate: all existing `tests/test_routing*.py` pass; parity test passes; static match ≤ 200 ns.

---

### Phase 9E — Native DI resolver

Implement `di_resolver.hpp/cpp` with C++ unit tests, then bindings.

**C++ tests:**
```cpp
TEST(DIResolver, CacheHitFast)
TEST(DIResolver, MissReturnsNull)
TEST(DIResolver, RequestScopeClear)
TEST(DIResolver, ScopeTableCorrect)
TEST(DIResolver, FreezeIsOneWay)
```

**Integration:** `Container.resolve_async` delegates to `_native_di.get(token_id)` before the Python cache lookup. On miss, falls through to existing Python logic unchanged.

Gate: all existing `tests/test_di*.py` pass; cached resolve ≤ 200 ns.

---

### Phase 9F — Native RequestContext

Implement `request_ctx.hpp/cpp` with bindings. This is the highest-value native component post-fixes.

**Design:** `RequestContext` is a nanobind class with fixed slots (`request`, `identity`, `session`, `auth`, `container`, `state`, `request_id`) and a `nb::dict` for `_extra`. No `__setattr__` override — nanobind's `def_rw` generates direct slot access.

**Integration:** `asgi.py` constructs `RequestContext()` instead of `RequestCtx(...)`. `RequestCtx` becomes a thin Python subclass of `RequestContext` for backward compatibility with code that `isinstance`-checks it.

Gate: all existing `tests/test_controller*.py` pass; `ctx_acquire_reset` ≤ 100 ns; `isinstance(ctx, RequestCtx)` still true.

---

### Phase 9G — Binding cache

Implement `binding_cache.hpp/cpp`. Caches `(handler_id → (signature, type_hints_dict))` in C++, eliminating the `get_type_hints` call on every request.

**Integration:** `ControllerEngine._bind_special_parameters` calls `_native_bindings.get_hints(id(handler))` instead of `get_type_hints(handler)`. On miss, calls Python `get_type_hints` and stores the result.

Gate: `get_type_hints` benchmark ≤ 20 ns (cache hit); all controller tests pass.

---

### Phase 9H — End-to-end validation

Run the full benchmark suite against the post-native baseline:

```
python benchmarks/engine/profile_baseline.py --json benchmarks/engine/post_native.json
python benchmarks/engine/e2e_attribution.py
python benchmarks/engine/evidence.py
python benchmarks/engine/evidence2.py
```

Compare `post_native.json` against `post_fixes.json`. Produce `docs/engine/09-results.md` with the final numbers.

Run the full test suite with `AQUILIA_ENGINE=0` (fallback parity gate).

---

## 3. File creation order

```
Phase 9B:  pyproject.toml (modified)
           aquilia/_core/CMakeLists.txt
           aquilia/_core/src/module.cpp
           aquilia/_core_loader.py
           aquilia/_core_fallback.py

Phase 9C:  aquilia/_core/src/arena.hpp
           aquilia/_core/src/arena.cpp
           aquilia/_core/src/interner.hpp
           aquilia/_core/tests/test_arena.cpp
           aquilia/_core/tests/test_interner.cpp

Phase 9D:  aquilia/_core/src/router.hpp
           aquilia/_core/src/router.cpp
           aquilia/_core/tests/test_router.cpp
           tests/engine/test_router_parity.py
           (modify) aquilia/controller/router.py

Phase 9E:  aquilia/_core/src/pyref.hpp
           aquilia/_core/src/di_resolver.hpp
           aquilia/_core/src/di_resolver.cpp
           aquilia/_core/tests/test_di_resolver.cpp
           tests/engine/test_di_parity.py
           (modify) aquilia/di/core.py

Phase 9F:  aquilia/_core/src/request_ctx.hpp
           aquilia/_core/src/request_ctx.cpp
           tests/engine/test_ctx_parity.py
           (modify) aquilia/controller/base.py
           (modify) aquilia/asgi.py

Phase 9G:  aquilia/_core/src/binding_cache.hpp
           aquilia/_core/src/binding_cache.cpp
           tests/engine/test_binding_cache.py
           (modify) aquilia/controller/engine.py

Phase 9H:  docs/engine/09-results.md
```

---

## 4. Success criteria (post-native, measured against post-fix baseline)

| Metric | Post-fix baseline | Post-native target |
|---|---|---|
| Full request, static | ~8 µs | ≤ 5 µs |
| Static route match | ~360 ns | ≤ 200 ns |
| DI cached resolve | ~200 ns | ≤ 200 ns (already met by P6) |
| RequestContext acquire | ~600 ns | ≤ 100 ns |
| `get_type_hints` (cache hit) | ~14 ns (P2) | ≤ 20 ns |
| Fallback parity | — | 100% test pass with `AQUILIA_ENGINE=0` |
| No import cycle | — | `import_graph.py` shows no new SCC members |
| ASAN/UBSAN | — | zero reports |
| Wheel builds | — | 3 OS × 3 Python, all green |

---

## 5. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| nanobind call overhead exceeds budget | Low | Measured at ~60 ns; 4–6 calls/request = 240–360 ns, within budget |
| `id(handler)` reuse in binding cache | Low | Handlers live for process lifetime; hot-reload clears the cache |
| `RequestContext` breaks `isinstance(ctx, RequestCtx)` | Medium | `RequestCtx` subclasses `RequestContext`; existing checks pass |
| C++ build fails on user machine | Medium | Fail-soft loader; pure-Python fallback always works |
| Free-threaded Python 3.13 | Low | Frozen router is lock-free; request state is per-request; documented |
| Phase 8 fixes change hot-spot ranking | Medium | Re-benchmark after 9A; update 9D–9G targets before implementing |
| `_extra` dynamic attribute writes break after pool removal | Medium | Audit grep in Phase 8 §3 before merging P3 |
