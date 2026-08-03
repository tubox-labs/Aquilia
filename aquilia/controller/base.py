"""
Controller Base Class

Provides the base Controller class, RequestCtx abstraction,
and controller-level features: versioning, throttling, interceptors,
exception filters, and handler timeouts.

Performance (v5 — native context):
- When the native engine is available, RequestCtx subclasses the C++
  ``RequestContext``, whose slots are nanobind data descriptors. A slot write is
  then a direct field store instead of a ``__setattr__`` round trip: measured
  58 ns -> 14.5 ns per write, and construction 555 ns -> 34 ns. With ~24 writes
  per request that is the dominant remaining per-request cost.
- Without the native engine, the pure-Python ``__slots__`` implementation is
  used unchanged. Both expose an identical API, including the ``_extra``
  escape hatch.
- The object pool was removed after measurement showed it was net-negative
  (1,972 ns acquire+release vs 588 ns direct construction). ``_ctx_pool``
  remains as a no-op shim for import compatibility.
"""

import logging
import os as _os
import time
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Any, Literal, Optional, overload

from aquilia._core_loader import NATIVE as _NATIVE
from aquilia._core_loader import RequestContext as _NativeRequestContext
from aquilia._datastructures import Headers, MultiDict
from aquilia._uploads import FormData
from aquilia.faults.domains import EffectNotAcquiredFault

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.effects import (
        CacheHandle,
        CacheServiceHandle,
        DBTxHandle,
        HTTPHandle,
        QueueHandle,
        StorageHandle,
        TaskQueueHandle,
    )
    from aquilia.request import Request
    from aquilia.response import Response
    from aquilia.sessions import Session
else:
    DBTxHandle = Any
    CacheHandle = Any
    CacheServiceHandle = Any
    QueueHandle = Any
    TaskQueueHandle = Any
    HTTPHandle = Any
    StorageHandle = Any

logger = logging.getLogger("aquilia.controller")

# Reusable empty dict to avoid allocation when state is unused
_EMPTY_STATE: dict[str, Any] = {}
_CURRENT_REQUEST_CTX: ContextVar["RequestCtx | None"] = ContextVar("aquilia_controller_request_ctx", default=None)


def _set_current_request_ctx(ctx: "RequestCtx") -> Token["RequestCtx | None"]:
    """Bind the current request context for helper APIs invoked during handler execution."""
    return _CURRENT_REQUEST_CTX.set(ctx)


def _reset_current_request_ctx(token: Token["RequestCtx | None"]) -> None:
    """Reset the bound request context token."""
    _CURRENT_REQUEST_CTX.reset(token)


def _get_current_request_ctx() -> "RequestCtx | None":
    """Get the current request context for the active task, if any."""
    return _CURRENT_REQUEST_CTX.get()


# ═══════════════════════════════════════════════════════════════════════════
#  RequestCtx
# ═══════════════════════════════════════════════════════════════════════════


# ── Base selection for RequestCtx ────────────────────────────────────────
# With the native engine, RequestCtx derives from the C++ RequestContext, whose
# seven slots are nanobind data descriptors. Attribute writes then bypass
# __setattr__ entirely (58 ns -> 14.5 ns) and construction drops 555 ns -> 34 ns.
#
# The native base is declared with dynamic_attr(), so instances get a __dict__
# and unknown attribute writes land there instead of raising -- which is what
# keeps the `_extra` escape hatch working without a __setattr__ override.
#
# Without the engine, the base is `object` and the pure-Python __slots__ path
# below is used unchanged.
_CtxBase: Any = _NativeRequestContext if _NATIVE else object


