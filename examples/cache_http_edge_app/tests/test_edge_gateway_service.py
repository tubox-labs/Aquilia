import pytest

from examples.cache_http_edge_app.modules.edge.services import EdgeGatewayService


@pytest.mark.asyncio
async def test_cache_aside_uses_origin_once_until_purge():
    service = EdgeGatewayService()
    await service.configure_origin("sku-1", {"sku": "sku-1", "stock": 8})

    first = await service.product_snapshot("sku-1")
    second = await service.product_snapshot("sku-1")
    deleted = await service.purge_product("sku-1")
    third = await service.product_snapshot("sku-1")
    await service.shutdown()

    assert first == second == third
    assert deleted is True
    assert service.origin_hits == 2
