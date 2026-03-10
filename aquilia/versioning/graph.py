"""
Aquilia Versioning — Version Graph

Compile-time version relationship map. The graph is built once during
server startup and encodes:

- All registered versions and their statuses
- Successor/predecessor relationships (for migration hints)
- Channel → version bindings
- Route-to-version mappings
- Version compatibility ranges

This eliminates per-request version tree walks — all lookups are O(1)
against pre-computed hash maps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from .core import ApiVersion, VersionChannel, VersionStatus


@dataclass
class VersionNode:
    """
    A node in the version graph.

    Each node represents a registered API version with its
    relationships and metadata.
    """

    version: ApiVersion
    successor: Optional[ApiVersion] = None
    predecessor: Optional[ApiVersion] = None
    channels: Set[VersionChannel] = field(default_factory=set)
    routes: Set[str] = field(default_factory=set)  # set of "METHOD /path" strings
    controllers: Set[str] = field(default_factory=set)  # controller class names
    deprecated_at: Optional[datetime] = None
    sunset_at: Optional[datetime] = None
    migration_url: Optional[str] = None

    @property
    def status(self) -> VersionStatus:
        return self.version.status

    @property
    def is_usable(self) -> bool:
        return self.version.is_usable

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for admin dashboard / API."""
        return {
            "version": str(self.version),
            "status": self.version.status.value,
            "successor": str(self.successor) if self.successor else None,
            "predecessor": str(self.predecessor) if self.predecessor else None,
            "channels": [c.value for c in self.channels],
            "route_count": len(self.routes),
            "controller_count": len(self.controllers),
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "sunset_at": self.sunset_at.isoformat() if self.sunset_at else None,
            "migration_url": self.migration_url,
        }


class VersionGraph:
    """
    Compile-time version relationship graph.

    Built during server startup from:
    1. Configured version list (``VersionConfig.versions``)
    2. Controller ``version`` attributes
    3. Route-level ``@version()`` decorators
    4. Channel mappings

    All lookups are O(1) against pre-computed maps.
    """

    def __init__(self) -> None:
        self._nodes: Dict[ApiVersion, VersionNode] = {}
        self._by_string: Dict[str, ApiVersion] = {}
        self._by_channel: Dict[VersionChannel, ApiVersion] = {}
        self._latest: Optional[ApiVersion] = None
        self._sorted_versions: List[ApiVersion] = []
        self._frozen = False

    # ── Registration ──────────────────────────────────────────────────

    def register(
        self,
        version: ApiVersion,
        *,
        successor: Optional[ApiVersion] = None,
        predecessor: Optional[ApiVersion] = None,
        channels: Optional[Set[VersionChannel]] = None,
        deprecated_at: Optional[datetime] = None,
        sunset_at: Optional[datetime] = None,
        migration_url: Optional[str] = None,
    ) -> VersionNode:
        """Register a version in the graph."""
        if self._frozen:
            raise RuntimeError("Version graph is frozen — cannot register new versions after startup.")

        if version in self._nodes:
            node = self._nodes[version]
            # Merge rather than overwrite
            if successor:
                node.successor = successor
            if predecessor:
                node.predecessor = predecessor
            if channels:
                node.channels.update(channels)
            if deprecated_at:
                node.deprecated_at = deprecated_at
            if sunset_at:
                node.sunset_at = sunset_at
            if migration_url:
                node.migration_url = migration_url
            return node

        node = VersionNode(
            version=version,
            successor=successor,
            predecessor=predecessor,
            channels=channels or set(),
            deprecated_at=deprecated_at,
            sunset_at=sunset_at,
            migration_url=migration_url,
        )
        self._nodes[version] = node
        self._by_string[str(version)] = version

        # Update channel map
        if channels:
            for channel in channels:
                self._by_channel[channel] = version

        return node

    def register_route(self, version: ApiVersion, method: str, path: str) -> None:
        """Associate a route with a version."""
        if version not in self._nodes:
            self.register(version)
        self._nodes[version].routes.add(f"{method} {path}")

    def register_controller(self, version: ApiVersion, controller_name: str) -> None:
        """Associate a controller with a version."""
        if version not in self._nodes:
            self.register(version)
        self._nodes[version].controllers.add(controller_name)

    def set_channel(self, channel: VersionChannel, version: ApiVersion) -> None:
        """Map a channel to a concrete version."""
        self._by_channel[channel] = version
        if version in self._nodes:
            self._nodes[version].channels.add(channel)

    # ── Freezing (compile) ────────────────────────────────────────────

    def freeze(self) -> None:
        """
        Freeze the graph after startup.

        Builds sorted version list and infers successor/predecessor
        relationships if not explicitly set.
        """
        self._sorted_versions = sorted(self._nodes.keys())

        # Auto-link successor/predecessor if not explicit
        for i, v in enumerate(self._sorted_versions):
            node = self._nodes[v]
            if node.predecessor is None and i > 0:
                node.predecessor = self._sorted_versions[i - 1]
            if node.successor is None and i < len(self._sorted_versions) - 1:
                node.successor = self._sorted_versions[i + 1]

        # Set latest to highest active version
        active = [
            v for v in self._sorted_versions
            if v.status in (VersionStatus.ACTIVE, VersionStatus.PREVIEW)
        ]
        if active:
            self._latest = active[-1]
        elif self._sorted_versions:
            self._latest = self._sorted_versions[-1]

        self._frozen = True

    # ── Lookups (all O(1)) ────────────────────────────────────────────

    def get(self, version: ApiVersion) -> Optional[VersionNode]:
        """Get node by ApiVersion."""
        return self._nodes.get(version)

    def get_by_string(self, version_str: str) -> Optional[ApiVersion]:
        """Get ApiVersion by string representation."""
        return self._by_string.get(version_str)

    def get_by_channel(self, channel: VersionChannel) -> Optional[ApiVersion]:
        """Get version for a named channel."""
        return self._by_channel.get(channel)

    @property
    def latest(self) -> Optional[ApiVersion]:
        """The latest active version."""
        return self._latest

    @property
    def versions(self) -> List[ApiVersion]:
        """All registered versions (sorted ascending)."""
        return list(self._sorted_versions)

    @property
    def active_versions(self) -> List[ApiVersion]:
        """Only active/preview versions."""
        return [v for v in self._sorted_versions if v.is_usable]

    @property
    def channels(self) -> Dict[VersionChannel, ApiVersion]:
        """Channel → version mapping."""
        return dict(self._by_channel)

    def contains(self, version: ApiVersion) -> bool:
        """Check if a version is registered."""
        return version in self._nodes

    def is_supported(self, version: ApiVersion) -> bool:
        """Check if a version is registered AND usable."""
        node = self._nodes.get(version)
        return node is not None and node.is_usable

    def get_successor(self, version: ApiVersion) -> Optional[ApiVersion]:
        """Get the successor version (for migration hints)."""
        node = self._nodes.get(version)
        return node.successor if node else None

    def get_migration_url(self, version: ApiVersion) -> Optional[str]:
        """Get migration guide URL for a version."""
        node = self._nodes.get(version)
        return node.migration_url if node else None

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire graph for admin dashboard."""
        return {
            "versions": [
                self._nodes[v].to_dict() for v in self._sorted_versions
            ],
            "channels": {
                c.value: str(v) for c, v in self._by_channel.items()
            },
            "latest": str(self._latest) if self._latest else None,
            "total": len(self._nodes),
            "active": len(self.active_versions),
        }

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, version: ApiVersion) -> bool:
        return version in self._nodes

    def __iter__(self):
        return iter(self._sorted_versions)
