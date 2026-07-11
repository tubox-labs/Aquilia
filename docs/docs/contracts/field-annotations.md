---
title: "Field Annotations & Computed Fields"
description: "Annotation-driven validation styles and computed fields using @computed and Field()"
icon: lucide/hash
---Aquilia Contracts provide a first-class, type-annotation-driven system that allows declaring schemas using standard Python type annotations. This system is entirely native to Aquilia, requiring no external validation libraries like Pydantic ([annotations.py:L4-6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L4-6)).

---

## Annotation-Driven Style vs Explicit Facets

When defining contracts in Aquilia, you can use two main declaration styles:
1. **Annotation-Driven Style**: Fields are declared using standard Python type annotations alongside the [Field](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L111) descriptor or raw defaults ([annotations.py:L12-19](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L12-19)).
2. **Explicit Facet Style**: Fields are declared by instantiating Facet objects directly in the class namespace.

### Syntax Comparison

```python
from aquilia.contracts import Contract, Field, computed
from aquilia.contracts.facets import TextFacet, IntFacet

# 1. Annotation-driven style
class UserContract(Contract):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=150)
    role: str = "user"  # raw default value

# 2. Explicit facet style
class LegacyUserContract(Contract):
    name = TextFacet(min_length=2, max_length=100)
    age = IntFacet(min_value=0, max_value=150)
    role = TextFacet(default="user")
```

---

## ANNOTATION_TO_FACET Mapping

The introspection engine utilizes the [ANNOTATION_TO_FACET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L87) lookup dictionary to map Python type annotations to native Aquilia Facets ([annotations.py:L87-106](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L87-106)):

| Python Type | Target Aquilia Facet Class |
| :--- | :--- |
| `str` | [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L463-L540) |
| `int` | [IntFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L626-L670) |
| `float` | [FloatFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L673-L726) |
| `bool` | [BoolFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L789-L811) |
| `Decimal` | [DecimalFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L729-L783) |
| `datetime` | [DateTimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L875-L903) |
| `date` | [DateFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L817-L844) |
| `time` | [TimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L847-L872) |
| `timedelta` | [DurationFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L906-L947) |
| `uuid.UUID` | [UUIDFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L950-L971) |
| `dict` | [DictFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1176-L1258) |
| `list` | [ListFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L977-L1040) |
| `set` | [SetFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1043-L1107) |
| `tuple` | [TupleFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1110-L1173) |
| `bytes` | [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L463-L540) |
| `UploadFile` | [UploadFileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1745-L1817) |
| `FormData` | [FormDataFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1820-L1866) |

---

## Field() Descriptor

The [Field](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L111) descriptor class supplies metadata and constraints for annotation-driven fields ([annotations.py:L111-260](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L111-260)).

### Parameters & Configuration

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `default` | `Any` | `UNSET` | Static default value for the field. |
| `default_factory` | `Callable \| None` | `None` | A zero-argument callable that dynamically produces the default value. |
| `required` | `bool \| None` | `None` | Explicit override to force or waive validation requirements. |
| `read_only` | `bool` | `False` | When True, the field is output-only and excluded from incoming payloads. |
| `write_only` | `bool` | `False` | When True, the field is input-only and excluded from serialized output. |
| `allow_null` | `bool` | `False` | Allows the field to accept None as a valid input value. |
| `allow_blank` | `bool` | `False` | Allows text fields to accept empty strings. |
| `source` | `str \| None` | `None` | Path/key mapping override on the underlying model instance. |
| `label` | `str \| None` | `None` | Human-readable label for documentation and UI. |
| `help_text` | `str \| None` | `None` | Documentation helper string. |
| `validators` | `Sequence[Callable] \| None` | `None` | List of custom validation callables to execute. |
| `ge` | `int \| float \| None` | `None` | Greater-than-or-equal (minimum value) constraint for numeric fields. |
| `le` | `int \| float \| None` | `None` | Less-than-or-equal (maximum value) constraint for numeric fields. |
| `gt` | `int \| float \| None` | `None` | Strictly greater-than constraint. |
| `lt` | `int \| float \| None` | `None` | Strictly less-than constraint. |
| `min_length` | `int \| None` | `None` | Minimum string length constraint. |
| `max_length` | `int \| None` | `None` | Maximum string length constraint. |
| `pattern` | `str \| None` | `None` | Regular expression pattern that string values must match. |
| `min_items` | `int \| None` | `None` | Minimum size constraint for collections (lists, tuples, sets). |
| `max_items` | `int \| None` | `None` | Maximum size constraint for collections (lists, tuples, sets). |
| `choices` | `Sequence \| None` | `None` | Enumerated sequence of allowed values. |
| `max_digits` | `int \| None` | `None` | Maximum total digits allowed in a Decimal. |
| `decimal_places` | `int \| None` | `None` | Maximum decimal places allowed in a Decimal. |
| `alias` | `str \| None` | `None` | Alternative key name used during incoming payload parsing. |


### Critical Validation Rules

