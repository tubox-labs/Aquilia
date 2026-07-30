# ORM Field Deconstruction & Snapshot Serialization

## Overview

Aquilia v1.3.8 fixes scalar default unwrapping during model field serialization (`_serialize_field()`), snapshot generation (`create_snapshot()`), and DSL column rendering (`_render_column_def()`).

---

## Technical Details

### 1. Enum Default Value Unwrapping

#### Previous Behavior
When a model field used an `EnumField` or `Enum` default (e.g. `status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)`), `_serialize_field()` failed to serialize the raw Enum instance into JSON, falling back to string representation:

```python
# Snapshot JSON (v1.3.7 Bug)
"default": "<UserStatus.ACTIVE: 'active'>"

# Migration DSL (v1.3.7 Bug - SyntaxError line 61)
status = C.text("status", default=<UserStatus.ACTIVE: 'active'>)
```

When Python loaded the migration file, `ast.parse()` and `importlib` failed with `SyntaxError: invalid syntax`.

#### New Implementation
`_serialize_field()` now unwrap `Enum` defaults through `fld.to_db(val)` or by extracting `.value` / `.name` directly:

```python
if hasattr(fld, "default") and fld.default is not None:
    if fld.default is not UNSET:
        val = fld.default
        if isinstance(fld, EnumField):
            val = fld.to_db(val)
        elif isinstance(val, Enum):
            val = val.name if getattr(fld, "store_name", False) else val.value

        try:
            json.dumps(val)
            info["default"] = val
        except (TypeError, ValueError):
            info["default"] = str(val)
```

And `_format_default()` in `migration_dsl.py` formats Enum instances into Python string literals:

```python
# Snapshot JSON (v1.3.8)
"default": "active"

# Migration DSL (v1.3.8 - Valid Python)
C.text("status", default='active')
```

---

### 2. Snapshot Diffing & Column Definition Generation

`_snapshot_field_to_column_def()` converts serialized field dictionaries back into `ColumnDef` objects for operation rendering. In v1.3.8, `_render_column_def()` formats column helper calls matching the target database column definition:

```python
# Primary Key Column
C.varchar("id", 36, primary_key=True)

# Foreign Key Column
C.foreign_key("user_id", "users", "id", null=True, on_delete="CASCADE", col_type="VARCHAR(36)")

# Varchar Column with Default
C.varchar("email", 254, unique=True)
```
