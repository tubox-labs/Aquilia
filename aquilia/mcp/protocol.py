"""Minimal MCP-compatible JSON-RPC protocol helpers."""

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


def parse_request(payload: Any) -> JSONRPCRequest:
    if not isinstance(payload, dict):
        raise MCPProtocolFault("JSON-RPC payload must be an object", code="MCP_INVALID_REQUEST")
    if payload.get("jsonrpc") != JSONRPC_VERSION:
        raise MCPProtocolFault("JSON-RPC version must be '2.0'", code="MCP_INVALID_REQUEST")
    method = payload.get("method")
    if not isinstance(method, str) or not method:
        raise MCPProtocolFault("JSON-RPC method must be a non-empty string", code="MCP_INVALID_REQUEST")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise MCPProtocolFault("JSON-RPC params must be an object", code="MCP_INVALID_PARAMS")
    return JSONRPCRequest(id=payload.get("id"), method=method, params=params)


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
        code = INVALID_PARAMS if "PARAM" in fault.code else INVALID_REQUEST
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
