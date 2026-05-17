# Models And ORM Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `ProtectedError` | `aquilia/models/deletion.py` | Raised when trying to delete a protected object. |
| `RestrictedError` | `aquilia/models/deletion.py` | Raised when trying to delete a restricted object. |
| `ValidationError` | `aquilia/models/fields/validators.py` | Raised by validators when a value fails validation. |
| `FieldValidationError` | `aquilia/models/fields_module.py` | Raised when field validation fails. |
| `AMDLParseError` | `aquilia/models/parser.py` | Raised when AMDL parsing fails. |
| `DatabaseNotReadyError` | `aquilia/models/startup_guard.py` | Raised when the database is not ready at server startup. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
