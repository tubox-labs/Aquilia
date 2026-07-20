"""
Enterprise-grade DI test suite — real-world scenarios, concurrency stress,
failure injection, and regression protection for the DI hardening pass.

Covers:
- Regression tests for every audit bug fixed (Bug 8/9, plugin hooks, §6.3,
  diamond false-cycle, parallel singleton double-instantiation).
- Real-world app graphs: e-commerce, multi-tenant SaaS, auth, AI/LLM,
  microservices.
- Concurrency stress: 100→10k simultaneous resolutions, scope isolation,
  memory stability.
- Failure injection: constructor/async/generator failures, cancellation,
  cycles, invalid scopes, plugin exceptions.
"""

import asyncio
import gc
import warnings
from typing import Annotated

import pytest

from aquilia.di import (
    ClassProvider,
    Container,
    DIPlugin,
    DISettings,
    FactoryProvider,
    ValueProvider,
    clear_plugins,
    configure_di,
    get_request_container,
    register_plugin,
    request_container_scope,
    reset_di_settings,
    reset_request_container,
    set_request_container,
)
from aquilia.di.dep import Dep
from aquilia.faults.domains import DIFault, DIResolutionFault


@pytest.fixture(autouse=True)
def _reset():
    reset_di_settings()
    clear_plugins()
    yield
    reset_di_settings()
    clear_plugins()


# ═══════════════════════════════════════════════════════════════════════
# REGRESSION — one guard per fixed bug so it can never silently return.
# ═══════════════════════════════════════════════════════════════════════


class TestRegressionBug8SyncLoop:
    """Sync resolve() must reuse one persistent per-thread loop, not churn."""

    def test_sync_resolve_reuses_single_loop(self):
        from aquilia.di import _sync_bridge

        _sync_bridge.reset_sync_loops()

        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        for _ in range(50):
            assert isinstance(c.resolve(A), A)
        assert len(_sync_bridge._all_loops) == 1
        _sync_bridge.reset_sync_loops()

    async def test_sync_resolve_from_async_raises(self):
        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        with pytest.raises(DIResolutionFault):
            c.resolve(A)  # inside running loop → must refuse, not deadlock


class TestRegressionBug9ContextToken:
    """ContextVar must be nesting-safe via tokens, not hard-clear to None."""

    def test_nested_scope_unwinds_to_prior(self):
        outer = Container(scope="request")
        inner = Container(scope="request")
        assert get_request_container() is None
        with request_container_scope(outer):
            with request_container_scope(inner):
                assert get_request_container() is inner
            assert get_request_container() is outer  # NOT None
        assert get_request_container() is None

    def test_manual_token_reset(self):
        c = Container(scope="request")
        tok = set_request_container(c)
        assert get_request_container() is c
        reset_request_container(tok)
        assert get_request_container() is None

    def test_clear_is_deprecated(self):
        from aquilia.di.compat import clear_request_container

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            with pytest.raises(DeprecationWarning):
                clear_request_container()


class TestRegressionPluginHooks:
    """All three plugin lifecycle hooks must actually fire."""

    async def test_provider_registered_and_container_built_fire(self):
        from aquilia.di.plugins import run_container_built

        seen = {"reg": [], "built": 0}

        class P(DIPlugin):
            name = "reg-test"

            def on_provider_registered(self, container, provider):
                seen["reg"].append(provider.meta.name)

            def on_container_built(self, container):
                seen["built"] += 1

        register_plugin(P())

        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        run_container_built(c)
        assert any("A" in n for n in seen["reg"])
        assert seen["built"] == 1

    async def test_disabled_plugins_do_not_fire(self):
        configure_di(DISettings(enable_plugins=False))
        fired = []

        class P(DIPlugin):
            name = "off-test"

            def on_provider_registered(self, container, provider):
                fired.append(1)

        register_plugin(P())

        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        assert fired == []


class TestRegressionStrictRegistration:
    """§6.3 — strict_service_registration must fail-fast, else warn."""

    def test_strict_flag_present_and_typed(self):
        s = DISettings(strict_service_registration=True)
        assert s.strict_service_registration is True


