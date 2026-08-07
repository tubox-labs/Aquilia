# 11 — Phase 2: Native Contracts Coverage Expansion

Phase 1 shipped a native `FieldPlan` covering nine scalar facets and four
`list[scalar]` shapes. This document records what Phase 2 added across three
tiers, why each addition is safe, and what was deliberately left in Python.

Phase 2 closes with **twelve scalar codes across five container shapes, plus
recursive nested Contracts** — measured at 1.3×–10.7× on `is_sealed()` depending
on how much work the field loop was doing (§6).

The safety property is unchanged and is worth restating, because every decision
below follows from it:

> The native plan is an optimisation whose only contract is **indistinguishability**
> from `Sigil.validate`. Any value the plan cannot decide with certainty aborts
> the whole payload back to Python, which then produces the authoritative
> `(errors, validated)` — so error messages stay byte-identical and correctly
> localised for free.

---

## 1. What Phase 2 added

### Tier 1

| Facet / constraint | Native | Notes |
|---|---|---|
| `ChoiceFacet` | ✅ | `frozenset` membership via `PySet_Contains` |
| `LiteralFacet` | ✅ | Compiles to the same code — it *is* a one-element `ChoiceFacet` |
| `IntFacet.multiple_of` | ✅ | `PyNumber_Remainder`, not C `%` (see §3.1) |
| `ListFacet.min_items` / `max_items` | ✅ | Counted after cast, matching `seal` order |
| `list[UUID]`, `list[date]` | ✅ | Reuse the scalar element casts |

### Tier 2

| Facet / constraint | Native | Notes |
|---|---|---|
| `EnumFacet` | ✅ | Value-then-name lookup; escapes on custom `_missing_` (§3.2) |
| `SetFacet` | ✅ | Dedupe semantics proven equivalent (§3.3) |
| `TupleFacet` | ✅ | Ordered; set input deferred (§3.4) |
| `DecimalFacet` cast | ✅ | `Decimal(str)`; non-finite deferred |
| `DecimalFacet.max_digits` / `decimal_places` | ✅ | Read off `Decimal.as_tuple()` — the same source Python reads |
| `DurationFacet` | ⚠️ Partial | `timedelta` passthrough + numeric seconds; string forms deferred (§3.5) |

`DecimalFacet` was an explicit v1 exclusion (`05 §3`, and the
`decimal-v1-exclusion` test id). Tier 2 lifts it; `tests/dataengine/test_eligibility.py`
now asserts the opposite and documents why.

### Tier 3

| Facet / constraint | Native | Notes |
|---|---|---|
| Nested `Contract` (single) | ✅ | Recursive sub-plan; escapes on wards / `validate()` override (§3.7) |
| Nested `Contract` (to-many) | ✅ | Composes with the container axis — one sub-plan per element |
| `TextFacet.pattern` | ✅ | Calls the compiled `re.Pattern.search` (§3.8) |
| `DictFacet` | ✅ | `max_keys`, str-key check, optional scalar `value_facet` (§3.9) |
| `BytesFacet` | ⚠️ Partial | `bytes`/`bytearray` + size bounds; base64/hex strings deferred (§3.10) |

Nested Contracts were the last structural exclusion, and the one that mattered
most: `_native_plan.py`'s own module docstring called them out as the reason the
native path was "effectively dead in production", because nested objects are the
normal shape of a real API payload. Per-field escape (Phase 1) stopped one
nested field sinking its siblings; Tier 3 removes the escape itself for the
common case.

---

## 2. Architecture change: two axes instead of one

Phase 1 encoded containers as distinct type codes — `ListStr`, `ListInt`,
`ListFloat`, `ListBool`, and later `ListUuid`, `ListDate`. Adding `Set`, `Tuple`,
and `Dict` on that scheme would have needed the same six codes three times more:
twenty-four codes to express six element types across four containers.

Phase 2 splits the axes:

