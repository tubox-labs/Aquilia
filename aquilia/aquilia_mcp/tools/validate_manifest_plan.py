"""validate_manifest_plan tool."""

from __future__ import annotations

from ..models import KnowledgeIndex

_CHECKS = [
    ("Module.register_", "Deprecated Module.register_* methods; declare components in AppManifest instead."),
    ("route_prefix=", "AppManifest.route_prefix is deprecated; use Module.route_prefix() in workspace.py."),
    ("DatabaseConfig(", "Manifest-level DatabaseConfig is deprecated and ignored at runtime."),
    ("database=DatabaseConfig", "AppManifest.database is deprecated and ignored at runtime."),
    ("ValueError(", "Prefer structured Aquilia faults for framework-domain failures."),
    ("RuntimeError(", "Prefer structured Aquilia faults where the error belongs to an Aquilia domain."),
    ("config.yaml", "YAML configuration is removed; use Python-native workspace.py/AquilaConfig patterns."),
    ("workspace.yml", "YAML configuration is removed; use Python-native workspace.py/AquilaConfig patterns."),
    ("middlewares=", "AppManifest.middlewares is legacy; use middleware=[MiddlewareConfig(...)] instead."),
    ("default_fault_domain=", "AppManifest.default_fault_domain is legacy; use FaultHandlingConfig(default_domain=...)."),
    ("aquilia.models.parser", "AMDL parser imports are deprecated; use Python-native Model classes."),
    ("aquilia.models.runtime", "AMDL runtime imports are deprecated; use Python-native Model classes."),
]


def validate_manifest_plan(index: KnowledgeIndex, arguments: dict) -> dict:
    plan = arguments["plan"]
    issues = [{"pattern": pattern, "message": message} for pattern, message in _CHECKS if pattern in plan]
    return {
        "valid": not issues,
        "issues": issues,
        "preferred_patterns": [
            "Workspace(...).module(Module(name).route_prefix(...))",
            "AppManifest(name=..., version=..., controllers=[...], services=[...], imports=[...], exports=[...])",
            "Workspace.database(...) or Integration.database(...) for database config",
            "ConfigInvalidFault, ConfigMissingFault, ManifestInvalidFault, RoutingFault, or domain-specific Fault subclasses",
        ],
        "anchors": index.deprecations,
    }
