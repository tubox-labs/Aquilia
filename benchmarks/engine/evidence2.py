"""Evidence part 2 — the costs that cProfile ranked ABOVE routing and DI.

The end-to-end attribution (e2e_attribution.py) showed routing+DI are only
~5.5% of a request. cProfile ranked these higher. This file isolates them.

Run: python benchmarks/engine/evidence2.py
"""

from __future__ import annotations

import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from aquilia.controller.base import RequestCtx  # noqa: E402  (module scope: get_type_hints must resolve it)

REPEAT = 7


# Module-level so their annotations resolve against module globals, exactly as a
# real controller handler's would. Defined here (not nested) because this file
# uses `from __future__ import annotations`, so annotations are strings that
# get_type_hints() must eval against __globals__.
async def _handler1(self, ctx: RequestCtx):
    return {}


async def _handler3(self, ctx: RequestCtx, item_id: int, q: str = "x"):
    return {}


def bench(stmt, *, label: str = "", target_s: float = 0.05) -> float:
    n = 1
    while True:
        t = timeit.timeit(stmt, number=n)
        if t >= target_s:
            break
        n = max(n * 2, int(n * target_s / max(t, 1e-9)) + 1)
        if n > 50_000_000:
            break
    ns = min(timeit.timeit(stmt, number=n) for _ in range(REPEAT)) / n * 1e9
    if label:
        print(f"  {label:<62} {ns:>10,.1f} ns")
    return ns


