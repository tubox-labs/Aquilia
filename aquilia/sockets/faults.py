"""
WebSocket Faults - Structured error handling for WebSocket operations

Integrates with Aquilia's Fault system for consistent error handling.
"""

from aquilia.faults import Fault, FaultDomain, Severity

# Define WebSocket fault domain
FaultDomain.NETWORK = FaultDomain("network", "Network and WebSocket errors")


class SocketFault(Fault):
    """Base fault for WebSocket operations."""

    def __init__(self, code: str, message: str, severity: Severity = Severity.ERROR, retryable: bool = False, **kwargs):
        super().__init__(
            code=code, message=message, domain=FaultDomain.NETWORK, severity=severity, retryable=retryable, **kwargs
        )


# Handshake faults


def WS_HANDSHAKE_FAILED(reason=""):
    return SocketFault(
        code="WS_HANDSHAKE_FAILED",
        message=f"WebSocket handshake failed: {reason}",
        severity=Severity.ERROR,
        retryable=False,
        metadata={"http_status": 400},
    )


def WS_AUTH_REQUIRED():
    return SocketFault(
        code="WS_AUTH_REQUIRED",
        message="Authentication required for WebSocket connection",
        severity=Severity.WARN,
        retryable=True,
        metadata={"http_status": 401},
    )


def WS_FORBIDDEN(reason=""):
    return SocketFault(
        code="WS_FORBIDDEN",
        message=f"WebSocket connection forbidden: {reason}",
        severity=Severity.WARN,
        retryable=False,
        metadata={"http_status": 403},
    )


def WS_ORIGIN_NOT_ALLOWED(origin=""):
    return SocketFault(
        code="WS_ORIGIN_NOT_ALLOWED",
        message=f"Origin not allowed: {origin}",
        severity=Severity.WARN,
        retryable=False,
        metadata={"http_status": 403},
    )


# Message faults


def WS_MESSAGE_INVALID(reason=""):
    return SocketFault(
        code="WS_MESSAGE_INVALID",
        message=f"Invalid message format: {reason}",
        severity=Severity.WARN,
        retryable=True,
        metadata={"ws_close_code": 1003},
    )


def WS_PAYLOAD_TOO_LARGE(size=0, limit=0):
    return SocketFault(
        code="WS_PAYLOAD_TOO_LARGE",
        message=f"Payload too large: {size} bytes (limit: {limit})",
        severity=Severity.WARN,
        retryable=True,
        metadata={"ws_close_code": 1009},
    )


def WS_UNSUPPORTED_EVENT(event=""):
    return SocketFault(
        code="WS_UNSUPPORTED_EVENT",
        message=f"Unsupported event type: {event}",
        severity=Severity.WARN,
        retryable=True,
    )


# Connection faults


def WS_CONNECTION_CLOSED(reason=""):
    return SocketFault(
        code="WS_CONNECTION_CLOSED",
        message=f"Connection closed: {reason}",
        severity=Severity.INFO,
        retryable=False,
        metadata={"ws_close_code": 1000},
    )


def WS_CONNECTION_TIMEOUT():
    return SocketFault(
        code="WS_CONNECTION_TIMEOUT",
        message="Connection timeout",
        severity=Severity.WARN,
        retryable=False,
        metadata={"ws_close_code": 1001},
    )


# Rate limiting & quotas


def WS_RATE_LIMIT_EXCEEDED(limit=0):
    return SocketFault(
        code="WS_RATE_LIMIT_EXCEEDED",
        message=f"Rate limit exceeded: {limit} messages/sec",
        severity=Severity.WARN,
        retryable=True,
        metadata={"ws_close_code": 1008},
    )


def WS_QUOTA_EXCEEDED(quota=""):
    return SocketFault(
        code="WS_QUOTA_EXCEEDED",
        message=f"Quota exceeded: {quota}",
        severity=Severity.WARN,
        retryable=True,
        metadata={"ws_close_code": 1008},
    )


# Room/subscription faults


def WS_ROOM_NOT_FOUND(room=""):
    return SocketFault(
        code="WS_ROOM_NOT_FOUND",
        message=f"Room not found: {room}",
        severity=Severity.WARN,
        retryable=True,
    )


def WS_ROOM_FULL(room="", capacity=0):
    return SocketFault(
        code="WS_ROOM_FULL",
        message=f"Room full: {room} (capacity: {capacity})",
        severity=Severity.WARN,
        retryable=True,
    )


def WS_ALREADY_SUBSCRIBED(room=""):
    return SocketFault(
        code="WS_ALREADY_SUBSCRIBED",
        message=f"Already subscribed to room: {room}",
        severity=Severity.INFO,
        retryable=True,
    )


def WS_NOT_SUBSCRIBED(room=""):
    return SocketFault(
        code="WS_NOT_SUBSCRIBED",
        message=f"Not subscribed to room: {room}",
        severity=Severity.WARN,
        retryable=True,
    )


# Adapter faults


def WS_ADAPTER_UNAVAILABLE(adapter=""):
    return SocketFault(
        code="WS_ADAPTER_UNAVAILABLE",
        message=f"Adapter unavailable: {adapter}",
        severity=Severity.CRITICAL,
        retryable=False,
    )


def WS_PUBLISH_FAILED(reason=""):
    return SocketFault(
        code="WS_PUBLISH_FAILED",
        message=f"Failed to publish message: {reason}",
        severity=Severity.ERROR,
        retryable=True,
    )
