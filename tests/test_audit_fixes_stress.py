"""
Audit-fix regression and stress tests.

Each section maps to a finding in the architecture audit report:
  §6.1  - Lifecycle hooks skipped for simple routes            (CRITICAL)
  §6.2  - authenticate_password unconditional JWT issuance     (SECURITY)
  §6.3  - Substring-based forward-ref type matching            (BUG)
  §6.4  - Conflict detector false positives for typed segments (BUG)
  §5.3  - id()-keyed cache correctness + clear_caches wiring   (ARCH)
  §7    - url_for O(1) lookup via name index                   (PERF)
  §8    - validate_scope silent swallow now logs warning        (SEC)
  §5.2  - Controller docstring documents pipeline vs clearance  (DOCS)
  STRESS - High-concurrency dispatch, route table exhaustion,
           cache GC robustness, large route table url_for.
"""

from __future__ import annotations

import asyncio
import gc
import inspect
import time
import unittest
from unittest.mock import patch

# ─── Minimal stubs so tests run without the full ASGI stack ──────────────────

class _FakeRequest:
    def __init__(self, path="/", method="GET", headers=None, state=None):
        self.path = path
        self.method = method
        self.headers = headers or {}
        self.state = state or {}

    def content_type(self):
        return self.headers.get("content-type", "")


class _FakeContainer:
    """Minimal DI container stub."""
    _providers: dict = {}
    _cache: dict = {}

    def _token_to_key(self, token):
        return token

    async def resolve_async(self, token, **kw):
        raise KeyError(token)

    def get_provider(self, token):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# §6.1 — Lifecycle hooks must fire for ALL route shapes, including simple ones
# ─────────────────────────────────────────────────────────────────────────────

