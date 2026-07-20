"""
Tests for the new enterprise DI capabilities:

- DISettings (typed, fault-based config) + configure_di
- Hierarchical child containers + runtime replace_provider
- Provider-level interceptors (AOP)
- Conditional / environment-gated providers
- DI plugin system
- Parallel constructor-dependency resolution
- Diagnostics event wiring
- Pool max-waiters cap
"""

import asyncio

import pytest

from aquilia.di import (
    ClassProvider,
    ConditionContext,
    Container,
    DIPlugin,
    DISettings,
    InterceptingProvider,
    ProviderInterceptor,
    ValueProvider,
    clear_plugins,
    conditional,
    configure_di,
    get_di_settings,
    get_plugins,
    intercept,
    register_plugin,
    reset_di_settings,
    should_register,
)
from aquilia.di.settings import DIConfigFault
from aquilia.faults.domains import DIFault


@pytest.fixture(autouse=True)
def _reset_di():
    reset_di_settings()
    clear_plugins()
    yield
    reset_di_settings()
    clear_plugins()


# ── DISettings ────────────────────────────────────────────────────────


class TestDISettings:
    def test_defaults(self):
        s = DISettings()
        assert s.scope_enforcement == "warn"
        assert s.strict_scopes is False
        assert s.scope_check_enabled is True

    def test_strict_scopes_derived(self):
        assert DISettings(scope_enforcement="raise").strict_scopes is True
        assert DISettings(scope_enforcement="off").scope_check_enabled is False

    def test_invalid_scope_enforcement_raises_fault(self):
        with pytest.raises(DIConfigFault):
            DISettings(scope_enforcement="bogus")

    def test_invalid_disposal_raises_fault(self):
        with pytest.raises(DIConfigFault):
            DISettings(disposal_strategy="nope")

    def test_invalid_pool_waiters_raises_fault(self):
        with pytest.raises(DIConfigFault):
            DISettings(pool_max_waiters=0)

    def test_from_mapping_ignores_unknown_keys(self):
        s = DISettings.from_mapping({"scope_enforcement": "raise", "unknown": 1})
        assert s.strict_scopes is True

    def test_from_mapping_none_returns_default(self):
        assert DISettings.from_mapping(None).scope_enforcement == "warn"

    def test_configure_and_get(self):
        configure_di(DISettings(parallel_resolution=True))
        assert get_di_settings().parallel_resolution is True


# ── Hierarchical children + replace ───────────────────────────────────


class TestChildContainersAndReplace:
    async def test_create_child_inherits_parent_providers(self):
        root = Container(scope="app")
        root.register(ValueProvider(value="v", token="T", scope="app"))
        child = root.create_child(scope="app")
        assert await child.resolve_async("T") == "v"

    async def test_child_register_is_isolated(self):
        root = Container(scope="app")
        child = root.create_child(scope="app")
        child.register(ValueProvider(value="child-only", token="C", scope="app"))
        assert await child.resolve_async("C") == "child-only"
        # Parent must not see the child's private registration.
        assert root.is_registered("C") is False

    async def test_replace_provider_swaps_and_evicts_cache(self):
        c = Container(scope="app")
        c.register(ValueProvider(value=1, token="N", scope="app"))
        assert await c.resolve_async("N") == 1
        await c.replace_provider("N", ValueProvider(value=2, token="N", scope="app"))
        assert await c.resolve_async("N") == 2


# ── Module containers / exports ───────────────────────────────────────


class TestModuleContainers:
    async def test_removed(self):
        # ModuleContainer was removed — the shipped runtime uses link-based
        # cross-app resolution (Container.add_dependency_link), not nested
        # module containers. See docs/design/di-cross-app-resolution.md.
        import aquilia.di as di

        assert not hasattr(di, "ModuleContainer")


# ── Interceptors ──────────────────────────────────────────────────────


class TestInterceptors:
    async def test_interceptor_wraps_instantiation(self):
        order = []

        class I1(ProviderInterceptor):
            async def around_instantiate(self, ctx, nxt):
                order.append("before")
                obj = await nxt()
                order.append("after")
                return obj

        class Svc:
            pass

        c = Container(scope="app")
        c.register(intercept(ClassProvider(Svc, scope="app"), I1()))
        inst = await c.resolve_async(Svc)
        assert isinstance(inst, Svc)
        assert order == ["before", "after"]

    async def test_interceptor_chain_order(self):
        seq = []

        def mk(name):
            class Ic(ProviderInterceptor):
                async def around_instantiate(self, ctx, nxt):
                    seq.append(f"{name}:in")
                    o = await nxt()
                    seq.append(f"{name}:out")
                    return o

            return Ic()

        class Svc:
            pass

        c = Container(scope="app")
        c.register(intercept(ClassProvider(Svc, scope="app"), mk("A"), mk("B")))
        await c.resolve_async(Svc)
        assert seq == ["A:in", "B:in", "B:out", "A:out"]

    def test_empty_interceptors_raises(self):
        class Svc:
            pass

        with pytest.raises(DIFault):
            InterceptingProvider(ClassProvider(Svc), [])


