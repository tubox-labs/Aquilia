# Models And ORM API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `Aggregate` | `aquilia/models/aggregate.py` | Expression | Base class for aggregate functions. |
| `Sum` | `aquilia/models/aggregate.py` | Aggregate | SQL SUM() aggregate. |
| `Avg` | `aquilia/models/aggregate.py` | Aggregate | SQL AVG() aggregate. |
| `Count` | `aquilia/models/aggregate.py` | Aggregate | SQL COUNT() aggregate. |
| `Max` | `aquilia/models/aggregate.py` | Aggregate | SQL MAX() aggregate. |
| `Min` | `aquilia/models/aggregate.py` | Aggregate | SQL MIN() aggregate. |
| `StdDev` | `aquilia/models/aggregate.py` | Aggregate | SQL STDDEV() aggregate (PostgreSQL) / stdev (SQLite extension). |
| `Variance` | `aquilia/models/aggregate.py` | Aggregate | SQL VARIANCE() aggregate. |
| `ArrayAgg` | `aquilia/models/aggregate.py` | Aggregate | PostgreSQL ARRAY_AGG() -- collect values into an array. |
| `StringAgg` | `aquilia/models/aggregate.py` | Aggregate | PostgreSQL STRING_AGG() -- concatenate strings with a delimiter. |
| `GroupConcat` | `aquilia/models/aggregate.py` | Aggregate | MySQL/SQLite GROUP_CONCAT() aggregate. |
| `BoolAnd` | `aquilia/models/aggregate.py` | Aggregate | PostgreSQL BOOL_AND() -- returns true if ALL values are true. |
| `BoolOr` | `aquilia/models/aggregate.py` | Aggregate | PostgreSQL BOOL_OR() -- returns true if ANY value is true. |
| `FieldType` | `aquilia/models/ast_nodes.py` | str, Enum | Built-in AMDL field types. |
| `LinkKind` | `aquilia/models/ast_nodes.py` | str, Enum | Relationship cardinality. |
| `SlotNode` | `aquilia/models/ast_nodes.py` | object | Represents a `slot` directive -- a model field/column. |
| `LinkNode` | `aquilia/models/ast_nodes.py` | object | Represents a `link` directive -- a relationship. |
| `IndexNode` | `aquilia/models/ast_nodes.py` | object | Represents an `index` directive. |
| `HookNode` | `aquilia/models/ast_nodes.py` | object | Represents a `hook` directive -- lifecycle binding. |
| `MetaNode` | `aquilia/models/ast_nodes.py` | object | Represents a `meta` directive. |
| `NoteNode` | `aquilia/models/ast_nodes.py` | object | Represents a `note` directive -- freeform documentation. |
| `ModelNode` | `aquilia/models/ast_nodes.py` | object | Represents a complete MODEL stanza. |
| `AMDLFile` | `aquilia/models/ast_nodes.py` | object | Represents a parsed `.amdl` file containing one or more models. |
| `ModelRegistry` | `aquilia/models/base.py` | object | Backward-compatible wrapper around registry.ModelRegistry. |
| `Model` | `aquilia/models/base.py` | object | Aquilia Model base class -- pure Python, async-first ORM. |
| `Deferrable` | `aquilia/models/constraint.py` | object | Constraint deferral modes for PostgreSQL. |
| `CheckConstraint` | `aquilia/models/constraint.py` | object | SQL CHECK constraint. |
| `ExclusionConstraint` | `aquilia/models/constraint.py` | object | PostgreSQL EXCLUDE constraint. |
| `OnDeleteHandler` | `aquilia/models/deletion.py` | object | Callable that implements on_delete behavior at the application level. |
| `SET` | `aquilia/models/deletion.py` | object | Factory for SET(value) / SET(callable) on_delete behavior. |
| `ProtectedError` | `aquilia/models/deletion.py` | ProtectedDeleteFault, Exception | Raised when trying to delete a protected object. |
| `RestrictedError` | `aquilia/models/deletion.py` | RestrictedDeleteFault, Exception | Raised when trying to delete a restricted object. |
| `TextChoices` | `aquilia/models/enums.py` | str, Enum | String-valued choices enum. |
| `IntegerChoices` | `aquilia/models/enums.py` | int, Enum | Integer-valued choices enum. |
| `Combinable` | `aquilia/models/expression.py` | object | Base class providing arithmetic operators for expressions. |
| `Expression` | `aquilia/models/expression.py` | Combinable | Base class for all SQL expressions. |
| `OrderBy` | `aquilia/models/expression.py` | object | Ordering directive -- wraps an expression with ASC/DESC. |
| `F` | `aquilia/models/expression.py` | Expression | Reference to a model field in an expression context. |
| `Value` | `aquilia/models/expression.py` | Expression | Wraps a literal Python value as an SQL expression. |
| `RawSQL` | `aquilia/models/expression.py` | Expression | Raw SQL expression -- use with caution. |
| `Col` | `aquilia/models/expression.py` | Expression | Reference to a specific table.column in a multi-table query. |
| `Star` | `aquilia/models/expression.py` | Expression | Represents * (all columns). |
| `CombinedExpression` | `aquilia/models/expression.py` | Expression | Represents two expressions combined with an operator. |
| `When` | `aquilia/models/expression.py` | Expression | Conditional WHEN clause for use inside Case(). |
| `Case` | `aquilia/models/expression.py` | Expression | SQL CASE expression. |
| `Subquery` | `aquilia/models/expression.py` | Expression | Wraps a query builder as a subquery expression. |
| `Exists` | `aquilia/models/expression.py` | Expression | SQL EXISTS() expression. |
| `OuterRef` | `aquilia/models/expression.py` | F | Reference to a field from the outer query (for use in Subquery/Exists). |
| `ExpressionWrapper` | `aquilia/models/expression.py` | Expression | Wraps an expression with an explicit output type. |
| `Func` | `aquilia/models/expression.py` | Expression | Generic SQL function call. |
| `Cast` | `aquilia/models/expression.py` | Expression | SQL CAST() expression. |
| `Coalesce` | `aquilia/models/expression.py` | Func | SQL COALESCE() -- returns first non-NULL argument. |
| `Greatest` | `aquilia/models/expression.py` | Func | SQL GREATEST() (MAX on SQLite) -- returns largest argument. |
| `Least` | `aquilia/models/expression.py` | Func | SQL LEAST() (MIN on SQLite) -- returns smallest argument. |
| `NullIf` | `aquilia/models/expression.py` | Expression | SQL NULLIF() -- returns NULL if expression1 equals expression2. |
| `Length` | `aquilia/models/expression.py` | Func | SQL LENGTH() -- return string length. |
| `Upper` | `aquilia/models/expression.py` | Func | SQL UPPER() -- convert to uppercase. |
| `Lower` | `aquilia/models/expression.py` | Func | SQL LOWER() -- convert to lowercase. |
| `Trim` | `aquilia/models/expression.py` | Func | SQL TRIM() -- remove leading and trailing whitespace. |
| `LTrim` | `aquilia/models/expression.py` | Func | SQL LTRIM() -- remove leading whitespace. |
| `RTrim` | `aquilia/models/expression.py` | Func | SQL RTRIM() -- remove trailing whitespace. |
| `Concat` | `aquilia/models/expression.py` | Expression &#124; SQL concatenation -- dialect-aware ( &#124; | for SQLite/PG, CONCAT for MySQL). |
| `Left` | `aquilia/models/expression.py` | Expression | SQL LEFT() / SUBSTR() -- extract leftmost characters. |
| `Right` | `aquilia/models/expression.py` | Expression | SQL RIGHT() / SUBSTR() -- extract rightmost characters. |
| `Substr` | `aquilia/models/expression.py` | Func | SQL SUBSTR() -- extract substring. |
| `Replace` | `aquilia/models/expression.py` | Func | SQL REPLACE() -- replace occurrences in a string. |
| `Abs` | `aquilia/models/expression.py` | Func | SQL ABS() -- absolute value. |
| `Round` | `aquilia/models/expression.py` | Expression | SQL ROUND() -- round to specified decimal places. |
| `Power` | `aquilia/models/expression.py` | Expression | SQL POWER() -- raise to a power. |
| `Now` | `aquilia/models/expression.py` | Expression | SQL current timestamp -- dialect-aware. |
| `CompositeAttribute` | `aquilia/models/fields/composite.py` | object | Descriptor that provides read/write access to a group of columns |
| `CompositeField` | `aquilia/models/fields/composite.py` | Field | Groups multiple primitive fields into one logical attribute. |
| `CompositePrimaryKey` | `aquilia/models/fields/composite.py` | object | Declares a composite primary key across multiple fields. |
| `EnumField` | `aquilia/models/fields/enum_field.py` | Field | Stores a Python Enum value in the database. |
| `Lookup` | `aquilia/models/fields/lookups.py` | object | Base class for field lookups. |
| `Exact` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `IExact` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive exact match. |
| `Contains` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `IContains` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive contains. |
| `StartsWith` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `IStartsWith` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive startswith. |
| `EndsWith` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `IEndsWith` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive endswith. |
| `In` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `Gt` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `Gte` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `Lt` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `Lte` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `IsNull` | `aquilia/models/fields/lookups.py` | Lookup | Public class. |
| `Range` | `aquilia/models/fields/lookups.py` | Lookup | Filter within a range: field__range=(lo, hi). |
| `Regex` | `aquilia/models/fields/lookups.py` | Lookup | Filter by regex (PostgreSQL: ~, SQLite: REGEXP if loaded). |
| `IRegex` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive regex. |
| `Date` | `aquilia/models/fields/lookups.py` | Lookup | Extract date from datetime and compare. |
| `Year` | `aquilia/models/fields/lookups.py` | Lookup | Extract year and compare. |
| `Month` | `aquilia/models/fields/lookups.py` | Lookup | Extract month and compare. |
| `Day` | `aquilia/models/fields/lookups.py` | Lookup | Extract day and compare. |
| `NullableMixin` | `aquilia/models/fields/mixins.py` | object | Mixin that makes a field nullable with sensible defaults. |
| `UniqueMixin` | `aquilia/models/fields/mixins.py` | object | Mixin that enforces uniqueness on a field. |
| `IndexedMixin` | `aquilia/models/fields/mixins.py` | object | Mixin that auto-adds a database index to a field. |
| `AutoNowMixin` | `aquilia/models/fields/mixins.py` | object | Mixin for fields that auto-update on save (like updated_at). |
| `ChoiceMixin` | `aquilia/models/fields/mixins.py` | object | Mixin that enforces validation of choices with display values. |
| `EncryptedMixin` | `aquilia/models/fields/mixins.py` | object | Placeholder mixin for encrypted field storage. |
| `ValidationError` | `aquilia/models/fields/validators.py` | ValueError | Raised by validators when a value fails validation. |
| `BaseValidator` | `aquilia/models/fields/validators.py` | object | Base class for all validators. |
| `MinValueValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure value >= limit. |
| `MaxValueValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure value <= limit. |
| `MinLengthValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure string length >= limit. |
| `MaxLengthValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure string length <= limit. |
| `RegexValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Validate against a regex pattern. |
| `EmailValidator` | `aquilia/models/fields/validators.py` | RegexValidator | Validate email address format. |
| `URLValidator` | `aquilia/models/fields/validators.py` | RegexValidator | Validate URL format. |
| `SlugValidator` | `aquilia/models/fields/validators.py` | RegexValidator | Validate slug format (letters, numbers, hyphens, underscores). |
| `ProhibitNullCharactersValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Reject strings containing null characters. |
| `DecimalValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Validate decimal precision and scale. |
| `FileExtensionValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Validate file extension against an allowed list. |
| `StepValueValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure value is a multiple of step (from offset). |
| `RangeValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Ensure value falls within [min_val, max_val] range. |
| `UniqueForDateValidator` | `aquilia/models/fields/validators.py` | BaseValidator | Validate uniqueness for a date-based scope. |
| `FieldValidationError` | `aquilia/models/fields_module.py` | _FieldValidationFault, ValueError | Raised when field validation fails. |
| `Field` | `aquilia/models/fields_module.py` | object | Base field descriptor -- all Aquilia fields inherit from this. |
| `AutoField` | `aquilia/models/fields_module.py` | Field | Auto-incrementing integer primary key (32-bit). |
| `BigAutoField` | `aquilia/models/fields_module.py` | Field | Auto-incrementing 64-bit integer primary key. |
| `SmallAutoField` | `aquilia/models/fields_module.py` | AutoField | Auto-incrementing 16-bit integer primary key. |
| `IntegerField` | `aquilia/models/fields_module.py` | Field | Standard 32-bit integer field. |
| `BigIntegerField` | `aquilia/models/fields_module.py` | Field | 64-bit integer field. |
| `SmallIntegerField` | `aquilia/models/fields_module.py` | Field | 16-bit integer field (-32768 to 32767). |
| `PositiveIntegerField` | `aquilia/models/fields_module.py` | Field | Positive 32-bit integer field (0 to 2147483647). |
| `PositiveSmallIntegerField` | `aquilia/models/fields_module.py` | Field | Positive 16-bit integer field (0 to 32767). |
| `PositiveBigIntegerField` | `aquilia/models/fields_module.py` | Field | Positive 64-bit integer field (0 to 9223372036854775807). |
| `FloatField` | `aquilia/models/fields_module.py` | Field | Double-precision floating-point field. |
| `DecimalField` | `aquilia/models/fields_module.py` | Field | Fixed-precision decimal field. |
| `CharField` | `aquilia/models/fields_module.py` | Field | Short text field -- requires max_length. |
| `VarcharField` | `aquilia/models/fields_module.py` | CharField | Explicit alias for CharField, representing a variable-length string. |
| `TextField` | `aquilia/models/fields_module.py` | Field | Long text field -- no length restriction. |
| `SlugField` | `aquilia/models/fields_module.py` | CharField | URL-friendly slug field. |
| `EmailField` | `aquilia/models/fields_module.py` | CharField | Email address field with validation. |
| `URLField` | `aquilia/models/fields_module.py` | CharField | URL field with validation. |
| `UUIDField` | `aquilia/models/fields_module.py` | Field | UUID field -- stored as VARCHAR(36) in database. |
| `FilePathField` | `aquilia/models/fields_module.py` | CharField | File system path field. |
| `DateField` | `aquilia/models/fields_module.py` | Field | Date field (year, month, day). |
| `TimeField` | `aquilia/models/fields_module.py` | Field | Time field (hour, minute, second, microsecond). |
| `DateTimeField` | `aquilia/models/fields_module.py` | Field | DateTime field with timezone support. |
| `DurationField` | `aquilia/models/fields_module.py` | Field | Stores timedelta -- as microseconds in database. |
| `BooleanField` | `aquilia/models/fields_module.py` | Field | Boolean field -- stored as INTEGER 0/1 in SQLite. |
| `BinaryField` | `aquilia/models/fields_module.py` | Field | Binary data field -- stored as BLOB. |
| `JSONField` | `aquilia/models/fields_module.py` | Field | JSON data field -- native on PostgreSQL, TEXT elsewhere. |
| `RelationField` | `aquilia/models/fields_module.py` | Field | Base class for relationship fields. |
| `ForeignKey` | `aquilia/models/fields_module.py` | RelationField | Many-to-one relationship field. |
| `OneToOneField` | `aquilia/models/fields_module.py` | ForeignKey | One-to-one relationship field. |
| `ManyToManyField` | `aquilia/models/fields_module.py` | RelationField | Many-to-many relationship field. |
| `GenericIPAddressField` | `aquilia/models/fields_module.py` | Field | IPv4 or IPv6 address field. |
| `FileField` | `aquilia/models/fields_module.py` | CharField | File path/URL field -- stores the path to the uploaded file. |
| `ImageField` | `aquilia/models/fields_module.py` | FileField | Image file field -- extends FileField with image validation. |
| `ArrayField` | `aquilia/models/fields_module.py` | Field | PostgreSQL array field. |
| `HStoreField` | `aquilia/models/fields_module.py` | Field | PostgreSQL hstore field (key-value pairs). |
| `RangeField` | `aquilia/models/fields_module.py` | Field | Base class for PostgreSQL range fields. |
| `IntegerRangeField` | `aquilia/models/fields_module.py` | RangeField | Public class. |
| `BigIntegerRangeField` | `aquilia/models/fields_module.py` | RangeField | Public class. |
| `DecimalRangeField` | `aquilia/models/fields_module.py` | RangeField | Public class. |
| `DateRangeField` | `aquilia/models/fields_module.py` | RangeField | Public class. |
| `DateTimeRangeField` | `aquilia/models/fields_module.py` | RangeField | Public class. |
| `CICharField` | `aquilia/models/fields_module.py` | CharField | Case-insensitive CharField (PostgreSQL CITEXT). |
| `CIEmailField` | `aquilia/models/fields_module.py` | EmailField | Case-insensitive EmailField (PostgreSQL CITEXT). |
| `CITextField` | `aquilia/models/fields_module.py` | TextField | Case-insensitive TextField (PostgreSQL CITEXT). |
| `InetAddressField` | `aquilia/models/fields_module.py` | GenericIPAddressField | PostgreSQL INET field -- stores IP address with optional netmask. |
| `GeneratedField` | `aquilia/models/fields_module.py` | Field | Database-computed generated field. |
| `OrderWrt` | `aquilia/models/fields_module.py` | IntegerField | Internal ordering helper field. |
| `Index` | `aquilia/models/fields_module.py` | object | Composite index declaration. |
| `UniqueConstraint` | `aquilia/models/fields_module.py` | object | Unique constraint declaration. |
| `GinIndex` | `aquilia/models/index.py` | _PostgresOnlyIndex | PostgreSQL GIN index -- useful for full-text search, JSONB, arrays. |
| `GistIndex` | `aquilia/models/index.py` | _PostgresOnlyIndex | PostgreSQL GiST index -- useful for geometric, range types, exclusion constraints. |
| `BrinIndex` | `aquilia/models/index.py` | _PostgresOnlyIndex | PostgreSQL BRIN index -- useful for very large tables with natural ordering. |
| `HashIndex` | `aquilia/models/index.py` | _PostgresOnlyIndex | PostgreSQL Hash index -- useful for equality lookups only. |
| `FunctionalIndex` | `aquilia/models/index.py` | object | Index on an expression or function call. |
| `QuerySet` | `aquilia/models/manager.py` | object | Reusable query method set -- compose into Manager via from_queryset(). |
| `BaseManager` | `aquilia/models/manager.py` | object | Base manager with Python descriptor protocol. |
| `Manager` | `aquilia/models/manager.py` | BaseManager | Default manager -- auto-attached as ``objects`` on every Model. |
| `ModelMeta` | `aquilia/models/metaclass.py` | type | Metaclass for Aquilia models. |
| `ColumnDef` | `aquilia/models/migration_dsl.py` | object | A column definition in the DSL. |
| `Operation` | `aquilia/models/migration_dsl.py` | object | Base class for all migration operations. |
| `CreateModel` | `aquilia/models/migration_dsl.py` | Operation | Create a new database table. |
| `DropModel` | `aquilia/models/migration_dsl.py` | Operation | Drop a table. |
| `RenameModel` | `aquilia/models/migration_dsl.py` | Operation | Rename a table (preserves data). |
| `AddField` | `aquilia/models/migration_dsl.py` | Operation | Add a column to an existing table. |
| `RemoveField` | `aquilia/models/migration_dsl.py` | Operation | Remove a column from an existing table. |
| `AlterField` | `aquilia/models/migration_dsl.py` | Operation | Alter a column's type, constraints, or default. |
| `RenameField` | `aquilia/models/migration_dsl.py` | Operation | Rename a column (preserves data). |
| `CreateIndex` | `aquilia/models/migration_dsl.py` | Operation | Create a database index. |
| `DropIndex` | `aquilia/models/migration_dsl.py` | Operation | Drop a database index. |
| `AddConstraint` | `aquilia/models/migration_dsl.py` | Operation | Add a constraint to a table. |
| `RemoveConstraint` | `aquilia/models/migration_dsl.py` | Operation | Remove a constraint from a table. |
| `RunSQL` | `aquilia/models/migration_dsl.py` | Operation | Execute raw SQL statements (forward and optionally reverse). |
| `RunPython` | `aquilia/models/migration_dsl.py` | Operation | Execute a Python callable as a data migration step. |
| `Migration` | `aquilia/models/migration_dsl.py` | object | Container for a set of migration operations with metadata. |
| `MigrationRecord` | `aquilia/models/migration_runner.py` | object | A record in the aquilia_migrations tracking table. |
| `MigrationRunner` | `aquilia/models/migration_runner.py` | object | Applies and tracks migrations against an AquiliaDatabase. |
| `MigrationOps` | `aquilia/models/migrations.py` | object | Migration operation builder -- used inside migration scripts. |
| `MigrationInfo` | `aquilia/models/migrations.py` | object | Metadata for a single migration file. |
| `MigrationRunner` | `aquilia/models/migrations.py` | object | Applies and tracks migrations against an AquiliaDatabase. |
| `Options` | `aquilia/models/options.py` | object | Parsed model options from inner Meta class. |
| `AMDLParseError` | `aquilia/models/parser.py` | AMDLParseFault | Raised when AMDL parsing fails. |
| `QNode` | `aquilia/models/query.py` | object | Composable filter node for complex WHERE clauses. |
| `Prefetch` | `aquilia/models/query.py` | object | Custom prefetch descriptor for prefetch_related(). |
| `Q` | `aquilia/models/query.py` | object | Aquilia QuerySet -- chainable, immutable, async-terminal query builder. |
| `ModelRegistry` | `aquilia/models/registry.py` | object | Global registry for all Model subclasses. |
| `Q` | `aquilia/models/runtime.py` | object | Aquilia Query builder -- chainable, async-terminal. |
| `ModelRegistry` | `aquilia/models/runtime.py` | object | Central registry for AMDL models and their runtime proxies. |
| `ModelProxy` | `aquilia/models/runtime.py` | object | Base class for AMDL-generated model proxies. |
| `SchemaDiff` | `aquilia/models/schema_snapshot.py` | object | Result of comparing two snapshots. |
| `ModelDiff` | `aquilia/models/schema_snapshot.py` | object | Changes within a single model. |
| `Signal` | `aquilia/models/signals.py` | object | A signal that can be connected to receiver functions. |
| `SQLBuilder` | `aquilia/models/sql_builder.py` | object | SELECT query builder with safe parameter binding. |
| `InsertBuilder` | `aquilia/models/sql_builder.py` | object | INSERT query builder. |
| `UpdateBuilder` | `aquilia/models/sql_builder.py` | object | UPDATE query builder. |
| `DeleteBuilder` | `aquilia/models/sql_builder.py` | object | DELETE query builder. |
| `CreateTableBuilder` | `aquilia/models/sql_builder.py` | object | CREATE TABLE DDL builder. |
| `AlterTableBuilder` | `aquilia/models/sql_builder.py` | object | ALTER TABLE DDL builder -- dialect-aware. |
| `UpsertBuilder` | `aquilia/models/sql_builder.py` | object | INSERT ... ON CONFLICT (upsert) query builder -- dialect-aware. |
| `UpsertIgnoreBuilder` | `aquilia/models/sql_builder.py` | object | INSERT ... ON CONFLICT DO NOTHING query builder -- dialect-aware. |
| `DatabaseNotReadyError` | `aquilia/models/startup_guard.py` | SystemExit | Raised when the database is not ready at server startup. |
| `Atomic` | `aquilia/models/transactions.py` | object | Async context manager for database transactions. |
| `TransactionManager` | `aquilia/models/transactions.py` | object | Higher-level transaction manager with properly scoped on_commit hooks. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `normalize_on_delete` | `aquilia/models/deletion.py` | `def normalize_on_delete(action: Any) -> Any` | Normalize an on_delete value to its canonical constant. |
| `lookup_registry` | `aquilia/models/fields/lookups.py` | `def lookup_registry() -> dict[str, type[Lookup]]` | Return a copy of the lookup registry. |
| `register_lookup` | `aquilia/models/fields/lookups.py` | `def register_lookup(name: str, cls: type[Lookup]) -> None` | Register a custom lookup type. |
| `resolve_lookup` | `aquilia/models/fields/lookups.py` | `def resolve_lookup(field_name: str, lookup_name: str, value: Any) -> Lookup` | Resolve a lookup name to a Lookup instance. |
| `raw_sql_to_operations` | `aquilia/models/migration_dsl.py` | `def raw_sql_to_operations(upgrade_sql: str, downgrade_sql: str = '') -> list[Operation]` | Convert raw SQL strings into a list of RunSQL operations. |
| `generate_dsl_migration` | `aquilia/models/migration_gen.py` | `def generate_dsl_migration(model_classes: list, migrations_dir: str &#124; Path, snapshot_path: str &#124; Path &#124; None = None, slug: str &#124; None = None) -> Path &#124; None` | Generate a DSL migration file from the diff between the current |
| `check_db_exists` | `aquilia/models/migration_runner.py` | `def check_db_exists(db_url: str) -> bool` | Check if a SQLite database file exists WITHOUT creating WAL/SHM files. |
| `check_migrations_applied` | `aquilia/models/migration_runner.py` | `def check_migrations_applied(db_url: str, migrations_dir: str &#124; Path = 'migrations') -> bool` | Check if there are unapplied migrations WITHOUT creating WAL/SHM. |
| `generate_migration_file` | `aquilia/models/migrations.py` | `def generate_migration_file(models: list[ModelNode], migrations_dir: str &#124; Path, slug: str &#124; None = None, dialect: str = 'sqlite') -> Path` | Generate a migration file from AMDL model nodes. |
| `generate_migration_from_models` | `aquilia/models/migrations.py` | `def generate_migration_from_models(model_classes: list, migrations_dir: str &#124; Path, slug: str &#124; None = None, dialect: str = 'sqlite') -> Path` | Generate a migration file from new Python Model subclasses. |
| `parse_amdl` | `aquilia/models/parser.py` | `def parse_amdl(source: str, file_path: str = '<string>') -> AMDLFile` | Parse AMDL source text into an AMDLFile. |
| `parse_amdl_file` | `aquilia/models/parser.py` | `def parse_amdl_file(path: str &#124; Path) -> AMDLFile` | Parse an `.amdl` file from disk. |
| `parse_amdl_directory` | `aquilia/models/parser.py` | `def parse_amdl_directory(directory: str &#124; Path) -> list[AMDLFile]` | Parse all `.amdl` files in a directory (non-recursive). |
| `generate_create_table_sql` | `aquilia/models/runtime.py` | `def generate_create_table_sql(model: ModelNode, dialect: str = 'sqlite') -> str` | Generate CREATE TABLE SQL from a ModelNode. |
| `generate_create_index_sql` | `aquilia/models/runtime.py` | `def generate_create_index_sql(model: ModelNode, dialect: str = 'sqlite') -> list[str]` | Generate CREATE INDEX statements for non-unique indexes. |
| `create_snapshot` | `aquilia/models/schema_snapshot.py` | `def create_snapshot(model_classes: list) -> dict[str, Any]` | Create a schema snapshot from a list of Model subclasses. |
| `save_snapshot` | `aquilia/models/schema_snapshot.py` | `def save_snapshot(snapshot: dict[str, Any], path: Path) -> None` | Write snapshot to file in CROUS binary format. |
| `load_snapshot` | `aquilia/models/schema_snapshot.py` | `def load_snapshot(path: Path) -> dict[str, Any] &#124; None` | Load snapshot from file in CROUS binary format. |
| `compute_diff` | `aquilia/models/schema_snapshot.py` | `def compute_diff(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> SchemaDiff` | Compute the diff between two schema snapshots. |
| `diff_to_operations` | `aquilia/models/schema_snapshot.py` | `def diff_to_operations(diff: SchemaDiff, old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> list[Operation]` | Convert a SchemaDiff into a list of DSL operations. |
| `receiver` | `aquilia/models/signals.py` | `def receiver(signal: Signal, *, sender: type &#124; None = None)` | Shorthand decorator to connect a function to a signal. |
| `check_db_ready` | `aquilia/models/startup_guard.py` | `def check_db_ready(db_url: str = 'sqlite:///db.sqlite3', migrations_dir: str &#124; Path = 'migrations', *, auto_migrate: bool &#124; None = None) -> bool` | Check if the database is ready for the application to start. |
| `atomic` | `aquilia/models/transactions.py` | `def atomic(db: AquiliaDatabase &#124; None = None, *, savepoint: bool = True, durable: bool = False, isolation: str &#124; None = None) -> Atomic` | Create an atomic transaction context manager. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `CASCADE` | `aquilia/models/deletion.py` | `'CASCADE'` |
| `SET_NULL` | `aquilia/models/deletion.py` | `'SET NULL'` |
| `PROTECT` | `aquilia/models/deletion.py` | `'PROTECT'` |
| `SET_DEFAULT` | `aquilia/models/deletion.py` | `'SET DEFAULT'` |
| `DO_NOTHING` | `aquilia/models/deletion.py` | `'DO NOTHING'` |
| `RESTRICT` | `aquilia/models/deletion.py` | `'RESTRICT'` |
| `_ON_DELETE_ALIASES` | `aquilia/models/deletion.py` | `{'CASCADE': CASCADE, 'SET_NULL': SET_NULL, 'SET NULL': SET_NULL, 'SETNULL': SET_NULL, 'PROTECT': PROTECT, 'SET_DEFAULT': SET_DEFAULT, 'SET DEFAULT': SET_DEFAULT` |
| `_SAFE_FUNC_RE` | `aquilia/models/expression.py` | `re.compile('^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)` |
| `_SAFE_TYPE_RE` | `aquilia/models/expression.py` | `re.compile('^[A-Z][A-Z0-9_ ]*(?:\\([0-9]+(?:\\s*,\\s*[0-9]+)?\\))?$', re.IGNORECASE)` |
| `_REGISTRY` | `aquilia/models/fields/lookups.py` | `dict[str, type[Lookup]]` |
| `_ON_DELETE_SQL_MAP` | `aquilia/models/fields_module.py` | `dict[str, str]` |
| `UNSET` | `aquilia/models/fields_module.py` | `_Unset()` |
| `M` | `aquilia/models/manager.py` | `TypeVar('M', bound='BaseManager')` |
| `_ON_DELETE_SQL_MAP` | `aquilia/models/migration_dsl.py` | `dict[str, str]` |
| `_SENTINEL` | `aquilia/models/migration_dsl.py` | `_SentinelType()` |
| `C` | `aquilia/models/migration_dsl.py` | `columns` |
| `MIGRATION_TABLE` | `aquilia/models/migration_runner.py` | `'aquilia_migrations'` |
| `MIGRATION_TABLE` | `aquilia/models/migrations.py` | `'aquilia_migrations'` |
| `ALLOWED_DEFAULTS` | `aquilia/models/parser.py` | `frozenset({'now_utc()', 'uuid4()', 'seq()'})` |
| `ALLOWED_DEFAULT_PATTERN` | `aquilia/models/parser.py` | `re.compile('^(now_utc\\(\\) &#124; uuid4\\(\\) &#124; seq\\(\\) &#124; env\\("[A-Za-z_][A-Za-z0-9_]*"\\))$')` |
| `RE_MODEL_OPEN` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*MODEL\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*≫\\s*$')` |
| `RE_MODEL_CLOSE` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*/MODEL\\s*≫\\s*$')` |
| `RE_SLOT` | `aquilia/models/parser.py` | `re.compile('^\\s*slot\\s+([a-z_][a-z0-9_]*)\\s*::\\s*([A-Za-z]+(?:\\([^)]*\\))?)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_LINK` | `aquilia/models/parser.py` | `re.compile('^\\s*link\\s+([a-z_][a-z0-9_]*)\\s*->\\s*(ONE &#124; MANY &#124; MANY_THROUGH)\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_INDEX` | `aquilia/models/parser.py` | `re.compile('^\\s*index\\s+\\[([^\\]]+)\\]\\s*(unique)?\\s*$')` |
| `RE_HOOK` | `aquilia/models/parser.py` | `re.compile('^\\s*hook\\s+([a-z_][a-z0-9_]*)\\s*->\\s*([a-z_][a-z0-9_]*)\\s*$')` |
| `RE_META` | `aquilia/models/parser.py` | `re.compile('^\\s*meta\\s+([a-z_][a-z0-9_]*)\\s*=\\s*"([^"]*)"\\s*$')` |
| `RE_NOTE` | `aquilia/models/parser.py` | `re.compile('^\\s*note\\s+"([^"]*)"\\s*$')` |
| `FIELD_TYPE_MAP` | `aquilia/models/parser.py` | `{ft.value: ft for ft in FieldType}` |
| `_SAFE_FIELD_RE` | `aquilia/models/query.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_EXPR_OP_MAP` | `aquilia/models/query.py` | `{'exact': '=', 'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=', 'ne': '!='}` |
| `_SAFE_DEFAULTS` | `aquilia/models/runtime.py` | `{'now_utc()': lambda: datetime.datetime.now(datetime.timezone.utc), 'uuid4()': lambda: str(uuid.uuid4()), 'seq()': lambda: None}` |
| `SQLITE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'INTEGER', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'INTEGER', ` |
| `POSTGRES_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'SERIAL', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'BOOLEAN', Fi` |
| `MYSQL_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'TINYINT(1)'` |
| `ORACLE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'NUMBER(10)', FieldType.INT: 'NUMBER(10)', FieldType.BIGINT: 'NUMBER(19)', FieldType.STR: 'VARCHAR2', FieldType.TEXT: 'CLOB', FieldType.BOOL: '` |
| `_TYPE_MAPS` | `aquilia/models/runtime.py` | `{'sqlite': SQLITE_TYPE_MAP, 'postgresql': POSTGRES_TYPE_MAP, 'mysql': MYSQL_TYPE_MAP, 'oracle': ORACLE_TYPE_MAP}` |
| `SNAPSHOT_VERSION` | `aquilia/models/schema_snapshot.py` | `1` |
| `RENAME_THRESHOLD` | `aquilia/models/schema_snapshot.py` | `0.6` |
| `_YELLOW` | `aquilia/models/startup_guard.py` | `'\x1b[93m'` |
| `_RESET` | `aquilia/models/startup_guard.py` | `'\x1b[0m'` |
| `_BOLD` | `aquilia/models/startup_guard.py` | `'\x1b[1m'` |
| `_SP_NAME_RE` | `aquilia/models/transactions.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |

## Detailed Classes And Methods

### Class: `Aggregate`

- Source: `aquilia/models/aggregate.py`
- Bases: `Expression`
- Summary: Base class for aggregate functions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` | `str` | `''` |
| `template` | `str` | `'{function}({distinct}{expression})'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Sum`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL SUM() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'SUM'` |

### Class: `Avg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL AVG() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'AVG'` |

### Class: `Count`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL COUNT() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'COUNT'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Max`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL MAX() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'MAX'` |

### Class: `Min`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL MIN() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'MIN'` |

