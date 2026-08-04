# Phase 1 — Architecture Audit: models / db / contracts

**Status:** analysis complete
**Scope:** `aquilia/models/` (30,241 lines), `aquilia/contracts/` (12,859), `aquilia/db/` (3,391), `aquilia/sqlite/` (2,684)
**Method:** source reading plus direct measurement. Every claim below is traceable to a file:line or to `benchmarks/models/baseline.json`.

---

## 1. Why this audit exists before any design

The Phase 9 controller-engine work produced a specific, transferable lesson: **design documents written from assumed costs get the target wrong.** That project assumed a ~60 ns Python/native boundary and budgeted against it; the measured figure was 7.7 ns. The 8× error inverted three of five component decisions — two planned components turned out to be strictly slower than the Python they would replace, and were cancelled after implementation had already been scoped.

This audit therefore establishes the *measured* cost structure first. Section 8 states the numbers that govern every subsequent design decision, and `02-performance-audit.md` derives them.

---

## 2. Subsystem map

| Path | Lines | Role | On the request hot path? |
|---|---|---|---|
| `models/base.py` | 2,319 | `Model`, `from_row`, save/delete, dirty tracking | **yes** (`from_row`) |
| `models/fields_module.py` | 3,778 | Field descriptors, `to_python`/`to_db`, SQL types | **yes** (per field, per row) |
| `models/query.py` | 2,041 | `QuerySet`, lazy chaining, `_hydrate_rows` | **yes** |
| `models/sql_builder.py` | 803 | Parameterised SQL string assembly | **yes** (per query) |
| `models/expression.py` | 1,301 | `F()`, `Q()`, expression `as_sql` | yes, when used |
| `models/manager.py` | 742 | Default manager, `objects` descriptor | entry only |
| `models/metaclass.py` | ~250 | Builds per-class caches at import | **no** (import time) |
| `models/migration/**` | ~6,500 | Schema diffing, codegen, executor | **no** (CLI only) |
| `models/registry.py` | 727 | Model registry, table creation | no |
| `models/signals.py` | 682 | `pre_init`/`post_init`/save signals | conditional |
| `contracts/sigil.py` | 1,413 | **Compiled schema IR + `validate()`** | **yes** |
| `contracts/facets.py` | 3,753 | Per-type `cast()`/`seal()` | **yes** (per field) |
| `contracts/core.py` | 2,852 | `Contract`, `is_sealed`, ward phases, `imprint` | **yes** |
| `contracts/annotations.py` | 1,583 | Annotation → facet resolution | **no** (class build) |
| `db/engine.py` | 774 | `AquiliaDatabase`, `fetch_all`/`fetch_one` | **yes** |
| `db/backends/*` | ~2,000 | Per-dialect adapters | **yes** |
| `sqlite/**` | 2,684 | Native async SQLite: pool, cursor, row factory | **yes** |

**Roughly 13,000 of the ~50,000 lines are on a per-request path.** Migrations, codegen, introspection, and the CLI surface are startup- or operator-time and are explicitly out of scope for any native work.

---

## 3. Execution flow: read path

```
QuerySet.all()
  └─ _build_select()                     models/query.py    → (sql, params)
  └─ await db.fetch_all(sql, params)     db/engine.py:519
       └─ adapter.fetch_all              db/backends/sqlite.py
            └─ sqlite3 cursor + row_factory   sqlite/_rows.py:116
                 → list[Row]   (Row subclasses dict)
  └─ _hydrate_rows(rows)                 models/query.py:1357
       └─ for each row: Model.from_row(row)    models/base.py:2045
            ├─ cls.__new__(cls)                 (bypasses __init__)
            ├─ for key, raw in row.items():
            │    ├─ col_to_attr.get(key)        metaclass-built dict
            │    ├─ field.to_python(raw)        fields_module.py
            │    ├─ isinstance(field, ForeignKey) → maybe RelatedNotLoaded wrap
            │    ├─ setattr(instance, attr, v)  → Field.__set__ → instance.__dict__
            │    └─ original[attr] = v          dirty-tracking snapshot
            ├─ deferred = {…}                   unconditional setcomp
            └─ instance._original_values = original
```

### Critical structural facts

