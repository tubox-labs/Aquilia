"""
StaticFilesIntegration — typed static file serving configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StaticFilesIntegration:
    """
    Typed static file serving configuration.

    Example::

        StaticFilesIntegration(
            directories={"/static": "static", "/media": "uploads"},
            cache_max_age=86400,
        )
    """

    _integration_type: str = field(default="static_files", init=False, repr=False)

    directories: Dict[str, str] = field(default_factory=lambda: {"/static": "static"})
    cache_max_age: int = 86400
    immutable: bool = False
    etag: bool = True
    gzip: bool = True
    brotli: bool = True
    memory_cache: bool = True
    html5_history: bool = False
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "static_files",
            "enabled": self.enabled,
            "directories": dict(self.directories),
            "cache_max_age": self.cache_max_age,
            "immutable": self.immutable,
            "etag": self.etag,
            "gzip": self.gzip,
            "brotli": self.brotli,
            "memory_cache": self.memory_cache,
            "html5_history": self.html5_history,
        }
