# SQLite API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `CompatConnection` | `aquilia/sqlite/_compat.py` | object | aiosqlite-compatible connection object. |
| `SqlitePoolConfig` | `aquilia/sqlite/_config.py` | object | Comprehensive SQLite configuration for the native pool. |
| `AsyncConnection` | `aquilia/sqlite/_connection.py` | object | Async wrapper around a single ``sqlite3.Connection``. |
| `AsyncCursor` | `aquilia/sqlite/_cursor.py` | object | Async wrapper around a ``sqlite3.Cursor``. |
| `SqliteError` | `aquilia/sqlite/_errors.py` | Exception | Base exception for all aquilia.sqlite errors. |
| `SqliteConnectionError` | `aquilia/sqlite/_errors.py` | SqliteError | Connection open / close failed. |
| `PoolExhaustedError` | `aquilia/sqlite/_errors.py` | SqliteError | All connections in the pool are busy and the wait timed out. |
| `SqliteQueryError` | `aquilia/sqlite/_errors.py` | SqliteError | Query execution failed. |
| `SqliteIntegrityError` | `aquilia/sqlite/_errors.py` | SqliteQueryError | Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL). |
| `SqliteSchemaError` | `aquilia/sqlite/_errors.py` | SqliteError | Schema-level error (missing table, missing column). |
| `SqliteTimeoutError` | `aquilia/sqlite/_errors.py` | SqliteError | Query or connection timed out. |
| `SqliteSecurityError` | `aquilia/sqlite/_errors.py` | SqliteError | Security violation (path traversal, sandbox escape). |
| `SqliteMetrics` | `aquilia/sqlite/_metrics.py` | object | Aggregated metrics for the SQLite connection pool. |
| `ConnectionPool` | `aquilia/sqlite/_pool.py` | object | Async connection pool for SQLite. |
| `Row` | `aquilia/sqlite/_rows.py` | object | Immutable row object returned by query methods. |
| `SqliteService` | `aquilia/sqlite/_service.py` | object | DI-managed SQLite connection pool. |
| `CacheStats` | `aquilia/sqlite/_statement_cache.py` | object | Observable statistics for a statement cache. |
| `StatementCache` | `aquilia/sqlite/_statement_cache.py` | object | LRU statement cache for tracking SQL statement reuse. |
| `TransactionContext` | `aquilia/sqlite/_transaction.py` | object | Async context manager for a database transaction. |
| `SavepointContext` | `aquilia/sqlite/_transaction.py` | object | Async context manager for a savepoint. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `backup_database` | `aquilia/sqlite/_backup.py` | `async def backup_database(source_path: str, target_path: str, *, pages: int = -1, progress: Any = None, executor: ThreadPoolExecutor &#124; None = None) -> None` | Perform an online backup of a SQLite database. |
| `connect` | `aquilia/sqlite/_compat.py` | `async def connect(database: str = ':memory:', **kwargs: Any) -> CompatConnection` | aiosqlite-compatible ``connect()`` function. |
| `map_sqlite_error` | `aquilia/sqlite/_errors.py` | `def map_sqlite_error(exc: Exception, *, operation: str = '', sql: str = '', url: str = '') -> SqliteError` | Convert a ``sqlite3`` exception to an ``aquilia.sqlite`` exception. |
| `to_aquilia_fault` | `aquilia/sqlite/_errors.py` | `def to_aquilia_fault(exc: SqliteError, *, url: str = '', model: str = '<sqlite>', operation: str = '') -> Fault` | Convert an ``aquilia.sqlite`` exception into an Aquilia fault object. |
| `create_pool` | `aquilia/sqlite/_pool.py` | `async def create_pool(url_or_config: str &#124; SqlitePoolConfig &#124; None = None, *, min_size: int &#124; None = None, max_size: int &#124; None = None, **kwargs: Any) -> ConnectionPool` | Create and open a connection pool. |
| `build_pragmas` | `aquilia/sqlite/_pragma.py` | `def build_pragmas(config: SqlitePoolConfig, *, readonly: bool = False) -> list[str]` | Build a list of PRAGMA SQL strings for a connection. |
| `apply_pragmas` | `aquilia/sqlite/_pragma.py` | `def apply_pragmas(conn: sqlite3.Connection, pragmas: Sequence[str]) -> None` | Execute a sequence of PRAGMA statements on a raw ``sqlite3.Connection``. |
| `row_factory` | `aquilia/sqlite/_rows.py` | `def row_factory(cursor: Any, row_tuple: tuple[Any, ...]) -> Row` | ``sqlite3`` row factory function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `JOURNAL_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DELETE', 'TRUNCATE', 'PERSIST', 'MEMORY', 'WAL', 'OFF'})` |
| `SYNC_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'OFF', 'NORMAL', 'FULL', 'EXTRA'})` |
| `TEMP_STORE_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DEFAULT', 'FILE', 'MEMORY'})` |
| `_SP_NAME_RE` | `aquilia/sqlite/_connection.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SCHEMA_PATTERNS` | `aquilia/sqlite/_errors.py` | `('no such table', 'no such column', 'table already exists', 'no such index', 'duplicate column name')` |
| `_CONNECTION_PATTERNS` | `aquilia/sqlite/_errors.py` | `('database is locked', 'unable to open', 'disk I/O error', 'database disk image is malformed', 'attempt to write a readonly database')` |

