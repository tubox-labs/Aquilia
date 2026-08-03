# Phase 9 — Implementation Results

**Status:** implemented
**Baseline:** post-9A Python fixes (`benchmarks/engine/post_fixes.json`)
**Measured:** `benchmarks/engine/post_native.json`, macOS arm64, CPython 3.11.15, nanobind 2.13

---

## 1. Summary

The native engine ships as an optional accelerator behind `aquilia/_core_loader.py`.
Two of the five planned native components were built. Three were **rejected on
measurement** — the number that killed them is in §5, and it is the single most
important result in this phase.

| Component | Planned | Outcome |
|---|---|---|
| Build system (9B) | scikit-build-core + CMake + nanobind | **shipped** |
| Interner (9C) | string → dense id | **shipped** (used by nothing on the hot path — see §6) |
| Arena (9C) | per-request bump allocator | **rejected**: zero consumers |
| Router (9D) | radix trie + static map | **shipped** |
| DI resolver (9E) | native cache + token interner | **rejected**: slower than the Python dict |
| RequestContext (9F) | fixed native slots | **shipped** — the largest win |
| Binding cache (9G) | native `get_type_hints` memo | **rejected**: 5× slower than `dict.get` |

---

## 2. End-to-end result

Same machine, same build, engine toggled with `AQUILIA_ENGINE`:

| Metric | Engine off | Engine on | Change |
|---|---|---|---|
| Static request | 7.98 µs | 7.14 µs | **−10.5%** |
| Dynamic request | 8.85 µs | 7.69 µs | **−13.1%** |
| Throughput, static | 125,312 req/s | 140,011 req/s | **+11.7%** |
| Throughput, dynamic | 113,034 req/s | 130,083 req/s | **+15.1%** |

Cumulative against the pre-9A baseline (16.49 µs static / 20.21 µs dynamic):
**−57% static, −62% dynamic.** The Phase 9A Python fixes did most of that; the
native engine added the last 10–13%.

---

## 3. Component measurements

| Operation | Engine off | Engine on | Change |
|---|---|---|---|
| `match_sync` static | 319 ns | 224 ns | −30% |
| `match_sync` dynamic | 710 ns | 373 ns | **−47%** |
| `match_sync` miss | 301 ns | 99 ns | **−67%** |
| Native match alone (no wrapper) | — | 42 ns | — |
| `RequestCtx` construct | 555 ns | 34 ns | **−94%** |
| Slot write | 58 ns | 14.5 ns | **−75%** |
| Slot read | 10.9 ns | 12.6 ns | +16% (see note) |

**Slot reads got marginally slower.** A nanobind `def_prop_rw` getter is a
function call where a Python `__slots__` read is a direct descriptor fetch. This
is a real regression on reads, accepted because writes outnumber reads on the
request path (~24 writes vs ~8 reads) and the write saving is 4× larger.

---

## 4. Gate status — honest accounting

| Gate | Target | Measured | Verdict |
|---|---|---|---|
| Static match | ≤ 200 ns | 224 ns | **missed by 12%** |
| Dynamic match | ≤ 300 ns | 373 ns | **missed by 24%** |
| Miss | ≤ 100 ns | 99 ns | met |
| Ctx acquire | ≤ 100 ns | 34 ns | met (3× better) |
| Full request static | ≤ 5 µs | 7.14 µs | **missed** |
| Fallback parity | 100% | 7,666 pass, engine off | met |
| ASAN/UBSAN | zero reports | zero | met |
| C++ unit tests | pass |  43/43 | met |

**Why the match gates were missed.** The native match is 42 ns; the gate measures
`match_sync`, which adds Python-side cost the native layer cannot touch:

```
native match                     42 ns
ControllerRouteMatch(...)        87 ns   <- dataclass __init__
match_sync frame + dispatch      12 ns
eligibility dict lookup, etc.   ~83 ns
                                ------
                                224 ns
```

`ControllerRouteMatch.__init__` alone costs **more than twice the native match**.
`slots=True` was added (93 → 87 ns); the remainder is dataclass `__init__`
bytecode. Reaching 200 ns means returning a native tuple instead of a Python
dataclass, which is an API change across every `match_sync` caller — out of scope
here and recorded as follow-up work.

**Why the 5 µs request gate was missed.** §7 of the Phase 2 audit already showed
routing + DI to be ~5% of a request. The current profile confirms it: with
routing and DI-scope made *free*, the request would drop 7.26 → 6.92 µs, a 4.6%
ceiling. The remaining 76% is the controller engine, middleware chain, and
response serialisation. **No router or DI work of any quality can reach 5 µs**;
that gate was set against a cost model the Phase 2 evidence had already refuted.

---

## 5. Why 9E and 9G were rejected

Both phases targeted paths that are already a single Python dict lookup after 9A.
The decisive measurement (`benchmarks/engine/call_overhead.py`):

| Operation | Cost |
|---|---|
| nanobind `noop()` — the binding floor | **7.7 ns** |
| nanobind call with real arguments | **~42 ns** |
| `dict.get(str)` — what 9E would replace | 11.1 ns |
| `dict.get(int)` — what 9G would replace | 8.3 ns |

**Crossing the binding boundary costs more than the lookup being replaced.** A
native binding cache is ~5× slower than the `dict.get(int)` it displaces. This is
not an implementation-quality question; it is arithmetic, and no amount of C++
skill changes it.

The Phase 6 design assumed ~60 ns call overhead and budgeted 4–6 calls per
request against it. The real floor is 7.7 ns — **8× better than assumed** — which
is why the router and context still win. But the same measurement that vindicates
those two components rules out the two that would replace dict lookups.

