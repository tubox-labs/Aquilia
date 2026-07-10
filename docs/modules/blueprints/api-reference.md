# Contracts API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/contracts/__init__.py` | 162 | 0 | 0 | Aquilia Contracts -- first-class model↔world contracts. |
| `aquilia/contracts/annotations.py` | 1117 | 3 | 2 | Aquilia Contract Annotations -- type-annotation–driven schema declaration. |
| `aquilia/contracts/core.py` | 1194 | 2 | 0 | Aquilia Contract Core -- the Contract metaclass and base class. |
| `aquilia/contracts/exceptions.py` | 150 | 7 | 0 | Aquilia Contract Exceptions -- Fault-domain-integrated error hierarchy. |
| `aquilia/contracts/facets.py` | 1397 | 27 | 1 | Aquilia Contract Facets -- the field-level primitives of a Contract. |
| `aquilia/contracts/integration.py` | 293 | 0 | 5 | Aquilia Contract Integration -- hooks into Controller, DI, Request/Response. |
| `aquilia/contracts/lenses.py` | 201 | 1 | 0 | Aquilia Contract Lenses -- depth-controlled relational views. |
| `aquilia/contracts/projections.py` | 146 | 1 | 0 | Aquilia Contract Projections -- named, reusable field subsets. |
| `aquilia/contracts/schema.py` | 68 | 0 | 2 | Aquilia Contract Schema -- OpenAPI/JSON Schema generation. |

## Public Exports

