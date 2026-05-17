# SQLite Architecture

## Runtime Role

The native async SQLite module with connection pool, pragmas, transactions, savepoints, cursors, rows, statement cache, backup, metrics, and Aquilia fault mapping.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 14 |
| `typing` | 9 |
| `collections` | 8 |
| `_config` | 6 |
| `logging` | 6 |
| `sqlite3` | 6 |
| `_metrics` | 4 |
| `_rows` | 4 |
| `aquilia` | 4 |
| `asyncio` | 4 |
| `concurrent` | 4 |
| `_errors` | 3 |
| `_pool` | 3 |
| `_transaction` | 3 |
| `dataclasses` | 3 |
| `_connection` | 2 |
| `_pragma` | 2 |
| `_statement_cache` | 2 |
| `time` | 2 |
| `_backup` | 1 |
| `_cursor` | 1 |
| `_service` | 1 |
| `contextlib` | 1 |
| `os` | 1 |
| `re` | 1 |
| `uuid` | 1 |
| `warnings` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
