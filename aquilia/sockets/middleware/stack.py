"""SocketMiddlewareStack — registration, ordering, and chain construction.

Structurally mirrors :class:`aquilia.middleware.MiddlewareStack`: same
``(scope_rank, priority)`` ascending sort, same collision detection, same
nested-closure fold. It diverges where the transport does — three chains instead
of one, and a return-value contract that admits ``None``.
"""

from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aquilia._middleware_ordering import collision_message, find_collision, scope_rank
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.sockets.middleware.base import (
    SocketMiddleware,
    implements_connect,
    implements_disconnect,
    implements_message,
)
from aquilia.sockets.middleware.types import ConnectHandler, MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware")

# Scope bands, ascending = outer. Mirrors the HTTP stack's
# global < app < controller < route with socket-shaped middle tiers.
SCOPE_ORDER = {"global": 0, "namespace": 1, "event": 2}

# Reserved priority bands. A documented convention plus the collision warning,
# not a type-level constraint — a tuple priority would make collisions
# structurally impossible but would diverge from the HTTP API this mirrors.
FRAMEWORK_PLUMBING_BAND = range(0, 10)
FRAMEWORK_SECURITY_BAND = range(10, 20)
RESERVED_BAND = range(20, 50)
APPLICATION_BAND = range(50, 100)


@dataclass
class SocketMiddlewareDescriptor:
    """Descriptor for a registered socket middleware."""

    middleware: SocketMiddleware
    scope: str  # "global", "namespace:/chat", "event:message.send"
    priority: int
    name: str


