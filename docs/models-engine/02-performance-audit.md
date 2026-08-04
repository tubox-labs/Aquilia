# Phase 2 — Performance Audit: models / db / contracts

**Status:** measured
**Harness:** `benchmarks/models/profile_baseline.py` → `benchmarks/models/baseline.json`
**Environment:** macOS arm64 (Apple Silicon), CPython 3.11.15, nanobind 2.13
**Method:** `timeit` best-of-5 (minimum, not mean — these are CPU-bound, so noise only adds time), plus cProfile for call-count attribution.

Every bottleneck below carries: root cause, current implementation with file:line, measured impact, proposed remedy, complexity, expected gain, and risk. Nothing here is estimated; where a number is a projection it is labelled as one.

---

## 1. Headline measurements

| Path | Cost | Batch cost |
|---|---|---|
| `Model.from_row`, 4 cheap columns | 1,106 ns | — |
| `Model.from_row`, 8 mixed columns | **3,002 ns** | 311 µs / 100 rows |
| `Sigil.validate`, 8 fields | **5,034 ns** | 501 µs / 100 payloads |
| `Contract(...).is_sealed()`, 8 fields | **7,797 ns** | — |
| SQL build, simple SELECT | 1,392 ns | — |
| SQL build, JOIN + 5 predicates | 2,378 ns | — |

For scale: a request serving a 100-row page pays **311 µs** in hydration alone. The entire post-Phase-9 request pipeline is **7.14 µs**. Hydration of one page is **43× the cost of the whole framework overhead of the request that carries it.** This is where the framework's real time goes.

---

## 2. The decomposition that determines the strategy

Summing the *irreducible* CPython conversion cost — what any implementation, native or not, must pay to produce identical Python objects:

| Path | Measured total | Irreducible conversion | **Framework overhead** |
|---|---|---|---|
| `from_row`, 8 columns | 3,002 ns | 859 ns | **2,143 ns — 71%** |
| `Sigil.validate`, 8 fields | 5,034 ns | 499 ns | **4,535 ns — 90%** |

Conversion floors measured individually:

| Conversion | Floor | Implementation |
|---|---|---|
| `str` passthrough | 3.2 ns | — |
| `date.fromisoformat` | 18.7 ns | C |
| `float(str)` | 21.4 ns | C |
| `datetime.fromisoformat` | 24.7 ns | C |
| `int(str)` | 27.2 ns | C |
| `Decimal(str)` | 44.7 ns | C (`_decimal`) |
| `uuid.UUID(str)` | 354.4 ns | **pure Python** |
| `json.loads` (small) | 378.9 ns | C scanner + Python wrapper |

**The cost is not in converting values. It is in the per-field Python interpretation around each conversion.** A design that targets "make the type conversions faster in C++" would be optimising 10–29% of the problem while paying a boundary cost on every field.

---

## 3. The boundary constraint

Measured against the Phase 9 native module already in the tree:

| Crossing | Cost |
|---|---|
| `noop()` — bare call | 8.1 ns |
| call with 2 string arguments | **43.3 ns** |

Per-conversion verdict for a **per-field** native API:

| Conversion | Floor | vs 43 ns | Verdict |
|---|---|---|---|
| `str` | 3.2 ns | 13× cheaper than the call | **LOSS** |
| `date` | 18.7 ns | 2.3× cheaper | **LOSS** |
| `float` | 21.4 ns | 2× cheaper | **LOSS** |
| `datetime` | 24.7 ns | 1.8× cheaper | **LOSS** |
| `int` | 27.2 ns | 1.6× cheaper | **LOSS** |
| `Decimal` | 44.7 ns | parity | marginal |
| `uuid` | 354.4 ns | 8× dearer | **WIN** |
| `json` | 378.9 ns | 8.8× dearer | **WIN** |

**A per-field native API is refuted before it is designed.** Six of eight conversions cost less than one boundary crossing. This is the same class of error that cancelled Phases 9E and 9G after they had been specified: the native call is not free, and most of CPython's scalar parsing is already C.

**Why UUID is the exception:** `uuid.UUID.__init__` is pure Python (`uuid.py:139`) — cProfile over 50,000 parses shows three `str.replace` calls plus `strip`, `count`, and `len` per parse. It is slow because it is interpreted, not because the work is hard. A C++ hex parse is a genuine ~10× win.

### Batch amortisation — why the API shape is the whole design

One crossing spread over a result set:

