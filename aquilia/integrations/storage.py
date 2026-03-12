"""
StorageIntegration — typed file storage configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StorageIntegration:
    """
    Typed file storage configuration.

    Example::

        StorageIntegration(
            default="local",
            backends={"local": {"backend": "local", "root": "./uploads"}},
        )
    """

    _integration_type: str = field(default="storage", init=False, repr=False)

    default: str = "default"
    backends: dict[str, Any] | None = None
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        backend_list: list[dict[str, Any]] = []
        for alias, cfg in (self.backends or {}).items():
            if hasattr(cfg, "to_dict"):
                entry = cfg.to_dict()
            elif isinstance(cfg, dict):
                entry = dict(cfg)
            else:
                entry = {"backend": str(cfg)}
            entry.setdefault("alias", alias)
            if alias == self.default:
                entry["default"] = True
            backend_list.append(entry)

        return {
            "_integration_type": "storage",
            "enabled": self.enabled,
            "default": self.default,
            "backends": backend_list,
        }
