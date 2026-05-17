# db Module

## Purpose

Database adapter configuration and engine facade. Use this module to configure SQLite, PostgreSQL, MySQL, and Oracle adapters, route framework database operations, and share database handles.

## Source Coverage

- Python files: 9
- Public classes: 15
- Dataclasses: 9
- Enums: 0
- Public functions: 4

## How It Fits In Aquilia

1. Import the package from `aquilia.db` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `DatabaseConfig` | `aquilia/db/configs.py` | Base database configuration. |
| `SqliteConfig` | `aquilia/db/configs.py` | SQLite database configuration. |
| `PostgresConfig` | `aquilia/db/configs.py` | PostgreSQL database configuration. |
| `MysqlConfig` | `aquilia/db/configs.py` | MySQL / MariaDB database configuration. |
| `OracleConfig` | `aquilia/db/configs.py` | Oracle database configuration. |
| `AquiliaDatabase` | `aquilia/db/engine.py` | Async database engine for Aquilia. |
| `AdapterCapabilities` | `aquilia/db/backends/base.py` | Describes what a specific backend supports. |
| `ColumnInfo` | `aquilia/db/backends/base.py` | Introspection result for a single column. |
| `TableInfo` | `aquilia/db/backends/base.py` | Introspection result for a table. |
| `IntrospectionResult` | `aquilia/db/backends/base.py` | Full database introspection result. |
| `DatabaseAdapter` | `aquilia/db/backends/base.py` | Abstract database adapter interface. |
| `MySQLAdapter` | `aquilia/db/backends/mysql.py` | MySQL / MariaDB adapter using aiomysql with connection pooling. |
| `OracleAdapter` | `aquilia/db/backends/oracle.py` | Oracle adapter using python-oracledb (async mode). |
| `PostgresAdapter` | `aquilia/db/backends/postgres.py` | PostgreSQL adapter using asyncpg with connection pooling. |
| `SQLiteAdapter` | `aquilia/db/backends/sqlite.py` | SQLite adapter using the native ``aquilia.sqlite`` connection pool. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `get_database` | `aquilia/db/engine.py` | Get a database instance by alias, or the default. |
| `configure_database` | `aquilia/db/engine.py` | Configure and return a database instance. |
| `set_database` | `aquilia/db/engine.py` | Set an externally-created database as the default or by alias. |
| `get_all_databases` | `aquilia/db/engine.py` | Return all configured database instances. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/db/__init__.py` | Aquilia Database -- async-first database layer. |
| `aquilia/db/backends/__init__.py` | Aquilia DB Backends Package -- pluggable database adapters. |
| `aquilia/db/backends/base.py` | Aquilia DB Backend -- Base Adapter Interface. |
| `aquilia/db/backends/mysql.py` | Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql. |
| `aquilia/db/backends/oracle.py` | Aquilia DB Backend -- Oracle adapter via python-oracledb. |
| `aquilia/db/backends/postgres.py` | Aquilia DB Backend -- PostgreSQL adapter via asyncpg. |
| `aquilia/db/backends/sqlite.py` | Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module. |
| `aquilia/db/configs.py` | Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs. |
| `aquilia/db/engine.py` | Aquilia Database Engine -- async-first, multi-backend, production-ready. |

## Testing Pointers

Search `tests/` for `db` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
