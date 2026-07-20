"""
Specula manifest & route binding.

``specula_route_table()`` maps SpeculaConfig path fields to controller handler
names — the single source of truth consumed by ``AquiliaServer._setup_specula()``
when injecting routes (admin-style ``CompiledRoute`` injection).
"""

from __future__ import annotations

from aquilia.manifest import AppManifest, ComponentKind, ComponentRef

from .config import SpeculaConfig


def create_specula_manifest() -> AppManifest:
    """Build the AppManifest for the ``_specula`` internal module."""
    return AppManifest(
        name="_specula",
        version="2.0.0",
        description="Specula API Observatory (aquilia.specula)",
        auto_discover=False,
        controllers=[
            ComponentRef(
                class_path="aquilia.specula.controller:SpeculaController",
                kind=ComponentKind.CONTROLLER,
            )
        ],
        services=[
            ComponentRef(
                class_path="aquilia.specula.service:SpeculaService",
                kind=ComponentKind.SERVICE,
                metadata={"scope": "singleton"},
            )
        ],
    )


def specula_route_table(config: SpeculaConfig) -> list[tuple[str, str, str]]:
    """
    Route table for SpeculaController: ``(http_method, url_path, handler_name)``.

    All paths come from :class:`SpeculaConfig` — never hardcoded. Static
    routes precede dynamic ones so the router's static index wins.
    """
    return [
        ("GET", config.json_path, "spec_json"),
        ("GET", config.yaml_path, "spec_yaml"),
        ("GET", config.ui_path, "observatory_ui"),
        ("GET", config.stream_path, "spec_stream"),
        ("GET", config.versions_path, "versions_index"),
        ("GET", f"{config.versions_path}/<ver:str>", "version_spec"),
        ("GET", config.schemas_path, "schemas_index"),
        ("GET", f"{config.schemas_path}/<name:str>", "schema_detail"),
        ("GET", config.routes_path, "routes_index"),
        ("POST", f"{config.mock_path}/*path", "mock_endpoint"),
        ("GET", f"{config.export_path}/postman", "export_postman"),
        ("GET", f"{config.export_path}/insomnia", "export_insomnia"),
    ]


def bind_specula_routes(controller_cls: type, config: SpeculaConfig) -> dict[str, str]:
    """
    Backwards-compatible helper: return ``{handler_name: path}`` for every
    handler in the route table that exists on ``controller_cls``.
    """
    return {
        handler_name: path
        for _method, path, handler_name in specula_route_table(config)
        if hasattr(controller_cls, handler_name)
    }