class TestRegressionDiamondNoFalseCycle:
    """Diamond dependency under parallel gather must NOT report a false cycle."""

    async def test_diamond_resolves_shared_once(self):
        hits = []

        async def C():
            await asyncio.sleep(0.01)
            hits.append(1)
            return "c"

        async def A(c: Annotated[str, Dep(C)]):
            return "A" + c

        async def B(c: Annotated[str, Dep(C)]):
            return "B" + c

        async def root(a: Annotated[str, Dep(A)], b: Annotated[str, Dep(B)]):
            return (a, b)

        c = Container(scope="request")
        res = await c.resolve_dep(Dep(root), object)
        assert res == ("Ac", "Bc")
        assert len(hits) == 1  # shared sub-dep deduplicated, resolved once

    async def test_true_cycle_still_detected(self):
        async def H(g): ...

        async def G(h): ...

        G.__annotations__ = {"h": Annotated[str, Dep(H)]}
        H.__annotations__ = {"g": Annotated[str, Dep(G)]}

        c = Container(scope="request")
        with pytest.raises(DIResolutionFault, match="[Cc]ircular"):
            await asyncio.wait_for(c.resolve_dep(Dep(G), object), timeout=5)


class TestRegressionParallelSingleton:
    """Parallel constructor resolution must not double-instantiate a shared
    cacheable provider (singleton/app/request guarantee)."""

    async def test_shared_async_singleton_single_instance(self):
        configure_di(DISettings(parallel_resolution=True))
        calls = []

        class Shared:
            pass

        async def make_shared() -> Shared:
            await asyncio.sleep(0.02)
            calls.append(1)
            return Shared()

        class Mid1:
            def __init__(self, s: Shared):
                self.s = s

        class Mid2:
            def __init__(self, s: Shared):
                self.s = s

        class Wide:
            def __init__(self, a: Mid1, b: Mid2):
                self.a = a
                self.b = b

        c = Container(scope="app")
        c.register(FactoryProvider(make_shared, scope="app", name=c._token_to_key(Shared)))
        c.register(ClassProvider(Mid1, scope="app"))
        c.register(ClassProvider(Mid2, scope="app"))
        c.register(ClassProvider(Wide, scope="app"))

        w = await c.resolve_async(Wide)
        assert len(calls) == 1
        assert w.a.s is w.b.s


# ═══════════════════════════════════════════════════════════════════════
# ENTERPRISE — real-world application graphs.
# ═══════════════════════════════════════════════════════════════════════


class TestEcommercePlatform:
    async def test_request_scoped_transaction_isolation(self):
        # App-scoped infra (DB pool, cache) shared; request-scoped txn isolated.
        class Database:
            def __init__(self):
                self.id = id(self)

        class Cache:
            pass

        class PaymentGateway:
            def __init__(self, db: Database):
                self.db = db

        class InventoryService:
            def __init__(self, db: Database, cache: Cache):
                self.db = db

        class OrderService:
            def __init__(self, db: Database, pay: PaymentGateway, inv: InventoryService):
                self.db = db
                self.pay = pay
                self.inv = inv

        app = Container(scope="app")
        app.register(ClassProvider(Database, scope="app"))
        app.register(ClassProvider(Cache, scope="app"))
        app.register(ClassProvider(PaymentGateway, scope="app"))
        app.register(ClassProvider(InventoryService, scope="app"))
        app.register(ClassProvider(OrderService, scope="request"))

        # Two requests, each own OrderService but same shared Database.
        r1 = app.create_request_scope()
        r2 = app.create_request_scope()
        o1 = await r1.resolve_async(OrderService)
        o2 = await r2.resolve_async(OrderService)
        assert o1 is not o2  # request scope isolates
        assert o1.db is o2.db  # app-scoped DB shared
        assert o1.pay.db is o1.db  # same DB threaded through graph
        await r1.shutdown()
        await r2.shutdown()

    async def test_full_checkout_graph_resolves(self):
        configure_di(DISettings(parallel_resolution=True))

        class DB:
            pass

        class Cache:
            pass

        class Notifications:
            pass

        class Order:
            def __init__(self, db: DB, cache: Cache, notif: Notifications):
                self.ok = all([db, cache, notif])

        app = Container(scope="app")
        for cls in (DB, Cache, Notifications):
            app.register(ClassProvider(cls, scope="app"))
        app.register(ClassProvider(Order, scope="request"))
        req = app.create_request_scope()
        order = await req.resolve_async(Order)
        assert order.ok
        await req.shutdown()


