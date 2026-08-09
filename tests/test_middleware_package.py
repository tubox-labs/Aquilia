"""Tests for the middleware package: base hooks, stack, builder, instruments.

Covers what the package split added on top of the behaviour
``test_middleware_refactoring.py`` already pins down:

- the hook-based base (``handle``/``before``/``after``) and its equivalence to
  the historical ``__call__`` interface
- declarative registration metadata
- conditional middleware via ``should_run``
- lifespan (``setup``/``teardown``)
- ``freeze()`` and ``describe()``
- the response-contract check naming the right middleware on the untraced path
- tracing and metrics instruments
"""

from __future__ import annotations

import pytest

from aquilia.middleware import Middleware
from aquilia.middleware.core.descriptor import MiddlewareMeta
from aquilia.middleware.core.priority import Priority
from aquilia.middleware.core.types import Scope
from aquilia.middleware.instrumentation.metrics import MetricsInstrument
from aquilia.middleware.stack import MiddlewareStack
from aquilia.middleware.stack.errors import (
    MiddlewareContractFault,
    MiddlewareRegistrationFault,
)
from aquilia.response import Response


async def _final(request, ctx):
    return Response.json({"ok": True})


def _request():
    """Minimal request stand-in. The middleware under test never touch the wire."""

    class _Req:
        def __init__(self):
            self.state: dict = {}
            self.scope: dict = {"headers": []}
            self.method = "GET"
            self.path = "/"

        def header(self, name, default=None):
            return default

    return _Req()


def _ctx():
    class _Ctx:
        def __init__(self):
            self.state: dict = {}
            self.request_id = None

    return _Ctx()


# ── Hook-based base ──────────────────────────────────────────────────────────


class TestHooks:
    async def test_before_and_after_run_around_the_chain(self):
        order: list[str] = []

        class Recorder(Middleware):
            async def before(self, request, ctx):
                order.append("before")
                return None

            async def after(self, request, ctx, response):
                order.append("after")
                response.headers["x-seen"] = "1"
                return response

        stack = MiddlewareStack()
        stack.add(Recorder(), name="recorder")
        response = await stack.build_handler(_final)(_request(), _ctx())

        assert order == ["before", "after"]
        assert response.headers["x-seen"] == "1"

    async def test_before_short_circuits_without_calling_the_handler(self):
        reached = False

        async def final(request, ctx):
            nonlocal reached
            reached = True
            return Response.json({"ok": True})

        class Gate(Middleware):
            async def before(self, request, ctx):
                return Response.json({"denied": True}, status=403)

            async def after(self, request, ctx, response):
                raise AssertionError("after must not run when before short-circuits")

        stack = MiddlewareStack()
        stack.add(Gate(), name="gate")
        response = await stack.build_handler(final)(_request(), _ctx())

        assert response.status == 403
        assert reached is False

    async def test_handle_override_wraps_the_continuation(self):
        class Wrapper(Middleware):
            async def handle(self, request, ctx, next_handler):
                response = await next_handler(request, ctx)
                response.headers["x-wrapped"] = "yes"
                return response

        stack = MiddlewareStack()
        stack.add(Wrapper(), name="wrapper")
        response = await stack.build_handler(_final)(_request(), _ctx())
        assert response.headers["x-wrapped"] == "yes"

    async def test_legacy_call_override_still_works(self):
        """The pre-package interface must keep running untouched."""

        class Legacy(Middleware):
            async def __call__(self, request, ctx, next_handler):
                response = await next_handler(request, ctx)
                response.headers["x-legacy"] = "1"
                return response

        stack = MiddlewareStack()
        stack.add(Legacy(), name="legacy")
        response = await stack.build_handler(_final)(_request(), _ctx())
        assert response.headers["x-legacy"] == "1"

    async def test_call_override_wins_over_handle(self):
        """A subclass defining both gets ``__call__``, as before the split."""

        class Both(Middleware):
            async def handle(self, request, ctx, next_handler):
                raise AssertionError("handle must not be used when __call__ is overridden")

            async def __call__(self, request, ctx, next_handler):
                return await next_handler(request, ctx)

        stack = MiddlewareStack()
        stack.add(Both(), name="both")
        assert (await stack.build_handler(_final)(_request(), _ctx())).status == 200

    async def test_plain_async_function_middleware(self):
        async def stamp(request, ctx, next_handler):
            response = await next_handler(request, ctx)
            response.headers["x-fn"] = "1"
            return response

        stack = MiddlewareStack()
        stack.add(stamp)
        response = await stack.build_handler(_final)(_request(), _ctx())
        assert response.headers["x-fn"] == "1"


# ── Declarative metadata ─────────────────────────────────────────────────────


