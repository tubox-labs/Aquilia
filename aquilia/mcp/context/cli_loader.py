"""Extract CLI command metadata from actual Click command declarations."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _decorator_name(decorator: ast.AST) -> tuple[str | None, str | None]:
    if isinstance(decorator, ast.Call):
        func = decorator.func
        command_name = None
        if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
            command_name = decorator.args[0].value
    else:
        func = decorator
        command_name = None
    if isinstance(func, ast.Attribute):
        if func.attr in {"command", "group"}:
            parent = func.value.id if isinstance(func.value, ast.Name) else None
            return parent, command_name
    return None, None


def load_cli_commands(root: Path) -> list[dict[str, Any]]:
    main = root / "aquilia" / "cli" / "__main__.py"
    if not main.exists():
        return []
    tree = ast.parse(main.read_text(encoding="utf-8"))
    known_names: dict[str, str] = {"cli": "aq"}
    commands: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            parent, explicit = _decorator_name(decorator)
            if parent is None:
                continue
            cmd = explicit or node.name.replace("_", "-")
            parent_path = known_names.get(parent, parent)
            full = f"{parent_path} {cmd}".strip()
            if parent == "cli":
                full = f"aq {cmd}"
            if any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "group" for d in node.decorator_list):
                known_names[node.name] = full
            commands.append(
                {
                    "name": cmd,
                    "function": node.name,
                    "parent": parent_path,
                    "command": full,
                    "path": "aquilia/cli/__main__.py",
                    "line": node.lineno,
                    "doc": ast.get_docstring(node) or "",
                }
            )
    return sorted(commands, key=lambda item: (item["command"], item["line"]))
