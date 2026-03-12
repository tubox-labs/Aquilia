"""
LoggingIntegration — typed request/response logging configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoggingIntegration:
    """
    Typed request logging configuration.

    Example::

        LoggingIntegration(
            slow_threshold_ms=500,
            skip_paths=["/health", "/metrics"],
        )
    """

    _integration_type: str = field(default="logging", init=False, repr=False)

    format: str = "%(method)s %(path)s %(status)s %(duration_ms).1fms"
    level: str = "INFO"
    slow_threshold_ms: float = 1000.0
    skip_paths: list[str] = field(default_factory=lambda: ["/health", "/healthz", "/ready", "/metrics"])
    include_headers: bool = False
    include_query: bool = True
    include_user_agent: bool = False
    log_request_body: bool = False
    log_response_body: bool = False
    colorize: bool = True
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "logging",
            "enabled": self.enabled,
            "format": self.format,
            "level": self.level,
            "slow_threshold_ms": self.slow_threshold_ms,
            "skip_paths": self.skip_paths,
            "include_headers": self.include_headers,
            "include_query": self.include_query,
            "include_user_agent": self.include_user_agent,
            "log_request_body": self.log_request_body,
            "log_response_body": self.log_response_body,
            "colorize": self.colorize,
        }
