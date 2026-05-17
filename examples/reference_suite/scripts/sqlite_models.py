from __future__ import annotations

import tempfile
from pathlib import Path

from aquilia.models import CharField, IntegerField, Model
from aquilia.sqlite import create_pool


class InventoryItem(Model):
    table = "inventory_items"

    sku = CharField(max_length=32, unique=True)
    name = CharField(max_length=120)
    stock = IntegerField(default=0)


async def run() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "inventory.db"
        pool = await create_pool(f"sqlite:///{db_path}")
        try:
            await pool.execute(
                "CREATE TABLE inventory_items (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, name TEXT, stock INTEGER)"
            )
            async with pool.acquire(readonly=False) as conn:
                async with conn.transaction(mode="IMMEDIATE"):
                    await conn.execute(
                        "INSERT INTO inventory_items (sku, name, stock) VALUES (?, ?, ?)",
                        ["AQ-REF", "Reference Item", 12],
                    )
            row = await pool.fetch_one("SELECT sku, stock FROM inventory_items WHERE sku = ?", ["AQ-REF"])
            return {
                "model_table": InventoryItem._table_name,
                "sku": row["sku"],
                "stock": row["stock"],
            }
        finally:
            await pool.close()
