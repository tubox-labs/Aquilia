from aquilia import Module, Workspace
from aquilia.integrations import CorsIntegration, CspIntegration, DiIntegration, RateLimitIntegration

workspace = (
    Workspace("middleware-security-app", version="1.0.0", description="Security middleware policy reference")
    .runtime(mode="dev", host="127.0.0.1", port=8069, reload=True)
    .module(Module("security", version="1.0.0").route_prefix("/security").tags("middleware", "security"))
    .integrate(CorsIntegration(allow_origins=["https://app.example.test"], allow_credentials=True))
    .integrate(CspIntegration(policy={"default-src": ["'self'"], "frame-ancestors": ["'none'"]}))
    .integrate(RateLimitIntegration(limit=60, window=60))
    .integrate(DiIntegration(auto_wire=True))
)