| Batch | Values | Boundary share per value |
|---|---|---|
| 1 row × 8 fields | 8 | 4.97 ns |
| 10 rows × 8 fields | 80 | 0.50 ns |
| 100 rows × 8 fields | 800 | **0.05 ns** |
| 1,000 rows × 8 fields | 8,000 | 0.005 ns |

At page-sized batches the boundary vanishes. Combined with §2 — that 71–90% of cost is per-field interpretation — the conclusion is forced: **cross the boundary once per result set, and move the interpretation loop, not the conversions, into native code.**

---

## 4. Bottleneck register — hydration

### B1 — `row_factory` rebuilds the key tuple for every row

- **Root cause:** `cursor.description` is constant for a result set; the factory recomputes from it per row.
- **Current:** `sqlite/_rows.py:130` — `keys = tuple(d[0] for d in cursor.description)`
- **Measured:** **196.6 ns/row** to rebuild vs **3.0 ns** to reuse a cached tuple.
- **Impact:** 19.7 µs per 100-row page, paid before hydration even begins.
- **Remedy:** cache the key tuple per cursor. Pure Python.
- **Complexity:** low. **Gain: ~193 ns/row (~98% of this cost).** **Risk:** low — needs care that the cache keys on the cursor, not the connection, since one connection serves many statements.

### B2 — `Row` construction costs 2× a plain dict

- **Current:** `sqlite/_rows.py:19` — `class Row(dict)` with custom `__init__`.
- **Measured:** `Row(keys, values)` **358.0 ns** vs `dict(zip(keys, values))` **184.5 ns**.
- **Impact:** 17.4 µs per 100-row page.
- **Remedy:** needs investigation before action — `Row` provides index *and* key access, which is public API. Possibly a `__slots__`-free fast path, possibly native.
- **Complexity:** medium. **Gain: up to 173 ns/row.** **Risk:** medium — `Row` semantics are user-visible.

### B3 — Descriptor protocol on every field write

- **Root cause:** `Field` is a data descriptor so class-level access returns the `Field` (needed for query building); the cost is paid on every instance write.
- **Current:** `fields_module.py:253` — `Field.__set__` → `instance.__dict__[attr] = value`
- **Measured:** `setattr` through descriptor **152.6 ns** vs raw dict write **38.8 ns** — **114 ns overhead per field**.
- **Impact:** 8 fields × 114 ns = **912 ns/row**, 30% of an 8-column `from_row`. 91 µs per 100-row page.
- **Remedy:** native hydration writes the instance `__dict__` directly, bypassing the descriptor — which is exactly what the descriptor does anyway. **The descriptor must stay** for class-level access.
- **Complexity:** medium (needs the batch engine). **Gain: ~912 ns/row.** **Risk:** medium — must not bypass a *custom* `__set__` on a user Field subclass; eligibility check required.

### B4 — Unconditional deferred-fields set comprehension

- **Root cause:** the setcomp runs on every row to detect `only()`/`defer()` exclusions, even when every column is present (the common case).
- **Current:** `base.py:2088` — `deferred = {attr for attr, _f in cls._non_m2m_fields if attr not in seen}`
- **Measured:** **152.4 ns/row** for 8 fields.
- **Impact:** 15.2 µs per 100-row page; 5% of `from_row`.
- **Remedy:** compare counts first — `len(seen) == len(cls._non_m2m_fields)` skips the comprehension entirely. Pure Python, ~2 lines.
- **Complexity:** trivial. **Gain: ~145 ns/row when nothing is deferred.** **Risk:** low.

### B5 — Dirty-tracking snapshot duplicates every value

- **Current:** `base.py:2075` — `original[attr_name] = converted` per field, plus the dict allocation.
- **Measured:** included in the 3,002 ns; a dict write is ~39 ns × 8 = ~312 ns/row plus allocation.
- **Impact:** ~31 µs per 100-row page.
- **Remedy:** **none proposed.** `save()` diffs against this to build minimal `UPDATE` statements (`base.py:1675`). Dropping it would either break minimal updates or force a full-column UPDATE. A native engine can build the snapshot more cheaply as a sibling dict during the same pass, but the semantics must not change.
- **Complexity:** medium. **Gain: modest.** **Risk:** high if semantics drift — recorded as a constraint, not an optimisation.

### B6 — `isinstance(field, ForeignKey)` per field per row

- **Current:** `base.py:2065`, inside the column loop.
- **Measured:** cProfile shows **75,000 `isinstance` calls** for 5,000 hydrations — 15 per row.
- **Remedy:** the FK-ness of a column is a static property of the model. It belongs in the compiled plan (a per-column flag), not a per-row type test.
- **Complexity:** low (Python) or free (native plan). **Gain: ~8 × 8 ns = 64 ns/row.** **Risk:** low.

