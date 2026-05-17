# Database Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| None detected |  |  |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/db/__init__.py`: Aquilia Database -- async-first database layer.
- `aquilia/db/backends/__init__.py`: Aquilia DB Backends Package -- pluggable database adapters.
- `aquilia/db/backends/base.py`: Aquilia DB Backend -- Base Adapter Interface.
- `aquilia/db/backends/mysql.py`: Aquilia DB Backend -- MySQL/MariaDB adapter via aiomysql.
- `aquilia/db/backends/oracle.py`: Aquilia DB Backend -- Oracle adapter via python-oracledb.
- `aquilia/db/backends/postgres.py`: Aquilia DB Backend -- PostgreSQL adapter via asyncpg.
- `aquilia/db/backends/sqlite.py`: Aquilia DB Backend -- SQLite adapter via native aquilia.sqlite module.
- `aquilia/db/configs.py`: Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs.
- `aquilia/db/engine.py`: Aquilia Database Engine -- async-first, multi-backend, production-ready.
