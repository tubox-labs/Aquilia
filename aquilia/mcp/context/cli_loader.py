"""Extract CLI command metadata from the actual Click command tree."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


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


def _load_click_tree() -> list[dict[str, Any]]:
    try:
        import click

        from aquilia.cli.__main__ import cli
    except Exception:
        return []

    commands: list[dict[str, Any]] = []

    def walk(command: click.Command, path: list[str]) -> None:
        if path:
            params = []
            for param in command.params:
                params.append(
                    {
                        "name": param.name,
                        "opts": list(getattr(param, "opts", []) or []),
                        "secondary_opts": list(getattr(param, "secondary_opts", []) or []),
                        "required": bool(getattr(param, "required", False)),
                        "default": _json_safe(getattr(param, "default", None)),
                        "kind": type(param).__name__,
                    }
                )
            commands.append(
                {
                    "name": path[-1],
                    "function": getattr(command.callback, "__name__", "") if command.callback else "",
                    "parent": " ".join(path[:-1]) or "aq",
                    "command": " ".join(path),
                    "path": "aquilia/cli/__main__.py",
                    "line": getattr(command.callback, "__code__", None).co_firstlineno if command.callback else 1,
                    "doc": command.help or command.short_help or "",
                    "params": params,
                }
            )
        if isinstance(command, click.Group):
            for name in sorted(command.commands):
                walk(command.commands[name], [*path, name])

    walk(cli, ["aq"])
    return commands


def _load_ast_fallback(root: Path) -> list[dict[str, Any]]:
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
            if any(
                isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "group"
                for d in node.decorator_list
            ):
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


def load_cli_commands(root: Path) -> list[dict[str, Any]]:
    package_root = Path(__file__).resolve().parents[3]
    commands = _load_click_tree() if root.resolve() == package_root else []
    if commands:
        return sorted(commands, key=lambda item: (item["command"], item["line"]))
    return _load_ast_fallback(root)
