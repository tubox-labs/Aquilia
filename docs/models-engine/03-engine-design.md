# Phase 3 — Native Engine Design: the batch-boundary architecture

**Status:** design
**Depends on:** `01-architecture-audit.md`, `02-performance-audit.md`
**Implements:** `aquilia/_dataengine/` — a second C++20 extension, sibling to the existing `aquilia/_core/`

---

## 1. Mandate, restated from measurement

Phase 2 established two facts that together determine everything below:

1. **71% of hydration and 90% of validation cost is per-field Python interpretation**, not value conversion.
2. **A per-field native API cannot win** — six of eight scalar conversions cost less than one 43 ns boundary crossing, because CPython's `fromisoformat`/`int`/`float` are already C.

The mandate is therefore *not* "make conversions fast in C++". It is:

> **Move the interpretation loop into native code, cross the boundary once per batch, and hand every conversion CPython already does well straight back to CPython.**

This inverts the naive design. The engine's value is in *not executing Python bytecode per field*, while still calling `PyFloat_FromString` and friends for the actual values.

---

## 2. The organising principle: plan once, replay per row

Two invariants make this possible, both established in the audit:

| Invariant | Source | Consequence |
|---|---|---|
| Row shape is constant within a result set | `01` §3.2 — one query, one `cursor.description` | The column→field mapping can be resolved **once per query**, not once per row |
| Sigil field set is fixed at class build | `01` §4.1 — `cls._sigil` is immutable | The per-field branch chain can be resolved **once per class**, not once per payload |

So the engine is a **compiler plus an interpreter of compiled plans**:

```
   build time (once)                    hot path (per batch)
   ─────────────────                    ────────────────────
   model class + row keys  ──compile──▶  RowPlan  ──execute──▶  list[Model]
   Sigil                   ──compile──▶  FieldPlan ──execute──▶  (errors, validated)
```

A plan is a flat array of per-column instructions. Executing it is a `switch` on a `uint8` opcode inside a tight loop — no attribute lookups, no `isinstance`, no method dispatch, no temporary allocation.

---

## 3. Why a separate extension from `aquilia/_core`

`_core` is the request-path engine: router and request context, loaded at import, exercised on every request. This engine is data-path: hydration and validation, exercised only when an app touches the ORM or contracts.

Keeping them separate means:

- an app using neither ORM nor contracts pays no load cost for this code;
- the two have independent build gates and can be disabled independently (`AQUILIA_ENGINE=0` vs `AQUILIA_DATAENGINE=0`);
- `_core`'s router/context correctness is not coupled to changes here.

They share the same fail-soft loader pattern and the same rule: **zero `aquilia.*` imports**, so the native module is a dependency of the framework, never a dependent (`01` §10).

```
aquilia/
  _dataengine/
    CMakeLists.txt
    src/
      typecode.hpp          ← the type enum shared by both plans
      convert.hpp/.cpp      ← scalar conversions; delegates to CPython where CPython wins
      uuid_parse.hpp/.cpp   ← the one conversion worth writing natively
      rowplan.hpp/.cpp      ← compiled hydration plan + executor
      fieldplan.hpp/.cpp    ← compiled validation plan + executor
      module.cpp            ← nanobind glue; the only Python-aware TU
    tests/
      test_convert.cpp
      test_uuid_parse.cpp
      test_rowplan.cpp
      test_fieldplan.cpp
  _dataengine.pyi
  _dataengine_loader.py     ← fail-soft; the only importer of _dataengine
```

---

## 4. Type codes — the dispatch primitive

One enum drives both plans. A `uint8` switch replaces every `isinstance` chain in the hot loops.

```cpp
enum class TypeCode : std::uint8_t {
    Passthrough = 0,  // value used as-is (str→str, int→int)
    Str         = 1,
    Int         = 2,
    Float       = 3,
    Bool        = 4,
    Date        = 5,
    DateTime    = 6,
    Time        = 7,
    Decimal     = 8,
    Uuid        = 9,   // native parse — the measured win
    Json        = 10,  // native scan, Python object build
    Bytes       = 11,
    // Everything else — custom field/facet, pipeline, validator, nested
    // contract, computed, injected — is NOT a type code. It marks the whole
    // plan ineligible and the batch runs in Python.
    Unsupported = 255,
};
```

**Eligibility is decided per plan, not per field.** If any column or field maps to `Unsupported`, the entire plan is rejected at compile time and the caller keeps the pure-Python path. This is the same conservative rule the Phase 9 router used per HTTP method, and it exists for the same reason: a partially-native path is a second implementation that can silently diverge. One code path per batch, chosen once.

---

## 5. Conversion policy — measured, not assumed