`ANNOTATION_TO_FACET`, `CONTRACT`, `Contract`, `ContractFault`, `ContractMeta`, `BoolFacet`, `CastFault`, `ChoiceFacet`, `Computed`, `Constant`, `DateFacet`, `DateTimeFacet`, `DecimalFacet`, `DictFacet`, `DurationFacet`, `EmailFacet`, `Facet`, `Field`, `FileFacet`, `FloatFacet`, `Hidden`, `IPFacet`, `ImprintFault`, `Inject`, `IntFacet`, `JSONFacet`, `LazyContractFacet`, `Lens`, `LensCycleFault`, `LensDepthFault`, `ListFacet`, `MODEL_FIELD_TO_FACET`, `NestedContractFacet`, `ProjectionFault`, `ProjectionRegistry`, `ReadOnly`, `SealFault`, `SlugFacet`, `TextFacet`, `TimeFacet`, `UNSET`, `URLFacet`, `UUIDFacet`, `WriteOnly`, `_contract_registry`, `bind_contract_to_request`, `computed`, `derive_facet`, `generate_component_schemas`, `generate_schema`, `introspect_annotations`, `is_contract_class`, `is_projected_contract`, `render_contract_response`, `resolve_contract_from_annotation`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `Field` | `aquilia/contracts/annotations.py` | object | Constraint descriptor for annotation-driven Contract fields. |
| `NestedContractFacet` | `aquilia/contracts/annotations.py` | Facet | A Facet that delegates validation to a nested Contract. |
| `LazyContractFacet` | `aquilia/contracts/annotations.py` | Facet | A Facet that delays resolution of a Contract class via its string name. Used for self-referential tree structures or forward references. |
| `ContractMeta` | `aquilia/contracts/core.py` | type | Metaclass for Contract classes. |
| `Contract` | `aquilia/contracts/core.py` | Generic[ModelT] | The Contract -- a contract between a Model and the outside world. |
| `ContractFault` | `aquilia/contracts/exceptions.py` | Fault | Base fault for all Contract errors. |
| `CastFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when incoming data cannot be cast to the expected type. |
| `SealFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when a validation seal is broken. |
| `ImprintFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when a write (imprint) operation fails. |
| `ProjectionFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when an invalid projection is requested. |
| `LensDepthFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when Lens traversal exceeds maximum depth. |
| `LensCycleFault` | `aquilia/contracts/exceptions.py` | ContractFault | Raised when a circular Lens reference is detected. |
| `Facet` | `aquilia/contracts/facets.py` | object | Base facet -- a single data point in a Contract. |
| `TextFacet` | `aquilia/contracts/facets.py` | Facet | Text/string facet with length constraints. |
| `EmailFacet` | `aquilia/contracts/facets.py` | TextFacet | Email address facet with format validation. |
| `URLFacet` | `aquilia/contracts/facets.py` | TextFacet | URL facet with format validation. |
| `SlugFacet` | `aquilia/contracts/facets.py` | TextFacet | URL slug facet (lowercase alphanumeric + hyphens). |
| `IPFacet` | `aquilia/contracts/facets.py` | TextFacet | IP address facet (v4 or v6). |
| `IntFacet` | `aquilia/contracts/facets.py` | Facet | Integer facet with range constraints. |
| `FloatFacet` | `aquilia/contracts/facets.py` | Facet | Floating-point facet. |
| `DecimalFacet` | `aquilia/contracts/facets.py` | Facet | Decimal facet with precision constraints. |
| `BoolFacet` | `aquilia/contracts/facets.py` | Facet | Boolean facet with truthy/falsy coercion. |
| `DateFacet` | `aquilia/contracts/facets.py` | Facet | Date facet (ISO 8601). |
| `TimeFacet` | `aquilia/contracts/facets.py` | Facet | Time facet (ISO 8601). |
| `DateTimeFacet` | `aquilia/contracts/facets.py` | Facet | DateTime facet (ISO 8601). |
| `DurationFacet` | `aquilia/contracts/facets.py` | Facet | Duration/timedelta facet. |
| `UUIDFacet` | `aquilia/contracts/facets.py` | Facet | UUID facet. |
| `ListFacet` | `aquilia/contracts/facets.py` | Facet | List/array facet with optional child facet. |
| `DictFacet` | `aquilia/contracts/facets.py` | Facet | Dictionary/object facet, optionally validating all values against a specific facet. |
| `JSONFacet` | `aquilia/contracts/facets.py` | Facet | Arbitrary JSON facet with configurable depth and type restrictions. |
| `FileFacet` | `aquilia/contracts/facets.py` | Facet | File reference facet -- stores path/URL string. |
| `ChoiceFacet` | `aquilia/contracts/facets.py` | Facet | Facet with a fixed set of allowed values. |
| `PolymorphicFacet` | `aquilia/contracts/facets.py` | Facet | A Facet that attempts to cast and seal through multiple candidate Facets. Useful for Union types like `Union[CatContract, DogContract]`. |
| `Computed` | `aquilia/contracts/facets.py` | Facet | A facet whose value is computed at output time -- never accepted as input. |
| `Constant` | `aquilia/contracts/facets.py` | Facet | A facet that always returns a fixed value -- useful for type discriminators, API versioning, etc. |
| `WriteOnly` | `aquilia/contracts/facets.py` | TextFacet | Convenience: a text facet that is write-only (e.g., passwords). |
| `ReadOnly` | `aquilia/contracts/facets.py` | Facet | A pass-through read-only facet. |
| `Hidden` | `aquilia/contracts/facets.py` | Facet | A hidden facet -- populated from default/DI, never in input or output. |
| `Inject` | `aquilia/contracts/facets.py` | Facet | A facet that resolves its value from the DI container at validation time. |
| `Lens` | `aquilia/contracts/lenses.py` | Facet | A relational facet that views related data through another Contract. |
| `ProjectionRegistry` | `aquilia/contracts/projections.py` | object | Manages named projections for a Contract class. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `computed` | `aquilia/contracts/annotations.py` | `def computed(func: Callable)` | Decorator to mark a Contract method as a computed output field. |
| `introspect_annotations` | `aquilia/contracts/annotations.py` | `def introspect_annotations(cls: type, namespace: dict[str, Any], bases: tuple, *, include_explicit_facets: bool=False)` | Introspect a Contract class's type annotations and produce Facet instances. |
| `derive_facet` | `aquilia/contracts/facets.py` | `def derive_facet(model_field: Any)` | Derive a Facet instance from an Aquilia Model field. |
| `is_contract_class` | `aquilia/contracts/integration.py` | `def is_contract_class(obj: Any)` | Check if an object is a Contract class (not instance). |
| `is_projected_contract` | `aquilia/contracts/integration.py` | `def is_projected_contract(obj: Any)` | Check if an object is a ProjectedRef (Contract["projection"]). |
| `resolve_contract_from_annotation` | `aquilia/contracts/integration.py` | `def resolve_contract_from_annotation(annotation: Any)` | Resolve a Contract class and projection from a type annotation. |
| `bind_contract_to_request` | `aquilia/contracts/integration.py` | `async def bind_contract_to_request(contract_cls: type[Contract], request: Any, *, projection: str \| None=None, partial: bool=False, context: dict[str, Any] \| None=None)` | Create and validate a Contract from an incoming request. |
| `render_contract_response` | `aquilia/contracts/integration.py` | `def render_contract_response(contract_or_cls: Contract \| type[Contract], data: Any=None, *, projection: str \| None=None, many: bool=False)` | Render data through a Contract for response output. |
| `generate_schema` | `aquilia/contracts/schema.py` | `def generate_schema(contract_cls: type[Contract], *, projection: str \| None=None, mode: str='output')` | Generate a JSON Schema for a Contract. |
| `generate_component_schemas` | `aquilia/contracts/schema.py` | `def generate_component_schemas(*contract_classes: type[Contract], include_projections: bool=True)` | Generate OpenAPI component schemas for multiple Contracts. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `ANNOTATION_TO_FACET` | `aquilia/contracts/annotations.py` | `dict[type, type[Facet]]` |
| `CONTRACT` | `aquilia/contracts/exceptions.py` | `FaultDomain(name='CONTRACT', description='Contract contract violations -- casting, sealing, imprinting')` |
| `UNSET` | `aquilia/contracts/facets.py` | `_Unset()` |
| `MODEL_FIELD_TO_FACET` | `aquilia/contracts/facets.py` | `dict[str, type[Facet]]` |
| `MAX_BODY_SIZE` | `aquilia/contracts/integration.py` | `int` |
| `MAX_UNFLATTEN_DEPTH` | `aquilia/contracts/integration.py` | `int` |
| `MAX_UNFLATTEN_KEYS` | `aquilia/contracts/integration.py` | `int` |

## Detailed Classes And Methods

### `Field`

- Source: `aquilia/contracts/annotations.py`
- Bases: `object`
- Summary: Constraint descriptor for annotation-driven Contract fields.

### `NestedContractFacet`

- Source: `aquilia/contracts/annotations.py`
- Bases: `Facet`
- Summary: A Facet that delegates validation to a nested Contract.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `MAX_NESTING_DEPTH` | `` | `32` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `target` | `def target(self)` |  |
| `cast` | `def cast(self, value: Any)` | Cast input through the nested Contract's seal pipeline. |
| `seal` | `def seal(self, value: Any)` | Already validated during cast -- pass through. |
| `mold` | `def mold(self, value: Any)` | Mold output through the nested Contract. |
| `extract` | `def extract(self, instance: Any)` | Extract the nested value from a model instance. |
| `to_schema` | `def to_schema(self)` | Generate JSON Schema with $ref to nested Contract. |

### `LazyContractFacet`

- Source: `aquilia/contracts/annotations.py`
- Bases: `Facet`
- Summary: A Facet that delays resolution of a Contract class via its string name. Used for self-referential tree structures or forward references.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `target` | `def target(self)` |  |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `extract` | `def extract(self, instance: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `ContractMeta`

- Source: `aquilia/contracts/core.py`
- Bases: `type`
- Summary: Metaclass for Contract classes.

### `Contract`

- Source: `aquilia/contracts/core.py`
- Bases: `Generic[ModelT]`
- Summary: The Contract -- a contract between a Model and the outside world.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `data` | `def data(self)` | The output representation -- molded from the instance. |
| `to_dict` | `def to_dict(self, instance: Any=None, *, _depth: int=0, _seen: set \| None=None)` | Mold a model instance into a dict, respecting projections. |
| `to_dict_many` | `def to_dict_many(self, instances: Any, *, _depth: int=0, _seen: set \| None=None)` | Mold multiple instances. |
| `is_sealed` | `def is_sealed(self, *, raise_fault: bool=False)` | Validate the input data through the full pipeline. |
| `is_sealed_async` | `async def is_sealed_async(self, *, raise_fault: bool=False)` | Async variant of is_sealed -- also runs async_seal_* methods. |
| `validate` | `def validate(self, data: dict[str, Any])` | Object-level validation hook. |
| `reject` | `def reject(self, field: str, message: str)` | Convenience method for seal methods to register a field error. |
| `validated_data` | `def validated_data(self)` | The validated data -- only available after successful sealing. |
| `errors` | `def errors(self)` | Validation errors -- available after sealing attempt. |
| `imprint` | `async def imprint(self, instance: None=None, *, partial: bool \| None=None)` |  |
| `imprint` | `async def imprint(self, instance: ModelT, *, partial: bool \| None=None)` |  |
| `imprint` | `async def imprint(self, instance: list[ModelT], *, partial: bool \| None=None)` |  |
| `imprint` | `async def imprint(self, instance: ModelT \| list[ModelT] \| None=None, *, partial: bool \| None=None)` | Write validated data back to a model instance. |
| `to_schema` | `def to_schema(cls, *, projection: str \| None=None, mode: str='output')` | Generate JSON Schema for this Contract. |
| `facet_names` | `def facet_names(cls, *, projection: str \| None=None)` | List facet names, optionally filtered by projection. |
| `get_facet` | `def get_facet(cls, name: str)` | Get a facet by name. |

### `ContractFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `Fault`
- Summary: Base fault for all Contract errors.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP000'` |
| `public` | `` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_response_body` | `def as_response_body(self)` | Structured error payload for API responses. |

### `CastFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when incoming data cannot be cast to the expected type.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP100'` |

### `SealFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when a validation seal is broken.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP200'` |

### `ImprintFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when a write (imprint) operation fails.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP300'` |

### `ProjectionFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when an invalid projection is requested.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP400'` |

### `LensDepthFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when Lens traversal exceeds maximum depth.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP500'` |

### `LensCycleFault`

- Source: `aquilia/contracts/exceptions.py`
- Bases: `ContractFault`
- Summary: Raised when a circular Lens reference is detected.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BP501'` |

### `Facet`

- Source: `aquilia/contracts/facets.py`
- Bases: `object`
- Summary: Base facet -- a single data point in a Contract.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `required` | `def required(self)` |  |
| `required` | `def required(self, value: bool)` |  |
| `bind` | `def bind(self, name: str, contract: Contract)` | Attach this facet to a Contract with a field name. |
| `clone` | `def clone(self)` | Create a shallow copy for Contract inheritance. |
| `cast` | `def cast(self, value: Any)` | Cast an incoming value to the internal Python type. |
| `mold` | `def mold(self, value: Any)` | Shape an outgoing value for the response. |
| `seal` | `def seal(self, value: Any)` | Run all field-level validators on a cast value. |
| `extract` | `def extract(self, instance: Any)` | Extract this facet's value from a model instance. |
| `to_schema` | `def to_schema(self)` | Generate JSON Schema for this facet. |
| `write_only` | `def write_only(cls, **kwargs)` | Factory: create a write-only facet. |
| `read_only` | `def read_only(cls, **kwargs)` | Factory: create a read-only facet. |

### `TextFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Text/string facet with length constraints.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `MAX_PATTERN_LENGTH` | `` | `500` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `EmailFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `TextFacet`
- Summary: Email address facet with format validation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `URLFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `TextFacet`
- Summary: URL facet with format validation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `SlugFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `TextFacet`
- Summary: URL slug facet (lowercase alphanumeric + hyphens).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `IPFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `TextFacet`
- Summary: IP address facet (v4 or v6).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `IntFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Integer facet with range constraints.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `FloatFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Floating-point facet.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `DecimalFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Decimal facet with precision constraints.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Decimal)` |  |
| `mold` | `def mold(self, value: Any)` | Decimals are molded to strings for JSON precision. |
| `to_schema` | `def to_schema(self)` |  |

### `BoolFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Boolean facet with truthy/falsy coercion.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |

