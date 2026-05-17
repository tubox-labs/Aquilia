# Database Documentation

This directory is the professional documentation set for `db`. It is implementation-driven and aligned with the current source files under `aquilia/db`.

## What This Covers

The async database adapter facade for SQLite, PostgreSQL, MySQL, and Oracle configuration and connection handling.

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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 9
- Public classes: 15
- Configuration or dataclass-like types: 9
- Public functions: 4
- Constants detected: 8

## Fast Start

```python
from aquilia.db import DatabaseConnectionFault, QueryFault, SchemaFault, AdapterCapabilities, DatabaseAdapter, MySQLAdapter

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