`02` §3 measured each conversion against the 43 ns boundary. The policy follows the measurement exactly:

| TypeCode | Implementation | Rationale |
|---|---|---|
| `Passthrough` | return borrowed ref, one incref | 3.2 ns floor; nothing to beat |
| `Str` | `PyUnicode` passthrough or decode | already minimal |
| `Int` | `PyLong_FromString` | CPython's own parser, 27 ns |
| `Float` | `PyFloat_FromString` | 21 ns, already C |
| `Bool` | inline compare against a small token set | trivial |
| `Date` | `PyObject_CallMethod(date, "fromisoformat")` | 18.7 ns, already C — **calling back into CPython is correct here** |
| `DateTime` | ditto | 24.7 ns, already C |
| `Decimal` | `PyObject_CallOneArg(Decimal, str)` | 44.7 ns, `_decimal` is C |
| `Uuid` | **native hex parse → `PyObject` via `UUID(int=…)` or direct struct fill** | 354 ns floor because `uuid.UUID.__init__` is *pure Python* (`uuid.py:139`, three `str.replace` per parse) |
| `Json` | native scan → Python containers | 378.9 ns floor |
| `Bytes` | `PyBytes_FromStringAndSize` | trivial |

**The engine deliberately calls back into CPython for date/datetime/decimal.** That contradicts the usual "no native→Python calls" rule (which `_core` enforces strictly), and it is the right trade here: `datetime.fromisoformat` is 24.7 ns of C, and reimplementing ISO-8601 parsing in C++ would risk correctness divergence on timezones, fractional seconds, and the `Z` suffix for a gain that measurement says is near zero.

**The re-entrancy this admits is bounded and must stay bounded:** the only Python called is a small set of *built-in C constructors* captured once at module init. No user code, no `__init__` overrides, no descriptors. `06`'s eligibility rules guarantee a plan containing user code never compiles.

---

## 6. Hydration engine — `RowPlan`

### 6.1 Structure

```cpp
struct ColumnOp {
    std::uint32_t key_index;    // position in the row's key tuple
    std::uint32_t attr_index;   // position in the plan's attr-name table
    TypeCode      code;
    std::uint8_t  flags;        // FK_WRAP | NULLABLE
};

class RowPlan {
    std::vector<ColumnOp> ops_;      // one per mapped column, in row order
    std::vector<PyRef>    attr_names_;   // interned Python str, borrowed from the class
    PyRef                 model_cls_;
    bool                  eligible_ = false;
};
```

`attr_names_` holds the *same* interned `str` objects the class already owns, so writing into `instance.__dict__` needs no string construction or hashing beyond the dict's own — Python interns attribute names, and reusing the identical object hits the dict's pointer-equality fast path.

### 6.2 Execution

```
execute(plan, rows) -> list[Model]:
    for each row:                          # native loop, no Python frames
        inst = model_cls.__new__(model_cls)
        d    = inst.__dict__               # borrowed
        orig = new dict                    # dirty-tracking snapshot
        for op in plan.ops_:               # switch on op.code
            raw = row_values[op.key_index]
            val = convert(op.code, raw)
            PyDict_SetItem(d,    attr_names_[op.attr_index], val)
            PyDict_SetItem(orig, attr_names_[op.attr_index], val)
        inst._original_values = orig
    return list
```

What this removes, per field, versus `base.py:2045`:

| Removed | Measured (`02` §4) |
|---|---|
| `col_to_attr.get(key)` dict lookup | ~8 ns |
| `field.to_python(raw)` Python call | ~30–100 ns of dispatch |
| `isinstance(field, ForeignKey)` | ~8 ns (B6) |
| `setattr` → descriptor `__set__` | **114 ns** (B3) |
| loop iteration bytecode | — |
| unconditional deferred setcomp | **152 ns/row** (B4) |

Writing `instance.__dict__` directly is not a shortcut — it is precisely what `Field.__set__` does (`fields_module.py:255`). The descriptor stays in place for class-level access; only the per-write dispatch is skipped, and only for plans proven to contain no custom `__set__`.

### 6.3 Semantics that must be preserved exactly

Detailed in `04-hydration-engine-spec.md`; summarised here because they constrain the design:

- `cls.__new__(cls)` — **no `__init__`**, so `pre_init`/`post_init` do not fire (they do not fire today).
- `_original_values` snapshot must be populated identically, or `save()` emits wrong `UPDATE` statements.
- Deferred fields must produce the guard-class swap, so `only()`/`defer()` still raise on access.
- FK columns must wrap in `RelatedNotLoaded`.
- Absent columns must **not** default to `None` — indistinguishable from a real NULL.

---

## 7. Validation engine — `FieldPlan`

### 7.1 Structure

