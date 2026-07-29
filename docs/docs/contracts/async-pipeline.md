---
title: "Async Validation & Serialization"
description: "Async-native validation, nested Contract rules, and awaiting ORM relations during serialization"
icon: lucide/refresh-cw
---

Aquilia Contracts expose symmetrical sync and async pipelines for both inbound
validation and outbound serialization. This page covers when each is required,
how nested Contracts participate, and how async ORM relations are resolved.

---

## Nested Contracts run their full pipeline

A nested Contract is validated exactly like a top-level one: structural
validation, then its `@ward` methods, then its object-level `validate()` hook.

```python
class AddressContract(Contract):
    postcode = TextFacet()

    @ward
    def postcode_serviceable(self, data):
        if data["postcode"].startswith("XX"):
            self.reject("postcode", "We do not deliver to this area")

class OrderContract(Contract):
    address = NestedContractFacet(AddressContract)

contract = OrderContract(data={"address": {"postcode": "XX1 1AA"}})
contract.is_sealed()   # False
contract.errors        # {"address": {"postcode": ["We do not deliver to this area"]}}
```

Errors are reported at the failing field's path. For a `many=True` nested
field, the index of the offending row is preserved:

```python
{"items": {"1": {"postcode": ["We do not deliver to this area"]}}}
```

!!! warning "Behavioral change"
    Before this was fixed, nested Contracts were validated *structurally only* —
    their wards and `validate()` hook never ran. A payload that a nested
    Contract's rules should have rejected was accepted silently. If your code
    relied on that, those rules now apply.

---

## Choosing `is_sealed()` vs `is_sealed_async()`

Use `is_sealed_async()` whenever any Contract in the tree — including a nested
one — declares `@ward(mode="async")`.

```python
class UserContract(Contract):
    email = EmailFacet()

    @ward(mode="async")
    async def email_unique(self, data):
        if await User.objects.filter(email=data["email"]).exists():
            self.reject("email", "Already registered")
```

`has_async_wards` walks the whole facet tree, so it reports `True` for a
Contract whose *nested* child declares an async ward even when the outer
Contract declares none:

```python
class ProfileContract(Contract):
    user = NestedContractFacet(UserContract)   # no wards of its own

ProfileContract(data=payload).has_async_wards   # True
```

Calling the sync `is_sealed()` on such a Contract raises
`ContractAsyncMismatchFault` rather than skipping the async wards. Failing
loudly is deliberate: silently skipping a uniqueness or authorization check
would let invalid data through.

```python
contract = ProfileContract(data=payload)
if not await contract.is_sealed_async():
    return Response.json(contract.errors, status=422)
```

Bulk bodies work the same way — async wards run once per row, with errors keyed
by row index.

---

## Async serialization

Aquilia's ORM relations are asynchronous: `RelatedManager.all()` is a coroutine
and cannot be read from a synchronous method. Two options:

### Prefetch, then serialize synchronously

```python
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).to_dict()
```

An unresolved relation on the sync path raises `LensUnresolvedFault` naming the
field. It does not return an empty list — `[]` is indistinguishable from "this
record genuinely has no related rows", which ships wrong data to clients.

### Serialize asynchronously

`to_dict_async()` awaits relations as it reaches them:

```python
order = await Order.objects.get(pk=1)
data = await OrderContract(instance=order).to_dict_async()
```

Both forms are available for collections:

| Sync | Async |
| :--- | :--- |
| `contract.to_dict()` | `await contract.to_dict_async()` |
| `contract.to_dict_many(rows)` | `await contract.to_dict_many_async(rows)` |
| `Contract.to_dict(obj)` | `await Contract.to_dict_async(obj)` |

Output is identical for already-materialized data — the async variants differ
only in their ability to await.

!!! note "Performance"
    Each unresolved to-many relation costs one query at the point it is reached
    — the N+1 pattern. `to_dict_async()` makes lazy relations *correct* rather
    than an error; it does not make prefetching unnecessary. Prefer
    `prefetch_related` on list endpoints.

Rows are serialized sequentially rather than gathered concurrently: firing one
lazy-relation query per row simultaneously would exhaust the connection pool on
a large result set.

---

## Copying and updating

`copy()` derives a new Contract with fields replaced, validating by default:

```python
updated = contract.copy(update={"status": "shipped"})
```

Pass `validate=False` to build up a payload in stages, or use `copy_async()`
when the Contract has async wards:

```python
draft = contract.copy(update={"status": "draft"}, validate=False)
updated = await contract.copy_async(update={"status": "shipped"})
```

Validation is on by default because an override can violate a constraint the
original satisfied — skipping it would produce a Contract whose
`validated_data` never passed the rules it claims to enforce.
