# Contracts — Nested Validation Pipeline — Aquilia v1.3.5

A deep audit of `aquilia/contracts/` found that a nested Contract's business rules never ran. `Sigil.validate()` recursed into the child's *structural* pass only — it validated field types and required-ness, then returned. Every `@ward` method and every object-level `validate()` override declared on a nested Contract was silently skipped.

This is the most severe defect fixed in this release. A nested Contract expressing an authorization check or a cross-field invariant enforced nothing, and the payload was accepted.

---

## 1. Nested Contracts never ran their wards or `validate()` hook

**Severity:** Critical — silent validation bypass.

### Previous behavior

```python
from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import IntFacet

class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # True  ← the ward never ran
order.errors        # {}
```

`qty=0` is structurally a valid integer, so the structural pass accepted it. The rule that says it is *business*-invalid never executed.

### Root cause

`Sigil.validate()` recursed directly into the child's compiled schema:

```python
sub_errors, sub_validated = nested_cls._sigil.validate(raw, ...)
```

A `Sigil` is the compiled *structural* representation of a Contract — field specs, types, required-ness. It has no knowledge of ward methods, which live on the Contract class and are invoked by `Contract.is_sealed()`. Because the nested Contract was never instantiated, `is_sealed()` was never called on it, so neither the ward phase nor the `validate()` hook ran.

This was not limited to async wards as originally reported. Synchronous wards were dead too.

### New behavior

Nested validation runs the child's full pipeline through a single shared helper, `run_nested_contract()`:

```python
order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
```

Errors are reported at the failing field's path. For a to-many relation the row index is preserved rather than flattened away, so a client can point at the offending item.

```python
order = Order(data={"items": [{"qty": 5}, {"qty": 0}]})
order.errors
# {"items": {"1": {"qty": ["Must be at least 1"]}}}
```

### User impact

**This is a behavioral change.** Payloads that previously passed validation may now be rejected — correctly. If a nested Contract in your application declares a `@ward` or overrides `validate()`, that rule is now enforced for the first time.

Before upgrading, review nested Contracts for rules that were silently inert. A rule written against an assumption that no longer holds will now start rejecting traffic.

---

## 2. `list[Contract]` annotations bypassed the nested pipeline

**Severity:** Critical — the fix above did not reach the most common spelling.

### Previous behavior

A to-many nested relation has two spellings that mean the same thing to a reader:

```python
# Spelling A — explicit facet
items = NestedContractFacet(LineItem, many=True)

# Spelling B — type annotation
items: list[LineItem] = None
```

They build *different facets*. Spelling A builds a `NestedContractFacet` with `many=True`. Spelling B builds a `ListFacet` whose `child` is a `NestedContractFacet`.

Nested detection matched only `NestedContractFacet`, so spelling B was classified as an ordinary list of values. It ran structural validation alone — meaning the nested-pipeline fix in section 1 did not apply to it, and `has_async_wards` reported `False` for a Contract whose children declared async wards.

```python
class Order(Contract):
    items: list[LineItem] = None       # ← annotated spelling

Order(data={}).has_async_wards          # False, even when LineItem has async wards
```

Because `has_async_wards` gates which entry point the framework uses, reporting `False` sent callers down the synchronous path — where the async ward was skipped silently rather than raising `ContractAsyncMismatchFault`.

### Root cause

`build_sigil()` set `is_nested_contract` with a direct type check:

```python
is_nested = isinstance(facet, (NestedContractFacet, LazyContractFacet))
```

A `ListFacet` wrapping a nested facet is not an instance of either, so the flag was `False` and every downstream consumer — validation routing, async-ward detection, JSON Schema generation — treated the field as a plain list.

### New behavior

Detection now looks through container facets. Both spellings route identically:

```python
class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
```

Async wards are detected through the list, so the sync entry point raises rather than skipping:

```python
Order(data={}).has_async_wards          # True
Order(data={"items": [...]}).is_sealed()  # raises ContractAsyncMismatchFault
await Order(data={"items": [...]}).is_sealed_async()   # correct
```

JSON Schema also improves, because an annotated list of Contracts is now emitted as an array of `$ref` rather than an untyped array:

```python
Order._sigil.to_json_schema()["properties"]["items"]
# {"type": "array", "items": {"$ref": "#/$defs/LineItem"}}
```

Two functions carry this:

| Function | Purpose |
|---|---|
| `is_nested_facet(facet)` | Whether a facet wraps a nested Contract, **without resolving it**. Used at class-body evaluation time, where a forward reference usually names the Contract currently being built. |
| `resolve_nested(facet)` | Returns `(contract_cls, is_many)`, looking through container facets. Returns `(None, False)` for an unresolvable forward reference rather than raising. |

