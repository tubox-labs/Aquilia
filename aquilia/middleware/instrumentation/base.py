"""The ``Instrument`` protocol — observability as a wrapper, not a branch.

Tracing used to be an ``if self.traced:`` fork inside the stack, with a
duplicated copy of the whole link body on each side. An instrument wraps a
finished link instead, so adding metrics (or anything else) needs no change to
the registry or the builder.

This module stays free of ``aquilia.inspector`` so importing it does not drag
the inspector into the graph; concrete instruments import their own backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from aquilia.middleware.core.descriptor import MiddlewareDescriptor
    from aquilia.middleware.core.types import Handler


class Instrument(Protocol):
    """Wraps one middleware link with observability.

    Implementations must be transparent: return the link's response unchanged,
    let exceptions propagate, and add no behaviour beyond measurement.
    """

    def wrap(self, descriptor: MiddlewareDescriptor, link: Handler) -> Handler:
        """Return *link*, or a handler that delegates to it."""
        ...


__all__ = ["Instrument"]
