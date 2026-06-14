# SQLite Module

> `aquilia.sqlite` — Native async SQLite operations

The SQLite module provides native, zero-dependency async SQLite operations with connection pooling, optimized query execution, and configuration management.

## When to Use

Use the SQLite module when you need:

- Direct SQLite operations without the full ORM
- Connection pooling for concurrent access
- Native async SQLite for development/testing
- Fine-grained control over SQLite configuration

## Key Classes

| Class | Purpose |
|---|---|
| `SqliteService` | Main async SQLite service |
| `ConnectionPool` | Thread-safe connection pool |
| `SqlitePoolConfig` | Pool size and timeout configuration |

## Quick Example

```python
from aquilia.sqlite import SqliteService, SqlitePoolConfig

config = SqlitePoolConfig(
    database="app.db",
    pool_size=5,
    timeout=30,
)
sqlite = SqliteService(config)

# Execute queries
await sqlite.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
await sqlite.execute("INSERT INTO users (name) VALUES (?)", "Alice")

# Fetch results
rows = await sqlite.fetchall("SELECT * FROM users")
row = await sqlite.fetchone("SELECT * FROM users WHERE id = ?", 1)

# Transaction
async with sqlite.transaction():
    await sqlite.execute("INSERT INTO users (name) VALUES (?)", "Bob")
    await sqlite.execute("INSERT INTO users (name) VALUES (?)", "Charlie")
```

## Import Path

```python
from aquilia.sqlite import SqliteService, ConnectionPool, SqlitePoolConfig
```

## Related Modules

- [db](../db/index.md) — Database abstraction with SQLite backend
- [models](../models/index.md) — ORM uses SQLite for development
- [filesystem](../filesystem/index.md) — File operations for SQLite databases