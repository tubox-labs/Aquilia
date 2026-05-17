# Database API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `AdapterCapabilities` | `aquilia/db/backends/base.py` | object | Describes what a specific backend supports. |
| `ColumnInfo` | `aquilia/db/backends/base.py` | object | Introspection result for a single column. |
| `TableInfo` | `aquilia/db/backends/base.py` | object | Introspection result for a table. |
| `IntrospectionResult` | `aquilia/db/backends/base.py` | object | Full database introspection result. |
| `DatabaseAdapter` | `aquilia/db/backends/base.py` | ABC | Abstract database adapter interface. |
| `MySQLAdapter` | `aquilia/db/backends/mysql.py` | DatabaseAdapter | MySQL / MariaDB adapter using aiomysql with connection pooling. |
| `OracleAdapter` | `aquilia/db/backends/oracle.py` | DatabaseAdapter | Oracle adapter using python-oracledb (async mode). |
| `PostgresAdapter` | `aquilia/db/backends/postgres.py` | DatabaseAdapter | PostgreSQL adapter using asyncpg with connection pooling. |
| `SQLiteAdapter` | `aquilia/db/backends/sqlite.py` | DatabaseAdapter | SQLite adapter using the native ``aquilia.sqlite`` connection pool. |
| `DatabaseConfig` | `aquilia/db/configs.py` | object | Base database configuration. |
| `SqliteConfig` | `aquilia/db/configs.py` | DatabaseConfig | SQLite database configuration. |
| `PostgresConfig` | `aquilia/db/configs.py` | DatabaseConfig | PostgreSQL database configuration. |
| `MysqlConfig` | `aquilia/db/configs.py` | DatabaseConfig | MySQL / MariaDB database configuration. |
| `OracleConfig` | `aquilia/db/configs.py` | DatabaseConfig | Oracle database configuration. |
| `AquiliaDatabase` | `aquilia/db/engine.py` | object | Async database engine for Aquilia. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `get_database` | `aquilia/db/engine.py` | `def get_database(alias: str &#124; None = None) -> AquiliaDatabase` | Get a database instance by alias, or the default. |
| `configure_database` | `aquilia/db/engine.py` | `def configure_database(url: str &#124; None = None, *, config: DatabaseConfig &#124; None = None, alias: str = 'default', **options: Any) -> AquiliaDatabase` | Configure and return a database instance. |
| `set_database` | `aquilia/db/engine.py` | `def set_database(db: AquiliaDatabase, *, alias: str = 'default') -> None` | Set an externally-created database as the default or by alias. |
| `get_all_databases` | `aquilia/db/engine.py` | `def get_all_databases() -> dict[str, AquiliaDatabase]` | Return all configured database instances. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_SP_NAME_RE` | `aquilia/db/backends/mysql.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/oracle.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_ORACLE_RESERVED` | `aquilia/db/backends/oracle.py` | `frozenset({'ACCESS', 'ADD', 'ALL', 'ALTER', 'AND', 'ANY', 'AS', 'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CHAR', 'CHECK', 'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'C` |
| `_SP_NAME_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_INSERT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^\\s*INSERT\\s+INTO\\s+', re.IGNORECASE)` |
| `_STATUS_ROWCOUNT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('(\\d+)\\s*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/sqlite.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/engine.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |

## Detailed Classes And Methods

### Class: `AdapterCapabilities`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Describes what a specific backend supports.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `supports_returning` | `bool` | `False` |
| `supports_json_type` | `bool` | `False` |
| `supports_arrays` | `bool` | `False` |
| `supports_hstore` | `bool` | `False` |
| `supports_citext` | `bool` | `False` |
| `supports_upsert` | `bool` | `True` |
| `supports_savepoints` | `bool` | `True` |
| `supports_window_functions` | `bool` | `True` |
| `supports_cte` | `bool` | `True` |
| `param_style` | `str` | `'qmark'` |
| `null_ordering` | `bool` | `False` |
| `name` | `str` | `'base'` |

### Class: `ColumnInfo`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Introspection result for a single column.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `data_type` | `str` |  |
| `nullable` | `bool` | `True` |
| `default` | `str &#124; None` | `None` |
| `primary_key` | `bool` | `False` |
| `unique` | `bool` | `False` |
| `max_length` | `int &#124; None` | `None` |

### Class: `TableInfo`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Introspection result for a table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `columns` | `list[ColumnInfo]` | `field(default_factory=list)` |
| `indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `foreign_keys` | `list[dict[str, Any]]` | `field(default_factory=list)` |

### Class: `IntrospectionResult`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Full database introspection result.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `tables` | `list[TableInfo]` | `field(default_factory=list)` |

### Class: `DatabaseAdapter`

- Source: `aquilia/db/backends/base.py`
- Bases: `ABC`
- Summary: Abstract database adapter interface.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `capabilities` | `AdapterCapabilities` | `AdapterCapabilities()` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options) -> None` | abstractmethod | Open a connection to the database. |
| `disconnect` | `async def disconnect(self) -> None` | abstractmethod | Close the database connection. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` | abstractmethod | Execute a SQL statement. Returns a cursor-like object. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` | abstractmethod | Execute a SQL statement with multiple parameter sets. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` | abstractmethod | Execute and return all rows as dicts. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` | abstractmethod | Execute and return one row as dict, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` | abstractmethod | Execute and return a scalar value. |
| `begin` | `async def begin(self) -> None` | abstractmethod | Start a transaction. |
| `commit` | `async def commit(self) -> None` | abstractmethod | Commit the current transaction. |
| `rollback` | `async def rollback(self) -> None` | abstractmethod | Rollback the current transaction. |
| `savepoint` | `async def savepoint(self, name: str) -> None` | abstractmethod | Create a savepoint. |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` | abstractmethod | Release (commit) a savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` | abstractmethod | Rollback to a savepoint. |
| `transaction` | `async def transaction(self) -> AsyncIterator[None]` | asynccontextmanager | Context manager for transactions. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` | abstractmethod | Check if a table exists. |
| `get_tables` | `async def get_tables(self) -> list[str]` | abstractmethod | List all table names. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` | abstractmethod | Get column info for a table. |
| `introspect` | `async def introspect(self) -> IntrospectionResult` |  | Full database introspection. |
| `adapt_sql` | `def adapt_sql(self, sql: str) -> str` |  | Adapt SQL placeholders from qmark (?) to the backend's param style. |
| `last_insert_id` | `def last_insert_id(self, cursor: Any) -> int &#124; None` |  | Extract last inserted ID from cursor. |
| `is_connected` | `def is_connected(self) -> bool` | property | Check if the adapter is connected. |
| `dialect` | `def dialect(self) -> str` | property | Return the SQL dialect name. |

### Class: `MySQLAdapter`

- Source: `aquilia/db/backends/mysql.py`
- Bases: `DatabaseAdapter`
- Summary: MySQL / MariaDB adapter using aiomysql with connection pooling.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `capabilities` |  | `AdapterCapabilities(supports_returning=False, supports_json_type=True, supports_arrays=False, supports_hstore=False, sup` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options) -> None` |  | Method. |
| `disconnect` | `async def disconnect(self) -> None` |  | Method. |
| `adapt_sql` | `def adapt_sql(self, sql: str) -> str` |  | Adapt generic SQL for MySQL: |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` |  | Method. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` |  | Method. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` |  | Method. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `begin` | `async def begin(self) -> None` |  | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self) -> None` |  | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self) -> None` |  | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Method. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Method. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` |  | Method. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | Method. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` |  | Method. |
| `get_indexes` | `async def get_indexes(self, table_name: str) -> list[dict[str, Any]]` |  | Get index info for a MySQL table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]` |  | Get foreign key info for a MySQL table. |
| `is_connected` | `def is_connected(self) -> bool` | property | Method. |
| `dialect` | `def dialect(self) -> str` | property | Method. |

### Class: `OracleAdapter`

- Source: `aquilia/db/backends/oracle.py`
- Bases: `DatabaseAdapter`
- Summary: Oracle adapter using python-oracledb (async mode).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `capabilities` |  | `AdapterCapabilities(supports_returning=True, supports_json_type=False, supports_arrays=False, supports_hstore=False, sup` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options) -> None` |  | Method. |
| `disconnect` | `async def disconnect(self) -> None` |  | Method. |
| `adapt_sql` | `def adapt_sql(self, sql: str) -> str` |  | Convert ``?`` placeholders to ``:1, :2, ...`` for oracledb. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` |  | Method. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` |  | Method. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` |  | Method. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `begin` | `async def begin(self) -> None` |  | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self) -> None` |  | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self) -> None` |  | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Oracle does not support RELEASE SAVEPOINT -- no-op. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Method. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` |  | Method. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | Method. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` |  | Method. |
| `get_indexes` | `async def get_indexes(self, table_name: str) -> list[dict[str, Any]]` |  | Get index info for an Oracle table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]` |  | Get foreign key info for an Oracle table. |
| `is_connected` | `def is_connected(self) -> bool` | property | Method. |
| `dialect` | `def dialect(self) -> str` | property | Method. |
| `last_insert_id` | `def last_insert_id(self, cursor: Any) -> int &#124; None` |  | Oracle does not have lastrowid in the same way. |

