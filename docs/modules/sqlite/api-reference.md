# Sqlite API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/sqlite/__init__.py` | 123 | 0 | 0 | ``aquilia.sqlite`` — Native async SQLite module for the Aquilia framework. |
| `aquilia/sqlite/_backup.py` | 58 | 0 | 1 | Backup — Online SQLite backup API. |
| `aquilia/sqlite/_compat.py` | 140 | 1 | 1 | Compatibility Shim — aiosqlite-compatible API for gradual migration. |
| `aquilia/sqlite/_config.py` | 206 | 1 | 0 | SQLite Configuration — Extended pool and PRAGMA config for native SQLite. |
| `aquilia/sqlite/_connection.py` | 538 | 1 | 0 | Async Connection — Thread-dispatched wrapper around ``sqlite3.Connection``. |
| `aquilia/sqlite/_cursor.py` | 97 | 1 | 0 | Async Cursor — Streaming row iteration over query results. |
| `aquilia/sqlite/_errors.py` | 233 | 8 | 2 | SQLite Errors — Exception hierarchy and fault mapping. |
| `aquilia/sqlite/_metrics.py` | 130 | 1 | 0 | SQLite Metrics — Observable counters for the native SQLite module. |
| `aquilia/sqlite/_pool.py` | 508 | 1 | 1 | Connection Pool — Async pool with N readers + 1 writer. |
| `aquilia/sqlite/_pragma.py` | 95 | 0 | 2 | PRAGMA Builder — Build and apply SQLite PRAGMA statements from config. |
| `aquilia/sqlite/_rows.py` | 134 | 1 | 1 | SQLite Row — Dict-like row with attribute access. |
| `aquilia/sqlite/_service.py` | 110 | 1 | 0 | SQLite Service — DI-integrated pool lifecycle management. |
| `aquilia/sqlite/_statement_cache.py` | 138 | 2 | 0 | Statement Cache — Per-connection LRU cache for prepared statements. |
| `aquilia/sqlite/_transaction.py` | 162 | 2 | 0 | Transaction & Savepoint — Async context managers for transaction control. |

## Public Exports

`AsyncConnection`, `AsyncCursor`, `CacheStats`, `CompatConnection`, `ConnectionPool`, `JOURNAL_MODES`, `PoolExhaustedError`, `Row`, `SYNC_MODES`, `SavepointContext`, `SqliteConnectionError`, `SqliteError`, `SqliteIntegrityError`, `SqliteMetrics`, `SqlitePoolConfig`, `SqliteQueryError`, `SqliteSchemaError`, `SqliteSecurityError`, `SqliteService`, `SqliteTimeoutError`, `StatementCache`, `TEMP_STORE_MODES`, `TransactionContext`, `apply_pragmas`, `backup_database`, `build_pragmas`, `connect`, `create_pool`, `map_sqlite_error`, `row_factory`, `to_aquilia_fault`

## Public Class Summary