class TestMetadata:
    def test_class_attributes_supply_registration_defaults(self):
        class Declared(Middleware):
            name = "declared"
            priority = 42
            scope = "controller:users"
            tags = ("audit",)

            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Declared())

        (desc,) = stack.middlewares
        assert desc.name == "declared"
        assert desc.priority == 42
        assert str(desc.scope) == "controller:users"
        assert desc.tags == ("audit",)

    def test_explicit_arguments_win_over_class_metadata(self):
        class Declared(Middleware):
            name = "declared"
            priority = 42

            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Declared(), priority=7, name="override")

        (desc,) = stack.middlewares
        assert (desc.name, desc.priority) == ("override", 7)

    def test_undeclared_middleware_gets_framework_defaults(self):
        class Bare(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Bare())

        (desc,) = stack.middlewares
        assert desc.name == "Bare"
        assert desc.priority == Priority.APPLICATION_DEFAULT
        assert str(desc.scope) == "global"

    def test_meta_of_plain_function(self):
        async def fn(request, ctx, next_handler): ...

        assert MiddlewareMeta.of(fn).name == "fn"


# ── Conditional middleware ───────────────────────────────────────────────────


class TestConditional:
    async def test_should_run_false_bypasses_the_middleware(self):
        ran: list[str] = []

        class OnlyPost(Middleware):
            async def should_run(self, request, ctx) -> bool:
                return request.method == "POST"

            async def before(self, request, ctx):
                ran.append(request.method)
                return None

        stack = MiddlewareStack()
        stack.add(OnlyPost(), name="only_post")
        handler = stack.build_handler(_final)

        request = _request()
        request.method = "GET"
        assert (await handler(request, _ctx())).status == 200
        assert ran == []

        request.method = "POST"
        await handler(request, _ctx())
        assert ran == ["POST"]

    def test_conditional_flag_is_only_set_when_overridden(self):
        """Middleware without the hook must not pay for the predicate wrapper."""

        class Plain(Middleware):
            async def before(self, request, ctx):
                return None

        class Gated(Middleware):
            async def should_run(self, request, ctx) -> bool:
                return True

            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Plain(), priority=1, name="plain")
        stack.add(Gated(), priority=2, name="gated")

        flags = {d.name: d.conditional for d in stack.middlewares}
        assert flags == {"plain": False, "gated": True}


# ── Lifespan ─────────────────────────────────────────────────────────────────


class TestLifespan:
    async def test_setup_and_teardown_run_in_opposite_orders(self):
        events: list[str] = []

        def make(label: str):
            class Resource(Middleware):
                async def setup(self, app):
                    events.append(f"setup:{label}")

                async def teardown(self, app):
                    events.append(f"teardown:{label}")

                async def before(self, request, ctx):
                    return None

            return Resource()

        stack = MiddlewareStack()
        stack.add(make("outer"), priority=1, name="outer")
        stack.add(make("inner"), priority=2, name="inner")

        await stack.startup(app=None)
        await stack.shutdown(app=None)

        assert events == [
            "setup:outer",
            "setup:inner",
            "teardown:inner",  # reverse: inner unwinds first
            "teardown:outer",
        ]

    async def test_teardown_failure_does_not_strand_the_others(self):
        torn: list[str] = []

        class Breaks(Middleware):
            async def teardown(self, app):
                raise RuntimeError("boom")

            async def before(self, request, ctx):
                return None

        class Works(Middleware):
            async def teardown(self, app):
                torn.append("works")

            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Works(), priority=1, name="works")
        stack.add(Breaks(), priority=2, name="breaks")

        await stack.shutdown(app=None)  # must not raise
        assert torn == ["works"]

    async def test_middleware_without_lifespan_is_skipped(self):
        class Plain(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Plain(), name="plain")
        assert stack.middlewares[0].lifespan is False

        await stack.startup(app=None)
        await stack.shutdown(app=None)


# ── Registration guards ──────────────────────────────────────────────────────


