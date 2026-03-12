"""
DatabaseIntegration — typed database configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DatabaseIntegration:
    """
    Typed database integration config.

    Accepts either a ``url`` string (backward compatible) or a typed
    ``config`` object (``SqliteConfig``, ``PostgresConfig``, etc.).

    Examples::

        # URL-based
        DatabaseIntegration(url="sqlite:///app.db")

        # Config-based
        from aquilia.db.configs import PostgresConfig
        DatabaseIntegration(
            config=PostgresConfig(host="localhost", name="mydb"),
            pool_size=10,
        )
    """

    _integration_type: str = field(default="database", init=False, repr=False)

    url: str | None = None
    config: Any | None = field(default=None, repr=False)
    auto_connect: bool = True
    auto_create: bool = True
    auto_migrate: bool = False
    migrations_dir: str = "migrations"
    pool_size: int = 5
    echo: bool = False
    model_paths: list[str] = field(default_factory=list)
    scan_dirs: list[str] = field(default_factory=lambda: ["models"])

    def to_dict(self) -> dict[str, Any]:
        if self.config is not None:
            result = self.config.to_dict()
            result.update(
                {
                    "_integration_type": "database",
                    "auto_connect": self.auto_connect,
                    "auto_create": self.auto_create,
                    "auto_migrate": self.auto_migrate,
                    "migrations_dir": self.migrations_dir,
                    "pool_size": self.pool_size,
                    "echo": self.echo,
                    "model_paths": list(self.model_paths),
                    "scan_dirs": list(self.scan_dirs),
                }
            )
            return result

        return {
            "_integration_type": "database",
            "enabled": True,
            "url": self.url or "sqlite:///db.sqlite3",
            "auto_connect": self.auto_connect,
            "auto_create": self.auto_create,
            "auto_migrate": self.auto_migrate,
            "migrations_dir": self.migrations_dir,
            "pool_size": self.pool_size,
            "echo": self.echo,
            "model_paths": list(self.model_paths),
            "scan_dirs": list(self.scan_dirs),
        }