def section(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# F1 — RequestCtx.__setattr__: the #3 tottime entry (72k calls / 3k requests)
# ---------------------------------------------------------------------------
def f1_setattr():
    section("F1  RequestCtx.__setattr__ — 24 calls per request (72,000 / 3,000)")
    print("  aquilia/controller/base.py:175 overrides __setattr__ with try/except")
    print("  Every pool acquire() sets 8 fields, release() sets 8 more.\n")

    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from profile_baseline import make_scope  # noqa

    req = Request(make_scope(), None)
    ctx = RequestCtx(request=req, container=None)

    # With the custom __setattr__ (as shipped)
    custom = bench(lambda: setattr(ctx, "identity", None), label="ctx.identity = None   (custom __setattr__)")

    # A control class with identical slots but NO __setattr__ override
    class PlainCtx:
        __slots__ = ("request", "identity", "session", "auth", "container", "state", "request_id", "_extra")

        def __init__(self):
            self.request = None
            self.identity = None
            self.session = None
            self.auth = None
            self.container = None
            self.state = None
            self.request_id = None
            self._extra = None

    plain = PlainCtx()
    native = bench(lambda: setattr(plain, "identity", None), label="plain.identity = None (native slot setattr)")
    print(f"  -> custom __setattr__ is {custom / native:.1f}x slower ({custom - native:,.0f} ns overhead per set)")
    print(f"  -> at 24 sets/request that is {(custom - native) * 24 / 1000:,.2f} us/request of pure overhead")
    return {"custom": custom, "native": native, "per_request_us": (custom - native) * 24 / 1000}


# ---------------------------------------------------------------------------
# F2 — get_type_hints per request in _bind_special_parameters
# ---------------------------------------------------------------------------
def f2_type_hints():
    section("F2  get_type_hints() called on EVERY request (uncached)")
    print("  aquilia/controller/engine.py:1494 — inside _bind_special_parameters")
    print("  _get_cached_signature caches the signature but NOT the type hints.\n")

    from typing import get_type_hints

    h1 = bench(lambda: get_type_hints(_handler1), label="get_type_hints(handler with 1 annotated param)")
    h2 = bench(lambda: get_type_hints(_handler3), label="get_type_hints(handler with 3 annotated params)")

    import inspect

    sig = bench(lambda: inspect.signature(_handler1), label="inspect.signature(handler)  [this IS cached]")

    hints = get_type_hints(_handler1)
    cached = bench(lambda: hints, label="a cached dict lookup (what it could be)")
    print(f"  -> get_type_hints costs {h1:,.0f} ns/request that a cache would make ~{cached:,.0f} ns")
    return {"hints_1": h1, "hints_3": h2, "signature": sig}


# ---------------------------------------------------------------------------
# F3 — register_instance per request: ValueProvider + COW + diagnostics
# ---------------------------------------------------------------------------
def f3_register_instance():
    section("F3  register_instance(Request) on every request")
    print("  aquilia/asgi.py:475 — awaited once per request on the request scope")
    print("  Triggers: ValueProvider alloc, COW dict copy, diagnostics emit, plugin check\n")

    import asyncio

    from aquilia.di import Container
    from aquilia.di.providers import ClassProvider, ValueProvider
    from aquilia.request import Request
    from profile_baseline import make_scope  # noqa

    def make_container(n):
        c = Container(scope="app")
        for i in range(n):
            cls = type(f"S{i}", (), {"__init__": lambda self: None})
            cls.__module__ = "bench.f3"
            c.register(ClassProvider(cls, scope="app"))
        return c

    scope = make_scope()
    req = Request(scope, None)
    loop = asyncio.new_event_loop()

    def abench(coro_factory, *, label="", target_s=0.05):
        """ns/op measured INSIDE one loop run.

        loop.run_until_complete costs ~25-33us on its own, which would dwarf
        the operation under test. Drive N awaits inside a single coroutine.
        """

        async def _run(k):
            import time

            t0 = time.perf_counter()
            for _ in range(k):
                await coro_factory()
            return time.perf_counter() - t0

        k = 64
        while True:
            t = loop.run_until_complete(_run(k))
            if t >= target_s:
                break
            k = max(k * 2, int(k * target_s / max(t, 1e-9)) + 1)
        ns = min(loop.run_until_complete(_run(k)) for _ in range(REPEAT)) / k * 1e9
        if label:
            print(f"  {label:<62} {ns:>10,.1f} ns")
        return ns

    print("  cost vs. number of app providers (COW copies the whole dict):")
    out = {}
    for n in (10, 50, 200, 1000):
        c = make_container(n)

        async def one(_c=c):
            child = _c.create_request_scope()
            await child.register_instance(Request, req, scope="request")

        v = abench(one, label=f"  create_request_scope + register_instance ({n:>4} providers)")
        out[n] = v

    async def _noop():
        return None

    abench(_noop, label="  baseline: await a no-op coroutine")

    # isolate the pieces at n=50
    c = make_container(50)
    bench(c.create_request_scope, label="  create_request_scope alone")
    bench(lambda: ValueProvider(token=Request, value=req, scope="request", name="x"), label="  ValueProvider(...) alloc")
    child = c.create_request_scope()
    bench(lambda: dict(c._providers), label="  dict(providers) COW copy at 50 providers")

    # what the alternative costs: a plain dict write
    d = {}
    bench(lambda: d.__setitem__("aquilia.request.Request", req), label="  plain dict write (the ideal)")
    loop.close()
    return out


# ---------------------------------------------------------------------------
# F4 — response construction + send
# ---------------------------------------------------------------------------
def f4_response():
    section("F4  Response construction and header preparation")
    from aquilia.response import Response

    payload = {"ok": True}
    j = bench(lambda: Response.json(payload), label="Response.json({'ok': True})")
    r = Response.json(payload)
    hdr = bench(r._prepare_headers, label="Response._prepare_headers()")

    import json

    raw = bench(lambda: json.dumps(payload).encode(), label="json.dumps(payload).encode() (the payload itself)")
    print(f"  -> framework overhead above raw serialisation: {j - raw:,.0f} ns")
    return {"response_json": j, "prepare_headers": hdr, "raw_json": raw}


# ---------------------------------------------------------------------------
# F5 — the per-request total, reassembled from parts
# ---------------------------------------------------------------------------
def f5_summary(f1, f2, f3, f4):
    section("F5  Reassembled per-request budget (static route, 16.49 us measured)")
    total = 16.49
    rows = [
        ("RequestCtx.__setattr__ overhead (24x)", f1["per_request_us"]),
        ("os.urandom(16).hex() in ctx pool", 0.716),
        ("get_type_hints (uncached, per req)", f2["hints_1"] / 1000),
        ("register_instance + request scope", f3[50] / 1000),
        ("router.match_sync (static)", 0.79),
        ("Response.json + headers", (f4["response_json"] + f4["prepare_headers"]) / 1000),
    ]
    acc = 0.0
    for label, us in rows:
        acc += us
        print(f"  {label:<44} {us:>8.2f} us  {us / total * 100:>5.1f}%")
    print(f"  {'-' * 44} {'-' * 8}")
    print(f"  {'accounted':<44} {acc:>8.2f} us  {acc / total * 100:>5.1f}%")
    print(f"  {'unaccounted (async machinery, mw, misc)':<44} {total - acc:>8.2f} us  {(total - acc) / total * 100:>5.1f}%")

    print("\n  Ranked by size — where a native engine should aim:")
    for label, us in sorted(rows, key=lambda r: -r[1]):
        print(f"    {us:>6.2f} us  {label}")


def main():
    f1 = f1_setattr()
    f2 = f2_type_hints()
    f3 = f3_register_instance()
    f4 = f4_response()
    f5_summary(f1, f2, f3, f4)


if __name__ == "__main__":
    main()
