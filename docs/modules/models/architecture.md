# Models Architecture

Pure-Python async ORM, fields, query builder, managers, SQL builders, migrations, schema snapshots, legacy AMDL parser/runtime, and transactions.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`models` has 33 Python files, 222 public classes, 23 public module-level functions, and 65 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 8 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.migration_dsl` | 17 |
| `..faults.domains` | 8 |
| `.ast_nodes` | 5 |
| `.runtime` | 5 |
| `..db.engine` | 3 |
| `..fields_module` | 3 |
| `.fields_module` | 3 |
| `.manager` | 3 |
| `.options` | 3 |
| `.query` | 3 |
| `.signals` | 3 |
| `.sql_builder` | 3 |
| `.constraint` | 2 |
| `.deletion` | 2 |
| `.expression` | 2 |
| `.migration_runner` | 2 |
| `.migrations` | 2 |
| `.parser` | 2 |
| `.registry` | 2 |
| `.schema_snapshot` | 2 |
| `..di.decorators` | 1 |
| `..models.fields_module` | 1 |
| `.aggregate` | 1 |
| `.base` | 1 |
| `.composite` | 1 |
| `.enum_field` | 1 |
| `.enums` | 1 |
| `.fields` | 1 |
| `.fields.lookups` | 1 |
| `.index` | 1 |
| `.lookups` | 1 |
| `.metaclass` | 1 |
| `.migration_gen` | 1 |
| `.mixins` | 1 |
| `.startup_guard` | 1 |
| `.transactions` | 1 |
| `.validators` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 30 |
| `typing` | 28 |
| `logging` | 12 |
| `collections` | 10 |
| `re` | 8 |
| `pathlib` | 6 |
| `dataclasses` | 5 |
| `datetime` | 5 |
| `hashlib` | 5 |
| `warnings` | 5 |
| `json` | 4 |
| `os` | 4 |
| `uuid` | 4 |
| `contextlib` | 3 |
| `decimal` | 3 |
| `enum` | 3 |
| `inspect` | 3 |
| `weakref` | 2 |
| `asyncio` | 1 |
| `base64` | 1 |
| `copy` | 1 |
| `difflib` | 1 |
| `importlib` | 1 |
| `ipaddress` | 1 |
| `struct` | 1 |
| `sys` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `HookNode` | `aquilia/models/ast_nodes.py` | Represents a `hook` directive -- lifecycle binding. |
| `ModelRegistry` | `aquilia/models/base.py` | Backward-compatible wrapper around registry.ModelRegistry. |
| `HStoreField` | `aquilia/models/fields_module.py` | PostgreSQL hstore field (key-value pairs). |
| `BaseManager` | `aquilia/models/manager.py` | Base manager with Python descriptor protocol. |
| `Manager` | `aquilia/models/manager.py` | Default manager -- auto-attached as ``objects`` on every Model. |
| `ModelRegistry` | `aquilia/models/registry.py` | Global registry for all Model subclasses. |
| `ModelRegistry` | `aquilia/models/runtime.py` | Central registry for AMDL models and their runtime proxies. |
| `TransactionManager` | `aquilia/models/transactions.py` | Higher-level transaction manager with properly scoped on_commit hooks. |

## Error Handling

Fault/error classes defined here:

`ProtectedError`, `RestrictedError`, `ValidationError`, `FieldValidationError`, `AMDLParseError`, `DatabaseNotReadyError`
