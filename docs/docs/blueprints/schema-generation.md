---
title: "Schema Generation"
description: "Generating JSON Schema and OpenAPI schemas from Contracts"
icon: lucide/file-json
---
Aquilia provides built-in utilities to compile Contract definitions into standard OpenAPI and JSON Schema formats. This enables automated API documentation generation, client SDK generation, and request/response validation.

The schema generation core resides in [aquilia/contracts/schema.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/schema.py).

---

## Functions

### `generate_schema()`

The `generate_schema()` function generates a standard JSON Schema dictionary for a single Contract class. Under the hood, it delegates to the class method `to_schema()` on the Contract.

#### Signature
```python
def generate_schema(
    contract_cls: type[Contract],
    *,
    projection: str | None = None,
    mode: str = "output",
) -> dict[str, Any]:
```
*(Defined in [schema.py:L19-37](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/schema.py#L19-L37))*

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `contract_cls` | `type[Contract]` |  | The Contract class to generate the JSON Schema for. |
| `projection` | `str \| None` | `None` | The name of the projection to use for filtering fields. If None, the default projection/full schema is used. |
| `mode` | `"output" \| "input"` | `"output"` | Determines the context of the schema. Use "output" for serialization/response bodies and "input" for deserialization/request bodies. |


#### Output Shape
Returns a `dict[str, Any]` representing the compiled JSON Schema. For instance, a schema generated for `UserContract` with `mode="output"` will produce:
```json
{
  "type": "object",
  "properties": {
    "id": { "type": "integer" },
    "email": { "type": "string", "format": "email" },
    "name": { "type": "string" }
  },
  "required": ["id", "email"]
}
```

---

### `generate_component_schemas()`

The `generate_component_schemas()` function generates OpenAPI-compliant component schemas for a collection of Contracts. It is designed to populate the `components.schemas` block of an OpenAPI document.

#### Signature
```python
def generate_component_schemas(
    *contract_classes: type[Contract],
    include_projections: bool = True,
) -> dict[str, dict[str, Any]]:
```
*(Defined in [schema.py:L39-68](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/schema.py#L39-L68))*

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `contract_classes` | `type[Contract]` |  | A variable number of Contract classes to compile. |
| `include_projections` | `bool` | `True` | If True, separate schemas will be generated for every projection defined on the Contract classes. |


#### Output Shape
Returns a nested dictionary `dict[str, dict[str, Any]]` mapping component names to their respective JSON Schema definitions. 

For each Contract class `bp_cls` passed as input, the function generates:
1. **Default Output Schema**: Registered under `bp_cls.__name__` (using `mode="output"`).
2. **Default Input Schema**: Registered under `f"{bp_cls.__name__}_Input"` (using `mode="input"`).
3. **Projection Schemas**: If `include_projections` is `True` and the Contract class has defined projections (e.g. `_projections.available` attribute), it creates a separate schema for each named projection (excluding the special `"__all__"` projection) under the key `f"{bp_cls.__name__}_{proj_name}"` (using `mode="output"`).

!!! info
    The implementation ignores the special `"__all__"` projection name when iterating over available projections (see [schema.py:L63-64](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/schema.py#L63-L64)).


---

## Facet Schema Mapping

Contract fields are represented by `Facet` objects. When compiling schemas, the engine calls the `to_schema()` method on each field's `Facet` class to convert it into its JSON Schema equivalent.

Here is how the core facets map to JSON Schema types, mapped via their `to_schema()` definitions (compiled from [.cache/index_contracts.json](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/.cache/index_contracts.json)):

| Facet / Class Name | Method Location | JSON Schema Representation |
| :--- | :--- | :--- |
| `Facet` | [facets.py:L396-409](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L396-L409) | Base class schema logic, sets common attributes like description, title, default values. |
| `TextFacet` | [facets.py:L532-540](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L532-L540) | `{"type": "string"}` (optionally with `minLength`, `maxLength`, `pattern`). |
| `EmailFacet` | [facets.py:L557-560](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L557-L560) | `{"type": "string", "format": "email"}`. |
| `URLFacet` | [facets.py:L579-582](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L579-L582) | `{"type": "string", "format": "uri"}`. |
| `SlugFacet` | [facets.py:L599-602](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L599-L602) | `{"type": "string", "format": "slug"}` (with slug character patterns). |
| `IPFacet` | [facets.py:L617-620](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L617-L620) | `{"type": "string", "format": "ipv4"}` or `{"format": "ipv6"}`. |
| `IntFacet` | [facets.py:L662-670](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L662-L670) | `{"type": "integer"}` (optionally with `minimum`, `maximum`). |
| `FloatFacet` | [facets.py:L718-726](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L718-L726) | `{"type": "number"}`. |
| `DecimalFacet` | [facets.py:L780-783](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L780-L783) | `{"type": "string", "format": "decimal"}`. |
| `DateFacet` | [facets.py:L841-844](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L841-L844) | `{"type": "string", "format": "date"}`. |
| `DateTimeFacet` | [facets.py:L900-903](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L900-L903) | `{"type": "string", "format": "date-time"}`. |
| `TimeFacet` | [facets.py:L869-872](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L869-L872) | `{"type": "string", "format": "time"}`. |
| `DurationFacet` | [facets.py:L944-947](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L944-L947) | `{"type": "number", "format": "duration"}` (represented as seconds). |
| `UUIDFacet` | [facets.py:L968-971](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L968-L971) | `{"type": "string", "format": "uuid"}`. |
| `ListFacet` | [facets.py:L1032-1040](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1032-L1040) | `{"type": "array", "items": {...}}`. |
| `SetFacet` | [facets.py:L1098-1107](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1098-L1107) | `{"type": "array", "uniqueItems": true, "items": {...}}`. |
| `TupleFacet` | [facets.py:L1165-1173](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1165-L1173) | `{"type": "array", "prefixItems": [...], "minItems": N, "maxItems": N}`. |
| `DictFacet` | [facets.py:L1254-1258](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1254-L1258) | `{"type": "object", "properties": {...}}`. |
| `ChoiceFacet` | [facets.py:L1375-1378](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1375-L1378) | `{"enum": [...]}` mapping allowed literal values. |
| `EnumFacet` | [facets.py:L1443-1455](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1443-L1455) | `{"enum": [...]}` mapping python Enum member values. |
| `Constant` | [facets.py:L1604-1607](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1604-L1607) | `{"const": value}`. |
| `FormDataFacet` | [facets.py:L1863-1866](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1863-L1866) | Multi-part form-data schema mappings. |
| `UploadFileFacet` | [facets.py:L1813-1817](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1813-L1817) | Binary file payload schema mapping (`{"type": "string", "format": "binary"}`). |

---

## Nested Contracts and $ref Generation (Lens)

Aquilia ensures schema modularity and prevents infinite recursion using JSON Schema `$ref` pointers.

### Nested Contract Facets

For direct inclusion of a sub-contract within a parent contract, the compiler uses `NestedContractFacet` or `LazyContractFacet`:
* **`NestedContractFacet`**: Handles statically imported nested Contracts (defined in [annotations.py:L310-473](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L310-L473), with `to_schema()` defined at [L465-473](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L465-L473)).
* **`LazyContractFacet`**: Handles lazy-loaded/forward-referenced nested Contracts by name (defined in [annotations.py:L479-545](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L479-L545), with `to_schema()` defined at [L544-545](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/annotations.py#L544-L545)).

During schema compilation, these facets generate schema references (such as `{"$ref": "#/components/schemas/NestedContractName"}`) to modularize the resulting JSON document.

### Relationships via Lens

A `Lens` represents a relationship/link to another Contract class (defined in [lenses.py:L26-184](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/lenses.py#L26-L184)).

Rather than inline-compiling the target Contract schema directly into the parent model, the `Lens.to_schema()` method (defined at [lenses.py:L170-184](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/lenses.py#L170-L184)) references the target Contract by outputting a `$ref` pointing to its registered component schema:

```json
{
  "type": "object",
  "properties": {
    "author": {
      "$ref": "#/components/schemas/AuthorContract"
    }
  }
}
```

#### Cycle Detection and Depth Control
Because relations between contracts can form cyclical references, Aquilia employs safeguard mechanisms:
* **`LensCycleFault`** (defined in [exceptions.py:L141-150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/exceptions.py#L141-L150)): Raised when a cyclical relationship loop is detected without appropriate projection boundaries.
* **`LensDepthFault`** (defined in [exceptions.py:L129-138](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/exceptions.py#L129-L138)): Raised when nesting/relation depth exceeds the maximum configured threshold.
