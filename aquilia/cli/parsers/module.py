"""Module manifest parser."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModuleManifest:
    """Parsed module manifest (module.aq)."""

    name: str
    version: str
    description: str = ""
    route_prefix: str = "/"
    fault_domain: str = "GENERIC"
    depends_on: list[str] = field(default_factory=list)
    providers: list[dict[str, Any]] = field(default_factory=list)
    routes: list[dict[str, Any]] = field(default_factory=list)
    _raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "ModuleManifest":
        """Load module manifest from file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        module = data.get("module", {})
        routing = data.get("routing", {})
        fault_handling = data.get("fault_handling", {})

        return cls(
            name=module.get("name", ""),
            version=module.get("version", "0.1.0"),
            description=module.get("description", ""),
            route_prefix=routing.get("prefix", "/"),
            fault_domain=fault_handling.get("domain", "GENERIC"),
            depends_on=data.get("dependencies") or [],
            providers=data.get("providers") or [],
            routes=data.get("routes") or [],
            _raw=data,
        )
