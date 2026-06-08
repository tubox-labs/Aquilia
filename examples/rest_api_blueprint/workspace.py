from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, FaultHandlingIntegration, RoutingIntegration

workspace = (
    Workspace("catalog-api", version="1.0.0", description="Product catalog REST API starter")
    .runtime(mode="dev", host="127.0.0.1", port=8000, reload=True)
    .module(Module("catalog", version="1.0.0").route_prefix("/catalog").tags("catalog", "rest"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True)
    .telemetry(metrics_enabled=True, logging_enabled=True)
)