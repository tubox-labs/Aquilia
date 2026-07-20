"""
Deep route introspection — enriched route catalogue from a built spec.
"""

from __future__ import annotations

from typing import Any


def enrich_routes(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Flatten a built OpenAPI spec into a developer-friendly route list with
    module, method, path, operationId, tags, deprecation, version, effects,
    and pipeline stage names.
    """
    routes: list[dict[str, Any]] = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            routes.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "operationId": operation.get("operationId", ""),
                    "summary": operation.get("summary", ""),
                    "tags": operation.get("tags", []),
                    "deprecated": operation.get("deprecated", False),
                    "module": operation.get("x-specula-module", ""),
                    "effects": operation.get("x-specula-effects", []),
                    "pipeline": operation.get("x-specula-pipeline", []),
                    "version": operation.get("x-specula-version", ""),
                    "websocket": operation.get("x-specula-websocket", False),
                }
            )
    return routes
