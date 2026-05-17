# Db Troubleshooting

Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers.

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
| `aquilia/db/__init__.py` | 68 | 0 | 0 | Aquilia Database -- async-first database layer. |
| `aquilia/db/backends/__init__.py` | 27 | 0 | 0 | Aquilia DB Backends Package -- pluggable database adapters. |
| `aquilia/db/backends/base.py` | 222 | 5 | 0 | Aquilia DB Backend -- Base Adapter Interface. |
| `aquilia/db/backends/mysql.py` | 443 | 1 | 0 | Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql. |
| `aquilia/db/backends/oracle.py` | 610 | 1 | 0 | Aquilia DB Backend -- Oracle adapter via python-oracledb. |
| `aquilia/db/backends/postgres.py` | 424 | 1 | 0 | Aquilia DB Backend -- PostgreSQL adapter via asyncpg. |
| `aquilia/db/backends/sqlite.py` | 332 | 1 | 0 | Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module. |
| `aquilia/db/configs.py` | 519 | 5 | 0 | Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs. |
| `aquilia/db/engine.py` | 621 | 1 | 4 | Aquilia Database Engine -- async-first, multi-backend, production-ready. |