---

## 5. Bottleneck register — validation

### B7 — ABC `isinstance` on the payload, once per field ★ largest single win

- **Root cause:** `Mapping` is an abstract base class; `isinstance` against it dispatches through `_abc_instancecheck` with a subclass-cache lookup, instead of the C-level type check a concrete class gets.
- **Current:** `sigil.py:823` — `isinstance(data, (dict, Mapping)) and not (…isinstance(data, _MULTIDICT_CLS))`
- **Measured:**

  | Test | Cost |
  |---|---|
  | `isinstance(d, dict)` | 7.9 ns |
  | `isinstance(d, Mapping)` (ABC) | **54.9 ns** |
  | `isinstance(d, (dict, Mapping))` | 15.7 ns |
  | `type(d) is dict` | 7.6 ns |

- **Impact:** cProfile over 5,000 validations: **230,000 `isinstance` calls**, of which **40,000 route through `_abc_instancecheck`**. This is the single highest call count in the profile.
- **Remedy:** hoist a `type(data) is dict` fast path before the ABC test. The tuple form short-circuits on `dict` already, so the win is in avoiding the *tuple* and the MultiDict follow-up check on the common path.
- **Complexity:** low. Pure Python. **Gain: measured 34.5 ns/field addressable** (see B8, same function). **Risk:** low — must preserve exact behaviour for `MultiDict`/`FormData`, which are not plain dicts.

### B8 — `get_field_value` allocates a list and an f-string per field

- **Root cause:** the `field[]` alternate key is only meaningful for `MultiDict`/`FormData` payloads, but is built unconditionally before the plain-dict path that never uses it.
- **Current:** `sigil.py:821` — `keys_to_try = [fname, f"{fname}[]"]`
- **Measured:** **24.5 ns/field** for the list + f-string; the whole function is **170.7 ns/field**.
- **Combined B7+B8 arithmetic:**

  | Path | Cost |
  |---|---|
  | current (ABC test + alloc + `in`/index) | 50.1 ns |
  | achievable (`type is dict` + `dict.get`) | 15.6 ns |
  | **addressable per field** | **34.5 ns** |

- **Impact:** 8 fields × 34.5 ns = **276 ns/payload**; 27.6 µs per 100 payloads.
- **Remedy:** build `keys_to_try` lazily, only after the plain-dict path has been ruled out.
- **Complexity:** low. **Gain: ~276 ns/payload.** **Risk:** low.

### B9 — Two Python calls per field for cast + seal

- **Current:** `sigil.py:395-396` — `facet.cast(raw)` then `facet.seal(cast_value)`.
- **Measured** (cast+seal pairs):

  | Facet | Cost | Conversion floor | Overhead |
  |---|---|---|---|
  | text | 202.4 ns | 3.2 ns | 199 ns |
  | bool | 130.3 ns | ~5 ns | 125 ns |
  | date | 139.9 ns | 18.7 ns | 121 ns |
  | datetime | 178.8 ns | 24.7 ns | 154 ns |
  | int | 221.2 ns | 27.2 ns | 194 ns |
  | float | 239.6 ns | 21.4 ns | 218 ns |
  | decimal | 230.9 ns | 44.7 ns | 186 ns |
  | uuid | 466.8 ns | 354.4 ns | 112 ns |

- **Impact:** **the overhead column is 112–218 ns per field and is nearly constant across types** — confirming it is dispatch, not work. ~1,300 ns of the 5,034 ns validation.
- **Remedy:** native batch validation executes a compiled per-field plan; cast+seal for the eight built-in scalar types becomes a switch on a type code with no Python call.
- **Complexity:** high. **Gain: projected ~1,000 ns/payload** for all-builtin schemas. **Risk:** medium — any custom facet, pipeline, or validator must fall back.

### B10 — `Sigil.validate` per-field branch chain

- **Root cause:** for each field the loop re-evaluates static properties: `isinstance(facet, (Computed, Constant))`, `isinstance(facet, Inject)`, `facet.read_only`, `spec.is_nested_contract`, `facet.default is not UNSET`, `facet.required`, `facet.allow_null`.
- **Current:** `sigil.py:255-300`.
- **Measured:** 46 `isinstance` calls per 8-field validation.
- **Remedy:** every one of these is fixed at class-build time. They belong as flags in `FieldSpec` (or a native plan), resolved once. `FieldSpec` already has `__slots__` and `is_nested_contract` — the pattern exists, it is just incompletely applied.
- **Complexity:** medium in Python, natural in a native plan. **Gain: projected 300–500 ns/payload.** **Risk:** low — the properties genuinely are static.

