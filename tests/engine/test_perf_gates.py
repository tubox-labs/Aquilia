"""Performance regression gates for the native engine.

These are regression detectors, not the design targets. The budgets below are the
*measured* post-native numbers plus headroom, so a future change that undoes the
native win fails here. Where a budget is looser than the Phase 3/5 design target,
that is recorded explicitly rather than quietly relaxed -- see
``docs/engine/09-results.md`` for why the residual is Python wrapper cost that a
native matcher cannot remove.

Marked ``slow`` because they are timing-sensitive: run them on an idle machine.
CI runs them nightly, not per-PR, since shared runners are too noisy for a
200 ns measurement.

Phase 9H. See docs/engine/07-testing-strategy.md section 10.
"""

from __future__ import annotations

import timeit

import pytest

from aquilia._core_loader import NATIVE

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not NATIVE, reason="native engine not built"),
]

# Budget in nanoseconds per operation, with the design target for reference.
# `budget` is what this test enforces; `target` is what Phases 3/5 aimed for.
GATES = {
    # native match alone, no Python wrapper
    "native_static_match": {"budget": 80, "target": 200},
    "native_dynamic_match": {"budget": 130, "target": 300},
    "native_miss": {"budget": 60, "target": 100},
    # native RequestContext
    "ctx_construct": {"budget": 60, "target": 100},
    "ctx_slot_write": {"budget": 30, "target": None},
    # binding floor -- if this regresses, every entry point regresses
    "noop_call": {"budget": 20, "target": None},
}

REPEAT = 5
NUMBER = 50_000

SETUPS = {
    "native_static_match": (
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "[r.add_static('GET', f'/r{i}', i) for i in range(100)]\n"
        "r.freeze()\n"
        "m = r.match",
        "m('GET', '/r50')",
    ),
    "native_dynamic_match": (
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "r.add_route('GET', '/u/<uid:int>', {'uid': _core.ParamKind.INT}, 1)\n"
        "r.freeze()\n"
        "m = r.match",
        "m('GET', '/u/42')",
    ),
    "native_miss": (
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "[r.add_static('GET', f'/r{i}', i) for i in range(100)]\n"
        "r.freeze()\n"
        "m = r.match",
        "m('GET', '/nope')",
    ),
    "ctx_construct": (
        "from aquilia._core import RequestContext",
        "RequestContext()",
    ),
    "ctx_slot_write": (
        "from aquilia._core import RequestContext\nc = RequestContext()\nv = object()",
        "c.request = v",
    ),
    "noop_call": ("from aquilia._core import noop", "noop()"),
}


def _measure(name: str) -> float:
    setup, stmt = SETUPS[name]
    timer = timeit.Timer(stmt, setup=setup)
    # Minimum, not mean: every noise source only adds time to a CPU-bound op.
    return min(timer.repeat(REPEAT, NUMBER)) / NUMBER * 1e9


import os

IS_CI = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
TOLERANCE = 2.0 if IS_CI else 1.25


@pytest.mark.parametrize("name", list(GATES))
def test_within_budget(name: str) -> None:
    """Measured cost must stay within budget (plus tolerance for machine noise)."""
    budget = GATES[name]["budget"]
    measured = _measure(name)
    assert measured <= budget * TOLERANCE, (
        f"{name}: {measured:.1f} ns exceeds budget {budget} ns ({TOLERANCE}x tol). "
        f"The native engine may have regressed or been bypassed."
    )


def test_native_beats_python_router() -> None:
    """The whole point: the native tier must actually be faster than the Python
    tiers it front-runs.

    Asserted as a ratio rather than an absolute, so it holds on any machine.
    """
    from aquilia import GET, Controller
    from aquilia.controller.compiler import ControllerCompiler
    from aquilia.controller.router import ControllerRouter

    class Bench(Controller):
        prefix = "/b"

        @GET("/items")
        async def items(self, ctx):
            pass

        @GET("/items/<iid:int>")
        async def item(self, ctx, iid: int):
            pass

    def build(native: bool) -> ControllerRouter:
        router = ControllerRouter()
        router.add_controller(ControllerCompiler().compile_controller(Bench))
        router.initialize()
        if not native:
            router._native = None
            router._native_methods = {}
        return router

    def timed(router: ControllerRouter, path: str) -> float:
        match = router.match_sync
        best = min(timeit.Timer(lambda: match(path, "GET")).repeat(REPEAT, 20_000))
        return best / 20_000 * 1e9

    native_router, python_router = build(True), build(False)
    for path in ("/b/items", "/b/items/42"):
        native_ns = timed(native_router, path)
        python_ns = timed(python_router, path)
        assert native_ns < python_ns, (
            f"{path}: native {native_ns:.0f} ns is not faster than "
            f"Python {python_ns:.0f} ns -- the native tier is not being used"
        )
