"""
VersioningIntegration — typed API versioning configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VersioningIntegration:
    """
    Typed API versioning configuration.

    Example::

        VersioningIntegration(
            strategy="composite",
            versions=["1.0", "2.0", "2.1"],
            default_version="2.0",
            channels={"stable": "2.0", "preview": "2.1"},
        )
    """

    _integration_type: str = field(default="versioning", init=False, repr=False)

    strategy: str = "header"
    versions: list[str] = field(default_factory=list)
    default_version: str | None = None
    require_version: bool = False
    header_name: str = "X-API-Version"
    query_param: str = "api_version"
    url_prefix: str = "v"
    url_segment_index: int = 0
    strip_version_from_path: bool = True
    media_type_param: str = "version"
    channels: dict[str, str] = field(default_factory=dict)
    channel_header: str = "X-API-Channel"
    channel_query_param: str = "api_channel"
    negotiation_mode: str = "exact"
    sunset_policy: Any | None = None
    sunset_schedules: dict[str, dict[str, Any]] | None = None
    include_version_header: bool = True
    response_header_name: str = "X-API-Version"
    include_supported_versions_header: bool = True
    neutral_paths: list[str] = field(default_factory=lambda: ["/_health", "/openapi.json", "/docs", "/redoc"])
    enabled: bool = True

    def __post_init__(self) -> None:
        valid_strategies = ("url", "header", "query", "media_type", "channel", "composite")
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid versioning strategy {self.strategy!r}. Must be one of {valid_strategies}")
        valid_negotiation = ("exact", "compatible", "best_match", "nearest", "latest")
        if self.negotiation_mode not in valid_negotiation:
            raise ValueError(f"Invalid negotiation mode {self.negotiation_mode!r}. Must be one of {valid_negotiation}")

    def to_dict(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "_integration_type": "versioning",
            "enabled": self.enabled,
            "strategy": self.strategy,
            "versions": list(self.versions),
            "default_version": self.default_version,
            "require_version": self.require_version,
            "header_name": self.header_name,
            "query_param": self.query_param,
            "url_prefix": self.url_prefix,
            "url_segment_index": self.url_segment_index,
            "strip_version_from_path": self.strip_version_from_path,
            "media_type_param": self.media_type_param,
            "channels": dict(self.channels),
            "channel_header": self.channel_header,
            "channel_query_param": self.channel_query_param,
            "negotiation_mode": self.negotiation_mode,
            "include_version_header": self.include_version_header,
            "response_header_name": self.response_header_name,
            "include_supported_versions_header": self.include_supported_versions_header,
            "neutral_paths": list(self.neutral_paths),
        }
        if self.sunset_policy is not None:
            config["sunset_policy"] = self.sunset_policy
        if self.sunset_schedules:
            config["sunset_schedules"] = self.sunset_schedules
        return config
