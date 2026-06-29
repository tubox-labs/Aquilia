from aquilia import Module, Workspace
from aquilia.integrations import CacheIntegration, DiIntegration, RoutingIntegration

workspace = (
    Workspace("cache-http-edge-app", version="1.0.0", description="Cache-aside HTTP gateway")
    .runtime(mode="dev", host="127.0.0.1", port=8062, reload=True)
    .module(Module("edge", version="1.0.0").route_prefix("/edge").tags("cache", "http"))
    .integrate(CacheIntegration(backend="memory", default_ttl=120, max_size=1000, namespace="edge"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
)
