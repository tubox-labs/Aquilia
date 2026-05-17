# SQLite Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `SqliteError` | `aquilia/sqlite/_errors.py` | Base exception for all aquilia.sqlite errors. |
| `SqliteConnectionError` | `aquilia/sqlite/_errors.py` | Connection open / close failed. |
| `PoolExhaustedError` | `aquilia/sqlite/_errors.py` | All connections in the pool are busy and the wait timed out. |
| `SqliteQueryError` | `aquilia/sqlite/_errors.py` | Query execution failed. |
| `SqliteIntegrityError` | `aquilia/sqlite/_errors.py` | Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL). |
| `SqliteSchemaError` | `aquilia/sqlite/_errors.py` | Schema-level error (missing table, missing column). |
| `SqliteTimeoutError` | `aquilia/sqlite/_errors.py` | Query or connection timed out. |
| `SqliteSecurityError` | `aquilia/sqlite/_errors.py` | Security violation (path traversal, sandbox escape). |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/sqlite/__init__.py`: ``aquilia.sqlite`` - Native async SQLite module for the Aquilia framework.
- `aquilia/sqlite/_backup.py`: Backup - Online SQLite backup API.
- `aquilia/sqlite/_compat.py`: Compatibility Shim - aiosqlite-compatible API for gradual migration.
- `aquilia/sqlite/_config.py`: SQLite Configuration - Extended pool and PRAGMA config for native SQLite.
- `aquilia/sqlite/_connection.py`: Async Connection - Thread-dispatched wrapper around ``sqlite3.Connection``.
- `aquilia/sqlite/_cursor.py`: Async Cursor - Streaming row iteration over query results.
- `aquilia/sqlite/_errors.py`: SQLite Errors - Exception hierarchy and fault mapping.
- `aquilia/sqlite/_metrics.py`: SQLite Metrics - Observable counters for the native SQLite module.
- `aquilia/sqlite/_pool.py`: Connection Pool - Async pool with N readers + 1 writer.
- `aquilia/sqlite/_pragma.py`: PRAGMA Builder - Build and apply SQLite PRAGMA statements from config.
- `aquilia/sqlite/_rows.py`: SQLite Row - Dict-like row with attribute access.
- `aquilia/sqlite/_service.py`: SQLite Service - DI-integrated pool lifecycle management.
- `aquilia/sqlite/_statement_cache.py`: Statement Cache - Per-connection LRU cache for prepared statements.
- `aquilia/sqlite/_transaction.py`: Transaction & Savepoint - Async context managers for transaction control.
