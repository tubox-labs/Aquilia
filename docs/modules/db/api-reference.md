# Db API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/db/__init__.py` | 68 | 0 | 0 | Aquilia Database -- async-first database layer. |
| `aquilia/db/backends/__init__.py` | 27 | 0 | 0 | Aquilia DB Backends Package -- pluggable database adapters. |
| `aquilia/db/backends/base.py` | 222 | 5 | 0 | Aquilia DB Backend -- Base Adapter Interface. |
| `aquilia/db/backends/mysql.py` | 443 | 1 | 0 | Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql. |
| `aquilia/db/backends/oracle.py` | 610 | 1 | 0 | Aquilia DB Backend -- Oracle adapter via python-oracledb. |
| `aquilia/db/backends/postgres.py` | 424 | 1 | 0 | Aquilia DB Backend -- PostgreSQL adapter via asyncpg. |
| `aquilia/db/backends/sqlite.py` | 332 | 1 | 0 | Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module. |
| `aquilia/db/configs.py` | 519 | 5 | 0 | Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs. |
| `aquilia/db/engine.py` | 621 | 1 | 4 | Aquilia Database Engine -- async-first, multi-backend, production-ready. |

## Public Exports

`AdapterCapabilities`, `AquiliaDatabase`, `ColumnInfo`, `DatabaseAdapter`, `DatabaseConfig`, `DatabaseConnectionFault`, `DatabaseError`, `IntrospectionResult`, `MySQLAdapter`, `MysqlConfig`, `OracleAdapter`, `OracleConfig`, `PostgresAdapter`, `PostgresConfig`, `QueryFault`, `SQLiteAdapter`, `SchemaFault`, `SqliteConfig`, `TableInfo`, `configure_database`, `get_database`, `set_database`

## Public Class Summary

