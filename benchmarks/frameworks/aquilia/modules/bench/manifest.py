from __future__ import annotations

from aquilia import AppManifest

manifest = AppManifest(
    name="bench",
    version="1.0.0",
    description="Aquilia benchmark module",
    controllers=[
        "benchmarks.frameworks.aquilia.modules.bench.controllers:BenchmarkController",
    ],
    socket_controllers=[
        "benchmarks.frameworks.aquilia.modules.bench.sockets:BenchmarkSocket",
    ],
    services=[
        "benchmarks.frameworks.aquilia.modules.bench.services:LeafService",
        "benchmarks.frameworks.aquilia.modules.bench.services:MidService",
        "benchmarks.frameworks.aquilia.modules.bench.services:TopService",
        "benchmarks.frameworks.aquilia.modules.bench.services:AquiliaDatabaseProvider",
    ],
    auto_discover=False,
)

__all__ = ["manifest"]
