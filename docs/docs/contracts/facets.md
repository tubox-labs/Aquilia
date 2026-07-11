---
title: "Facets"
description: "Detailed catalog of all built-in validation, type coercion, and injection facets in Aquilia"
icon: lucide/gem
---
### What is a Facet?

In Aquilia, a **Facet** is the field-level primitive of a `Contract` ([facets.py:L2](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L2)). 

A [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L228-L458) represents a single aspect of a model exposed through a `Contract` ([facets.py:L4](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L4)). Facets can auto-derive from model fields, but they can also be overridden, composed, or created standalone ([facets.py:L5-L6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L5-L6)). It replaces traditional serialization field abstractions with clean, Contract-native semantics defined across three primary stages ([facets.py:L11-L12](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L11-L12)):

*   **Inbound Cast**: Raw request data is processed, type-coerced, and parsed into Python objects ([facets.py:L325-L332](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L325-L332)).
*   **Inbound Validation (Seal)**: The cast Python objects are validated against constraints and user-defined validation callables ([facets.py:L346-L360](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L346-L360)).
*   **Outbound Mold**: Attributes from internal model instances are shaped, normalized, and formatted for the outbound response ([facets.py:L336-L342](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L336-L342)).

---

### Base Facet API

Every built-in facet inherits from the base [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L228-L458) class.

#### Parameters & Defaults

The [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L228-L458) base constructor accepts the following parameters ([facets.py:L256-L280](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L256-L280)):

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `source` | `str \| None` | `None` | Model attribute name to read from. Defaults to the facet\ |
| `required` | `bool \| None` | `None` | Specifies if the field is mandatory in inbound requests. If None, it is dynamically computed based on defaults and nullability (facets.py:L291-L299). |
| `read_only` | `bool` | `false` | If True, the facet only appears in outbound responses and is ignored during inbound casting (facets.py:L272). |
| `write_only` | `bool` | `false` | If True, the facet is only accepted in inbound requests and is omitted from outbound serialization (facets.py:L273). |
| `default` | `Any` | `UNSET` | Default value used if the key is missing from inbound data. Uses the UNSET sentinel (facets.py:L274). |
| `allow_null` | `bool` | `false` | If True, None is accepted as a valid cast value (facets.py:L275). |
| `allow_blank` | `bool` | `false` | If True, empty strings are allowed in text-based facets (facets.py:L276). |
| `label` | `str \| None` | `None` | A human-readable label for documentation and form generation (facets.py:L277). |
| `help_text` | `str \| None` | `None` | Documentation string explaining the field\ |
| `validators` | `Sequence[Callable] \| None` | `None` | List of additional validation callables that run during seal() (facets.py:L279). |


#### Life-Cycle Methods

A [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L228-L458) processes data using several standard lifecycle methods:

*   **`cast(value: Any) -> Any`** ([facets.py:L325-L332](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L325-L332))
    Coerces raw inbound input to the correct Python type. Overridden by subclasses to perform specific type checks and parsing. Raises `CastFault` on failure.
*   **`seal(value: Any) -> Any`** ([facets.py:L346-L360](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L346-L360))
    Validates a cast value against constraints and runs custom callables in `self.validators`. Raises `CastFault` (wrapping `ValueError` or `TypeError`) if validation fails.
*   **`mold(value: Any) -> Any`** ([facets.py:L336-L342](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L336-L342))
    Converts internal Python values into JSON-serializable formats for outbound responses.
*   **`extract(instance: Any) -> Any`** ([facets.py:L364-L392](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L364-L392))
    Extracts the raw attribute from a model instance. Supports dotted strings (e.g., `user.profile.avatar`) and extracts values from nested dictionaries or contracts safely. If `source="*"`, the entire instance is returned.
*   **`bind(name: str, contract: Contract) -> None`** ([facets.py:L304-L310](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L304-L310))
    Links a facet instance to a specific attribute name on a parent Contract class.
