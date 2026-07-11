---
title: "Contract Unions"
description: "Handling polymorphic types and union schemas with ContractUnion"
icon: lucide/merge
---`ContractUnion` is a compiled discriminated union wrapper constructed via the bitwise OR (`|`) operator on Contracts. It is defined in [core.py:L676-787](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L676-787). It is designed to handle polymorphic types, polymorphic responses, and union schemas dynamically.

---

## What is ContractUnion

The [ContractUnion](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L676-787) class wraps multiple member Contracts to provide a unified validation and schema generation interface.

- **Bitwise Construction**: It is constructed when combining Contracts using the `|` operator (e.g., `UserContract | AdminContract`), which is implemented via `__or__` ([core.py:L772-775](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L772-775)) and `__ror__` ([core.py:L777-778](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L777-778)).
- **Low Memory Overhead**: Utilizes python `__slots__` containing `("members", "discriminator_field", "_dispatch")` ([core.py:L679](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L679)) to prevent dynamic dict creation.

---

## Constructor and API

### Constructor

```python
def __init__(self, members: tuple):
    self.members = members
    self.discriminator_field, self._dispatch = self._build_dispatch()
```
*Citations: [core.py:L681-683](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L681-683)*

When initialized, the union attempts to construct a dispatch mapping by locating or auto-detecting a discriminator field among its members.

### Core Methods

#### `validate(self, data: Any) -> tuple[dict, dict]`
Validates incoming data against the union's members.
- **Discriminated dispatch**: If a discriminator mapping exists, it retrieves the discriminator value from the input dictionary and routes the validation to the matching Contract's `_sigil.validate(data)` method ([core.py:L748-756](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L748-756)).
- **Try-Each Fallback**: If no discriminator mapping is defined, it loops through each member Contract, attempting validation. The first member that validates without errors is selected ([core.py:L766-769](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L766-769)). If all fail, it returns a union mismatch error ([core.py:L770](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L770)).

*Citations: [core.py:L743-770](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L743-770)*

#### `to_json_schema(self) -> dict`
Generates a JSON schema representation of the union using the `oneOf` schema combiner with all members' schemas. If a discriminator field exists, it includes OpenAPI/JSON Schema compatible discriminator mapping metadata.

*Citations: [core.py:L780-787](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L780-787)*

---

## Dispatch and Auto-Detection

The `_build_dispatch(self)` method resolves how input data is routed ([core.py:L685-741](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L685-741)):

1. **Explicit Discriminator Check**:
   First checks if any member Contract has defined an explicit discriminator via its configuration spec (`Spec.discriminator`) ([core.py:L688-692](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L688-692)).
2. **Implicit Discriminator Auto-Detection**:
   If not explicitly set, scans all facets defined in all member Contracts. It searches for a common field present across all members where:
   - The field is a `ChoiceFacet` ([core.py:L700-703](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L700-703)).
   - The allowed values of the `ChoiceFacet` across all members are completely disjoint (unique per member) ([core.py:L711-726](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L711-726)).
3. **Dispatch Table Building**:
   Maps each disjoint value to its respective member Contract class ([core.py:L728-739](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L728-739)).

!!! warning
    If no discriminator field can be found, the union falls back to try-each validation. This invokes `validate()` sequentially on each member contract, which can be computationally expensive and raises a `RuntimeWarning` ([core.py:L757-765](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/core.py#L757-765)).


---

## When to Use It

1. **Polymorphic Responses**:
   Use when your API endpoints return different schemas under different circumstances (e.g., a successful resource payload versus an error payload, or differing types of media entities).
2. **Discriminated Unions / Heterogeneous Payloads**:
   Use when parsing payloads representing different subtypes (e.g., paying via `CreditCard` versus `PayPal` in a payment payload), where a common field like `type` determines the schema.

---

## Code Example

Below is a practical example showing how to declare polymorphic models and compile them into a `ContractUnion` using the `|` operator:

```python
from typing import Literal
from aquilia.contracts import Contract
from aquilia.contracts.facets import ChoiceFacet

# 1. Define distinct polymorphic member contracts
class CreditCardPayment(Contract):
    # Kind facet with unique value triggers auto-detection
    type = ChoiceFacet(allowed_values=("credit_card",))
    card_number: str
    expiration: str

class PayPalPayment(Contract):
    type = ChoiceFacet(allowed_values=("paypal",))
    email: str

# 2. Combine contracts using the | operator
PaymentUnion = CreditCardPayment | PayPalPayment

# 3. Validation handles dispatching dynamically based on the 'type' field
errors, validated = PaymentUnion.validate({
    "type": "paypal",
    "email": "user@example.com"
})
# Successfully validated against PayPalPayment

# 4. Unknown type results in validation error
errors, validated = PaymentUnion.validate({
    "type": "bank_transfer",
    "account": "123456789"
})
# errors contains: {"type": ["Unknown discriminator value: 'bank_transfer'"]}
```