### Class: `PostgresAdapter`

- Source: `aquilia/db/backends/postgres.py`
- Bases: `DatabaseAdapter`
- Summary: PostgreSQL adapter using asyncpg with connection pooling.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `capabilities` |  | `AdapterCapabilities(supports_returning=True, supports_json_type=True, supports_arrays=True, supports_hstore=True, suppor` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options) -> None` |  | Method. |
| `disconnect` | `async def disconnect(self) -> None` |  | Method. |
| `adapt_sql` | `def adapt_sql(self, sql: str) -> str` |  | Convert ``?`` placeholders to ``$1, $2, ...`` for asyncpg. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` |  | Method. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` |  | Method. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` |  | Method. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `begin` | `async def begin(self) -> None` |  | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self) -> None` |  | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self) -> None` |  | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Method. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Method. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` |  | Method. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | Method. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` |  | Method. |
| `get_indexes` | `async def get_indexes(self, table_name: str) -> list[dict[str, Any]]` |  | Get index info for a PostgreSQL table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]` |  | Get foreign key info for a PostgreSQL table. |
| `is_connected` | `def is_connected(self) -> bool` | property | Method. |
| `dialect` | `def dialect(self) -> str` | property | Method. |

### Class: `SQLiteAdapter`

- Source: `aquilia/db/backends/sqlite.py`
- Bases: `DatabaseAdapter`
- Summary: SQLite adapter using the native ``aquilia.sqlite`` connection pool.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `capabilities` |  | `AdapterCapabilities(supports_returning=False, supports_json_type=False, supports_arrays=False, supports_hstore=False, su` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options) -> None` |  | Method. |
| `disconnect` | `async def disconnect(self) -> None` |  | Method. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` |  | Method. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` |  | Method. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` |  | Method. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Method. |
| `begin` | `async def begin(self) -> None` |  | Method. |
| `commit` | `async def commit(self) -> None` |  | Method. |
| `rollback` | `async def rollback(self) -> None` |  | Method. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Method. |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Method. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Method. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` |  | Method. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | Method. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` |  | Method. |
| `get_indexes` | `async def get_indexes(self, table_name: str) -> list[dict[str, Any]]` |  | Get index info for a table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]` |  | Get foreign key info for a table. |
| `is_connected` | `def is_connected(self) -> bool` | property | Method. |
| `dialect` | `def dialect(self) -> str` | property | Method. |
| `pool` | `def pool(self) -> ConnectionPool &#124; None` | property | Access the underlying connection pool (for advanced usage). |
| `metrics` | `def metrics(self) -> SqliteMetrics &#124; None` | property | Access pool metrics. |

### Class: `DatabaseConfig`

- Source: `aquilia/db/configs.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `engine` | `str` | `'sqlite'` |
| `pool_size` | `int` | `5` |
| `pool_min_size` | `int` | `2` |
| `pool_max_size` | `int` | `10` |
| `echo` | `bool` | `False` |
| `auto_connect` | `bool` | `True` |
| `auto_create` | `bool` | `True` |
| `auto_migrate` | `bool` | `False` |
| `migrations_dir` | `str` | `'migrations'` |
| `connect_retries` | `int` | `3` |
| `connect_retry_delay` | `float` | `0.5` |
| `conn_max_age` | `int` | `0` |
| `conn_health_checks` | `bool` | `False` |
| `options` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_url` | `def to_url(self) -> str` |  | Generate a database connection URL. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to a flat dictionary for integration with ConfigLoader. |
| `get_engine_options` | `def get_engine_options(self) -> dict[str, Any]` |  | Get kwargs to pass to AquiliaDatabase / adapter. |
| `from_url` | `def from_url(cls, url: str, **overrides) -> DatabaseConfig` | classmethod | Create a config from a URL string. |

### Class: `SqliteConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Decorators: `dataclass`
- Summary: SQLite database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `engine` | `str` | `'sqlite'` |
| `path` | `str` | `'db.sqlite3'` |
| `journal_mode` | `str` | `'WAL'` |
| `foreign_keys` | `bool` | `True` |
| `busy_timeout` | `int` | `5000` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_url` | `def to_url(self) -> str` |  | Method. |
| `from_url` | `def from_url(cls, url: str, **overrides) -> SqliteConfig` | classmethod | Parse a sqlite:// URL into a SqliteConfig. |

### Class: `PostgresConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Decorators: `dataclass`
- Summary: PostgreSQL database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `engine` | `str` | `'postgresql'` |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `5432` |
| `name` | `str` | `''` |
| `database` | `str` | `''` |
| `user` | `str` | `''` |
| `password` | `str` | `''` |
| `schema` | `str` | `'public'` |
| `sslmode` | `str` | `'prefer'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_url` | `def to_url(self) -> str` |  | Method. |
| `get_engine_options` | `def get_engine_options(self) -> dict[str, Any]` |  | Method. |
| `from_url` | `def from_url(cls, url: str, **overrides) -> PostgresConfig` | classmethod | Parse a postgresql:// URL into a PostgresConfig. |

### Class: `MysqlConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Decorators: `dataclass`
- Summary: MySQL / MariaDB database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `engine` | `str` | `'mysql'` |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `3306` |
| `name` | `str` | `''` |
| `database` | `str` | `''` |
| `user` | `str` | `''` |
| `password` | `str` | `''` |
| `charset` | `str` | `'utf8mb4'` |
| `collation` | `str` | `'utf8mb4_unicode_ci'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_url` | `def to_url(self) -> str` |  | Method. |
| `get_engine_options` | `def get_engine_options(self) -> dict[str, Any]` |  | Method. |
| `from_url` | `def from_url(cls, url: str, **overrides) -> MysqlConfig` | classmethod | Parse a mysql:// URL into a MysqlConfig. |

### Class: `OracleConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Decorators: `dataclass`
- Summary: Oracle database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `engine` | `str` | `'oracle'` |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `1521` |
| `service_name` | `str` | `'ORCL'` |
| `database` | `str` | `''` |
| `user` | `str` | `''` |
| `password` | `str` | `''` |
| `sid` | `str` | `''` |
| `thick_mode` | `bool` | `False` |
| `encoding` | `str` | `'UTF-8'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_url` | `def to_url(self) -> str` |  | Method. |
| `get_dsn` | `def get_dsn(self) -> str` |  | Get Oracle DSN in Easy Connect format. |
| `get_engine_options` | `def get_engine_options(self) -> dict[str, Any]` |  | Method. |
| `from_url` | `def from_url(cls, url: str, **overrides) -> OracleConfig` | classmethod | Parse an oracle:// URL into an OracleConfig. |

### Class: `AquiliaDatabase`

- Source: `aquilia/db/engine.py`
- Bases: `object`
- Decorators: `service`
- Summary: Async database engine for Aquilia.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `async def on_startup(self) -> None` |  | Lifecycle hook -- called by ``LifecycleCoordinator`` at app start. |
| `on_shutdown` | `async def on_shutdown(self) -> None` |  | Lifecycle hook -- called by ``LifecycleCoordinator`` at app stop. |
| `connect` | `async def connect(self) -> None` |  | Open database connection with retry logic. |
| `disconnect` | `async def disconnect(self) -> None` |  | Close database connection. |
| `ensure_connected` | `async def ensure_connected(self) -> None` |  | Ensure a live connection exists, reconnecting if needed. |
| `transaction` | `async def transaction(self) -> AsyncIterator[None]` | asynccontextmanager | Async context manager for transactions. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Create a named savepoint within a transaction. |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Release (commit) a named savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Roll back to a named savepoint. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Execute a SQL statement. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None` |  | Execute a SQL statement with multiple parameter sets. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[dict[str, Any]]` |  | Execute query and return all rows as dicts. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> dict[str, Any] &#124; None` |  | Execute query and return first row as dict, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Execute query and return scalar value from first row, first column. |
| `table_exists` | `async def table_exists(self, table_name: str) -> bool` |  | Check if a table exists in the database. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | List all table names in the database. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[ColumnInfo]` |  | Get column metadata for a table. |
| `is_connected` | `def is_connected(self) -> bool` | property | Method. |
| `url` | `def url(self) -> str` | property | Method. |
| `driver` | `def driver(self) -> str` | property | Method. |
| `dialect` | `def dialect(self) -> str` | property | Return the SQL dialect name (sqlite, postgresql, mysql). |
| `capabilities` | `def capabilities(self) -> AdapterCapabilities` | property | Return backend capabilities. |
| `adapter` | `def adapter(self) -> DatabaseAdapter` | property | Direct access to the underlying adapter (advanced use). |
| `in_transaction` | `def in_transaction(self) -> bool` | property | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `get_database` | `aquilia/db/engine.py` | `def get_database(alias: str &#124; None = None) -> AquiliaDatabase` | Get a database instance by alias, or the default. |
| `configure_database` | `aquilia/db/engine.py` | `def configure_database(url: str &#124; None = None, *, config: DatabaseConfig &#124; None = None, alias: str = 'default', **options: Any) -> AquiliaDatabase` | Configure and return a database instance. |
| `set_database` | `aquilia/db/engine.py` | `def set_database(db: AquiliaDatabase, *, alias: str = 'default') -> None` | Set an externally-created database as the default or by alias. |
| `get_all_databases` | `aquilia/db/engine.py` | `def get_all_databases() -> dict[str, AquiliaDatabase]` | Return all configured database instances. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_SP_NAME_RE` | `aquilia/db/backends/mysql.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/oracle.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_ORACLE_RESERVED` | `aquilia/db/backends/oracle.py` | `frozenset({'ACCESS', 'ADD', 'ALL', 'ALTER', 'AND', 'ANY', 'AS', 'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CHAR', 'CHECK', 'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'C` |
| `_SP_NAME_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_INSERT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^\\s*INSERT\\s+INTO\\s+', re.IGNORECASE)` |
| `_STATUS_ROWCOUNT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('(\\d+)\\s*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/sqlite.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/engine.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