# ── Conditional providers ─────────────────────────────────────────────


class TestConditional:
    def test_conditional_predicate(self):
        @conditional(lambda c: c.is_env("prod"))
        class ProdOnly:
            pass

        assert should_register(ProdOnly, ConditionContext(env="prod")) is True
        assert should_register(ProdOnly, ConditionContext(env="dev")) is False

    def test_no_condition_always_registers(self):
        class Plain:
            pass

        assert should_register(Plain, ConditionContext(env="dev")) is True

    def test_condition_error_skips(self):
        @conditional(lambda c: 1 / 0)
        class Boom:
            pass

        assert should_register(Boom, ConditionContext(env="dev")) is False

    def test_condition_context_get_from_dict(self):
        ctx = ConditionContext(env="prod", config={"cache": {"backend": "redis"}})
        assert ctx.get("cache.backend") == "redis"
        assert ctx.get("cache.missing", "d") == "d"


# ── Plugins ───────────────────────────────────────────────────────────


class TestPlugins:
    def test_register_and_get(self):
        class P(DIPlugin):
            name = "p1"

        register_plugin(P())
        assert [p.name for p in get_plugins()] == ["p1"]

    def test_register_idempotent_by_name(self):
        class P(DIPlugin):
            name = "dup"

        register_plugin(P())
        register_plugin(P())
        assert len([p for p in get_plugins() if p.name == "dup"]) == 1

    def test_plugins_disabled_returns_empty(self):
        class P(DIPlugin):
            name = "x"

        register_plugin(P())
        configure_di(DISettings(enable_plugins=False))
        assert get_plugins() == []

    def test_invalid_plugin_raises(self):
        with pytest.raises(DIFault):
            register_plugin(object())  # type: ignore[arg-type]


# ── Parallel resolution ───────────────────────────────────────────────


class TestParallelResolution:
    async def test_parallel_faster_than_sequential(self):
        class A:
            async def async_init(self):
                await asyncio.sleep(0.05)

        class B:
            async def async_init(self):
                await asyncio.sleep(0.05)

        class C:
            def __init__(self, a: A, b: B):
                self.a = a
                self.b = b

        configure_di(DISettings(parallel_resolution=True))
        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        c.register(ClassProvider(B, scope="app"))
        c.register(ClassProvider(C, scope="app"))
        inst = await c.resolve_async(C)
        assert isinstance(inst.a, A)
        assert isinstance(inst.b, B)


# ── Diagnostics ───────────────────────────────────────────────────────


class TestDiagnostics:
    async def test_resolution_events_emitted_when_enabled(self):
        events = []

        class L:
            def on_event(self, e):
                events.append(e.type.value)

        configure_di(DISettings(diagnostics_enabled=True))
        c = Container(scope="app")
        c.add_diagnostic_listener(L())
        c.register(ValueProvider(value=1, token="D", scope="app"))
        await c.resolve_async("D")
        assert "resolution_start" in events
        assert "resolution_success" in events

    async def test_no_resolution_events_when_disabled(self):
        events = []

        class L:
            def on_event(self, e):
                events.append(e.type.value)

        configure_di(DISettings(diagnostics_enabled=False))
        c = Container(scope="app")
        c.add_diagnostic_listener(L())
        c.register(ValueProvider(value=1, token="D", scope="app"))
        await c.resolve_async("D")
        assert "resolution_start" not in events


# ── Pool waiter cap ───────────────────────────────────────────────────


class TestPoolWaiters:
    async def test_max_waiters_fast_fails(self):
        from aquilia.di.core import ResolveCtx
        from aquilia.di.providers import PoolProvider

        async def factory():
            return object()

        p = PoolProvider(factory, max_size=1, token="X", max_waiters=1)
        ctx = ResolveCtx(container=None)
        # Drain the single slot.
        await p.instantiate(ctx)

        async def waiter():
            try:
                await asyncio.wait_for(p.instantiate(ctx), timeout=0.2)
                return "ok"
            except DIFault:
                return "fault"
            except (TimeoutError, asyncio.TimeoutError):
                return "timeout"

        results = await asyncio.gather(waiter(), waiter())
        # One is allowed to wait (times out); the other exceeds the cap → fault.
        assert "fault" in results


# ── Scope enforcement modes ───────────────────────────────────────────


class TestScopeEnforcement:
    async def test_raise_mode_raises_on_violation(self):
        from aquilia.di.errors import ScopeViolationError

        configure_di(DISettings(scope_enforcement="raise"))
        app = Container(scope="app")
        # A request-scoped provider resolved directly in an app container is a
        # captive-dependency violation.
        app.register(ValueProvider(value="r", token="R", scope="request"))
        with pytest.raises(ScopeViolationError):
            await app.resolve_async("R")

    async def test_off_mode_skips_check(self):
        configure_di(DISettings(scope_enforcement="off"))
        app = Container(scope="app")
        app.register(ValueProvider(value="r", token="R", scope="request"))
        # No raise, no problem.
        assert await app.resolve_async("R") == "r"