### Class: `StdDev`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL STDDEV() aggregate (PostgreSQL) / stdev (SQLite extension).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'STDDEV'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Variance`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL VARIANCE() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'VARIANCE'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `ArrayAgg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL ARRAY_AGG() -- collect values into an array.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'ARRAY_AGG'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `StringAgg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL STRING_AGG() -- concatenate strings with a delimiter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'STRING_AGG'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `GroupConcat`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: MySQL/SQLite GROUP_CONCAT() aggregate.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'GROUP_CONCAT'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `BoolAnd`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL BOOL_AND() -- returns true if ALL values are true.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'BOOL_AND'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `BoolOr`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL BOOL_OR() -- returns true if ANY value is true.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `function` |  | `'BOOL_OR'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `FieldType`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Built-in AMDL field types.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `AUTO` |  | `'Auto'` |
| `INT` |  | `'Int'` |
| `BIGINT` |  | `'BigInt'` |
| `STR` |  | `'Str'` |
| `TEXT` |  | `'Text'` |
| `BOOL` |  | `'Bool'` |
| `FLOAT` |  | `'Float'` |
| `DECIMAL` |  | `'Decimal'` |
| `JSON` |  | `'JSON'` |
| `BYTES` |  | `'Bytes'` |
| `DATETIME` |  | `'DateTime'` |
| `DATE` |  | `'Date'` |
| `TIME` |  | `'Time'` |
| `UUID` |  | `'UUID'` |
| `ENUM` |  | `'Enum'` |
| `FOREIGN_KEY` |  | `'ForeignKey'` |

