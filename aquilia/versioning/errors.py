"""
Aquilia Versioning — Version Errors

Structured error types for the versioning system, integrated with
Aquilia's Fault system.
"""

from __future__ import annotations

from typing import Any

from ..faults import Fault, FaultDomain, Severity


class VersionError(Fault):
    """Base class for all versioning errors."""

    domain = FaultDomain.ROUTING
    severity = Severity.ERROR
    public = True


class InvalidVersionError(VersionError):
    """Raised when a version string cannot be parsed."""

    code = "INVALID_API_VERSION"
    message = "Invalid API version"

    def __init__(self, raw_version: str, reason: str = "", **kw: Any) -> None:
        super().__init__(
            code=self.code,
            message=f"Invalid API version '{raw_version}'. {reason}".strip(),
            metadata={"raw_version": raw_version, "reason": reason, **kw},
        )
        self.raw_version = raw_version


class UnsupportedVersionError(VersionError):
    """Raised when a valid version is not in the supported set."""

    code = "UNSUPPORTED_API_VERSION"
    message = "Unsupported API version"

    def __init__(
        self,
        version: Any,
        supported: list | None = None,
        **kw: Any,
    ) -> None:
        supported_str = ", ".join(str(v) for v in supported) if supported else "none"
        super().__init__(
            code=self.code,
            message=(f"API version '{version}' is not supported. Supported versions: {supported_str}"),
            metadata={
                "requested_version": str(version),
                "supported_versions": [str(v) for v in supported] if supported else [],
                **kw,
            },
        )
        self.version = version
        self.supported = supported or []


class VersionSunsetError(VersionError):
    """Raised when a version has been sunset (permanently retired)."""

    code = "API_VERSION_SUNSET"
    message = "API version has been retired"

    def __init__(
        self,
        version: Any,
        sunset_date: str | None = None,
        migration_url: str | None = None,
        successor: Any | None = None,
        **kw: Any,
    ) -> None:
        parts = [f"API version '{version}' has been retired."]
        if sunset_date:
            parts.append(f"Sunset date: {sunset_date}.")
        if successor:
            parts.append(f"Please migrate to version '{successor}'.")
        if migration_url:
            parts.append(f"Migration guide: {migration_url}")

        super().__init__(
            code=self.code,
            message=" ".join(parts),
            metadata={
                "version": str(version),
                "sunset_date": sunset_date,
                "migration_url": migration_url,
                "successor": str(successor) if successor else None,
                **kw,
            },
        )
        self.version = version
        self.sunset_date = sunset_date
        self.migration_url = migration_url
        self.successor = successor


class MissingVersionError(VersionError):
    """Raised when no version is present and no default is configured."""

    code = "MISSING_API_VERSION"
    message = "API version is required"

    def __init__(self, strategies: list | None = None, **kw: Any) -> None:
        hint_parts = []
        if strategies:
            hint_parts.append("Send version via: " + ", ".join(str(s) for s in strategies))
        super().__init__(
            code=self.code,
            message=("API version is required but was not provided. " + " ".join(hint_parts)).strip(),
            metadata={
                "strategies": [str(s) for s in strategies] if strategies else [],
                **kw,
            },
        )


class VersionNegotiationError(VersionError):
    """Raised when version negotiation fails."""

    code = "VERSION_NEGOTIATION_FAILED"
    message = "Version negotiation failed"

    def __init__(
        self,
        requested: Any,
        available: list | None = None,
        **kw: Any,
    ) -> None:
        available_str = ", ".join(str(v) for v in available) if available else "none"
        super().__init__(
            code=self.code,
            message=(f"Could not negotiate API version for request '{requested}'. Available versions: {available_str}"),
            metadata={
                "requested": str(requested),
                "available": [str(v) for v in available] if available else [],
                **kw,
            },
        )