*   **`to_schema() -> dict[str, Any]`** ([facets.py:L396-L409](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L396-L409))
    Generates a compliant JSON Schema fragment representing the facet's type, constraints, defaults, and visibility flags.

#### Composition Operators

*   **Subscript Slice Constraints (`__getitem__`)** ([facets.py:L425-L447](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L425-L447))
    Allows applying range constraints to existing facet instances or factory proxies using Python's slice syntax:
    ```python
    username_facet = TextFacet()[3:20] # min_length=3, max_length=20
    int_range_facet = IntFacet()[0:100:5] # min_value=0, max_value=100, multiple_of=5
    ```
*   **Pipeline Composition (`__rshift__`)** ([facets.py:L449-L453](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L449-L453))
    Chains facets or transformations left-to-right using the pipeline operator (`>>`), passing the output of one cast/seal sequence to the next.

---

### Facet Taxonomy Table

All built-in facets exported in the global `__all__` list are documented below ([facets.py:L33-L65](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L33-L65)):

| Facet / Symbol | Schema Type | Inbound Coercion / Constraints | Outbound Normalization |
| :--- | :--- | :--- | :--- |
| [Facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L228-L458) | `any` | No default type coercion. | Passes values directly. |
| [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L463-L541) | `string` | Strips whitespace (if `trim=True`). Coerces safe primitives. Checks min/max lengths & ReDoS-safe patterns. | Returns string. |
| [IntFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L626-L671) | `integer` | Coerces numeric strings, floats. Rejects booleans. Checks min/max boundaries & multiples. | Returns integer. |
| [FloatFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L673-L727) | `number` | Coerces numeric values. Validates NaN & Infinity rules. Checks boundaries & multiples. | Returns float. |
| [DecimalFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L729-L784) | `string` | Safe string-based decimal cast. Checks total digits & decimal places. | Molded to `str` to preserve precision ([facets.py:L774-L778](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L774-L778)). |
| [BoolFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L789-L811) | `boolean` | Coerces truthy/falsy strings (e.g., `yes`, `off`) and integers (1, 0). | Returns boolean. |
| [DateFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L817-L844) | `string` | Parses ISO 8601 strings, converts `datetime` objects. | Formatted to ISO 8601 string. |
| [TimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L847-L872) | `string` | Parses ISO 8601 time string (`HH:MM:SS`). | Formatted to ISO 8601 string. |
| [DateTimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L875-L903) | `string` | Parses ISO 8601 datetime strings (converts trailing `Z` timezone markers). | Formatted to ISO 8601 string. |
| [DurationFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L906-L947) | `string` | Parses floats/ints (seconds) or `HH:MM:SS` duration formats. | Molded to total seconds as a float ([facets.py:L937-L942](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L937-L942)). |
| [UUIDFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L950-L971) | `string` | Parses standard UUID strings into Python `uuid.UUID` objects. | Formatted to string. |
| [EmailFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L543-L560) | `string` | Lowercases input string and validates against standard email regex format. | Returns lowercase string. |
| [URLFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L563-L582) | `string` | Validates HTTP/HTTPS URL formats. | Returns string. |
| [SlugFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L585-L602) | `string` | Lowercases input. Validates lowercase alphanumeric characters, underscores, and hyphens. | Returns lowercase string. |
| [IPFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L605-L620) | `string` | Validates v4 and v6 IP address formats using standard python `ipaddress`. | Returns string. |
| [ListFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L977-L1041) | `array` | Expects list/tuple. Casts and validates nested items via optional `child` facet. | Recursively molds list items. |
| [DictFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1176-L1258) | `object` | Expects dictionary or parses JSON object. Limits keys. Casts nested values via `value_facet`. | Recursively molds nested values. |
| [JSONFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1261-L1314) | `object` | Parses stringified JSON. Restricts type options and maximum nesting depth. | Returns json object structure. |
| [FileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1319-L1337) | `string` | Stores paths, URLs, or file references. | Formatted to string. |
| [ChoiceFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1342-L1379) | `string` | Validates against a static set of allowed values or mappings. | Passes selected key/value. |
| [LiteralFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1381-L1387) | `string` | Constrains value to match one exact literal. | Returns literal. |
| [EnumFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1389-L1456) | *dynamic* | Coerces to Python Enum members (via value conversion or string member name). | Returns the underlying enum `.value` ([facets.py:L1436-L1441](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1436-L1441)). |
| [UploadFileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1745-L1818) | `string` | Validates uploaded files, checking size constraints and mime types. | Returns metadata dict: filename, size, and mime type. |
| [FormDataFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1820-L1867) | *dynamic* | Handles multipart form field casting using a dynamically compiled child facet. | Delegates molding to child facet. |
| [Computed](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1522-L1580) | `any` | Ignored on input (marked as `read_only=True`). | Dynamically computed at response-generation. |
| [Constant](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1582-L1607) | `any` | Ignored on input. Outbound value is locked to a static constant. | Returns the locked value. |
| [WriteOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1610-L1621) | `string` | Write-only constraints (used for passwords/secrets). | Omitted from response output. |
| [ReadOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1624-L1647) | `any` | Ignored on input (marked as `read_only=True`). | Passes values with auto-serialization. |
| [Hidden](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1650-L1662) | `any` | Populated inbound via default/DI. | Omitted from response output. |
| [Inject](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1668-L1742) | `any` | Resolves value from Dependency Injection container or context. | Passes resolved value. |
| [UNSET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L88) | `-` | Sentinel indicating no value was passed. | Ignored. |

