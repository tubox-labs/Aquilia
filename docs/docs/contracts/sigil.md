---
title: "Sigil & FieldSpec"
description: "Understanding the Sigil pattern and FieldSpec configuration in Contracts"
icon: lucide/stamp
---## Overview

A **Sigil** is the compiled, immutable representation of a Contract validation schema ([sigil.py:L4-6, L102](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L4-L6)). It is compiled exactly once per Contract class definition and cached as `cls._sigil` ([sigil.py:L4](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L4)).

A **FieldSpec** represents the compiled specification of a single field within the Sigil schema ([sigil.py:L64](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L64)).

---

## Relationship to Contract Field Declarations

When a Contract class is defined, the compilation process constructs a `Sigil` using [build_sigil](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L939-L981):

1. **Facet Processing**: The compiler iterates over the facets found in `cls._all_facets.items()` ([sigil.py:L945](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L945)).
2. **Metadata Flags**:
   - It checks whether each facet wraps a nested Contract (`NestedContractFacet` or `LazyContractFacet`) ([sigil.py:L946](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L946)).
   - It determines if a facet represents a Lens field (`Lens`) ([sigil.py:L947](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L947)).
3. **Pipeline Extraction**: It extracts any pipeline configurations registered during annotations parsing (`getattr(facet, "_pipeline", None)`) ([sigil.py:L950](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L950)).
4. **FieldSpec Construction**: It builds a [FieldSpec](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L63-L99) mapping for the field name with all validation parameters (facet constraints, defaults, pipelines, etc.) ([sigil.py:L952-L961](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L952-L961)).
5. **Schema Spec Mapping**: It reads schema-level specifications from `cls._spec` ([sigil.py:L964-L969](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L964-L969)):
   - `strict`: Whether validation operates in strict mode by default.
   - `revision`: Schema revision identifier.
   - `migrate_from`: Map of prior schema revisions to migration callbacks.
   - `migrate_step`: Sequence-based migration callback on `cls`.
   - `discriminator`: Field name denoting polymorphic schema variants.
6. **Ward Methods**: It extracts custom validations registered as `_ward_methods` ([sigil.py:L971](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L971)).

> [!NOTE]
> **Unknown from inspected source**:
> - How Contract metaclass class creation hooks (e.g. `__new__`) parse fields and facets, and trigger `build_sigil`.
> - How the fields are initialized, how `cls._all_facets`, `cls._spec`, and `cls._ward_methods` are populated, or how the `_sigil` attribute is attached back to `cls`.
> - How internal classes/facets like `NestedContractFacet`, `LazyContractFacet`, `Lens`, `Pipeline`, and `CastFault` are defined and function.

---

## FieldSpec API

