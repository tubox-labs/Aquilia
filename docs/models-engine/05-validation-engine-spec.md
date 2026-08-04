# Phase 5 — Validation Engine Specification

**Status:** design
**Targets:** `02-performance-audit.md` bottlenecks B7–B11
**Replaces:** the per-field body of `Sigil.validate` (`aquilia/contracts/sigil.py:169`) for eligible plans only

---

## 1. Scope

This engine replaces **Phase 1+2 only** of the four-phase seal pipeline:

```
Contract.is_sealed()                         contracts/core.py:1269
  ├─ Phase 1+2: Sigil.validate()             ← THIS ENGINE
  ├─ Phase 3:   _run_ward_phase()            stays Python — arbitrary user code
  └─ Phase 4:   _run_validate_hook()         stays Python — arbitrary user code
```

`@ward` methods and the `validate()` hook run *after* `Sigil.validate` returns, so they are not eligibility concerns — they are simply out of scope. A contract with twenty wards can still use the native structural pass.

Entry point after:

```python
plan = _dataengine_loader.field_plan_for(type(self))
if plan is not None and type(data) is dict and not partial and not is_strict:
    errors, validated_dict = plan.execute(data)
else:
    errors, validated_dict = self._sigil.validate(data, ...)
```

`Sigil.validate` remains the reference implementation and the fallback.

---

## 2. Plan compilation

One plan per Contract class — the Sigil is immutable after class build (`01` §4.1), so the plan is too.

### 2.1 Inputs

Per `FieldSpec` (`sigil.py:84`) and its facet:

| Input | Used for |
|---|---|
| `spec.name` | interned dict key |
| `type(spec.facet)` | type code |
| `facet.required`, `facet.allow_null`, `facet.read_only` | flag bits |
| `facet.default` | literal default (a *callable* default → ineligible) |
| `spec.pipeline` | must be `None` |
| `spec.is_nested_contract` | must be `False` |
| `facet.validators` | must be empty |
| facet constraints (`min_value`, `max_length`, …) | inlined into the op |

### 2.2 Type-code assignment

| Facet | TypeCode | Constraints inlined |
|---|---|---|
| `TextFacet` | `Str` | `min_length`, `max_length`, `pattern`, `strip`, `choices` |
| `IntFacet` | `Int` | `min_value`, `max_value`, `multiple_of` |
| `FloatFacet` | `Float` | `min_value`, `max_value` |
| `DecimalFacet` | `Decimal` | `max_digits`, `decimal_places`, bounds |
| `BoolFacet` | `Bool` | — |
| `DateFacet` | `Date` | bounds |
| `DateTimeFacet` | `DateTime` | bounds |
| `TimeFacet` | `Time` | bounds |
| `UUIDFacet` | `Uuid` | version |
| `DurationFacet`, `DictFacet`, `ListFacet`, `FileFacet` | `Unsupported` | — (v1) |
| `Computed`, `Constant`, `Inject` | `Unsupported` | context-dependent |
| any custom subclass | `Unsupported` | — |

### 2.3 Eligibility

The plan compiles only when **every** field satisfies all of:

1. Facet class is exactly one of the supported classes — **not a subclass**. Checked by `type(facet) is TextFacet`, not `isinstance`, because a subclass may override `cast`/`seal`.
2. `spec.pipeline is None`
3. `not spec.is_nested_contract`
4. `not facet.validators`
5. `facet.default` is `UNSET` or a non-callable literal (a `default_factory` is Python code)
6. Facet is not `Computed`/`Constant`/`Inject`

### 2.4 Per-call eligibility

Even with a compiled plan, the native path is used only when:

- `type(data) is dict` — exactly `dict`, not a subclass, not `MultiDict`, not `FormData`. The alternate-key logic (`field[]`, flat-list extraction) stays entirely in Python.
- `partial is False` — PATCH semantics excluded from v1
- `strict is False` — strict mode has *different* semantics (cast is skipped entirely, `sigil.py:368`), so it is a separate execution mode, not a flag
- `revision`/`migrate_from` is unset — schema migration runs before the field loop (`sigil.py:222`)

---

## 3. Semantics that must be reproduced exactly

The facet `cast`/`seal` pairs encode deliberate, documented decisions. Several are counter-intuitive and are exactly where a reimplementation would silently diverge. These are the contract:

### 3.1 `IntFacet.cast` — the subtle one

From `facets.py:1449`:

| Input | Behaviour | Rationale (from source) |
|---|---|---|
| `True` / `False` | **reject** — "Boolean is not a valid integer" | bool is an `int` subclass in Python; accepting it silently would let `True` become `1` |
| `3.0` | accept → `3` | no information lost |
| `3.9` | **reject** — not truncate | "Truncation is silent data corruption — a client sending `{"quantity": 3.9}` would otherwise get `3` persisted with no indication anything was dropped" |
| `NaN`, `±inf` | reject | — |
| `Decimal("3.0")` | accept → `3` | via `to_integral_value` comparison |
| `Decimal("3.9")` | reject | same rule as float |
| `"3"` | accept → `3` | — |
| `"3.9"` | reject (`int()` raises) | — |

**A native `int` conversion that simply calls `strtoll` would accept `"3.9"`-shaped input differently and would accept `True`.** The native path must replicate this table exactly, and `07` pins every row of it.

### 3.2 `IntFacet.seal` — constraint order

`facets.py:1485`: `min_value` → `max_value` → `multiple_of` → `super().seal()` (validators). The **first** violation raises, so the error message for a value violating two constraints is deterministic. Constraint order must be preserved.

### 3.3 Base `Facet.seal` runs validators

