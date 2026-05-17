# Models And ORM Documentation

This directory is the professional documentation set for `models`. It is implementation-driven and aligned with the current source files under `aquilia/models`.

## What This Covers

The Python-native async ORM with fields, query builder, managers, migrations, schema snapshots, relationships, constraints, signals, transactions, expressions, and aggregate support.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 33
- Public classes: 222
- Configuration or dataclass-like types: 28
- Public functions: 23
- Constants detected: 43

## Fast Start

```python
from aquilia.models import Model
from aquilia.models.fields import BooleanField, CharField, DateTimeField

class User(Model):
    table = "users"
    email = CharField(max_length=255, unique=True)
    name = CharField(max_length=150)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

user = await User.objects.create(email="ada@example.com", name="Ada")
active_users = await User.objects.filter(active=True).all()
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