### B11 — `Contract.is_sealed` overhead above `Sigil.validate`

- **Measured:** `is_sealed` 7,797 ns vs `Sigil.validate` 5,034 ns → **2,763 ns of Contract-level overhead**, plus 204 ns construction.
- **Root cause:** async-ward guard, `adapt_input`, `is_mapping_like`, unknown-field set construction, `DataObject` wrapping, ward phase dispatch, validate hook, freeze.
- **Remedy:** the unknown-field check rebuilds `set(self._bound_facets.keys())` per call (`core.py:1349`) — that set is static per class and should be cached on it.
- **Complexity:** low for the set; the rest is structural. **Gain: projected 200–400 ns/payload** for the cached set alone. **Risk:** low.

---

## 6. Bottleneck register — SQL generation

### B12 — SQL string assembly per query

- **Measured:** simple SELECT **1,392 ns**; JOIN + 5 predicates **2,378 ns**.
- **Assessment:** **not a priority.** One query yields N rows; at 100 rows the build is 1.4 µs against 311 µs of hydration — **0.45%**. Native SQL assembly would optimise a rounding error.
- **Remedy:** none proposed. Recorded so that a future proposal to "move the query builder to C++" can be answered with the measurement.

---

## 7. Bottleneck ranking by addressable cost

Per 100-row page (hydration) and per 100 payloads (validation), ordered by what is actually recoverable:

| # | Bottleneck | Addressable | Fix type |
|---|---|---|---|
| B3 | Descriptor writes | 91 µs/page | native batch |
| B9+B10 | Facet dispatch + branch chain | ~130 µs/100 payloads | native batch |
| B1 | `row_factory` key rebuild | 19.3 µs/page | **Python** |
| B2 | `Row` construction | 17.3 µs/page | investigate |
| B4 | Deferred setcomp | 14.5 µs/page | **Python** |
| B7+B8 | `get_field_value` | 27.6 µs/100 payloads | **Python** |
| B11 | Contract-level set rebuild | ~30 µs/100 payloads | **Python** |
| B6 | Per-row FK `isinstance` | 6.4 µs/page | **Python** |
| B5 | Dirty snapshot | — | constraint, do not change |
| B12 | SQL build | 0.45% | **do not touch** |

**The Python-only fixes (B1, B4, B6, B7, B8, B11) total roughly 40 µs/page and 58 µs/100 payloads with no C++ at all.** They must land first and be re-baselined — they change the profile that the native engine is designed against, exactly as the Phase 9A fixes did before the controller engine work.

---

## 8. What this audit refutes

Three plausible designs are ruled out by measurement, recorded so they are not re-proposed:

1. **"Rewrite the type converters in C++."** Six of eight scalar conversions are already C and cost less than a single boundary crossing (§3). Only UUID and JSON parsing win per-call, and only because `uuid.UUID.__init__` is interpreted.

2. **"Rewrite the query builder in C++."** It is 0.45% of a page-serving request (B12).

3. **"Rewrite the ORM in C++."** 37,000 of the ~50,000 lines are migrations, codegen, introspection, registry, and CLI — none on a per-request path. The addressable surface is `from_row`, `Sigil.validate`, and the row factory.

---

## 9. What this audit supports

A **batch-boundary engine** that:

- crosses once per result set / payload list, making the boundary free (§3);
- replays a **plan compiled once per (model, row-shape)** or per Sigil, since row shape is invariant within a result set (`01-architecture-audit.md` §3.2);
- eliminates per-field interpretation — the 71–90% (§2) — rather than the conversions;
- delegates every conversion CPython already does well back to CPython, and natively implements only UUID (and possibly JSON), where the floor measurement shows a real win;
- falls back wholesale to Python whenever a custom field, custom facet, pipeline, validator, ward, or nested contract appears.

Projected ceiling, stated explicitly as a projection: removing the measured framework overhead (2,143 ns/row and 4,535 ns/payload) while retaining the conversion floors would give **~1,000 ns/row** (from 3,002) and **~1,200 ns/payload** (from 5,034). That is **~3× on hydration and ~4× on validation** — but it is arithmetic on measured components, not a benchmark, and `09-implementation-plan.md` gates each milestone on measurement rather than on this figure.

---

## 10. Reproducing

```bash
python benchmarks/models/profile_baseline.py --json benchmarks/models/baseline.json
```

Prints all three sections plus cProfile attribution for both hot paths. Run on an idle machine; the harness takes minimums, but a loaded machine still inflates them.