---

### Primitive Facets

#### TextFacet
The [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L463-L541) parses string values, supports stripping, and enforces length and regex boundaries.
*   **Constraints**:
    *   `min_length: int | None`: Minimum character length ([facets.py:L481](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L481)).
    *   `max_length: int | None`: Maximum character length ([facets.py:L482](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L482)).
    *   `trim: bool = True`: If True, trims leading and trailing whitespaces during casting ([facets.py:L483](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L483)).
    *   `pattern: str | None`: Regular expression pattern to enforce ([facets.py:L484](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L484)).
*   **Coercion**: Coerces safe primitive types (`int`, `float`, `bool`) to string format ([facets.py:L513-L514](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L513-L514)). Rejects non-primitive types with `CastFault` ([facets.py:L516](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L516)).

#### IntFacet
The [IntFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L626-L671) processes integer inputs.
*   **Constraints**: `min_value`, `max_value`, and `multiple_of` ([facets.py:L640-L642](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L640-L642)).
*   **Coercion**: Explicitly rejects `bool` inputs, preventing python's implicit mapping of `True` -> `1` and `False` -> `0` ([facets.py:L645-L646](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L645-L646)). Coerces other valid numeric/string structures using `int(value)` ([facets.py:L648](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L648)).

#### FloatFacet
The [FloatFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L673-L727) validates floating-point numbers.
*   **Constraints**: `min_value`, `max_value`, `multiple_of`, `allow_nan: bool = False`, and `allow_infinity: bool = False` ([facets.py:L689-L693](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L689-L693)).
*   **Multiple-Of Precision**: Float modulo is highly susceptible to float precision errors. The modulo check validates that the remainder is within a minute tolerance boundary (`1e-9`) from a whole integer representation ([facets.py:L714-L715](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L714-L715)).

#### DecimalFacet
The [DecimalFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L729-L784) is used for exact precision calculations (such as currency values).
*   **Constraints**: `max_digits`, `decimal_places`, `min_value`, and `max_value` ([facets.py:L744-L747](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L744-L747)).
*   **Coercion & Mold**: Converts floats to strings during cast to prevent intermediate precision loss ([facets.py:L750-L751](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L750-L751)). Outbound decimal values are molded into string representations to ensure zero precision loss over JSON transport ([facets.py:L774-L778](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L774-L778)).