Two corrections to earlier analysis, recorded so they are not repeated:

1. The Phase 4 spec cites `_unwrap_token` at 1,167 ns. It is now **48.8 ns** —
   the 9A P6 fast-exit already fixed it. The spec's premise is stale.
2. An intermediate measurement suggested the DI cache-key f-string cost 38 ns and
   was worth a Python-side fix. That was **wrong**: `di/core.py:530` already
   short-circuits when `tag is None`, so the untagged path costs **4.5 ns**. The
   38 ns figure measured an f-string that the real code does not execute.

---

## 6. Why the Arena was not built, and what the Interner is for

**Arena — rejected.** The Phase 3 design specifies a per-request bump allocator
for "path-param strings, header value copies, binding-result temporaries". The
router as built needs none of them: segments are `string_view`s into the caller's
path buffer, captured params are `(offset, length)` pairs in a fixed stack array,
and Python objects are constructed only after a match succeeds. An allocator with
no allocations to serve is dead code, so it was not written.

**Interner — built, but honestly: it is not on the hot path.** It is specified as
the backing for route-segment and version-id interning. Route segments do not use
it: a trie node's fan-out is 2–8, so a linear scan of inline `memcmp` beats
hashing a segment to get an id and then comparing integers. Version constraints
do not use it either, because version filtering stayed in Python (§7). It is
shipped, unit-tested, and available for the version work if that is ever made
native — but it currently earns its place only as a tested primitive, not as a
measured win. Recorded plainly rather than dressed up.

---

## 7. Scope boundaries the native router deliberately keeps

Native matching is decided **per method**, and conservatively. A method falls back
entirely to Python if *any* of its routes has:

- version metadata (route, bound, or controller level)
- query-param requirements
- validators on a path param
- a param type outside `str`/`int`/`float`
- a route conflict (duplicate static path or trie terminal)

This keeps the native tier a pure accelerator. Version filtering in particular was
left in Python because the design's freeze-time approach converts a per-request
`RoutingFault(ROUTE_CONFLICT)` into a startup failure — better behaviour, but a
*behaviour change*, and not one worth making for the unversioned fast path that
already dominates.

### Two correctness traps found during implementation

1. **`{name}` is not the pattern syntax it looks like.** `PatternCompiler` reports
   *zero* params for `/u/{id}`. But the HTTP decorators normalise `{name}` to
   `<name:str>` *before* compilation, so `route.full_path` is `/u/{id}` while
   `compiled_pattern.raw` is `/u/<id:str>` and `params` contains `id`. Building
   the native router from `full_path` made it treat `{id}` as a literal segment —
   matching the text `/u/{id}` and missing `/u/42`, while Python did the opposite.
   The native router is built from `cp.raw`, the only string that agrees with
   `cp.params`. Pinned by `test_brace_syntax_normalises_to_a_param`.

2. **`int()` is more permissive than a digit scan.** CPython accepts `1_000`,
   `" 42"`, and Unicode decimal digits. A native matcher that rejected those would
   turn a Python match into a 404. The router returns a third state, `DEFER`
   (= `NotImplemented`), for values outside its strict ASCII fast path, and the
   Python tiers then decide. Pinned by `IntFormsCPythonAcceptsAreDeferred`.

---

## 8. Verification

| Check | Result |
|---|---|
| Full suite, engine on | **7,850 passed**, 8 skipped |
| Full suite, engine off (`AQUILIA_ENGINE=0`) | **7,666 passed**, 192 skipped |
| Full suite, extension file **physically removed** | **7,666 passed**, 192 skipped |
| C++ unit tests (`ctest`) | 43/43 pass (34 router, 9 interner) |
| C++ tests under ASAN + UBSAN | 43/43 pass, zero reports |
| Router parity (native vs Python) | 172 assertions pass |
| Refcount balance, 10k slot writes | net zero |
| Object growth, 80k matches | < 100 objects |
| Perf gates | 7/7 within budget |
| `ruff check` / `ruff format` | clean |

**On the nanobind shutdown report.** A full run prints `leaked 3 instances`. This
is *retention, not a leak*: the count is fixed at 3 across runs of 7,850 tests
that construct ~48,000 contexts, and the objects are two `RequestCtx` held in
`ContextVar`s plus one `Router` held by a test server at interpreter exit. A real
refcount bug scales with operation count; `tests/engine/test_memory.py` asserts
that it does not. The one instance that *was* mine — a custom `_Defer` sentinel
class — was removed by using `NotImplemented` instead.

---

## 9. Follow-up work

| Item | Value | Note |
|---|---|---|
| Return a tuple from `match_sync` instead of `ControllerRouteMatch` | ~87 ns/request | API change across all callers; would meet the 200 ns gate |
| Target the controller engine / middleware / response path | up to 76% of a request | Where the remaining time actually is |
| Native version filtering | ~58 ns/request | Requires accepting startup-time conflict detection |
| Splat (`*rest`) routes do not match on **either** path | correctness | Pre-existing, unrelated to this work; reproduces with the engine off |
| Package import cycle (`di → faults → middleware → di`) | maintainability | Pre-existing; `from aquilia.di.core import ...` as a first import fails on a clean tree |

The honest summary: **the native engine delivered 10–13% end-to-end, not the
2.5× the Phase 3 mandate projected.** That projection assumed ~10 µs of
addressable cost; the Phase 9A Python fixes had already removed most of it for
~35 lines of Python. The measurable remainder lives in the controller engine and
response path, which is where the next phase should go — not further into C++.
