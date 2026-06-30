from __future__ import annotations

import os
from pathlib import Path

from aquilia import AquilaConfig, Module, Workspace
from aquilia.integrations import (
    DiIntegration,
    FaultHandlingIntegration,
    MiddlewareChain,
    RoutingIntegration,
)


class BenchEnv(AquilaConfig):
    env = "prod"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8100
        workers = 1
        reload = False


# Path to the techempower SQLite database relative to this file
DB_FILE = Path(__file__).resolve().parents[2] / "techempower" / "techempower.db"

middleware_chain = (
    MiddlewareChain()
    .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=False)
    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
)

# Dynamically stack middleware layers to benchmark overhead
layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
for i in range(layers_count):
    middleware_chain.use("benchmarks.frameworks.aquilia.middleware.PathNoopMiddleware", priority=20 + i, layer_id=i)

workspace = (
    Workspace(
        name="aquilia-benchmark",
        version="1.0.0",
        description="Aquilia Framework Benchmark App",
    )
    .env_config(BenchEnv)
    .middleware(middleware_chain)
    .module(Module("bench", version="1.0.0", description="Benchmark module").route_prefix("/").tags("benchmark"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .database(url=f"sqlite:///{DB_FILE.resolve()}", auto_connect=True, auto_create=False, auto_migrate=False)
)

__all__ = ["workspace"]
