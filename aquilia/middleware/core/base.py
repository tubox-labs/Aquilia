"""The ``Middleware`` base class — dependency-free leaf module.

This module is imported by :mod:`aquilia.faults.engine` (for ``FaultMiddleware``)
and by every concrete middleware in the framework. It must stay free of
``aquilia.faults``, or the ``aquilia.middleware`` ↔ ``aquilia.faults`` cycle that
motivated the old ``aquilia/_middleware_base.py`` comes straight back.

``tests/test_import_order.py`` enforces that boundary in a subprocess. Import
nothing here beyond :mod:`aquilia.typing.middleware` and this package's
``core.types``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from aquilia.middleware.core.types import Handler, MiddlewareCallable

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response


class Middleware:
    """Base class for all framework and extension middleware.

    A middleware sees every request that reaches it, may inspect or replace the
    response, and may short-circuit the chain entirely. Pick the narrowest hook
    that does the job:

    - :meth:`before` — inspect the request; return a ``Response`` to short-circuit.
    - :meth:`after` — inspect or rewrite the response on the way out.
    - :meth:`handle` — full control over the continuation (timeouts, retries,
      ``try``/``except`` around the rest of the chain).

    Overriding ``__call__`` directly remains fully supported; it is what every
    middleware written before 1.3 does, and the stack invokes it in preference
    to ``handle`` when a subclass defines it.

    Example::

        class TenantMiddleware(Middleware):
            name = "tenant"
            priority = Priority.APPLICATION_DEFAULT

            async def before(self, request, ctx):
                tenant = request.header("x-tenant-id")
                if not tenant:
                    return Response.json({"error": "missing tenant"}, status=400)
                ctx.state["tenant"] = tenant

            async def after(self, request, ctx, response):
                response.headers["X-Tenant"] = ctx.state["tenant"]
                return response

    Declarative metadata (``name``, ``priority``, ``scope``, ``tags``) supplies
    registration defaults, so ``stack.add(TenantMiddleware())`` needs no repeated
    arguments. Explicit arguments to ``add()`` always win.

    Every hook must be ``async def``; the registry rejects sync ones at boot
    rather than failing on the first request.
    """

    # ── Declarative registration metadata ─────────────────────────────────
    #: Display name. Defaults to the class name when unset.
    name: ClassVar[str | None] = None
    #: Default priority. Ascending = outer = runs first. See ``core.priority``.
    priority: ClassVar[int | None] = None
    #: Default scope band, e.g. ``"global"`` or ``"controller:users"``.
    scope: ClassVar[str] = "global"
    #: Free-form labels surfaced by ``MiddlewareStack.describe()``.
    tags: ClassVar[tuple[str, ...]] = ()

    # ── Primary hook ──────────────────────────────────────────────────────

    async def handle(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        """Run the middleware around *next_handler*.

        The default implementation dispatches to :meth:`before` and
        :meth:`after`. Override this when you need to wrap the continuation
        itself — a timeout, a retry, or an ``except`` clause covering the rest
        of the chain.
        """
        early = await self.before(request, ctx)
        if early is not None:
            return early
        return await self.after(request, ctx, await next_handler(request, ctx))

    # ── Conveniences ──────────────────────────────────────────────────────

    async def before(self, request: Request, ctx: RequestCtx) -> Response | None:
        """Inspect the request before the chain continues.

        Return ``None`` to continue, or a ``Response`` to short-circuit — the
        rest of the chain and the route handler never run, and this
        middleware's :meth:`after` is skipped. Outer middleware still unwind
        normally.
        """
        return None

    async def after(self, request: Request, ctx: RequestCtx, response: Response) -> Response:
        """Inspect or rewrite the response on the way out. Must return one."""
        return response

    # ── Opt-in extensions ─────────────────────────────────────────────────

    async def should_run(self, request: Request, ctx: RequestCtx) -> bool:
        """Decide per request whether this middleware runs at all.

        Overriding this costs one extra ``await`` per request *for this
        middleware only* — the registry detects the override at registration
        time and omits the predicate wrapper entirely when it is absent, so
        middleware that do not use it pay nothing.

        Do not use this for authorization. A predicate that raises is a bug; a
        guard that rejects should return a 401/403 response from :meth:`before`.
        """
        return True

    async def setup(self, app: object) -> None:
        """Acquire resources during application startup.

        Called once from the ASGI lifespan startup, before the first request.
        Middleware that own a connection, a client, or a bucket store should
        build it here rather than in ``__init__`` so failures surface at boot.
        """
        return None

    async def teardown(self, app: object) -> None:
        """Release what :meth:`setup` acquired, during lifespan shutdown.

        Runs in reverse registration order so inner middleware unwind first. An
        exception here is logged; the remaining teardowns still run.
        """
        return None

    # ── Invocation ────────────────────────────────────────────────────────

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        """Entry point. Delegates to :meth:`handle` unless a subclass overrides it."""
        return await self.handle(request, ctx, next_handler)


# Sentinels captured once at class-definition time so override detection is an
# identity check rather than a signature comparison. Mirrors the technique in
# ``aquilia/sockets/middleware/base.py``.
_BASE_CALL = Middleware.__call__
_BASE_HANDLE = Middleware.handle
_BASE_BEFORE = Middleware.before
_BASE_AFTER = Middleware.after
_BASE_SHOULD_RUN = Middleware.should_run
_BASE_SETUP = Middleware.setup
_BASE_TEARDOWN = Middleware.teardown


def _overrides(middleware: object, hook: str, base: object) -> bool:
    return getattr(type(middleware), hook, base) is not base


def resolve_entrypoint(middleware: object) -> MiddlewareCallable:
    """Bind the callable the chain should invoke, once, at registration time.

    A subclass overriding ``__call__`` gets ``__call__``. One overriding only
    ``handle`` gets ``handle`` bound directly, skipping a stack frame per
    request. Plain functions are returned as-is.

    Resolving here rather than per request is what lets the hook-based base
    cost nothing relative to the old callable-only one.
    """
    if not isinstance(middleware, Middleware):
        return middleware  # type: ignore[return-value]  # plain async function
    if _overrides(middleware, "__call__", _BASE_CALL):
        return middleware.__call__
    if _overrides(middleware, "handle", _BASE_HANDLE):
        return middleware.handle
    return middleware.__call__


def implements_should_run(middleware: object) -> bool:
    """True when *middleware* overrides :meth:`Middleware.should_run`."""
    return _overrides(middleware, "should_run", _BASE_SHOULD_RUN)


def implements_lifespan(middleware: object) -> bool:
    """True when *middleware* overrides :meth:`Middleware.setup` or :meth:`Middleware.teardown`."""
    return _overrides(middleware, "setup", _BASE_SETUP) or _overrides(middleware, "teardown", _BASE_TEARDOWN)


def implements_any_hook(middleware: object) -> bool:
    """True when *middleware* overrides at least one request-path hook.

    A subclass that overrides none of ``__call__``/``handle``/``before``/``after``
    is a no-op pass-through — worth a warning at registration.
    """
    return any(
        _overrides(middleware, hook, base)
        for hook, base in (
            ("__call__", _BASE_CALL),
            ("handle", _BASE_HANDLE),
            ("before", _BASE_BEFORE),
            ("after", _BASE_AFTER),
        )
    )


__all__ = [
    "Middleware",
    "resolve_entrypoint",
    "implements_should_run",
    "implements_lifespan",
    "implements_any_hook",
]