class RequestCtx(_CtxBase):
    """
    Request context provided to controller methods.

    Compact memory layout and fast attribute access: native fixed slots when the
    core engine is available, ``__slots__`` otherwise.  Middleware/plugins can
    attach data via the ``state`` dict or by setting attributes directly (the
    ``_extra`` escape hatch for truly dynamic attributes).
    """

    # Only meaningful on the pure-Python path. When the base is the native type,
    # the seven real fields are descriptors on that base and instances carry a
    # __dict__ from dynamic_attr(), so declaring __slots__ here would shadow the
    # descriptors with empty slot storage. `_extra` alone is declared so the
    # attribute exists on both paths.
    __slots__ = (
        (
            "request",
            "identity",
            "session",
            "auth",
            "container",
            "state",
            "request_id",
            "_extra",
        )
        if not _NATIVE
        else ()
    )

    def __init__(
        self,
        request: "Request",
        identity: Optional["Identity"] = None,
        session: Optional["Session"] = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        if _NATIVE:
            # The native base has a nullary constructor; slots default to None.
            super().__init__()
        self.request = request
        self.identity = identity
        self.session = session
        self.auth = auth
        self.container = container
        self.state: dict[str, Any] = state if state is not None else {}
        self.request_id = request_id
        if not _NATIVE:
            # On the native path `_extra` is served by __getattr__/__setattr__
            # over the instance __dict__; there is no slot to initialise.
            self._extra: dict[str, Any] | None = None

    @overload
    def get_effect(self, name: Literal["DBTx", "db"]) -> DBTxHandle: ...

    @overload
    def get_effect(self, name: Literal["Cache", "cache"]) -> CacheHandle | CacheServiceHandle: ...

    @overload
    def get_effect(self, name: Literal["Queue", "queue"]) -> QueueHandle | TaskQueueHandle: ...

    @overload
    def get_effect(self, name: Literal["HTTP", "http"]) -> HTTPHandle: ...

    @overload
    def get_effect(self, name: Literal["Storage", "storage"]) -> StorageHandle: ...

    @overload
    def get_effect(self, name: str) -> Any: ...

    def get_effect(self, name: str) -> Any:
        """
        Get an acquired effect resource by name.

        Delegates to ``request.get_effect(name)``.  Effects must be declared
        with ``@requires(name)`` below the HTTP method decorator and the
        ``EffectMiddleware`` must be active in the middleware chain.

        Raises:
            ``EffectNotAcquiredFault``: with actionable diagnostics if the
            effect was not acquired for this request.

        Examples::

            @POST("/orders")
            @requires("DBTx", "Cache")
            async def create(self, ctx: RequestCtx):
                db    = ctx.get_effect("DBTx")
                cache = ctx.get_effect("Cache")
        """
        if self.request is not None:
            return self.request.get_effect(name)

        raise EffectNotAcquiredFault(
            effect_name=name,
            reason="No request object available in this context.",
            middleware_active=False,
        )

    def has_effect(self, name: str) -> bool:
        """Check if an effect resource is currently acquired."""
        if self.request is not None:
            return self.request.has_effect(name)
        return False

    # -- dynamic attribute escape hatch for plugins/middleware -------
    if _NATIVE:
        # Native path: the seven real fields are data descriptors on the C++ base
        # and dynamic_attr() gives instances a __dict__, so normal attribute
        # lookup already handles both. NO __setattr__ override is defined here on
        # purpose -- defining one would reintroduce the 58 ns/write cost this
        # phase exists to remove, on every field write of every request.
        #
        # Only __getattr__ is needed, and only for the `_extra` contract: reading
        # `ctx._extra` must yield the dynamic attributes as a dict (or None when
        # there are none), matching the pure-Python behaviour.
        def __getattr__(self, name: str) -> Any:
            # Only called when normal lookup fails, so slots and __dict__ entries
            # never reach here.
            if name == "_extra":
                d = object.__getattribute__(self, "__dict__")
                return d if d else None
            raise AttributeError(f"'RequestCtx' object has no attribute {name!r}")

    else:

        def __getattr__(self, name: str) -> Any:
            """Fallback for dynamic attributes stored in _extra."""
            # __slots__ attrs are handled natively; this only fires for unknowns
            extra = object.__getattribute__(self, "_extra")
            if extra is not None and name in extra:
                return extra[name]
            raise AttributeError(f"'RequestCtx' object has no attribute {name!r}")

        def __setattr__(self, name: str, value: Any) -> None:
            """Allow setting extra dynamic attributes via _extra dict."""
            # Fast path: known slots
            try:
                object.__setattr__(self, name, value)
            except AttributeError:
                extra = object.__getattribute__(self, "_extra")
                if extra is None:
                    extra = {}
                    object.__setattr__(self, "_extra", extra)
                extra[name] = value

    @property
    def path(self) -> str:
        """Request path."""
        return self.request.path

    @property
    def method(self) -> str:
        """Request method."""
        return self.request.method

    @property
    def headers(self) -> Headers:
        """Request headers."""
        return self.request.headers

    @property
    def query_params(self) -> MultiDict:
        """Query parameters (parsed from query string)."""
        return self.request.query_params

    def query_param(self, key: str, default: str | None = None) -> str | None:
        """Get single query parameter."""
        return self.request.query_param(key, default)

    async def json(self) -> Any:
        """Parse request body as JSON."""
        return await self.request.json()

    async def body(self) -> bytes:
        """Read raw request body bytes."""
        return await self.request.body()

    async def form(self) -> FormData:
        """Parse request body as form data."""
        return await self.request.form()

    async def multipart(self):
        """Parse multipart/form-data (file uploads)."""
        return await self.request.multipart()


# ═══════════════════════════════════════════════════════════════════════════
#  RequestCtx Object Pool  (retired)
# ═══════════════════════════════════════════════════════════════════════════
#
# _RequestCtxPool was removed after measurement showed it was net-negative:
# acquire()+release() cost 1,972 ns versus 588 ns to simply construct a
# RequestCtx. The pool set 8 fields on acquire and 8 more on release, and
# every one of those 16 writes went through RequestCtx.__setattr__ (a
# try/except override, 3.1x slower than a native slot write), plus an
# os.urandom(16).hex() call (716 ns) to regenerate a request_id that
# RequestIdMiddleware immediately overwrites on the very next hop.
#
# Direct construction is 70% faster and allocation was never the bottleneck
# (__slots__ objects are cheap; tracemalloc measured <1 byte/op amortised).
#
# The __setattr__ override is deliberately KEPT: RequestCtx's docstring
# advertises `_extra` as a public escape hatch for middleware and plugins, so
# removing it would break third-party code for a further ~469 ns. That
# remaining cost is addressed by the native RequestContext (Phase 9F), which
# gets native slot writes without changing the Python-visible contract.
#
# A module-level `_ctx_pool` shim is retained below for backward compatibility
# with any external caller that imported it.


class _RetiredCtxPool:
    """Backward-compatible no-op stand-in for the removed RequestCtx pool.

    ``acquire()`` constructs a fresh :class:`RequestCtx` and ``release()`` is a
    no-op. Kept so that external code importing ``_ctx_pool`` keeps working.
    """

    __slots__ = ()

    def acquire(
        self,
        request: "Request",
        identity: Optional["Identity"] = None,
        session: Optional["Session"] = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> RequestCtx:
        """Construct a fresh RequestCtx (no pooling)."""
        if request_id is None:
            request_id = _os.urandom(16).hex()
        return RequestCtx(
            request=request,
            identity=identity,
            session=session,
            auth=auth,
            container=container,
            state=state,
            request_id=request_id,
        )

    def release(self, ctx: RequestCtx) -> None:
        """No-op: contexts are garbage-collected normally."""
        return None


# Module-level shim singleton (retained for import compatibility)
_ctx_pool = _RetiredCtxPool()


# ═══════════════════════════════════════════════════════════════════════════
#  Exception Filter
# ═══════════════════════════════════════════════════════════════════════════


class ExceptionFilter:
    """
    Base class for exception filters.

    Exception filters intercept unhandled exceptions from controller
    handlers and convert them into proper HTTP responses.

    Usage::

        class NotFoundFilter(ExceptionFilter):
            catches = [KeyError, LookupError]

            async def catch(self, exception, ctx):
                return Response.json(
                    {"error": "Not found", "detail": str(exception)},
                    status=404,
                )

        class UsersController(Controller):
            prefix = "/users"
            exception_filters = [NotFoundFilter()]
    """

    catches: list[type] = []  # Exception types this filter handles

    async def catch(
        self,
        exception: Exception,
        ctx: "RequestCtx",
    ) -> Optional["Response"]:
        """
        Handle the exception and return a Response.

        Return ``None`` to let the exception propagate.
        """
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════
#  Interceptor -- before/after hooks
# ═══════════════════════════════════════════════════════════════════════════


class Interceptor:
    """
    Base class for controller interceptors.

    Interceptors wrap handler execution with before/after logic,
    supporting cross-cutting concerns like logging, caching, timing,
    and response transformation.

    Usage::

        class TimingInterceptor(Interceptor):
            async def before(self, ctx):
                ctx.state["_start"] = time.monotonic()

            async def after(self, ctx, result):
                elapsed = time.monotonic() - ctx.state["_start"]
                if isinstance(result, dict):
                    result["_elapsed_ms"] = round(elapsed * 1000, 2)
                return result

        class UsersController(Controller):
            prefix = "/users"
            interceptors = [TimingInterceptor()]
    """

    async def before(self, ctx: "RequestCtx") -> Optional["Response"]:
        """
        Called before the handler executes.

        Return a ``Response`` to short-circuit the handler.
        Return ``None`` to continue.
        """
        return None

    async def after(
        self,
        ctx: "RequestCtx",
        result: Any,
    ) -> Any:
        """
        Called after the handler executes.

        Receives the handler result and can transform it.
        """
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  Throttle -- Controller-level rate limiting
# ═══════════════════════════════════════════════════════════════════════════


class Throttle:
    """
    Simple sliding-window rate limiter with pluggable backends.

    Usage::

        class UsersController(Controller):
            throttle = Throttle(limit=100, window=60)  # 100 req / 60s

    Or per-route::

        @GET("/", throttle=Throttle(limit=10, window=60))
        async def list(self, ctx): ...
    """

    def __init__(self, limit: int = 100, window: int = 60, max_clients: int = 10000, backend: Any = None):
        self.limit = limit
        self.window = window
        self.max_clients = max_clients
        self.backend = backend
        self._requests: dict[str, list] = {}  # key -> [timestamps]
        self._last_cleanup: float = 0.0

    def _client_key(self, request: Any) -> str:
        """Extract a client identifier from the request.

        Delegates to ``request.client_ip()`` when available so that
        trusted-proxy chain validation is honoured.  Falls back to the
        ASGI scope's direct client tuple.
        """
        # Prefer the request object's validated client_ip()
        if hasattr(request, "client_ip") and callable(request.client_ip):
            try:
                return str(request.client_ip())
            except Exception:
                pass

        # Fallback: direct ASGI client (never trust X-Forwarded-For directly)
        if hasattr(request, "scope"):
            client = request.scope.get("client")
            if client:
                return str(client[0])
        return "unknown"

    def check(self, request: Any) -> bool:
        """
        Check if the request is within the rate limit (synchronous, backward compat).

        Returns True if allowed, False if throttled.
        """
        now = time.monotonic()
        key = self._client_key(request)

        # Periodic full cleanup (every window interval)
        if now - self._last_cleanup > self.window:
            self._cleanup_expired(now)
            self._last_cleanup = now

        if key not in self._requests:
            # SEC-CTRL-04: Evict oldest client if at capacity
            if len(self._requests) >= self.max_clients:
                self._evict_oldest(now)
            self._requests[key] = []

        # Prune expired entries for this client
        cutoff = now - self.window
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

        if len(self._requests[key]) >= self.limit:
            return False

        self._requests[key].append(now)
        return True

    def _cleanup_expired(self, now: float) -> None:
        """Remove all clients whose entries have fully expired."""
        cutoff = now - self.window
        expired_keys = [k for k, timestamps in self._requests.items() if not timestamps or timestamps[-1] <= cutoff]
        for k in expired_keys:
            del self._requests[k]

    def _evict_oldest(self, now: float) -> None:
        """Evict the client with the oldest last-access time."""
        if not self._requests:
            return
        oldest_key = None
        oldest_time = now
        for k, timestamps in self._requests.items():
            last_ts = timestamps[-1] if timestamps else 0.0
            if last_ts < oldest_time:
                oldest_time = last_ts
                oldest_key = k
        if oldest_key is not None:
            del self._requests[oldest_key]

    @property
    def retry_after(self) -> int:
        """Seconds until the window resets (approximate)."""
        return self.window

    def reset(self):
        """Clear all rate limit state (sync)."""
        self._requests.clear()

    async def acheck(self, request: Any) -> bool:
        """Async rate limit check using the configured backend."""
        key = self._client_key(request)
        if self.backend:
            return await self.backend.is_allowed(key, self.limit, self.window)

        # Fallback to in-memory check but safely wrapped in asyncio if needed, or just call check
        # Since sync check modifies dict, we'll just run it.
        # In a real scenario, MemoryThrottleBackend is provided if backend=None is handled appropriately
        # But we were told "When backend is None, use MemoryThrottleBackend (backward compat) / fallback to sync check".
        # We will just call the backend if set, otherwise instantiate MemoryThrottleBackend lazily or run sync check.
        # Actually, let's just run sync check if backend is missing.
        return self.check(request)

    @classmethod
    def with_redis(cls, redis_url: str, limit: int, window: int, **kwargs) -> "Throttle":
        from aquilia.controller.throttle import ThrottleBackendFactory

        backend = ThrottleBackendFactory.create(redis_url, **kwargs)
        return cls(limit=limit, window=window, backend=backend)

    @classmethod
    def with_memory(cls, limit: int, window: int, **kwargs) -> "Throttle":
        from aquilia.controller.throttle import ThrottleBackendFactory

        backend = ThrottleBackendFactory.create("memory", **kwargs)
        return cls(limit=limit, window=window, backend=backend)


# ═══════════════════════════════════════════════════════════════════════════
#  ControllerMeta -- descriptor metaclass to fix mutable defaults
# ═══════════════════════════════════════════════════════════════════════════


class _ControllerMeta(type):
    """
    Metaclass for Controller that prevents the mutable-default-list bug.

    When a subclass declares ``pipeline = [Auth.guard()]`` it must get
    its OWN list, not share the base-class list.  This metaclass copies
    ``pipeline``, ``tags``, ``interceptors``, and ``exception_filters``
    during class creation so that mutations to one subclass never leak
    to another.
    """

    _COPY_FIELDS = ("pipeline", "tags", "interceptors", "exception_filters")

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        try:
            cls = super().__new__(mcs, name, bases, namespace)
        except RuntimeError as e:
            from aquilia.faults.domains import ConfigInvalidFault

            if e.__cause__ is not None and isinstance(e.__cause__, ConfigInvalidFault):
                raise e.__cause__ from None
            raise
        for field in mcs._COPY_FIELDS:
            # If the subclass didn't explicitly set the field, copy from
            # the inherited value so each class has its own list.
            val = getattr(cls, field, None)
            if val is not None and isinstance(val, list):
                setattr(cls, field, list(val))
        return cls


# ═══════════════════════════════════════════════════════════════════════════
#  Controller
# ═══════════════════════════════════════════════════════════════════════════


class Controller(metaclass=_ControllerMeta):
    """
    Base Controller class.

    Controllers are class-based request handlers with:
    - Constructor DI injection
    - Method-level route definitions
    - Class-level and method-level pipelines
    - Lifecycle hooks
    - Template rendering support
    - API versioning
    - Rate limiting (throttle)
    - Interceptors (before/after handler hooks)
    - Exception filters (structured error handling)
    - Handler execution timeouts

    Class Attributes:
        prefix: URL prefix for all routes (e.g., "/users")
        pipeline: List of pipeline nodes applied to all methods
        tags: OpenAPI tags
        instantiation_mode: "per_request" or "singleton"
        version: API version string (e.g., "v1", "v2")
        throttle: Throttle instance for rate limiting
        interceptors: List of Interceptor instances
        exception_filters: List of ExceptionFilter instances
        timeout: Handler execution timeout in seconds (0 = no timeout)
        max_body_size: Max request body size in bytes (0 = no limit)

    Lifecycle Hooks:
        async def on_startup(self, ctx): Called at app startup (singleton only)
        async def on_shutdown(self, ctx): Called at app shutdown (singleton only)
        async def on_request(self, ctx): Called before each request
        async def on_response(self, ctx, response): Called after each request

    Pipeline vs. Clearance -- decision rule (section 5.2):
        Aquilia has two mechanisms to gate a request before the handler runs:

        1. pipeline -- use for middleware-style, non-identity cross-cutting
           concerns: rate-limit guards, logging enrichment, feature-flag checks,
           request-body transforms.  Items are FlowNode/FlowGuard subclasses or
           plain async callables that can short-circuit with a Response.

        2. clearance -- use for declarative, identity-aware access control
           (@require_clearance(), @require_roles(), @require_scopes()).
           Clearance is evaluated AFTER the pipeline, has direct access to the
           resolved Identity, and returns structured 401/403 via ClearanceEngine.

        Rule: auth/role/permission/scope checks -> clearance.
        Everything else (transforms, logging, non-identity guards) -> pipeline.
        Never duplicate the same check in both systems.

    Example:

        class UsersController(Controller):
            prefix = "/users"
            version = "v1"
            pipeline = [Auth.guard()]
            throttle = Throttle(limit=100, window=60)
            timeout = 30

            def __init__(self, repo: UserRepo, templates: TemplateEngine):
                self.repo = repo
                self.templates = templates

            @GET("/")
            async def list(self, ctx):
                users = self.repo.list_all()
                return self.render("users/list.html", {"users": users}, ctx)
    """

    # Class-level configuration
    prefix: str = ""
    pipeline: list[Any] = []
    tags: list[str] = []
    instantiation_mode: str = "per_request"  # or "singleton"

    # ── New industry-standard features ──
    version: str | None = None  # API version: "v1", "v2", etc.
    throttle: Throttle | None = None  # Rate limiting
    interceptors: list[Any] = []  # Interceptor instances
    exception_filters: list[Any] = []  # ExceptionFilter instances
    timeout: float = 0  # Handler timeout in seconds (0=disabled)
    max_body_size: int = 0  # Max body size in bytes (0=disabled)

    # Template engine (injected via DI)
    _template_engine: Any | None = None

    async def render(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
        request_ctx: RequestCtx | None = None,
        *,
        engine: Any | None = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> "Response":
        """
        Render template and return Response.

        Convenience method for template rendering in controllers.
        Automatically injects request context if available.

        Args:
            template_name: Template name
            context: Template variables
            request_ctx: Request context (auto-injects request/session/identity)
            engine: Template engine (optional, can be injected or passed)
            status: HTTP status code
            headers: Additional headers

        Returns:
            Response with rendered template

        Example:
        ```
            @GET("/profile")
            async def profile(self, ctx):
                user = await self.repo.get(ctx.identity.id)
                return await self.render("profile.html", {"user": user}, ctx)
        """
        from aquilia.response import Response

        # Allow render(...) to work without explicitly passing ctx from handlers.
        if request_ctx is None:
            request_ctx = _get_current_request_ctx()

        # Get template engine (if not provided as parameter)
        if engine is None:
            engine = getattr(self, "_template_engine", None) or getattr(self, "templates", None)

        return await Response.render(
            template_name, context, status=status, headers=headers, engine=engine, request_ctx=request_ctx
        )

    # Lifecycle hooks (optional)

    async def on_startup(self, ctx: RequestCtx) -> None:
        """
        Called when controller is initialized (singleton mode only).

        Use for one-time initialization like opening DB connections.
        """
        pass

    async def on_shutdown(self, ctx: RequestCtx) -> None:
        """
        Called when controller is destroyed (singleton mode only).

        Use for cleanup like closing connections.
        """
        pass

    async def on_request(self, ctx: RequestCtx) -> None:
        """
        Called before each request is processed.

        Use for per-request initialization or validation.
        """
        pass

    async def on_response(self, ctx: RequestCtx, response: "Response") -> "Response":
        """
        Called after each request is processed.

        Can modify the response before it's sent.

        Args:
            ctx: Request context
            response: The response to be sent

        Returns:
            Modified response
        """
        return response

    # Context manager support for per-request lifecycle

    async def __aenter__(self):
        """Enter request context (per-request mode)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit request context (per-request mode)."""
        pass
