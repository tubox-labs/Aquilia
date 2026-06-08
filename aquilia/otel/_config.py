"""OTel configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OTelConfig:
    """
    OpenTelemetry configuration for Aquilia.

    Attributes:
        service_name:     Service name in traces (required).
        service_version:  Service version string. Defaults to Aquilia version.
        otlp_endpoint:    OTLP gRPC endpoint (e.g. 'http://localhost:4317').
                          None disables export (traces only go to SDK).
        trace_all:        If True, every request gets a span. Default True.
        propagators:      List of propagator names ('tracecontext', 'baggage').
        resource_attrs:   Extra OTEL_RESOURCE_ATTRIBUTES-style key/value pairs.
    """

    service_name: str = "aquilia-app"
    service_version: str = ""
    otlp_endpoint: str | None = None
    trace_all: bool = True
    propagators: list[str] = field(default_factory=lambda: ["tracecontext", "baggage"])
    resource_attrs: dict[str, str] = field(default_factory=dict)