`get_nested_contract_cls()` remains, now delegating to `resolve_nested()`, so existing callers are unaffected.

### User impact

The same behavioral change as section 1, now applying to the annotated spelling. Since `items: list[LineItem]` is the idiomatic form, most applications are affected by this fix rather than by section 1 alone.

---

## 3. `has_async_wards` consulted only the top-level class

**Severity:** High — silent skip instead of a clear error.

### Previous behavior

```python
class Child(Contract):
    sku = TextFacet()

    @ward(mode="async")
    async def in_stock(self, data):
        if not await lookup(data["sku"]):
            self.reject("sku", "Out of stock")

class Parent(Contract):
    child: Child = None

Parent(data={}).has_async_wards   # False
```

The property checked `self._ward_methods` — the wards declared on *this* class. A Contract whose nested child declared an async ward reported `False`, so callers took the synchronous path and the ward never ran. The intended failure mode was a loud `ContractAsyncMismatchFault`; the actual behavior was a silent skip.

### New behavior

The property walks the facet tree:

```python
Parent(data={}).has_async_wards   # True
```

Implementation notes that matter for correctness:

- **Memoized per class** (`_async_wards_deep_cache`) so the walk costs nothing after the first call. Contract classes are compiled once at import, so the answer cannot change at runtime.
- **Cycle detection** via a `_seen` set of class IDs, so a self-referential Contract (`Node` containing `list[Node]`) terminates.
- **Incomplete answers are never cached.** If the walk hits an unresolved forward reference or truncates at a cycle, the result is returned but not memoized — caching `False` from a truncated walk would permanently disable async detection for that class.

### User impact

A Contract with async wards nested beneath it now correctly requires `is_sealed_async()`. Code that called `is_sealed()` and appeared to work was not running the ward at all; it now raises `ContractAsyncMismatchFault` naming the problem.

---

## 4. No async serialization path existed

**Severity:** High — an async ORM with a sync-only serializer.

### Previous behavior

Aquilia's ORM relations are async, but every serialization entry point was synchronous. An un-awaited `RelatedManager` reaching `Lens.mold()` could only raise — there was no path that awaited it.

```python
order = await Order.objects.get(pk=1)
OrderContract(instance=order).to_dict()
# LensUnresolvedFault — and no async alternative existed
```

The only workaround was to prefetch every relation before serializing.

### New behavior

Three async entry points, mirroring the sync ones:

```python
# Single instance
data = await OrderContract.to_dict_async(order)

# Collection
rows = await OrderContract.to_dict_many_async(orders)
```

`Lens.mold_async()` awaits the relation, so prefetching becomes an optimization rather than a requirement:

```python
class OrderContract(Contract):
    items = Lens(ItemContract, many=True)

order = await Order.objects.get(pk=1)          # items not prefetched
data = await OrderContract.to_dict_async(order)  # awaits order.items
```

The synchronous path still raises `LensUnresolvedFault` — see section 5.

### Design: one field loop, two drivers

Sync and async serialization share a single field-molding generator, `_mold_steps()`, which yields `(facet, raw_value)` pairs for a driver to resolve:

```python
# Sync driver
for facet, raw in self._mold_steps(...):
    result[name] = facet.mold(raw)

# Async driver
for facet, raw in self._mold_steps(...):
    result[name] = await facet.mold_async(raw)
```

The field-selection logic — projections, `write_only` exclusion, computed fields, source resolution — exists once. A copy-paste async variant would drift from its sync twin at the first bug fix applied to only one of them.

### Performance

`to_dict_async()` awaits relations sequentially, one relation at a time. It is not slower than the sync path for prefetched data — awaiting an already-materialized list is close to free. For un-prefetched relations it issues one query per relation, so **prefetching remains the right choice on hot paths**; the async path exists so that forgetting to prefetch degrades performance rather than raising.

---

## 5. `Lens(many=True)` silently returned `[]` for unresolved relations

**Severity:** High — silent wrong data shipped to clients.

### Previous behavior

```python
order = await Order.objects.get(pk=1)   # items NOT prefetched
OrderContract(instance=order).data
# {"items": []}   ← indistinguishable from "this order has no items"
```

An un-awaited `RelatedManager` produced an empty list with no error. A client could not tell the difference between an order with no line items and an order whose line items failed to load.

### New behavior

```python
OrderContract(instance=order).data
# LensUnresolvedFault (BP503): naming the field and the fix
```

Three ways to resolve it:

```python
# 1. Prefetch (best for hot paths)
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the async serializer, which awaits for you
await OrderContract.to_dict_async(order)
```

