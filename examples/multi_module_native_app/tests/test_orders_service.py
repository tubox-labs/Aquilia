import pytest

from modules.orders.services import OrdersService


@pytest.mark.asyncio
async def test_create_order():
    service = OrdersService()
    order = await service.create_order(
        {"customer_email": "buyer@example.com", "lines": [{"sku": "AQ-STARTER", "quantity": 1}]}
    )
    assert order["id"].startswith("ord_")
    assert order["status"] == "accepted"
