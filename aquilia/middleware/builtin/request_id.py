"""Request correlation IDs."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.priority import Priority
from aquilia.middleware.core.types import Handler, RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

__all__ = ["RequestIdMiddleware"]

# Inbound request IDs are echoed into a response header, so they must be
# constrained to a safe charset/length before they ever reach the wire —
# a client-supplied "abc\r\nX-Injected: 1" must not survive the round trip.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class RequestIdMiddleware(Middleware):
    """Attaches a unique request ID to each request and echoes it back.

    Honours an inbound ID header when the client supplies one, so a request ID
    minted at the edge survives across services.

    Performance: ``os.urandom(16).hex()`` is roughly 4× faster than
    ``uuid.uuid4()``, and the inbound header is found by scanning raw ASGI
    headers rather than building a ``Headers`` object.
    """

    name = "request_id"
    priority = Priority.REQUEST_ID

    def __init__(self, header_name: str = "X-Request-ID"):
        self.header_name = header_name
        self._header_name_bytes = header_name.lower().encode("latin-1")
        self._urandom = os.urandom

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler | RequestHandler,
    ) -> Response:
        request_id = None
        target = self._header_name_bytes
        for header_name, value in request.scope.get("headers", ()):
            if header_name == target:
                candidate = value.decode("latin-1")
                if _SAFE_REQUEST_ID.match(candidate):
                    request_id = candidate
                break

        if not request_id:
            request_id = ctx.request_id or self._urandom(16).hex()

        request.state["request_id"] = request_id
        ctx.request_id = request_id

        response = await next_handler(request, ctx)
        response.headers[self.header_name] = request_id
        return response