## Detailed Classes And Methods

### Class: `CompatConnection`

- Source: `aquilia/sqlite/_compat.py`
- Bases: `object`
- Summary: aiosqlite-compatible connection object.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `execute` | `async def execute(self, sql: str, parameters: Sequence[Any] = ()) -> Any` |  | Execute a SQL statement (returns cursor-like). |
| `executemany` | `async def executemany(self, sql: str, parameters: Sequence[Sequence[Any]]) -> Any` |  | Execute with multiple parameter sets. |
| `executescript` | `async def executescript(self, script: str) -> None` |  | Execute a multi-statement script. |
| `commit` | `async def commit(self) -> None` |  | Commit (no-op: auto-commit is the default). |
| `rollback` | `async def rollback(self) -> None` |  | Rollback. |
| `close` | `async def close(self) -> None` |  | Close the pool. |

### Class: `SqlitePoolConfig`

- Source: `aquilia/sqlite/_config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Comprehensive SQLite configuration for the native pool.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `path` | `str` | `'db.sqlite3'` |
| `journal_mode` | `str` | `'WAL'` |
| `foreign_keys` | `bool` | `True` |
| `busy_timeout` | `int` | `5000` |
| `synchronous` | `str` | `'NORMAL'` |
| `cache_size` | `int` | `-8000` |
| `mmap_size` | `int` | `268435456` |
| `temp_store` | `str` | `'MEMORY'` |
| `wal_autocheckpoint` | `int` | `1000` |
| `pool_size` | `int` | `5` |
| `pool_min_size` | `int` | `2` |
| `pool_max_idle_time` | `float` | `300.0` |
| `pool_timeout` | `float` | `30.0` |
| `statement_cache_size` | `int` | `256` |
| `query_timeout` | `float` | `30.0` |
| `echo` | `bool` | `False` |
| `auto_commit` | `bool` | `True` |
| `enforce_path_security` | `bool` | `True` |
| `sandbox_root` | `str &#124; None` | `None` |
| `options` | `dict[str, Any]` | `field(default_factory=dict)` |
| `connect_retries` | `int` | `3` |
| `connect_retry_delay` | `float` | `0.5` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_sqlite_config` | `def from_sqlite_config(cls, cfg: SqliteConfig, **overrides: Any) -> SqlitePoolConfig` | classmethod | Create a ``SqlitePoolConfig`` from an existing ``SqliteConfig``. |
| `from_url` | `def from_url(cls, url: str, **overrides: Any) -> SqlitePoolConfig` | classmethod | Create from a ``sqlite:///`` URL string. |
| `to_url` | `def to_url(self) -> str` |  | Generate a ``sqlite:///`` URL from this config. |
| `is_memory` | `def is_memory(self) -> bool` | property | True if this is an in-memory database. |

### Class: `AsyncConnection`

- Source: `aquilia/sqlite/_connection.py`
- Bases: `object`
- Summary: Async wrapper around a single ``sqlite3.Connection``.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> AsyncCursor` |  | Execute a single SQL statement. |
| `execute_many` | `async def execute_many(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> int` |  | Execute a statement with multiple parameter sets. |
| `execute_script` | `async def execute_script(self, script: str) -> None` |  | Execute a multi-statement SQL script. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[Row]` |  | Execute and return all rows. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> Row &#124; None` |  | Execute and return the first row, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None, *, column: int = 0) -> Any` |  | Execute and return a single scalar value. |
| `begin` | `async def begin(self, *, mode: str = 'DEFERRED') -> None` |  | Start a transaction. |
| `commit` | `async def commit(self) -> None` |  | Commit the current transaction. |
| `rollback` | `async def rollback(self) -> None` |  | Rollback the current transaction. |
| `savepoint` | `async def savepoint(self, name: str) -> None` |  | Create a savepoint. |
| `release_savepoint` | `async def release_savepoint(self, name: str) -> None` |  | Release (commit) a savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str) -> None` |  | Rollback to a savepoint. |
| `transaction` | `def transaction(self, *, mode: str = 'DEFERRED') -> TransactionContext` |  | Return a transaction context manager. |
| `savepoint_ctx` | `def savepoint_ctx(self, name: str) -> SavepointContext` |  | Return a savepoint context manager. |
| `table_exists` | `async def table_exists(self, name: str) -> bool` |  | Check if a table exists. |
| `get_tables` | `async def get_tables(self) -> list[str]` |  | List all user table names. |
| `get_columns` | `async def get_columns(self, table_name: str) -> list[dict[str, Any]]` |  | Get column info for a table (PRAGMA table_info). |
| `get_indexes` | `async def get_indexes(self, table_name: str) -> list[dict[str, Any]]` |  | Get index info for a table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]` |  | Get foreign key info for a table. |
| `backup` | `async def backup(self, target: str &#124; AsyncConnection, *, pages: int = -1) -> None` |  | Online backup to another database. |
| `clear_cache` | `def clear_cache(self) -> None` |  | Clear the statement cache. |
| `cache_stats` | `def cache_stats(self) -> CacheStats` | property | Statement cache statistics. |
| `close` | `async def close(self) -> None` |  | Close the underlying sqlite3 connection. |
| `readonly` | `def readonly(self) -> bool` | property | Whether this is a read-only connection. |
| `in_transaction` | `def in_transaction(self) -> bool` | property | Whether a transaction is active. |
| `closed` | `def closed(self) -> bool` | property | Whether the connection has been closed. |
| `conn_id` | `def conn_id(self) -> int` | property | Unique connection identifier. |
| `age` | `def age(self) -> float` | property | Seconds since this connection was created. |
| `path` | `def path(self) -> str` | property | Database file path. |

### Class: `AsyncCursor`

- Source: `aquilia/sqlite/_cursor.py`
- Bases: `object`
- Summary: Async wrapper around a ``sqlite3.Cursor``.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `fetch_one` | `async def fetch_one(self) -> Row &#124; None` |  | Fetch the next row, or None if exhausted. |
| `fetch_many` | `async def fetch_many(self, size: int = 100) -> list[Row]` |  | Fetch up to *size* rows. |
| `fetch_all` | `async def fetch_all(self) -> list[Row]` |  | Fetch all remaining rows. |
| `close` | `async def close(self) -> None` |  | Close the cursor. |
| `description` | `def description(self) -> tuple[Any, ...] &#124; None` | property | Column descriptions from the last query. |
| `rowcount` | `def rowcount(self) -> int` | property | Number of rows affected by the last operation. |
| `lastrowid` | `def lastrowid(self) -> int &#124; None` | property | Row ID of the last inserted row. |

### Class: `SqliteError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `Exception`
- Summary: Base exception for all aquilia.sqlite errors.

### Class: `SqliteConnectionError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Connection open / close failed.

### Class: `PoolExhaustedError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: All connections in the pool are busy and the wait timed out.

### Class: `SqliteQueryError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Query execution failed.

### Class: `SqliteIntegrityError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteQueryError`
- Summary: Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL).

