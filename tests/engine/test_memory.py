"""Refcount and lifetime correctness for the native engine.

nanobind prints a "leaked N instances" report at interpreter shutdown for any
instance still reachable when the module is torn down. That report is *not* by
itself evidence of a refcount bug: an object held in a ContextVar or a
module-level singleton at exit is reported identically to one that leaked.

These tests distinguish the two by measuring growth. A refcount bug scales with
the number of operations; retention does not.

Phase 9F. See docs/engine/07-testing-strategy.md section 8.
"""

from __future__ import annotations

import gc
import sys

import pytest

from aquilia._core_loader import NATIVE
from aquilia.controller.base import RequestCtx

pytestmark = pytest.mark.skipif(not NATIVE, reason="native engine not built")


def _live_contexts() -> int:
    from aquilia._core import RequestContext

    gc.collect()
    return sum(1 for o in gc.get_objects() if isinstance(o, RequestContext))


def test_context_construction_does_not_accumulate() -> None:
    """10k contexts must not leave 10k objects behind."""
    gc.collect()
    before = _live_contexts()
    for _ in range(10_000):
        ctx = RequestCtx(request=object())
        ctx.identity = "x"
        ctx.dynamic_attr = 1
        del ctx
    after = _live_contexts()
    # A couple may survive in the local frame / gc generations; 10k may not.
    assert after - before < 10, f"contexts accumulated: {before} -> {after}"


def test_slot_writes_balance_refcounts() -> None:
    """Binding, rebinding, and clearing a slot must leave the target's refcount
    exactly where it started.

    This is the assertion that actually catches a missing decref in PyRef's
    assignment operators: a leaked reference per write would show up as +10000.
    """
    target = object()
    before = sys.getrefcount(target)
    for _ in range(10_000):
        ctx = RequestCtx(request=target)
        ctx.identity = target
        ctx.session = target
        ctx.identity = None  # overwrite must decref the old value
        del ctx
    gc.collect()
    assert sys.getrefcount(target) == before


def test_router_match_balances_refcounts() -> None:
    """Repeated matching must not grow the object graph.

    Covers the params dict, the interned param-name strings, and the int
    conversion on the hit path, plus the miss and defer paths.
    """
    from aquilia._core import ParamKind, Router

    router = Router()
    router.add_route("GET", "/u/<uid:int>", {"uid": ParamKind.INT}, 1)
    router.add_static("GET", "/static", 2)
    router.freeze()

    gc.collect()
    before = len(gc.get_objects())
    for _ in range(20_000):
        router.match("GET", "/u/42")  # hit with a param
        router.match("GET", "/static")  # hit, no params
        router.match("GET", "/nope")  # miss
        router.match("GET", "/u/1_000")  # defer
    gc.collect()
    after = len(gc.get_objects())
    assert after - before < 100, f"object graph grew by {after - before}"


def test_returned_params_are_independent_objects() -> None:
    """Each match must return a fresh dict, not a shared buffer.

    A reused dict would make two concurrent requests observe each other's params.
    """
    from aquilia._core import ParamKind, Router

    router = Router()
    router.add_route("GET", "/u/<uid>", {"uid": ParamKind.STR}, 1)
    router.freeze()

    _, first = router.match("GET", "/u/alice")
    _, second = router.match("GET", "/u/bob")
    assert first == {"uid": "alice"}
    assert second == {"uid": "bob"}
    assert first is not second


def test_context_slots_release_their_referents() -> None:
    """Dropping a context must release everything it held.

    Uses a sentinel whose collection is observable, so this fails if PyRef's
    destructor does not decref.
    """
    import weakref

    class Holder:
        pass

    target = Holder()
    ref = weakref.ref(target)

    ctx = RequestCtx(request=target)
    ctx.identity = target
    del target, ctx
    gc.collect()

    assert ref() is None, "context did not release its referents"
