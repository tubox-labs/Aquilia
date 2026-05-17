import pytest

from examples.rest_api_blueprint.modules.catalog.blueprints import ProductCreateBlueprint
from examples.rest_api_blueprint.modules.catalog.services import CatalogService


@pytest.mark.asyncio
async def test_create_blueprint_and_service_roundtrip():
    blueprint = ProductCreateBlueprint(
        data={"sku": "aq-test", "name": "Test Product", "price_cents": 1000, "tags": ["test"]}
    )
    assert await blueprint.is_sealed_async() is True

    service = CatalogService()
    created = await service.create_product(blueprint.validated_data)

    assert created["sku"] == "AQ-TEST"
    assert created["price_cents"] == 1000
