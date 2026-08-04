# Phase 6 — Python-First Fixes (no C++ required)

**Status:** ready to implement
**Sequencing:** these land **before** any native work and the baseline is re-measured afterwards
**Verified:** every fix below was prototyped and measured against the current implementation. Numbers are measured deltas, not estimates.

---

## 1. Why these come first

The Phase 9 controller-engine project established the sequencing rule the hard way: the 9A Python fixes delivered a −49% static request for ~35 lines of Python, and in doing so **changed which costs dominated**. Two native components specified against the pre-fix profile (9E, 9G) turned out to be slower than the Python they would replace and were cancelled.

The same risk exists here. `02-performance-audit.md` §7 ranks the bottlenecks; six of the top ten are pure-Python fixes. If the native engine is designed against the *current* profile rather than the post-fix profile, its targets will be wrong in the same way.

**These fixes also change the eligibility calculus.** F1 in particular removes 53% of `get_field_value`, which is a significant fraction of what the native validation engine was going to win. That must be known before the native work is scoped, not after.

---

## 2. The fixes

### F1 — `get_field_value`: ABC `isinstance` + eager allocation ★ largest

**File:** `aquilia/contracts/sigil.py:797`
**Bottlenecks:** B7, B8

Two problems on the same line pair. `isinstance(data, (dict, Mapping))` tests against an abstract base class, which dispatches through `_abc_instancecheck` instead of a C-level type check. And `keys_to_try = [fname, f"{fname}[]"]` allocates a list plus an f-string per field, before the plain-dict path that never needs the second key.

Current:

```python
keys_to_try = [fname, f"{fname}[]"]

if isinstance(data, (dict, Mapping)) and not (_MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS)):
    for k in keys_to_try:
        if k in data:
            return data[k]
    return UNSET
```

Proposed — add a fast path, leave the existing logic untouched beneath it:

```python
# Fast path: an exact dict, which is what a parsed JSON body always is.
# `type() is dict` rather than isinstance: it cannot match MultiDict or
# FormData (both need the alternate-key handling below), and it avoids the
# ABC dispatch that `Mapping` forces -- measured 54.9 ns vs 7.9 ns.
# The "[]" key is only built if the plain name misses, so the common case
# allocates nothing.
if type(data) is dict:
    value = data.get(fname, UNSET)
    if value is not UNSET:
        return value
    return data.get(f"{fname}[]", UNSET)

# ... existing logic unchanged for MultiDict / FormData / Mapping subclasses
```

| | Measured |
|---|---|
| current | 77.3 ns |
| proposed | 36.6 ns |
| **saving** | **40.7 ns/field (53%)** |
| per 8-field payload | 325 ns |
| per 100 payloads | **32.5 µs** |

**Risk:** low. `MultiDict` and `FormData` are not exact `dict`s, so they take the unchanged path. A plain-`dict` payload with a `field[]` key still resolves, via the second `.get`. Verified against `tests/test_contract_binding_formats.py`, which covers all three payload shapes.

---

### F2 — `from_row`: unconditional deferred set comprehension

**File:** `aquilia/models/base.py:2088`
**Bottleneck:** B4

The comprehension detects `only()`/`defer()` exclusions. It runs on every row even when every column is present, which is the common case.

Current:

```python
deferred = {attr_name for attr_name, _field in cls._non_m2m_fields if attr_name not in seen}
```

Proposed:

```python
# `seen` can only contain attrs that are in _non_m2m_fields, so equal counts
# means nothing was excluded -- skip building the set at all. only()/defer()
# is the exception, not the rule, and this runs once per row.
if len(seen) == len(cls._non_m2m_fields):
    deferred = None
else:
    deferred = {attr_name for attr_name, _field in cls._non_m2m_fields if attr_name not in seen}
```

| | Measured |
|---|---|
| current | 175.7 ns |
| proposed | 27.9 ns |
| **saving** | **147.8 ns/row (84%)** |
| per 100-row page | **14.8 µs** |

**Risk:** low. The invariant holds because `seen` is populated only from `_col_to_attr` lookups, which resolve to `_non_m2m_fields` entries. A duplicate column cannot inflate the count because `seen` is a set. Worth an assertion in tests rather than in the hot path.

---

