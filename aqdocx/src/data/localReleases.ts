export const localReleases: Record<string, Record<string, string>> = {
  "1.3.9": {
    "README.md": `# Aquilia v1.3.9 Release Notes — "Database Sentinel"

Aquilia v1.3.9 introduces **Strict auto_migrate=False Enforcement**, **Non-Fatal Database Startup Readiness Model (DatabaseState)**, **Single-Authority Migration Engine Architecture (MigrationRunner, DDLExecutor, MigrationPlanner)**, and **Atomic Transactional DDL & Migration History Guarantees** across the Aquilia Database, ORM, and Server Startup subsystems.

---

## Table of Contents

1. [Strict auto_migrate=False Enforcement](auto_migrate_enforcement.md)
2. [Non-Fatal Database Startup Readiness (DatabaseState)](non_fatal_startup_guard.md)
3. [Atomic Transactional DDL Execution](atomic_ddl_transactions.md)
4. [Single-Authority Migration Engine Architecture](single_authority_migration_engine.md)
5. [DDL Executor & Migration Planner Architecture](ddl_executor_and_planner.md)
6. [Bug Fixes & Audit](bugfixes.md)
7. [Migration Guide & Upgrade Checklist](migration.md)
`,
    "auto_migrate_enforcement.md": `# Strict auto_migrate=False Schema Enforcement

In Aquilia v1.3.9, the framework strictly enforces the developer's \`auto_migrate=False\` setting across all startup phases.

When \`auto_migrate=False\` is set, Aquilia strictly guarantees that **no tables will be created**, **no schema will be modified**, and **no DDL statements will execute** on startup—even if \`auto_create=True\` is set on the integration.
`,
    "non_fatal_startup_guard.md": `# Non-Fatal Database Readiness Model (DatabaseState)

In Aquilia v1.3.9, database startup readiness checks no longer treat uninitialized databases as fatal process-crashing exceptions.

Introduced the \`DatabaseState\` enum in \`aquilia.models.startup_guard\`:
- \`READY\`
- \`MISSING_DATABASE\`
- \`PENDING_MIGRATIONS\`
- \`CORRUPTED_HISTORY\`
- \`SCHEMA_MISMATCH\`
- \`UNAVAILABLE\`
`,
    "atomic_ddl_transactions.md": `# Atomic Transactional DDL & Migration Rollback

In Aquilia v1.3.9, table creation (\`ModelRegistry.create_tables()\`) and migration application (\`MigrationRunner.execute_plan()\`) are executed within explicit database transaction blocks (\`async with db.transaction():\`).

If any DDL statement fails, all changes roll back cleanly, guaranteeing 0 partial tables or columns are left behind.
`,
    "single_authority_migration_engine.md": `# Single-Authority Migration Engine Architecture

In Aquilia v1.3.9, the database schema creation and migration execution pipeline is unified under a single authority: the **Migration Engine** (\`MigrationRunner\`, \`MigrationPlanner\`, and \`DDLExecutor\`).

\`ModelRegistry\` has been completely stripped of DDL execution authority. It delegates \`create_tables()\` and \`drop_tables()\` directly to \`MigrationRunner\`. Initial schema creation is recorded as \`0000_initial_schema\` in \`aquilia_migrations\`.
`,
    "ddl_executor_and_planner.md": `# DDL Executor & Migration Planner Architecture

Aquilia v1.3.9 introduces \`DDLExecutor\` and \`MigrationPlanner\` in \`aquilia.models\`.

- \`DDLExecutor\`: Compiles DSL operations into strongly-typed \`ExecutableStatement\` objects with \`StatementType\` categories (\`CREATE_TABLE\`, \`ALTER_TABLE\`, \`CREATE_INDEX\`, etc.) and executes them atomically.
- \`InitialSchemaPlanner\`: Plans zero-revision initial schema creation directly from model descriptors without empty-snapshot diffing.
- \`DatabaseAdapter.should_ignore_ddl_error()\`: Encapsulates dialect-specific DDL error codes (e.g. MySQL 1061/1091).
`,
    "bugfixes.md": `# Bug Fixes & Deep Audit Report (v1.3.9)

Resolved Bug 1 (auto_migrate=False bypassed by auto_create), Bug 2 (Database not ready fatal SchemaFault), and Bug 3 (Partial schema pollution on DDL failure).
`,
    "migration.md": `# Migration & Upgrade Guide for Aquilia v1.3.9

Fully backward-compatible release. Run \`aq db migrate\` in CI/CD pipeline when deploying with \`auto_migrate=False\`. Initial schema creation is tracked cleanly under \`0000_initial_schema\`.
`
  },
  "1.3.8": {
    "README.md": `# Aquilia v1.3.8 Release Notes — "Migration Architect"

Aquilia v1.3.8 introduces **DSL Migration Generator Architectural Overhaul**, **Topological Foreign Key Model Dependency Ordering**, **Character-Split Index Normalization**, **Strict Foreign Key Target Table Resolution**, **Scalar Enum Default Serialization**, and **Comprehensive Migration Dependencies Metadata** across the Aquilia Database and ORM Migration subsystem.

Before this release, auto-generated migration DSL files produced by \`aq db makemigrations\` (and \`generate_dsl_migration()\`) contained critical correctness bugs: index column names were split into single characters (\`columns=['t', 'o', 'k', 'e', 'n']\`), foreign key references targeted raw un-pluralized model class name stubs (\`C.foreign_key("user_id", "usersmodel", "id")\`), Enum field default values emitted stringified enum representation objects (\`default=<UserStatus.ACTIVE: 'active'>\`) breaking Python syntax, model creation operations were ordered arbitrarily rather than by foreign key dependencies, and index/constraint column targets failed to resolve model attribute names to actual database column names (\`"user"\` instead of \`"user_id"\`).

This release addresses all 19 identified migration DSL generator vulnerabilities, implements post-order topological dependency sorting (\`_topologically_sort_models()\`), adds strict foreign key target table resolution (\`_resolve_target_table()\`), normalizes database column resolution (\`_resolve_db_column_name()\`), unwraps Enum defaults to DB-storable primitive scalars, and adds migration dependency tracking metadata (\`dependencies = [...]\`).

---

## Table of Contents

1. [Migration DSL Generator Overhaul](migration_dsl_generator_fixes.md)
   - Index column normalization (fixing character-split index column arrays)
   - Foreign key target table resolution (\`_resolve_target_table()\`)
   - Model attribute to database column name mapping (\`_resolve_db_column_name()\`)
   - Foreign key SQL type inference consistency (\`col_type="VARCHAR(36)"\`)
2. [Topological Model Dependency Ordering](model_dependency_ordering.md)
   - Dependency graph construction for \`CreateModel\` operations
   - Post-order depth-first topological traversal (\`_topologically_sort_models()\`)
   - Self-referential and cyclic foreign key resolution
3. [ORM Field Deconstruction & Serialization](orm_field_deconstruct_serialization.md)
   - Scalar Enum default value unwrapping (\`'active'\` instead of \`<Enum: 'active'>\`)
   - Snapshot serialization (\`create_snapshot()\`) and diffing (\`diff_to_operations()\`)
   - Column definition generator (\`_render_column_def()\`)
4. [Bug Fixes](bugfixes.md)
   - Comprehensive audit of all 19 migration generator issues, root causes, and resolutions
5. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### 1. Character-Split Index Column Normalization

Index field declarations—whether provided as strings (\`Index(fields="token")\`), tuples, or list expressions—are strictly normalized into database column arrays (\`columns=['token']\`), eliminating corrupted index column arrays (\`['t', 'o', 'k', 'e', 'n']\`) and index names (\`idx_email_verification_t_o_k_e_n\`).

\`\`\`python
# Generated Migration DSL (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
),
\`\`\`

### 2. Foreign Key Target Table Resolution

Foreign key references dynamically resolve to actual database table names (\`"users"\`), taking into account \`_meta.table_name\` overrides, \`ModelRegistry\` lookups, and PascalCase-to-snake_case pluralization fallbacks.

\`\`\`python
# Generated Migration DSL (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)"),
\`\`\`

### 3. Scalar Enum Default Serialization

Enum defaults are unwrapped during snapshot serialization and code generation to DB-storable primitive scalar literals (\`'active'\` or \`1\`), ensuring generated Python migration files parse cleanly via \`ast.parse()\`.

\`\`\`python
# Generated Migration DSL (v1.3.8)
C.text("status", default='active'),
\`\`\`

### 4. Topological Model Creation Ordering

\`CreateModel\` operations in generated migrations are topologically sorted based on foreign key table dependencies. Referenced tables (\`users\`) are always created before dependent tables (\`email_verification\`, \`user_roles\`).

\`\`\`python
# Generated Migration DSL (v1.3.8 operations list)
operations = [
    CreateModel(name='UserModel', table='users', fields=[...]),
    CreateModel(name='Post', table='posts', fields=[...]),
    CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[...]),
    CreateModel(name='UserRoleModel', table='user_roles', fields=[...]),
]
\`\`\`

### 5. Migration Dependency Tracking Metadata

Generated migration modules now explicitly include prerequisite revision IDs in \`Meta.dependencies\`.

\`\`\`python
class Meta:
    revision = "20260730_201500"
    slug = "post_useremailverificationmodel_and_2_more"
    models = ['Post', 'UserEmailVerificationModel', 'UserModel', 'UserRoleModel']
    dependencies = ['20260730_143000']
\`\`\`

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| \`aquilia.models.schema_snapshot\` | Added \`_resolve_db_column_name()\`, \`_resolve_target_table()\`, \`_topologically_sort_models()\` | Resolves DB column names, FK target tables, and topological \`CreateModel\` execution order |
| \`aquilia.models.migration_gen\` | Updated \`generate_dsl_migration()\`, \`_render_migration_file()\`, \`_render_column_def()\` | Emits syntactically valid Python source text with dependencies metadata |
| \`aquilia.models.migration_dsl\` | Updated \`_format_default()\` | Unwraps Enum defaults to scalar Python literals in DSL column definitions |
| \`aquilia.models.fields_module\` | Updated \`Index.__init__()\` | Safely normalizes string or tuple \`fields\` parameters into string lists |
| \`aquilia.models.index\` | Updated \`_PostgresOnlyIndex.__init__()\` | Normalizes index column inputs across PostgreSQL index variants |
`,
    "migration_dsl_generator_fixes.md": `# Migration DSL Generator Overhaul

## Overview

In Aquilia v1.3.8, the Migration DSL Generator (\`aquilia.models.migration_gen\` and \`aquilia.models.schema_snapshot\`) underwent a comprehensive architectural overhaul. The generator is responsible for transforming model definitions into schema snapshots (\`create_snapshot()\`), calculating diffs (\`diff_to_operations()\`), and emitting human-readable, executable Python DSL migration files (\`generate_dsl_migration()\`).

---

## Technical Details

### 1. Character-Split Index Column Normalization

#### Previous Behavior
When an index was declared using a single string or when \`Index.deconstruct()\` returned \`fields: "token"\`, \`schema_snapshot.py\` iterated over the string as a sequence (\`list("token")\`), splitting column names into character arrays:

\`\`\`python
# Old Output (v1.3.7 Bug)
CreateIndex(
    name='idx_email_verification_t_o_k_e_n',
    table='email_verification',
    columns=['t', 'o', 'k', 'e', 'n'],
    unique=False,
)
\`\`\`

#### New Implementation
\`Index.__init__()\` and \`_PostgresOnlyIndex.__init__()\` normalize \`fields\` arguments upon instantiation. Furthermore, \`create_snapshot()\` inspects and normalizes string column names into strict \`list[str]\` objects before building auto index names or emitting DSL \`CreateIndex\` operations:

\`\`\`python
# New Output (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
)
\`\`\`

---

### 2. Strict Foreign Key Target Table Resolution

#### Previous Behavior
When a \`ForeignKey\` field referenced a model using a string class name (e.g. \`ForeignKey("UserModel")\`), \`_serialize_field()\` fell back to lowercasing the raw string (\`"usersmodel"\`), ignoring \`UserModel._meta.table_name\` (\`"users"\`):

\`\`\`python
# Old Output (v1.3.7 Bug)
C.foreign_key("user_id", "usersmodel", "id")
\`\`\`

#### New Implementation
\`_resolve_target_table(to_ref, model_classes)\` resolves target table names through a multi-pass lookup pipeline:
1. Inspects \`to_ref._meta.table_name\` if \`to_ref\` is a \`Model\` subclass.
2. Scans \`model_classes\` passed to snapshot creation for matching \`__name__\` or \`_meta.table_name\`.
3. Queries \`ModelRegistry\` for registered model class metadata.
4. Applies a PascalCase-to-snake_case pluralization fallback (\`"UserModel"\` -> \`"users"\`).

\`\`\`python
# New Output (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)")
\`\`\`

---

### 3. Model Attribute Name to Database Column Name Resolution

#### Previous Behavior
When indexes or constraints referenced model attribute names (e.g. \`Index(fields=["user"])\` or \`UniqueConstraint(fields=["user", "role"])\`), the generator emitted the Python attribute name (\`"user"\`) rather than the database column name (\`"user_id"\`):

\`\`\`python
# Old Output (v1.3.7 Bug)
CreateIndex(name='idx_user_roles_user', table='user_roles', columns=['user'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user", "role")')
\`\`\`

#### New Implementation
\`_resolve_db_column_name(model_cls, field_or_name)\` inspects \`model_cls._fields\` descriptors. If the field is a \`ForeignKey\` or has a custom \`column_name\`/\`db_column\` attribute, it extracts the actual database column name (\`"user"\` -> \`"user_id"\`):

\`\`\`python
# New Output (v1.3.8)
CreateIndex(name='idx_user_roles_user_id', table='user_roles', columns=['user_id'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user_id", "role")')
\`\`\`

---

### 4. Foreign Key SQL Type Inference Consistency

#### Previous Behavior
If a foreign key target model (e.g., \`UserModel\` with UUID primary key \`id = UUIDField(primary_key=True)\`) was un-resolved at field initialization time, \`_field_to_sql_type()\` returned \`"INTEGER"\` for one model and \`"VARCHAR(36)"\` for another, causing column definition type mismatches in generated migrations.

#### New Implementation
\`_field_to_sql_type(fld, model_classes=model_classes)\` dynamically inspects \`model_classes\` and \`ModelRegistry\` during snapshot creation to determine the exact primary key SQL type of the target model (\`"VARCHAR(36)"\`), emitting \`col_type="VARCHAR(36)"\` consistently across all referencing foreign key column definitions.
`,
    "model_dependency_ordering.md": `# Topological Model Dependency Ordering

## Overview

In Aquilia v1.3.8, \`diff_to_operations()\` implements post-order topological dependency sorting (\`_topologically_sort_models()\`) for \`CreateModel\` operations in generated migrations.

---

## The Problem

Before v1.3.8, added models in a migration diff were processed in simple alphabetical order. For example, given the models:

- \`Post\` (table \`posts\`)
- \`UserEmailVerificationModel\` (table \`email_verification\`, referencing \`users.id\`)
- \`UserModel\` (table \`users\`, primary key \`id\`)
- \`UserRoleModel\` (table \`user_roles\`, referencing \`users.id\`)

Alphabetical iteration produced \`CreateModel\` operations in the following sequence:

1. \`CreateModel(name='Post', table='posts', ...)\`
2. \`CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[C.foreign_key("user_id", "users", "id"), ...])\`
3. \`CreateModel(name='UserModel', table='users', ...)\`
4. \`CreateModel(name='UserRoleModel', table='user_roles', fields=[C.foreign_key("user_id", "users", "id"), ...])\`

When the migration runner attempted to execute \`CREATE TABLE email_verification\` on PostgreSQL or SQLite with foreign key enforcement active, the execution failed with:

\`\`\`
[MIGRATION_FAILED] Cannot add foreign key constraint: table 'users' does not exist
\`\`\`

---

## Architectural Implementation

### Dependency Graph Construction & Topological Sorting

\`_topologically_sort_models(added_models, models_data)\` constructs a directed dependency graph where:
- Each node represents an added model name.
- A directed edge A -> B indicates that Model A contains a \`ForeignKey\` referencing Model B's database table (B != A).

\`\`\`python
def _topologically_sort_models(
    added_models: list[str],
    models_data: dict[str, Any],
) -> list[str]:
    if len(added_models) <= 1:
        return added_models

    table_to_model = {}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        t_name = m_info.get("table", m_name.lower())
        table_to_model[t_name] = m_name

    deps: dict[str, set[str]] = {m: set() for m in added_models}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        fields = m_info.get("fields", {})
        for f_info in fields.values():
            ref = f_info.get("references")
            if ref and isinstance(ref, dict):
                ref_table = ref.get("table")
                if ref_table and ref_table in table_to_model:
                    target_m = table_to_model[ref_table]
                    if target_m != m_name:
                        deps[m_name].add(target_m)

    sorted_models: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            return
        if node not in visited:
            visiting.add(node)
            for dep in sorted(deps[node]):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_models.append(node)

    for m_name in sorted(added_models):
        if m_name not in visited:
            visit(m_name)

    return sorted_models
\`\`\`

---

## Execution Guarantees

1. **Dependency First**: Tables referenced by foreign keys (\`users\`) are guaranteed to appear in \`CreateModel\` operations before tables that reference them (\`email_verification\`, \`user_roles\`).
2. **Cycle Safety**: Self-referential models (Model A -> Model A) ignore self-loops, and circular dependencies (Model A -> Model B -> Model A) are broken gracefully without recursion errors.
3. **Determinism**: Ties are broken using sorted model names, ensuring byte-for-byte deterministic migration file generation across platforms.
`,
    "orm_field_deconstruct_serialization.md": `# ORM Field Deconstruction & Snapshot Serialization

## Overview

Aquilia v1.3.8 fixes scalar default unwrapping during model field serialization (\`_serialize_field()\`), snapshot generation (\`create_snapshot()\`), and DSL column rendering (\`_render_column_def()\`).

---

## Technical Details

### 1. Enum Default Value Unwrapping

#### Previous Behavior
When a model field used an \`EnumField\` or \`Enum\` default (e.g. \`status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)\`), \`_serialize_field()\` failed to serialize the raw Enum instance into JSON, falling back to string representation:

\`\`\`python
# Snapshot JSON (v1.3.7 Bug)
"default": "<UserStatus.ACTIVE: 'active'>"

# Migration DSL (v1.3.7 Bug - SyntaxError line 61)
status = C.text("status", default=<UserStatus.ACTIVE: 'active'>)
\`\`\`

When Python loaded the migration file, \`ast.parse()\` and \`importlib\` failed with \`SyntaxError: invalid syntax\`.

#### New Implementation
\`_serialize_field()\` now unwrap \`Enum\` defaults through \`fld.to_db(val)\` or by extracting \`.value\` / \`.name\` directly:

\`\`\`python
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
\`\`\`

And \`_format_default()\` in \`migration_dsl.py\` formats Enum instances into Python string literals:

\`\`\`python
# Snapshot JSON (v1.3.8)
"default": "active"

# Migration DSL (v1.3.8 - Valid Python)
C.text("status", default='active')
\`\`\`

---

### 2. Snapshot Diffing & Column Definition Generation

\`_snapshot_field_to_column_def()\` converts serialized field dictionaries back into \`ColumnDef\` objects for operation rendering. In v1.3.8, \`_render_column_def()\` formats column helper calls matching the target database column definition:

\`\`\`python
# Primary Key Column
C.varchar("id", 36, primary_key=True)

# Foreign Key Column
C.foreign_key("user_id", "users", "id", null=True, on_delete="CASCADE", col_type="VARCHAR(36)")

# Varchar Column with Default
C.varchar("email", 254, unique=True)
\`\`\`
`,
    "bugfixes.md": `# Comprehensive Bug Fixes in v1.3.8

This document details all 19 bug fixes and correctness improvements implemented in Aquilia v1.3.8.

---

## 1. Character-Split Index Columns (Critical)

- **Previous Behavior**: \`Index(fields="token")\` or tuple inputs converted column strings to character arrays (\`columns=['t', 'o', 'k', 'e', 'n']\`).
- **Root Cause**: \`Index.deconstruct()\` returned \`fields: "token"\`. Snapshot logic called \`list("token")\`, splitting the string into single characters.
- **New Behavior**: Strictly normalizes string fields into string lists (\`columns=['token']\`).

---

## 2. Foreign Key Target Table Name Mismatch (Critical)

- **Previous Behavior**: Foreign key references emitted raw low-cased class stubs (\`C.foreign_key("user_id", "usersmodel", "id")\`).
- **Root Cause**: Unbound string target model names (\`"UserModel"\`) bypassed model registry resolution and fell back to \`to.lower()\`.
- **New Behavior**: \`_resolve_target_table()\` queries model classes, metadata, and registry to resolve actual database table names (\`"users"\`).

---

## 3. Un-serializable Enum Default Repr Syntax Error (Critical)

- **Previous Behavior**: \`default=<UserStatus.ACTIVE: 'active'>\` emitted in migration DSL, causing \`SyntaxError\` on import.
- **Root Cause**: \`_serialize_field()\` stringified Enum objects when \`json.dumps()\` failed instead of unwrapping \`.value\` or calling \`to_db()\`.
- **New Behavior**: Unwraps Enum default instances to scalar primitives (\`default='active'\`).

---

## 4. Wrong Index Name Generation (High)

- **Previous Behavior**: \`_auto_index_name\` produced corrupted names like \`idx_email_verification_t_o_k_e_n\`.
- **Root Cause**: \`_auto_index_name\` joined character-split arrays (\`"_".join(['t', 'o', 'k', 'e', 'n'])\`).
- **New Behavior**: Uses normalized column lists, producing \`idx_email_verification_token\`.

---

## 5. Index Column Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: \`Index(fields=["user"])\` produced \`columns=['user']\` instead of \`columns=['user_id']\`.
- **Root Cause**: Generator serialized model attribute names directly without mapping through descriptor column names.
- **New Behavior**: \`_resolve_db_column_name()\` maps model attributes to database column names (\`"user"\` -> \`"user_id"\`).

---

## 6. Unique Constraint Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: \`UniqueConstraint(fields=["user", "role"])\` produced \`UNIQUE ("user", "role")\`.
- **Root Cause**: Constraint fields were not resolved to underlying database column names.
- **New Behavior**: Maps constraint fields to database column names, producing \`UNIQUE ("user_id", "role")\`.

---

## 7. Foreign Key Column Type Inference Inconsistency (High)

- **Previous Behavior**: Foreign key column types defaulted to \`"INTEGER"\` on some models and \`"VARCHAR(36)"\` on others.
- **Root Cause**: \`_field_to_sql_type()\` failed to inspect target model primary key types for string references.
- **New Behavior**: Dynamically resolves target model primary key types (\`"VARCHAR(36)"\`), ensuring type consistency across models.

---

## 8. Table Naming Inconsistency Across Model References (High)

- **Previous Behavior**: String reference targets were inconsistently resolved depending on model declaration order.
- **Root Cause**: Lack of unified target table resolution pipeline.
- **New Behavior**: Unified target table resolution pipeline guarantees consistent table names regardless of declaration order.

---

## 9. Missing Foreign Key Metadata (Medium)

- **Previous Behavior**: \`on_delete\`, \`on_update\`, and \`null=True\` were omitted from generated DSL foreign key calls.
- **Root Cause**: Generator omitted default options from rendered \`C.foreign_key()\` argument strings.
- **New Behavior**: \`_render_column_def()\` renders all non-default foreign key metadata.

---

## 10. Reverse Relation Metadata Leakage in DDL (Medium)

- **Previous Behavior**: Reverse relation descriptors populated metadata into snapshot field maps.
- **Root Cause**: Descriptor scanning did not filter out virtual relation properties.
- **New Behavior**: Virtual relation properties are handled cleanly without polluting DDL operation definitions.

---

## 11. Field Options & Timestamp Metadata Loss (Medium)

- **Previous Behavior**: \`auto_now\` and \`auto_now_add\` flags were omitted from snapshot metadata.
- **Root Cause**: \`_serialize_field()\` did not record timestamp flags.
- **New Behavior**: Captures timestamp metadata cleanly in snapshot definitions.

---

## 12. Case-Insensitive Unique Constraint DDL Generation (Medium)

- **Previous Behavior**: Case-insensitive fields emitted broken constraint DDL.
- **Root Cause**: \`CIEmailField\` expression unique constraints were formatted without parenthesis escaping.
- **New Behavior**: Properly compiles schema expressions for case-insensitive unique constraints.

---

## 13. Redundant Column-Level Uniqueness (Medium)

- **Previous Behavior**: Fields with table-level unique constraints also emitted \`unique=True\` on column definitions.
- **Root Cause**: Generator did not check table-level constraint duplicates.
- **New Behavior**: Suppresses redundant column-level \`unique=True\` when expression-based unique constraints exist.

---

## 14. Arbitrary Model Dependency Creation Ordering (Critical)

- **Previous Behavior**: \`CreateModel\` operations were emitted in alphabetical order, causing foreign key creation crashes.
- **Root Cause**: Added models list was iterated without topological dependency analysis.
- **New Behavior**: \`_topologically_sort_models()\` sorts \`CreateModel\` operations dependency-first.

---

## 15. Migration Revision Dependency Metadata Omission (Medium)

- **Previous Behavior**: \`Meta.dependencies\` was omitted from generated migration source text.
- **Root Cause**: Generator did not collect previous migration revision IDs.
- **New Behavior**: Scans \`migrations_dir\` and includes \`dependencies = ['<prev_rev>']\` in \`Meta\`.

---

## 16. State Operation Support (Low)

- **Previous Behavior**: Migration DSL did not support custom SQL state operations cleanly.
- **Root Cause**: Lack of \`RunSQL\` operation rendering.
- **New Behavior**: Full support for \`RunSQL\` rendering and execution.

---

## 17. Field Options Preservation (Low)

- **Previous Behavior**: Options like \`max_digits\` and \`decimal_places\` were lost during snapshot roundtripping.
- **Root Cause**: Missing parameter serialization in \`_serialize_field()\`.
- **New Behavior**: Preserves all field parameters cleanly.

---

## 18. Nullable Foreign Key Definition Rendering (Low)

- **Previous Behavior**: Nullable foreign keys emitted \`null=False\` in rendered DSL column definitions.
- **Root Cause**: \`nullable\` property was not passed to \`C.foreign_key()\`.
- **New Behavior**: Emits \`C.foreign_key(..., null=True)\` when \`nullable=True\`.

---

## 19. Postgres Index Abstraction Support (Low)

- **Previous Behavior**: Custom Postgres index variants (\`GinIndex\`, \`GistIndex\`) dropped \`condition\` or \`opclasses\`.
- **Root Cause**: Generator omitted index options in snapshot dict.
- **New Behavior**: Preserves condition and operator class overrides in index snapshot metadata.
`,
    "migration.md": `# Aquilia v1.3.8 Migration Guide

## Upgrade Overview

Aquilia v1.3.8 is a **zero-breaking-change patch release** focused on ORM Migration DSL Generator correctness, topological model dependency sorting, and snapshot serialization robustness.

All existing code, model definitions, and applied database migrations remain 100% compatible with v1.3.8.

---

## Upgrade Steps

### 1. Upgrade Package Version

Upgrade Aquilia in your environment via \`pip\` or \`uv\`:

\`\`\`bash
pip install --upgrade aquilia==1.3.8
\`\`\`

Or using \`uv\`:

\`\`\`bash
uv add aquilia==1.3.8
\`\`\`

### 2. Verify Generated Migrations

If you previously generated migration DSL files with v1.3.7 that experienced syntax errors (such as \`default=<UserStatus.ACTIVE: 'active'>\`) or character-split indexes (\`columns=['t', 'o', 'k', 'e', 'n']\`), delete those un-applied migration files and re-run:

\`\`\`bash
aq db makemigrations
\`\`\`

The newly generated migration files will automatically incorporate:
- Topological model creation order (\`users\` created before \`email_verification\`).
- Resolved target table names (\`"users"\` instead of \`"usersmodel"\`).
- Resolved database column names (\`"user_id"\` instead of \`"user"\`).
- Clean scalar Enum defaults (\`default='active'\`).
- Valid index column arrays (\`columns=['token']\`).

### 3. Apply Pending Migrations

Execute the migration runner:

\`\`\`bash
aq db migrate
\`\`\`

---

## Compatibility Summary

| Component | Status | Notes |
|---|---|---|
| Model Definitions | 100% Compatible | No changes required to \`Model\` or \`Field\` declarations. |
| Existing Applied Migrations | 100% Compatible | Applied migration files in \`migrations/\` continue to work without modification. |
| Migration Runner | Enhanced | Fully supports topological model execution and dependencies metadata. |
| Database Engines | 100% Compatible | Verified against SQLite, PostgreSQL, MySQL, and Oracle. |
`
  },
  "1.3.7": {
    "README.md": `# Aquilia v1.3.7 Release Notes — "Thread Sentinel"

Aquilia v1.3.7 introduces **Thread-Safe Model Registration & Descriptor Access**, **Type-Annotated Nested Contract Facets**, **Multi-Dialect Database Field Conversions**, and **Comprehensive 10-Point Standard Docstrings** across core Contract primitives.

Before this release, concurrent multi-threaded execution could experience subtle race conditions when registering models or accessing manager descriptors on model subclasses. Furthermore, imprinting contracts back into ORM models containing \`EnumField\` or \`CompositeField\` raised a \`TypeError\` due to missing dialect parameters, and nested contracts required verbose \`NestedContractFacet\` explicit declarations rather than standard Python type hints.

This release addresses all concurrency vulnerabilities with re-entrant locking (\`threading.RLock\`) in \`ModelRegistry\`, implements thread-isolated descriptor binding copies in \`BaseManager\`, enables type hint introspection for \`NestedContractFacet\`, extends dialect support across all ORM field conversions, and adds industry-grade 10-point documentation to the entire Contracts subsystem.

---

## Table of Contents

1. [Thread-Safe Model Registry](thread_safe_registry.md)
   - \`ModelRegistry\` thread safety via \`threading.RLock\`
   - Re-entrant locking strategy across registration, lookup, reset, and DDL
   - Reverse relation cache invalidation (\`_clear_reverse_relation_caches()\`)
2. [Manager Descriptor Thread Safety](manager_descriptor_thread_safety.md)
   - Subclass manager lookup isolation via bound shallow copies (\`copy.copy\`)
   - Strict descriptor access rules (\`ManagerInstanceAccessFault\`)
3. [Nested Contract Type Hint Annotations](nested_contract_annotations.md)
   - Python type hint introspection for \`NestedContractFacet\`
   - Support for \`NestedContractFacet[SubContract]\`, \`SubContract\`, and \`list[...]\`
4. [Multi-Dialect Field Conversions](field_dialect_support.md)
   - \`dialect\` parameter support in \`EnumField.to_db()\` and \`CompositeField.to_db()\`
   - Seamless contract imprinting (\`contract.imprint()\`) across SQLite, Postgres, MySQL, and Oracle
5. [Contract Standardized Docstrings](contract_docstrings.md)
   - 10-point industry docstring coverage across \`facets.py\`, \`exceptions.py\`, \`integration.py\`, \`lenses.py\`, \`pipeline.py\`, \`projections.py\`, \`schema.py\`, and \`ward.py\`
6. [Bug Fixes](bugfixes.md)
   - Critical fixes in model imprinting, registry concurrency, and manager descriptor binding
7. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### Thread-Safe ModelRegistry & Reverse-Relation Invalidation

All global model registry operations are now fully thread-safe, guarded by a re-entrant \`threading.RLock\`. Additionally, registering new models or resetting the registry automatically invalidates lazily-cached reverse foreign key lookups across all registered models.

\`\`\`python
import threading
from aquilia.models import ModelRegistry

def worker_thread(model_cls):
    # Safe concurrent registration across worker threads
    ModelRegistry.register(model_cls)
\`\`\`

### Thread-Isolated Subclass Managers

\`BaseManager.__get__()\` now creates a thread-isolated bound shallow copy when accessed on model subclasses, ensuring concurrent queries on inherited managers never corrupt shared manager state.

\`\`\`python
class BaseItem(Model):
    objects = Manager()

class ConcreteItem(BaseItem):
    pass

# Accessing SubModel.objects dynamically binds to SubModel safely in multi-threaded environments
items = await ConcreteItem.objects.all()
\`\`\`

### Type-Annotated Nested Contracts

Declare nested contract structures cleanly using standard Python type annotations. \`ContractMeta\` automatically wraps direct contract classes or \`NestedContractFacet[...]\` annotations.

\`\`\`python
class NameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class UserRegistrationContract(Contract[UserModel]):
    # Modern Python type annotation syntax:
    name: NameContract
    aliases: list[NameContract]
\`\`\`

### Multi-Dialect Field Support in Contract Imprinting

\`EnumField.to_db()\` and \`CompositeField.to_db()\` now accept the \`dialect\` keyword argument (defaulting to \`"sqlite"\`), preventing runtime \`TypeError\` exceptions during \`contract.imprint()\`.

\`\`\`python
field = EnumField(enum_class=UserStatus, store_name=False)
field.to_db(UserStatus.ACTIVE, dialect="postgresql")  # -> 'active'
\`\`\`

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| \`aquilia.models.registry\` | \`threading.RLock\` guarding all registry methods; reverse relation cache invalidation | Prevents race conditions during concurrent model registration & reload |
| \`aquilia.models.manager\` | \`BaseManager.__get__\` creates bound shallow copies for subclasses | Guarantees thread isolation when accessing managers on derived models |
| \`aquilia.models.fields\` | \`EnumField\` & \`CompositeField\` accept \`dialect\` in \`to_db()\` | Fixes contract \`imprint()\` crashes on models with Enum/Composite fields |
| \`aquilia.contracts\` | \`ContractMeta\` introspects type hints for \`NestedContractFacet\` | Allows clean Python type hint syntax for nested contract definitions |
| \`aquilia.contracts\` | 10-point standard docstrings across all facet & core contract modules | Full IDE intellisense, architectural clarity, and documentation integrity |

Check the [Migration Guide](migration.md) for full details on upgrading to v1.3.7.
`,
    "thread_safe_registry.md": `# Thread-Safe ModelRegistry & Cache Invalidation

Aquilia v1.3.7 refactors \`ModelRegistry\` (\`aquilia.models.registry.ModelRegistry\`) to introduce **full thread safety** via a re-entrant lock (\`threading.RLock\`) and automated **reverse-relation cache invalidation**.

---

## Why It Changed

In multi-threaded ASGI server configurations, worker threads or background tasks may dynamically import modules, execute testing fixtures, or register models concurrently. 

Previously, \`ModelRegistry\` maintained shared dictionaries (\`_models\` and \`_app_models\`) without thread synchronization:
- Concurrent calls to \`ModelRegistry.register()\` during app startup or dynamic module loading could cause dictionary mutation race conditions (\`RuntimeError: dictionary changed size during iteration\`).
- Foreign key resolution (\`_resolve_relations()\`) running in one thread while another registered a new model could lead to incomplete or corrupted foreign key mapping.
- Models lazily cached their reverse foreign key relationships (\`_reverse_fk_cache\` and \`_reverse_relation_cache\`). When test suites or dynamic reloads registered new models pointing back to existing models, the existing models held onto stale, un-updated reverse relationship caches.

---

## Architecture & Implementation

### 1. Re-Entrant Lock Guard (\`threading.RLock\`)

\`ModelRegistry\` now owns a class-level \`_lock = threading.RLock()\`. Re-entrant locking ensures that nested registry calls (e.g. \`register()\` calling \`_resolve_relations()\`, which queries registered models) can acquire the lock on the same thread without deadlocks.

Thread locks guard every public and internal operation:
- \`ModelRegistry.register(model_cls)\`
- \`ModelRegistry.reset()\`
- \`ModelRegistry.set_database(db)\`
- \`ModelRegistry.get_database()\`
- \`ModelRegistry.get_models(app_label)\`
- \`ModelRegistry.get_model(name, app_label)\`
- \`ModelRegistry._resolve_relations()\`
- \`ModelRegistry.create_tables(db, app_label)\`
- \`ModelRegistry.drop_tables(db, app_label)\`

\`\`\`python
class ModelRegistry:
    _models: dict[str, type[Model]] = {}
    _db: AquiliaDatabase | None = None
    _app_models: dict[str, dict[str, type[Model]]] = {}
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        with cls._lock:
            # 1. Update global lookups
            # 2. Invalidate reverse relation caches on existing models
            # 3. Resolve pending string foreign keys
            ...
\`\`\`

### 2. Reverse Relation Cache Invalidation

When a new model is registered or the registry is reset, \`ModelRegistry\` automatically calls \`_clear_reverse_relation_caches()\` on all registered \`Model\` subclasses.

\`\`\`python
# In aquilia.models.base.Model
@classmethod
def _clear_reverse_relation_caches(cls) -> None:
    """Clear cached reverse FK references and relation maps on this class."""
    cls._reverse_fk_cache = None
    cls._reverse_relation_cache = None
\`\`\`

---

## Code Examples

### Multi-Threaded Model Registration (Concurrent Safety)

\`\`\`python
import threading
from aquilia.models import Model, ModelRegistry, fields

def define_and_register(name: str):
    class DynamicUser(Model):
        table = f"users_{name}"
        username = fields.TextField()

    # Thread-safe registration under high concurrency
    ModelRegistry.register(DynamicUser)

threads = [
    threading.Thread(target=define_and_register, args=(f"worker_{i}",))
    for i in range(20)
]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert len(ModelRegistry.get_models()) >= 20
\`\`\`

---

## Performance Considerations

The performance impact of \`threading.RLock\` acquisition for model lookups is negligible (sub-microsecond), while completely eliminating data race crashes in multi-threaded application servers or test runners.
`,
    "manager_descriptor_thread_safety.md": `# Manager Descriptor Thread Safety & Subclass Binding

Aquilia v1.3.7 refactors \`BaseManager\` (\`aquilia.models.manager.BaseManager\`) descriptor access to guarantee **thread isolation** when accessing model managers across derived classes.

---

## Why It Changed

Model managers in Aquilia are attached as descriptors to model classes (e.g. \`objects = Manager()\`). In Python's descriptor protocol, accessing \`Model.objects\` calls \`BaseManager.__get__(self, instance, owner)\`.

Prior to v1.3.7:
- When a subclass inherited a manager from a base model (or when multiple worker threads accessed \`SubModel.objects\`), \`__get__\` re-assigned \`self._model_cls = owner\` directly on the shared \`BaseManager\` instance.
- In multi-threaded environments, if Thread A accessed \`ParentModel.objects\` while Thread B accessed \`ChildModel.objects\`, a race condition occurred where \`_model_cls\` on the shared manager instance could be mutated while Thread A was building a query. This caused queries in Thread A to target \`ChildModel\` instead of \`ParentModel\`.

---

## Architecture & Implementation

### 1. Bound Shallow Copy Protocol

In \`BaseManager.__get__()\`:
1. Instance access check: If \`instance is not None\`, raises \`ManagerInstanceAccessFault\` (blocking \`user.objects\` access).
2. Owner matching: If \`owner\` matches \`self._model_cls\` or \`self._model_cls\` is \`None\`, \`self._model_cls\` is set to \`owner\` and \`self\` is returned.
3. Subclass isolation: If accessed from a subclass (\`owner != self._model_cls\`), \`BaseManager.__get__()\` returns a **shallow copy** (\`copy.copy(self)\`) bound to \`owner\`.

\`\`\`python
def __get__(self: M, instance: Any, owner: type) -> M:
    if instance is not None:
        from aquilia.faults.domains import ManagerInstanceAccessFault
        raise ManagerInstanceAccessFault(
            f"Manager '{self.__class__.__name__}' is non-accessible from "
            f"'{instance.__class__.__name__}' instance. Access it from the class instead."
        )

    if self._model_cls is None or self._model_cls is owner:
        self._model_cls = cast("type[TModel]", owner)
        return self

    # Subclass or different owner access -- return a bound copy for thread safety
    bound = copy.copy(self)
    bound._model_cls = cast("type[TModel]", owner)
    return bound
\`\`\`

---

## Code Examples

### Subclass Manager Access in Multi-Threaded Environments

\`\`\`python
import asyncio
from aquilia.models import Model, Manager, fields

class BaseContent(Model):
    table = "base_contents"
    title = fields.TextField()
    objects = Manager()

class Article(BaseContent):
    table = "articles"
    body = fields.TextField()

class Video(BaseContent):
    table = "videos"
    duration = fields.IntField()

async def concurrent_queries():
    # Concurrently query derived models without cross-thread manager state corruption
    article_task = asyncio.create_task(Article.objects.all())
    video_task = asyncio.create_task(Video.objects.all())
    await asyncio.gather(article_task, video_task)
\`\`\`

---

## Behavioral Guarantees

- **Thread Safety**: Accessing managers across inheritance hierarchies produces distinct, thread-bound descriptors.
- **Instance Protection**: Accessing \`instance.objects\` continues to raise \`ManagerInstanceAccessFault\` deterministically.
`,
    "nested_contract_annotations.md": `# Type-Annotated Nested Contract Facets

Aquilia v1.3.7 updates \`ContractMeta\` (\`aquilia.contracts.annotations\`) and \`NestedContractFacet\` to support **standard Python type hint annotations** for nested contracts and nested contract lists.

---

## Why It Changed

Previously, defining nested contracts required explicit facet assignment syntax:

\`\`\`python
class NameContract(Contract):
    first_name: str
    last_name: str

class UserRegistrationContract(Contract):
    # Old explicit syntax:
    name = NestedContractFacet(NameContract)
\`\`\`

While functional, this syntax did not leverage standard Python type annotations (\`typing.Annotated\` or direct class annotations) and required developers to remember two distinct ways of declaring fields on Contracts.

---

## Supported Type Hint Syntaxes

In v1.3.7, \`ContractMeta\` introspects class type annotations and automatically converts nested contract annotations into \`NestedContractFacet\` instances.

### 1. Direct Contract Class Annotation

\`\`\`python
class AuditUserNameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class RegistrationContract(Contract):
    # Direct Contract class annotation
    name: AuditUserNameContract
\`\`\`

### 2. Explicit \`NestedContractFacet[SubContract]\` Annotation

\`\`\`python
from aquilia.contracts import Contract, NestedContractFacet

class RegistrationContract(Contract):
    # Parameterized NestedContractFacet type annotation
    name: NestedContractFacet[AuditUserNameContract]
\`\`\`

### 3. Nested Contract Lists

\`\`\`python
class OrganizationContract(Contract):
    # List of nested contracts
    members: list[AuditUserNameContract]
    # Or parameterized list:
    teams: list[NestedContractFacet[TeamContract]]
\`\`\`

---

## How It Works Internally

During \`ContractMeta.__new__()\` processing:
1. \`ContractMeta\` iterates over \`__annotations__\`.
2. If an annotation target is a subclass of \`Contract\` (or a \`typing.get_origin()\` matching \`list\` with a \`Contract\` argument), \`ContractMeta\` wraps the target into a \`NestedContractFacet(target_contract, many=is_list)\`.
3. The resulting facet is attached to \`_all_facets\` on the contract class, supporting full validation, sealing, and model imprinting (\`contract.imprint()\`).

---

## Full Code Example

\`\`\`python
import typing
import uuid
from aquilia.contracts import Contract, Facet, NestedContractFacet, ward
from aquilia.contracts.transforms import strip, lower
from aquilia.models import Model
from aquilia.models.fields import UUIDField, TextField

class AddressContract(Contract):
    street: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    city: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    zip_code: typing.Annotated[str, Facet.text(min_length=5, max_length=10) >> strip]

class UserProfileContract(Contract):
    address: AddressContract
    previous_addresses: list[AddressContract]
    email: typing.Annotated[str, Facet.email() >> strip >> lower]

# Sealing and validation work seamlessly:
contract = UserProfileContract(data={
    "address": {"street": "123 Main St", "city": "Metropolis", "zip_code": "10001"},
    "previous_addresses": [
        {"street": "456 Old Rd", "city": "Gotham", "zip_code": "10002"}
    ],
    "email": "USER@EXAMPLE.COM"
})

assert contract.is_sealed()
\`\`\`
`,
    "field_dialect_support.md": `# Multi-Dialect Field Conversion Support

Aquilia v1.3.7 updates \`EnumField.to_db()\` (\`aquilia.models.fields.enum_field\`) and \`CompositeField.to_db()\` (\`aquilia.models.fields.composite\`) to accept the \`dialect\` keyword parameter.

---

## Why It Changed

In the Aquilia ORM, all field classes derive from \`Field\` (\`aquilia.models.fields.base.Field\`), which defines the method signature:

\`\`\`python
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    ...
\`\`\`

When contract data is imprinted back onto model instances (\`contract.imprint()\`) or when query engines compile SQL statements across different database backends (SQLite, PostgreSQL, MySQL, Oracle), the database driver invokes \`field.to_db(value, dialect=dialect)\`.

Previously:
- \`EnumField.to_db(self, value)\` and \`CompositeField.to_db(self, value)\` lacked the \`dialect\` parameter in their function signatures.
- Calling \`contract.imprint()\` on a model containing an \`EnumField\` or \`CompositeField\` resulted in a fatal \`TypeError\`:

\`\`\`text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
\`\`\`

---

## What Changed

\`EnumField.to_db()\` and \`CompositeField.to_db()\` now explicitly include \`dialect: str = "sqlite"\` in their method signatures, matching \`Field.to_db()\`.

### Updated Signatures

\`\`\`python
# EnumField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if isinstance(value, self.enum_class):
        return value.name if self.store_name else value.value
    return value

# CompositeField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if self.strategy == "json":
        return json.dumps(value)
    return value
\`\`\`

---

## Code Examples

### Contract Imprinting with EnumField Models

\`\`\`python
import typing
from aquilia.contracts import Contract, Facet
from aquilia.models import Model
from aquilia.models.enums import TextChoices
from aquilia.models.fields import UUIDField, TextField, EnumField

class UserStatus(TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"

class UserModel(Model):
    table = "users"
    id = UUIDField(primary_key=True)
    name = TextField()
    status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)

class UserContract(Contract[UserModel]):
    name: typing.Annotated[str, Facet.text()]

    class Spec:
        model = UserModel

# Imprinting works seamlessly across all database dialects
contract = UserContract(data={"name": "Alice"})
assert contract.is_sealed()

user_model = contract.imprint()
assert user_model.status == UserStatus.ACTIVE
\`\`\`
`,
    "contract_docstrings.md": `# Standardized 10-Point Contract Docstrings

Aquilia v1.3.7 completes a major documentation standardization effort across the entire Contracts subsystem (\`aquilia.contracts\`).

Every Facet primitive in \`facets.py\` and core contract module (\`exceptions.py\`, \`integration.py\`, \`lenses.py\`, \`pipeline.py\`, \`projections.py\`, \`schema.py\`, \`ward.py\`) now carries a comprehensive 10-point industry-standard docstring.

---

## The 10-Point Standard Structure

Each public class and method in \`aquilia.contracts\` follows the exact 10-point documentation standard:

1. **Purpose**: High-level architectural role and intent.
2. **Lifecycle**: When and how the component is initialized, invoked, and destroyed.
3. **Execution Order**: Pre-conditions, pipeline step ordering, and post-conditions.
4. **Parameters**: Explicit type signatures, descriptions, and defaults for all arguments.
5. **Return Value**: Precise return types and behavior on success.
6. **Exceptions**: Exhaustive list of raised exceptions and failure conditions.
7. **Notes**: Design rationale, thread safety, and immutability notes.
8. **Edge Cases**: Empty inputs, \`None\` values, overflow handling, and boundary behavior.
9. **Internal Behaviour**: Key implementation details, private helpers, and cache interactions.
10. **Examples**: Executable doctests and real-world usage patterns.

---

## Affected Modules

Docstrings were added or expanded across the following files:

- \`aquilia/contracts/facets.py\` (all \`Facet\` subclasses including \`TextFacet\`, \`IntFacet\`, \`FloatFacet\`, \`DecimalFacet\`, \`BoolFacet\`, \`DateTimeField\`, \`DateField\`, \`TimeField\`, \`UUIDFacet\`, \`EmailFacet\`, \`URLFacet\`, \`EnumFacet\`, \`ListFacet\`, \`DictFacet\`, \`NestedContractFacet\`, \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\`).
- \`aquilia/contracts/exceptions.py\` (\`ContractFault\`, \`ContractValidationFault\`, \`ContractSealedFault\`, \`LensUnresolvedFault\`, \`NestingDepthFault\`, etc.).
- \`aquilia/contracts/integration.py\` (\`ContractIntegration\`, \`configure_contracts\`).
- \`aquilia/contracts/lenses.py\` (\`Lens\`, \`LensRegistry\`, \`mold_async\`).
- \`aquilia/contracts/pipeline.py\` (\`ContractPipeline\`, \`Sigil\`).
- \`aquilia/contracts/projections.py\` (\`Projection\`, \`ProjectionRegistry\`).
- \`aquilia/contracts/schema.py\` (\`ContractSchema\`, \`OpenAPIGenerator\`).
- \`aquilia/contracts/ward.py\` (\`ward\`, \`WardDescriptor\`).

---

## Benefits for Developers

- **Rich IDE Intellisense**: Hover documentation in VSCode, PyCharm, and language servers displays complete usage examples, parameter descriptions, and edge-case warnings.
- **Zero Ambiguity**: Clear distinction between sync validation (\`is_sealed()\`) and async validation (\`is_sealed_async()\`).
- **Architectural Traceability**: Deep insight into pipeline execution order and ward priority levels.
`,
    "bugfixes.md": `# Bug Fixes in Aquilia v1.3.7

Aquilia v1.3.7 resolves key issues identified in model field handling, multi-threaded model registry operations, manager descriptor subclass access, and test assertions.

---

## 1. Missing Dialect Parameter in EnumField & CompositeField

**The Bug:**
When calling \`contract.imprint()\` on a \`Contract\` bound to a \`Model\` containing an \`EnumField\` or \`CompositeField\`, the framework passed \`dialect="sqlite"\` to \`field.to_db()\`. Because \`EnumField.to_db()\` and \`CompositeField.to_db()\` did not accept \`dialect\`, Python raised a \`TypeError\`:

\`\`\`text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
\`\`\`

**The Fix:**
Added \`dialect: str = "sqlite"\` to \`EnumField.to_db()\` and \`CompositeField.to_db()\`, aligning their method signatures with \`Field.to_db()\`.

---

## 2. Race Conditions in ModelRegistry Under Concurrency

**The Bug:**
In multi-threaded ASGI environments or test runners with parallel test execution, concurrent model registration or calls to \`ModelRegistry.reset()\` could cause data race mutations on \`_models\` and \`_app_models\`, occasionally causing \`RuntimeError: dictionary changed size during iteration\`.

**The Fix:**
Guarded all \`ModelRegistry\` operations with a re-entrant lock (\`threading.RLock\`). Added \`_clear_reverse_relation_caches()\` on \`Model\` to clear stale \`_reverse_fk_cache\` and \`_reverse_relation_cache\` entries when models are registered or reset.

---

## 3. Subclass Manager Descriptor Mutation Race Condition

**The Bug:**
Accessing \`SubModel.objects\` when \`objects = Manager()\` was inherited from \`ParentModel\` mutated \`self._model_cls\` directly on the shared \`BaseManager\` instance, causing cross-thread manager state pollution.

**The Fix:**
Refactored \`BaseManager.__get__()\` to return a bound shallow copy (\`copy.copy(self)\`) when accessed on a subclass or different owner.

---

## 4. Test Suite HMAC Secret Warning & Envelope Format Assertions

**The Bug:**
Bytecode cache and snapshot tests emitted HMAC secret warning messages during testing and failed envelope dictionary format assertions under strict test runs.

**The Fix:**
Updated test fixtures and envelope dict format assertions in \`tests/test_phase15_faults_security.py\` and \`tests/test_admin_v3.py\` to ensure clean test suite execution.
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.7

Aquilia v1.3.7 is a **100% backward-compatible release**. All existing v1.3.6 applications will run without any code modifications or database migration requirements.

---

## Upgrading

Upgrade Aquilia using \`pip\`:

\`\`\`bash
pip install aquilia==1.3.7
\`\`\`

Or using Poetry / uv / pipenv:

\`\`\`bash
uv pip install aquilia==1.3.7
\`\`\`

---

## Upgrade Checklist

1. **Update Dependency**: Upgrade \`aquilia\` to \`1.3.7\`.
2. **Run Test Suite**: Run \`pytest\` across your application codebase to verify all existing contracts, models, and manager queries pass.
3. **Optional Code Cleanup**: Simplify nested contract declarations by replacing \`NestedContractFacet(SubContract)\` with clean Python type annotations \`name: SubContract\`.

---

## New Capabilities You Can Adopt

### 1. Python Type Annotations for Nested Contracts

\`\`\`python
# Before (v1.3.6 and earlier):
class UserContract(Contract):
    profile = NestedContractFacet(ProfileContract)

# New in v1.3.7:
class UserContract(Contract):
    profile: ProfileContract
\`\`\`

### 2. Multi-Threaded Model Operations

You can safely perform model registration, reset, and dynamic schema inspection across multiple threads without manual locking mechanisms.

---

## Verification

After upgrading, run your test suite:

\`\`\`bash
pytest
\`\`\`

All 7,410+ framework tests continue to pass seamlessly.
`
  },
  "1.3.6": {
    "README.md": `# Aquilia v1.3.6 Release Notes — "Artifact Forge"

Aquilia v1.3.6 introduces the **Artifact Subsystem** — a unified, production-grade infrastructure for all framework-generated metadata, build outputs, indexes, compiled representations, and caches.

Before this release, framework artifacts like template bytecode, discovery caches, and MCP indexes were scattered across different files, sometimes in an \`artifacts/\` directory at the project root, and sometimes wherever the subsystem decided. They used varying file formats and I/O strategies, which occasionally led to inconsistent atomic writes.

This release unifies all of this under a single \`.aquilia/artifacts/\` directory and a standardized \`ArtifactEnvelope\` JSON format. It guarantees atomic writes across all producers, introduces HMAC-SHA256 signatures for integrity (like the bytecode cache), and provides a new \`aq artifacts\` CLI to manage them.

The new artifact infrastructure is entirely transparent to most applications, but if you have tooling that expects artifacts in specific paths or legacy formats, you may need to update them.

---

## Table of Contents

1. [Artifact Store Deep Dive](artifact_store.md)
   - \`aquilia.artifacts\` architecture
   - \`ArtifactStore\` and \`ArtifactEnvelope\` APIs
   - \`JSONFileBackend\` atomic writes and HMAC-SHA256 signing
   - The \`aq artifacts\` CLI commands
2. [Unified Artifact Directory](unified_artifact_directory.md)
   - Consolidation from \`artifacts/\` to \`.aquilia/artifacts/\`
   - Complete directory layout
   - Configuration via \`[aquilia.artifacts]\` and \`AQUILIA_ARTIFACT_ROOT\`
3. [Producer Migrations](producer_migrations.md)
   - How \`DiscoveryCache\`, \`JSONBytecodeCache\`, etc. were migrated
   - Backward compatibility for legacy formats
4. [Bug Fixes](bugfixes.md)
   - Centralized atomic write guarantees
   - HMAC verification fixes
5. [Migration Guide](migration.md)
   - Upgrade checklist and breaking changes
   - Handling the path and format changes

---

## Highlights

### Unified Artifact Directory

All framework artifacts now live under \`.aquilia/artifacts/\` instead of scattering across the project root.

\`\`\`bash
# Before:
# artifacts/templates.bytecode.json
# artifacts/ws.json
# ...

# After:
# .aquilia/artifacts/templates.bytecode.json
# .aquilia/artifacts/ws.json
# .aquilia/artifacts/discovery_cache.json
# ...
\`\`\`

### The \`aq artifacts\` CLI

Manage all your framework artifacts with the new command group:

\`\`\`bash
aq artifacts status           # See what's on disk, sizes, schemas
aq artifacts verify           # Verify HMAC signatures and integrity
aq artifacts clean            # Remove stale/orphaned artifacts
\`\`\`

### Standardized Wire Format

Every artifact now uses the \`ArtifactEnvelope\` canonical format, providing clear schema versioning and traceability.

\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:...",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { ... }
}
\`\`\`

### Breaking Changes

1. **Artifact file format changed** — All artifact files now use the \`ArtifactEnvelope\` JSON format. Backward compatibility is provided for some legacy formats on load (\`DiscoveryCache\`, schema snapshots, MCP index), but bytecode cache and frozen registry will be regenerated.
2. **\`JSONBytecodeCache(cache_dir=...)\` parameter now defaults to \`None\`** — Previously defaulted to \`"artifacts"\`. The cache now lives in \`.aquilia/artifacts/\`.
3. **Template manifest default location changed** — Moved from \`artifacts/templates.json\` to \`.aquilia/artifacts/templates.json\`.
4. **WebSocket artifact default location changed** — Moved from \`artifacts/ws.json\` to \`.aquilia/artifacts/ws.json\`.

Check the [Migration Guide](migration.md) for full details on upgrading.
`,
    "artifact_store.md": `# Artifact Store Deep Dive

The **Artifact Subsystem** (\`aquilia.artifacts\`) is a new foundational layer in Aquilia v1.3.6 designed to manage all generated data — from discovery caches to compiled bytecode. 

## Why it was built

Historically, each Aquilia subsystem managed its own caching and file I/O. The discovery engine wrote a JSON file, the template engine wrote a different JSON file and a custom HMAC format for bytecode, and the WebSocket compiler wrote another file. 
This led to:
- Inconsistent file locations (some in \`artifacts/\`, some in project root).
- Varying levels of atomic write guarantees (some used \`mkstemp\` + \`replace\`, some just \`write_text\`).
- No unified way to inspect, verify, or clean up generated data.

The Artifact Store centralizes this, providing a unified API with robust integrity and concurrency guarantees.

## Architecture Overview

The subsystem is composed of several key components:

1. **\`ArtifactStore\`**: The primary async facade for reading, writing, and managing artifacts.
2. **\`ArtifactEnvelope\`**: The canonical JSON wire format that wraps every payload.
3. **\`JSONFileBackend\` & \`MemoryBackend\`**: The physical storage layer.
4. **\`ArtifactRegistry\`**: The central registry of known artifact types.
5. **Canonicalization & Integrity**: Core logic for fingerprinting and HMAC signing.

### ArtifactStore

The \`ArtifactStore\` provides an async interface for all artifact operations.

\`\`\`python
from aquilia.artifacts import provide_artifact_store

store = provide_artifact_store()

# Async API
await store.put("discovery_cache", "main", payload_dict)
envelope = await store.get("discovery_cache", "main")
await store.verify("templates.bytecode")
await store.prune()
\`\`\`

It also supports an **\`ArtifactTransaction\`** for all-or-nothing multi-artifact commits:

\`\`\`python
async with store.transaction() as tx:
    await tx.put("discovery_cache", "main", discovery_data)
    await tx.put("route_index", "main", route_data)
# Both are committed atomically at the end of the block.
\`\`\`

### JSONFileBackend

\`JSONFileBackend\` handles the actual disk I/O, ensuring absolute safety against partial writes and concurrent access.

- **Atomic Writes**: Uses \`tempfile.mkstemp\` to write a temporary file, \`os.fsync\` to flush it to disk, and \`os.replace\` to atomically move it into place.
- **Signed Mode**: If \`signed=True\`, the backend computes an HMAC-SHA256 signature using the active secret key, appending it to the top of the file: \`<64-char-hex-HMAC>\\n<JSON>\`.

### ArtifactEnvelope Wire Format

Every artifact written to disk (except signed files, which prepend the HMAC) is a strict JSON document matching the \`ArtifactEnvelope\` format:

\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { 
      "modules": [...],
      "routes": [...]
  }
}
\`\`\`

This ensures that any tool, inside or outside of Aquilia, can safely parse, identify, and verify the age/schema of any artifact.

### ArtifactRegistry

The \`ArtifactRegistry\` keeps track of what artifacts exist and how to handle them.

\`\`\`python
from aquilia.artifacts import register_artifact_type, ArtifactTypeDescriptor

register_artifact_type(ArtifactTypeDescriptor(
    name="my_custom_cache",
    schema_version="1.0",
    signed=False
))
\`\`\`

There are currently 10 registered types in Aquilia: \`discovery_cache\`, \`frozen_registry\`, \`schema_snapshot\`, \`ws_metadata\`, \`template_manifest\`, \`mcp_knowledge_index\`, \`template_bytecode\`, \`di_manifest\`, \`route_index\`, \`migration_file\`.

## Dependency Injection

The store is available via the DI container with an app-scoped provider:

\`\`\`python
from aquilia.artifacts import ArtifactStoreProvider

# Available automatically in controllers/services:
class MyService:
    store: ArtifactStore = Inject(ArtifactStore)
\`\`\`

## CLI: \`aq artifacts\`

A new command group allows you to manage the store from the terminal:

- \`aq artifacts status [--root PATH]\`: Lists all registered artifact types, showing which are present on disk, file size, last modified time, and schema version.
- \`aq artifacts verify [PATH] [--root PATH]\`: Verifies the integrity of one or all artifacts, strictly checking the HMAC for signed types.
- \`aq artifacts clean [--root PATH] [--orphaned-only]\`: Removes stale, corrupted, or orphaned artifacts.

## Configuration

The root directory defaults to \`.aquilia/artifacts\` in your project root. You can override this globally:

\`\`\`toml
# pyproject.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
\`\`\`

Or via environment variable:
\`\`\`bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
\`\`\`
`,
    "unified_artifact_directory.md": `# Unified Artifact Directory

A critical path fix in Aquilia v1.3.6 is the consolidation of all framework-generated files into a single, predictable location.

## Before

In previous versions, artifacts were scattered, usually landing in an \`artifacts/\` folder created at the current working directory, or sometimes in the project root directly:

- \`artifacts/templates.bytecode.json\`
- \`artifacts/ws.json\`
- \`artifacts/templates.json\`

This polluted the project root, often conflicted with user folders named "artifacts", and lacked a standardized structure.

## After

**ALL** framework artifacts now live under a unified hidden directory: \`.aquilia/artifacts/\`.

This change is driven by \`resolve_artifact_root()\`, which locates the project root and appends \`.aquilia/artifacts\`.

### Directory Layout

\`\`\`text
<project_root>/
└── .aquilia/
    └── artifacts/
        ├── discovery_cache.json          # auto-discovery engine cache
        ├── schema_snapshot.json          # ORM schema snapshot for migrations
        ├── templates.bytecode.json       # compiled Jinja2 bytecode (HMAC-signed)
        ├── templates.json                # template manifest / inventory
        ├── ws.json                       # WebSocket controller metadata
        ├── mcp_knowledge_index.json      # MCP context knowledge index
        ├── di_manifest.json              # DI provider graph
        └── route_index.json              # compiled route index
\`\`\`

## Breaking Changes & Path Adjustments

Because the default path changed, any tooling or manual scripts that expected files in \`artifacts/\` will need to be updated.

- \`JSONBytecodeCache.__init__(cache_dir: str | None = None)\`: Default changed from \`"artifacts"\` to \`None\` (which dynamically resolves to \`.aquilia/artifacts\`).
- \`create_template_engine_from_config(cache_dir: str | None = None)\`: Default changed to \`None\`.
- \`TemplateManager.compile_all(output_path=None)\`: Default changed from \`"artifacts/templates.json"\` to \`.aquilia/artifacts/templates.json\`.
- \`cmd_compile(output=None)\`: Resolves via \`resolve_artifact_root() / "templates.json"\`.
- \`cmd_clear_cache(cache_dir=None)\`: Resolves via \`resolve_artifact_root()\`.
- \`aq ws inspect --artifacts-dir\`: Default changed from \`"artifacts"\` to \`None\`.
- \`aq ws gen-client --artifacts-dir\`: Default changed from \`"artifacts"\` to \`None\`.

**Backward Compatibility:** If your code explicitly passes \`cache_dir="artifacts"\`, the framework will respect it and continue to use the old directory. 

## Migration Steps

1. **Update \`.gitignore\`**: You should ignore the new directory.
   \`\`\`bash
   echo '.aquilia/artifacts/' >> .gitignore
   \`\`\`

2. **Clean up old artifacts**: You can safely delete the old scattered files.
   \`\`\`bash
   rm -rf artifacts/
   \`\`\`
   The framework will automatically regenerate everything inside \`.aquilia/artifacts/\` on the next run.

3. **Verify**: Run the new CLI command to ensure things are working:
   \`\`\`bash
   aq artifacts status
   \`\`\`

## Custom Configuration

If you deploy to a read-only filesystem and need to direct artifacts to a writable volume (like \`/tmp\` or \`/var/lib/\`), you can override the root path globally:

\`\`\`toml
# pyproject.toml or aquilia.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
\`\`\`

Or via environment variable (useful for Docker containers):
\`\`\`bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
\`\`\`
`,
    "producer_migrations.md": `# Producer Migrations

In v1.3.6, all 9 primary artifact producers were migrated from ad-hoc file I/O to the new \`ArtifactStore\` backend. This ensures uniform atomic writes, consistent formatting, and centralized integrity checking.

Below are the details on how each producer was migrated and backward compatibility notes.

## 1. Discovery Cache (\`aquilia/discovery/engine.py\`)

**Before:**
\`DiscoveryCache.save()\` and \`load()\` used raw \`Path.write_text()\` with a plain dictionary format. It did not verify integrity on load.

**After:**
Uses \`JSONFileBackend.write_sync\`/\`read_sync\` + \`ArtifactEnvelope\`. Integrity is implicitly checked by the backend when resolving the envelope.

**Backward Compatibility:**
The loader detects the legacy plain dict format and gracefully loads it. It will be seamlessly upgraded to the envelope format on the next save.

## 2. Aquilary Registry (\`aquilia/aquilary/core.py\`)

**Before:**
\`AquilaryRegistry.export_manifest()\` used standard file writing to dump the frozen registry.

**After:**
\`export_manifest()\` and \`_from_frozen_manifest()\` use \`JSONFileBackend(signed=True)\` + \`ArtifactEnvelope\`.

**Backward Compatibility:**
No backward compatibility provided. The frozen registry is ephemeral to the deployment and will be cleanly regenerated on the first boot of a v1.3.6 application.

## 3. Schema Snapshots (\`aquilia/models/schema_snapshot.py\`)

**Before:**
\`save_snapshot()\` and \`load_snapshot()\` wrote a raw JSON dict to disk.

**After:**
Uses \`JSONFileBackend\` + \`ArtifactEnvelope\`. 

**Backward Compatibility:**
Like the discovery cache, legacy plain dict files are detected and read seamlessly.

## 4. Template Manifest (\`aquilia/templates/manifest_integration.py\`)

**Before:**
\`generate_template_manifest()\` wrote directly to \`artifacts/templates.json\`.

**After:**
Uses \`bare_fingerprint\` + \`ArtifactEnvelope\` + \`JSONFileBackend\`, writing to \`.aquilia/artifacts/templates.json\`.

**Backward Compatibility:**
Safe to regenerate. If you rely on the manifest file for external tooling, update the tool to parse the new \`payload\` key inside the envelope.

## 5. Bytecode Cache (\`aquilia/templates/bytecode_cache.py\`)

**Before:**
\`JSONBytecodeCache._save()\`/\`_load()\` used manual HMAC signing logic with \`Path.replace()\` (not \`os.replace()\`), writing to \`artifacts/templates.bytecode.json\`.

**After:**
Delegates to \`self._backend\` (\`JSONFileBackend\` with \`signed=True\`). \`__init__\` now accepts \`cache_dir: str | None = None\`, dynamically resolving the directory.

**Backward Compatibility:**
No backward compatibility for the file format. The cache will be invalidated and regenerated correctly under the new system. Existing code passing \`cache_dir="artifacts"\` continues to work but gets the new envelope format.

## 6. Socket Compiler (\`aquilia/sockets/compile.py\`)

**Before:**
\`SocketCompiler.generate_artifacts()\` wrote directly to \`artifacts/ws.json\`.

**After:**
Uses \`ArtifactEnvelope\` + \`JSONFileBackend\`, writing to \`.aquilia/artifacts/ws.json\`.

**Backward Compatibility:**
Regenerated on demand.

## 7. MCP Knowledge Index (\`aquilia/mcp/context/indexer.py\`)

**Before:**
\`save_index()\` and \`load_index()\` read/wrote a plain dictionary.

**After:**
Uses \`ArtifactEnvelope\` + \`JSONFileBackend\`.

**Backward Compatibility:**
Legacy plain dict formats are still loadable.

## Performance Impact

Despite the additional metadata overhead, there is **no measurable performance degradation**. The previous systems that used atomic writes were already paying the cost of \`mkstemp\` + \`os.replace\`. The abstraction simply centralizes this logic. Systems that previously used \`write_text\` are now slightly slower (on the order of single-digit milliseconds) but gain absolute resilience against partial writes and process crashes.
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.6

Aquilia v1.3.6 brings the new **Artifact Subsystem**. For most standard web applications, this upgrade is entirely transparent. The framework handles the migration, recreation, and cleanup of generated artifacts automatically.

However, if you maintain CI/CD pipelines, Dockerfiles, or external tooling that interacts with Aquilia's artifact files, you will need to apply a few small changes.

---

## Upgrading

\`\`\`bash
pip install aquilia==1.3.6
\`\`\`

---

## Upgrade Checklist

1. \`pip install aquilia==1.3.6\`
2. **Update \`.gitignore\`**: Add \`.aquilia/artifacts/\` to your \`.gitignore\`.
3. **Delete old artifacts**: Run \`rm -rf artifacts/\` from your project root.
4. **Update CI/CD caches**: If your CI caches the \`artifacts/\` folder, update the path to \`.aquilia/artifacts/\`.
5. **Update Dockerfiles**: If you \`COPY artifacts/ /app/artifacts/\`, update it to \`COPY .aquilia/artifacts/ /app/.aquilia/artifacts/\`.
6. **Update external scripts**: If you have tools parsing \`templates.json\` or \`ws.json\`, update them to read from the new path and parse the \`.payload\` property of the new JSON envelope.

---

## Breaking Changes Summary

### 1. Default Artifact Path Changed
The default path for all artifacts is now \`.aquilia/artifacts/\`.
* \`JSONBytecodeCache(cache_dir=None)\` previously defaulted to \`"artifacts"\`.
* Template compilation commands output to \`.aquilia/artifacts/templates.json\`.
* WebSocket inspect commands read from \`.aquilia/artifacts/ws.json\`.

If your code explicitly provided \`cache_dir="artifacts"\`, that code will continue to work, but the files written inside it will use the new JSON format.

### 2. Artifact File Format Changed
All framework JSON artifacts are now wrapped in an \`ArtifactEnvelope\`.

**Old Format (e.g. \`discovery_cache.json\`):**
\`\`\`json
{
  "modules": ["app.users", "app.billing"],
  "timestamp": 123456789
}
\`\`\`

**New Format:**
\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "...",
  "created_at": "...",
  "payload": {
    "modules": ["app.users", "app.billing"]
  }
}
\`\`\`

The framework automatically handles backward compatibility for reading legacy \`discovery_cache.json\`, \`schema_snapshot.json\`, and \`mcp_knowledge_index.json\`. Other caches (like bytecode) will be regenerated.

---

## Verification

After upgrading, boot your application or run your tests, then use the new CLI tool to verify the store:

\`\`\`bash
aq artifacts status
\`\`\`

You should see a table showing the newly generated artifacts in the \`.aquilia/artifacts/\` directory.

---

## Rollback Procedure

If you need to roll back to v1.3.5:
1. \`pip install aquilia==1.3.5\`
2. Delete the new directory: \`rm -rf .aquilia/artifacts/\`
3. Delete any legacy \`artifacts/\` directory just to be safe.
4. Reboot the application; v1.3.5 will regenerate the artifacts in the old format and old locations.
`,
    "bugfixes.md": `# Bug Fixes

The introduction of the unified \`ArtifactStore\` in v1.3.6 inherently resolves several long-standing, subtle bugs related to file I/O and caching across the framework.

## 1. Centralized Atomic Write Guarantees

**The Bug:**
Different subsystems implemented file writing differently. Some, like the bytecode cache, attempted atomic writes but used \`Path.replace()\` (which is not guaranteed to be atomic across all filesystems/platforms) instead of \`os.replace()\`. Others, like the discovery engine, used a raw \`Path.write_text()\`, meaning a crash during the write could leave a corrupted, partially written JSON file on disk, breaking the app on the next boot.

**The Fix:**
All artifact writing now routes through \`JSONFileBackend.write_sync()\`. This function rigorously employs \`tempfile.mkstemp\` (ensuring the temporary file is on the same filesystem), writes the data, calls \`os.fsync\` to guarantee durability, and then uses \`os.replace\` for a true atomic swap. No partial writes are possible.

## 2. Inconsistent HMAC Verification

**The Bug:**
While the bytecode cache properly verified its HMAC signature on load, other caches (like the discovery cache) did not verify integrity at all. If the \`discovery_cache.json\` file was manually tampered with or corrupted without breaking JSON syntax, the framework would load it blindly.

**The Fix:**
The \`JSONFileBackend\` natively supports a \`signed=True\` mode, and the \`ArtifactEnvelope\` includes a \`fingerprint\` property. The \`ArtifactStore\` verifies signatures on load for all configured artifact types, throwing an \`ArtifactCorruptFault\` if tampering or corruption is detected.

## 3. Directory Clutter & Collisions

**The Bug:**
The framework created an \`artifacts/\` directory in the current working directory of the process. If a developer ran a command from a subdirectory, a second \`artifacts/\` directory would be created there. Furthermore, the generic name \`artifacts/\` often collided with user-created folders or CI output directories.

**The Fix:**
All generated artifacts are now strictly confined to \`.aquilia/artifacts/\` relative to the project root, resolved predictably via \`resolve_artifact_root()\`.
`,
  },
  "1.3.5": {
    "README.md": `# Aquilia v1.3.5 Release Notes — "Distributed Tide"

Aquilia v1.3.5 makes the background task system genuinely distributed and durable, turns the mail subsystem into a production-grade delivery pipeline, and closes a silent validation bypass in Contracts.

Before this release, background tasks ran in a single process on an in-memory queue — jobs were lost on restart, a second web worker meant a second independent queue, and \`backend="redis"\` was accepted by configuration and then silently ignored. Mail was sent inline inside the request handler, with no bounce handling and no suppression list. And a nested Contract's \`@ward\` methods never ran at all: a validation rule declared on a nested Contract enforced nothing.

This release closes all three gaps: jobs now execute across multiple worker processes and multiple machines with lease-based coordination and crash recovery; job state survives restarts on Redis or SQL; jobs compose into chains, groups, chords, and arbitrary DAGs; duplicate enqueues are collapsed by an enforced fingerprint; mail is delivered by background workers with provider webhook processing and automatic suppression of bounced and complaining recipients; and nested Contract validation runs the child's full pipeline.

The tasks and mail work is entirely backward compatible. The Contracts audit ships four deliberate behavioral corrections — each one replacing incorrect behavior — listed under [Breaking Changes](#breaking-changes).

---

## Table of Contents

1. [Distributed & Persistent Task Backends](distributed_tasks.md)
   - \`RedisBackend\` — atomic Lua claim, \`SET NX\` fingerprint reservation
   - \`SQLBackend\` — durable queue on the application's own database
   - Lease-based claiming, heartbeat renewal, and crash recovery
   - \`Job.to_payload()\` / \`Job.from_payload()\` transport serialization
   - Registry-based callable resolution across process boundaries
2. [Workflows & DAGs](workflows.md)
   - \`Signature\`, \`Workflow\`, \`WorkflowResult\`
   - \`chain\` (sequential), \`group\` (parallel), \`chord\` (fan-in)
   - Arbitrary DAGs via \`depends_on\`
   - \`with_parent_results()\` continuation passing
   - Cycle and unknown-dependency validation
3. [Idempotency & Distributed Deduplication](idempotency.md)
   - \`Job.fingerprint\` finally enforced
   - \`dedup="allow" | "skip" | "raise"\`
   - Cross-process locking via Redis \`SET NX\` and a SQL unique constraint
4. [Mail Delivery Queue](mail_queue.md)
   - \`EnvelopeStore\` — \`MemoryEnvelopeStore\` and \`SQLEnvelopeStore\`
   - Background delivery through the existing task scheduler
   - Envelope-ID-only jobs, designed for distributed workers
   - Send-time deduplication by idempotency key and content digest
5. [Bounce Handling, Webhooks & Suppression](bounces_suppression.md)
   - \`parse_ses\`, \`parse_sendgrid\`, \`parse_mailgun\` with signature verification
   - \`process_webhook\` applying bounces and complaints
   - \`SuppressionList\` — permanent and TTL suppression, enforced on send
6. [Mail Security, MIME & Templates](mail_security.md)
   - Shared MIME assembly across every provider
   - Real DKIM signing at the byte level
   - XOAUTH2 authentication, TLS enforcement, PII redaction
   - ATS template filters and autoescaping
7. [Native HTTP Client & Dependency Cleanup](http_native.md)
   - Zero third-party HTTP client dependencies (\`httpx\` removed)
   - \`SendGridProvider\` and \`LiveServerTestCase\` updated to \`aquilia.http\`
8. [Contracts — Nested Validation Pipeline](contracts_pipeline.md)
   - Nested Contracts never ran their wards or \`validate()\` hook (CRITICAL)
   - \`list[Contract]\` annotations bypassed the nested pipeline (CRITICAL)
   - \`has_async_wards\` consulted only the top-level class
   - \`to_dict_async()\` / \`to_dict_many_async()\` / \`Lens.mold_async()\`
   - \`LensUnresolvedFault\` replaces a silent empty list
   - Input adapters for dataclasses, attrs, and \`TypedDict\`
9. [Contracts — Validation Control & Typing](contracts_validation.md)
   - \`@ward(order=..., when=..., groups=...)\`, \`Spec.fail_fast\`
   - \`Spec.frozen\`, \`Contract.__eq__\`, \`copy()\` / \`copy_async()\`
   - \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\`
   - \`Contract.from_env()\` and \`Contract.from_cli()\`
   - Localized validation messages via \`contract_message()\`
10. [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
    - \`aq contracts stubs\` — \`.pyi\` emission for \`mypy\` and \`pyright\`
    - \`seal_*\` / \`async_seal_*\` prefix convention deprecated
11. [CLI Changes](cli.md)
    - \`aq mail check\` validates DKIM configuration
    - \`aq contracts stubs\` generates Contract type stubs
12. [Bug Fixes](bugfixes.md)
    - Mail delivery task unresolvable across processes (CRITICAL)
    - Consumer-only workers polled nothing (CRITICAL)
    - Job results degraded to \`repr\` strings on persistent backends
    - \`queue.persistent\` had no configuration surface
13. [Migration Guide](migration.md)
    - Upgrade checklist, per-feature migrations, compatibility notes, known issues

---

## Highlights

### Distributed execution with crash recovery

A worker claims a job under a time-bounded lease and renews it by heartbeat. If the worker dies, the lease lapses and a peer reclaims the job instead of the job being lost.

\`\`\`python
# workspace.py — production
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=16,
    lease_seconds=120,
)
\`\`\`

Task code is unchanged between backends. Switching is configuration, not a rewrite.

### Workflows

\`\`\`python
from aquilia.tasks.workflow import chain, chord

# Sequential, each step fed by the previous
await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)

# Parallel shards, then a fan-in callback
await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(tasks)
\`\`\`

The graph is durable the moment it is submitted. No orchestrator process, and a \`WAITING\` step holds no worker slot.

### Enforced idempotency

\`\`\`python
# Ten identical requests; one job.
await tasks.enqueue(rebuild_index, dedup="skip")
\`\`\`

Correctness comes from the storage layer — Redis \`SET NX\`, or a SQL primary-key constraint — so two racing processes produce one job.

### Background mail delivery

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

\`asend()\` returns as soon as the envelope is stored. Delivery, retries, and backoff run on a worker — reusing the task scheduler rather than introducing a second queue.

### Automatic bounce suppression

\`\`\`python
events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
await process_webhook(events, suppression=mail.suppression, store=mail.store)
\`\`\`

A hard bounce or spam complaint removes the address from every future send, protecting sender reputation without application code.

### Nested Contract rules are enforced

\`\`\`python
class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

Order(data={"items": [{"qty": 0}]}).is_sealed()
# v1.3.4: True — the ward never ran
# v1.3.5: False, errors = {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

A nested Contract was validated *structurally only*, so every \`@ward\` and every \`validate()\` override on it was silently skipped. See [Nested Validation Pipeline](contracts_pipeline.md).

### Contract fields visible to type checkers

\`\`\`bash
aq contracts stubs myapp.contracts        # writes myapp/contracts.pyi
aq contracts stubs myapp.contracts --check  # CI freshness gate
\`\`\`

\`\`\`python
reveal_type(contract.total)    # decimal.Decimal — was Any
\`\`\`

A portable \`.pyi\` every type checker consumes with no plugin. See [Stub Generation](contracts_tooling.md).

---

## What's New

| Capability | Summary |
|---|---|
| \`RedisBackend\` | Distributed, durable task queue with atomic Lua claim |
| \`SQLBackend\` | Durable task queue on the existing application database |
| \`Job.to_payload()\` / \`from_payload()\` | JSON transport form with fail-at-enqueue validation |
| \`Workflow\`, \`Signature\`, \`WorkflowResult\` | Job graphs with dependencies |
| \`chain\`, \`group\`, \`chord\` | Sequential, parallel, and fan-in composition |
| \`dedup="skip" \\| "raise"\` | Enforced fingerprint deduplication |
| \`TaskDuplicateFault\`, \`TaskSerializationFault\`, \`TaskBackendFault\`, \`TaskWorkflowFault\` | New structured faults |
| \`EnvelopeStore\` | Durable record of accepted mail |
| \`SuppressionList\` | Bounce and complaint suppression, enforced on send |
| \`parse_ses\` / \`parse_sendgrid\` / \`parse_mailgun\` | Provider webhook parsing with signature verification |
| \`process_webhook\` | Applies delivery events to suppression and envelope status |
| \`build_mime_message\` / \`message_to_bytes\` / \`sign_dkim\` | Shared MIME assembly and DKIM signing |
| \`redact_email\` / \`redact_pii\` | PII redaction for mail logs |
| \`MailAuth.oauth2(...)\` | XOAUTH2 bearer-token SMTP authentication |
| \`aquilia[mail-dkim]\` | New optional extra for DKIM signing |
| \`aq contracts stubs\` | \`.pyi\` stub emission so \`mypy\`/\`pyright\` see Contract fields |
| \`Contract.to_dict_async()\` / \`to_dict_many_async()\` | Async serialization that awaits ORM relations |
| \`@ward(order=..., when=..., groups=...)\` | Validator ordering, conditional rules, and validation groups |
| \`Spec.frozen\` / \`Spec.fail_fast\` | Immutable validated data; stop at the first ward error |
| \`Contract.copy()\` / \`copy_async()\` | Derive an updated Contract, re-validating by default |
| \`Contract.from_env()\` / \`from_cli()\` | Build a Contract from environment variables or CLI arguments |
| \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\` | Strongly-typed primitives that previously fell through to \`TextFacet\` |
| \`aquilia.contracts.messages\` | Localized validation messages via the i18n catalog |
| \`NestingDepthFault\`, \`LensUnresolvedFault\`, \`StubGenerationFault\` | New structured Contract faults |

---

## Major Improvements

- **Backend selection is honest.** \`backend="redis"\` used to log a warning and fall back to in-memory. It now builds a real Redis backend; only an unknown backend name or an unreachable service falls back, and both say so loudly.
- **Serialization fails at the call site.** A non-JSON argument raises \`TaskSerializationFault\` at \`enqueue()\`, not on a remote worker hours later.
- **Queue discovery.** A consumer-only worker polls the queues declared by its \`@task\` descriptors, plus any queue it discovers on the shared backend.
- **Mail providers share one MIME implementation.** Header handling, attachments, and tracking headers no longer drift between SMTP, SES, SendGrid, and the development backends.
- **Graceful degradation everywhere.** An unreachable Redis, database, or DKIM dependency degrades with an error naming exactly what was lost, rather than aborting startup.

---

## Performance Improvements

- Mail moves off the request path entirely: a full SMTP conversation becomes one store write plus one enqueue.
- Workflow steps in \`WAITING\` consume no worker slot, replacing the pattern of a long-lived job blocking on its children.
- \`dedup="skip"\` collapses duplicate work before it executes — the cheapest possible optimization for a burst of identical requests.
- \`MemoryBackend\` is untouched; single-process applications see no change.
- \`SQLBackend\` claim is a single conditional \`UPDATE\` in a transaction; \`RedisBackend\` claim is one round trip against a sorted set.

---

## Developer Experience Improvements

- One mental model for background work: mail delivery is an ordinary task on an ordinary queue, visible in the admin dashboard alongside everything else.
- \`aq mail check\` catches DKIM misconfiguration before the first send fails.
- Structured faults name the failure precisely — \`TaskSerializationFault\` reports which argument, \`TaskWorkflowFault\` names the cycle.
- The \`aquilia.tasks\` package docstring no longer claims distributed backends and workflows are unimplemented.
- **Contract fields are visible to type checkers.** \`aq contracts stubs\` emits a \`.pyi\` so \`contract.total\` resolves to \`decimal.Decimal\` rather than \`Any\`, and a field typo fails CI instead of production.
- **Validation rules carry their own metadata.** Ordering, conditions, and groups live on \`@ward\` rather than inside ward bodies, so a rule's applicability is inspectable.
- **Configuration validates like request data.** \`Contract.from_env()\` runs environment variables through the same facets, so a bad \`PORT\` fails at startup with a field error instead of at first use with a \`ValueError\`.
- **Validation messages localize.** Every built-in message resolves through the i18n catalog's \`contracts.\` namespace, with no change for applications that do not configure i18n.

---

## Security Improvements

- **Webhook signature verification** for SES (topic ARN), SendGrid (ECDSA public key), and Mailgun (HMAC signing key), with replay rejection via a timestamp window. Without it, anyone can forge a bounce and suppress an arbitrary address.
- **DKIM signing** applied at the byte level immediately before transmission, covering exactly what the provider receives. Failures raise rather than shipping unsigned mail.
- **TLS enforcement** on SMTP remains on by default.
- **PII redaction** masks recipient local parts in logs while preserving domains.
- **Registry-only callable resolution** means a queue entry can never name a function the application did not register — a durable queue is not an arbitrary-code-execution channel.
- **Parameterized SQL throughout** the new backends and stores; table and column identifiers are validated against a restricted character set.

---

## Bug Fixes

| Issue | Subsystem | Fix |
|---|---|---|
| Mail delivery task unresolvable across processes | Mail / Tasks | Delivery registered as \`@task(name="aquilia.mail.deliver")\`; workers resolve it by stable name. |
| Consumer-only workers polled nothing | Tasks | Queues seeded from \`@task\` descriptors and refreshed from \`backend.get_queue_stats()\`. |
| Job results degraded to \`repr\` strings | Tasks | JSON-safe values round-trip; only non-serializable values fall back to \`repr\`. |
| \`queue.persistent\` had no config surface | Mail | Threaded through \`Integration.mail\`, \`MailIntegration\`, \`QueueConfigContract\`, and store selection. |
| \`Job.fingerprint\` computed but never read | Tasks | Enforced at enqueue via \`dedup\`. |
| \`MailSuppressedFault\` unreachable | Mail | Now part of a working suppression path. |
| Stale package docstring | Tasks | No longer lists shipped features as "deliberately absent". |
| Nested Contracts never ran wards or \`validate()\` | Contracts | Nested validation runs the child's full pipeline via \`run_nested_contract()\`. |
| \`list[Contract]\` annotations bypassed nested validation | Contracts | Detection looks through container facets, so both spellings route identically. |
| \`has_async_wards\` missed nested async wards | Contracts | Walks the facet tree, memoized, with cycle detection. |
| \`Lens(many=True)\` returned \`[]\` for unresolved relations | Contracts | Raises \`LensUnresolvedFault\` instead of shipping wrong data. |
| No async serialization path existed | Contracts | \`to_dict_async()\`, \`to_dict_many_async()\`, \`Lens.mold_async()\`. |
| Non-mapping input reported every field as missing | Contracts | Reports \`{"__all__": ["Expected an object, got str"]}\`. |
| \`IntFacet\` silently truncated \`3.9\` to \`3\` | Contracts | Fractional floats rejected; integral ones still accepted. |
| \`bytes\` fields were non-functional end to end | Contracts | \`bytes\` annotations route to the new \`BytesFacet\`. |
| \`"__minimal__"\` projection exposed every field | Contracts | Resolves to primary-key plus \`read_only\` facets. |
| Nesting-depth guard unreachable from the real path | Contracts | Depth threaded through \`Sigil.validate()\`; structured error. |
| Depth counter was global mutable state | Contracts | Replaced with a \`contextvars.ContextVar\`. |
| \`@computed\` ran against an uninitialized instance | Contracts | The live Contract instance is threaded in explicitly. |
| \`validate()\` ran up to three times per row in bulk paths | Contracts | Single shared \`_seal_row()\` / \`_seal_row_async()\`. |
| Top-level async wards bypassed groups and ordering | Contracts | \`is_sealed_async()\` uses the shared ward phase. |

Contract fixes are detailed in [Nested Validation Pipeline](contracts_pipeline.md) and [Validation Control & Typing](contracts_validation.md).

---

## Breaking Changes

The tasks, mail, and HTTP work introduces no breaking changes.

The Contracts audit ships **four deliberate behavioral corrections**. Each replaces behavior that was incorrect, so the change is the fix rather than a side effect of it:

| Change | Previously | Now | Who is affected |
|---|---|---|---|
| Nested Contract rules are enforced | A nested \`@ward\` or \`validate()\` override never ran | Runs, and rejects | Anyone whose nested Contracts declare rules. Payloads previously accepted may now be rejected. |
| \`Lens(many=True)\` unresolved relation | Returned \`[]\`, indistinguishable from "no rows" | Raises \`LensUnresolvedFault\` | Anyone serializing a to-many Lens without prefetching. Prefetch, materialize, or use \`to_dict_async()\`. |
| Malformed body error shape | Per-field "This field is required" | \`{"__all__": ["Expected an object, got str"]}\` | Clients parsing a 422 body that assume every key is a field name. |
| \`IntFacet\` fractional input | \`3.9\` silently became \`3\` | Rejected | Anyone relying on silent truncation. \`3.0\` is still accepted. |

\`"__minimal__"\` projections also return a restricted field set now; the previous output — every field — was never correct.

See the [Migration Guide](migration.md) for the review steps.

---

## Deprecated / Removed

**Deprecated:** the \`seal_*\` / \`async_seal_*\` Contract validator naming convention. Deprecated in 1.3.0, removed in 2.0.0. Declaring such a method now emits a \`DeprecationWarning\` naming its exact replacement decorator. Behavior is unchanged in 1.x — these methods continue to run exactly as before.

Migration is mechanical: decorate the method with \`@ward\` (or \`@ward(mode="async")\`); the body does not change. Find every affected method with \`python -W error::DeprecationWarning -c "import myapp.contracts"\`. Full guide in [Stub Generation & Deprecations](contracts_tooling.md#deprecated-the-seal_--async_seal_-prefix-convention).

**Removed:** the third-party \`httpx\` dependency. See [Native HTTP Client](http_native.md).

---

## Internal Refactoring

- MIME assembly extracted from four providers into \`aquilia/mail/mime.py\`.
- PII redaction extracted into \`aquilia/mail/redaction.py\`.
- The \`TaskBackend\` ABC gained \`heartbeat\`, \`reclaim_expired\`, \`reserve_fingerprint\`, \`release_fingerprint\`, and \`get_dependency_results\`, so \`MemoryBackend\` and the durable backends satisfy one contract.
- SMTP provider restructured around shared MIME assembly, byte-level signing, and pluggable authentication.

---

## Compatibility

| Area | Status |
|---|---|
| Python 3.10–3.13 | Supported, unchanged |
| Existing workspaces and manifests | No changes required |
| Existing \`@task\` functions | No changes required |
| Existing mail call sites | No changes required |
| Default behavior | Identical to v1.3.4 |

---

## Known Issues

- The Redis backend has no automated test coverage in this release; the SQL backend carries the durable-path integration tests.
- Mailgun signature verification is opt-in and warns when omitted.
- No built-in webhook route ships; applications wire the parsers into their own controller.
- Workflow steps whose parent failed remain \`WAITING\` rather than being cancelled.

Details and workarounds in the [Migration Guide](migration.md#known-issues).

---

## Testing

\`tests/test_tasks_mail_enterprise.py\` adds 43 tests covering job serialization, deduplication semantics, workflow composition and validation, durable-backend behavior driven against real SQLite (restart survival, cross-process queue discovery, cross-manager deduplication, lease reclaim), the mail delivery queue, suppression, webhook parsing and processing, and template autoescaping.

\`tests/test_audit_tasks_mail.py\` covers the mail provider, DKIM, MIME, redaction, and rate-limiting paths.

The Contracts audit adds 217 tests across six files (\`BP-SEC-014\` … \`BP-SEC-037\`):

| File | Covers |
|---|---|
| \`test_contract_audit_regressions.py\` | First-pass fixes: projections, depth guard, thread isolation, bulk-path \`validate()\` |
| \`test_contract_nested_pipeline.py\` | Nested wards, \`list[Contract]\` routing, async serialization, input adapters |
| \`test_contract_typing_features.py\` | New facets, equality, copy, frozen Contracts |
| \`test_contract_validation_control.py\` | Ward ordering/conditions/groups, fail-fast, i18n messages, \`from_env\`/\`from_cli\` |
| \`test_contract_stubs.py\` | Facet Python types, module stubs, the \`--check\` staleness gate |
| \`test_contract_ward_deprecation.py\` | \`seal_*\` warning content, and that legacy validators still run |

Full suite: 7,403 passing.

---

## Credits

Thanks to everyone who reported that \`backend="redis"\` did not do anything.
`,
    "bounces_suppression.md": `# Bounce Handling, Webhooks & Suppression Lists — Aquilia v1.3.5

Provider delivery events are now parsed, verified, and applied. A hard bounce or spam complaint automatically removes the address from all future sends. Before this release, \`MailSuppressedFault\` existed in the fault taxonomy but nothing raised it — there was no suppression list and no webhook handling at all.

---

## Motivation

Deliverability is reputation, and reputation is destroyed by continuing to mail addresses that bounce. Every ESP tracks bounce and complaint rates; exceed their thresholds and legitimate mail starts landing in spam or being rejected outright.

Handling this correctly requires three things Aquilia did not have: parsing each provider's webhook format, verifying those webhooks are genuine, and a persistent list consulted on every send.

---

## Architecture

\`\`\`
provider webhook (HTTP POST)
        │
        ▼
parse_ses / parse_sendgrid / parse_mailgun    ← verify signature, normalize
        │
        ▼
   list[WebhookEvent]                          ← provider-neutral
        │
        ▼
   process_webhook(events, suppression=..., store=...)
        │
        ├─ suppress the address (permanent or TTL)
        └─ update the envelope's status
        │
        ▼
next send → MailService filters suppressed recipients
\`\`\`

---

## Webhook Parsing

Three provider parsers normalize into one vocabulary:

\`\`\`python
from aquilia.mail import parse_ses, parse_sendgrid, parse_mailgun

parse_ses(payload, *, verify_topic_arn=None)
parse_sendgrid(payload, *, headers=None, public_key=None, max_age_seconds=600.0)
parse_mailgun(payload, *, signing_key=None, max_age_seconds=600.0)
\`\`\`

Each returns \`list[WebhookEvent]\`:

\`\`\`python
@dataclass
class WebhookEvent:
    event_type: EventType
    email: str
    provider: str
    timestamp: datetime
    message_id: str | None = None
    envelope_id: str | None = None   # from the X-Aquilia-Envelope-ID header
    detail: str | None = None        # e.g. the SMTP rejection line
    raw: dict[str, Any]              # original payload, kept for auditing
\`\`\`

\`EventType\` normalizes each provider's vocabulary: \`DELIVERED\`, \`HARD_BOUNCE\`, \`SOFT_BOUNCE\`, \`COMPLAINT\`, \`REJECTED\`, \`OPENED\`, \`CLICKED\`, \`UNSUBSCRIBED\`, \`DEFERRED\`, \`UNKNOWN\`. An unrecognized event becomes \`UNKNOWN\` and is preserved rather than dropped, so a provider adding a new type stays visible.

### Signature verification

**Verify webhooks in production.** An unverified endpoint lets anyone POST a forged bounce and suppress an arbitrary address — a trivial denial-of-service against your own users.

- **SES** — pass \`verify_topic_arn\` to reject notifications from any other SNS topic.
- **SendGrid** — pass \`public_key\` (the ECDSA verification key from your SendGrid settings) with the request \`headers\`. Replays older than \`max_age_seconds\` are rejected.
- **Mailgun** — pass \`signing_key\`. The HMAC signature and timestamp are verified.

Omitting these parameters parses without verification and logs a warning naming the risk.

---

## Suppression Lists

\`\`\`python
from aquilia.mail import SuppressionReason

await suppression.suppress(
    email,
    reason=SuppressionReason.HARD_BOUNCE,
    expires_in=None,      # seconds; ignored for permanent reasons
    provider="ses",
    detail="550 5.1.1 user unknown",
)
await suppression.unsuppress(email)          # -> bool
await suppression.is_suppressed(email)       # -> bool
await suppression.get(email)                 # -> SuppressionEntry | None
await suppression.list_all(limit=100, offset=0)
await suppression.filter_recipients(emails)  # -> (allowed, blocked)
await suppression.cleanup()                  # drop expired entries
\`\`\`

| Reason | Permanence |
|---|---|
| \`HARD_BOUNCE\` | Permanent — the address does not exist |
| \`SOFT_BOUNCE\` | Expires (defaults to 24 hours) — mailbox full, server down |
| \`COMPLAINT\` | Permanent — the most reputation-damaging signal a provider tracks |
| \`UNSUBSCRIBE\` | Permanent |
| \`MANUAL\` | Permanent — operator-added |

Two implementations ship: \`MemorySuppressionList\` (default) and \`SQLSuppressionList\` (table \`aquilia_mail_suppressions\`, selected by \`queue_persistent=True\`).

Addresses are normalized — lowercased and trimmed — before storage and lookup, so \`User@Example.COM\` and \` user@example.com \` are the same entry.

---

## Wiring a Webhook Endpoint

Aquilia does not register a webhook route for you; the path, authentication, and CSRF exemption belong to the application. The handler is a few lines:

\`\`\`python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        summary = await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        )
        return Response.json(summary)   # {"suppressed": 2, "delivered": 5, "ignored": 1}
\`\`\`

Exempt the webhook path from CSRF — providers do not carry your CSRF token. Rely on signature verification for authenticity instead.

---

## Enforcement on Send

\`MailService\` consults the suppression list while preparing every envelope. Suppressed recipients are removed; if *every* recipient is suppressed the envelope is marked \`CANCELLED\` and no delivery is attempted.

\`\`\`python
await mail.suppression.suppress("bounced@example.com", reason=SuppressionReason.HARD_BOUNCE)

envelope_id = await EmailMessage(subject="Hi", body="x", to="bounced@example.com").asend()
envelope = await mail.store.get(envelope_id)
envelope.status    # EnvelopeStatus.CANCELLED
\`\`\`

---

## Edge Cases

**Partial suppression.** An envelope with three recipients where one is suppressed sends to the remaining two. Only an envelope with no deliverable recipients is cancelled.

**Soft bounce TTL.** \`process_webhook\` suppresses soft bounces for \`soft_bounce_ttl\` (default 86,400 seconds) rather than permanently, since the cause is usually transient. Tune it per provider.

**Events with no address.** Counted as \`ignored\` rather than raising — a malformed event should not fail the whole batch.

**Non-suppressing events.** \`DELIVERED\`, \`OPENED\`, \`CLICKED\`, and \`DEFERRED\` update envelope status where applicable but never suppress.

**Malformed payloads.** A body that is not valid JSON raises \`MailFault\`, so a broken request surfaces as a 4xx rather than being silently swallowed.

**Envelope correlation.** Providers that echo custom headers return \`X-Aquilia-Envelope-ID\`, letting an event update the exact envelope. Providers that do not echo headers still suppress by address; the envelope simply is not correlated.

---

## Performance Implications

One suppression lookup per envelope on the send path. \`MemorySuppressionList\` is a dict lookup. \`SQLSuppressionList\` is an indexed primary-key read; \`filter_recipients\` batches a multi-recipient envelope rather than issuing one query per address.

Webhook processing is O(n) in events, with one suppression write per suppressing event.

---

## Compatibility

Purely additive. \`MailService.suppression\` defaults to an empty \`MemorySuppressionList\`, so no address is suppressed until a webhook or an operator adds one — existing applications see no behavioral change. \`MailSuppressedFault\`, previously unreachable, is now part of a working path.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "bugfixes.md": `# Bug Fixes — Aquilia v1.3.5

Four defects were found and fixed while auditing the enterprise task and mail work. Three would only surface once a durable or distributed backend was in use — which is exactly what this release enables, so each would have been a first-day production failure for anyone adopting the new capability.

---

## 1. Mail delivery task unresolvable across processes

**Severity:** Critical, on any persistent backend.

### Previous behavior

Background mail delivery enqueued a plain module-level function. On \`MemoryBackend\` this worked, because the job carried the live callable in-process.

The moment a durable backend was configured, delivery stopped. The job serialized to a module-path reference, and the consuming worker — which resolves callables through the \`@task\` registry rather than importing arbitrary paths — could not resolve it. Envelopes sat in \`QUEUED\` forever. Nothing crashed loudly; mail simply never arrived.

### Root cause

\`_deliver_envelope_task\` was a bare \`async def\`, never registered with \`@task\`. Worker resolution goes through \`get_task(job.func_ref)\`, which only knows about registered descriptors. This is a deliberate security property — a queue entry must not be able to name arbitrary importable code — but it means an unregistered function is unreachable.

### New behavior

The delivery task is registered under a stable name:

\`\`\`python
@task(name="aquilia.mail.deliver", queue=MailService.retry_queue, max_retries=0)
async def _deliver_envelope_task(envelope_id: str) -> None: ...
\`\`\`

A worker in any process resolves it by name. The name is stable, so a future rename of the Python function does not orphan jobs already in the queue.

### User impact

Anyone enabling \`queue_enabled=True\` together with \`backend="redis"\` or \`backend="sql"\` would have had silently undelivered mail. Fixed before either capability shipped.

---

## 2. Consumer-only workers polled nothing

**Severity:** Critical, for distributed deployments.

### Previous behavior

A dedicated worker process — one that consumes jobs but never enqueues any — processed nothing. Jobs queued by web workers on any queue other than \`default\` were ignored indefinitely.

### Root cause

\`TaskManager._queues\` was populated exclusively as a side effect of \`enqueue()\`. A process that never enqueues therefore knew about exactly one queue: its configured \`default_queue\`. The worker loop iterates the known queue set, so work on \`mail\`, \`reports\`, or any other queue was invisible to it.

This was harmless while everything ran in one process — the enqueuer and the worker were the same object. It becomes fatal the moment producer and consumer are separate processes, which is the entire point of a distributed backend.

### New behavior

Two additions:

1. \`_bind_task_descriptors()\` registers the queue of every \`@task\` descriptor, so importing a task module is enough to poll its queue.
2. On a distributed backend, the manager adopts queues reported by \`backend.get_queue_stats()\` at startup and refreshes them on each reclaim tick — so a queue created by a peer after startup is picked up.

### User impact

Dedicated worker processes now consume the queues their producers use, without needing to be told which those are.

---

## 3. Job results degraded to repr strings on persistent backends

**Severity:** High — silent data corruption in workflows.

### Previous behavior

\`\`\`python
# In-process
job.result.value    # 4  (int)

# Same job on a SQL or Redis backend
job.result.value    # '4'  (str)
\`\`\`

A chord callback consuming \`parent_results\` received \`['4', '6']\` instead of \`[4, 6]\`. Arithmetic silently produced string concatenation or a \`TypeError\` far from the cause.

### Root cause

\`JobResult.to_dict()\` serialized unconditionally with \`repr(self.value)\`. The rationale — an arbitrary return value is not guaranteed to be JSON-compatible — was sound, but the blanket application destroyed values that serialize perfectly well.

### New behavior

JSON-safe values round-trip unchanged; only genuinely non-serializable values fall back to \`repr\`:

\`\`\`python
value = self.value
if value is not None:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        value = repr(value)
\`\`\`

### User impact

Workflow fan-in receives real values on every backend. Applications that had adapted to the string form — parsing \`repr\` output back — should remove that workaround.

\`\`\`python
# Before — workaround
total = sum(int(r) for r in parent_results)

# After
total = sum(parent_results)
\`\`\`

---

## 4. \`queue.persistent\` had no configuration surface or wiring

**Severity:** Medium — an advertised capability that could not be reached.

### Previous behavior

\`SQLEnvelopeStore\` and \`SQLSuppressionList\` existed and worked, but nothing constructed them from configuration. The only way to get durable mail state was to instantiate the stores by hand and pass them to \`MailService(store=..., suppression=...)\`. The \`queue\` config block had no \`persistent\` key at all, so setting it in \`workspace.py\` was silently dropped by contract validation.

### New behavior

\`persistent\` is a real config field, threaded end to end:

- \`Integration.mail(queue_persistent=True)\`
- \`MailIntegration.queue_persistent\`
- \`QueueConfigContract.persistent\`
- \`MailService._prepare_stores()\` selects SQL-backed stores when set

An unavailable database logs an error naming the durability that was lost and falls back to in-memory stores, rather than aborting startup — mail degrades to non-durable instead of taking the application down.

Explicitly-supplied stores still win: a caller passing \`store=\` meant it, and configuration does not override that.

### User impact

Durable envelope and suppression storage is now reachable from \`workspace.py\`.

---

## Documentation Correctness Fix

The \`aquilia.tasks\` package docstring listed "Persistent or distributed backends", "Job chaining / workflow DAGs" under **"Not implemented today (deliberately absent, not stubbed)"**. All three shipped in this release; the docstring is updated. It now documents the at-least-once delivery contract instead, and the one thing still genuinely absent (per-queue rate limiting).

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Mail Delivery Queue](mail_queue.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — Contract subsystem fixes in this release
- [Migration Guide](migration.md)
`,
    "cli.md": `# CLI Changes — Aquilia v1.3.5

One command group was added (\`aq contracts\`). One existing command gained new validation. Nothing was removed or renamed.

---

## New: \`aq contracts stubs\`

Emits \`.pyi\` type stubs so \`mypy\` and \`pyright\` can see Contract fields.

### Why

A Contract builds its fields at class-body evaluation time and serves them through \`__getattr__\`. Neither is visible to a static analyser, so \`contract.email\` was \`Any\` at best and an attribute error under \`--strict\` at worst. For a team with a type-checking gate in CI, this was the single largest adoption barrier.

A generated \`.pyi\` is a portable artifact: every type checker consumes it with no plugin, no configuration, and no version coupling.

### Usage

\`\`\`bash
aq contracts stubs MODULES... [--check] [--path DIR]
\`\`\`

| Flag | Purpose |
|---|---|
| \`--check\` | Do not write. Exit non-zero if any stub is missing or out of date. |
| \`--path DIR\` | Directory prepended to \`sys.path\` before importing. Default: current directory. |

### Examples

\`\`\`bash
# Write myapp/contracts.pyi
aq contracts stubs myapp.contracts

# Several modules at once
aq contracts stubs myapp.users.contracts myapp.orders.contracts

# CI freshness gate
aq contracts stubs myapp.contracts --check
\`\`\`

### Output

Success:

\`\`\`
$ aq contracts stubs myapp.contracts
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
\`\`\`

Anything that could not be typed faithfully is emitted as \`Any\` and named, so a lost annotation is reported rather than silently weakening the module's types:

\`\`\`
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
      REGISTRY: module-level value emitted as Any
\`\`\`

\`--check\` on a stale or missing stub exits \`1\` and prints the fix:

\`\`\`
$ aq contracts stubs myapp.contracts --check
  ✘ myapp.contracts: contracts.pyi is missing or out of date
      2 contract(s): AddressContract, OrderContract

  Stubs are out of date. Regenerate with:
      aq contracts stubs myapp.contracts
\`\`\`

A module that fails to import, or that has no source file, exits \`1\` with the reason.

### Recommended workflow

Commit the generated stubs, then gate on freshness:

\`\`\`bash
# Once, after declaring or changing Contracts
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
\`\`\`

\`\`\`yaml
# .github/workflows/ci.yml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check

- name: Type check
  run: mypy myapp/
\`\`\`

Generation is deterministic — regenerating unchanged input is a byte-identical no-op, so \`--check\` cannot fail at random.

Full details in [Stub Generation & Deprecations](contracts_tooling.md).

---

## \`aq mail check\`

\`aq mail check\` validates mail configuration without sending anything. It now also validates DKIM configuration.

### Why

DKIM signing failures raise at send time rather than silently shipping an unsigned message — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or a loud error. That is the right runtime behavior, but it means a misconfiguration is not discovered until the first real send, possibly in production.

\`aq mail check\` now surfaces both failure modes up front.

### New checks

When \`dkim_enabled\` is true:

1. **\`dkim_domain\` unset** — signing cannot proceed without a domain.
2. **\`dkimpy\` not installed** — the signing dependency is missing.

### Output

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

A clean configuration reports no issues, as before.

### Recommended workflow

\`\`\`bash
# After enabling DKIM in workspace.py
pip install aquilia[mail-dkim]
aq mail check                          # verify configuration
aq mail send-test --to you@example.com # verify real delivery
\`\`\`

Add \`aq mail check\` to CI or a deploy preflight step for any application that sends mail.

---

## Unchanged Commands

\`aq mail send-test\` and \`aq mail inspect\` are unchanged. No flags were added, changed, or deprecated, and no output formats changed.

Background task workers are not started by a dedicated CLI command; a worker process is a normal Aquilia application configured with \`num_workers\` and a shared backend. See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Related

- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "contracts_pipeline.md": `# Contracts — Nested Validation Pipeline — Aquilia v1.3.5

A deep audit of \`aquilia/contracts/\` found that a nested Contract's business rules never ran. \`Sigil.validate()\` recursed into the child's *structural* pass only — it validated field types and required-ness, then returned. Every \`@ward\` method and every object-level \`validate()\` override declared on a nested Contract was silently skipped.

This is the most severe defect fixed in this release. A nested Contract expressing an authorization check or a cross-field invariant enforced nothing, and the payload was accepted.

---

## 1. Nested Contracts never ran their wards or \`validate()\` hook

**Severity:** Critical — silent validation bypass.

### Previous behavior

\`\`\`python
from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import IntFacet

class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # True  ← the ward never ran
order.errors        # {}
\`\`\`

\`qty=0\` is structurally a valid integer, so the structural pass accepted it. The rule that says it is *business*-invalid never executed.

### Root cause

\`Sigil.validate()\` recursed directly into the child's compiled schema:

\`\`\`python
sub_errors, sub_validated = nested_cls._sigil.validate(raw, ...)
\`\`\`

A \`Sigil\` is the compiled *structural* representation of a Contract — field specs, types, required-ness. It has no knowledge of ward methods, which live on the Contract class and are invoked by \`Contract.is_sealed()\`. Because the nested Contract was never instantiated, \`is_sealed()\` was never called on it, so neither the ward phase nor the \`validate()\` hook ran.

This was not limited to async wards as originally reported. Synchronous wards were dead too.

### New behavior

Nested validation runs the child's full pipeline through a single shared helper, \`run_nested_contract()\`:

\`\`\`python
order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

Errors are reported at the failing field's path. For a to-many relation the row index is preserved rather than flattened away, so a client can point at the offending item.

\`\`\`python
order = Order(data={"items": [{"qty": 5}, {"qty": 0}]})
order.errors
# {"items": {"1": {"qty": ["Must be at least 1"]}}}
\`\`\`

### User impact

**This is a behavioral change.** Payloads that previously passed validation may now be rejected — correctly. If a nested Contract in your application declares a \`@ward\` or overrides \`validate()\`, that rule is now enforced for the first time.

Before upgrading, review nested Contracts for rules that were silently inert. A rule written against an assumption that no longer holds will now start rejecting traffic.

---

## 2. \`list[Contract]\` annotations bypassed the nested pipeline

**Severity:** Critical — the fix above did not reach the most common spelling.

### Previous behavior

A to-many nested relation has two spellings that mean the same thing to a reader:

\`\`\`python
# Spelling A — explicit facet
items = NestedContractFacet(LineItem, many=True)

# Spelling B — type annotation
items: list[LineItem] = None
\`\`\`

They build *different facets*. Spelling A builds a \`NestedContractFacet\` with \`many=True\`. Spelling B builds a \`ListFacet\` whose \`child\` is a \`NestedContractFacet\`.

Nested detection matched only \`NestedContractFacet\`, so spelling B was classified as an ordinary list of values. It ran structural validation alone — meaning the nested-pipeline fix in section 1 did not apply to it, and \`has_async_wards\` reported \`False\` for a Contract whose children declared async wards.

\`\`\`python
class Order(Contract):
    items: list[LineItem] = None       # ← annotated spelling

Order(data={}).has_async_wards          # False, even when LineItem has async wards
\`\`\`

Because \`has_async_wards\` gates which entry point the framework uses, reporting \`False\` sent callers down the synchronous path — where the async ward was skipped silently rather than raising \`ContractAsyncMismatchFault\`.

### Root cause

\`build_sigil()\` set \`is_nested_contract\` with a direct type check:

\`\`\`python
is_nested = isinstance(facet, (NestedContractFacet, LazyContractFacet))
\`\`\`

A \`ListFacet\` wrapping a nested facet is not an instance of either, so the flag was \`False\` and every downstream consumer — validation routing, async-ward detection, JSON Schema generation — treated the field as a plain list.

### New behavior

Detection now looks through container facets. Both spellings route identically:

\`\`\`python
class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

Async wards are detected through the list, so the sync entry point raises rather than skipping:

\`\`\`python
Order(data={}).has_async_wards          # True
Order(data={"items": [...]}).is_sealed()  # raises ContractAsyncMismatchFault
await Order(data={"items": [...]}).is_sealed_async()   # correct
\`\`\`

JSON Schema also improves, because an annotated list of Contracts is now emitted as an array of \`$ref\` rather than an untyped array:

\`\`\`python
Order._sigil.to_json_schema()["properties"]["items"]
# {"type": "array", "items": {"$ref": "#/$defs/LineItem"}}
\`\`\`

Two functions carry this:

| Function | Purpose |
|---|---|
| \`is_nested_facet(facet)\` | Whether a facet wraps a nested Contract, **without resolving it**. Used at class-body evaluation time, where a forward reference usually names the Contract currently being built. |
| \`resolve_nested(facet)\` | Returns \`(contract_cls, is_many)\`, looking through container facets. Returns \`(None, False)\` for an unresolvable forward reference rather than raising. |

\`get_nested_contract_cls()\` remains, now delegating to \`resolve_nested()\`, so existing callers are unaffected.

### User impact

The same behavioral change as section 1, now applying to the annotated spelling. Since \`items: list[LineItem]\` is the idiomatic form, most applications are affected by this fix rather than by section 1 alone.

---

## 3. \`has_async_wards\` consulted only the top-level class

**Severity:** High — silent skip instead of a clear error.

### Previous behavior

\`\`\`python
class Child(Contract):
    sku = TextFacet()

    @ward(mode="async")
    async def in_stock(self, data):
        if not await lookup(data["sku"]):
            self.reject("sku", "Out of stock")

class Parent(Contract):
    child: Child = None

Parent(data={}).has_async_wards   # False
\`\`\`

The property checked \`self._ward_methods\` — the wards declared on *this* class. A Contract whose nested child declared an async ward reported \`False\`, so callers took the synchronous path and the ward never ran. The intended failure mode was a loud \`ContractAsyncMismatchFault\`; the actual behavior was a silent skip.

### New behavior

The property walks the facet tree:

\`\`\`python
Parent(data={}).has_async_wards   # True
\`\`\`

Implementation notes that matter for correctness:

- **Memoized per class** (\`_async_wards_deep_cache\`) so the walk costs nothing after the first call. Contract classes are compiled once at import, so the answer cannot change at runtime.
- **Cycle detection** via a \`_seen\` set of class IDs, so a self-referential Contract (\`Node\` containing \`list[Node]\`) terminates.
- **Incomplete answers are never cached.** If the walk hits an unresolved forward reference or truncates at a cycle, the result is returned but not memoized — caching \`False\` from a truncated walk would permanently disable async detection for that class.

### User impact

A Contract with async wards nested beneath it now correctly requires \`is_sealed_async()\`. Code that called \`is_sealed()\` and appeared to work was not running the ward at all; it now raises \`ContractAsyncMismatchFault\` naming the problem.

---

## 4. No async serialization path existed

**Severity:** High — an async ORM with a sync-only serializer.

### Previous behavior

Aquilia's ORM relations are async, but every serialization entry point was synchronous. An un-awaited \`RelatedManager\` reaching \`Lens.mold()\` could only raise — there was no path that awaited it.

\`\`\`python
order = await Order.objects.get(pk=1)
OrderContract(instance=order).to_dict()
# LensUnresolvedFault — and no async alternative existed
\`\`\`

The only workaround was to prefetch every relation before serializing.

### New behavior

Three async entry points, mirroring the sync ones:

\`\`\`python
# Single instance
data = await OrderContract.to_dict_async(order)

# Collection
rows = await OrderContract.to_dict_many_async(orders)
\`\`\`

\`Lens.mold_async()\` awaits the relation, so prefetching becomes an optimization rather than a requirement:

\`\`\`python
class OrderContract(Contract):
    items = Lens(ItemContract, many=True)

order = await Order.objects.get(pk=1)          # items not prefetched
data = await OrderContract.to_dict_async(order)  # awaits order.items
\`\`\`

The synchronous path still raises \`LensUnresolvedFault\` — see section 5.

### Design: one field loop, two drivers

Sync and async serialization share a single field-molding generator, \`_mold_steps()\`, which yields \`(facet, raw_value)\` pairs for a driver to resolve:

\`\`\`python
# Sync driver
for facet, raw in self._mold_steps(...):
    result[name] = facet.mold(raw)

# Async driver
for facet, raw in self._mold_steps(...):
    result[name] = await facet.mold_async(raw)
\`\`\`

The field-selection logic — projections, \`write_only\` exclusion, computed fields, source resolution — exists once. A copy-paste async variant would drift from its sync twin at the first bug fix applied to only one of them.

### Performance

\`to_dict_async()\` awaits relations sequentially, one relation at a time. It is not slower than the sync path for prefetched data — awaiting an already-materialized list is close to free. For un-prefetched relations it issues one query per relation, so **prefetching remains the right choice on hot paths**; the async path exists so that forgetting to prefetch degrades performance rather than raising.

---

## 5. \`Lens(many=True)\` silently returned \`[]\` for unresolved relations

**Severity:** High — silent wrong data shipped to clients.

### Previous behavior

\`\`\`python
order = await Order.objects.get(pk=1)   # items NOT prefetched
OrderContract(instance=order).data
# {"items": []}   ← indistinguishable from "this order has no items"
\`\`\`

An un-awaited \`RelatedManager\` produced an empty list with no error. A client could not tell the difference between an order with no line items and an order whose line items failed to load.

### New behavior

\`\`\`python
OrderContract(instance=order).data
# LensUnresolvedFault (BP503): naming the field and the fix
\`\`\`

Three ways to resolve it:

\`\`\`python
# 1. Prefetch (best for hot paths)
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the async serializer, which awaits for you
await OrderContract.to_dict_async(order)
\`\`\`

### User impact

**This is a behavioral change.** Code relying on the silent empty-list fallback now raises. That fallback produced incorrect API responses — an empty relation and a failed-to-load relation are different facts, and conflating them ships wrong data without any signal.

---

## 6. Non-mapping input reported every field as missing

**Severity:** Medium — a misdiagnosis that cost debugging time.

### Previous behavior

A scalar or list request body was coerced to \`{}\`:

\`\`\`python
UserContract(data="not an object").errors
# {"name": ["This field is required"],
#  "email": ["This field is required"],
#  "age": ["This field is required"]}
\`\`\`

The real problem — the body was a string, not an object — was invisible. Developers chased missing fields that were never missing.

### New behavior

\`\`\`python
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

### User impact

**This is a behavioral change** in error *shape*, not in accept/reject. A malformed body previously produced per-field errors and now produces a single \`__all__\` entry. Clients that parse the 422 body and assume every key is a field name should treat \`__all__\` as a document-level error.

The same correction applies to the bulk paths:

\`\`\`python
UserContract.seal_many(["not a row"])[0].errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

---

## 7. Top-level async wards bypassed group and ordering semantics

**Severity:** Medium — inconsistent behavior between entry points.

### Previous behavior

\`is_sealed_async()\` ran async wards through its own inline loop rather than the shared ward phase. The result: \`order\`, \`when\`, \`groups\`, and \`Spec.fail_fast\` applied on the bulk paths (\`seal_many\`, \`seal_stream\`) but not on the single-item async path.

\`\`\`python
class Checkout(Contract):
    @ward(groups=("checkout",), mode="async")
    async def payment_valid(self, data): ...

await Checkout(data=...).is_sealed_async()   # ran the ward regardless of groups
\`\`\`

### Root cause

Duplicated logic. \`_run_ward_phase_async()\` already existed and implemented all four features; \`is_sealed_async()\` predated it and kept its own copy.

### New behavior

The duplicate loop is gone. \`is_sealed_async()\` calls \`_run_ward_phase_async()\`, so every entry point applies identical semantics:

\`\`\`python
await Checkout(data=...).is_sealed_async()                      # grouped ward skipped
await Checkout(data=...).is_sealed_async(groups="checkout")     # grouped ward runs
\`\`\`

---

## Input adapters: dataclasses, attrs, and TypedDict

Contracts now accept dataclass instances, attrs classes, and \`TypedDict\` values as input, at every level:

\`\`\`python
from dataclasses import dataclass

@dataclass
class LineItemDTO:
    qty: int

class Order(Contract):
    items: list[LineItem] = None

Order(data={"items": [LineItemDTO(qty=3)]}).is_sealed()   # True
\`\`\`

Adaptation happens at a single point (\`sigil.adapt_input\`) that feeds the *existing* cast/seal pipeline. There is no parallel validation path for dataclass input, so a dataclass and the equivalent dict validate identically.

Adaptation is **shallow by design**. A dataclass field holding another dataclass is handled by the nested-Contract branch, not by recursive adaptation — the nested Contract knows the target shape, and a blind deep walk would convert values the target facet expects to receive intact.

---

## Depth guard correctness

Two related fixes to the recursion guard:

### The guard was unreachable from the real validation path

\`MAX_NESTING_DEPTH = 32\` was enforced in \`NestedContractFacet.cast()\`. The primary path (\`Contract(data=...).is_sealed()\`) never called \`cast()\` — it recursed through the Sigil — so the guard and its tests were unreachable from ordinary request validation. A few kilobytes of deeply nested JSON against any endpoint accepting a self-referential Contract raised an uncaught \`RecursionError\` inside the request coroutine.

Depth is now threaded through \`Sigil.validate()\` and yields a structured error:

\`\`\`python
Node(data=deeply_nested).errors
# {"child": ["Nested Contract depth exceeds maximum of 32"]}
\`\`\`

\`MAX_NESTING_DEPTH\` moved to \`aquilia/contracts/exceptions.py\` so the Sigil and facet layers cannot disagree about the limit.

### The depth counter was global mutable state

\`NestedContractFacet._current_nesting_depth\` was a plain class attribute mutated with \`+=\`/\`-=\` — shared across every instance, every Contract class, and every thread, despite a source comment claiming thread-locality. Concurrent validation could both reject shallow payloads spuriously *and* undercount deep ones, defeating the guard exactly when it mattered.

It is now a \`contextvars.ContextVar\`, correct for threads and asyncio tasks alike, covered by a 20-thread concurrency test.

---

## Related pages

- [Contracts — Validation Control & Typing](contracts_validation.md) — ward ordering, groups, new facets, i18n messages
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — \`aq contracts stubs\`, \`seal_*\` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
- [Bug Fixes](bugfixes.md) — task and mail subsystem fixes in this release
`,
    "contracts_tooling.md": `# Contracts — Stub Generation & Deprecations — Aquilia v1.3.5

Two developer-experience changes: a new \`aq contracts stubs\` command that makes Contract fields visible to \`mypy\` and \`pyright\`, and a formal deprecation of the \`seal_*\` / \`async_seal_*\` validator naming convention.

---

## \`aq contracts stubs\` — static typing support

### Motivation

A Contract resolves its fields at class-body evaluation time and serves them through \`__getattr__\`. Both are invisible to a static analyser:

\`\`\`python
class UserContract(Contract):
    email = TextFacet()
    age = IntFacet()

contract = UserContract(data=payload)
contract.is_sealed()
reveal_type(contract.email)   # Any — the type checker sees nothing
contract.emial                # typo: no error until runtime
\`\`\`

For a team running \`mypy --strict\` or \`pyright\` in CI, this was the single largest adoption barrier. Every Contract access was an untyped hole, and a field typo survived review to fail in production.

### Design goals

Two approaches were considered:

| Approach | Trade-off |
|---|---|
| A \`mypy\` plugin | Deep integration, but bespoke per type checker. \`pyright\` users get nothing. Plugin APIs are unstable across releases. |
| **Generated \`.pyi\` stubs** | A portable artifact every type checker consumes with no plugin, no configuration, and no version coupling. Checked into the repository like any other generated file. |

Stubs won. The output is inspectable, diffable in review, and works identically under \`mypy\`, \`pyright\`, and any editor's language server.

### Usage

\`\`\`bash
# Write myapp/contracts.pyi
aq contracts stubs myapp.contracts

# Several modules at once
aq contracts stubs myapp.users.contracts myapp.orders.contracts

# CI gate: fail if a stub is missing or stale
aq contracts stubs myapp.contracts --check
\`\`\`

| Flag | Purpose |
|---|---|
| \`--check\` | Do not write. Exit non-zero if any stub is missing or out of date. |
| \`--path\` | Directory prepended to \`sys.path\` before importing. Default: current directory. |

### Example output

Given:

\`\`\`python
# myapp/contracts.py
from __future__ import annotations

import enum

from aquilia.contracts import Contract
from aquilia.contracts.facets import ChoiceFacet, DecimalFacet, IntFacet, ListFacet, TextFacet


class Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


class AddressContract(Contract):
    city = TextFacet()
    zip = TextFacet(allow_null=True)


class OrderContract(Contract):
    id = IntFacet()
    total = DecimalFacet()
    tags = ListFacet(child=TextFacet())
    status = ChoiceFacet(choices=["new", "paid"])

    async def refresh(self, count: int) -> str: ...
\`\`\`

\`aq contracts stubs myapp.contracts\` produces:

\`\`\`python
# myapp/contracts.pyi
# Generated by \`aq contracts stubs\`. Do not edit by hand.
# Regenerate after changing the Contract declarations in the paired module.

from typing import Any, Literal
import enum
from aquilia.contracts import Contract
from aquilia.contracts.facets import ChoiceFacet, DecimalFacet, IntFacet, ListFacet, TextFacet
import aquilia.contracts.core
import decimal

class Colour(enum.Enum):
    RED = 'red'
    BLUE = 'blue'

class AddressContract(aquilia.contracts.core.Contract):
    city: str
    zip: str | None

class OrderContract(aquilia.contracts.core.Contract):
    id: int
    total: decimal.Decimal
    tags: list[str]
    status: Literal['new', 'paid']
    async def refresh(self, count: int) -> str: ...
\`\`\`

Now the type checker sees the fields:

\`\`\`python
reveal_type(contract.total)    # decimal.Decimal
reveal_type(contract.tags)     # list[str]
reveal_type(contract.status)   # Literal['new'] | Literal['paid']
\`\`\`

### How it works

Stubs are generated **at runtime, after \`ContractMeta\` has compiled the class** — that is what makes the facets inspectable. A purely static generator would have to re-implement annotation resolution and would drift from the real one.

Each facet reports the Python type it *produces*, through a \`python_type()\` method:

\`\`\`python
IntFacet().python_type()                         # "int"
DecimalFacet().python_type()                     # "decimal.Decimal"
ListFacet(child=TextFacet()).python_type()       # "list[str]"
ChoiceFacet(choices=["a", "b"]).python_type()    # "Literal['a', 'b']"
\`\`\`

Facets are the source of truth rather than a parallel mapping table in the generator, so a new facet declares its own type and stub generation picks it up with no second edit.

**The type is the post-cast type, not the wire type.** \`IntFacet\` accepts the string \`"42"\` on the wire but yields \`int\`, and the stub says \`int\` — that is what a caller reading \`contract.qty\` actually receives.

Notable resolutions:

| Facet | Emitted type | Reason |
|---|---|---|
| \`SecretFacet\` | \`Secret\` | \`cast()\` wraps the value. Promising \`str\` would let \`contract.password.lower()\` type-check and fail at runtime. |
| \`PathFacet\` | \`pathlib.PurePosixPath\` | The validated value, not the input string. |
| \`Lens(...)\` | \`dict[str, Any]\` | A Lens molds to a dict. Naming the Contract would let \`order.customer.is_sealed()\` type-check against a dict. |
| Nested Contract | \`dict[str, Any]\` | Same reason — the validated payload is a mapping. |
| \`EnumFacet(Colour)\` | \`myapp.enums.Colour\` | Fully qualified, so the import is derivable from the name. |

**Nullability is widened.** A facet accepting \`None\` — via \`allow_null\`, or by defaulting to it — is annotated optional:

\`\`\`python
zip = TextFacet(allow_null=True)     # → zip: str | None
\`\`\`

Omitting \`| None\` would be worse than emitting no stub at all: it tells the type checker a guard is unnecessary at exactly the points one is required.

### Limitations

**A \`.pyi\` replaces its module for the type checker — it does not augment it.** The generator therefore reproduces the whole module surface, not only its Contracts: import statements are replayed from the source AST, and module-level classes, functions, and constants are emitted with their runtime signatures.

Anything that cannot be rendered faithfully is emitted as \`Any\` and reported:

\`\`\`
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
      REGISTRY: module-level value emitted as Any
\`\`\`

A lost annotation is named rather than silently weakening the module's types.

Other limits:

- The module must be importable. Import side effects run during generation.
- A module with no \`__file__\` — a namespace package, or a synthetic module — raises \`StubGenerationFault\` (\`BP600\`), since there is nowhere a stub could sit.
- Facets that declare no narrower type emit \`Any\` and appear in the degraded list.

### CI workflow

Commit the generated stubs, then gate on freshness:

\`\`\`yaml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts myapp.orders.contracts --check
\`\`\`

\`--check\` exits non-zero when a stub is missing or stale, and prints the command to regenerate:

\`\`\`
  ✘ myapp.contracts: contracts.pyi is missing or out of date
      2 contract(s): AddressContract, OrderContract

  Stubs are out of date. Regenerate with:
      aq contracts stubs myapp.contracts
\`\`\`

Generation is deterministic — regenerating unchanged input is a byte-identical no-op, so \`--check\` cannot fail at random.

### Python API

The CLI is a thin wrapper; the same functions are importable:

\`\`\`python
from aquilia.contracts import generate_module_stub, write_module_stub
import myapp.contracts

report = write_module_stub(myapp.contracts)
report.path         # PosixPath('/app/myapp/contracts.pyi')
report.contracts    # ('AddressContract', 'OrderContract')
report.degraded     # () — members emitted as Any
report.is_current   # True

# Build without touching the filesystem
report = write_module_stub(myapp.contracts, dry_run=True)
\`\`\`

---

## Deprecated: the \`seal_*\` / \`async_seal_*\` prefix convention

**Deprecated in 1.3.0 — removed in 2.0.0.**

Before the \`@ward\` decorator existed, a method was registered as a cross-field validator purely because its name began with \`seal_\` or \`async_seal_\`. Declaring one now emits a \`DeprecationWarning\` at class-body evaluation:

\`\`\`
DeprecationWarning: OrderContract.seal_total is registered as a validator by the
deprecated seal_*/async_seal_* prefix convention (deprecated in Aquilia 1.3.0,
removed in 2.0.0). Decorate it with @ward instead — the method body does not need
to change, and you may then rename it freely. After 2.0.0, OrderContract.seal_total
will be treated as an ordinary method and will silently stop validating.
\`\`\`

**Behavior is unchanged in 1.x.** These methods continue to run exactly as before; only the warning is new. Deprecating the convention must not disarm it — a rule that stopped firing in a feature release would ship the exact bug the deprecation warns about.

### Why the convention is going away

Each of these has cost real debugging time:

- **A rename silently disables validation.** Renaming \`seal_total\` to \`check_total\` during a routine cleanup removes the rule with no error, no warning, and no failing test unless one happens to cover that exact rule. The Contract keeps reporting success on payloads it should reject.
- **A name collision silently creates one.** A helper legitimately named \`seal_envelope\` is executed as a validator on every request, its return value discarded and any exception it raises turned into a user-facing field error.
- **Async mode was inferred, not declared.** Mode came from \`inspect.iscoroutinefunction\`, so a validator awaiting the database while written as a sync \`def\` registered as sync — the coroutine was created, never awaited, and the check never ran.
- **No room to grow.** Ordering, conditions, and validation groups have nowhere to live in a naming convention. \`@ward\` carries them as metadata. See [Validation Control](contracts_validation.md#ward-ordering-conditions-and-groups).

### Migration

Mechanical — decorate the method. The body does not change.

\`\`\`python
# Before (deprecated)
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")

# After
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

Two things change beyond the decorator: \`mode="async"\` becomes explicit rather than inferred, and the methods can be renamed to describe the rule rather than to satisfy the scanner.

Adding \`@ward\` without renaming is a valid intermediate step — the decorator is the registration, so the name becomes irrelevant and the warning goes quiet:

\`\`\`python
@ward
def seal_total(self, data): ...    # no warning; rename later at leisure
\`\`\`

### Finding every affected method

Promote the warning to an error and import your Contract modules:

\`\`\`bash
python -W error::DeprecationWarning -c "import myapp.contracts"
\`\`\`

Or fail the test suite on it:

\`\`\`toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
\`\`\`

Both report each legacy method with its class name, its exact replacement decorator, and the file and line that declared it. Because registration happens at class-body evaluation, **importing the module is enough** — no request needs to run.

### Version constants

The deprecation timeline is programmatically available:

\`\`\`python
from aquilia.contracts.ward import (
    DEPRECATED_PREFIX_SINCE,       # "1.3.0"
    DEPRECATED_PREFIX_REMOVED_IN,  # "2.0.0"
)
\`\`\`

---

## Related pages

- [Contracts — Validation Control & Typing](contracts_validation.md) — \`@ward\` ordering, conditions, and groups
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — nested wards, async serialization
- [CLI Changes](cli.md) — all CLI changes in this release
- [Migration Guide](migration.md) — upgrade checklist
`,
    "contracts_validation.md": `# Contracts — Validation Control & Typing — Aquilia v1.3.5

The second half of the Contracts audit closed the gaps between what a Contract could express and what real validation needs: rule ordering, conditional rules, validation groups, fail-fast, frozen Contracts, and the strongly-typed primitives that previously fell through to a permissive \`TextFacet\`.

Everything here is additive. A Contract that declares none of it behaves exactly as it did in v1.3.4.

---

## Ward ordering, conditions, and groups

### Motivation

\`@ward\` had exactly one knob: \`mode\`. Real validation needs three more, and without them each was hand-rolled inside ward bodies where it could not be inspected, reordered, or reused.

| Need | Previous workaround |
|---|---|
| Run a cheap check before an expensive one | Rely on definition order and hope nobody reorders the methods |
| A rule that applies only to some payloads | \`if\` at the top of the ward body |
| Different rules for different operations | A separate Contract subclass per operation |

### \`order\` — deterministic sequencing

\`\`\`python
class OrderContract(Contract):
    @ward(order=-10)
    def total_not_negative(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(order=0)          # default
    async def payment_authorized(self, data):
        ...                  # expensive: hits the payment provider
\`\`\`

Lower runs first. Wards sharing an \`order\` keep definition order — the sort is stable, so a Contract that sets no \`order\` behaves exactly as before.

Use it when one ward's rejection makes another's work redundant or misleading: there is no point authorizing payment on a negative total.

### \`when\` — conditional rules

\`\`\`python
class OrderContract(Contract):
    @ward(when=lambda data: data["kind"] == "physical")
    def needs_shipping_address(self, data):
        if not data.get("shipping_address"):
            self.reject("shipping_address", "Required for physical orders")
\`\`\`

The predicate receives the validated data. Moving the condition into metadata means the rule's applicability is inspectable rather than buried in the body.

**Edge case — a predicate that raises is treated as "does not apply."** The predicate is a routing decision, not a validation rule. A broken predicate must not manufacture a field error attributed to the ward it was gating, because that error would name the wrong field and the wrong cause.

### \`groups\` — per-operation rule sets

\`\`\`python
class UserContract(Contract):
    @ward(groups=("registration",))
    def password_strength(self, data):
        ...

    @ward(groups=("admin",))
    def role_assignable(self, data):
        ...

    @ward
    def email_wellformed(self, data):    # no groups — always runs
        ...
\`\`\`

Select groups per validation pass:

\`\`\`python
contract.is_sealed(groups="registration")
contract.is_sealed(groups=["registration", "admin"])
await contract.is_sealed_async(groups="checkout")
\`\`\`

**An ungrouped ward always runs.** It expresses an invariant that holds regardless of which group the caller asked for — an email must be well-formed whether or not this is a registration. Grouping an invariant would silently disable it for every pass that did not name its group.

Groups propagate to nested Contracts, so a group selected at the top level applies through the whole tree.

### \`Spec.fail_fast\`

\`\`\`python
class OrderContract(Contract):
    class Spec:
        fail_fast = True

    @ward
    def first(self, data): ...
    @ward
    def second(self, data): ...    # never runs if \`first\` rejected
\`\`\`

Stops at the first ward error instead of accumulating all of them. Default is \`False\`, unchanged — accumulating every error is the right default for a form, where a user should see all problems at once. \`fail_fast\` suits pipelines where a later rule's output would be noise once an earlier one has failed.

Applies to the ward phase only; structural field validation always accumulates.

---

## Frozen Contracts, equality, and copy

### \`Spec.frozen\`

\`\`\`python
class ConfigContract(Contract):
    port = IntFacet()

    class Spec:
        frozen = True

config = ConfigContract(data={"port": 8000})
config.is_sealed()
config.validated_data["port"] = 9000     # TypeError
\`\`\`

**Motivation:** \`is_sealed()\` returning \`True\` is a guarantee that the data satisfied every rule. That guarantee expires the moment a caller assigns to a field. Freezing makes the guarantee durable for the lifetime of the object.

### \`Contract.__eq__\`

\`\`\`python
a = UserContract(data={"name": "Ada"})
b = UserContract(data={"name": "Ada"})
a.is_sealed(); b.is_sealed()
a == b     # True
\`\`\`

Two Contracts are equal when they are the same class and carry the same validated data. Unvalidated Contracts compare on their raw input, so a comparison before sealing is still meaningful rather than degrading to identity.

**Contracts remain unhashable:**

\`\`\`python
hash(a)
# TypeError: UserContract is unhashable (its validated data is mutable)
\`\`\`

This is deliberate. Defining \`__eq__\` without \`__hash__\` would make Python set \`__hash__ = None\` silently; an explicit \`__hash__\` that raises names the reason instead. Validated data is mutable by default, so a hash computed at insertion time would go stale and the object would become unfindable in its own dict.

### \`copy(update=...)\`

\`\`\`python
updated = contract.copy(update={"name": "Grace"})
\`\`\`

Derives a new Contract with fields replaced. Keys absent from \`update\` carry over.

**Re-validates by default.** An override can violate a constraint the original satisfied, and skipping validation would produce a Contract whose \`validated_data\` never passed the rules it claims to enforce:

\`\`\`python
contract.copy(update={"age": -5})
# SealFault — the override is validated, not trusted
\`\`\`

Defer validation when building a payload in stages:

\`\`\`python
draft = contract.copy(update={"name": "Grace"}, validate=False)
final = draft.copy(update={"email": "g@example.com"})    # validates here
\`\`\`

For Contracts with async wards, use \`copy_async()\`:

\`\`\`python
updated = await contract.copy_async(update={"sku": "ABC"})
\`\`\`

\`copy()\` on a Contract with async wards raises \`ContractAsyncMismatchFault\` rather than silently skipping them.

---

## New facets

Four types previously fell through to a permissive \`TextFacet\` or had no facet at all.

### \`BytesFacet\`

Binary data over a JSON transport.

\`\`\`python
class UploadContract(Contract):
    payload = BytesFacet()                    # base64 (default)
    checksum = BytesFacet(encoding="hex")

UploadContract(data={"payload": "aGVsbG8=", "checksum": "68656c6c6f"})
# validated_data: {"payload": b"hello", "checksum": b"hello"}
\`\`\`

**Bug fixed:** \`bytes\` annotations previously mapped to \`TextFacet\`, whose cast whitelist *rejects real \`bytes\`*. A \`payload: bytes\` field rejected every genuine value while accepting plain strings — non-functional end to end. \`bytes\` annotations now route to \`BytesFacet\`.

Size constraints apply to the **decoded** length, which is what matters for storage and memory:

\`\`\`python
thumbnail = BytesFacet(max_length=64 * 1024)
\`\`\`

Always bound \`max_length\` on a client-facing binary field. Base64 expands roughly 33%, so a modest request body still decodes to a large allocation — an unbounded field is a memory-exhaustion vector.

JSON Schema emits \`{"type": "string", "format": "byte"}\`.

### \`PathFacet\`

Filesystem paths, validated as \`pathlib.PurePosixPath\`.

\`\`\`python
class UploadContract(Contract):
    destination = PathFacet()

UploadContract(data={"destination": "reports/q3.pdf"})
# validated_data: {"destination": PurePosixPath('reports/q3.pdf')}
\`\`\`

**Security defaults reject the two ways a client-supplied path escapes its root:**

| Input | Result | Why |
|---|---|---|
| \`/etc/passwd\` | \`Path must be relative\` | \`Path("/root") / "/etc/passwd"\` resolves to \`/etc/passwd\`, discarding the root |
| \`../../etc/passwd\` | \`Path may not contain '..' segments\` | Traversal out of the intended directory |
| \`a\\x00b\` | \`Path may not contain null bytes\` | Truncates at the OS layer, so a name passing an extension check can open a different file |

Null bytes are rejected unconditionally. The other two relax only for paths that never originate from a request:

\`\`\`python
destination = PathFacet(must_be_relative=False, allow_traversal=True)
\`\`\`

Windows separators are normalized before the \`..\` check, so a backslash cannot smuggle a segment past it on a POSIX server.

Values are \`PurePosixPath\` so a payload validates identically regardless of server platform. Convert with \`Path(value)\` at the point of filesystem access.

### \`SecretFacet\` and \`Secret\`

Sensitive strings that never appear in output or tracebacks.

\`\`\`python
class LoginContract(Contract):
    password = SecretFacet(min_length=8)

contract = LoginContract(data={"password": "hunter2hunter2"})
contract.is_sealed()

repr(contract.validated_data["password"])       # "Secret('**********')"
str(contract.validated_data["password"])        # "**********"
contract.validated_data["password"].reveal()    # "hunter2hunter2"
\`\`\`

\`write_only\` by default, so the field is accepted inbound and omitted from every serialized representation.

**Equality is constant-time** (\`hmac.compare_digest\`), so comparing a submitted value against a stored one does not leak the shared-prefix length through timing:

\`\`\`python
if contract.validated_data["password"] == stored_secret:   # constant-time
    ...
\`\`\`

**Security scope:** masking defends against *accidental* disclosure — log lines, exception reports, debug pages. It is not a substitute for hashing or encryption at rest. Call \`.reveal()\` only at the point of use.

JSON Schema emits \`{"type": "string", "format": "password", "writeOnly": true}\`.

### \`MACAddressFacet\`

\`\`\`python
class DeviceContract(Contract):
    mac = MACAddressFacet()
\`\`\`

Accepts colon, dash, and Cisco notations, normalizing to lowercase colon-separated form:

| Input | Validated value |
|---|---|
| \`AA:BB:CC:DD:EE:FF\` | \`aa:bb:cc:dd:ee:ff\` |
| \`aa-bb-cc-dd-ee-ff\` | \`aa:bb:cc:dd:ee:ff\` |
| \`aabb.ccdd.eeff\` | \`aa:bb:cc:dd:ee:ff\` |

Normalizing at validation means downstream comparisons and database lookups do not each reimplement it.

### Annotation routing

These types now resolve to the right facet from a plain annotation:

\`\`\`python
import ipaddress, pathlib
from aquilia.contracts.facets import Secret

class DeviceContract(Contract):
    address: ipaddress.IPv4Address    # IPFacet
    config_path: pathlib.Path         # PathFacet
    api_key: Secret                   # SecretFacet
\`\`\`

---

## \`IntFacet\` no longer truncates silently

### Previous behavior

\`\`\`python
class QuantityContract(Contract):
    qty = IntFacet()

QuantityContract(data={"qty": 3.9}).validated_data["qty"]   # 3   ← silently truncated
QuantityContract(data={"qty": "3.9"}).errors                # rejected
\`\`\`

The same logical input behaved differently depending on its wire type. A JSON body with \`3.9\` was accepted and quietly became \`3\`; the string \`"3.9"\` was correctly rejected.

### New behavior

\`\`\`python
QuantityContract(data={"qty": 3.9}).errors
# {"qty": ["Expected integer, got non-integer number 3.9"]}

QuantityContract(data={"qty": 3.0}).is_sealed()   # True — integral float still accepted
\`\`\`

\`NaN\` and \`Infinity\` are rejected explicitly.

**This is a behavioral change.** Payloads previously accepted with silent truncation now fail validation. Silent truncation of a quantity, a price in cents, or a page offset is a data-integrity bug that surfaces far from its cause.

---

## Alternate data sources

### \`Contract.from_env()\`

\`\`\`python
class SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()

settings = SettingsContract.from_env(prefix="APP_")
# reads APP_PORT and APP_DATABASE_URL
\`\`\`

Field names map to upper-case variable names. Absent variables are **omitted rather than set empty**, so each field's \`default\` and \`required\` rules decide the outcome exactly as they would for a JSON body.

Every value arrives as a string; normal facet casting turns \`"8000"\` into an \`int\`. Configuration therefore gets the same validation as request data instead of a parallel parsing path.

**Validates by default** — configuration errors should surface at startup, not at first use. Pass \`seal=False\` to defer.

### \`Contract.from_cli()\`

\`\`\`python
class ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)
    tags = ListFacet(child=TextFacet(), required=False)

options = ImportContract.from_cli(["--source", "data.csv", "--dry-run",
                                   "--tags", "a", "--tags", "b"])
# {"source": "data.csv", "dry_run": True, "tags": ["a", "b"]}
\`\`\`

Parses \`--flag value\`, \`--flag=value\`, and bare \`--flag\` (boolean). Dashes map to underscores, so \`--database-url\` fills \`database_url\`. A repeated flag collects into a list for a \`ListFacet\` to validate.

**Limitations, deliberately:** a small parser for feeding a Contract, not a replacement for the \`aq\` CLI's Click layer. Unknown flags are ignored so a Contract can read the subset of arguments it cares about from a larger command line. No short flags, no subcommands, no \`--\` terminator.

---

## Localized validation messages

Every built-in validation message now resolves through \`contract_message()\`:

\`\`\`python
from aquilia.contracts.messages import contract_message

contract_message("min_length", min=5)
# "Must be at least 5 characters"
\`\`\`

Resolution order:

1. The active i18n catalog's \`contracts.\` namespace, if an i18n service is bound to the request.
2. The built-in English default, with ICU-style \`{name}\` parameter substitution.

\`\`\`yaml
# locales/fr/messages.yaml
contracts:
  required: "Ce champ est obligatoire"
  min_length: "Doit contenir au moins {min} caractères"
\`\`\`

The service and locale are read from \`contextvars\`, so a request's locale applies to validation errors raised anywhere in its call tree without threading a locale parameter through every facet.

**Applications without i18n configured see byte-identical messages** to v1.3.4.

**Resolution never raises.** A missing key, a malformed template, or a broken i18n service falls back to the built-in text. Failing to render the message for a rejected payload would turn a 422 into a 500 — the client would lose the validation errors entirely because of a translation problem.

33 message keys ship: field presence, type, length, numeric range, collection size, choice, format (email/URL/slug/IP/MAC/UUID), and path safety.

---

## Related pages

- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — the nested-pipeline and async serialization fixes
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — \`aq contracts stubs\`, \`seal_*\` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
`,
    "distributed_tasks.md": `# Distributed & Persistent Task Backends — Aquilia v1.3.5

Background tasks now run across multiple worker processes and multiple machines, with job state that survives a restart. Before this release the only backend was \`MemoryBackend\`: jobs lived in the worker process and were lost on restart, and \`backend="redis"\` logged a warning and silently fell back to in-memory.

---

## Motivation

The task system was single-process. That is fine for a cron-like cleanup job, but it fails the moment an application scales horizontally:

- Two web workers each ran their own queue, so a periodic task fired twice.
- A deploy dropped every queued job on the floor.
- A worker crash lost whatever that worker was executing, permanently.
- \`Integration.tasks(backend="redis")\` was accepted by config validation and then ignored at runtime.

---

## Design Goals

1. **Backend choice is configuration, not code.** Task functions, decorators, and \`enqueue()\` calls are identical on every backend.
2. **No lost work on crash.** A worker that dies mid-job must have that job picked up by a peer.
3. **Fail at enqueue, not on a remote worker.** Anything that cannot cross a process boundary must be rejected at the call site, where the stack trace is useful.
4. **Existing single-process apps unaffected.** \`memory\` stays the default and behaves exactly as before.

---

## Architecture

### Job serialization

A job that crosses a process boundary cannot carry a live Python callable or arbitrary objects. Two new methods on \`Job\` define the transport form:

\`\`\`python
payload = job.to_payload()      # JSON-compatible dict
restored = Job.from_payload(payload)
\`\`\`

\`to_payload()\` validates \`args\` and \`kwargs\` against \`json.dumps\` and raises \`TaskSerializationFault\` if they cannot be represented. \`from_payload()\` deliberately leaves the callable unset — the worker resolves it from \`func_ref\` through the \`@task\` registry, so a queue entry can never name a function the application did not register.

\`Job.to_dict()\` is unchanged and remains the human-facing view used by the admin dashboard.

### Lease-based claiming

Both durable backends use the same coordination model:

1. A worker claims a job and takes a lease for \`lease_seconds\` (default \`300.0\`).
2. While executing, it renews the lease every \`heartbeat_interval\` seconds (default \`30.0\`).
3. A background reclaim loop sweeps every \`reclaim_interval\` seconds (default \`60.0\`) and returns jobs whose lease lapsed to the runnable pool.

If a worker is killed, its lease expires and a peer reclaims the job instead of the job being lost.

**This is at-least-once delivery.** A worker that stalls past its lease — a long GC pause, a blocked event loop — can have its job reclaimed and executed a second time. Task functions should be idempotent.

### \`RedisBackend\`

Multi-process and multi-machine, backed by Redis. Claims are atomic through a Lua script against a sorted set; fingerprint reservation uses \`SET NX\`. Fastest option, and the right default for high throughput.

### \`SQLBackend\`

Durable state on the database the application already uses — no new infrastructure. Works on SQLite, PostgreSQL, MySQL, and Oracle through Aquilia's existing parameterized query layer.

A claim is a conditional \`UPDATE ... WHERE id = ? AND state = ?\` inside a transaction; \`rowcount == 0\` means another worker won the race, so the loser moves on rather than double-running the job. This works on every supported dialect without needing \`SELECT ... FOR UPDATE SKIP LOCKED\`, which SQLite does not have.

Two tables are created on first \`initialize()\`:

\`\`\`
aquilia_tasks(
    id TEXT PRIMARY KEY, queue TEXT, priority INTEGER, state TEXT,
    func_ref TEXT, payload TEXT,             -- full JSON job
    available_at TEXT,                        -- when it may run
    lease_expires_at TEXT, owner TEXT,        -- distributed claim
    dedup_key TEXT, workflow_id TEXT,
    created_at TEXT, completed_at TEXT, sequence INTEGER
)
aquilia_task_locks(fingerprint TEXT PRIMARY KEY, job_id TEXT, expires_at TEXT)
\`\`\`

The unique primary key on \`aquilia_task_locks.fingerprint\` is what makes deduplication correct under concurrency: two workers racing to reserve the same fingerprint both attempt an \`INSERT\`, and the database rejects exactly one.

Redis is faster and scales further. SQL wins when you cannot add a Redis dependency, or when you want jobs to commit in the *same transaction* as the business data that created them, so a rolled-back request cannot leave an orphaned job behind. Above roughly a few hundred jobs/second, prefer Redis.

---

## Configuration

\`\`\`python
# workspace.py

# Development — single process, non-durable (default, unchanged)
Integration.tasks(num_workers=4)

# Production — distributed workers, durable queue
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    redis_prefix="aquilia:tasks:",
    num_workers=16,
    lease_seconds=120,
    heartbeat_interval=30,
    reclaim_interval=60,
)

# Durable without extra infrastructure
Integration.tasks(backend="sql", sql_table="aquilia_tasks")
\`\`\`

### New options

| Option | Default | Purpose |
|---|---|---|
| \`backend\` | \`"memory"\` | \`"memory"\`, \`"redis"\`, or \`"sql"\` (aliases: \`"database"\`, \`"db"\`) |
| \`redis_url\` | \`None\` | Redis connection URL; falls back to \`$REDIS_URL\` |
| \`redis_prefix\` | \`"aquilia:tasks:"\` | Key namespace, so several apps can share one Redis |
| \`sql_table\` | \`"aquilia_tasks"\` | Job table name for the SQL backend |
| \`lease_seconds\` | \`300.0\` | How long a claimed job stays owned before a peer may reclaim it |
| \`heartbeat_interval\` | \`30.0\` | Lease renewal cadence; must be well under \`lease_seconds\` |
| \`reclaim_interval\` | \`60.0\` | How often to sweep for jobs abandoned by crashed workers |
| \`dedup_ttl\` | \`3600.0\` | How long a deduplication reservation is held |
| \`worker_id\` | \`None\` | Worker identity recorded as a job's owner; defaults to \`hostname:pid:random\` |

Install the Redis extra with \`pip install aquilia[redis]\`. The SQL backend requires \`Integration.database(...)\` and no extra dependency.

---

## Usage

Task code does not change between backends:

\`\`\`python
from aquilia.tasks import task

@task(queue="reports", max_retries=3)
async def rebuild_report(report_id: int) -> dict:
    return {"rebuilt": report_id}
\`\`\`

\`\`\`python
job_id = await tasks.enqueue(rebuild_report, 42)
job = await tasks.get_job(job_id)
\`\`\`

### Running a dedicated worker process

A process that only consumes work is a normal Aquilia app with \`num_workers\` set and no enqueueing of its own. The queues it polls are derived from the \`@task\` descriptors it has imported, plus any queue it discovers on the shared backend — so a worker does not need to know in advance which queues its producers use.

---

## Edge Cases

**Non-serializable arguments.** On a persistent backend, passing an object JSON cannot represent raises \`TaskSerializationFault\` at \`enqueue()\`:

\`\`\`python
await tasks.enqueue(process, open("f.txt"))   # TaskSerializationFault
\`\`\`

This is deliberate. The alternative is a job that enqueues cleanly and then fails unrecoverably on a remote worker, far from the call site. On \`MemoryBackend\` live objects still work, because the job never leaves the process.

**Unregistered task names.** A worker resolves \`func_ref\` through the \`@task\` registry. If the consumer process has not imported the module that registers the task, the job raises \`TaskResolutionFault\` rather than executing arbitrary named code. Ensure every worker imports the same task modules.

**Backend unavailable at startup.** A Redis or database that cannot be reached logs an error naming the durability that was lost and falls back to \`MemoryBackend\`, rather than aborting startup. The application still serves requests; queued jobs are not durable until the backend recovers and the process restarts.

**Unknown backend name.** A typo such as \`backend="rabbitmq"\` logs a warning listing the valid values and uses \`MemoryBackend\`. A typo does not take production down.

**Clock skew across machines.** Leases are stored as absolute timestamps. Significant clock skew between workers can cause premature reclaim (duplicate execution) or delayed reclaim. Run NTP.

---

## Performance Implications

- \`MemoryBackend\` is unchanged; single-process applications see no difference.
- \`RedisBackend\` claim is one round trip against an in-memory sorted set.
- \`SQLBackend\` claim is one \`UPDATE\` inside a transaction. Throughput is bounded by database write capacity; above a few hundred jobs/second prefer Redis.
- The reclaim loop runs once per \`reclaim_interval\` per process and issues one sweep query. Raising \`reclaim_interval\` reduces load; lowering it shortens the window during which a crashed worker's job sits idle.

---

## Compatibility

Fully backward compatible. \`memory\` remains the default, \`MemoryBackend\` behavior is unchanged, and every existing \`@task\` and \`enqueue()\` call works untouched. The new configuration options are additive with defaults matching prior behavior.

---

## Related

- [Workflows & DAGs](workflows.md) — composing jobs, which requires a shared backend to span processes
- [Idempotency & Deduplication](idempotency.md) — the distributed lock built on this coordination layer
- [Mail Delivery Queue](mail_queue.md) — the first framework subsystem to run on it
- [Migration Guide](migration.md)
`,
    "http_native.md": `# Native HTTP Client & Third-Party HTTP Removal — Aquilia v1.3.5

In Aquilia v1.3.5, all remaining traces of third-party HTTP clients (specifically \`httpx\`) have been completely removed from the framework codebase, dependencies, test suite, and documentation in favor of Aquilia's native zero-dependency \`aquilia.http\` client.

---

## 1. Overview & Motivation

Aquilia features a production-grade, fully asynchronous HTTP client implementation in \`aquilia.http\` built directly on Python standard library primitives (\`asyncio\`, \`ssl\`, \`gzip\`, \`zlib\`).

Previously, optional subsystems like \`SendGridProvider\` and test helpers like \`LiveServerTestCase\` relied on \`httpx\` as a third-party dependency. In v1.3.5:

1. **SendGrid Mail Provider** (\`aquilia.mail.providers.sendgrid.SendGridProvider\`) uses native \`aquilia.http.AsyncHTTPClient\`.
2. **\`LiveServerTestCase\`** (\`aquilia.testing.cases.LiveServerTestCase\`) documentation and usage examples use native \`aquilia.http.AsyncHTTPClient\`.
3. **Dependency Clean-Up**: \`httpx\` has been removed from \`pyproject.toml\`, \`setup.py\`, \`aquilia.egg-info\`, and all extra dependency bundles (\`mail-sendgrid\`, \`testing\`, \`dev\`).

---

## 2. Changes in SendGrid Provider

The \`SendGridProvider\` now initializes \`AsyncHTTPClient\` directly from \`aquilia.http\`:

\`\`\`python
from aquilia.http import AsyncHTTPClient

class SendGridProvider:
    async def initialize(self) -> None:
        self._client = AsyncHTTPClient(
            base_url=self.api_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aquilia-mail/1.0",
            },
            timeout=self.timeout,
        )
\`\`\`

Error handling consumes the async \`HTTPClientResponse\` API:

\`\`\`python
body = await response.json()
\`\`\`

---

## 3. Backward Compatibility & \`aclose\` Alias

To ensure smooth transition for any external callers expecting \`aclose()\`, \`aquilia.http.AsyncHTTPClient\` now provides an alias:

\`\`\`python
class AsyncHTTPClient:
    async def close(self) -> None: ...

    aclose = close
\`\`\`

Both \`await client.close()\` and \`await client.aclose()\` work seamlessly.

---

## 4. Dependencies Updated

- \`mail-sendgrid\` extra: no longer installs \`httpx\`.
- \`testing\` extra: no longer installs \`httpx\`.
- \`dev\` extra: no longer installs \`httpx\`.
`,
    "idempotency.md": `# Idempotency & Distributed Deduplication — Aquilia v1.3.5

\`Job.fingerprint\` existed since the task system shipped but nothing ever read it. As of v1.3.5 it is enforced at enqueue time, and on durable backends that enforcement is a real distributed lock: two processes racing to queue the same work produce one job, not two.

---

## Motivation

The classic double-send. A user double-clicks, a retried HTTP request replays, a webhook is delivered twice, two web workers react to the same event — and the same background job is queued twice. Applications worked around this with their own Redis \`SETNX\` guards or a \`processed\` table, reimplementing per project what the framework already had the raw material for.

\`Job.fingerprint\` was computed and stored. It simply had no readers.

---

## How It Works

### The fingerprint

A stable digest over \`func_ref\`, \`queue\`, \`args\`, and \`kwargs\` — two enqueue calls that would do identical work share a fingerprint:

\`\`\`python
job.fingerprint    # 12-hex-character digest
\`\`\`

It is computed from the JSON form when possible, so equal-but-not-identical values agree across processes: a tuple \`(1, 2)\` and a list \`[1, 2]\` produce the same fingerprint. Non-JSON values fall back to \`repr\`, which keeps the in-memory backend working with live objects.

### The \`dedup\` parameter

\`\`\`python
await manager.enqueue(rebuild_index, dedup="allow")   # default — always enqueue
await manager.enqueue(rebuild_index, dedup="skip")    # return the in-flight job's ID
await manager.enqueue(rebuild_index, dedup="raise")   # raise TaskDuplicateFault
\`\`\`

| Mode | Behavior |
|---|---|
| \`"allow"\` | Always enqueue. Preserves historical behavior, so existing code is unaffected. |
| \`"skip"\` | If identical work is already in flight, return that job's ID instead of enqueueing a second copy. |
| \`"raise"\` | Raise \`TaskDuplicateFault\` instead. Use when a duplicate indicates a caller bug. |

A reservation is held for \`dedup_ttl\` seconds (default \`3600.0\`) and released when the job reaches a terminal state.

### Distributed enforcement

The backend owns the reservation, so correctness under concurrency comes from the storage layer, not from application-level check-then-act:

- **\`RedisBackend\`** — \`SET NX\` on the fingerprint key. Exactly one caller wins.
- **\`SQLBackend\`** — \`INSERT\` into \`aquilia_task_locks\`, whose \`fingerprint\` column is the primary key. Two workers racing both attempt the insert and the database rejects exactly one.
- **\`MemoryBackend\`** — an in-process map, correct within a single process.

---

## Examples

### Collapsing a burst

\`\`\`python
# Ten requests arrive; one job runs.
job_id = await tasks.enqueue(rebuild_search_index, dedup="skip")
\`\`\`

### Treating a duplicate as an error

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

### Across processes

\`\`\`python
# Web worker A and web worker B, sharing one Redis or SQL backend
a = await tasks.enqueue(send_invoice, order_id, dedup="skip")
b = await tasks.enqueue(send_invoice, order_id, dedup="skip")
assert a == b   # one job
\`\`\`

---

## Before vs After

\`\`\`python
# Before v1.3.5 — hand-rolled guard in every application
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

\`\`\`python
# v1.3.5
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version is also correct in a case the hand-rolled one usually is not: the reservation is released when the job reaches a terminal state, so a failed job can be retried immediately instead of being blocked until the TTL expires.

---

## Edge Cases

**Deduplication suppresses duplicate *enqueues*, not duplicate *execution*.** Distributed backends are at-least-once: a job whose worker stalls past its lease may be reclaimed and run twice. Task functions should still be idempotent. These are two different guarantees and \`dedup\` provides only the first.

**Fingerprints include the queue.** The same function with the same arguments on two different queues is two different fingerprints, and both will be enqueued.

**Argument order matters for positional arguments.** \`f(1, 2)\` and \`f(2, 1)\` are distinct. Keyword arguments are sorted, so \`f(a=1, b=2)\` and \`f(b=2, a=1)\` match.

**Non-JSON arguments still deduplicate in-process.** The \`repr\` fallback means two live objects deduplicate only if their \`repr\` matches. On a persistent backend such arguments raise \`TaskSerializationFault\` before dedup is reached.

**The default is unchanged.** Existing code that never passes \`dedup\` continues to enqueue every call. This is deliberate — silently collapsing jobs in an existing application would be a breaking behavioral change.

---

## Performance Implications

\`dedup="allow"\` (the default) adds no work: no fingerprint reservation is attempted. \`"skip"\` and \`"raise"\` add one reservation operation per enqueue — a single \`SET NX\` on Redis, a single \`INSERT\` on SQL. In exchange, collapsed duplicates avoid an entire job execution.

---

## Compatibility

Fully backward compatible. \`dedup\` is a new keyword-only parameter defaulting to \`"allow"\`, which is exactly the prior behavior. \`TaskDuplicateFault\` is a new fault raised only when explicitly requested via \`dedup="raise"\`.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — the coordination layer this builds on
- [Workflows & DAGs](workflows.md)
- [Migration Guide](migration.md)
`,
    "mail_queue.md": `# Mail Delivery Queue — Aquilia v1.3.5

Outbound mail can now be delivered by background workers instead of inside the request handler. \`send_message()\` persists an envelope, schedules a delivery job, and returns — the SMTP conversation happens on a worker, with retries, backoff, and delayed sends managed by the task scheduler.

This reuses Aquilia's existing task system. No second queue implementation was introduced.

---

## Motivation

Sending mail inside a request handler ties the response time of a user-facing endpoint to a third party's SMTP latency. A slow provider makes signup slow; an unreachable provider makes signup fail. Retrying meant either blocking the request further or losing the message.

---

## Design Goals

1. **Reuse the scheduler.** Retries, delayed delivery, persistence, and worker execution are the task system's job, not mail's.
2. **Same API whether queued or not.** Enabling the queue is a configuration change; call sites are unchanged.
3. **Survive the jump to distributed workers with no API change.** The delivery job had to be designed for a persistent backend from day one.
4. **Never accept mail that cannot be sent.** Recording an envelope as queued when nothing can deliver it is worse than sending inline.

---

## Architecture

\`\`\`
send_message()
  │
  ├─ build envelope (validate, apply suppression, dedupe)
  ├─ EnvelopeStore.save(envelope)          ← durable record
  └─ enqueue "aquilia.mail.deliver"(envelope_id)
                    │
                    ▼
             task worker (possibly another process)
                    │
                    ├─ EnvelopeStore.get(envelope_id)
                    ├─ provider.send(...)  → SENT
                    └─ on failure → schedule retry with backoff
\`\`\`

### \`EnvelopeStore\`

The durable record of accepted mail. Two implementations ship:

| Class | Durability |
|---|---|
| \`MemoryEnvelopeStore\` | In-process, bounded (\`max_envelopes\`, default 10,000). Default. |
| \`SQLEnvelopeStore\` | Application database, table \`aquilia_mail_envelopes\`. |

The interface covers \`save\`, \`get\`, \`list_by_status\`, \`find_by_digest\`, \`find_by_idempotency_key\`, \`cleanup\`, and \`stats\`.

### The delivery task

Delivery is a registered task named \`aquilia.mail.deliver\`, on queue \`mail\`.

**It takes an envelope ID, not an envelope.** A live \`MailEnvelope\` cannot survive a persistent or distributed backend, which serializes jobs as JSON. The worker — which may be in another process entirely — reloads the envelope from the shared store. This is what lets mail delivery run on another machine without any API change.

It is registered under a stable name rather than enqueued as a bare callable, so a worker in another process resolves it through the \`@task\` registry; a module-path reference would not survive a rename.

Mail owns its own retry policy, so the job is enqueued with \`max_retries=0\` and the mail service schedules its own follow-up attempts with backoff.

---

## Configuration

\`\`\`python
# workspace.py

# Inline delivery (default, unchanged)
Integration.mail(default_from="noreply@example.com", providers=[...])

# Background delivery
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
)

# Background delivery with durable envelopes and suppression
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`queue_enabled\` | \`False\` | Deliver via background tasks instead of inside the request |
| \`queue_persistent\` | \`False\` | Keep envelopes and suppression records in the application database |
| \`queue_dedupe_window_seconds\` | \`3600\` | Window in which an identical send is collapsed rather than sent twice |
| \`queue_retention_days\` | \`30\` | How long delivered envelopes are retained |

For an end-to-end durable path, pair \`queue_persistent=True\` with a durable task backend:

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")
Integration.mail(queue_enabled=True, queue_persistent=True, ...)
\`\`\`

\`queue_persistent=True\` requires \`Integration.database(...)\`.

---

## Usage

Call sites are identical whether the queue is on or off:

\`\`\`python
from aquilia.mail import EmailMessage

envelope_id = await EmailMessage(
    subject="Welcome",
    body="Thanks for signing up",
    to=user.email,
).asend()
\`\`\`

With the queue enabled, \`asend()\` returns as soon as the envelope is stored — typically sub-millisecond — and delivery completes on a worker. The returned envelope ID is the handle for checking status:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status      # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
envelope.attempts
\`\`\`

---

## Send-Time Deduplication

Independent of the task system's job-level deduplication, mail collapses duplicate *sends*:

- An explicit \`idempotency_key\` on the message matches first.
- Otherwise a content digest matches within \`queue_dedupe_window_seconds\`.

This guards the classic double-send: a retried request or a double-clicked button producing two identical emails.

---

## Edge Cases

**No task manager, queue enabled.** Delivery falls back to inline sending. Recording an envelope as queued when nothing can deliver it would silently drop mail. The fallback also applies when a manager exists but has not been started — enqueueing into a stopped manager would park the message forever.

**Persistent stores with no database.** If \`queue_persistent=True\` but the database is unavailable, mail logs an error naming the durability that was lost and falls back to in-memory stores rather than aborting startup.

**Every recipient suppressed.** The envelope is marked \`CANCELLED\` and no delivery job is scheduled. See [Bounce Handling & Suppression](bounces_suppression.md).

**Missing envelope at delivery time.** A delivery job whose envelope has been cleaned up or cancelled logs a warning and is treated as success rather than retried forever — no amount of retrying will bring it back.

**Attachments.** Attachment payloads live in envelope metadata as blobs keyed by digest, so an envelope reloaded on another worker still carries its attachments.

---

## Performance Implications

Request-path cost drops from a full SMTP conversation (tens to hundreds of milliseconds, or a provider timeout on failure) to one store write plus one enqueue. Throughput of actual delivery becomes a function of worker count and provider rate limits rather than request concurrency.

\`MemoryEnvelopeStore\` evicts oldest-first past \`max_envelopes\`; an evicted envelope's delivery job will find nothing and give up. Use \`queue_persistent=True\` for any deployment where that matters.

---

## Compatibility

Fully backward compatible. \`queue_enabled\` defaults to \`False\`, so mail continues to send inline exactly as before unless explicitly enabled. \`EmailMessage\`, \`send_message()\`, and \`asend()\` signatures are unchanged. \`MailService.store\` and \`MailService.suppression\` are new attributes; passing explicit \`store=\` / \`suppression=\` to the constructor still overrides configuration.

---

## Related

- [Bounce Handling & Suppression](bounces_suppression.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "mail_security.md": `# Mail Security, MIME & Templates — Aquilia v1.3.5

The mail subsystem's message construction, signing, logging, and templating were consolidated and hardened. MIME assembly now lives in one place shared by every provider, DKIM signing is real, log output redacts personal data on request, and the ATS template engine gained a documented filter set with autoescaping on by default.

---

## Shared MIME Assembly

Every provider previously built its own MIME message, which meant header handling, attachment encoding, and multipart structure drifted between SMTP, SES, SendGrid, and the file/console backends. \`aquilia/mail/mime.py\` is now the single implementation:

\`\`\`python
from aquilia.mail import build_mime_message, message_to_bytes, sign_dkim

build_mime_message(envelope, *, extra_headers=None)   # -> MIMEMultipart
message_to_bytes(msg, security=None)                  # -> bytes, DKIM-signed if configured
sign_dkim(raw_message, security)                      # -> bytes
\`\`\`

\`build_mime_message()\` produces a \`multipart/mixed\` message with a generated \`Message-ID\` and Aquilia tracking headers — \`X-Aquilia-Envelope-ID\`, plus trace and tenant IDs when set. Attachment payloads are read from envelope metadata, so an envelope reloaded on another worker still carries its attachments. The \`extra_headers\` argument is merged last, letting a provider add its own header (an ESP configuration set, for example) without forking the builder.

\`extract_domain(email)\` is also exported, used for per-domain rate limiting and DKIM domain defaulting.

### Why it matters

Bugs fixed in one provider now apply to all of them, and the \`X-Aquilia-Envelope-ID\` header is emitted consistently — which is what lets provider webhooks correlate a bounce back to the exact envelope. See [Bounce Handling & Suppression](bounces_suppression.md).

---

## DKIM Signing

DKIM signing is applied at the byte level, immediately before transmission, so the signature covers exactly what the provider receives.

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    dkim_enabled=True,
    dkim_domain="example.com",
    dkim_selector="aquilia",
)
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`dkim_enabled\` | \`False\` | Sign outbound mail |
| \`dkim_domain\` | \`None\` | Signing domain (\`d=\`). Required when enabled |
| \`dkim_selector\` | \`"aquilia"\` | Selector (\`s=\`); must match your DNS TXT record |
| \`dkim_private_key_path\` | \`None\` | Path to the PEM private key |
| \`dkim_private_key_env\` | \`"AQUILIA_DKIM_PRIVATE_KEY"\` | Environment variable holding the PEM key |

Signing requires the \`dkimpy\` package:

\`\`\`bash
pip install aquilia[mail-dkim]
\`\`\`

**DKIM failures raise at send time rather than shipping an unsigned message.** Silently sending unsigned mail would defeat the purpose — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or an error.

Because that failure is at send time, \`aq mail check\` now validates the configuration up front:

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

---

## TLS Enforcement

\`require_tls\` defaults to \`True\`. SMTP delivery negotiates STARTTLS and aborts rather than transmitting credentials or message content in cleartext. Disable only for a local development relay.

---

## XOAUTH2 Authentication

\`MailAuth.oauth2()\` supports SMTP providers that require bearer tokens (Gmail, Microsoft 365):

\`\`\`python
Integration.mail(
    auth=MailAuth.oauth2(
        client_id="...",
        client_secret_env="MAIL_OAUTH_SECRET",
        access_token_env="MAIL_OAUTH_TOKEN",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://mail.google.com/",
    ),
    providers=[...],
)
\`\`\`

Aquilia does not perform the token exchange. Supply a currently valid token — literally or through \`access_token_env\` — from whatever component owns the refresh cycle. \`token_url\`, \`scope\`, and \`refresh_token\` are recorded for that component's use. The token is presented to SMTP via the XOAUTH2 mechanism.

---

## PII Redaction in Logs

Mail logs contain recipient addresses by nature. \`pii_redaction\` masks them:

\`\`\`python
Integration.mail(pii_redaction=True, ...)
\`\`\`

\`\`\`python
from aquilia.mail import redact_email, redact_pii

redact_email("alice@example.com")               # "a***e@example.com"
redact_pii("contact alice@example.com", enabled=True)
\`\`\`

Local parts are masked while the domain is preserved, so logs remain useful for diagnosing a domain-wide delivery problem without recording individual identities. Off by default — enabling it reduces debuggability, which should be a deliberate choice.

---

## ATS Templates

The mail template engine (\`<< expression >>\` syntax, distinct from the Jinja engine used for HTML views) gained a documented public API and filter set.

\`\`\`python
from aquilia.mail.template import configure, register_filter, render_string, render_template, FILTERS

configure(template_dirs=["mail_templates"])
render_string(template_text, context, *, autoescape=True)
render_template(template_name, context, *, template_dirs=None, autoescape=None)
register_filter(name, fn)
\`\`\`

### Autoescaping

**Interpolated values are HTML-escaped by default.** A username containing \`<script>\` cannot inject markup into an HTML mail body.

\`\`\`python
render_string("<p><< name >></p>", {"name": "<script>alert(1)</script>"})
# '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
\`\`\`

Two escape hatches:

- The \`safe\` filter, for a value that is known-good markup: \`<< body|safe >>\`
- \`autoescape=False\`, for plain-text bodies and subject headers, where escaping would corrupt output (\`&amp;\` in a subject line)

Subject rendering uses \`autoescape=False\` internally for exactly this reason.

### Built-in filters

\`currency\`, \`default\`, \`escape\`, \`join\`, \`length\`, \`lower\`, \`safe\`, \`title\`, \`trim\`, \`truncate\`, \`upper\`.

\`\`\`
<< total|currency("EUR") >>        →  EUR 12.50
<< blurb|truncate(5) >>            →  abcde…
<< tags|join(", ") >>
<< nickname|default("friend") >>
<< name|trim|title >>
\`\`\`

Filters compose left to right. Arguments must be literals — no expressions — so a template cannot execute arbitrary code.

Register your own:

\`\`\`python
register_filter("shout", lambda v: f"{v}!!!")
\`\`\`

### Control flow is rejected, loudly

Jinja-style control tags (\`[[% if %]]\`, \`[[% for %]]\`) are **not** supported and raise \`MailTemplateFault\` rather than being passed through. Shipping a raw \`[[% if %]]\` token to a recipient's inbox is worse than failing the render. Build conditional content in Python and pass the result in the context.

### Error behavior

- Unknown filter, malformed filter arguments, or a control-flow tag → \`MailTemplateFault\`
- A missing context variable renders as empty rather than raising, so an optional field does not break a send
- Dotted lookups work against dicts and objects: \`<< user.name >>\`

---

## Provider Changes

All providers now build messages through the shared MIME layer:

- **SMTP** — restructured around shared MIME assembly, byte-level DKIM signing, STARTTLS enforcement, and XOAUTH2 authentication.
- **SES** — sends the fully assembled raw message, preserving custom headers and the DKIM signature.
- **SendGrid** — consistent header handling and attachment encoding.
- **Console / File** — render the same MIME structure as production providers, so what you inspect in development matches what ships.

---

## Compatibility

Backward compatible. \`require_tls\` already defaulted to \`True\`. DKIM, PII redaction, and OAuth2 are opt-in. Template rendering already autoescaped; this release documents the behavior and the filter set rather than changing it. Provider configuration and \`EmailMessage\` signatures are unchanged.

The one behavior worth calling out: with \`dkim_enabled=True\` and a broken configuration, sends now **fail** instead of shipping unsigned mail. Run \`aq mail check\` after enabling DKIM.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [CLI Changes](cli.md)
- [Migration Guide](migration.md)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.5

Aquilia v1.3.5 is a feature release with **no API removals or signature changes**. Every workspace, manifest, task, and mail configuration from 1.3.4 continues to work without modification.

The tasks, mail, and HTTP work is fully backward compatible. The **Contracts audit ships four behavioral corrections** — each replacing behavior that was incorrect — which require a review pass if your application uses nested Contracts, to-many Lenses, or integer fields fed by JSON. Those are covered first, since they are the only part of this release that can change how existing code behaves.

---

## Upgrading

\`\`\`bash
pip install aquilia==1.3.5
\`\`\`

Optional extras for the new capabilities:

\`\`\`bash
pip install aquilia[redis]        # distributed task backend
pip install aquilia[mail-dkim]    # DKIM signing for outbound mail
\`\`\`

For tasks and mail, nothing else is required. If you change no configuration, those subsystems behave exactly as in v1.3.4:

- Tasks run on \`MemoryBackend\`, single process.
- Mail sends inline, inside the request.
- No addresses are suppressed.
- No deduplication is applied.

Contracts require a review pass — see [Migration 0](#migration-0--contracts-behavioral-review) below.

---

## Upgrade Checklist

1. \`pip install aquilia==1.3.5\`
2. **Review Contract behavioral changes — see [Migration 0](#migration-0--contracts-behavioral-review).**
3. Run your test suite. Expect failures only where a nested Contract rule was previously inert, or a to-many Lens was serialized without prefetching.
4. *(Optional)* Generate Contract type stubs: \`aq contracts stubs myapp.contracts\`.
5. *(Optional)* Migrate \`seal_*\` validators to \`@ward\` — see [Migration 7](#migration-7--seal_-validators-to-ward).
6. *(Optional)* Move tasks to a durable backend — see below.
7. *(Optional)* Enable background mail delivery — see below.
8. *(Optional)* Wire provider webhooks for bounce handling.
9. If you use SendGrid or testing helpers, note that third-party \`httpx\` is no longer required as Aquilia uses native \`aquilia.http\`.
10. If you use DKIM, run \`aq mail check\` and install \`aquilia[mail-dkim]\`.
11. Remove any hand-rolled job deduplication in favour of \`dedup="skip"\`.
12. Remove any workaround that parsed \`repr\`-form job results.

---

## Migration 0 — Contracts Behavioral Review

**Required if your application uses Contracts.** Four corrections can change whether an existing payload is accepted.

### 0.1 — Nested Contract rules are now enforced

**What changed.** A nested Contract was validated structurally only. Every \`@ward\` method and every \`validate()\` override declared on a nested Contract was silently skipped. They now run.

**Why.** \`Sigil.validate()\` recursed into the child's compiled schema rather than instantiating the child Contract, so the ward phase was never reached. A nested Contract expressing an authorization check enforced nothing.

**How to check.** Find nested Contracts that declare rules:

\`\`\`bash
# Contracts referenced by another Contract's field, that declare a ward
grep -rn "@ward\\|def validate(self" --include="*.py" myapp/
\`\`\`

For each, confirm the rule is one you actually want enforced. A rule written years ago against an assumption that no longer holds will now start rejecting live traffic.

\`\`\`python
class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

# v1.3.4: True  (the ward never ran)
# v1.3.5: False, errors = {"items": {"0": {"qty": ["Must be at least 1"]}}}
Order(data={"items": [{"qty": 0}]}).is_sealed()
\`\`\`

**Also affected: async wards.** A Contract whose *nested* child declares \`@ward(mode="async")\` now correctly reports \`has_async_wards is True\`, so calling \`is_sealed()\` raises \`ContractAsyncMismatchFault\` instead of skipping the ward. Switch those call sites to \`is_sealed_async()\`.

Details: [Nested Validation Pipeline](contracts_pipeline.md).

### 0.2 — \`Lens(many=True)\` raises on an unresolved relation

**What changed.** An un-awaited related manager produced an empty list. It now raises \`LensUnresolvedFault\` (\`BP503\`).

**Why.** \`[]\` is indistinguishable from "this record genuinely has no related rows", so the previous behavior shipped wrong data to clients with no signal.

**How to fix.** Three options:

\`\`\`python
# 1. Prefetch — best for hot paths
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the new async serializer, which awaits for you
await OrderContract.to_dict_async(order)
\`\`\`

### 0.3 — Malformed-body error shape changed

**What changed.** A scalar or list request body previously produced a "This field is required" error per field. It now produces one document-level error.

\`\`\`python
# v1.3.4
UserContract(data="not an object").errors
# {"name": ["This field is required"], "email": ["This field is required"]}

# v1.3.5
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

**Who is affected.** Clients that parse a 422 response body and assume every key is a field name. Treat \`__all__\` as a document-level error and render it separately from field errors.

### 0.4 — \`IntFacet\` rejects fractional input

**What changed.** \`3.9\` was silently truncated to \`3\`. It is now rejected. \`3.0\` is still accepted.

**Why.** \`int(3.9)\` returned \`3\` while the string \`"3.9"\` was correctly rejected — the same logical input behaved differently depending on wire type. Silent truncation of a quantity or a price in cents is a data-integrity bug that surfaces far from its cause.

**How to fix.** If a client legitimately sends fractional values you intend to round, do it explicitly before validation, or use \`FloatFacet\`/\`DecimalFacet\` and round in your handler.

### 0.5 — \`"__minimal__"\` projections return fewer fields

**What changed.** \`"__minimal__"\` stored an empty placeholder that no code resolved. Because an empty set is falsy, the per-field filter passed *every* field. It now resolves to primary-key facets plus every \`read_only\` facet.

**Who is affected.** Anyone using \`"__minimal__"\`. The previous output — all fields, including ones deliberately kept private — was never correct. Verify the new field set matches what the projection was meant to expose.

---

## Migration 7 — \`seal_*\` Validators to \`@ward\`

**Optional in 1.x. Required before 2.0.0.**

Methods named \`seal_*\` or \`async_seal_*\` still register as validators and still run, but now emit a \`DeprecationWarning\`.

### Find every affected method

\`\`\`bash
python -W error::DeprecationWarning -c "import myapp.contracts"
\`\`\`

Or fail the test suite on it:

\`\`\`toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
\`\`\`

Registration happens at class-body evaluation, so importing the module is enough — no request needs to run.

### Before

\`\`\`python
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

The name was the registration. Renaming \`seal_total\` during a cleanup removed the rule with no error and no failing test.

### After

\`\`\`python
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

Two things change beyond the decorator: \`mode="async"\` becomes explicit rather than inferred from \`iscoroutinefunction\`, and methods can be renamed to describe the rule.

**Intermediate step:** adding \`@ward\` without renaming silences the warning immediately, since the decorator is the registration and the name becomes irrelevant.

\`\`\`python
@ward
def seal_total(self, data): ...    # no warning; rename later
\`\`\`

Details: [Stub Generation & Deprecations](contracts_tooling.md#deprecated-the-seal_--async_seal_-prefix-convention).

---

## Migration 8 — Adopt Contract Type Stubs

**Optional.** Makes Contract fields visible to \`mypy\` and \`pyright\`.

### Before

\`\`\`python
contract = UserContract(data=payload)
contract.is_sealed()
reveal_type(contract.email)   # Any
contract.emial                # typo survives review
\`\`\`

### After

\`\`\`bash
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
\`\`\`

\`\`\`python
reveal_type(contract.email)   # str
contract.emial                # error: "UserContract" has no attribute "emial"
\`\`\`

### Keeping stubs honest

\`\`\`yaml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check
\`\`\`

\`--check\` exits non-zero on a missing or stale stub and prints the regeneration command. Generation is deterministic, so it cannot fail at random.

Details: [Stub Generation & Deprecations](contracts_tooling.md).

---

## Migration 1 — Durable, Distributed Tasks

### Before

\`\`\`python
# workspace.py
Integration.tasks(num_workers=4)
\`\`\`

Jobs lived in the web worker process and were lost on restart. Running two web workers meant two independent queues, so a periodic task fired twice.

### After

\`\`\`python
# workspace.py
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=8,
    lease_seconds=120,
)
\`\`\`

Or, with no new infrastructure:

\`\`\`python
Integration.tasks(backend="sql")   # requires Integration.database(...)
\`\`\`

### What you must check

**Task arguments must be JSON-serializable.** On a durable backend, a non-serializable argument raises \`TaskSerializationFault\` at \`enqueue()\`. Audit your enqueue calls for ORM instances, file handles, and custom objects:

\`\`\`python
# Breaks on a durable backend
await tasks.enqueue(send_welcome, user)          # ORM instance

# Correct
await tasks.enqueue(send_welcome, user.id)       # worker re-loads it
\`\`\`

**Every worker must import every task module.** Workers resolve jobs by registered name. A worker process that has not imported the module defining a task raises \`TaskResolutionFault\` for that job. Declaring tasks in your module manifests handles this automatically.

**Task functions should be idempotent.** Distributed backends are at-least-once: a worker that stalls past its lease can have its job reclaimed and run twice.

See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Migration 2 — Replace Hand-Rolled Deduplication

### Before

\`\`\`python
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

### After

\`\`\`python
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version releases the reservation when the job reaches a terminal state, so a failed job can be retried immediately rather than being blocked until the TTL expires.

Use \`dedup="raise"\` where a duplicate indicates a caller bug:

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

The default remains \`"allow"\`, so nothing changes until you opt in.

See [Idempotency & Deduplication](idempotency.md).

---

## Migration 3 — Replace Ad-Hoc Job Sequencing

### Before

\`\`\`python
# One long-lived job orchestrating the rest — lost on restart,
# and holding a worker slot while doing nothing
@task(name="pipeline")
async def pipeline(source):
    rows = await extract(source)
    cleaned = await clean(rows)
    await load(cleaned)
\`\`\`

### After

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    clean.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)
\`\`\`

Each step is an independent job with its own retry budget. The graph is durable the moment it is submitted, so a restart resumes rather than restarting from the top. A \`WAITING\` step occupies no worker slot.

See [Workflows & DAGs](workflows.md).

---

## Migration 4 — Background Mail Delivery

### Before

\`\`\`python
Integration.mail(default_from="noreply@example.com", providers=[...])
\`\`\`

\`asend()\` performed the SMTP conversation inside the request. Response time was tied to provider latency.

### After

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")

Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

**Call sites do not change.** \`EmailMessage(...).asend()\` still returns an envelope ID; it now returns before delivery completes.

### What you must check

**Code that assumed mail was sent on return.** With the queue enabled, a returned envelope ID means *accepted*, not *delivered*. Poll status where that distinction matters:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status   # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
\`\`\`

**Tests asserting on a mail outbox.** Tests that send through a queued service must drive the task manager, or configure the mail service without \`queue_enabled\` for that test.

**\`queue_persistent=True\` requires \`Integration.database(...)\`.** Without a reachable database, mail logs an error and falls back to in-memory stores.

See [Mail Delivery Queue](mail_queue.md).

---

## Migration 5 — Bounce Handling

New capability; there is nothing to migrate from. Add a webhook endpoint:

\`\`\`python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        return Response.json(await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        ))
\`\`\`

Two things to get right:

- **Verify signatures.** Pass \`verify_topic_arn\` (SES), \`public_key\` (SendGrid), or \`signing_key\` (Mailgun). An unverified endpoint lets anyone forge a bounce and suppress an arbitrary address.
- **Exempt the path from CSRF.** Providers do not carry your CSRF token; signature verification is the authenticity check.

If you already maintain a suppression list in your own tables, import it:

\`\`\`python
for row in await LegacySuppression.all():
    await mail.suppression.suppress(row.email, reason=SuppressionReason.HARD_BOUNCE)
\`\`\`

See [Bounce Handling & Suppression](bounces_suppression.md).

---

## Migration 6 — Job Result Handling

If you worked around results arriving as \`repr\` strings on a persistent backend, remove the workaround:

\`\`\`python
# Before — parsing the repr form back
total = sum(int(r) for r in parent_results)

# After — JSON-safe values round-trip intact
total = sum(parent_results)
\`\`\`

Values that are not JSON-serializable still arrive as \`repr\` strings, which is unavoidable — return dicts, lists, and primitives from steps whose results are consumed downstream.

See [Bug Fixes](bugfixes.md).

---

## Deprecated Features

**The \`seal_*\` / \`async_seal_*\` Contract validator naming convention.** Deprecated in 1.3.0, removed in 2.0.0.

Behavior is unchanged in 1.x — these methods continue to register and run exactly as before. Declaring one now emits a \`DeprecationWarning\` naming its exact replacement decorator. Migration is mechanical; see [Migration 7](#migration-7--seal_-validators-to-ward).

Nothing else was deprecated.

## Removed Features

The third-party \`httpx\` dependency was removed in favour of the native \`aquilia.http\` client. No public API changed. See [Native HTTP Client](http_native.md).

## Breaking Changes

The tasks, mail, and HTTP work introduces no breaking changes.

**Contracts ships four behavioral corrections**, each replacing behavior that was incorrect:

| Change | Previously | Now | Action |
|---|---|---|---|
| Nested Contract rules enforced | Nested \`@ward\` / \`validate()\` never ran | Runs, and rejects | Review nested Contracts — see [0.1](#01--nested-contract-rules-are-now-enforced) |
| \`Lens(many=True)\` unresolved | Returned \`[]\` | Raises \`LensUnresolvedFault\` | Prefetch, materialize, or use \`to_dict_async()\` — see [0.2](#02--lensmanytrue-raises-on-an-unresolved-relation) |
| Malformed-body errors | Per-field "required" | \`{"__all__": [...]}\` | Update clients that parse 422 bodies — see [0.3](#03--malformed-body-error-shape-changed) |
| \`IntFacet\` fractional input | \`3.9\` became \`3\` | Rejected | Round explicitly, or use \`FloatFacet\` — see [0.4](#04--intfacet-rejects-fractional-input) |

\`"__minimal__"\` projections also return a restricted field set now; the previous output was never correct. See [0.5](#05--__minimal__-projections-return-fewer-fields).

Two further behavior changes worth noting, neither an API break:

- With \`dkim_enabled=True\` and an incomplete configuration, sends now fail rather than shipping unsigned mail. Run \`aq mail check\` after enabling DKIM. See [CLI Changes](cli.md).
- A Contract with async wards *nested* beneath it now correctly raises \`ContractAsyncMismatchFault\` from \`is_sealed()\`. Previously it reported no async wards and skipped them silently.

---

## Compatibility Notes

| Area | Notes |
|---|---|
| Python | 3.10–3.13, unchanged |
| Existing manifests | No changes required |
| \`MemoryBackend\` | Behavior unchanged; still the default |
| Inline mail | Behavior unchanged; still the default |
| \`TaskManager.enqueue()\` | New keyword-only params, all defaulted to prior behavior |
| \`MailService\` | New \`store\` / \`suppression\` attributes; constructor arguments still win |
| Task result values | JSON-safe values now round-trip; previously \`repr\` on persistent backends |
| \`Contract\` public API | No signature changes. \`is_sealed()\` / \`is_sealed_async()\` gained an optional keyword-only \`groups\` parameter, defaulting to prior behavior. |
| \`@ward\` | \`order\`, \`when\`, and \`groups\` are optional; a bare \`@ward\` behaves exactly as before |
| \`Spec\` | \`frozen\` and \`fail_fast\` both default to \`False\` — prior behavior |
| Validation messages | Byte-identical unless an i18n catalog defines the \`contracts.\` namespace |
| \`get_nested_contract_cls()\` | Still present, now delegating to \`resolve_nested()\` |
| Contract \`.pyi\` stubs | Entirely opt-in; not generating them changes nothing |

---

## Known Issues

- **Redis backend lacks automated test coverage** in this release; the SQL backend carries the durable-path integration tests. The Redis implementation is exercised manually and by the shared backend contract.
- **Mailgun signature verification is opt-in.** Omitting \`signing_key\` parses without verification and logs a warning. Treat it as required in production.
- **No built-in webhook route.** Applications wire \`parse_*\` and \`process_webhook\` into their own controller, so path, authentication, and CSRF policy stay under application control.
- **Workflow steps whose parent failed remain \`WAITING\`** rather than being cancelled. They will not run; inspect them with \`failed_jobs()\`.
- **Generic Contracts (\`Contract[T]\`) are not supported.** \`Contract.__class_getitem__\` already means *projection* (\`UserContract["public"]\`), so type parameterization needs an API decision: dispatch on argument type (backward compatible, but one syntax with two meanings), or move projections to an explicit method (cleaner, but breaks every existing subscript call site). \`typing.Self\`, \`Protocol\`, and \`NewType\` resolution are blocked behind the same decision. Deferred rather than guessed.
- **\`.pyi\` stubs replace their module for the type checker.** The generator reproduces the whole module surface, not only its Contracts. Anything it cannot render faithfully is emitted as \`Any\` and named in the command output.
- **\`to_dict_async()\` awaits relations sequentially.** Prefetching remains the right choice on hot paths; the async path exists so a missing prefetch degrades performance rather than raising.

---

## Related

- [Release Overview](README.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Idempotency & Deduplication](idempotency.md)
- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [Mail Security & MIME](mail_security.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md)
- [Contracts — Validation Control & Typing](contracts_validation.md)
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [CLI Changes](cli.md)
- [Bug Fixes](bugfixes.md)
`,
    "surp_to_json_migration.md": `# SURP Binary Format Removal & JSON Standardization (v1.3.5)

## Overview

In Aquilia v1.3.5, the legacy \`surp\` binary serialization format and library dependency have been completely removed across the entire framework in favor of native, standardized \`json\` format (\`.json\` artifacts, \`JSONBytecodeCache\`, \`JSONCatalog\`, \`JSONAuditStore\`, \`schema_snapshot.json\`, \`credentials.json\`, \`ws.json\`, \`discovery_cache.json\`).

---

## Key Changes

1. **HTTP Core Layer**:
   - \`Request\` no longer has \`is_surp()\`, \`accepts_surp()\`, \`prefers_surp()\`, or \`surp()\` methods. \`request.data()\` returns \`request.json()\`.
   - \`Response\` no longer has \`Response.surp()\` or \`@requires_surp\` decorator. \`Response.negotiated()\` defaults to JSON encoding.
   - Removed \`InvalidSurp\` and \`SurpUnavailable\` fault classes.

2. **Internationalization (i18n)**:
   - \`SurpCatalog\` and \`has_surp()\` removed.
   - \`JSONCatalog\` is the default file catalog backend.
   - Default \`catalog_format\` in \`I18nConfig\` is \`"json"\`.

3. **Template Engine**:
   - \`SurpBytecodeCache\` renamed to \`JSONBytecodeCache\`.
   - Template compilation artifacts default to \`artifacts/templates.json\` with envelope \`"__format__": "json"\`.

4. **Aquilary & Auto-Discovery**:
   - Manifest exports and imports use \`.json\` format (\`frozen.json\`).
   - Discovery cache stored at \`.aquilia/discovery_cache.json\`.

5. **Models & Database**:
   - Migration DSL snapshots use \`schema_snapshot.json\`.
   - Migration CLI commands default \`--format\` option to \`"json"\`.

6. **Admin Audit Trail & Providers**:
   - Audit store updated to \`JSONAuditStore\` saving to \`.aquilia/audit.json\`.
   - Provider credential storage updated to \`credentials.json\`.

7. **Build & CI**:
   - Removed \`surp\` optional dependency from \`pyproject.toml\`, \`setup.py\`, and CI workflows.

---

## Migration Steps for Applications

- **File Extensions**: Rename any \`.surp\` configuration or manifest files in your project workspace to \`.json\`.
- **API Calls**: Replace any calls to \`request.surp()\` or \`Response.surp()\` with \`request.json()\` or \`Response.json()\`. Remove \`@requires_surp\` decorators from controller routes.
- **Imports**: Replace imports of \`SurpCatalog\` or \`SurpBytecodeCache\` with \`JSONCatalog\` and \`JSONBytecodeCache\`.
`,
    "workflows.md": `# Workflows & DAGs — Aquilia v1.3.5

Jobs can now declare dependencies on other jobs. Sequential chains, parallel groups, fan-in callbacks, and arbitrary directed acyclic graphs are all expressed through the same queue and the same workers — equivalent to Celery Canvas or BullMQ Flows.

Previously there was no way to say "run B after A". Applications either awaited a job's completion inside another job (occupying a worker slot while doing nothing) or polled \`get_job()\` in application code.

---

## Motivation

Real background work is rarely one isolated function:

- An import pipeline extracts, transforms, then loads.
- A report shards across N workers and merges the results.
- A deploy runs migrations, then warms caches, then notifies.

Without dependency support, each of these had to be orchestrated by a long-lived coroutine that survives for the whole pipeline — which loses everything on restart and does not distribute.

---

## Design Goals

1. **The graph is durable the moment it is submitted.** Every job is created up front with its dependencies recorded, so the workflow survives a restart on a persistent backend.
2. **No orchestrator process.** The backend releases dependent jobs as their dependencies complete. Nothing needs to stay resident.
3. **Reuse the existing queue.** Workflows are ordinary jobs with a \`depends_on\` field, not a parallel execution system.
4. **A failed step stops its branch.** Downstream jobs must not run on missing input.

---

## Architecture

### \`Signature\`

A task plus the arguments it will be called with, not yet enqueued — the same concept as Celery's signature, and named the same way.

\`\`\`python
from aquilia.tasks.workflow import Signature

step = Signature(send_email, ("user@example.com",), {"subject": "Hi"})
\`\`\`

Or, more idiomatically, from a \`@task\` descriptor:

\`\`\`python
step = send_email.s("user@example.com", subject="Hi")
\`\`\`

\`with_parent_results()\` returns a copy that receives its dependencies' return values as a \`parent_results\` keyword at execution time:

\`\`\`python
merge.s().with_parent_results()   # merge(parent_results=[...])
\`\`\`

The marker stored in the job's kwargs is a plain string, replaced with real values by the worker at execution time. That keeps the job JSON-serializable and lets results be read after a restart.

### \`Workflow\`

The graph builder. \`add()\` returns an index used to declare dependencies:

\`\`\`python
from aquilia.tasks.workflow import Workflow

wf = Workflow("nightly")
extract = wf.add(extract_rows.s(source))
clean   = wf.add(clean_rows.s(), depends_on=[extract])
enrich  = wf.add(enrich_rows.s(), depends_on=[extract])
wf.add(load_rows.s().with_parent_results(), depends_on=[clean, enrich])

result = await wf.run(manager)
\`\`\`

\`run()\` validates the graph, enqueues every node with its dependencies already wired, and returns a \`WorkflowResult\`. Dependent jobs start in \`WAITING\` and are released by the backend as their dependencies complete.

### \`WorkflowResult\`

\`\`\`python
await result.is_complete(manager)    # every terminal job reached a terminal state
await result.results(manager)        # terminal jobs' return values, in declaration order
await result.failed_jobs(manager)    # jobs that ended FAILED or DEAD
\`\`\`

\`is_complete()\` returns \`True\` for failure as well as success — use \`failed_jobs()\` to distinguish.

---

## Helpers

### \`chain\` — sequential

Each step waits for the previous one to complete successfully.

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(manager)
\`\`\`

### \`group\` — parallel

Pure fan-out. Every step runs concurrently with no dependencies between them.

\`\`\`python
from aquilia.tasks.workflow import group

await group([shard.s(n) for n in range(8)]).run(manager)
\`\`\`

### \`chord\` — parallel then fan-in

A \`group\` header plus a callback that runs once every header job has completed, receiving their results.

\`\`\`python
from aquilia.tasks.workflow import chord

await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(manager)
\`\`\`

### Arbitrary DAGs

\`chain\`, \`group\`, and \`chord\` are conveniences over \`Workflow.add(..., depends_on=[...])\`. Any acyclic shape — diamonds, multi-level fan-out/fan-in, mixed widths — is expressible directly.

---

## Validation

Graph errors raise \`TaskWorkflowFault\` before anything is enqueued, so a malformed workflow never partially executes:

- An empty workflow.
- A cycle — detected by depth-first traversal with a path stack; the fault names the cycle.
- A dependency index that does not exist.

\`\`\`python
wf = Workflow("bad")
wf.add(step.s(), depends_on=[99])   # TaskWorkflowFault — unknown dependency
\`\`\`

---

## Edge Cases

**A failed dependency does not release its dependents.** If a step exhausts its retries, everything downstream stays \`WAITING\` rather than running on missing input. Inspect with \`failed_jobs()\`. These jobs are not automatically cancelled — a \`WAITING\` job whose parent is dead will not run and will not complete.

**Result fidelity.** Dependency results arrive as the actual returned value when it is JSON-compatible. A non-JSON return value degrades to its \`repr\` on a persistent backend, because an arbitrary object cannot be reconstructed from JSON. Return dicts, lists, and primitives from steps whose results are consumed downstream.

**Serialization applies to every step.** \`Workflow.run()\` enqueues through the normal path, so a step with non-serializable arguments raises \`TaskSerializationFault\` on a persistent backend — at submission, before any step runs.

**Workflows do not span backends.** Every job in a workflow lives on the manager it was submitted to. To span processes, use a shared durable backend.

**Ordering within a group is not guaranteed.** \`results()\` returns terminal values in *declaration* order, but execution order and completion order are arbitrary.

---

## Performance Implications

Workflow submission is O(n) enqueues for n steps, performed up front. There is no polling process and no idle worker held open waiting for a dependency — a \`WAITING\` job occupies no worker slot. Dependency resolution is one lookup per dependency at release time.

For very wide graphs (thousands of parallel steps), submission cost is dominated by the enqueue round trips; on \`RedisBackend\` these are pipelined by the backend.

---

## Compatibility

Purely additive. \`Workflow\`, \`Signature\`, \`WorkflowResult\`, \`chain\`, \`group\`, and \`chord\` are new exports from \`aquilia.tasks\`. The \`depends_on\`, \`workflow_id\`, and \`initial_state\` parameters on \`TaskManager.enqueue()\` are new keyword-only arguments with defaults that preserve prior behavior. No existing API changed.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — required for workflows that span processes
- [Idempotency & Deduplication](idempotency.md)
- [Migration Guide](migration.md)
`,
  },
  "1.3.4": {
    "README.md": `# Aquilia v1.3.4 Release Notes — "Structural Integrity & Controller Expansion"

Aquilia v1.3.4 is a major architecture audit and feature release focusing on framework stability, registry correctness, controller integrity, workspace discovery robustness, and scalability.

This release combines Phase 1 (registry, workspace, config, and runtime audit fixes) with Phase 2 (controller system audit fixes, strict resolved-import discovery mode, distributed throttle backends, and Resource / ViewSet CRUD controllers).

## Table of Contents

1. [Phase 1: Round 1 Bugfixes](bugfixes_r1.md)
2. [Phase 1: Round 2 Bugfixes](bugfixes_r2.md)
3. [Phase 1: Performance Improvements](performance.md)
4. [Phase 1: Manifest System Changes](manifest_system.md)
5. [Phase 1: Workspace Discovery Enhancements](workspace_discovery.md)
6. [Phase 1: CLI Updates](cli.md)
7. [Phase 2: Controller System Audit Fixes](controller_audit.md)
8. [Phase 2: Strict Resolved-Import Discovery Mode](strict_discovery.md)
9. [Phase 2: Distributed Throttle Backends](distributed_throttle.md)
10. [Phase 2: Resource / ViewSet CRUD Controllers](resource_viewset.md)
11. [Migration Guide](migration.md)
`,
    "controller_audit.md": `# Controller System Audit Fixes

Details of the fixes applied to ControllerEngine, AuthManager, and routing in Aquilia v1.3.4 (§6.1–§8 of architectural audit report).

## §6.1 Lifecycle Hook Bypass (CRITICAL)
is_simple check now consults _has_lifecycle_hooks cache. Simple routes on controllers with custom on_request/on_response execute hooks unconditionally.

## §6.2 Unintended Token Generation (SECURITY)
Added issue_tokens: bool = True to authenticate_password() and SignInProvisionPolicy. Set False for session-only auth without minting JWTs.

## §6.3 Forward-Reference Type Resolution (BUG)
Exact string match replaces substring matching in _extract_method_params(). Fallback to __annotations__ when get_type_hints() raises.

## §6.4 Dynamic Segment Route Conflict False Positives (BUG)
_routes_conflict() compares type castors. /<id:int> and /<slug:str> are no longer flagged as conflicts.

## §5.3 Class-Level Cache Contamination (ARCH)
Added clear_caches() classmethods to ControllerEngine and ControllerFactory to flush id()-keyed caches between test runs.
`,
    "strict_discovery.md": `# Strict Resolved-Import Discovery Mode

Runtime-import-based discovery engine (StrictDiscoveryEngine) using importlib and inspect.getmro().

- Resolves transitive inheritance chains and aliased imports (e.g. Controller as Base)
- CLI usage: aq discover --strict
- Programmatic usage: engine.discover(strict=True)
- Handles ImportError gracefully per file with log warning
`,
    "distributed_throttle.md": `# Distributed Throttle Backends

Pluggable ThrottleBackend architecture supporting single-instance and multi-worker cluster rate limiting.

- MemoryThrottleBackend: sliding window with asyncio.Lock and LRU eviction
- RedisThrottleBackend: Redis sorted set sliding window with fail_open graceful degradation
- Ergonomic factories: Throttle.with_redis() and Throttle.with_memory()
`,
    "resource_viewset.md": `# Resource & ViewSet CRUD Controllers

Declarative CRUD controller abstraction via Resource[T], CRUDResource[T], ReadOnlyResource[T], and @action decorator.

- Auto-registers list (GET /), retrieve (GET /{id}), create (POST /), update (PUT /{id}), partial_update (PATCH /{id}), destroy (DELETE /{id})
- Custom routes via @action(detail=True/False)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.4

Complete migration instructions for all v1.3.4 changes.

- Secret(env="VAR") explicit environment variable lookup
- AppManifest(imports=[...]) v2 API preference
- AQUILIA_FAIL_FAST=1 startup error option
- authenticate_password(issue_tokens=False) session auth pattern
- Throttle.with_redis() distributed rate limiting upgrade

## Phase 3 - Cache, Storage & Filesystem

Every public API is preserved. Three behaviours change as corrections of clearly-wrong behaviour:

- Cache keys gain a version segment (key_version now reaches the key builder). Expect one cold cache on deploy, or set key_version=0 to keep the old layout.
- @cached no longer drops the first positional argument, so decorated functions stop returning other calls' values. Flush affected namespaces on a distributed backend.
- Authenticated responses are no longer served from the shared HTTP cache. Opt in with cache_authenticated=True plus the identity header in vary_headers.

Optional adoption: Integration.filesystem() for a DI-injectable FileSystem, distributed_stampede_lock for cross-process coalescing, serializer_secret_key for signed pickle, multipart_threshold for large S3 objects, and allow_unsandboxed=False for a fail-loudly sandbox posture.
`,
    "cache_audit.md": `# Cache System Audit Fixes

Fixes applied to aquilia.cache in v1.3.4, from the Cache & Storage architectural audit.

## Critical

- @cached dropped the first positional argument, so all calls to a single-argument function collapsed onto one key and returned another call's value. A silent data-correctness bug, not an error.
- CacheMiddleware cached identity-bearing responses under an identity-independent key, serving the first authenticated user's response to everyone. Requests carrying Cookie or Authorization now bypass the cache, and Set-Cookie responses are never stored, unless cache_authenticated=True is set alongside the identity header in vary_headers.
- The middleware read a nonexistent Response.content, so every cached entry stored an empty body. Response now exposes public content and body() accessors; unmaterialisable content is treated as not cacheable.
- Server._setup_cache() passed an invalid ttl= argument; the TypeError was swallowed and the middleware was silently never installed even when enabled.

## Correctness

- key_version was parsed from config and never reached the key builder, so the documented mass-invalidation workflow did nothing.
- decorators.py held a second key builder pinned at version=0, embedding the namespace twice and ignoring key_prefix. Decorator and service keys now share one layout.
- Functions returning None were never cached and recomputed forever. They are cached now; opt out with condition=lambda r: r is not None.
- Cache-Control no-store/private and the X-Cache-TTL override were read case-sensitively against a lowercase header map and never matched.

## Performance and leaks

- LFU eviction was a linear scan despite documenting O(log n). A real (frequency, key) min-heap now backs it.
- The TTL heap grew without bound when the same TTL'd key was rewritten. Both heaps compact against live entries: 2,000 rewrites now bound the heap to at most 16 entries.

## Redis

- The docstring claimed Lua atomicity that did not exist; increment() was a check-then-act race. It now runs the existence check and INCRBY in one script.
- Tag and namespace sets accumulated members whose keys expired naturally. A Lua prune removes them during ordinary reads.
- get() never returned tags, silently diverging from MemoryBackend. A TTL-matched sidecar restores tags and namespace.
- Stampede prevention was per-process. RedisBackend now offers a leased, token-checked SET NX PX lock so only one worker in the fleet recomputes.

## Configuration

- serializer="pickle" was unreachable because no secret key could be supplied. Added serializer_secret_key.
- CompositeBackend discarded async L2 write tasks, so shutdown could drop them. Tasks are tracked and drained.`,
    "storage_filesystem_audit.md": `# Storage & Filesystem Audit Fixes

Fixes applied to aquilia.storage and aquilia.filesystem in v1.3.4. The central finding was that path containment had been implemented twice - correctly in filesystem, incorrectly in storage. There is now exactly one implementation, used by both.

## Critical

- The streaming path ignored its sandbox entirely. stream_read and stream_copy accepted config and sandbox arguments and never passed them to the validator, while presenting the same method shape as the protected whole-file helpers. Paths are now validated before any descriptor is opened.
- Every FileSystem directory method raised TypeError: list_dir() got an unexpected keyword argument 'config'. The underlying functions now accept and enforce config and sandbox.
- LocalStorage used str.startswith() for containment, so /var/data-private satisfied a root of /var/data. It now delegates to the framework's canonical validate_path, which resolves symlinks and compares path components.

## Performance and scale

- Local and S3 backends buffered whole objects in memory despite documenting a streaming contract. Both stream in chunks now; content materialises only on an explicit read().
- S3 used put_object for everything, capping objects at 5 GB. Multipart upload is used above multipart_threshold, and a failed part aborts the upload.
- All cloud backends used the shared default executor via the deprecated get_event_loop(). A dedicated bounded pool (aquilia-storage threads, AQUILIA_STORAGE_MAX_WORKERS) replaces it.

## Robustness

- StorageRegistry.initialize_all() aborted the whole subsystem if any backend failed. Only a failing default backend is fatal now; optional backends degrade and report unhealthy.
- FileSystemConfig gained allow_unsandboxed. Setting it to False makes an unset sandbox_root a boot-time error instead of silently disabling containment.
- validate_path documents that symlinks are always resolved for containment regardless of follow_symlinks, which governs metadata semantics only.
- StorageRegistry.create_backend() imports any dotted path in configuration; the trust boundary is now documented.`,
    "subsystem_lifecycle.md": `# Subsystem Lifecycle & Health

Boot, health, and DI integration changes for cache, storage, and filesystem in v1.3.4.

## Filesystem is a first-class subsystem

Previously FileSystem required manual construction and DI registration, with no managed pool lifecycle and no health reporting. Integration.filesystem() now registers it in every DI container, starts the pool at startup, and drains it at shutdown. Disabled by default, so existing applications are unaffected.

## Health checks reflect reality

Cache and storage health were registered as literal HEALTHY without probing anything, so an unreachable backend was invisible to /health. The cache now performs a real write/read/delete round trip; storage pings every backend and publishes one storage.alias entry per disk plus a healthy/degraded/unhealthy aggregate naming the failing aliases; the filesystem reports pool state.

## StorageSubsystem clarified, not deleted

StorageSubsystem is the BootContext entry point for embedders, tests, and alternative runners, while AquiliaServer boots storage through its own ordered setup sequence. Both share StorageRegistry, so behaviour cannot diverge - only the orchestration differs. This is now stated in the module docstring rather than left ambiguous.

## DI exception contract restored

patch_di_container() re-raised ProviderNotFoundFault in place of ProviderNotFoundError, so every handler catching ProviderNotFoundError silently stopped working once any server was constructed. The conversion was redundant - ProviderNotFoundError already subclasses DIFault. The original error is now enriched in place and re-raised unchanged, and the patch is idempotent.`
  },
  "1.3.2": {
    "README.md": `# Aquilia v1.3.2 Release Notes — "Specula API Observatory"

Aquilia v1.3.2 introduces **Specula**, a major evolution of the framework's documentation and API exploration subsystem. Specula completely replaces the legacy OpenAPI 3.1.0 generator and static Swagger/ReDoc pages with a compiled, introspective ASGI dashboard (the Specula Observatory), reactive hot-reloading streams, automated security and clearance level mapping, a schema-synthesized mock server, and Postman/Insomnia collection exporters.

## Table of Contents

1. [Specula Observatory UI & Integration](observatory.md)
   * The new dashboard philosophy.
   * Integrating Specula via \`Integration.specula(...)\`.
   * UI branding and Server-Sent Events (SSE) live streams.
2. [Spec Compilation & Schema Inference](compilation.md)
   * The compiler-integrated \`SpeculaBuilder\`.
   * Python-to-JSON Schema type mapping.
   * Multi-strategy request body and response resolution.
3. [Automated Security & Clearance Detection](security.md)
   * Inferred security schemes from pipeline guards.
   * Integrated authorization clearance level detection.
   * Extended metadata (\`x-specula-security\`) vendor extensions.
4. [Mock Server & Collection Exports](mock_exports.md)
   * Interactive mocking engine at \`/specula/mock\`.
   * Schema synthesis with configurable recursion depth limits.
   * Dynamic exports for Postman v2.1 and Insomnia v4.
5. [Migration Guide](migration.md)
   * Removing legacy \`OpenAPIIntegration\` references.
   * Replaced classes, paths, and deprecations.

---

## Key Subsystem Improvements

1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.
`,

    "compilation.md": `# Spec Compilation & Schema Inference

Specula features a compiler-integrated OpenAPI 3.1.0 specification engine (\`SpeculaBuilder\`). Instead of scanning source files at startup, it introspects Aquilia's compiled routing topology in memory, extracting schemas, bindings, parameters, and outputs.

---

## Python-to-JSON Schema Mapping

When generating schema objects, Specula inspects standard type hints and maps them to their OpenAPI 3.1.0 JSON Schema equivalents. 

Specula is fully compliant with the OpenAPI 3.1.0 specification:
* **Option types** use \`oneOf\` blocks combined with \`{"type": "null"}\` instead of the deprecated \`nullable\` property.
* **Complex Python structures** map cleanly to nested schemas.

### Mapping Reference Table

| Python Type Hint | JSON Schema Equivalent |
| :--- | :--- |
| \`str\` | \`{"type": "string"}\` |
| \`int\` | \`{"type": "integer"}\` |
| \`float\` | \`{"type": "number", "format": "double"}\` |
| \`bool\` | \`{"type": "boolean"}\` |
| \`bytes\` | \`{"type": "string", "format": "binary"}\` |
| \`None\` / \`type(None)\` | \`{"type": "null"}\` |
| \`Optional[T]\` / \`T \| None\` | \`{"oneOf": [{"type": T_schema}, {"type": "null"}]}\` |
| \`list[T]\` / \`List[T]\` | \`{"type": "array", "items": T_schema}\` |
| \`dict[str, T]\` / \`Dict[str, T]\` | \`{"type": "object", "additionalProperties": T_schema}\` |
| \`tuple[T1, T2]\` | \`{"type": "array", "prefixItems": [T1_schema, T2_schema], "minItems": 2, "maxItems": 2}\` |
| \`Contract\` / \`Model\` | \`{"\$ref": "#/components/schemas/Name"}\` |

---

## Request Body Inference Strategies

Specula resolves request payloads through a 5-tier inference engine, prioritizing explicit developer configurations over implicit code analysis.

### 1. The \`request_contract\` Parameter
If a route decorator declares a validation contract directly, the builder generates a reference schema:
\`\`\`python
@POST("/users", request_contract=UserCreateContract)
async def create_user(self, ctx: RequestCtx): ...
\`\`\`

### 2. Contract Parameter Type Hints
If a route handler receives a parameter type-hinted with an Aquilia \`Contract\` class, it is automatically mapped as the JSON body payload:
\`\`\`python
@POST("/users")
async def create_user(self, ctx: RequestCtx, payload: UserCreateContract): ...
\`\`\`

### 3. Explicit \`Body\` Metadata Annotations
If a parameter is annotated using standard Python type annotations with \`Body()\`, it is mapped to a properties-based object payload:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx, amount: Annotated[int, Body()] = 1): ...
\`\`\`

### 4. Docstring Body Mappings
The builder parses Google-style docstrings, extracting raw examples from \`Body:\` headers:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx):
    """
    Create an item.

    Body: {"name": "Widget", "count": 10}
    """
    ...
\`\`\`

### 5. Source Code Introspection
As a fallback, Specula scans the compiled handler source code for extraction patterns:
* Finding \`await ctx.json()\` infers a generic \`application/json\` object.
* Finding \`await ctx.form()\` infers an \`application/x-www-form-urlencoded\` form.

---

## Response Shapes Resolution

Specula automatically maps success and error response channels.

### Success Shapes
1. **Model / Contract Mappings**: Declaring \`response_model\` or \`response_contract\` registers the corresponding schema (input contracts map with \`Input\` suffix, output contracts map directly) and binds them under status code \`2xx\`.
2. **Standard Output Fallbacks**: If no return contract is specified, Specula inspects handler code:
   * Calls to \`Response.json(...)\` default to \`application/json\`.
   * Calls to \`Response.html(...)\` or template rendering functions default to \`text/html\`.
   * References to \`SSEResponse(...)\` default to \`text/event-stream\`.

### Error Shapes
* **Raises Docstring Section**: Specula compiles exception details declared in Google-style docstrings into typed status responses:
  \`\`\`python
  @GET("/users/<id:int>")
  async def get_user(self, id: int):
      """
      Get user by ID.

      Raises:
          UserNotFoundFault (404): The user does not exist.
      """
      ...
  \`\`\`
  Specula compiles this raises annotation into a structured \`404 Not Found\` response returning the standard \`AquiliaError\` schema.
* **Auto-Validation Errors**: All write routes (\`POST\`, \`PUT\`, \`PATCH\`) automatically carry a default \`422 Unprocessable Entity\` response mapping returning the structured \`AquiliaValidationError\` schema.
`,

    "migration.md": `# OpenAPI to Specula Migration Guide

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine. This guide outlines how to migrate your configuration, imports, and endpoints.

---

## 1. Configuration & Integration Upgrades

The old \`OpenAPIIntegration\` has been replaced by \`SpeculaIntegration\`. In your \`workspace.py\`, update your registrations:

### Legacy Style (Removed)
\`\`\`python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
\`\`\`

### New Style (Active)
\`\`\`python
from aquilia.integrations import SpeculaIntegration

# Option A: Direct class registration
workspace.integrate(SpeculaIntegration(
    title="Store API",
    ui_path="/apidocs",
    ui_theme="dark"
))

# Option B: Fluent helper
# workspace.integrate(Integration.specula(
#     title="Store API",
#     ui_path="/apidocs",
#     ui_theme="dark"
# ))
\`\`\`

### Parameter Mapping Table

Use this reference table to map configuration options from legacy OpenAPI attributes to Specula attributes:

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| \`docs_path\` | \`ui_path\` | Default changes from \`/docs\` to \`/specula\`. |
| \`openapi_json_path\` | \`json_path\` | Default changes from \`/openapi.json\` to \`/specula/spec.json\`. |
| \`redoc_path\` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| \`swagger_ui_theme\` | \`ui_theme\` | Values: \`"auto"\`, \`"light"\`, \`"dark"\`. |
| \`swagger_ui_config\` | (Removed) | Replaced by direct dashboard configuration. |

---

## 2. Replaced Imports & Engines

If you manually generated specs, update your imports and instantiation:

\`\`\`python
# --- Legacy Imports (Removed) ---
# from aquilia.controller.openapi import OpenAPIConfig, OpenAPIGenerator
# config = OpenAPIConfig(title="API")
# spec = OpenAPIGenerator(config=config).generate(router)

# --- New Imports (Active) ---
from aquilia.specula.config import SpeculaConfig
from aquilia.specula.schema.builder import SpeculaBuilder

config = SpeculaConfig(title="API")
spec = SpeculaBuilder(config=config).build(router)
\`\`\`

---

## 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path \`/docs\` is replaced by \`/specula\`.
* **ReDoc Docs**: Old path \`/redoc\` is deprecated. Use the unified \`/specula\` dashboard.
* **JSON Specification**: Old path \`/openapi.json\` is replaced by \`/specula/spec.json\`.
* **YAML Specification**: Specula now supports rendering YAML natively at \`/specula/spec.yaml\`.
`,

    "mock_exports.md": `# Mock Server & Collection Exports

Specula features a schema-driven Mock Server and dynamic collection exporters to support rapid frontend integration and testing.

---

## Interactive Mock Server (\`/specula/mock\`)

The mock server lets developers call any documented API endpoint and receive a plausible response payload without executing any business logic.

### Enabling the Mock Server
The mock server is disabled by default. Enable it in your workspace configuration:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Customer API",
    mock_server_enabled=True,
    mock_max_depth=4 # limit recursive definitions mapping
))
\`\`\`

### How Payload Synthesis Works
When a request is sent to \`/specula/mock/<path>\`, the mock router matches the path against the compiled API specification. It resolves the success response (\`200\`, \`201\`, or \`202\`) and inspects the JSON Schema:

1. **Explicit Examples**: If the schema or individual fields define an \`example\` or \`examples\` block, those values are returned directly.
2. **Plausible Synthesis**: If no examples are configured, Specula inspects the schema field types and synthesizes logical placeholders:
   * **Formatting Matchers**: String formats like \`email\`, \`uuid\`, \`uri\`, and \`date-time\` map to real formatted values (e.g. \`user@example.com\`, \`550e8400-e29b-41d4-a716-446655440000\`).
   * **Key Name Inference**: If a string field matches common keys (such as \`email\` or \`url\`), appropriate values are auto-injected.
   * **Standard Defaults**: Integers default to \`42\`, numbers to \`3.14\`, booleans to \`True\`, and arrays to single-item arrays.
3. **Recursion Safety**: Self-referencing models (e.g., a node containing a list of children of its own type) are automatically truncated when nesting depth exceeds \`mock_max_depth\` (default \`4\`).

---

## Exporters

Specula exposes dynamic endpoints to download client collections configured with your current workspace routing topology and security schemes.

### 1. Postman Collection v2.1
* **Endpoint**: \`/specula/export/postman\`
* **Output**: A compliant Postman v2.1 collection JSON file.
* **Details**:
  * Groups endpoints into folders based on their tags or manifest module names.
  * Translates route variables like \`/users/<id:int>\` into Postman-compatible environment syntax: \`/users/{{id}}\`.
  * Pre-populates request bodies with JSON examples synthesized from Contract definitions.
  * Embeds default authorization headers mapped to the \`{{access_token}}\` environment variable.

### 2. Insomnia v4 Collection
* **Endpoint**: \`/specula/export/insomnia\`
* **Output**: A standard Insomnia v4 export file.
* **Details**:
  * Includes workspace configuration mapping the current API.
  * Sets up base environment variables referencing \`{{ _.base_url }}\`.
  * Configures HTTP methods, headers, and body payloads automatically.
`,

    "observatory.md": `# Specula Observatory UI & Integration

The Specula Observatory is a built-in interactive dashboard served natively by Aquilia at \`/specula\`. It provides a CDN-free developer sandbox that works entirely offline, inline-cached, and features hot-reload awareness.

## Workspace Integration

Specula is registered at the workspace level inside \`workspace.py\`. You configure it using the \`Integration.specula(...)\` builder method or by importing and instantiating \`SpeculaIntegration\` directly:

\`\`\`python
# workspace.py
from aquilia.workspace import Workspace
from aquilia.integrations import Integration, SpeculaIntegration

workspace = (
    Workspace("user-portal")
    
    # Style A: Fluent Integration helper
    .integrate(Integration.specula(
        title="User Portal API",
        version="1.4.0",
        ui_theme="dark"
    ))
    
    # Style B: Direct Instantiation (provides static checks and autocomplete)
    # .integrate(SpeculaIntegration(
    #     title="User Portal API",
    #     version="1.4.0",
    #     ui_theme="dark"
    # ))
)
\`\`\`

---

## Configuration Reference (\`SpeculaConfig\`)

When you configure Specula, your parameters map to the \`SpeculaConfig\` dataclass. The primary settings available are:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Info / Branding** | | | |
| \`title\` | \`str\` | \`"Aquilia API"\` | Name of the API, visible in the UI header and spec exports. |
| \`version\` | \`str\` | \`"1.0.0"\` | The current API release version. |
| \`description\` | \`str\` | \`""\` | Detailed description of the API. |
| \`ui_theme\` | \`str\` | \`"auto"\` | \`"auto"\` (matches system preferences), \`"light"\`, or \`"dark"\`. |
| \`ui_primary_color\`| \`str\` | \`"#22c55e"\` | Hex code for branding the main interface buttons and tags. |
| **URL Paths** | | | |
| \`ui_path\` | \`str\` | \`"/specula"\` | Browser path to view the Observatory HTML dashboard. |
| \`json_path\` | \`str\` | \`"/specula/spec.json"\`| JSON endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`yaml_path\` | \`str\` | \`"/specula/spec.yaml"\`| YAML endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`stream_path\` | \`str\` | \`"/specula/stream"\`| SSE stream pushing route updates to the UI. |
| \`mock_path\` | \`str\` | \`"/specula/mock"\` | Endpoint path for the mock server router. |
| **Feature Toggles** | | | |
| \`enabled\` | \`bool\` | \`True\` | Master toggle to enable or disable Specula routes. |
| \`include_internal\`| \`bool\` | \`False\` | Whether routes matching \`/_*\` are included in the spec. |
| \`detect_security\` | \`bool\` | \`True\` | Scan route guards and decorators to construct security schemes. |
| \`mock_server_enabled\`| \`bool\` | \`False\` | Set \`True\` to enable schema-synthesized mock responses. |
| \`spec_cache_ttl\` | \`int\` | \`60\` | In-memory cache duration (in seconds) for compiled spec payloads. |

---

## Hot-Reloading SSE Stream (\`/specula/stream\`)

During development, Aquilia runs with file watchers. When you modify controller code, the worker process reloads. 

Specula exposes a native ASGI Server-Sent Events (SSE) stream endpoint at \`/specula/stream\`. When the dashboard is loaded in a browser, it subscribes to this stream. When a reload happens, the server pushes an invalidation event down the pipe:

\`\`\`json
{"event": "update", "data": {"status": "invalidated", "version": "2.0.0"}}
\`\`\`

The Observatory frontend listens to this event and immediately fetches the newly compiled specification and routes dynamically, refreshing the client view with zero hard refreshes.

---

## Production Security Locks

By default, the Specula Observatory is fully open. In production environments, you can lock access down to authenticated users with specific roles:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Corporate Core API",
    docs_auth_required=True,
    docs_roles=["admin", "ops-team"]
))
\`\`\`

When \`docs_auth_required\` is enabled, the Specula controller inspects the request context using the configured \`AuthMiddleware\` pipeline. If the visitor lacks the required roles, they receive a \`403 Forbidden\` response.
`,

    "security.md": `# Automated Security & Clearance Detection

Specula integrates with Aquilia's security pipeline to automatically detect, map, and document authentication configurations. It translates pipeline guards and clearance levels into standard OpenAPI security requirements and rich custom metadata tags.

---

## Inferred Security Schemes

The spec builder scans your controllers' and routes' pipeline nodes and handler decorators to identify authentication mechanisms. It automatically registers and configures security definitions in the OpenAPI \`components.securitySchemes\` catalog:

| Inferred Guard Class Name | Generated Security Scheme | Schema Details |
| :--- | :--- | :--- |
| \`AuthGuard\` / \`Auth\` / \`@authenticated\` | \`bearerAuth\` | HTTP Bearer token (JWT) authentication. |
| \`ApiKeyGuard\` / \`ApiKey\` | \`apiKeyAuth\` | \`X-API-Key\` request header authorization. |
| \`SessionGuard\` / \`Session\` | \`cookieAuth\` | Session-based cookie verification (\`session\`). |
| \`BasicAuthGuard\` / \`Basic\` | \`basicAuth\` | HTTP Basic authentication. |
| \`OAuth2Guard\` / \`OAuth2\` | \`oauth2\` | OAuth2 Authorization Code flow. |

\`\`\`python
# Specula automatically registers bearerAuth with ["read", "write"] scopes
class OrderController(Controller):
    pipeline = [AuthGuard(), ScopeGuard("read", "write")]
    
    @GET("/")
    async def list_orders(self, ctx: RequestCtx): ...
\`\`\`

---

## Integrated Clearance Detection

Specula integrates directly with the \`aquilia.auth.clearance\` system to identify role-based and attribute-based clearance levels. 

The builder resolves the merged clearance level from the controller boundary and individual route overrides:
1. **Public Routes**: If the effective clearance resolves to \`AccessLevel.PUBLIC\` (e.g. via \`@grant(level=AccessLevel.PUBLIC)\`), security requirements are omitted for that route.
2. **Protected Routes**: If the effective clearance is higher than public, \`bearerAuth\` is automatically registered as a requirement.

---

## Rich Metadata Extensions (\`x-specula-security\`)

To support advanced observability and client generation, Specula embeds the full resolved authorization metadata in a custom vendor extension block (\`x-specula-security\`) inside each route's spec operation:

\`\`\`json
"x-specula-security": {
  "authenticated": true,
  "guards": [
    {
      "name": "RoleGuard",
      "type": "instance",
      "roles": ["admin", "compliance"],
      "require_all": false
    }
  ],
  "clearance": {
    "level": "INTERNAL",
    "level_value": 30,
    "entitlements": ["view_audit_logs", "override_fees"],
    "conditions": ["IsDuringOfficeHours", "IPRangeCondition"],
    "compartment": "finance"
  }
}
\`\`\`

This vendor block exposes:
* **\`authenticated\`**: Boolean flag indicating if verification is required.
* **\`guards\`**: Detailed list of active pipeline guard configurations, including roles, scopes, optional tags, resources, and evaluation settings.
* **\`clearance\`**: The full clearance metadata, including \`level\` name, \`level_value\` integer, required \`entitlements\` lists, active \`conditions\` names, and matching resource \`compartment\` boundaries.
`
  },
  "1.3.1": {
    "README.md": `# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (\`aquilia.auth\`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new \`AuthBackend\` protocol.
   * Built-in backends: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
   * The \`resolve_backend\` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: \`AuthGuard\`, \`RoleGuard\`, \`ScopeGuard\`, \`PolicyGuard\`.
   * Context-First Decorators: \`@authenticated\`, \`@roles_required\`, \`@scopes_required\`, \`@optional_auth\`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight \`AuthPrincipal\` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from \`strategies\` to \`backends\`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive \`PermissionEngine\`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.
5. **DI Scope Performance**: Deprecate the class/object-based \`ServiceScope\` Enum in favor of high-performance raw string literals backed by \`typing.Literal\` to eliminate import-time namespace scanning and runtime attribute lookup overhead.`,

    "backends.md": `# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the \`AuthBackend\` protocol. It is responsible for accepting a credential dictionary and resolving it to an \`Identity\`.

## The \`AuthBackend\` Protocol

The \`AuthBackend\` protocol is defined in \`aquilia.auth.backends.base\` using Python's structural subtyping (\`typing.Protocol\`):

\`\`\`python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity.
        
        May raise specific auth faults (e.g., AUTH_TOKEN_EXPIRED, AUTH_INVALID_CREDENTIALS).
        """
        ...
\`\`\`

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. \`TokenBackend\`
Validates JWT Bearer tokens. It verifies signatures, checks \`exp\` and \`nbf\` claims (with clock-skew tolerance), and validates token revocation via \`TokenManager\`.
* **Accepted Credentials**: \`{"token": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  \`\`\`

### 2. \`SessionBackend\`
Restores identity from a cookie-backed session. It looks up the \`identity_id\` from the session data or from \`session.principal\`, and fetches the corresponding active identity.
* **Accepted Credentials**: \`{"session": Session}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, identity_store: IdentityStore)
  \`\`\`

### 3. \`PasswordBackend\`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: \`{"username": str, "password": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  \`\`\`

### 4. \`ApiKeyBackend\`
Authenticates API requests via an opaque API key. It hashes the incoming key using \`HMAC-SHA256\` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: \`{"api_key": str, "required_scopes": list[str] | None}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  \`\`\`

---

## The Backend Resolver

To simplify instantiation, the \`resolve_backend\` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

\`\`\`python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
\`\`\`

It maps:
* Short names: \`"token"\` (TokenBackend), \`"session"\` (SessionBackend), \`"password"\` (PasswordBackend), \`"api_key"\` (ApiKeyBackend).
* Class references: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
* Dotted paths: \`"my_app.auth.backends.CustomBackend"\`.

### Example Configuration in \`workspace.py\`

\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
\`\`\``,

    "guards.md": `# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified \`PermissionEngine\`

The \`PermissionEngine\` (defined in \`aquilia.auth.permissions\`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* \`define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None\`: Declare a role and its transitively implied parents.
* \`role_implies(role: str, target: str) -> bool\`: Query the role DAG structure.
* \`register_policy(key: str, policy: PolicyCallable) -> None\`: Define a rule matching the signature \`(identity, resource) -> bool\`.
* \`check_role(identity: Identity, role: str) -> None\`: Asserts role ownership; raises \`AUTHZ_INSUFFICIENT_ROLE\` on failure.
* \`check_scope(identity: Identity, scope: str) -> None\`: Asserts scope ownership; raises \`AUTHZ_INSUFFICIENT_SCOPE\` on failure.
* \`check_policy(key: str, identity: Identity, resource: Any = None) -> None\`: Asserts policy assertion passes; raises \`AUTHZ_POLICY_DENIED\` on failure.
* \`has_role(identity: Identity, role: str) -> bool\`: Returns a boolean indicating role membership.
* \`has_scope(identity: Identity, scope: str) -> bool\`: Returns a boolean indicating scope membership.
* \`evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool\`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in \`aquilia.auth.guards\`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### \`AuthGuard\`
Verifies authentication status.
* **Optional Mode**: When \`optional=True\`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, \`AuthGuard\` attempts to proactively extract and authenticate a Bearer token using DI container-resolved \`AuthManager\`.
* **Signature**: \`AuthGuard(auth_manager=None, optional=False)\`

### \`RoleGuard\`
Ensures the identity holds required roles.
* **Resolution**: Uses \`PermissionEngine\` if found in the DI container; otherwise, falls back to direct membership testing of \`identity.get_attribute("roles", [])\`.
* **Signature**: \`RoleGuard(*roles, engine=None, require_all=True)\`

### \`ScopeGuard\`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard \`"*"\` scope.
* **Signature**: \`ScopeGuard(*scopes, require_all=True)\`

### \`PolicyGuard\`
Evaluates a policy registered in the permission engine.
* **Signature**: \`PolicyGuard(key, engine, resource=None)\`

---

## 3. Context-First Decorators

Decorators (defined in \`aquilia.auth.decorators\`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., \`identity\`, \`user\`, \`session\`, \`principal\`).

### \`@authenticated\`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has \`redirect_if_html=True\` or \`login_url\` configured, and accepts HTML, it performs a \`303 Redirect\` to the login page with a \`next\` query parameter.
* **Signature**:
  \`\`\`python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  \`\`\`

### \`@roles_required\` / \`@scopes_required\`
Evaluates role or scope conditions before executing the controller action.
\`\`\`python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

### \`@optional_auth\`
Evaluates the proactive \`AuthGuard(optional=True)\` check. It injects the user if found but does not block anonymous traffic.

### \`@requires\`
Composes multiple guards (both classes and instances) sequentially:
\`\`\`python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

---

## 4. Unified \`AuthMiddleware\`

The new unified \`AuthMiddleware\` (defined in \`aquilia.auth.middleware\`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  \`\`\`python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  \`\`\`
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If \`session_engine\` is provided, resolves the session and binds it to \`ctx.session\` and \`request.state["session"]\`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable \`backends\` (defaults to \`TokenBackend\` and \`SessionBackend\`). The first backend that accepts the credentials and returns an \`Identity\` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If \`require_auth=True\` and no identity is resolved, returns a \`401 Unauthorized\` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to \`request.state["identity"]\`, \`request.state["authenticated"]\`, and \`ctx.identity\`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.`,

    "migration.md": `# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based \`strategies\` setting has been removed. You must now configure the list of identity-resolution backends using the \`backends\` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on \`AquilaConfig.Auth\`.

### Legacy Configuration (v1.3.0)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
\`\`\`

### Refactored Configuration (v1.3.1)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
    # Store type: "memory" or "redis"
    store_type = "memory"
    
    # Rate Limiting configuration parameters
    rate_limit_max_attempts = 5
    rate_limit_window_seconds = 900
    rate_limit_lockout_seconds = 3600
    
    # MFA settings
    mfa_enabled = False
    mfa_required = False
    
    # Clock skew tolerance (in seconds) for JWT validations
    clock_skew_seconds = 5
    
    # Audit trail activation
    audit_enabled = True
\`\`\`

---

## 2. Replaced & Removed Decorators

The legacy decorators \`AdminGuard\` and \`VerifiedEmailGuard\` have been removed.

* **\`AdminGuard\`**: Replace with \`@roles_required("admin")\`.
* **\`VerifiedEmailGuard\`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
\`\`\`python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
\`\`\`

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in \`flow_guards.py\`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| \`RequireAuthGuard\` | \`AuthGuard\` |
| \`RequireRolesGuard\` | \`RoleGuard\` |
| \`RequireScopesGuard\` | \`ScopeGuard\` |
| \`RequirePolicyGuard\` | \`PolicyGuard\` |

### Pipeline Registration Example

#### Before:
\`\`\`python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
\`\`\`

---

## 4. Upgrading Session Guards

The legacy \`SessionGuard\` class and \`@requires\` decorator in \`aquilia.sessions.decorators\` have been removed. Switch to the unified \`PermissionEngine\` and the unified \`@requires\` decorator.

#### Before:
\`\`\`python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import requires

class CustomGuard:
    def check(self, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED
        session = getattr(ctx, "session", None)
        if session is None or not session.data.get("special_user"):
            raise AUTHZ_POLICY_DENIED()

@requires(CustomGuard())
async def handler(ctx):
    ...
\`\`\`

---

## 5. Removing the Fluent \`AuthConfig\` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the \`AuthConfig\` builder, you must remove it. Configure integrations directly using dictionary payloads or the \`AquilaConfig.Auth\` classes.

#### Before:
\`\`\`python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
\`\`\`

#### After:
\`\`\`python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
\`\`\`

---

## 6. Deprecated APIs & Relocations

* **\`AuthManager.logout()\`**: Deprecated in favor of \`AuthManager.sign_out()\`. Calling \`logout()\` now raises a \`DeprecationWarning\` but will invoke \`sign_out()\` internally for backward compatibility.
* **\`OptionalAuthMiddleware\`**: Deprecated in favor of \`AquilAuthMiddleware(require_auth=False)\` or the new \`AuthMiddleware\` class.
* **\`RateLimiter\` relocation**: The \`RateLimiter\` class has been moved from the \`manager\` module to \`aquilia.auth.manager_types\` to prevent circular imports. Update imports if you reference it directly.
* **\`ServiceScope\` Enum class**: Deprecated in favor of plain string literals (e.g., \`"singleton"\`, \`"app"\`, \`"request"\`, \`"transient"\`, \`"pooled"\`, \`"ephemeral"\`) paired with \`typing.Literal\` type hints (\`ServiceScopeLiteral\`). Using \`ServiceScope.SINGLETON\` or other members will now emit a \`DeprecationWarning\`.`,

    "sessions.md": `# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined \`AuthManager\` API and a standalone \`RateLimiter\` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

\`\`\`python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
\`\`\`

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The \`bind_identity\` function only writes core identifiers:

\`\`\`python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
\`\`\`

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The \`SessionBackend\` captures the active session credentials.
* It extracts the \`identity_id\` (either from \`session.principal\` or from \`session.data["identity_id"]\`).
* It fetches a fresh \`Identity\` object directly from the \`IdentityStore\` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: \`RateLimiter\`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone \`RateLimiter\` class in \`aquilia.auth.manager_types\` (and re-exported in \`aquilia.auth.manager\` for backward compatibility).

* **Constructor & Parameters**:
  \`\`\`python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  \`\`\`
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * \`record_attempt(key: str) -> None\`: Records a failed attempt. If attempts exceed \`max_attempts\` within the window, locks out the key.
  * \`is_locked_out(key: str) -> bool\`: Checks if the key is currently locked out.
  * \`get_remaining_attempts(key: str) -> int\`: Returns attempts left before lockout.
  * \`reset(key: str) -> None\`: Clears attempt history for the key on successful authentication.

---

## 3. \`AuthManager\` Refactored APIs

The \`AuthManager\` class (defined in \`aquilia.auth.manager\`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (\`jti\`) and blacklisting it:
* \`async def revoke_token(self, token: str, token_type: str = "refresh") -> None\`:
  * If \`token_type == "refresh"\`, revokes the refresh token directly.
  * If \`token_type == "access"\`, validates the access token, extracts the \`jti\` claim, and revokes it so subsequent validations reject it.

### Deprecated \`logout()\`
* **Signature**: \`async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None\`
* **Status**: **Deprecated** in favor of \`sign_out()\`. Raises a \`DeprecationWarning\` when called.

---

## 4. \`SessionAuthBridge\`

The \`SessionAuthBridge\` coordinates actions between \`AuthManager\` and \`SessionEngine\`:
* \`create_auth_session(identity, request, token_claims=None)\`: Resolves and binds authentication credentials to a new session.
* \`rotate_on_privilege_escalation(session, response)\`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* \`logout(session, response)\`: Destroys the current session.
* \`logout_all_devices(identity_id)\`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.`
  }
};