```cpp
enum class TypeCode      { Str, Int, Float, Bool, Date, DateTime, Time,
                           Decimal, Uuid, Duration, Choice, Enum, Nested, ... };
enum class ContainerKind { None, List, Set, Tuple, Dict };
```

A `FieldOp` now carries both. When `container != None`, `code` describes the
**element** type and the scalar cast is applied per item — per *value*, for
`Dict`. Six codes plus four kinds, and a new container costs one enum value
rather than six.

This is why `cast_element()` exists as a separate function: it is the single
place a scalar type's semantics live, shared by the scalar path and all four
containers. There is no second implementation that could drift.

The payoff showed up immediately in Tier 3. `list[ItemContract]` needed no new
machinery at all — `TypeCode::Nested` combined with `ContainerKind::List` is a
sub-plan applied per element, and it fell out of the existing container loop.

---

## 3. Why each addition is exact

### 3.1 `multiple_of` — Python's `%`, not C's

Python's `%` takes the sign of the **divisor**; C's takes the sign of the
**dividend**:

```
Python:  -7 % 5 ==  3
C:       -7 % 5 == -2
```

A C modulo would therefore accept and reject different negative values than
`IntFacet.seal` does. The native check calls `PyNumber_Remainder`, which *is*
Python's operator.

`FloatFacet.multiple_of` is **not** reproduced. It uses an epsilon test
(`abs(v/m - round(v/m)) > 1e-9`) whose result at the boundary depends on binary
rounding, so a float `multiple_of` is escaped at compile time.

### 3.2 `EnumFacet` — the `_missing_` hazard

`EnumFacet.cast` calls `enum_class(value)`, which is `EnumMeta.__call__`. That
consults `_value2member_map_` and, **on a miss, invokes the `_missing_` hook** —
arbitrary user Python that can return any member it likes.

The native path replaces that call with a plain dict lookup, which is exact only
while `_missing_` is the inherited no-op. So the compiler checks:

```python
own = enum_class._missing_
base = Enum._missing_
return own.__func__ is base.__func__
```

An Enum with a custom hook is escaped. The lookup order (value first, then name)
is preserved, which matters when a member's *name* collides with another
member's *value* — `tests/.../test_enum_name_value_collision_parity` pins it.

The `IntEnum`/`StrEnum` coercion step (`int(value)` / `str(value)` before the
lookup) is deliberately **not** reproduced. A miss defers, so Python still gets
to try the coercion — `"1"` on an `IntEnum` falls back and resolves correctly.

### 3.3 `SetFacet` — cast-then-dedupe vs dedupe-then-cast

Python dedupes the **raw** values, then casts:

```python
result = set(value)                      # dedupe first
cast_items = {self.child.cast(i) for i in result}
```

The native path casts, then dedupes. These are equivalent only if equal raw
values cast to equal outputs — and they are, for the element types the plan
accepts, because every mismatched pair defers:

| Raw pair | Equal? | Native behaviour |
|---|---|---|
| `1`, `True` | yes | `cast_int` rejects `bool` → defer |
| `1`, `True` (TextFacet child) | yes | `cast_text` rejects non-`str` → defer |
| `"1"`, `1` | no | both cast to `1`; both paths yield `{1}` |

Item counts are judged **after** dedup, matching `seal`: `["a","a"]` with
`min_items=2` fails in both paths.

### 3.4 Set input is refused for every container

Iterating a Python `set` has no defined order. For `TupleFacet` that ordering is
observable in the result. Python has the same non-determinism, but reproducing
it natively would mean the two paths could disagree on a given run while both
being "correct" — which is untestable. All three containers defer on set input.

### 3.5 `DurationFacet` — partial by choice

`DurationFacet.cast` handles `timedelta`, numeric seconds, and two string forms
(bare float, and `HH:MM:SS` with sign handling). Only the first two are native;
strings defer.

`bool` is also deferred. `isinstance(True, int)` is true in Python, so
`DurationFacet` actually accepts `True` and yields `timedelta(seconds=1)` — real
behaviour, but surprising enough that deferring is cheaper than risking a subtle
mismatch.

