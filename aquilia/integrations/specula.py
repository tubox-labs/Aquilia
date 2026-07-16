"""
SpeculaIntegration — typed Specula configuration for ``Integration.specula(...)``.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Literal

from aquilia.specula.config import SpeculaConfig


@dataclass
class SpeculaIntegration:
    """
    Typed configuration for the Specula API Observatory. Fields mirror
    :class:`~aquilia.specula.config.SpeculaConfig`.

    Usage::

        workspace = (
            Workspace("my-api")
            .integrate(Integration.specula(
                title="Payment API",
                version="3.0.0",
                ui_theme="dark",
                spec_cache_ttl=60,
                mock_server_enabled=True,
            ))
        )
    """

    _integration_type: str = field(default="specula", init=False, repr=False)

    # Info
    title: str = "Aquilia API"
    version: str = "1.0.0"
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""
    license_identifier: str = ""

    # URL paths
    ui_path: str = "/specula"
    json_path: str = "/specula/spec.json"
    yaml_path: str = "/specula/spec.yaml"
    stream_path: str = "/specula/stream"
    versions_path: str = "/specula/versions"
    schemas_path: str = "/specula/schemas"
    routes_path: str = "/specula/routes"
    export_path: str = "/specula/export"
    mock_path: str = "/specula/mock"

    # Servers
    servers: list[dict[str, Any]] = field(default_factory=list)

    # Feature flags
    enabled: bool = True
    include_internal: bool = False
    group_by_module: bool = True
    infer_request_body: bool = True
    infer_responses: bool = True
    detect_security: bool = True
    include_examples: bool = True
    include_extensions: bool = True
    include_effect_annotations: bool = True
    include_pipeline_annotations: bool = True
    include_deprecation_details: bool = True
    include_version_graph: bool = True

    # Caching
    spec_cache_ttl: int = 60
    spec_cache_key: str = "aquilia:specula:spec:{version}"

    # Docs auth
    docs_auth_required: bool = False
    docs_roles: list[str] = field(default_factory=list)

    # UI appearance
    ui_theme: Literal["auto", "light", "dark"] = "auto"
    ui_primary_color: str = "#22c55e"
    ui_logo_url: str = ""
    ui_favicon_url: str = ""
    ui_custom_css: str = ""

    # External docs
    external_docs_url: str = ""
    external_docs_description: str = ""

    # Mock server
    mock_server_enabled: bool = False
    mock_max_depth: int = 4

    # Webhooks / tags / security / codegen
    webhooks: dict[str, Any] = field(default_factory=dict)
    tag_groups: list[dict[str, Any]] = field(default_factory=list)
    extra_security_schemes: dict[str, Any] = field(default_factory=dict)
    codegen_hints: dict[str, Any] = field(default_factory=dict)

    def to_specula_config(self) -> SpeculaConfig:
        """Build a :class:`SpeculaConfig` from this integration."""
        data = dataclasses.asdict(self)
        data.pop("_integration_type", None)
        return SpeculaConfig.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a config dict keyed with ``_integration_type``."""
        data = dataclasses.asdict(self)
        data["_integration_type"] = "specula"
        return data
