"""Native/Python router parity.

The native router is a pure accelerator: for any (method, path) it must either
produce exactly what the Python tiers produce, or decline (miss/DEFER) and let
them run. These tests assert that equivalence directly, by matching the same
probe paths through a router with the native engine active and one with it
forced off.

Phase 9D. See docs/engine/07-testing-strategy.md section 4.
"""

from __future__ import annotations

import pytest

from aquilia import GET, POST, Controller
from aquilia.controller.compiler import ControllerCompiler
from aquilia.controller.router import _NATIVE, ControllerRouter

pytestmark = pytest.mark.skipif(not _NATIVE, reason="native engine not built")


class ProbeController(Controller):
    """Route shapes that exercise every native eligibility branch."""

    prefix = "/api"

    @GET("/users")
    async def list_users(self, ctx):
        pass

    @GET("/users/me")
    async def me(self, ctx):
        pass

    @GET("/users/<uid:int>")
    async def get_user(self, ctx, uid: int):
        pass

    @GET("/users/<uid:int>/posts/<pid:int>")
    async def get_post(self, ctx, uid: int, pid: int):
        pass

    @GET("/tags/<name>")
    async def get_tag(self, ctx, name: str):
        pass

    @GET("/measure/<value:float>")
    async def measure(self, ctx, value: float):
        pass

    @POST("/users")
    async def create_user(self, ctx):
        pass

    @GET("/")
    async def root(self, ctx):
        pass


class UuidController(Controller):
    """A uuid param is not a native kind, so its whole method stays on Python."""

    prefix = "/u"

    @GET("/item/<ident:uuid>")
    async def get_item(self, ctx, ident):
        pass

    @GET("/other")
    async def other(self, ctx):
        pass


class SplatController(Controller):
    """Splat compiles to a `path` param -- also not a native kind."""

    prefix = "/s"

    @GET("/files/*rest")
    async def files(self, ctx, rest: str):
        pass


PROBE_PATHS = [
    "/",
    "/api",
    "/api/",
    "/api/users",
    "/api/users/",
    "/api/users//",
    "/api/users/me",
    "/api/users/42",
    "/api/users/-1",
    "/api/users/+7",
    "/api/users/abc",  # int cast must fail
    "/api/users/1_000",  # CPython int() accepts; native must not claim a miss
    "/api/users/ 42",
    "/api/users/999999999999999999999999999999",  # unbounded int
    "/api/users/42/posts/7",
    "/api/users/42/posts/abc",
    "/api/users/42/extra",
    "/api/tags/python",
    "/api/tags/",
    "/api/measure/1.5",
    "/api/measure/-0.25",
    "/api/measure/1e10",
    "/api/measure/abc",
    "/api/measure/1.2.3",
    "/api/USERS",  # case sensitivity
    "/nope",
    "/api/nope/deeper",
    "",
    "//",
    "/api/users/42/",
    "/u/item/550e8400-e29b-41d4-a716-446655440000",
    "/u/other",
    "/s/files/a/b/c.txt",
]

METHODS = ["GET", "POST", "PUT", "DELETE", "HEAD"]


def _build(controllers, *, native: bool) -> ControllerRouter:
    """Build a router with the native tier either active or disabled.

    Disabling by clearing `_native` after initialize() is deliberate: it leaves
    the Python tiers byte-identical between the two routers, so any divergence
    is attributable to the native tier alone.
    """
    router = ControllerRouter()
    compiler = ControllerCompiler()
    for controller in controllers:
        router.add_controller(compiler.compile_controller(controller))
    router.initialize()
    if not native:
        router._native = None
        router._native_methods = {}
    return router


def _describe(match) -> tuple | None:
    """Comparable projection of a match result."""
    if match is None:
        return None
    return (
        match.route.controller_class.__name__,
        match.route.route_metadata.handler_name,
        dict(match.params),
        dict(match.query),
    )


ALL_CONTROLLERS = [ProbeController, UuidController, SplatController]


@pytest.mark.parametrize("path", PROBE_PATHS)
@pytest.mark.parametrize("method", METHODS)
def test_match_parity(method: str, path: str) -> None:
    """Native and Python must agree on every probe, for every method."""
    native = _build(ALL_CONTROLLERS, native=True)
    fallback = _build(ALL_CONTROLLERS, native=False)

    got = _describe(native.match_sync(path, method))
    want = _describe(fallback.match_sync(path, method))
    assert got == want, f"divergence on {method} {path}: native={got!r} python={want!r}"