1. **`row_factory` rebuilds the key tuple per row.** `sqlite/_rows.py:130` runs `tuple(d[0] for d in cursor.description)` for *every* row, though `cursor.description` is constant for the whole result set. This is O(columns) redundant work per row.

2. **Row shape is invariant within a result set.** Every row from one query has identical keys in identical order. `from_row` does not exploit this — it re-dispatches `col_to_attr.get(key)` per column per row. This invariant is the single most important fact for the design: it means a *plan* can be computed once per query and reused for every row.

3. **`from_row` bypasses `__init__`** via `cls.__new__(cls)`, so `pre_init`/`post_init` signals do **not** fire on hydration. Any replacement must preserve this, or hydrating 1,000 rows would emit 2,000 signals that do not fire today.

4. **The deferred-field setcomp runs unconditionally** (`base.py:2088`), even when every column is present — measured at **152 ns/row**, ~5% of an 8-column `from_row`.

5. **Dirty tracking duplicates every value.** `original[attr_name] = converted` writes a second dict entry per field. `save()` diffs against it (`_snapshot_original`, `base.py:1675`) to build minimal `UPDATE` statements. It is load-bearing and cannot simply be dropped.

6. **Field access is a data descriptor.** `Field.__get__`/`__set__` (`fields_module.py:238`/`253`) wrap `instance.__dict__`. Measured: descriptor `setattr` 152.6 ns vs raw dict write 38.8 ns — **114 ns of protocol overhead per field write**. The descriptor is public API (class-level access returns the `Field` for query building), so it cannot be removed.

---

## 4. Execution flow: validation path

```
Contract(data=payload).is_sealed()        contracts/core.py:1269
  ├─ async-ward guard
  ├─ adapt_input / is_mapping_like        contracts/sigil.py
  ├─ optional unknown-field rejection     (builds a set of known fields per call)
  ├─ Sigil.validate(data, …)              contracts/sigil.py:169   ← Phase 1+2
  │    └─ for fname, spec in self.fields.items():
  │         ├─ isinstance(facet, (Computed, Constant))
  │         ├─ isinstance(facet, Inject)
  │         ├─ facet.read_only check
  │         ├─ get_field_value(data, fname, facet)   sigil.py:797
  │         ├─ UNSET / None / default handling
  │         ├─ nested-contract resolution            (if applicable)
  │         └─ facet.cast(raw) → facet.seal(cast)    facets.py
  ├─ _run_ward_phase(validated)           Phase 3: cross-field @ward methods
  └─ _run_validate_hook(validated)        Phase 4: object-level validate()
```

### Critical structural facts

1. **`Sigil` is already a compiled IR.** `sigil.py:4` — built once per Contract class, stored as `cls._sigil`, with `FieldSpec.__slots__`. The *architecture* is right; the per-field interpretation of it is what costs.

2. **`get_field_value` uses an ABC in its type test.** `sigil.py:823` runs `isinstance(data, (dict, Mapping))` where `Mapping` is `collections.abc.Mapping`. ABC `isinstance` dispatches through `_abc_instancecheck`: measured **54.9 ns for `Mapping` vs 7.9 ns for `dict`**. This runs once per field per payload, on the overwhelmingly common case where `data` is a plain `dict`.

3. **`get_field_value` allocates per field.** `sigil.py:821` builds `keys_to_try = [fname, f"{fname}[]"]` — a list plus an f-string — on every call, before the plain-dict fast path that never needs the second key. Measured **24.5 ns**.

4. **`isinstance` dominates the profile by call count.** cProfile over 5,000 validations of an 8-field payload: **230,000 `isinstance` calls** (46 per validation), of which 40,000 route through `_abc_instancecheck`.

5. **Error accumulation is per-field `setdefault`.** Failures build `errors.setdefault(fname, []).append(...)`. Fine for the failure path; it is not on the success path and needs no optimisation.

6. **Facets are Python objects with `cast`/`seal` pairs.** ~18 facet types, each a separate method pair (`facets.py:531`–`2184`). Two Python calls per field minimum.

---

## 5. Metaclass-built caches (the assets a native engine inherits)

`models/metaclass.py` computes these once at class creation:

