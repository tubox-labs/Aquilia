"""Request timeout enforcement.

Bounds how long a request may occupy a worker. The naive version — wrapping
the chain in ``asyncio.wait_for`` and raising on expiry — has three problems
this addresses:

- **Cancellation is misreported.** When a client disconnects, the server task
  is cancelled. ``asyncio.CancelledError`` derives from ``BaseException``
  precisely so it is not swept up by ``except Exception``; a handler that
  catches broadly turns a disconnect into a 408 and swallows a cancellation
  the event loop needs to observe.
- **No per-route control.** A 30s default that must accommodate a report
  export forces every cheap endpoint to wait 30s before shedding load.
- **No signal to the handler.** A handler that wants to return partial results
  before the deadline has no way to know how long is left.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import Handler

if TYPE_CHECKING:
    from collections.abc import Callable

    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

__all__ = ["TimeoutMiddleware"]


class TimeoutMiddleware(Middleware):
    """Aborts a request that exceeds its deadline.

    Args:
        timeout_seconds: Default budget for every request.
        per_path: Optional ``{path_prefix: seconds}`` overrides, longest
            prefix wins. Exports and uploads usually need their own budget.
        exempt: Paths that are never timed out — SSE streams, WebSocket
            upgrades, long-poll endpoints, which are *supposed* to be slow.
        resolver: Optional ``(request) -> float | None`` for budgets that
            depend on more than the path (a plan tier, a header). Returning
            ``None`` falls through to ``per_path``, then the default.

    Raises ``RequestTimeoutFault`` (408) so the failure flows through the fault
    system and ``ExceptionMiddleware`` renders it per content negotiation.

    The remaining budget is published to ``request.state["deadline"]`` (a
    monotonic timestamp) and ``ctx.state["timeout_budget"]``, so a handler can
    trim its own work — ask a database for 2s less than it has left, or return
    partial results rather than being killed mid-write.

    Overrides ``handle`` rather than ``before``/``after`` because it must wrap
    the continuation itself.
    """

    name = "timeout"

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        *,
        per_path: dict[str, float] | None = None,
        exempt: tuple[str, ...] = (),
        resolver: Callable[[Request], float | None] | None = None,
    ):
        self.timeout = timeout_seconds
        # Longest prefix first, so "/api/export" wins over "/api".
        self.per_path = dict(sorted((per_path or {}).items(), key=lambda kv: -len(kv[0])))
        self.exempt = tuple(exempt)
        self.resolver = resolver

    def resolve_timeout(self, request: Request) -> float | None:
        """The budget for *request*, or ``None`` when it is exempt."""
        path = getattr(request, "path", "") or ""

        if any(path.startswith(prefix) for prefix in self.exempt):
            return None

        if self.resolver is not None:
            resolved = self.resolver(request)
            if resolved is not None:
                return resolved

        for prefix, seconds in self.per_path.items():
            if path.startswith(prefix):
                return seconds

        return self.timeout

    async def handle(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        budget = self.resolve_timeout(request)
        if budget is None:
            return await next_handler(request, ctx)

        # Publish the deadline so handlers can bound their own work.
        request.state["deadline"] = time.monotonic() + budget
        request.state["timeout_budget"] = budget
        if hasattr(ctx, "state"):
            ctx.state["timeout_budget"] = budget

        try:
            return await asyncio.wait_for(next_handler(request, ctx), timeout=budget)
        # Both names are caught because they are the same object on 3.11+ but
        # distinct classes on 3.10, where ``asyncio.wait_for`` raises the
        # asyncio one. ``asyncio.CancelledError`` needs no handler: it derives
        # from BaseException, so it bypasses this clause and propagates
        # untouched — a client disconnect or a server shutdown cancels this
        # task too, and reporting either as a 408 would be a lie. Catching
        # ``Exception`` instead of these two names would be the bug.
        except (TimeoutError, asyncio.TimeoutError):
            from aquilia.faults.domains import RequestTimeoutFault

            raise RequestTimeoutFault(
                detail=f"Request exceeded {budget}s timeout",
            ) from None
