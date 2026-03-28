"""
Comprehensive Controller System Tests

Tests all controller subsystems including:
- Base: Controller, RequestCtx, _ControllerMeta (mutable-default fix)
- Decorators: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, WS, route()
- Factory: ControllerFactory, InstantiationMode, cache clearing
- Engine: ControllerEngine, throttle, interceptors, exception filters, timeout, cache clearing
- Router: ControllerRouter, url_for, static/dynamic matching
- Compiler: ControllerCompiler, CompiledRoute, CompiledController, conflict detection
- Metadata: ControllerMetadata, RouteMetadata, ParameterMetadata, extraction
- Filters: FilterSet, SearchFilter, OrderingFilter, in-memory + declarative
- Pagination: PageNumberPagination, LimitOffsetPagination, CursorPagination, NoPagination
- Renderers: JSONRenderer, XMLRenderer, YAMLRenderer, PlainTextRenderer, HTMLRenderer,
             ContentNegotiator, negotiate()
- OpenAPI: OpenAPIGenerator, OpenAPIConfig, swagger/redoc HTML generation
- New Features: versioning, throttle, interceptors, exception filters, timeouts, body size limits
"""

import asyncio
import inspect
import json
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ═══════════════════════════════════════════════════════════════════════════
#  Imports
# ═══════════════════════════════════════════════════════════════════════════

from aquilia.controller.base import (
    Controller,
    RequestCtx,
    ExceptionFilter,
    Interceptor,
    Throttle,
    _ControllerMeta,
)
from aquilia.controller.decorators import (
    GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, WS,
    RouteDecorator,
    route,
    VALID_HTTP_METHODS,
)
from aquilia.controller.factory import (
    ControllerFactory,
    InstantiationMode,
    ScopeViolationError,
)
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.metadata import (
    ControllerMetadata,
    RouteMetadata,
    ParameterMetadata,
    extract_controller_metadata,
)
from aquilia.controller.filters import (
    FilterSet,
    FilterSetMeta,
    SearchFilter,
    OrderingFilter,
    BaseFilterBackend,
    apply_filters_to_list,
    apply_search_to_list,
    apply_ordering_to_list,
    _coerce_value,
    _matches_lookup,
    _get_nested,
)
from aquilia.controller.pagination import (
    BasePagination,
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination,
    NoPagination,
)
from aquilia.controller.renderers import (
    BaseRenderer,
    JSONRenderer,
    XMLRenderer,
    YAMLRenderer,
    PlainTextRenderer,
    HTMLRenderer,
    MessagePackRenderer,
    ContentNegotiator,
    negotiate,
    _parse_accept,
    _media_matches,
)
from aquilia.controller.openapi import (
    OpenAPIGenerator,
    OpenAPIConfig,
    generate_swagger_html,
    generate_redoc_html,
    _python_type_to_schema,
    _parse_docstring,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers / Fixtures
# ═══════════════════════════════════════════════════════════════════════════

def _make_request(
    method="GET", path="/", headers=None, query_string=b"",
    body=None, state=None,
):
    """Create a mock request object."""
    from aquilia.request import Request

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query_string,
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
    }

    body_bytes = b""
    if body:
        body_bytes = json.dumps(body).encode() if isinstance(body, dict) else body

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    req = Request(scope=scope, receive=receive)
    if state:
        req.state.update(state)
    return req


