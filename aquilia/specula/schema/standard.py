"""
Standard Aquilia component schemas — registered in ``components.schemas``
whenever Specula is active.
"""

from __future__ import annotations

from typing import Any

from .fault import aquilia_error_schema, aquilia_validation_error_schema


def _standard_schemas() -> dict[str, dict[str, Any]]:
    return {
        "AquiliaError": aquilia_error_schema(),
        "AquiliaValidationError": aquilia_validation_error_schema(),
        "PaginatedResponse": {
            "type": "object",
            "description": "Standard Aquilia paginated list response (PageNumberPagination)",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer", "description": "Total record count"},
                "next": {"oneOf": [{"type": "string", "format": "uri"}, {"type": "null"}]},
                "previous": {"oneOf": [{"type": "string", "format": "uri"}, {"type": "null"}]},
                "results": {"type": "array", "items": {}},
            },
        },
        "LimitOffsetResponse": {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer"},
                "next": {"oneOf": [{"type": "string", "format": "uri"}, {"type": "null"}]},
                "previous": {"oneOf": [{"type": "string", "format": "uri"}, {"type": "null"}]},
                "results": {"type": "array", "items": {}},
            },
        },
        "CursorPaginatedResponse": {
            "type": "object",
            "required": ["results"],
            "properties": {
                "next": {
                    "oneOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Opaque cursor token",
                },
                "previous": {"oneOf": [{"type": "string"}, {"type": "null"}]},
                "results": {"type": "array", "items": {}},
            },
        },
        "HealthResponse": {
            "type": "object",
            "description": "Aquilia health check response",
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                "version": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "subsystems": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                            "latency": {
                                "type": "number",
                                "format": "double",
                                "description": "Latency in milliseconds",
                            },
                        },
                    },
                },
            },
        },
        "AuthTokenResponse": {
            "type": "object",
            "description": "JWT token pair response",
            "required": ["access_token", "token_type"],
            "properties": {
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
                "token_type": {"type": "string", "enum": ["bearer"], "default": "bearer"},
                "expires_in": {"type": "integer", "description": "Seconds until access token expires"},
                "scope": {"type": "string"},
            },
        },
        "AquiliaIdentity": {
            "type": "object",
            "description": "Authenticated user identity (aquilia.auth.core.Identity)",
            "properties": {
                "id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "roles": {"type": "array", "items": {"type": "string"}},
                "scopes": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object", "additionalProperties": True},
            },
        },
        "EmptyResponse": {
            "type": "object",
            "description": "Empty success response (HTTP 204)",
            "properties": {},
        },
    }


#: Standard schema dict — built once at import of this module (pure data, no IO).
STANDARD_SCHEMAS: dict[str, dict[str, Any]] = _standard_schemas()