| Class | Source | Bases | Summary |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `backup_database` | `aquilia/sqlite/_backup.py` | `async def backup_database(source_path: str, target_path: str, *, pages: int=-1, progress: Any=None, executor: ThreadPoolExecutor \| None=None)` | Perform an online backup of a SQLite database. |
| `connect` | `aquilia/sqlite/_compat.py` | `async def connect(database: str=':memory:', **kwargs: Any)` | aiosqlite-compatible ``connect()`` function. |
| `map_sqlite_error` | `aquilia/sqlite/_errors.py` | `def map_sqlite_error(exc: Exception, *, operation: str='', sql: str='', url: str='')` | Convert a ``sqlite3`` exception to an ``aquilia.sqlite`` exception. |
| `to_aquilia_fault` | `aquilia/sqlite/_errors.py` | `def to_aquilia_fault(exc: SqliteError, *, url: str='', model: str='<sqlite>', operation: str='')` | Convert an ``aquilia.sqlite`` exception into an Aquilia fault object. |
| `create_pool` | `aquilia/sqlite/_pool.py` | `async def create_pool(url_or_config: str \| SqlitePoolConfig \| None=None, *, min_size: int \| None=None, max_size: int \| None=None, **kwargs: Any)` | Create and open a connection pool. |
| `build_pragmas` | `aquilia/sqlite/_pragma.py` | `def build_pragmas(config: SqlitePoolConfig, *, readonly: bool=False)` | Build a list of PRAGMA SQL strings for a connection. |
| `apply_pragmas` | `aquilia/sqlite/_pragma.py` | `def apply_pragmas(conn: sqlite3.Connection, pragmas: Sequence[str])` | Execute a sequence of PRAGMA statements on a raw ``sqlite3.Connection``. |
| `row_factory` | `aquilia/sqlite/_rows.py` | `def row_factory(cursor: Any, row_tuple: tuple[Any, ...])` | ``sqlite3`` row factory function. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `JOURNAL_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DELETE', 'TRUNCATE', 'PERSIST', 'MEMORY', 'WAL', 'OFF'})` |
| `SYNC_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'OFF', 'NORMAL', 'FULL', 'EXTRA'})` |
| `TEMP_STORE_MODES` | `aquilia/sqlite/_config.py` | `frozenset({'DEFAULT', 'FILE', 'MEMORY'})` |
| `_SP_NAME_RE` | `aquilia/sqlite/_connection.py` | `re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')` |
| `_SCHEMA_PATTERNS` | `aquilia/sqlite/_errors.py` | `('no such table', 'no such column', 'table already exists', 'no such index', 'duplicate column name')` |
| `_CONNECTION_PATTERNS` | `aquilia/sqlite/_errors.py` | `('database is locked', 'unable to open', 'disk I/O error', 'database disk image is malformed', 'attempt to write a readonly database')` |

## Detailed Classes And Methods

### `CompatConnection`

- Source: `aquilia/sqlite/_compat.py`
- Bases: `object`
- Summary: aiosqlite-compatible connection object.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `execute` | `async def execute(self, sql: str, parameters: Sequence[Any]=())` | Execute a SQL statement (returns cursor-like). |
| `executemany` | `async def executemany(self, sql: str, parameters: Sequence[Sequence[Any]])` | Execute with multiple parameter sets. |
| `executescript` | `async def executescript(self, script: str)` | Execute a multi-statement script. |
| `commit` | `async def commit(self)` | Commit (no-op: auto-commit is the default). |
| `rollback` | `async def rollback(self)` | Rollback. |
| `close` | `async def close(self)` | Close the pool. |

### `SqlitePoolConfig`

