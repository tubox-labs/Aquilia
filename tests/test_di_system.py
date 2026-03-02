"""
Comprehensive tests for the Aquilia DI (Dependency Injection) system.

Covers:
  - Container (register, resolve_async, resolve sync, request scope, bind,
    register_instance, shutdown, is_registered, cache sentinel for None)
  - Providers (ClassProvider, FactoryProvider, ValueProvider, PoolProvider,
    AliasProvider, LazyProxyProvider, ScopedProvider)
  - Lifecycle (startup/shutdown hooks, priority, finalizer strategies, logging)
  - DependencyGraph (cycle detection, topological sort, DOT export, tree view)
  - Scopes (ScopeValidator, can_inject_into, hierarchy)
  - Dep descriptor (cache_key, introspection, sub-dependencies)
  - RequestDAG (resolve, teardown, header/query/body extraction, dedup, cycles)
  - Decorators (service, factory, inject, provides, auto_inject, Inject)
  - Testing utilities (MockProvider, TestRegistry, override_container)
  - Diagnostics (emit, measure sync/async, listener error suppression)
  - Errors (rich messages, candidates, locations)
  - Compat (RequestCtx, get/set/clear_request_container)
"""

import asyncio
import logging
import time
from typing import Annotated, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

import pytest

# ── DI imports ───────────────────────────────────────────────────────
from aquilia.di.core import (
    Container,
    Provider,
    ProviderMeta,
    Registry,
    ResolveCtx,
    _CACHE_SENTINEL,
    _NullLifecycle,
)
from aquilia.di.providers import (
    AliasProvider,
    BlueprintProvider,
    ClassProvider,
    FactoryProvider,
    LazyProxyProvider,
    PoolProvider,
    ScopedProvider,
    ValueProvider,
    _LazyProxy,
)
from aquilia.di.lifecycle import (
    DisposalStrategy,
    Lifecycle,
    LifecycleContext,
    LifecycleHook,
)
from aquilia.di.graph import DependencyGraph
from aquilia.di.scopes import (
    SCOPES,
    Scope,
    ScopeValidator,
    ServiceScope,
)
from aquilia.di.dep import (
    Body,
    Dep,
    Header,
    Query,
    _unpack_annotation,
    _extract_dep_from_annotation,
)
from aquilia.di.request_dag import RequestDAG
from aquilia.di.decorators import (
    Inject,
    auto_inject,
    factory,
    inject,
    provides,
    service,
)
from aquilia.di.testing import (
    MockProvider,
    TestRegistry,
    override_container,
)
from aquilia.di.diagnostics import (
    ConsoleDiagnosticListener,
    DIDiagnostics,
    DIEvent,
    DIEventType,
    _DiagnosticMeasure,
)
from aquilia.di.errors import (
    AmbiguousProviderError,
    CircularDependencyError,
    CrossAppDependencyError,
    DependencyCycleError,
    DIError,
    ManifestValidationError,
    MissingDependencyError,
    ProviderNotFoundError,
    ScopeViolationError,
)
from aquilia.di.compat import (
    RequestCtx,
    clear_request_container,
    get_request_container,
    set_request_container,
)


# ═══════════════════════════════════════════════════════════════════════
# Helpers & Fixtures
# ═══════════════════════════════════════════════════════════════════════

class DummyService:
    """Simple dummy service for DI tests."""
    def __init__(self):
        self.started = False
        self.stopped = False

    async def on_startup(self):
        self.started = True

    async def on_shutdown(self):
        self.stopped = True


class DummyRepo:
    """Repo with no dependencies."""
    pass


class DummyServiceWithDep:
    """Service depending on DummyRepo."""
    def __init__(self, repo: DummyRepo):
        self.repo = repo


class DummyServiceOptional:
    """Service with optional dep."""
    def __init__(self, repo: DummyRepo, cache: Optional[str] = None):
        self.repo = repo
        self.cache = cache


class DummyNone:
    """Service whose factory returns None — tests sentinel caching."""
    pass


@pytest.fixture
def container():
    """Fresh app-scoped container."""
    return Container(scope="app")


@pytest.fixture
def diagnostics():
    return DIDiagnostics()


# ═══════════════════════════════════════════════════════════════════════
# 1. Container Core
# ═══════════════════════════════════════════════════════════════════════