* **Mutually Exclusive Defaults**: You cannot specify both `default` and `default_factory`. Attempting to do so raises a `ConfigInvalidFault` ([annotations.py:L216-222](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L216-222)).
* **Creation Ordering**: The descriptor tracks its instantiation order using a class-level counter `_creation_counter`. This maintains declaration order in the final contract schemas ([annotations.py:L157-158](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L157-158), [L249-250](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L249-250)).

---

## @computed Decorator

The [@computed](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L568) decorator marks a contract method as an output-only computed field ([annotations.py:L568-585](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L568-585)).

* **Under the Hood**: The decorator wraps the function in a `[_ComputedMarker](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L551)` ([annotations.py:L551-565](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L551-565)).
* **Facet Conversion**: During class introspection, markers are converted into a `Computed` facet ([annotations.py:L561-565](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L561-565)).
* **Behavior**: Methods decorated with `@computed` are read-only, never accepted as inputs, and receive `(self, instance)` parameters to evaluate their return value ([annotations.py:L570-573](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L570-573)).

```python
class ProfileContract(Contract):
    first_name: str
    last_name: str

    @computed
    def display_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"
```

---

## NestedContractFacet

The [NestedContractFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L310) delegates validation, casting, and output molding directly to another nested Contract class ([annotations.py:L310-473](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L310-473)).

* **Instantiation**: Supports class indexing syntax `NestedContractFacet[ChildContract]` or `NestedContractFacet[ChildContract, True]` (sets `many=True`) through `__class_getitem__` ([annotations.py:L342-364](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L342-364)).
* **Array Support**: Setting `many=True` handles validation and serialization of lists of nested contracts (`_cast_many`) ([annotations.py:L333](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L333), [L402-425](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L402-425)).
* **Stack Overflow Prevention**: Imposes a recursion guard using a thread-local counter `_current_nesting_depth` and a configurable limit `MAX_NESTING_DEPTH = 32`. Exceeding this depth raises a `CastFault` ([annotations.py:L323-327](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L323-327), [L372-384](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L372-384)).
* **Schema Generation**: Automatically produces JSON schemas containing `$ref` pointing to `#/components/schemas/{NestedContractName}` ([annotations.py:L465-473](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L465-473)).

---

## LazyContractFacet

The [LazyContractFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L479) acts as a placeholder that delays the resolution of a nested Contract class via its string reference name ([annotations.py:L479-547](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L479-547)).

* **Use Cases**: Critical for self-referential tree structures or forward references to contracts defined later in the module ([annotations.py:L481-483](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L481-483)).
* **Resolution**: Queries the global `_contract_registry` during the casting/validation phase. If the name is unresolved, it raises a `RegistryFault` ([annotations.py:L497-507](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L497-507)).
* **Mapping Promotion**: Once resolved, it instantiates and caches an underlying [NestedContractFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L310) and merges validator lists ([annotations.py:L519-526](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L519-526)).

---

## introspect_annotations()

The [introspect_annotations](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L1224) function parses class-level type annotations and transforms them into concrete Facet structures ([annotations.py:L1224-1416](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L1224-1416)).

* **Resolution Scope**: Resolves string-based type annotations (PEP 563) by evaluating expressions against standard typing namespaces, the defining module's globals, class namespace, and parent MRO class frames ([annotations.py:L1280-1337](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L1280-1337)).
* **AST Parsing & Safety**: Leverages `_safe_resolve_annotation` ([annotations.py:L656-730](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L656-730)) to parse generic subscripts (e.g. `list[str]`, `dict[str, int]`) and PEP 604 unions without falling back to standard `eval()`, preventing potential security risks.
* **Fallback Sentinel**: Uses `AutoResolveMapping` ([annotations.py:L1274-1279](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L1274-1279)) to convert unknown symbols into `ForwardRef` objects dynamically during runtime resolution.

---

## Optional Fields

Optional properties are represented by annotations wrapped in `typing.Optional[T]` or using PEP 604 `T | None` union syntax.

* **Unwrapping**: The helper [\_unwrap_optional](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L755) decomposes the union, extracting the inner type and returning a boolean flag indicating optional status ([annotations.py:L755-788](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L755-788)).
* **Introspection Behavior**: When `_unwrap_optional` flags a field as optional, the introspection engine automatically overrides its constraints to set `allow_null=True` and `required=False` ([annotations.py:L988-991](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L988-991)).

---

## Code Examples

### Full Declaration Example

Here is a contract using custom fields, constrained scalars, computed properties, and nested relationships:

```python
from decimal import Decimal
from uuid import UUID
from aquilia.contracts import Contract, Field, computed

class AddressContract(Contract):
    street: str
    city: str
    postal_code: str = Field(pattern=r"^\d{5}$")

class CompanyContract(Contract):
    # Scalar Mapping
    company_id: UUID
    name: str = Field(min_length=2, max_length=150)
    
    # Optional field (sets allow_null=True and required=False)
    description: str | None = None
    
    # Nested single and multiple contracts
    hq_address: AddressContract
    branches: list[AddressContract] = Field(default_factory=list)
    
    # Constrained Decimal
    annual_revenue: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    
    # Constrained choices
    status: str = Field(default="active", choices=["active", "inactive", "suspended"])

    @computed
    def is_enterprise(self, instance) -> bool:
        return instance.annual_revenue > Decimal("10000000.00")
```