- Source: `aquilia/sqlite/_config.py`
- Bases: `object`
- Summary: Comprehensive SQLite configuration for the native pool.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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
| `sandbox_root` | `str \| None` | `None` |
| `options` | `dict[str, Any]` | `field(default_factory=dict)` |
| `connect_retries` | `int` | `3` |
| `connect_retry_delay` | `float` | `0.5` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_sqlite_config` | `def from_sqlite_config(cls, cfg: SqliteConfig, **overrides: Any)` | Create a ``SqlitePoolConfig`` from an existing ``SqliteConfig``. |
| `from_url` | `def from_url(cls, url: str, **overrides: Any)` | Create from a ``sqlite:///`` URL string. |
| `to_url` | `def to_url(self)` | Generate a ``sqlite:///`` URL from this config. |
| `is_memory` | `def is_memory(self)` | True if this is an in-memory database. |

### `AsyncConnection`

- Source: `aquilia/sqlite/_connection.py`
- Bases: `object`
- Summary: Async wrapper around a single ``sqlite3.Connection``.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` | Execute a single SQL statement. |
| `execute_many` | `async def execute_many(self, sql: str, params_seq: Sequence[Sequence[Any]])` | Execute a statement with multiple parameter sets. |
| `execute_script` | `async def execute_script(self, script: str)` | Execute a multi-statement SQL script. |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` | Execute and return all rows. |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` | Execute and return the first row, or None. |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None, *, column: int=0)` | Execute and return a single scalar value. |
| `begin` | `async def begin(self, *, mode: str='DEFERRED')` | Start a transaction. |
| `commit` | `async def commit(self)` | Commit the current transaction. |
| `rollback` | `async def rollback(self)` | Rollback the current transaction. |
| `savepoint` | `async def savepoint(self, name: str)` | Create a savepoint. |
| `release_savepoint` | `async def release_savepoint(self, name: str)` | Release (commit) a savepoint. |
| `rollback_to_savepoint` | `async def rollback_to_savepoint(self, name: str)` | Rollback to a savepoint. |
| `transaction` | `def transaction(self, *, mode: str='DEFERRED')` | Return a transaction context manager. |
| `savepoint_ctx` | `def savepoint_ctx(self, name: str)` | Return a savepoint context manager. |
| `table_exists` | `async def table_exists(self, name: str)` | Check if a table exists. |
| `get_tables` | `async def get_tables(self)` | List all user table names. |
| `get_columns` | `async def get_columns(self, table_name: str)` | Get column info for a table (PRAGMA table_info). |
| `get_indexes` | `async def get_indexes(self, table_name: str)` | Get index info for a table. |
| `get_foreign_keys` | `async def get_foreign_keys(self, table_name: str)` | Get foreign key info for a table. |
| `backup` | `async def backup(self, target: str \| AsyncConnection, *, pages: int=-1)` | Online backup to another database. |
| `clear_cache` | `def clear_cache(self)` | Clear the statement cache. |
| `cache_stats` | `def cache_stats(self)` | Statement cache statistics. |
| `close` | `async def close(self)` | Close the underlying sqlite3 connection. |
| `readonly` | `def readonly(self)` | Whether this is a read-only connection. |
| `in_transaction` | `def in_transaction(self)` | Whether a transaction is active. |
| `closed` | `def closed(self)` | Whether the connection has been closed. |
| `conn_id` | `def conn_id(self)` | Unique connection identifier. |
| `age` | `def age(self)` | Seconds since this connection was created. |
| `path` | `def path(self)` | Database file path. |

### `AsyncCursor`

- Source: `aquilia/sqlite/_cursor.py`
- Bases: `object`
- Summary: Async wrapper around a ``sqlite3.Cursor``.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `fetch_one` | `async def fetch_one(self)` | Fetch the next row, or None if exhausted. |
| `fetch_many` | `async def fetch_many(self, size: int=100)` | Fetch up to *size* rows. |
| `fetch_all` | `async def fetch_all(self)` | Fetch all remaining rows. |
| `close` | `async def close(self)` | Close the cursor. |
| `description` | `def description(self)` | Column descriptions from the last query. |
| `rowcount` | `def rowcount(self)` | Number of rows affected by the last operation. |
| `lastrowid` | `def lastrowid(self)` | Row ID of the last inserted row. |

### `SqliteError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `Exception`
- Summary: Base exception for all aquilia.sqlite errors.

### `SqliteConnectionError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Connection open / close failed.

### `PoolExhaustedError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: All connections in the pool are busy and the wait timed out.

### `SqliteQueryError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Query execution failed.

### `SqliteIntegrityError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteQueryError`
- Summary: Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL).

### `SqliteSchemaError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Schema-level error (missing table, missing column).

### `SqliteTimeoutError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Query or connection timed out.

### `SqliteSecurityError`

- Source: `aquilia/sqlite/_errors.py`
- Bases: `SqliteError`
- Summary: Security violation (path traversal, sandbox escape).

### `SqliteMetrics`

- Source: `aquilia/sqlite/_metrics.py`
- Bases: `object`
- Summary: Aggregated metrics for the SQLite connection pool.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `record_query` | `def record_query(self, elapsed_ns: int, row_count: int=0)` | Record a successful query execution. |
| `record_query_error` | `def record_query_error(self)` | Record a failed query. |
| `record_transaction` | `def record_transaction(self, elapsed_ns: int, *, committed: bool)` | Record a completed transaction. |
| `record_cache_access` | `def record_cache_access(self, *, hit: bool)` | Record a statement cache access. |
| `snapshot` | `def snapshot(self)` | Return a JSON-friendly snapshot of all metrics. |
| `reset` | `def reset(self)` | Reset all counters to zero (useful in tests). |

### `ConnectionPool`

