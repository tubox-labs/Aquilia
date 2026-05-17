from __future__ import annotations

from typing import Any

from aquilia.mlops import AquiliaModel
from aquilia.mlops._types import RolloutConfig
from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.plugins.host import PluginHost
from aquilia.mlops.release.rollout import RolloutEngine


class SentimentModel(AquiliaModel):
    async def predict(self, inputs: dict[str, Any]) -> dict[str, Any]:
        text = inputs.get("text", "")
        score = 0.9 if "love" in text.lower() else 0.2
        return {"label": "positive" if score >= 0.5 else "negative", "score": score}


class AuditPlugin:
    name = "audit-plugin"
    version = "1.0.0"

    def on_prediction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"audited": True, "model": payload.get("model")}


class MLOpsRegistryService:
    def __init__(self) -> None:
        self.registry = ModelRegistry()
        self.rollouts = RolloutEngine()
        self.plugins = PluginHost()
        self.plugins.register(AuditPlugin())

    async def register_model(self, version: str = "v1") -> dict[str, Any]:
        entry = await self.registry.register(
            name="sentiment",
            version=version,
            model_class=SentimentModel,
            config={"device": "cpu", "batch_size": 4},
            tags=["nlp", "example"],
        )
        return entry.to_dict()

    async def predict_locally(self, text: str) -> dict[str, Any]:
        model = SentimentModel()
        outputs = await model.postprocess(await model.predict(await model.preprocess({"text": text})))
        outputs["health"] = await model.health()
        return outputs

    async def start_canary(self) -> dict[str, Any]:
        state = await self.rollouts.start(RolloutConfig(from_version="v1", to_version="v2", percentage=10))
        advanced = await self.rollouts.advance(state.id, percentage=50)
        return {"id": advanced.id, "phase": advanced.phase.value, "percentage": advanced.current_percentage}

    def plugin_inventory(self) -> list[str]:
        return [descriptor.name for descriptor in self.plugins.list_plugins()]
