# Phase 10 — Results

**Status:** measured
**Environment:** macOS arm64 (Apple Silicon), CPython 3.11.15, nanobind 2.x, idle machine
**Method:** `timeit` best-of-5/7/9 (minimum), per `08-benchmark-strategy.md` §1
**Baselines:** `benchmarks/models/baseline.json` → `post_fixes.json` → `post_native.json`

Written to the template of `docs/engine/09-results.md`: gates met **and missed**,
components rejected with the measurement that rejected them, and corrections to
the projections the design was built on.

---

## 1. Headline

| Path | Before | After | Factor |
|---|---|---|---|
| **Real 100-row query, end-to-end** | 449.4 µs | **215.8 µs** | **2.08×** |
| Hydration within that query | 314.7 µs | **81.0 µs** | 3.89× |
| `from_row` equivalent, 9 columns | 2,696 ns | **742 ns** | 3.63× |
| `Sigil.validate` equivalent, 8 fields | 3,931 ns | **232 ns** | 16.9× |
| 100-payload validation | 358.2 µs | **11.8 µs** | 30.4× |
| `get_field_value` (Python-only fix) | 168.7 ns | **61.7 ns** | 2.73× |

The end-to-end figure is the one that matters, and it is **measured, not
arithmetic** — `benchmarks/models/e2e_query.py` runs a real async sqlite query
through the executor and times both hydration paths over the same rows.

---

## 2. Gates

### Met

| Gate | Target | Measured | |
|---|---|---|---|
| M1 hydration share of a real query | ≥ 25% | **70.0%** | PASS |
| M2 `uv pip install -e .`, both extensions load | — | `DATAENGINE_NATIVE is True` | PASS |
| M2 suite with extension present / disabled / deleted | all pass | 7,941 / 7,701 / 7,701 | PASS |
| M3 conversion parity, exhaustive | 100% | 113 tests | PASS |
| M3 C++ tests under ASAN+UBSAN | zero reports | 26 tests, clean | PASS |
| M4 `Sigil.validate` equivalent | ≤ 1,500 ns | **232 ns** | PASS |
| M4 100 payloads | ≤ 120 µs | **11.8 µs** | PASS |
| M4 error messages byte-identical | required | by construction (§4.1) | PASS |
| M5 `from_row` equivalent | ≤ 1,200 ns | **742 ns** | PASS |
| M5 100-row page | ≤ 120 µs | **74.3 µs** | PASS |
| M5 `save()` round-trip identical | required | `_original_values` byte-identical | PASS |
| Existing tests unmodified | 7,850 | 7,850 (+240 new) | PASS |
| Fallback parity `AQUILIA_DATAENGINE=0` | 100% | 7,701 pass, 248 skip | PASS |

### Missed

**M3 — native UUID parse ≤ 50 ns. Measured 85.2 ns.**

Missed, and the reason is structural rather than an implementation shortfall.
Decomposing the 85 ns:

| Component | Cost |
|---|---|
| `PyLong_FromString` for the 128-bit int | ~48 ns |
| `tp_alloc` for the UUID object | ~30 ns |
| hex validation + slot writes | ~7 ns |

**~78 ns of the budget is spent producing objects the Python path must also
produce.** The 50 ns gate was set without accounting for that floor, so no
parsing implementation could have met it. What native code actually removes is
the interpretation around the allocation — the three `str.replace` calls plus
`strip`/`count`/`len` in `uuid.UUID.__init__` — which is worth **4.47×**
(380.5 → 85.2 ns).

The `09` §6.3 stop condition was "native UUID under ~3×". At 4.47× it is not
tripped, so the milestone proceeded. This is exactly the outcome M3 existed to
discover before the plan machinery was built on top of it.

**M0 — `from_row` ≤ 2,650 ns. Measured 2,904 ns.**

The `from_row` and 100-row-page gates in `06` §5 were missed, while the
validation gates passed comfortably. Cause: **the benchmark fixture never
exercises two of the five fixes.**

- `Wide` has an auto-injected `id` PK that `ROW_FULL` omits, so every benchmark
  row has one deferred field and F2's fast path never fires. Measured directly:
  2,910 ns with a deferred field vs **2,622 ns** on a row that covers every
  field — F2 works, the fixture just never reaches it.
- F3 lives in `sqlite/_rows.py` and the harness hydrates plain dicts, never
  going through a cursor. Measured head-to-head instead: **609.6 → 431.6 ns per
  row**, 17.8 µs per 100-row page.

So the M0 gate as written measured a shape that two of its own fixes do not
apply to. The fixes are real; the gate was mis-specified.

---

## 3. What each phase actually delivered

### M0 — Python fixes (no C++)

| Fix | Target | Measured |
|---|---|---|
| F1 | `get_field_value` ABC `isinstance` + eager alloc | 168.7 → **60.0 ns** (2.8×) |
| F2 | unconditional deferred setcomp | 2,910 → **2,622 ns** when live |
| F3 | `row_factory` key-tuple rebuild | 609.6 → **431.6 ns/row** (17.8 µs/page) |
| F4 | `is_sealed` known-field set | 83 → 3 ns, reject-mode only |
| F5 | per-row FK `isinstance` | 16.2 → **7.5 ns** per column |

