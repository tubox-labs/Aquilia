from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, FaultHandlingIntegration, RoutingIntegration
from aquilia.sessions import DEFAULT_USER_POLICY

workspace = (
    Workspace("auth-starter", version="1.0.0", description="Authentication starter application")
    .runtime(mode="dev", port=8020, reload=True)
    .module(Module("accounts", version="1.0.0").route_prefix("/accounts").tags("auth", "users"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .sessions(policies=[DEFAULT_USER_POLICY])
    .security(cors_enabled=True, csrf_protection=False, helmet_enabled=True, rate_limiting=True)
)
