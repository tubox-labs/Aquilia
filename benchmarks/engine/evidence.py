"""Root-cause isolation for the Phase 2 performance audit.

Each experiment below isolates ONE suspected cost so the audit can attribute
nanoseconds to a specific line of the existing implementation rather than to a
guess. Every number printed here is reproducible on the host machine.

Run: python benchmarks/engine/evidence.py
"""

from __future__ import annotations

import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 7


def bench(stmt, *, target_s: float = 0.05, label: str = "") -> float:
    n = 1
    while True:
        t = timeit.timeit(stmt, number=n)
        if t >= target_s:
            break
        n = max(n * 2, int(n * target_s / max(t, 1e-9)) + 1)
        if n > 50_000_000:
            break
    samples = [timeit.timeit(stmt, number=n) for _ in range(REPEAT)]
    ns = min(samples) / n * 1e9
    if label:
        print(f"  {label:<58} {ns:>10,.1f} ns")
    return ns


def section(title: str):
    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")


# ---------------------------------------------------------------------------
# E1 — the `import` statement inside a hot function
# ---------------------------------------------------------------------------
def e1_import_in_hot_path():
    section("E1  Cost of a module-level `import` executed inside a hot function")
    print("  aquilia/controller/router.py:382-386 runs 2 `from ... import` per call")
    print("  aquilia/di/core.py:1263 runs `from typing import get_args, get_origin`")

    def two_imports():
        from aquilia.versioning.core import VERSION_MISSING as _VM  # noqa: F401
        from aquilia.versioning.core import VERSION_NEUTRAL as _VN  # noqa: F401

    def one_import():
        from aquilia.versioning.core import VERSION_NEUTRAL as _VN  # noqa: F401

    def typing_import():
        from typing import get_args, get_origin  # noqa: F401

    def no_import():
        pass

    base = bench(no_import, label="baseline: empty function body")
    t1 = bench(one_import, label="1x `from aquilia.versioning.core import X`")
    t2 = bench(two_imports, label="2x `from aquilia.versioning.core import X` (router)")
    t3 = bench(typing_import, label="`from typing import get_args, get_origin` (di)")
    print(f"  -> per-import overhead ~= {(t2 - base) / 2:,.0f} ns")
    return {"import_1": t1, "import_2": t2, "import_typing": t3, "baseline": base}


# ---------------------------------------------------------------------------
# E2 — router: what fraction of a "O(1) static match" is the version check
# ---------------------------------------------------------------------------
def e2_router_breakdown():
    section("E2  Router: static O(1) match decomposed")
    from profile_baseline import build_router  # noqa

    router, ns, nd = build_router(100, 50)
    static_path = "/api/static/res99/list"
    norm = static_path
    static_map = router._static_routes["GET"]
    route = static_map[norm][0][0]

    raw_dict = bench(lambda: static_map.get(norm), label="raw dict.get on the static map (theoretical floor)")
    vm = bench(lambda: router._version_matches(route, None), label="_version_matches(route, None)")
    full = bench(lambda: router.match_sync(static_path, "GET"), label="router.match_sync (full static path)")
    print(f"  -> _version_matches is {vm / full * 100:.0f}% of a static match")
    print(f"  -> dict.get is only {raw_dict / full * 100:.1f}% of a static match")

    # dynamic: trie walk
    dyn = "/api/dyn/res49/12345"
    trie = router._tries["GET"]
    walk = bench(lambda: router._trie_match(trie, dyn, None, None), label="_trie_match (dynamic walk incl. version)")
    full_dyn = bench(lambda: router.match_sync(dyn, "GET"), label="router.match_sync (full dynamic path)")
    split = bench(lambda: dyn.strip("/").split("/"), label="path.strip('/').split('/') (per-request alloc)")
    return {
        "dict_get": raw_dict,
        "version_matches": vm,
        "match_static": full,
        "trie_match": walk,
        "match_dynamic": full_dyn,
        "path_split": split,
    }


# ---------------------------------------------------------------------------
# E3 — DI: what a "cached hit" actually costs
# ---------------------------------------------------------------------------
def e3_di_breakdown():
    section("E3  DI: cached resolve decomposed (should be ~1 dict lookup)")
    from profile_baseline import build_container  # noqa

    container, types_ = build_container(50)
    target = types_[25]
    key = f"{target.__module__}.{target.__qualname__}"

    import asyncio

    loop = asyncio.new_event_loop()
    loop.run_until_complete(container.resolve_async(target))  # warm

    cache = container._cache
    raw = bench(lambda: cache.get(key), label="raw dict.get on _cache (theoretical floor)")
    unwrap = bench(lambda: container._unwrap_token(target), label="_unwrap_token(type)  [runs on EVERY resolve]")
    tok = bench(lambda: container._token_to_key(target), label="_token_to_key(type)  [calls _unwrap_token]")

    # decompose _unwrap_token
    from typing import get_origin

    ha = bench(
        lambda: (
            hasattr(target, "_inject_token") or hasattr(target, "_inject_tag") or hasattr(target, "_inject_optional")
        ),
        label="  3x hasattr(_inject_*) on a plain class",
    )
    go = bench(lambda: get_origin(target), label="  get_origin(type)")

    def norm():
        from aquilia.di.providers import _normalize_optional_token

        return _normalize_optional_token(target)

    no = bench(norm, label="  import + _normalize_optional_token(type)")
    print(f"  -> hasattr+get_origin+normalize = {ha + go + no:,.0f} ns of the {unwrap:,.0f} ns _unwrap_token")

    # settings lookup on the miss path
    def settings():
        from aquilia.di.settings import get_di_settings

        return get_di_settings()

    st = bench(settings, label="import + get_di_settings() [miss path, every resolve]")
    loop.close()
    return {"dict_get": raw, "unwrap_token": unwrap, "token_to_key": tok, "get_di_settings": st}


