from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("jobs-starter", version="1.0.0", description="Background job starter application")
    .runtime(mode="dev", port=8040, reload=True)
    .tasks(num_workers=2, backend="memory", scheduler_tick=10.0)
    .module(Module("jobs", version="1.0.0").route_prefix("/jobs").tags("tasks", "background"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True))
)
