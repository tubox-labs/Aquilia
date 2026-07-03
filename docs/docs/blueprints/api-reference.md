---
title: "Blueprints API Reference"
description: "Complete API reference for the Aquilia Blueprints module"
icon: lucide/database
---
## Overview

This is the comprehensive API reference for the `aquilia.blueprints` package. It details every class, function, decorator, and constant exported in the module's public interface, linking each back to its source code implementation.

---

## 1. Core Classes & Schemas

### [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075)

- **Summary**: The core contract definition class mapping model data to the outside world.
- **Evidence Citation**: `aquilia/blueprints/core.py:826-2075`
- **Class Signature**:
  ```python
  class Blueprint(Generic[ModelT], metaclass=BlueprintMeta)
  ```
- **Initializer Signature**:
  ```python
  def __init__(
      self,
      instance: ModelT | list[ModelT] | None = None,
      *,
      data: Any = UNSET,
      many: bool = False,
      partial: bool = False,
      projection: str | None = None,
      context: dict[str, Any] | None = None,
  )
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `instance` | `ModelT \| list[ModelT] \| None` | `None` | Model instance for outbound (mold) operations. |
| `data` | `Any` | `UNSET` | Raw input data for inbound (cast + seal) operations. |
| `many` | `bool` | `False` | If True, expect a list of instances or input data. |
| `partial` | `bool` | `False` | If True, bypass required check constraints (PATCH semantics). |
| `projection` | `str \| None` | `None` | Named projection subset of fields to serialize/deserialize. |
| `context` | `dict[str, Any] \| None` | `None` | Context dictionary containing request container or other DI objects. |

- **Return Type**: `Blueprint`
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): When input values cannot be cast to target facet types.
  - [SealFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L82-L108): When field or cross-field validation rules fail.
  - [ProjectionFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L117-L126): When an unknown projection name is requested.

---

### [BlueprintMeta](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L239-L644)

- **Summary**: Metaclass for Blueprint classes handling Spec parsing, Facet collection, and model field derivation.
- **Evidence Citation**: `aquilia/blueprints/core.py:239-644`
- **Signature**:
  ```python
  class BlueprintMeta(type)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `(None)` | Name of the class. |
| `bases` | `tuple[type, ...]` | `(None)` | Base classes of the new Blueprint class. |
| `namespace` | `dict[str, Any]` | `(None)` | Class attributes and methods namespace dict. |

- **Return Type**: `BlueprintMeta`
- **Raises**: None.

---

### [ward](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L57-L110)

- **Summary**: Decorator/decorator-factory for registering cross-field validator methods on a Blueprint.
- **Evidence Citation**: `aquilia/blueprints/ward.py:57-110`
- **Signature**:
  ```python
  def ward(fn: Callable[..., Any] | None = None, *, mode: str = "sync") -> Any
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `fn` | `Callable[..., Any] \| None` | `None` | The validation function to decorate. |
| `mode` | `str` | `"sync"` | Execution mode. Must be "sync" or "async". |

- **Return Type**: `Callable[..., Any] | ward`
- **Raises**:
  - `ValueError`: If the mode is not `"sync"` or `"async"`.
  - `TypeError`: If the decorated object is not a callable.

---

### [WardMethod](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/ward.py#L42-L47)

- **Summary**: Dataclass descriptor representing a registered cross-field validator.
- **Evidence Citation**: `aquilia/blueprints/ward.py:42-47`
- **Signature**:
  ```python
  class WardMethod
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `(None)` | Method name. |
| `fn` | `object` | `(None)` | The validator method callable. |
| `mode` | `str` | `(None)` | Validation mode ("sync" or "async"). |

- **Return Type**: `WardMethod`
- **Raises**: None.

---

### [Sigil](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/sigil.py#L101-L498)

