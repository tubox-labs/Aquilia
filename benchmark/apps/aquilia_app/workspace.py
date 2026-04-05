"""Aquilia benchmark workspace."""

from __future__ import annotations

from aquilia import Integration, Module, Workspace
from aquilia.config_builders import AquilaConfig


class BenchEnv(AquilaConfig):
    env = "prod"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8100
        workers = 1
        reload = False


middleware_chain = (
    Integration.middleware.chain()
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
    .integrate(Integration.di(auto_wire=True))
    .integrate(Integration.routing(strict_matching=True))
    .integrate(Integration.fault_handling(default_strategy="propagate"))
    .integrate(
        Integration.static_files(
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