### Class: `LinkKind`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Relationship cardinality.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ONE` |  | `'ONE'` |
| `MANY` |  | `'MANY'` |
| `MANY_THROUGH` |  | `'MANY_THROUGH'` |

### Class: `SlotNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a `slot` directive -- a model field/column.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `field_type` | `FieldType` |  |
| `type_params` | `tuple[Any, ...] &#124; None` | `None` |
| `modifiers` | `dict[str, Any]` | `field(default_factory=dict)` |
| `is_pk` | `bool` | `False` |
| `is_unique` | `bool` | `False` |
| `is_nullable` | `bool` | `False` |
| `max_length` | `int &#124; None` | `None` |
| `default_expr` | `str &#124; None` | `None` |
| `note` | `str &#124; None` | `None` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `LinkNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a `link` directive -- a relationship.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `kind` | `LinkKind` |  |
| `target_model` | `str` |  |
| `fk_field` | `str &#124; None` | `None` |
| `back_name` | `str &#124; None` | `None` |
| `through_model` | `str &#124; None` | `None` |
| `modifiers` | `dict[str, Any]` | `field(default_factory=dict)` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `IndexNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents an `index` directive.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fields` | `list[str]` | `field(default_factory=list)` |
| `is_unique` | `bool` | `False` |
| `name` | `str &#124; None` | `None` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `HookNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a `hook` directive -- lifecycle binding.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `event` | `str` |  |
| `handler_name` | `str` |  |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `MetaNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a `meta` directive.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `key` | `str` |  |
| `value` | `str` |  |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `NoteNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a `note` directive -- freeform documentation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `text` | `str` |  |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### Class: `ModelNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a complete MODEL stanza.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `slots` | `list[SlotNode]` | `field(default_factory=list)` |
| `links` | `list[LinkNode]` | `field(default_factory=list)` |
| `indexes` | `list[IndexNode]` | `field(default_factory=list)` |
| `hooks` | `list[HookNode]` | `field(default_factory=list)` |
| `meta` | `dict[str, str]` | `field(default_factory=dict)` |
| `notes` | `list[str]` | `field(default_factory=list)` |
| `source_file` | `str` | `''` |
| `start_line` | `int` | `0` |
| `end_line` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `table_name` | `def table_name(self) -> str` | property | Get table name from meta or derive from model name. |
| `pk_slot` | `def pk_slot(self) -> SlotNode &#124; None` | property | Get primary key slot, if any. |
| `get_slot` | `def get_slot(self, name: str) -> SlotNode &#124; None` |  | Find slot by name. |
| `fingerprint` | `def fingerprint(self) -> str` |  | Compute a deterministic hash for migration diffing. |

### Class: `AMDLFile`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a parsed `.amdl` file containing one or more models.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `path` | `str` |  |
| `models` | `list[ModelNode]` | `field(default_factory=list)` |
| `errors` | `list[str]` | `field(default_factory=list)` |

### Class: `ModelRegistry`

- Source: `aquilia/models/base.py`
- Bases: `object`
- Summary: Backward-compatible wrapper around registry.ModelRegistry.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(cls, model_cls: type[Model]) -> None` | classmethod | Method. |
| `get` | `def get(cls, name: str) -> type[Model] &#124; None` | classmethod | Method. |
| `all_models` | `def all_models(cls) -> dict[str, type[Model]]` | classmethod | Method. |
| `set_database` | `def set_database(cls, db: AquiliaDatabase) -> None` | classmethod | Method. |
| `get_database` | `def get_database(cls) -> AquiliaDatabase &#124; None` | classmethod | Method. |
| `create_tables` | `async def create_tables(cls, db: AquiliaDatabase &#124; None = None) -> list[str]` | classmethod | Method. |
| `reset` | `def reset(cls) -> None` | classmethod | Method. |
| `on_startup` | `async def on_startup(self) -> None` |  | Lifecycle hook -- called by LifecycleCoordinator at app start. |
| `on_shutdown` | `async def on_shutdown(self) -> None` |  | Method. |

### Class: `Model`

