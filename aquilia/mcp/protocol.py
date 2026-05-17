"""MCP-compatible JSON-RPC protocol helpers.

The MCP server intentionally keeps protocol handling small and explicit
instead of depending on a client SDK.  The helpers in this module validate
JSON-RPC envelopes, preserve request/response correlation, and map Aquilia
faults to stable JSON-RPC error responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aquilia.faults.core import Fault

from .faults import MCPProtocolFault

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-11-25"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


@dataclass(frozen=True)
class JSONRPCRequest:
    id: str | int | None
    method: str
    params: dict[str, Any]
    notification: bool = False


def parse_request(payload: Any) -> JSONRPCRequest:
    if not isinstance(payload, dict):
        raise MCPProtocolFault("JSON-RPC payload must be an object", code="MCP_INVALID_REQUEST")
    if payload.get("jsonrpc") != JSONRPC_VERSION:
        raise MCPProtocolFault("JSON-RPC version must be '2.0'", code="MCP_INVALID_REQUEST")
    if "result" in payload or "error" in payload:
        raise MCPProtocolFault("JSON-RPC responses are not accepted on the server input stream")
    method = payload.get("method")
    if not isinstance(method, str) or not method:
        raise MCPProtocolFault("JSON-RPC method must be a non-empty string", code="MCP_INVALID_REQUEST")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise MCPProtocolFault("JSON-RPC params must be an object", code="MCP_INVALID_PARAMS")
    request_id = payload.get("id")
    if request_id is not None and not isinstance(request_id, (str, int)):
        raise MCPProtocolFault("JSON-RPC id must be a string, integer, or null", code="MCP_INVALID_REQUEST")
    return JSONRPCRequest(
        id=request_id,
        method=method,
        params=params,
        notification="id" not in payload,
    )


def success_response(request_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def error_response(
    request_id: str | int | None,
    code: int,
    message: str,
    *,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error = {"code": code, "message": message}
    if data:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def fault_to_error(fault: Exception) -> tuple[int, str, dict[str, Any]]:
    if isinstance(fault, MCPProtocolFault):
        if fault.code == "MCP_METHOD_NOT_FOUND":
            code = METHOD_NOT_FOUND
        elif "PARAM" in fault.code:
            code = INVALID_PARAMS
        else:
            code = INVALID_REQUEST
    elif isinstance(fault, Fault):
        code = INVALID_PARAMS
    else:
        code = INTERNAL_ERROR
    data: dict[str, Any] = {"type": type(fault).__name__}
    if isinstance(fault, Fault):
        data.update(
            {
                "fault_code": fault.code,
                "domain": str(fault.domain),
                "severity": str(fault.severity.value),
                "metadata": fault.metadata,
            }
        )
    return code, str(fault), data