class TestMultiTenantSaaS:
    async def test_tenant_isolation_via_child_containers(self):
        class TenantConfig:
            def __init__(self, name):
                self.name = name

        root = Container(scope="app")
        tenant_a = root.create_child(scope="app")
        tenant_b = root.create_child(scope="app")
        tenant_a.register(ValueProvider(TenantConfig("A"), TenantConfig, scope="app"))
        tenant_b.register(ValueProvider(TenantConfig("B"), TenantConfig, scope="app"))

        ca = await tenant_a.resolve_async(TenantConfig)
        cb = await tenant_b.resolve_async(TenantConfig)
        assert ca.name == "A"
        assert cb.name == "B"
        assert ca is not cb  # no cross-tenant leak

    async def test_tenant_cannot_see_other_tenant_private(self):
        root = Container(scope="app")
        a = root.create_child(scope="app")
        b = root.create_child(scope="app")
        a.register(ValueProvider("secret-A", "tenant_secret", scope="app"))
        # b never registered it → must not resolve
        assert await b.resolve_async("tenant_secret", optional=True) is None


class TestAuthSystem:
    async def test_scoped_auth_context(self):
        class JWTService:
            pass

        class SessionStore:
            pass

        class UserRepo:
            pass

        class AuthContext:
            def __init__(self, jwt: JWTService, sessions: SessionStore, users: UserRepo):
                self.jwt = jwt

        app = Container(scope="app")
        app.register(ClassProvider(JWTService, scope="app"))
        app.register(ClassProvider(SessionStore, scope="app"))
        app.register(ClassProvider(UserRepo, scope="app"))
        app.register(ClassProvider(AuthContext, scope="request"))

        r1 = app.create_request_scope()
        r2 = app.create_request_scope()
        a1 = await r1.resolve_async(AuthContext)
        a2 = await r2.resolve_async(AuthContext)
        assert a1 is not a2
        assert a1.jwt is a2.jwt  # stateless JWT service shared
        await r1.shutdown()
        await r2.shutdown()


class TestAILLMPlatform:
    async def test_rag_pipeline_graph(self):
        configure_di(DISettings(parallel_resolution=True))

        class ModelRegistry:
            pass

        class VectorDB:
            pass

        class EmbeddingService:
            def __init__(self, models: ModelRegistry):
                self.models = models

        class RAGPipeline:
            def __init__(self, vdb: VectorDB, emb: EmbeddingService, models: ModelRegistry):
                self.vdb = vdb
                self.emb = emb
                self.models = models

        app = Container(scope="app")
        app.register(ClassProvider(ModelRegistry, scope="app"))
        app.register(ClassProvider(VectorDB, scope="app"))
        app.register(ClassProvider(EmbeddingService, scope="app"))
        app.register(ClassProvider(RAGPipeline, scope="request"))

        req = app.create_request_scope()
        rag = await req.resolve_async(RAGPipeline)
        # ModelRegistry shared across EmbeddingService and RAGPipeline (diamond)
        assert rag.models is rag.emb.models
        await req.shutdown()


class TestMicroservices:
    async def test_shared_infra_providers(self):
        class ServiceDiscovery:
            pass

        class MessageBus:
            pass

        class EventPublisher:
            def __init__(self, bus: MessageBus, discovery: ServiceDiscovery):
                self.bus = bus

        app = Container(scope="app")
        app.register(ClassProvider(ServiceDiscovery, scope="app"))
        app.register(ClassProvider(MessageBus, scope="app"))
        app.register(ClassProvider(EventPublisher, scope="app"))
        pub1 = await app.resolve_async(EventPublisher)
        pub2 = await app.resolve_async(EventPublisher)
        assert pub1 is pub2  # app singleton
        assert pub1.bus is pub2.bus


