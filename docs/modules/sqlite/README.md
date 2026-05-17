# sqlite Module

## Purpose

Native async SQLite support. Use this module for pooled SQLite connections, pragmas, statements, transactions, savepoints, backups, row factories, metrics, and Aquilia fault mapping.

## Source Coverage

- Python files: 14
- Public classes: 20
- Dataclasses: 3
- Enums: 0
- Public functions: 8

## How It Fits In Aquilia

1. Import the package from `aquilia.sqlite` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `CompatConnection` | `aquilia/sqlite/_compat.py` | aiosqlite-compatible connection object. |
| `SqlitePoolConfig` | `aquilia/sqlite/_config.py` | Comprehensive SQLite configuration for the native pool. |
| `AsyncConnection` | `aquilia/sqlite/_connection.py` | Async wrapper around a single ``sqlite3.Connection``. |
| `AsyncCursor` | `aquilia/sqlite/_cursor.py` | Async wrapper around a ``sqlite3.Cursor``. |
| `SqliteError` | `aquilia/sqlite/_errors.py` | Base exception for all aquilia.sqlite errors. |
| `SqliteConnectionError` | `aquilia/sqlite/_errors.py` | Connection open / close failed. |
| `PoolExhaustedError` | `aquilia/sqlite/_errors.py` | All connections in the pool are busy and the wait timed out. |
| `SqliteQueryError` | `aquilia/sqlite/_errors.py` | Query execution failed. |
| `SqliteIntegrityError` | `aquilia/sqlite/_errors.py` | Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL). |
| `SqliteSchemaError` | `aquilia/sqlite/_errors.py` | Schema-level error (missing table, missing column). |
| `SqliteTimeoutError` | `aquilia/sqlite/_errors.py` | Query or connection timed out. |
| `SqliteSecurityError` | `aquilia/sqlite/_errors.py` | Security violation (path traversal, sandbox escape). |
| `SqliteMetrics` | `aquilia/sqlite/_metrics.py` | Aggregated metrics for the SQLite connection pool. |
| `ConnectionPool` | `aquilia/sqlite/_pool.py` | Async connection pool for SQLite. |
| `Row` | `aquilia/sqlite/_rows.py` | Immutable row object returned by query methods. |
| `SqliteService` | `aquilia/sqlite/_service.py` | DI-managed SQLite connection pool. |
| `CacheStats` | `aquilia/sqlite/_statement_cache.py` | Observable statistics for a statement cache. |
| `StatementCache` | `aquilia/sqlite/_statement_cache.py` | LRU statement cache for tracking SQL statement reuse. |
| `TransactionContext` | `aquilia/sqlite/_transaction.py` | Async context manager for a database transaction. |
| `SavepointContext` | `aquilia/sqlite/_transaction.py` | Async context manager for a savepoint. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `backup_database` | `aquilia/sqlite/_backup.py` | Perform an online backup of a SQLite database. |
| `connect` | `aquilia/sqlite/_compat.py` | aiosqlite-compatible ``connect()`` function. |
| `map_sqlite_error` | `aquilia/sqlite/_errors.py` | Convert a ``sqlite3`` exception to an ``aquilia.sqlite`` exception. |
| `to_aquilia_fault` | `aquilia/sqlite/_errors.py` | Convert an ``aquilia.sqlite`` exception into an Aquilia fault object. |
| `create_pool` | `aquilia/sqlite/_pool.py` | Create and open a connection pool. |
| `build_pragmas` | `aquilia/sqlite/_pragma.py` | Build a list of PRAGMA SQL strings for a connection. |
| `apply_pragmas` | `aquilia/sqlite/_pragma.py` | Execute a sequence of PRAGMA statements on a raw ``sqlite3.Connection``. |
| `row_factory` | `aquilia/sqlite/_rows.py` | ``sqlite3`` row factory function. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/sqlite/__init__.py` | ``aquilia.sqlite`` - Native async SQLite module for the Aquilia framework. |
| `aquilia/sqlite/_backup.py` | Backup - Online SQLite backup API. |
| `aquilia/sqlite/_compat.py` | Compatibility Shim - aiosqlite-compatible API for gradual migration. |
| `aquilia/sqlite/_config.py` | SQLite Configuration - Extended pool and PRAGMA config for native SQLite. |
| `aquilia/sqlite/_connection.py` | Async Connection - Thread-dispatched wrapper around ``sqlite3.Connection``. |
| `aquilia/sqlite/_cursor.py` | Async Cursor - Streaming row iteration over query results. |
| `aquilia/sqlite/_errors.py` | SQLite Errors - Exception hierarchy and fault mapping. |
| `aquilia/sqlite/_metrics.py` | SQLite Metrics - Observable counters for the native SQLite module. |
| `aquilia/sqlite/_pool.py` | Connection Pool - Async pool with N readers + 1 writer. |
| `aquilia/sqlite/_pragma.py` | PRAGMA Builder - Build and apply SQLite PRAGMA statements from config. |
| `aquilia/sqlite/_rows.py` | SQLite Row - Dict-like row with attribute access. |
| `aquilia/sqlite/_service.py` | SQLite Service - DI-integrated pool lifecycle management. |
| `aquilia/sqlite/_statement_cache.py` | Statement Cache - Per-connection LRU cache for prepared statements. |
| `aquilia/sqlite/_transaction.py` | Transaction & Savepoint - Async context managers for transaction control. |

## Testing Pointers

Search `tests/` for `sqlite` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
