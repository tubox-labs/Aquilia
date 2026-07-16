"""
Aquilia fault → OpenAPI error response schema bridge.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault


def aquilia_error_schema() -> dict[str, Any]:
    """Standard Aquilia structured error response schema (``AquiliaError``)."""
    return {
        "type": "object",
        "description": "Aquilia structured fault response (aquilia.faults.Fault)",
        "required": ["code", "message", "domain"],
        "properties": {
            "code": {"type": "string", "description": "Machine-readable fault code", "example": "USER_NOT_FOUND"},
            "message": {"type": "string", "description": "Human-readable fault description"},
            "domain": {"type": "string", "description": "Fault domain, e.g. AUTH, ROUTING, SPECULA"},
            "severity": {"type": "string", "enum": ["info", "warn", "error", "fatal"]},
            "request_id": {"type": "string", "format": "uuid"},
            "detail": {
                "type": "object",
                "additionalProperties": True,
                "description": "Fault-specific structured detail",
            },
            "timestamp": {"type": "string", "format": "date-time"},
        },
        "examples": {
            "not_found": {
                "summary": "Resource not found",
                "value": {
                    "code": "USER_NOT_FOUND",
                    "message": "User with ID 42 does not exist",
                    "domain": "MODEL",
                    "severity": "error",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "detail": {"resource": "User", "id": 42},
                    "timestamp": "2025-01-15T10:30:00Z",
                },
            },
            "validation": {
                "summary": "Contract validation failure",
                "value": {
                    "code": "CONTRACT_SEAL_FAILED",
                    "message": "Request validation failed",
                    "domain": "CONTRACT",
                    "severity": "error",
                    "request_id": "550e8400-e29b-41d4-a716-446655440001",
                    "detail": {"fields": {"email": "Not a valid email", "age": "Must be >= 0"}},
                    "timestamp": "2025-01-15T10:30:00Z",
                },
            },
        },
    }


def aquilia_validation_error_schema() -> dict[str, Any]:
    """422 Unprocessable Entity response body schema (``AquiliaValidationError``)."""
    return {
        "type": "object",
        "description": "Contract validation failure (HTTP 422)",
        "required": ["code", "message", "fields"],
        "properties": {
            "code": {"type": "string", "example": "CONTRACT_SEAL_FAILED"},
            "message": {"type": "string", "example": "Request validation failed"},
            "domain": {"type": "string", "example": "CONTRACT"},
            "fields": {
                "type": "object",
                "description": "Per-field validation errors keyed by field name",
                "additionalProperties": {"type": "string"},
                "example": {"email": "Not a valid email address", "age": "Must be at least 18"},
            },
        },
    }


def fault_to_response(fault_cls: type[Fault]) -> dict[str, Any]:
    """Convert a specific ``Fault`` subclass to an OpenAPI response object."""
    domain = getattr(fault_cls, "domain", None)
    severity = getattr(fault_cls, "severity", None)
    return {
        "description": (fault_cls.__doc__ or fault_cls.__name__).strip().split("\n")[0],
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AquiliaError"},
                "example": {
                    "code": getattr(fault_cls, "code", fault_cls.__name__.upper()),
                    "message": (fault_cls.__doc__ or "An error occurred").strip().split("\n")[0],
                    "domain": getattr(domain, "value", str(domain)) if domain else "UNKNOWN",
                    "severity": getattr(severity, "value", str(severity)) if severity else "error",
                },
            }
        },
    }
