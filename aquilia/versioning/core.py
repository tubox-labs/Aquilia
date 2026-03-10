"""
Aquilia Versioning — Core Types

Defines the fundamental value objects for the versioning system:
- ApiVersion: Immutable, comparable version with semantic major.minor.patch
- VersionChannel: Named release channels (stable, preview, legacy, sunset)
- VersionStatus: Lifecycle status (active, deprecated, sunset, retired)
- VERSION_NEUTRAL / VERSION_ANY: Sentinel values
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import total_ordering
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Union


# ═══════════════════════════════════════════════════════════════════════════
#  Sentinels
# ═══════════════════════════════════════════════════════════════════════════

class _VersionSentinel:
    """Sentinel marker for special version semantics."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _VersionSentinel):
            return self._name == other._name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._name)

    def __bool__(self) -> bool:
        return True


VERSION_NEUTRAL = _VersionSentinel("VERSION_NEUTRAL")
"""Routes marked VERSION_NEUTRAL respond to ALL versions (like NestJS).
Use for health checks, docs, etc."""

VERSION_ANY = _VersionSentinel("VERSION_ANY")
"""Matches any version during resolution. Used internally for fallback."""


# ═══════════════════════════════════════════════════════════════════════════
#  VersionStatus — lifecycle state machine
# ═══════════════════════════════════════════════════════════════════════════

class VersionStatus(str, Enum):
    """Version lifecycle status.

    State machine::

        PREVIEW → ACTIVE → DEPRECATED → SUNSET → RETIRED
                    ↑                       │
                    └── ACTIVE (re-promote) ─┘ (only before RETIRED)
    """
    PREVIEW = "preview"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    RETIRED = "retired"

    @property
    def is_usable(self) -> bool:
        """Whether this version can still serve requests."""
        return self in (VersionStatus.PREVIEW, VersionStatus.ACTIVE, VersionStatus.DEPRECATED)

    @property
    def is_warn(self) -> bool:
        """Whether clients should be warned."""
        return self in (VersionStatus.DEPRECATED, VersionStatus.SUNSET)

    @property
    def is_terminal(self) -> bool:
        """Whether this version is permanently unavailable."""
        return self == VersionStatus.RETIRED


# ═══════════════════════════════════════════════════════════════════════════
#  VersionChannel — named release channel
# ═══════════════════════════════════════════════════════════════════════════

class VersionChannel(str, Enum):
    """Named release channels.

    Channels allow clients to request versions by intent rather than
    number, e.g. ``X-API-Channel: stable`` vs ``X-API-Version: 2.1``.

    The mapping from channel → concrete version is configured in
    ``VersionConfig`` and can change over time (deployment-time, not
    request-time).
    """
    STABLE = "stable"
    PREVIEW = "preview"
    LEGACY = "legacy"
    SUNSET = "sunset"
    CANARY = "canary"

    @classmethod
    def from_string(cls, value: str) -> "VersionChannel":
        """Parse channel from string (case-insensitive)."""
        try:
            return cls(value.lower().strip())
        except ValueError:
            # Allow custom channels by returning STABLE as fallback
            return cls.STABLE


# ═══════════════════════════════════════════════════════════════════════════
#  ApiVersion — immutable, comparable version value object
# ═══════════════════════════════════════════════════════════════════════════

@total_ordering
@dataclass(frozen=True, slots=True)
class ApiVersion:
    """
    Immutable API version value object.

    Supports:
    - Semantic versioning: ``major.minor.patch`` (minor/patch optional)
    - Epoch labels: ``"2025-01"`` → major=2025, minor=1
    - Simple integers: ``"2"`` → major=2, minor=0
    - String prefixes: ``"v2.1"`` → major=2, minor=1

    Comparison uses ``(major, minor, patch)`` tuple ordering.

    Examples::

        ApiVersion(1, 0)          # v1.0
        ApiVersion(2, 1)          # v2.1
        ApiVersion(2025, 1)       # epoch "2025-01"
        ApiVersion.parse("v2.1")  # v2.1
    """

    major: int
    minor: int = 0
    patch: int = 0
    label: str = ""
    status: VersionStatus = VersionStatus.ACTIVE
    channel: Optional[VersionChannel] = None
    metadata: Dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    # ── Comparison ────────────────────────────────────────────────────
    def _compare_key(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ApiVersion):
            return self._compare_key() == other._compare_key()
        if isinstance(other, str):
            try:
                return self._compare_key() == ApiVersion.parse(other)._compare_key()
            except Exception:
                return NotImplemented
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, ApiVersion):
            return self._compare_key() < other._compare_key()
        if isinstance(other, str):
            try:
                return self._compare_key() < ApiVersion.parse(other)._compare_key()
            except Exception:
                return NotImplemented
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._compare_key())

    # ── Display ───────────────────────────────────────────────────────
    def __str__(self) -> str:
        if self.label:
            return self.label
        if self.patch:
            return f"{self.major}.{self.minor}.{self.patch}"
        if self.minor:
            return f"{self.major}.{self.minor}"
        return str(self.major)

    def __repr__(self) -> str:
        parts = [f"ApiVersion({self.major}, {self.minor}"]
        if self.patch:
            parts[0] += f", {self.patch}"
        parts[0] += ")"
        if self.label:
            parts.append(f"label={self.label!r}")
        if self.status != VersionStatus.ACTIVE:
            parts.append(f"status={self.status.value}")
        return " ".join(parts)

    @property
    def is_usable(self) -> bool:
        """Whether this version can serve requests."""
        return self.status.is_usable

    @property
    def short(self) -> str:
        """Short display form (e.g. 'v2.1')."""
        return f"v{self}"

    @property
    def url_segment(self) -> str:
        """URL path segment form (e.g. 'v2' or 'v2.1')."""
        if self.minor:
            return f"v{self.major}.{self.minor}"
        return f"v{self.major}"

    def matches(self, other: "ApiVersion") -> bool:
        """Check if this version matches another (major.minor match only)."""
        return self.major == other.major and self.minor == other.minor

    def is_compatible_with(self, other: "ApiVersion") -> bool:
        """Check if this version is backward-compatible with another.

        Compatible = same major, >= minor.
        """
        return self.major == other.major and (
            self.minor >= other.minor
        )

    def with_status(self, status: VersionStatus) -> "ApiVersion":
        """Return a copy with updated status."""
        return ApiVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            label=self.label,
            status=status,
            channel=self.channel,
            metadata=self.metadata,
        )

    def with_channel(self, channel: VersionChannel) -> "ApiVersion":
        """Return a copy with updated channel."""
        return ApiVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            label=self.label,
            status=self.status,
            channel=channel,
            metadata=self.metadata,
        )

    # ── Parsing ───────────────────────────────────────────────────────
    @classmethod
    def parse(cls, raw: str) -> "ApiVersion":
        """
        Parse version from string.

        Supports:
        - ``"1"`` → (1, 0, 0)
        - ``"1.0"`` → (1, 0, 0)
        - ``"2.1"`` → (2, 1, 0)
        - ``"2.1.3"`` → (2, 1, 3)
        - ``"v2"`` → (2, 0, 0)
        - ``"v2.1"`` → (2, 1, 0)
        - ``"2025-01"`` → (2025, 1, 0) with label="2025-01"
        """
        from .parser import SemanticVersionParser
        return SemanticVersionParser().parse(raw)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "label": self.label,
            "status": self.status.value,
            "channel": self.channel.value if self.channel else None,
            "display": str(self),
        }