#### BoolFacet
The [BoolFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L789-L811) maps values to booleans.
*   **Coercion Mapping**:
    *   **True Coercions**: `"true"`, `"1"`, `"yes"`, `"on"`, `"t"`, `"y"`, and integer/float `1` ([facets.py:L794, L807-L808](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L794)).
    *   **False Coercions**: `"false"`, `"0"`, `"no"`, `"off"`, `"f"`, `"n"`, and integer/float `0` ([facets.py:L795, L809-L810](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L795)).

---

### Temporal Facets

Temporal facets parse formatted ISO 8601 strings inbound and normalize output objects back to standard formats.

*   **[DateFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L817-L844)**:
    *   **Inbound**: Accepts `datetime` (extracts date), direct `date` object, or calls `date.fromisoformat()` on string inputs ([facets.py:L823-L829](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L823-L829)).
    *   **Outbound**: Calls `.isoformat()` ([facets.py:L838](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L838)).
*   **[TimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L847-L872)**:
    *   **Inbound**: Accepts direct `time` objects or parses ISO time strings (`HH:MM:SS`) using `time.fromisoformat()` ([facets.py:L853-L857](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L853-L857)).
    *   **Outbound**: Calls `.isoformat()` ([facets.py:L866](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L866)).
*   **[DateTimeFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L875-L903)**:
    *   **Inbound**: Accepts standard `datetime` objects. If passed a string, it strips spaces and maps the trailing `"Z"` timezone marker to the Python-compliant ISO offset `"+00:00"` before parsing via `datetime.fromisoformat()` ([facets.py:L880-L888](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L880-L888)).
    *   **Outbound**: Calls `.isoformat()` ([facets.py:L897](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L897)).
*   **[DurationFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L906-L947)**:
    *   **Inbound**: Accepts `timedelta` objects directly ([facets.py:L912](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L912)). Numeric values (int/float) are treated as raw seconds ([facets.py:L914-L915](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L914-L915)). Strings are evaluated for sign notation (`-` or `+`) ([facets.py:L918-L923](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L918-L923)) and parsed as float seconds ([facets.py:L925](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L925)) or duration format `HH:MM:SS` ([facets.py:L928-L932](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L928-L932)).
    *   **Outbound**: Molded into float seconds using `value.total_seconds()` ([facets.py:L941](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L941)).

---

### Identity Facets

Identity facets validate format strings and patterns.

*   **[UUIDFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L950-L971)**: Validates input compatibility by converting to Python `uuid.UUID` objects ([facets.py:L959](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L959)). Normalizes outbound values to canonical string UUIDs ([facets.py:L966](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L966)).
*   **[EmailFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L543-L560)**: Casts input to lowercase and matches against the regex format `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` ([facets.py:L546, L550, L553](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L546)).
*   **[URLFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L563-L582)**: Restricts values to standard HTTP/HTTPS schemes and formats via regex match ([facets.py:L566-L572, L575](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L566-L572)).
*   **[SlugFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L585-L602)**: Coerces to lowercase and validates that the string consists solely of alphanumeric characters, hyphens, and underscores (`^[-a-zA-Z0-9_]+$`) ([facets.py:L588, L591, L594](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L588)).
*   **[IPFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L605-L620)**: Uses Python's standard `ipaddress.ip_address` module during validation to ensure the string represents a valid IPv4 or IPv6 address ([facets.py:L609-L614](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L609-L614)).

---

### Collection Facets

Collection facets process nested objects or lists, providing comprehensive index tracking in error paths.

*   **[ListFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L977-L1041)**:
    *   **Parameters**: `child: Facet | None`, `min_items: int | None`, `max_items: int | None` ([facets.py:L985-L987](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L985-L987)).
    *   **Nested Errors**: During `cast` and `seal`, if a child validation fails, the index is appended to the field name path, producing clear error messages like `tags[2]` ([facets.py:L1006-L1007, L1022](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1006-L1007)).
*   **[SetFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1043-L1108)**:
    *   Same constraints as `ListFacet`, but enforces uniqueness. It casts inbound collections to Python `set` objects ([facets.py:L1064](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1064)) and formats them outbound as sorted lists ([facets.py:L1095-L1096](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1095-L1096)). Error path mapping defaults to wildcard index `[*]` ([facets.py:L1072, L1088](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1072)).
