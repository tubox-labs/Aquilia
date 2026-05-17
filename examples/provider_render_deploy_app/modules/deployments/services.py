from __future__ import annotations

from typing import Any

from aquilia.integrations import RenderIntegration
from aquilia.providers.render.deployer import DeployResult
from aquilia.providers.render.types import RenderDeployConfig, RenderEnvVar, RenderPlan, RenderRegion


class RenderDeploymentPlanner:
    def __init__(self, integration: RenderIntegration | None = None) -> None:
        self.integration = integration or RenderIntegration(
            service_name="provider-render-deploy-app",
            region=RenderRegion.OREGON.value,
            plan=RenderPlan.STARTER.value,
            num_instances=1,
            image="registry.example/aquilia:latest",
        )

    def build_config(self, env: dict[str, str] | None = None) -> RenderDeployConfig:
        data = self.integration.to_dict()
        return RenderDeployConfig(
            service_name=data.get("service_name", "aquilia-app"),
            image=data.get("image", ""),
            plan=RenderPlan(data.get("plan", RenderPlan.STARTER.value)),
            region=data.get("region", RenderRegion.OREGON.value),
            num_instances=int(data.get("num_instances", 1)),
            health_check_path=data.get("health_path", "/_health"),
            env_vars=[RenderEnvVar(key=k, value=v) for k, v in sorted((env or {}).items())],
        )

    def dry_run(self, env: dict[str, str] | None = None) -> dict[str, Any]:
        config = self.build_config(env)
        payload = config.to_service_payload()
        result = DeployResult(success=True, steps_completed=["[dry-run] validated Render service payload"])
        return {
            "success": result.success,
            "steps": result.steps_completed,
            "service_name": config.service_name,
            "payload": payload,
        }