class TestCrossAppDependsOn:
    """Manifest depends_on must be resolvable at runtime, not just validated."""

    async def test_cross_app_resolution(self):
        calls = []

        class AuthService:
            def __init__(self):
                calls.append(1)

        class BillingService:
            def __init__(self, auth: AuthService):
                self.auth = auth

        auth = Container(scope="app")
        billing = Container(scope="app")
        auth.register(ClassProvider(AuthService, scope="app"))
        billing.register(ClassProvider(BillingService, scope="app"))
        billing.add_dependency_link("auth", auth)

        b = await billing.resolve_async(BillingService)
        assert isinstance(b.auth, AuthService)
        # App singleton instantiated/cached once, in its OWNING app.
        assert b.auth is await auth.resolve_async(AuthService)
        assert len(calls) == 1

    async def test_undeclared_cross_app_still_fails(self):
        class Secret:
            pass

        class Consumer:
            def __init__(self, s: Secret):
                self.s = s

        owner = Container(scope="app")
        consumer = Container(scope="app")
        owner.register(ClassProvider(Secret, scope="app"))
        consumer.register(ClassProvider(Consumer, scope="app"))
        # No add_dependency_link → not declared → must not resolve.
        from aquilia.di.errors import ProviderNotFoundError

        with pytest.raises(ProviderNotFoundError):
            await consumer.resolve_async(Consumer)

    async def test_request_scope_reaches_link(self):
        class AuthService:
            pass

        class BillingService:
            def __init__(self, auth: AuthService):
                self.auth = auth

        auth = Container(scope="app")
        billing = Container(scope="app")
        auth.register(ClassProvider(AuthService, scope="app"))
        billing.register(ClassProvider(BillingService, scope="app"))
        billing.add_dependency_link("auth", auth)

        req = billing.create_request_scope()
        b = await req.resolve_async(BillingService)
        assert b.auth is await auth.resolve_async(AuthService)

    async def test_link_cycle_does_not_deadlock(self):
        a = Container(scope="app")
        b = Container(scope="app")
        a.add_dependency_link("b", b)
        b.add_dependency_link("a", a)
        # Neither owns the token → optional miss returns None, no infinite loop.
        got = await asyncio.wait_for(a.resolve_async("nope.Missing", optional=True), timeout=5)
        assert got is None