### Class: `SqliteSchemaError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Schema-level error (missing table, missing column).

### Class: `SqliteTimeoutError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Query or connection timed out.

### Class: `SqliteSecurityError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Security violation (path traversal, sandbox escape).

### Class: `SqliteMetrics`

- Source: `aquilia/sqlite/_metrics.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregated metrics for the SQLite connection pool.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `pool_size` | `int` | `0` |
| `pool_idle` | `int` | `0` |
| `pool_waiting` | `int` | `0` |
| `queries_total` | `int` | `0` |
| `query_errors_total` | `int` | `0` |
| `query_rows_total` | `int` | `0` |
| `query_latency_ns` | `int` | `0` |
| `transactions_total` | `int` | `0` |
| `transaction_commits` | `int` | `0` |
| `transaction_rollbacks` | `int` | `0` |
| `transaction_latency_ns` | `int` | `0` |
| `cache_hits` | `int` | `0` |
| `cache_misses` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record_query` | `def record_query(self, elapsed_ns: int, row_count: int = 0) -> None` |  | Record a successful query execution. |
| `record_query_error` | `def record_query_error(self) -> None` |  | Record a failed query. |
| `record_transaction` | `def record_transaction(self, elapsed_ns: int, *, committed: bool) -> None` |  | Record a completed transaction. |
| `record_cache_access` | `def record_cache_access(self, *, hit: bool) -> None` |  | Record a statement cache access. |
| `snapshot` | `def snapshot(self) -> dict[str, int &#124; float]` |  | Return a JSON-friendly snapshot of all metrics. |
| `reset` | `def reset(self) -> None` |  | Reset all counters to zero (useful in tests). |