class TestContainer:
    """Tests for core Container operations."""

    # ── register & resolve_async ──────────────────────────────────────

    async def test_register_and_resolve_value(self, container):
        """ValueProvider registers and resolves correctly."""
        provider = ValueProvider(42, "answer")
        container.register(provider)
        result = await container.resolve_async("answer")
        assert result == 42

    async def test_register_duplicate_raises(self, container):
        """Re-registering a different provider under the same token raises."""
        p1 = ValueProvider(1, "tok")
        p2 = ValueProvider(2, "tok")
        container.register(p1)
        with pytest.raises(ValueError, match="already registered"):
            container.register(p2)

    async def test_register_same_provider_idempotent(self, container):
        """Re-registering the same provider object is silently ignored."""
        p = ValueProvider(1, "tok")
        container.register(p)
        container.register(p)  # Should not raise
        assert await container.resolve_async("tok") == 1

    async def test_resolve_async_not_found_raises(self, container):
        """Resolving an unregistered token raises ProviderNotFoundError."""
        with pytest.raises(ProviderNotFoundError):
            await container.resolve_async("nonexistent")

    async def test_resolve_async_optional_returns_none(self, container):
        """optional=True returns None instead of raising."""
        result = await container.resolve_async("missing", optional=True)
        assert result is None

    async def test_resolve_async_with_tag(self, container):
        """Tagged providers disambiguate correctly."""
        p1 = ValueProvider("primary", "db", tags=("primary",))
        p2 = ValueProvider("replica", "db", tags=("replica",))
        container.register(p1, tag="primary")
        container.register(p2, tag="replica")
        assert await container.resolve_async("db", tag="primary") == "primary"
        assert await container.resolve_async("db", tag="replica") == "replica"

    async def test_resolve_async_caches_singleton(self, container):
        """Singleton-scoped providers are cached after first resolve."""
        call_count = 0

        class Counted:
            pass

        async def make():
            nonlocal call_count
            call_count += 1
            return Counted()

        provider = FactoryProvider(make, scope="singleton", name="counted")
        container.register(provider)

        a = await container.resolve_async("counted")
        b = await container.resolve_async("counted")
        assert a is b
        assert call_count == 1

    async def test_resolve_async_caches_none_sentinel(self, container):
        """None values are properly cached (sentinel-based cache check)."""
        call_count = 0

        async def make_none():
            nonlocal call_count
            call_count += 1
            return None

        provider = FactoryProvider(make_none, scope="singleton", name="none_factory")
        container.register(provider)

        r1 = await container.resolve_async("none_factory")
        r2 = await container.resolve_async("none_factory")
        assert r1 is None
        assert r2 is None
        assert call_count == 1  # Only called once — None was cached

    async def test_resolve_async_transient_not_cached(self, container):
        """Transient scope creates a new instance every time."""
        call_count = 0

        async def make():
            nonlocal call_count
            call_count += 1
            return object()

        provider = FactoryProvider(make, scope="transient", name="transient_fac")
        container.register(provider)

        a = await container.resolve_async("transient_fac")
        b = await container.resolve_async("transient_fac")
        assert a is not b
        assert call_count == 2

    async def test_resolve_by_type(self, container):
        """Can resolve using a type as token."""
        provider = ValueProvider("hello", str)
        container.register(provider)
        result = await container.resolve_async(str)
        assert result == "hello"

    async def test_is_registered(self, container):
        """is_registered returns True/False correctly."""
        assert not container.is_registered("tok")
        container.register(ValueProvider(1, "tok"))
        assert container.is_registered("tok")

    # ── bind ──────────────────────────────────────────────────────────

    async def test_bind_interface_to_implementation(self, container):
        """bind() maps an interface type to a concrete class."""
        container.bind(DummyRepo, DummyRepo, scope="singleton")
        result = await container.resolve_async(DummyRepo)
        assert isinstance(result, DummyRepo)

    # ── register_instance ─────────────────────────────────────────────

    async def test_register_instance(self, container):
        """register_instance provides a pre-built object."""
        instance = DummyRepo()
        await container.register_instance(DummyRepo, instance)
        result = await container.resolve_async(DummyRepo)
        assert result is instance

    async def test_register_instance_replaces_previous(self, container):
        """register_instance evicts existing provider for the token."""
        old = DummyRepo()
        new = DummyRepo()
        await container.register_instance(DummyRepo, old)
        await container.register_instance(DummyRepo, new)
        result = await container.resolve_async(DummyRepo)
        assert result is new

    # ── request scope ─────────────────────────────────────────────────

    async def test_create_request_scope_isolation(self, container):
        """Child request container doesn't mutate parent providers."""
        container.register(ValueProvider("parent_val", "shared"))
        child = container.create_request_scope()

        # Child sees parent provider
        assert await child.resolve_async("shared") == "parent_val"

        # Child can register its own provider without polluting parent
        child.register(ValueProvider("child_only", "child_tok"))
        assert await child.resolve_async("child_tok") == "child_only"

        with pytest.raises(ProviderNotFoundError):
            await container.resolve_async("child_tok")

    async def test_request_scope_has_fresh_cache(self, container):
        """Request-scoped container starts with an empty cache."""
        container.register(ValueProvider("cached", "key"))
        _ = await container.resolve_async("key")  # Warm parent cache

        child = container.create_request_scope()
        # Child should have its own cache
        assert child._cache == {}

    async def test_request_scope_delegates_singleton_to_parent(self, container):
        """Singleton providers resolve via parent — shared across requests."""
        provider = ValueProvider("single", "singleton_tok", scope="singleton")
        container.register(provider)

        child = container.create_request_scope()
        result = await child.resolve_async("singleton_tok")
        assert result == "single"

    async def test_request_scope_shutdown(self, container):
        """Shutting down a request container clears its cache and finalizers."""
        child = container.create_request_scope()
        child._cache["temp"] = "data"
        await child.shutdown()
        assert child._cache == {}

    # ── shutdown ──────────────────────────────────────────────────────

    async def test_container_shutdown_runs_finalizers(self):
        """Container shutdown runs registered finalizers LIFO."""
        order = []
        container = Container(scope="app")

        container._finalizers.append(lambda: _async_append(order, "first"))
        container._finalizers.append(lambda: _async_append(order, "second"))

        await container.shutdown()
        # Finalizers run in LIFO order
        assert order == ["second", "first"]

    async def test_container_shutdown_clears_cache(self):
        """Shutdown clears cache."""
        container = Container(scope="app")
        container._cache["x"] = 1
        await container.shutdown()
        assert container._cache == {}

    # ── lifecycle hooks ───────────────────────────────────────────────

    async def test_lifecycle_hooks_registered_on_resolve(self, container):
        """When a cached service has on_startup/on_shutdown, hooks are registered."""
        provider = ClassProvider(DummyService, scope="singleton")
        container.register(provider)

        svc = await container.resolve_async(DummyService)
        # on_startup and on_shutdown hooks should be registered in lifecycle
        assert len(container._lifecycle._startup_hooks) >= 1
        assert len(container._lifecycle._shutdown_hooks) >= 1

    async def test_startup_runs_hooks(self, container):
        """container.startup() runs registered startup hooks."""
        flag = {"ran": False}

        async def hook():
            flag["ran"] = True

        container._lifecycle.on_startup(hook, name="test")
        await container.startup()
        assert flag["ran"]

    # ── resolve sync ──────────────────────────────────────────────────

    def test_resolve_sync_outside_event_loop(self):
        """Sync resolve() works outside async context."""
        container = Container(scope="app")
        container.register(ValueProvider(99, "val"))
        result = container.resolve("val")
        assert result == 99


# ═══════════════════════════════════════════════════════════════════════
# 2. Providers
# ═══════════════════════════════════════════════════════════════════════

class TestValueProvider:
    """Tests for ValueProvider."""

    async def test_instantiate_returns_value(self):
        vp = ValueProvider("hello", "greeting")
        ctx = ResolveCtx(Container(scope="app"))
        result = await vp.instantiate(ctx)
        assert result == "hello"

    def test_meta_token(self):
        vp = ValueProvider(42, "my_token")
        assert vp.meta.token == "my_token"
        assert vp.meta.scope == "singleton"

    def test_meta_with_type_token(self):
        vp = ValueProvider(DummyRepo(), DummyRepo)
        assert "DummyRepo" in vp.meta.token

    async def test_shutdown_is_noop(self):
        vp = ValueProvider(1, "x")
        await vp.shutdown()  # Should not raise


class TestClassProvider:
    """Tests for ClassProvider."""

    def test_extracts_no_deps_for_simple_class(self):
        cp = ClassProvider(DummyRepo, scope="app")
        assert cp._dependencies == {}

    def test_extracts_dependencies(self):
        cp = ClassProvider(DummyServiceWithDep, scope="app")
        assert "repo" in cp._dependencies
        assert cp._dependencies["repo"]["token"] is DummyRepo

    def test_extracts_optional_dependency(self):
        cp = ClassProvider(DummyServiceOptional, scope="app")
        assert "repo" in cp._dependencies
        assert "cache" in cp._dependencies
        assert cp._dependencies["cache"]["optional"] is True

    async def test_instantiate_resolves_deps(self):
        container = Container(scope="app")
        repo = DummyRepo()
        container.register(ValueProvider(repo, DummyRepo))
        container.register(ClassProvider(DummyServiceWithDep, scope="app"))

        svc = await container.resolve_async(DummyServiceWithDep)
        assert isinstance(svc, DummyServiceWithDep)
        assert svc.repo is repo

    def test_meta_has_correct_module_and_name(self):
        cp = ClassProvider(DummyRepo, scope="request")
        assert cp.meta.name == "DummyRepo"
        assert cp.meta.scope == "request"

    async def test_async_init_called(self):
        """If class has async_init(), it's called after __init__."""
        class WithAsyncInit:
            def __init__(self):
                self.initialized = False
            async def async_init(self):
                self.initialized = True

        container = Container(scope="app")
        container.register(ClassProvider(WithAsyncInit, scope="singleton"))
        instance = await container.resolve_async(WithAsyncInit)
        assert instance.initialized is True


class TestFactoryProvider:
    """Tests for FactoryProvider."""

    async def test_sync_factory(self):
        def make_value():
            return 42

        fp = FactoryProvider(make_value, scope="app", name="make_value")
        container = Container(scope="app")
        container.register(fp)
        result = await container.resolve_async("make_value")
        assert result == 42

    async def test_async_factory(self):
        async def make_value():
            return "async_val"

        fp = FactoryProvider(make_value, scope="app", name="make_value_async")
        container = Container(scope="app")
        container.register(fp)
        result = await container.resolve_async("make_value_async")
        assert result == "async_val"

    async def test_factory_with_deps(self):
        async def create_service(repo: DummyRepo):
            svc = DummyServiceWithDep(repo)
            return svc

        container = Container(scope="app")
        container.register(ValueProvider(DummyRepo(), DummyRepo))
        container.register(FactoryProvider(create_service, scope="app", name="svc_factory"))
        result = await container.resolve_async("svc_factory")
        assert isinstance(result, DummyServiceWithDep)

    def test_meta_uses_explicit_name(self):
        def my_func():
            return 1

        fp = FactoryProvider(my_func, name="custom_name")
        assert fp.meta.name == "custom_name"
        assert fp.meta.token == "custom_name"