| Cache | Line | Contents |
|---|---|---|
| `_fields` | 191 | `{attr_name: Field}` |
| `_m2m_fields` | 192 | M2M subset (excluded from row mapping) |
| `_non_m2m_fields` | 223 | `[(attr_name, field)]`, ordered |
| `_col_to_attr` | 228–231 | `{column_name: (attr, field)}` **and** `{attr_name: (attr, field)}` |
| `_attr_names` | 102 | For `_snapshot_original` |

`_col_to_attr` is keyed by both column and attribute name, so a row keyed either way hydrates. A native plan builder must resolve through the same dict to stay consistent with `only()`/`defer()`/`select_related` aliasing.

---

## 6. Ownership and lifetime boundaries

| Object | Owner | Lifetime | Can native code hold it? |
|---|---|---|---|
| `Field` instances | model class | process | borrowed only; they hold Python callables |
| `Model` instances | caller | request | native must *produce*, never retain |
| `_col_to_attr` | model class | process | read at plan-build time only |
| `Sigil` / `FieldSpec` | contract class | process | read at plan-build time only |
| Facet objects | contract class | process | borrowed; hold validators/pipelines |
| `Row` (sqlite) | cursor → caller | statement | borrowed for the duration of hydration |
| Validators / `@ward` methods | contract class | process | **must stay in Python — arbitrary user code** |
| `default_factory` callables | facet | process | **must stay in Python** |

**The hard rule this implies:** the native layer may compute *plans* from these structures at query/class time, and may convert *values*, but must never own a framework object, and must never call a Python callable. Anything that dispatches to user code (validators, pipelines, wards, computed fields, custom `to_python` overrides) stays on the Python path by construction.

---

## 7. Extension points that must survive unchanged

Each of these is public API. Any native path must fall back to Python when one is present, not attempt to reproduce it.

1. **Custom `Field` subclasses** overriding `to_python`/`to_db`/`validate`.
2. **Custom `Facet` subclasses** overriding `cast`/`seal`.
3. **`@ward` cross-field validators**, sync and async.
4. **`validate()`** object-level hook.
5. **`Pipeline`** per-field transform chains (`spec.pipeline`).
6. **`Computed` / `Constant` / `Inject`** facets (context-resolved).
7. **Nested contracts**, including `many=True` lists.
8. **`Lens` / projections / facets** re-shaping (`contracts/lenses.py`, `projections.py`).
9. **Signals** — `pre_save`/`post_save`/`pre_delete`/`post_delete`.
10. **`select_related` / `prefetch_related`** hydration paths.
11. **`only()` / `defer()`** → deferred-field guard classes.
12. **`RelatedNotLoaded`** FK sentinel wrapping.
13. **Model inheritance** and abstract bases.
14. **Multiple dialects** — sqlite / postgres / mysql / oracle `as_sql` branches.

---

## 8. Measured cost structure — the numbers that govern the design

From `benchmarks/models/profile_baseline.py` (macOS arm64, CPython 3.11.15):

### Hydration

| Operation | Cost |
|---|---|
| `from_row`, 4 cheap columns | 1,106 ns |
| `from_row`, 8 mixed columns | **3,002 ns** |
| hydrate 100 rows × 8 columns | **311 µs** |
| `to_python` CharField | 29.8 ns |
| `to_python` DateTimeField | 105.1 ns |
| `to_python` DecimalField | 96.1 ns |
| `to_python` UUIDField | **433.7 ns** |
| `to_python` JSONField | **378.3 ns** |
| descriptor `setattr` | 152.6 ns |
| raw dict write | 38.8 ns |
| deferred setcomp (unconditional) | 152.4 ns |

### Validation

| Operation | Cost |
|---|---|
| `Sigil.validate`, 8 fields | **5,034 ns** |
| `Contract(...).is_sealed()`, 8 fields | **7,797 ns** |
| `Contract(...)` construction | 204.3 ns |
| validate 100 payloads | **501 µs** |
| `get_field_value` | 170.7 ns |
| facet cast+seal, text | 202.4 ns |
| facet cast+seal, int | 221.2 ns |
| facet cast+seal, uuid | 466.8 ns |

### SQL generation

| Operation | Cost |
|---|---|
| simple SELECT build | 1,392 ns |
| 5-predicate + JOIN build | 2,378 ns |

### The decisive decomposition

Summing the *irreducible* CPython conversion cost — what any implementation must pay to produce the same Python objects:

