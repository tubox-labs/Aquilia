# Sqlite Troubleshooting

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq db makemigrations`
- `aq db migrate`
- `aq db dump`
- `aq db shell`
- `aq db inspectdb`
- `aq db showmigrations`
- `aq db sqlmigrate`
- `aq db status`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