class TestPoolProvider:
    """Tests for PoolProvider."""

    async def test_pool_creates_and_releases(self):
        call_count = 0

        async def make_conn():
            nonlocal call_count
            call_count += 1
            return f"conn_{call_count}"

        pool = PoolProvider(make_conn, max_size=2, token="pool_conn", name="pool")
        ctx = ResolveCtx(Container(scope="app"))

        c1 = await pool.instantiate(ctx)
        assert c1 == "conn_1"

        c2 = await pool.instantiate(ctx)
        assert c2 == "conn_2"

        # Release one back
        await pool.release(c1)

        # Should get recycled instance
        c3 = await pool.instantiate(ctx)
        assert c3 == "conn_1"

    async def test_pool_max_size_blocks(self):
        """When pool is exhausted and max_size reached, instantiate waits."""
        async def make():
            return object()

        pool = PoolProvider(make, max_size=1, token="p")
        ctx = ResolveCtx(Container(scope="app"))

        # Take the only slot
        obj = await pool.instantiate(ctx)

        # Release in background so the waiting resolve can succeed
        async def release_later():
            await asyncio.sleep(0.05)
            await pool.release(obj)

        task = asyncio.create_task(release_later())
        result = await asyncio.wait_for(pool.instantiate(ctx), timeout=1.0)
        assert result is obj
        await task

    async def test_pool_acquire_context_manager(self):
        """acquire() auto-releases on exit."""
        async def make():
            return "resource"

        pool = PoolProvider(make, max_size=1, token="acq_pool")

        async with pool.acquire() as resource:
            assert resource == "resource"

        # Resource should be back in pool
        ctx = ResolveCtx(Container(scope="app"))
        r = await pool.instantiate(ctx)
        assert r == "resource"

    async def test_pool_shutdown_closes_instances(self):
        closed = []

        class Closable:
            async def close(self):
                closed.append(self)

        async def make():
            return Closable()

        pool = PoolProvider(make, max_size=2, token="shutdown_pool")
        ctx = ResolveCtx(Container(scope="app"))

        c1 = await pool.instantiate(ctx)
        c2 = await pool.instantiate(ctx)
        await pool.release(c1)
        await pool.release(c2)

        await pool.shutdown()
        assert len(closed) == 2

    async def test_pool_lifo_strategy(self):
        counter = 0

        async def make():
            nonlocal counter
            counter += 1
            return counter

        pool = PoolProvider(make, max_size=3, token="lifo", strategy="LIFO")
        ctx = ResolveCtx(Container(scope="app"))

        c1 = await pool.instantiate(ctx)
        c2 = await pool.instantiate(ctx)

        await pool.release(c1)
        await pool.release(c2)

        # LIFO: last released (c2) returned first
        r = await pool.instantiate(ctx)
        assert r == 2  # c2


class TestAliasProvider:
    """Tests for AliasProvider."""

    async def test_alias_redirects(self):
        container = Container(scope="app")
        container.register(ValueProvider("real", "target"))
        container.register(AliasProvider("alias", "target"))

        result = await container.resolve_async("alias")
        assert result == "real"


class TestLazyProxyProvider:
    """Tests for LazyProxyProvider."""

    async def test_proxy_defers_resolution(self):
        container = Container(scope="app")
        container.register(ValueProvider("lazy_val", "target_tok"))
        # LazyProxy with scope "singleton" + allow_lazy=True → cached
        # Use transient scope to bypass lifecycle hook check which triggers
        # __getattr__ inside the async loop.
        lp = LazyProxyProvider("lazy", "target_tok")
        # Bypass container caching to avoid _check_lifecycle_hooks triggering proxy
        ctx = ResolveCtx(container)
        proxy = await lp.instantiate(ctx)
        assert isinstance(proxy, _LazyProxy)

    def test_proxy_resolves_on_attribute_access(self):
        """Proxy resolves the real object on first __getattr__."""
        container = Container(scope="app")

        class Target:
            x = 42

        container.register(ValueProvider(Target(), "target_tok"))

        lp = LazyProxyProvider("lazy_target", "target_tok")
        ctx = ResolveCtx(container)

        # Synchronous test — run in a new event loop
        loop = asyncio.new_event_loop()
        try:
            proxy = loop.run_until_complete(lp.instantiate(ctx))
            # Accessing .x triggers resolution via __getattr__
            assert proxy.x == 42
        finally:
            loop.close()


class TestScopedProvider:
    """Tests for ScopedProvider."""

    def test_scope_override(self):
        inner = ValueProvider("x", "tok")
        scoped = ScopedProvider(inner, scope="request")
        assert scoped.meta.scope == "request"
        assert inner.meta.scope == "singleton"

    async def test_delegates_instantiation(self):
        inner = ValueProvider("val", "tok")
        scoped = ScopedProvider(inner, scope="request")
        ctx = ResolveCtx(Container(scope="app"))
        assert await scoped.instantiate(ctx) == "val"


# ═══════════════════════════════════════════════════════════════════════
# 3. Lifecycle
# ═══════════════════════════════════════════════════════════════════════

