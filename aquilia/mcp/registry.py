"""Tool, resource, and prompt registry for Aquilia MCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .faults import MCPToolFault

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]
PromptHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    read_only: bool = True

    def to_mcp(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {
                "readOnlyHint": self.read_only,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }


@dataclass(frozen=True)
class PromptSpec:
    name: str
    description: str
    arguments: list[dict[str, Any]]
    handler: PromptHandler

    def to_mcp(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "arguments": self.arguments}


class MCPRegistry:
    """Deterministic registry for MCP tools and prompts."""

    def __init__(self) -> None:
        self.tools: dict[str, ToolSpec] = {}
        self.prompts: dict[str, PromptSpec] = {}

    def register_tool(self, spec: ToolSpec) -> None:
        if spec.name in self.tools:
            raise MCPToolFault(f"Duplicate tool registration: {spec.name}")
        self.tools[spec.name] = spec

    def register_prompt(self, spec: PromptSpec) -> None:
        if spec.name in self.prompts:
            raise MCPToolFault(f"Duplicate prompt registration: {spec.name}")
        self.prompts[spec.name] = spec

    def list_tools(self) -> list[dict[str, Any]]:
        return [self.tools[name].to_mcp() for name in sorted(self.tools)]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = self.tools.get(name)
        if spec is None:
            raise MCPToolFault(f"Unknown tool: {name}", metadata={"tool": name})
        _validate_schema(arguments, spec.input_schema)
        return spec.handler(arguments)

    def list_prompts(self) -> list[dict[str, Any]]:
        return [self.prompts[name].to_mcp() for name in sorted(self.prompts)]

    def get_prompt(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = self.prompts.get(name)
        if spec is None:
            raise MCPToolFault(f"Unknown prompt: {name}", metadata={"prompt": name})
        return spec.handler(arguments)


def _validate_schema(arguments: dict[str, Any], schema: dict[str, Any]) -> None:
    if not isinstance(arguments, dict):
        raise MCPToolFault("Tool arguments must be a JSON object")
    properties = schema.get("properties", {})
    allowed = set(properties)
    unknown = sorted(set(arguments) - allowed)
    if unknown:
        raise MCPToolFault(f"Unknown argument(s): {', '.join(unknown)}")
    for required in schema.get("required", []):
        if required not in arguments:
            raise MCPToolFault(f"Missing required argument: {required}")
    for key, value in arguments.items():
        prop = properties.get(key, {})
        expected = prop.get("type")
        if expected == "string" and not isinstance(value, str):
            raise MCPToolFault(f"Argument '{key}' must be a string")
        if expected == "integer" and not isinstance(value, int):
            raise MCPToolFault(f"Argument '{key}' must be an integer")
        if expected == "array" and not isinstance(value, list):
            raise MCPToolFault(f"Argument '{key}' must be an array")
        if expected == "boolean" and not isinstance(value, bool):
            raise MCPToolFault(f"Argument '{key}' must be a boolean")
        if expected == "integer":
            minimum = prop.get("minimum")
            maximum = prop.get("maximum")
            if minimum is not None and value < minimum:
                raise MCPToolFault(f"Argument '{key}' must be >= {minimum}")
            if maximum is not None and value > maximum:
                raise MCPToolFault(f"Argument '{key}' must be <= {maximum}")
        enum = prop.get("enum")
        if enum is not None and value not in enum:
            raise MCPToolFault(f"Argument '{key}' must be one of: {', '.join(map(str, enum))}")