### 3.6 `DecimalFacet` — significant digits, not written digits

`max_digits` counts **significant** digits from `Decimal.as_tuple()`, so
`Decimal("0.001")` has *one* digit and *three* decimal places. Surprising, but it
is exactly what `facets.py` counts, and the native check reads the same tuple.

Non-finite Decimals (`NaN`, `Infinity`) parse successfully but compare unusably
against bounds, and `DecimalFacet.seal` has no guard for them. The native cast
checks `is_finite()` and defers, so behaviour matches whatever Python does.

Float input also defers: `Decimal(str(0.1))` is `Decimal("0.1")` while
`Decimal(0.1)` keeps the binary error, and letting Python perform its own
conversion removes any doubt about which one happens.

### 3.7 Nested Contracts — what the Python path does *besides* validating

`sigil.run_nested_contract` is not just the child's field loop. It instantiates
the child Contract, runs its `@ward` methods, and calls its `validate()` hook.
Both are user Python, which the engine may never execute.

So the native sub-plan is only built when the child provably has neither:

```python
if getattr(nested_cls, "_ward_methods", None):        return None
if nested_cls.validate is not Contract.validate:      return None
```

With both absent, `run_nested_contract` reduces to exactly the child's
structural pass, and a recursive `FieldPlan` reproduces it.

Three further gates:

- **A partial child is refused.** If the child's own plan escapes any field, the
  parent has no way to report that from inside its single native pass. The child
  must be *fully* covered or the parent field escapes.
- **Self-reference is refused.** `class Node: child: Node` would recurse forever
  at compile time, and a strong ref from a plan to itself would leak. A
  compile-in-progress set breaks the cycle and escapes that field — its siblings
  still compile, because the guard is per field.
- **Compile depth is capped** at `_MAX_NESTED_COMPILE_DEPTH`, so a pathological
  schema cannot blow the C stack during recursion.

The result the sub-plan produces is a plain `dict`, where Python produced
`dict(DataObject)`. Those are indistinguishable: `DataObject` subclasses `dict`,
and the parent re-wraps the value on access regardless.

### 3.8 `pattern` — calling the regex, not reimplementing it

`TextFacet.seal` runs `self.pattern.search(value)` — `search`, not `match`, a
distinction easy to get wrong in a rewrite. The native path calls that same
compiled `re.Pattern` object via `PyObject_CallMethodOneArg`.

This is not user code: `re.Pattern.search` is `_sre`, implemented in C. What is
saved is not the match itself but the field's *escape* — before Tier 3 a single
patterned field dropped out of the plan entirely.

Order matters and is preserved: blank check → `min_length` → `max_length` →
`pattern`. Python reports the first violation, so reordering would change which
message a caller sees.

Subclasses still escape. `EmailFacet`, `URLFacet`, and `SlugFacet` are
`TextFacet` subclasses, and the compiler matches on `type(facet) is TextFacet`,
so their overridden semantics can never be reached by the base path.

### 3.9 `DictFacet` — the key checks, not the values' semantics

Native handles what is mechanical: `dict` input, `max_keys` (the DoS guard),
and the str-key requirement. A `value_facet` is applied per value through the
same `cast_element` the containers use, and only when that facet is a plain
scalar with no constraints of its own.

String input is deferred. `DictFacet.cast` will `json.loads` a value that looks
like a JSON object, and that path is already C with its own error semantics.

### 3.10 `BytesFacet` — passthrough only

`bytes` and `bytearray` inputs are handled, with `min_length`/`max_length`
checked in bytes. Everything else defers, and the reason is the `encoding`
parameter: `BytesFacet` decodes `str` input as **base64 by default**, with hex
and utf-8 as alternatives. Reproducing three decoders with matching validation
errors buys nothing over `base64.b64decode`, which is already C.

---

## 4. What stays in Python, and why

