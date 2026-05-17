# Database Architecture

## Runtime Role

The async database adapter facade for SQLite, PostgreSQL, MySQL, and Oracle configuration and connection handling.

The implementation is split across 9 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/db/__init__.py`: Aquilia Database -- async-first database layer.
- `aquilia/db/backends/__init__.py`: Aquilia DB Backends Package -- pluggable database adapters.
- `aquilia/db/backends/base.py`: Aquilia DB Backend -- Base Adapter Interface.
- `aquilia/db/backends/mysql.py`: Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql.
- `aquilia/db/backends/oracle.py`: Aquilia DB Backend -- Oracle adapter via python-oracledb.
- `aquilia/db/backends/postgres.py`: Aquilia DB Backend -- PostgreSQL adapter via asyncpg.
- `aquilia/db/backends/sqlite.py`: Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module.
- `aquilia/db/configs.py`: Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs.
- `aquilia/db/engine.py`: Aquilia Database Engine -- async-first, multi-backend, production-ready.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 7 |
| `typing` | 7 |
| `collections` | 6 |
| `logging` | 6 |
| `base` | 5 |
| `contextlib` | 5 |
| `re` | 5 |
| `asyncio` | 2 |
| `backends` | 2 |
| `configs` | 2 |
| `dataclasses` | 2 |
| `faults` | 2 |
| `abc` | 1 |
| `aquilia` | 1 |
| `di` | 1 |
| `engine` | 1 |
| `mysql` | 1 |
| `oracle` | 1 |
| `postgres` | 1 |
| `sqlite` | 1 |
| `time` | 1 |
| `urllib` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