The [FieldSpec](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L63-L99) class uses `__slots__` optimization ([sigil.py:L66-L75](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L66-L75)) and exposes the following parameters via its constructor ([sigil.py:L77-L95](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L77-L95)):

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` |  | The field name defined in the Contract schema. |
| `facet` | `Any` |  | The compiled field constraint constraints (e.g. a validation Facet). |
| `required` | `bool` |  | Denotes whether the field is required. |
| `default` | `Any` |  | Static default value when the field is omitted. |
| `default_factory` | `Any` |  | A callable factory returning dynamic default values. |
| `pipeline` | `Pipeline \| None` |  | Optional transformation pipeline of runes executed on the field value. |
| `is_nested_contract` | `bool` |  | True if the field points to a nested Contract. |
| `is_lens` | `bool` |  | True if the field is a Lens representation. |


---

## Sigil API

The [Sigil](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L101-L500) class holds the compiled schema fields and options ([sigil.py:L104-L135](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L104-L135)):

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `fields` | `dict[str, FieldSpec]` |  | Map of field names to their compiled specification. |
| `ward_methods` | `tuple[Any, ...]` |  | Ward validator methods. |
| `strict` | `bool` |  | Default strict validation enforcement flag. |
| `revision` | `int \| None` |  | Current schema revision number. |
| `migrate_from` | `dict[int, Callable[[dict], dict]]` |  | Revision-based migrations mapping. |
| `migrate_step` | `Callable[[dict, int], dict] \| None` |  | Sequenced step migration callback. |
| `discriminator` | `str \| None` |  | Discriminator key name for polymorphic models. |
| `content_hash` | `str` |  | Deterministic SHA-256 hash representing structural constraints shape. |


### Content Hash Calculation

The `content_hash` attribute is calculated by `_compute_content_hash(self)` during initialization ([sigil.py:L134, L136-L146](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L134-L146)):
1. Sorts schema fields lexicographically by name ([sigil.py:L140](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L140)).
2. Computes the shape of each field's facet by calling `serialize_facet_shape` ([sigil.py:L141](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L141)).
3. Hashes the string representation (`repr`) of the consolidated list `[(field_name, facet_type, shape)]` using SHA-256 ([sigil.py:L142-L146](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L142-L146)).

---

## Validation Lifecycle

The `validate` method provides a robust, non-raising entrypoint to validate raw input data against the Sigil schema constraints ([sigil.py:L148-L322](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L148-L322)):

```python
def validate(
    self,
    data: Any,
    *,
    strict: bool | None = None,
    partial: bool = False,
    context: dict[str, Any] | None = None,
) -> tuple[dict[str, list[str]], dict[str, Any]]
```

The validation sequence operates as follows:

### 1. Sequential Migrations
If `self.revision` is set, `self.migrate_from` is configured, and input `data` is mapping-like, validation runs migrations ([sigil.py:L163](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L163)):
- Checks `data` for the key `__revision__` ([sigil.py:L165-L166](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L165-L166)).
- If missing, defaults to the lowest revision key in `migrate_from` ([sigil.py:L170](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L170)).
- Progresses through migrations sequentially towards `self.revision` ([sigil.py:L175](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L175)):
  - Calls `self.migrate_step(data, current_rev)` if defined ([sigil.py:L177-L180](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L177-L180)).
  - Otherwise, retrieves and calls the migration function from `self.migrate_from` ([sigil.py:L184-L188](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L184-L188)).
- If migration raises an exception, validation halts immediately, returning migration errors ([sigil.py:L181-L182, L189-L190](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L181-L182)).

### 2. Field Filtering
- Excludes `Computed` and `Constant` facets ([sigil.py:L198-L199](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L198-L199)).
- Resolves `Inject` facets from context values ([sigil.py:L201-L205](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L201-L205)).
- Skips `read_only` fields ([sigil.py:L207-L208](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L207-L208)).
- Extracts the raw field value via `get_field_value(data, fname, facet)` ([sigil.py:L210](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L210)).

### 3. Missing Values (`UNSET`)
If a field is missing from input:
- If `partial=True`, skips the field validation ([sigil.py:L214](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L214)).
- If `facet.default` is not `UNSET`, evaluates it (resolving callable defaults) ([sigil.py:L216-L219](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L216-L219)).
- If `facet.required` is True, registers `"This field is required"` ([sigil.py:L220-L222](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L220-L222)).
- If `facet.allow_null` is True, sets the validated field to `None` ([sigil.py:L223-L225](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L223-L225)).

### 4. Null Handling
If the field value is `None`:
- If `facet.allow_null` is True, passes validation as `None` ([sigil.py:L229-L232](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L229-L232)).
- Otherwise, registers `"This field may not be null"` ([sigil.py:L233-L234](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L233-L234)).

### 5. Nested Contract Parsing
Checks if the facet wraps a nested Contract schema class ([sigil.py:L237](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L237)):
- **List Facets (`many=True`)**:
  - Validates that the input is a list/tuple ([sigil.py:L240-L243](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L240-L243)).
  - Evaluates each list element recursively calling the sub-contract's `validate()` method ([sigil.py:L250-L252](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L250-L252)).
  - Accumulates index-keyed errors or seals successful elements ([sigil.py:L253-L266](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L253-L266)).
- **Single Facets**:
  - Validates that the input is mapping-like ([sigil.py:L268-L270](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L268-L270)).
  - Recursively validates ([sigil.py:L271-L273](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L271-L273)) and seals success outputs ([sigil.py:L278](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L278)).

### 6. Value Cast and Seal
- **Strict Mode**: Verifies that the raw input type matches constraints using `check_strict_type` ([sigil.py:L288](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L288)). Runs pipelines or calls `facet.seal(raw)` ([sigil.py:L294, L301](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L294-L301)).
- **Coercive Mode**: Runs pipelines or casts values using `facet.cast(raw)` before calling `facet.seal(...)` ([sigil.py:L307, L314-L315](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L307-L315)).

---

## JSON Schema Generation

The `to_json_schema` method compiles the Sigil schema into a standard JSON Schema 2020-12 representation ([sigil.py:L324-L401](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L324-L401)):

1. Caches compiled representations to `_json_schema_cache` ([sigil.py:L326-L327](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L326-L327)).
2. Retrieves individual field schemas via `facet.to_schema()` ([sigil.py:L335](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L335)).
3. Integrates schemas defined inside pipeline runes ([sigil.py:L337-L343](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L337-L343)).
4. Resolves nested Contracts, hoisting sub-definitions to `$defs` and referencing them via `$ref` ([sigil.py:L345-L359](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L345-L359)).
5. Maps constraints such as `multipleOf` ([sigil.py:L361-L363](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L361-L363)).
6. Translates `ChoiceFacet` inputs into standard JSON Schema `const` or `enum` format ([sigil.py:L367-L373](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L367-L373)).
7. Configures `PolymorphicFacet` instances using `oneOf` blocks combined with property-name discriminator configurations ([sigil.py:L377-L384](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L377-L384)).

---

## Schema Diffing

The `diff` method determines structural changes and computes whether they represent breaking modifications ([sigil.py:L403-L499](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L403-L499)):

### Diff Logic & Breaking Changes

A diff check is marked as **breaking** (`breaking=True`) under the following conditions:

- **Removed Fields**: Any field that existed in the source schema but is missing from the target schema is breaking ([sigil.py:L415-L417](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L415-L417)).
- **Added Required Fields**: Any new field added in the target schema that is marked as required is breaking ([sigil.py:L420-L424](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L420-L424)).
- **Constraint Narrowing**:
  - Transitioning an existing field from optional to required ([sigil.py:L438-L439](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L438-L439)).
  - Increasing the `min_length` constraint or adding it where it did not previously exist ([sigil.py:L446-L450](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L446-L450)).
  - Decreasing the `max_length` constraint or adding it where it did not previously exist ([sigil.py:L454-L458](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L454-L458)).
  - Increasing the `min_value` constraint or adding it where it did not previously exist ([sigil.py:L464-L468](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L464-L468)).
  - Decreasing the `max_value` constraint or adding it where it did not previously exist ([sigil.py:L472-L476](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L472-L476)).
- **Facet Type Mismatches**: Changing the class type of the facet instance representing the field ([sigil.py:L481-L482](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L481-L482)).

---

## Diff Dataclasses

Diff operations return standard frozen data structures ([sigil.py:L506-L518](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L506-L518)):

### FieldDiff

Stores string representations of changes for a single field.

```python
@dataclass(frozen=True, slots=True)
class FieldDiff:
    was: str
    now: str
    breaking: bool
