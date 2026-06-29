from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RenderIntegration

workspace = (
    Workspace("provider-render-deploy-app", version="1.0.0", description="Render provider dry-run deployment planning")
    .runtime(mode="dev", host="127.0.0.1", port=8072, reload=True)
    .module(Module("deployments", version="1.0.0").route_prefix("/deployments").tags("provider", "render"))
    .integrate(
        RenderIntegration(
            service_name="provider-render-deploy-app",
            region="oregon",
            plan="starter",
            num_instances=1,
            image="registry.example/aquilia:latest",
        )
    )
    .integrate(DiIntegration(auto_wire=True))
)