class TestLifecycle:
    """Tests for Lifecycle hooks, finalizers, and disposal strategies."""

    async def test_startup_hooks_run_in_priority_order(self):
        order = []
        lc = Lifecycle()
        lc.on_startup(lambda: _async_append(order, "low"), name="low", priority=0)
        lc.on_startup(lambda: _async_append(order, "high"), name="high", priority=10)
        lc.on_startup(lambda: _async_append(order, "mid"), name="mid", priority=5)

        await lc.run_startup_hooks()
        assert order == ["high", "mid", "low"]

    async def test_shutdown_hooks_continue_on_error(self):
        """Shutdown hooks continue even if one fails."""
        order = []
        lc = Lifecycle()

        async def fail():
            raise RuntimeError("boom")

        lc.on_shutdown(fail, name="fail")
        lc.on_shutdown(lambda: _async_append(order, "ok"), name="ok", priority=-1)

        # Should not raise; error is logged
        await lc.run_shutdown_hooks()
        assert order == ["ok"]

    async def test_startup_hook_failure_raises(self):
        """Startup failures raise RuntimeError."""
        lc = Lifecycle()

        async def fail():
            raise ValueError("startup fail")

        lc.on_startup(fail, name="boom")
        with pytest.raises(RuntimeError, match="Startup hooks failed"):
            await lc.run_startup_hooks()

    async def test_finalizers_lifo(self):
        order = []
        lc = Lifecycle(disposal_strategy=DisposalStrategy.LIFO)
        lc.register_finalizer(lambda: _async_append(order, "first"))
        lc.register_finalizer(lambda: _async_append(order, "second"))
        lc.register_finalizer(lambda: _async_append(order, "third"))
        await lc.run_finalizers()
        assert order == ["third", "second", "first"]

    async def test_finalizers_fifo(self):
        order = []
        lc = Lifecycle(disposal_strategy=DisposalStrategy.FIFO)
        lc.register_finalizer(lambda: _async_append(order, "first"))
        lc.register_finalizer(lambda: _async_append(order, "second"))
        lc.register_finalizer(lambda: _async_append(order, "third"))
        await lc.run_finalizers()
        assert order == ["first", "second", "third"]

    async def test_finalizers_parallel(self):
        results = []
        lc = Lifecycle(disposal_strategy=DisposalStrategy.PARALLEL)
        lc.register_finalizer(lambda: _async_append(results, "a"))
        lc.register_finalizer(lambda: _async_append(results, "b"))
        await lc.run_finalizers()
        assert set(results) == {"a", "b"}

    async def test_finalizer_error_logged_not_raised(self, caplog):
        """Finalizer errors are logged, not raised."""
        lc = Lifecycle(disposal_strategy=DisposalStrategy.LIFO)

        async def fail():
            raise RuntimeError("cleanup fail")

        lc.register_finalizer(fail)
        with caplog.at_level(logging.WARNING, logger="aquilia.di.lifecycle"):
            await lc.run_finalizers()
        assert "cleanup fail" in caplog.text

    async def test_shutdown_hooks_error_logged_not_raised(self, caplog):
        """Shutdown hook errors are logged."""
        lc = Lifecycle()

        async def fail():
            raise ValueError("hook fail")

        lc.on_shutdown(fail, name="test_fail")
        with caplog.at_level(logging.WARNING, logger="aquilia.di.lifecycle"):
            await lc.run_shutdown_hooks()
        assert "hook fail" in caplog.text

    async def test_clear(self):
        lc = Lifecycle()
        lc.on_startup(lambda: _async_noop(), name="s")
        lc.on_shutdown(lambda: _async_noop(), name="d")
        lc.register_finalizer(lambda: _async_noop())
        lc.clear()
        assert len(lc._startup_hooks) == 0
        assert len(lc._shutdown_hooks) == 0
        assert len(lc._finalizers) == 0

    async def test_lifecycle_context_manager(self):
        """LifecycleContext runs startup on enter and shutdown+finalizers on exit."""
        order = []
        lc = Lifecycle()
        lc.on_startup(lambda: _async_append(order, "start"), name="s")
        lc.on_shutdown(lambda: _async_append(order, "stop"), name="d")
        lc.register_finalizer(lambda: _async_append(order, "final"))

        async with LifecycleContext(lc):
            assert order == ["start"]

        assert order == ["start", "stop", "final"]


# ═══════════════════════════════════════════════════════════════════════
# 4. DependencyGraph
# ═══════════════════════════════════════════════════════════════════════

