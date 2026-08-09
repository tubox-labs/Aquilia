"""Chain construction — folding a sorted stack into nested closures.

The fold happens once, at startup; ``ASGIAdapter`` caches the result, so the
per-request cost is chain traversal rather than chain construction. There is one
chain per process, not one per route.

The response contract is enforced in exactly one place here. It used to be
copy-pasted three times across the traced and untraced wrappers, and the two
copies had drifted: the untraced path — the one production runs — reported
``type(middleware).__name__``, which prints ``"function"`` for function
middleware, while the traced path correctly used the registered name.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aquilia.middleware.core.descriptor import MiddlewareDescriptor
from aquilia.middleware.core.types import Handler
from aquilia.middleware.stack.errors import MiddlewareContractFault

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.middleware.instrumentation.base import Instrument
    from aquilia.request import Request
    from aquilia.response import Response


def enforce_contract(result: object, name: str) -> Response:
    """Every middleware owes a ``Response``. Fail loudly and name the culprit."""
    from aquilia.response import Response

    if result.__class__ is Response or isinstance(result, Response):
        return result  # type: ignore[return-value]
    if result is None:
        raise MiddlewareContractFault.returned_none(name)
    raise MiddlewareContractFault.returned_wrong_type(name, type(result).__name__)


class ChainBuilder:
    """Folds descriptors into a single handler.

    Instruments wrap each link rather than reimplementing it, which is what
    keeps tracing (and, later, metrics) from duplicating the contract check.
    Adding an instrument requires no change to this class or to the registry.
    """

    __slots__ = ("_instruments",)

    def __init__(self, instruments: Sequence[Instrument] = ()):
        self._instruments = tuple(instruments)

    def build(self, entries: Sequence[MiddlewareDescriptor], final_handler: Handler) -> Handler:
        """Wrap *final_handler* in *entries*, outermost first.

        Entries must already be sorted. The fold runs in reverse so the first
        entry ends up outermost — ascending priority = outer = runs first.
        """
        handler = final_handler

        for descriptor in reversed(entries):
            link = self._link(descriptor, handler)

            # Applied only when the middleware actually overrides should_run,
            # so unconditional middleware compile to the same closure shape as
            # before this hook existed.
            if descriptor.conditional:
                link = self._conditional(descriptor, link, handler)

            for instrument in self._instruments:
                link = instrument.wrap(descriptor, link)

            handler = link

        return handler

    @staticmethod
    def _link(descriptor: MiddlewareDescriptor, next_handler: Handler) -> Handler:
        """One middleware, wrapped around *next_handler*."""
        call = descriptor.entrypoint
        name = descriptor.name

        async def link(request: Request, ctx: RequestCtx) -> Response:
            return enforce_contract(await call(request, ctx, next_handler), name)

        link.__name__ = f"mw_{name}"
        return link

    @staticmethod
    def _conditional(descriptor: MiddlewareDescriptor, link: Handler, bypass: Handler) -> Handler:
        """Gate *link* behind the middleware's ``should_run`` predicate."""
        should_run = descriptor.middleware.should_run
        name = descriptor.name

        async def gated(request: Request, ctx: RequestCtx) -> Response:
            if await should_run(request, ctx):
                return await link(request, ctx)
            return await bypass(request, ctx)

        gated.__name__ = f"mw_{name}_gated"
        return gated


__all__ = ["ChainBuilder", "enforce_contract"]
