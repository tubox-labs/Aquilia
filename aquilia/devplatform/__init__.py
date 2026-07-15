"""
aquilia.devplatform — Aquilia Native Development Platform (ADP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Framework-aware ASGI **development** server with:

- Native h11-based HTTP/1.1 transport (default) + RFC 6455 WebSocket engine,
  or uvicorn as an alternative transport (``--http auto``)
- Intelligent hot-reload with state preservation, driven by AST-based
  static import analysis and Aquilia's AutoDiscoveryEngine
- Per-request profiling, tracing, and SQL diagnostics
- Plugin architecture for first- and third-party extensions

Framework integration
---------------------

The ADP is a first-class Aquilia subsystem: it raises structured
:class:`~aquilia.devplatform.faults.DevPlatformFault` subclasses on the
``devplatform`` fault domain (surfaced automatically through Inspector's
fault bridge), loads its configuration through :class:`aquilia.pyconfig.Env`,
reuses ``aquilia.typing`` aliases, and emits ``Lane.DEVPLATFORM`` spans.
Debugging surfaces through Aquilia's Inspector (``aquilia.inspector``), not a
separate dashboard.

.. warning::
    The ADP is a **development** server. Do not run it for production
    traffic — deploy with uvicorn or another mature ASGI server (hypercorn,
    daphne). ``aq run`` enforces this: production mode always uses uvicorn.

Usage::

    from aquilia.devplatform import AquiliaDevelopmentServer, AquiliaDevelopmentConfig

    config = AquiliaDevelopmentConfig(port=8000)
    server = AquiliaDevelopmentServer(config)
    await server.start(app)
"""

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord, TraceSpan
from aquilia.devplatform.devserver import AquiliaDevelopmentServer
from aquilia.devplatform.faults import (
    ConfigurationFault,
    DevPlatformFault,
    InspectorFault,
    ReloadFault,
    StartupFault,
    WorkerFault,
)
from aquilia.devplatform.logging import ADPLogRouter, LogEvent, LogMode, get_router
from aquilia.devplatform.platform import AquiliaDevelopmentPlatform

__all__ = [
    "AquiliaDevelopmentConfig",
    "AquiliaDevelopmentServer",
    "AquiliaDevelopmentPlatform",
    "RuntimeStateStore",
    "RequestRecord",
    "TraceSpan",
    "DevPlatformFault",
    "StartupFault",
    "ReloadFault",
    "InspectorFault",
    "WorkerFault",
    "ConfigurationFault",
    "ADPLogRouter",
    "LogMode",
    "LogEvent",
    "get_router",
]
