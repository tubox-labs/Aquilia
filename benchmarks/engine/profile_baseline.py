"""Baseline profiling harness for the Aquilia Core Engine audit (Phase 2).

Measures the real framework hot paths with no engine involvement:
  * route matching (static / dynamic / miss)
  * DI resolution (cached / uncached / request-scope creation)
  * request-scope container creation (copy-on-write cost)
  * metadata extraction

Run:  python benchmarks/engine/profile_baseline.py [--routes N] [--providers N]

Methodology: each measurement is a timeit loop with an inner repetition count
chosen so a single sample runs >=50ms, repeated `REPEAT` times; we report the
minimum (least noise) as ns/op. Allocation counts come from tracemalloc deltas
over a fixed operation count.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import statistics
import sys
import timeit
import tracemalloc
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 7


def _bench(stmt, *, setup=lambda: None, target_s: float = 0.05) -> float:
    """Return ns/op for `stmt`, auto-scaling the inner loop."""
    setup()
    n = 1
    while True:
        t = timeit.timeit(stmt, number=n)
        if t >= target_s:
            break
        n = max(n * 2, int(n * target_s / max(t, 1e-9)) + 1)
        if n > 50_000_000:
            break
    samples = [timeit.timeit(stmt, number=n) for _ in range(REPEAT)]
    return min(samples) / n * 1e9


def _alloc_delta(fn, iterations: int = 2000) -> tuple[float, float]:
    """Return (bytes/op, blocks/op) allocated by `fn`."""
    gc.collect()
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    for _ in range(iterations):
        fn()
    after = tracemalloc.take_snapshot()
    tracemalloc.stop()
    stats = after.compare_to(before, "filename")
    total_bytes = sum(s.size_diff for s in stats)
    total_blocks = sum(s.count_diff for s in stats)
    return total_bytes / iterations, total_blocks / iterations


# ---------------------------------------------------------------------------
# Fixtures built from the REAL framework classes
# ---------------------------------------------------------------------------


def build_router(n_static: int, n_dynamic: int):
    """Build a real ControllerRouter with n routes via the real compiler."""
    from aquilia.controller.base import Controller
    from aquilia.controller.compiler import ControllerCompiler
    from aquilia.controller.decorators import GET
    from aquilia.controller.router import ControllerRouter

    ns: dict[str, Any] = {"prefix": "/api", "tags": ["bench"]}

    for i in range(n_static):

        async def handler(self, ctx, _i=i):
            return {"i": _i}

        handler.__name__ = f"static_{i}"
        ns[f"static_{i}"] = GET(f"/static/res{i}/list")(handler)

    for i in range(n_dynamic):

        async def dhandler(self, ctx, item_id: int = 0, _i=i):
            return {"i": _i, "id": item_id}

        dhandler.__name__ = f"dyn_{i}"
        ns[f"dyn_{i}"] = GET(f"/dyn/res{i}/{{item_id}}")(dhandler)

    ctrl = type("BenchController", (Controller,), ns)

    compiler = ControllerCompiler()
    compiled = compiler.compile_controller(ctrl)
    router = ControllerRouter()
    router.add_controller(compiled)
    router.initialize()
    return router, n_static, n_dynamic


def build_container(n_providers: int):
    """Build a real app Container with n class providers."""
    from aquilia.di import Container
    from aquilia.di.providers import ClassProvider

    container = Container(scope="app")
    types_ = []
    for i in range(n_providers):
        cls = type(f"Svc{i}", (), {"__init__": lambda self: None})
        cls.__module__ = "bench.services"
        types_.append(cls)
        container.register(ClassProvider(cls, scope="app"))
    return container, types_


def build_chained_container(depth: int):
    """Container whose services form a dependency chain of `depth` links."""
    from aquilia.di import Container
    from aquilia.di.providers import ClassProvider

    container = Container(scope="app")
    prev = None
    created = []
    for i in range(depth):
        if prev is None:

            def init(self):
                pass

            ann: dict[str, Any] = {}
        else:

            def init(self, dep=None):
                self.dep = dep

            ann = {"dep": prev}
        cls = type(f"Chain{i}", (), {"__init__": init, "__annotations__": {}})
        cls.__module__ = "bench.chain"
        if ann:
            cls.__init__.__annotations__ = ann
        container.register(ClassProvider(cls, scope="app"))
        created.append(cls)
        prev = cls
    return container, created


def make_scope(scope_env: str = "http"):
    return {
        "type": "http",
        "method": "GET",
        "path": "/api/static/res0/list",
        "raw_path": b"/api/static/res0/list",
        "query_string": b"limit=10",
        "headers": [(b"host", b"localhost"), (b"accept", b"application/json")],
        "client": ("127.0.0.1", 5000),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
        "http_version": "1.1",
        "root_path": "",
    }


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


def measure_routing(results: dict, n_static: int, n_dynamic: int):
    router, ns, nd = build_router(n_static, n_dynamic)

    static_path = f"/api/static/res{ns - 1}/list"
    dyn_path = f"/api/dyn/res{nd - 1}/12345"
    miss_path = "/api/nope/not/here"

    results["route_match_static_ns"] = _bench(lambda: router.match_sync(static_path, "GET"))
    results["route_match_dynamic_ns"] = _bench(lambda: router.match_sync(dyn_path, "GET"))
    results["route_match_miss_ns"] = _bench(lambda: router.match_sync(miss_path, "GET"))
    results["route_allowed_methods_ns"] = _bench(lambda: router.get_allowed_methods(miss_path))

    b, blk = _alloc_delta(lambda: router.match_sync(dyn_path, "GET"))
    results["route_match_dynamic_bytes"] = b
    results["route_match_dynamic_blocks"] = blk
    b, blk = _alloc_delta(lambda: router.match_sync(static_path, "GET"))
    results["route_match_static_bytes"] = b
    results["route_match_static_blocks"] = blk

    # registration / compile cost
    def _reg():
        build_router(n_static, n_dynamic)

    t = timeit.timeit(_reg, number=3) / 3
    results["route_build_total_s"] = t
    results["route_build_per_route_us"] = t / (ns + nd) * 1e6
    results["n_static"] = ns
    results["n_dynamic"] = nd

    # isolate _version_matches (the per-candidate import)
    routes = router.get_routes_full()
    r0 = routes[0]
    results["version_matches_ns"] = _bench(lambda: router._version_matches(r0, None))
    return router


def _abench(coro_factory, *, target_s: float = 0.05) -> float:
    """ns/op for an awaitable, measured INSIDE one event loop run.

    `loop.run_until_complete` costs ~25µs on its own, which would swamp a
    sub-microsecond DI resolve. So we drive N awaits inside a single coroutine
    and subtract nothing but the loop entry (amortised over N).
    """
    loop = asyncio.new_event_loop()
    try:

        async def _run(n: int) -> float:
            import time

            t0 = time.perf_counter()
            for _ in range(n):
                await coro_factory()
            return time.perf_counter() - t0

        n = 64
        while True:
            t = loop.run_until_complete(_run(n))
            if t >= target_s:
                break
            n = max(n * 2, int(n * target_s / max(t, 1e-9)) + 1)
            if n > 20_000_000:
                break
        samples = [loop.run_until_complete(_run(n)) for _ in range(REPEAT)]
        return min(samples) / n * 1e9
    finally:
        loop.close()


def measure_di(results: dict, n_providers: int):
    container, types_ = build_container(n_providers)
    loop = asyncio.new_event_loop()

    target = types_[n_providers // 2]
    key = f"{target.__module__}.{target.__qualname__}"

    # Warm the cache first
    loop.run_until_complete(container.resolve_async(target))

    results["di_resolve_cached_ns"] = _abench(lambda: container.resolve_async(target))

    # Uncached: evict the cache key each iteration so we hit the miss path.
    async def _uncached():
        container._cache.pop(key, None)
        return await container.resolve_async(target)

    results["di_resolve_uncached_ns"] = _abench(_uncached)

    # Baseline: cost of awaiting a trivial coroutine (subtract to isolate DI work)
    async def _noop():
        return None

    results["await_noop_ns"] = _abench(_noop)

    # request scope creation (the per-request COW path)
    results["di_request_scope_ns"] = _bench(container.create_request_scope)
    b, blk = _alloc_delta(container.create_request_scope)
    results["di_request_scope_bytes"] = b
    results["di_request_scope_blocks"] = blk

    # register_instance on a request scope == what ASGI does per request
    from aquilia.request import Request

    scope = make_scope()

    async def _per_request_di():
        child = container.create_request_scope()
        req = Request(scope, None)
        await child.register_instance(Request, req, scope="request")

    results["di_per_request_register_ns"] = _abench(_per_request_di)

    def _sync_per_request():
        child = container.create_request_scope()
        req = Request(scope, None)
        loop.run_until_complete(child.register_instance(Request, req, scope="request"))

    b, blk = _alloc_delta(_sync_per_request, iterations=1000)
    results["di_per_request_register_bytes"] = b
    results["di_per_request_register_blocks"] = blk

    # token/key helpers
    results["di_token_to_key_ns"] = _bench(lambda: container._token_to_key(target))
    results["di_unwrap_token_ns"] = _bench(lambda: container._unwrap_token(target))
    results["di_lookup_provider_ns"] = _bench(lambda: container._lookup_provider(key, None))

    # graph build + cycle detection
    chained, _ = build_chained_container(64)

    def _graph():
        from aquilia.di.graph import DependencyGraph

        g = DependencyGraph()
        for i, p in enumerate(chained._providers.values()):
            g.add_provider(p, [])
        g.detect_cycles()

    results["di_graph_detect_cycles_64_us"] = _bench(_graph) / 1000.0
    results["n_providers"] = n_providers
    loop.close()


def measure_request(results: dict):
    from aquilia.request import Request

    scope = make_scope()
    results["request_construct_ns"] = _bench(lambda: Request(scope, None))
    b, blk = _alloc_delta(lambda: Request(scope, None))
    results["request_construct_bytes"] = b
    results["request_construct_blocks"] = blk

    req = Request(scope, None)
    results["request_headers_ns"] = _bench(lambda: req.header("accept"))

    from aquilia.controller.base import RequestCtx, _ctx_pool

    results["ctx_pool_acquire_release_ns"] = _bench(
        lambda: _ctx_pool.release(_ctx_pool.acquire(request=req, container=None))
    )
    results["ctx_direct_construct_ns"] = _bench(lambda: RequestCtx(request=req, container=None))
    b, blk = _alloc_delta(lambda: _ctx_pool.release(_ctx_pool.acquire(request=req, container=None)))
    results["ctx_pool_bytes"] = b
    results["ctx_pool_blocks"] = blk


def measure_metadata(results: dict):
    from aquilia.controller.base import Controller
    from aquilia.controller.decorators import GET
    from aquilia.controller.metadata import extract_controller_metadata

    async def h(self, ctx, item_id: int, q: str = "x"):
        return {}

    ctrl = type(
        "MetaCtl",
        (Controller,),
        {"prefix": "/m", "get_one": GET("/one/{item_id}")(h)},
    )
    results["metadata_extract_us"] = _bench(lambda: extract_controller_metadata(ctrl, "bench:MetaCtl")) / 1000.0

    # Facet rebuild per request (di/core._resolve_extracted_parameter_sync path)
    from aquilia.contracts.annotations import _build_facet_from_annotation
    from aquilia.contracts.facets import UNSET

    results["facet_build_ns"] = _bench(
        lambda: _build_facet_from_annotation(name="q", annotation=int, field_spec=None, class_default=UNSET)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", type=int, default=100, help="static routes (dynamic = routes//2)")
    ap.add_argument("--providers", type=int, default=50)
    ap.add_argument("--json", type=str, default="")
    args = ap.parse_args()

    results: dict[str, Any] = {}
    print("== routing ==", flush=True)
    measure_routing(results, args.routes, max(args.routes // 2, 1))
    print("== di ==", flush=True)
    measure_di(results, args.providers)
    print("== request ==", flush=True)
    measure_request(results)
    print("== metadata ==", flush=True)
    measure_metadata(results)

    width = max(len(k) for k in results)
    for k, v in results.items():
        if isinstance(v, float):
            print(f"{k:<{width}}  {v:>14,.1f}")
        else:
            print(f"{k:<{width}}  {v:>14}")

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
