"""deprecation_guard tool."""

from __future__ import annotations

from ..models import KnowledgeIndex

_RULES = [
    (
        ("Module.register_controllers", ".register_controllers("),
        "Module.register_controllers",
        "Declare controllers in modules/<name>/manifest.py AppManifest(controllers=[...]).",
    ),
    (
        ("Module.register_services", ".register_services("),
        "Module.register_services",
        "Declare services in modules/<name>/manifest.py AppManifest(services=[...]).",
    ),
    (("Module.register_models", ".register_models("), "Module.register_models", "Declare models in AppManifest(models=[...])."),
    (("Module.register_routes", ".register_routes("), "Module.register_routes", "Use Controller subclasses and @GET/@POST decorators."),
    (
        ("Module.register_sockets", ".register_sockets("),
        "Module.register_sockets",
        "Declare socket_controllers in AppManifest(socket_controllers=[...]).",
    ),
    ("route_prefix=", "Move route prefixes to workspace.py with Module.route_prefix(...)."),
    ("DatabaseConfig(", "Use Workspace.database(...) or Integration.database(...)."),
    ("database=DatabaseConfig", "Use Workspace.database(...) or Integration.database(...)."),
]


def deprecation_guard(index: KnowledgeIndex, arguments: dict) -> dict:
    code = arguments["code"]
    findings = []
    for rule in _RULES:
        if len(rule) == 3:
            patterns, label, replacement = rule
            if any(pattern in code for pattern in patterns):
                findings.append({"pattern": label, "replacement": replacement})
        else:
            pattern, replacement = rule
            if pattern in code:
                findings.append({"pattern": pattern, "replacement": replacement})
    return {"ok": not findings, "findings": findings, "anchors": index.deprecations}
