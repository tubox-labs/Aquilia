# Db Configuration

Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/db/__init__.py` | 68 | 0 | 0 | Aquilia Database -- async-first database layer. |
| `aquilia/db/backends/__init__.py` | 27 | 0 | 0 | Aquilia DB Backends Package -- pluggable database adapters. |
| `aquilia/db/backends/base.py` | 222 | 5 | 0 | Aquilia DB Backend -- Base Adapter Interface. |
| `aquilia/db/backends/mysql.py` | 443 | 1 | 0 | Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql. |
| `aquilia/db/backends/oracle.py` | 610 | 1 | 0 | Aquilia DB Backend -- Oracle adapter via python-oracledb. |
| `aquilia/db/backends/postgres.py` | 424 | 1 | 0 | Aquilia DB Backend -- PostgreSQL adapter via asyncpg. |
| `aquilia/db/backends/sqlite.py` | 332 | 1 | 0 | Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module. |
| `aquilia/db/configs.py` | 519 | 5 | 0 | Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs. |
| `aquilia/db/engine.py` | 621 | 1 | 4 | Aquilia Database Engine -- async-first, multi-backend, production-ready. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `DatabaseConfig` | `aquilia/db/configs.py` | `to_url`, `to_dict`, `get_engine_options`, `from_url` | Base database configuration. |
| `SqliteConfig` | `aquilia/db/configs.py` | `to_url`, `from_url` | SQLite database configuration. |
| `PostgresConfig` | `aquilia/db/configs.py` | `to_url`, `get_engine_options`, `from_url` | PostgreSQL database configuration. |
| `MysqlConfig` | `aquilia/db/configs.py` | `to_url`, `get_engine_options`, `from_url` | MySQL / MariaDB database configuration. |
| `OracleConfig` | `aquilia/db/configs.py` | `to_url`, `get_dsn`, `get_engine_options`, `from_url` | Oracle database configuration. |

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