# ---------------------------------------------------------------------------
# E4 — per-request ctx pool: the urandom tax
# ---------------------------------------------------------------------------
def e4_ctx_pool():
    section("E4  RequestCtx pool: acquire() generates a random id every time")
    print("  aquilia/controller/base.py:269-272 — os.urandom(16).hex() per acquire")
    import os

    from aquilia.controller.base import RequestCtx, _ctx_pool
    from aquilia.request import Request
    from profile_baseline import make_scope  # noqa

    req = Request(make_scope(), None)

    ur = bench(lambda: os.urandom(16).hex(), label="os.urandom(16).hex()")
    imp = bench(lambda: __import__("os"), label="`import os` inside acquire()")
    acq = bench(
        lambda: _ctx_pool.release(_ctx_pool.acquire(request=req, container=None)),
        label="_ctx_pool.acquire()+release()",
    )
    direct = bench(lambda: RequestCtx(request=req, container=None), label="RequestCtx(...) direct construction")
    print(f"  -> urandom+import = {ur + imp:,.0f} ns of {acq:,.0f} ns ({(ur + imp) / acq * 100:.0f}%)")
    print(f"  -> pooling is {acq / direct:.1f}x SLOWER than just constructing the object")
    return {"urandom": ur, "import_os": imp, "acquire_release": acq, "direct": direct}


# ---------------------------------------------------------------------------
# E5 — router scaling: does the trie actually scale?
# ---------------------------------------------------------------------------
def e5_router_scaling():
    section("E5  Router scaling: match cost vs route count")
    from profile_baseline import build_router  # noqa

    out = {}
    print(f"  {'routes':>8} {'static ns':>12} {'dynamic ns':>12} {'miss ns':>12} {'build/route us':>16}")
    for n in (10, 100, 500, 2000):
        import time

        t0 = time.perf_counter()
        router, ns_, nd_ = build_router(n, max(n // 2, 1))
        build = (time.perf_counter() - t0) / (ns_ + nd_) * 1e6
        s = bench(lambda: router.match_sync(f"/api/static/res{ns_ - 1}/list", "GET"))
        d = bench(lambda: router.match_sync(f"/api/dyn/res{nd_ - 1}/999", "GET"))
        m = bench(lambda: router.match_sync("/api/zzz/none", "GET"))
        print(f"  {ns_ + nd_:>8} {s:>12,.0f} {d:>12,.0f} {m:>12,.0f} {build:>16,.1f}")
        out[ns_ + nd_] = {"static": s, "dynamic": d, "miss": m, "build_per_route_us": build}
    return out


# ---------------------------------------------------------------------------
# E6 — metadata / facet rebuild
# ---------------------------------------------------------------------------
def e6_metadata():
    section("E6  Metadata & per-request Facet rebuild")
    print("  aquilia/di/core.py:1956 _build_facet_from_annotation runs per request per param")
    from aquilia.contracts.annotations import _build_facet_from_annotation
    from aquilia.contracts.facets import UNSET

    f_int = bench(
        lambda: _build_facet_from_annotation(name="q", annotation=int, field_spec=None, class_default=UNSET),
        label="_build_facet_from_annotation(int)",
    )
    f_str = bench(
        lambda: _build_facet_from_annotation(name="q", annotation=str, field_spec=None, class_default=UNSET),
        label="_build_facet_from_annotation(str)",
    )

    import inspect

    from aquilia.controller.base import Controller
    from aquilia.controller.decorators import GET
    from aquilia.controller.metadata import extract_controller_metadata

    async def h(self, ctx, item_id: int, q: str = "x"):
        return {}

    ctrl = type("MetaCtl", (Controller,), {"prefix": "/m", "get_one": GET("/one/{item_id}")(h)})
    ex = bench(lambda: extract_controller_metadata(ctrl, "bench:MetaCtl"), label="extract_controller_metadata (1 route)")
    sig = bench(lambda: inspect.signature(h), label="inspect.signature(handler)")
    hints = bench(lambda: __import__("typing").get_type_hints(h), label="typing.get_type_hints(handler)")
    return {"facet_int": f_int, "facet_str": f_str, "extract": ex, "signature": sig, "hints": hints}


def main():
    res = {}
    res["e1"] = e1_import_in_hot_path()
    res["e2"] = e2_router_breakdown()
    res["e3"] = e3_di_breakdown()
    res["e4"] = e4_ctx_pool()
    res["e5"] = e5_router_scaling()
    res["e6"] = e6_metadata()

    import json

    out = Path(__file__).parent / "evidence.json"
    out.write_text(json.dumps(res, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
