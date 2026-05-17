# Sqlite Architecture

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

## Source Boundaries

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

## Internal Shape

`sqlite` has 14 Python files, 20 public classes, 8 public module-level functions, and 20 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 8 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `._config` | 6 |
| `._metrics` | 4 |
| `._rows` | 4 |
| `._errors` | 3 |
| `._pool` | 3 |
| `._transaction` | 3 |
| `._connection` | 2 |
| `._pragma` | 2 |
| `._statement_cache` | 2 |
| `._backup` | 1 |
| `._cursor` | 1 |
| `._service` | 1 |
| `aquilia.db.configs` | 1 |
| `aquilia.di.decorators` | 1 |
| `aquilia.faults.core` | 1 |
| `aquilia.faults.domains` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 14 |
| `typing` | 9 |
| `collections` | 8 |
| `logging` | 6 |
| `sqlite3` | 6 |
| `asyncio` | 4 |
| `concurrent` | 4 |
| `dataclasses` | 3 |
| `time` | 2 |
| `contextlib` | 1 |
| `os` | 1 |
| `re` | 1 |
| `uuid` | 1 |
| `warnings` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `SqlitePoolConfig` | `aquilia/sqlite/_config.py` | Comprehensive SQLite configuration for the native pool. |

## Error Handling

Fault/error classes defined here:

`SqliteError`, `SqliteConnectionError`, `PoolExhaustedError`, `SqliteQueryError`, `SqliteIntegrityError`, `SqliteSchemaError`, `SqliteTimeoutError`, `SqliteSecurityError`
