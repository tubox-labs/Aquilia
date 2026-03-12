"""
Aquilia Versioning — Sunset Lifecycle

RFC 8594 (Sunset Header) and RFC 9745 (Deprecation Header) compliant
sunset/deprecation management.

Features:
- Automatic ``Deprecation`` and ``Sunset`` response headers
- ``Link`` header with migration guide URL
- Configurable grace periods
- Hard sunset enforcement (reject requests to retired versions)
- Sunset schedule registry for admin visibility

Unique to Aquilia:
- Declarative sunset policies per-version
- Channel-aware sunset (sunset "legacy" channel, not just version number)
- Gradual sunset with percentage-based traffic rejection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from .core import ApiVersion, VersionStatus

if TYPE_CHECKING:
    from ..response import Response  # noqa: F401


@dataclass
class SunsetPolicy:
    """
    Global sunset policy configuration.

    Controls how deprecation and sunset are communicated to clients.
    """

    # Whether to add Deprecation/Sunset headers automatically
    warn_header: bool = True

    # Grace period: how long a version stays DEPRECATED before SUNSET
    grace_period: timedelta = field(default_factory=lambda: timedelta(days=180))

    # Whether to hard-reject requests to SUNSET versions (410 Gone)
    enforce_sunset: bool = True

    # Whether to hard-reject requests to RETIRED versions (410 Gone)
    enforce_retired: bool = True

    # Custom response message for sunset versions
    sunset_message: str = (
        "This API version has been retired. "
        "Please migrate to the latest version."
    )

    # Default migration guide URL template
    # {version} is replaced with the sunset version string
    migration_url_template: str | None = None

    # Gradual sunset: percentage of requests to reject (0-100)
    # 0 = no rejection (warn only), 100 = full rejection
    gradual_rejection_percent: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "warn_header": self.warn_header,
            "grace_period_days": self.grace_period.days,
            "enforce_sunset": self.enforce_sunset,
            "enforce_retired": self.enforce_retired,
            "gradual_rejection_percent": self.gradual_rejection_percent,
        }


@dataclass
class SunsetEntry:
    """
    Per-version sunset schedule entry.
    """

    version: ApiVersion
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    retired_at: datetime | None = None
    successor: ApiVersion | None = None
    migration_url: str | None = None
    notes: str = ""

    @property
    def is_deprecated(self) -> bool:
        if self.deprecated_at is None:
            return False
        return datetime.now(timezone.utc) >= self.deprecated_at

    @property
    def is_sunset(self) -> bool:
        if self.sunset_at is None:
            return False
        return datetime.now(timezone.utc) >= self.sunset_at

    @property
    def is_retired(self) -> bool:
        if self.retired_at is None:
            return False
        return datetime.now(timezone.utc) >= self.retired_at

    @property
    def effective_status(self) -> VersionStatus:
        """Compute current status from dates."""
        if self.is_retired:
            return VersionStatus.RETIRED
        if self.is_sunset:
            return VersionStatus.SUNSET
        if self.is_deprecated:
            return VersionStatus.DEPRECATED
        return self.version.status

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": str(self.version),
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "sunset_at": self.sunset_at.isoformat() if self.sunset_at else None,
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
            "successor": str(self.successor) if self.successor else None,
            "migration_url": self.migration_url,
            "effective_status": self.effective_status.value,
            "notes": self.notes,
        }


class SunsetRegistry:
    """
    Registry of sunset schedules.

    Tracks deprecation/sunset/retirement dates for each version
    and provides lookup for the SunsetEnforcer.
    """

    def __init__(self) -> None:
        self._entries: dict[ApiVersion, SunsetEntry] = {}

    def register(
        self,
        version: ApiVersion,
        *,
        deprecated_at: datetime | None = None,
        sunset_at: datetime | None = None,
        retired_at: datetime | None = None,
        successor: ApiVersion | None = None,
        migration_url: str | None = None,
        notes: str = "",
    ) -> SunsetEntry:
        """Register a sunset schedule for a version."""
        entry = SunsetEntry(
            version=version,
            deprecated_at=deprecated_at,
            sunset_at=sunset_at,
            retired_at=retired_at,
            successor=successor,
            migration_url=migration_url,
            notes=notes,
        )
        self._entries[version] = entry
        return entry

    def get(self, version: ApiVersion) -> SunsetEntry | None:
        """Get sunset entry for a version."""
        return self._entries.get(version)

    def get_deprecated(self) -> list[SunsetEntry]:
        """Get all currently deprecated versions."""
        return [e for e in self._entries.values() if e.is_deprecated and not e.is_sunset]

    def get_sunset(self) -> list[SunsetEntry]:
        """Get all currently sunset versions."""
        return [e for e in self._entries.values() if e.is_sunset and not e.is_retired]

    def get_retired(self) -> list[SunsetEntry]:
        """Get all retired versions."""
        return [e for e in self._entries.values() if e.is_retired]

    @property
    def entries(self) -> list[SunsetEntry]:
        return list(self._entries.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedules": [e.to_dict() for e in self._entries.values()],
            "deprecated_count": len(self.get_deprecated()),
            "sunset_count": len(self.get_sunset()),
            "retired_count": len(self.get_retired()),
        }


class SunsetEnforcer:
    """
    Enforces sunset policies at request time.

    Adds deprecation/sunset response headers (RFC 8594/9745) and
    optionally rejects requests to retired versions.
    """

    def __init__(
        self,
        policy: SunsetPolicy,
        registry: SunsetRegistry,
    ) -> None:
        self._policy = policy
        self._registry = registry
        self._rejection_counter = 0  # For gradual sunset

    def check(self, version: ApiVersion) -> dict[str, Any] | None:
        """
        Check if a version is sunset/retired and should be rejected.

        Returns:
            None if the request is allowed.
            Dict with error info if the request should be rejected.
        """
        entry = self._registry.get(version)
        if entry is None:
            return None

        status = entry.effective_status

        # RETIRED → always reject
        if status == VersionStatus.RETIRED and self._policy.enforce_retired:
            return {
                "code": "API_VERSION_RETIRED",
                "message": self._policy.sunset_message,
                "version": str(version),
                "successor": str(entry.successor) if entry.successor else None,
                "migration_url": entry.migration_url,
            }

        # SUNSET → reject based on policy
        if status == VersionStatus.SUNSET and self._policy.enforce_sunset:
            # Gradual rejection
            if self._policy.gradual_rejection_percent > 0:
                self._rejection_counter += 1
                if (self._rejection_counter % 100) >= self._policy.gradual_rejection_percent:
                    return None  # Allow this request

            return {
                "code": "API_VERSION_SUNSET",
                "message": self._policy.sunset_message,
                "version": str(version),
                "successor": str(entry.successor) if entry.successor else None,
                "migration_url": entry.migration_url,
            }

        return None

    def get_headers(self, version: ApiVersion) -> dict[str, str]:
        """
        Get deprecation/sunset response headers for a version.

        Headers added (RFC 8594/9745):
        - ``Deprecation``: ISO 8601 date when version was deprecated
        - ``Sunset``: ISO 8601 date when version will be/was sunset
        - ``Link``: Migration guide URL with ``rel="deprecation"``
        """
        if not self._policy.warn_header:
            return {}

        entry = self._registry.get(version)
        if entry is None:
            return {}

        headers: dict[str, str] = {}
        status = entry.effective_status

        if status in (VersionStatus.DEPRECATED, VersionStatus.SUNSET):
            # Deprecation header (RFC 9745)
            if entry.deprecated_at:
                headers["Deprecation"] = entry.deprecated_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            # Sunset header (RFC 8594)
            if entry.sunset_at:
                headers["Sunset"] = entry.sunset_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            # Link header with migration guide
            migration_url = entry.migration_url
            if not migration_url and self._policy.migration_url_template:
                migration_url = self._policy.migration_url_template.replace(
                    "{version}", str(version)
                )
            if migration_url:
                headers["Link"] = f'<{migration_url}>; rel="deprecation"'

            # Successor hint
            if entry.successor:
                headers["X-API-Successor-Version"] = str(entry.successor)

        return headers