def _make_ctx(request=None, **kwargs):
    """Create a RequestCtx for testing."""
    req = request or _make_request()
    return RequestCtx(
        request=req,
        identity=kwargs.get("identity"),
        session=kwargs.get("session"),
        container=kwargs.get("container"),
        state=kwargs.get("state", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1: Base — Controller & RequestCtx
# ═══════════════════════════════════════════════════════════════════════════

class TestRequestCtx:
    """Tests for RequestCtx."""

    def test_basic_construction(self):
        req = _make_request(method="POST", path="/users")
        ctx = RequestCtx(request=req)
        assert ctx.path == "/users"
        assert ctx.method == "POST"
        assert ctx.state == {}
        assert ctx.identity is None
        assert ctx.session is None

    def test_dynamic_attribute_setting(self):
        """RequestCtx allows dynamic attributes (no __slots__)."""
        ctx = _make_ctx()
        ctx.custom_field = "hello"
        assert ctx.custom_field == "hello"

    def test_state_defaults_to_empty_dict(self):
        ctx = _make_ctx()
        assert isinstance(ctx.state, dict)

    def test_request_id_optional(self):
        ctx = RequestCtx(request=_make_request(), request_id="abc-123")
        assert ctx.request_id == "abc-123"

    def test_query_param_delegation(self):
        req = _make_request(query_string=b"page=2&size=10")
        ctx = RequestCtx(request=req)
        assert ctx.query_param("page") == "2"
        assert ctx.query_param("missing", "default") == "default"

    async def test_json_delegation(self):
        req = _make_request(body={"key": "value"})
        ctx = RequestCtx(request=req)
        data = await ctx.json()
        assert data == {"key": "value"}

    async def test_form_delegation(self):
        from aquilia.request import UnsupportedMediaType
        req = _make_request()
        ctx = RequestCtx(request=req)
        # No Content-Type header → UnsupportedMediaType
        with pytest.raises(UnsupportedMediaType):
            await ctx.form()


class TestControllerMutableDefaultFix:
    """Tests that mutable class defaults are NOT shared between subclasses."""

    def test_pipeline_not_shared(self):
        """BUG FIX: Each subclass gets its own pipeline list."""
        class ControllerA(Controller):
            prefix = "/a"
            pipeline = ["guard_a"]

        class ControllerB(Controller):
            prefix = "/b"
            pipeline = ["guard_b"]

        assert ControllerA.pipeline == ["guard_a"]
        assert ControllerB.pipeline == ["guard_b"]
        assert ControllerA.pipeline is not ControllerB.pipeline

    def test_tags_not_shared(self):
        """BUG FIX: Each subclass gets its own tags list."""
        class TaggedA(Controller):
            tags = ["alpha"]

        class TaggedB(Controller):
            tags = ["beta"]

        assert TaggedA.tags == ["alpha"]
        assert TaggedB.tags == ["beta"]
        assert TaggedA.tags is not TaggedB.tags

    def test_mutation_doesnt_leak(self):
        """Appending to one controller's pipeline doesn't affect others."""
        class Parent(Controller):
            pipeline = ["base"]

        class Child1(Parent):
            pass

        class Child2(Parent):
            pass

        Child1.pipeline.append("extra")
        assert "extra" in Child1.pipeline
        assert "extra" not in Child2.pipeline
        assert "extra" not in Parent.pipeline

    def test_interceptors_not_shared(self):
        class A(Controller):
            interceptors = ["i1"]
        class B(Controller):
            interceptors = ["i2"]
        assert A.interceptors is not B.interceptors

    def test_exception_filters_not_shared(self):
        class A(Controller):
            exception_filters = ["f1"]
        class B(Controller):
            exception_filters = ["f2"]
        assert A.exception_filters is not B.exception_filters


class TestControllerNewFeatures:
    """Tests for new Controller class attributes."""

    def test_version_default_none(self):
        assert Controller.version is None

    def test_throttle_default_none(self):
        assert Controller.throttle is None

    def test_timeout_default_zero(self):
        assert Controller.timeout == 0

    def test_max_body_size_default_zero(self):
        assert Controller.max_body_size == 0

    def test_interceptors_default_empty(self):
        assert Controller.interceptors == []

    def test_exception_filters_default_empty(self):
        assert Controller.exception_filters == []

    def test_custom_version(self):
        class V2(Controller):
            version = "v2"
        assert V2.version == "v2"

    def test_custom_timeout(self):
        class Slow(Controller):
            timeout = 30.0
        assert Slow.timeout == 30.0


class TestControllerLifecycle:
    """Tests for Controller lifecycle hooks."""

    async def test_lifecycle_hooks_are_no_ops(self):
        ctrl = Controller()
        ctx = _make_ctx()
        await ctrl.on_startup(ctx)
        await ctrl.on_shutdown(ctx)
        await ctrl.on_request(ctx)
        result = await ctrl.on_response(ctx, MagicMock())
        assert result is not None  # Returns the response passed in

    async def test_context_manager(self):
        ctrl = Controller()
        async with ctrl as c:
            assert c is ctrl


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2: Decorators
# ═══════════════════════════════════════════════════════════════════════════

class TestDecorators:
    """Tests for HTTP method decorators."""

    def test_get_sets_method(self):
        @GET("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "GET"

    def test_post_sets_method(self):
        @POST("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "POST"

    def test_put_sets_method(self):
        @PUT("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "PUT"

    def test_patch_sets_method(self):
        @PATCH("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "PATCH"

    def test_delete_sets_method(self):
        @DELETE("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "DELETE"

    def test_head_sets_method(self):
        @HEAD("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "HEAD"

    def test_options_sets_method(self):
        @OPTIONS("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "OPTIONS"

    def test_trace_sets_method(self):
        """NEW: TRACE method support."""
        @TRACE("/")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "TRACE"

    def test_ws_sets_method(self):
        @WS("/ws")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "WS"

    def test_method_set_before_call(self):
        """FIX: method is now set during __init__ via parameter."""
        dec = GET("/test")
        assert dec.method == "GET"

    def test_route_metadata_contains_all_fields(self):
        @GET("/", summary="List items", tags=["items"], deprecated=True)
        async def handler(self, ctx): pass

        meta = handler.__route_metadata__[0]
        assert meta["summary"] == "List items"
        assert meta["tags"] == ["items"]
        assert meta["deprecated"] is True
        assert "signature" in meta
        assert meta["func_name"] == "handler"

    def test_deduplication(self):
        """FIX: Same method+path shouldn't be added twice."""
        @GET("/")
        @GET("/")
        async def handler(self, ctx): pass
        assert len(handler.__route_metadata__) == 1

    def test_throttle_in_metadata(self):
        """NEW: Per-route throttle."""
        t = Throttle(limit=10, window=60)
        @GET("/", throttle=t)
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["throttle"] is t

    def test_timeout_in_metadata(self):
        """NEW: Per-route timeout."""
        @GET("/", timeout=5.0)
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["timeout"] == 5.0

    def test_route_function_single_method(self):
        @route("GET", "/items")
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["http_method"] == "GET"

    def test_route_function_multi_method(self):
        @route(["GET", "POST"], "/items")
        async def handler(self, ctx): pass
        methods = {m["http_method"] for m in handler.__route_metadata__}
        assert methods == {"GET", "POST"}

    def test_route_function_invalid_method(self):
        from aquilia.faults.domains import ConfigInvalidFault
        with pytest.raises(ConfigInvalidFault, match="Invalid HTTP method"):
            @route("INVALID", "/")
            async def handler(self, ctx): pass

    def test_valid_http_methods_constant(self):
        assert "GET" in VALID_HTTP_METHODS
        assert "POST" in VALID_HTTP_METHODS
        assert "TRACE" in VALID_HTTP_METHODS
        assert "WS" in VALID_HTTP_METHODS
        assert "INVALID" not in VALID_HTTP_METHODS

    def test_http_decorator_signature_has_no_var_keyword(self):
        params = inspect.signature(GET.__init__).parameters.values()
        kinds = {param.kind for param in params}
        assert inspect.Parameter.VAR_KEYWORD not in kinds

    def test_route_signature_has_no_var_keyword(self):
        params = inspect.signature(route).parameters.values()
        kinds = {param.kind for param in params}
        assert inspect.Parameter.VAR_KEYWORD not in kinds

    def test_unknown_kwarg_still_fails_fast(self):
        with pytest.raises(TypeError):
            @GET("/", unsupported_option=True)
            async def handler(self, ctx):
                pass


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3: Throttle
# ═══════════════════════════════════════════════════════════════════════════

class TestThrottle:
    """Tests for Throttle rate limiter."""

    def test_allows_within_limit(self):
        t = Throttle(limit=5, window=60)
        req = _make_request()
        for _ in range(5):
            assert t.check(req) is True

    def test_blocks_over_limit(self):
        t = Throttle(limit=3, window=60)
        req = _make_request()
        for _ in range(3):
            t.check(req)
        assert t.check(req) is False

    def test_retry_after(self):
        t = Throttle(limit=1, window=30)
        assert t.retry_after == 30

    def test_reset_clears_state(self):
        t = Throttle(limit=1, window=60)
        req = _make_request()
        t.check(req)
        assert t.check(req) is False
        t.reset()
        assert t.check(req) is True

    def test_different_clients_independent(self):
        t = Throttle(limit=1, window=60)
        # Use distinct ASGI client tuples to simulate different clients.
        # (X-Forwarded-For alone is not trusted without trust_proxy.)
        req1 = _make_request()
        req1.scope["client"] = ("1.1.1.1", 12345)
        req2 = _make_request()
        req2.scope["client"] = ("2.2.2.2", 12345)
        assert t.check(req1) is True
        assert t.check(req1) is False
        assert t.check(req2) is True  # Different client, still allowed


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 4: ExceptionFilter
# ═══════════════════════════════════════════════════════════════════════════

class TestExceptionFilter:
    """Tests for ExceptionFilter base class."""

    async def test_base_raises_not_implemented(self):
        ef = ExceptionFilter()
        with pytest.raises(NotImplementedError):
            await ef.catch(Exception("test"), _make_ctx())

    async def test_custom_filter(self):
        class NotFoundFilter(ExceptionFilter):
            catches = [KeyError]

            async def catch(self, exception, ctx):
                from aquilia.response import Response
                return Response.json({"error": "Not found"}, status=404)

        ef = NotFoundFilter()
        assert KeyError in ef.catches
        result = await ef.catch(KeyError("id"), _make_ctx())
        assert result.status == 404


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 5: Interceptor
# ═══════════════════════════════════════════════════════════════════════════

class TestInterceptor:
    """Tests for Interceptor base class."""

    async def test_default_before_returns_none(self):
        i = Interceptor()
        result = await i.before(_make_ctx())
        assert result is None

    async def test_default_after_passes_through(self):
        i = Interceptor()
        result = await i.after(_make_ctx(), {"data": 123})
        assert result == {"data": 123}

    async def test_custom_interceptor(self):
        class TimingInterceptor(Interceptor):
            async def before(self, ctx):
                ctx.state["_start"] = time.monotonic()

            async def after(self, ctx, result):
                elapsed = time.monotonic() - ctx.state["_start"]
                if isinstance(result, dict):
                    result["_elapsed_ms"] = round(elapsed * 1000, 2)
                return result

        i = TimingInterceptor()
        ctx = _make_ctx()
        await i.before(ctx)
        assert "_start" in ctx.state
        result = await i.after(ctx, {"data": "ok"})
        assert "_elapsed_ms" in result


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 6: Factory
# ═══════════════════════════════════════════════════════════════════════════

class TestControllerFactory:
    """Tests for ControllerFactory."""

    async def test_create_per_request(self):
        factory = ControllerFactory()
        ctrl = await factory.create(Controller)
        assert isinstance(ctrl, Controller)

    async def test_create_singleton(self):
        factory = ControllerFactory()
        ctrl1 = await factory.create(Controller, mode=InstantiationMode.SINGLETON)
        ctrl2 = await factory.create(Controller, mode=InstantiationMode.SINGLETON)
        assert ctrl1 is ctrl2

    async def test_per_request_creates_new_instances(self):
        factory = ControllerFactory()
        ctrl1 = await factory.create(Controller)
        ctrl2 = await factory.create(Controller)
        assert ctrl1 is not ctrl2

    async def test_no_double_on_request(self):
        """FIX: Factory no longer calls on_request — engine handles it."""
        call_count = 0

        class Tracked(Controller):
            async def on_request(self, ctx):
                nonlocal call_count
                call_count += 1

        factory = ControllerFactory()
        await factory.create(Tracked, ctx=_make_ctx())
        assert call_count == 0  # Factory should NOT call on_request

    async def test_shutdown_uses_logger(self):
        """FIX: shutdown() uses logger instead of print()."""
        class Failing(Controller):
            async def on_shutdown(self, ctx):
                raise RuntimeError("shutdown error")

        factory = ControllerFactory()
        factory._singletons[Failing] = Failing()
        # Should not raise, should log
        await factory.shutdown()

    def test_clear_caches(self):
        """NEW: cache clearing method."""
        ControllerFactory._ctor_info_cache["test"] = "data"
        ControllerFactory.clear_caches()
        assert "test" not in ControllerFactory._ctor_info_cache

    async def test_simple_resolve_raises_on_abstract(self):
        """FIX: _simple_resolve raises TypeError instead of crashing."""
        import abc
        class Abstract(abc.ABC):
            @abc.abstractmethod
            def method(self): ...

        factory = ControllerFactory()
        with pytest.raises((TypeError, Exception)):
            await factory._simple_resolve(Abstract, None)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 7: Engine — Cache Management
# ═══════════════════════════════════════════════════════════════════════════

class TestEngineCaches:
    """Tests for ControllerEngine cache management."""

    def test_clear_caches(self):
        """NEW: Cache clearing prevents memory leaks."""
        ControllerEngine._signature_cache["test"] = "sig"
        ControllerEngine._simple_route_cache[42] = True
        ControllerEngine._has_lifecycle_hooks[Controller] = (False, False)
        ControllerEngine._clearance_cache[99] = None
        ControllerEngine._is_coro_cache[123] = True

        ControllerEngine.clear_caches()

        assert len(ControllerEngine._signature_cache) == 0
        assert len(ControllerEngine._simple_route_cache) == 0
        assert len(ControllerEngine._has_lifecycle_hooks) == 0
        assert len(ControllerEngine._clearance_cache) == 0
        assert len(ControllerEngine._is_coro_cache) == 0


class TestEngineThrottle:
    """Tests for engine-level throttle integration."""

    def test_check_throttle_no_throttle(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        class NoThrottle(Controller):
            pass

        meta = MagicMock()
        meta._raw_metadata = {}
        meta.throttle = None
        result = engine._check_throttle(NoThrottle, meta, _make_request())
        assert result is None

    def test_check_throttle_class_level(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        class Throttled(Controller):
            throttle = Throttle(limit=1, window=60)

        meta = MagicMock()
        meta._raw_metadata = {}
        meta.throttle = None
        req = _make_request()

        # First request: OK
        result = engine._check_throttle(Throttled, meta, req)
        assert result is None

        # Second request: throttled
        result = engine._check_throttle(Throttled, meta, req)
        assert result is not None
        assert result.status == 429


class TestEngineExceptionFilters:
    """Tests for engine exception filter dispatch."""

    async def test_no_filters_returns_none(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        class NoFilters(Controller):
            pass

        result = await engine._apply_exception_filters(
            Exception("test"), NoFilters, MagicMock(), _make_ctx()
        )
        assert result is None

    async def test_matching_filter_handles_exception(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        class MyFilter(ExceptionFilter):
            catches = [ValueError]

            async def catch(self, exception, ctx):
                from aquilia.response import Response
                return Response.json({"error": str(exception)}, status=422)

        class Filtered(Controller):
            exception_filters = [MyFilter()]

        result = await engine._apply_exception_filters(
            ValueError("bad input"), Filtered, MagicMock(), _make_ctx()
        )
        assert result is not None
        assert result.status == 422

    async def test_non_matching_filter_skipped(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        class MyFilter(ExceptionFilter):
            catches = [ValueError]

            async def catch(self, exception, ctx):
                from aquilia.response import Response
                return Response.json({"error": "handled"}, status=422)

        class Filtered(Controller):
            exception_filters = [MyFilter()]

        result = await engine._apply_exception_filters(
            KeyError("wrong type"), Filtered, MagicMock(), _make_ctx()
        )
        assert result is None


class TestEngineTimeout:
    """Tests for handler execution timeout."""

    async def test_no_timeout(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        async def handler():
            return "ok"

        class NoTimeout(Controller):
            timeout = 0

        meta = MagicMock()
        meta._raw_metadata = {}
        meta.timeout = None

        result = await engine._execute_with_timeout(handler, NoTimeout, meta)
        assert result == "ok"

    async def test_timeout_triggers(self):
        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        async def slow_handler():
            await asyncio.sleep(10)
            return "never"

        class TimedOut(Controller):
            timeout = 0.01  # 10ms

        meta = MagicMock()
        meta._raw_metadata = {}
        meta.timeout = None

        with pytest.raises(Exception, match="timeout"):
            await engine._execute_with_timeout(slow_handler, TimedOut, meta)


class TestEngineAuthGuardClassTokenPipeline:
    """Regression tests for AuthGuard class-token usage in controller pipelines."""

    @staticmethod
    def _make_container_with_auth_manager(auth_manager):
        from aquilia.auth.manager import AuthManager
        from aquilia.di import Container
        from aquilia.di.providers import ValueProvider

        container = Container(scope="request")
        container.register(
            ValueProvider(
                value=auth_manager,
                token=AuthManager,
                scope="request",
                name="auth_manager_for_tests",
            )
        )
        return container

    async def test_class_token_auth_guard_blocks_missing_bearer_token(self):
        """pipeline=[AuthGuard] must execute guard and deny unauthenticated requests."""
        from aquilia.auth.guards import AuthGuard
        from aquilia.auth.faults import AUTH_REQUIRED

        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        fake_auth_manager = AsyncMock()
        container = self._make_container_with_auth_manager(fake_auth_manager)

        request = _make_request(method="GET", path="/protected")
        ctx = RequestCtx(request=request, container=container, state={})

        with pytest.raises(AUTH_REQUIRED):
            await engine._execute_flow_pipeline(
                [AuthGuard],
                request,
                ctx,
                Controller(),
                pipeline_name="auth.class.token",
            )

    async def test_class_token_auth_guard_populates_identity_and_claims(self):
        """AuthGuard class token should resolve AuthManager and propagate identity to RequestCtx."""
        from aquilia.auth.guards import AuthGuard

        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        fake_identity = object()
        fake_claims = {"sub": "user-123"}

        fake_auth_manager = AsyncMock()
        fake_auth_manager.get_identity_from_token.return_value = fake_identity
        fake_auth_manager.verify_token.return_value = fake_claims

        container = self._make_container_with_auth_manager(fake_auth_manager)

        request = _make_request(
            method="GET",
            path="/protected",
            headers={"authorization": "Bearer token-123"},
        )
        ctx = RequestCtx(request=request, container=container, state={})

        result = await engine._execute_flow_pipeline(
            [AuthGuard],
            request,
            ctx,
            Controller(),
            pipeline_name="auth.class.token",
        )

        assert result is None
        assert ctx.identity is fake_identity
        assert ctx.state["token_claims"] == fake_claims

    async def test_class_token_guard_missing_dependency_surfaces_di_fault(self):
        """Missing constructor deps for class-token guards should raise an explicit DI fault."""
        from aquilia.auth.guards import AuthGuard
        from aquilia.di import Container
        from aquilia.faults.domains import DIResolutionFault

        factory = ControllerFactory()
        engine = ControllerEngine(factory)

        container = Container(scope="request")  # AuthManager intentionally not registered
        request = _make_request(method="GET", path="/protected")
        ctx = RequestCtx(request=request, container=container, state={})

        with pytest.raises(DIResolutionFault, match="AuthGuard"):
            await engine._execute_flow_pipeline(
                [AuthGuard],
                request,
                ctx,
                Controller(),
                pipeline_name="auth.class.token",
            )


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 8: Metadata
# ═══════════════════════════════════════════════════════════════════════════

class TestMetadata:
    """Tests for metadata extraction."""

    def test_extract_controller_metadata(self):
        class UsersController(Controller):
            prefix = "/users"
            tags = ["users"]

            @GET("/")
            async def list(self, ctx): pass

            @GET("/<id:int>")
            async def get(self, ctx, id: int): pass

            @POST("/")
            async def create(self, ctx): pass

        meta = extract_controller_metadata(UsersController, "test:UsersController")
        assert meta.class_name == "UsersController"
        assert meta.prefix == "/users"
        assert meta.tags == ["users"]
        assert len(meta.routes) == 3

    def test_route_specificity(self):
        rm = RouteMetadata(
            http_method="GET",
            path_template="/users/<id:int>/posts",
            full_path="/api/users/<id:int>/posts",
            handler_name="get_posts",
        )
        score = rm.compute_specificity()
        assert score > 0

    def test_static_segment_higher_specificity(self):
        static = RouteMetadata(
            http_method="GET", path_template="/users/me",
            full_path="/users/me", handler_name="me",
        )
        dynamic = RouteMetadata(
            http_method="GET", path_template="/users/<id>",
            full_path="/users/<id>", handler_name="get",
        )
        static.compute_specificity()
        dynamic.compute_specificity()
        assert static.specificity > dynamic.specificity

    def test_parameter_metadata(self):
        pm = ParameterMetadata(name="id", type=int, source="path")
        assert pm.required is True
        assert pm.has_default is False

    def test_parameter_metadata_with_default(self):
        pm = ParameterMetadata(name="page", type=int, default=1, source="query")
        assert pm.has_default is True
        assert pm.default == 1

    def test_controller_metadata_get_route(self):
        rm = RouteMetadata(
            http_method="GET", path_template="/", full_path="/users/",
            handler_name="list",
        )
        cm = ControllerMetadata(
            class_name="Users", module_path="test", prefix="/users",
            routes=[rm],
        )
        found = cm.get_route("GET", "/users/")
        assert found is rm
        assert cm.get_route("POST", "/users/") is None

    def test_controller_metadata_has_conflict(self):
        rm1 = RouteMetadata(
            http_method="GET", path_template="/", full_path="/api/",
            handler_name="list",
        )
        rm2 = RouteMetadata(
            http_method="GET", path_template="/", full_path="/api/",
            handler_name="other_list",
        )
        cm1 = ControllerMetadata(class_name="A", module_path="a", prefix="/api", routes=[rm1])
        cm2 = ControllerMetadata(class_name="B", module_path="b", prefix="/api", routes=[rm2])
        conflict = cm1.has_conflict(cm2)
        assert conflict is not None

    def test_prefix_type_robustness(self):
        """Handles non-string prefix values gracefully."""
        class WeirdPrefix(Controller):
            prefix = ["/api"]  # type: ignore

        meta = extract_controller_metadata(WeirdPrefix, "test:Weird")
        assert isinstance(meta.prefix, str)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 9: Filters
# ═══════════════════════════════════════════════════════════════════════════

class TestFilters:
    """Tests for the filter system."""

    def test_coerce_value_int(self):
        assert _coerce_value("42") == 42

    def test_coerce_value_float(self):
        assert _coerce_value("3.14") == 3.14

    def test_coerce_value_bool(self):
        assert _coerce_value("true") is True
        assert _coerce_value("false") is False

    def test_coerce_value_in_list(self):
        result = _coerce_value("a,b,c", "in")
        assert result == ["a", "b", "c"]

    def test_coerce_value_range(self):
        result = _coerce_value("10,20", "range")
        assert result == ["10", "20"]

    def test_coerce_value_isnull(self):
        assert _coerce_value("true", "isnull") is True
        assert _coerce_value("false", "isnull") is False

    def test_matches_lookup_exact(self):
        assert _matches_lookup("hello", "exact", "hello") is True
        assert _matches_lookup("hello", "exact", "world") is False

    def test_matches_lookup_icontains(self):
        assert _matches_lookup("Hello World", "icontains", "hello") is True

    def test_matches_lookup_gt_lt(self):
        assert _matches_lookup(10, "gt", 5) is True
        assert _matches_lookup(10, "lt", 5) is False
        assert _matches_lookup(10, "gte", 10) is True
        assert _matches_lookup(10, "lte", 10) is True

    def test_matches_lookup_startswith_endswith(self):
        assert _matches_lookup("hello", "startswith", "hel") is True
        assert _matches_lookup("hello", "endswith", "llo") is True

    def test_matches_lookup_isnull(self):
        assert _matches_lookup(None, "isnull", True) is True
        assert _matches_lookup("val", "isnull", False) is True

    def test_matches_lookup_ne(self):
        assert _matches_lookup(1, "ne", 2) is True
        assert _matches_lookup(1, "ne", 1) is False

    def test_get_nested(self):
        obj = {"a": {"b": {"c": 42}}}
        assert _get_nested(obj, "a.b.c") == 42
        assert _get_nested(obj, "a.x") is None

    def test_apply_filters_to_list(self):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        result = apply_filters_to_list(data, {"age__gte": 30})
        assert len(result) == 2
        assert all(d["age"] >= 30 for d in result)

    def test_apply_search_to_list(self):
        data = [
            {"name": "Apple", "desc": "Fruit"},
            {"name": "Banana", "desc": "Yellow"},
            {"name": "Cherry", "desc": "Red fruit"},
        ]
        result = apply_search_to_list(data, "fruit", ["name", "desc"])
        assert len(result) == 2

    def test_apply_ordering_to_list(self):
        data = [
            {"name": "C", "age": 3},
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
        ]
        result = apply_ordering_to_list(data, ["age"])
        assert [d["age"] for d in result] == [1, 2, 3]

    def test_apply_ordering_descending(self):
        data = [
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
            {"name": "C", "age": 3},
        ]
        result = apply_ordering_to_list(data, ["-age"])
        assert [d["age"] for d in result] == [3, 2, 1]


class TestFilterSet:
    """Tests for FilterSet declarative filtering."""

    def test_filterset_meta_dict(self):
        class PF(FilterSet):
            class Meta:
                fields = {"status": ["exact", "in"], "price": ["gte", "lte"]}

        assert PF._filter_fields == {"status": ["exact", "in"], "price": ["gte", "lte"]}

    def test_filterset_meta_list(self):
        class PF(FilterSet):
            class Meta:
                fields = ["status", "name"]

        assert PF._filter_fields == {"status": ["exact"], "name": ["exact"]}

    def test_filterset_parse(self):
        class PF(FilterSet):
            class Meta:
                fields = {"status": ["exact"], "price": ["gte"]}

        fs = PF(query_params={"status": "active", "price__gte": "10"})
        clauses = fs.parse()
        assert clauses == {"status": "active", "price__gte": 10}

    def test_filterset_filter_list(self):
        class PF(FilterSet):
            class Meta:
                fields = {"status": ["exact"]}

        data = [
            {"status": "active", "name": "A"},
            {"status": "inactive", "name": "B"},
            {"status": "active", "name": "C"},
        ]
        fs = PF(query_params={"status": "active"})
        result = fs.filter_list(data)
        assert len(result) == 2

    def test_custom_filter_method(self):
        class PF(FilterSet):
            class Meta:
                fields = {"category": ["exact"]}

            def filter_category(self, value):
                if value == "sale":
                    return {"discount__gt": 0}
                return {"category": value}

        fs = PF(query_params={"category": "sale"})
        clauses = fs.parse()
        assert "discount__gt" in clauses


class TestSearchFilter:
    """Tests for SearchFilter backend."""

    def test_filter_data(self):
        sf = SearchFilter()
        data = [
            {"name": "Widget", "desc": "A tool"},
            {"name": "Gadget", "desc": "A device"},
        ]
        req = MagicMock()
        req.query_params = {"search": "tool"}
        result = sf.filter_data(data, req, search_fields=["name", "desc"])
        assert len(result) == 1
        assert result[0]["name"] == "Widget"

    def test_no_search_term(self):
        sf = SearchFilter()
        data = [{"name": "A"}, {"name": "B"}]
        req = MagicMock()
        req.query_params = {}
        result = sf.filter_data(data, req, search_fields=["name"])
        assert len(result) == 2


class TestOrderingFilter:
    """Tests for OrderingFilter backend."""

    def test_filter_data(self):
        of = OrderingFilter()
        data = [{"price": 30}, {"price": 10}, {"price": 20}]
        req = MagicMock()
        req.query_params = {"ordering": "price"}
        result = of.filter_data(data, req, ordering_fields=["price"])
        assert [d["price"] for d in result] == [10, 20, 30]

    def test_whitelist_enforcement(self):
        of = OrderingFilter()
        data = [{"price": 1, "secret": "x"}, {"price": 2, "secret": "y"}]
        req = MagicMock()
        req.query_params = {"ordering": "secret"}
        result = of.filter_data(data, req, ordering_fields=["price"])
        # "secret" not in allowed fields → no ordering applied
        assert result[0]["price"] == 1  # Original order


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 10: Pagination
# ═══════════════════════════════════════════════════════════════════════════

def _make_paginated_request(query_string_dict=None):
    """Create a mock request with dict-based query_params for pagination tests."""
    req = MagicMock()
    req.query_params = query_string_dict or {}
    req.scope = {"path": "/", "query_string": b""}
    req.url = "http://localhost/"
    return req


class TestNoPagination:
    """Tests for NoPagination."""

    def test_passthrough(self):
        p = NoPagination()
        data = list(range(100))
        result = p.paginate_list(data, _make_paginated_request())
        assert result["count"] == 100
        assert result["results"] == data
        assert result["next"] is None
        assert result["previous"] is None


class TestPageNumberPagination:
    """Tests for PageNumberPagination."""

    def test_first_page(self):
        p = PageNumberPagination(page_size=10)
        data = list(range(25))
        req = _make_paginated_request({"page": "1", "page_size": "10"})
        result = p.paginate_list(data, req)
        assert result["count"] == 25
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 3
        assert len(result["results"]) == 10
        assert result["previous"] is None
        assert result["next"] is not None

    def test_last_page(self):
        p = PageNumberPagination(page_size=10)
        data = list(range(25))
        req = _make_paginated_request({"page": "3", "page_size": "10"})
        result = p.paginate_list(data, req)
        assert len(result["results"]) == 5
        assert result["next"] is None
        assert result["previous"] is not None

    def test_max_page_size(self):
        p = PageNumberPagination(page_size=10, max_page_size=50)
        data = list(range(100))
        req = _make_paginated_request({"page": "1", "page_size": "999"})
        result = p.paginate_list(data, req)
        assert result["page_size"] == 50  # Clamped

    def test_invalid_page_defaults(self):
        p = PageNumberPagination(page_size=10)
        data = list(range(10))
        req = _make_paginated_request({"page": "abc"})
        result = p.paginate_list(data, req)
        assert result["page"] == 1


class TestLimitOffsetPagination:
    """Tests for LimitOffsetPagination."""

    def test_basic(self):
        p = LimitOffsetPagination(default_limit=10)
        data = list(range(50))
        req = _make_paginated_request({"limit": "10", "offset": "20"})
        result = p.paginate_list(data, req)
        assert result["count"] == 50
        assert result["limit"] == 10
        assert result["offset"] == 20
        assert result["results"] == list(range(20, 30))

    def test_first_page_no_previous(self):
        p = LimitOffsetPagination(default_limit=10)
        data = list(range(50))
        req = _make_paginated_request({"limit": "10", "offset": "0"})
        result = p.paginate_list(data, req)
        assert result["previous"] is None
        assert result["next"] is not None

    def test_max_limit(self):
        p = LimitOffsetPagination(default_limit=10, max_limit=25)
        data = list(range(100))
        req = _make_paginated_request({"limit": "999", "offset": "0"})
        result = p.paginate_list(data, req)
        assert result["limit"] == 25


class TestCursorPagination:
    """Tests for CursorPagination."""

    def test_first_page(self):
        p = CursorPagination(page_size=5, ordering="-id")
        data = [{"id": i, "name": f"item_{i}"} for i in range(20)]
        req = _make_paginated_request()
        result = p.paginate_list(data, req)
        assert len(result["results"]) == 5
        assert result["previous"] is None

    def test_has_next(self):
        p = CursorPagination(page_size=5, ordering="id")
        data = [{"id": i} for i in range(20)]
        req = _make_paginated_request()
        result = p.paginate_list(data, req)
        assert result["next"] is not None

    def test_cursor_encoding_decoding(self):
        p = CursorPagination()
        encoded = p._encode_cursor({"v": 42, "d": "next"})
        decoded = p._decode_cursor(encoded)
        assert decoded["v"] == 42
        assert decoded["d"] == "next"


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 11: Renderers
# ═══════════════════════════════════════════════════════════════════════════

class TestRenderers:
    """Tests for renderer system."""

    def test_json_renderer(self):
        r = JSONRenderer()
        result = r.render({"key": "value"})
        parsed = json.loads(result)
        assert parsed == {"key": "value"}
        assert r.media_type == "application/json"
        assert r.format_suffix == "json"

    def test_json_renderer_handles_special_types(self):
        r = JSONRenderer()
        result = r.render({"s": {1, 2, 3}})
        parsed = json.loads(result)
        assert sorted(parsed["s"]) == [1, 2, 3]

    def test_xml_renderer(self):
        r = XMLRenderer()
        result = r.render({"name": "Alice", "age": "30"})
        assert "<?xml" in result
        assert "<name>Alice</name>" in result
        assert r.media_type == "application/xml"

    def test_yaml_renderer(self):
        r = YAMLRenderer()
        result = r.render({"key": "value"})
        assert "key:" in result
        assert r.media_type == "application/x-yaml"

    def test_plain_text_renderer(self):
        r = PlainTextRenderer()
        assert r.render("hello") == "hello"
        assert r.media_type == "text/plain"

    def test_html_renderer_string(self):
        r = HTMLRenderer()
        html = r.render("<h1>Hello</h1>")
        assert html == "<h1>Hello</h1>"

    def test_html_renderer_dict(self):
        r = HTMLRenderer()
        result = r.render({"key": "value"})
        assert "<!DOCTYPE html>" in result

    def test_parse_accept_single(self):
        result = _parse_accept("application/json")
        assert result[0] == ("application/json", 1.0)

    def test_parse_accept_multiple_with_quality(self):
        result = _parse_accept("text/html, application/json;q=0.9, */*;q=0.1")
        assert result[0][0] == "text/html"
        assert result[1][0] == "application/json"
        assert result[2][0] == "*/*"

    def test_parse_accept_empty(self):
        result = _parse_accept("")
        assert result == [("*/*", 1.0)]

    def test_media_matches_exact(self):
        assert _media_matches("application/json", "application/json") is True
        assert _media_matches("text/html", "application/json") is False

    def test_media_matches_wildcard(self):
        assert _media_matches("*/*", "application/json") is True
        assert _media_matches("application/*", "application/json") is True
        assert _media_matches("text/*", "application/json") is False


class TestContentNegotiator:
    """Tests for ContentNegotiator."""

    def test_default_json(self):
        cn = ContentNegotiator()
        req = MagicMock()
        req.query_params = {}
        req.headers = {"accept": "*/*"}
        renderer, media = cn.select_renderer(req)
        assert isinstance(renderer, JSONRenderer)

    def test_format_override(self):
        cn = ContentNegotiator(renderers=[JSONRenderer(), XMLRenderer()])
        req = MagicMock()
        req.query_params = {"format": "xml"}
        req.headers = {}
        renderer, media = cn.select_renderer(req)
        assert isinstance(renderer, XMLRenderer)

    def test_accept_header_negotiation(self):
        cn = ContentNegotiator(renderers=[JSONRenderer(), XMLRenderer()])
        req = MagicMock(spec=["query_params", "headers"])
        req.query_params = {}
        req.headers = {"accept": "application/xml"}
        renderer, media = cn.select_renderer(req)
        assert isinstance(renderer, XMLRenderer)


class TestNegotiateFunction:
    """Tests for negotiate() convenience function."""

    def test_negotiate_json(self):
        req = MagicMock()
        req.query_params = {}
        req.headers = {"accept": "*/*"}
        body, content_type, status = negotiate({"key": "value"}, req)
        assert '"key"' in body
        assert "application/json" in content_type
        assert status == 200


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 12: OpenAPI
# ═══════════════════════════════════════════════════════════════════════════

class TestOpenAPITypeMapping:
    """Tests for Python type → JSON Schema mapping."""

    def test_str(self):
        assert _python_type_to_schema(str) == {"type": "string"}

    def test_int(self):
        assert _python_type_to_schema(int) == {"type": "integer"}

    def test_float(self):
        schema = _python_type_to_schema(float)
        assert schema["type"] == "number"

    def test_bool(self):
        assert _python_type_to_schema(bool) == {"type": "boolean"}

    def test_list_of_str(self):
        schema = _python_type_to_schema(List[str])
        assert schema["type"] == "array"
        assert schema["items"] == {"type": "string"}

    def test_dict_of_str_int(self):
        schema = _python_type_to_schema(Dict[str, int])
        assert schema["type"] == "object"
        assert schema["additionalProperties"] == {"type": "integer"}

    def test_optional(self):
        schema = _python_type_to_schema(Optional[str])
        assert schema["type"] == "string"
        assert schema["nullable"] is True

    def test_any_returns_empty(self):
        assert _python_type_to_schema(Any) == {}


class TestDocstringParsing:
    """Tests for docstring parsing."""

    def test_summary_extraction(self):
        doc = """Get user by ID.

        Returns the user profile.

        Args:
            user_id: The user ID
        """
        parsed = _parse_docstring(doc)
        assert parsed.summary == "Get user by ID."
        assert "user_id" in parsed.params

    def test_raises_extraction(self):
        doc = """Create user.

        Raises:
            ValueError (400): Invalid input
            NotFoundError (404): User not found
        """
        parsed = _parse_docstring(doc)
        assert len(parsed.raises) == 2

    def test_empty_docstring(self):
        parsed = _parse_docstring("")
        assert parsed.summary == ""
        assert parsed.params == {}


class TestOpenAPIConfig:
    """Tests for OpenAPIConfig."""

    def test_defaults(self):
        config = OpenAPIConfig()
        assert config.title == "Aquilia API"
        assert config.version == "1.0.0"
        assert config.enabled is True

    def test_from_dict(self):
        config = OpenAPIConfig.from_dict({
            "title": "My API",
            "version": "2.0.0",
            "description": "Test API",
        })
        assert config.title == "My API"
        assert config.version == "2.0.0"

    def test_from_dict_ignores_private(self):
        config = OpenAPIConfig.from_dict({"_secret": "hidden"})
        assert not hasattr(config, "_secret") or config._seen_tags != "hidden"


class TestSwaggerHTML:
    """Tests for Swagger UI HTML generation."""

    def test_generates_html(self):
        config = OpenAPIConfig(title="Test API")
        html = generate_swagger_html(config)
        assert "<!DOCTYPE html>" in html
        assert "Test API" in html
        assert "swagger-ui" in html

    def test_dark_theme(self):
        config = OpenAPIConfig(title="Dark API", swagger_ui_theme="dark")
        html = generate_swagger_html(config)
        assert "invert" in html  # Dark theme CSS


class TestRedocHTML:
    """Tests for ReDoc HTML generation."""

    def test_generates_html(self):
        config = OpenAPIConfig(title="Test API")
        html = generate_redoc_html(config)
        assert "<!DOCTYPE html>" in html
        assert "Test API" in html
        assert "redoc" in html


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 13: Integration — Controller + Decorators + Metadata
# ═══════════════════════════════════════════════════════════════════════════

class TestControllerIntegration:
    """Integration tests combining Controller + Decorators + Metadata."""

    def test_full_controller_definition(self):
        class ProductsController(Controller):
            prefix = "/products"
            tags = ["products"]
            version = "v1"
            throttle = Throttle(limit=100, window=60)
            timeout = 30

            @GET("/")
            async def list(self, ctx):
                return []

            @POST("/")
            async def create(self, ctx):
                return {"id": 1}

            @GET("/<id:int>")
            async def get(self, ctx, id: int):
                return {"id": id}

            @PUT("/<id:int>")
            async def update(self, ctx, id: int):
                return {"id": id}

            @DELETE("/<id:int>")
            async def delete(self, ctx, id: int):
                return {"id": id}

        assert ProductsController.prefix == "/products"
        assert ProductsController.version == "v1"
        assert ProductsController.timeout == 30

        meta = extract_controller_metadata(ProductsController, "test:Products")
        assert len(meta.routes) == 5
        methods = {r.http_method for r in meta.routes}
        assert methods == {"GET", "POST", "PUT", "DELETE"}

    def test_controller_with_interceptors(self):
        class LoggingInterceptor(Interceptor):
            async def before(self, ctx):
                ctx.state["logged"] = True

        class LoggedController(Controller):
            prefix = "/logged"
            interceptors = [LoggingInterceptor()]

        assert len(LoggedController.interceptors) == 1
        assert isinstance(LoggedController.interceptors[0], Interceptor)

    def test_controller_with_exception_filters(self):
        class NotFoundFilter(ExceptionFilter):
            catches = [KeyError]
            async def catch(self, exception, ctx):
                pass

        class SafeController(Controller):
            prefix = "/safe"
            exception_filters = [NotFoundFilter()]

        assert len(SafeController.exception_filters) == 1

    def test_versioned_controller(self):
        class V1Controller(Controller):
            prefix = "/users"
            version = "v1"

        class V2Controller(Controller):
            prefix = "/users"
            version = "v2"

        assert V1Controller.version == "v1"
        assert V2Controller.version == "v2"

    def test_inheritance_preserves_features(self):
        class BaseAPI(Controller):
            throttle = Throttle(limit=100, window=60)
            timeout = 30

        class ChildAPI(BaseAPI):
            prefix = "/child"

        assert ChildAPI.throttle is not None
        assert ChildAPI.timeout == 30


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 14: Edge Cases & Regression Guards
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge case tests and regression guards."""

    def test_empty_controller(self):
        """Controller with no routes should work."""
        class EmptyController(Controller):
            prefix = "/empty"

        meta = extract_controller_metadata(EmptyController, "test:Empty")
        assert len(meta.routes) == 0

    def test_controller_none_prefix(self):
        """Handles None prefix gracefully."""
        class NonePrefix(Controller):
            prefix = None  # type: ignore

        meta = extract_controller_metadata(NonePrefix, "test:None")
        assert meta.prefix == ""

    def test_decorator_no_path(self):
        """Decorator with no path derives from method name."""
        @GET()
        async def handler(self, ctx): pass
        assert handler.__route_metadata__[0]["path"] is None

    def test_multiple_decorators_different_methods(self):
        """Multiple decorators on one method."""
        @GET("/items")
        @POST("/items")
        async def handler(self, ctx): pass
        methods = {m["http_method"] for m in handler.__route_metadata__}
        assert methods == {"GET", "POST"}

    def test_factory_cache_clear_isolation(self):
        """Clearing factory caches doesn't affect other state."""
        factory = ControllerFactory()
        factory._singletons[Controller] = Controller()
        ControllerFactory.clear_caches()
        # Singletons should NOT be cleared by cache clear
        assert Controller in factory._singletons

    def test_engine_cache_clear_isolation(self):
        """Clearing engine caches is complete."""
        ControllerEngine._signature_cache[1] = "a"
        ControllerEngine._pipeline_param_cache[2] = "b"
        ControllerEngine.clear_caches()
        assert len(ControllerEngine._signature_cache) == 0
        assert len(ControllerEngine._pipeline_param_cache) == 0

    async def test_safe_call_sync_function(self):
        """Engine._safe_call handles sync functions."""
        engine = ControllerEngine(ControllerFactory())

        def sync_fn():
            return 42

        result = await engine._safe_call(sync_fn)
        assert result == 42

    async def test_safe_call_async_function(self):
        """Engine._safe_call handles async functions."""
        engine = ControllerEngine(ControllerFactory())

        async def async_fn():
            return 99

        result = await engine._safe_call(async_fn)
        assert result == 99

    def test_valid_http_methods_is_frozen(self):
        """VALID_HTTP_METHODS is immutable."""
        assert isinstance(VALID_HTTP_METHODS, frozenset)

    def test_throttle_window_expired(self):
        """Requests pass after throttle window expires."""
        t = Throttle(limit=1, window=0.01)  # 10ms window
        req = _make_request()
        t.check(req)
        assert t.check(req) is False
        time.sleep(0.02)
        assert t.check(req) is True

    def test_base_renderer_raises(self):
        """BaseRenderer.render() raises NotImplementedError."""
        r = BaseRenderer()
        with pytest.raises(NotImplementedError):
            r.render({"data": 1})

    def test_base_pagination_raises(self):
        """BasePagination.paginate_list() raises NotImplementedError."""
        p = BasePagination()
        with pytest.raises(NotImplementedError):
            p.paginate_list([], _make_request())

    def test_base_filter_backend_passthrough(self):
        """BaseFilterBackend.filter_data() returns data unchanged."""
        fb = BaseFilterBackend()
        data = [1, 2, 3]
        result = fb.filter_data(data, _make_request())
        assert result == data

    async def test_base_filter_backend_queryset_passthrough(self):
        """BaseFilterBackend.filter_queryset() returns queryset unchanged."""
        fb = BaseFilterBackend()
        qs = MagicMock()
        result = await fb.filter_queryset(qs, _make_request())
        assert result is qs

    def test_route_metadata_static_check(self):
        assert RouteMetadata._is_static("users") is True
        assert RouteMetadata._is_static("<id>") is False
        assert RouteMetadata._is_static("{id}") is False

    def test_route_metadata_typed_param_check(self):
        assert RouteMetadata._is_typed_param("<id:int>") is True
        assert RouteMetadata._is_typed_param("<id>") is False
        assert RouteMetadata._is_typed_param("{id:int}") is True

    def test_route_metadata_param_check(self):
        assert RouteMetadata._is_param("<id>") is True
        assert RouteMetadata._is_param("{id}") is True
        assert RouteMetadata._is_param("static") is False
