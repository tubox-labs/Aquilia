"""
OpenAPIIntegration — typed OpenAPI documentation configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenAPIIntegration:
    """
    Typed OpenAPI spec / Swagger UI configuration.

    Example::

        OpenAPIIntegration(
            title="My API",
            version="2.0.0",
            swagger_ui_theme="dark",
        )
    """

    _integration_type: str = field(default="openapi", init=False, repr=False)

    title: str = "Aquilia API"
    version: str = "1.0.0"
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""
    servers: list[dict[str, str]] = field(default_factory=list)
    docs_path: str = "/docs"
    openapi_json_path: str = "/openapi.json"
    redoc_path: str = "/redoc"
    include_internal: bool = False
    group_by_module: bool = True
    infer_request_body: bool = True
    infer_responses: bool = True
    detect_security: bool = True
    external_docs_url: str = ""
    external_docs_description: str = ""
    swagger_ui_theme: str = ""
    swagger_ui_config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "openapi",
            "enabled": self.enabled,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "terms_of_service": self.terms_of_service,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_url": self.contact_url,
            "license_name": self.license_name,
            "license_url": self.license_url,
            "servers": self.servers,
            "docs_path": self.docs_path,
            "openapi_json_path": self.openapi_json_path,
            "redoc_path": self.redoc_path,
            "include_internal": self.include_internal,
            "group_by_module": self.group_by_module,
            "infer_request_body": self.infer_request_body,
            "infer_responses": self.infer_responses,
            "detect_security": self.detect_security,
            "external_docs_url": self.external_docs_url,
            "external_docs_description": self.external_docs_description,
            "swagger_ui_theme": self.swagger_ui_theme,
            "swagger_ui_config": self.swagger_ui_config,
        }
