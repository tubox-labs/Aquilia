# Phase 4 — Hydration Engine Specification

**Status:** design
**Targets:** `02-performance-audit.md` bottlenecks B1–B6
**Replaces:** the per-row body of `Model.from_row` (`aquilia/models/base.py:2045`) for eligible plans only

---

## 1. Scope

This engine replaces one thing: the loop that turns a list of database rows into a list of model instances. It does **not** touch query building, SQL execution, the write path (`save`/`to_db`), relations traversal, or migrations.

Entry point today:

```python
# aquilia/models/query.py:1416
return [self._model_cls.from_row(row) for row in rows]
```

Entry point after:

```python
plan = _dataengine_loader.row_plan_for(self._model_cls, row_keys)
if plan is not None:
    return plan.execute(rows)          # one boundary crossing for the whole page
return [self._model_cls.from_row(row) for row in rows]
```

The Python `from_row` remains the reference implementation and the fallback. It is never deleted.

---

## 2. Plan compilation

Compiled once per `(model_class, row_key_tuple)`, cached on the model class.

### 2.1 Inputs

| Input | Source | Used for |
|---|---|---|
| `cls._col_to_attr` | `metaclass.py:228` | column name → `(attr_name, field)` |
| `cls._non_m2m_fields` | `metaclass.py:223` | detecting deferred columns |
| row key tuple | `cursor.description` | column order, fixed per result set |
| each `field.__class__` | — | type code assignment |

### 2.2 Type-code assignment

| Field class | TypeCode | Conversion |
|---|---|---|
| `CharField`, `TextField`, `EmailField`, `SlugField`, `URLField` | `Str` | passthrough or decode |
| `IntegerField`, `BigIntegerField`, `SmallIntegerField`, `AutoField` | `Int` | `PyLong_FromString` if str, else passthrough |
| `FloatField` | `Float` | `PyFloat_FromString` if str |
| `BooleanField` | `Bool` | inline token compare |
| `DateField` | `Date` | `date.fromisoformat` (CPython C) |
| `DateTimeField` | `DateTime` | `datetime.fromisoformat` (CPython C) |
| `TimeField` | `Time` | `time.fromisoformat` |
| `DecimalField` | `Decimal` | `Decimal(str)` (CPython `_decimal`) |
| `UUIDField` | `Uuid` | **native hex parse** |
| `JSONField` | `Json` | native scan |
| `BinaryField` | `Bytes` | `PyBytes_FromStringAndSize` |
| `ForeignKey`, `OneToOneField` | underlying pk code + `FK_WRAP` flag | convert, then wrap |
| anything else | `Unsupported` | **plan rejected** |

### 2.3 Eligibility — the plan compiles only if all hold

1. Every row key resolves through `_col_to_attr`, **or** is a `select_related` alias — aliases make the plan ineligible (splitting stays in Python, `query.py:1367`).
2. Every mapped field's class is in the table above.
3. No field overrides `to_python`. Checked by identity:
   ```python
   type(field).to_python is BaseField.to_python
   ```
   A subclass with a custom converter must run its own Python code.
4. No field overrides `__set__` (same identity check against `Field.__set__`).
5. The model does not override `__new__`.
6. The model is not already a deferred-guard variant (`__deferred_guard__`).

If any check fails the compiler returns `None` and the caller uses `from_row`. **There is no partial plan** — a mixed path would be a second implementation that could diverge silently.

---

## 3. Semantics that must be reproduced exactly

Each item below is behaviour the current `from_row` has. Divergence on any of them is a correctness bug, not a performance trade.

### 3.1 `__init__` is bypassed

```python
instance = cls.__new__(cls)     # base.py:2054
```

Hydration must **not** call `__init__`, and therefore must **not** fire `pre_init`/`post_init` signals (`models/signals.py:598,607`). Hydrating a 1,000-row page fires zero init signals today; the engine must keep it that way.

### 3.2 Dirty-tracking snapshot

```python
original[attr_name] = converted     # base.py:2075
instance._original_values = original
```

`save()` diffs against `_original_values` via `get_dirty_fields()` to build minimal `UPDATE` statements (`base.py:1675`). The snapshot must contain **the converted value, not the raw one**, and must contain exactly the attributes that were set — not all fields.

**Failure mode if wrong:** `save()` either writes columns that did not change, or silently skips columns that did. The second is data loss. This is the highest-severity invariant in the spec, and `07` gates it with a dedicated round-trip test.

### 3.3 Deferred fields

```python
deferred = {attr for attr, _f in cls._non_m2m_fields if attr not in seen}   # base.py:2088
if deferred:
    instance._deferred_fields = deferred
    instance.__class__ = _deferred_guard_class(cls)                          # base.py:2092
```

`_deferred_guard_class` (`base.py:255`) builds and caches a subclass whose `__getattribute__` raises `DeferredFieldAccessFault` for deferred names.

The engine must reproduce this, including the class swap. Critically: **an absent column must not become `None`**, because `None` is indistinguishable from a real SQL NULL (`base.py:2079-2087` documents exactly this).

The plan knows at compile time whether the row shape covers every field, so the common "nothing deferred" case is a compile-time constant — this is where B4's 152 ns/row goes.

