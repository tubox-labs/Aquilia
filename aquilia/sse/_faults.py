"""SSE fault classes."""

from aquilia.faults.core import Fault, FaultDomain, Severity

SSE_DOMAIN = FaultDomain.custom("sse", "Server-Sent Events subsystem faults")


class SSEFault(Fault):
    domain = SSE_DOMAIN
    severity = Severity.ERROR


class SSEStreamAbortedFault(SSEFault):
    code = "sse.stream_aborted"
    message = "SSE stream was aborted before completion"


class SSESerializationFault(SSEFault):
    code = "sse.serialization_error"
    message = "Failed to serialise SSE event data"
