# Blueprints API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `Field` | `aquilia/blueprints/annotations.py` | object | Constraint descriptor for annotation-driven Blueprint fields. |
| `NestedBlueprintFacet` | `aquilia/blueprints/annotations.py` | Facet | A Facet that delegates validation to a nested Blueprint. |
| `LazyBlueprintFacet` | `aquilia/blueprints/annotations.py` | Facet | A Facet that delays resolution of a Blueprint class via its string name. |
| `BlueprintMeta` | `aquilia/blueprints/core.py` | type | Metaclass for Blueprint classes. |
| `Blueprint` | `aquilia/blueprints/core.py` | Generic[ModelT] | The Blueprint -- a contract between a Model and the outside world. |
| `BlueprintFault` | `aquilia/blueprints/exceptions.py` | Fault | Base fault for all Blueprint errors. |
| `CastFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when incoming data cannot be cast to the expected type. |
| `SealFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when a validation seal is broken. |
| `ImprintFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when a write (imprint) operation fails. |
| `ProjectionFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when an invalid projection is requested. |
| `LensDepthFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when Lens traversal exceeds maximum depth. |
| `LensCycleFault` | `aquilia/blueprints/exceptions.py` | BlueprintFault | Raised when a circular Lens reference is detected. |
| `Facet` | `aquilia/blueprints/facets.py` | object | Base facet -- a single data point in a Blueprint. |
| `TextFacet` | `aquilia/blueprints/facets.py` | Facet | Text/string facet with length constraints. |
| `EmailFacet` | `aquilia/blueprints/facets.py` | TextFacet | Email address facet with format validation. |
| `URLFacet` | `aquilia/blueprints/facets.py` | TextFacet | URL facet with format validation. |
| `SlugFacet` | `aquilia/blueprints/facets.py` | TextFacet | URL slug facet (lowercase alphanumeric + hyphens). |
| `IPFacet` | `aquilia/blueprints/facets.py` | TextFacet | IP address facet (v4 or v6). |
| `IntFacet` | `aquilia/blueprints/facets.py` | Facet | Integer facet with range constraints. |
| `FloatFacet` | `aquilia/blueprints/facets.py` | Facet | Floating-point facet. |
| `DecimalFacet` | `aquilia/blueprints/facets.py` | Facet | Decimal facet with precision constraints. |
| `BoolFacet` | `aquilia/blueprints/facets.py` | Facet | Boolean facet with truthy/falsy coercion. |
| `DateFacet` | `aquilia/blueprints/facets.py` | Facet | Date facet (ISO 8601). |
| `TimeFacet` | `aquilia/blueprints/facets.py` | Facet | Time facet (ISO 8601). |
| `DateTimeFacet` | `aquilia/blueprints/facets.py` | Facet | DateTime facet (ISO 8601). |
| `DurationFacet` | `aquilia/blueprints/facets.py` | Facet | Duration/timedelta facet. |
| `UUIDFacet` | `aquilia/blueprints/facets.py` | Facet | UUID facet. |
| `ListFacet` | `aquilia/blueprints/facets.py` | Facet | List/array facet with optional child facet. |
| `DictFacet` | `aquilia/blueprints/facets.py` | Facet | Dictionary/object facet, optionally validating all values against a specific facet. |
| `JSONFacet` | `aquilia/blueprints/facets.py` | Facet | Arbitrary JSON facet with configurable depth and type restrictions. |
| `FileFacet` | `aquilia/blueprints/facets.py` | Facet | File reference facet -- stores path/URL string. |
| `ChoiceFacet` | `aquilia/blueprints/facets.py` | Facet | Facet with a fixed set of allowed values. |
| `PolymorphicFacet` | `aquilia/blueprints/facets.py` | Facet | A Facet that attempts to cast and seal through multiple candidate Facets. |
| `Computed` | `aquilia/blueprints/facets.py` | Facet | A facet whose value is computed at output time -- never accepted as input. |
| `Constant` | `aquilia/blueprints/facets.py` | Facet | A facet that always returns a fixed value -- useful for type |
| `WriteOnly` | `aquilia/blueprints/facets.py` | TextFacet | Convenience: a text facet that is write-only (e.g., passwords). |
| `ReadOnly` | `aquilia/blueprints/facets.py` | Facet | A pass-through read-only facet. |
| `Hidden` | `aquilia/blueprints/facets.py` | Facet | A hidden facet -- populated from default/DI, never in input or output. |
| `Inject` | `aquilia/blueprints/facets.py` | Facet | A facet that resolves its value from the DI container at validation time. |
| `Lens` | `aquilia/blueprints/lenses.py` | Facet | A relational facet that views related data through another Blueprint. |
| `ProjectionRegistry` | `aquilia/blueprints/projections.py` | object | Manages named projections for a Blueprint class. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `computed` | `aquilia/blueprints/annotations.py` | `def computed(func: Callable) -> _ComputedMarker` | Decorator to mark a Blueprint method as a computed output field. |
| `introspect_annotations` | `aquilia/blueprints/annotations.py` | `def introspect_annotations(cls: type, namespace: dict[str, Any], bases: tuple, *, include_explicit_facets: bool = False) -> dict[str, Facet]` | Introspect a Blueprint class's type annotations and produce Facet instances. |
| `derive_facet` | `aquilia/blueprints/facets.py` | `def derive_facet(model_field: Any) -> Facet` | Derive a Facet instance from an Aquilia Model field. |
| `is_blueprint_class` | `aquilia/blueprints/integration.py` | `def is_blueprint_class(obj: Any) -> bool` | Check if an object is a Blueprint class (not instance). |
| `is_projected_blueprint` | `aquilia/blueprints/integration.py` | `def is_projected_blueprint(obj: Any) -> bool` | Check if an object is a ProjectedRef (Blueprint["projection"]). |
| `resolve_blueprint_from_annotation` | `aquilia/blueprints/integration.py` | `def resolve_blueprint_from_annotation(annotation: Any) -> tuple[type[Blueprint] &#124; None, str &#124; None]` | Resolve a Blueprint class and projection from a type annotation. |
| `bind_blueprint_to_request` | `aquilia/blueprints/integration.py` | `async def bind_blueprint_to_request(blueprint_cls: type[Blueprint], request: Any, *, projection: str &#124; None = None, partial: bool = False, context: dict[str, Any] &#124; None = None) -> Blueprint` | Create and validate a Blueprint from an incoming request. |
| `render_blueprint_response` | `aquilia/blueprints/integration.py` | `def render_blueprint_response(blueprint_or_cls: Blueprint &#124; type[Blueprint], data: Any = None, *, projection: str &#124; None = None, many: bool = False) -> Any` | Render data through a Blueprint for response output. |
| `generate_schema` | `aquilia/blueprints/schema.py` | `def generate_schema(blueprint_cls: type[Blueprint], *, projection: str &#124; None = None, mode: str = 'output') -> dict[str, Any]` | Generate a JSON Schema for a Blueprint. |
| `generate_component_schemas` | `aquilia/blueprints/schema.py` | `def generate_component_schemas(*blueprint_classes: type[Blueprint], include_projections: bool = True) -> dict[str, dict[str, Any]]` | Generate OpenAPI component schemas for multiple Blueprints. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `ANNOTATION_TO_FACET` | `aquilia/blueprints/annotations.py` | `dict[type, type[Facet]]` |
| `BLUEPRINT` | `aquilia/blueprints/exceptions.py` | `FaultDomain(name='BLUEPRINT', description='Blueprint contract violations -- casting, sealing, imprinting')` |
| `UNSET` | `aquilia/blueprints/facets.py` | `_Unset()` |
| `MODEL_FIELD_TO_FACET` | `aquilia/blueprints/facets.py` | `dict[str, type[Facet]]` |
| `MAX_BODY_SIZE` | `aquilia/blueprints/integration.py` | `int` |
| `MAX_UNFLATTEN_DEPTH` | `aquilia/blueprints/integration.py` | `int` |
| `MAX_UNFLATTEN_KEYS` | `aquilia/blueprints/integration.py` | `int` |

## Detailed Classes And Methods

### Class: `Field`

- Source: `aquilia/blueprints/annotations.py`
- Bases: `object`
- Summary: Constraint descriptor for annotation-driven Blueprint fields.

### Class: `NestedBlueprintFacet`

- Source: `aquilia/blueprints/annotations.py`
- Bases: `Facet`
- Summary: A Facet that delegates validation to a nested Blueprint.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `MAX_NESTING_DEPTH` |  | `32` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `target` | `def target(self) -> type` | property | Method. |
| `cast` | `def cast(self, value: Any) -> Any` |  | Cast input through the nested Blueprint's seal pipeline. |
| `seal` | `def seal(self, value: Any) -> Any` |  | Already validated during cast -- pass through. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Mold output through the nested Blueprint. |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Extract the nested value from a model instance. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Generate JSON Schema with $ref to nested Blueprint. |

### Class: `LazyBlueprintFacet`

- Source: `aquilia/blueprints/annotations.py`
- Bases: `Facet`
- Summary: A Facet that delays resolution of a Blueprint class via its string name.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `target` | `def target(self) -> type` | property | Method. |
| `cast` | `def cast(self, value: Any) -> Any` |  | Method. |
| `seal` | `def seal(self, value: Any) -> Any` |  | Method. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Method. |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `BlueprintMeta`

- Source: `aquilia/blueprints/core.py`
- Bases: `type`
- Summary: Metaclass for Blueprint classes.

### Class: `Blueprint`

- Source: `aquilia/blueprints/core.py`
- Bases: `Generic[ModelT]`
- Summary: The Blueprint -- a contract between a Model and the outside world.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `data` | `def data(self) -> dict[str, Any] &#124; list[dict[str, Any]]` | property | The output representation -- molded from the instance. |
| `to_dict` | `def to_dict(self, instance: Any = None, *, _depth: int = 0, _seen: set &#124; None = None) -> dict[str, Any]` |  | Mold a model instance into a dict, respecting projections. |
| `to_dict_many` | `def to_dict_many(self, instances: Any, *, _depth: int = 0, _seen: set &#124; None = None) -> list[dict[str, Any]]` |  | Mold multiple instances. |
| `is_sealed` | `def is_sealed(self, *, raise_fault: bool = False) -> bool` |  | Validate the input data through the full pipeline. |
| `is_sealed_async` | `async def is_sealed_async(self, *, raise_fault: bool = False) -> bool` |  | Async variant of is_sealed -- also runs async_seal_* methods. |
| `validate` | `def validate(self, data: dict[str, Any]) -> dict[str, Any]` |  | Object-level validation hook. |
| `reject` | `def reject(self, field: str, message: str) -> None` |  | Convenience method for seal methods to register a field error. |
| `validated_data` | `def validated_data(self) -> dict[str, Any] &#124; list[dict[str, Any]] &#124; None` | property | The validated data -- only available after successful sealing. |
| `errors` | `def errors(self) -> dict[str, list[str]]` | property | Validation errors -- available after sealing attempt. |
| `imprint` | `async def imprint(self, instance: None = None, *, partial: bool &#124; None = None) -> ModelT &#124; list[ModelT]` | overload | Method. |
| `imprint` | `async def imprint(self, instance: ModelT, *, partial: bool &#124; None = None) -> ModelT` | overload | Method. |
| `imprint` | `async def imprint(self, instance: list[ModelT], *, partial: bool &#124; None = None) -> list[ModelT]` | overload | Method. |
| `imprint` | `async def imprint(self, instance: ModelT &#124; list[ModelT] &#124; None = None, *, partial: bool &#124; None = None) -> ModelT &#124; list[ModelT]` |  | Write validated data back to a model instance. |
| `to_schema` | `def to_schema(cls, *, projection: str &#124; None = None, mode: str = 'output') -> dict[str, Any]` | classmethod | Generate JSON Schema for this Blueprint. |
| `facet_names` | `def facet_names(cls, *, projection: str &#124; None = None) -> list[str]` | classmethod | List facet names, optionally filtered by projection. |
| `get_facet` | `def get_facet(cls, name: str) -> Facet &#124; None` | classmethod | Get a facet by name. |

### Class: `BlueprintFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `Fault`
- Summary: Base fault for all Blueprint errors.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `BLUEPRINT` |
| `severity` |  | `Severity.ERROR` |
| `code` |  | `'BP000'` |
| `public` |  | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_response_body` | `def as_response_body(self) -> dict[str, Any]` |  | Structured error payload for API responses. |

### Class: `CastFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when incoming data cannot be cast to the expected type.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP100'` |

### Class: `SealFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when a validation seal is broken.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP200'` |

### Class: `ImprintFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when a write (imprint) operation fails.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP300'` |

### Class: `ProjectionFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when an invalid projection is requested.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP400'` |

### Class: `LensDepthFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when Lens traversal exceeds maximum depth.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP500'` |

### Class: `LensCycleFault`

- Source: `aquilia/blueprints/exceptions.py`
- Bases: `BlueprintFault`
- Summary: Raised when a circular Lens reference is detected.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BP501'` |

### Class: `Facet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `object`
- Summary: Base facet -- a single data point in a Blueprint.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `required` | `def required(self) -> bool` | property | Method. |
| `required` | `def required(self, value: bool) -> None` | required.setter | Method. |
| `bind` | `def bind(self, name: str, blueprint: Blueprint) -> None` |  | Attach this facet to a Blueprint with a field name. |
| `clone` | `def clone(self) -> Facet` |  | Create a shallow copy for Blueprint inheritance. |
| `cast` | `def cast(self, value: Any) -> Any` |  | Cast an incoming value to the internal Python type. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Shape an outgoing value for the response. |
| `seal` | `def seal(self, value: Any) -> Any` |  | Run all field-level validators on a cast value. |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Extract this facet's value from a model instance. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Generate JSON Schema for this facet. |
| `write_only` | `def write_only(cls, **kwargs) -> Facet` | classmethod | Factory: create a write-only facet. |
| `read_only` | `def read_only(cls, **kwargs) -> Facet` | classmethod | Factory: create a read-only facet. |

### Class: `TextFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Text/string facet with length constraints.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `MAX_PATTERN_LENGTH` |  | `500` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> str` |  | Method. |
| `seal` | `def seal(self, value: Any) -> str` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `EmailFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `TextFacet`
- Summary: Email address facet with format validation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> str` |  | Method. |
| `seal` | `def seal(self, value: Any) -> str` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `URLFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `TextFacet`
- Summary: URL facet with format validation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `seal` | `def seal(self, value: Any) -> str` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `SlugFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `TextFacet`
- Summary: URL slug facet (lowercase alphanumeric + hyphens).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> str` |  | Method. |
| `seal` | `def seal(self, value: Any) -> str` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `IPFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `TextFacet`
- Summary: IP address facet (v4 or v6).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `seal` | `def seal(self, value: Any) -> str` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `IntFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Integer facet with range constraints.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> int` |  | Method. |
| `seal` | `def seal(self, value: Any) -> int` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `FloatFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Floating-point facet.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> float` |  | Method. |
| `seal` | `def seal(self, value: Any) -> float` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `DecimalFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Decimal facet with precision constraints.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> Decimal` |  | Method. |
| `seal` | `def seal(self, value: Decimal) -> Decimal` |  | Method. |
| `mold` | `def mold(self, value: Any) -> str` |  | Decimals are molded to strings for JSON precision. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `BoolFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Boolean facet with truthy/falsy coercion.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> bool` |  | Method. |

### Class: `DateFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Date facet (ISO 8601).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> date` |  | Method. |
| `mold` | `def mold(self, value: Any) -> str &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `TimeFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Time facet (ISO 8601).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> time` |  | Method. |
| `mold` | `def mold(self, value: Any) -> str &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `DateTimeFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: DateTime facet (ISO 8601).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> datetime` |  | Method. |
| `mold` | `def mold(self, value: Any) -> str &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `DurationFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Duration/timedelta facet.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> timedelta` |  | Method. |
| `mold` | `def mold(self, value: Any) -> float &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `UUIDFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: UUID facet.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> uuid.UUID` |  | Method. |
| `mold` | `def mold(self, value: Any) -> str &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `ListFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: List/array facet with optional child facet.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> list` |  | Method. |
| `seal` | `def seal(self, value: list) -> list` |  | Method. |
| `mold` | `def mold(self, value: Any) -> list &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `DictFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Dictionary/object facet, optionally validating all values against a specific facet.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEFAULT_MAX_KEYS` |  | `1000` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> dict` |  | Method. |
| `seal` | `def seal(self, value: dict) -> dict` |  | Method. |
| `mold` | `def mold(self, value: Any) -> dict &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `JSONFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Arbitrary JSON facet with configurable depth and type restrictions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEFAULT_MAX_DEPTH` |  | `32` |
| `JSON_SAFE_TYPES` |  | `(str, int, float, bool, type(None), list, dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> Any` |  | Method. |

### Class: `FileFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: File reference facet -- stores path/URL string.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `mold` | `def mold(self, value: Any) -> str &#124; None` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `ChoiceFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: Facet with a fixed set of allowed values.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> Any` |  | Method. |
| `seal` | `def seal(self, value: Any) -> Any` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `PolymorphicFacet`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A Facet that attempts to cast and seal through multiple candidate Facets.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cast` | `def cast(self, value: Any) -> Any` |  | Method. |
| `seal` | `def seal(self, value: Any) -> Any` |  | Method. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `Computed`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A facet whose value is computed at output time -- never accepted as input.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Compute the value from the instance. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Method. |

### Class: `Constant`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A facet that always returns a fixed value -- useful for type

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Method. |
| `mold` | `def mold(self, value: Any) -> Any` |  | Method. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Method. |

### Class: `WriteOnly`

- Source: `aquilia/blueprints/facets.py`
- Bases: `TextFacet`
- Summary: Convenience: a text facet that is write-only (e.g., passwords).

### Class: `ReadOnly`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A pass-through read-only facet.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `mold` | `def mold(self, value: Any) -> Any` |  | Method. |

### Class: `Hidden`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A hidden facet -- populated from default/DI, never in input or output.

### Class: `Inject`

- Source: `aquilia/blueprints/facets.py`
- Bases: `Facet`
- Summary: A facet that resolves its value from the DI container at validation time.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve_from_context` | `def resolve_from_context(self, context: dict[str, Any]) -> Any` |  | Resolve value from DI container or context in Blueprint context. |

### Class: `Lens`

- Source: `aquilia/blueprints/lenses.py`
- Bases: `Facet`
- Summary: A relational facet that views related data through another Blueprint.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `target` | `def target(self) -> type[Blueprint] &#124; None` | property | Method. |
| `bind` | `def bind(self, name: str, blueprint: Blueprint) -> None` |  | Method. |
| `mold` | `def mold(self, value: Any, *, _depth: int = 0, _seen: set &#124; None = None) -> Any` |  | Mold related data through the target Blueprint. |
| `extract` | `def extract(self, instance: Any) -> Any` |  | Extract related data from the instance. |
| `to_schema` | `def to_schema(self) -> dict[str, Any]` |  | Generate JSON Schema with $ref for the target Blueprint. |

### Class: `ProjectionRegistry`

- Source: `aquilia/blueprints/projections.py`
- Bases: `object`
- Summary: Manages named projections for a Blueprint class.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `configure` | `def configure(self, projections: dict[str, str &#124; list[str]] &#124; None, default: str &#124; None, all_facet_names: set[str], write_only_names: set[str]) -> None` |  | Configure projections from Spec definitions. |
| `resolve` | `def resolve(self, name: str &#124; None = None) -> frozenset[str]` |  | Resolve a projection name to a set of facet names. |
| `default_name` | `def default_name(self) -> str &#124; None` | property | Method. |
| `available` | `def available(self) -> list[str]` | property | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `computed` | `aquilia/blueprints/annotations.py` | `def computed(func: Callable) -> _ComputedMarker` | Decorator to mark a Blueprint method as a computed output field. |
| `introspect_annotations` | `aquilia/blueprints/annotations.py` | `def introspect_annotations(cls: type, namespace: dict[str, Any], bases: tuple, *, include_explicit_facets: bool = False) -> dict[str, Facet]` | Introspect a Blueprint class's type annotations and produce Facet instances. |
| `derive_facet` | `aquilia/blueprints/facets.py` | `def derive_facet(model_field: Any) -> Facet` | Derive a Facet instance from an Aquilia Model field. |
| `is_blueprint_class` | `aquilia/blueprints/integration.py` | `def is_blueprint_class(obj: Any) -> bool` | Check if an object is a Blueprint class (not instance). |
| `is_projected_blueprint` | `aquilia/blueprints/integration.py` | `def is_projected_blueprint(obj: Any) -> bool` | Check if an object is a ProjectedRef (Blueprint["projection"]). |
| `resolve_blueprint_from_annotation` | `aquilia/blueprints/integration.py` | `def resolve_blueprint_from_annotation(annotation: Any) -> tuple[type[Blueprint] &#124; None, str &#124; None]` | Resolve a Blueprint class and projection from a type annotation. |
| `bind_blueprint_to_request` | `aquilia/blueprints/integration.py` | `async def bind_blueprint_to_request(blueprint_cls: type[Blueprint], request: Any, *, projection: str &#124; None = None, partial: bool = False, context: dict[str, Any] &#124; None = None) -> Blueprint` | Create and validate a Blueprint from an incoming request. |
| `render_blueprint_response` | `aquilia/blueprints/integration.py` | `def render_blueprint_response(blueprint_or_cls: Blueprint &#124; type[Blueprint], data: Any = None, *, projection: str &#124; None = None, many: bool = False) -> Any` | Render data through a Blueprint for response output. |
| `generate_schema` | `aquilia/blueprints/schema.py` | `def generate_schema(blueprint_cls: type[Blueprint], *, projection: str &#124; None = None, mode: str = 'output') -> dict[str, Any]` | Generate a JSON Schema for a Blueprint. |
| `generate_component_schemas` | `aquilia/blueprints/schema.py` | `def generate_component_schemas(*blueprint_classes: type[Blueprint], include_projections: bool = True) -> dict[str, dict[str, Any]]` | Generate OpenAPI component schemas for multiple Blueprints. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `ANNOTATION_TO_FACET` | `aquilia/blueprints/annotations.py` | `dict[type, type[Facet]]` |
| `BLUEPRINT` | `aquilia/blueprints/exceptions.py` | `FaultDomain(name='BLUEPRINT', description='Blueprint contract violations -- casting, sealing, imprinting')` |
| `UNSET` | `aquilia/blueprints/facets.py` | `_Unset()` |
| `MODEL_FIELD_TO_FACET` | `aquilia/blueprints/facets.py` | `dict[str, type[Facet]]` |
| `MAX_BODY_SIZE` | `aquilia/blueprints/integration.py` | `int` |
| `MAX_UNFLATTEN_DEPTH` | `aquilia/blueprints/integration.py` | `int` |
| `MAX_UNFLATTEN_KEYS` | `aquilia/blueprints/integration.py` | `int` |
