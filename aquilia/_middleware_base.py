"""Middleware base class — dependency-free leaf module.

This lives apart from :mod:`aquilia.middleware` to break an import cycle:
``aquilia.middleware`` imports ``aquilia.faults``, and ``aquilia.faults.engine``
needs the ``Middleware`` base for ``FaultMiddleware``. Importing the base from
here keeps ``aquilia.faults`` from reaching back into ``aquilia.middleware``.

Import nothing from ``aquilia.faults`` (or anything that pulls it in) here, or
the cycle comes back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.typing.middleware import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class Middleware:
    """Base class for all framework and extension middlewares."""

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        raise NotImplementedError("Middleware must implement __call__")
