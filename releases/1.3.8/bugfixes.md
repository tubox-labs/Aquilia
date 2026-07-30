# Comprehensive Bug Fixes in v1.3.8

This document details all 19 bug fixes and correctness improvements implemented in Aquilia v1.3.8.

---

## 1. Character-Split Index Columns (Critical)

- **Previous Behavior**: `Index(fields="token")` or tuple inputs converted column strings to character arrays (`columns=['t', 'o', 'k', 'e', 'n']`).
- **Root Cause**: `Index.deconstruct()` returned `fields: "token"`. Snapshot logic called `list("token")`, splitting the string into single characters.
- **New Behavior**: Strictly normalizes string fields into string lists (`columns=['token']`).

---

## 2. Foreign Key Target Table Name Mismatch (Critical)

- **Previous Behavior**: Foreign key references emitted raw low-cased class stubs (`C.foreign_key("user_id", "usersmodel", "id")`).
- **Root Cause**: Unbound string target model names (`"UserModel"`) bypassed model registry resolution and fell back to `to.lower()`.
- **New Behavior**: `_resolve_target_table()` queries model classes, metadata, and registry to resolve actual database table names (`"users"`).

---

## 3. Un-serializable Enum Default Repr Syntax Error (Critical)

- **Previous Behavior**: `default=<UserStatus.ACTIVE: 'active'>` emitted in migration DSL, causing `SyntaxError` on import.
- **Root Cause**: `_serialize_field()` stringified Enum objects when `json.dumps()` failed instead of unwrapping `.value` or calling `to_db()`.
- **New Behavior**: Unwraps Enum default instances to scalar primitives (`default='active'`).

---

## 4. Wrong Index Name Generation (High)

- **Previous Behavior**: `_auto_index_name` produced corrupted names like `idx_email_verification_t_o_k_e_n`.
- **Root Cause**: `_auto_index_name` joined character-split arrays (`"_".join(['t', 'o', 'k', 'e', 'n'])`).
- **New Behavior**: Uses normalized column lists, producing `idx_email_verification_token`.

---

## 5. Index Column Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: `Index(fields=["user"])` produced `columns=['user']` instead of `columns=['user_id']`.
- **Root Cause**: Generator serialized model attribute names directly without mapping through descriptor column names.
- **New Behavior**: `_resolve_db_column_name()` maps model attributes to database column names (`"user"` $\rightarrow$ `"user_id"`).

---

## 6. Unique Constraint Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: `UniqueConstraint(fields=["user", "role"])` produced `UNIQUE ("user", "role")`.
- **Root Cause**: Constraint fields were not resolved to underlying database column names.
- **New Behavior**: Maps constraint fields to database column names, producing `UNIQUE ("user_id", "role")`.

---

## 7. Foreign Key Column Type Inference Inconsistency (High)

- **Previous Behavior**: Foreign key column types defaulted to `"INTEGER"` on some models and `"VARCHAR(36)"` on others.
- **Root Cause**: `_field_to_sql_type()` failed to inspect target model primary key types for string references.
- **New Behavior**: Dynamically resolves target model primary key types (`"VARCHAR(36)"`), ensuring type consistency across models.

---

## 8. Table Naming Inconsistency Across Model References (High)

- **Previous Behavior**: String reference targets were inconsistently resolved depending on model declaration order.
- **Root Cause**: Lack of unified target table resolution pipeline.
- **New Behavior**: Unified target table resolution pipeline guarantees consistent table names regardless of declaration order.

---

## 9. Missing Foreign Key Metadata (Medium)

- **Previous Behavior**: `on_delete`, `on_update`, and `null=True` were omitted from generated DSL foreign key calls.
- **Root Cause**: Generator omitted default options from rendered `C.foreign_key()` argument strings.
- **New Behavior**: `_render_column_def()` renders all non-default foreign key metadata.

---

## 10. Reverse Relation Metadata Leakage in DDL (Medium)

- **Previous Behavior**: Reverse relation descriptors populated metadata into snapshot field maps.
- **Root Cause**: Descriptor scanning did not filter out virtual relation properties.
- **New Behavior**: Virtual relation properties are handled cleanly without polluting DDL operation definitions.

---

## 11. Field Options & Timestamp Metadata Loss (Medium)

- **Previous Behavior**: `auto_now` and `auto_now_add` flags were omitted from snapshot metadata.
- **Root Cause**: `_serialize_field()` did not record timestamp flags.
- **New Behavior**: Captures timestamp metadata cleanly in snapshot definitions.

---

## 12. Case-Insensitive Unique Constraint DDL Generation (Medium)

- **Previous Behavior**: Case-insensitive fields emitted broken constraint DDL.
- **Root Cause**: `CIEmailField` expression unique constraints were formatted without parenthesis escaping.
- **New Behavior**: Properly compiles schema expressions for case-insensitive unique constraints.

---

## 13. Redundant Column-Level Uniqueness (Medium)

- **Previous Behavior**: Fields with table-level unique constraints also emitted `unique=True` on column definitions.
- **Root Cause**: Generator did not check table-level constraint duplicates.
- **New Behavior**: Suppresses redundant column-level `unique=True` when expression-based unique constraints exist.

---

## 14. Arbitrary Model Dependency Creation Ordering (Critical)

- **Previous Behavior**: `CreateModel` operations were emitted in alphabetical order, causing foreign key creation crashes.
- **Root Cause**: Added models list was iterated without topological dependency analysis.
- **New Behavior**: `_topologically_sort_models()` sorts `CreateModel` operations dependency-first.

---

## 15. Migration Revision Dependency Metadata Omission (Medium)

- **Previous Behavior**: `Meta.dependencies` was omitted from generated migration source text.
- **Root Cause**: Generator did not collect previous migration revision IDs.
- **New Behavior**: Scans `migrations_dir` and includes `dependencies = ['<prev_rev>']` in `Meta`.

---

## 16. State Operation Support (Low)

- **Previous Behavior**: Migration DSL did not support custom SQL state operations cleanly.
- **Root Cause**: Lack of `RunSQL` operation rendering.
- **New Behavior**: Full support for `RunSQL` rendering and execution.

---

## 17. Field Options Preservation (Low)

- **Previous Behavior**: Options like `max_digits` and `decimal_places` were lost during snapshot roundtripping.
- **Root Cause**: Missing parameter serialization in `_serialize_field()`.
- **New Behavior**: Preserves all field parameters cleanly.

---

## 18. Nullable Foreign Key Definition Rendering (Low)

- **Previous Behavior**: Nullable foreign keys emitted `null=False` in rendered DSL column definitions.
- **Root Cause**: `nullable` property was not passed to `C.foreign_key()`.
- **New Behavior**: Emits `C.foreign_key(..., null=True)` when `nullable=True`.

---

## 19. Postgres Index Abstraction Support (Low)

- **Previous Behavior**: Custom Postgres index variants (`GinIndex`, `GistIndex`) dropped `condition` or `opclasses`.
- **Root Cause**: Generator omitted index options in snapshot dict.
- **New Behavior**: Preserves condition and operator class overrides in index snapshot metadata.
