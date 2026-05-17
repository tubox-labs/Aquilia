from aquilia import Integration, Module, Workspace
from aquilia.integrations import VersioningIntegration

workspace = (
    Workspace("versioned-public-api-app", version="1.0.0", description="Header-versioned public API")
    .runtime(mode="dev", host="127.0.0.1", port=8066, reload=True)
    .module(Module("publicapi", version="1.0.0").route_prefix("/public").tags("versioning"))
    .integrate(VersioningIntegration(default_version="1.0", versions=["1.0", "2.0"], strategy="header"))
    .integrate(Integration.di(auto_wire=True))
)