- Source: `aquilia/models/base.py`
- Bases: `object`
- Summary: Aquilia Model base class -- pure Python, async-first ORM.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `objects` | `ClassVar[Manager]` |  |
| `refresh_from_db` |  | `refresh` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `pk` | `def pk(self) -> Any` | property | Shortcut for accessing the primary key value. |
| `pk` | `def pk(self, value: Any) -> None` | pk.setter | Set the primary key value. |
| `create` | `async def create(cls, **data: Any) -> Model` | classmethod | Create and persist a new record. |
| `get` | `async def get(cls, pk: Any = None, **filters: Any) -> Model` | classmethod | Get a single record by PK or filters. |
| `get_or_none` | `async def get_or_none(cls, pk: Any = None, **filters: Any) -> Model &#124; None` | classmethod | Get a single record, returning ``None`` if not found. |
| `get_or_create` | `async def get_or_create(cls, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` | classmethod | Get existing or create new record. |
| `update_or_create` | `async def update_or_create(cls, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` | classmethod | Update existing or create new record. |
| `find_or_create` | `async def find_or_create(cls, defaults: dict[str, Any] &#124; None = None, create_defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` | classmethod | Atomically find an existing record or create a new one. |
| `bulk_create` | `async def bulk_create(cls, instances: list[dict[str, Any]], *, batch_size: int &#124; None = None, ignore_conflicts: bool = False) -> list[Model]` | classmethod | Create multiple records efficiently using batched inserts. |
| `bulk_update` | `async def bulk_update(cls, instances: list[Model], fields: list[str], *, batch_size: int &#124; None = None) -> int` | classmethod | Update specific fields on multiple model instances efficiently. |
| `query` | `def query(cls) -> Q` | classmethod | Start a query chain. |
| `all` | `async def all(cls) -> list[Model]` | classmethod | Shortcut: get all records. |
| `count` | `async def count(cls) -> int` | classmethod | Shortcut: count all records. |
| `latest` | `async def latest(cls, field_name: str &#124; None = None) -> Model` | classmethod | Return the latest record by date field. |
| `earliest` | `async def earliest(cls, field_name: str &#124; None = None) -> Model` | classmethod | Return the earliest record by date field. |
| `raw` | `async def raw(cls, sql: str, params: list[Any] &#124; None = None) -> list[Model]` | classmethod | Execute raw SQL and return model instances. |
| `using` | `def using(cls, db_alias: str) -> Q` | classmethod | Target a specific database for this query. |
| `save` | `async def save(self, *, update_fields: list[str] &#124; None = None, force_insert: bool = False, force_update: bool = False, validate: bool = False) -> Model` |  | Save instance (insert or update). |
| `delete_instance` | `async def delete_instance(self) -> int` |  | Delete this instance from database. |
| `full_clean` | `def full_clean(self, exclude: list[str] &#124; None = None) -> None` |  | Validate instance completely. |
| `clean_fields` | `def clean_fields(self, exclude: list[str] &#124; None = None) -> None` |  | Validate all fields on this instance. |
| `clean` | `def clean(self) -> None` |  | Model-level validation hook -- override in subclasses. |
| `refresh` | `async def refresh(self, fields: list[str] &#124; None = None) -> Model` |  | Reload instance from database. |
| `get_dirty_fields` | `def get_dirty_fields(self) -> dict[str, Any]` |  | Return dict of fields whose values differ from the DB snapshot. |
| `related` | `async def related(self, name: str) -> Any` |  | Access a related model via FK or M2M. |
| `attach` | `async def attach(self, name: str, *targets: Any) -> None` |  | Attach records to a M2M relationship. |
| `detach` | `async def detach(self, name: str, *targets: Any) -> None` |  | Detach records from a M2M relationship. |
| `to_dict` | `def to_dict(self, *, fields: list[str] &#124; None = None, exclude: list[str] &#124; None = None) -> dict[str, Any]` |  | Serialize model instance to dict. |
| `from_row` | `def from_row(cls, row: dict[str, Any]) -> Model` | classmethod | Create model instance from database row dict. |
| `generate_create_table_sql` | `def generate_create_table_sql(cls, dialect: str = 'sqlite') -> str` | classmethod | Generate CREATE TABLE SQL using CreateTableBuilder. |
| `generate_index_sql` | `def generate_index_sql(cls, dialect: str = 'sqlite') -> list[str]` | classmethod | Generate CREATE INDEX statements from Meta.indexes. |
| `generate_m2m_sql` | `def generate_m2m_sql(cls, dialect: str = 'sqlite') -> list[str]` | classmethod | Generate junction table SQL for M2M fields. |
| `fingerprint` | `def fingerprint(cls) -> str` | classmethod | Compute deterministic hash for migration diffing. |

### Class: `Deferrable`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: Constraint deferral modes for PostgreSQL.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEFERRED` |  | `'DEFERRABLE INITIALLY DEFERRED'` |
| `IMMEDIATE` |  | `'DEFERRABLE INITIALLY IMMEDIATE'` |