### `DateFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Date facet (ISO 8601).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `TimeFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Time facet (ISO 8601).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `DateTimeFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: DateTime facet (ISO 8601).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `DurationFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Duration/timedelta facet.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `UUIDFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: UUID facet.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `ListFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: List/array facet with optional child facet.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: list)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `DictFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Dictionary/object facet, optionally validating all values against a specific facet.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEFAULT_MAX_KEYS` | `` | `1000` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: dict)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `JSONFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Arbitrary JSON facet with configurable depth and type restrictions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEFAULT_MAX_DEPTH` | `` | `32` |
| `JSON_SAFE_TYPES` | `` | `(str, int, float, bool, type(None), list, dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |

### `FileFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: File reference facet -- stores path/URL string.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `ChoiceFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: Facet with a fixed set of allowed values.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `PolymorphicFacet`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A Facet that attempts to cast and seal through multiple candidate Facets. Useful for Union types like `Union[CatContract, DogContract]`.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `cast` | `def cast(self, value: Any)` |  |
| `seal` | `def seal(self, value: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `Computed`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A facet whose value is computed at output time -- never accepted as input.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `extract` | `def extract(self, instance: Any)` | Compute the value from the instance. |
| `mold` | `def mold(self, value: Any)` |  |

### `Constant`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A facet that always returns a fixed value -- useful for type discriminators, API versioning, etc.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `extract` | `def extract(self, instance: Any)` |  |
| `mold` | `def mold(self, value: Any)` |  |
| `to_schema` | `def to_schema(self)` |  |

### `WriteOnly`

- Source: `aquilia/contracts/facets.py`
- Bases: `TextFacet`
- Summary: Convenience: a text facet that is write-only (e.g., passwords).

### `ReadOnly`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A pass-through read-only facet.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `mold` | `def mold(self, value: Any)` |  |

### `Hidden`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A hidden facet -- populated from default/DI, never in input or output.

### `Inject`

- Source: `aquilia/contracts/facets.py`
- Bases: `Facet`
- Summary: A facet that resolves its value from the DI container at validation time.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve_from_context` | `def resolve_from_context(self, context: dict[str, Any])` | Resolve value from DI container or context in Contract context. |

### `Lens`

- Source: `aquilia/contracts/lenses.py`
- Bases: `Facet`
- Summary: A relational facet that views related data through another Contract.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `target` | `def target(self)` |  |
| `bind` | `def bind(self, name: str, contract: Contract)` |  |
| `mold` | `def mold(self, value: Any, *, _depth: int=0, _seen: set \| None=None)` | Mold related data through the target Contract. |
| `extract` | `def extract(self, instance: Any)` | Extract related data from the instance. |
| `to_schema` | `def to_schema(self)` | Generate JSON Schema with $ref for the target Contract. |

### `ProjectionRegistry`

- Source: `aquilia/contracts/projections.py`
- Bases: `object`
- Summary: Manages named projections for a Contract class.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `configure` | `def configure(self, projections: dict[str, str \| list[str]] \| None, default: str \| None, all_facet_names: set[str], write_only_names: set[str])` | Configure projections from Spec definitions. |
| `resolve` | `def resolve(self, name: str \| None=None)` | Resolve a projection name to a set of facet names. |
| `default_name` | `def default_name(self)` |  |
| `available` | `def available(self)` |  |
