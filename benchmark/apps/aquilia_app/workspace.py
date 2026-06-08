"""Aquilia benchmark workspace."""

from __future__ import annotations

from aquilia import AquilaConfig, Module, Workspace
from aquilia.integrations import (
    DiIntegration,
    FaultHandlingIntegration,
    MiddlewareChain,
    RoutingIntegration,
    StaticFilesIntegration,
)


class BenchEnv(AquilaConfig):
    env = "prod"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8100
        workers = 1
        reload = False


middleware_chain = (
    MiddlewareChain()
    .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=False)
    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
    .use("benchmark.apps.aquilia_app.middleware.PathNoopMiddleware", priority=20, layer_id=1)
    .use("benchmark.apps.aquilia_app.middleware.PathNoopMiddleware", priority=21, layer_id=2)
    .use("benchmark.apps.aquilia_app.middleware.PathNoopMiddleware", priority=22, layer_id=3)
    .use("benchmark.apps.aquilia_app.middleware.PathNoopMiddleware", priority=23, layer_id=4)
    .use("benchmark.apps.aquilia_app.middleware.PathNoopMiddleware", priority=24, layer_id=5)
)


workspace = (
    Workspace(
        name="aquilia-benchmark",
        version="1.0.0",
        description="Benchmark app for framework comparison",
    )
    .env_config(BenchEnv)
    .middleware(middleware_chain)
    .module(
        Module("bench", version="1.0.0", description="Benchmark module")
        .route_prefix("/")
        .tags("benchmark")
    )
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(
        StaticFilesIntegration(
            directories={"/static": "static"},
            cache_max_age=0,
            etag=False,
            gzip=False,
            brotli=False,
            memory_cache=False,
        )
    )
)

__all__ = ["workspace"]
