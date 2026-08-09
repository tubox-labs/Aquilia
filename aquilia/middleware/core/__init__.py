"""Core middleware abstractions — the fault-free leaf zone.

Nothing in this subpackage may import :mod:`aquilia.faults`,
:mod:`aquilia.debug`, :mod:`aquilia.inspector`, or
:mod:`aquilia.middleware.stack`. That boundary is what keeps
``aquilia.faults.engine`` able to import ``Middleware`` without a cycle, and it
is asserted in ``tests/test_import_order.py``.
"""

from aquilia.middleware.core.base import (
    Middleware,
    implements_any_hook,
    implements_lifespan,
    implements_should_run,
    resolve_entrypoint,
)
from aquilia.middleware.core.descriptor import MiddlewareDescriptor, MiddlewareMeta
from aquilia.middleware.core.priority import (
    APPLICATION_BAND,
    FRAMEWORK_BAND,
    PLUMBING_BAND,
    SCOPE_ORDER,
    SECURITY_BAND,
    Priority,
    sort_key,
)
from aquilia.middleware.core.types import (
    Handler,
    MiddlewareCallable,
    MiddlewareProtocol,
    RequestHandler,
    Scope,
)

__all__ = [
    "Middleware",
    "MiddlewareDescriptor",
    "MiddlewareMeta",
    "Handler",
    "MiddlewareCallable",
    "MiddlewareProtocol",
    "RequestHandler",
    "Scope",
    "Priority",
    "SCOPE_ORDER",
    "PLUMBING_BAND",
    "SECURITY_BAND",
    "FRAMEWORK_BAND",
    "APPLICATION_BAND",
    "sort_key",
    "resolve_entrypoint",
    "implements_should_run",
    "implements_lifespan",
    "implements_any_hook",
]
