from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, FaultHandlingIntegration, RoutingIntegration

workspace = (
    Workspace("project-tracker", version="1.0.0", description="CRUD starter application")
    .runtime(mode="dev", port=8010, reload=True)
    .database(url="sqlite:///runtime/projects.db", auto_create=True, auto_migrate=False)
    .module(Module("projects", version="1.0.0").route_prefix("/projects").tags("crud", "projects"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)