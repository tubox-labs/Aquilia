# Models Configuration

Pure-Python async ORM, fields, query builder, managers, SQL builders, migrations, schema snapshots, legacy AMDL parser/runtime, and transactions.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/models/__init__.py` | 611 | 0 | 0 | Aquilia Model System -- Pure Python, production-grade ORM. |
| `aquilia/models/__init__old.py` | 113 | 0 | 0 | Aquilia Model System -- AMDL-based, async-first models. |
| `aquilia/models/aggregate.py` | 308 | 13 | 0 | Aquilia Aggregates -- Sum, Avg, Count, Max, Min for QuerySet. |
| `aquilia/models/ast_nodes.py` | 234 | 10 | 0 | AMDL AST Node Types -- Aquilia Model Definition Language. |
| `aquilia/models/base.py` | 1696 | 2 | 0 | Aquilia Model Base -- Pure Python, metaclass-driven, async-first ORM. |
| `aquilia/models/constraint.py` | 169 | 3 | 0 | Aquilia Model Constraints -- CheckConstraint, ExclusionConstraint. |
| `aquilia/models/deletion.py` | 288 | 4 | 1 | Aquilia Model Deletion -- on_delete behaviors for ForeignKey fields. |
| `aquilia/models/enums.py` | 116 | 2 | 0 | Aquilia Model Enums -- standard enum helpers for model fields. |
| `aquilia/models/expression.py` | 1001 | 36 | 0 | Aquilia Expression System -- F(), Value(), RawSQL() for query expressions. |
| `aquilia/models/fields/__init__.py` | 260 | 0 | 0 | Aquilia Model Fields Package -- split-module field system. |
| `aquilia/models/fields/composite.py` | 214 | 3 | 0 | Aquilia Composite Fields -- group multiple primitives into one logical attribute. |
| `aquilia/models/fields/enum_field.py` | 120 | 1 | 0 | Aquilia EnumField -- store Python enums with database mapping. |
| `aquilia/models/fields/lookups.py` | 338 | 22 | 3 | Aquilia Field Lookups -- extensible lookup system for query filters. |
| `aquilia/models/fields/mixins.py` | 418 | 6 | 0 | Aquilia Field Mixins -- reusable behaviors for model fields. |
| `aquilia/models/fields/validators.py` | 421 | 16 | 0 | Aquilia Field Validators -- reusable validation callables. |
| `aquilia/models/fields_module.py` | 2335 | 51 | 0 | Aquilia Model Fields -- Pure Python, production-grade field system. |
| `aquilia/models/index.py` | 156 | 5 | 0 | Aquilia Model Indexes -- standalone index rendering. |
| `aquilia/models/manager.py` | 520 | 3 | 0 | Aquilia Model Manager -- descriptor-based QuerySet access. |
| `aquilia/models/metaclass.py` | 150 | 1 | 0 | Aquilia Model Metaclass -- field collection, auto-PK, Meta parsing, registration. |
| `aquilia/models/migration_dsl.py` | 848 | 16 | 1 | Aquilia Migration DSL -- declarative, human-readable migration operations. |
| `aquilia/models/migration_gen.py` | 324 | 0 | 1 | Aquilia Migration File Generator -- creates DSL migration files. |
| `aquilia/models/migration_runner.py` | 561 | 2 | 2 | Aquilia Migration Runner -- executes DSL and raw-SQL migrations. |
| `aquilia/models/migrations.py` | 988 | 3 | 2 | Aquilia Migration System -- generate and apply schema migrations. |
| `aquilia/models/options.py` | 136 | 1 | 0 | Aquilia Model Options -- parsed from inner Meta class. |
| `aquilia/models/parser.py` | 406 | 1 | 3 | AMDL Parser -- Aquilia Model Definition Language. |
| `aquilia/models/query.py` | 1730 | 3 | 0 | Aquilia Query Builder -- chainable, immutable, async-terminal Q object. |
| `aquilia/models/registry.py` | 277 | 1 | 0 | Aquilia Model Registry -- global registry for all Model subclasses. |
| `aquilia/models/runtime.py` | 922 | 3 | 2 | Aquilia Model Runtime -- ModelProxy, Q (query), and ModelRegistry. |
| `aquilia/models/schema_snapshot.py` | 723 | 2 | 5 | Aquilia Schema Snapshot & Diff Engine. |
| `aquilia/models/signals.py` | 361 | 1 | 1 | Aquilia Model Signals -- pre/post save, delete, init hooks. |
| `aquilia/models/sql_builder.py` | 590 | 8 | 0 | Aquilia SQL Builder -- safe, parameterized SQL generation. |
| `aquilia/models/startup_guard.py` | 142 | 1 | 1 | Aquilia Safe DB Startup -- guards against implicit database creation. |
| `aquilia/models/transactions.py` | 369 | 2 | 1 | Aquilia Transactions -- atomic() context manager with savepoint support. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `Options` | `aquilia/models/options.py` | `label`, `label_lower` | Parsed model options from inner Meta class. |
| `SQLBuilder` | `aquilia/models/sql_builder.py` | `select`, `from_table`, `distinct`, `join`, `left_join`, `right_join`, `where`, `where_in`, `group_by`, `having`, `order_by`, `limit`, `offset`, `build`, `build_count` | SELECT query builder with safe parameter binding. |
| `InsertBuilder` | `aquilia/models/sql_builder.py` | `columns`, `values`, `from_dict`, `returning`, `build`, `build_many` | INSERT query builder. |
| `UpdateBuilder` | `aquilia/models/sql_builder.py` | `set`, `set_dict`, `where`, `build` | UPDATE query builder. |
| `DeleteBuilder` | `aquilia/models/sql_builder.py` | `where`, `build` | DELETE query builder. |
| `CreateTableBuilder` | `aquilia/models/sql_builder.py` | `column`, `constraint`, `build` | CREATE TABLE DDL builder. |
| `AlterTableBuilder` | `aquilia/models/sql_builder.py` | `add_column`, `drop_column`, `rename_column`, `rename_to`, `add_constraint`, `drop_constraint`, `alter_column_type`, `set_not_null`, `drop_not_null`, `set_default`, `drop_default`, `build` | ALTER TABLE DDL builder -- dialect-aware. |
| `UpsertBuilder` | `aquilia/models/sql_builder.py` | `columns`, `values`, `from_dict`, `conflict_target`, `update_columns`, `build` | INSERT ... ON CONFLICT (upsert) query builder -- dialect-aware. |
| `UpsertIgnoreBuilder` | `aquilia/models/sql_builder.py` | `columns`, `values`, `from_dict`, `conflict_target`, `build` | INSERT ... ON CONFLICT DO NOTHING query builder -- dialect-aware. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