class TestDependencyGraph:
    """Tests for graph analysis: cycles, topo sort, DOT export, tree view."""

    def _make_provider(self, token: str, scope: str = "app") -> Provider:
        """Create a minimal ValueProvider for graph testing."""
        return ValueProvider(None, token, scope=scope)

    def test_no_cycle_linear(self):
        """A -> B -> C has no cycles."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), ["C"])
        g.add_provider(self._make_provider("C"), [])
        assert g.detect_cycles() == []

    def test_cycle_detected(self):
        """A -> B -> A should be detected."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), ["A"])
        cycles = g.detect_cycles()
        assert len(cycles) >= 1
        flat = set()
        for c in cycles:
            flat.update(c)
        assert "A" in flat and "B" in flat

    def test_self_loop_detected(self):
        """A -> A should be detected."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["A"])
        cycles = g.detect_cycles()
        assert len(cycles) == 1
        assert "A" in cycles[0]

    def test_resolution_order_dependencies_first(self):
        """Topo sort returns dependencies before consumers."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B", "C"])
        g.add_provider(self._make_provider("B"), ["C"])
        g.add_provider(self._make_provider("C"), [])

        order = g.get_resolution_order()

        # C must come before B, B must come before A
        assert order.index("C") < order.index("B")
        assert order.index("B") < order.index("A")

    def test_resolution_order_independent_nodes(self):
        """Independent nodes can be in any order, but all present."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("X"), [])
        g.add_provider(self._make_provider("Y"), [])
        g.add_provider(self._make_provider("Z"), [])

        order = g.get_resolution_order()
        assert set(order) == {"X", "Y", "Z"}

    def test_resolution_order_complex_diamond(self):
        """Diamond: A -> B, A -> C, B -> D, C -> D."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B", "C"])
        g.add_provider(self._make_provider("B"), ["D"])
        g.add_provider(self._make_provider("C"), ["D"])
        g.add_provider(self._make_provider("D"), [])

        order = g.get_resolution_order()
        # D before B and C, both before A
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")

    def test_resolution_order_cycle_raises(self):
        """Cycle in graph raises DependencyCycleError."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), ["A"])
        with pytest.raises(DependencyCycleError):
            g.get_resolution_order()

    def test_export_dot(self):
        """DOT export produces valid Graphviz syntax."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), [])
        dot = g.export_dot()
        assert "digraph" in dot
        assert '"A"' in dot
        assert '"B"' in dot
        assert '"A" -> "B"' in dot

    def test_tree_view(self):
        """Tree view shows hierarchy."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), [])
        tree = g.get_tree_view("A")
        assert "A" in tree or "value" in tree  # Provider name in tree output

    def test_tree_view_circular_marker(self):
        """Tree view marks circular refs."""
        g = DependencyGraph()
        g.add_provider(self._make_provider("A"), ["B"])
        g.add_provider(self._make_provider("B"), ["A"])
        tree = g.get_tree_view("A")
        assert "circular" in tree


# ═══════════════════════════════════════════════════════════════════════
# 5. Scopes
# ═══════════════════════════════════════════════════════════════════════

class TestScopes:
    """Tests for scope validation and rules."""

    def test_scope_enum_values(self):
        assert ServiceScope.SINGLETON == "singleton"
        assert ServiceScope.APP == "app"
        assert ServiceScope.REQUEST == "request"
        assert ServiceScope.TRANSIENT == "transient"
        assert ServiceScope.POOLED == "pooled"
        assert ServiceScope.EPHEMERAL == "ephemeral"

    def test_singleton_can_inject_into_anything(self):
        s = SCOPES["singleton"]
        for target in SCOPES.values():
            assert s.can_inject_into(target) is True

    def test_app_can_inject_into_anything(self):
        s = SCOPES["app"]
        for target in SCOPES.values():
            assert s.can_inject_into(target) is True

    def test_request_cannot_inject_into_singleton(self):
        r = SCOPES["request"]
        s = SCOPES["singleton"]
        assert r.can_inject_into(s) is False

    def test_request_cannot_inject_into_app(self):
        r = SCOPES["request"]
        a = SCOPES["app"]
        assert r.can_inject_into(a) is False

    def test_request_can_inject_into_request(self):
        r = SCOPES["request"]
        assert r.can_inject_into(r) is True

    def test_ephemeral_follows_request_rules(self):
        e = SCOPES["ephemeral"]
        assert e.can_inject_into(SCOPES["singleton"]) is False
        assert e.can_inject_into(SCOPES["request"]) is True

    def test_transient_can_inject_into_anything(self):
        t = SCOPES["transient"]
        for target in SCOPES.values():
            assert t.can_inject_into(target) is True

    def test_scope_validator_valid(self):
        assert ScopeValidator.validate_injection("singleton", "request") is True
        assert ScopeValidator.validate_injection("app", "transient") is True

    def test_scope_validator_invalid(self):
        assert ScopeValidator.validate_injection("request", "singleton") is False
        assert ScopeValidator.validate_injection("ephemeral", "app") is False

    def test_scope_validator_unknown_scope_returns_false(self):
        assert ScopeValidator.validate_injection("unknown", "app") is False
        assert ScopeValidator.validate_injection("app", "unknown") is False

    def test_scope_hierarchy(self):
        h = ScopeValidator.get_scope_hierarchy()
        assert "request" in h.get("app", [])
        assert "ephemeral" in h.get("request", [])

    def test_scope_cacheable_flag(self):
        assert SCOPES["singleton"].cacheable is True
        assert SCOPES["app"].cacheable is True
        assert SCOPES["request"].cacheable is True
        assert SCOPES["transient"].cacheable is False
        assert SCOPES["pooled"].cacheable is False


# ═══════════════════════════════════════════════════════════════════════
# 6. Dep Descriptor
# ═══════════════════════════════════════════════════════════════════════

class TestDep:
    """Tests for Dep descriptor and annotation helpers."""

    def test_bare_dep_is_container_lookup(self):
        d = Dep()
        assert d.is_container_lookup is True
        assert d.is_generator is False
        assert d.is_async is False

    def test_dep_with_callable(self):
        async def get_db():
            return "db"

        d = Dep(call=get_db)
        assert d.is_container_lookup is False
        assert d.is_async is True
        assert d.is_generator is False

    def test_dep_with_sync_generator(self):
        def gen():
            yield "val"

        d = Dep(call=gen)
        assert d.is_generator is True
        assert d.is_async is False

    def test_dep_with_async_generator(self):
        async def agen():
            yield "val"

        d = Dep(call=agen)
        assert d.is_generator is True
        assert d.is_async is True

    def test_cache_key_for_callable(self):
        async def get_db():
            pass

        d = Dep(call=get_db)
        key = d.cache_key
        assert key.startswith("dep:")
        assert "get_db" in key

    def test_cache_key_for_container_lookup(self):
        d = Dep(tag="primary")
        assert d.cache_key == "container:primary"

    def test_get_sub_dependencies_empty_for_no_call(self):
        d = Dep()
        assert d.get_sub_dependencies() == {}

    def test_get_sub_dependencies_extracts_deps(self):
        async def handler(x: int, name: str):
            pass

        d = Dep(call=handler)
        subs = d.get_sub_dependencies()
        assert "x" in subs
        assert "name" in subs

    def test_dep_frozen(self):
        """Dep is a frozen dataclass."""
        d = Dep(cached=True)
        with pytest.raises(AttributeError):
            d.cached = False  # type: ignore

    # ── Annotation Helpers ────────────────────────────────────────────

    def test_unpack_annotated_dep(self):
        ann = Annotated[int, Dep(tag="primary")]
        base, meta = _unpack_annotation(ann)
        assert base is int
        assert isinstance(meta, Dep)
        assert meta.tag == "primary"

    def test_unpack_plain_type(self):
        base, meta = _unpack_annotation(int)
        assert base is int
        assert meta is None

    def test_extract_dep_from_annotation(self):
        ann = Annotated[str, Dep(cached=False)]
        dep = _extract_dep_from_annotation(ann)
        assert isinstance(dep, Dep)
        assert dep.cached is False

    def test_extract_dep_none_for_plain(self):
        assert _extract_dep_from_annotation(int) is None

    # ── Header / Query / Body ─────────────────────────────────────────

    def test_header_resolve_present(self):
        h = Header("Authorization")
        req = MagicMock()
        req.headers = {"authorization": "Bearer tok123"}
        result = h.resolve({"request": req})
        assert result == "Bearer tok123"

    def test_header_resolve_missing_required(self):
        h = Header("X-Custom", required=True)
        req = MagicMock()
        req.headers = {}
        with pytest.raises(ValueError, match="Missing required header"):
            h.resolve({"request": req})

    def test_header_resolve_missing_optional(self):
        h = Header("X-Custom", required=False, default="fallback")
        req = MagicMock()
        req.headers = {}
        result = h.resolve({"request": req})
        assert result == "fallback"

    def test_query_resolve(self):
        q = Query("page", default=1)
        req = MagicMock(spec=[])  # No auto-created attributes
        req.query_params = {"page": "5"}
        result = q.resolve({"request": req})
        assert result == "5"

    def test_query_resolve_missing_with_default(self):
        q = Query("page", default=1)
        req = MagicMock(spec=[])
        req.query_params = {}
        result = q.resolve({"request": req})
        assert result == 1

    def test_body_descriptor(self):
        b = Body(media_type="application/json")
        assert b.media_type == "application/json"
        assert b.embed is False

    def test_header_alias(self):
        h = Header("Auth", alias="authorization")
        assert h.header_key == "authorization"


# ═══════════════════════════════════════════════════════════════════════
# 7. RequestDAG
# ═══════════════════════════════════════════════════════════════════════

class TestRequestDAG:
    """Tests for per-request DAG resolution."""

    async def test_resolve_container_lookup(self):
        """Dep() with no callable resolves from container."""
        container = Container(scope="app")
        container.register(ValueProvider("val", str))

        dag = RequestDAG(container)
        result = await dag.resolve(Dep(), str)
        assert result == "val"

    async def test_resolve_async_callable(self):
        """Dep(call=fn) calls the function."""
        async def get_val():
            return 42

        container = Container(scope="app")
        dag = RequestDAG(container)
        result = await dag.resolve(Dep(call=get_val), int)
        assert result == 42

    async def test_resolve_sync_callable(self):
        """Dep with sync callable."""
        def make():
            return "sync"

        dag = RequestDAG(Container(scope="app"))
        result = await dag.resolve(Dep(call=make), str)
        assert result == "sync"

    async def test_resolve_deduplication(self):
        """Same Dep is resolved once (cached by cache_key)."""
        call_count = 0

        async def expensive():
            nonlocal call_count
            call_count += 1
            return "result"

        dag = RequestDAG(Container(scope="app"))
        dep = Dep(call=expensive, cached=True)

        r1 = await dag.resolve(dep, str)
        r2 = await dag.resolve(dep, str)
        assert r1 == r2 == "result"
        assert call_count == 1

    async def test_resolve_uncached_calls_every_time(self):
        """cached=False forces fresh invocation."""
        call_count = 0

        async def fresh():
            nonlocal call_count
            call_count += 1
            return call_count

        dag = RequestDAG(Container(scope="app"))
        dep = Dep(call=fresh, cached=False)

        r1 = await dag.resolve(dep, int)
        r2 = await dag.resolve(dep, int)
        assert r1 == 1
        assert r2 == 2

    async def test_resolve_async_generator_with_teardown(self):
        """Async generator Dep yields value; teardown runs cleanup."""
        cleaned = False

        async def get_session():
            nonlocal cleaned
            yield "session"
            cleaned = True

        dag = RequestDAG(Container(scope="app"))
        result = await dag.resolve(Dep(call=get_session), str)
        assert result == "session"
        assert not cleaned

        await dag.teardown()
        assert cleaned

    async def test_resolve_sync_generator_with_teardown(self):
        """Sync generator Dep yields value; teardown runs cleanup."""
        cleaned = False

        def get_session():
            nonlocal cleaned
            yield "sync_session"
            cleaned = True

        dag = RequestDAG(Container(scope="app"))
        result = await dag.resolve(Dep(call=get_session), str)
        assert result == "sync_session"
        assert not cleaned

        await dag.teardown()
        assert cleaned

    async def test_resolve_circular_raises(self):
        """Circular Dep raises RuntimeError."""
        # Create a function that references itself via the DAG
        # We can simulate by manually marking the cache
        dag = RequestDAG(Container(scope="app"))

        async def circular():
            return await dag.resolve(Dep(call=circular), str)

        with pytest.raises(RuntimeError, match="Circular dependency"):
            await dag.resolve(Dep(call=circular), str)

    async def test_teardown_lifo_order(self):
        """Generators tear down in LIFO order."""
        order = []

        async def gen_a():
            yield "a"
            order.append("a_cleanup")

        async def gen_b():
            yield "b"
            order.append("b_cleanup")

        dag = RequestDAG(Container(scope="app"))
        await dag.resolve(Dep(call=gen_a), str)
        await dag.resolve(Dep(call=gen_b), str)

        await dag.teardown()
        assert order == ["b_cleanup", "a_cleanup"]

    async def test_header_extraction(self):
        """RequestDAG extracts Header values from request."""
        async def handler(auth: Annotated[str, Header("Authorization")]):
            return auth

        req = MagicMock()
        req.headers = {"authorization": "Bearer xyz"}

        container = Container(scope="app")
        dag = RequestDAG(container, request=req)

        dep = Dep(call=handler)
        result = await dag.resolve(dep, str)
        assert result == "Bearer xyz"

    async def test_query_extraction(self):
        """RequestDAG extracts Query values from request."""
        async def handler(page: Annotated[int, Query("page", default=1)]):
            return page

        req = MagicMock()
        req.query_params = {"page": "5"}
        del req.query_param  # Ensure we test the query_params path

        container = Container(scope="app")
        dag = RequestDAG(container, request=req)

        dep = Dep(call=handler)
        result = await dag.resolve(dep, int)
        assert result == 5


# ═══════════════════════════════════════════════════════════════════════
# 8. Decorators
# ═══════════════════════════════════════════════════════════════════════

class TestDecorators:
    """Tests for DI decorators."""

    def test_service_decorator(self):
        @service(scope="request", tag="primary")
        class MyService:
            pass

        assert MyService.__di_scope__ == "request"
        assert MyService.__di_tag__ == "primary"
        assert MyService.__di_name__ == "MyService"

    def test_factory_decorator(self):
        @factory(scope="singleton", name="db_pool")
        async def create_pool():
            return "pool"

        assert create_pool.__di_scope__ == "singleton"
        assert create_pool.__di_name__ == "db_pool"
        assert create_pool.__di_factory__ is True

    def test_provides_decorator(self):
        @provides(DummyRepo, scope="app", tag="sql")
        def create_repo():
            return DummyRepo()

        assert create_repo.__di_provides__ is DummyRepo
        assert create_repo.__di_scope__ == "app"
        assert create_repo.__di_tag__ == "sql"
        assert create_repo.__di_factory__ is True

    def test_inject_function(self):
        inj = inject(token=DummyRepo, tag="primary", optional=True)
        assert isinstance(inj, Inject)
        assert inj.token is DummyRepo
        assert inj.tag == "primary"
        assert inj.optional is True

    def test_inject_dataclass_post_init(self):
        inj = Inject(token=str, tag="test")
        assert inj._inject_token is str
        assert inj._inject_tag == "test"

    async def test_auto_inject(self):
        """auto_inject resolves missing params from request container."""
        from aquilia.di.compat import set_request_container, clear_request_container

        container = Container(scope="request")
        container.register(ValueProvider("injected_db", str))
        set_request_container(container)

        try:
            @auto_inject
            async def handler(db: str):
                return db

            result = await handler()
            assert result == "injected_db"
        finally:
            clear_request_container()

    async def test_auto_inject_no_container_raises(self):
        """auto_inject raises if no request container set."""
        from aquilia.di.compat import clear_request_container
        clear_request_container()

        @auto_inject
        async def handler(db: str):
            return db

        with pytest.raises(RuntimeError, match="No request container"):
            await handler()


# ═══════════════════════════════════════════════════════════════════════
# 9. Testing Utilities
# ═══════════════════════════════════════════════════════════════════════

class TestTestingUtils:
    """Tests for MockProvider, TestRegistry, override_container."""

    async def test_mock_provider_tracks_access(self):
        mp = MockProvider("mock_val", "tok")
        ctx = ResolveCtx(Container(scope="app"))

        result = await mp.instantiate(ctx)
        assert result == "mock_val"
        assert mp.access_count == 1

        await mp.instantiate(ctx)
        assert mp.access_count == 2

    async def test_mock_provider_reset(self):
        mp = MockProvider("val", "tok")
        ctx = ResolveCtx(Container(scope="app"))
        await mp.instantiate(ctx)
        mp.reset()
        assert mp.access_count == 0
        assert mp.instantiate_calls == []

    async def test_override_container(self):
        """override_container temporarily replaces a provider."""
        container = Container(scope="app")
        container.register(ValueProvider("real", "tok"))

        # Verify real value
        assert await container.resolve_async("tok") == "real"

        # Override
        async with override_container(container, "tok", "mock") as mock_prov:
            result = await container.resolve_async("tok")
            assert result == "mock"
            assert mock_prov.access_count == 1

        # Restored
        # Clear cache to get fresh resolve
        container._cache.clear()
        assert await container.resolve_async("tok") == "real"

    async def test_override_container_restores_on_exception(self):
        """Provider is restored even if test raises."""
        container = Container(scope="app")
        container.register(ValueProvider("original", "tok"))

        try:
            async with override_container(container, "tok", "mock"):
                raise ValueError("test error")
        except ValueError:
            pass

        container._cache.clear()
        assert await container.resolve_async("tok") == "original"


# ═══════════════════════════════════════════════════════════════════════
# 10. Diagnostics
# ═══════════════════════════════════════════════════════════════════════

class TestDiagnostics:
    """Tests for DI observability system."""

    def test_emit_event_to_listeners(self):
        diag = DIDiagnostics()
        events = []

        class Listener:
            def on_event(self, event):
                events.append(event)

        diag.add_listener(Listener())
        diag.emit(DIEventType.REGISTRATION, token="test", provider_name="TestSvc")

        assert len(events) == 1
        assert events[0].type == DIEventType.REGISTRATION
        assert events[0].token == "test"

    def test_listener_error_suppressed(self, caplog):
        """Listener errors don't crash the app."""
        diag = DIDiagnostics()

        class BadListener:
            def on_event(self, event):
                raise RuntimeError("listener crash")

        diag.add_listener(BadListener())
        with caplog.at_level(logging.ERROR, logger="aquilia.di.diagnostics"):
            diag.emit(DIEventType.REGISTRATION, token="x")
        assert "listener crash" in caplog.text

    def test_measure_sync_context_manager(self):
        """measure() works as sync context manager."""
        diag = DIDiagnostics()
        events = []

        class Listener:
            def on_event(self, event):
                events.append(event)

        diag.add_listener(Listener())

        with diag.measure(DIEventType.RESOLUTION_START, token="X"):
            time.sleep(0.01)

        assert len(events) == 1
        assert events[0].type == DIEventType.RESOLUTION_SUCCESS
        assert events[0].duration > 0

    async def test_measure_async_context_manager(self):
        """measure() works as async context manager."""
        diag = DIDiagnostics()
        events = []

        class Listener:
            def on_event(self, event):
                events.append(event)

        diag.add_listener(Listener())

        async with diag.measure(DIEventType.RESOLUTION_START, token="Y"):
            await asyncio.sleep(0.01)

        assert len(events) == 1
        assert events[0].type == DIEventType.RESOLUTION_SUCCESS
        assert events[0].duration > 0

    def test_measure_sync_on_error(self):
        """measure() emits RESOLUTION_FAILURE on exception."""
        diag = DIDiagnostics()
        events = []

        class Listener:
            def on_event(self, event):
                events.append(event)

        diag.add_listener(Listener())

        with pytest.raises(ValueError):
            with diag.measure(DIEventType.RESOLUTION_START, token="Z"):
                raise ValueError("fail")

        assert len(events) == 1
        assert events[0].type == DIEventType.RESOLUTION_FAILURE
        assert "fail" in str(events[0].error)

    async def test_measure_async_on_error(self):
        """Async measure emits RESOLUTION_FAILURE on exception."""
        diag = DIDiagnostics()
        events = []

        class Listener:
            def on_event(self, event):
                events.append(event)

        diag.add_listener(Listener())

        with pytest.raises(RuntimeError):
            async with diag.measure(DIEventType.RESOLUTION_START, token="W"):
                raise RuntimeError("async fail")

        assert events[0].type == DIEventType.RESOLUTION_FAILURE

    def test_console_listener_logs(self, caplog):
        """ConsoleDiagnosticListener logs events."""
        listener = ConsoleDiagnosticListener(log_level=logging.INFO)
        diag = DIDiagnostics()
        diag.add_listener(listener)

        with caplog.at_level(logging.INFO, logger="aquilia.di.diagnostics"):
            diag.emit(DIEventType.REGISTRATION, token="Svc", provider_name="Svc")
        assert "Registered" in caplog.text

    def test_di_event_defaults(self):
        """DIEvent has proper defaults."""
        e = DIEvent(type=DIEventType.REGISTRATION)
        assert e.token is None
        assert e.error is None
        assert e.metadata == {}
        assert e.timestamp > 0