*   **[TupleFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1110-L1173)**:
    *   Enforces positional typing or bounds, casting inbound values to Python `tuple` objects ([facets.py:L1131](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1131)) and outputting lists. Maps index paths like `[0]`, `[1]`, etc. ([facets.py:L1139, L1155](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1139)).
*   **[DictFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1176-L1258)**:
    *   **Parameters**: `value_facet: Facet | None`, `max_keys: int | None` ([facets.py:L1184-L1187](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1184-L1187)).
    *   **Security Bounds**: Defends against Hash-Collision DoS attacks by restricting total dictionary keys to `max_keys` (defaults to `1000` keys) ([facets.py:L1182, L1203-L1207](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1182)).
    *   **Formatting**: Accepts raw dictionaries or parses stringified JSON structures starting with `{` ([facets.py:L1190-L1198](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1190-L1198)). Enforces that all keys are string types ([facets.py:L1211-L1212](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1211-L1212)). Maps error paths to the specific key, e.g., `metadata[item_id]` ([facets.py:L1215-L1219](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1215-L1219)).
*   **[JSONFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1261-L1314)**:
    *   Allows arbitrary JSON payloads.
    *   **Security Bounds**: Restricts nesting depth to prevent stack overflow exploits during parsing. The maximum depth limit is configurable via `max_depth` (defaults to `32`) ([facets.py:L1267, L1280, L1283-L1290](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1267)).
    *   **Type Allowlist**: Validates that all node structures consist only of types in `allowed_types` (defaults to `JSON_SAFE_TYPES`: `str, int, float, bool, NoneType, list, dict`) ([facets.py:L1270, L1281, L1290-L1294](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1270)).

---

### Special Facets

Specialized facets offer custom runtime behaviors such as read/write rules, dynamic output calculation, and dependency injection.

*   **[Computed](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1522-L1580)**:
    *   Forces `read_only=True` ([facets.py:L1533](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1533)).
    *   **Resolution Order**: Accepts a string (representing a method name) or a callable ([facets.py:L1532](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1532)). 
        1. If it's a string, it looks for that method on the bound `Contract` instance first ([facets.py:L1541-L1544](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1541-L1544)), falling back to calling a method on the model instance itself ([facets.py:L1546-L1549](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1546-L1549)).
        2. If it's a callable, it inspects its parameter signature using `inspect.signature`. If the signature contains 2 or more arguments, it is treated as an unbound class method. Computed walks module namespaces to instantiate a temporary parent `Contract` instance and calls the method as `func(contract_self, instance)` ([facets.py:L1553-L1573](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1553-L1573)). Otherwise, it invokes the callable directly as `func(instance)` ([facets.py:L1576](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1576)).
*   **[Constant](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1582-L1607)**:
    *   Forces `read_only=True` ([facets.py:L1594](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1594)). Always extracts and molds a fixed constant value, ignoring instance values ([facets.py:L1598-L1599, L1601-L1602](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1598-L1599)). Generates a schema with a JSON Schema `const` constraint ([facets.py:L1606](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1606)).
*   **[WriteOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1610-L1621)**:
    *   Inherits from `TextFacet`. Forces `write_only=True` ([facets.py:L1620](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1620)). Useful for inbound parameters like passwords.
*   **[ReadOnly](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1624-L1647)**:
    *   Forces `read_only=True` ([facets.py:L1634](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1634)). Automatically molds dates, times, decimals, UUIDs, and durations into standard JSON-compliant serialization formats ([facets.py:L1638-L1646](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1638-L1646)).
*   **[Hidden](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1650-L1662)**:
    *   Forces `write_only=True` and acts as a placeholder for internal defaults or system arguments (e.g., audit trails, transaction contexts). It is omitted from outbound response formats.