### Class: `ConnectionPool`

- Source: `aquilia/sqlite/_pool.py`
- Bases: `object`
- Summary: Async connection pool for SQLite.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `open` | `async def open(self) -> None` |  | Open the pool: create the executor, writer, and initial readers. |
| `close` | `async def close(self) -> None` |  | Close all connections and shut down the executor. |
| `acquire` | `def acquire(self, *, readonly: bool = False) -> _AcquireContext` |  | Acquire a connection from the pool. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] &#124; None = None) -> Any` |  | Execute a write statement (acquires writer automatically). |
| `execute_many` | `async def execute_many(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> int` |  | Execute with multiple param sets (acquires writer). |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] &#124; None = None) -> list[Row]` |  | Fetch all rows (acquires reader). |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] &#124; None = None) -> Row &#124; None` |  | Fetch one row (acquires reader). |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] &#124; None = None, *, column: int = 0) -> Any` |  | Fetch a scalar value (acquires reader). |
| `transaction` | `def transaction(self, *, mode: str = 'DEFERRED') -> TransactionContext` |  | Create a transaction context manager using the writer connection. |
| `checkpoint` | `async def checkpoint(self, *, mode: str = 'PASSIVE') -> None` |  | Force a WAL checkpoint. |
| `vacuum` | `async def vacuum(self) -> None` |  | Run VACUUM on the database (requires exclusive access). |
| `size` | `def size(self) -> int` | property | Current total connections (readers + writer). |
| `idle` | `def idle(self) -> int` | property | Current idle reader connections. |
| `metrics` | `def metrics(self) -> SqliteMetrics` | property | Pool metrics. |
| `is_open` | `def is_open(self) -> bool` | property | Whether the pool is open. |
| `config` | `def config(self) -> SqlitePoolConfig` | property | Pool configuration. |

### Class: `Row`

- Source: `aquilia/sqlite/_rows.py`
- Bases: `object`
- Summary: Immutable row object returned by query methods.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `keys` | `def keys(self) -> tuple[str, ...]` |  | Return column names. |
| `values` | `def values(self) -> tuple[Any, ...]` |  | Return column values. |
| `items` | `def items(self) -> tuple[tuple[str, Any], ...]` |  | Return (key, value) pairs. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to a plain dictionary. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Get a value by column name with a default. |

### Class: `SqliteService`

- Source: `aquilia/sqlite/_service.py`
- Bases: `object`
- Decorators: `service`
- Summary: DI-managed SQLite connection pool.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `startup` | `async def startup(self) -> None` |  | Open the connection pool. |
| `shutdown` | `async def shutdown(self) -> None` |  | Close the connection pool. |
| `pool` | `def pool(self) -> ConnectionPool` | property | The underlying connection pool. |
| `metrics` | `def metrics(self) -> SqliteMetrics` | property | Pool metrics. |
| `is_running` | `def is_running(self) -> bool` | property | Whether the service is running. |

### Class: `CacheStats`

