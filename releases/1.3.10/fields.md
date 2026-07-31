# Field Improvements — Aquilia v1.3.10

---

## `EnumField` — Dotted-String `enum_class` for Migration Round-Trips

### Problem

Generated migration files must be valid Python that can be imported by the migration executor. An `EnumField` declaration requires the actual `Enum` class to be present at import time. When `EnumField.deconstruct()` serializes the field for a migration file, it must write the class reference in a form that can be reconstructed.

### Solution: `_resolve_enum_class()`

`EnumField` now accepts a dotted-string path as `enum_class` in addition to the class itself:

```python
# Both of these are now valid:
status = EnumField(enum_class=UserStatus)                      # direct class reference
status = EnumField(enum_class="myapp.models.UserStatus")       # dotted-string path
```

The dotted-string form is what `deconstruct()` writes into generated migration files. At load time, `_resolve_enum_class()` imports the module and resolves the class.

### `_resolve_enum_class()` Behaviour

| Input | Result |
|---|---|
| `UserStatus` (an Enum subclass) | Returns `UserStatus` unchanged |
| `"myapp.models.UserStatus"` | Imports `myapp.models`, returns `UserStatus` |
| `"UserStatus"` (no module) | Raises `FieldValidationError` with clear message |
| `"myapp.models.NotAnEnum"` | Raises `FieldValidationError` after confirming it is not `Enum` |
| Import fails | Raises `FieldValidationError` with message including the original `ImportError` |

### Error Messages

The error message from `_resolve_enum_class()` includes the instruction to keep the enum importable:

```
FieldValidationError: enum_class: cannot import 'myapp.models.OldStatus':
No module named 'myapp.models'. The enum must remain importable for any
migration referencing it to load.
```

### Migration Round-Trip

```python
# Model definition
class Post(Model):
    status = EnumField(enum_class=PostStatus)

# What deconstruct() produces (written to migration file)
{
    "enum_class": "myapp.models.PostStatus",
    "max_length": 50,
    ...
}

# When the migration file is loaded, _resolve_enum_class("myapp.models.PostStatus")
# imports the module and returns the PostStatus class.
```

### Breaking Change

`EnumField(enum_class=...)` now validates the argument immediately at field construction time. Previously, passing an invalid `enum_class` would fail lazily (e.g. when accessing choices). This means invalid declarations fail loudly at import time instead of silently at runtime.

---

## `BigAutoField` — MySQL `BIGINT`

### Previous Behaviour

`BigAutoField.sql_type("mysql")` returned `"INTEGER"` (the SQLite fallback), which on MySQL is a 32-bit type — silently losing the 64-bit guarantee the field exists to provide.

### New Behaviour

```python
BigAutoField().sql_type("mysql")    # → "BIGINT"
BigAutoField().sql_type("sqlite")   # → "INTEGER"  (unchanged — SQLite INTEGER is 64-bit)
BigAutoField().sql_type("postgresql")  # → "BIGSERIAL"  (unchanged)
BigAutoField().sql_type("oracle")   # → "NUMBER(19)"  (unchanged)
```

**Why not `BIGINT` on SQLite?** Only the exact type string `INTEGER` aliases the 64-bit rowid on SQLite; `BIGINT` would silently lose the auto-increment behaviour.

---

## `SmallAutoField` — MySQL `SMALLINT`

Same fix as `BigAutoField`. `SmallAutoField.sql_type("mysql")` now returns `"SMALLINT"` instead of `"INTEGER"`.

```python
SmallAutoField().sql_type("mysql")       # → "SMALLINT"
SmallAutoField().sql_type("sqlite")      # → "INTEGER"  (unchanged)
SmallAutoField().sql_type("postgresql")  # → "SMALLSERIAL"  (unchanged)
SmallAutoField().sql_type("oracle")      # → "NUMBER(5)"  (unchanged)
```

---

## `GeneratedField` — `deconstruct()` for Snapshotting

### Problem

`GeneratedField` did not override `deconstruct()`. Without `expression`, `db_persist`, and `output_field` in the deconstructed dict, migration snapshotting was invisible to generated columns: a change to the expression would not be detected as a schema change, and the `GENERATED ALWAYS AS (...)` clause would be dropped from generated DDL entirely.

### Solution

`GeneratedField` now overrides `deconstruct()` to include:

```python
{
    "expression": "UPPER(name)",   # the SQL expression
    "db_persist": True,            # STORED vs VIRTUAL
    "output_field": {              # nested deconstruct() of the output field
        "__class__": "CharField",
        "max_length": 200,
        ...
    },
    ...
}
```

`output_field` is serialized as its own nested `deconstruct()` dict, keeping the result JSON-safe while still naming the concrete field class needed to resolve the column's SQL type.

### Before / After

```python
# Before v1.3.10: GeneratedField.deconstruct() returned only base Field fields
# Changes to expression or db_persist were invisible to the migration system

# After v1.3.10:
class Article(Model):
    title = CharField(max_length=200)
    title_upper = GeneratedField(
        expression="UPPER(title)",
        output_field=CharField(max_length=200),
        db_persist=True,
    )

# Running makemigrations now correctly captures the generated column.
# Changing the expression produces an AlterField operation.
```

---

## `compile_schema_expression()` — Moved to `expression` Module

### Change

The function `_compile_schema_expression` was previously defined in `aquilia.models.schema_snapshot` (now deleted). It has been reimplemented as the public function `compile_schema_expression` in `aquilia.models.expression`.

### New Import Path

```python
# Old (no longer exists)
from aquilia.models.schema_snapshot import _compile_schema_expression

# New
from aquilia.models.expression import compile_schema_expression
```

### What It Does

Renders a query-expression object (`F`, `Value`, `Func`, `CombinedExpression`, `RawSQL`, or any `Expression` with `as_sql`) as inline SQL text for use in schema artifacts (index/constraint DDL, snapshot diffing).

Unlike normal query compilation, this produces a single self-contained SQL string with parameters inlined (via naive `'` doubling) rather than a `(sql, params)` pair — appropriate for DDL contexts like `CREATE INDEX ... (expression)` where there is no query executor to bind parameters.

```python
from aquilia.models.expression import compile_schema_expression, F, Value, Func

compile_schema_expression(F("title"))               # → '"title"'
compile_schema_expression(Value("hello"))           # → "'hello'"
compile_schema_expression(F("author__name"))        # → '"author"."name"'
compile_schema_expression(Func("UPPER", F("title")))  # → 'UPPER("title")'
```

This function is used internally by `base.py` (unique constraint DDL), `fields_module.py` (Index DDL), and the new migration backends.

---

## Summary

| Field / Function | Change | Impact |
|---|---|---|
| `EnumField.enum_class` | Accepts dotted-string path for migration round-trips | Enables generated migration files to reconstruct `EnumField` |
| `BigAutoField.sql_type("mysql")` | Now `"BIGINT"` instead of `"INTEGER"` | Fixes silent 32-bit truncation on MySQL |
| `SmallAutoField.sql_type("mysql")` | Now `"SMALLINT"` instead of `"INTEGER"` | Fixes incorrect type on MySQL |
| `GeneratedField.deconstruct()` | Now includes `expression`, `db_persist`, `output_field` | Makes generated columns visible to migration snapshotting |
| `compile_schema_expression` | Moved to `expression.py` (public); removed from `schema_snapshot` | Updated import path required |