*   **[Inject](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1668-L1742)**:
    *   Forces `read_only=True` ([facets.py:L1695](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1695)). Resolves values from Aquilia's DI container or context arguments at validation time ([facets.py:L1701-L1702](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1701-L1702)).
    *   **Resolution Order**:
        1. Checks the DI container (`context.get("container")`) and calls `container.resolve(token)` ([facets.py:L1711-L1714](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1711-L1714)). If resolved, calls `via` (a method on the resolved service) or reads `attr` (attribute name) if configured ([facets.py:L1719-L1726](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1719-L1726)).
        2. Fallback: Checks the direct context dict (`context.get(token)`) to resolve context parameters like `"identity"` or `"request"` directly, then extracts `via`/`attr` properties as required ([facets.py:L1730-L1740](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1730-L1740)).

---

### Upload Facets

*   **[FileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1319-L1337)**: Simple file reference facet that accepts and returns path or URL strings ([facets.py:L1320, L1328-L1331](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1320)).
*   **[UploadFileFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1745-L1818)**:
    *   **Constraints**: `max_size: int | None` and `allowed_types: list[str] | None` ([facets.py:L1753-L1754](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1753-L1754)).
    *   **Inbound Cast**: Enforces that input values are instances of `UploadFile` ([facets.py:L1766-L1770](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1766-L1770)). Validates file sizes against `max_size` ([facets.py:L1772-L1777](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1772-L1777)) and validates content-types (MIME) using exact match or wildcards (e.g., `image/*`) against the `allowed_types` list ([facets.py:L1779-L1796](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1779-L1796)).
    *   **Outbound Mold**: Converts file references to metadata objects containing `filename`, `content_type`, and `size` properties ([facets.py:L1806-L1810](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1806-L1810)).
*   **[FormDataFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1820-L1867)**:
    *   Used for form field inputs. Builds an internal child facet dynamically from a type annotation using `_build_facet_from_annotation` ([facets.py:L1833-L1840](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1833-L1840)), and delegates all casting, sealing, and molding lifecycle methods directly to this child facet ([facets.py:L1846-L1848, L1853-L1855, L1859-L1860](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1846-L1848)).

---

### Choice & Enum Facets

*   **[ChoiceFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1342-L1379)**:
    *   **Parameters**: `choices: Sequence` ([facets.py:L1347](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1347)).
    *   **Input formats**: Can accept dictionaries (mapping valid keys to labels), lists of tuples/lists (representing `(key, label)` pairs), or flat sequences of simple choices ([facets.py:L1349-L1357](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1349-L1357)).
    *   **Validation**: Asserts values exist in the choices set, raising a `CastFault` detailing the invalid selection and a sorted list of permitted values ([facets.py:L1368-L1372](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1368-L1372)).
*   **[LiteralFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1381-L1387)**: Inherits from `ChoiceFacet`. Restricts the field's allowed options to a single literal value ([facets.py:L1385-L1386](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1385-L1386)).
*   **[EnumFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1389-L1456)**:
    *   **Parameters**: `enum_class: type` ([facets.py:L1392](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1392)).
    *   **Cast Coercion**: Attempts to match values directly. If the enum class inherits from `int` or `str`, it performs intermediate coercion of the raw input ([facets.py:L1409-L1418](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1409-L1418)). It also supports matching against the string names of the Enum members ([facets.py:L1424-L1425](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1424-L1425)).
    *   **Outbound Mold**: Serializes Enum values back to their underlying scalar values (`member.value`) ([facets.py:L1439-L1440](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1439-L1440)).

---

### FacetMeta Factory Methods

The [FacetMeta](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L94-L176) metaclass enables fluent, inline facet definitions using properties and helper functions on the base `Facet` class name ([facets.py:L94-L95](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L94-L95)).