| Feature | Reason |
|---|---|
| Pipelines (`>>`) | User callables — the engine must never call Python user code |
| `validators=[...]` | Same |
| `@ward` methods, `validate()` hook | Same; they run *after* the plan regardless |
| Nested Contract with wards / `validate()` | The child's own user Python (§3.7) |
| Nested Contract that is self-referential | Non-terminating compile; ownership cycle (§3.7) |
| `EmailFacet`, `URLFacet`, `IPFacet`, `SlugFacet` | Complex validation already backed by C stdlib; hand-rolling the regexes is pure divergence risk for near-zero gain |
| `PathFacet` | Security-critical (traversal, null bytes) — not worth a second implementation |
| `JSONFacet` | Already `json.loads` (C) plus a recursive depth walk |
| `BytesFacet` string input | base64/hex/utf-8 decoders already C (§3.10) |
| `FloatFacet.multiple_of` | Epsilon comparison; boundary depends on binary rounding (§3.1) |
| `Computed`, `Constant`, `Inject` | Not payload-derived; free to escape |
| `Lens` | Async ORM traversal |
| `strict=True` contracts | Different semantics — `cast` is skipped entirely |
| Contracts with `revision` + `migrate_from` | Migrations rewrite the payload before the field loop |

---

## 5. Testing

Two differential suites, 268 tests total:

- `tests/dataengine/test_fieldplan_phase2_parity.py` — Tier 1
- `tests/dataengine/test_fieldplan_tier2_parity.py` — Tier 2

Every test asserts the same thing: validating a payload with the engine **on**
produces an identical `(sealed, validated_data, errors)` triple to validating it
with the engine **off**. Python is the reference implementation by construction,
so a test can never encode a second opinion about what Python does.

Tier 3 adds a third suite, `tests/dataengine/test_fieldplan_tier3_parity.py`, and
weights it toward the nested cases — including the *negative* ones. A child
carrying a ward, a child overriding `validate()`, a child whose own plan is
partial, and a self-referential field each get both an eligibility assertion
(the escape happens) and a parity assertion (the escape still agrees with
all-Python). An escape that silently stopped escaping would otherwise be
invisible.

### Anti-vacuity guards

A parity test that compares Python against Python passes unconditionally and
proves nothing. Both suites therefore assert explicitly that their fixtures
*reach* the native path:

```python
compiled = native_plan.field_plan_for(contract_cls)
assert compiled is not None
assert not compiled.escaped
```

If a compiler change starts escaping one of these fields, this fails loudly
rather than letting the parity tests silently test nothing.

### NaN handling in the harness

`Decimal("NaN") == Decimal("NaN")` is False by IEEE-754. The comparator treats
two NaNs of the same type as equal — the question the suite asks is whether the
two paths are *distinguishable*, and two NaNs are not.

### Removability

The engine remains fully removable. `AQUILIA_DATAENGINE=0` runs the entire suite
on the pure-Python path:

```
engine on:   8828 passed,   8 skipped
engine off:  8542 passed, 294 skipped
```

---

## 6. Measured results

`Contract.is_sealed()` throughput, best of 7×20 000 runs, engine toggled in a
subprocess (`benchmarks/contracts/microbench_tier2.py`, `microbench_tier3.py`).

### Tier 1 + 2

| Case | Python (ns) | Native (ns) | Speedup |
|---|---:|---:|---:|
| `choice` | 2 784 | 2 160 | 1.29× |
| `enum` | 3 138 | 2 205 | 1.42× |
| `decimal` | 3 310 | 2 492 | 1.33× |
| `set` | 3 810 | 2 246 | 1.70× |
| `tuple` | 3 732 | 2 202 | 1.69× |
| `duration` | 2 937 | 2 367 | 1.24× |
| `list_int_bounded` (8 items) | 4 688 | 2 164 | 2.17× |
| `kitchen_sink` (9 fields) | 9 097 | 3 110 | **2.92×** |
| **median** | | | **1.56×** |

