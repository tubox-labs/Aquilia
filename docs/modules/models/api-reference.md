# Models API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`AMDLFile`, `AMDLParseError`, `AMDLParseFault`, `Abs`, `Aggregate`, `ArrayAgg`, `ArrayField`, `Atomic`, `AutoField`, `AutoNowMixin`, `Avg`, `BaseManager`, `BaseValidator`, `BigAutoField`, `BigIntegerField`, `BigIntegerRangeField`, `BinaryField`, `BoolAnd`, `BoolOr`, `BooleanField`, `BrinIndex`, `C`, `CASCADE`, `CICharField`, `CIEmailField`, `CITextField`, `Case`, `Cast`, `CharField`, `CheckConstraint`, `ChoiceMixin`, `Choices`, `Coalesce`, `Col`, `ColumnDef`, `Combinable`, `CombinedExpression`, `CompositeAttribute`, `CompositeField`, `CompositePrimaryKey`, `Concat`, `Contains`, `Count`, `CreateTableBuilder`, `DO_NOTHING`, `DSLAddConstraint`, `DSLAddField`, `DSLAlterField`, `DSLCreateIndex`, `DSLCreateModel`, `DSLDropIndex`, `DSLDropModel`, `DSLMigrationRunner`, `DSLRemoveConstraint`, `DSLRemoveField`, `DSLRenameField`, `DSLRenameModel`, `DSLRunPython`, `DSLRunSQL`, `DatabaseConnectionFault`, `DatabaseNotReadyError`, `Date`, `DateField`, `DateRangeField`, `DateTimeField`, `DateTimeRangeField`, `Day`, `DecimalField`, `DecimalRangeField`, `DecimalValidator`, `Deferrable`, `DeleteBuilder`, `DurationField`, `EmailField`, `EmailValidator`, `EncryptedMixin`, `EndsWith`, `EnhancedOptions`, `EnumField`, `Exact`, `ExclusionConstraint`, `Exists`, `Expression`, `ExpressionWrapper`, `F`, `Field`, `FieldType`, `FieldValidationError`, `FileExtensionValidator`, `FileField`, `FilePathField`, `FloatField`, `ForeignKey`, `Func`, `FunctionalIndex`, `GeneratedField`, `GenericIPAddressField`, `GinIndex`, `GistIndex`, `Greatest`, `GroupConcat`, `Gt`, `Gte`, `HStoreField`, `HashIndex`, `HookNode`, `IContains`, `IEndsWith`, `IExact`, `IRegex`, `IStartsWith`, `ImageField`, `In`, `Index`, `IndexNode`, `IndexedMixin`, `InetAddressField`, `InsertBuilder`, `IntegerChoices`, `IntegerField`, `IntegerRangeField`, `IsNull`, `JSONField`, `LTrim`, `Least`, `Left`, `LegacyModelRegistry`, `LegacyQ`, `Length`, `LinkKind`, `LinkNode`, `Lookup`, `Lower`, `Lt`, `Lte`, `Manager`, `ManyToManyField`, `Max`, `MaxLengthValidator`, `MaxValueValidator`, `MetaNode`, `Migration`, `MigrationConflictFault`, `MigrationFault`, `MigrationInfo`, `MigrationOps`, `MigrationRunner`, `Min`, `MinLengthValidator`, `MinValueValidator`, `Model`, `ModelDiff`, `ModelFault`, `ModelMeta`, `ModelNode`, `ModelNotFoundFault`, `ModelProxy`, `ModelRegistrationFault`, `ModelRegistry`, `Month`, `NewModelRegistry`, `NoteNode`, `Now`, `NullIf`, `NullableMixin`, `OnDeleteHandler`, `OneToOneField`, `Operation`, `Options`, `OrderBy`, `OrderWrt`, `OuterRef`, `PROTECT`, `PositiveBigIntegerField`, `PositiveIntegerField`, `PositiveSmallIntegerField`, `Power`, `Prefetch`, `ProhibitNullCharactersValidator`, `ProtectedError`, `Q`, `QCombination`, `QNode`, `QueryBuilder`, `QueryFault`, `QuerySet`, `RESTRICT`, `RTrim`, `Range`, `RangeField`, `RangeValidator`, `RawSQL`, `Regex`, `RegexValidator`, `RelationField`, `Replace`, `RestrictedError`, `Right`, `Round`, `SET`, `SET_DEFAULT`, `SET_NULL`, `SQLBuilder`, `SchemaDiff`, `SchemaFault`, `Signal`, `SlotNode`, `SlugField`, `SlugValidator`, `SmallAutoField`, `SmallIntegerField`, `Star`, `StartsWith`, `StdDev`, `StepValueValidator`, `StringAgg`, `Subquery`, `Substr`, `Sum`, `TextChoices`, `TextField`, `TimeField`, `TransactionManager`, `Trim`, `UNSET`, `URLField`, `URLValidator`, `UUIDField`, `UniqueConstraint`, `UniqueForDateValidator`, `UniqueMixin`, `UpdateBuilder`, `Upper`, `UpsertBuilder`, `UpsertIgnoreBuilder`, `ValidationError`, `Value`, `VarcharField`, `Variance`, `When`, `Year`, `atomic`, `check_db_exists`, `check_db_ready`, `check_migrations_applied`, `class_prepared`, `columns`, `compute_diff`, `create_snapshot`, `diff_to_operations`, `generate_create_index_sql`, `generate_create_table_sql`, `generate_dsl_migration`, `generate_migration_file`, `generate_migration_from_models`, `load_snapshot`, `lookup_registry`, `m2m_changed`, `normalize_on_delete`, `op`, `parse_amdl`, `parse_amdl_directory`, `parse_amdl_file`, `post_delete`, `post_init`, `post_migrate`, `post_save`, `pre_delete`, `pre_init`, `pre_migrate`, `pre_save`, `receiver`, `register_lookup`, `resolve_lookup`, `save_snapshot`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `Concat` | `aquilia/models/expression.py` | Expression | SQL concatenation -- dialect-aware (\|\| for SQLite/PG, CONCAT for MySQL). |
| `Left` | `aquilia/models/expression.py` | Expression | SQL LEFT() / SUBSTR() -- extract leftmost characters. |
| `Right` | `aquilia/models/expression.py` | Expression | SQL RIGHT() / SUBSTR() -- extract rightmost characters. |
| `Substr` | `aquilia/models/expression.py` | Func | SQL SUBSTR() -- extract substring. |
| `Replace` | `aquilia/models/expression.py` | Func | SQL REPLACE() -- replace occurrences in a string. |
| `Abs` | `aquilia/models/expression.py` | Func | SQL ABS() -- absolute value. |
| `Round` | `aquilia/models/expression.py` | Expression | SQL ROUND() -- round to specified decimal places. |
| `Power` | `aquilia/models/expression.py` | Expression | SQL POWER() -- raise to a power. |
| `Now` | `aquilia/models/expression.py` | Expression | SQL current timestamp -- dialect-aware. |
| `CompositeAttribute` | `aquilia/models/fields/composite.py` | object | Descriptor that provides read/write access to a group of columns as a single Python dict/namedtuple. |
| `CompositeField` | `aquilia/models/fields/composite.py` | Field | Groups multiple primitive fields into one logical attribute. |
| `CompositePrimaryKey` | `aquilia/models/fields/composite.py` | object | Declares a composite primary key across multiple fields. |
| `EnumField` | `aquilia/models/fields/enum_field.py` | Field | Stores a Python Enum value in the database. |
| `Lookup` | `aquilia/models/fields/lookups.py` | object | Base class for field lookups. |
| `Exact` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `IExact` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive exact match. |
| `Contains` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `IContains` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive contains. |
| `StartsWith` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `IStartsWith` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive startswith. |
| `EndsWith` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `IEndsWith` | `aquilia/models/fields/lookups.py` | Lookup | Case-insensitive endswith. |
| `In` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `Gt` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `Gte` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `Lt` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `Lte` | `aquilia/models/fields/lookups.py` | Lookup |  |
| `IsNull` | `aquilia/models/fields/lookups.py` | Lookup |  |
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
| `IntegerRangeField` | `aquilia/models/fields_module.py` | RangeField |  |
| `BigIntegerRangeField` | `aquilia/models/fields_module.py` | RangeField |  |
| `DecimalRangeField` | `aquilia/models/fields_module.py` | RangeField |  |
| `DateRangeField` | `aquilia/models/fields_module.py` | RangeField |  |
| `DateTimeRangeField` | `aquilia/models/fields_module.py` | RangeField |  |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `normalize_on_delete` | `aquilia/models/deletion.py` | `def normalize_on_delete(action: Any)` | Normalize an on_delete value to its canonical constant. |
| `lookup_registry` | `aquilia/models/fields/lookups.py` | `def lookup_registry()` | Return a copy of the lookup registry. |
| `register_lookup` | `aquilia/models/fields/lookups.py` | `def register_lookup(name: str, cls: type[Lookup])` | Register a custom lookup type. |
| `resolve_lookup` | `aquilia/models/fields/lookups.py` | `def resolve_lookup(field_name: str, lookup_name: str, value: Any)` | Resolve a lookup name to a Lookup instance. |
| `raw_sql_to_operations` | `aquilia/models/migration_dsl.py` | `def raw_sql_to_operations(upgrade_sql: str, downgrade_sql: str='')` | Convert raw SQL strings into a list of RunSQL operations. |
| `generate_dsl_migration` | `aquilia/models/migration_gen.py` | `def generate_dsl_migration(model_classes: list, migrations_dir: str \| Path, snapshot_path: str \| Path \| None=None, slug: str \| None=None)` | Generate a DSL migration file from the diff between the current snapshot and the current model definitions. |
| `check_db_exists` | `aquilia/models/migration_runner.py` | `def check_db_exists(db_url: str)` | Check if a SQLite database file exists WITHOUT creating WAL/SHM files. |
| `check_migrations_applied` | `aquilia/models/migration_runner.py` | `def check_migrations_applied(db_url: str, migrations_dir: str \| Path='migrations')` | Check if there are unapplied migrations WITHOUT creating WAL/SHM. |
| `generate_migration_file` | `aquilia/models/migrations.py` | `def generate_migration_file(models: list[ModelNode], migrations_dir: str \| Path, slug: str \| None=None, dialect: str='sqlite')` | Generate a migration file from AMDL model nodes. |
| `generate_migration_from_models` | `aquilia/models/migrations.py` | `def generate_migration_from_models(model_classes: list, migrations_dir: str \| Path, slug: str \| None=None, dialect: str='sqlite')` | Generate a migration file from new Python Model subclasses. |
| `parse_amdl` | `aquilia/models/parser.py` | `def parse_amdl(source: str, file_path: str='<string>')` | Parse AMDL source text into an AMDLFile. |
| `parse_amdl_file` | `aquilia/models/parser.py` | `def parse_amdl_file(path: str \| Path)` | Parse an `.amdl` file from disk. |
| `parse_amdl_directory` | `aquilia/models/parser.py` | `def parse_amdl_directory(directory: str \| Path)` | Parse all `.amdl` files in a directory (non-recursive). |
| `generate_create_table_sql` | `aquilia/models/runtime.py` | `def generate_create_table_sql(model: ModelNode, dialect: str='sqlite')` | Generate CREATE TABLE SQL from a ModelNode. |
| `generate_create_index_sql` | `aquilia/models/runtime.py` | `def generate_create_index_sql(model: ModelNode, dialect: str='sqlite')` | Generate CREATE INDEX statements for non-unique indexes. |
| `create_snapshot` | `aquilia/models/schema_snapshot.py` | `def create_snapshot(model_classes: list)` | Create a schema snapshot from a list of Model subclasses. |
| `save_snapshot` | `aquilia/models/schema_snapshot.py` | `def save_snapshot(snapshot: dict[str, Any], path: Path)` | Write snapshot to file in CROUS binary format. |
| `load_snapshot` | `aquilia/models/schema_snapshot.py` | `def load_snapshot(path: Path)` | Load snapshot from file in CROUS binary format. |
| `compute_diff` | `aquilia/models/schema_snapshot.py` | `def compute_diff(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any])` | Compute the diff between two schema snapshots. |
| `diff_to_operations` | `aquilia/models/schema_snapshot.py` | `def diff_to_operations(diff: SchemaDiff, old_snapshot: dict[str, Any], new_snapshot: dict[str, Any])` | Convert a SchemaDiff into a list of DSL operations. |
| `receiver` | `aquilia/models/signals.py` | `def receiver(signal: Signal, *, sender: type \| None=None)` | Shorthand decorator to connect a function to a signal. |
| `check_db_ready` | `aquilia/models/startup_guard.py` | `def check_db_ready(db_url: str='sqlite:///db.sqlite3', migrations_dir: str \| Path='migrations', *, auto_migrate: bool \| None=None)` | Check if the database is ready for the application to start. |
| `atomic` | `aquilia/models/transactions.py` | `def atomic(db: AquiliaDatabase \| None=None, *, savepoint: bool=True, durable: bool=False, isolation: str \| None=None)` | Create an atomic transaction context manager. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `CASCADE` | `aquilia/models/deletion.py` | `'CASCADE'` |
| `SET_NULL` | `aquilia/models/deletion.py` | `'SET NULL'` |
| `PROTECT` | `aquilia/models/deletion.py` | `'PROTECT'` |
| `SET_DEFAULT` | `aquilia/models/deletion.py` | `'SET DEFAULT'` |
| `DO_NOTHING` | `aquilia/models/deletion.py` | `'DO NOTHING'` |
| `RESTRICT` | `aquilia/models/deletion.py` | `'RESTRICT'` |
| `_ON_DELETE_ALIASES` | `aquilia/models/deletion.py` | `{'CASCADE': CASCADE, 'SET_NULL': SET_NULL, 'SET NULL': SET_NULL, 'SETNULL': SET_NULL, 'PROTECT': PROTECT, 'SET_DEFAULT': SET_DEFAULT, 'SET DEFAULT': SET_DEFAULT, 'SETDEFAULT': SET_DEFAULT, 'DO_NOTHING': DO_NOTHING, 'DO NOTHING': DO_NOTHING, 'DONOTHING': DO_NOTHING, 'RESTRICT': RESTRICT}` |
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
| `ALLOWED_DEFAULT_PATTERN` | `aquilia/models/parser.py` | `re.compile('^(now_utc\\(\\)\|uuid4\\(\\)\|seq\\(\\)\|env\\("[A-Za-z_][A-Za-z0-9_]*"\\))$')` |
| `RE_MODEL_OPEN` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*MODEL\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*≫\\s*$')` |
| `RE_MODEL_CLOSE` | `aquilia/models/parser.py` | `re.compile('^\\s*≪\\s*/MODEL\\s*≫\\s*$')` |
| `RE_SLOT` | `aquilia/models/parser.py` | `re.compile('^\\s*slot\\s+([a-z_][a-z0-9_]*)\\s*::\\s*([A-Za-z]+(?:\\([^)]*\\))?)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_LINK` | `aquilia/models/parser.py` | `re.compile('^\\s*link\\s+([a-z_][a-z0-9_]*)\\s*->\\s*(ONE\|MANY\|MANY_THROUGH)\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*(?:\\[([^\\]]*)\\])?\\s*$')` |
| `RE_INDEX` | `aquilia/models/parser.py` | `re.compile('^\\s*index\\s+\\[([^\\]]+)\\]\\s*(unique)?\\s*$')` |
| `RE_HOOK` | `aquilia/models/parser.py` | `re.compile('^\\s*hook\\s+([a-z_][a-z0-9_]*)\\s*->\\s*([a-z_][a-z0-9_]*)\\s*$')` |
| `RE_META` | `aquilia/models/parser.py` | `re.compile('^\\s*meta\\s+([a-z_][a-z0-9_]*)\\s*=\\s*"([^"]*)"\\s*$')` |
| `RE_NOTE` | `aquilia/models/parser.py` | `re.compile('^\\s*note\\s+"([^"]*)"\\s*$')` |
| `FIELD_TYPE_MAP` | `aquilia/models/parser.py` | `{ft.value: ft for ft in FieldType}` |
| `_SAFE_FIELD_RE` | `aquilia/models/query.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_EXPR_OP_MAP` | `aquilia/models/query.py` | `{'exact': '=', 'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=', 'ne': '!='}` |
| `_SAFE_DEFAULTS` | `aquilia/models/runtime.py` | `{'now_utc()': lambda: datetime.datetime.now(datetime.timezone.utc), 'uuid4()': lambda: str(uuid.uuid4()), 'seq()': lambda: None}` |
| `SQLITE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'INTEGER', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'INTEGER', FieldType.FLOAT: 'REAL', FieldType.DECIMAL: 'DECIMAL', FieldType.JSON: 'TEXT', FieldType.BYTES: 'BLOB', FieldType.DATETIME: 'TIMESTAMP', FieldType.DATE: 'DATE', FieldType.TIME: 'TIME', FieldType.UUID: 'VARCHAR(36)', FieldType.ENUM: 'VARCHAR(100)', FieldType.FOREIGN_KEY: 'INTEGER'}` |
| `POSTGRES_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'SERIAL', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'BOOLEAN', FieldType.FLOAT: 'DOUBLE PRECISION', FieldType.DECIMAL: 'DECIMAL', FieldType.JSON: 'JSONB', FieldType.BYTES: 'BYTEA', FieldType.DATETIME: 'TIMESTAMP WITH TIME ZONE', FieldType.DATE: 'DATE', FieldType.TIME: 'TIME', FieldType.UUID: 'UUID', FieldType.ENUM: 'VARCHAR(100)', FieldType.FOREIGN_KEY: 'INTEGER'}` |
| `MYSQL_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'INTEGER', FieldType.INT: 'INTEGER', FieldType.BIGINT: 'BIGINT', FieldType.STR: 'VARCHAR', FieldType.TEXT: 'TEXT', FieldType.BOOL: 'TINYINT(1)', FieldType.FLOAT: 'DOUBLE', FieldType.DECIMAL: 'DECIMAL', FieldType.JSON: 'JSON', FieldType.BYTES: 'LONGBLOB', FieldType.DATETIME: 'DATETIME', FieldType.DATE: 'DATE', FieldType.TIME: 'TIME', FieldType.UUID: 'VARCHAR(36)', FieldType.ENUM: 'VARCHAR(100)', FieldType.FOREIGN_KEY: 'INTEGER'}` |
| `ORACLE_TYPE_MAP` | `aquilia/models/runtime.py` | `{FieldType.AUTO: 'NUMBER(10)', FieldType.INT: 'NUMBER(10)', FieldType.BIGINT: 'NUMBER(19)', FieldType.STR: 'VARCHAR2', FieldType.TEXT: 'CLOB', FieldType.BOOL: 'NUMBER(1)', FieldType.FLOAT: 'BINARY_DOUBLE', FieldType.DECIMAL: 'NUMBER', FieldType.JSON: 'CLOB', FieldType.BYTES: 'BLOB', FieldType.DATETIME: 'TIMESTAMP WITH TIME ZONE', FieldType.DATE: 'DATE', FieldType.TIME: 'TIMESTAMP', FieldType.UUID: 'VARCHAR2(36)', FieldType.ENUM: 'VARCHAR2(100)', FieldType.FOREIGN_KEY: 'NUMBER(10)'}` |
| `_TYPE_MAPS` | `aquilia/models/runtime.py` | `{'sqlite': SQLITE_TYPE_MAP, 'postgresql': POSTGRES_TYPE_MAP, 'mysql': MYSQL_TYPE_MAP, 'oracle': ORACLE_TYPE_MAP}` |
| `SNAPSHOT_VERSION` | `aquilia/models/schema_snapshot.py` | `1` |
| `RENAME_THRESHOLD` | `aquilia/models/schema_snapshot.py` | `0.6` |
| `_YELLOW` | `aquilia/models/startup_guard.py` | `'\x1b[93m'` |
| `_RESET` | `aquilia/models/startup_guard.py` | `'\x1b[0m'` |
| `_BOLD` | `aquilia/models/startup_guard.py` | `'\x1b[1m'` |
| `_SP_NAME_RE` | `aquilia/models/transactions.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |

## Detailed Classes And Methods

### `Aggregate`

- Source: `aquilia/models/aggregate.py`
- Bases: `Expression`
- Summary: Base class for aggregate functions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `str` | `''` |
| `template` | `str` | `'{function}({distinct}{expression})'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Sum`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL SUM() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'SUM'` |