### F3 — `row_factory`: rebuilding the key tuple for every row

**File:** `aquilia/sqlite/_rows.py:116`
**Bottleneck:** B1

`cursor.description` is constant for a result set; the factory rebuilds a tuple from it per row.

Current:

```python
def row_factory(cursor, row_tuple):
    keys = tuple(d[0] for d in cursor.description)
    return Row(keys, row_tuple)
```

Proposed — cache keyed on the `description` object:

```python
_KEY_CACHE: dict[int, tuple[str, ...]] = {}

def row_factory(cursor, row_tuple):
    # cursor.description is a fresh tuple per statement but constant across
    # every row of that statement, so rebuilding the key tuple per row is
    # O(columns) of pure waste -- measured 204 ns/row for 8 columns.
    desc = cursor.description
    keys = _KEY_CACHE.get(id(desc))
    if keys is None:
        keys = tuple(d[0] for d in desc)
        _KEY_CACHE[id(desc)] = keys
    return Row(keys, row_tuple)
```

| | Measured |
|---|---|
| current | 204.3 ns |
| proposed | 3.2 ns |
| **saving** | **201 ns/row (98%)** |
| per 100-row page | **20.1 µs** |

**Risk:** medium, and the `id()` key is the reason. `id()` is reusable after the object is freed, so a cache keyed on it can return a stale tuple for a *different* description that happens to land at the same address. Two mitigations, and the implementation must pick one:

1. **Preferred:** attach the cache to the cursor rather than a module dict — `cursor._aq_keys` — so its lifetime is exactly the cursor's and no `id()` reuse is possible.
2. Store `(desc_object, keys)` and verify identity on hit, keeping a strong reference so the address cannot be reused.

Option 1 is simpler and has no aliasing hazard. **Do not ship the module-level `id()` dict as written above** — it is shown only to make the hazard explicit.

---

### F4 — `Contract.is_sealed`: rebuilding the known-field set

**File:** `aquilia/contracts/core.py:1349`
**Bottleneck:** B11

```python
known_fields = set(self._bound_facets.keys())
```

`_bound_facets` is fixed per class, so this set is a class constant rebuilt per call.

Proposed: compute once in the metaclass (or memoise on first use) as `cls._known_field_names: frozenset[str]`.

| | Measured |
|---|---|
| current | 83.0 ns |
| proposed | 3.2 ns |
| **saving** | **79.8 ns/payload (96%)** |

**Risk:** low. **Caveat:** this only runs when `extra_fields == "reject"`, so it is not on the default path. Included because it is a two-line change with no downside, but its real-world impact is smaller than the raw number suggests — stated so it is not over-credited.

---

### F5 — `from_row`: per-row `isinstance(field, ForeignKey)`

**File:** `aquilia/models/base.py:2065`
**Bottleneck:** B6

FK-ness is a static property of the field, tested per field per row. cProfile shows 15 `isinstance` calls per row.

Proposed: extend the metaclass cache to carry the flag. `_col_to_attr` currently stores `(attr_name, field)`; make it `(attr_name, field, is_fk)`, computed at `metaclass.py:228`.

| | Estimated |
|---|---|
| saving | ~8 ns × columns/row |
| per 100-row page, 8 columns | ~6.4 µs |

**Risk:** low, but this changes a cache tuple's shape. `_col_to_attr` is internal, but must be grepped for external readers before changing arity. Alternatively add a parallel `_fk_attrs: frozenset[str]` and leave the tuple alone — lower blast radius, and preferred.

**Labelled estimate, not measured** — the saving is inferred from the `isinstance` cost, not prototyped end to end.

---

### F6 — `Row` construction is 2× a plain dict

**File:** `aquilia/sqlite/_rows.py:19`
**Bottleneck:** B2

| | Measured |
|---|---|
| `Row(keys, values)` | 358.0 ns |
| `dict(zip(keys, values))` | 184.5 ns |
| difference | 173.5 ns/row → **17.4 µs per 100-row page** |

**No fix proposed yet.** `Row` provides both index and key access and is user-visible. Reducing its cost requires deciding what of that API is load-bearing, which is a separate investigation. Recorded with its measurement so the decision is informed; explicitly **not** bundled into this phase.

---

## 3. Totals