- **Summary**: Immutable compiled representation of a Blueprint's validation schema.
- **Evidence Citation**: `aquilia/blueprints/sigil.py:101-498`
- **Signature**:
  ```python
  class Sigil
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `fields` | `dict[str, FieldSpec]` | `(None)` | Compiled specifications for all fields in the schema. |
| `ward_methods` | `tuple[Any, ...]` | `(None)` | Tuple of compiled cross-field validator methods. |
| `strict` | `bool` | `False` | If True, extra keys in input payloads will trigger validation failures. |
| `revision` | `int \| None` | `None` | Schema revision number for data migrations. |
| `migrate_from` | `dict[int, Callable[[dict], dict]] \| None` | `None` | Dictionary mapping old revision numbers to migration hooks. |
| `migrate_step` | `Callable[[dict, int], dict] \| None` | `None` | Dynamic step-based migration hook. |
| `discriminator` | `str \| None` | `None` | Polymorphic discriminator field name for unions. |

- **Return Type**: `Sigil`
- **Raises**: None.

---

### [FieldSpec](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/sigil.py#L63-L98)

- **Summary**: Compiled field specification inside a Sigil schema.
- **Evidence Citation**: `aquilia/blueprints/sigil.py:63-98`
- **Signature**:
  ```python
  class FieldSpec
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `(None)` | Field name. |
| `facet` | `Any` | `(None)` | Facet instance. |
| `required` | `bool` | `(None)` | True if field is mandatory. |
| `default` | `Any` | `(None)` | Static default value. |
| `default_factory` | `Any` | `(None)` | Zero-arg callable providing dynamic default. |
| `pipeline` | `Pipeline \| None` | `None` | Compiled transforms pipeline. |
| `is_nested_blueprint` | `bool` | `False` | True if referencing a nested blueprint. |
| `is_lens` | `bool` | `False` | True if referencing a lens. |

- **Return Type**: `FieldSpec`
- **Raises**: None.

---

### [SealOutcome](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L2086-L2090)

- **Summary**: Dataclass representing the validation outcome of a single row in batch validation.
- **Evidence Citation**: `aquilia/blueprints/core.py:2086-2090`
- **Signature**:
  ```python
  class SealOutcome
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `index` | `int` | `(None)` | List index of the evaluated row. |
| `ok` | `bool` | `(None)` | True if validation succeeded. |
| `value` | `dict \| None` | `(None)` | Sealed validated dictionary, or None if failed. |
| `errors` | `dict \| None` | `(None)` | Field errors dictionary, or None if ok. |

- **Return Type**: `SealOutcome`

---

### [ColumnarReport](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L2094-L2096)

- **Summary**: Columnar error summary for high-performance batch validation.
- **Evidence Citation**: `aquilia/blueprints/core.py:2094-2096`
- **Signature**:
  ```python
  class ColumnarReport
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `valid_mask` | `list[bool]` | `(None)` | List showing validation status (True/False) per row. |
| `errors_by_column` | `dict[str, list[str \| None]]` | `(None)` | Errors list mapped by column field name. |

- **Return Type**: `ColumnarReport`

---

### [BlueprintUnion](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L676-L787)

- **Summary**: Compiled wrapper for polymorphic discriminated blueprint unions constructed via standard OR `|` operator.
- **Evidence Citation**: `aquilia/blueprints/core.py:676-787`
- **Signature**:
  ```python
  class BlueprintUnion
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `members` | `tuple` | `(None)` | Blueprint classes in this union. |

- **Return Type**: `BlueprintUnion`

---

## 2. Facet Base & Built-in Facets

### [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L228-L457)

- **Summary**: Abstract base class representing a single field data contract point.
- **Evidence Citation**: `aquilia/blueprints/facets.py:228-457`
- **Class Signature**:
  ```python
  class Facet(metaclass=FacetMeta)
  ```
- **Initializer Signature**:
  ```python
  def __init__(
      self,
      *,
      source: str | None = None,
      required: bool | None = None,
      read_only: bool = False,
      write_only: bool = False,
      default: Any = UNSET,
      allow_null: bool = False,
      allow_blank: bool = False,
      label: str | None = None,
      help_text: str | None = None,
      validators: Sequence[Callable] | None = None,
  )
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `source` | `str \| None` | `None` | Model attribute name to pull from. |
| `required` | `bool \| None` | `None` | Must be present in input. None will auto-detect from model field settings. |
| `read_only` | `bool` | `False` | Outbound only; omitted from API requests. |
| `write_only` | `bool` | `False` | Inbound only; omitted from API responses. |
| `default` | `Any` | `UNSET` | Default value if field is omitted. |
| `allow_null` | `bool` | `False` | Allows None type to pass validation. |
| `allow_blank` | `bool` | `False` | Allows empty string values (text types only). |
| `label` | `str \| None` | `None` | Readable title. |
| `help_text` | `str \| None` | `None` | Field description. |
| `validators` | `Sequence[Callable] \| None` | `None` | List of validator hook callbacks. |

