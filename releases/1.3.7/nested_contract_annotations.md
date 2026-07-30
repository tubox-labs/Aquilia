# Type-Annotated Nested Contract Facets

Aquilia v1.3.7 updates `ContractMeta` (`aquilia.contracts.annotations`) and `NestedContractFacet` to support **standard Python type hint annotations** for nested contracts and nested contract lists.

---

## Why It Changed

Previously, defining nested contracts required explicit facet assignment syntax:

```python
class NameContract(Contract):
    first_name: str
    last_name: str

class UserRegistrationContract(Contract):
    # Old explicit syntax:
    name = NestedContractFacet(NameContract)
```

While functional, this syntax did not leverage standard Python type annotations (`typing.Annotated` or direct class annotations) and required developers to remember two distinct ways of declaring fields on Contracts.

---

## Supported Type Hint Syntaxes

In v1.3.7, `ContractMeta` introspects class type annotations and automatically converts nested contract annotations into `NestedContractFacet` instances.

### 1. Direct Contract Class Annotation

```python
class AuditUserNameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class RegistrationContract(Contract):
    # Direct Contract class annotation
    name: AuditUserNameContract
```

### 2. Explicit `NestedContractFacet[SubContract]` Annotation

```python
from aquilia.contracts import Contract, NestedContractFacet

class RegistrationContract(Contract):
    # Parameterized NestedContractFacet type annotation
    name: NestedContractFacet[AuditUserNameContract]
```

### 3. Nested Contract Lists

```python
class OrganizationContract(Contract):
    # List of nested contracts
    members: list[AuditUserNameContract]
    # Or parameterized list:
    teams: list[NestedContractFacet[TeamContract]]
```

---

## How It Works Internally

During `ContractMeta.__new__()` processing:
1. `ContractMeta` iterates over `__annotations__`.
2. If an annotation target is a subclass of `Contract` (or a `typing.get_origin()` matching `list` with a `Contract` argument), `ContractMeta` wraps the target into a `NestedContractFacet(target_contract, many=is_list)`.
3. The resulting facet is attached to `_all_facets` on the contract class, supporting full validation, sealing, and model imprinting (`contract.imprint()`).

---

## Full Code Example

```python
import typing
import uuid
from aquilia.contracts import Contract, Facet, NestedContractFacet, ward
from aquilia.contracts.transforms import strip, lower
from aquilia.models import Model
from aquilia.models.fields import UUIDField, TextField

class AddressContract(Contract):
    street: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    city: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    zip_code: typing.Annotated[str, Facet.text(min_length=5, max_length=10) >> strip]

class UserProfileContract(Contract):
    address: AddressContract
    previous_addresses: list[AddressContract]
    email: typing.Annotated[str, Facet.email() >> strip >> lower]

# Sealing and validation work seamlessly:
contract = UserProfileContract(data={
    "address": {"street": "123 Main St", "city": "Metropolis", "zip_code": "10001"},
    "previous_addresses": [
        {"street": "456 Old Rd", "city": "Gotham", "zip_code": "10002"}
    ],
    "email": "USER@EXAMPLE.COM"
})

assert contract.is_sealed()
```
