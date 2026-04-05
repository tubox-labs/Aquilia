from aquilia import AppManifest

manifest = AppManifest(
    name="bench",
    version="1.0.0",
    description="Aquilia benchmark module",
    controllers=[
        "modules.bench.controllers:BenchmarkController",
    ],
    socket_controllers=[
        "modules.bench.sockets:BenchmarkSocket",
    ],
    services=[
        "modules.bench.services:LeafService",
        "modules.bench.services:MidService",
        "modules.bench.services:TopService",
    ],
    auto_discover=False,
)

__all__ = ["manifest"]
