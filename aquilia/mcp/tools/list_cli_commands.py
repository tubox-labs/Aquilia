"""list_cli_commands tool."""

from __future__ import annotations

from ..models import KnowledgeIndex


def list_cli_commands(index: KnowledgeIndex, arguments: dict) -> dict:
    query = str(arguments.get("query") or "").lower()
    limit = min(int(arguments.get("limit", 50)), 200)
    commands = index.cli_commands
    if query:
        commands = [
            command
            for command in commands
            if query in command["command"].lower() or query in command.get("doc", "").lower()
        ]
    return {"commands": commands[:limit], "count": len(commands)}
