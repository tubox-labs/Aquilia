"""Structured faults for Aquilia MCP operations."""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

MCP_DOMAIN = FaultDomain.custom("mcp", "Model Context Protocol server faults")


class MCPFault(Fault):
    """Base class for all MCP domain faults."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        public: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            domain=MCP_DOMAIN,
            severity=severity,
            retryable=False,
            public=public,
            metadata=metadata,
        )


class MCPProtocolFault(MCPFault):
    """A JSON-RPC/MCP protocol request is malformed or unsupported."""

    def __init__(self, message: str, *, code: str = "MCP_PROTOCOL_ERROR", metadata: dict[str, Any] | None = None):
        super().__init__(code=code, message=message, metadata=metadata)


class MCPToolFault(MCPFault):
    """A tool call failed validation or execution."""

    def __init__(self, message: str, *, metadata: dict[str, Any] | None = None):
        super().__init__(code="MCP_TOOL_ERROR", message=message, metadata=metadata)


class MCPIndexFault(MCPFault):
    """The source-backed knowledge index could not be built or read."""

    def __init__(self, message: str, *, metadata: dict[str, Any] | None = None):
        super().__init__(code="MCP_INDEX_ERROR", message=message, metadata=metadata)


class MCPSecurityFault(MCPFault):
    """A request violated the MCP server security model."""

    def __init__(self, message: str, *, metadata: dict[str, Any] | None = None):
        super().__init__(code="MCP_SECURITY_ERROR", message=message, severity=Severity.WARN, metadata=metadata)
