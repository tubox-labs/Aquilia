# Phase 9 — Implementation Plan

**Status:** design
**Prerequisite:** `06-python-fixes.md` must land and be re-benchmarked before any C++ is written.

---

## 1. Sequencing rationale

The Python fixes come first for three reasons, and the third is the one that has already cost this project once:

1. **They are worth ~41 µs/page and ~40 µs/100 payloads for ~30 lines** (`06` §3) — a better return per unit of risk than anything in the native plan.
2. **They reduce the native engine's scope.** F1 removes 53% of `get_field_value`, which was a meaningful share of what native validation was going to win.
3. **They change the profile the engine is designed against.** In the Phase 9 controller work, two native components (9E, 9G) were fully specified against a pre-fix profile, then cancelled after measurement showed they would be *slower* than the Python they replaced. Designing against a stale profile is the specific failure this ordering prevents.

---

## 2. Milestones

### M0 — Python fixes (`06`)

Implement F1–F5, one commit each, suite green between each. Then:

```bash
python benchmarks/models/profile_baseline.py --json benchmarks/models/post_fixes.json
```

**Exit gate:** `from_row` ≤ 2,650 ns, `Sigil.validate` ≤ 4,700 ns, 7,850 tests still pass.

**If the gains differ materially from `06` §3, revise `03` §13 and this document before proceeding.** This gate is not a formality — it is the checkpoint that decides whether the native work is still worth its projected shape.

---

### M1 — Missing benchmarks (`08` §2.4)

Before any C++, close the measurement gaps:

- `benchmarks/models/e2e_query.py` — hydration as a percentage of a **real** sqlite query. Currently the entire ROI argument rests on component numbers.
- `benchmarks/models/conversion_floors.py` — promote from scratch.
- `benchmarks/models/boundary.py` — per-platform boundary cost.
- `benchmarks/models/scaling.py` — rows/columns/fields axes.

**Exit gate:** hydration is ≥ 25% of a real 100-row query. **If it is not, stop** — a native engine that halves 5% of a query is not worth a second C++ extension, and this plan should be abandoned in favour of the M0 fixes alone.

This gate can genuinely fail. It is stated as a stop condition, not a formality.

---

### M2 — Build system + loader

```
aquilia/_dataengine/CMakeLists.txt
aquilia/_dataengine/src/module.cpp        ← NB_MODULE + noop()
aquilia/_dataengine_loader.py             ← fail-soft, mirrors _core_loader
aquilia/_dataengine.pyi
```

Reuses the `scikit-build-core` backend already configured for `_core`. The second extension is added to the same CMake project.

**Exit gate:** `uv pip install -e .` succeeds; `DATAENGINE_NATIVE is True`; suite passes with the extension present, absent, and disabled.

---

### M3 — Conversions + UUID parser

`convert.hpp/.cpp`, `uuid_parse.hpp/.cpp`, with C++ unit tests. No plans yet.

This milestone exists to validate the single riskiest measured assumption — that native UUID parsing is a real ~10× win (`02` §3) — **before** building the plan machinery that depends on it.

**Exit gate:** `ctest` passes under ASAN+UBSAN; native UUID parse ≤ 50 ns (from 354); conversion parity tests pass exhaustively (`07` §4), including the `Decimal` exponent and unbounded-integer cases.

---

### M4 — Validation engine (`05`)

Chosen **before** hydration deliberately: validation has 90% framework overhead vs hydration's 71% (`02` §2), it has no `save()`-corruption risk (`07` §3.1), and its integration point is a single call site (`core.py:1364`) rather than a query-path rewrite. It is the higher-value, lower-risk half.

`fieldplan.hpp/.cpp` + bindings + integration.

**Exit gate:** `Sigil.validate` equivalent ≤ 1,500 ns; 100 payloads ≤ 120 µs; error messages byte-identical; all `tests/test_contract*` pass unmodified; ineligible contracts fall back.

---

### M5 — Hydration engine (`04`)

`rowplan.hpp/.cpp` + bindings + integration at `query.py:1416`.

**Exit gate:** `from_row` equivalent ≤ 1,200 ns; 100 rows ≤ 120 µs; **`save()` round-trip SQL identical** (the data-loss gate, `07` §3.1); deferred/FK/no-signal semantics preserved; all `tests/test_models*` pass unmodified.

---

### M6 — End-to-end validation and results

Run the full suite against `post_fixes.json`, produce `docs/models-engine/10-results.md` following the `docs/engine/09-results.md` template: gates met **and missed**, rejected components with their evidence, corrections to projections.

---

### M7 — Deferred: adapter row protocol (`04` §6)

If the adapter handed the engine raw tuples plus one key tuple, B1 and B2 would disappear entirely rather than being optimised (~37 µs/page). This requires changing `DatabaseAdapter.fetch_all`'s contract (`db/backends/base.py:115`), which is public API implemented by four backends.

Separate milestone with its own compatibility analysis. **Not** bundled into M5.

---

## 3. File creation order

