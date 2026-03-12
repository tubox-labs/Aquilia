"""
TemplatesIntegration — typed template configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplatesIntegration:
    """
    Typed template engine configuration.

    Supports both direct construction and fluent builder style::

        # Direct
        TemplatesIntegration(search_paths=["templates", "shared"])

        # Fluent
        TemplatesIntegration.builder().source("templates").cached().secure()
    """

    _integration_type: str = field(default="templates", init=False, repr=False)

    enabled: bool = True
    search_paths: list[str] = field(default_factory=lambda: ["templates"])
    cache: str = "memory"
    sandbox: bool = True
    sandbox_policy: str = "strict"
    precompile: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "templates",
            "enabled": self.enabled,
            "search_paths": list(self.search_paths),
            "cache": self.cache,
            "sandbox": self.sandbox,
            "sandbox_policy": self.sandbox_policy,
            "precompile": self.precompile,
        }

    # ── Fluent builder ───────────────────────────────────────────────

    class _Builder(dict):
        """Fluent builder inheriting from dict for compatibility."""

        def __init__(self) -> None:
            super().__init__(
                {
                    "enabled": True,
                    "search_paths": ["templates"],
                    "cache": "memory",
                    "sandbox": True,
                    "precompile": False,
                }
            )

        def source(self, *paths: str) -> TemplatesIntegration._Builder:
            current = self.get("search_paths", [])
            if current == ["templates"]:
                current = []
            self["search_paths"] = current + list(paths)
            return self

        def scan_modules(self) -> TemplatesIntegration._Builder:
            return self

        def cached(self, strategy: str = "memory") -> TemplatesIntegration._Builder:
            self["cache"] = strategy
            return self

        def secure(self, strict: bool = True) -> TemplatesIntegration._Builder:
            self["sandbox"] = True
            self["sandbox_policy"] = "strict" if strict else "permissive"
            return self

        def unsafe_dev_mode(self) -> TemplatesIntegration._Builder:
            self["sandbox"] = False
            self["cache"] = "none"
            return self

        def precompile(self) -> TemplatesIntegration._Builder:
            self["precompile"] = True
            return self

    @classmethod
    def builder(cls) -> _Builder:
        """Start a fluent builder."""
        return cls._Builder()

    @classmethod
    def source(cls, *paths: str) -> _Builder:
        """Start builder with source paths."""
        return cls._Builder().source(*paths)

    @classmethod
    def defaults(cls) -> _Builder:
        """Start with default configuration."""
        return cls._Builder()