### User impact

**This is a behavioral change.** Code relying on the silent empty-list fallback now raises. That fallback produced incorrect API responses — an empty relation and a failed-to-load relation are different facts, and conflating them ships wrong data without any signal.

---

## 6. Non-mapping input reported every field as missing

**Severity:** Medium — a misdiagnosis that cost debugging time.

### Previous behavior

A scalar or list request body was coerced to `{}`:

```python
UserContract(data="not an object").errors
# {"name": ["This field is required"],
#  "email": ["This field is required"],
#  "age": ["This field is required"]}
```

The real problem — the body was a string, not an object — was invisible. Developers chased missing fields that were never missing.

### New behavior

```python
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
```

### User impact

**This is a behavioral change** in error *shape*, not in accept/reject. A malformed body previously produced per-field errors and now produces a single `__all__` entry. Clients that parse the 422 body and assume every key is a field name should treat `__all__` as a document-level error.

The same correction applies to the bulk paths:

```python
UserContract.seal_many(["not a row"])[0].errors
# {"__all__": ["Expected an object, got str"]}
```

---

## 7. Top-level async wards bypassed group and ordering semantics

**Severity:** Medium — inconsistent behavior between entry points.

### Previous behavior

`is_sealed_async()` ran async wards through its own inline loop rather than the shared ward phase. The result: `order`, `when`, `groups`, and `Spec.fail_fast` applied on the bulk paths (`seal_many`, `seal_stream`) but not on the single-item async path.

```python
class Checkout(Contract):
    @ward(groups=("checkout",), mode="async")
    async def payment_valid(self, data): ...

await Checkout(data=...).is_sealed_async()   # ran the ward regardless of groups
```

### Root cause

Duplicated logic. `_run_ward_phase_async()` already existed and implemented all four features; `is_sealed_async()` predated it and kept its own copy.

### New behavior

The duplicate loop is gone. `is_sealed_async()` calls `_run_ward_phase_async()`, so every entry point applies identical semantics:

```python
await Checkout(data=...).is_sealed_async()                      # grouped ward skipped
await Checkout(data=...).is_sealed_async(groups="checkout")     # grouped ward runs
```

---

## Input adapters: dataclasses, attrs, and TypedDict

Contracts now accept dataclass instances, attrs classes, and `TypedDict` values as input, at every level:

```python
from dataclasses import dataclass

@dataclass
class LineItemDTO:
    qty: int

class Order(Contract):
    items: list[LineItem] = None

Order(data={"items": [LineItemDTO(qty=3)]}).is_sealed()   # True
```

Adaptation happens at a single point (`sigil.adapt_input`) that feeds the *existing* cast/seal pipeline. There is no parallel validation path for dataclass input, so a dataclass and the equivalent dict validate identically.

Adaptation is **shallow by design**. A dataclass field holding another dataclass is handled by the nested-Contract branch, not by recursive adaptation — the nested Contract knows the target shape, and a blind deep walk would convert values the target facet expects to receive intact.

---

## Depth guard correctness

Two related fixes to the recursion guard:

### The guard was unreachable from the real validation path

`MAX_NESTING_DEPTH = 32` was enforced in `NestedContractFacet.cast()`. The primary path (`Contract(data=...).is_sealed()`) never called `cast()` — it recursed through the Sigil — so the guard and its tests were unreachable from ordinary request validation. A few kilobytes of deeply nested JSON against any endpoint accepting a self-referential Contract raised an uncaught `RecursionError` inside the request coroutine.

Depth is now threaded through `Sigil.validate()` and yields a structured error:

```python
Node(data=deeply_nested).errors
# {"child": ["Nested Contract depth exceeds maximum of 32"]}
```

`MAX_NESTING_DEPTH` moved to `aquilia/contracts/exceptions.py` so the Sigil and facet layers cannot disagree about the limit.

### The depth counter was global mutable state

`NestedContractFacet._current_nesting_depth` was a plain class attribute mutated with `+=`/`-=` — shared across every instance, every Contract class, and every thread, despite a source comment claiming thread-locality. Concurrent validation could both reject shallow payloads spuriously *and* undercount deep ones, defeating the guard exactly when it mattered.

It is now a `contextvars.ContextVar`, correct for threads and asyncio tasks alike, covered by a 20-thread concurrency test.

---

## Related pages

- [Contracts — Validation Control & Typing](contracts_validation.md) — ward ordering, groups, new facets, i18n messages
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — `aq contracts stubs`, `seal_*` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
- [Bug Fixes](bugfixes.md) — task and mail subsystem fixes in this release