```
M0:  aquilia/contracts/sigil.py            (modify — F1)
     aquilia/models/base.py                (modify — F2, F5)
     aquilia/sqlite/_rows.py               (modify — F3)
     aquilia/contracts/core.py             (modify — F4)
     benchmarks/models/post_fixes.json

M1:  benchmarks/models/e2e_query.py
     benchmarks/models/conversion_floors.py
     benchmarks/models/boundary.py
     benchmarks/models/scaling.py

M2:  aquilia/_dataengine/CMakeLists.txt
     aquilia/_dataengine/src/module.cpp
     aquilia/_dataengine_loader.py
     aquilia/_dataengine.pyi
     .github/workflows/dataengine.yml

M3:  aquilia/_dataengine/src/typecode.hpp
     aquilia/_dataengine/src/convert.hpp/.cpp
     aquilia/_dataengine/src/uuid_parse.hpp/.cpp
     aquilia/_dataengine/tests/test_convert.cpp
     aquilia/_dataengine/tests/test_uuid_parse.cpp
     tests/dataengine/test_convert_parity.py

M4:  aquilia/_dataengine/src/fieldplan.hpp/.cpp
     aquilia/_dataengine/tests/test_fieldplan.cpp
     tests/dataengine/test_validation_parity.py
     tests/dataengine/test_eligibility.py
     aquilia/contracts/core.py             (modify — plan hook)

M5:  aquilia/_dataengine/src/rowplan.hpp/.cpp
     aquilia/_dataengine/tests/test_rowplan.cpp
     tests/dataengine/test_hydration_parity.py
     tests/dataengine/test_memory.py
     aquilia/models/query.py               (modify — plan hook)

M6:  docs/models-engine/10-results.md
```

---

## 4. Success criteria, measured against `post_fixes.json`

| Metric | Now | After M0 | After M5 |
|---|---|---|---|
| `from_row`, 8 columns | 3,002 ns | ≤ 2,650 ns | ≤ 1,200 ns |
| `Sigil.validate`, 8 fields | 5,034 ns | ≤ 4,700 ns | ≤ 1,500 ns |
| 100-row page | 311 µs | ≤ 275 µs | ≤ 120 µs |
| 100 payloads | 501 µs | ≤ 465 µs | ≤ 120 µs |
| Boundary crossings/batch | — | — | exactly 1 |
| Fallback parity | — | — | 100% with `AQUILIA_DATAENGINE=0` |
| ASAN/UBSAN | — | — | zero reports |
| Existing tests | 7,850 | 7,850 | 7,850, unmodified |

---

## 5. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Hydration is a small fraction of a real query** | medium | **fatal to the whole plan** | M1 gate measures it before any C++; explicit stop condition |
| **`_original_values` divergence → `save()` data loss** | medium | **severe, silent** | `07` §3.1 round-trip gate; M5 cannot pass without it |
| `IntFacet` cast semantics reimplemented wrongly (`3.9` truncated, `True` accepted) | medium | severe, silent | `07` §3.2 pins every row of the table |
| `Decimal` exponent lost (`1.10` → `1.1`) | medium | severe for money | `07` §4 `as_tuple()` assertion |
| Unbounded ints wrapped at int64 | low | severe | `07` §4 corpus includes 30-digit values |
| Error message drift → changed 422 bodies | medium | moderate, user-visible | byte-identical assertion, `07` §3.4 |
| Plan cache unbounded across projections | low | moderate | bounded by distinct `only()`/`defer()` shapes; measured in `08` §5 |
| `id()` reuse in the F3 row-key cache | medium | moderate | `06` §F3 mandates the cursor-attached cache, not the `id()` dict |
| Native→Python calls for date/decimal introduce re-entrancy | low | moderate | only captured CPython C constructors; eligibility excludes all user code (`03` §5) |
| Second extension inflates build time / wheel matrix | medium | low | shares the CMake project; optional, fail-soft |
| M0 fixes change the profile enough to invalidate M4/M5 targets | **high** | moderate | that is exactly what the M0 exit gate is for |
| Free-threaded build races on plan cache | low | low | plans immutable; duplicate build is harmless (`03` §11) |

---

## 6. What would make this project not worth doing

Stated plainly, so the answer is decided by measurement rather than by momentum:

1. **M1 shows hydration < 25% of a real query.** Then driver and I/O dominate, and the M0 Python fixes are the whole deliverable.
2. **M0 alone reaches within ~30% of the native targets.** Then the second extension is not worth its build, CI, and maintenance cost.
3. **M3 shows native UUID parsing under ~3×.** UUID and JSON are the only per-value native wins (`02` §3); if UUID does not deliver, the value rests entirely on removing interpretation overhead, which is still real but roughly halves the projected gain.

The Phase 9 engine delivered 10–13% end-to-end against a projected 2.5× — because the Python fixes had already captured most of the available gain before the C++ was written. **That outcome is a likely outcome here too, and the M0 and M1 gates exist to discover it early rather than after two extensions are in the tree.**

---

## 7. Relationship to the existing `_core` engine

| | `_core` (shipped) | `_dataengine` (proposed) |
|---|---|---|
| Path | request | data |
| Exercised | every request | ORM/contract use only |
| Components | router, request context | row plan, field plan, conversions |
| Boundary crossings | per request (4–6) | per batch (1) |
| Loader | `_core_loader.py` | `_dataengine_loader.py` |
| Disable | `AQUILIA_ENGINE=0` | `AQUILIA_DATAENGINE=0` |

Deliberately independent: separate loaders, separate env vars, separate CI gates. Neither can break the other, and either can be disabled alone. They share the `PyRef` implementation and the fail-soft loader pattern, both already ASAN-clean under the Phase 9 suite.
