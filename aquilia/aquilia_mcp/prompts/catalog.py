"""Prompt catalog registration."""

from __future__ import annotations

from ..models import KnowledgeIndex
from ..registry import MCPRegistry, PromptSpec
from .templates import PROMPT_NAMES, render_workflow_prompt


def build_prompt_registry(index: KnowledgeIndex, registry: MCPRegistry | None = None) -> MCPRegistry:
    registry = registry or MCPRegistry()
    for name in PROMPT_NAMES:
        registry.register_prompt(
            PromptSpec(
                name=name,
                description=f"Source-backed Aquilia workflow prompt for {name.removeprefix('aquilia.')}.",
                arguments=[
                    {
                        "name": "goal",
                        "description": "Specific feature or debugging goal.",
                        "required": False,
                    }
                ],
                handler=lambda args, prompt_name=name: {
                    "description": f"Aquilia workflow prompt: {prompt_name}",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": render_workflow_prompt(index, prompt_name, args),
                            },
                        }
                    ],
                },
            )
        )
    return registry
