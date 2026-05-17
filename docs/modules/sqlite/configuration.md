# Sqlite Configuration

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `SqlitePoolConfig` | `aquilia/sqlite/_config.py` | `from_sqlite_config`, `from_url`, `to_url`, `is_memory` | Comprehensive SQLite configuration for the native pool. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