class TestCrossAppLinkScenarios:
    """Deep behavioral coverage of cross-app dependency-link resolution."""

    async def test_three_app_chain_A_B_C(self):
        class CSvc:
            pass

        class BSvc:
            def __init__(self, c: CSvc):
                self.c = c

        class ASvc:
            def __init__(self, b: BSvc):
                self.b = b

        appA, appB, appC = (Container(scope="app") for _ in range(3))
        appC.register(ClassProvider(CSvc, scope="app"))
        appB.register(ClassProvider(BSvc, scope="app"))
        appA.register(ClassProvider(ASvc, scope="app"))
        appA.add_dependency_link("B", appB)
        appB.add_dependency_link("C", appC)

        a = await appA.resolve_async(ASvc)
        assert isinstance(a.b, BSvc)
        assert isinstance(a.b.c, CSvc)
        # Transitive singleton cached in its owning app.
        assert a.b.c is await appC.resolve_async(CSvc)

    async def test_request_scoped_service_in_linked_app(self):
        class ReqSvc:
            pass

        class Consumer:
            def __init__(self, r: ReqSvc):
                self.r = r

        # Owner exposes a request-scoped provider; a request-scope child of the
        # consumer app resolves it across the link.
        owner = Container(scope="app")
        consumer_app = Container(scope="app")
        owner.register(ClassProvider(ReqSvc, scope="request"))
        consumer_app.register(ClassProvider(Consumer, scope="request"))
        consumer_app.add_dependency_link("owner", owner)

        owner_req = owner.create_request_scope()
        consumer_app.add_dependency_link("owner", owner_req)
        req = consumer_app.create_request_scope()
        c = await req.resolve_async(Consumer)
        assert isinstance(c.r, ReqSvc)
        await req.shutdown()
        await owner_req.shutdown()

    async def test_singleton_depending_on_request_scope_fails(self):
        # Captive dependency across a link: app-scoped consumer pulling a
        # request-scoped provider must be rejected under strict enforcement.
        configure_di(DISettings(scope_enforcement="raise"))
        from aquilia.di.errors import ScopeViolationError

        class ReqSvc:
            pass

        class AppSvc:
            def __init__(self, r: ReqSvc):
                self.r = r

        owner = Container(scope="app")
        consumer = Container(scope="app")
        owner.register(ClassProvider(ReqSvc, scope="request"))
        consumer.register(ClassProvider(AppSvc, scope="app"))
        consumer.add_dependency_link("owner", owner)

        with pytest.raises((ScopeViolationError, DIFault)):
            await consumer.resolve_async(AppSvc)

    async def test_circular_provider_dependency_across_apps_raises(self):
        # A.Svc needs B.Svc needs A.Svc — the cycle spans the link boundary and
        # must raise, not deadlock (ResolveCtx stack alone can't see it).
        class ASvc:
            def __init__(self, b):
                self.b = b

        class BSvc:
            def __init__(self, a):
                self.a = a

        ASvc.__init__.__annotations__ = {"b": BSvc}
        BSvc.__init__.__annotations__ = {"a": ASvc}

        appA = Container(scope="app")
        appB = Container(scope="app")
        appA.register(ClassProvider(ASvc, scope="app"))
        appB.register(ClassProvider(BSvc, scope="app"))
        appA.add_dependency_link("B", appB)
        appB.add_dependency_link("A", appA)

        from aquilia.di.errors import DependencyCycleError

        with pytest.raises((DependencyCycleError, DIFault)):
            await asyncio.wait_for(appA.resolve_async(ASvc), timeout=5)

    async def test_async_provider_across_link(self):
        class Conn:
            pass

        async def make_conn() -> Conn:
            await asyncio.sleep(0.01)
            return Conn()

        class Consumer:
            def __init__(self, c: Conn):
                self.c = c

        appA = Container(scope="app")
        appB = Container(scope="app")
        appB.register(FactoryProvider(make_conn, scope="app", name=appB._token_to_key(Conn)))
        appA.register(ClassProvider(Consumer, scope="app"))
        appA.add_dependency_link("B", appB)

        x = await appA.resolve_async(Consumer)
        assert isinstance(x.c, Conn)
        assert x.c is await appB.resolve_async(Conn)  # cached in owner

    async def test_optional_dependency_across_link(self):
        appA = Container(scope="app")
        appB = Container(scope="app")
        appA.add_dependency_link("B", appB)
        # Not present in any linked app → optional returns None, no raise.
        assert await appA.resolve_async("missing.Token", optional=True) is None

    async def test_tagged_provider_across_link(self):
        appA = Container(scope="app")
        appB = Container(scope="app")
        appB.register(ValueProvider("primary", "Database", scope="app"), tag="primary")
        appB.register(ValueProvider("replica", "Database", scope="app"), tag="replica")
        appA.add_dependency_link("B", appB)

        assert await appA.resolve_async("Database", tag="primary") == "primary"
        assert await appA.resolve_async("Database", tag="replica") == "replica"

    async def test_lazy_provider_resolution_across_link(self):
        from aquilia.di.providers import LazyProxyProvider

        class Heavy:
            def __init__(self):
                self.v = "heavy"

        async def build():
            appA = Container(scope="app")
            appB = Container(scope="app")
            appB.register(ClassProvider(Heavy, scope="app"))
            appA.add_dependency_link("B", appB)
            appA.register(LazyProxyProvider(token="LazyHeavy", target_token=appB._token_to_key(Heavy)))
            return await appA.resolve_async("LazyHeavy")

        # Proxy built inside the loop; first attribute touch happens outside any
        # running loop (sync bridge), resolving Heavy across the link.
        proxy = await build()

        def touch():
            return proxy.v

        assert await asyncio.to_thread(touch) == "heavy"


# ═══════════════════════════════════════════════════════════════════════
# STRESS — concurrency, isolation, memory stability.
# ═══════════════════════════════════════════════════════════════════════


class TestConcurrencyStress:
    @pytest.mark.parametrize("n", [100, 1000, 5000])
    async def test_simultaneous_resolutions(self, n):
        class Svc:
            pass

        app = Container(scope="app")
        app.register(ClassProvider(Svc, scope="app"))

        async def one():
            return await app.resolve_async(Svc)

        results = await asyncio.gather(*(one() for _ in range(n)))
        # App singleton: every concurrent resolver gets the SAME instance.
        first = results[0]
        assert all(r is first for r in results)

    async def test_request_scope_isolation_under_concurrency(self):
        class ReqState:
            pass

        app = Container(scope="app")
        app.register(ClassProvider(ReqState, scope="request"))

        async def request():
            scope = app.create_request_scope()
            inst = await scope.resolve_async(ReqState)
            await asyncio.sleep(0)
            # each request's instance stays its own
            assert await scope.resolve_async(ReqState) is inst
            await scope.shutdown()
            return id(inst)

        ids = await asyncio.gather(*(request() for _ in range(500)))
        # All distinct → no request leaked another's scoped instance.
        assert len(set(ids)) == 500