| Class | Source | Bases | Summary |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `get_database` | `aquilia/db/engine.py` | `def get_database(alias: str \| None=None)` | Get a database instance by alias, or the default. |
| `configure_database` | `aquilia/db/engine.py` | `def configure_database(url: str \| None=None, *, config: DatabaseConfig \| None=None, alias: str='default', **options: Any)` | Configure and return a database instance. |
| `set_database` | `aquilia/db/engine.py` | `def set_database(db: AquiliaDatabase, *, alias: str='default')` | Set an externally-created database as the default or by alias. |
| `get_all_databases` | `aquilia/db/engine.py` | `def get_all_databases()` | Return all configured database instances. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_SP_NAME_RE` | `aquilia/db/backends/mysql.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/oracle.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_ORACLE_RESERVED` | `aquilia/db/backends/oracle.py` | `frozenset({'ACCESS', 'ADD', 'ALL', 'ALTER', 'AND', 'ANY', 'AS', 'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CHAR', 'CHECK', 'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'CREATE', 'CURRENT', 'DATE', 'DECIMAL', 'DEFAULT', 'DELETE', 'DESC', 'DISTINCT', 'DROP', 'ELSE', 'EXCLUSIVE', 'EXISTS', 'FILE', 'FLOAT', 'FOR', 'FROM', 'GRANT', 'GROUP', 'HAVING', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT', 'INDEX', 'INITIAL', 'INSERT', 'INTEGER', 'INTERSECT', 'INTO', 'IS', 'LEVEL', 'LIKE', 'LOCK', 'LONG', 'MAXEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT', 'NOCOMPRESS', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OF', 'OFFLINE', 'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER', 'PCTFREE', 'PRIOR', 'PUBLIC', 'RAW', 'RENAME', 'RESOURCE', 'REVOKE', 'ROW', 'ROWID', 'ROWNUM', 'ROWS', 'SELECT', 'SESSION', 'SET', 'SHARE', 'SIZE', 'SMALLINT', 'START', 'SUCCESSFUL', 'SYNONYM', 'SYSDATE', 'TABLE', 'THEN', 'TO', 'TRIGGER', 'UID', 'UNION', 'UNIQUE', 'UPDATE', 'USER', 'VALIDATE', 'VALUES', 'VARCHAR', 'VARCHAR2', 'VIEW', 'WHENEVER', 'WHERE', 'WITH'})` |
| `_SP_NAME_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_INSERT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('^\\s*INSERT\\s+INTO\\s+', re.IGNORECASE)` |
| `_STATUS_ROWCOUNT_RE` | `aquilia/db/backends/postgres.py` | `re.compile('(\\d+)\\s*$')` |
| `_SP_NAME_RE` | `aquilia/db/backends/sqlite.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SP_NAME_RE` | `aquilia/db/engine.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |

## Detailed Classes And Methods

### `AdapterCapabilities`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Summary: Describes what a specific backend supports.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

### `ColumnInfo`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Summary: Introspection result for a single column.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `data_type` | `str` | `` |
| `nullable` | `bool` | `True` |
| `default` | `str \| None` | `None` |
| `primary_key` | `bool` | `False` |
| `unique` | `bool` | `False` |
| `max_length` | `int \| None` | `None` |

### `TableInfo`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Summary: Introspection result for a table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `columns` | `list[ColumnInfo]` | `field(default_factory=list)` |
| `indexes` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `foreign_keys` | `list[dict[str, Any]]` | `field(default_factory=list)` |

### `IntrospectionResult`

- Source: `aquilia/db/backends/base.py`
- Bases: `object`
- Summary: Full database introspection result.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `tables` | `list[TableInfo]` | `field(default_factory=list)` |

### `DatabaseAdapter`

- Source: `aquilia/db/backends/base.py`
- Bases: `ABC`
- Summary: Abstract database adapter interface.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `capabilities` | `AdapterCapabilities` | `AdapterCapabilities()` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options)` | Open a connection to the database. |
| `disconnect` | `async def disconnect(self)` | Close the database connection. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` | Execute a SQL statement. Returns a cursor-like object. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` | Execute a SQL statement with multiple parameter sets. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` | Execute and return all rows as dicts. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` | Execute and return one row as dict, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` | Execute and return a scalar value. |
| `begin` | `async def begin(self)` | Start a transaction. |
| `commit` | `async def commit(self)` | Commit the current transaction. |
| `rollback` | `async def rollback(self)` | Rollback the current transaction. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a savepoint. |
| `release_savepoint` | `async def release_savepoint(self, name: str)` | Release (commit) a savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` | Rollback to a savepoint. |
| `transaction` | `async def transaction(self)` | Context manager for transactions. |
| `table_exists` | `async def table_exists(self, table_name: str)` | Check if a table exists. |
| `get_tables` | `async def get_tables(self)` | List all table names. |
| `get_columns` | `async def get_columns(self, table_name: str)` | Get column info for a table. |
| `introspect` | `async def introspect(self)` | Full database introspection. |
| `adapt_sql` | `def adapt_sql(self, sql: str)` | Adapt SQL placeholders from qmark (?) to the backend's param style. |
| `last_insert_id` | `def last_insert_id(self, cursor: Any)` | Extract last inserted ID from cursor. |
| `is_connected` | `def is_connected(self)` | Check if the adapter is connected. |
| `dialect` | `def dialect(self)` | Return the SQL dialect name. |

### `MySQLAdapter`

- Source: `aquilia/db/backends/mysql.py`
- Bases: `DatabaseAdapter`
- Summary: MySQL / MariaDB adapter using aiomysql with connection pooling.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options)` |  |
| `disconnect` | `async def disconnect(self)` |  |
| `adapt_sql` | `def adapt_sql(self, sql: str)` | Adapt generic SQL for MySQL: - Strip ``IF NOT EXISTS`` from ``CREATE INDEX`` (MySQL does not support this syntax; duplicate-index errors are caught at runtime) - Convert ``?`` placeholders to ``%s`` - Convert double-quoted identifiers to backtick-quoted (MySQL uses backticks; double quotes are for ANSI_QUOTES mode) |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` |  |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `begin` | `async def begin(self)` | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self)` | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self)` | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str)` |  |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` |  |
| `table_exists` | `async def table_exists(self, table_name: str)` |  |
| `get_tables` | `async def get_tables(self)` |  |
| `get_columns` | `async def get_columns(self, table_name: str)` |  |
| `get_indexes` | `async def get_indexes(self, table_name: str)` | Get index info for a MySQL table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str)` | Get foreign key info for a MySQL table. |
| `is_connected` | `def is_connected(self)` |  |
| `dialect` | `def dialect(self)` |  |

### `OracleAdapter`

- Source: `aquilia/db/backends/oracle.py`
- Bases: `DatabaseAdapter`
- Summary: Oracle adapter using python-oracledb (async mode).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options)` |  |
| `disconnect` | `async def disconnect(self)` |  |
| `adapt_sql` | `def adapt_sql(self, sql: str)` | Convert ``?`` placeholders to ``:1, :2, ...`` for oracledb. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` |  |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `begin` | `async def begin(self)` | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self)` | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self)` | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str)` | Oracle does not support RELEASE SAVEPOINT -- no-op. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` |  |
| `table_exists` | `async def table_exists(self, table_name: str)` |  |
| `get_tables` | `async def get_tables(self)` |  |
| `get_columns` | `async def get_columns(self, table_name: str)` |  |
| `get_indexes` | `async def get_indexes(self, table_name: str)` | Get index info for an Oracle table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str)` | Get foreign key info for an Oracle table. |
| `is_connected` | `def is_connected(self)` |  |
| `dialect` | `def dialect(self)` |  |
| `last_insert_id` | `def last_insert_id(self, cursor: Any)` | Oracle does not have lastrowid in the same way. Use RETURNING INTO clause or sequences instead. |