#### Class Properties
Accessing these properties returns a factory proxy `_FactoryProxy` targeting specific classes ([facets.py:L98-L120](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L98-L120)):
*   `Facet.text` -> returns a factory proxy for `TextFacet` ([facets.py:L98-L99](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L98-L99)).
*   `Facet.int` -> returns a factory proxy for `IntFacet` ([facets.py:L102-L103](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L102-L103)).
*   `Facet.float` -> returns a factory proxy for `FloatFacet` ([facets.py:L106-L107](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L106-L107)).
*   `Facet.bool` -> returns a factory proxy for `BoolFacet` ([facets.py:L110-L111](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L110-L111)).
*   `Facet.list` -> returns a factory proxy for `ListFacet` ([facets.py:L114-L115](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L114-L115)).
*   `Facet.dict` -> returns a factory proxy for `DictFacet` ([facets.py:L118-L119](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L118-L119)).

#### Class Methods
Helpers to construct specialized facets with explicit options ([facets.py:L121-L176](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L121-L176)):
*   `Facet.pattern(regex, **kwargs)` ([facets.py:L121-L123](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L121-L123))
*   `Facet.email(**kwargs)` ([facets.py:L125-L127](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L125-L127))
*   `Facet.url(**kwargs)` ([facets.py:L129-L131](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L129-L131))
*   `Facet.uuid(**kwargs)` ([facets.py:L133-L135](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L133-L135))
*   `Facet.choice(choices, **kwargs)` ([facets.py:L137-L139](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L137-L139))
*   `Facet.date(**kwargs)` ([facets.py:L141-L143](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L141-L143))
*   `Facet.datetime(**kwargs)` ([facets.py:L145-L147](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L145-L147))
*   `Facet.decimal(**kwargs)` ([facets.py:L149-L151](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L149-L151))
*   `Facet.ip(**kwargs)` ([facets.py:L153-L155](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L153-L155))
*   `Facet.slug(**kwargs)` ([facets.py:L157-L159](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L157-L159))
*   `Facet.time(**kwargs)` ([facets.py:L161-L163](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L161-L163))
*   `Facet.json(**kwargs)` ([facets.py:L165-L167](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L165-L167))
*   `Facet.file(**kwargs)` ([facets.py:L169-L171](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L169-L171))
*   `Facet.duration(**kwargs)` ([facets.py:L173-L175](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L173-L175))

#### Subscript Proxy Syntax
The proxy class `_FactoryProxy` maps Python slice syntax to bounds constraints ([facets.py:L178-L224](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L178-L224)):

*   **`Facet.text[min_length:max_length]`**
    ```python
    username = Facet.text[3:20]
    ```
*   **`Facet.int[min_val:max_val:multiple_of]`**
    ```python
    percent = Facet.int[0:100:5]
    ```
*   **`Facet.float[min_val:max_val:multiple_of]`**
    ```python
    weight = Facet.float[0.5:20.0:0.1]
    ```
*   **`Facet.list[child_facet, min_items:max_items]`** or **`Facet.list[min_items:max_items]`**
    ```python
    tags = Facet.list[Facet.text[1:10], 1:5]
    simple_list = Facet.list[1:10]
    ```

---

### Model Field Autoderivation: `derive_facet`

The function [derive_facet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1917-L1986) automatically creates a correctly configured `Facet` from an Aquilia Model field.

1.  **Class Name Mapping**: Resolves the type of model field to a matching facet class using `MODEL_FIELD_TO_FACET` (e.g., `CharField` -> `TextFacet`, `UUIDField` -> `UUIDFacet`, etc.) ([facets.py:L1924-L1925, L1872-L1914](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1872-L1914)).
2.  **Nullability & Blankness**: Reads `.null` and `.blank` properties of the model field to configure `allow_null` and `allow_blank` on the facet ([facets.py:L1930-L1933](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1930)).
3.  **Read-Only Flags**: Automatically flags primary keys, non-editable fields (`editable=False`), or auto-updating date/time fields (`auto_now` or `auto_now_add`) as `read_only=True` ([facets.py:L1950-L1955](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1950)).
4.  **Required Inference**: If a field is not read-only, it marks `required=False` if the model field is nullable, blankable, or contains a default value ([facets.py:L1958-L1963](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1958)).
5.  **Choices**: If `.choices` exists, returns a `ChoiceFacet` directly ([facets.py:L1966-L1967](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1966)).
6.  **Type Constraints Extraction**: Automatically passes length limits (`max_length`), numeric boundaries (`min_value`/`max_value`), and decimal constraints (`max_digits`/`decimal_places`) to the new facet instance ([facets.py:L1970-L1985](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L1970)).

