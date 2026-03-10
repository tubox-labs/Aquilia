"""
Aquilia Versioning — Version Negotiation

Intelligent version selection when the client sends a version range,
wildcard, or when the exact version is not available.

Negotiation strategies (unique to Aquilia):
- **exact**: Only match the exact version
- **compatible**: Match any backward-compatible version (same major)
- **latest**: Always use the latest active version
- **best_match**: Find the highest matching version within constraints
- **nearest**: Find the nearest registered version
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from .core import ApiVersion, VersionStatus, VERSION_NEUTRAL
from .errors import VersionNegotiationError

if TYPE_CHECKING:
    from .graph import VersionGraph


class NegotiationMode(str, Enum):
    """Version negotiation mode."""
    EXACT = "exact"
    COMPATIBLE = "compatible"
    LATEST = "latest"
    BEST_MATCH = "best_match"
    NEAREST = "nearest"


class VersionNegotiator:
    """
    Version negotiation engine.

    Resolves a requested version to the best available version
    based on the configured negotiation mode.
    """

    def __init__(
        self,
        graph: "VersionGraph",
        mode: NegotiationMode = NegotiationMode.EXACT,
    ) -> None:
        self._graph = graph
        self._mode = mode

    @property
    def mode(self) -> NegotiationMode:
        return self._mode

    def negotiate(
        self,
        requested: ApiVersion,
        *,
        fallback: Optional[ApiVersion] = None,
    ) -> ApiVersion:
        """
        Negotiate the best version for a request.

        Args:
            requested: The version requested by the client.
            fallback: Fallback version if negotiation fails.

        Returns:
            The resolved ``ApiVersion``.

        Raises:
            VersionNegotiationError: If no suitable version is found.
        """
        if self._mode == NegotiationMode.EXACT:
            return self._negotiate_exact(requested, fallback)
        elif self._mode == NegotiationMode.COMPATIBLE:
            return self._negotiate_compatible(requested, fallback)
        elif self._mode == NegotiationMode.LATEST:
            return self._negotiate_latest(fallback)
        elif self._mode == NegotiationMode.BEST_MATCH:
            return self._negotiate_best_match(requested, fallback)
        elif self._mode == NegotiationMode.NEAREST:
            return self._negotiate_nearest(requested, fallback)
        else:
            return self._negotiate_exact(requested, fallback)

    # ── Strategies ────────────────────────────────────────────────────

    def _negotiate_exact(
        self,
        requested: ApiVersion,
        fallback: Optional[ApiVersion],
    ) -> ApiVersion:
        """Exact match only."""
        if self._graph.is_supported(requested):
            return requested
        if fallback and self._graph.is_supported(fallback):
            return fallback
        raise VersionNegotiationError(
            requested=requested,
            available=self._graph.active_versions,
        )

    def _negotiate_compatible(
        self,
        requested: ApiVersion,
        fallback: Optional[ApiVersion],
    ) -> ApiVersion:
        """Match any backward-compatible version (same major, >= minor)."""
        # Try exact first
        if self._graph.is_supported(requested):
            return requested

        # Find highest compatible version
        compatible = [
            v for v in self._graph.active_versions
            if v.major == requested.major and v.minor >= requested.minor
        ]
        if compatible:
            return compatible[-1]  # Highest compatible

        if fallback and self._graph.is_supported(fallback):
            return fallback

        raise VersionNegotiationError(
            requested=requested,
            available=self._graph.active_versions,
        )

    def _negotiate_latest(
        self,
        fallback: Optional[ApiVersion],
    ) -> ApiVersion:
        """Always return the latest active version."""
        latest = self._graph.latest
        if latest:
            return latest
        if fallback and self._graph.is_supported(fallback):
            return fallback
        raise VersionNegotiationError(
            requested="latest",
            available=self._graph.active_versions,
        )

    def _negotiate_best_match(
        self,
        requested: ApiVersion,
        fallback: Optional[ApiVersion],
    ) -> ApiVersion:
        """
        Find the best matching version.

        Priority:
        1. Exact match
        2. Same major, highest minor
        3. Nearest version
        """
        # 1. Exact
        if self._graph.is_supported(requested):
            return requested

        # 2. Same major
        same_major = [
            v for v in self._graph.active_versions
            if v.major == requested.major
        ]
        if same_major:
            # Prefer >= requested.minor, else take highest available
            gte = [v for v in same_major if v.minor >= requested.minor]
            if gte:
                return gte[0]  # Lowest that's >= requested
            return same_major[-1]  # Highest in same major

        # 3. Nearest
        return self._negotiate_nearest(requested, fallback)

    def _negotiate_nearest(
        self,
        requested: ApiVersion,
        fallback: Optional[ApiVersion],
    ) -> ApiVersion:
        """Find the nearest registered version by distance."""
        active = self._graph.active_versions
        if not active:
            if fallback and self._graph.is_supported(fallback):
                return fallback
            raise VersionNegotiationError(
                requested=requested,
                available=[],
            )

        def distance(v: ApiVersion) -> int:
            return abs(v.major - requested.major) * 1000 + abs(v.minor - requested.minor)

        return min(active, key=distance)
