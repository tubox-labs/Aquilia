"""
Controller Base Class

Provides the base Controller class, RequestCtx abstraction,
and controller-level features: versioning, throttling, interceptors,
exception filters, and handler timeouts.

Performance (v3 — scalability):
- RequestCtx uses __slots__ for ~40% faster attribute access.
- Object pool (_RequestCtxPool) eliminates per-request allocation.
- Pool uses a pre-allocated ring buffer; acquire() resets fields in-place.
"""

import logging
import time
from typing import TYPE_CHECKING, Any, Optional

from aquilia._datastructures import Headers, MultiDict
from aquilia._uploads import FormData

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.request import Request
    from aquilia.response import Response
    from aquilia.sessions import Session

logger = logging.getLogger("aquilia.controller")

# Reusable empty dict to avoid allocation when state is unused
_EMPTY_STATE: dict[str, Any] = {}


# ═══════════════════════════════════════════════════════════════════════════
#  RequestCtx
# ═══════════════════════════════════════════════════════════════════════════


class RequestCtx:
    """
    Request context provided to controller methods.

    Uses __slots__ for compact memory layout and faster attribute access.
    Pooled via _RequestCtxPool to eliminate per-request heap allocation.
    Middleware/plugins can still attach data via the ``state`` dict or
    the ``_extra`` dict (escape hatch for truly dynamic attributes).
    """

    __slots__ = (
        "request",
        "identity",
        "session",
        "auth",
        "container",
        "state",
        "request_id",
        "_extra",
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
        self.request = request
        self.identity = identity
        self.session = session
        self.auth = auth
        self.container = container
        self.state: dict[str, Any] = state if state is not None else {}
        self.request_id = request_id
        self._extra: dict[str, Any] | None = None

    # -- dynamic attribute escape hatch for plugins/middleware -------
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
#  RequestCtx Object Pool
# ═══════════════════════════════════════════════════════════════════════════


class _RequestCtxPool:
    """
    Lock-free object pool for RequestCtx instances.

    Eliminates per-request heap allocation by recycling RequestCtx objects.
    The pool is safe for single-threaded async code (no locks needed).

    Usage::

        ctx = _ctx_pool.acquire(request=req, container=di)
        ...  # process request
        _ctx_pool.release(ctx)
    """

    __slots__ = ("_pool", "_max_size")

    def __init__(self, max_size: int = 256):
        self._max_size = max_size
        self._pool: list[RequestCtx] = []

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
        """Get a RequestCtx from the pool or create a new one.

        ARCH-08: If *request_id* is ``None``, a fresh random ID is generated
        to ensure reused contexts never carry a stale request_id.
        """
        import os

        if request_id is None:
            request_id = os.urandom(16).hex()

        if self._pool:
            ctx = self._pool.pop()
            # Reset fields in-place (avoids __init__ overhead)
            ctx.request = request
            ctx.identity = identity
            ctx.session = session
            ctx.auth = auth
            ctx.container = container
            ctx.state = state if state is not None else {}
            ctx.request_id = request_id
            ctx._extra = None
            return ctx
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
        """Return a RequestCtx to the pool for reuse."""
        if len(self._pool) < self._max_size:
            # Clear references to allow GC of request-scoped objects
            ctx.request = None  # type: ignore[assignment]
            ctx.identity = None
            ctx.session = None
            ctx.auth = None
            ctx.container = None
            ctx.state = _EMPTY_STATE
            ctx.request_id = None
            ctx._extra = None
            self._pool.append(ctx)


# Module-level pool singleton
_ctx_pool = _RequestCtxPool(max_size=256)


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
    Simple in-memory sliding-window rate limiter.

    Usage::

        class UsersController(Controller):
            throttle = Throttle(limit=100, window=60)  # 100 req / 60s

    Or per-route::

        @GET("/", throttle=Throttle(limit=10, window=60))
        async def list(self, ctx): ...
    """

    def __init__(self, limit: int = 100, window: int = 60, max_clients: int = 10000):
        self.limit = limit
        self.window = window
        self.max_clients = max_clients
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
        Check if the request is within the rate limit.

        Returns True if allowed, False if throttled.

        SEC-CTRL-04: Includes periodic cleanup of expired entries and
        LRU eviction when max_clients is reached to prevent unbounded
        memory growth.
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
        """Clear all rate limit state."""
        self._requests.clear()


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
        cls = super().__new__(mcs, name, bases, namespace)
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
            @GET("/profile")
            async def profile(self, ctx):
                user = await self.repo.get(ctx.identity.id)
                return await self.render("profile.html", {"user": user}, ctx)
        """
        from aquilia.response import Response

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
