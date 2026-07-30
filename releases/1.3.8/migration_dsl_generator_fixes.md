# Migration DSL Generator Overhaul

## Overview

In Aquilia v1.3.8, the Migration DSL Generator (`aquilia.models.migration_gen` and `aquilia.models.schema_snapshot`) underwent a comprehensive architectural overhaul. The generator is responsible for transforming model definitions into schema snapshots (`create_snapshot()`), calculating diffs (`diff_to_operations()`), and emitting human-readable, executable Python DSL migration files (`generate_dsl_migration()`).

---

## Technical Details

### 1. Character-Split Index Column Normalization

#### Previous Behavior
When an index was declared using a single string or when `Index.deconstruct()` returned `fields: "token"`, `schema_snapshot.py` iterated over the string as a sequence (`list("token")`), splitting column names into character arrays:

```python
# Old Output (v1.3.7 Bug)
CreateIndex(
    name='idx_email_verification_t_o_k_e_n',
    table='email_verification',
    columns=['t', 'o', 'k', 'e', 'n'],
    unique=False,
)
```

#### New Implementation
`Index.__init__()` and `_PostgresOnlyIndex.__init__()` normalize `fields` arguments upon instantiation. Furthermore, `create_snapshot()` inspects and normalizes string column names into strict `list[str]` objects before building auto index names or emitting DSL `CreateIndex` operations:

```python
# New Output (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
)
```

---

### 2. Strict Foreign Key Target Table Resolution

#### Previous Behavior
When a `ForeignKey` field referenced a model using a string class name (e.g. `ForeignKey("UserModel")`), `_serialize_field()` fell back to lowercasing the raw string (`"usersmodel"`), ignoring `UserModel._meta.table_name` (`"users"`):

```python
# Old Output (v1.3.7 Bug)
C.foreign_key("user_id", "usersmodel", "id")
```

#### New Implementation
`_resolve_target_table(to_ref, model_classes)` resolves target table names through a multi-pass lookup pipeline:
1. Inspects `to_ref._meta.table_name` if `to_ref` is a `Model` subclass.
2. Scans `model_classes` passed to snapshot creation for matching `__name__` or `_meta.table_name`.
3. Queries `ModelRegistry` for registered model class metadata.
4. Applies a PascalCase-to-snake_case pluralization fallback (`"UserModel"` $\rightarrow$ `"users"`).

```python
# New Output (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)")
```

---

### 3. Model Attribute Name to Database Column Name Resolution

#### Previous Behavior
When indexes or constraints referenced model attribute names (e.g. `Index(fields=["user"])` or `UniqueConstraint(fields=["user", "role"])`), the generator emitted the Python attribute name (`"user"`) rather than the database column name (`"user_id"`):

```python
# Old Output (v1.3.7 Bug)
CreateIndex(name='idx_user_roles_user', table='user_roles', columns=['user'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user", "role")')
```

#### New Implementation
`_resolve_db_column_name(model_cls, field_or_name)` inspects `model_cls._fields` descriptors. If the field is a `ForeignKey` or has a custom `column_name`/`db_column` attribute, it extracts the actual database column name (`"user"` $\rightarrow$ `"user_id"`):

```python
# New Output (v1.3.8)
CreateIndex(name='idx_user_roles_user_id', table='user_roles', columns=['user_id'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user_id", "role")')
```

---

### 4. Foreign Key SQL Type Inference Consistency

#### Previous Behavior
If a foreign key target model (e.g., `UserModel` with UUID primary key `id = UUIDField(primary_key=True)`) was un-resolved at field initialization time, `_field_to_sql_type()` returned `"INTEGER"` for one model and `"VARCHAR(36)"` for another, causing column definition type mismatches in generated migrations.

#### New Implementation
`_field_to_sql_type(fld, model_classes=model_classes)` dynamically inspects `model_classes` and `ModelRegistry` during snapshot creation to determine the exact primary key SQL type of the target model (`"VARCHAR(36)"`), emitting `col_type="VARCHAR(36)"` consistently across all referencing foreign key column definitions.
