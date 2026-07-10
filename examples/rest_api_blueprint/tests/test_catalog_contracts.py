import pytest

from examples.rest_api_contract.modules.catalog.contracts import ProductCreateContract
from examples.rest_api_contract.modules.catalog.services import CatalogService


@pytest.mark.asyncio
async def test_create_contract_and_service_roundtrip():
    contract = ProductCreateContract(
        data={"sku": "aq-test", "name": "Test Product", "price_cents": 1000, "tags": ["test"]}
    )
    assert await contract.is_sealed_async() is True

    service = CatalogService()
    created = await service.create_product(contract.validated_data)

    assert created["sku"] == "AQ-TEST"
    assert created["price_cents"] == 1000
