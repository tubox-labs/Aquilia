"""
Aquilia OTel — Optional OpenTelemetry distributed tracing.

Install: pip install aquilia[otel]

Quick start::

    from aquilia.config_builders import Workspace, Integration
    from aquilia.otel import OTelConfig

    workspace = (
        Workspace("myapp", version="1.0.0")
        .integrate(Integration.otel(OTelConfig(
            service_name    = "my-api",
            otlp_endpoint   = "http://otel-collector:4317",
        )))
    )

All requests are automatically traced. Access the current span::

    from aquilia.otel import get_current_span

    @GET("/users/{id:int}")
    async def get_user(self, ctx, id: int):
        span = get_current_span()
        span.set_attribute("user.id", id)
        ...
"""

from typing import Any

from ._config import OTelConfig
from ._faults import OTEL_DOMAIN, OTelConfigFault, OTelExportFault, OTelFault
from ._middleware import OTelMiddleware
from ._tracer import get_tracer, setup, shutdown


def get_current_span() -> Any:
    """Return the currently active OTel span, or a no-op span."""
    try:
        from opentelemetry import trace

        return trace.get_current_span()
    except ImportError:
        from ._tracer import _NoOpSpan

        return _NoOpSpan()


__all__ = [
    "OTelConfig",
    "OTelMiddleware",
    "OTelFault",
    "OTelConfigFault",
    "OTelExportFault",
    "OTEL_DOMAIN",
    "get_tracer",
    "get_current_span",
    "setup",
    "shutdown",
]
