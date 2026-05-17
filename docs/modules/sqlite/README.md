# SQLite Documentation

This directory is the professional documentation set for `sqlite`. It is implementation-driven and aligned with the current source files under `aquilia/sqlite`.

## What This Covers

The native async SQLite module with connection pool, pragmas, transactions, savepoints, cursors, rows, statement cache, backup, metrics, and Aquilia fault mapping.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 20
- Configuration or dataclass-like types: 3
- Public functions: 8
- Constants detected: 6

## Fast Start

```python
from aquilia.sqlite import SqlitePoolConfig, create_pool

pool = await create_pool(SqlitePoolConfig(database="app.db", min_size=1, max_size=5))
async with pool.acquire() as conn:
    await conn.execute("create table if not exists events (id integer primary key, name text)")
    await conn.execute("insert into events (name) values (?)", ("started",))
await pool.close()
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
