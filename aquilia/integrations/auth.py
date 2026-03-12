"""
AuthIntegration — typed auth configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuthIntegration:
    """
    Typed authentication integration config.

    Example::

        AuthIntegration(
            enabled=True,
            store_type="memory",
            secret_key="super-secret",
            access_token_ttl_minutes=30,
        )
    """

    _integration_type: str = field(default="auth", init=False, repr=False)

    enabled: bool = True
    store_type: str = "memory"
    secret_key: str | None = None
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: str = "aquilia-app"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    require_auth_by_default: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "auth",
            "enabled": self.enabled,
            "store": {"type": self.store_type},
            "tokens": {
                "secret_key": self.secret_key,
                "algorithm": self.algorithm,
                "issuer": self.issuer,
                "audience": self.audience,
                "access_token_ttl_minutes": self.access_token_ttl_minutes,
                "refresh_token_ttl_days": self.refresh_token_ttl_days,
            },
            "security": {
                "require_auth_by_default": self.require_auth_by_default,
            },
        }
