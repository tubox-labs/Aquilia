# blueprints Module

## Purpose

Model to world contracts. Use this module for request casting, response molding, validation, projections, lenses, OpenAPI schema generation, and model imprinting.

## Source Coverage

- Python files: 9
- Public classes: 41
- Dataclasses: 0
- Enums: 0
- Public functions: 10

## How It Fits In Aquilia

1. Declare facets with Python annotations or explicit Facet objects.
2. Instantiate with inbound data, call is_sealed or is_sealed_async, then read validated_data.
3. Use mold for outbound data, projections for thin views, and imprint when creating or updating model objects.

## Practical Guidance

- Blueprints reject unsafe input shapes and protect against large body, recursive JSON, and many-item cases. Prefer Spec.extra_fields = "reject" for write APIs.
- Use async validation through is_sealed_async whenever a seal method is async.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `Field` | `aquilia/blueprints/annotations.py` | Constraint descriptor for annotation-driven Blueprint fields. |
| `NestedBlueprintFacet` | `aquilia/blueprints/annotations.py` | A Facet that delegates validation to a nested Blueprint. |
| `LazyBlueprintFacet` | `aquilia/blueprints/annotations.py` | A Facet that delays resolution of a Blueprint class via its string name. |
| `BlueprintMeta` | `aquilia/blueprints/core.py` | Metaclass for Blueprint classes. |
| `Blueprint` | `aquilia/blueprints/core.py` | The Blueprint -- a contract between a Model and the outside world. |
| `BlueprintFault` | `aquilia/blueprints/exceptions.py` | Base fault for all Blueprint errors. |
| `CastFault` | `aquilia/blueprints/exceptions.py` | Raised when incoming data cannot be cast to the expected type. |
| `SealFault` | `aquilia/blueprints/exceptions.py` | Raised when a validation seal is broken. |
| `ImprintFault` | `aquilia/blueprints/exceptions.py` | Raised when a write (imprint) operation fails. |
| `ProjectionFault` | `aquilia/blueprints/exceptions.py` | Raised when an invalid projection is requested. |
| `LensDepthFault` | `aquilia/blueprints/exceptions.py` | Raised when Lens traversal exceeds maximum depth. |
| `LensCycleFault` | `aquilia/blueprints/exceptions.py` | Raised when a circular Lens reference is detected. |
| `Facet` | `aquilia/blueprints/facets.py` | Base facet -- a single data point in a Blueprint. |
| `TextFacet` | `aquilia/blueprints/facets.py` | Text/string facet with length constraints. |
| `EmailFacet` | `aquilia/blueprints/facets.py` | Email address facet with format validation. |
| `URLFacet` | `aquilia/blueprints/facets.py` | URL facet with format validation. |
| `SlugFacet` | `aquilia/blueprints/facets.py` | URL slug facet (lowercase alphanumeric + hyphens). |
| `IPFacet` | `aquilia/blueprints/facets.py` | IP address facet (v4 or v6). |
| `IntFacet` | `aquilia/blueprints/facets.py` | Integer facet with range constraints. |
| `FloatFacet` | `aquilia/blueprints/facets.py` | Floating-point facet. |
| `DecimalFacet` | `aquilia/blueprints/facets.py` | Decimal facet with precision constraints. |
| `BoolFacet` | `aquilia/blueprints/facets.py` | Boolean facet with truthy/falsy coercion. |
| `DateFacet` | `aquilia/blueprints/facets.py` | Date facet (ISO 8601). |
| `TimeFacet` | `aquilia/blueprints/facets.py` | Time facet (ISO 8601). |
| `DateTimeFacet` | `aquilia/blueprints/facets.py` | DateTime facet (ISO 8601). |
| `DurationFacet` | `aquilia/blueprints/facets.py` | Duration/timedelta facet. |
| `UUIDFacet` | `aquilia/blueprints/facets.py` | UUID facet. |
| `ListFacet` | `aquilia/blueprints/facets.py` | List/array facet with optional child facet. |
| `DictFacet` | `aquilia/blueprints/facets.py` | Dictionary/object facet, optionally validating all values against a specific facet. |
| `JSONFacet` | `aquilia/blueprints/facets.py` | Arbitrary JSON facet with configurable depth and type restrictions. |
| `FileFacet` | `aquilia/blueprints/facets.py` | File reference facet -- stores path/URL string. |
| `ChoiceFacet` | `aquilia/blueprints/facets.py` | Facet with a fixed set of allowed values. |
| `PolymorphicFacet` | `aquilia/blueprints/facets.py` | A Facet that attempts to cast and seal through multiple candidate Facets. |
| `Computed` | `aquilia/blueprints/facets.py` | A facet whose value is computed at output time -- never accepted as input. |
| `Constant` | `aquilia/blueprints/facets.py` | A facet that always returns a fixed value -- useful for type |
| `WriteOnly` | `aquilia/blueprints/facets.py` | Convenience: a text facet that is write-only (e.g., passwords). |
| `ReadOnly` | `aquilia/blueprints/facets.py` | A pass-through read-only facet. |
| `Hidden` | `aquilia/blueprints/facets.py` | A hidden facet -- populated from default/DI, never in input or output. |
| `Inject` | `aquilia/blueprints/facets.py` | A facet that resolves its value from the DI container at validation time. |
| `Lens` | `aquilia/blueprints/lenses.py` | A relational facet that views related data through another Blueprint. |
| `ProjectionRegistry` | `aquilia/blueprints/projections.py` | Manages named projections for a Blueprint class. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `computed` | `aquilia/blueprints/annotations.py` | Decorator to mark a Blueprint method as a computed output field. |
| `introspect_annotations` | `aquilia/blueprints/annotations.py` | Introspect a Blueprint class's type annotations and produce Facet instances. |
| `derive_facet` | `aquilia/blueprints/facets.py` | Derive a Facet instance from an Aquilia Model field. |
| `is_blueprint_class` | `aquilia/blueprints/integration.py` | Check if an object is a Blueprint class (not instance). |
| `is_projected_blueprint` | `aquilia/blueprints/integration.py` | Check if an object is a ProjectedRef (Blueprint["projection"]). |
| `resolve_blueprint_from_annotation` | `aquilia/blueprints/integration.py` | Resolve a Blueprint class and projection from a type annotation. |
| `bind_blueprint_to_request` | `aquilia/blueprints/integration.py` | Create and validate a Blueprint from an incoming request. |
| `render_blueprint_response` | `aquilia/blueprints/integration.py` | Render data through a Blueprint for response output. |
| `generate_schema` | `aquilia/blueprints/schema.py` | Generate a JSON Schema for a Blueprint. |
| `generate_component_schemas` | `aquilia/blueprints/schema.py` | Generate OpenAPI component schemas for multiple Blueprints. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/blueprints/__init__.py` | Aquilia Blueprints -- first-class model↔world contracts. |
| `aquilia/blueprints/annotations.py` | Aquilia Blueprint Annotations -- type-annotation-driven schema declaration. |
| `aquilia/blueprints/core.py` | Aquilia Blueprint Core -- the Blueprint metaclass and base class. |
| `aquilia/blueprints/exceptions.py` | Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy. |
| `aquilia/blueprints/facets.py` | Aquilia Blueprint Facets -- the field-level primitives of a Blueprint. |
| `aquilia/blueprints/integration.py` | Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response. |
| `aquilia/blueprints/lenses.py` | Aquilia Blueprint Lenses -- depth-controlled relational views. |
| `aquilia/blueprints/projections.py` | Aquilia Blueprint Projections -- named, reusable field subsets. |
| `aquilia/blueprints/schema.py` | Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation. |

## Testing Pointers

Search `tests/` for `blueprints` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
