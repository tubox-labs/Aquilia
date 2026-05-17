import pytest

from examples.mlops_model_registry_app.modules.mlopsdemo.services import MLOpsRegistryService


@pytest.mark.asyncio
async def test_mlops_registry_prediction_and_rollout():
    service = MLOpsRegistryService()
    entry = await service.register_model("v1")
    prediction = await service.predict_locally("I love this")
    rollout = await service.start_canary()

    assert entry["name"] == "sentiment"
    assert prediction["label"] == "positive"
    assert rollout["percentage"] == 50


def test_plugin_inventory_includes_registered_plugin():
    service = MLOpsRegistryService()
    assert "audit-plugin" in service.plugin_inventory()
