# SQLite Inventory

The SQLite Inventory example demonstrates Aquilia's native SQLite service, connection
pool lifecycle, parameterized queries, and explicit transactions.

---

## What It Demonstrates

- `SqliteService` wrapping a native SQLite connection pool
- `SqlitePoolConfig` for pool size, timeout, and mode configuration
- Connection pool lifecycle: `startup()`, `shutdown()`
- Parameterized queries via `ConnectionPool.fetch_one()`, `fetch_all()`, `execute()`
- Explicit `IMMEDIATE` transactions via `TransactionContext`
- Atomic inventory reservation with over-reservation protection
- Schema creation on startup with `CREATE TABLE IF NOT EXISTS`

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Includes database configuration |
| `modules/inventory/manifest.py` | Declares `InventoryController` and `InventorySqliteService` |
| `modules/inventory/controllers.py` | HTTP endpoints: add, list, get, reserve |
| `modules/inventory/services.py` | `InventorySqliteService` with pool management and queries |

## Workspace Configuration

```python
workspace = Workspace("sqlite-inventory-app", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8067, reload=True)
    .module(Module("inventory", version="1.0.0").route_prefix("/inventory"))
    .database(url="sqlite:///inventory.db", auto_create=True)
```

Or via typed integration:

```python
from aquilia.integrations import DatabaseIntegration

workspace.integrate(DatabaseIntegration(
    url="sqlite:///inventory.db",
    auto_create=True,
))
```

## SqliteService with Connection Pool

The service manages the full SQLite lifecycle:

```python
from aquilia.sqlite import ConnectionPool, SqlitePoolConfig, SqliteService, TransactionContext

class InventorySqliteService:
    def __init__(self, db_path: str = "inventory.db"):
        config = SqlitePoolConfig(
            database=db_path,
            pool_size=5,
            timeout=30.0,
        )
        self._service = SqliteService(config)

    async def startup(self):
        await self._service.startup()
        await self._create_schema()

    async def shutdown(self):
        await self._service.shutdown()

    async def _create_schema(self):
        await self._service.pool.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price_cents INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
```

### Pool Lifecycle

1. `startup()` — opens the SQLite file, initializes the connection pool
2. Operations — `fetch_one()`, `fetch_all()`, `execute()`
3. `shutdown()` — closes all connections, flushes WAL

## Parameterized Queries

All queries use parameterized placeholders — never interpolate user input:

```python
async def add_item(self, name: str, sku: str, quantity: int, price_cents: int) -> dict:
    row = await self._service.pool.fetch_one(
        "INSERT INTO inventory (name, sku, quantity, price_cents) VALUES (:name, :sku, :quantity, :price_cents) RETURNING id, name, sku, quantity, price_cents, created_at",
        {"name": name, "sku": sku, "quantity": quantity, "price_cents": price_cents},
    )
    return dict(row)

async def list_items(self, limit: int = 50, offset: int = 0) -> list[dict]:
    rows = await self._service.pool.fetch_all(
        "SELECT * FROM inventory ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
        {"limit": limit, "offset": offset},
    )
    return [dict(row) for row in rows]

async def get_item(self, sku: str) -> dict | None:
    row = await self._service.pool.fetch_one(
        "SELECT * FROM inventory WHERE sku = :sku",
        {"sku": sku},
    )
    return dict(row) if row else None
```

## Transactional Operations

Reservation uses an explicit `IMMEDIATE` transaction for atomicity:

```python
async def reserve(self, sku: str, quantity: int) -> dict:
    async with TransactionContext(self._service.pool.writer, mode="IMMEDIATE") as tx:
        item = await tx.fetch_one(
            "SELECT * FROM inventory WHERE sku = :sku",
            {"sku": sku},
        )
        if item is None:
            raise NotFoundFault(detail=f"Item {sku!r} not found")

        current_qty = item["quantity"]
        if current_qty < quantity:
            raise ConflictFault(detail=f"Insufficient inventory: have {current_qty}, requested {quantity}")

        await tx.execute(
            "UPDATE inventory SET quantity = quantity - :quantity WHERE sku = :sku",
            {"quantity": quantity, "sku": sku},
        )
        return {"reserved": quantity, "sku": sku, "remaining": current_qty - quantity}
```

Key transaction patterns:

- `TransactionContext(pool.writer, mode="IMMEDIATE")` begins a write transaction
- `mode="IMMEDIATE"` prevents `SQLITE_BUSY` errors by acquiring the write lock early
- The transaction is committed on successful exit or rolled back on exception
- `tx.fetch_one()` and `tx.execute()` operate within the transaction

## Connection Pool Methods

| Method | Purpose |
| ------ | ------- |
| `pool.fetch_one(sql, params)` | Execute a query, return a single row or `None` |
| `pool.fetch_all(sql, params)` | Execute a query, return a list of rows |
| `pool.execute(sql, params)` | Execute a statement, return row count |
| `pool.writer` | The dedicated writer connection for transactions |

## Running

```bash
cd examples/sqlite_inventory_app
python -m uvicorn runtime:app --reload --port 8067
```

```bash
# Add an item
curl -X POST http://127.0.0.1:8067/inventory/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","sku":"WDG-001","quantity":100,"price_cents":1500}'

# List all items
curl http://127.0.0.1:8067/inventory/items

# Get a specific item
curl http://127.0.0.1:8067/inventory/items/WDG-001

# Reserve inventory (atomic)
curl -X POST http://127.0.0.1:8067/inventory/items/WDG-001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 5}'

# Attempt over-reservation (fails with conflict)
curl -X POST http://127.0.0.1:8067/inventory/items/WDG-001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 999}'

# Run tests
python -m pytest examples/sqlite_inventory_app -q
```

## What You'll Learn

- How to configure and manage `SqliteService` with `SqlitePoolConfig`
- How to handle the SQLite connection pool lifecycle (`startup()`/`shutdown()`)
- How to write parameterized queries to prevent SQL injection
- How to use `TransactionContext` for atomic operations
- How to use `IMMEDIATE` transactions for safe concurrent writes
- How to structure service methods around a native SQLite connection pool