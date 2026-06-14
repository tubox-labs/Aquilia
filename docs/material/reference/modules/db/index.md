# DB Module

> `aquilia.db` — Async database abstraction layer

The DB module provides an async, backend-agnostic database abstraction with support for SQLite, PostgreSQL, MySQL, and Oracle — each with their own optimised connection pool and query execution.

## When to Use

Use the DB module when you need:

- Async database connections for the ORM
- Raw SQL execution with parameterised queries
- Connection pooling and lifecycle management
- Backend-specific features (PostgreSQL asyncpg, MySQL aiomysql, etc.)

## Key Classes

| Class | Purpose |
|---|---|
| `AquiliaDatabase` | Main async database client |
| `DatabaseError` | Base database exception |

## Backends

| Backend | Driver | Config |
|---|---|---|
| SQLite | `aiosqlite` | `sqlite:///path/to/db.sqlite3` |
| PostgreSQL | `asyncpg` | `postgresql://user:pass@host:5432/db` |
| MySQL | `aiomysql` | `mysql://user:pass@host:3306/db` |
| Oracle | `oracledb` | `oracle://user:pass@host:1521/db` |

## Quick Example

```python
from aquilia.db import AquiliaDatabase, configure_database

# Configure
db = configure_database("sqlite:///app.db")

# Execute
result = await db.execute("SELECT 1")
rows = await db.fetchall("SELECT * FROM users WHERE active = ?", True)
row = await db.fetchone("SELECT * FROM users WHERE id = ?", user_id)

# Transaction
async with db.transaction():
    await db.execute("INSERT INTO orders (...) VALUES (...)")
    await db.execute("UPDATE inventory SET count = count - 1 WHERE ...")
```

## Import Path

```python
from aquilia.db import (
    AquiliaDatabase,
    DatabaseError,
    configure_database,
    get_database,
    set_database,
)
```

## Related Modules

- [models](../models/index.md) — ORM layer built on top of this module
- [sqlite](../sqlite/index.md) — Native SQLite operations
- [integrations](../integrations/index.md) — `DatabaseIntegration` config builder