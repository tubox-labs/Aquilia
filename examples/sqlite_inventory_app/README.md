# SQLite Inventory App

## Purpose

Demonstrates Aquilia's native SQLite service, connection pool lifecycle, parameterized queries, and explicit transactions.

## Architecture

- `workspace.py` includes database configuration.
- `InventorySqliteService` owns `SqliteService` and creates schema on startup.
- `reserve()` uses an `IMMEDIATE` transaction through the pool writer connection.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/sqlite_inventory_app -q
```

## Run

```bash
cd examples/sqlite_inventory_app
python -m uvicorn runtime:app --reload --port 8067
```

## Expected Behavior

Items can be inserted, fetched, and reserved atomically. Over-reservation raises a service error.

## Common Pitfalls

- Call `SqliteService.startup()` before using `.pool`.
- Use parameterized SQL; do not interpolate request values into SQL strings.

## Extension Ideas

Add AMDL model migration examples, stock movement history, read replicas, and admin integration.

## Related APIs

`SqliteService`, `SqlitePoolConfig`, `ConnectionPool.fetch_one`, `ConnectionPool.execute`, `TransactionContext`.
