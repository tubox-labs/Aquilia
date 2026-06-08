"""SSE fault classes."""

from aquilia.faults.core import Fault, FaultDomain, Severity

OTEL_DOMAIN = FaultDomain.custom("otel", "OpenTelemetry tracing faults")


class OTelFault(Fault):
    domain = OTEL_DOMAIN
    severity = Severity.WARN


class OTelConfigFault(OTelFault):
    code = "otel.config_invalid"
    message = "Invalid OpenTelemetry configuration"


class OTelExportFault(OTelFault):
    code = "otel.export_failed"
    message = "Failed to export spans to OTLP endpoint"
