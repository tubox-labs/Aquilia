"""Inspector tracing as an ``Instrument``.

Replaces ``MiddlewareStack._wrap_middleware_traced``, which duplicated the
entire link body — including the response-contract check — on both the
traced and untraced sides of an ``if``. Here the link is already built; this
only measures it.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from aquilia.inspector.trace import current_trace

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.middleware.core.descriptor import MiddlewareDescriptor
    from aquilia.middleware.core.types import Handler
    from aquilia.request import Request
    from aquilia.response import Response


class TracingInstrument:
    """Records one inspector span per middleware execution.

    When no trace is active — every request outside dev mode — this costs one
    ``current_trace()`` lookup and a direct call, with no timing work.
    """

    __slots__ = ()

    def wrap(self, descriptor: MiddlewareDescriptor, link: Handler) -> Handler:
        name = descriptor.name

        async def traced(request: Request, ctx: RequestCtx) -> Response:
            trace = current_trace()
            if trace is None:
                return await link(request, ctx)

            started = time.monotonic()
            try:
                return await link(request, ctx)
            finally:
                elapsed = time.monotonic() - started
                trace.add_span(
                    "middleware",
                    name,
                    start_offset_ms=(started - trace.started_monotonic) * 1000.0,
                    duration_ms=elapsed * 1000.0,
                )

        traced.__name__ = f"traced_{name}"
        return traced


__all__ = ["TracingInstrument"]