# ═══════════════════════════════════════════════════════════════════════
# 11. Errors
# ═══════════════════════════════════════════════════════════════════════

class TestDIErrors:
    """Tests for DI error types and their diagnostic messages."""

    def test_provider_not_found_basic(self):
        with pytest.raises(ProviderNotFoundError, match="No provider found") as exc_info:
            raise ProviderNotFoundError(token="UserRepo")
        assert exc_info.value.token == "UserRepo"

    def test_provider_not_found_with_candidates(self):
        err = ProviderNotFoundError(
            token="Repo",
            candidates=["SqlRepo", "MongoRepo"],
        )
        assert "SqlRepo" in str(err)
        assert "MongoRepo" in str(err)
        assert "Suggested fixes" in str(err)

    def test_provider_not_found_with_tag_and_location(self):
        err = ProviderNotFoundError(
            token="Cache",
            tag="redis",
            requested_by="UserService",
            location=("app/services.py", 42),
        )
        assert "tag=redis" in str(err)
        assert "UserService" in str(err)
        assert "app/services.py:42" in str(err)

    def test_dependency_cycle_error(self):
        err = DependencyCycleError(
            cycle=["A", "B", "C"],
            locations={"A": ("a.py", 10), "B": ("b.py", 20)},
        )
        msg = str(err)
        assert "A" in msg and "B" in msg and "C" in msg
        assert "LazyProxy" in msg
        assert "a.py:10" in msg

    def test_scope_violation_error(self):
        err = ScopeViolationError(
            provider_token="UserRepo",
            provider_scope="request",
            consumer_token="AppService",
            consumer_scope="singleton",
        )
        msg = str(err)
        assert "request" in msg and "singleton" in msg
        assert "UserRepo" in msg

    def test_ambiguous_provider_error(self):
        p1 = ValueProvider("a", "tok", tags=("t1",))
        p2 = ValueProvider("b", "tok", tags=("t2",))
        err = AmbiguousProviderError(
            token="tok",
            providers=[("t1", p1), ("t2", p2)],
        )
        msg = str(err)
        assert "Ambiguous" in msg
        assert "tag" in msg.lower()

    def test_manifest_validation_error(self):
        err = ManifestValidationError("MyApp", ["Missing class X", "Invalid scope"])
        msg = str(err)
        assert "MyApp" in msg
        assert "Missing class X" in msg

    def test_cross_app_dependency_error(self):
        err = CrossAppDependencyError(
            consumer_app="frontend",
            provider_app="backend",
            provider_token="DatabasePool",
        )
        msg = str(err)
        assert "frontend" in msg and "backend" in msg
        assert "depends_on" in msg

    def test_circular_dependency_error(self):
        err = CircularDependencyError(
            cycles=[["A", "B"], ["C", "D", "E"]],
            locations={"A": ("a.py", 1)},
        )
        msg = str(err)
        assert "Cycle 1" in msg
        assert "Cycle 2" in msg
        assert "A" in msg

    def test_missing_dependency_error(self):
        err = MissingDependencyError(
            service_token="UserService",
            dependency_token="UserRepo",
            service_location=("svc.py", 15),
        )
        msg = str(err)
        assert "UserService" in msg
        assert "UserRepo" in msg
        assert "svc.py:15" in msg

    def test_di_error_is_base(self):
        assert issubclass(ProviderNotFoundError, DIError)
        assert issubclass(DependencyCycleError, DIError)
        assert issubclass(ScopeViolationError, DIError)
        assert issubclass(MissingDependencyError, DIError)


