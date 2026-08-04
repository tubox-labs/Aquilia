# Phase 8 — Benchmark Strategy

**Status:** design
**Harness:** `benchmarks/models/profile_baseline.py` (exists, produces `baseline.json`)
**Principle:** every claim in `03`–`06` is either already measured or is explicitly labelled a projection. This document defines how the projections get converted into measurements, and how a regression gets caught.

---

## 1. Methodology

**Minimum, not mean.** These are CPU-bound operations where every noise source — scheduling, thermal throttling, other processes — only adds time. The minimum of N runs is the closest estimate of the true cost. `timeit.repeat(5, number)` then `min()`.

**Iteration counts sized so one measurement exceeds ~50 ms**, keeping timer granularity irrelevant: 200,000 for sub-100 ns operations, 20,000 for microsecond ones, 100–500 for batch operations.

**Batch measurements are the ones that matter.** A per-row number is an interesting decomposition; a per-100-row-page number is what a user experiences. Both are reported, and the acceptance gates in `03`–`05` are stated in both.

**cProfile for attribution, never for timing.** Its overhead inflates absolute numbers by ~2×, but call *counts* are exact — which is how `02` found the 230,000 `isinstance` calls. Timing comes from `timeit`, attribution from cProfile, and the documents never mix them.

**Environment recorded with every result set**: OS, arch, CPython version, and whether the machine was idle. A number without its environment is not reproducible.

---

## 2. What gets measured

### 2.1 Component level (`profile_baseline.py`, exists)

| Group | Metrics |
|---|---|
| Hydration | `from_row` 4-col / 8-col; per-type `to_python`; descriptor vs raw dict write; deferred setcomp |
| Validation | `Sigil.validate`; `Contract.is_sealed`; construction; per-facet cast+seal; `get_field_value` |
| SQL | simple and complex builder |
| Batch | 100-row hydration, 100-payload validation |

### 2.2 Conversion floors (`/tmp` prototype → to be promoted)

The floor for each type — the cheapest possible Python producing an identical object. This is what determines whether a native conversion can win at all, and it is the measurement that refuted the per-field API in `02` §3. It belongs in the committed harness, not a scratch file.

**Action:** promote to `benchmarks/models/conversion_floors.py`.

### 2.3 Boundary cost

`noop()` and a two-string-argument call, measured against the *installed* `_core` module. Re-measured per platform, because the 43.3 ns figure is arm64-specific and the whole per-field-vs-batch decision hinges on it.

**Action:** `benchmarks/models/boundary.py`, or extend the existing `benchmarks/engine/call_overhead.py`.

### 2.4 End-to-end, through a real query

The component numbers omit driver time, and a native hydration engine that halves a cost representing 5% of a real query is not worth shipping. This measures the honest denominator.

```
sqlite in-memory, N rows, 8 columns
  ├─ query execution (driver)
  ├─ row_factory + Row construction
  ├─ hydration
  └─ total
```

Reported as a percentage breakdown, so "hydration is X% of a real read" is a measured statement rather than an assumption.

**Action:** `benchmarks/models/e2e_query.py`. **This is the most important missing benchmark** — without it, the whole project's ROI rests on component numbers that may be a small fraction of a real query.

---

## 3. Scaling

Costs must be checked for shape, not just magnitude. A per-row cost that is O(columns²) would be invisible at 8 columns.

| Axis | Points | Expectation |
|---|---|---|
| Rows per batch | 1, 10, 100, 1,000, 10,000 | linear; per-row cost flat after ~10 |
| Columns per row | 4, 8, 16, 32, 64 | linear in columns |
| Fields per payload | 4, 8, 16, 32 | linear |
| Distinct projections | 1, 10, 100 | plan cache bounded, build cost amortised |
| Nesting depth | 1, 2, 4 | Python path only — records the fallback cost |

The rows axis is also what validates the batch-amortisation claim in `02` §3: if the per-row cost does not flatten by ~10 rows, the boundary is not being amortised as designed.

---

## 4. Regression gates

Two mechanisms, different purposes:

**Committed baselines.** `baseline.json` (now), `post_fixes.json` (after `06`), `post_native.json` (after the engine). Each phase compares against the previous one and the deltas go in the results document. This is how `06`'s exit gate is evaluated.

**`tests/dataengine/test_perf_gates.py`.** Budgets at the measured value plus 25% tolerance, marked `slow`, run nightly. Catches a regression that lands between phases.

Plus the machine-independent ratio assertion, which holds on any hardware:

```python
def test_native_beats_python():
    assert time_native() < time_python()
```

An absolute budget tuned on an M-series laptop will fail spuriously on a shared CI runner; the ratio will not.

---

## 5. Correctness measurements that are not timing

Some acceptance criteria are numeric but not about speed. They belong in the benchmark harness because they are measured the same way.

| Metric | Method | Gate |
|---|---|---|
| Boundary crossings per batch | count `noop`-equivalent entries | exactly 1 |
| Allocations per hydrated row | `tracemalloc` delta | ≤ Python path |
| Plan cache size | `len(cache)` after a workload | ≤ distinct projections |
| Refcount growth | `gc.get_objects()` delta | < 100 per 100k rows |
| Plan build cost | one-off timing | amortised over ≥ 100 uses |

The last one matters: if compiling a plan costs 50 µs and a typical query returns 10 rows, the plan must be cached across queries or it is a net loss on first use. Measuring build cost is how that is verified rather than assumed.

---

## 6. Reporting

Each phase produces a results document with:

1. Before/after table, both per-unit and per-batch.
2. **Gates met and gates missed, stated plainly.** Phase 9 missed two of its gates; reporting that honestly — with the reason, which turned out to be a Python-side dataclass constructor rather than the native code — was more useful than the gates it met.
3. Rejected components with the measurement that rejected them.
4. Corrections to earlier projections.

The Phase 9 results document is the template: `docs/engine/09-results.md`.

---

## 7. Reproducing

```bash
# component baseline (exists)
python benchmarks/models/profile_baseline.py --json benchmarks/models/baseline.json

# to be added
python benchmarks/models/conversion_floors.py
python benchmarks/models/boundary.py
python benchmarks/models/e2e_query.py
python benchmarks/models/scaling.py
```

Run on an idle machine. The harness takes minimums, but a loaded machine still inflates them, and a benchmark run on a busy laptop has produced more bad architecture decisions than any other single cause.