---

### Sentinel value: `UNSET`

The [UNSET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L88) object is a singleton instance of the private `_Unset` class ([facets.py:L71-L88](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L71-L88)). 

In Python, `None` is often a valid application value (e.g. clearing a nullable field by sending `{"middle_name": null}`). To distinguish between a field being explicitly set to null versus a field not being sent in the payload at all, Aquilia uses [UNSET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L88).
*   **Represents**: "no value provided".
*   **Behavior**:
    *   Returns `"<UNSET>"` for `__repr__` output ([facets.py:L81-L82](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L81)).
    *   Evaluates to `False` in conditional boolean checks ([facets.py:L84-L85](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L84)).

---

### ReDoS-Safe Regex Validation

To guard applications against Regular Expression Denial of Service (ReDoS) attacks, [TextFacet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L463-L541) enforces compile-time security validations on custom regex patterns:

1.  **Length Limit Check** ([facets.py:L485-L489](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L485-L489)):
    Custom patterns are limited to a maximum of `500` characters (`MAX_PATTERN_LENGTH = 500` ([facets.py:L469](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L469))). Exceeding this limit immediately raises a `CastFault`.
2.  **Nested Quantifier Detection** ([facets.py:L490-L502](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/facets.py#L490-L502)):
    Before compilation, patterns are checked against a defensive regex to identify nested or overlapping quantifiers (e.g., `(a+)+` or `(a*)*`) which cause catastrophic backtracking:
    ```python
    _nested_quantifier = re.compile(
        r"(\([^)]*[+*]\)[+*?]|\([^)]*\)\{[0-9,]+\}[+*?]|"
        r"[+*]\{[0-9,]+\}|[+*][+*])"
    )
    ```
    If a dangerous quantifier is detected, it raises a `CastFault`, advising developers to simplify the pattern or use a non-backtracking regex engine.

---

### Code Examples

#### 1. Basic Contract Definition
Using factory shortcuts and subscripts to define validation boundaries:

```python
from aquilia.contracts import Contract
from aquilia.contracts.facets import Facet, ChoiceFacet

class UserContract(Contract):
    # Text bounds using subscript syntax
    username = Facet.text[3:20]
    
    # Numeric bounds and multiples
    age = Facet.int[18:99]
    score = Facet.int[0:100:5]  # Multiple of 5
    
    # Email with standard regex constraints
    email = Facet.email()
    
    # Choices
    role = ChoiceFacet(choices=["admin", "editor", "viewer"])
```

#### 2. Advanced Special Facets: Computed, Constant & Inject
Utilizing injection and computed properties to shape runtime behaviors:

```python
from aquilia.contracts import Contract
from aquilia.contracts.facets import Facet, Computed, Constant, Inject

class OrderContract(Contract):
    # Constant API Version metadata
    api_version = Constant("v2")
    
    # Resolve value dynamically from direct context key (e.g. current user)
    processed_by = Inject("identity", attr="username")
    
    # Computed read-only value executing a contract method
    formatted_total = Computed("get_formatted_total")
    
    def get_formatted_total(self, order) -> str:
        return f"${order.total_amount:.2f}"
```

#### 3. Nested Collections
Defining structured document validators with lists and objects:

```python
from aquilia.contracts import Contract
from aquilia.contracts.facets import Facet, ListFacet, DictFacet

class ConfigContract(Contract):
    # A list containing text elements
    tags = Facet.list[Facet.text[1:15], 1:10]
    
    # A dictionary where values must adhere to FloatFacet constraints
    thresholds = DictFacet(
        value_facet=Facet.float[0.0:1.0], 
        max_keys=20
    )
```
