"""scaffold_module tool."""

from __future__ import annotations

from ..models import KnowledgeIndex


def scaffold_module(index: KnowledgeIndex, arguments: dict) -> dict:
    name = arguments["name"]
    prefix = arguments.get("route_prefix") or f"/{name}"
    minimal = bool(arguments.get("minimal", False))
    class_name = "".join(part.capitalize() for part in name.replace("-", "_").split("_"))
    files = [
        {"path": f"modules/{name}/__init__.py", "shape": "module package marker"},
        {
            "path": f"modules/{name}/manifest.py",
            "shape": {
                "manifest": "AppManifest",
                "name": name,
                "version": "0.1.0",
                "controllers": [f"modules.{name}.controllers:{class_name}Controller"],
                "services": [] if minimal else [f"modules.{name}.services:{class_name}Service"],
                "base_path": f"modules.{name}",
                "imports": [],
                "exports": [] if minimal else [f"modules.{name}.services:{class_name}Service"],
            },
        },
        {
            "path": f"modules/{name}/controllers.py",
            "shape": "class <Name>Controller(Controller) with prefix='/' and @GET/@POST decorators",
        },
        {"path": "workspace.py", "shape": f'.module(Module("{name}").route_prefix("{prefix}"))'},
    ]
    if not minimal:
        files.extend(
            [
                {"path": f"modules/{name}/services.py", "shape": "business logic service resolved by DI"},
                {
                    "path": f"modules/{name}/faults.py",
                    "shape": "module-specific Fault subclasses using aquilia.faults.core.Fault and FaultDomain.custom(...)",
                },
            ]
        )
    files.append(
        {
            "path": f"tests/test_{name.replace('-', '_')}.py",
            "shape": "focused pytest coverage for service/controller behavior",
        }
    )
    return {
        "module": name,
        "files": files,
        "anti_patterns": [
            "Do not call Module.register_controllers/register_services.",
            "Do not put route_prefix in AppManifest.",
            "Do not configure AppManifest.database.",
        ],
        "validation": ["aq validate", "aq inspect routes", "python -m pytest tests/"],
        "anchors": [fact for fact in index.facts if "manifest" in fact["id"] or "routing" in fact["id"]],
    }