class TestLifecycleHookSimpleRoute(unittest.IsolatedAsyncioTestCase):
    """
    The critical §6.1 regression test.

    A controller with an overridden on_request/on_response and a route that
    would previously be classified as 'simple' (path-only params, no pipeline,
    no contract, no filters) must still invoke the lifecycle hooks.
    """

    def _make_minimal_engine(self):
        from aquilia.controller.engine import ControllerEngine
        from aquilia.controller.factory import ControllerFactory

        factory = ControllerFactory(app_container=_FakeContainer())
        engine = ControllerEngine(factory=factory)
        # Clear class-level caches so previous test state doesn't bleed through
        ControllerEngine.clear_caches()
        return engine

    def _make_compiled_route(self, controller_class, handler_name, path="/<id:int>"):
        """Build a minimal CompiledRoute pointing at controller_class."""
        from aquilia.controller.compiler import ControllerCompiler

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(controller_class)
        for route in compiled.routes:
            if route.route_metadata.handler_name == handler_name:
                return route
        raise ValueError(f"Route {handler_name!r} not found")

    async def test_on_request_fires_on_simple_path_param_route(self):
        """§6.1: on_request must be called even for the simplest path-param route."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        hook_calls = []

        class SimpleController(Controller):
            prefix = "/items"

            async def on_request(self, ctx):
                hook_calls.append("on_request")

            @GET("/<id:int>")
            async def get(self, ctx, id: int):
                return {"id": id}

        engine = self._make_minimal_engine()
        route = self._make_compiled_route(SimpleController, "get")

        request = _FakeRequest(path="/items/42")
        container = _FakeContainer()

        instance = SimpleController.__new__(SimpleController)
        with patch.object(engine.factory, "create", return_value=instance):
            response = await engine.execute(route, request, {"id": 42}, container)

        assert "on_request" in hook_calls, (
            "§6.1 REGRESSION: on_request was NOT called for a simple path-param route. "
            "The fast path silently skipped the lifecycle hook."
        )

    async def test_on_response_fires_on_simple_path_param_route(self):
        """§6.1: on_response must be called even for the simplest path-param route."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        hook_calls = []

        class SimpleController2(Controller):
            prefix = "/things"

            async def on_response(self, ctx, response):
                hook_calls.append(("on_response", type(response).__name__))

            @GET("/<id:int>")
            async def get(self, ctx, id: int):
                return {"id": id}

        engine = self._make_minimal_engine()
        route = self._make_compiled_route(SimpleController2, "get")

        request = _FakeRequest(path="/things/7")
        container = _FakeContainer()

        instance = SimpleController2.__new__(SimpleController2)
        with patch.object(engine.factory, "create", return_value=instance):
            await engine.execute(route, request, {"id": 7}, container)

        assert any(call[0] == "on_response" for call in hook_calls), (
            "§6.1 REGRESSION: on_response was NOT called for a simple path-param route."
        )

    async def test_route_without_hooks_still_takes_fast_path(self):
        """
        Regression guard: routes on controllers WITHOUT lifecycle hooks must
        still use the fast path (is_simple=True) for performance.
        """
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET
        from aquilia.controller.engine import ControllerEngine

        class NoHookController(Controller):
            prefix = "/fast"

            @GET("/<id:int>")
            async def get(self, ctx, id: int):
                return {"id": id}

        engine = self._make_minimal_engine()
        from aquilia.controller.compiler import ControllerCompiler
        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(NoHookController)
        route = compiled.routes[0]

        request = _FakeRequest(path="/fast/1")
        container = _FakeContainer()
        instance = NoHookController.__new__(NoHookController)
        with patch.object(engine.factory, "create", return_value=instance):
            await engine.execute(route, request, {"id": 1}, container)

        is_simple = ControllerEngine._simple_route_cache.get(id(route))
        assert is_simple is True, (
            "Controller without lifecycle hooks should classify as simple for performance. "
            f"Got is_simple={is_simple!r}"
        )

    async def test_both_hooks_fire_in_order(self):
        """§6.1: Both on_request and on_response fire, in the right order."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        order = []

        class BothHooksController(Controller):
            prefix = "/ordered"

            async def on_request(self, ctx):
                order.append("on_request")

            async def on_response(self, ctx, response):
                order.append("on_response")

            @GET("/<id:int>")
            async def get(self, ctx, id: int):
                order.append("handler")
                return {"id": id}

        engine = self._make_minimal_engine()
        route = self._make_compiled_route(BothHooksController, "get")

        request = _FakeRequest(path="/ordered/5")
        container = _FakeContainer()
        instance = BothHooksController.__new__(BothHooksController)
        with patch.object(engine.factory, "create", return_value=instance):
            await engine.execute(route, request, {"id": 5}, container)

        assert order == ["on_request", "handler", "on_response"], (
            f"§6.1: Hooks fired in wrong order: {order}"
        )

    async def test_no_hooks_no_pipeline_no_contract_is_simple(self):
        """A plain no-frills path-param route is simple (fast-path eligible)."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET
        from aquilia.controller.engine import ControllerEngine

        class PlainController(Controller):
            prefix = "/plain"

            @GET("/<val:str>")
            async def show(self, ctx, val: str):
                return val

        engine = self._make_minimal_engine()
        from aquilia.controller.compiler import ControllerCompiler
        route = ControllerCompiler().compile_controller(PlainController).routes[0]

        request = _FakeRequest(path="/plain/hello")
        container = _FakeContainer()
        instance = PlainController.__new__(PlainController)
        with patch.object(engine.factory, "create", return_value=instance):
            await engine.execute(route, request, {"val": "hello"}, container)

        assert ControllerEngine._simple_route_cache.get(id(route)) is True


# ─────────────────────────────────────────────────────────────────────────────
# §6.2 — authenticate_password issue_tokens=False skips JWT issuance
# ─────────────────────────────────────────────────────────────────────────────

def _make_test_auth_manager():
    from aquilia.auth.hashing import PasswordHasher
    from aquilia.auth.manager import AuthManager
    from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore, MemoryTokenStore
    from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager

    identity_store = MemoryIdentityStore()
    credential_store = MemoryCredentialStore()
    token_store = MemoryTokenStore()
    key = KeyDescriptor.generate(kid="test-key", algorithm="HS256", secret="unit-test-secret-long-enough-for-hs256")
    token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=token_store)

    return AuthManager(
        identity_store=identity_store,
        credential_store=credential_store,
        token_manager=token_manager,
        password_hasher=PasswordHasher(),
    )


