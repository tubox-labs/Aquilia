from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("project-tracker", version="1.0.0", description="CRUD starter application")
    .runtime(mode="dev", port=8010, reload=True)
    .database(url="sqlite:///runtime/projects.db", auto_create=True, auto_migrate=False)
    .module(Module("projects", version="1.0.0").route_prefix("/projects").tags("crud", "projects"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)
