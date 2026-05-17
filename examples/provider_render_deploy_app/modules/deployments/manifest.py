from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="deployments",
    version="1.0.0",
    description="Deployment planning module using RenderIntegration and Render provider dataclasses without network calls.",
    controllers=["modules.deployments.controllers:DeploymentsController"],
    services=["modules.deployments.services:RenderDeploymentPlanner"],
    exports=["modules.deployments.services:RenderDeploymentPlanner"],
    tags=["provider", "render", "deploy"],
)