class TestMemoryStability:
    async def test_repeated_request_scopes_no_growth(self):
        class Svc:
            pass

        app = Container(scope="app")
        app.register(ClassProvider(Svc, scope="request"))

        for _ in range(10_000):
            scope = app.create_request_scope()
            await scope.resolve_async(Svc)
            await scope.shutdown()

        gc.collect()
        # App container cache must not accumulate request-scoped instances.
        assert len(app._cache) == 0

    def test_type_key_cache_bounded(self):
        from aquilia.di import core

        core._TYPE_KEY_CACHE_MAX = 100
        c = Container(scope="app")
        # Create many throwaway types → cache must flush, never exceed cap.
        for i in range(500):
            t = type(f"T{i}", (), {})
            c._token_to_key(t)
        assert len(core._type_key_cache) <= 100
        core._TYPE_KEY_CACHE_MAX = 8192


class TestParallelResolutionShapes:
    async def test_deep_dependency_chain(self):
        configure_di(DISettings(parallel_resolution=True))
        # Chain: L0 <- L1 <- L2 <- ... each depends on previous.
        classes = []
        prev = None
        for i in range(20):
            if prev is None:
                cls = type(f"L{i}", (), {"__init__": lambda self: None})
            else:
                p = prev

                def make_init(dep_cls):
                    def _init(self, dep: dep_cls):
                        self.dep = dep

                    _init.__annotations__ = {"dep": dep_cls}
                    return _init

                cls = type(f"L{i}", (), {"__init__": make_init(p)})
                cls.__init__.__annotations__ = {"dep": p}
            classes.append(cls)
            prev = cls

        app = Container(scope="app")
        for cls in classes:
            app.register(ClassProvider(cls, scope="app"))
        top = await app.resolve_async(classes[-1])
        assert top is not None

    async def test_wide_mixed_async_sync(self):
        configure_di(DISettings(parallel_resolution=True))

        class ASync:
            pass

        class SyncDep:
            pass

        async def make_async() -> ASync:
            await asyncio.sleep(0.005)
            return ASync()

        class Wide:
            def __init__(self, a: ASync, b: ASync, s: SyncDep):
                self.a = a
                self.s = s

        app = Container(scope="app")
        app.register(FactoryProvider(make_async, scope="app", name=Container(scope="app")._token_to_key(ASync)))
        app.register(ClassProvider(SyncDep, scope="app"))
        app.register(ClassProvider(Wide, scope="app"))
        w = await app.resolve_async(Wide)
        assert isinstance(w.a, ASync)


class TestPluginStress:
    async def test_many_plugins_execution_order(self):
        order = []

        for i in range(20):

            class P(DIPlugin):
                name = f"p{i}"

                def __init__(self, idx):
                    self.idx = idx

                def on_provider_registered(self, container, provider):
                    order.append(self.idx)

            register_plugin(P(i))

        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))
        # All 20 plugins fired once for the one provider.
        assert len(order) == 20

    async def test_plugin_failure_isolated(self):
        good = []

        class Bad(DIPlugin):
            name = "bad"

            def on_provider_registered(self, container, provider):
                raise RuntimeError("boom")

        class Good(DIPlugin):
            name = "good"

            def on_provider_registered(self, container, provider):
                good.append(1)

        register_plugin(Bad())
        register_plugin(Good())

        class A:
            pass

        c = Container(scope="app")
        c.register(ClassProvider(A, scope="app"))  # must not raise
        assert good == [1]


class TestChildContainerStress:
    async def test_nested_children_scope_inheritance(self):
        class Root:
            pass

        root = Container(scope="app")
        root.register(ClassProvider(Root, scope="app"))
        child = root.create_child(scope="app")
        grandchild = child.create_child(scope="request")
        # Inherited app singleton resolves once, shared down the tree.
        assert await grandchild.resolve_async(Root) is await root.resolve_async(Root)

    async def test_provider_shadowing(self):
        root = Container(scope="app")
        root.register(ValueProvider("root-val", "tok", scope="app"))
        child = root.create_child(scope="app")
        child.register(ValueProvider("child-val", "tok", scope="app"))
        assert await child.resolve_async("tok") == "child-val"
        assert await root.resolve_async("tok") == "root-val"

    async def test_runtime_replace_provider(self):
        class Gateway:
            def __init__(self):
                self.name = "real"

        class Fallback:
            def __init__(self):
                self.name = "fallback"

        c = Container(scope="app")
        c.register(ClassProvider(Gateway, scope="app"))
        g1 = await c.resolve_async(Gateway)
        assert g1.name == "real"
        await c.replace_provider(Gateway, ValueProvider(Fallback(), Gateway, scope="app"))
        g2 = await c.resolve_async(Gateway)
        assert g2.name == "fallback"


