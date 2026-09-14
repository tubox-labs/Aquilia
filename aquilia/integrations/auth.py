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
            access_token_ttl_seconds=1800,
            stateless=True,
        )
    """

    _integration_type: str = field(default="auth", init=False, repr=False)

    enabled: bool = True
    store_type: str = "memory"
    secret_key: str | None = None
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: str | list[str] = field(default_factory=lambda: ["api"])
    #: Access token lifetime in seconds (canonical unit). ``None`` derives
    #: from the minute alias when set, else the framework default.
    access_token_ttl_seconds: int | None = None
    #: Refresh token lifetime in seconds (canonical unit). ``None`` derives
    #: from the day alias when set, else the framework default.
    refresh_token_ttl_seconds: int | None = None
    #: Legacy minute/day aliases.
    access_token_ttl_minutes: int | None = 60
    refresh_token_ttl_days: int | None = 30
    require_auth_by_default: bool = False
    backends: list[str] = field(default_factory=lambda: ["token", "session"])
    #: Guards applied to every route (NestJS ``APP_GUARD`` equivalent).
    global_guards: list = field(default_factory=list)
    #: Dotted path ``(identity, claims) -> principal`` for app principals.
    principal_factory: str | None = None
    #: Verify Bearer tokens without a per-request identity lookup.
    stateless: bool = False
    #: One generic 401 for every token failure (anti-enumeration).
    collapse_token_errors: bool = False
    #: Explicit store overrides: ready-made objects or ``{"type": ...}`` specs.
    identity_store: Any = None
    credential_store: Any = None
    token_store: Any = None
    clock_skew_seconds: int = 0

    def to_dict(self) -> dict[str, Any]:
        tokens: dict[str, Any] = {
            "secret_key": self.secret_key,
            "algorithm": self.algorithm,
            "issuer": self.issuer,
            "audience": self.audience,
            "stateless": self.stateless,
            "collapse_token_errors": self.collapse_token_errors,
            "clock_skew_seconds": self.clock_skew_seconds,
        }
        # Emit only what was explicitly set: the canonical seconds fields
        # when present, else the aliases — never both (the alias must not be
        # masked by a default).
        if self.access_token_ttl_seconds is not None:
            tokens["access_token_ttl_seconds"] = self.access_token_ttl_seconds
        elif self.access_token_ttl_minutes is not None:
            tokens["access_token_ttl_minutes"] = self.access_token_ttl_minutes
        if self.refresh_token_ttl_seconds is not None:
            tokens["refresh_token_ttl_seconds"] = self.refresh_token_ttl_seconds
        elif self.refresh_token_ttl_days is not None:
            tokens["refresh_token_ttl_days"] = self.refresh_token_ttl_days
        return {
            "_integration_type": "auth",
            "enabled": self.enabled,
            "store": {"type": self.store_type},
            "tokens": tokens,
            "security": {
                "require_auth_by_default": self.require_auth_by_default,
                "backends": self.backends,
                "global_guards": self.global_guards,
                "principal_factory": self.principal_factory,
            },
            "identity_store": self.identity_store,
            "credential_store": self.credential_store,
            "token_store": self.token_store,
        }
