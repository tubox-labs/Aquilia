from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RoutingIntegration

workspace = (
    Workspace("jobs-starter", version="1.0.0", description="Background job starter application")
    .runtime(mode="dev", port=8040, reload=True)
    .tasks(num_workers=2, backend="memory", scheduler_tick=10.0)
    .module(Module("jobs", version="1.0.0").route_prefix("/jobs").tags("tasks", "background"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
)
