"""
Regression tests for the nanobind ``RequestContext`` reference leak.

The bug
-------
``aquilia._core.RequestContext`` stores its seven slots as raw owning
``PyObject*`` (``aq::PyRef``). nanobind installs ``tp_traverse``/``tp_clear``
for the ``__dict__`` that ``nb::dynamic_attr()`` adds, but it cannot know about
C++ fields -- so a reference cycle that runs *through a slot* is invisible to
the cycle collector and the instance is never freed:

    ctx.state = {"ctx": ctx}      # slot -> dict -> instance

That produced ``nanobind: leaked N instances of type
"aquilia.controller.base.RequestCtx"``, one per request, i.e. unbounded memory
growth in a long-running server.

The fix is in ``aquilia/_core/src/request_ctx.hpp`` + ``module.cpp``: a custom
``tp_traverse``/``tp_clear`` pair that visits the slots as well as the dict and
the type.

These tests assert the *observable* property -- no live instances survive a
collection -- rather than inspecting nanobind internals, so they keep working
if the implementation of the fix changes.
"""

from __future__ import annotations

import gc

import pytest

from aquilia import GET, Controller, RequestCtx, Response
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

try:
    from aquilia._core import RequestContext as _NativeRequestContext

    NATIVE = True
except ImportError:  # pragma: no cover - pure-Python build
    _NativeRequestContext = None
    NATIVE = False

native_only = pytest.mark.skipif(not NATIVE, reason="requires the _core native extension")


def _live(type_name: str) -> int:
    """Count GC-visible instances of a type, by name.

    By name rather than by identity so this works for both the native base and
    the ``RequestCtx`` subclass without importing either conditionally.
    """
    gc.collect()
    gc.collect()
    return sum(1 for o in gc.get_objects() if type(o).__name__ == type_name)


# ── The mechanism, in isolation ─────────────────────────────────────────────


@native_only
def test_cycle_through_native_slot_is_collectable():
    """A cycle running through a C++ slot must be breakable by the collector.

    This is the exact shape of the production leak. Before the fix this left
    ``n`` instances live forever; ``gc.collect()`` reported 0 collected because
    ``tp_traverse`` never told the collector the slot reference existed.
    """
    baseline = _live("RequestContext")

    for _ in range(100):
        c = _NativeRequestContext()
        c.state = {"ctx": c}  # slot -> dict -> instance
        del c

    assert _live("RequestContext") == baseline


@native_only
def test_cycle_through_every_slot_is_collectable():
    """Each of the seven slots must be traversed, not just the one we fixed first.

    A traverse that visits some slots and not others is the same bug with a
    smaller blast radius, and it would not be caught by testing one slot.
    """
    slots = ("request", "identity", "session", "auth", "container", "state", "request_id")
    for slot in slots:
        baseline = _live("RequestContext")
        for _ in range(20):
            c = _NativeRequestContext()
            setattr(c, slot, {"ctx": c})
            del c
        assert _live("RequestContext") == baseline, f"slot {slot!r} is not traversed"


@native_only
def test_cycle_through_dict_is_collectable():
    """The ``dynamic_attr`` dict must stay collectable after we override traverse.

    Supplying a custom ``Py_tp_traverse`` makes nanobind skip installing its
    own, so a fix that forgets the dict would trade one leak for another.
    """
    baseline = _live("RequestContext")
    for _ in range(100):
        c = _NativeRequestContext()
        c.selfref = c  # -> __dict__ -> instance
        del c
    assert _live("RequestContext") == baseline


@native_only
def test_slots_still_readable_and_writable():
    """tp_clear must not disturb ordinary slot semantics."""
    c = _NativeRequestContext()
    assert c.request is None
    sentinel = object()
    c.request = sentinel
    assert c.request is sentinel
    c.request = None
    assert c.request is None


@native_only
def test_no_cycle_still_freed_eagerly():
    """Acyclic instances must still be freed by refcounting, without a collection."""
    baseline = sum(1 for o in gc.get_objects() if type(o).__name__ == "RequestContext")
    c = _NativeRequestContext()
    c.state = {"plain": 1}
    del c
    # No gc.collect() -- refcounting alone must have freed it.
    assert sum(1 for o in gc.get_objects() if type(o).__name__ == "RequestContext") == baseline


# ── The property that actually matters: end to end ──────────────────────────


class LeakController(Controller):
    @GET("/ping")
    async def ping(self, ctx: RequestCtx):
        return Response.json({"ok": True})


def _manifest() -> AppManifest:
    return AppManifest(
        name="leak_app",
        version="0.0.1",
        controllers=["tests.test_native_ctx_leak:LeakController"],
    )


@pytest.mark.asyncio
async def test_no_request_ctx_leaks_over_repeated_requests():
    """Zero leaked ``RequestCtx`` after a run of real requests.

    This is the regression gate named in the audit: the leak was one instance
    per request, so a few hundred requests makes it unmissable while keeping
    the test fast. It runs on pure-Python builds too -- there it simply asserts
    the property has not regressed some other way.
    """
    async with TestServer(manifests=[_manifest()], debug=False) as server:
        client = TestClient(server)

        # Warm up: the first request populates caches that legitimately retain
        # objects (route match, compiled middleware chain), so the baseline has
        # to be taken after them, not before.
        for _ in range(5):
            resp = await client.get("/leak_app/ping")
            assert resp.status_code == 200

        baseline = _live("RequestCtx")

        for _ in range(300):
            resp = await client.get("/leak_app/ping")
            assert resp.status_code == 200

        leaked = _live("RequestCtx") - baseline

    assert leaked == 0, f"{leaked} RequestCtx instances leaked over 300 requests"
