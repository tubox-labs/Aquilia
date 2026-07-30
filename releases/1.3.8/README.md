# Aquilia v1.3.8 Release Notes — "Migration Architect"

Aquilia v1.3.8 introduces **DSL Migration Generator Architectural Overhaul**, **Topological Foreign Key Model Dependency Ordering**, **Character-Split Index Normalization**, **Strict Foreign Key Target Table Resolution**, **Scalar Enum Default Serialization**, and **Comprehensive Migration Dependencies Metadata** across the Aquilia Database and ORM Migration subsystem.

Before this release, auto-generated migration DSL files produced by `aq db makemigrations` (and `generate_dsl_migration()`) contained critical correctness bugs: index column names were split into single characters (`columns=['t', 'o', 'k', 'e', 'n']`), foreign key references targeted raw un-pluralized model class name stubs (`C.foreign_key("user_id", "usersmodel", "id")`), Enum field default values emitted stringified enum representation objects (`default=<UserStatus.ACTIVE: 'active'>`) breaking Python syntax, model creation operations were ordered arbitrarily rather than by foreign key dependencies, and index/constraint column targets failed to resolve model attribute names to actual database column names (`"user"` instead of `"user_id"`).

This release addresses all 19 identified migration DSL generator vulnerabilities, implements post-order topological dependency sorting (`_topologically_sort_models()`), adds strict foreign key target table resolution (`_resolve_target_table()`), normalizes database column resolution (`_resolve_db_column_name()`), unwraps Enum defaults to DB-storable primitive scalars, and adds migration dependency tracking metadata (`dependencies = [...]`).

---

## Table of Contents

1. [Migration DSL Generator Overhaul](migration_dsl_generator_fixes.md)
   - Index column normalization (fixing character-split index column arrays)
   - Foreign key target table resolution (`_resolve_target_table()`)
   - Model attribute to database column name mapping (`_resolve_db_column_name()`)
   - Foreign key SQL type inference consistency (`col_type="VARCHAR(36)"`)
2. [Topological Model Dependency Ordering](model_dependency_ordering.md)
   - Dependency graph construction for `CreateModel` operations
   - Post-order depth-first topological traversal (`_topologically_sort_models()`)
   - Self-referential and cyclic foreign key resolution
3. [ORM Field Deconstruction & Serialization](orm_field_deconstruct_serialization.md)
   - Scalar Enum default value unwrapping (`'active'` instead of `<Enum: 'active'>`)
   - Snapshot serialization (`create_snapshot()`) and diffing (`diff_to_operations()`)
   - Column definition generator (`_render_column_def()`)
4. [Bug Fixes](bugfixes.md)
   - Comprehensive audit of all 19 migration generator issues, root causes, and resolutions
5. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### 1. Character-Split Index Column Normalization

Index field declarations—whether provided as strings (`Index(fields="token")`), tuples, or list expressions—are strictly normalized into database column arrays (`columns=['token']`), eliminating corrupted index column arrays (`['t', 'o', 'k', 'e', 'n']`) and index names (`idx_email_verification_t_o_k_e_n`).

```python
# Generated Migration DSL (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
),
```

### 2. Foreign Key Target Table Resolution

Foreign key references dynamically resolve to actual database table names (`"users"`), taking into account `_meta.table_name` overrides, `ModelRegistry` lookups, and PascalCase-to-snake_case pluralization fallbacks.

```python
# Generated Migration DSL (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)"),
```

### 3. Scalar Enum Default Serialization

Enum defaults are unwrapped during snapshot serialization and code generation to DB-storable primitive scalar literals (`'active'` or `1`), ensuring generated Python migration files parse cleanly via `ast.parse()`.

```python
# Generated Migration DSL (v1.3.8)
C.text("status", default='active'),
```

### 4. Topological Model Creation Ordering

`CreateModel` operations in generated migrations are topologically sorted based on foreign key table dependencies. Referenced tables (`users`) are always created before dependent tables (`email_verification`, `user_roles`).

```python
# Generated Migration DSL (v1.3.8 operations list)
operations = [
    CreateModel(name='UserModel', table='users', fields=[...]),
    CreateModel(name='Post', table='posts', fields=[...]),
    CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[...]),
    CreateModel(name='UserRoleModel', table='user_roles', fields=[...]),
]
```

### 5. Migration Dependency Tracking Metadata

Generated migration modules now explicitly include prerequisite revision IDs in `Meta.dependencies`.

```python
class Meta:
    revision = "20260730_201500"
    slug = "post_useremailverificationmodel_and_2_more"
    models = ['Post', 'UserEmailVerificationModel', 'UserModel', 'UserRoleModel']
    dependencies = ['20260730_143000']
```

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| `aquilia.models.schema_snapshot` | Added `_resolve_db_column_name()`, `_resolve_target_table()`, `_topologically_sort_models()` | Resolves DB column names, FK target tables, and topological `CreateModel` execution order |
| `aquilia.models.migration_gen` | Updated `generate_dsl_migration()`, `_render_migration_file()`, `_render_column_def()` | Emits syntactically valid Python source text with dependencies metadata |
| `aquilia.models.migration_dsl` | Updated `_format_default()` | Unwraps Enum defaults to scalar Python literals in DSL column definitions |
| `aquilia.models.fields_module` | Updated `Index.__init__()` | Safely normalizes string or tuple `fields` parameters into string lists |
| `aquilia.models.index` | Updated `_PostgresOnlyIndex.__init__()` | Normalizes index column inputs across PostgreSQL index variants |
