"""Register Aquilia-aware MCP tools."""

from __future__ import annotations

from ..models import KnowledgeIndex
from ..registry import MCPRegistry, ToolSpec
from .deprecation_guard import deprecation_guard
from .explain_bootstrap import explain_bootstrap
from .find_api import find_api
from .find_examples import find_examples
from .generate_agent_prompt import generate_agent_prompt
from .list_cli_commands import list_cli_commands
from .recommend_integrations import recommend_integrations
from .scaffold_module import scaffold_module
from .scaffold_workspace import scaffold_workspace
from .suggest_architecture import suggest_architecture
from .validate_manifest_plan import validate_manifest_plan


def _schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required or [],
    }


def build_tool_registry(index: KnowledgeIndex) -> MCPRegistry:
    registry = MCPRegistry()
    registry.register_tool(
        ToolSpec(
            "find_api",
            "Find Aquilia APIs, symbols, docs, examples, or tests from the local source index.",
            _schema(
                {
                    "query": {"type": "string", "description": "API, symbol, subsystem, or concept to find."},
                    "limit": {"type": "integer", "description": "Maximum number of results, default 8."},
                    "kind": {"type": "string", "description": "Optional source kind: python or markdown."},
                },
                ["query"],
            ),
            lambda args: find_api(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "explain_bootstrap",
            "Explain Aquilia bootstrap and request lifecycle using source-backed facts.",
            _schema({"topic": {"type": "string", "description": "Optional focus area."}}),
            lambda args: explain_bootstrap(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "suggest_architecture",
            "Suggest an Aquilia module/workspace architecture using current manifest-first conventions.",
            _schema(
                {
                    "goal": {"type": "string", "description": "Application or feature goal."},
                    "features": {"type": "array", "description": "Feature keywords such as auth, db, tasks, websocket."},
                },
                ["goal"],
            ),
            lambda args: suggest_architecture(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "scaffold_workspace",
            "Return a read-only workspace scaffold plan aligned with Workspace, Module, AquilaConfig, Env, and Secret.",
            _schema(
                {
                    "name": {"type": "string"},
                    "modules": {"type": "array"},
                    "features": {"type": "array"},
                },
                ["name"],
            ),
            lambda args: scaffold_workspace(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "scaffold_module",
            "Return a read-only module scaffold plan with manifest.py, controllers, services, tests, and validation.",
            _schema(
                {
                    "name": {"type": "string"},
                    "route_prefix": {"type": "string"},
                    "features": {"type": "array"},
                    "minimal": {"type": "boolean"},
                },
                ["name"],
            ),
            lambda args: scaffold_module(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "validate_manifest_plan",
            "Validate a proposed AppManifest/workspace plan against current Aquilia conventions.",
            _schema({"plan": {"type": "string"}}, ["plan"]),
            lambda args: validate_manifest_plan(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "recommend_integrations",
            "Recommend Aquilia Integration.* and Workspace.* configuration paths for a feature goal.",
            _schema({"goal": {"type": "string"}}, ["goal"]),
            lambda args: recommend_integrations(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "deprecation_guard",
            "Find deprecated Aquilia APIs in a code snippet or plan and return preferred replacements.",
            _schema({"code": {"type": "string"}}, ["code"]),
            lambda args: deprecation_guard(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "list_cli_commands",
            "List aq CLI commands discovered from the actual Click command tree.",
            _schema({"query": {"type": "string"}, "limit": {"type": "integer"}}),
            lambda args: list_cli_commands(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "find_examples",
            "Find runnable Aquilia examples mapped to framework features.",
            _schema({"query": {"type": "string"}, "limit": {"type": "integer"}}),
            lambda args: find_examples(index, args),
        )
    )
    registry.register_tool(
        ToolSpec(
            "generate_agent_prompt",
            "Generate a source-backed prompt for an Aquilia coding agent workflow.",
            _schema(
                {
                    "workflow": {"type": "string"},
                    "goal": {"type": "string"},
                },
                ["workflow"],
            ),
            lambda args: generate_agent_prompt(index, args),
        )
    )
    return registry
