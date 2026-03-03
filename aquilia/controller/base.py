"""
Controller Base Class

Provides the base Controller class, RequestCtx abstraction,
and controller-level features: versioning, throttling, interceptors,
exception filters, and handler timeouts.
"""

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import asyncio
import logging
import time

if TYPE_CHECKING:
    from aquilia.request import Request
    from aquilia.response import Response
    from aquilia.sessions import Session
    from aquilia.auth.core import Identity

logger = logging.getLogger("aquilia.controller")


# ═══════════════════════════════════════════════════════════════════════════
#  RequestCtx
# ═══════════════════════════════════════════════════════════════════════════

class RequestCtx:
    """
    Request context provided to controller methods.

    Uses manual __init__ instead of @dataclass for faster construction.
    No __slots__ to allow dynamic attribute setting by middleware/plugins.
    """

    def __init__(
        self,
        request: "Request",
        identity: Optional["Identity"] = None,
        session: Optional["Session"] = None,
        container: Optional[Any] = None,
        state: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.request = request
        self.identity = identity
        self.session = session
        self.container = container
        self.state = state if state is not None else {}
        self.request_id = request_id
    
    @property
    def path(self) -> str:
        """Request path."""
        return self.request.path
    
    @property
    def method(self) -> str:
        """Request method."""
        return self.request.method
    
    @property
    def headers(self) -> Dict[str, str]:
        """Request headers."""
        return self.request.headers
    
    @property
    def query_params(self) -> Dict[str, list]:
        """Query parameters (parsed from query string)."""
        return self.request.query_params
    
    def query_param(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get single query parameter."""
        return self.request.query_param(key, default)
    
    async def json(self) -> Any:
        """Parse request body as JSON."""
        return await self.request.json()

    async def body(self) -> bytes:
        """Read raw request body bytes."""
        return await self.request.body()

    async def form(self) -> Dict[str, Any]:
        """Parse request body as form data."""
        return await self.request.form()

    async def multipart(self):
        """Parse multipart/form-data (file uploads)."""
        return await self.request.multipart()


# ═══════════════════════════════════════════════════════════════════════════
#  Exception Filter -- NestJS-style
# ═══════════════════════════════════════════════════════════════════════════

class ExceptionFilter:
    """
    Base class for exception filters.

    Exception filters intercept unhandled exceptions from controller
    handlers and convert them into proper HTTP responses.  Inspired
    by NestJS ``ExceptionFilter``.

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

    catches: List[type] = []  # Exception types this filter handles

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
#  Interceptor -- NestJS-style before/after hooks
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

    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window
        self._requests: Dict[str, list] = {}  # key -> [timestamps]

    def _client_key(self, request: Any) -> str:
        """Extract a client identifier from the request."""
        if hasattr(request, "scope"):
            client = request.scope.get("client")
            if client:
                return str(client[0])
        if hasattr(request, "headers"):
            forwarded = None
            hdrs = request.headers
            if hasattr(hdrs, "get"):
                forwarded = hdrs.get("x-forwarded-for") or hdrs.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return "unknown"

    def check(self, request: Any) -> bool:
        """
        Check if the request is within the rate limit.

        Returns True if allowed, False if throttled.
        """
        now = time.monotonic()
        key = self._client_key(request)

        if key not in self._requests:
            self._requests[key] = []

        # Prune expired entries
        cutoff = now - self.window
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

        if len(self._requests[key]) >= self.limit:
            return False

        self._requests[key].append(now)
        return True

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
    pipeline: List[Any] = []
    tags: List[str] = []
    instantiation_mode: str = "per_request"  # or "singleton"
    
    # ── New industry-standard features ──
    version: Optional[str] = None          # API version: "v1", "v2", etc.
    throttle: Optional[Throttle] = None    # Rate limiting
    interceptors: List[Any] = []           # Interceptor instances
    exception_filters: List[Any] = []      # ExceptionFilter instances
    timeout: float = 0                     # Handler timeout in seconds (0=disabled)
    max_body_size: int = 0                 # Max body size in bytes (0=disabled)
    
    # Template engine (injected via DI)
    _template_engine: Optional[Any] = None
    
    async def render(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        request_ctx: Optional[RequestCtx] = None,
        *,
        engine: Optional[Any] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None
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
            template_name,
            context,
            status=status,
            headers=headers,
            engine=engine,
            request_ctx=request_ctx
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
