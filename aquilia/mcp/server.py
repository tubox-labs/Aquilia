"""Aquilia MCP server implementation."""

from __future__ import annotations

from typing import Any

from .config import MCPConfig
from .context.indexer import build_index
from .faults import MCPProtocolFault, MCPToolFault
from .models import KnowledgeIndex
from .prompts.catalog import build_prompt_registry
from .protocol import MCP_PROTOCOL_VERSION
from .registry import MCPRegistry
from .security import resolve_readable_file
from .tools.catalog import build_tool_registry
from .transport.stdio import StdioTransport
from .version import __version__


class AquiliaMCPServer:
    """Local MCP server backed by the Aquilia source tree."""

    def __init__(self, config: MCPConfig, index: KnowledgeIndex | None = None, registry: MCPRegistry | None = None):
        self.config = config
        self.index = index or build_index(config.root)
        self.registry = registry or build_tool_registry(self.index)
        build_prompt_registry(self.index, self.registry)
        self._cancelled: set[str | int] = set()

    def initialize(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": request.get("protocolVersion") or MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {"name": self.config.server_name, "version": __version__},
            "instructions": "Use Aquilia MCP tools for source-backed Aquilia architecture, CLI, manifest, and example guidance.",
        }

    def list_tools(self) -> dict[str, Any]:
        return {"tools": self.registry.list_tools()}

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise MCPToolFault("Tool arguments must be a JSON object", metadata={"tool": name})
        result = self.registry.call_tool(name, arguments)
        return {
            "content": [{"type": "text", "text": _compact_text(result)}],
            "structuredContent": result,
            "isError": False,
        }

    def list_resources(self) -> dict[str, Any]:
        resources = [
            {
                "uri": f"aquilia://{source.path}",
                "name": source.title or source.path,
                "description": source.summary,
                "mimeType": "text/markdown" if source.kind == "markdown" else "text/x-python",
            }
            for source in self.index.sources[:500]
        ]
        return {"resources": resources}

    def read_resource(self, uri: str) -> dict[str, Any]:
        path = resolve_readable_file(self.config.root, uri)
        data = path.read_bytes()[: self.config.max_read_bytes]
        text = data.decode("utf-8", errors="replace")
        rel = path.relative_to(self.config.root).as_posix()
        return {
            "contents": [
                {
                    "uri": f"aquilia://{rel}",
                    "mimeType": "text/markdown" if path.suffix == ".md" else "text/plain",
                    "text": text,
                }
            ]
        }

    def list_prompts(self) -> dict[str, Any]:
        return {"prompts": self.registry.list_prompts()}

    def get_prompt(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise MCPToolFault("Prompt arguments must be a JSON object", metadata={"prompt": name})
        return self.registry.get_prompt(name, arguments)

    def cancel(self, request_id: str | int | None) -> None:
        if request_id is not None:
            self._cancelled.add(request_id)

    def handle(self, method: str, params: dict[str, Any]) -> dict[str, Any] | None:
        if method == "initialize":
            return self.initialize(params)
        if method == "ping":
            return {}
        if method == "tools/list":
            return self.list_tools()
        if method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or not name:
                raise MCPProtocolFault("tools/call requires a non-empty string 'name'", code="MCP_INVALID_PARAMS")
            return self.call_tool(name, params.get("arguments") or {})
        if method == "resources/list":
            return self.list_resources()
        if method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str) or not uri:
                raise MCPProtocolFault("resources/read requires a non-empty string 'uri'", code="MCP_INVALID_PARAMS")
            return self.read_resource(uri)
        if method == "prompts/list":
            return self.list_prompts()
        if method == "prompts/get":
            name = params.get("name")
            if not isinstance(name, str) or not name:
                raise MCPProtocolFault("prompts/get requires a non-empty string 'name'", code="MCP_INVALID_PARAMS")
            return self.get_prompt(name, params.get("arguments") or {})
        if method in {"notifications/initialized", "$/cancelRequest", "notifications/cancelled"}:
            self.cancel((params.get("requestId") or params.get("id")) if isinstance(params, dict) else None)
            return None

        raise MCPProtocolFault(f"Unknown MCP method: {method}", code="MCP_METHOD_NOT_FOUND")

    def serve_stdio(self) -> None:
        StdioTransport(self, max_request_bytes=self.config.max_request_bytes).serve()

    def serve_socket(self) -> None:
        from .transport.socket import SocketTransport

        SocketTransport(self, host=self.config.host, port=self.config.port).serve()


def _compact_text(data: dict[str, Any]) -> str:
    import json

    text = json.dumps(data, indent=2, sort_keys=True)
    return text[:40_000]
