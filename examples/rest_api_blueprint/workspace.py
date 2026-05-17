from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("catalog-api", version="1.0.0", description="Product catalog REST API starter")
    .runtime(mode="dev", host="127.0.0.1", port=8000, reload=True)
    .module(Module("catalog", version="1.0.0").route_prefix("/catalog").tags("catalog", "rest"))
    .integrate(Integration.di(auto_wire=True, manifest_validation=True))
    .integrate(Integration.routing(strict_matching=True, compression=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True)
    .telemetry(metrics_enabled=True, logging_enabled=True)
)
