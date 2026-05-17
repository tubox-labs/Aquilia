"""scaffold_workspace tool."""

from __future__ import annotations

from ..models import KnowledgeIndex


def scaffold_workspace(index: KnowledgeIndex, arguments: dict) -> dict:
    name = arguments["name"]
    modules = [str(m) for m in arguments.get("modules", [])] or ["api"]
    features = [str(f).lower() for f in arguments.get("features", [])]
    integrations = []
    if "db" in features or "database" in features:
        integrations.append("Integration.database(...) or Workspace.database(...)")
    if "auth" in features:
        integrations.append("Integration.auth(...) plus sessions")
    if "cache" in features:
        integrations.append("Integration.cache(...)")
    if "storage" in features:
        integrations.append("Workspace.storage(...) or Integration.storage(...)")
    if "tasks" in features:
        integrations.append("Workspace.tasks(...) or Integration.tasks(...)")
    return {
        "files": [
            {
                "path": "workspace.py",
                "shape": [
                    "from aquilia import Integration, Module, Workspace",
                    f'workspace = Workspace("{name}", version="0.1.0")',
                    *[f'    .module(Module("{module}").route_prefix("/{module}"))' for module in modules],
                    *[f"    .integrate({integration})" for integration in integrations],
                ],
            },
            {"path": "modules/<name>/manifest.py", "shape": "AppManifest with controllers/services and imports/exports"},
        ],
        "validation": ["python -m pytest tests/", "aq validate", "aq inspect routes"],
        "anchors": [fact for fact in index.facts if "config" in fact["id"] or "manifest" in fact["id"]],
    }