```cpp
struct FieldOp {
    PyRef         name;          // interned field name
    TypeCode      code;
    std::uint8_t  flags;         // REQUIRED | ALLOW_NULL | HAS_DEFAULT | READ_ONLY
    PyRef         default_value; // literal only; a default_factory is Unsupported
    // Constraint payload resolved at compile time: min/max, length, pattern id
    std::int64_t  imin, imax;
    std::uint32_t min_len, max_len;
    std::int32_t  pattern_id;    // -1 = none
};

class FieldPlan {
    std::vector<FieldOp> ops_;
    bool eligible_ = false;
};
```

Every flag here replaces a per-field `isinstance` or attribute read from `sigil.py:255-300` (B10) — `Computed`/`Constant`/`Inject` checks, `read_only`, `required`, `allow_null`, `default is not UNSET`. All are static per class; all become bits resolved once.

### 7.2 Execution

```
execute(plan, payload) -> (errors, validated):
    validated = new dict
    errors    = nullptr             # allocated lazily, only on first failure
    for op in plan.ops_:
        raw = PyDict_GetItem(payload, op.name)     # plain-dict fast path
        if !raw:
            handle missing via flags (default / required / allow_null)
            continue
        if raw is None:
            handle via ALLOW_NULL flag
            continue
        val = convert_and_check(op, raw)           # switch on code, inline constraints
        if failed: record error; continue
        PyDict_SetItem(validated, op.name, val)
    return errors, validated
```

Three costs from `02` §5 disappear:

- **B7** — no ABC `isinstance`. The plan is only eligible for plain-`dict` payloads; `MultiDict`/`FormData` route to Python, where the alternate-key logic lives.
- **B8** — no `keys_to_try` list, no `f"{fname}[]"`. One `PyDict_GetItem` with a pre-interned key.
- **B9/B10** — no `cast`/`seal` Python calls, no per-field branch chain.

**Errors are allocated lazily.** The success path never builds a dict. On failure the native side produces `{field: [message]}` in exactly the shape `sigil.validate` returns, so `core.py:1371`'s `self._errors.update(errors)` is unchanged.

---

## 8. Eligibility — the rule that keeps this safe

A plan compiles only when **every** field/column is representable. Any of the following makes the whole plan `Unsupported`:

**Hydration:**
- a `Field` subclass overriding `to_python` or `__set__` (checked by comparing the bound method against the base implementation)
- a field type outside the `TypeCode` set
- M2M fields (already excluded from `_col_to_attr`)
- `select_related` aliased columns (`rel__attr`) — the splitting logic stays in Python
- a model with a custom `__new__`

**Validation:**
- a custom `Facet` subclass overriding `cast`/`seal`
- `spec.pipeline is not None`
- any validator on the facet
- `Computed` / `Constant` / `Inject` facets
- nested contracts (`is_nested_contract`)
- `default_factory` (a Python callable)
- non-`dict` payload (`MultiDict`, `FormData`)
- `strict` mode (different semantics: cast is skipped)
- `partial` mode — supportable later, excluded from v1

`@ward` methods and the `validate()` hook are **not** eligibility concerns: they run in Phase 3/4 of `is_sealed`, after `Sigil.validate` returns. The native engine replaces Phase 1+2 only.

> **Superseded in part.** This list is the v1 rule. Phase 2 narrowed several
> entries — eligibility is now decided **per field** rather than per contract, and
> nested contracts, `pattern`, `choices`, `multiple_of`, and the collection facets
> are covered. The current rule lives in `_native_plan.py`; see
> [`11-phase2-coverage-expansion.md`](11-phase2-coverage-expansion.md) for what
> moved and why. A child Contract declaring a `@ward` or overriding `validate()`
> *does* become an eligibility concern once the parent's nested field compiles
> natively, because the sub-plan would otherwise skip that user code.

---

## 9. Memory and ownership

| Object | Owner | Lifetime | Native holds |
|---|---|---|---|
| `RowPlan` / `FieldPlan` | Python (`nb::class_`) | cached on the model/contract class | its own vectors |
| Model instances | caller | request | **produced, never retained** |
| `attr_names_`, `FieldOp::name` | the class | process | borrowed `PyRef` (strong, but to immortal-ish interned strs) |
| Row values | the caller's row objects | the call | borrowed for the call only |
| `Decimal`/`date`/`datetime` constructors | CPython | process | captured once at module init |

**The engine never owns a framework object.** It reads class metadata at compile time, produces Python objects at execute time, and retains nothing between calls except the plan itself.

`PyRef` is reused from `_core/src/request_ctx.hpp` — a single-pointer owning reference with copy-increfs and destructor-decrefs, already ASAN-clean under the Phase 9 test suite.

