"""Derive source-backed Aquilia architecture facts from indexed files."""

from __future__ import annotations

from ..models import SourceFile

_FACT_SPECS = [
    (
        "bootstrap.runtime_pipeline",
        "AquiliaRuntime runs configure(), discover(), then bootstrap() before exposing app/server.",
        "aquilia/runtime.py",
        ("def configure", "def discover", "def bootstrap"),
    ),
    (
        "bootstrap.entrypoint_delegates",
        "aquilia.entrypoint delegates application creation to AquiliaRuntime.",
        "aquilia/entrypoint.py",
        ("AquiliaRuntime.from_workspace",),
    ),
    (
        "config.python_native",
        "ConfigLoader loads Python-native workspace.py/aquilia.py and explicitly rejects YAML.",
        "aquilia/config.py",
        ("YAML configuration is no longer supported",),
    ),
    (
        "manifest.module_internals",
        "AppManifest declares module controllers, services, models, middleware, sockets, tasks, imports, and exports.",
        "aquilia/manifest.py",
        ("class AppManifest", "controllers", "services", "socket_controllers"),
    ),
    (
        "routing.workspace_prefix",
        "Workspace Module.route_prefix() is the runtime source of truth for module route prefixes.",
        "aquilia/aquilary/core.py",
        ("workspace prefix", "AppManifest.route_prefix"),
    ),
    (
        "deprecation.module_register_methods",
        "Module.register_* methods are deprecated no-ops; component declarations belong in module manifests.",
        "aquilia/config_builders.py",
        ("register_controllers", "deprecated"),
    ),
    (
        "deprecation.manifest_database",
        "Manifest-level database config is deprecated and ignored at runtime.",
        "aquilia/manifest.py",
        ("AppManifest.database", "ignored at runtime"),
    ),
    (
        "request.lifecycle",
        "ASGIAdapter handles HTTP, WebSocket, and lifespan scopes and dispatches matched controller routes.",
        "aquilia/asgi.py",
        ("handle_http", "handle_websocket", "handle_lifespan"),
    ),
]


def derive_facts(sources: list[SourceFile]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_path = {source.path: source for source in sources}
    facts: list[dict[str, object]] = []
    deprecations: list[dict[str, object]] = []
    for fact_id, summary, path, markers in _FACT_SPECS:
        source = by_path.get(path)
        if not source:
            continue
        text = source.text
        if all(marker in text for marker in markers):
            line = 1
            first_marker = markers[0]
            for idx, source_line in enumerate(text.splitlines(), start=1):
                if first_marker in source_line:
                    line = idx
                    break
            item = {"id": fact_id, "summary": summary, "path": path, "line": line}
            facts.append(item)
            if fact_id.startswith("deprecation."):
                deprecations.append(item)
    return facts, deprecations