### 3.4 Foreign-key wrapping

```python
if isinstance(field, ForeignKey) and converted is not None:
    converted = RelatedNotLoaded(converted, field_name=attr_name, owner_model_name=cls.__name__)
```

A raw FK id is wrapped in `RelatedNotLoaded` (`models/relations.py:47`) so that attribute access raises `RelatedNotLoadedFault` with guidance instead of an `AttributeError` on an `int`. `bool()`, `.pk`, and `==` work on the sentinel without a query.

The engine carries this as the `FK_WRAP` flag, resolved at compile time rather than by a per-row `isinstance` (B6). `None` FK values are **not** wrapped.

### 3.5 Column-key resolution

`_col_to_attr` is keyed by **both** column name and attribute name (`metaclass.py:230-231`), so a row keyed either way hydrates. The plan resolves through the same dict, so both spellings keep working.

### 3.6 Unmapped keys are ignored

Keys not in `_col_to_attr` are skipped silently (the `if mapping is not None` guard). Annotations, aggregates, and `select_related` aliases arrive this way. The plan must skip them identically — not error.

---

## 4. Execution

```
execute(rows) -> list[Model]:
    out = PyList_New(len(rows))
    for i, row in enumerate(rows):
        inst = model_cls.__new__(model_cls)
        d    = inst.__dict__
        orig = PyDict_New()
        for op in ops_:                       # switch on op.code — no Python frames
            raw = row_value(row, op.key_index)
            val = convert(op.code, raw)       # may call a captured CPython constructor
            if op.flags & FK_WRAP and val is not None:
                val = RelatedNotLoaded(val, ...)
            PyDict_SetItem(d,    attr_names_[op.attr_index], val)
            PyDict_SetItem(orig, attr_names_[op.attr_index], val)
        PyObject_SetAttr(inst, "_original_values", orig)
        if plan.has_deferred:                 # compile-time constant
            set _deferred_fields; swap __class__
        PyList_SET_ITEM(out, i, inst)
    return out
```

### Why writing `instance.__dict__` directly is correct

`Field.__set__` is exactly `instance.__dict__[self.attr_name] = value` (`fields_module.py:255`). Writing the dict directly performs the same store and skips only the descriptor dispatch — 114 ns per field (B3). Eligibility rule §2.3.4 guarantees no field has a custom `__set__`, so nothing is bypassed except the cost.

The descriptor itself stays: class-level access (`Model.field` returning the `Field` for query building) is unaffected, because that goes through `__get__` on the class, which the engine never touches.

---

## 5. Row access

Rows arrive as `aquilia.sqlite._rows.Row` (a `dict` subclass) or plain dicts from other adapters. The plan stores `key_index` positions, but a `dict` has no stable positional access from C without re-hashing.

**Resolution:** the plan holds the interned key `str` objects and uses `PyDict_GetItem` with them. Interned keys make this a pointer-equality hit in the dict's lookup fast path. `key_index` remains in `ColumnOp` for the tuple-row path (§6).

---

## 6. Interaction with B1/B2 — the row factory

`02` B1 and B2 identify 196.6 ns/row rebuilding the key tuple and 358 ns/row constructing `Row`. Those are **Python-side fixes in `06-python-fixes.md`**, sequenced before this engine.

There is a larger opportunity worth recording but **not** taking in v1: if the adapter handed the engine the raw `cursor.fetchall()` tuples plus one key tuple, the engine could index rows positionally and skip `Row` construction entirely — removing B1 and B2 outright rather than optimising them.

That requires changing the `DatabaseAdapter.fetch_all` contract (`db/backends/base.py:115`), which returns `list[dict]` and is public API implemented by four backends. Deferred to `09` as a follow-on milestone with its own compatibility analysis.

---

## 7. Error handling

| Situation | Behaviour |
|---|---|
| Conversion raises (bad ISO string, invalid UUID) | abort the whole batch, return `None`, caller re-runs in Python so the existing exception and its diagnostics surface unchanged |
| Row shape differs from the plan mid-batch | abort, return `None`, caller falls back |
| `std::bad_alloc` | translate to `MemoryError` |
| Partial hydration | **never** — a batch either completes or returns nothing |

Aborting rather than raising keeps every domain error's message, fault code, and traceback identical to today's, because the error is ultimately produced by the same Python code that produces it now.

---

## 8. Acceptance criteria

| Criterion | Target |
|---|---|
| `from_row` equivalent, 8 columns | ≤ 1,200 ns (from 3,002) |
| 100-row page | ≤ 120 µs (from 311) |
| `_original_values` parity | byte-identical dict for every test model |
| `save()` after native hydration | emits identical SQL to save-after-Python-hydration |
| Deferred fields | `DeferredFieldAccessFault` still raised; guard class identical |
| FK wrapping | `RelatedNotLoaded` for non-null FKs, raw `None` for null |
| No init signals | `pre_init`/`post_init` fire zero times over 1,000 rows |
| Unmapped keys | ignored, not errored |
| Ineligible plans | fall back; results identical |
| Refcount balance | no growth over 100,000 rows |
| Existing `tests/test_models*` | 100% pass, unmodified |