---

## 10. GIL policy

Every entry point **holds the GIL**, without exception. Both executors touch `PyObject*` on every iteration; releasing and re-acquiring around a 1 µs batch would cost more than the batch.

This is a deliberate scope limit worth stating: the engine makes each batch cheaper, it does **not** make hydration parallel. Releasing the GIL would require converting to intermediate C++ values first and building Python objects in a second GIL-held pass — a legitimate future design, but a different one, and only worthwhile for very large result sets. Recorded in `09` as future work, not attempted here.

---

## 11. Plan caching and invalidation

**Hydration:** keyed by `(model_class, row_key_tuple)`. Row shape varies with `only()`/`defer()`/`values()`, so the key must include the actual key tuple, not just the class. Cached on the model class in a small dict; bounded by the number of distinct projections an app uses, which is static per codebase.

**Validation:** keyed by contract class alone — the Sigil is fixed at class build. One plan per contract, built on first use.

**Invalidation:** plans are immutable once built. Dev-mode hot reload creates new classes, which miss the cache naturally. No explicit invalidation path, therefore no staleness bug.

**Free-threading:** plans are immutable after build and the caches are plain dicts written once. Under a free-threaded build, concurrent first-use could build the same plan twice — harmless (both are identical, one is discarded). No lock needed.

---

## 12. Error propagation

Same contract as `_core`: **C++ exceptions never cross the boundary, and domain errors are not raised from C++.**

| Situation | Native behaviour | Python behaviour |
|---|---|---|
| Field conversion fails | record in the errors dict | caller raises the existing `Fault` |
| Plan ineligible | return `nullptr`/`None` at compile time | caller uses the Python path |
| Row shape mismatch at execute | return `None`, do not partially hydrate | caller falls back |
| `std::bad_alloc` | translated to `MemoryError` | — |

All framework errors remain structured `Fault` subclasses raised from Python with their full diagnostic payloads, per the project's fault convention.

---

## 13. Projected gains — labelled as projections

From the `02` §2 decomposition. These are arithmetic on measured components, **not** benchmark results, and `09` gates every milestone on measurement rather than on these numbers.

| Path | Now | Conversion floor | Projected | Projected factor |
|---|---|---|---|---|
| `from_row`, 8 columns | 3,002 ns | 859 ns | ~1,000 ns | **~3×** |
| `Sigil.validate`, 8 fields | 5,034 ns | 499 ns | ~1,200 ns | **~4×** |
| 100-row page hydration | 311 µs | — | ~100 µs | ~3× |
| 100-payload validation | 501 µs | — | ~120 µs | ~4× |

The projection assumes the native loop reaches roughly 150 ns/row and 90 ns/field of residual overhead above the conversion floor. If measurement after Milestone 3 shows materially worse, `09`'s exit gate requires revising the plan rather than continuing.

---

## 14. What is explicitly not in this design

| Rejected | Why | Evidence |
|---|---|---|
| Per-field native conversion API | boundary (43 ns) exceeds six of eight conversion floors | `02` §3 |
| Native SQL builder | 0.45% of a page-serving request | `02` B12 |
| Native query-set / expression compiler | startup-ish, not per-row | `01` §2 |
| Native migrations / codegen / introspection | CLI-time | `01` §2 |
| Native `to_db` (write path) | writes are 1 row per statement; no batch to amortise over | — |
| Native ISO-8601 parsing | CPython's is C and 18–25 ns; reimplementation risks tz/fractional-second divergence for ~zero gain | `02` §3 |
| Native cycle/graph work | not on the hot path | `01` §2 |
| GIL-released parallel hydration | needs a two-pass design; different project | §10 |
| Native dirty-tracking removal | `save()` depends on it | `02` B5 |

---

## 15. Success criteria

| Criterion | Target | Measured by |
|---|---|---|
| `from_row` 8 columns | ≤ 1,200 ns | `benchmarks/models/profile_baseline.py` |
| `Sigil.validate` 8 fields | ≤ 1,500 ns | same |
| 100-row hydration | ≤ 120 µs | same |
| Boundary crossings per batch | exactly 1 | review + `noop()` accounting |
| Fallback parity | 100% of suite with `AQUILIA_DATAENGINE=0` | CI gate |
| Plan-ineligible fallback | identical results, verified by parity tests | `07` |
| ASAN/UBSAN | zero reports | CI gate |
| Refcount balance | no growth over 100k rows | `07` §memory |
| No import cycle | zero new SCC members | `import_graph.py` |

Continues in `04-hydration-engine-spec.md` and `05-validation-engine-spec.md` for exact semantics, and `06-python-fixes.md` for the work that must land **before** any of this.