### `Avg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL AVG() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'AVG'` |

### `Count`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL COUNT() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'COUNT'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Max`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL MAX() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'MAX'` |

### `Min`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL MIN() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'MIN'` |

### `StdDev`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL STDDEV() aggregate (PostgreSQL) / stdev (SQLite extension).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'STDDEV'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Variance`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: SQL VARIANCE() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'VARIANCE'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `ArrayAgg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL ARRAY_AGG() -- collect values into an array.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'ARRAY_AGG'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `StringAgg`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL STRING_AGG() -- concatenate strings with a delimiter.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'STRING_AGG'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `GroupConcat`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: MySQL/SQLite GROUP_CONCAT() aggregate.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'GROUP_CONCAT'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `BoolAnd`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL BOOL_AND() -- returns true if ALL values are true.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'BOOL_AND'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `BoolOr`

- Source: `aquilia/models/aggregate.py`
- Bases: `Aggregate`
- Summary: PostgreSQL BOOL_OR() -- returns true if ANY value is true.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `function` | `` | `'BOOL_OR'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `FieldType`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Built-in AMDL field types.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `AUTO` | `` | `'Auto'` |
| `INT` | `` | `'Int'` |
| `BIGINT` | `` | `'BigInt'` |
| `STR` | `` | `'Str'` |
| `TEXT` | `` | `'Text'` |
| `BOOL` | `` | `'Bool'` |
| `FLOAT` | `` | `'Float'` |
| `DECIMAL` | `` | `'Decimal'` |
| `JSON` | `` | `'JSON'` |
| `BYTES` | `` | `'Bytes'` |
| `DATETIME` | `` | `'DateTime'` |
| `DATE` | `` | `'Date'` |
| `TIME` | `` | `'Time'` |
| `UUID` | `` | `'UUID'` |
| `ENUM` | `` | `'Enum'` |
| `FOREIGN_KEY` | `` | `'ForeignKey'` |

### `LinkKind`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Relationship cardinality.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ONE` | `` | `'ONE'` |
| `MANY` | `` | `'MANY'` |
| `MANY_THROUGH` | `` | `'MANY_THROUGH'` |

