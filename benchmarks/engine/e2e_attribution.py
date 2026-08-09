"""End-to-end request cost attribution — the ROI question for the native engine.

Micro-benchmarks show routing at ~0.8µs and DI at ~1.3µs. Those numbers only
matter in proportion to a whole request. This harness drives a REAL request
through the REAL ASGIAdapter (router + DI + middleware + controller engine +
response) and attributes the total.

If routing+DI are a small fraction of end-to-end, a native router/DI engine
cannot deliver a large end-to-end win, and the architecture must target the
dominant cost instead. This file exists to make that call on evidence.

Run: python benchmarks/engine/e2e_attribution.py
"""

from __future__ import annotations

import asyncio
import cProfile
import io
import pstats
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 5


def build_app(n_routes: int = 50):
    """Build a minimal but REAL Aquilia stack: compiler → router → engine → ASGI."""
    from aquilia.asgi import ASGIAdapter
    from aquilia.controller.base import Controller
    from aquilia.controller.compiler import ControllerCompiler
    from aquilia.controller.decorators import GET
    from aquilia.controller.engine import ControllerEngine
    from aquilia.controller.factory import ControllerFactory
    from aquilia.controller.router import ControllerRouter
    from aquilia.di import Container
    from aquilia.middleware.stack import MiddlewareStack

    ns = {"prefix": "/api", "tags": ["bench"]}

    async def hello(self, ctx):
        return {"ok": True}

    hello.__name__ = "hello"
    ns["hello"] = GET("/hello")(hello)

    async def item(self, ctx, item_id: int = 0):
        return {"id": item_id}

    item.__name__ = "item"
    ns["item"] = GET("/items/{item_id}")(item)

    for i in range(n_routes):

        async def filler(self, ctx, _i=i):
            return {"i": _i}

        filler.__name__ = f"filler_{i}"
        ns[f"filler_{i}"] = GET(f"/filler/res{i}/list")(filler)

    ctrl = type("BenchController", (Controller,), ns)

    compiler = ControllerCompiler()
    compiled = compiler.compile_controller(ctrl)
    router = ControllerRouter()
    router.add_controller(compiled)
    router.initialize()

    app_container = Container(scope="app")
    factory = ControllerFactory()
    engine = ControllerEngine(factory=factory, enable_lifecycle=False)
    stack = MiddlewareStack()

    adapter = ASGIAdapter(
        controller_router=router,
        controller_engine=engine,
        middleware_stack=stack,
        server=None,
    )
    adapter._default_container = app_container
    return adapter, router, app_container


def make_scope(path="/api/hello", method="GET"):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"host", b"localhost"), (b"accept", b"application/json")],
        "client": ("127.0.0.1", 5000),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
        "http_version": "1.1",
        "root_path": "",
    }


async def drive(adapter, scope, n: int) -> float:
    """Drive n full requests through the adapter; return total seconds."""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent = []

    async def send(msg):
        sent.append(msg)

    t0 = time.perf_counter()
    for _ in range(n):
        sent.clear()
        await adapter(scope, receive, send)
    return time.perf_counter() - t0


def measure_e2e(adapter, path: str, label: str) -> float:
    loop = asyncio.new_event_loop()
    scope = make_scope(path)
    try:
        loop.run_until_complete(drive(adapter, scope, 50))  # warm
        n = 2000
        samples = [loop.run_until_complete(drive(adapter, scope, n)) for _ in range(REPEAT)]
        per = min(samples) / n * 1e6
        print(f"  {label:<44} {per:>10,.2f} us/req  ({1e6 / per:>9,.0f} req/s)")
        return per
    finally:
        loop.close()


def profile_e2e(adapter, path: str, n: int = 3000):
    """cProfile a batch of requests; print the top cumulative costs."""
    loop = asyncio.new_event_loop()
    scope = make_scope(path)
    try:
        loop.run_until_complete(drive(adapter, scope, 50))
        pr = cProfile.Profile()
        pr.enable()
        loop.run_until_complete(drive(adapter, scope, n))
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(28)
        out = s.getvalue()
        # trim the header noise
        lines = out.splitlines()
        start = next((i for i, ln in enumerate(lines) if "ncalls" in ln), 0)
        print("\n".join(lines[start : start + 30]))
    finally:
        loop.close()


def main():
    print("=" * 78)
    print("END-TO-END REQUEST COST ATTRIBUTION (real ASGIAdapter, no network)")
    print("=" * 78)

    adapter, router, container = build_app(50)

    print("\n-- full request through ASGIAdapter --")
    static_us = measure_e2e(adapter, "/api/hello", "static route, no params")
    dyn_us = measure_e2e(adapter, "/api/items/42", "dynamic route, 1 int param")

    print("\n-- isolated components (from the same stack) --")
    import timeit

    def b(stmt, label):
        n = 1
        while True:
            t = timeit.timeit(stmt, number=n)
            if t >= 0.05:
                break
            n = max(n * 2, int(n * 0.05 / max(t, 1e-9)) + 1)
        v = min(timeit.timeit(stmt, number=n) for _ in range(REPEAT)) / n * 1e6
        print(f"  {label:<44} {v:>10,.2f} us")
        return v

    route_us = b(lambda: router.match_sync("/api/hello", "GET"), "router.match_sync (static)")
    route_dyn_us = b(lambda: router.match_sync("/api/items/42", "GET"), "router.match_sync (dynamic)")
    scope_us = b(container.create_request_scope, "container.create_request_scope")

    from aquilia.request import Request

    sc = make_scope()
    req_us = b(lambda: Request(sc, None), "Request(scope, receive)")

    from aquilia.controller.base import _ctx_pool

    r = Request(sc, None)
    ctx_us = b(lambda: _ctx_pool.release(_ctx_pool.acquire(request=r, container=None)), "ctx pool acquire+release")

    print("\n-- attribution --")
    accounted = route_us + scope_us + req_us + ctx_us
    print(f"  {'routing':<28} {route_us:>8.2f} us  {route_us / static_us * 100:>5.1f}% of request")
    print(f"  {'request-scope container':<28} {scope_us:>8.2f} us  {scope_us / static_us * 100:>5.1f}%")
    print(f"  {'Request object':<28} {req_us:>8.2f} us  {req_us / static_us * 100:>5.1f}%")
    print(f"  {'RequestCtx pool':<28} {ctx_us:>8.2f} us  {ctx_us / static_us * 100:>5.1f}%")
    print(f"  {'-- accounted --':<28} {accounted:>8.2f} us  {accounted / static_us * 100:>5.1f}%")
    print(f"  {'-- rest (engine+mw+resp) --':<28} {static_us - accounted:>8.2f} us  "
          f"{(static_us - accounted) / static_us * 100:>5.1f}%")

    print("\n-- cProfile: where the time actually goes (static route) --")
    profile_e2e(adapter, "/api/hello")

    print("\n-- theoretical ceiling --")
    print(f"  If routing+DI-scope became FREE (0 ns), request drops")
    print(f"  {static_us:.2f} us -> {static_us - route_us - scope_us:.2f} us "
          f"= {(route_us + scope_us) / static_us * 100:.1f}% best-case gain")


if __name__ == "__main__":
    main()