F1 alone moved `Sigil.validate` from 5,094 → 4,094 ns (**19.6%**) with no C++.

One correction to `06` §F3: the document's *preferred* mitigation — attaching
the key cache to the cursor as `cursor._aq_keys` — **is not possible**.
`sqlite3.Cursor` is a C type with no `__dict__`, so the attribute assignment
raises. Option 2 was used instead: the cache value holds a strong reference to
the `description` tuple, which is what makes the `id()` key sound (the address
cannot be recycled while the entry lives), plus an identity re-check on hit.

One correction to `06` §F5: the document assumed `isinstance` was cheaper than a
set membership test and recommended the `frozenset` only for blast radius.
Measured, the `frozenset` is also *faster* — 7.5 ns vs 16.2 ns — so it wins on
both counts.

### M1 — the benchmarks that decide the project

`e2e_query.py` supplied the denominator the whole ROI argument was missing:

| Rows | driver | row build | hydration | hydration share |
|---|---|---|---|---|
| 1 | 27.9 µs | 2.0 µs | 2.9 µs | **8.8%** |
| 10 | 32.2 µs | 8.4 µs | 28.8 µs | 41.5% |
| 100 | 86.9 µs | 47.9 µs | 314.7 µs | **70.0%** |
| 1,000 | 590.8 µs | 536.3 µs | 3,349 µs | 74.8% |

**The 1-row number is worth recording as a scope limit:** at a single row,
hydration is only 8.8% and executor overhead dominates, so this engine does
nearly nothing for single-row lookups. Its value is concentrated in list and
pagination endpoints.

`boundary.py` measured **55.5 ns** for a two-string-argument call against the
43.3 ns `02` §3 recorded. The higher figure *strengthens* the conclusion: even
more conversions fall below one crossing, so a per-field native API is refuted
more decisively, and the batch design is more clearly correct.

`conversion_floors.py` reproduced `02` §3 exactly against that measured
boundary — only `uuid` (378.7 ns) and `json` (390.6 ns) clear it.

`scaling.py` found all three axes linear: rows flat at ~2.9 µs/row from 1 to
10,000, columns and fields flat per unit. No superlinear cost was hiding below
the 8-column measurements the rest of the harness uses.

### M4 — validation

`Sigil.validate` 3,931 → **232 ns** (16.9×) on an eligible 8-field contract;
100 payloads 358.2 → **11.8 µs** (30.4×).

### M5 — hydration

`from_row` 2,696 → **742 ns** (3.63×); 100-row page 276.9 → **74.3 µs** (3.73×).

---

## 4. Corrections to the design documents

Three specification rules could not be followed as written. Each is recorded
with what replaced it.

### 4.1 `05` §3.7 — caching resolved error messages is unsound

The spec proposed caching resolved message strings in the plan at compile time,
formatting parameterised ones natively.

`contract_message()` resolves through a **request-scoped i18n ContextVar**
(`contracts/messages.py`), so the same key yields different text per request
locale. Compile-time caching would pin one locale's wording into every
subsequent request — a correctness bug, and a subtle one.

**Replaced with:** any failure aborts the payload back to `Sigil.validate`.
Errors are then produced by the identical Python code that produces them today,
so they are byte-identical *and* correctly localised by construction rather than
by careful reimplementation. The cost falls only on the failure path, which is
not the path being optimised. This is strictly better than the spec's design,
not merely a workaround.

### 4.2 `04` §2.3.3 — the `to_python` eligibility rule inverts its own purpose

The spec requires that no field override `to_python`, checked by identity
against the base implementation.

Applied literally, that rejects **eight of the built-in field types** — Boolean,
Date, DateTime, Time, Decimal, UUID, JSON, Binary all override it — which is
precisely the set the `TypeCode` table exists to serve. The engine would have
been permanently idle while every parity test passed, which is the exact failure
mode `07` §5 warns about.

**Replaced with:** exact-type matching in `_field_type_code` (`type(field) is X`),
so a *user* subclass is unrecognised and its plan rejected, while each built-in's
`to_python` is reproduced exactly.

Reproducing them exactly required a **separate conversion path** for hydration.
The ORM's `to_python` is not the contracts' facet `cast`, and three differences
would have been silent data corruption if merged:

- Date/DateTime/Time/Decimal/UUID map a blank or whitespace-only string to
  `None` — a blank text column and a real NULL both mean "no value"
- `DecimalField` is `Decimal(str(value))`; the `str()` is load-bearing for float
  input, where `Decimal(float)` would carry binary representation error
- `JSONField` returns an unparseable string **as-is** rather than raising

`convert_hydrate()` is therefore separate from `convert()`, and only ASCII
strings are decided for the blank check — a non-ASCII string defers, because
`str.strip()` follows Unicode rules the fast path does not model.

### 4.3 `06` §F3 — the preferred cursor-attached cache is impossible