class SocketMiddlewareStack:
    """
    Manages WebSocket middleware with deterministic ordering.

    Order: ``global`` < ``namespace:*`` < ``event:*``, then by priority
    ascending. **Ascending priority = outer = runs first inbound.** This is the
    same contract as the HTTP stack, deliberately: reversing it is what produced
    the per-user rate-limit ordering bug there, and a developer's intuition
    should transfer between the two without adjustment.

    One registration feeds three chains. A middleware appears only in the chains
    whose hook it overrides, so an ``on_message``-only middleware costs nothing
    at connect time.

    Set ``strict_priorities`` to turn the collision warning into a fatal
    ``ConfigInvalidFault`` at startup.
    """

    def __init__(self, *, strict_priorities: bool = False, traced: bool = False):
        self.middlewares: list[SocketMiddlewareDescriptor] = []
        self.strict_priorities = strict_priorities
        self.traced = traced
        self._sorted = True

        # Pre-filtered per-stage views, rebuilt on sort.
        self._connect: list[SocketMiddlewareDescriptor] = []
        self._message: list[SocketMiddlewareDescriptor] = []
        self._disconnect: list[SocketMiddlewareDescriptor] = []

    # ── Registration ─────────────────────────────────────────────────────

    def add(
        self,
        middleware: SocketMiddleware,
        scope: str = "global",
        priority: int = 50,
        name: str | None = None,
    ) -> None:
        """Register a middleware.

        Validates the base class, hook signatures, and coroutine-ness up front so
        a mistake surfaces at boot rather than on the first message of the first
        connection.

        Args:
            middleware: A :class:`SocketMiddleware` instance.
            scope: ``"global"``, ``"namespace:<path>"``, or ``"event:<name>"``.
            priority: Lower runs first. See the reserved bands in this module.
            name: Display name; defaults to the class name.
        """
        if not isinstance(middleware, SocketMiddleware):
            raise ConfigInvalidFault("socket.middleware", self._rejection_reason(middleware))

        if name is None:
            name = type(middleware).__name__

        self._validate_hooks(middleware, name)

        descriptor = SocketMiddlewareDescriptor(
            middleware=middleware,
            scope=scope,
            priority=priority,
            name=name,
        )

        collision = find_collision(self.middlewares, scope, priority)
        if collision is not None:
            message = collision_message(name, collision.name, scope, priority)
            if self.strict_priorities:
                raise ConfigInvalidFault("socket.middleware.priority", message)
            logger.warning(message)

        self.middlewares.append(descriptor)
        self._sorted = False

    _HOOK_SIGNATURES = {
        "on_connect": (2, "(ctx, next_handler)"),
        "on_message": (3, "(envelope, ctx, next_handler)"),
        "on_disconnect": (2, "(ctx, reason)"),
    }

    @staticmethod
    def _rejection_reason(middleware: Any) -> str:
        """Explain why *middleware* was rejected, naming a migration where one exists.

        The pre-package socket middleware was a bare callable taking
        ``(conn, envelope, next)``. It was never invoked by the runtime, so
        anything still written that way has never run — pointing that out is more
        useful than "must inherit from SocketMiddleware".
        """
        type_name = type(middleware).__name__
        call = getattr(middleware, "__call__", None)

        if call is not None and inspect.iscoroutinefunction(call):
            try:
                params = [
                    p
                    for p in inspect.signature(call).parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                ]
            except (TypeError, ValueError):
                params = []

            if len(params) == 3:
                return (
                    f"'{type_name}' looks like pre-1.5 socket middleware: an async "
                    f"__call__(conn, envelope, next). That interface was never invoked by "
                    f"the socket runtime, so this middleware has not been running. Port it "
                    f"to SocketMiddleware — rename __call__ to on_message and take "
                    f"(envelope, ctx, next_handler); reach the connection via ctx.connection"
                )

        return (
            f"middleware of type '{type_name}' must inherit from 'SocketMiddleware'. "
            f"WebSocket middleware has three lifecycle hooks (on_connect / on_message / "
            f"on_disconnect), which a bare callable cannot express — subclass "
            f"SocketMiddleware and override the hooks you need"
        )

    def _validate_hooks(self, middleware: SocketMiddleware, name: str) -> None:
        """Every overridden hook must be async and bind the right arity."""
        overridden = {
            "on_connect": implements_connect(middleware),
            "on_message": implements_message(middleware),
            "on_disconnect": implements_disconnect(middleware),
        }

        if not any(overridden.values()):
            logger.warning(
                "Socket middleware '%s' overrides none of on_connect / on_message / "
                "on_disconnect, so registering it has no effect.",
                name,
            )
            return

        for hook, is_overridden in overridden.items():
            if not is_overridden:
                continue

            func = getattr(middleware, hook)
            arity, shape = self._HOOK_SIGNATURES[hook]

            if not inspect.iscoroutinefunction(func):
                raise ConfigInvalidFault(
                    "socket.middleware",
                    f"'{name}.{hook}' must be a coroutine function (async def)",
                )

            try:
                inspect.signature(func).bind(*([None] * arity))
            except TypeError as exc:
                raise ConfigInvalidFault(
                    "socket.middleware",
                    f"'{name}.{hook}' has an invalid signature: {exc}. "
                    f"It must accept exactly {arity} parameters: {shape}",
                ) from exc

    # ── Ordering ─────────────────────────────────────────────────────────

    def _sort_middlewares(self) -> None:
        self.middlewares.sort(key=lambda d: (scope_rank(d.scope, SCOPE_ORDER), d.priority))
        self._connect = [d for d in self.middlewares if implements_connect(d.middleware)]
        self._message = [d for d in self.middlewares if implements_message(d.middleware)]
        self._disconnect = [d for d in self.middlewares if implements_disconnect(d.middleware)]

    def _ensure_sorted(self) -> None:
        if not self._sorted:
            self._sort_middlewares()
            self._sorted = True

    def describe(self) -> list[dict[str, Any]]:
        """Ordered view of the stack, for diagnostics and ``aq ws`` output."""
        self._ensure_sorted()
        return [
            {
                "name": d.name,
                "scope": d.scope,
                "priority": d.priority,
                "hooks": [
                    hook
                    for hook, present in (
                        ("on_connect", implements_connect(d.middleware)),
                        ("on_message", implements_message(d.middleware)),
                        ("on_disconnect", implements_disconnect(d.middleware)),
                    )
                    if present
                ],
            }
            for d in self.middlewares
        ]

    def scoped(self, namespace: str) -> SocketMiddlewareStack:
        """Return a stack holding only the middleware applicable to *namespace*.

        Global middleware always applies. ``namespace:X`` applies only when ``X``
        matches. ``event:X`` middleware is namespace-agnostic and is filtered per
        message inside the chain instead.
        """
        sub = SocketMiddlewareStack(strict_priorities=self.strict_priorities, traced=self.traced)
        for d in self.middlewares:
            kind, _, value = d.scope.partition(":")
            if kind == "namespace" and value != namespace:
                continue
            sub.middlewares.append(d)
        sub._sorted = False
        return sub

    # ── Chain construction ───────────────────────────────────────────────

    def build_connect_handler(self, final_handler: ConnectHandler) -> ConnectHandler:
        """Fold the connect chain around *final_handler* (accept + ``@OnConnect``)."""
        self._ensure_sorted()

        handler = final_handler
        for desc in reversed(self._connect):
            handler = self._wrap_connect(desc, handler)
        return handler

    def build_message_handler(self, final_handler: MessageHandler) -> MessageHandler:
        """Fold the message chain around *final_handler* (event dispatch)."""
        self._ensure_sorted()

        handler = final_handler
        for desc in reversed(self._message):
            handler = self._wrap_message(desc, handler)
        return handler

    def disconnect_hooks(self) -> list[SocketMiddlewareDescriptor]:
        """Descriptors implementing ``on_disconnect``, in teardown (reverse) order.

        Not a chain: disconnect is a notification fan-out. Reverse order means a
        middleware unwinds after everything inside it has finished, the way
        nested context managers exit.
        """
        self._ensure_sorted()
        return list(reversed(self._disconnect))

    async def run_disconnect(self, ctx: SocketCtx, reason: str | None) -> None:
        """Run every ``on_disconnect`` hook, isolating failures.

        A middleware that raises during teardown must not prevent the rest from
        running — a metrics hook blowing up cannot be allowed to strand a
        presence record.
        """
        for desc in self.disconnect_hooks():
            try:
                await desc.middleware.on_disconnect(ctx, reason)
            except Exception as exc:  # noqa: BLE001 — teardown must not propagate
                logger.error(
                    "Socket middleware '%s' failed during on_disconnect: %s",
                    desc.name,
                    exc,
                    exc_info=True,
                )

    # ── Wrappers ─────────────────────────────────────────────────────────

    def _wrap_connect(self, desc: SocketMiddlewareDescriptor, next_handler: ConnectHandler) -> ConnectHandler:
        middleware = desc.middleware

        async def wrapped(ctx: SocketCtx) -> None:
            trace = self._trace()
            if trace is None:
                await middleware.on_connect(ctx, next_handler)
                return

            t0 = time.monotonic()
            try:
                await middleware.on_connect(ctx, next_handler)
            finally:
                self._add_span(trace, f"{desc.name}.on_connect", t0)

        return wrapped

    def _wrap_message(self, desc: SocketMiddlewareDescriptor, next_handler: MessageHandler) -> MessageHandler:
        middleware = desc.middleware
        scope_kind, _, scope_value = desc.scope.partition(":")
        event_filter = scope_value if scope_kind == "event" else None

        async def wrapped(envelope: MessageEnvelope, ctx: SocketCtx) -> dict | None:
            # Event-scoped middleware only runs for its own event. The chain is
            # built once per namespace, so this has to be a per-message check.
            if event_filter is not None and envelope.event != event_filter:
                return await next_handler(envelope, ctx)

            trace = self._trace()
            if trace is None:
                return _validate_message_result(
                    await middleware.on_message(envelope, ctx, next_handler),
                    desc.name,
                )

            t0 = time.monotonic()
            try:
                return _validate_message_result(
                    await middleware.on_message(envelope, ctx, next_handler),
                    desc.name,
                )
            finally:
                self._add_span(trace, f"{desc.name}.on_message", t0)

        return wrapped

    # ── Tracing ──────────────────────────────────────────────────────────
    # One wrapper with the trace lookup inside it, rather than the HTTP stack's
    # two parallel wrappers — that duplication is why its response-validation
    # logic ended up copy-pasted three times.

    def _trace(self) -> Any:
        if not self.traced:
            return None
        try:
            from aquilia.inspector.trace import current_trace

            return current_trace()
        except ImportError:
            return None

    @staticmethod
    def _add_span(trace: Any, label: str, t0: float) -> None:
        try:
            from aquilia.inspector.trace import Lane

            duration_ms = (time.monotonic() - t0) * 1000.0
            trace.add_span(
                lane=Lane.SOCKETS,
                label=label,
                start_offset_ms=(t0 - trace.started_monotonic) * 1000.0,
                duration_ms=duration_ms,
            )
        except Exception:  # noqa: BLE001 — observability must never break traffic
            pass


def _validate_message_result(result: Any, name: str) -> dict | None:
    """Enforce the ``dict | None`` contract for ``on_message``.

    The HTTP stack can treat ``None`` as "you forgot to return" because every
    handler owes a ``Response``. A socket handler legitimately replies with
    nothing, so ``None`` has to be accepted and that diagnostic is unavailable
    here. A wrong *type* is still catchable.
    """
    if result is None or isinstance(result, dict):
        return result
    raise ConfigInvalidFault(
        "socket.middleware",
        f"'{name}.on_message' returned '{type(result).__name__}'; expected a dict (ack payload) or None (no reply)",
    )


__all__ = [
    "SocketMiddlewareStack",
    "SocketMiddlewareDescriptor",
    "SCOPE_ORDER",
]