```

### SigilDiff

Describes differences across the entire schema.

```python
@dataclass(frozen=True, slots=True)
class SigilDiff:
    added_fields: list[str]
    removed_fields: list[str]
    changed_fields: dict[str, FieldDiff]
    breaking: bool
```

---

## Internal Helper Utilities

The `sigil.py` module defines several internal helper functions to handle mapping transformations, value lookups, and strict type verification:

- **[serialize_facet_shape](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L526-L550)**: Extracts dynamic parameters from facet state (excluding metadata like help text, order, or labels) to compute a stable signature representing constraint configurations ([sigil.py:L526-L550](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L526-L550)).
- **[check_strict_type](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L552-L593)**: Performs precise type matching against standard Python objects (avoiding coercion or false positive assertions such as boolean/integer overlaps) ([sigil.py:L552-L593](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L552-L593)).
- **[get_field_value](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L617-L762)**: Extracts values from mapping structures, managing bracket list notations, file lists in `FormData` and `MultiDict` payloads, and resolving empty inputs ([sigil.py:L617-L762](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L617-L762)).
- **[extract_nested_mapping](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L779-L874)**: Maps bracket (`[key]`) and dot (`.key`) path access conventions within flat mapping schemas onto structured sub-namespaces ([sigil.py:L779-L874](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L779-L874)).
- **[extract_flat_list_mapping](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L877-L923)**: Resolves numbered prefix sequences in mapping dictionaries into clean sorted lists ([sigil.py:L877-L923](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L877-L923)).
- **[get_nested_contract_cls](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L926-L936)**: Inspects and resolves the target class of facets referencing sub-contracts ([sigil.py:L926-L936](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/sigil.py#L926-L936)).
