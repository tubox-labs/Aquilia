"""generate_agent_prompt tool."""

from __future__ import annotations

from ..models import KnowledgeIndex
from ..prompts.templates import render_workflow_prompt


def generate_agent_prompt(index: KnowledgeIndex, arguments: dict) -> dict:
    workflow = arguments["workflow"]
    goal = str(arguments.get("goal") or "")
    return {
        "workflow": workflow,
        "prompt": render_workflow_prompt(index, workflow, {"goal": goal}),
    }