### `SlotNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a `slot` directive -- a model field/column.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `field_type` | `FieldType` | `` |
| `type_params` | `tuple[Any, ...] \| None` | `None` |
| `modifiers` | `dict[str, Any]` | `field(default_factory=dict)` |
| `is_pk` | `bool` | `False` |
| `is_unique` | `bool` | `False` |
| `is_nullable` | `bool` | `False` |
| `max_length` | `int \| None` | `None` |
| `default_expr` | `str \| None` | `None` |
| `note` | `str \| None` | `None` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `LinkNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a `link` directive -- a relationship.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `kind` | `LinkKind` | `` |
| `target_model` | `str` | `` |
| `fk_field` | `str \| None` | `None` |
| `back_name` | `str \| None` | `None` |
| `through_model` | `str \| None` | `None` |
| `modifiers` | `dict[str, Any]` | `field(default_factory=dict)` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `IndexNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents an `index` directive.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `fields` | `list[str]` | `field(default_factory=list)` |
| `is_unique` | `bool` | `False` |
| `name` | `str \| None` | `None` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `HookNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a `hook` directive -- lifecycle binding.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `event` | `str` | `` |
| `handler_name` | `str` | `` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `MetaNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a `meta` directive.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `key` | `str` | `` |
| `value` | `str` | `` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `NoteNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a `note` directive -- freeform documentation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `text` | `str` | `` |
| `line_number` | `int` | `0` |
| `source_file` | `str` | `''` |

### `ModelNode`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a complete MODEL stanza.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `table_name` | `def table_name(self)` | Get table name from meta or derive from model name. |
| `pk_slot` | `def pk_slot(self)` | Get primary key slot, if any. |
| `get_slot` | `def get_slot(self, name: str)` | Find slot by name. |
| `fingerprint` | `def fingerprint(self)` | Compute a deterministic hash for migration diffing. |

### `AMDLFile`

- Source: `aquilia/models/ast_nodes.py`
- Bases: `object`
- Summary: Represents a parsed `.amdl` file containing one or more models.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `path` | `str` | `` |
| `models` | `list[ModelNode]` | `field(default_factory=list)` |
| `errors` | `list[str]` | `field(default_factory=list)` |

### `ModelRegistry`

- Source: `aquilia/models/base.py`
- Bases: `object`
- Summary: Backward-compatible wrapper around registry.ModelRegistry.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(cls, model_cls: type[Model])` |  |
| `get` | `def get(cls, name: str)` |  |
| `all_models` | `def all_models(cls)` |  |
| `set_database` | `def set_database(cls, db: AquiliaDatabase)` |  |
| `get_database` | `def get_database(cls)` |  |
| `create_tables` | `async def create_tables(cls, db: AquiliaDatabase \| None=None)` |  |
| `reset` | `def reset(cls)` |  |
| `on_startup` | `async def on_startup(self)` | Lifecycle hook -- called by LifecycleCoordinator at app start. |
| `on_shutdown` | `async def on_shutdown(self)` |  |

### `Model`