class TestAuthIssueTokensFlag(unittest.IsolatedAsyncioTestCase):
    """§6.2: authenticate_password must honour issue_tokens=False."""

    async def _register_user(self, manager, username, password):
        from aquilia.auth.manager import SignInProvisionPolicy
        await manager.sign_in(
            username=username,
            password=password,
            provision=SignInProvisionPolicy(allow_username_bootstrap=True),
        )

    async def test_issue_tokens_true_default_returns_tokens(self):
        manager = _make_test_auth_manager()
        await self._register_user(manager, "user@example.com", "password123")

        result = await manager.authenticate_password(
            username="user@example.com",
            password="password123",
        )
        assert result.access_token is not None, "Default issue_tokens=True must return access_token"
        assert result.refresh_token is not None, "Default issue_tokens=True must return refresh_token"
        assert result.expires_in > 0

    async def test_issue_tokens_false_returns_no_tokens(self):
        """§6.2: session-only auth must NOT mint JWT tokens."""
        manager = _make_test_auth_manager()
        await self._register_user(manager, "session_user@example.com", "securepass")

        result = await manager.authenticate_password(
            username="session_user@example.com",
            password="securepass",
            issue_tokens=False,
        )
        assert result.access_token is None, (
            "§6.2 REGRESSION: issue_tokens=False should not return an access_token. "
            f"Got: {result.access_token!r}"
        )
        assert result.refresh_token is None, (
            "§6.2 REGRESSION: issue_tokens=False should not return a refresh_token. "
            f"Got: {result.refresh_token!r}"
        )
        assert result.identity is not None, "Identity must still be populated"
        assert result.expires_in == 0

    async def test_sign_in_provision_policy_issue_tokens_false(self):
        """§6.2: SignInProvisionPolicy.issue_tokens=False flows through sign_in."""
        from aquilia.auth.manager import SignInProvisionPolicy

        manager = _make_test_auth_manager()
        policy = SignInProvisionPolicy(
            allow_username_bootstrap=True,
            issue_tokens=False,
        )
        result = await manager.sign_in(
            username="sess@example.com",
            password="testpass",
            provision=policy,
        )
        assert result.access_token is None
        assert result.refresh_token is None

    async def test_sign_in_provision_policy_issue_tokens_true_default(self):
        """§6.2: Default SignInProvisionPolicy.issue_tokens=True still issues tokens."""
        from aquilia.auth.manager import SignInProvisionPolicy

        manager = _make_test_auth_manager()
        policy = SignInProvisionPolicy(allow_username_bootstrap=True, issue_tokens=True)
        result = await manager.sign_in(
            username="tok@example.com",
            password="testpass",
            provision=policy,
        )
        assert result.access_token is not None
        assert result.refresh_token is not None

    async def test_identity_still_resolved_when_issue_tokens_false(self):
        """Even without tokens the identity must be correctly resolved."""
        manager = _make_test_auth_manager()
        await self._register_user(manager, "id_check@example.com", "mypassword")

        result = await manager.authenticate_password(
            username="id_check@example.com",
            password="mypassword",
            issue_tokens=False,
        )
        assert result.identity.id is not None


# ─────────────────────────────────────────────────────────────────────────────
# §6.3 — Substring-based type-name matching in metadata._extract_method_params
# ─────────────────────────────────────────────────────────────────────────────