`sqlite3.Cursor` is a C type with no `__dict__`; `cursor._aq_keys = ...` raises
`AttributeError`. The document's option 2 was used instead. See §3.

---

## 5. Rejected and deferred, with the measurement

| Component | Verdict | Evidence |
|---|---|---|
| Per-field native conversion API | **rejected** | boundary 55.5 ns exceeds 6 of 8 conversion floors (`conversion_floors.py`) |
| Native ISO-8601 parsing | **rejected** | `fromisoformat` is C at 44–50 ns; reimplementation risks tz/fractional divergence for ~zero gain |
| `_PyLong_FromByteArray` for UUID | **rejected** | declared in `cpython/longobject.h` but not exported by this build; `PyLong_FromString` over the normalised hex is portable |
| `PyObject_CallOneArg` | **rejected** | same — not exported; `PyObject_CallFunctionObjArgs` used |
| `DecimalFacet` in validation v1 | **deferred** | `seal` enforces `max_digits`/`decimal_places`, needing exponent-aware inspection for a conversion already at parity with one crossing |
| Deferred/partial row hydration | **deferred** | needs the guard-class `__class__` swap; an absent column must never become `None` |
| `select_related` aliased columns | **deferred** | column splitting lives in `query.py`; getting it subtly wrong is not worth the speed |
| `strict` / `partial` validation modes | **deferred** | `strict` skips cast entirely — different semantics, not a flag |
| Native SQL builder | **rejected** | 0.45% of a page-serving request (`02` B12) |
| M7 adapter row protocol | **deferred** | would remove B1+B2 outright; needs its own compatibility analysis across four backends |

---

## 6. Bugs found during implementation

Recorded because each says something about where the risk actually was.

1. **Double-DECREF in `FieldPlan::execute`** — a bounds-check failure after a
   successful cast released `value` twice, segfaulting. Found by the *existing*
   mail-config tests, not by the new dataengine tests. Fixed with a single
   release path.

2. **`default=None` collapsed to `nullptr`** — `default=None` is a legitimate
   default, distinct from having no default; the binding mapped it to null, so
   `HAS_DEFAULT` pointed at NULL and `PyDict_SetItem` segfaulted on the first
   contract that used it. Fixed, with an `assert` now pinning the invariant.

3. **Out-of-bounds read in a C++ test** — `"...\0000"` is `\000` followed by
   `'0'` (34 bytes), declared as 36. **ASAN caught it**, which is the argument
   for the sanitizer gate existing at all.

The pattern worth noting: **both production segfaults were found by the
pre-existing suite rather than by the purpose-written parity tests.** The
7,850-test regression gate did more for safety here than any new test file.

---

## 7. Honest assessment

`09` §6 asked what would make this project not worth doing. Answering it with
the measurements now in hand:

**1. "M1 shows hydration < 25% of a real query."** It showed 70.0%. Not tripped
— this was the strongest possible outcome for the project.

**2. "M0 alone reaches within ~30% of the native targets."** It did not. M0
delivered 19.6% on validation and ~10% on hydration; native delivered a further
16.9× and 3.6×. The second extension earned its place, which is a *different*
outcome from the Phase 9 precedent that `09` §6 warned would likely repeat.

**3. "M3 shows native UUID under ~3×."** It showed 4.47×. Not tripped, though
the 50 ns gate itself was unreachable — see §2.

**Where the projections were right:** `02` §2's central claim — that the cost is
interpretation, not conversion — held everywhere. Validation, at 90% framework
overhead, delivered 16.9×; hydration, at 71%, delivered 3.6×. The ordering and
the ratio between them both match the decomposition.

**Where they were optimistic:** `03` §13 projected ~3× hydration and ~4×
validation. Hydration landed at 3.6× (better), validation at 16.9× (far better)
— but only for *eligible* shapes. The projections did not account for how much
real-world traffic the conservative eligibility rules exclude: any contract with
a `Decimal`, a regex pattern, or a validator falls back entirely, as does any
`only()`/`defer()` query. **The component speedups are real; the fleet-wide
average will be lower**, and by how much depends on a given codebase's field
types. That is the honest caveat on the headline number.

**Cost of the fallback path:** 30.9 ns per call for the plan-cache lookup —
0.46% of an ineligible `is_sealed`, within run-to-run noise.

---

## 8. Reproducing

```bash
python benchmarks/models/profile_baseline.py --json benchmarks/models/post_native.json
python benchmarks/models/e2e_query.py --all-sizes      # the end-to-end number
python benchmarks/models/boundary.py                    # per-platform boundary
python benchmarks/models/conversion_floors.py
python benchmarks/models/scaling.py

pytest tests/dataengine/ -q                             # 240 engine tests
AQUILIA_DATAENGINE=0 pytest tests/ -q                   # the deletability gate

cmake -S aquilia/_dataengine -B build-asan-data \
  -DAQUILIA_ENGINE_TESTS=ON -DCMAKE_BUILD_TYPE=Debug \
  -DAQUILIA_SANITIZE=address,undefined
ctest --test-dir build-asan-data --output-on-failure
```

Run on an idle machine. The harness takes minimums, but a loaded machine still
inflates them.