class TestRegistration:
    def test_freeze_rejects_late_registration(self):
        """Post-boot registration used to be a silent no-op: the chain is cached."""

        class Late(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.freeze()

        with pytest.raises(MiddlewareRegistrationFault, match="stack is frozen"):
            stack.add(Late(), name="late")

    def test_registration_fault_is_still_a_type_error(self):
        """Back-compat: call sites written before the fault system catch TypeError."""

        class NotMiddleware:
            async def __call__(self, request, ctx, next_handler): ...

        stack = MiddlewareStack()
        with pytest.raises(TypeError):
            stack.add(NotMiddleware())

    def test_sync_hook_is_rejected_at_registration(self):
        class SyncHook(Middleware):
            def before(self, request, ctx):  # not async
                return None

        stack = MiddlewareStack()
        with pytest.raises(MiddlewareRegistrationFault, match="coroutine function"):
            stack.add(SyncHook(), name="sync_hook")

    def test_noop_middleware_warns(self, caplog):
        import logging

        class Noop(Middleware):
            pass

        stack = MiddlewareStack()
        with caplog.at_level(logging.WARNING, logger="aquilia.middleware"):
            stack.add(Noop(), name="noop")

        assert "has no effect" in caplog.text

    def test_describe_reports_the_sorted_stack(self):
        class Any(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Any(), priority=20, name="late", tags=["b"])
        stack.add(Any(), priority=5, name="early", tags=["a"])

        described = stack.describe()
        assert [d["name"] for d in described] == ["early", "late"]
        assert described[0]["priority"] == 5
        assert described[0]["tags"] == ["a"]
        assert described[0]["scope"] == "global"


# ── Response contract ────────────────────────────────────────────────────────


class TestResponseContract:
    async def test_missing_return_names_the_registered_middleware(self):
        """The untraced path used to report ``type(mw).__name__``, so a function
        middleware surfaced as ``'function'``."""

        async def forgets_to_return(request, ctx, next_handler):
            await next_handler(request, ctx)

        stack = MiddlewareStack()
        stack.add(forgets_to_return, name="forgetful")

        with pytest.raises(MiddlewareContractFault, match="'forgetful' returned None"):
            await stack.build_handler(_final)(_request(), _ctx())

    async def test_wrong_type_is_reported_as_type_error(self):
        async def returns_string(request, ctx, next_handler):
            return "not a response"

        stack = MiddlewareStack()
        stack.add(returns_string, name="stringy")

        with pytest.raises(TypeError, match="returned invalid type 'str'"):
            await stack.build_handler(_final)(_request(), _ctx())


# ── Instruments ──────────────────────────────────────────────────────────────


class TestInstruments:
    async def test_metrics_instrument_counts_calls(self):
        class Plain(Middleware):
            async def before(self, request, ctx):
                return None

        metrics = MetricsInstrument()
        stack = MiddlewareStack(instruments=[metrics])
        stack.add(Plain(), name="plain")

        handler = stack.build_handler(_final)
        await handler(_request(), _ctx())
        await handler(_request(), _ctx())

        snapshot = metrics.snapshot()
        assert snapshot["plain"]["calls"] == 2
        assert snapshot["plain"]["errors"] == 0
        assert snapshot["plain"]["total_ms"] >= 0.0

    async def test_metrics_instrument_counts_errors_and_reraises(self):
        class Boom(Middleware):
            async def before(self, request, ctx):
                raise RuntimeError("boom")

        metrics = MetricsInstrument()
        stack = MiddlewareStack(instruments=[metrics])
        stack.add(Boom(), name="boom")

        with pytest.raises(RuntimeError, match="boom"):
            await stack.build_handler(_final)(_request(), _ctx())

        assert metrics.snapshot()["boom"]["errors"] == 1

    async def test_tracing_instrument_is_transparent_without_a_trace(self):
        class Plain(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack(traced=True)
        stack.add(Plain(), name="plain")

        response = await stack.build_handler(_final)(_request(), _ctx())
        assert response.status == 200


# ── Scope ────────────────────────────────────────────────────────────────────


class TestScope:
    def test_parse_and_roundtrip(self):
        assert Scope.parse("global") == Scope("global", "")
        assert Scope.parse("controller:users") == Scope("controller", "users")
        assert str(Scope.parse("route:/health")) == "route:/health"

    def test_global_matches_everything(self):
        assert Scope.parse("global").matches("controller", "users") is True

    def test_targeted_scope_matches_only_its_target(self):
        scope = Scope.parse("controller:users")
        assert scope.matches("controller", "users") is True
        assert scope.matches("controller", "orders") is False
        assert scope.matches("route", "users") is False

    def test_bandwide_scope_matches_any_target_in_band(self):
        assert Scope.parse("controller").matches("controller", "anything") is True


class TestScopedSelection:
    """The scoped-execution seam.

    ``build_handler`` still includes every middleware regardless of scope —
    that is today's behaviour and narrowing it is a separate, announced change.
    ``select``/``build_scoped_handler`` are the explicit opt-in.
    """

    def _stack(self):
        class Any(Middleware):
            async def before(self, request, ctx):
                return None

        stack = MiddlewareStack()
        stack.add(Any(), scope="global", priority=1, name="global_mw")
        stack.add(Any(), scope="controller:users", priority=2, name="users_mw")
        stack.add(Any(), scope="controller:orders", priority=3, name="orders_mw")
        return stack

    def test_select_filters_by_target(self):
        names = [d.name for d in self._stack().select("controller", "users")]
        assert names == ["global_mw", "users_mw"]

    def test_select_preserves_ordering(self):
        stack = self._stack()
        assert [d.name for d in stack.select("controller", "orders")] == ["global_mw", "orders_mw"]

    def test_build_handler_still_includes_every_scope(self):
        """Guard against silently turning scope into a filter."""
        stack = self._stack()
        assert len(stack.middlewares) == 3
        assert [d.name for d in stack] == ["global_mw", "users_mw", "orders_mw"]

    async def test_build_scoped_handler_runs_only_matching_middleware(self):
        ran: list[str] = []

        def make(label: str):
            class Recorder(Middleware):
                async def before(self, request, ctx):
                    ran.append(label)
                    return None

            return Recorder()

        stack = MiddlewareStack()
        stack.add(make("global"), scope="global", priority=1, name="g")
        stack.add(make("users"), scope="controller:users", priority=2, name="u")
        stack.add(make("orders"), scope="controller:orders", priority=3, name="o")

        handler = stack.build_scoped_handler(_final, "controller", "users")
        await handler(_request(), _ctx())

        assert ran == ["global", "users"]