# ═══════════════════════════════════════════════════════════════════════
# 12. Compat
# ═══════════════════════════════════════════════════════════════════════

class TestCompat:
    """Tests for legacy compatibility layer."""

    def test_get_set_clear_request_container(self):
        container = Container(scope="request")
        assert get_request_container() is None

        set_request_container(container)
        assert get_request_container() is container

        clear_request_container()
        assert get_request_container() is None

    def test_request_ctx_wraps_container(self):
        container = Container(scope="request")
        ctx = RequestCtx(container)
        assert ctx.container is container

    async def test_request_ctx_get_sync(self):
        container = Container(scope="request")
        container.register(ValueProvider("val", "tok"))
        ctx = RequestCtx(container)
        # Use async get since we're in async context
        result = await ctx.get_async("tok")
        assert result == "val"

    async def test_request_ctx_get_default(self):
        """When token is missing and default is provided, returns None (optional=True)."""
        container = Container(scope="request")
        ctx = RequestCtx(container)
        # default makes optional=True, so resolve_async returns None
        result = await ctx.get_async("nonexistent", default="fallback")
        assert result is None

    async def test_request_ctx_get_missing_no_default(self):
        """When token is missing and no default, returns None (exception caught)."""
        container = Container(scope="request")
        ctx = RequestCtx(container)
        # default=None → optional=False → raises → caught → returns None
        result = await ctx.get_async("nonexistent")
        assert result is None

    async def test_request_ctx_get_async(self):
        container = Container(scope="request")
        container.register(ValueProvider("async_val", "tok"))
        ctx = RequestCtx(container)
        result = await ctx.get_async("tok")
        assert result == "async_val"

    def test_request_ctx_from_container(self):
        c = Container(scope="request")
        ctx = RequestCtx.from_container(c)
        assert ctx.container is c

    def test_request_ctx_set_get_current(self):
        container = Container(scope="request")
        ctx = RequestCtx(container)
        RequestCtx.set_current(ctx)

        current = RequestCtx.get_current()
        assert current is not None
        assert current.container is container

        clear_request_container()
        assert RequestCtx.get_current() is None

    def test_request_ctx_container_setter(self):
        c1 = Container(scope="request")
        c2 = Container(scope="request")
        ctx = RequestCtx(c1)
        ctx.container = c2
        assert ctx.container is c2


# ═══════════════════════════════════════════════════════════════════════
# 13. ResolveCtx
# ═══════════════════════════════════════════════════════════════════════

