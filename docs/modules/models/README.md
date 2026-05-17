# models Module

## Purpose

Pure Python async ORM and model compiler. Use this module for model declarations, fields, query expressions, migrations, schema snapshots, signals, transactions, aggregates, relationships, and startup checks.

## Source Coverage

- Python files: 33
- Public classes: 222
- Dataclasses: 27
- Enums: 4
- Public functions: 23

## How It Fits In Aquilia

1. Declare Model subclasses with field objects.
2. Bind a database through ModelRegistry or runtime startup.
3. Use objects.create, objects.filter, objects.get, query expressions, migrations, and transactions for async data access.

## Practical Guidance

- The manifest-level DatabaseConfig is deprecated and ignored at runtime. Configure the database at workspace or integration level.
- Model definitions are import-time registry participants, so keep model modules side-effect light.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `Aggregate` | `aquilia/models/aggregate.py` | Base class for aggregate functions. |
| `Sum` | `aquilia/models/aggregate.py` | SQL SUM() aggregate. |
| `Avg` | `aquilia/models/aggregate.py` | SQL AVG() aggregate. |
| `Count` | `aquilia/models/aggregate.py` | SQL COUNT() aggregate. |
| `Max` | `aquilia/models/aggregate.py` | SQL MAX() aggregate. |
| `Min` | `aquilia/models/aggregate.py` | SQL MIN() aggregate. |
| `StdDev` | `aquilia/models/aggregate.py` | SQL STDDEV() aggregate (PostgreSQL) / stdev (SQLite extension). |
| `Variance` | `aquilia/models/aggregate.py` | SQL VARIANCE() aggregate. |
| `ArrayAgg` | `aquilia/models/aggregate.py` | PostgreSQL ARRAY_AGG() -- collect values into an array. |
| `StringAgg` | `aquilia/models/aggregate.py` | PostgreSQL STRING_AGG() -- concatenate strings with a delimiter. |
| `GroupConcat` | `aquilia/models/aggregate.py` | MySQL/SQLite GROUP_CONCAT() aggregate. |
| `BoolAnd` | `aquilia/models/aggregate.py` | PostgreSQL BOOL_AND() -- returns true if ALL values are true. |
| `BoolOr` | `aquilia/models/aggregate.py` | PostgreSQL BOOL_OR() -- returns true if ANY value is true. |
| `FieldType` | `aquilia/models/ast_nodes.py` | Built-in AMDL field types. |
| `LinkKind` | `aquilia/models/ast_nodes.py` | Relationship cardinality. |
| `SlotNode` | `aquilia/models/ast_nodes.py` | Represents a `slot` directive -- a model field/column. |
| `LinkNode` | `aquilia/models/ast_nodes.py` | Represents a `link` directive -- a relationship. |
| `IndexNode` | `aquilia/models/ast_nodes.py` | Represents an `index` directive. |
| `HookNode` | `aquilia/models/ast_nodes.py` | Represents a `hook` directive -- lifecycle binding. |
| `MetaNode` | `aquilia/models/ast_nodes.py` | Represents a `meta` directive. |
| `NoteNode` | `aquilia/models/ast_nodes.py` | Represents a `note` directive -- freeform documentation. |
| `ModelNode` | `aquilia/models/ast_nodes.py` | Represents a complete MODEL stanza. |
| `AMDLFile` | `aquilia/models/ast_nodes.py` | Represents a parsed `.amdl` file containing one or more models. |
| `ModelRegistry` | `aquilia/models/base.py` | Backward-compatible wrapper around registry.ModelRegistry. |
| `Model` | `aquilia/models/base.py` | Aquilia Model base class -- pure Python, async-first ORM. |
| `Deferrable` | `aquilia/models/constraint.py` | Constraint deferral modes for PostgreSQL. |
| `CheckConstraint` | `aquilia/models/constraint.py` | SQL CHECK constraint. |
| `ExclusionConstraint` | `aquilia/models/constraint.py` | PostgreSQL EXCLUDE constraint. |
| `OnDeleteHandler` | `aquilia/models/deletion.py` | Callable that implements on_delete behavior at the application level. |
| `SET` | `aquilia/models/deletion.py` | Factory for SET(value) / SET(callable) on_delete behavior. |
| `ProtectedError` | `aquilia/models/deletion.py` | Raised when trying to delete a protected object. |
| `RestrictedError` | `aquilia/models/deletion.py` | Raised when trying to delete a restricted object. |
| `TextChoices` | `aquilia/models/enums.py` | String-valued choices enum. |
| `IntegerChoices` | `aquilia/models/enums.py` | Integer-valued choices enum. |
| `Combinable` | `aquilia/models/expression.py` | Base class providing arithmetic operators for expressions. |
| `Expression` | `aquilia/models/expression.py` | Base class for all SQL expressions. |
| `OrderBy` | `aquilia/models/expression.py` | Ordering directive -- wraps an expression with ASC/DESC. |
| `F` | `aquilia/models/expression.py` | Reference to a model field in an expression context. |
| `Value` | `aquilia/models/expression.py` | Wraps a literal Python value as an SQL expression. |
| `RawSQL` | `aquilia/models/expression.py` | Raw SQL expression -- use with caution. |
| `Col` | `aquilia/models/expression.py` | Reference to a specific table.column in a multi-table query. |
| `Star` | `aquilia/models/expression.py` | Represents * (all columns). |
| `CombinedExpression` | `aquilia/models/expression.py` | Represents two expressions combined with an operator. |
| `When` | `aquilia/models/expression.py` | Conditional WHEN clause for use inside Case(). |
| `Case` | `aquilia/models/expression.py` | SQL CASE expression. |
| `Subquery` | `aquilia/models/expression.py` | Wraps a query builder as a subquery expression. |
| `Exists` | `aquilia/models/expression.py` | SQL EXISTS() expression. |
| `OuterRef` | `aquilia/models/expression.py` | Reference to a field from the outer query (for use in Subquery/Exists). |
| `ExpressionWrapper` | `aquilia/models/expression.py` | Wraps an expression with an explicit output type. |
| `Func` | `aquilia/models/expression.py` | Generic SQL function call. |
| `Cast` | `aquilia/models/expression.py` | SQL CAST() expression. |
| `Coalesce` | `aquilia/models/expression.py` | SQL COALESCE() -- returns first non-NULL argument. |
| `Greatest` | `aquilia/models/expression.py` | SQL GREATEST() (MAX on SQLite) -- returns largest argument. |
| `Least` | `aquilia/models/expression.py` | SQL LEAST() (MIN on SQLite) -- returns smallest argument. |
| `NullIf` | `aquilia/models/expression.py` | SQL NULLIF() -- returns NULL if expression1 equals expression2. |
| `Length` | `aquilia/models/expression.py` | SQL LENGTH() -- return string length. |
| `Upper` | `aquilia/models/expression.py` | SQL UPPER() -- convert to uppercase. |
| `Lower` | `aquilia/models/expression.py` | SQL LOWER() -- convert to lowercase. |
| `Trim` | `aquilia/models/expression.py` | SQL TRIM() -- remove leading and trailing whitespace. |
| `LTrim` | `aquilia/models/expression.py` | SQL LTRIM() -- remove leading whitespace. |
| `RTrim` | `aquilia/models/expression.py` | SQL RTRIM() -- remove trailing whitespace. |
| `Concat` | `aquilia/models/expression.py` | SQL concatenation -- dialect-aware (|| for SQLite/PG, CONCAT for MySQL). |
| `Left` | `aquilia/models/expression.py` | SQL LEFT() / SUBSTR() -- extract leftmost characters. |
| `Right` | `aquilia/models/expression.py` | SQL RIGHT() / SUBSTR() -- extract rightmost characters. |
| `Substr` | `aquilia/models/expression.py` | SQL SUBSTR() -- extract substring. |
| `Replace` | `aquilia/models/expression.py` | SQL REPLACE() -- replace occurrences in a string. |
| `Abs` | `aquilia/models/expression.py` | SQL ABS() -- absolute value. |
| `Round` | `aquilia/models/expression.py` | SQL ROUND() -- round to specified decimal places. |
| `Power` | `aquilia/models/expression.py` | SQL POWER() -- raise to a power. |
| `Now` | `aquilia/models/expression.py` | SQL current timestamp -- dialect-aware. |
| `FieldValidationError` | `aquilia/models/fields_module.py` | Raised when field validation fails. |
| `Field` | `aquilia/models/fields_module.py` | Base field descriptor -- all Aquilia fields inherit from this. |
| `AutoField` | `aquilia/models/fields_module.py` | Auto-incrementing integer primary key (32-bit). |
| `BigAutoField` | `aquilia/models/fields_module.py` | Auto-incrementing 64-bit integer primary key. |
| `SmallAutoField` | `aquilia/models/fields_module.py` | Auto-incrementing 16-bit integer primary key. |
| `IntegerField` | `aquilia/models/fields_module.py` | Standard 32-bit integer field. |
| `BigIntegerField` | `aquilia/models/fields_module.py` | 64-bit integer field. |
| `SmallIntegerField` | `aquilia/models/fields_module.py` | 16-bit integer field (-32768 to 32767). |
| `PositiveIntegerField` | `aquilia/models/fields_module.py` | Positive 32-bit integer field (0 to 2147483647). |
| `PositiveSmallIntegerField` | `aquilia/models/fields_module.py` | Positive 16-bit integer field (0 to 32767). |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `normalize_on_delete` | `aquilia/models/deletion.py` | Normalize an on_delete value to its canonical constant. |
| `raw_sql_to_operations` | `aquilia/models/migration_dsl.py` | Convert raw SQL strings into a list of RunSQL operations. |
| `generate_dsl_migration` | `aquilia/models/migration_gen.py` | Generate a DSL migration file from the diff between the current |
| `check_db_exists` | `aquilia/models/migration_runner.py` | Check if a SQLite database file exists WITHOUT creating WAL/SHM files. |
| `check_migrations_applied` | `aquilia/models/migration_runner.py` | Check if there are unapplied migrations WITHOUT creating WAL/SHM. |
| `generate_migration_file` | `aquilia/models/migrations.py` | Generate a migration file from AMDL model nodes. |
| `generate_migration_from_models` | `aquilia/models/migrations.py` | Generate a migration file from new Python Model subclasses. |
| `parse_amdl` | `aquilia/models/parser.py` | Parse AMDL source text into an AMDLFile. |
| `parse_amdl_file` | `aquilia/models/parser.py` | Parse an `.amdl` file from disk. |
| `parse_amdl_directory` | `aquilia/models/parser.py` | Parse all `.amdl` files in a directory (non-recursive). |
| `generate_create_table_sql` | `aquilia/models/runtime.py` | Generate CREATE TABLE SQL from a ModelNode. |
| `generate_create_index_sql` | `aquilia/models/runtime.py` | Generate CREATE INDEX statements for non-unique indexes. |
| `create_snapshot` | `aquilia/models/schema_snapshot.py` | Create a schema snapshot from a list of Model subclasses. |
| `save_snapshot` | `aquilia/models/schema_snapshot.py` | Write snapshot to file in CROUS binary format. |
| `load_snapshot` | `aquilia/models/schema_snapshot.py` | Load snapshot from file in CROUS binary format. |
| `compute_diff` | `aquilia/models/schema_snapshot.py` | Compute the diff between two schema snapshots. |
| `diff_to_operations` | `aquilia/models/schema_snapshot.py` | Convert a SchemaDiff into a list of DSL operations. |
| `receiver` | `aquilia/models/signals.py` | Shorthand decorator to connect a function to a signal. |
| `check_db_ready` | `aquilia/models/startup_guard.py` | Check if the database is ready for the application to start. |
| `atomic` | `aquilia/models/transactions.py` | Create an atomic transaction context manager. |
| `lookup_registry` | `aquilia/models/fields/lookups.py` | Return a copy of the lookup registry. |
| `register_lookup` | `aquilia/models/fields/lookups.py` | Register a custom lookup type. |
| `resolve_lookup` | `aquilia/models/fields/lookups.py` | Resolve a lookup name to a Lookup instance. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/models/__init__.py` | Aquilia Model System -- Pure Python, production-grade ORM. |
| `aquilia/models/__init__old.py` | Aquilia Model System -- AMDL-based, async-first models. |
| `aquilia/models/aggregate.py` | Aquilia Aggregates -- Sum, Avg, Count, Max, Min for QuerySet. |
| `aquilia/models/ast_nodes.py` | AMDL AST Node Types -- Aquilia Model Definition Language. |
| `aquilia/models/base.py` | Aquilia Model Base -- Pure Python, metaclass-driven, async-first ORM. |
| `aquilia/models/constraint.py` | Aquilia Model Constraints -- CheckConstraint, ExclusionConstraint. |
| `aquilia/models/deletion.py` | Aquilia Model Deletion -- on_delete behaviors for ForeignKey fields. |
| `aquilia/models/enums.py` | Aquilia Model Enums -- standard enum helpers for model fields. |
| `aquilia/models/expression.py` | Aquilia Expression System -- F(), Value(), RawSQL() for query expressions. |
| `aquilia/models/fields/__init__.py` | Aquilia Model Fields Package -- split-module field system. |
| `aquilia/models/fields/composite.py` | Aquilia Composite Fields -- group multiple primitives into one logical attribute. |
| `aquilia/models/fields/enum_field.py` | Aquilia EnumField -- store Python enums with database mapping. |
| `aquilia/models/fields/lookups.py` | Aquilia Field Lookups -- extensible lookup system for query filters. |
| `aquilia/models/fields/mixins.py` | Aquilia Field Mixins -- reusable behaviors for model fields. |
| `aquilia/models/fields/validators.py` | Aquilia Field Validators -- reusable validation callables. |
| `aquilia/models/fields_module.py` | Aquilia Model Fields -- Pure Python, production-grade field system. |
| `aquilia/models/index.py` | Aquilia Model Indexes -- standalone index rendering. |
| `aquilia/models/manager.py` | Aquilia Model Manager -- descriptor-based QuerySet access. |
| `aquilia/models/metaclass.py` | Aquilia Model Metaclass -- field collection, auto-PK, Meta parsing, registration. |
| `aquilia/models/migration_dsl.py` | Aquilia Migration DSL -- declarative, human-readable migration operations. |
| `aquilia/models/migration_gen.py` | Aquilia Migration File Generator -- creates DSL migration files. |
| `aquilia/models/migration_runner.py` | Aquilia Migration Runner -- executes DSL and raw-SQL migrations. |
| `aquilia/models/migrations.py` | Aquilia Migration System -- generate and apply schema migrations. |
| `aquilia/models/options.py` | Aquilia Model Options -- parsed from inner Meta class. |
| `aquilia/models/parser.py` | AMDL Parser -- Aquilia Model Definition Language. |
| `aquilia/models/query.py` | Aquilia Query Builder -- chainable, immutable, async-terminal Q object. |
| `aquilia/models/registry.py` | Aquilia Model Registry -- global registry for all Model subclasses. |
| `aquilia/models/runtime.py` | Aquilia Model Runtime -- ModelProxy, Q (query), and ModelRegistry. |
| `aquilia/models/schema_snapshot.py` | Aquilia Schema Snapshot & Diff Engine. |
| `aquilia/models/signals.py` | Aquilia Model Signals -- pre/post save, delete, init hooks. |
| `aquilia/models/sql_builder.py` | Aquilia SQL Builder -- safe, parameterized SQL generation. |
| `aquilia/models/startup_guard.py` | Aquilia Safe DB Startup -- guards against implicit database creation. |
| `aquilia/models/transactions.py` | Aquilia Transactions -- atomic() context manager with savepoint support. |

## Testing Pointers

Search `tests/` for `models` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