- **Return Type**: `Facet`

---

### [UNSET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L88)

- **Summary**: Sentinel constant used to distinguish between a field explicitly passed as `None` vs. a field omitted entirely.
- **Evidence Citation**: `aquilia/blueprints/facets.py:88`
- **Signature**:
  ```python
  UNSET = _Unset()
  ```

---

### [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L463-L540)

- **Summary**: String facet with length limits and regex pattern checking.
- **Evidence Citation**: `aquilia/blueprints/facets.py:463-540`
- **Signature**:
  ```python
  class TextFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `min_length` | `int \| None` | `None` | Min character length. |
| `max_length` | `int \| None` | `None` | Max character length. |
| `trim` | `bool` | `True` | Strip leading/trailing whitespace. |
| `pattern` | `str \| None` | `None` | Regex validation pattern (maximum length: 500). |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If value is not a string/primitive, or if regex pattern fails safety checks (ReDoS protection).

---

### [EmailFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L543-L560)

- **Summary**: String facet with RFC email validation.
- **Evidence Citation**: `aquilia/blueprints/facets.py:543-560`
- **Signature**:
  ```python
  class EmailFacet(TextFacet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If format is invalid.

---

### [URLFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L563-L582)

- **Summary**: String facet with standard URL scheme check.
- **Evidence Citation**: `aquilia/blueprints/facets.py:563-582`
- **Signature**:
  ```python
  class URLFacet(TextFacet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If format is invalid.

---

### [SlugFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L585-L602)

- **Summary**: String facet matching lowercase alphanumeric and hyphens.
- **Evidence Citation**: `aquilia/blueprints/facets.py:585-602`
- **Signature**:
  ```python
  class SlugFacet(TextFacet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If format is invalid.

---

### [IPFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L605-L620)

- **Summary**: String facet validating IPv4 or IPv6 format.
- **Evidence Citation**: `aquilia/blueprints/facets.py:605-620`
- **Signature**:
  ```python
  class IPFacet(TextFacet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If address is invalid.

---

### [IntFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L626-L670)

- **Summary**: Integer facet with range limits and multipleOf validation.
- **Evidence Citation**: `aquilia/blueprints/facets.py:626-670`
- **Signature**:
  ```python
  class IntFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `min_value` | `int \| None` | `None` | Minimum allowed value. |
| `max_value` | `int \| None` | `None` | Maximum allowed value. |
| `multiple_of` | `int \| None` | `None` | Enforces value % multiple_of == 0. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If integer coercion fails or constraints are violated.

---

### [FloatFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L673-L726)

- **Summary**: Float facet with NaN/Infinity control.
- **Evidence Citation**: `aquilia/blueprints/facets.py:673-726`
- **Signature**:
  ```python
  class FloatFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `min_value` | `float \| None` | `None` | Minimum value. |
| `max_value` | `float \| None` | `None` | Maximum value. |
| `allow_nan` | `bool` | `False` | Allow NaN values. |
| `allow_infinity` | `bool` | `False` | Allow infinity values. |
| `multiple_of` | `float \| None` | `None` | Multiple of constraint. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If parsing fails, or NaN/Infinity values are illegal.

---

### [DecimalFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L729-L783)

- **Summary**: Decimal facet enforcing digit and decimal place constraints.
- **Evidence Citation**: `aquilia/blueprints/facets.py:729-783`
- **Signature**:
  ```python
  class DecimalFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_digits` | `int \| None` | `None` | Max total digits. |
| `decimal_places` | `int \| None` | `None` | Max decimal places. |
| `min_value` | `Decimal \| float \| None` | `None` | Min decimal value. |
| `max_value` | `Decimal \| float \| None` | `None` | Max decimal value. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If invalid decimal input is passed, or precision constraints fail.

---

### [BoolFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L789-L811)

- **Summary**: Boolean facet coercing common truthy/falsy values.
- **Evidence Citation**: `aquilia/blueprints/facets.py:789-811`
- **Signature**:
  ```python
  class BoolFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If input is not cleanly coercible to bool.

---

### [DateFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L817-L844)

- **Summary**: ISO 8601 YYYY-MM-DD date facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:817-844`
- **Signature**:
  ```python
  class DateFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If string format is invalid.

---

### [TimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L847-L872)

- **Summary**: ISO 8601 HH:MM:SS time facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:847-872`
- **Signature**:
  ```python
  class TimeFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If string format is invalid.

---

### [DateTimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L875-L903)

- **Summary**: ISO 8601 datetime facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:875-903`
- **Signature**:
  ```python
  class DateTimeFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If string format is invalid.

---

### [DurationFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L906-L947)

- **Summary**: Timedelta facet parsing float seconds or HH:MM:SS format.
- **Evidence Citation**: `aquilia/blueprints/facets.py:906-947`
- **Signature**:
  ```python
  class DurationFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If parsing fails.

---

### [UUIDFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L950-L971)

- **Summary**: UUID parsing facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:950-971`
- **Signature**:
  ```python
  class UUIDFacet(Facet)
  ```
- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If value cannot be parsed as UUID.

---

### [ListFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L977-L1040)

- **Summary**: Array facet delegating elements validation to a child facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:977-1040`
- **Signature**:
  ```python
  class ListFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `child` | `Facet \| None` | `None` | Optional facet applied to validate each item. |
| `min_items` | `int \| None` | `None` | Minimum items count. |
| `max_items` | `int \| None` | `None` | Maximum items count. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If input is not list/tuple or if element validation fails.

---

### [SetFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1043-L1107)

- **Summary**: Array facet with unique element checking.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1043-1107`
- **Signature**:
  ```python
  class SetFacet(Facet)
  ```
- **Parameters**: Same as `ListFacet`.
- **Raises**: Same as `ListFacet`.

---

### [TupleFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1110-L1173)

- **Summary**: Tuple array facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1110-1173`
- **Signature**:
  ```python
  class TupleFacet(Facet)
  ```
- **Parameters**: Same as `ListFacet`.
- **Raises**: Same as `ListFacet`.

---

### [DictFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1176-L1258)

- **Summary**: Key-value map facet, optionally validating all values against a value facet.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1176-1258`
- **Signature**:
  ```python
  class DictFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `value_facet` | `Facet \| None` | `None` | Optional facet applied to validate each dictionary value. |
| `max_keys` | `int \| None` | `1000` | Maximum permitted dictionary keys (protects against hash-collision DoS). |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If value is not a dict, key limit is exceeded, or key types are invalid.

---

### [JSONFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1261-L1313)

- **Summary**: Arbitrary JSON blob facet with maximum nesting depth safety check.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1261-1313`
- **Signature**:
  ```python
  class JSONFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_depth` | `int \| None` | `32` | Max nesting depth limit. |
| `allowed_types` | `tuple` | `(str, int, float, bool, NoneType, list, dict)` | Allowed primitive JSON types. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If depth limit or disallowed types are detected.

---

### [FileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1319-L1336)

- **Summary**: Base reference facet validating file pathways/URLs.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1319-1336`
- **Signature**:
  ```python
  class FileFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `allowed_types` | `list[str] \| None` | `None` | List of allowed MIME types/extensions. |


---

### [ChoiceFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1342-L1378)

- **Summary**: Facet validating that values belong to a static choices collection.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1342-1378`
- **Signature**:
  ```python
  class ChoiceFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `choices` | `Sequence` | `(None)` | A list/tuple of choices, or dictionary of keys. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): When validation value is not in permitted set.

---

### [LiteralFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1381-L1386)

- **Summary**: Facet restricting validation to a single exact literal value.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1381-1386`
- **Signature**:
  ```python
  class LiteralFacet(ChoiceFacet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `value` | `Any` | `(None)` | The static exact value. |


---

### [EnumFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1389-L1455)

- **Summary**: Facet validating and mapping values to Python Enum members.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1389-1455`
- **Signature**:
  ```python
  class EnumFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enum_class` | `type` | `(None)` | Python Enum class definition. |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): If casting to enum fails.

---

### [UploadFileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1745-L1817)

- **Summary**: Facet wrapping uploaded file buffers with size and type checks.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1745-1817`
- **Signature**:
  ```python
  class UploadFileFacet(FileFacet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_size` | `int \| None` | `None` | Max file size allowed in bytes. |
| `allowed_types` | `list[str] \| None` | `None` | Allowed mime type patterns (e.g. image/*). |

- **Raises**:
  - [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79): When input is not `UploadFile`, exceeds max_size, or violates MIME rules.

---

### [FormDataFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1820-L1866)

- **Summary**: Facet parsing data fields from URL-encoded or multi-part payloads.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1820-1866`
- **Signature**:
  ```python
  class FormDataFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `type` | `Any` | `str` | Target type or facet structure to validate against. |


---

### [Computed](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1522-L1579)

- **Summary**: Read-only facet whose value is calculated dynamically on serialization.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1522-1579`
- **Signature**:
  ```python
  class Computed(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `compute` | `Callable \| str` | `(None)` | Method name string or callable taking (instance). |


---

### [Constant](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1582-L1607)

- **Summary**: Read-only facet returning a fixed preconfigured constant value.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1582-1607`
- **Signature**:
  ```python
  class Constant(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `value` | `Any` | `(None)` | The static constant value. |


---

### [WriteOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1610-L1621)

- **Summary**: Convenience subclass of `TextFacet` marked write-only.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1610-1621`
- **Signature**:
  ```python
  class WriteOnly(TextFacet)
  ```

---

### [ReadOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1624-L1647)

- **Summary**: Read-only passthrough facet auto-serializing standard primitives.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1624-1647`
- **Signature**:
  ```python
  class ReadOnly(Facet)
  ```

---

### [Hidden](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1650-L1662)

- **Summary**: Facet hidden from input and output, used internally or populated via DI.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1650-1662`
- **Signature**:
  ```python
  class Hidden(Facet)
  ```

---

### [Inject](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1668-L1742)

- **Summary**: Read-only facet resolving its value from the DI container or thread context.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1668-1742`
- **Signature**:
  ```python
  class Inject(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `token` | `Any` | `(None)` | DI class key/token or context dictionary key name string. |
| `via` | `str \| None` | `None` | Method to call on the resolved service object. |
| `attr` | `str \| None` | `None` | Attribute to pull from the resolved service object. |


---

### [derive_facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1917-L1986)

- **Summary**: Derive a Facet instance from an Aquilia Model field definition.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1917-1986`
- **Signature**:
  ```python
  def derive_facet(model_field: Any) -> Facet
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model_field` | `Any` | `(None)` | Aquilia Model field instance. |

- **Return Type**: `Facet`

---

### [MODEL_FIELD_TO_FACET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/facets.py#L1872-L1914)

- **Summary**: Dictionary mapping model database field names to corresponding facet classes.
- **Evidence Citation**: `aquilia/blueprints/facets.py:1872-1914`
- **Signature**:
  ```python
  MODEL_FIELD_TO_FACET: dict[str, type[Facet]] = {...}
  ```

---

## 3. Annotation & Decorator Helpers

### [Field](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/annotations.py#L111-L260)

- **Summary**: Constraint descriptor specifying validations and defaults for annotation-driven fields.
- **Evidence Citation**: `aquilia/blueprints/annotations.py:111-260`
- **Class Signature**:
  ```python
  class Field
  ```
- **Initializer Signature**:
  ```python
  def __init__(
      self,
      *,
      default: Any = UNSET,
      default_factory: Callable | None = None,
      required: bool | None = None,
      read_only: bool = False,
      write_only: bool = False,
      allow_null: bool = False,
      allow_blank: bool = False,
      source: str | None = None,
      label: str | None = None,
      help_text: str | None = None,
      validators: Sequence[Callable] | None = None,
      ge: int | float | None = None,
      le: int | float | None = None,
      gt: int | float | None = None,
      lt: int | float | None = None,
      min_length: int | None = None,
      max_length: int | None = None,
      pattern: str | None = None,
      min_items: int | None = None,
      max_items: int | None = None,
      choices: Sequence | None = None,
      max_digits: int | None = None,
      decimal_places: int | None = None,
      alias: str | None = None,
  )
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `default` | `Any` | `UNSET` | Static default value. |
| `default_factory` | `Callable \| None` | `None` | Dynamic default value factory callable. |
| `required` | `bool \| None` | `None` | Manually specify field is mandatory. |
| `read_only` | `bool` | `False` | Mark field read-only. |
| `write_only` | `bool` | `False` | Mark field write-only. |
| `allow_null` | `bool` | `False` | Allow None values. |
| `allow_blank` | `bool` | `False` | Allow empty string values. |
| `source` | `str \| None` | `None` | Override model field source path. |
| `label` | `str \| None` | `None` | Readable field label. |
| `help_text` | `str \| None` | `None` | Documentation string. |
| `validators` | `Sequence[Callable] \| None` | `None` | List of validator hook callbacks. |
| `ge` | `int \| float \| None` | `None` | Greater than or equal constraint. |
| `le` | `int \| float \| None` | `None` | Less than or equal constraint. |
| `gt` | `int \| float \| None` | `None` | Strictly greater than constraint. |
| `lt` | `int \| float \| None` | `None` | Strictly less than constraint. |
| `min_length` | `int \| None` | `None` | Min character length. |
| `max_length` | `int \| None` | `None` | Max character length. |
| `pattern` | `str \| None` | `None` | Regex pattern string. |
| `min_items` | `int \| None` | `None` | Min list items count. |
| `max_items` | `int \| None` | `None` | Max list items count. |
| `choices` | `Sequence \| None` | `None` | List of allowed values. |
| `max_digits` | `int \| None` | `None` | Decimal max total digits. |
| `decimal_places` | `int \| None` | `None` | Decimal max decimal places. |
| `alias` | `str \| None` | `None` | Input parameter key alias mapping. |

- **Return Type**: `Field`
- **Raises**:
  - `ConfigInvalidFault`: If both `default` and `default_factory` are passed simultaneously.

---

### [computed](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/annotations.py#L568-L585)

- **Summary**: Decorator marking a Blueprint method as a computed read-only output field.
- **Evidence Citation**: `aquilia/blueprints/annotations.py:568-585`
- **Signature**:
  ```python
  def computed(func: Callable) -> _ComputedMarker
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `func` | `Callable` | `(None)` | The Blueprint method method taking (self, instance). |

- **Return Type**: `_ComputedMarker`

---

### [NestedBlueprintFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/annotations.py#L310-L473)

- **Summary**: Facet that delegates validation to another Blueprint class.
- **Evidence Citation**: `aquilia/blueprints/annotations.py:310-473`
- **Signature**:
  ```python
  class NestedBlueprintFacet(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_cls` | `type` | `(None)` | Target Blueprint class to instantiate and validate against. |
| `many` | `bool` | `False` | If True, validates a collection list of objects. |
| `max_nesting_depth` | `int \| None` | `32` | Depth limit to avoid stack overflow recursion. |

- **Return Type**: `NestedBlueprintFacet`
- **Raises**:
  - `TypeError`: Under subscription if MyBlueprint type arguments are invalid.

---

## 4. Relation Traversal & Projections

### [Lens](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L26-L184)

- **Summary**: A relational facet viewing sub-objects through another Blueprint, with recursion guards and PK fallback.
- **Evidence Citation**: `aquilia/blueprints/lenses.py:26-184`
- **Signature**:
  ```python
  class Lens(Facet)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `target` | `type[Blueprint] \| _ProjectedRef \| None` | `None` | Target Blueprint or ProjectedRef to render against. |
| `many` | `bool` | `False` | Set True to render a list collection of relations. |
| `depth` | `int` | `3` | Maximum nesting depth to prevent infinite loops. |
| `projection` | `str \| None` | `None` | Target Blueprint named projection format. |

- **Return Type**: `Lens`

---

### [ProjectionRegistry](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L26-L146)

- **Summary**: Registry compiling and managing named subsets of field selections (projections) on a Blueprint.
- **Evidence Citation**: `aquilia/blueprints/projections.py:26-146`
- **Signature**:
  ```python
  class ProjectionRegistry
  ```
- **Return Type**: `ProjectionRegistry`

---

## 5. Schema & OpenAPI Compilation

### [generate_schema](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/schema.py#L19-L36)

- **Summary**: Generate JSON Schema for a Blueprint class projection.
- **Evidence Citation**: `aquilia/blueprints/schema.py:19-36`
- **Signature**:
  ```python
  def generate_schema(
      blueprint_cls: type[Blueprint],
      *,
      projection: str | None = None,
      mode: str = "output",
  ) -> dict[str, Any]
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_cls` | `type[Blueprint]` | `(None)` | Blueprint class definition. |
| `projection` | `str \| None` | `None` | Named projection (None = default projection). |
| `mode` | `str` | `"output"` | OpenAPI direction: "output" (response) or "input" (request body). |

- **Return Type**: `dict[str, Any]`

---

### [generate_component_schemas](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/schema.py#L39-L68)

- **Summary**: Compile OpenAPI components section dictionary for multiple Blueprints.
- **Evidence Citation**: `aquilia/blueprints/schema.py:39-68`
- **Signature**:
  ```python
  def generate_component_schemas(
      *blueprint_classes: type[Blueprint],
      include_projections: bool = True,
  ) -> dict[str, dict[str, Any]]
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_classes` | `type[Blueprint]` | `(None)` | Variable arguments list of Blueprint class types. |
| `include_projections` | `bool` | `True` | Generate separate schemas for each named projection. |

- **Return Type**: `dict[str, dict[str, Any]]`

---

## 6. Integration Hooks

### [is_blueprint_class](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L46-L48)

- **Summary**: Utility checker verifying an object is a subclass of `Blueprint`.
- **Evidence Citation**: `aquilia/blueprints/integration.py:46-48`
- **Signature**:
  ```python
  def is_blueprint_class(obj: Any) -> bool
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` | `(None)` | Object reference to evaluate. |

- **Return Type**: `bool`

---

### [is_projected_blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L51-L53)

- **Summary**: Utility checker verifying an object is a subscripted `ProjectedRef` class.
- **Evidence Citation**: `aquilia/blueprints/integration.py:51-53`
- **Signature**:
  ```python
  def is_projected_blueprint(obj: Any) -> bool
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` | `(None)` | Object reference to evaluate. |

- **Return Type**: `bool`

---

### [resolve_blueprint_from_annotation](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L56-L76)

- **Summary**: Resolve Blueprint class and projection string from standard controller type annotations.
- **Evidence Citation**: `aquilia/blueprints/integration.py:56-76`
- **Signature**:
  ```python
  def resolve_blueprint_from_annotation(annotation: Any) -> tuple[type[Blueprint] | None, str | None]
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `annotation` | `Any` | `(None)` | The parameter type annotation. |

- **Return Type**: `tuple[type[Blueprint] | None, str | None]`

---

### [bind_blueprint_to_request](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L298-L538)

- **Summary**: Instantiate and validate (seal) a Blueprint directly from an incoming request payload.
- **Evidence Citation**: `aquilia/blueprints/integration.py:298-538`
- **Signature**:
  ```python
  async def bind_blueprint_to_request(
      blueprint_cls: type[Blueprint],
      request: Any,
      *,
      projection: str | None = None,
      partial: bool = False,
      context: dict[str, Any] | None = None,
  ) -> Blueprint
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_cls` | `type[Blueprint]` | `(None)` | Target Blueprint class. |
| `request` | `Any` | `(None)` | Incoming Request instance. |
| `projection` | `str \| None` | `None` | Optional projection subset override. |
| `partial` | `bool` | `False` | Allows partial payload inputs (PATCH updates). |
| `context` | `dict[str, Any] \| None` | `None` | Extra context dictionary variables passed to the Blueprint. |

- **Return Type**: `Blueprint`
- **Raises**:
  - [SealFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L82-L108): If validation fails.

---

### [render_blueprint_response](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L541-L581)

- **Summary**: Serialize database models or lists of database models through a Blueprint for JSON outputs.
- **Evidence Citation**: `aquilia/blueprints/integration.py:541-581`
- **Signature**:
  ```python
  def render_blueprint_response(
      blueprint_or_cls: Blueprint | type[Blueprint],
      data: Any = None,
      *,
      projection: str | None = None,
      many: bool = False,
  ) -> Any
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_or_cls` | `Blueprint \| type[Blueprint]` | `(None)` | Blueprint class reference or active instance. |
| `data` | `Any` | `None` | Object or sequence of objects to serialize. |
| `projection` | `str \| None` | `None` | Specific projection output schema shape. |
| `many` | `bool` | `False` | Set True if data is a list sequence of model instances. |

- **Return Type**: `Any` (dict or list of dicts)

---

## 7. Exception Hierarchy & Fault Domain

### [BlueprintFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L25-L56)

- **Summary**: Unified base exception class for all Blueprint errors.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:25-56`
- **Signature**:
  ```python
  class BlueprintFault(Fault)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `message` | `str` | `"Blueprint validation failed"` | Error detail message. |
| `errors` | `dict[str, list[str]] \| None` | `None` | Detailed errors mapped per field. |
| `code` | `str \| None` | `None` | Fault code (defaults to BP000). |
| `metadata` | `dict[str, Any] \| None` | `None` | Metadata logging payload dict. |

- **Return Type**: `BlueprintFault`

---

### [CastFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L62-L79)

- **Summary**: Raised during the casting phase when inputs cannot be coerced.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:62-79`
- **Signature**:
  ```python
  class CastFault(BlueprintFault)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `field` | `str` | `(None)` | The key field name where coercion failed. |
| `message` | `str` | `"Invalid value"` | Casting failure explanation. |
| `metadata` | `dict[str, Any] \| None` | `None` | Logging metadata payload. |

- **Return Type**: `CastFault`

---

### [SealFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L82-L108)

- **Summary**: Raised when field or cross-field validation rules fail.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:82-108`
- **Signature**:
  ```python
  class SealFault(BlueprintFault)
  ```
- **Parameters**: Same as `BlueprintFault`.
- **Return Type**: `SealFault`

---

### [ImprintFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L111-L114)

- **Summary**: Raised when persistent model mapping back-writes (imprinting) fail.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:111-114`
- **Signature**:
  ```python
  class ImprintFault(BlueprintFault)
  ```
- **Return Type**: `ImprintFault`

---

### [ProjectionFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L117-L126)

- **Summary**: Raised when an unknown or invalid projection is requested.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:117-126`
- **Signature**:
  ```python
  class ProjectionFault(BlueprintFault)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `projection` | `str` | `(None)` | The requested invalid projection key. |
| `available` | `list[str]` | `(None)` | List of valid projections configured on the Spec. |

- **Return Type**: `ProjectionFault`

---

### [LensDepthFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L129-L138)

- **Summary**: Raised when relation traversal depth limits are exceeded.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:129-138`
- **Signature**:
  ```python
  class LensDepthFault(BlueprintFault)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `path` | `str` | `(None)` | Nesting path where limits were breached. |
| `max_depth` | `int` | `(None)` | Maximum depth limit configured on the Lens. |

- **Return Type**: `LensDepthFault`

---

### [LensCycleFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L141-L150)

- **Summary**: Raised when infinite circular relational Lens loops are detected.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py#L141-L150`
- **Signature**:
  ```python
  class LensCycleFault(BlueprintFault)
  ```
- **Parameters**:
  | Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cycle_path` | `list[str]` | `(None)` | Relation loop path names. |

- **Return Type**: `LensCycleFault`

---

### [BLUEPRINT](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L16)

- **Summary**: Fault domain namespace constant registering Blueprint validation errors.
- **Evidence Citation**: `aquilia/blueprints/exceptions.py:16`
- **Signature**:
  ```python
  BLUEPRINT = FaultDomain(name="BLUEPRINT", description="...")
  ```