### Class: `CheckConstraint`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: SQL CHECK constraint.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Generate the constraint SQL for CREATE TABLE body. |
| `sql_alter_add` | `def sql_alter_add(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Generate ALTER TABLE ADD CONSTRAINT SQL. |
| `sql_alter_drop` | `def sql_alter_drop(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Generate ALTER TABLE DROP CONSTRAINT SQL. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `ExclusionConstraint`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: PostgreSQL EXCLUDE constraint.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Generate constraint SQL (PostgreSQL only). |
| `sql_alter_add` | `def sql_alter_add(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Method. |
| `sql_alter_drop` | `def sql_alter_drop(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `OnDeleteHandler`

- Source: `aquilia/models/deletion.py`
- Bases: `object`
- Summary: Callable that implements on_delete behavior at the application level.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `handle` | `async def handle(self, db, source_model, target_field_name: str, pk_value: Any) -> int` |  | Execute the on_delete action. |
| `for_action` | `def for_action(cls, action: Any) -> OnDeleteHandler` | classmethod | Factory method -- create an OnDeleteHandler from any on_delete value. |

### Class: `SET`

- Source: `aquilia/models/deletion.py`
- Bases: `object`
- Summary: Factory for SET(value) / SET(callable) on_delete behavior.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `value` | `def value(self) -> Any` | property | The raw value or callable (for backward compatibility). |
| `resolve` | `def resolve(self) -> Any` |  | Resolve the SET value -- call it if it's a callable. |

### Class: `ProtectedError`

- Source: `aquilia/models/deletion.py`
- Bases: `ProtectedDeleteFault, Exception`
- Summary: Raised when trying to delete a protected object.

### Class: `RestrictedError`

- Source: `aquilia/models/deletion.py`
- Bases: `RestrictedDeleteFault, Exception`
- Summary: Raised when trying to delete a restricted object.

### Class: `TextChoices`

- Source: `aquilia/models/enums.py`
- Bases: `str, Enum`
- Summary: String-valued choices enum.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `label` | `def label(self) -> str` | property | Method. |

### Class: `IntegerChoices`

- Source: `aquilia/models/enums.py`
- Bases: `int, Enum`
- Summary: Integer-valued choices enum.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `label` | `def label(self) -> str` | property | Method. |

### Class: `Combinable`

- Source: `aquilia/models/expression.py`
- Bases: `object`
- Summary: Base class providing arithmetic operators for expressions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ADD` |  | `'+'` |
| `SUB` |  | `'-'` |
| `MUL` |  | `'*'` |
| `DIV` |  | `'/'` |
| `MOD` |  | `'%'` |
| `BITAND` |  | `'&'` |
| `BITOR` | &#124; `' | '` |

### Class: `Expression`

- Source: `aquilia/models/expression.py`
- Bases: `Combinable`
- Summary: Base class for all SQL expressions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Render expression to SQL with bind parameters. |
| `resolve_expression` | `def resolve_expression(self, query = None, allow_joins = True)` |  | Hook for QuerySet to resolve the expression in context. |

### Class: `OrderBy`

- Source: `aquilia/models/expression.py`
- Bases: `object`
- Summary: Ordering directive -- wraps an expression with ASC/DESC.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `F`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Reference to a model field in an expression context.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |
| `asc` | `def asc(self, *, nulls_first: bool &#124; None = None, nulls_last: bool &#124; None = None) -> OrderBy` |  | Create ascending ORDER BY directive. |
| `desc` | `def desc(self, *, nulls_first: bool &#124; None = None, nulls_last: bool &#124; None = None) -> OrderBy` |  | Create descending ORDER BY directive. |

### Class: `Value`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps a literal Python value as an SQL expression.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `RawSQL`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Raw SQL expression -- use with caution.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Col`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Reference to a specific table.column in a multi-table query.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Star`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Represents * (all columns).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `CombinedExpression`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Represents two expressions combined with an operator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `When`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Conditional WHEN clause for use inside Case().

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Case`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL CASE expression.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Subquery`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps a query builder as a subquery expression.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Exists`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL EXISTS() expression.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `OuterRef`

- Source: `aquilia/models/expression.py`
- Bases: `F`
- Summary: Reference to a field from the outer query (for use in Subquery/Exists).

### Class: `ExpressionWrapper`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps an expression with an explicit output type.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Func`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Generic SQL function call.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Cast`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL CAST() expression.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Coalesce`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL COALESCE() -- returns first non-NULL argument.

### Class: `Greatest`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL GREATEST() (MAX on SQLite) -- returns largest argument.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Least`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LEAST() (MIN on SQLite) -- returns smallest argument.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `NullIf`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL NULLIF() -- returns NULL if expression1 equals expression2.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Length`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LENGTH() -- return string length.

### Class: `Upper`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL UPPER() -- convert to uppercase.

### Class: `Lower`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LOWER() -- convert to lowercase.

### Class: `Trim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL TRIM() -- remove leading and trailing whitespace.

### Class: `LTrim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LTRIM() -- remove leading whitespace.

### Class: `RTrim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL RTRIM() -- remove trailing whitespace.

### Class: `Concat`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL concatenation -- dialect-aware (|| for SQLite/PG, CONCAT for MySQL).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Left`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL LEFT() / SUBSTR() -- extract leftmost characters.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Right`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL RIGHT() / SUBSTR() -- extract rightmost characters.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Substr`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL SUBSTR() -- extract substring.

### Class: `Replace`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL REPLACE() -- replace occurrences in a string.

### Class: `Abs`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL ABS() -- absolute value.

### Class: `Round`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL ROUND() -- round to specified decimal places.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Power`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL POWER() -- raise to a power.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Now`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL current timestamp -- dialect-aware.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `CompositeAttribute`

- Source: `aquilia/models/fields/composite.py`
- Bases: `object`
- Summary: Descriptor that provides read/write access to a group of columns

### Class: `CompositeField`

- Source: `aquilia/models/fields/composite.py`
- Bases: `Field`
- Summary: Groups multiple primitive fields into one logical attribute.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `CompositePrimaryKey`

- Source: `aquilia/models/fields/composite.py`
- Bases: `object`
- Summary: Declares a composite primary key across multiple fields.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql` | `def sql(self) -> str` |  | Generate the SQL PRIMARY KEY constraint. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `EnumField`

- Source: `aquilia/models/fields/enum_field.py`
- Bases: `Field`
- Summary: Stores a Python Enum value in the database.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `Lookup`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `object`
- Summary: Base class for field lookups.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` | `ClassVar[str]` | `''` |
| `sql_operator` | `ClassVar[str]` | `'='` |
| `bilateral` | `ClassVar[bool]` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Return (sql_clause, params) for this lookup. |

### Class: `Exact`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'exact'` |
| `sql_operator` |  | `'='` |

### Class: `IExact`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive exact match.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'iexact'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Contains`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'contains'` |
| `sql_operator` |  | `'LIKE'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `IContains`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive contains.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'icontains'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `StartsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'startswith'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `IStartsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive startswith.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'istartswith'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `EndsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'endswith'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `IEndsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive endswith.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'iendswith'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `In`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'in'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Gt`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'gt'` |
| `sql_operator` |  | `'>'` |

### Class: `Gte`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'gte'` |
| `sql_operator` |  | `'>='` |

### Class: `Lt`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'lt'` |
| `sql_operator` |  | `'<'` |

### Class: `Lte`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'lte'` |
| `sql_operator` |  | `'<='` |

### Class: `IsNull`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'isnull'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Range`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Filter within a range: field__range=(lo, hi).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'range'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Regex`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Filter by regex (PostgreSQL: ~, SQLite: REGEXP if loaded).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'regex'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `IRegex`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive regex.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'iregex'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Date`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract date from datetime and compare.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'date'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Year`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract year and compare.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'year'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Month`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract month and compare.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'month'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `Day`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract day and compare.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `lookup_name` |  | `'day'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str = 'sqlite') -> tuple[str, list[Any]]` |  | Method. |

### Class: `NullableMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that makes a field nullable with sensible defaults.

### Class: `UniqueMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that enforces uniqueness on a field.

### Class: `IndexedMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that auto-adds a database index to a field.

### Class: `AutoNowMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin for fields that auto-update on save (like updated_at).

### Class: `ChoiceMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that enforces validation of choices with display values.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_display` | `def get_display(self, value: Any) -> str` |  | Return the human-readable display value for a stored value. |
| `choice_values` | `def choice_values(self) -> list` | property | Return list of valid stored values. |

### Class: `EncryptedMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Placeholder mixin for encrypted field storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `configure_encryption_key` | `def configure_encryption_key(cls, key: str &#124; bytes) -> None` | classmethod | Configure symmetric encryption using *key*. |
| `configure_encryption` | `def configure_encryption(cls, encrypt: Callable[[str], str], decrypt: Callable[[str], str]) -> None` | classmethod | Configure encryption/decryption functions. |
| `to_db` | `def to_db(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |

### Class: `ValidationError`

- Source: `aquilia/models/fields/validators.py`
- Bases: `ValueError`
- Summary: Raised by validators when a value fails validation.

### Class: `BaseValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `object`
- Summary: Base class for all validators.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `message` | `str` | `'Invalid value.'` |
| `code` | `str` | `'invalid'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Override in subclasses. Return True if value is valid. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `MinValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value >= limit.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'min_value'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `MaxValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value <= limit.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'max_value'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `MinLengthValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure string length >= limit.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'min_length'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `MaxLengthValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure string length <= limit.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'max_length'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `RegexValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate against a regex pattern.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'invalid'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `EmailValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate email address format.

### Class: `URLValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate URL format.

### Class: `SlugValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate slug format (letters, numbers, hyphens, underscores).

### Class: `ProhibitNullCharactersValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Reject strings containing null characters.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'null_characters_not_allowed'` |
| `message` |  | `'Null characters are not allowed.'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |

### Class: `DecimalValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate decimal precision and scale.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'invalid_decimal'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `FileExtensionValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate file extension against an allowed list.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'invalid_extension'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `StepValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value is a multiple of step (from offset).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'invalid_step'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `RangeValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value falls within [min_val, max_val] range.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'out_of_range'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |
| `get_message` | `def get_message(self, value: Any) -> str` |  | Method. |

### Class: `UniqueForDateValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate uniqueness for a date-based scope.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'unique_for_date'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any) -> bool` |  | Method. |

### Class: `FieldValidationError`

- Source: `aquilia/models/fields_module.py`
- Bases: `_FieldValidationFault, ValueError`
- Summary: Raised when field validation fails.

### Class: `Field`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Base field descriptor -- all Aquilia fields inherit from this.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `column_name` | `def column_name(self) -> str` | property | Database column name. |
| `has_default` | `def has_default(self) -> bool` |  | Check if field has a default value. |
| `get_default` | `def get_default(self) -> Any` |  | Get default value, calling it if callable. |
| `validate` | `def validate(self, value: Any) -> Any` |  | Validate and coerce value. Returns cleaned value. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Convert database value to Python object. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Convert Python value to database-ready value. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Return SQL type string for this field. |
| `sql_column_def` | `def sql_column_def(self, dialect: str = 'sqlite') -> str` |  | Generate full SQL column definition. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Serialize field definition for migrations. |
| `clone` | `def clone(self) -> Field` |  | Create a deep copy of this field. |

### Class: `AutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Auto-incrementing integer primary key (32-bit).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `BigAutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Auto-incrementing 64-bit integer primary key.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `SmallAutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `AutoField`
- Summary: Auto-incrementing 16-bit integer primary key.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `IntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Standard 32-bit integer field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `BigIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: 64-bit integer field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `SmallIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: 16-bit integer field (-32768 to 32767).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `PositiveIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 32-bit integer field (0 to 2147483647).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `PositiveSmallIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 16-bit integer field (0 to 32767).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `PositiveBigIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 64-bit integer field (0 to 9223372036854775807).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `FloatField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Double-precision floating-point field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `DecimalField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Fixed-precision decimal field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `CharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Short text field -- requires max_length.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `VarcharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Explicit alias for CharField, representing a variable-length string.

### Class: `TextField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Long text field -- no length restriction.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `SlugField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: URL-friendly slug field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |

### Class: `EmailField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Email address field with validation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |

### Class: `URLField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: URL field with validation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |

### Class: `UUIDField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: UUID field -- stored as VARCHAR(36) in database.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `FilePathField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: File system path field.

### Class: `DateField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Date field (year, month, day).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool) -> Any` |  | Auto-set value before save. |

### Class: `TimeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Time field (hour, minute, second, microsecond).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool) -> Any` |  | Auto-set time value before save. |

### Class: `DateTimeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: DateTime field with timezone support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool) -> Any` |  | Auto-set value before save. |

### Class: `DurationField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Stores timedelta -- as microseconds in database.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `BooleanField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Boolean field -- stored as INTEGER 0/1 in SQLite.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `BinaryField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Binary data field -- stored as BLOB.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `JSONField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: JSON data field -- native on PostgreSQL, TEXT elsewhere.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `RelationField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Base class for relationship fields.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `related_model` | `def related_model(self) -> type[Model] &#124; None` | property | Resolve the related model (handles forward references). |
| `resolve_model` | `def resolve_model(self, registry: dict[str, type[Model]]) -> None` |  | Resolve string-based model reference. |

### Class: `ForeignKey`

- Source: `aquilia/models/fields_module.py`
- Bases: `RelationField`
- Summary: Many-to-one relationship field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `sql_column_def` | `def sql_column_def(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `OneToOneField`

- Source: `aquilia/models/fields_module.py`
- Bases: `ForeignKey`
- Summary: One-to-one relationship field.

### Class: `ManyToManyField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RelationField`
- Summary: Many-to-many relationship field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `junction_table_name` | `def junction_table_name(self, source_model: type[Model]) -> str` |  | Generate junction table name. |
| `junction_columns` | `def junction_columns(self, source_model: type[Model]) -> tuple[str, str]` |  | Return (source_fk_col, target_fk_col) for junction table. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `sql_column_def` | `def sql_column_def(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `GenericIPAddressField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: IPv4 or IPv6 address field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `FileField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: File path/URL field -- stores the path to the uploaded file.

### Class: `ImageField`

- Source: `aquilia/models/fields_module.py`
- Bases: `FileField`
- Summary: Image file field -- extends FileField with image validation.

### Class: `ArrayField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: PostgreSQL array field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `HStoreField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: PostgreSQL hstore field (key-value pairs).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `RangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Base class for PostgreSQL range fields.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `to_python` | `def to_python(self, value: Any) -> Any` |  | Method. |
| `to_db` | `def to_db(self, value: Any, dialect: str = 'sqlite') -> Any` |  | Method. |

### Class: `IntegerRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `BigIntegerRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `DecimalRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `DateRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `DateTimeRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `CICharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Case-insensitive CharField (PostgreSQL CITEXT).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `CIEmailField`

- Source: `aquilia/models/fields_module.py`
- Bases: `EmailField`
- Summary: Case-insensitive EmailField (PostgreSQL CITEXT).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `CITextField`

- Source: `aquilia/models/fields_module.py`
- Bases: `TextField`
- Summary: Case-insensitive TextField (PostgreSQL CITEXT).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, value: Any) -> Any` |  | Method. |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `InetAddressField`

- Source: `aquilia/models/fields_module.py`
- Bases: `GenericIPAddressField`
- Summary: PostgreSQL INET field -- stores IP address with optional netmask.

### Class: `GeneratedField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Database-computed generated field.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str = 'sqlite') -> str` |  | Method. |
| `sql_column_def` | `def sql_column_def(self, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `OrderWrt`

- Source: `aquilia/models/fields_module.py`
- Bases: `IntegerField`
- Summary: Internal ordering helper field.

### Class: `Index`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Composite index declaration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Method. |

### Class: `UniqueConstraint`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Unique constraint declaration.

### Class: `GinIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL GIN index -- useful for full-text search, JSONB, arrays.

### Class: `GistIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL GiST index -- useful for geometric, range types, exclusion constraints.

### Class: `BrinIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL BRIN index -- useful for very large tables with natural ordering.

### Class: `HashIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL Hash index -- useful for equality lookups only.

### Class: `FunctionalIndex`

- Source: `aquilia/models/index.py`
- Bases: `object`
- Summary: Index on an expression or function call.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str = 'sqlite') -> str` |  | Method. |
| `deconstruct` | `def deconstruct(self) -> dict[str, Any]` |  | Method. |

### Class: `QuerySet`

- Source: `aquilia/models/manager.py`
- Bases: `object`
- Summary: Reusable query method set -- compose into Manager via from_queryset().

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_queryset` | `def get_queryset(self) -> Q` |  | Method. |

### Class: `BaseManager`

- Source: `aquilia/models/manager.py`
- Bases: `object`
- Summary: Base manager with Python descriptor protocol.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `order_by` |  | `order` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_queryset` | `def get_queryset(self) -> Q` |  | Override point for custom managers. |
| `filter` | `def filter(self, *q_nodes: Any, **kwargs: Any) -> Q` |  | Field filtering. See Q.filter() for details. |
| `exclude` | `def exclude(self, **kwargs: Any) -> Q` |  | Negated filter. See Q.exclude() for details. |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any) -> Q` |  | Raw WHERE clause (Aquilia-only). See Q.where() for details. |
| `order` | `def order(self, *fields: Any) -> Q` |  | ORDER BY. See Q.order() for details -- supports str, F().desc(), OrderBy. |
| `limit` | `def limit(self, n: int) -> Q` |  | Method. |
| `offset` | `def offset(self, n: int) -> Q` |  | Method. |
| `distinct` | `def distinct(self) -> Q` |  | Method. |
| `only` | `def only(self, *fields: str) -> Q` |  | Load only specified fields. |
| `defer` | `def defer(self, *fields: str) -> Q` |  | Defer loading of specified fields. |
| `annotate` | `def annotate(self, **expressions: Any) -> Q` |  | Add annotations. See Q.annotate() for details. |
| `group_by` | `def group_by(self, *fields: str) -> Q` |  | Method. |
| `having` | `def having(self, clause: str, *args: Any) -> Q` |  | HAVING clause (use after group_by). |
| `union` | `def union(self, *querysets: Any, all: bool = False) -> Q` |  | UNION set operation. |
| `intersection` | `def intersection(self, *querysets: Any) -> Q` |  | INTERSECT set operation. |
| `difference` | `def difference(self, *querysets: Any) -> Q` |  | EXCEPT set operation. |
| `select_related` | `def select_related(self, *fields: str) -> Q` |  | JOIN-based eager loading. |
| `prefetch_related` | `def prefetch_related(self, *lookups: Any) -> Q` |  | Separate-query prefetching. Accepts strings or Prefetch objects. |
| `select_for_update` | `def select_for_update(self, **kwargs: Any) -> Q` |  | SELECT ... FOR UPDATE (locking). |
| `iterator` | `def iterator(self, chunk_size: int = 2000) -> Q` |  | Memory-efficient chunked iteration. See Q.iterator() for details. |
| `using` | `def using(self, db_alias: str) -> Q` |  | Target a specific database. |
| `none` | `def none(self) -> Q` |  | Return an empty queryset. |
| `apply_q` | `def apply_q(self, q_node: Any) -> Q` |  | Apply a QNode filter. |
| `all` | `async def all(self) -> list[Model]` |  | Method. |
| `first` | `async def first(self) -> Model &#124; None` |  | Method. |
| `last` | `async def last(self) -> Model &#124; None` |  | Method. |
| `one` | `async def one(self) -> Model` |  | Return exactly one row. Raises if 0 or >1 (Aquilia-only). |
| `latest` | `async def latest(self, field_name: str &#124; None = None) -> Model` |  | Return latest record by date field. |
| `earliest` | `async def earliest(self, field_name: str &#124; None = None) -> Model` |  | Return earliest record by date field. |
| `count` | `async def count(self) -> int` |  | Method. |
| `exists` | `async def exists(self) -> bool` |  | Method. |
| `values` | `async def values(self, *fields: str) -> list[dict[str, Any]]` |  | Method. |
| `values_list` | `async def values_list(self, *fields: str, flat: bool = False) -> list[Any]` |  | Method. |
| `update` | `async def update(self, values: dict[str, Any] &#124; None = None, **kwargs: Any) -> int` |  | Method. |
| `delete` | `async def delete(self) -> int` |  | Method. |
| `aggregate` | `async def aggregate(self, **expressions: Any) -> dict[str, Any]` |  | Compute aggregates. See Q.aggregate() for details. |
| `in_bulk` | `async def in_bulk(self, id_list: list[Any]) -> dict[Any, Model]` |  | Return dict mapping PKs to instances. |
| `explain` | `async def explain(self, **kwargs: Any) -> str` |  | Return query execution plan. |
| `get` | `async def get(self, pk: Any = None, **filters: Any) -> Model &#124; None` |  | Get a single instance by PK or filter kwargs. |
| `get_or_create` | `async def get_or_create(self, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` |  | Get existing instance or create a new one. |
| `update_or_create` | `async def update_or_create(self, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` |  | Update existing instance or create a new one. |
| `create` | `async def create(self, **data: Any) -> Model` |  | Create and save a new instance. |
| `bulk_create` | `async def bulk_create(self, instances: list[Any], *, batch_size: int &#124; None = None, ignore_conflicts: bool = False) -> list[Model]` |  | Create multiple instances efficiently. |
| `bulk_update` | `async def bulk_update(self, instances: list[Model], fields: list[str], *, batch_size: int &#124; None = None) -> int` |  | Update specific fields on multiple instances. |
| `raw` | `async def raw(self, sql: str, params: list[Any] &#124; None = None) -> list[Model]` |  | Execute raw SQL and return model instances. |

### Class: `Manager`

- Source: `aquilia/models/manager.py`
- Bases: `BaseManager`
- Summary: Default manager -- auto-attached as ``objects`` on every Model.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_queryset` | `def from_queryset(cls, queryset_class: type, class_name: str &#124; None = None) -> type` | classmethod | Create a Manager subclass that includes methods from a QuerySet. |

### Class: `ModelMeta`

- Source: `aquilia/models/metaclass.py`
- Bases: `type`
- Summary: Metaclass for Aquilia models.

### Class: `ColumnDef`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A column definition in the DSL.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `col_type` | `str` |  |
| `primary_key` | `bool` | `False` |
| `autoincrement` | `bool` | `False` |
| `unique` | `bool` | `False` |
| `nullable` | `bool` | `False` |
| `default` | `Any` | `_SENTINEL` |
| `references` | `tuple[str, str] &#124; None` | `None` |
| `on_delete` | `str` | `'CASCADE'` |
| `on_update` | `str` | `'CASCADE'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> str` |  | Compile this column to a SQL column definition. |
| `to_snapshot` | `def to_snapshot(self) -> dict[str, Any]` |  | Serialize this column to a snapshot-compatible dict. |
| `from_snapshot` | `def from_snapshot(cls, data: dict[str, Any]) -> ColumnDef` | classmethod | Deserialize from snapshot dict. |

### Class: `Operation`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Summary: Base class for all migration operations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `reversible` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Compile this operation to SQL statement(s). |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Compile the reverse of this operation to SQL. |
| `describe` | `def describe(self) -> str` |  | Human-readable description. |
| `to_snapshot_delta` | `def to_snapshot_delta(self) -> dict[str, Any]` |  | Describe the snapshot change this operation implies. |

### Class: `CreateModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Create a new database table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `table` | `str` |  |
| `fields` | `list[ColumnDef]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `DropModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Drop a table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `table` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RenameModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Rename a table (preserves data).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `old_name` | `str` |  |
| `new_name` | `str` |  |
| `old_table` | `str` |  |
| `new_table` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `AddField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Add a column to an existing table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` |  |
| `table` | `str` |  |
| `column` | `ColumnDef` | `field(default_factory=lambda: ColumnDef(name='', col_type=''))` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RemoveField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Remove a column from an existing table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` |  |
| `table` | `str` |  |
| `column_name` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `AlterField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Alter a column's type, constraints, or default.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` |  |
| `table` | `str` |  |
| `column_name` | `str` |  |
| `new_type` | `str &#124; None` | `None` |
| `nullable` | `bool &#124; None` | `None` |
| `new_default` | `Any` | `_SENTINEL` |
| `drop_default` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RenameField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Rename a column (preserves data).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` |  |
| `table` | `str` |  |
| `old_name` | `str` |  |
| `new_name` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `CreateIndex`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Create a database index.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `table` | `str` |  |
| `columns` | `list[str]` | `field(default_factory=list)` |
| `unique` | `bool` | `False` |
| `condition` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `DropIndex`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Drop a database index.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `table` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `AddConstraint`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Add a constraint to a table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `table` | `str` |  |
| `constraint_sql` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RemoveConstraint`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Remove a constraint from a table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `table` | `str` |  |
| `name` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RunSQL`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Execute raw SQL statements (forward and optionally reverse).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `sql` | `str &#124; list[str]` | `''` |
| `reverse` | `str &#124; list[str]` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `RunPython`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Decorators: `dataclass`
- Summary: Execute a Python callable as a data migration step.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `forward` | `Callable &#124; None` | `None` |
| `reverse` | `Callable &#124; None` | `None` |
| `reversible` |  | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `reverse_sql` | `def reverse_sql(self, dialect: str = 'sqlite') -> list[str]` |  | Method. |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `Migration`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Container for a set of migration operations with metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `revision` | `str` |  |
| `slug` | `str` |  |
| `models` | `list[str]` | `field(default_factory=list)` |
| `dependencies` | `list[str]` | `field(default_factory=list)` |
| `operations` | `list[Operation]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile_upgrade` | `def compile_upgrade(self, dialect: str = 'sqlite') -> list[str]` |  | Compile all operations to forward SQL. |
| `compile_downgrade` | `def compile_downgrade(self, dialect: str = 'sqlite') -> list[str]` |  | Compile all operations (reversed) to rollback SQL. |
| `get_python_ops` | `def get_python_ops(self) -> list[RunPython]` |  | Get all RunPython operations (for the runner). |
| `describe` | `def describe(self) -> str` |  | Method. |

### Class: `MigrationRecord`

- Source: `aquilia/models/migration_runner.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A record in the aquilia_migrations tracking table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `revision` | `str` |  |
| `slug` | `str` |  |
| `checksum` | `str` |  |
| `applied_at` | `str &#124; None` | `None` |

### Class: `MigrationRunner`

- Source: `aquilia/models/migration_runner.py`
- Bases: `object`
- Summary: Applies and tracks migrations against an AquiliaDatabase.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `ensure_tracking_table` | `async def ensure_tracking_table(self) -> None` |  | Create the aquilia_migrations tracking table if it doesn't exist. |
| `get_applied` | `async def get_applied(self) -> list[str]` |  | Get list of applied revision IDs, ordered by application time. |
| `get_pending` | `async def get_pending(self) -> list[Path]` |  | Get migration files that haven't been applied yet. |
| `status` | `async def status(self) -> dict[str, Any]` |  | Get migration status -- applied, pending, totals. |
| `show_status` | `async def show_status(self) -> str` |  | Return a human-readable status string. |
| `plan` | `async def plan(self, target: str &#124; None = None) -> list[str]` |  | Preview migrations without executing (--plan / dry-run). |
| `sqlmigrate` | `async def sqlmigrate(self, revision: str) -> list[str]` |  | Get the SQL for a specific migration (aq db sqlmigrate). |
| `migrate` | `async def migrate(self, *, target: str &#124; None = None, fake: bool = False, database: str &#124; None = None) -> list[str]` |  | Apply all pending migrations. |
| `verify_checksums` | `async def verify_checksums(self) -> list[dict[str, str]]` |  | Verify that applied migration files haven't been tampered with. |

### Class: `MigrationOps`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Summary: Migration operation builder -- used inside migration scripts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `dialect` | `def dialect(self) -> str` | property | Method. |
| `dialect` | `def dialect(self, value: str) -> None` | dialect.setter | Method. |
| `create_table` | `def create_table(self, name: str, columns: list[str]) -> None` |  | Generate CREATE TABLE statement. |
| `drop_table` | `def drop_table(self, name: str, cascade: bool = False) -> None` |  | Generate DROP TABLE statement. |
| `rename_table` | `def rename_table(self, old_name: str, new_name: str) -> None` |  | Generate RENAME TABLE statement (dialect-aware). |
| `add_column` | `def add_column(self, table: str, column_def: str) -> None` |  | Generate ALTER TABLE ADD COLUMN. |
| `drop_column` | `def drop_column(self, table: str, column: str) -> None` |  | Generate ALTER TABLE DROP COLUMN (dialect-aware). |
| `rename_column` | `def rename_column(self, table: str, old_name: str, new_name: str) -> None` |  | Generate ALTER TABLE RENAME COLUMN (dialect-aware). |
| `alter_column` | `def alter_column(self, table: str, column: str, *, type: str &#124; None = None, nullable: bool &#124; None = None, default: Any &#124; None = None, drop_default: bool = False) -> None` |  | Generate ALTER TABLE ALTER COLUMN (dialect-aware). |
| `create_index` | `def create_index(self, name: str, table: str, columns: list[str], unique: bool = False, condition: str &#124; None = None) -> None` |  | Generate CREATE INDEX (with optional partial index condition). |
| `drop_index` | `def drop_index(self, name: str, table: str &#124; None = None) -> None` |  | Generate DROP INDEX (dialect-aware). |
| `add_constraint` | `def add_constraint(self, table: str, constraint_sql: str) -> None` |  | Generate ALTER TABLE ADD CONSTRAINT. |
| `drop_constraint` | `def drop_constraint(self, table: str, name: str) -> None` |  | Generate ALTER TABLE DROP CONSTRAINT (not supported on SQLite). |
| `execute_sql` | `def execute_sql(self, sql: str) -> None` |  | Add raw SQL statement. |
| `run_python` | `def run_python(self, func: Callable) -> None` |  | Mark a Python callable as a data-migration step. |
| `pk` | `def pk(name: str = 'id', *, dialect: str = 'sqlite') -> str` | staticmethod | Primary key column definition. |
| `bigpk` | `def bigpk(name: str = 'id', *, dialect: str = 'sqlite') -> str` | staticmethod | Big integer primary key. |
| `integer` | `def integer(name: str, nullable: bool = False, unique: bool = False) -> str` | staticmethod | Method. |
| `biginteger` | `def biginteger(name: str, nullable: bool = False, unique: bool = False, *, dialect: str = 'sqlite') -> str` | staticmethod | Big integer column. |
| `varchar` | `def varchar(name: str, length: int = 255, nullable: bool = False, unique: bool = False) -> str` | staticmethod | Method. |
| `text` | `def text(name: str, nullable: bool = False) -> str` | staticmethod | Method. |
| `blob` | `def blob(name: str, nullable: bool = False) -> str` | staticmethod | Method. |
| `boolean` | `def boolean(name: str, nullable: bool = False, default: bool &#124; None = None, *, dialect: str = 'sqlite') -> str` | staticmethod | Boolean column (dialect-aware). |
| `timestamp` | `def timestamp(name: str, nullable: bool = False, default: str &#124; None = None, *, dialect: str = 'sqlite') -> str` | staticmethod | Timestamp column (dialect-aware). |
| `decimal` | `def decimal(name: str, max_digits: int = 10, decimal_places: int = 2, nullable: bool = False, *, dialect: str = 'sqlite') -> str` | staticmethod | Decimal / numeric column. |
| `json` | `def json(name: str, nullable: bool = False, *, dialect: str = 'sqlite') -> str` | staticmethod | JSON column (dialect-aware). |
| `uuid` | `def uuid(name: str, nullable: bool = False, *, dialect: str = 'sqlite') -> str` | staticmethod | UUID column (dialect-aware). |
| `real` | `def real(name: str, nullable: bool = False) -> str` | staticmethod | Method. |
| `foreign_key` | `def foreign_key(name: str, ref_table: str, ref_column: str = 'id', on_delete: str = 'CASCADE', nullable: bool = False) -> str` | staticmethod | Foreign key column with inline REFERENCES. |
| `get_statements` | `def get_statements(self) -> list[Any]` |  | Return accumulated SQL statements (strings and callables). |
| `clear` | `def clear(self) -> None` |  | Reset accumulated statements. |

### Class: `MigrationInfo`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Metadata for a single migration file.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `revision` | `str` |  |
| `slug` | `str` |  |
| `models` | `list[str]` |  |
| `path` | `Path &#124; None` | `None` |
| `applied` | `bool` | `False` |

### Class: `MigrationRunner`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Summary: Applies and tracks migrations against an AquiliaDatabase.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `ensure_tracking_table` | `async def ensure_tracking_table(self) -> None` |  | Create the migrations tracking table if it doesn't exist. |
| `get_applied` | `async def get_applied(self) -> list[str]` |  | Get list of applied revision IDs. |
| `get_pending` | `async def get_pending(self) -> list[Path]` |  | Get migration files that haven't been applied yet. |
| `status` | `async def status(self) -> dict[str, Any]` |  | Get migration status -- applied, pending, and total counts. |
| `show_status` | `async def show_status(self) -> str` |  | Return a human-readable status string. |
| `dry_run` | `async def dry_run(self, target: str &#124; None = None) -> list[str]` |  | Preview migrations without executing. Returns list of SQL strings. |
| `apply_migration` | `async def apply_migration(self, path: Path) -> None` |  | Apply a single migration file. |
| `migrate` | `async def migrate(self, target: str &#124; None = None) -> list[str]` |  | Apply all pending migrations. |
| `verify_checksums` | `async def verify_checksums(self) -> list[dict[str, str]]` |  | Verify that applied migration files haven't been tampered with. |

### Class: `Options`

- Source: `aquilia/models/options.py`
- Bases: `object`
- Summary: Parsed model options from inner Meta class.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `label` | `def label(self) -> str` | property | Return app_label.ModelName style label. |
| `label_lower` | `def label_lower(self) -> str` | property | Return app_label.model_name style label (lowercase). |

### Class: `AMDLParseError`

- Source: `aquilia/models/parser.py`
- Bases: `AMDLParseFault`
- Summary: Raised when AMDL parsing fails.

### Class: `QNode`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Composable filter node for complex WHERE clauses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `AND` |  | `'AND'` |
| `OR` |  | `'OR'` |

### Class: `Prefetch`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Custom prefetch descriptor for prefetch_related().

### Class: `Q`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Aquilia QuerySet -- chainable, immutable, async-terminal query builder.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `order_by` |  | `order` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any) -> Q` |  | Add raw WHERE clause (Aquilia-only syntax). |
| `filter` | `def filter(self, *q_nodes: Any, **kwargs: Any) -> Q` |  | Field lookup filter. |
| `exclude` | `def exclude(self, *q_nodes: Any, **kwargs: Any) -> Q` |  | Negated filter -- exclude matching records. |
| `order` | `def order(self, *fields: Any) -> Q` |  | ORDER BY -- Aquilia's primary ordering method. |
| `union` | `def union(self, *querysets: Q, all: bool = False) -> Q` |  | Combine this queryset with others using UNION. |
| `intersection` | `def intersection(self, *querysets: Q) -> Q` |  | Combine with INTERSECT -- only rows in ALL querysets. |
| `difference` | `def difference(self, *querysets: Q) -> Q` |  | Combine with EXCEPT -- rows in this set but not in others. |
| `limit` | `def limit(self, n: int) -> Q` |  | Set LIMIT on query results. |
| `offset` | `def offset(self, n: int) -> Q` |  | Set OFFSET for pagination. |
| `distinct` | `def distinct(self) -> Q` |  | Apply SELECT DISTINCT. |
| `only` | `def only(self, *fields: str) -> Q` |  | Load only specified fields (deferred loading for others). |
| `defer` | `def defer(self, *fields: str) -> Q` |  | Defer loading of specified fields. |
| `annotate` | `def annotate(self, **expressions: Any) -> Q` |  | Add aggregate/expression annotations to each row. |
| `group_by` | `def group_by(self, *fields: str) -> Q` |  | GROUP BY clause. |
| `having` | `def having(self, clause: str, *args: Any) -> Q` |  | HAVING clause (use after group_by). |
| `select_related` | `def select_related(self, *fields: str) -> Q` |  | Eager-load FK/OneToOne relations via JOINs. |
| `prefetch_related` | `def prefetch_related(self, *lookups: Any) -> Q` |  | Prefetch related objects via separate queries. |
| `select_for_update` | `def select_for_update(self, *, nowait: bool = False, skip_locked: bool = False) -> Q` |  | Lock selected rows (SELECT ... FOR UPDATE). |
| `using` | `def using(self, db_alias: str) -> Q` |  | Target a specific database for this query. |
| `apply_q` | `def apply_q(self, q_node: QNode) -> Q` |  | Apply a QNode filter to this queryset (Aquilia-only). |
| `iterator` | `def iterator(self, chunk_size: int = 2000) -> Q` |  | Return a queryset that uses chunked iteration for memory efficiency. |
| `none` | `def none(self) -> Q` |  | Return an empty queryset that evaluates to []. |
| `all` | `async def all(self) -> list[Model]` |  | Execute and return all matching rows as model instances. |
| `one` | `async def one(self) -> Model` |  | Return exactly one row. Raises if 0 or >1 (Aquilia-only). |
| `first` | `async def first(self) -> Model &#124; None` |  | Return first matching row or None. |
| `last` | `async def last(self) -> Model &#124; None` |  | Return last matching row or None (reverses ordering). |
| `latest` | `async def latest(self, field_name: str &#124; None = None) -> Model` |  | Return the latest record by date field. |
| `earliest` | `async def earliest(self, field_name: str &#124; None = None) -> Model` |  | Return the earliest record by date field. |
| `count` | `async def count(self) -> int` |  | Return count of matching rows. |
| `exists` | `async def exists(self) -> bool` |  | Check if any matching rows exist. |
| `update` | `async def update(self, values: dict[str, Any] &#124; None = None, **kwargs: Any) -> int` |  | Update matching rows. Returns number of affected rows. |
| `delete` | `async def delete(self) -> int` |  | Delete matching rows. Returns number of deleted rows. |
| `values` | `async def values(self, *fields: str) -> list[dict[str, Any]]` |  | Return rows as dicts with only specified field values. |
| `values_list` | `async def values_list(self, *fields: str, flat: bool = False) -> list[Any]` |  | Return field values as tuples, or flat list if single field + flat=True. |
| `in_bulk` | `async def in_bulk(self, id_list: list[Any], *, batch_size: int = 999) -> dict[Any, Model]` |  | Return a dict mapping PKs to instances for the given ID list. |
| `aggregate` | `async def aggregate(self, **expressions: Any) -> dict[str, Any]` |  | Compute aggregates and return a dict. |
| `create` | `async def create(self, **data: Any) -> Model` |  | Create a new record (shortcut on queryset). |
| `get_or_create` | `async def get_or_create(self, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` |  | Get existing or create new. |
| `update_or_create` | `async def update_or_create(self, defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` |  | Update existing or create new. |
| `find_or_create` | `async def find_or_create(self, defaults: dict[str, Any] &#124; None = None, create_defaults: dict[str, Any] &#124; None = None, **lookup: Any) -> tuple[Model, bool]` |  | Atomically find an existing record or create a new one. |
| `explain` | `async def explain(self, *, format: str &#124; None = None) -> str` |  | Return the query execution plan (EXPLAIN). |
| `query` | `def query(self) -> str` | property | Return the raw SQL that would be executed. |

### Class: `ModelRegistry`

- Source: `aquilia/models/registry.py`
- Bases: `object`
- Summary: Global registry for all Model subclasses.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(cls, model_cls: type[Model]) -> None` | classmethod | Register a model class. |
| `get` | `def get(cls, name: str) -> type[Model] &#124; None` | classmethod | Get model class by name. |
| `all_models` | `def all_models(cls) -> dict[str, type[Model]]` | classmethod | Get all registered models. |
| `get_app_models` | `def get_app_models(cls, app_label: str) -> dict[str, type[Model]]` | classmethod | Get all models for a specific app. |
| `set_database` | `def set_database(cls, db: AquiliaDatabase) -> None` | classmethod | Set global database for all models. |
| `get_database` | `def get_database(cls) -> AquiliaDatabase &#124; None` | classmethod | Method. |
| `create_tables` | `async def create_tables(cls, db: AquiliaDatabase &#124; None = None) -> list[str]` | classmethod | Create tables for all registered models in topological order. |
| `drop_tables` | `async def drop_tables(cls, db: AquiliaDatabase &#124; None = None) -> list[str]` | classmethod | Drop all registered model tables (dangerous!). |
| `reset` | `def reset(cls) -> None` | classmethod | Clear registry (for testing). |
| `check_constraints` | `def check_constraints(cls) -> list[str]` | classmethod | Validate all model constraints and return a list of issues. |
| `on_startup` | `async def on_startup(self) -> None` |  | Method. |
| `on_shutdown` | `async def on_shutdown(self) -> None` |  | Method. |

### Class: `Q`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Summary: Aquilia Query builder -- chainable, async-terminal.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any) -> Q` |  | Add WHERE clause. |
| `filter` | `def filter(self, **kwargs: Any) -> Q` |  | Field lookups. |
| `order` | `def order(self, *fields: str) -> Q` |  | Add ORDER BY clause. |
| `limit` | `def limit(self, n: int) -> Q` |  | Set LIMIT. |
| `offset` | `def offset(self, n: int) -> Q` |  | Set OFFSET. |
| `all` | `async def all(self) -> list[ModelProxy]` |  | Execute query and return all matching rows as proxy instances. |
| `one` | `async def one(self) -> ModelProxy` |  | Execute query and return exactly one row. Raises ModelNotFoundFault if 0 or >1. |
| `first` | `async def first(self) -> ModelProxy &#124; None` |  | Return first matching row or None. |
| `count` | `async def count(self) -> int` |  | Return count of matching rows. |
| `update` | `async def update(self, values: dict[str, Any]) -> int` |  | Update matching rows. Returns affected row count. |
| `delete` | `async def delete(self) -> int` |  | Delete matching rows. Returns affected row count. |

### Class: `ModelRegistry`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Decorators: `service`
- Summary: Central registry for AMDL models and their runtime proxies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `async def on_startup(self) -> None` |  | Lifecycle hook -- create tables for all registered models. |
| `on_shutdown` | `async def on_shutdown(self) -> None` |  | Lifecycle hook -- cleanup (reserved for future use). |
| `register_model` | `def register_model(self, model: ModelNode) -> type[ModelProxy]` |  | Register an AMDL model and generate its runtime proxy class. |
| `get_model` | `def get_model(self, name: str) -> ModelNode &#124; None` |  | Get parsed model AST by name. |
| `get_proxy` | `def get_proxy(self, name: str) -> type[ModelProxy] &#124; None` |  | Get generated proxy class by model name. |
| `all_models` | `def all_models(self) -> list[ModelNode]` |  | Get all registered model nodes. |
| `all_proxies` | `def all_proxies(self) -> dict[str, type[ModelProxy]]` |  | Get all proxy classes. |
| `create_tables` | `async def create_tables(self, db: AquiliaDatabase &#124; None = None) -> list[str]` |  | Create all registered model tables. |
| `set_database` | `def set_database(self, db: AquiliaDatabase) -> None` |  | Update database reference for all proxies. |
| `emit_python` | `def emit_python(self) -> str` |  | Generate Python source code for all model proxies. |

### Class: `ModelProxy`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Summary: Base class for AMDL-generated model proxies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize model instance to dict. |

### Class: `SchemaDiff`

- Source: `aquilia/models/schema_snapshot.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of comparing two snapshots.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `added_models` | `list[str]` | `field(default_factory=list)` |
| `removed_models` | `list[str]` | `field(default_factory=list)` |
| `renamed_models` | `list[tuple[str, str]]` | `field(default_factory=list)` |
| `altered_models` | `dict[str, ModelDiff]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `has_changes` | `def has_changes(self) -> bool` | property | Method. |

### Class: `ModelDiff`

- Source: `aquilia/models/schema_snapshot.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Changes within a single model.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `added_fields` | `list[str]` | `field(default_factory=list)` |
| `removed_fields` | `list[str]` | `field(default_factory=list)` |
| `renamed_fields` | `list[tuple[str, str]]` | `field(default_factory=list)` |
| `altered_fields` | `list[str]` | `field(default_factory=list)` |
| `added_indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `removed_indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `has_changes` | `def has_changes(self) -> bool` | property | Method. |

### Class: `Signal`

- Source: `aquilia/models/signals.py`
- Bases: `object`
- Summary: A signal that can be connected to receiver functions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `def connect(self, receiver: Callable = None, *, sender: type &#124; None = None, weak: bool = False, priority: int = 100)` |  | Connect a receiver function. Can be used as a decorator. |
| `disconnect` | `def disconnect(self, receiver: Callable, *, sender: type &#124; None = None) -> bool` |  | Disconnect a receiver. |
| `send` | `async def send(self, sender: type, **kwargs) -> list[Any]` |  | Fire the signal, calling all connected receivers. |
| `send_sync` | `def send_sync(self, sender: type, **kwargs) -> list[Any]` |  | Fire the signal synchronously (for sync receivers only). |
| `robust_send` | `async def robust_send(self, sender: type, **kwargs) -> list[Any]` |  | Fire the signal, catching exceptions from each receiver. |
| `receivers` | `def receivers(self) -> list[Callable]` | property | List of connected receiver functions (resolved, alive only). |
| `has_listeners` | `def has_listeners(self, sender: type &#124; None = None) -> bool` |  | Check if any receivers are connected (optionally for a sender). |
| `connected` | `def connected(self, fn: Callable, *, sender: type &#124; None = None, priority: int = 100)` | contextlib.contextmanager | Context manager for temporary signal connection. |
| `clear` | `def clear(self) -> None` |  | Remove all receivers (useful for testing). |

### Class: `SQLBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: SELECT query builder with safe parameter binding.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `select` | `def select(self, *columns: str) -> SQLBuilder` |  | Set columns to select. |
| `from_table` | `def from_table(self, table: str, alias: str &#124; None = None) -> SQLBuilder` |  | Set the FROM table. |
| `distinct` | `def distinct(self) -> SQLBuilder` |  | Add DISTINCT modifier. |
| `join` | `def join(self, table: str, on: str, join_type: str = 'INNER', params: list[Any] &#124; None = None) -> SQLBuilder` |  | Add a JOIN clause. |
| `left_join` | `def left_join(self, table: str, on: str, params: list[Any] &#124; None = None) -> SQLBuilder` |  | Method. |
| `right_join` | `def right_join(self, table: str, on: str, params: list[Any] &#124; None = None) -> SQLBuilder` |  | Method. |
| `where` | `def where(self, clause: str, *args: Any) -> SQLBuilder` |  | Add a WHERE condition with parameters. |
| `where_in` | `def where_in(self, column: str, values: Sequence[Any]) -> SQLBuilder` |  | Add a WHERE ... IN (...) clause. |
| `group_by` | `def group_by(self, *columns: str) -> SQLBuilder` |  | Add GROUP BY columns. |
| `having` | `def having(self, clause: str, *args: Any) -> SQLBuilder` |  | Add HAVING condition. |
| `order_by` | `def order_by(self, *fields: str) -> SQLBuilder` |  | Add ORDER BY clause. |
| `limit` | `def limit(self, n: int) -> SQLBuilder` |  | Method. |
| `offset` | `def offset(self, n: int) -> SQLBuilder` |  | Method. |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Build the final SQL string and parameter list. |
| `build_count` | `def build_count(self) -> tuple[str, list[Any]]` |  | Build a COUNT(*) version of this query. |

### Class: `InsertBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT query builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `columns` | `def columns(self, *cols: str) -> InsertBuilder` |  | Method. |
| `values` | `def values(self, *vals: Any) -> InsertBuilder` |  | Method. |
| `from_dict` | `def from_dict(self, data: dict[str, Any]) -> InsertBuilder` |  | Set columns and values from a dict. |
| `returning` | `def returning(self, column: str) -> InsertBuilder` |  | Add RETURNING clause (PostgreSQL). |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Method. |
| `build_many` | `def build_many(self, rows: list[dict[str, Any]]) -> tuple[str, list[list[Any]]]` |  | Build INSERT for executemany. |

### Class: `UpdateBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: UPDATE query builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set` | `def set(self, **kwargs: Any) -> UpdateBuilder` |  | Method. |
| `set_dict` | `def set_dict(self, data: dict[str, Any]) -> UpdateBuilder` |  | Method. |
| `where` | `def where(self, clause: str, *args: Any) -> UpdateBuilder` |  | Method. |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Method. |

### Class: `DeleteBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: DELETE query builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any) -> DeleteBuilder` |  | Method. |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Method. |

### Class: `CreateTableBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: CREATE TABLE DDL builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `column` | `def column(self, definition: str) -> CreateTableBuilder` |  | Method. |
| `constraint` | `def constraint(self, definition: str) -> CreateTableBuilder` |  | Method. |
| `build` | `def build(self) -> str` |  | Method. |

### Class: `AlterTableBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: ALTER TABLE DDL builder -- dialect-aware.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_column` | `def add_column(self, column_def: str) -> AlterTableBuilder` |  | Add a column. |
| `drop_column` | `def drop_column(self, column: str) -> AlterTableBuilder` |  | Drop a column (SQLite 3.35+, PostgreSQL, MySQL). |
| `rename_column` | `def rename_column(self, old_name: str, new_name: str) -> AlterTableBuilder` |  | Rename a column (SQLite 3.25+, PostgreSQL, MySQL 8+). |
| `rename_to` | `def rename_to(self, new_name: str) -> AlterTableBuilder` |  | Rename the table. |
| `add_constraint` | `def add_constraint(self, constraint_sql: str) -> AlterTableBuilder` |  | Add a constraint. |
| `drop_constraint` | `def drop_constraint(self, name: str) -> AlterTableBuilder` |  | Drop a constraint (not supported on SQLite). |
| `alter_column_type` | `def alter_column_type(self, column: str, new_type: str) -> AlterTableBuilder` |  | Change column type (PostgreSQL only; generates comment for SQLite). |
| `set_not_null` | `def set_not_null(self, column: str) -> AlterTableBuilder` |  | Set NOT NULL on a column. |
| `drop_not_null` | `def drop_not_null(self, column: str) -> AlterTableBuilder` |  | Drop NOT NULL from a column. |
| `set_default` | `def set_default(self, column: str, default_value: str) -> AlterTableBuilder` |  | Set a default value on a column. |
| `drop_default` | `def drop_default(self, column: str) -> AlterTableBuilder` |  | Drop the default value from a column. |
| `build` | `def build(self) -> list[str]` |  | Return the list of ALTER TABLE DDL statements. |

### Class: `UpsertBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT ... ON CONFLICT (upsert) query builder -- dialect-aware.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `columns` | `def columns(self, *cols: str) -> UpsertBuilder` |  | Method. |
| `values` | `def values(self, *vals: Any) -> UpsertBuilder` |  | Method. |
| `from_dict` | `def from_dict(self, data: dict[str, Any]) -> UpsertBuilder` |  | Set columns and values from a dict. |
| `conflict_target` | `def conflict_target(self, *columns: str) -> UpsertBuilder` |  | Set the conflict detection columns (unique constraint). |
| `update_columns` | `def update_columns(self, *columns: str) -> UpsertBuilder` |  | Set columns to update on conflict. |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Method. |

### Class: `UpsertIgnoreBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT ... ON CONFLICT DO NOTHING query builder -- dialect-aware.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `columns` | `def columns(self, *cols: str) -> UpsertIgnoreBuilder` |  | Set the column names for the INSERT. |
| `values` | `def values(self, *vals: Any) -> UpsertIgnoreBuilder` |  | Set the values for the INSERT. |
| `from_dict` | `def from_dict(self, data: dict[str, Any]) -> UpsertIgnoreBuilder` |  | Set columns and values from a dict. |
| `conflict_target` | `def conflict_target(self, *columns: str) -> UpsertIgnoreBuilder` |  | Set the conflict detection columns (unique constraint). |
| `build` | `def build(self) -> tuple[str, list[Any]]` |  | Build the SQL statement and parameters. |

### Class: `DatabaseNotReadyError`

- Source: `aquilia/models/startup_guard.py`
- Bases: `SystemExit`
- Summary: Raised when the database is not ready at server startup.

### Class: `Atomic`

- Source: `aquilia/models/transactions.py`
- Bases: `object`
- Summary: Async context manager for database transactions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_commit` | `def on_commit(self, fn: Callable) -> None` |  | Register a function to call after successful outermost commit. |
| `on_rollback` | `def on_rollback(self, fn: Callable) -> None` |  | Register a function to call if this block rolls back. |
| `savepoint` | `async def savepoint(self) -> str` |  | Create an explicit savepoint within this atomic block. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, savepoint_id: str) -> None` |  | Roll back to a specific savepoint. |
| `release_savepoint` | `async def release_savepoint(self, savepoint_id: str) -> None` |  | Release (commit) a savepoint. |

### Class: `TransactionManager`

- Source: `aquilia/models/transactions.py`
- Bases: `object`
- Summary: Higher-level transaction manager with properly scoped on_commit hooks.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_commit` | `def on_commit(self, func: Callable) -> None` |  | Register a function to be called after successful commit. |
| `on_rollback` | `def on_rollback(self, func: Callable) -> None` |  | Register a function to be called on rollback. |
| `atomic` | `async def atomic(self, **kwargs) -> AsyncIterator[Atomic]` | asynccontextmanager | Use as: async with manager.atomic() as txn: ... |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `normalize_on_delete` | `aquilia/models/deletion.py` | `def normalize_on_delete(action: Any) -> Any` | Normalize an on_delete value to its canonical constant. |
| `lookup_registry` | `aquilia/models/fields/lookups.py` | `def lookup_registry() -> dict[str, type[Lookup]]` | Return a copy of the lookup registry. |
| `register_lookup` | `aquilia/models/fields/lookups.py` | `def register_lookup(name: str, cls: type[Lookup]) -> None` | Register a custom lookup type. |
| `resolve_lookup` | `aquilia/models/fields/lookups.py` | `def resolve_lookup(field_name: str, lookup_name: str, value: Any) -> Lookup` | Resolve a lookup name to a Lookup instance. |
| `raw_sql_to_operations` | `aquilia/models/migration_dsl.py` | `def raw_sql_to_operations(upgrade_sql: str, downgrade_sql: str = '') -> list[Operation]` | Convert raw SQL strings into a list of RunSQL operations. |
| `generate_dsl_migration` | `aquilia/models/migration_gen.py` | `def generate_dsl_migration(model_classes: list, migrations_dir: str &#124; Path, snapshot_path: str &#124; Path &#124; None = None, slug: str &#124; None = None) -> Path &#124; None` | Generate a DSL migration file from the diff between the current |
| `check_db_exists` | `aquilia/models/migration_runner.py` | `def check_db_exists(db_url: str) -> bool` | Check if a SQLite database file exists WITHOUT creating WAL/SHM files. |
| `check_migrations_applied` | `aquilia/models/migration_runner.py` | `def check_migrations_applied(db_url: str, migrations_dir: str &#124; Path = 'migrations') -> bool` | Check if there are unapplied migrations WITHOUT creating WAL/SHM. |
| `generate_migration_file` | `aquilia/models/migrations.py` | `def generate_migration_file(models: list[ModelNode], migrations_dir: str &#124; Path, slug: str &#124; None = None, dialect: str = 'sqlite') -> Path` | Generate a migration file from AMDL model nodes. |
| `generate_migration_from_models` | `aquilia/models/migrations.py` | `def generate_migration_from_models(model_classes: list, migrations_dir: str &#124; Path, slug: str &#124; None = None, dialect: str = 'sqlite') -> Path` | Generate a migration file from new Python Model subclasses. |
| `parse_amdl` | `aquilia/models/parser.py` | `def parse_amdl(source: str, file_path: str = '<string>') -> AMDLFile` | Parse AMDL source text into an AMDLFile. |
| `parse_amdl_file` | `aquilia/models/parser.py` | `def parse_amdl_file(path: str &#124; Path) -> AMDLFile` | Parse an `.amdl` file from disk. |
| `parse_amdl_directory` | `aquilia/models/parser.py` | `def parse_amdl_directory(directory: str &#124; Path) -> list[AMDLFile]` | Parse all `.amdl` files in a directory (non-recursive). |
| `generate_create_table_sql` | `aquilia/models/runtime.py` | `def generate_create_table_sql(model: ModelNode, dialect: str = 'sqlite') -> str` | Generate CREATE TABLE SQL from a ModelNode. |
| `generate_create_index_sql` | `aquilia/models/runtime.py` | `def generate_create_index_sql(model: ModelNode, dialect: str = 'sqlite') -> list[str]` | Generate CREATE INDEX statements for non-unique indexes. |
| `create_snapshot` | `aquilia/models/schema_snapshot.py` | `def create_snapshot(model_classes: list) -> dict[str, Any]` | Create a schema snapshot from a list of Model subclasses. |
| `save_snapshot` | `aquilia/models/schema_snapshot.py` | `def save_snapshot(snapshot: dict[str, Any], path: Path) -> None` | Write snapshot to file in CROUS binary format. |
| `load_snapshot` | `aquilia/models/schema_snapshot.py` | `def load_snapshot(path: Path) -> dict[str, Any] &#124; None` | Load snapshot from file in CROUS binary format. |
| `compute_diff` | `aquilia/models/schema_snapshot.py` | `def compute_diff(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> SchemaDiff` | Compute the diff between two schema snapshots. |
| `diff_to_operations` | `aquilia/models/schema_snapshot.py` | `def diff_to_operations(diff: SchemaDiff, old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> list[Operation]` | Convert a SchemaDiff into a list of DSL operations. |
| `receiver` | `aquilia/models/signals.py` | `def receiver(signal: Signal, *, sender: type &#124; None = None)` | Shorthand decorator to connect a function to a signal. |
| `check_db_ready` | `aquilia/models/startup_guard.py` | `def check_db_ready(db_url: str = 'sqlite:///db.sqlite3', migrations_dir: str &#124; Path = 'migrations', *, auto_migrate: bool &#124; None = None) -> bool` | Check if the database is ready for the application to start. |
| `atomic` | `aquilia/models/transactions.py` | `def atomic(db: AquiliaDatabase &#124; None = None, *, savepoint: bool = True, durable: bool = False, isolation: str &#124; None = None) -> Atomic` | Create an atomic transaction context manager. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `CASCADE` | `aquilia/models/deletion.py` | `'CASCADE'` |
| `SET_NULL` | `aquilia/models/deletion.py` | `'SET NULL'` |
| `PROTECT` | `aquilia/models/deletion.py` | `'PROTECT'` |
| `SET_DEFAULT` | `aquilia/models/deletion.py` | `'SET DEFAULT'` |
| `DO_NOTHING` | `aquilia/models/deletion.py` | `'DO NOTHING'` |
| `RESTRICT` | `aquilia/models/deletion.py` | `'RESTRICT'` |
| `_ON_DELETE_ALIASES` | `aquilia/models/deletion.py` | `{'CASCADE': CASCADE, 'SET_NULL': SET_NULL, 'SET NULL': SET_NULL, 'SETNULL': SET_NULL, 'PROTECT': PROTECT, 'SET_DEFAULT': SET_DEFAULT, 'SET DEFAULT': SET_DEFAULT` |
| `_SAFE_FUNC_RE` | `aquilia/models/expression.py` | `re.compile('^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)` |
| `_SAFE_TYPE_RE` | `aquilia/models/expression.py` | `re.compile('^[A-Z][A-Z0-9_ ]*(?:\\([0-9]+(?:\\s*,\\s*[0-9]+)?\\))?$', re.IGNORECASE)` |
| `_REGISTRY` | `aquilia/models/fields/lookups.py` | `dict[str, type[Lookup]]` |
| `_ON_DELETE_SQL_MAP` | `aquilia/models/fields_module.py` | `dict[str, str]` |
| `UNSET` | `aquilia/models/fields_module.py` | `_Unset()` |
| `M` | `aquilia/models/manager.py` | `TypeVar('M', bound='BaseManager')` |
| `_ON_DELETE_SQL_MAP` | `aquilia/models/migration_dsl.py` | `dict[str, str]` |
| `_SENTINEL` | `aquilia/models/migration_dsl.py` | `_SentinelType()` |
| `C` | `aquilia/models/migration_dsl.py` | `columns` |
| `MIGRATION_TABLE` | `aquilia/models/migration_runner.py` | `'aquilia_migrations'` |
| `MIGRATION_TABLE` | `aquilia/models/migrations.py` | `'aquilia_migrations'` |
| `ALLOWED_DEFAULTS` | `aquilia/models/parser.py` | `frozenset({'now_utc()', 'uuid4()', 'seq()'})` |
| `ALLOWED_DEFAULT_PATTERN` | `aquilia/models/parser.py` | `re.compile('^(now_utc\\(\\) &#124; uuid4\\(\\) &#124; seq\\(\\) &#124; env\\("[A-Za-z_][A-Za-z0-9_]*"\\))$')` |
| `RE_MODEL_OPEN` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*MODEL\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*≫\\s*$')` |
| `RE_MODEL_CLOSE` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*/MODEL\\s*≫\\s*$')` |
| `RE_SLOT` | `aquilia/models/parser.py` | `re.compile('^\\s*slot\\s+([a-z_][a-z0-9_]*)\\s*::\\s*([A-Za-z]+(?:\\([^)]*\\))?)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_LINK` | `aquilia/models/parser.py` | `re.compile('^\\s*link\\s+([a-z_][a-z0-9_]*)\\s*->\\s*(ONE &#124; MANY &#124; MANY_THROUGH)\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_INDEX` | `aquilia/models/parser.py` | `re.compile('^\\s*index\\s+\\[([^\\]]+)\\]\\s*(unique)?\\s*$')` |
| `RE_HOOK` | `aquilia/models/parser.py` | `re.compile('^\\s*hook\\s+([a-z_][a-z0-9_]*)\\s*->\\s*([a-z_][a-z0-9_]*)\\s*$')` |
| `RE_META` | `aquilia/models/parser.py` | `re.compile('^\\s*meta\\s+([a-z_][a-z0-9_]*)\\s*=\\s*"([^"]*)"\\s*$')` |
| `RE_NOTE` | `aquilia/models/parser.py` | `re.compile('^\\s*note\\s+"([^"]*)"\\s*$')` |
| `FIELD_TYPE_MAP` | `aquilia/models/parser.py` | `{ft.value: ft for ft in FieldType}` |
| `_SAFE_FIELD_RE` | `aquilia/models/query.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_EXPR_OP_MAP` | `aquilia/models/query.py` | `{'exact': '=', 'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=', 'ne': '!='}` |
| `_SAFE_DEFAULTS` | `aquilia/models/runtime.py` | `{'now_utc()': lambda: datetime.datetime.now(datetime.timezone.utc), 'uuid4()': lambda: str(uuid.uuid4()), 'seq()': lambda: None}` |
| `SQLITE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'INTEGER', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'INTEGER', ` |
| `POSTGRES_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'SERIAL', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'BOOLEAN', Fi` |
| `MYSQL_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'TINYINT(1)'` |
| `ORACLE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'NUMBER(10)', FieldType.INT: 'NUMBER(10)', FieldType.BIGINT: 'NUMBER(19)', FieldType.STR: 'VARCHAR2', FieldType.TEXT: 'CLOB', FieldType.BOOL: '` |
| `_TYPE_MAPS` | `aquilia/models/runtime.py` | `{'sqlite': SQLITE_TYPE_MAP, 'postgresql': POSTGRES_TYPE_MAP, 'mysql': MYSQL_TYPE_MAP, 'oracle': ORACLE_TYPE_MAP}` |
| `SNAPSHOT_VERSION` | `aquilia/models/schema_snapshot.py` | `1` |
| `RENAME_THRESHOLD` | `aquilia/models/schema_snapshot.py` | `0.6` |
| `_YELLOW` | `aquilia/models/startup_guard.py` | `'\x1b[93m'` |
| `_RESET` | `aquilia/models/startup_guard.py` | `'\x1b[0m'` |
| `_BOLD` | `aquilia/models/startup_guard.py` | `'\x1b[1m'` |
| `_SP_NAME_RE` | `aquilia/models/transactions.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