- Source: `aquilia/sqlite/_pool.py`
- Bases: `object`
- Summary: Async connection pool for SQLite.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `open` | `async def open(self)` | Open the pool: create the executor, writer, and initial readers. |
| `close` | `async def close(self)` | Close all connections and shut down the executor. |
| `acquire` | `def acquire(self, *, readonly: bool=False)` | Acquire a connection from the pool. |
| `execute` | `async def execute(self, sql: str, params: Sequence[Any] \| None=None)` | Execute a write statement (acquires writer automatically). |
| `execute_many` | `async def execute_many(self, sql: str, params_seq: Sequence[Sequence[Any]])` | Execute with multiple param sets (acquires writer). |
| `fetch_all` | `async def fetch_all(self, sql: str, params: Sequence[Any] \| None=None)` | Fetch all rows (acquires reader). |
| `fetch_one` | `async def fetch_one(self, sql: str, params: Sequence[Any] \| None=None)` | Fetch one row (acquires reader). |
| `fetch_val` | `async def fetch_val(self, sql: str, params: Sequence[Any] \| None=None, *, column: int=0)` | Fetch a scalar value (acquires reader). |
| `transaction` | `def transaction(self, *, mode: str='DEFERRED')` | Create a transaction context manager using the writer connection. |
| `checkpoint` | `async def checkpoint(self, *, mode: str='PASSIVE')` | Force a WAL checkpoint. |
| `vacuum` | `async def vacuum(self)` | Run VACUUM on the database (requires exclusive access). |
| `size` | `def size(self)` | Current total connections (readers + writer). |
| `idle` | `def idle(self)` | Current idle reader connections. |
| `metrics` | `def metrics(self)` | Pool metrics. |
| `is_open` | `def is_open(self)` | Whether the pool is open. |
| `config` | `def config(self)` | Pool configuration. |

### `Row`

- Source: `aquilia/sqlite/_rows.py`
- Bases: `object`
- Summary: Immutable row object returned by query methods.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `keys` | `def keys(self)` | Return column names. |
| `values` | `def values(self)` | Return column values. |
| `items` | `def items(self)` | Return (key, value) pairs. |
| `to_dict` | `def to_dict(self)` | Convert to a plain dictionary. |
| `get` | `def get(self, key: str, default: Any=None)` | Get a value by column name with a default. |

### `SqliteService`

- Source: `aquilia/sqlite/_service.py`
- Bases: `object`
- Summary: DI-managed SQLite connection pool.
- Decorators: `service(scope='app', name='SqliteService')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `startup` | `async def startup(self)` | Open the connection pool. |
| `shutdown` | `async def shutdown(self)` | Close the connection pool. |
| `pool` | `def pool(self)` | The underlying connection pool. |
| `metrics` | `def metrics(self)` | Pool metrics. |
| `is_running` | `def is_running(self)` | Whether the service is running. |

### `CacheStats`

- Source: `aquilia/sqlite/_statement_cache.py`
- Bases: `object`
- Summary: Observable statistics for a statement cache.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `hits` | `int` | `0` |
| `misses` | `int` | `0` |
| `evictions` | `int` | `0` |
| `size` | `int` | `0` |
| `capacity` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `hit_rate` | `def hit_rate(self)` | Fraction of hits out of total accesses (0.0 – 1.0). |
| `snapshot` | `def snapshot(self)` | Return a JSON-friendly snapshot. |

### `StatementCache`

- Source: `aquilia/sqlite/_statement_cache.py`
- Bases: `object`
- Summary: LRU statement cache for tracking SQL statement reuse.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `stats` | `def stats(self)` | Current cache statistics. |
| `touch` | `def touch(self, sql: str)` | Record an SQL statement access. |
| `clear` | `def clear(self)` | Clear all cached statement entries. |

### `TransactionContext`

- Source: `aquilia/sqlite/_transaction.py`
- Bases: `object`
- Summary: Async context manager for a database transaction.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `savepoint` | `def savepoint(self, name: str)` | Create a nested savepoint within this transaction. |

### `SavepointContext`

- Source: `aquilia/sqlite/_transaction.py`
- Bases: `object`
- Summary: Async context manager for a savepoint.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `rollback` | `async def rollback(self)` | Manually rollback to this savepoint. |
| `release` | `async def release(self)` | Manually release (commit) this savepoint. |