### Tier 3

| Case | Python (ns) | Native (ns) | Speedup |
|---|---:|---:|---:|
| `bytes` | 2 860 | 2 173 | 1.32× |
| `pattern` | 3 078 | 2 283 | 1.35× |
| `dict_plain` (8 keys) | 3 170 | 2 336 | 1.36× |
| `dict_typed` (8 keys) | 5 448 | 2 322 | 2.35× |
| `nested_1_field` | 6 318 | 2 213 | 2.86× |
| `nested_wide_child` (5 fields) | 7 778 | 2 321 | 3.35× |
| `nested_3_levels` | 8 894 | 2 271 | 3.92× |
| `tier3_sink` (6 fields) | 15 722 | 2 594 | **6.06×** |
| `nested_many_8` | 26 860 | 2 509 | **10.71×** |
| **median** | | | **2.86×** |

The gain scales with field count, which confirms the mechanism: the win is not
faster per-value conversion (six of eight scalar conversions already delegate
to CPython's own C code) but the **elimination of per-field Python bytecode
dispatch** — the `isinstance` chains, attribute reads, and `UNSET` comparisons
that `Sigil.validate` re-evaluates for every field of every request.

Nested Contracts add a second, larger saving on top of that. The Python path
constructs a child `Contract` *instance* per nested field per payload — metaclass
lookup, `__init__`, error dict, `DataObject` wrap — and the native sub-plan
replaces all of it with a recursive loop over a pre-resolved op table. That is
why `nested_many_8` reaches 10.7×: it removes eight instantiations per request,
and the native time barely moves from the single-field case (2 509 ns vs
2 213 ns) while the Python time grows more than fourfold.

The ~2.2 µs native floor is `is_sealed()` overhead *outside* the field loop
(instance construction, projection, error assembly), which the engine does not
touch. Speedup therefore tracks how much work the loop itself was doing: a
single scalar field recovers ~600–1 500 ns, a nine-field contract ~6 000 ns, and
a to-many nested field ~24 000 ns.

---

## 7. Extending this further

To add a facet:

1. **Read its `cast` and `seal` in `facets.py` line by line.** Every deferral in
   this document exists because a line did something non-obvious.
2. Add a `TypeCode` (or a `ContainerKind`, for a new shape).
3. Write `cast_x` / `check_x` in `fieldplan.cpp`. Return `kFallback` for anything
   you cannot decide with certainty — a false fallback costs speed, a false
   accept is a silent correctness bug.
4. Map it in `_facet_type_code()` and pass any constraint data through
   `_build_plan()` via `FieldSpec`.
5. Add differential parity tests **and** an anti-vacuity assertion.
6. Confirm the field compiles with `escaped == frozenset()`.

The bar for step 3 is not "does this usually work". It is *can the native plan
reproduce this field's semantics exactly*, and anything short of certainty
answers no.

### If the facet runs anything user-supplied

Tier 3's nested Contracts set the pattern for this, and it generalises. Ask what
the Python path does *besides* converting the value. `run_nested_contract` also
ran wards and a `validate()` hook, so the compiler proves both are absent before
building a sub-plan rather than trying to reproduce them.

Three questions worth asking of any recursive or composite facet:

- **Does compiling it terminate?** A self-referential schema does not. Guard with
  a compile-in-progress set and escape the cycle.
- **Does it create an ownership cycle?** A plan holding a strong ref to itself
  leaks. Escaping self-reference solves both at once.
- **Can a partially-covered child report its escapes?** In this design it cannot,
  because the parent makes one native pass. So a partial child means the parent
  field escapes whole.

### `FieldSpec` over positional arguments

`add()` reached 18 positional parameters at the end of Tier 2, and Tier 3 needed
four more. It now takes a `FieldSpec` struct with defaulted members, so a new
constraint is one named field and touches no existing call site or binding
signature. Adding a 23rd constraint should not be a reason to re-read the other
22 in order.
