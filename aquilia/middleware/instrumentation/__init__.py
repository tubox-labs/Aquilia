"""Middleware instrumentation — tracing, metrics, and the protocol they satisfy.

Instruments wrap a built chain link. They are applied by
:class:`~aquilia.middleware.stack.builder.ChainBuilder` and are the extension
point for anything that observes middleware execution without changing it.
"""

from aquilia.middleware.instrumentation.base import Instrument
from aquilia.middleware.instrumentation.metrics import MetricsInstrument, MiddlewareStats
from aquilia.middleware.instrumentation.tracing import TracingInstrument

__all__ = [
    "Instrument",
    "TracingInstrument",
    "MetricsInstrument",
    "MiddlewareStats",
]