class TestMetadataForwardRefMatching(unittest.TestCase):
    """
    §6.3: types whose names contain "Request" as a substring must NOT be
    silently reclassified as the injected request context.
    """

    def _extract_params(self, handler_func, path="/<id:int>"):
        import inspect as ins

        from aquilia.controller.metadata import _extract_method_params
        sig = ins.signature(handler_func)
        return _extract_method_params(handler_func, sig, path)

    def test_request_log_not_classified_as_special(self):
        """
        §6.3: 'RequestLog' contains 'Request' as substring — must NOT be
        skipped by the special-param detector when used as a forward ref.
        """
        def handler(self, id: int, log: RequestLog):  # noqa: F821
            pass

        params = self._extract_params(handler)
        param_names = [p.name for p in params]
        assert "log" in param_names, (
            "§6.3 REGRESSION: parameter annotated 'RequestLog' (forward ref string) "
            "was wrongly classified as the injected request context and dropped. "
            f"Params found: {param_names}"
        )

    def test_password_reset_request_not_classified_as_special(self):
        """§6.3: 'PasswordResetRequest' contains 'Request' — must not be dropped."""
        def handler(self, body: PasswordResetRequest):  # noqa: F821
            pass

        params = self._extract_params(handler, path="/reset")
        param_names = [p.name for p in params]
        assert "body" in param_names, (
            "§6.3 REGRESSION: 'PasswordResetRequest' forward ref was treated as "
            f"a special param and silently dropped. Params: {param_names}"
        )

    def test_exact_request_ctx_string_is_still_special(self):
        """§6.3: The exact string 'RequestCtx' must still be treated as special."""
        def handler(self, ctx: RequestCtx):  # noqa: F821
            pass

        params = self._extract_params(handler, path="/items")
        param_names = [p.name for p in params]
        assert "ctx" not in param_names, (
            "Exact 'RequestCtx' forward ref must still be treated as special (injected)."
        )

    def test_exact_request_string_is_still_special(self):
        """§6.3: The exact string 'Request' must still be treated as special."""
        def handler(self, request: Request):  # noqa: F821
            pass

        params = self._extract_params(handler, path="/items")
        param_names = [p.name for p in params]
        assert "request" not in param_names, (
            "Exact 'Request' forward ref must still be treated as special (injected)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# §6.4 — Conflict detector: differently-typed dynamic segments are NOT conflicts
# ─────────────────────────────────────────────────────────────────────────────

class TestConflictDetectorTypedSegments(unittest.TestCase):
    """§6.4: routes differing only by segment type must NOT be false-positive conflicts."""

    def _compile(self, *controller_classes):
        from aquilia.controller.compiler import ControllerCompiler
        compiler = ControllerCompiler()
        compiled = [compiler.compile_controller(cls) for cls in controller_classes]
        return compiler, compiled

    def test_int_vs_str_not_a_conflict(self):
        """GET /items/<id:int> vs GET /items/<slug:str> -- different types, NOT a conflict."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        class IntController(Controller):
            prefix = "/items"

            @GET("/<id:int>")
            async def get_by_id(self, ctx, id: int):
                return {}

        class StrController(Controller):
            prefix = "/items"

            @GET("/<slug:str>")
            async def get_by_slug(self, ctx, slug: str):
                return {}

        compiler, compiled = self._compile(IntController, StrController)
        conflicts = compiler.validate_route_tree(compiled)

        dynamic_conflicts = [
            c for c in conflicts
            if "get_by_id" in (c["route1"]["handler"], c["route2"]["handler"])
            and "get_by_slug" in (c["route1"]["handler"], c["route2"]["handler"])
        ]
        assert len(dynamic_conflicts) == 0, (
            "§6.4 REGRESSION: int vs str typed segments wrongly reported as a conflict. "
            f"Conflicts: {dynamic_conflicts}"
        )

    def test_same_type_dynamic_is_a_conflict(self):
        """GET /same/<id:int> vs GET /same/<other_id:int> -- SAME type, IS a conflict."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        class A(Controller):
            prefix = "/same"

            @GET("/<id:int>")
            async def get_a(self, ctx, id: int):
                return {}

        class B(Controller):
            prefix = "/same"

            @GET("/<other_id:int>")
            async def get_b(self, ctx, other_id: int):
                return {}

        compiler, compiled = self._compile(A, B)
        conflicts = compiler.validate_route_tree(compiled)
        assert len(conflicts) > 0, (
            "§6.4: Two int-typed params at the same position must be flagged as a conflict."
        )

    def test_static_vs_dynamic_not_a_conflict(self):
        """GET /items/list vs GET /items/<id:int> -- static trumps dynamic, no conflict."""
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET

        class StaticController(Controller):
            prefix = "/items"

            @GET("/list")
            async def list_all(self, ctx):
                return []

        class DynController(Controller):
            prefix = "/items"

            @GET("/<id:int>")
            async def get_one(self, ctx, id: int):
                return {}

        compiler, compiled = self._compile(StaticController, DynController)
        conflicts = compiler.validate_route_tree(compiled)
        assert len(conflicts) == 0, (
            f"Static vs dynamic segment falsely reported as conflict: {conflicts}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# §5.3 — id()-keyed cache safety: clear_caches() prevents stale hits
# ─────────────────────────────────────────────────────────────────────────────

class TestCacheGCRobustness(unittest.TestCase):
    """§5.3: After clear_caches() the engine must not serve stale entries."""

    def test_clear_caches_removes_simple_route_classification(self):
        from aquilia.controller.engine import ControllerEngine

        fake_route_id = 0xDEADBEEF
        ControllerEngine._simple_route_cache[fake_route_id] = True
        ControllerEngine._clearance_cache[fake_route_id] = ...

        ControllerEngine.clear_caches()

        assert fake_route_id not in ControllerEngine._simple_route_cache
        assert fake_route_id not in ControllerEngine._clearance_cache

    def test_clear_caches_removes_lifecycle_hook_cache(self):
        from aquilia.controller.engine import ControllerEngine

        class _DummyCtrl:
            pass

        ControllerEngine._has_lifecycle_hooks[_DummyCtrl] = (True, False)
        ControllerEngine.clear_caches()

        assert _DummyCtrl not in ControllerEngine._has_lifecycle_hooks

    def test_factory_clear_caches_removes_ctor_info(self):
        from aquilia.controller.factory import ControllerFactory

        class _SomeCtrl:
            def __init__(self):
                pass

        ControllerFactory._ctor_info_cache[_SomeCtrl] = [("x", int, False, None)]
        ControllerFactory.clear_caches()

        assert _SomeCtrl not in ControllerFactory._ctor_info_cache

    def test_gc_after_cache_population_does_not_cause_errors(self):
        from aquilia.controller.engine import ControllerEngine

        ControllerEngine.clear_caches()

        class _Obj:
            pass

        obj1 = _Obj()
        addr = id(obj1)
        ControllerEngine._simple_route_cache[addr] = True

        del obj1
        gc.collect()

        obj2 = _Obj()
        _ = ControllerEngine._simple_route_cache.get(id(obj2))
        ControllerEngine.clear_caches()
        assert id(obj2) not in ControllerEngine._simple_route_cache


# ─────────────────────────────────────────────────────────────────────────────
# §7 — url_for() O(1) lookup via name index
# ─────────────────────────────────────────────────────────────────────────────

class TestUrlForIndexedLookup(unittest.TestCase):
    """§7/§11.11: url_for must use _name_index (O(1)) built at initialize() time."""

    def _build_router_with_n_routes(self, n: int):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.router import ControllerRouter

        compiler = ControllerCompiler()
        router = ControllerRouter()

        for i in range(n):
            handler_name = f"get_item_{i}"

            async def _handler(self, ctx, item_id: int, _i=i):
                return {"i": _i}
            _handler.__name__ = handler_name

            decorated = GET("/<item_id:int>")(_handler)

            ctrl_cls = type(
                f"BenchController{i}",
                (Controller,),
                {
                    "prefix": f"/bench_{i}",
                    handler_name: decorated,
                },
            )
            compiled = compiler.compile_controller(ctrl_cls)
            router.add_controller(compiled)

        router.initialize()
        return router

    def test_name_index_built_after_initialize(self):
        router = self._build_router_with_n_routes(10)
        assert len(router._name_index) > 0

    def test_url_for_resolves_by_full_name(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.router import ControllerRouter

        class NamedController(Controller):
            prefix = "/named"

            @GET("/<user_id:int>")
            async def get_user(self, ctx, user_id: int):
                return {}

        router = ControllerRouter()
        router.add_controller(ControllerCompiler().compile_controller(NamedController))
        router.initialize()

        url = router.url_for("NamedController.get_user", user_id=42)
        assert "42" in url, f"url_for did not substitute param: {url!r}"

    def test_url_for_resolves_by_bare_handler_name(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.router import ControllerRouter

        class BareController(Controller):
            prefix = "/bare"

            @GET("/<pk:int>")
            async def retrieve(self, ctx, pk: int):
                return {}

        router = ControllerRouter()
        router.add_controller(ControllerCompiler().compile_controller(BareController))
        router.initialize()

        url = router.url_for("retrieve", pk=99)
        assert "99" in url

    def test_url_for_large_route_table_performance(self):
        """url_for on 500-route table must complete in <500ms (O(1) not O(n))."""
        router = self._build_router_with_n_routes(500)
        names = list(router._name_index.keys())
        target = names[-1]

        start = time.perf_counter()
        for _ in range(1000):
            try:
                router.url_for(target)
            except Exception:
                pass
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, (
            f"url_for on 500-route table took {elapsed_ms:.1f}ms for 1000 calls -- "
            "should be O(1); possible regression to O(n) linear scan."
        )


# ─────────────────────────────────────────────────────────────────────────────
# §8 — validate_scope() silent swallow now logs a warning
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateScopeLogsOnFailure(unittest.TestCase):
    """§8: When scope validation raises an unexpected exception, it must be logged."""

    def test_scope_validation_exception_is_logged(self):
        from aquilia.controller.factory import ControllerFactory

        class WeirdContainer:
            def get_provider(self, token):
                raise RuntimeError("Inspection failure!")

        factory = ControllerFactory(app_container=WeirdContainer())

        from aquilia.controller.base import Controller
        from aquilia.controller.factory import InstantiationMode

        class SomeController(Controller):
            prefix = "/x"
            def __init__(self, dep: int):
                self.dep = dep

        with self.assertLogs("aquilia.controller.factory", level="WARNING") as cm:
            factory.validate_scope(SomeController, InstantiationMode.SINGLETON)

        log_text = "\n".join(cm.output)
        assert "Scope validation" in log_text or "scope" in log_text.lower(), (
            "§8 REGRESSION: scope validation exception was swallowed silently; "
            f"no warning logged. Got: {cm.output}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# §5.2 — Controller docstring documents pipeline vs. clearance
# ─────────────────────────────────────────────────────────────────────────────

class TestControllerDocstringDecisionRule(unittest.TestCase):
    """§5.2/§9: The Controller docstring must contain the pipeline vs clearance rule."""

    def test_docstring_contains_pipeline_vs_clearance_rule(self):
        from aquilia.controller.base import Controller

        doc = Controller.__doc__ or ""
        assert "pipeline" in doc.lower() and "clearance" in doc.lower(), (
            "§5.2: Controller docstring must document the pipeline vs. clearance "
            "decision rule."
        )
        assert "decision rule" in doc.lower() or "rule" in doc.lower()


# ─────────────────────────────────────────────────────────────────────────────
# STRESS — High-concurrency dispatch (200 requests)
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentDispatchStress(unittest.IsolatedAsyncioTestCase):
    """200 concurrent requests; lifecycle hooks must fire exactly N times in order."""

    async def test_200_concurrent_requests_lifecycle_hooks(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.engine import ControllerEngine
        from aquilia.controller.factory import ControllerFactory

        ControllerEngine.clear_caches()

        call_log = []
        lock = asyncio.Lock()

        class StressController(Controller):
            prefix = "/stress"

            async def on_request(self, ctx):
                async with lock:
                    call_log.append("on_request")

            async def on_response(self, ctx, response):
                async with lock:
                    call_log.append("on_response")

            @GET("/<n:int>")
            async def handle(self, ctx, n: int):
                return {"n": n}

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(StressController)
        route = compiled.routes[0]

        factory = ControllerFactory(app_container=_FakeContainer())
        engine = ControllerEngine(factory=factory)

        async def one_request(i: int):
            request = _FakeRequest(path=f"/stress/{i}")
            container = _FakeContainer()
            instance = StressController.__new__(StressController)
            with patch.object(engine.factory, "create", return_value=instance):
                await engine.execute(route, request, {"n": i}, container)

        N = 200
        await asyncio.gather(*[one_request(i) for i in range(N)])

        on_req = call_log.count("on_request")
        on_resp = call_log.count("on_response")

        assert on_req == N, f"Expected {N} on_request calls, got {on_req}"
        assert on_resp == N, f"Expected {N} on_response calls, got {on_resp}"


# ─────────────────────────────────────────────────────────────────────────────
# STRESS — Large route table conflict detection
# ─────────────────────────────────────────────────────────────────────────────

class TestLargeRouteTableConflictPerformance(unittest.TestCase):
    """300 controllers with unique prefixes must have zero false-positive conflicts."""

    def _build_large_route_table(self, n: int):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET

        compiler = ControllerCompiler()
        compiled_list = []
        for i in range(n):
            async def h(self, ctx, item_id: int, _i=i):
                return _i

            h.__name__ = f"get_{i}"
            decorated = GET("/<item_id:int>")(h)
            cls = type(
                f"LC{i}",
                (Controller,),
                {"prefix": f"/resource_{i}", f"get_{i}": decorated},
            )
            compiled_list.append(compiler.compile_controller(cls))

        return compiler, compiled_list

    def test_300_controllers_zero_false_positives(self):
        compiler, compiled = self._build_large_route_table(300)
        start = time.perf_counter()
        conflicts = compiler.validate_route_tree(compiled)
        elapsed = time.perf_counter() - start

        assert len(conflicts) == 0, (
            f"§6.4: {len(conflicts)} false-positive conflicts in 300-controller table. "
            f"First: {conflicts[0] if conflicts else 'N/A'}"
        )
        assert elapsed < 10.0, f"validate_route_tree on 300 controllers took {elapsed:.2f}s"


# ─────────────────────────────────────────────────────────────────────────────
# STRESS — Cache stability under rapid class churn
# ─────────────────────────────────────────────────────────────────────────────

class TestCacheStabilityUnderChurn(unittest.TestCase):
    """Create+GC many controller classes to exercise id()-keyed cache safety."""

    def test_cache_survives_class_churn(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.engine import ControllerEngine

        ControllerEngine.clear_caches()

        for i in range(200):
            cls = type(f"ChurnCtrl_{i}", (Controller,), {"prefix": f"/churn_{i}"})
            ControllerEngine._has_lifecycle_hooks[cls] = (False, False)
            del cls
            gc.collect()

        ControllerEngine.clear_caches()
        assert len(ControllerEngine._has_lifecycle_hooks) == 0


# ─────────────────────────────────────────────────────────────────────────────
# STRESS — Concurrent auth with mixed issue_tokens flags
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthConcurrentMixedTokenIssuance(unittest.IsolatedAsyncioTestCase):
    """Concurrent auth calls with mixed issue_tokens flags must not interfere."""

    async def test_concurrent_auth_mixed_issue_tokens(self):
        import asyncio

        from aquilia.auth.manager import SignInProvisionPolicy

        manager = _make_test_auth_manager()

        policy = SignInProvisionPolicy(allow_username_bootstrap=True)
        await manager.sign_in(username="concurrent@test.com", password="password123", provision=policy)

        async def auth_with_tokens():
            result = await manager.authenticate_password(
                username="concurrent@test.com",
                password="password123",
                issue_tokens=True,
            )
            assert result.access_token is not None
            return "with_tokens"

        async def auth_without_tokens():
            result = await manager.authenticate_password(
                username="concurrent@test.com",
                password="password123",
                issue_tokens=False,
            )
            assert result.access_token is None
            return "without_tokens"

        tasks = [auth_with_tokens() if i % 2 == 0 else auth_without_tokens()
                 for i in range(50)]
        results = await asyncio.gather(*tasks)

        with_count = results.count("with_tokens")
        without_count = results.count("without_tokens")
        assert with_count == 25 and without_count == 25


# ─────────────────────────────────────────────────────────────────────────────
# REGRESSION MATRIX — Source-level guards that each fix is in place
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditRegressionMatrix(unittest.TestCase):
    """Quick smoke-test matrix: verify each fix exists at the source level."""

    def test_s61_fast_path_excludes_lifecycle_hook_classes(self):
        from aquilia.controller import engine as eng_mod
        src = inspect.getsource(eng_mod.ControllerEngine.execute)
        assert "has_on_request" in src and "has_on_response" in src, (
            "§6.1: execute() must reference has_on_request/has_on_response in is_simple check."
        )
        assert "not has_on_request" in src, (
            "§6.1: is_simple condition must exclude controllers with on_request hooks."
        )

    def test_s62_authenticate_password_has_issue_tokens_param(self):
        from aquilia.auth.manager import AuthManager
        sig = inspect.signature(AuthManager.authenticate_password)
        assert "issue_tokens" in sig.parameters

    def test_s62_signin_provision_policy_has_issue_tokens(self):
        import dataclasses

        from aquilia.auth.manager import SignInProvisionPolicy
        fields = {f.name for f in dataclasses.fields(SignInProvisionPolicy)}
        assert "issue_tokens" in fields

    def test_s63_forward_ref_uses_exact_match(self):
        from aquilia.controller import metadata as m
        src = inspect.getsource(m._extract_method_params)
        assert "endswith" in src or 'param_type == x' in src, (
            "§6.3: Forward-ref string check must use exact/endswith match, not substring."
        )

    def test_s64_both_dynamic_branch_has_type_comparison(self):
        from aquilia.controller import compiler as c
        src = inspect.getsource(c.ControllerCompiler._routes_conflict)
        assert "info1 != info2" in src or "info1 == info2" in src

    def test_s8_validate_scope_logs_warning(self):
        from aquilia.controller import factory as f
        src = inspect.getsource(f.ControllerFactory.validate_scope)
        assert "logger.warning" in src

    def test_s52_controller_docstring_has_decision_rule(self):
        from aquilia.controller.base import Controller
        doc = Controller.__doc__ or ""
        assert "clearance" in doc.lower()

    def test_s7_router_has_name_index(self):
        from aquilia.controller.router import ControllerRouter
        router = ControllerRouter()
        assert hasattr(router, "_name_index")


if __name__ == "__main__":
    unittest.main(verbosity=2)