### `PostgresAdapter`

- Source: `aquilia/db/backends/postgres.py`
- Bases: `DatabaseAdapter`
- Summary: PostgreSQL adapter using asyncpg with connection pooling.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options)` |  |
| `disconnect` | `async def disconnect(self)` |  |
| `adapt_sql` | `def adapt_sql(self, sql: str)` | Convert ``?`` placeholders to ``$1, $2, ...`` for asyncpg. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` |  |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `begin` | `async def begin(self)` | Acquire a dedicated connection and start a transaction. |
| `commit` | `async def commit(self)` | Commit the transaction and release the connection. |
| `rollback` | `async def rollback(self)` | Rollback the transaction and release the connection. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a savepoint (must be inside a transaction). |
| `release_savepoint` | `async def release_savepoint(self, name: str)` |  |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` |  |
| `table_exists` | `async def table_exists(self, table_name: str)` |  |
| `get_tables` | `async def get_tables(self)` |  |
| `get_columns` | `async def get_columns(self, table_name: str)` |  |
| `get_indexes` | `async def get_indexes(self, table_name: str)` | Get index info for a PostgreSQL table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str)` | Get foreign key info for a PostgreSQL table. |
| `is_connected` | `def is_connected(self)` |  |
| `dialect` | `def dialect(self)` |  |

### `SQLiteAdapter`

- Source: `aquilia/db/backends/sqlite.py`
- Bases: `DatabaseAdapter`
- Summary: SQLite adapter using the native ``aquilia.sqlite`` connection pool.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `connect` | `async def connect(self, url: str, **options)` |  |
| `disconnect` | `async def disconnect(self)` |  |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` |  |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` |  |
| `begin` | `async def begin(self)` |  |
| `commit` | `async def commit(self)` |  |
| `rollback` | `async def rollback(self)` |  |
| `savepoint` | `async def savepoint(self, name: str)` |  |
| `release_savepoint` | `async def release_savepoint(self, name: str)` |  |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` |  |
| `table_exists` | `async def table_exists(self, table_name: str)` |  |
| `get_tables` | `async def get_tables(self)` |  |
| `get_columns` | `async def get_columns(self, table_name: str)` |  |
| `get_indexes` | `async def get_indexes(self, table_name: str)` | Get index info for a table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str)` | Get foreign key info for a table. |
| `is_connected` | `def is_connected(self)` |  |
| `dialect` | `def dialect(self)` |  |
| `pool` | `def pool(self)` | Access the underlying connection pool (for advanced usage). |
| `metrics` | `def metrics(self)` | Access pool metrics. |