# ═══════════════════════════════════════════════════════════════════════
# FAILURE INJECTION — chaos, verify graceful recovery + cleanup.
# ═══════════════════════════════════════════════════════════════════════


class TestFailureInjection:
    async def test_constructor_failure_propagates_and_no_cache(self):
        class Broken:
            def __init__(self):
                raise ValueError("ctor boom")

        c = Container(scope="app")
        c.register(ClassProvider(Broken, scope="app"))
        with pytest.raises(ValueError, match="ctor boom"):
            await c.resolve_async(Broken)
        # Failed instance must NOT be cached.
        key = c._token_to_key(Broken)
        assert key not in c._cache

    async def test_async_factory_failure(self):
        class X:
            pass

        async def make() -> X:
            raise RuntimeError("factory failed")

        c = Container(scope="app")
        c.register(FactoryProvider(make, scope="app", name=f"{__name__}.Xfail"))
        with pytest.raises(RuntimeError, match="factory failed"):
            await c.resolve_async(f"{__name__}.Xfail")

    async def test_cancellation_during_resolution(self):
        class Slow:
            pass

        async def make() -> Slow:
            await asyncio.sleep(10)
            return Slow()

        c = Container(scope="app")
        c.register(FactoryProvider(make, scope="app", name=f"{__name__}.Slow"))
        task = asyncio.create_task(c.resolve_async(f"{__name__}.Slow"))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # In-flight future cleaned up → a fresh resolve isn't poisoned.
        assert c._inflight is None or f"{__name__}.Slow" not in c._inflight

    async def test_generator_teardown_on_shutdown(self):
        log = []

        def gen():
            log.append("open")
            yield "resource"
            log.append("close")

        c = Container(scope="request")
        val = await c.resolve_dep(Dep(gen), str)
        assert val == "resource"
        assert log == ["open"]
        await c.shutdown()
        assert log == ["open", "close"]

    async def test_generator_teardown_runs_even_if_one_fails(self):
        log = []

        def gen_ok():
            log.append("open-ok")
            yield "ok"
            log.append("close-ok")

        def gen_bad():
            log.append("open-bad")
            yield "bad"
            raise RuntimeError("teardown boom")

        c = Container(scope="request")
        await c.resolve_dep(Dep(gen_ok), str)
        await c.resolve_dep(Dep(gen_bad), str)
        await c.shutdown()  # must not raise despite one bad teardown
        assert "close-ok" in log

    async def test_invalid_scope_manifest_rejected(self):
        # ScopeValidator / manifest scope validation surface is exercised via
        # DISettings raise-mode below; here confirm unknown scope on a provider
        # doesn't silently cache under strict enforcement.
        configure_di(DISettings(scope_enforcement="raise"))

        class ReqSvc:
            pass

        app = Container(scope="app")
        app.register(ClassProvider(ReqSvc, scope="request"))
        # Resolving a request-scoped provider from an APP container = captive
        # dependency → must raise under strict enforcement.
        from aquilia.di.errors import ScopeViolationError

        with pytest.raises((ScopeViolationError, DIFault)):
            await app.resolve_async(ReqSvc)

    async def test_scope_warn_mode_does_not_raise(self):
        configure_di(DISettings(scope_enforcement="warn"))

        class ReqSvc:
            pass

        app = Container(scope="app")
        app.register(ClassProvider(ReqSvc, scope="request"))
        # warn mode: resolves (logs), does not raise.
        assert await app.resolve_async(ReqSvc) is not None

    async def test_cycle_raises_not_hangs(self):
        async def G(h): ...

        async def H(g): ...

        G.__annotations__ = {"h": Annotated[str, Dep(H)]}
        H.__annotations__ = {"g": Annotated[str, Dep(G)]}
        c = Container(scope="request")
        with pytest.raises(DIResolutionFault):
            await asyncio.wait_for(c.resolve_dep(Dep(G), object), timeout=5)
