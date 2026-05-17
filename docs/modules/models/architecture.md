# Models And ORM Architecture

## Runtime Role

The Python-native async ORM with fields, query builder, managers, migrations, schema snapshots, relationships, constraints, signals, transactions, expressions, and aggregate support.

The implementation is split across 33 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/models/__init__.py`: Aquilia Model System -- Pure Python, production-grade ORM.
- `aquilia/models/__init__old.py`: Aquilia Model System -- AMDL-based, async-first models.
- `aquilia/models/aggregate.py`: Aquilia Aggregates -- Sum, Avg, Count, Max, Min for QuerySet.
- `aquilia/models/ast_nodes.py`: AMDL AST Node Types -- Aquilia Model Definition Language.
- `aquilia/models/base.py`: Aquilia Model Base -- Pure Python, metaclass-driven, async-first ORM.
- `aquilia/models/constraint.py`: Aquilia Model Constraints -- CheckConstraint, ExclusionConstraint.
- `aquilia/models/deletion.py`: Aquilia Model Deletion -- on_delete behaviors for ForeignKey fields.
- `aquilia/models/enums.py`: Aquilia Model Enums -- standard enum helpers for model fields.
- `aquilia/models/expression.py`: Aquilia Expression System -- F(), Value(), RawSQL() for query expressions.
- `aquilia/models/fields/__init__.py`: Aquilia Model Fields Package -- split-module field system.
- `aquilia/models/fields/composite.py`: Aquilia Composite Fields -- group multiple primitives into one logical attribute.
- `aquilia/models/fields/enum_field.py`: Aquilia EnumField -- store Python enums with database mapping.
- `aquilia/models/fields/lookups.py`: Aquilia Field Lookups -- extensible lookup system for query filters.
- `aquilia/models/fields/mixins.py`: Aquilia Field Mixins -- reusable behaviors for model fields.
- `aquilia/models/fields/validators.py`: Aquilia Field Validators -- reusable validation callables.
- `aquilia/models/fields_module.py`: Aquilia Model Fields -- Pure Python, production-grade field system.
- `aquilia/models/index.py`: Aquilia Model Indexes -- standalone index rendering.
- `aquilia/models/manager.py`: Aquilia Model Manager -- descriptor-based QuerySet access.
- `aquilia/models/metaclass.py`: Aquilia Model Metaclass -- field collection, auto-PK, Meta parsing, registration.
- `aquilia/models/migration_dsl.py`: Aquilia Migration DSL -- declarative, human-readable migration operations.
- `aquilia/models/migration_gen.py`: Aquilia Migration File Generator -- creates DSL migration files.
- `aquilia/models/migration_runner.py`: Aquilia Migration Runner -- executes DSL and raw-SQL migrations.
- `aquilia/models/migrations.py`: Aquilia Migration System -- generate and apply schema migrations.
- `aquilia/models/options.py`: Aquilia Model Options -- parsed from inner Meta class.
- `aquilia/models/parser.py`: AMDL Parser -- Aquilia Model Definition Language.
- `aquilia/models/query.py`: Aquilia Query Builder -- chainable, immutable, async-terminal Q object.
- `aquilia/models/registry.py`: Aquilia Model Registry -- global registry for all Model subclasses.
- `aquilia/models/runtime.py`: Aquilia Model Runtime -- ModelProxy, Q (query), and ModelRegistry.
- `aquilia/models/schema_snapshot.py`: Aquilia Schema Snapshot & Diff Engine.
- `aquilia/models/signals.py`: Aquilia Model Signals -- pre/post save, delete, init hooks.
- `aquilia/models/sql_builder.py`: Aquilia SQL Builder -- safe, parameterized SQL generation.
- `aquilia/models/startup_guard.py`: Aquilia Safe DB Startup -- guards against implicit database creation.
- `aquilia/models/transactions.py`: Aquilia Transactions -- atomic() context manager with savepoint support.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 30 |
| `typing` | 28 |
| `logging` | 12 |
| `collections` | 10 |
| `faults` | 8 |
| `re` | 8 |
| `fields_module` | 6 |
| `pathlib` | 6 |
| `ast_nodes` | 5 |
| `dataclasses` | 5 |
| `datetime` | 5 |
| `hashlib` | 5 |
| `warnings` | 5 |
| `json` | 4 |
| `migration_dsl` | 4 |
| `os` | 4 |
| `uuid` | 4 |
| `contextlib` | 3 |
| `db` | 3 |
| `decimal` | 3 |
| `enum` | 3 |
| `inspect` | 3 |
| `manager` | 3 |
| `options` | 3 |
| `runtime` | 3 |
| `signals` | 3 |
| `sql_builder` | 3 |
| `constraint` | 2 |
| `deletion` | 2 |
| `expression` | 2 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
