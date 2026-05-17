import pytest

from examples.sqlite_inventory_app.modules.inventory.services import InventorySqliteService


@pytest.mark.asyncio
async def test_sqlite_inventory_upsert_and_reserve(tmp_path):
    service = InventorySqliteService(tmp_path / "inventory.db")
    await service.startup()
    created = await service.upsert_item("sku-1", "Desk", 10)
    remaining = await service.reserve("sku-1", 3)
    await service.shutdown()

    assert created["quantity"] == 10
    assert remaining["quantity"] == 7


@pytest.mark.asyncio
async def test_sqlite_inventory_rejects_over_reservation(tmp_path):
    service = InventorySqliteService(tmp_path / "inventory.db")
    await service.startup()
    await service.upsert_item("sku-1", "Desk", 1)
    with pytest.raises(ValueError):
        await service.reserve("sku-1", 2)
    await service.shutdown()
