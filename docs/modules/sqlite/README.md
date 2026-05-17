# Sqlite Documentation

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

## Coverage Snapshot

- Source files: 14
- Source lines: 2672
- Public classes: 20
- Public module functions: 8
- Constants/module flags: 20
- Public exports in `__all__`: 31

## Source Files Read

- `aquilia/sqlite/__init__.py`: ``aquilia.sqlite`` — Native async SQLite module for the Aquilia framework.
- `aquilia/sqlite/_backup.py`: Backup — Online SQLite backup API.
- `aquilia/sqlite/_compat.py`: Compatibility Shim — aiosqlite-compatible API for gradual migration.
- `aquilia/sqlite/_config.py`: SQLite Configuration — Extended pool and PRAGMA config for native SQLite.
- `aquilia/sqlite/_connection.py`: Async Connection — Thread-dispatched wrapper around ``sqlite3.Connection``.
- `aquilia/sqlite/_cursor.py`: Async Cursor — Streaming row iteration over query results.
- `aquilia/sqlite/_errors.py`: SQLite Errors — Exception hierarchy and fault mapping.
- `aquilia/sqlite/_metrics.py`: SQLite Metrics — Observable counters for the native SQLite module.
- `aquilia/sqlite/_pool.py`: Connection Pool — Async pool with N readers + 1 writer.
- `aquilia/sqlite/_pragma.py`: PRAGMA Builder — Build and apply SQLite PRAGMA statements from config.
- `aquilia/sqlite/_rows.py`: SQLite Row — Dict-like row with attribute access.
- `aquilia/sqlite/_service.py`: SQLite Service — DI-integrated pool lifecycle management.
- `aquilia/sqlite/_statement_cache.py`: Statement Cache — Per-connection LRU cache for prepared statements.
- `aquilia/sqlite/_transaction.py`: Transaction & Savepoint — Async context managers for transaction control.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
