# Db Documentation

Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers.

## Coverage Snapshot

- Source files: 9
- Source lines: 3266
- Public classes: 15
- Public module functions: 4
- Constants/module flags: 16
- Public exports in `__all__`: 22

## Source Files Read

- `aquilia/db/__init__.py`: Aquilia Database -- async-first database layer.
- `aquilia/db/backends/__init__.py`: Aquilia DB Backends Package -- pluggable database adapters.
- `aquilia/db/backends/base.py`: Aquilia DB Backend -- Base Adapter Interface.
- `aquilia/db/backends/mysql.py`: Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql.
- `aquilia/db/backends/oracle.py`: Aquilia DB Backend -- Oracle adapter via python-oracledb.
- `aquilia/db/backends/postgres.py`: Aquilia DB Backend -- PostgreSQL adapter via asyncpg.
- `aquilia/db/backends/sqlite.py`: Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module.
- `aquilia/db/configs.py`: Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs.
- `aquilia/db/engine.py`: Aquilia Database Engine -- async-first, multi-backend, production-ready.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