- Source: `aquilia/sqlite/_statement_cache.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Observable statistics for a statement cache.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `hits` | `int` | `0` |
| `misses` | `int` | `0` |
| `evictions` | `int` | `0` |
| `size` | `int` | `0` |
| `capacity` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `hit_rate` | `def hit_rate(self) -> float` | property | Fraction of hits out of total accesses (0.0 - 1.0). |
| `snapshot` | `def snapshot(self) -> dict[str, Any]` |  | Return a JSON-friendly snapshot. |

### Class: `StatementCache`

- Source: `aquilia/sqlite/_statement_cache.py`
- Bases: `object`
- Summary: LRU statement cache for tracking SQL statement reuse.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `stats` | `def stats(self) -> CacheStats` | property | Current cache statistics. |
| `touch` | `def touch(self, sql: str) -> bool` |  | Record an SQL statement access. |
| `clear` | `def clear(self) -> None` |  | Clear all cached statement entries. |

### Class: `TransactionContext`

- Source: `aquilia/sqlite/_transaction.py`
- Bases: `object`
- Summary: Async context manager for a database transaction.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `savepoint` | `def savepoint(self, name: str) -> SavepointContext` |  | Create a nested savepoint within this transaction. |

### Class: `SavepointContext`

- Source: `aquilia/sqlite/_transaction.py`
- Bases: `object`
- Summary: Async context manager for a savepoint.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `rollback` | `async def rollback(self) -> None` |  | Manually rollback to this savepoint. |
| `release` | `async def release(self) -> None` |  | Manually release (commit) this savepoint. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `backup_database` | `aquilia/sqlite/_backup.py` | `async def backup_database(source_path: str, target_path: str, *, pages: int = -1, progress: Any = None, executor: ThreadPoolExecutor &#124; None = None) -> None` | Perform an online backup of a SQLite database. |
| `connect` | `aquilia/sqlite/_compat.py` | `async def connect(database: str = ':memory:', **kwargs: Any) -> CompatConnection` | aiosqlite-compatible ``connect()`` function. |
| `map_sqlite_error` | `aquilia/sqlite/_errors.py` | `def map_sqlite_error(exc: Exception, *, operation: str = '', sql: str = '', url: str = '') -> SqliteError` | Convert a ``sqlite3`` exception to an ``aquilia.sqlite`` exception. |
| `to_aquilia_fault` | `aquilia/sqlite/_errors.py` | `def to_aquilia_fault(exc: SqliteError, *, url: str = '', model: str = '<sqlite>', operation: str = '') -> Fault` | Convert an ``aquilia.sqlite`` exception into an Aquilia fault object. |
| `create_pool` | `aquilia/sqlite/_pool.py` | `async def create_pool(url_or_config: str &#124; SqlitePoolConfig &#124; None = None, *, min_size: int &#124; None = None, max_size: int &#124; None = None, **kwargs: Any) -> ConnectionPool` | Create and open a connection pool. |
| `build_pragmas` | `aquilia/sqlite/_pragma.py` | `def build_pragmas(config: SqlitePoolConfig, *, readonly: bool = False) -> list[str]` | Build a list of PRAGMA SQL strings for a connection. |
| `apply_pragmas` | `aquilia/sqlite/_pragma.py` | `def apply_pragmas(conn: sqlite3.Connection, pragmas: Sequence[str]) -> None` | Execute a sequence of PRAGMA statements on a raw ``sqlite3.Connection``. |
| `row_factory` | `aquilia/sqlite/_rows.py` | `def row_factory(cursor: Any, row_tuple: tuple[Any, ...]) -> Row` | ``sqlite3`` row factory function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `JOURNAL_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DELETE', 'TRUNCATE', 'PERSIST', 'MEMORY', 'WAL', 'OFF'})` |
| `SYNC_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'OFF', 'NORMAL', 'FULL', 'EXTRA'})` |
| `TEMP_STORE_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DEFAULT', 'FILE', 'MEMORY'})` |
| `_SP_NAME_RE` | `aquilia/sqlite/_connection.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SCHEMA_PATTERNS` | `aquilia/sqlite/_errors.py` | `('no such table', 'no such column', 'table already exists', 'no such index', 'duplicate column name')` |
| `_CONNECTION_PATTERNS` | `aquilia/sqlite/_errors.py` | `('database is locked', 'unable to open', 'disk I/O error', 'database disk image is malformed', 'attempt to write a readonly database')` |