def test_param_values_and_types_match() -> None:
    """Param conversion must produce equal values AND equal types.

    An int param arriving as `float` would compare equal for 42 but break a
    handler annotated `uid: int`, so the type is asserted too.
    """
    native = _build(ALL_CONTROLLERS, native=True)
    fallback = _build(ALL_CONTROLLERS, native=False)

    for path in ("/api/users/42", "/api/users/42/posts/7", "/api/measure/1.5", "/api/tags/py"):
        n = native.match_sync(path, "GET")
        f = fallback.match_sync(path, "GET")
        assert n is not None and f is not None, path
        assert n.params == f.params, path
        for key, value in n.params.items():
            assert type(value) is type(f.params[key]), f"{path}: {key} type differs"


def test_native_tier_is_actually_used() -> None:
    """Guard against the whole suite passing because nothing is eligible.

    Without this, an eligibility bug that rejected every method would leave all
    parity tests green while the native engine sat idle.
    """
    router = _build([ProbeController], native=True)
    assert router._native is not None
    assert router._native_methods.get("GET") is True
    assert router._native_methods.get("POST") is True
    assert len(router._native_routes) > 0
    assert router._native.static_count > 0
    assert router._native.node_count > 0


def test_uuid_param_method_is_not_native() -> None:
    """A uuid param disqualifies its method; sibling routes fall back with it."""
    router = _build([UuidController], native=True)
    assert router._native_methods.get("GET") is False
    # Still matches, via the Python tiers.
    assert router.match_sync("/u/other", "GET") is not None


def test_splat_param_method_is_not_native() -> None:
    """`*rest` compiles to a `path` param, which is not a native kind.

    Only eligibility is asserted. Splat routes do not match on the pure-Python
    path either (``/s/files/a/b`` returns None with the native tier disabled), so
    this test deliberately does not assert that they match -- that would be
    pinning a pre-existing bug unrelated to the engine.
    """
    router = _build([SplatController], native=True)
    assert router._native_methods.get("GET") is False

    # Parity is what matters here: native declines, so both paths must agree.
    fallback = _build([SplatController], native=False)
    for path in ("/s/files/a/b", "/s/files/x", "/s/files/"):
        assert _describe(router.match_sync(path, "GET")) == _describe(fallback.match_sync(path, "GET")), path


def test_brace_syntax_normalises_to_a_param() -> None:
    """`{name}` in a decorator IS a param -- but only after normalisation.

    The HTTP decorators rewrite `{name}` to `<name:str>` before compilation, so
    for `@GET("/lit/{id}")`:

        route.full_path            == "/lit/{id}"       <- pre-normalisation
        route.compiled_pattern.raw == "/lit/<id:str>"   <- what params reflect

    The native router must be built from `cp.raw`. Building it from `full_path`
    makes it read `{id}` as a literal segment, so it matches the text "/lit/{id}"
    and misses "/lit/42", while the Python trie does the opposite. That is a
    silent routing divergence, so both directions are pinned here.
    """

    class BraceController(Controller):
        prefix = "/lit"

        @GET("/{id}")
        async def braced(self, ctx):
            pass

    native = _build([BraceController], native=True)
    fallback = _build([BraceController], native=False)

    for path in ("/lit/{id}", "/lit/42", "/lit/abc"):
        assert _describe(native.match_sync(path, "GET")) == _describe(fallback.match_sync(path, "GET")), path

    # The braces normalised to a param, so a value matches and is captured.
    match = native.match_sync("/lit/42", "GET")
    assert match is not None
    assert match.params == {"id": "42"}


def test_allowed_methods_parity() -> None:
    """405 handling must see the same method set on both paths."""
    native = _build(ALL_CONTROLLERS, native=True)
    fallback = _build(ALL_CONTROLLERS, native=False)
    for path in ("/api/users", "/api/users/42", "/nope"):
        assert sorted(native.get_allowed_methods(path)) == sorted(fallback.get_allowed_methods(path)), path


def test_repeated_match_is_deterministic() -> None:
    """Frozen router: the same input must give the same answer every time."""
    router = _build(ALL_CONTROLLERS, native=True)
    first = _describe(router.match_sync("/api/users/42", "GET"))
    for _ in range(100):
        assert _describe(router.match_sync("/api/users/42", "GET")) == first