| Path | Total | Irreducible conversion | **Framework overhead** |
|---|---|---|---|
| `from_row`, 8 columns | 3,002 ns | 859 ns | **2,143 ns (71%)** |
| `Sigil.validate`, 8 fields | 5,034 ns | 499 ns | **4,535 ns (90%)** |

**This is the finding that makes native work worthwhile, and it is not the finding the obvious design would target.** The cost is not in converting values — it is in the per-field Python interpretation surrounding each conversion: attribute lookups, method dispatch, `isinstance` chains, temporary allocation, descriptor protocol.

### The boundary arithmetic that constrains the API shape

| Measurement | Value |
|---|---|
| nanobind bare call | 8.1 ns |
| nanobind call, 2 string args | **43.3 ns** |

Compared against each conversion floor:

| Conversion | Floor | vs 43 ns boundary |
|---|---|---|
| `str` passthrough | 3.2 ns | **loss** |
| `date.fromisoformat` | 18.7 ns | **loss** |
| `float(str)` | 21.4 ns | **loss** |
| `datetime.fromisoformat` | 24.7 ns | **loss** |
| `int(str)` | 27.2 ns | **loss** |
| `Decimal(str)` | 44.7 ns | marginal |
| `json.loads` | 378.9 ns | **win** |
| `uuid.UUID(str)` | 354.4 ns | **win** |

**A per-field native API is dead on arrival.** CPython's `fromisoformat`, `int()`, and `float()` are already C and cost less than one boundary crossing. Only UUID and JSON parsing are slow enough to win per-call — and `uuid.UUID.__init__` is slow precisely *because it is pure Python* (`uuid.py:139`, three `str.replace` calls plus `strip`/`count`/`len` per parse).

**A batch API changes the arithmetic completely.** One crossing amortised over a result set:

| Batch | Values | Boundary share per value |
|---|---|---|
| 1 row × 8 fields | 8 | 4.97 ns |
| 10 rows × 8 fields | 80 | 0.50 ns |
| 100 rows × 8 fields | 800 | **0.05 ns** |
| 1,000 rows × 8 fields | 8,000 | 0.005 ns |

At page-sized batches the boundary is free. This dictates the engine's shape: **cross once per result set or per payload, never once per field.**

---

## 9. Concurrency and thread safety

- All hydration and validation is **synchronous CPU work** called from async contexts. Neither releases the GIL today.
- `Sigil` and the metaclass caches are **immutable after class creation** — safe to read from any thread, and safe to build native plans from without synchronisation.
- `sqlite/_pool.py` manages connection concurrency; hydration happens after rows are materialised, outside any connection lock.
- `_statement_cache.py` is per-connection, so no cross-thread contention.
- Under free-threaded builds, plan caches keyed by model class would need either immutability-after-build (preferred) or a lock. Immutability is achievable: plans depend only on `_col_to_attr` and the row key tuple, both fixed.

---

## 10. Import graph

`aquilia.models` and `aquilia.contracts` are inside the package's existing 40-node SCC. A native module must have **zero `aquilia.*` imports** — it is a dependency of the framework, not a dependent — exactly as `aquilia/_core/` already does, loaded through a fail-soft `_core_loader`.

A pre-existing cycle is worth recording: `from aquilia.di.core import Container` as a process's *first* import fails (`di → faults → middleware → middleware_ext → di`). Reproduces on a clean tree; unrelated to this work, but it constrains where a loader may be imported from.

---

## 11. What the audit concludes

1. **The hot paths are `Model.from_row` and `Sigil.validate`.** Everything else in these 50k lines is startup, CLI, or migration work.
2. **71–90% of their cost is framework overhead, not value conversion.** The target is per-field interpretation, not arithmetic.
3. **A per-field native API cannot win.** The boundary costs more than most conversions.
4. **A batch API can win decisively**, because row shape is invariant within a result set and payload shape is fixed by the Sigil — so the interpretation can be *compiled once and replayed*.
5. **Several substantial wins need no C++ at all** — the ABC `isinstance`, the per-field list/f-string allocation, and the unconditional deferred setcomp. These must land and be re-baselined *first*, exactly as the Phase 9A Python fixes did, because they change the profile the native engine is designed against.

Continues in `02-performance-audit.md` (evidence per bottleneck) and `06-python-fixes.md` (the no-C++ wins, which are sequenced first).
