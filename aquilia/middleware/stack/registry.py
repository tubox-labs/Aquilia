"""``MiddlewareStack`` — registration, ordering, and compilation.

Ordering contract, unchanged from the original implementation: sort by
``(scope_rank, priority)`` ascending, stable. **Ascending priority = outer =
runs first.** Priority is a flat integer namespace shared by framework
internals, security config, the template engine, inspector tooling, and
third-party manifests, so same-``(scope, priority)`` pairs are reported at
``add()`` time rather than silently resolved by registration order.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any

from aquilia.middleware.core.descriptor import MiddlewareDescriptor, MiddlewareMeta
from aquilia.middleware.core.priority import Priority, sort_key
from aquilia.middleware.core.types import Handler, Scope
from aquilia.middleware.stack.builder import ChainBuilder
from aquilia.middleware.stack.errors import (
    MiddlewarePriorityCollisionFault,
    MiddlewareRegistrationFault,
)
from aquilia.middleware.stack.validation import display_name, is_noop, validate, validate_hooks
from aquilia.middleware.utils.ordering import collision_message, find_collision

if TYPE_CHECKING:
    from aquilia.middleware.instrumentation.base import Instrument

logger = logging.getLogger("aquilia.middleware")


class MiddlewareStack:
    """Manages middleware with deterministic ordering.

    Order: ``global`` < ``app`` < ``controller`` < ``route``, then by priority
    ascending. Unknown scope bands sort last, so foreign middleware still runs
    — just after the framework tiers.

    Set ``strict_priorities`` to turn the collision warning into a fatal
    ``MiddlewarePriorityCollisionFault`` at startup. Set ``traced`` to attach
    the inspector tracing instrument.

    Example::

        stack = MiddlewareStack(strict_priorities=True)
        stack.add(FaultMiddleware(engine), priority=Priority.FAULTS, name="faults")
        stack.add(TenantMiddleware())            # picks up class metadata
        stack.freeze()
        handler = stack.build_handler(final_handler)
    """

    def __init__(
        self,
        *,
        strict_priorities: bool = False,
        traced: bool = False,
        instruments: Sequence[Instrument] = (),
    ):
        self.middlewares: list[MiddlewareDescriptor] = []
        self.strict_priorities = strict_priorities
        self._traced = traced
        self._extra_instruments: list[Instrument] = list(instruments)
        self._sorted = True
        self._frozen = False

    # ── Tracing ──────────────────────────────────────────────────────────
    #
    # Kept as a property because callers mutate it after construction
    # (``server.py`` enables it once the inspector config is known). Writing to
    # it invalidates any compiled chain.

    @property
    def traced(self) -> bool:
        """Whether the inspector tracing instrument is attached."""
        return self._traced

    @traced.setter
    def traced(self, value: bool) -> None:
        self._traced = bool(value)

    def add_instrument(self, instrument: Instrument) -> None:
        """Attach an extra instrument. Must happen before ``build_handler()``."""
        self._extra_instruments.append(instrument)

    def _instruments(self) -> list[Instrument]:
        """Resolve the instrument list. Tracing is imported lazily so the
        inspector stays out of the import graph when tracing is off."""
        instruments: list[Instrument] = []
        if self._traced:
            from aquilia.middleware.instrumentation.tracing import TracingInstrument

            instruments.append(TracingInstrument())
        instruments.extend(self._extra_instruments)
        return instruments

    # ── Registration ─────────────────────────────────────────────────────

    def add(
        self,
        middleware: Any,
        scope: str | Scope | None = None,
        priority: int | None = None,
        name: str | None = None,
        *,
        tags: Sequence[str] = (),
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register *middleware*.

        Validates the base class, signature, and coroutine-ness up front so a
        mistake surfaces at boot rather than on the first request.

        ``scope``, ``priority``, and ``name`` fall back to the class-level
        metadata the middleware declares, then to framework defaults. Explicit
        arguments always win.

        Args:
            middleware: A ``Middleware`` instance or an async function taking
                ``(request, ctx, next_handler)``.
            scope: ``"global"``, ``"app:<name>"``, ``"controller:<name>"``, or
                ``"route:<pattern>"``.
            priority: Lower runs first. See ``core.priority.Priority``.
            name: Display name; defaults to the class or function name.
            tags: Labels surfaced by :meth:`describe`.
            metadata: Free-form data attached to the descriptor.

        Raises:
            MiddlewareRegistrationFault: Invalid middleware, or a frozen stack.
            MiddlewarePriorityCollisionFault: Under ``strict_priorities`` only.
        """
        if self._frozen:
            raise MiddlewareRegistrationFault.frozen(name or display_name(middleware))

        reason = validate(middleware) or validate_hooks(middleware)
        if reason is not None:
            raise MiddlewareRegistrationFault(reason, name=name or display_name(middleware))

        meta = MiddlewareMeta.of(middleware)
        resolved_scope = Scope.parse(scope if scope is not None else meta.scope)
        resolved_priority = (
            priority
            if priority is not None
            else (meta.priority if meta.priority is not None else Priority.APPLICATION_DEFAULT)
        )
        resolved_name = name or meta.name or display_name(middleware)

        if is_noop(middleware):
            logger.warning(
                "Middleware '%s' overrides none of __call__ / handle / before / after, "
                "so registering it has no effect.",
                resolved_name,
            )

        self._check_collision(resolved_name, resolved_scope, resolved_priority)

        self.middlewares.append(
            MiddlewareDescriptor.build(
                middleware,
                scope=resolved_scope,
                priority=resolved_priority,
                name=resolved_name,
                tags=tuple(tags) or meta.tags,
                metadata=metadata,
            )
        )
        self._sorted = False  # sorting deferred to build_handler()

    def _check_collision(self, name: str, scope: Scope, priority: int) -> None:
        """Report a same-scope, same-priority registration.

        Their relative order would fall back to registration order — an
        implementation detail that changes silently when registration code is
        reordered, which is exactly the class of bug worth failing loudly on.
        """
        clash = find_collision(self.middlewares, str(scope), priority)
        if clash is None:
            return
        message = collision_message(name, clash.name, str(scope), priority)
        if self.strict_priorities:
            raise MiddlewarePriorityCollisionFault(message)
        logger.warning(message)

    def freeze(self) -> None:
        """Close the stack to further registration.

        The chain is compiled and cached once by ``ASGIAdapter``, so a
        middleware added after that point would never run. Freezing turns that
        silent no-op into a loud fault at the call site.
        """
        self._frozen = True

    @property
    def frozen(self) -> bool:
        return self._frozen

    # ── Ordering ─────────────────────────────────────────────────────────

    def _sort_middlewares(self) -> None:
        """Sort in place by ``(scope_rank, priority)`` ascending."""
        self.middlewares.sort(key=sort_key)
        self._sorted = True

    def _ensure_sorted(self) -> None:
        if not self._sorted:
            self._sort_middlewares()

    # ── Compilation ──────────────────────────────────────────────────────

    def build_handler(self, final_handler: Handler) -> Handler:
        """Fold the sorted stack into a single handler wrapping *final_handler*.

        Called once at startup; the result is cached by ``ASGIAdapter``, so the
        per-request cost is chain traversal rather than chain construction.

        Every registered middleware is included, whatever its scope. Scope
        currently determines *order*, not *applicability* — see :meth:`select`
        for the filtered view, and the note there about why the two are still
        separate.
        """
        self._ensure_sorted()
        return ChainBuilder(self._instruments()).build(self.middlewares, final_handler)

    def select(self, band: str, target: str) -> list[MiddlewareDescriptor]:
        """Descriptors applicable to one ``band``/``target`` pair, in order.

        ``global`` middleware always applies; ``controller:users`` applies only
        to that controller; a bare band like ``controller`` applies to all of
        them.

        This is the seam for scoped execution. It is deliberately *not* wired
        into :meth:`build_handler` yet: today every middleware runs on every
        request regardless of scope, and silently narrowing that would change
        behaviour for anyone who registered ``controller:``-scoped middleware
        and (knowingly or not) depends on it running everywhere. Callers that
        want per-route chains — the router, when it compiles them — can build
        from this list explicitly.
        """
        self._ensure_sorted()
        return [d for d in self.middlewares if d.scope.matches(band, target)]

    def build_scoped_handler(self, final_handler: Handler, band: str, target: str) -> Handler:
        """Like :meth:`build_handler`, but only middleware matching the target.

        Intended for per-controller or per-route chains. Each call folds a new
        chain, so cache the result rather than building per request.
        """
        return ChainBuilder(self._instruments()).build(self.select(band, target), final_handler)

    # ── Lifespan ─────────────────────────────────────────────────────────

    async def startup(self, app: object) -> None:
        """Run ``setup()`` on every middleware that defines one, outermost first.

        Middleware owning a connection, client, or bucket store build it here so
        failures surface at boot rather than on the first request.
        """
        self._ensure_sorted()
        for descriptor in self.middlewares:
            if descriptor.lifespan:
                await descriptor.middleware.setup(app)

    async def shutdown(self, app: object) -> None:
        """Run ``teardown()`` in reverse order, so inner middleware unwind first.

        An exception in one teardown is logged and the rest still run — a
        failure to release one resource must not strand the others.
        """
        self._ensure_sorted()
        for descriptor in reversed(self.middlewares):
            if not descriptor.lifespan:
                continue
            try:
                await descriptor.middleware.teardown(app)
            except Exception:
                logger.exception("Middleware '%s' teardown failed", descriptor.name)

    # ── Diagnostics ──────────────────────────────────────────────────────

    def describe(self) -> list[dict[str, Any]]:
        """Ordered view of the stack, for ``aq inspect`` and debugging.

        Matches ``SocketMiddlewareStack.describe()`` so both transports report
        the same shape.
        """
        self._ensure_sorted()
        return [descriptor.describe() for descriptor in self.middlewares]

    def __len__(self) -> int:
        return len(self.middlewares)

    def __iter__(self) -> Iterator[MiddlewareDescriptor]:
        self._ensure_sorted()
        return iter(self.middlewares)

    def __repr__(self) -> str:
        state = "frozen" if self._frozen else "open"
        return f"<MiddlewareStack {len(self.middlewares)} middleware, {state}>"


__all__ = ["MiddlewareStack"]
