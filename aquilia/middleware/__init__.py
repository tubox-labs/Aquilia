"""Middleware — composable, async-first request processing.

Layout::

    core/             abstractions; fault-free leaf zone
    stack/            registration, validation, chain compilation
    instrumentation/  tracing and metrics, as wrappers rather than branches
    builtin/          framework-owned middleware (incl. builtin/security/)
    utils/            transport-agnostic helpers shared with the socket stack

Writing middleware::

    from aquilia import Middleware, Response

    class TenantMiddleware(Middleware):
        name = "tenant"
        priority = 50

        async def before(self, request, ctx):
            tenant = request.header("x-tenant-id")
            if not tenant:
                return Response.json({"error": "missing tenant"}, status=400)
            ctx.state["tenant"] = tenant

Overriding ``__call__(request, ctx, next_handler)`` directly is still fully
supported and is what middleware written before 1.3 do.

**This module resolves its exports lazily**, via
:func:`aquilia.lazy.install_lazy_exports` — the same primitive the top-level
``aquilia`` barrel uses. Importing ``aquilia.middleware.core.base`` executes
this file, so an eager façade would pull ``aquilia.faults``, ``aquilia.debug``
and ``aquilia.inspector`` into the graph and resurrect the
``aquilia.middleware`` ↔ ``aquilia.faults`` cycle through the package rather
than the module. ``tests/test_import_order.py`` asserts the boundary holds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.lazy import install_lazy_exports

# The one eager import: the base class is a fault-free leaf, and every user who
# imports this module wants it. Keeping it eager also guarantees a single
# ``Middleware`` identity across every import path, so ``isinstance`` holds.
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import Handler, RequestHandler

if TYPE_CHECKING:
    from aquilia.middleware.builtin import (
        CompressionMiddleware,
        CORSMiddleware,
        ExceptionMiddleware,
        LoggingMiddleware,
        RequestIdMiddleware,
        TimeoutMiddleware,
    )
    from aquilia.middleware.core import MiddlewareDescriptor, MiddlewareMeta, Priority, Scope
    from aquilia.middleware.instrumentation import (
        Instrument,
        MetricsInstrument,
        TracingInstrument,
    )
    from aquilia.middleware.stack import (
        ChainBuilder,
        MiddlewareContractFault,
        MiddlewarePriorityCollisionFault,
        MiddlewareRegistrationFault,
        MiddlewareStack,
    )

# name -> (module, attribute). Resolved on first access by install_lazy_exports.
_EXPORTS: dict[str, tuple[str, str]] = {
    # ── Core ──
    "MiddlewareDescriptor": (".core.descriptor", "MiddlewareDescriptor"),
    "MiddlewareMeta": (".core.descriptor", "MiddlewareMeta"),
    "Priority": (".core.priority", "Priority"),
    "Scope": (".core.types", "Scope"),
    # ── Stack ──
    "MiddlewareStack": (".stack.registry", "MiddlewareStack"),
    "ChainBuilder": (".stack.builder", "ChainBuilder"),
    "MiddlewareRegistrationFault": (".stack.errors", "MiddlewareRegistrationFault"),
    "MiddlewarePriorityCollisionFault": (".stack.errors", "MiddlewarePriorityCollisionFault"),
    "MiddlewareContractFault": (".stack.errors", "MiddlewareContractFault"),
    # ── Instrumentation ──
    "Instrument": (".instrumentation.base", "Instrument"),
    "TracingInstrument": (".instrumentation.tracing", "TracingInstrument"),
    "MetricsInstrument": (".instrumentation.metrics", "MetricsInstrument"),
    # ── Built-in middleware ──
    "ExceptionMiddleware": (".builtin.exceptions", "ExceptionMiddleware"),
    "RequestIdMiddleware": (".builtin.request_id", "RequestIdMiddleware"),
    "TimeoutMiddleware": (".builtin.timeout", "TimeoutMiddleware"),
    "CompressionMiddleware": (".builtin.compression", "CompressionMiddleware"),
    # Re-exported from their canonical homes: both were importable from
    # ``aquilia.middleware`` before the package split.
    "LoggingMiddleware": (".builtin.logging", "LoggingMiddleware"),
    "CORSMiddleware": (".builtin.security.cors", "CORSMiddleware"),
}

__all__ = [
    "Middleware",
    "Handler",
    "RequestHandler",
    *sorted(_EXPORTS),
]

install_lazy_exports(__name__, globals(), _EXPORTS)
