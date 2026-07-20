"""
Specula fault hierarchy — all faults carry the SPECULA fault domain.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

#: Specula's own fault domain — every Specula fault carries this.
SPECULA_DOMAIN = FaultDomain.custom(
    "SPECULA",
    "Specula API Observatory subsystem (aquilia.specula)",
)


class SpeculaFault(Fault):
    """Base fault for all Specula errors."""

    code = "SPECULA_ERROR"
    message = "Specula error"
    status_code = 500

    def __init__(self, message: str | None = None, *, detail: Any | None = None, **kwargs: Any):
        kwargs.setdefault("domain", SPECULA_DOMAIN)
        kwargs.setdefault("severity", Severity.ERROR)
        kwargs.setdefault("public", True)
        if detail is not None:
            self.detail = detail
            kwargs["detail"] = detail
        super().__init__(message=message, **kwargs)


class SpecBuildFault(SpeculaFault):
    """Raised when the OpenAPI 3.1.0 spec cannot be generated."""

    code = "SPECULA_SPEC_BUILD_FAILED"
    message = "Failed to build OpenAPI specification"
    status_code = 500


class SchemaResolutionFault(SpeculaFault):
    """Raised when a Contract/Model/type cannot be mapped to a JSON Schema."""

    code = "SPECULA_SCHEMA_RESOLUTION_FAILED"
    message = "Failed to resolve schema"
    status_code = 500


class SpecCacheFault(SpeculaFault):
    """Raised on CacheService read/write failure. Non-fatal — falls back."""

    code = "SPECULA_SPEC_CACHE_FAILED"
    message = "Spec cache operation failed"
    status_code = 500

    def __init__(self, message: str | None = None, **kwargs: Any):
        kwargs.setdefault("severity", Severity.WARN)
        super().__init__(message=message, **kwargs)


class VersionNotFoundFault(SpeculaFault):
    """Raised when a requested API version does not exist in the version graph."""

    code = "SPECULA_VERSION_NOT_FOUND"
    message = "API version not found"
    status_code = 404


class MockServerFault(SpeculaFault):
    """Raised when the mock server encounters an unresolvable operation."""

    code = "SPECULA_MOCK_SERVER_ERROR"
    message = "Mock server error"
    status_code = 500


class ObservatoryForbiddenFault(SpeculaFault):
    """Raised when an unauthenticated user accesses a protected observatory."""

    code = "SPECULA_OBSERVATORY_FORBIDDEN"
    message = "Observatory access forbidden"
    status_code = 403
