from __future__ import annotations

from pathlib import Path
from typing import Any

from aquilia.sqlite import SqlitePoolConfig, SqliteService


class InventorySqliteService:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db = SqliteService(SqlitePoolConfig(path=str(db_path), pool_min_size=1, pool_size=2))

    async def startup(self) -> None:
        await self.db.startup()
        await self.db.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_items (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    async def shutdown(self) -> None:
        await self.db.shutdown()

    async def upsert_item(self, sku: str, name: str, quantity: int) -> dict[str, Any]:
        await self.db.pool.execute(
            """
            INSERT INTO inventory_items (sku, name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                quantity = excluded.quantity,
                updated_at = CURRENT_TIMESTAMP
            """,
            (sku, name, quantity),
        )
        return await self.get_item(sku)

    async def get_item(self, sku: str) -> dict[str, Any]:
        row = await self.db.pool.fetch_one("SELECT sku, name, quantity FROM inventory_items WHERE sku = ?", (sku,))
        if row is None:
            raise KeyError(sku)
        return {"sku": row["sku"], "name": row["name"], "quantity": row["quantity"]}

    async def reserve(self, sku: str, quantity: int) -> dict[str, Any]:
        async with self.db.pool.acquire(readonly=False) as conn:
            async with conn.transaction(mode="IMMEDIATE"):
                current = await conn.fetch_val("SELECT quantity FROM inventory_items WHERE sku = ?", (sku,))
                if current is None:
                    raise KeyError(sku)
                if current < quantity:
                    raise ValueError("insufficient stock")
                await conn.execute("UPDATE inventory_items SET quantity = quantity - ? WHERE sku = ?", (quantity, sku))
        return await self.get_item(sku)
