"""suggest_architecture tool."""

from __future__ import annotations

from ..models import KnowledgeIndex

_FEATURE_MODULE_HINTS = {
    "auth": ["accounts"],
    "db": ["catalog"],
    "crud": ["projects"],
    "tasks": ["jobs"],
    "websocket": ["realtime"],
    "mail": ["notifications"],
    "templates": ["portal"],
    "admin": ["operations"],
}


def suggest_architecture(index: KnowledgeIndex, arguments: dict) -> dict:
    goal = arguments["goal"]
    features = [str(f).lower() for f in arguments.get("features", [])]
    modules: list[str] = []
    for feature in features:
        modules.extend(_FEATURE_MODULE_HINTS.get(feature, [feature.replace("-", "_")]))
    if not modules:
        modules = ["core", "operations"]
    modules = list(dict.fromkeys(modules))
    return {
        "goal": goal,
        "workspace_shape": {
            "workspace": "Workspace(...).runtime(...).module(Module(...).route_prefix(...)).integrate(...)",
            "module_boundary": "workspace.py declares modules and integrations; modules/<name>/manifest.py declares internals.",
            "modules": [
                {
                    "name": name,
                    "workspace": f'Module("{name}").route_prefix("/{name}")',
                    "manifest": "AppManifest(name=..., version=..., controllers=[...], services=[...], imports=[...])",
                }
                for name in modules
            ],
        },
        "guards": [
            "Do not use Module.register_* in new workspace code.",
            "Do not set AppManifest.database or AppManifest.route_prefix in new manifests.",
            "Use Integration.* or Workspace.* for global subsystem configuration.",
        ],
        "anchors": index.facts[:8],
    }