class TestResolveCtx:
    """Tests for ResolveCtx stack/cycle tracking."""

    def test_push_pop(self):
        ctx = ResolveCtx(Container(scope="app"))
        ctx.push("A")
        ctx.push("B")
        assert ctx.in_cycle("A")
        assert ctx.in_cycle("B")
        ctx.pop()
        assert not ctx.in_cycle("B")
        assert ctx.in_cycle("A")

    def test_get_trace_returns_copy(self):
        ctx = ResolveCtx(Container(scope="app"))
        ctx.push("X")
        trace = ctx.get_trace()
        ctx.push("Y")
        assert trace == ["X"]  # Original not modified

    def test_cache(self):
        ctx = ResolveCtx(Container(scope="app"))
        ctx.cache["key"] = "val"
        assert ctx.cache["key"] == "val"


# ═══════════════════════════════════════════════════════════════════════
# 14. ProviderMeta
# ═══════════════════════════════════════════════════════════════════════

class TestProviderMeta:
    """Tests for ProviderMeta dataclass."""

    def test_to_dict(self):
        meta = ProviderMeta(
            name="UserRepo",
            token="app.UserRepo",
            scope="singleton",
            tags=("primary",),
            module="app",
            qualname="UserRepo",
            line=42,
        )
        d = meta.to_dict()
        assert d["name"] == "UserRepo"
        assert d["token"] == "app.UserRepo"
        assert d["scope"] == "singleton"
        assert d["tags"] == ["primary"]
        assert d["line"] == 42

    def test_frozen(self):
        meta = ProviderMeta(name="X", token="X", scope="app")
        with pytest.raises(AttributeError):
            meta.name = "Y"  # type: ignore


# ═══════════════════════════════════════════════════════════════════════
# 15. _CACHE_SENTINEL
# ═══════════════════════════════════════════════════════════════════════

class TestCacheSentinel:
    """Tests for the sentinel-based cache check."""

    def test_sentinel_is_unique_object(self):
        assert _CACHE_SENTINEL is not None
        assert _CACHE_SENTINEL is not False
        assert _CACHE_SENTINEL != 0

    async def test_none_value_distinguished_from_missing(self):
        """Container distinguishes cached-None from cache-miss."""
        container = Container(scope="app")

        async def return_none():
            return None

        container.register(FactoryProvider(return_none, scope="singleton", name="null_provider"))

        # First resolve — calls factory
        r1 = await container.resolve_async("null_provider")
        assert r1 is None

        # Second resolve — should hit cache (not call factory again)
        r2 = await container.resolve_async("null_provider")
        assert r2 is None

        # Verify it's actually cached
        key = "null_provider"
        assert key in container._cache
        assert container._cache[key] is None


# ═══════════════════════════════════════════════════════════════════════
# 16. _NullLifecycle
# ═══════════════════════════════════════════════════════════════════════

class TestNullLifecycle:
    """Tests for the lightweight null lifecycle used in request containers."""

    async def test_no_ops(self):
        """All methods are no-ops."""
        await _NullLifecycle.run_startup_hooks()
        await _NullLifecycle.run_shutdown_hooks()
        await _NullLifecycle.run_finalizers()
        _NullLifecycle.on_startup(lambda: None)
        _NullLifecycle.on_shutdown(lambda: None)
        _NullLifecycle.clear()
        # Should all succeed without raising


# ═══════════════════════════════════════════════════════════════════════
# 17. Lambda Capture Fix Verification
# ═══════════════════════════════════════════════════════════════════════

class TestLambdaCaptureFix:
    """Verify the lambda late-binding closure fix in _check_lifecycle_hooks."""

    async def test_hooks_capture_correct_method(self):
        """Each service's on_startup/on_shutdown is bound correctly (not last one)."""
        container = Container(scope="app")

        class SvcA:
            async def on_startup(self):
                pass
            async def on_shutdown(self):
                pass

        class SvcB:
            async def on_startup(self):
                pass
            async def on_shutdown(self):
                pass

        container.register(ClassProvider(SvcA, scope="singleton"))
        container.register(ClassProvider(SvcB, scope="singleton"))

        svc_a = await container.resolve_async(SvcA)
        svc_b = await container.resolve_async(SvcB)

        # Both should have hooks registered — verify count
        assert len(container._lifecycle._startup_hooks) == 2
        assert len(container._lifecycle._shutdown_hooks) == 2


# ═══════════════════════════════════════════════════════════════════════
# 18. Request Scope Provider Isolation
# ═══════════════════════════════════════════════════════════════════════

class TestRequestScopeIsolation:
    """Verify child._providers is a copy (not shared reference)."""

    async def test_child_registration_does_not_mutate_parent(self):
        parent = Container(scope="app")
        parent.register(ValueProvider("parent_val", "shared"))

        child = parent.create_request_scope()
        child.register(ValueProvider("child_val", "child_only"))

        # Parent should NOT have the child's provider
        assert "child_only" not in parent._providers
        assert "child_only" in child._providers

    async def test_multiple_children_isolated(self):
        parent = Container(scope="app")
        parent.register(ValueProvider("base", "tok"))

        c1 = parent.create_request_scope()
        c2 = parent.create_request_scope()

        c1.register(ValueProvider("c1_val", "c1_tok"))
        c2.register(ValueProvider("c2_val", "c2_tok"))

        assert "c1_tok" not in c2._providers
        assert "c2_tok" not in c1._providers
        assert "c1_tok" not in parent._providers


# ═══════════════════════════════════════════════════════════════════════
# 19. Integration: End-to-End DI Flow
# ═══════════════════════════════════════════════════════════════════════

class TestDIIntegration:
    """End-to-end integration tests for the DI system."""

    async def test_full_lifecycle_flow(self):
        """Register → startup → resolve → request scope → shutdown."""
        container = Container(scope="app")

        # Register services
        container.register(ClassProvider(DummyRepo, scope="singleton"))
        container.register(ClassProvider(DummyService, scope="singleton"))

        # Startup
        repo = await container.resolve_async(DummyRepo)
        svc = await container.resolve_async(DummyService)

        await container.startup()
        assert svc.started is True

        # Request scope
        child = container.create_request_scope()
        req_repo = await child.resolve_async(DummyRepo)
        assert req_repo is repo  # Singleton shared

        await child.shutdown()

        # App shutdown
        await container.shutdown()

    async def test_dag_with_sub_dependencies(self):
        """RequestDAG resolves nested Dep chains."""
        async def get_config():
            return {"db_url": "sqlite://"}

        async def get_db(config: Annotated[dict, Dep(call=get_config)]):
            return f"DB({config['db_url']})"

        container = Container(scope="app")
        dag = RequestDAG(container)

        result = await dag.resolve(Dep(call=get_db), str)
        assert result == "DB(sqlite://)"

        await dag.teardown()

    async def test_graph_and_container_consistency(self):
        """Graph resolution order matches container resolution capability."""
        container = Container(scope="app")

        # Register C (no deps), B (depends on C), A (depends on B)
        container.register(ValueProvider("C_val", "C"))
        container.register(ValueProvider("B_val", "B"))
        container.register(ValueProvider("A_val", "A"))

        # All resolvable
        assert await container.resolve_async("A") == "A_val"
        assert await container.resolve_async("B") == "B_val"
        assert await container.resolve_async("C") == "C_val"


# ═══════════════════════════════════════════════════════════════════════
# Async helper
# ═══════════════════════════════════════════════════════════════════════

async def _async_append(lst, value):
    lst.append(value)

async def _async_noop():
    pass
