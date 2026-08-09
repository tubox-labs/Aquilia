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

**This module resolves its exports lazily.** Importing
``aquilia.middleware.core.base`` executes this file, so an eager façade would
pull ``aquilia.faults``, ``aquilia.debug``, and ``aquilia.inspector`` into the
graph and resurrect the ``aquilia.middleware`` ↔ ``aquilia.faults`` cycle
through the package rather than the module. ``tests/test_import_order.py``
asserts the boundary holds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    from aquilia.middleware.core import MiddlewareDescriptor, Priority, Scope
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

# name -> (module, attribute). Resolved on first access via __getattr__.
_LAZY: dict[str, tuple[str, str]] = {
    # ── Core ──
    "MiddlewareDescriptor": ("aquilia.middleware.core.descriptor", "MiddlewareDescriptor"),
    "MiddlewareMeta": ("aquilia.middleware.core.descriptor", "MiddlewareMeta"),
    "Priority": ("aquilia.middleware.core.priority", "Priority"),
    "Scope": ("aquilia.middleware.core.types", "Scope"),
    # ── Stack ──
    "MiddlewareStack": ("aquilia.middleware.stack.registry", "MiddlewareStack"),
    "ChainBuilder": ("aquilia.middleware.stack.builder", "ChainBuilder"),
    "MiddlewareRegistrationFault": ("aquilia.middleware.stack.errors", "MiddlewareRegistrationFault"),
    "MiddlewarePriorityCollisionFault": (
        "aquilia.middleware.stack.errors",
        "MiddlewarePriorityCollisionFault",
    ),
    "MiddlewareContractFault": ("aquilia.middleware.stack.errors", "MiddlewareContractFault"),
    # ── Instrumentation ──
    "Instrument": ("aquilia.middleware.instrumentation.base", "Instrument"),
    "TracingInstrument": ("aquilia.middleware.instrumentation.tracing", "TracingInstrument"),
    "MetricsInstrument": ("aquilia.middleware.instrumentation.metrics", "MetricsInstrument"),
    # ── Built-in middleware ──
    "ExceptionMiddleware": ("aquilia.middleware.builtin.exceptions", "ExceptionMiddleware"),
    "RequestIdMiddleware": ("aquilia.middleware.builtin.request_id", "RequestIdMiddleware"),
    "TimeoutMiddleware": ("aquilia.middleware.builtin.timeout", "TimeoutMiddleware"),
    "CompressionMiddleware": ("aquilia.middleware.builtin.compression", "CompressionMiddleware"),
    # Re-exported from their canonical homes for backward compatibility: both
    # were importable from ``aquilia.middleware`` before the package split.
    "LoggingMiddleware": ("aquilia.middleware.builtin.logging", "LoggingMiddleware"),
    "CORSMiddleware": ("aquilia.middleware.builtin.security.cors", "CORSMiddleware"),
}

__all__ = [
    "Middleware",
    "Handler",
    "RequestHandler",
    *sorted(_LAZY),
]


def __getattr__(name: str) -> Any:
    """Resolve a public export on first access (PEP 562)."""
    try:
        module_path, attribute = _LAZY[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    import importlib

    value = getattr(importlib.import_module(module_path), attribute)
    globals()[name] = value  # cache: subsequent lookups skip __getattr__
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
