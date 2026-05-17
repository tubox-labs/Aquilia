# Models Troubleshooting

Pure-Python async ORM, fields, query builder, managers, SQL builders, migrations, schema snapshots, legacy AMDL parser/runtime, and transactions.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq db makemigrations`
- `aq db migrate`
- `aq db dump`
- `aq db shell`
- `aq db inspectdb`
- `aq db showmigrations`
- `aq db sqlmigrate`
- `aq db status`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
