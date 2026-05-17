# Db Architecture

Async database engine facade, typed database configs, adapters for SQLite/Postgres/MySQL/Oracle, and schema introspection helpers.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`db` has 9 Python files, 15 public classes, 4 public module-level functions, and 16 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 8 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.base` | 5 |
| `..faults.domains` | 2 |
| `.configs` | 2 |
| `..di.decorators` | 1 |
| `.backends` | 1 |
| `.backends.base` | 1 |
| `.engine` | 1 |
| `.mysql` | 1 |
| `.oracle` | 1 |
| `.postgres` | 1 |
| `.sqlite` | 1 |
| `aquilia.sqlite` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 7 |
| `typing` | 7 |
| `collections` | 6 |
| `logging` | 6 |
| `contextlib` | 5 |
| `re` | 5 |
| `asyncio` | 2 |
| `dataclasses` | 2 |
| `abc` | 1 |
| `time` | 1 |
| `urllib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `AdapterCapabilities` | `aquilia/db/backends/base.py` | Describes what a specific backend supports. |
| `DatabaseAdapter` | `aquilia/db/backends/base.py` | Abstract database adapter interface. |
| `MySQLAdapter` | `aquilia/db/backends/mysql.py` | MySQL / MariaDB adapter using aiomysql with connection pooling. |
| `OracleAdapter` | `aquilia/db/backends/oracle.py` | Oracle adapter using python-oracledb (async mode). |
| `PostgresAdapter` | `aquilia/db/backends/postgres.py` | PostgreSQL adapter using asyncpg with connection pooling. |
| `SQLiteAdapter` | `aquilia/db/backends/sqlite.py` | SQLite adapter using the native ``aquilia.sqlite`` connection pool. |
| `DatabaseConfig` | `aquilia/db/configs.py` | Base database configuration. |
| `SqliteConfig` | `aquilia/db/configs.py` | SQLite database configuration. |
| `PostgresConfig` | `aquilia/db/configs.py` | PostgreSQL database configuration. |
| `MysqlConfig` | `aquilia/db/configs.py` | MySQL / MariaDB database configuration. |
| `OracleConfig` | `aquilia/db/configs.py` | Oracle database configuration. |

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.