| Fix | Target | Saving | Confidence |
|---|---|---|---|
| F1 | `get_field_value` | 32.5 µs / 100 payloads | measured |
| F2 | deferred setcomp | 14.8 µs / 100-row page | measured |
| F3 | row key tuple | 20.1 µs / 100-row page | measured |
| F4 | known-field set | 8.0 µs / 100 payloads (reject mode only) | measured |
| F5 | FK `isinstance` | ~6.4 µs / 100-row page | estimated |
| F6 | `Row` construction | 17.4 µs / 100-row page | measured, no fix yet |

**Actionable now: ~41 µs per 100-row page and ~40 µs per 100 payloads**, for roughly 30 lines of Python across four files.

For scale: hydrating a 100-row page currently costs 311 µs. These fixes address ~13% of it with no C++, no new build dependency, and no new failure mode.

---

## 4. Implementation order

Each fix is a separate commit, in this order, with the suite green between each:

1. **F2** — smallest blast radius, single file, single expression.
2. **F1** — highest value; touches the validation hot path, so land it alone and re-run `tests/test_contract_binding_formats.py` specifically.
3. **F3** — must use the cursor-attached cache (§F3 option 1), not the `id()` dict.
4. **F4** — trivial; verify with an `extra_fields="reject"` contract test.
5. **F5** — prefer the parallel `frozenset` over changing `_col_to_attr` arity.

Then:

```bash
python benchmarks/models/profile_baseline.py --json benchmarks/models/post_fixes.json
```

Commit `post_fixes.json`. **This is the baseline the native engine is designed and measured against.**

---

## 5. Exit gate

| Metric | Now | Target after fixes |
|---|---|---|
| `from_row`, 8 columns | 3,002 ns | ≤ 2,650 ns |
| `Sigil.validate`, 8 fields | 5,034 ns | ≤ 4,700 ns |
| 100-row page | 311 µs | ≤ 275 µs |
| 100 payloads | 501 µs | ≤ 465 µs |
| Full test suite | 7,850 pass | 7,850 pass, unmodified |

**If the measured gains differ materially from §3, revise `03-engine-design.md` §13 and `09-implementation-plan.md` before writing any C++.** That is the specific failure this sequencing exists to prevent.

---

## 6. Rejected — components measurement rules out

Recorded so they are not re-proposed. Each was considered and refuted by a number.

| Proposal | Verdict | Evidence |
|---|---|---|
| **Native per-field type conversion** | **rejected** — six of eight conversion floors are below the 43 ns boundary cost; `fromisoformat`/`int`/`float` are already C | `02` §3 |
| **Native SQL builder** | **rejected** — 1.4 µs per query against 311 µs of hydration for the page it feeds: 0.45% | `02` B12 |
| **Native query-set / expression compiler** | **rejected** — runs once per query, not per row | `01` §2 |
| **Native migrations / codegen / introspection** | **rejected** — CLI-time, never per-request | `01` §2 |
| **Native ISO-8601 parsing** | **rejected** — CPython's is C at 18–25 ns; a reimplementation risks timezone and fractional-second divergence for ~zero gain | `02` §3 |
| **Native `to_db` / write path** | **rejected for v1** — writes are one row per statement, so there is no batch to amortise the boundary over | `03` §14 |
| **Removing dirty tracking** | **rejected** — `save()` diffs `_original_values` to build minimal `UPDATE`s; removing it means full-column updates or data loss | `02` B5 |
| **Removing the `Field` descriptor** | **rejected** — class-level access returns the `Field` for query building; it is public API. The engine bypasses the *dispatch*, not the descriptor | `01` §3.6 |
| **GIL-released parallel hydration** | **deferred** — needs a two-pass convert-then-build design; a different project | `03` §10 |

### Two pre-existing issues found during this audit

Neither is caused by, nor fixed by, this work. Both reproduce on a clean tree and are recorded because they constrain where a loader may be imported:

1. **`aquilia.di` import cycle** — `from aquilia.di.core import Container` as a process's first import fails: `di → faults → middleware → middleware_ext → di`.
2. **`aquilia.sqlite` import cycle** — `from aquilia.sqlite._rows import Row` as a first import fails: `sqlite → db → backends.sqlite → sqlite`. Importing `aquilia.db` first works around it.
