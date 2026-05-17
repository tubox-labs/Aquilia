from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("cache-http-edge-app", version="1.0.0", description="Cache-aside HTTP gateway")
    .runtime(mode="dev", host="127.0.0.1", port=8062, reload=True)
    .module(Module("edge", version="1.0.0").route_prefix("/edge").tags("cache", "http"))
    .integrate(Integration.cache(backend="memory", default_ttl=120, max_size=1000, namespace="edge"))
    .integrate(Integration.di(auto_wire=True))
    .integrate(Integration.routing(strict_matching=True))
)