- Source: `aquilia/models/base.py`
- Bases: `object`
- Summary: Aquilia Model base class -- pure Python, async-first ORM.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `objects` | `ClassVar[Manager]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `pk` | `def pk(self)` | Shortcut for accessing the primary key value. |
| `pk` | `def pk(self, value: Any)` | Set the primary key value. |
| `create` | `async def create(cls, **data: Any)` | Create and persist a new record. |
| `get` | `async def get(cls, pk: Any=None, **filters: Any)` | Get a single record by PK or filters. |
| `get_or_none` | `async def get_or_none(cls, pk: Any=None, **filters: Any)` | Get a single record, returning ``None`` if not found. |
| `get_or_create` | `async def get_or_create(cls, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Get existing or create new record. |
| `update_or_create` | `async def update_or_create(cls, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Update existing or create new record. |
| `find_or_create` | `async def find_or_create(cls, defaults: dict[str, Any] \| None=None, create_defaults: dict[str, Any] \| None=None, **lookup: Any)` | Atomically find an existing record or create a new one. |
| `bulk_create` | `async def bulk_create(cls, instances: list[dict[str, Any]], *, batch_size: int \| None=None, ignore_conflicts: bool=False)` | Create multiple records efficiently using batched inserts. |
| `bulk_update` | `async def bulk_update(cls, instances: list[Model], fields: list[str], *, batch_size: int \| None=None)` | Update specific fields on multiple model instances efficiently. |
| `query` | `def query(cls)` | Start a query chain. |
| `all` | `async def all(cls)` | Shortcut: get all records. |
| `count` | `async def count(cls)` | Shortcut: count all records. |
| `latest` | `async def latest(cls, field_name: str \| None=None)` | Return the latest record by date field. |
| `earliest` | `async def earliest(cls, field_name: str \| None=None)` | Return the earliest record by date field. |
| `raw` | `async def raw(cls, sql: str, params: list[Any] \| None=None)` | Execute raw SQL and return model instances. |
| `using` | `def using(cls, db_alias: str)` | Target a specific database for this query. |
| `save` | `async def save(self, *, update_fields: list[str] \| None=None, force_insert: bool=False, force_update: bool=False, validate: bool=False)` | Save instance (insert or update). |
| `delete_instance` | `async def delete_instance(self)` | Delete this instance from database. |
| `full_clean` | `def full_clean(self, exclude: list[str] \| None=None)` | Validate instance completely. |
| `clean_fields` | `def clean_fields(self, exclude: list[str] \| None=None)` | Validate all fields on this instance. |
| `clean` | `def clean(self)` | Model-level validation hook -- override in subclasses. |
| `refresh` | `async def refresh(self, fields: list[str] \| None=None)` | Reload instance from database. |
| `get_dirty_fields` | `def get_dirty_fields(self)` | Return dict of fields whose values differ from the DB snapshot. |
| `related` | `async def related(self, name: str)` | Access a related model via FK or M2M. |
| `attach` | `async def attach(self, name: str, *targets: Any)` | Attach records to a M2M relationship. |
| `detach` | `async def detach(self, name: str, *targets: Any)` | Detach records from a M2M relationship. |
| `to_dict` | `def to_dict(self, *, fields: list[str] \| None=None, exclude: list[str] \| None=None)` | Serialize model instance to dict. |
| `from_row` | `def from_row(cls, row: dict[str, Any])` | Create model instance from database row dict. |
| `generate_create_table_sql` | `def generate_create_table_sql(cls, dialect: str='sqlite')` | Generate CREATE TABLE SQL using CreateTableBuilder. |
| `generate_index_sql` | `def generate_index_sql(cls, dialect: str='sqlite')` | Generate CREATE INDEX statements from Meta.indexes. |
| `generate_m2m_sql` | `def generate_m2m_sql(cls, dialect: str='sqlite')` | Generate junction table SQL for M2M fields. |
| `fingerprint` | `def fingerprint(cls)` | Compute deterministic hash for migration diffing. |

### `Deferrable`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: Constraint deferral modes for PostgreSQL.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEFERRED` | `` | `'DEFERRABLE INITIALLY DEFERRED'` |
| `IMMEDIATE` | `` | `'DEFERRABLE INITIALLY IMMEDIATE'` |

### `CheckConstraint`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: SQL CHECK constraint.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str='sqlite')` | Generate the constraint SQL for CREATE TABLE body. |
| `sql_alter_add` | `def sql_alter_add(self, table_name: str, dialect: str='sqlite')` | Generate ALTER TABLE ADD CONSTRAINT SQL. |
| `sql_alter_drop` | `def sql_alter_drop(self, table_name: str, dialect: str='sqlite')` | Generate ALTER TABLE DROP CONSTRAINT SQL. |
| `deconstruct` | `def deconstruct(self)` |  |

### `ExclusionConstraint`

- Source: `aquilia/models/constraint.py`
- Bases: `object`
- Summary: PostgreSQL EXCLUDE constraint.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str='sqlite')` | Generate constraint SQL (PostgreSQL only). |
| `sql_alter_add` | `def sql_alter_add(self, table_name: str, dialect: str='sqlite')` |  |
| `sql_alter_drop` | `def sql_alter_drop(self, table_name: str, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `OnDeleteHandler`

- Source: `aquilia/models/deletion.py`
- Bases: `object`
- Summary: Callable that implements on_delete behavior at the application level.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `handle` | `async def handle(self, db, source_model, target_field_name: str, pk_value: Any)` | Execute the on_delete action. |
| `for_action` | `def for_action(cls, action: Any)` | Factory method -- create an OnDeleteHandler from any on_delete value. |

### `SET`

- Source: `aquilia/models/deletion.py`
- Bases: `object`
- Summary: Factory for SET(value) / SET(callable) on_delete behavior.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `value` | `def value(self)` | The raw value or callable (for backward compatibility). |
| `resolve` | `def resolve(self)` | Resolve the SET value -- call it if it's a callable. |

### `ProtectedError`

- Source: `aquilia/models/deletion.py`
- Bases: `ProtectedDeleteFault, Exception`
- Summary: Raised when trying to delete a protected object.

### `RestrictedError`

- Source: `aquilia/models/deletion.py`
- Bases: `RestrictedDeleteFault, Exception`
- Summary: Raised when trying to delete a restricted object.

### `TextChoices`

- Source: `aquilia/models/enums.py`
- Bases: `str, Enum`
- Summary: String-valued choices enum.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `label` | `def label(self)` |  |

### `IntegerChoices`

- Source: `aquilia/models/enums.py`
- Bases: `int, Enum`
- Summary: Integer-valued choices enum.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `label` | `def label(self)` |  |

### `Combinable`

- Source: `aquilia/models/expression.py`
- Bases: `object`
- Summary: Base class providing arithmetic operators for expressions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ADD` | `` | `'+'` |
| `SUB` | `` | `'-'` |
| `MUL` | `` | `'*'` |
| `DIV` | `` | `'/'` |
| `MOD` | `` | `'%'` |
| `BITAND` | `` | `'&'` |
| `BITOR` | `` | `'\|'` |

### `Expression`

- Source: `aquilia/models/expression.py`
- Bases: `Combinable`
- Summary: Base class for all SQL expressions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` | Render expression to SQL with bind parameters. |
| `resolve_expression` | `def resolve_expression(self, query=None, allow_joins=True)` | Hook for QuerySet to resolve the expression in context. |

### `OrderBy`

- Source: `aquilia/models/expression.py`
- Bases: `object`
- Summary: Ordering directive -- wraps an expression with ASC/DESC.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `F`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Reference to a model field in an expression context.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |
| `asc` | `def asc(self, *, nulls_first: bool \| None=None, nulls_last: bool \| None=None)` | Create ascending ORDER BY directive. |
| `desc` | `def desc(self, *, nulls_first: bool \| None=None, nulls_last: bool \| None=None)` | Create descending ORDER BY directive. |

### `Value`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps a literal Python value as an SQL expression.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `RawSQL`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Raw SQL expression -- use with caution.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Col`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Reference to a specific table.column in a multi-table query.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Star`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Represents * (all columns).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `CombinedExpression`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Represents two expressions combined with an operator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `When`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Conditional WHEN clause for use inside Case().

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Case`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL CASE expression.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Subquery`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps a query builder as a subquery expression.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Exists`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL EXISTS() expression.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `OuterRef`

- Source: `aquilia/models/expression.py`
- Bases: `F`
- Summary: Reference to a field from the outer query (for use in Subquery/Exists).

### `ExpressionWrapper`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Wraps an expression with an explicit output type.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Func`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: Generic SQL function call.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Cast`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL CAST() expression.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Coalesce`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL COALESCE() -- returns first non-NULL argument.

### `Greatest`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL GREATEST() (MAX on SQLite) -- returns largest argument.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Least`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LEAST() (MIN on SQLite) -- returns smallest argument.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `NullIf`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL NULLIF() -- returns NULL if expression1 equals expression2.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Length`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LENGTH() -- return string length.

### `Upper`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL UPPER() -- convert to uppercase.

### `Lower`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LOWER() -- convert to lowercase.

### `Trim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL TRIM() -- remove leading and trailing whitespace.

### `LTrim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL LTRIM() -- remove leading whitespace.

### `RTrim`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL RTRIM() -- remove trailing whitespace.

### `Concat`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL concatenation -- dialect-aware (|| for SQLite/PG, CONCAT for MySQL).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Left`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL LEFT() / SUBSTR() -- extract leftmost characters.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Right`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL RIGHT() / SUBSTR() -- extract rightmost characters.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Substr`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL SUBSTR() -- extract substring.

### `Replace`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL REPLACE() -- replace occurrences in a string.

### `Abs`

- Source: `aquilia/models/expression.py`
- Bases: `Func`
- Summary: SQL ABS() -- absolute value.

### `Round`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL ROUND() -- round to specified decimal places.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Power`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL POWER() -- raise to a power.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Now`

- Source: `aquilia/models/expression.py`
- Bases: `Expression`
- Summary: SQL current timestamp -- dialect-aware.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `CompositeAttribute`

- Source: `aquilia/models/fields/composite.py`
- Bases: `object`
- Summary: Descriptor that provides read/write access to a group of columns as a single Python dict/namedtuple.

### `CompositeField`

- Source: `aquilia/models/fields/composite.py`
- Bases: `Field`
- Summary: Groups multiple primitive fields into one logical attribute.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `CompositePrimaryKey`

- Source: `aquilia/models/fields/composite.py`
- Bases: `object`
- Summary: Declares a composite primary key across multiple fields.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql` | `def sql(self)` | Generate the SQL PRIMARY KEY constraint. |
| `deconstruct` | `def deconstruct(self)` |  |

### `EnumField`

- Source: `aquilia/models/fields/enum_field.py`
- Bases: `Field`
- Summary: Stores a Python Enum value in the database.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `Lookup`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `object`
- Summary: Base class for field lookups.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `ClassVar[str]` | `''` |
| `sql_operator` | `ClassVar[str]` | `'='` |
| `bilateral` | `ClassVar[bool]` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` | Return (sql_clause, params) for this lookup. |

### `Exact`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'exact'` |
| `sql_operator` | `` | `'='` |

### `IExact`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive exact match.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'iexact'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Contains`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'contains'` |
| `sql_operator` | `` | `'LIKE'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `IContains`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive contains.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'icontains'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `StartsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'startswith'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `IStartsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive startswith.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'istartswith'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `EndsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'endswith'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `IEndsWith`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive endswith.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'iendswith'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `In`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'in'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Gt`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'gt'` |
| `sql_operator` | `` | `'>'` |

### `Gte`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'gte'` |
| `sql_operator` | `` | `'>='` |

### `Lt`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'lt'` |
| `sql_operator` | `` | `'<'` |

### `Lte`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'lte'` |
| `sql_operator` | `` | `'<='` |

### `IsNull`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'isnull'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Range`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Filter within a range: field__range=(lo, hi).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'range'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Regex`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Filter by regex (PostgreSQL: ~, SQLite: REGEXP if loaded).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'regex'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `IRegex`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Case-insensitive regex.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'iregex'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Date`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract date from datetime and compare.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'date'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Year`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract year and compare.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'year'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Month`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract month and compare.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'month'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `Day`

- Source: `aquilia/models/fields/lookups.py`
- Bases: `Lookup`
- Summary: Extract day and compare.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `lookup_name` | `` | `'day'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_sql` | `def as_sql(self, dialect: str='sqlite')` |  |

### `NullableMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that makes a field nullable with sensible defaults.

### `UniqueMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that enforces uniqueness on a field.

### `IndexedMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that auto-adds a database index to a field.

### `AutoNowMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin for fields that auto-update on save (like updated_at).

### `ChoiceMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Mixin that enforces validation of choices with display values.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_display` | `def get_display(self, value: Any)` | Return the human-readable display value for a stored value. |
| `choice_values` | `def choice_values(self)` | Return list of valid stored values. |

### `EncryptedMixin`

- Source: `aquilia/models/fields/mixins.py`
- Bases: `object`
- Summary: Placeholder mixin for encrypted field storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `configure_encryption_key` | `def configure_encryption_key(cls, key: str \| bytes)` | Configure symmetric encryption using *key*. |
| `configure_encryption` | `def configure_encryption(cls, encrypt: Callable[[str], str], decrypt: Callable[[str], str])` | Configure encryption/decryption functions. |
| `to_db` | `def to_db(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |

### `ValidationError`

- Source: `aquilia/models/fields/validators.py`
- Bases: `ValueError`
- Summary: Raised by validators when a value fails validation.

### `BaseValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `object`
- Summary: Base class for all validators.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `message` | `str` | `'Invalid value.'` |
| `code` | `str` | `'invalid'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` | Override in subclasses. Return True if value is valid. |
| `get_message` | `def get_message(self, value: Any)` |  |

### `MinValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value >= limit.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'min_value'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `MaxValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value <= limit.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'max_value'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `MinLengthValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure string length >= limit.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'min_length'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `MaxLengthValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure string length <= limit.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'max_length'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `RegexValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate against a regex pattern.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'invalid'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `EmailValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate email address format.

### `URLValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate URL format.

### `SlugValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `RegexValidator`
- Summary: Validate slug format (letters, numbers, hyphens, underscores).

### `ProhibitNullCharactersValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Reject strings containing null characters.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'null_characters_not_allowed'` |
| `message` | `` | `'Null characters are not allowed.'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |

### `DecimalValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate decimal precision and scale.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'invalid_decimal'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `FileExtensionValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate file extension against an allowed list.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'invalid_extension'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `StepValueValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value is a multiple of step (from offset).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'invalid_step'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `RangeValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Ensure value falls within [min_val, max_val] range.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'out_of_range'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |
| `get_message` | `def get_message(self, value: Any)` |  |

### `UniqueForDateValidator`

- Source: `aquilia/models/fields/validators.py`
- Bases: `BaseValidator`
- Summary: Validate uniqueness for a date-based scope.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'unique_for_date'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_valid` | `def is_valid(self, value: Any)` |  |

### `FieldValidationError`

- Source: `aquilia/models/fields_module.py`
- Bases: `_FieldValidationFault, ValueError`
- Summary: Raised when field validation fails.

### `Field`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Base field descriptor -- all Aquilia fields inherit from this.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `column_name` | `def column_name(self)` | Database column name. |
| `has_default` | `def has_default(self)` | Check if field has a default value. |
| `get_default` | `def get_default(self)` | Get default value, calling it if callable. |
| `validate` | `def validate(self, value: Any)` | Validate and coerce value. Returns cleaned value. Override in subclasses for type-specific validation. |
| `to_python` | `def to_python(self, value: Any)` | Convert database value to Python object. |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` | Convert Python value to database-ready value. |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` | Return SQL type string for this field. |
| `sql_column_def` | `def sql_column_def(self, dialect: str='sqlite')` | Generate full SQL column definition. |
| `deconstruct` | `def deconstruct(self)` | Serialize field definition for migrations. |
| `clone` | `def clone(self)` | Create a deep copy of this field. |

### `AutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Auto-incrementing integer primary key (32-bit).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `BigAutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Auto-incrementing 64-bit integer primary key.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `SmallAutoField`

- Source: `aquilia/models/fields_module.py`
- Bases: `AutoField`
- Summary: Auto-incrementing 16-bit integer primary key.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `IntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Standard 32-bit integer field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `BigIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: 64-bit integer field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `SmallIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: 16-bit integer field (-32768 to 32767).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `PositiveIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 32-bit integer field (0 to 2147483647).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `PositiveSmallIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 16-bit integer field (0 to 32767).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `PositiveBigIntegerField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Positive 64-bit integer field (0 to 9223372036854775807).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `FloatField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Double-precision floating-point field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `DecimalField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Fixed-precision decimal field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `CharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Short text field -- requires max_length.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `VarcharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Explicit alias for CharField, representing a variable-length string.

### `TextField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Long text field -- no length restriction.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `SlugField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: URL-friendly slug field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |

### `EmailField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Email address field with validation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |

### `URLField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: URL field with validation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |

### `UUIDField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: UUID field -- stored as VARCHAR(36) in database.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `FilePathField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: File system path field.

### `DateField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Date field (year, month, day).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool)` | Auto-set value before save. |

### `TimeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Time field (hour, minute, second, microsecond).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool)` | Auto-set time value before save. |

### `DateTimeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: DateTime field with timezone support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `pre_save` | `def pre_save(self, instance: Any, is_create: bool)` | Auto-set value before save. |

### `DurationField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Stores timedelta -- as microseconds in database.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `BooleanField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Boolean field -- stored as INTEGER 0/1 in SQLite.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `BinaryField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Binary data field -- stored as BLOB.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `JSONField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: JSON data field -- native on PostgreSQL, TEXT elsewhere.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `RelationField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Base class for relationship fields.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `related_model` | `def related_model(self)` | Resolve the related model (handles forward references). |
| `resolve_model` | `def resolve_model(self, registry: dict[str, type[Model]])` | Resolve string-based model reference. |

### `ForeignKey`

- Source: `aquilia/models/fields_module.py`
- Bases: `RelationField`
- Summary: Many-to-one relationship field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `sql_column_def` | `def sql_column_def(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `OneToOneField`

- Source: `aquilia/models/fields_module.py`
- Bases: `ForeignKey`
- Summary: One-to-one relationship field.

### `ManyToManyField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RelationField`
- Summary: Many-to-many relationship field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `junction_table_name` | `def junction_table_name(self, source_model: type[Model])` | Generate junction table name. |
| `junction_columns` | `def junction_columns(self, source_model: type[Model])` | Return (source_fk_col, target_fk_col) for junction table. |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `sql_column_def` | `def sql_column_def(self, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `GenericIPAddressField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: IPv4 or IPv6 address field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `FileField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: File path/URL field -- stores the path to the uploaded file.

### `ImageField`

- Source: `aquilia/models/fields_module.py`
- Bases: `FileField`
- Summary: Image file field -- extends FileField with image validation.

### `ArrayField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: PostgreSQL array field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `HStoreField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: PostgreSQL hstore field (key-value pairs).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `RangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Base class for PostgreSQL range fields.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `to_python` | `def to_python(self, value: Any)` |  |
| `to_db` | `def to_db(self, value: Any, dialect: str='sqlite')` |  |

### `IntegerRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `BigIntegerRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `DecimalRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `DateRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `DateTimeRangeField`

- Source: `aquilia/models/fields_module.py`
- Bases: `RangeField`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `CICharField`

- Source: `aquilia/models/fields_module.py`
- Bases: `CharField`
- Summary: Case-insensitive CharField (PostgreSQL CITEXT).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `CIEmailField`

- Source: `aquilia/models/fields_module.py`
- Bases: `EmailField`
- Summary: Case-insensitive EmailField (PostgreSQL CITEXT).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `CITextField`

- Source: `aquilia/models/fields_module.py`
- Bases: `TextField`
- Summary: Case-insensitive TextField (PostgreSQL CITEXT).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, value: Any)` |  |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |

### `InetAddressField`

- Source: `aquilia/models/fields_module.py`
- Bases: `GenericIPAddressField`
- Summary: PostgreSQL INET field -- stores IP address with optional netmask.

### `GeneratedField`

- Source: `aquilia/models/fields_module.py`
- Bases: `Field`
- Summary: Database-computed generated field.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql_type` | `def sql_type(self, dialect: str='sqlite')` |  |
| `sql_column_def` | `def sql_column_def(self, dialect: str='sqlite')` |  |

### `OrderWrt`

- Source: `aquilia/models/fields_module.py`
- Bases: `IntegerField`
- Summary: Internal ordering helper field.

### `Index`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Composite index declaration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str='sqlite')` |  |

### `UniqueConstraint`

- Source: `aquilia/models/fields_module.py`
- Bases: `object`
- Summary: Unique constraint declaration.

### `GinIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL GIN index -- useful for full-text search, JSONB, arrays.

### `GistIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL GiST index -- useful for geometric, range types, exclusion constraints.

### `BrinIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL BRIN index -- useful for very large tables with natural ordering.

### `HashIndex`

- Source: `aquilia/models/index.py`
- Bases: `_PostgresOnlyIndex`
- Summary: PostgreSQL Hash index -- useful for equality lookups only.

### `FunctionalIndex`

- Source: `aquilia/models/index.py`
- Bases: `object`
- Summary: Index on an expression or function call.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sql` | `def sql(self, table_name: str, dialect: str='sqlite')` |  |
| `deconstruct` | `def deconstruct(self)` |  |

### `QuerySet`

- Source: `aquilia/models/manager.py`
- Bases: `object`
- Summary: Reusable query method set -- compose into Manager via from_queryset().

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_queryset` | `def get_queryset(self)` |  |

### `BaseManager`

- Source: `aquilia/models/manager.py`
- Bases: `object`
- Summary: Base manager with Python descriptor protocol.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_queryset` | `def get_queryset(self)` | Override point for custom managers. |
| `filter` | `def filter(self, *q_nodes: Any, **kwargs: Any)` | Field filtering. See Q.filter() for details. |
| `exclude` | `def exclude(self, **kwargs: Any)` | Negated filter. See Q.exclude() for details. |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any)` | Raw WHERE clause (Aquilia-only). See Q.where() for details. |
| `order` | `def order(self, *fields: Any)` | ORDER BY. See Q.order() for details -- supports str, F().desc(), OrderBy. |
| `limit` | `def limit(self, n: int)` |  |
| `offset` | `def offset(self, n: int)` |  |
| `distinct` | `def distinct(self)` |  |
| `only` | `def only(self, *fields: str)` | Load only specified fields. |
| `defer` | `def defer(self, *fields: str)` | Defer loading of specified fields. |
| `annotate` | `def annotate(self, **expressions: Any)` | Add annotations. See Q.annotate() for details. |
| `group_by` | `def group_by(self, *fields: str)` |  |
| `having` | `def having(self, clause: str, *args: Any)` | HAVING clause (use after group_by). |
| `union` | `def union(self, *querysets: Any, all: bool=False)` | UNION set operation. |
| `intersection` | `def intersection(self, *querysets: Any)` | INTERSECT set operation. |
| `difference` | `def difference(self, *querysets: Any)` | EXCEPT set operation. |
| `select_related` | `def select_related(self, *fields: str)` | JOIN-based eager loading. |
| `prefetch_related` | `def prefetch_related(self, *lookups: Any)` | Separate-query prefetching. Accepts strings or Prefetch objects. |
| `select_for_update` | `def select_for_update(self, **kwargs: Any)` | SELECT ... FOR UPDATE (locking). |
| `iterator` | `def iterator(self, chunk_size: int=2000)` | Memory-efficient chunked iteration. See Q.iterator() for details. |
| `using` | `def using(self, db_alias: str)` | Target a specific database. |
| `none` | `def none(self)` | Return an empty queryset. |
| `apply_q` | `def apply_q(self, q_node: Any)` | Apply a QNode filter. |
| `all` | `async def all(self)` |  |
| `first` | `async def first(self)` |  |
| `last` | `async def last(self)` |  |
| `one` | `async def one(self)` | Return exactly one row. Raises if 0 or >1 (Aquilia-only). |
| `latest` | `async def latest(self, field_name: str \| None=None)` | Return latest record by date field. |
| `earliest` | `async def earliest(self, field_name: str \| None=None)` | Return earliest record by date field. |
| `count` | `async def count(self)` |  |
| `exists` | `async def exists(self)` |  |
| `values` | `async def values(self, *fields: str)` |  |
| `values_list` | `async def values_list(self, *fields: str, flat: bool=False)` |  |
| `update` | `async def update(self, values: dict[str, Any] \| None=None, **kwargs: Any)` |  |
| `delete` | `async def delete(self)` |  |
| `aggregate` | `async def aggregate(self, **expressions: Any)` | Compute aggregates. See Q.aggregate() for details. |
| `in_bulk` | `async def in_bulk(self, id_list: list[Any])` | Return dict mapping PKs to instances. |
| `explain` | `async def explain(self, **kwargs: Any)` | Return query execution plan. |
| `get` | `async def get(self, pk: Any=None, **filters: Any)` | Get a single instance by PK or filter kwargs. |
| `get_or_create` | `async def get_or_create(self, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Get existing instance or create a new one. |
| `update_or_create` | `async def update_or_create(self, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Update existing instance or create a new one. |
| `create` | `async def create(self, **data: Any)` | Create and save a new instance. |
| `bulk_create` | `async def bulk_create(self, instances: list[Any], *, batch_size: int \| None=None, ignore_conflicts: bool=False)` | Create multiple instances efficiently. |
| `bulk_update` | `async def bulk_update(self, instances: list[Model], fields: list[str], *, batch_size: int \| None=None)` | Update specific fields on multiple instances. |
| `raw` | `async def raw(self, sql: str, params: list[Any] \| None=None)` | Execute raw SQL and return model instances. |

### `Manager`

- Source: `aquilia/models/manager.py`
- Bases: `BaseManager`
- Summary: Default manager -- auto-attached as ``objects`` on every Model.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_queryset` | `def from_queryset(cls, queryset_class: type, class_name: str \| None=None)` | Create a Manager subclass that includes methods from a QuerySet. |

### `ModelMeta`

- Source: `aquilia/models/metaclass.py`
- Bases: `type`
- Summary: Metaclass for Aquilia models.

### `ColumnDef`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Summary: A column definition in the DSL.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `col_type` | `str` | `` |
| `primary_key` | `bool` | `False` |
| `autoincrement` | `bool` | `False` |
| `unique` | `bool` | `False` |
| `nullable` | `bool` | `False` |
| `default` | `Any` | `_SENTINEL` |
| `references` | `tuple[str, str] \| None` | `None` |
| `on_delete` | `str` | `'CASCADE'` |
| `on_update` | `str` | `'CASCADE'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` | Compile this column to a SQL column definition. |
| `to_snapshot` | `def to_snapshot(self)` | Serialize this column to a snapshot-compatible dict. |
| `from_snapshot` | `def from_snapshot(cls, data: dict[str, Any])` | Deserialize from snapshot dict. |

### `Operation`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Summary: Base class for all migration operations.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `reversible` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` | Compile this operation to SQL statement(s). |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` | Compile the reverse of this operation to SQL. |
| `describe` | `def describe(self)` | Human-readable description. |
| `to_snapshot_delta` | `def to_snapshot_delta(self)` | Describe the snapshot change this operation implies. |

### `CreateModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Create a new database table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `table` | `str` | `` |
| `fields` | `list[ColumnDef]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `DropModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Drop a table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `table` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RenameModel`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Rename a table (preserves data).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `old_name` | `str` | `` |
| `new_name` | `str` | `` |
| `old_table` | `str` | `` |
| `new_table` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `AddField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Add a column to an existing table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_name` | `str` | `` |
| `table` | `str` | `` |
| `column` | `ColumnDef` | `field(default_factory=lambda: ColumnDef(name='', col_type=''))` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RemoveField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Remove a column from an existing table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_name` | `str` | `` |
| `table` | `str` | `` |
| `column_name` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `AlterField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Alter a column's type, constraints, or default.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_name` | `str` | `` |
| `table` | `str` | `` |
| `column_name` | `str` | `` |
| `new_type` | `str \| None` | `None` |
| `nullable` | `bool \| None` | `None` |
| `new_default` | `Any` | `_SENTINEL` |
| `drop_default` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RenameField`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Rename a column (preserves data).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_name` | `str` | `` |
| `table` | `str` | `` |
| `old_name` | `str` | `` |
| `new_name` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `CreateIndex`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Create a database index.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `table` | `str` | `` |
| `columns` | `list[str]` | `field(default_factory=list)` |
| `unique` | `bool` | `False` |
| `condition` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `DropIndex`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Drop a database index.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `table` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `AddConstraint`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Add a constraint to a table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `table` | `str` | `` |
| `constraint_sql` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RemoveConstraint`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Remove a constraint from a table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `table` | `str` | `` |
| `name` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RunSQL`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Execute raw SQL statements (forward and optionally reverse).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `sql` | `str \| list[str]` | `''` |
| `reverse` | `str \| list[str]` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `RunPython`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `Operation`
- Summary: Execute a Python callable as a data migration step.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `forward` | `Callable \| None` | `None` |
| `reverse` | `Callable \| None` | `None` |
| `reversible` | `` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_sql` | `def to_sql(self, dialect: str='sqlite')` |  |
| `reverse_sql` | `def reverse_sql(self, dialect: str='sqlite')` |  |
| `describe` | `def describe(self)` |  |

### `Migration`

- Source: `aquilia/models/migration_dsl.py`
- Bases: `object`
- Summary: Container for a set of migration operations with metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `revision` | `str` | `` |
| `slug` | `str` | `` |
| `models` | `list[str]` | `field(default_factory=list)` |
| `dependencies` | `list[str]` | `field(default_factory=list)` |
| `operations` | `list[Operation]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compile_upgrade` | `def compile_upgrade(self, dialect: str='sqlite')` | Compile all operations to forward SQL. |
| `compile_downgrade` | `def compile_downgrade(self, dialect: str='sqlite')` | Compile all operations (reversed) to rollback SQL. |
| `get_python_ops` | `def get_python_ops(self)` | Get all RunPython operations (for the runner). |
| `describe` | `def describe(self)` |  |

### `MigrationRecord`

- Source: `aquilia/models/migration_runner.py`
- Bases: `object`
- Summary: A record in the aquilia_migrations tracking table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `revision` | `str` | `` |
| `slug` | `str` | `` |
| `checksum` | `str` | `` |
| `applied_at` | `str \| None` | `None` |

### `MigrationRunner`

- Source: `aquilia/models/migration_runner.py`
- Bases: `object`
- Summary: Applies and tracks migrations against an AquiliaDatabase.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `ensure_tracking_table` | `async def ensure_tracking_table(self)` | Create the aquilia_migrations tracking table if it doesn't exist. |
| `get_applied` | `async def get_applied(self)` | Get list of applied revision IDs, ordered by application time. |
| `get_pending` | `async def get_pending(self)` | Get migration files that haven't been applied yet. |
| `status` | `async def status(self)` | Get migration status -- applied, pending, totals. |
| `show_status` | `async def show_status(self)` | Return a human-readable status string. |
| `plan` | `async def plan(self, target: str \| None=None)` | Preview migrations without executing (--plan / dry-run). |
| `sqlmigrate` | `async def sqlmigrate(self, revision: str)` | Get the SQL for a specific migration (aq db sqlmigrate). |
| `migrate` | `async def migrate(self, *, target: str \| None=None, fake: bool=False, database: str \| None=None)` | Apply all pending migrations. |
| `verify_checksums` | `async def verify_checksums(self)` | Verify that applied migration files haven't been tampered with. |

### `MigrationOps`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Summary: Migration operation builder -- used inside migration scripts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `dialect` | `def dialect(self)` |  |
| `dialect` | `def dialect(self, value: str)` |  |
| `create_table` | `def create_table(self, name: str, columns: list[str])` | Generate CREATE TABLE statement. |
| `drop_table` | `def drop_table(self, name: str, cascade: bool=False)` | Generate DROP TABLE statement. |
| `rename_table` | `def rename_table(self, old_name: str, new_name: str)` | Generate RENAME TABLE statement (dialect-aware). |
| `add_column` | `def add_column(self, table: str, column_def: str)` | Generate ALTER TABLE ADD COLUMN. |
| `drop_column` | `def drop_column(self, table: str, column: str)` | Generate ALTER TABLE DROP COLUMN (dialect-aware). |
| `rename_column` | `def rename_column(self, table: str, old_name: str, new_name: str)` | Generate ALTER TABLE RENAME COLUMN (dialect-aware). |
| `alter_column` | `def alter_column(self, table: str, column: str, *, type: str \| None=None, nullable: bool \| None=None, default: Any \| None=None, drop_default: bool=False)` | Generate ALTER TABLE ALTER COLUMN (dialect-aware). |
| `create_index` | `def create_index(self, name: str, table: str, columns: list[str], unique: bool=False, condition: str \| None=None)` | Generate CREATE INDEX (with optional partial index condition). |
| `drop_index` | `def drop_index(self, name: str, table: str \| None=None)` | Generate DROP INDEX (dialect-aware). |
| `add_constraint` | `def add_constraint(self, table: str, constraint_sql: str)` | Generate ALTER TABLE ADD CONSTRAINT. |
| `drop_constraint` | `def drop_constraint(self, table: str, name: str)` | Generate ALTER TABLE DROP CONSTRAINT (not supported on SQLite). |
| `execute_sql` | `def execute_sql(self, sql: str)` | Add raw SQL statement. |
| `run_python` | `def run_python(self, func: Callable)` | Mark a Python callable as a data-migration step. |
| `pk` | `def pk(name: str='id', *, dialect: str='sqlite')` | Primary key column definition. |
| `bigpk` | `def bigpk(name: str='id', *, dialect: str='sqlite')` | Big integer primary key. |
| `integer` | `def integer(name: str, nullable: bool=False, unique: bool=False)` |  |
| `biginteger` | `def biginteger(name: str, nullable: bool=False, unique: bool=False, *, dialect: str='sqlite')` | Big integer column. |
| `varchar` | `def varchar(name: str, length: int=255, nullable: bool=False, unique: bool=False)` |  |
| `text` | `def text(name: str, nullable: bool=False)` |  |
| `blob` | `def blob(name: str, nullable: bool=False)` |  |
| `boolean` | `def boolean(name: str, nullable: bool=False, default: bool \| None=None, *, dialect: str='sqlite')` | Boolean column (dialect-aware). |
| `timestamp` | `def timestamp(name: str, nullable: bool=False, default: str \| None=None, *, dialect: str='sqlite')` | Timestamp column (dialect-aware). |
| `decimal` | `def decimal(name: str, max_digits: int=10, decimal_places: int=2, nullable: bool=False, *, dialect: str='sqlite')` | Decimal / numeric column. |
| `json` | `def json(name: str, nullable: bool=False, *, dialect: str='sqlite')` | JSON column (dialect-aware). |
| `uuid` | `def uuid(name: str, nullable: bool=False, *, dialect: str='sqlite')` | UUID column (dialect-aware). |
| `real` | `def real(name: str, nullable: bool=False)` |  |
| `foreign_key` | `def foreign_key(name: str, ref_table: str, ref_column: str='id', on_delete: str='CASCADE', nullable: bool=False)` | Foreign key column with inline REFERENCES. |
| `get_statements` | `def get_statements(self)` | Return accumulated SQL statements (strings and callables). |
| `clear` | `def clear(self)` | Reset accumulated statements. |

### `MigrationInfo`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Summary: Metadata for a single migration file.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `revision` | `str` | `` |
| `slug` | `str` | `` |
| `models` | `list[str]` | `` |
| `path` | `Path \| None` | `None` |
| `applied` | `bool` | `False` |

### `MigrationRunner`

- Source: `aquilia/models/migrations.py`
- Bases: `object`
- Summary: Applies and tracks migrations against an AquiliaDatabase.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `ensure_tracking_table` | `async def ensure_tracking_table(self)` | Create the migrations tracking table if it doesn't exist. |
| `get_applied` | `async def get_applied(self)` | Get list of applied revision IDs. |
| `get_pending` | `async def get_pending(self)` | Get migration files that haven't been applied yet. |
| `status` | `async def status(self)` | Get migration status -- applied, pending, and total counts. |
| `show_status` | `async def show_status(self)` | Return a human-readable status string. |
| `dry_run` | `async def dry_run(self, target: str \| None=None)` | Preview migrations without executing. Returns list of SQL strings. |
| `apply_migration` | `async def apply_migration(self, path: Path)` | Apply a single migration file. |
| `migrate` | `async def migrate(self, target: str \| None=None)` | Apply all pending migrations. |
| `verify_checksums` | `async def verify_checksums(self)` | Verify that applied migration files haven't been tampered with. |

### `Options`

- Source: `aquilia/models/options.py`
- Bases: `object`
- Summary: Parsed model options from inner Meta class.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `label` | `def label(self)` | Return app_label.ModelName style label. |
| `label_lower` | `def label_lower(self)` | Return app_label.model_name style label (lowercase). |

### `AMDLParseError`

- Source: `aquilia/models/parser.py`
- Bases: `AMDLParseFault`
- Summary: Raised when AMDL parsing fails.

### `QNode`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Composable filter node for complex WHERE clauses.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `AND` | `` | `'AND'` |
| `OR` | `` | `'OR'` |

### `Prefetch`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Custom prefetch descriptor for prefetch_related().

### `Q`

- Source: `aquilia/models/query.py`
- Bases: `object`
- Summary: Aquilia QuerySet -- chainable, immutable, async-terminal query builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any)` | Add raw WHERE clause (Aquilia-only syntax). |
| `filter` | `def filter(self, *q_nodes: Any, **kwargs: Any)` | Field lookup filter. |
| `exclude` | `def exclude(self, *q_nodes: Any, **kwargs: Any)` | Negated filter -- exclude matching records. |
| `order` | `def order(self, *fields: Any)` | ORDER BY -- Aquilia's primary ordering method. |
| `union` | `def union(self, *querysets: Q, all: bool=False)` | Combine this queryset with others using UNION. |
| `intersection` | `def intersection(self, *querysets: Q)` | Combine with INTERSECT -- only rows in ALL querysets. |
| `difference` | `def difference(self, *querysets: Q)` | Combine with EXCEPT -- rows in this set but not in others. |
| `limit` | `def limit(self, n: int)` | Set LIMIT on query results. |
| `offset` | `def offset(self, n: int)` | Set OFFSET for pagination. |
| `distinct` | `def distinct(self)` | Apply SELECT DISTINCT. |
| `only` | `def only(self, *fields: str)` | Load only specified fields (deferred loading for others). |
| `defer` | `def defer(self, *fields: str)` | Defer loading of specified fields. |
| `annotate` | `def annotate(self, **expressions: Any)` | Add aggregate/expression annotations to each row. |
| `group_by` | `def group_by(self, *fields: str)` | GROUP BY clause. |
| `having` | `def having(self, clause: str, *args: Any)` | HAVING clause (use after group_by). |
| `select_related` | `def select_related(self, *fields: str)` | Eager-load FK/OneToOne relations via JOINs. |
| `prefetch_related` | `def prefetch_related(self, *lookups: Any)` | Prefetch related objects via separate queries. |
| `select_for_update` | `def select_for_update(self, *, nowait: bool=False, skip_locked: bool=False)` | Lock selected rows (SELECT ... FOR UPDATE). |
| `using` | `def using(self, db_alias: str)` | Target a specific database for this query. |
| `apply_q` | `def apply_q(self, q_node: QNode)` | Apply a QNode filter to this queryset (Aquilia-only). |
| `iterator` | `def iterator(self, chunk_size: int=2000)` | Return a queryset that uses chunked iteration for memory efficiency. |
| `none` | `def none(self)` | Return an empty queryset that evaluates to []. |
| `all` | `async def all(self)` | Execute and return all matching rows as model instances. |
| `one` | `async def one(self)` | Return exactly one row. Raises if 0 or >1 (Aquilia-only). |
| `first` | `async def first(self)` | Return first matching row or None. |
| `last` | `async def last(self)` | Return last matching row or None (reverses ordering). |
| `latest` | `async def latest(self, field_name: str \| None=None)` | Return the latest record by date field. |
| `earliest` | `async def earliest(self, field_name: str \| None=None)` | Return the earliest record by date field. |
| `count` | `async def count(self)` | Return count of matching rows. |
| `exists` | `async def exists(self)` | Check if any matching rows exist. |
| `update` | `async def update(self, values: dict[str, Any] \| None=None, **kwargs: Any)` | Update matching rows. Returns number of affected rows. |
| `delete` | `async def delete(self)` | Delete matching rows. Returns number of deleted rows. |
| `values` | `async def values(self, *fields: str)` | Return rows as dicts with only specified field values. |
| `values_list` | `async def values_list(self, *fields: str, flat: bool=False)` | Return field values as tuples, or flat list if single field + flat=True. |
| `in_bulk` | `async def in_bulk(self, id_list: list[Any], *, batch_size: int=999)` | Return a dict mapping PKs to instances for the given ID list. |
| `aggregate` | `async def aggregate(self, **expressions: Any)` | Compute aggregates and return a dict. |
| `create` | `async def create(self, **data: Any)` | Create a new record (shortcut on queryset). |
| `get_or_create` | `async def get_or_create(self, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Get existing or create new. |
| `update_or_create` | `async def update_or_create(self, defaults: dict[str, Any] \| None=None, **lookup: Any)` | Update existing or create new. |
| `find_or_create` | `async def find_or_create(self, defaults: dict[str, Any] \| None=None, create_defaults: dict[str, Any] \| None=None, **lookup: Any)` | Atomically find an existing record or create a new one. |
| `explain` | `async def explain(self, *, format: str \| None=None)` | Return the query execution plan (EXPLAIN). |
| `query` | `def query(self)` | Return the raw SQL that would be executed. |

### `ModelRegistry`

- Source: `aquilia/models/registry.py`
- Bases: `object`
- Summary: Global registry for all Model subclasses.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(cls, model_cls: type[Model])` | Register a model class. |
| `get` | `def get(cls, name: str)` | Get model class by name. |
| `all_models` | `def all_models(cls)` | Get all registered models. |
| `get_app_models` | `def get_app_models(cls, app_label: str)` | Get all models for a specific app. |
| `set_database` | `def set_database(cls, db: AquiliaDatabase)` | Set global database for all models. |
| `get_database` | `def get_database(cls)` |  |
| `create_tables` | `async def create_tables(cls, db: AquiliaDatabase \| None=None)` | Create tables for all registered models in topological order. |
| `drop_tables` | `async def drop_tables(cls, db: AquiliaDatabase \| None=None)` | Drop all registered model tables (dangerous!). |
| `reset` | `def reset(cls)` | Clear registry (for testing). |
| `check_constraints` | `def check_constraints(cls)` | Validate all model constraints and return a list of issues. |
| `on_startup` | `async def on_startup(self)` |  |
| `on_shutdown` | `async def on_shutdown(self)` |  |

### `Q`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Summary: Aquilia Query builder -- chainable, async-terminal.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any, **kwargs: Any)` | Add WHERE clause. |
| `filter` | `def filter(self, **kwargs: Any)` | Field lookups. |
| `order` | `def order(self, *fields: str)` | Add ORDER BY clause. |
| `limit` | `def limit(self, n: int)` | Set LIMIT. |
| `offset` | `def offset(self, n: int)` | Set OFFSET. |
| `all` | `async def all(self)` | Execute query and return all matching rows as proxy instances. |
| `one` | `async def one(self)` | Execute query and return exactly one row. Raises ModelNotFoundFault if 0 or >1. |
| `first` | `async def first(self)` | Return first matching row or None. |
| `count` | `async def count(self)` | Return count of matching rows. |
| `update` | `async def update(self, values: dict[str, Any])` | Update matching rows. Returns affected row count. |
| `delete` | `async def delete(self)` | Delete matching rows. Returns affected row count. |

### `ModelRegistry`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Summary: Central registry for AMDL models and their runtime proxies.
- Decorators: `service(scope='app', name='ModelRegistry')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `async def on_startup(self)` | Lifecycle hook -- create tables for all registered models. |
| `on_shutdown` | `async def on_shutdown(self)` | Lifecycle hook -- cleanup (reserved for future use). |
| `register_model` | `def register_model(self, model: ModelNode)` | Register an AMDL model and generate its runtime proxy class. |
| `get_model` | `def get_model(self, name: str)` | Get parsed model AST by name. |
| `get_proxy` | `def get_proxy(self, name: str)` | Get generated proxy class by model name. |
| `all_models` | `def all_models(self)` | Get all registered model nodes. |
| `all_proxies` | `def all_proxies(self)` | Get all proxy classes. |
| `create_tables` | `async def create_tables(self, db: AquiliaDatabase \| None=None)` | Create all registered model tables. |
| `set_database` | `def set_database(self, db: AquiliaDatabase)` | Update database reference for all proxies. |
| `emit_python` | `def emit_python(self)` | Generate Python source code for all model proxies. Useful for `aq model dump --emit`. |

### `ModelProxy`

- Source: `aquilia/models/runtime.py`
- Bases: `object`
- Summary: Base class for AMDL-generated model proxies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize model instance to dict. |

### `SchemaDiff`

- Source: `aquilia/models/schema_snapshot.py`
- Bases: `object`
- Summary: Result of comparing two snapshots.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `added_models` | `list[str]` | `field(default_factory=list)` |
| `removed_models` | `list[str]` | `field(default_factory=list)` |
| `renamed_models` | `list[tuple[str, str]]` | `field(default_factory=list)` |
| `altered_models` | `dict[str, ModelDiff]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `has_changes` | `def has_changes(self)` |  |

### `ModelDiff`

- Source: `aquilia/models/schema_snapshot.py`
- Bases: `object`
- Summary: Changes within a single model.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `added_fields` | `list[str]` | `field(default_factory=list)` |
| `removed_fields` | `list[str]` | `field(default_factory=list)` |
| `renamed_fields` | `list[tuple[str, str]]` | `field(default_factory=list)` |
| `altered_fields` | `list[str]` | `field(default_factory=list)` |
| `added_indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `removed_indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `has_changes` | `def has_changes(self)` |  |

### `Signal`

- Source: `aquilia/models/signals.py`
- Bases: `object`
- Summary: A signal that can be connected to receiver functions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `def connect(self, receiver: Callable=None, *, sender: type \| None=None, weak: bool=False, priority: int=100)` | Connect a receiver function. Can be used as a decorator. |
| `disconnect` | `def disconnect(self, receiver: Callable, *, sender: type \| None=None)` | Disconnect a receiver. |
| `send` | `async def send(self, sender: type, **kwargs)` | Fire the signal, calling all connected receivers. |
| `send_sync` | `def send_sync(self, sender: type, **kwargs)` | Fire the signal synchronously (for sync receivers only). |
| `robust_send` | `async def robust_send(self, sender: type, **kwargs)` | Fire the signal, catching exceptions from each receiver. |
| `receivers` | `def receivers(self)` | List of connected receiver functions (resolved, alive only). |
| `has_listeners` | `def has_listeners(self, sender: type \| None=None)` | Check if any receivers are connected (optionally for a sender). |
| `connected` | `def connected(self, fn: Callable, *, sender: type \| None=None, priority: int=100)` | Context manager for temporary signal connection. |
| `clear` | `def clear(self)` | Remove all receivers (useful for testing). |

### `SQLBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: SELECT query builder with safe parameter binding.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `select` | `def select(self, *columns: str)` | Set columns to select. |
| `from_table` | `def from_table(self, table: str, alias: str \| None=None)` | Set the FROM table. |
| `distinct` | `def distinct(self)` | Add DISTINCT modifier. |
| `join` | `def join(self, table: str, on: str, join_type: str='INNER', params: list[Any] \| None=None)` | Add a JOIN clause. |
| `left_join` | `def left_join(self, table: str, on: str, params: list[Any] \| None=None)` |  |
| `right_join` | `def right_join(self, table: str, on: str, params: list[Any] \| None=None)` |  |
| `where` | `def where(self, clause: str, *args: Any)` | Add a WHERE condition with parameters. |
| `where_in` | `def where_in(self, column: str, values: Sequence[Any])` | Add a WHERE ... IN (...) clause. |
| `group_by` | `def group_by(self, *columns: str)` | Add GROUP BY columns. |
| `having` | `def having(self, clause: str, *args: Any)` | Add HAVING condition. |
| `order_by` | `def order_by(self, *fields: str)` | Add ORDER BY clause. |
| `limit` | `def limit(self, n: int)` |  |
| `offset` | `def offset(self, n: int)` |  |
| `build` | `def build(self)` | Build the final SQL string and parameter list. |
| `build_count` | `def build_count(self)` | Build a COUNT(*) version of this query. |

### `InsertBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT query builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `columns` | `def columns(self, *cols: str)` |  |
| `values` | `def values(self, *vals: Any)` |  |
| `from_dict` | `def from_dict(self, data: dict[str, Any])` | Set columns and values from a dict. |
| `returning` | `def returning(self, column: str)` | Add RETURNING clause (PostgreSQL). |
| `build` | `def build(self)` |  |
| `build_many` | `def build_many(self, rows: list[dict[str, Any]])` | Build INSERT for executemany. |

### `UpdateBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: UPDATE query builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set` | `def set(self, **kwargs: Any)` |  |
| `set_dict` | `def set_dict(self, data: dict[str, Any])` |  |
| `where` | `def where(self, clause: str, *args: Any)` |  |
| `build` | `def build(self)` |  |

### `DeleteBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: DELETE query builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `where` | `def where(self, clause: str, *args: Any)` |  |
| `build` | `def build(self)` |  |

### `CreateTableBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: CREATE TABLE DDL builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `column` | `def column(self, definition: str)` |  |
| `constraint` | `def constraint(self, definition: str)` |  |
| `build` | `def build(self)` |  |

### `AlterTableBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: ALTER TABLE DDL builder -- dialect-aware.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_column` | `def add_column(self, column_def: str)` | Add a column. |
| `drop_column` | `def drop_column(self, column: str)` | Drop a column (SQLite 3.35+, PostgreSQL, MySQL). |
| `rename_column` | `def rename_column(self, old_name: str, new_name: str)` | Rename a column (SQLite 3.25+, PostgreSQL, MySQL 8+). |
| `rename_to` | `def rename_to(self, new_name: str)` | Rename the table. |
| `add_constraint` | `def add_constraint(self, constraint_sql: str)` | Add a constraint. |
| `drop_constraint` | `def drop_constraint(self, name: str)` | Drop a constraint (not supported on SQLite). |
| `alter_column_type` | `def alter_column_type(self, column: str, new_type: str)` | Change column type (PostgreSQL only; generates comment for SQLite). |
| `set_not_null` | `def set_not_null(self, column: str)` | Set NOT NULL on a column. |
| `drop_not_null` | `def drop_not_null(self, column: str)` | Drop NOT NULL from a column. |
| `set_default` | `def set_default(self, column: str, default_value: str)` | Set a default value on a column. |
| `drop_default` | `def drop_default(self, column: str)` | Drop the default value from a column. |
| `build` | `def build(self)` | Return the list of ALTER TABLE DDL statements. |

### `UpsertBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT ... ON CONFLICT (upsert) query builder -- dialect-aware.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `columns` | `def columns(self, *cols: str)` |  |
| `values` | `def values(self, *vals: Any)` |  |
| `from_dict` | `def from_dict(self, data: dict[str, Any])` | Set columns and values from a dict. |
| `conflict_target` | `def conflict_target(self, *columns: str)` | Set the conflict detection columns (unique constraint). |
| `update_columns` | `def update_columns(self, *columns: str)` | Set columns to update on conflict. |
| `build` | `def build(self)` |  |

### `UpsertIgnoreBuilder`

- Source: `aquilia/models/sql_builder.py`
- Bases: `object`
- Summary: INSERT ... ON CONFLICT DO NOTHING query builder -- dialect-aware.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `columns` | `def columns(self, *cols: str)` | Set the column names for the INSERT. |
| `values` | `def values(self, *vals: Any)` | Set the values for the INSERT. |
| `from_dict` | `def from_dict(self, data: dict[str, Any])` | Set columns and values from a dict. |
| `conflict_target` | `def conflict_target(self, *columns: str)` | Set the conflict detection columns (unique constraint). |
| `build` | `def build(self)` | Build the SQL statement and parameters. |

### `DatabaseNotReadyError`

- Source: `aquilia/models/startup_guard.py`
- Bases: `SystemExit`
- Summary: Raised when the database is not ready at server startup.

### `Atomic`

- Source: `aquilia/models/transactions.py`
- Bases: `object`
- Summary: Async context manager for database transactions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_commit` | `def on_commit(self, fn: Callable)` | Register a function to call after successful outermost commit. |
| `on_rollback` | `def on_rollback(self, fn: Callable)` | Register a function to call if this block rolls back. |
| `savepoint` | `async def savepoint(self)` | Create an explicit savepoint within this atomic block. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, savepoint_id: str)` | Roll back to a specific savepoint. |
| `release_savepoint` | `async def release_savepoint(self, savepoint_id: str)` | Release (commit) a savepoint. |

### `TransactionManager`

- Source: `aquilia/models/transactions.py`
- Bases: `object`
- Summary: Higher-level transaction manager with properly scoped on_commit hooks.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_commit` | `def on_commit(self, func: Callable)` | Register a function to be called after successful commit. |
| `on_rollback` | `def on_rollback(self, func: Callable)` | Register a function to be called on rollback. |
| `atomic` | `async def atomic(self, **kwargs)` | Use as: async with manager.atomic() as txn: ... |