`facets.py:570` iterates `self.validators`, wrapping `ValueError`/`TypeError` into `CastFault`. Eligibility rule §2.3.4 excludes any facet with validators, so the native path never needs this — but if that rule is ever relaxed, this behaviour comes with it.

### 3.4 Missing-value resolution order

From `sigil.py:272-285`, in exactly this order:

```
raw is UNSET:
    if partial:                 skip field entirely
    if facet.default is not UNSET:
        value = default() if callable(default) else default
        → validated
    if facet.required:          error "required"
    if facet.allow_null:        validated[f] = None
    otherwise:                  skip silently
```

Note that `default` is checked **before** `required` — a field that is both required and defaulted uses the default and does not error.

### 3.5 Explicit `None`

`sigil.py:288-293` — distinct from missing. `allow_null` → `validated[f] = None`; otherwise error `not_null`. A missing key and an explicit `None` are **not** interchangeable.

### 3.6 Skipped facet kinds

`Computed` and `Constant` are skipped in the loop entirely (`sigil.py:257`) — they are populated elsewhere. `Inject` resolves from context (`sigil.py:260`). `read_only` facets are skipped (`sigil.py:266`). All three are `Unsupported`, so the native plan never sees them.

### 3.7 Error shape

`Sigil.validate` returns `(errors, validated)` where `errors` maps field name → **list of message strings** (nested mappings for nested collections, which are `Unsupported` here). `core.py:1371` does `self._errors.update(errors)`.

The native engine must produce the identical shape, with messages from the same `contract_message()` catalogue (`contracts/messages.py`). **Message strings are user-visible API** — they appear in HTTP 422 bodies — so they must match byte-for-byte, not merely be equivalent.

**Implementation consequence:** the plan caches the *resolved message strings* at compile time where they are constant (`"required"`, `"not_null"`), and formats parameterised ones (`min_value`, `max_length`) natively using the same template. `07` diff-tests every message against the Python path.

### 3.8 Never raises

`Sigil.validate`'s contract is "never raises" (`sigil.py:181`) — every failure becomes an entry in `errors`. The native path must uphold this: a conversion failure is an error entry, never a propagated exception.

---

## 4. Execution

```
execute(payload: dict) -> (errors, validated):
    validated = PyDict_New()
    errors    = nullptr                     # lazily allocated — success path allocates none
    for op in ops_:                         # switch on op.code, no Python frames
        raw = PyDict_GetItem(payload, op.name)     # interned key → pointer-equality fast path
        if raw == nullptr:
            if op.flags & HAS_DEFAULT:  PyDict_SetItem(validated, op.name, op.default); continue
            if op.flags & REQUIRED:     add_error(op.name, MSG_REQUIRED); continue
            if op.flags & ALLOW_NULL:   PyDict_SetItem(validated, op.name, Py_None); continue
            continue
        if raw is Py_None:
            if op.flags & ALLOW_NULL:   PyDict_SetItem(validated, op.name, Py_None); continue
            add_error(op.name, MSG_NOT_NULL); continue
        val = convert(op, raw)              # cast semantics per §3.1
        if failed:  add_error(op.name, msg); continue
        if !check_constraints(op, val):     add_error(op.name, msg); continue
        PyDict_SetItem(validated, op.name, val)
    return errors ? errors : empty_dict, validated
```

Costs removed relative to `sigil.py:255-401`:

| Removed | Measured |
|---|---|
| ABC `isinstance(data, (dict, Mapping))` per field (B7) | part of 34.5 ns/field |
| `keys_to_try` list + f-string per field (B8) | 24.5 ns/field |
| `facet.cast()` + `facet.seal()` Python calls (B9) | 112–218 ns/field |
| per-field `isinstance`/attribute branch chain (B10) | ~46 `isinstance` per 8 fields |

---

## 5. Contract-level integration

`Contract.is_sealed` (`core.py:1269`) keeps its structure. Two changes:

1. The `Sigil.validate` call at `core.py:1364` consults the plan first.
2. The unknown-field check at `core.py:1349` rebuilds `set(self._bound_facets.keys())` per call — that set is static per class and belongs cached on it. This is a **Python fix** (B11), listed in `06`.

Phases 3 and 4 are untouched.

---

## 6. What stays in Python, and why

| Feature | Reason |
|---|---|
| `@ward` methods (sync + async) | arbitrary user code; runs after this engine |
| `validate()` hook | same |
| `Pipeline` transforms | user callables |
| Field validators | user callables |
| Nested contracts | recursion + depth guard + async accumulator; v1 scope limit |
| `ListFacet` / `DictFacet` | element recursion; v2 candidate |
| `Computed` / `Constant` / `Inject` | context-dependent, not payload-dependent |
| `MultiDict` / `FormData` payloads | alternate-key and flat-list extraction logic |
| `strict` mode | different semantics — skips cast entirely |
| `partial` mode | v1 scope limit; straightforward to add later |
| Schema migrations (`revision`) | runs before the field loop |
| `mold()` / serialisation | output path, not measured as hot |

---

## 7. Acceptance criteria

| Criterion | Target |
|---|---|
| `Sigil.validate` equivalent, 8 fields | ≤ 1,500 ns (from 5,034) |
| 100 payloads | ≤ 120 µs (from 501) |
| Error messages | byte-identical to the Python path |
| Error shape | `{field: [str]}`, identical keys and order-independent equality |
| `IntFacet` semantics | every row of §3.1's table verified |
| Missing vs `None` | distinct, per §3.4/§3.5 |
| Success path allocation | zero error-dict allocation |
| Never raises | property test over arbitrary payloads |
| Ineligible plans | fall back; results identical |
| Existing `tests/test_contract*` | 100% pass, unmodified |