### `DatabaseConfig`

- Source: `aquilia/db/configs.py`
- Bases: `object`
- Summary: Base database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `to_url` | `def to_url(self)` | Generate a database connection URL. |
| `to_dict` | `def to_dict(self)` | Serialize to a flat dictionary for integration with ConfigLoader. |
| `get_engine_options` | `def get_engine_options(self)` | Get kwargs to pass to AquiliaDatabase / adapter. |
| `from_url` | `def from_url(cls, url: str, **overrides)` | Create a config from a URL string. |

### `SqliteConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Summary: SQLite database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `engine` | `str` | `'sqlite'` |
| `path` | `str` | `'db.sqlite3'` |
| `journal_mode` | `str` | `'WAL'` |
| `foreign_keys` | `bool` | `True` |
| `busy_timeout` | `int` | `5000` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_url` | `def to_url(self)` |  |
| `from_url` | `def from_url(cls, url: str, **overrides)` | Parse a sqlite:// URL into a SqliteConfig. |

### `PostgresConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Summary: PostgreSQL database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `to_url` | `def to_url(self)` |  |
| `get_engine_options` | `def get_engine_options(self)` |  |
| `from_url` | `def from_url(cls, url: str, **overrides)` | Parse a postgresql:// URL into a PostgresConfig. |

### `MysqlConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Summary: MySQL / MariaDB database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `to_url` | `def to_url(self)` |  |
| `get_engine_options` | `def get_engine_options(self)` |  |
| `from_url` | `def from_url(cls, url: str, **overrides)` | Parse a mysql:// URL into a MysqlConfig. |

### `OracleConfig`

- Source: `aquilia/db/configs.py`
- Bases: `DatabaseConfig`
- Summary: Oracle database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `to_url` | `def to_url(self)` |  |
| `get_dsn` | `def get_dsn(self)` | Get Oracle DSN in Easy Connect format. |
| `get_engine_options` | `def get_engine_options(self)` |  |
| `from_url` | `def from_url(cls, url: str, **overrides)` | Parse an oracle:// URL into an OracleConfig. |

### `AquiliaDatabase`

- Source: `aquilia/db/engine.py`
- Bases: `object`
- Summary: Async database engine for Aquilia.
- Decorators: `service(scope='app', name='AquiliaDatabase')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `async def on_startup(self)` | Lifecycle hook -- called by ``LifecycleCoordinator`` at app start. |
| `on_shutdown` | `async def on_shutdown(self)` | Lifecycle hook -- called by ``LifecycleCoordinator`` at app stop. |
| `connect` | `async def connect(self)` | Open database connection with retry logic. |
| `disconnect` | `async def disconnect(self)` | Close database connection. |
| `ensure_connected` | `async def ensure_connected(self)` | Ensure a live connection exists, reconnecting if needed. |
| `transaction` | `async def transaction(self)` | Async context manager for transactions. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a named savepoint within a transaction. |
| `release_savepoint` | `async def release_savepoint(self, name: str)` | Release (commit) a named savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` | Roll back to a named savepoint. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` | Execute a SQL statement. |
| `execute_many` | `async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]])` | Execute a SQL statement with multiple parameter sets. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` | Execute query and return all rows as dicts. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` | Execute query and return first row as dict, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None)` | Execute query and return scalar value from first row, first column. |
| `table_exists` | `async def table_exists(self, table_name: str)` | Check if a table exists in the database. |
| `get_tables` | `async def get_tables(self)` | List all table names in the database. |
| `get_columns` | `async def get_columns(self, table_name: str)` | Get column metadata for a table. |
| `is_connected` | `def is_connected(self)` |  |
| `url` | `def url(self)` |  |
| `driver` | `def driver(self)` |  |
| `dialect` | `def dialect(self)` | Return the SQL dialect name (sqlite, postgresql, mysql). |
| `capabilities` | `def capabilities(self)` | Return backend capabilities. |
| `adapter` | `def adapter(self)` | Direct access to the underlying adapter (advanced use). |
| `in_transaction` | `def in_transaction(self)` |  |
