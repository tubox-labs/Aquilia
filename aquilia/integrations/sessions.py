"""
SessionIntegration — typed session configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SessionIntegration:
    """
    Typed session integration config.

    Example::

        SessionIntegration(
            policy=SessionPolicy.for_web_users(),
            store=MemoryStore.with_capacity(50000),
        )
    """

    _integration_type: str = field(default="sessions", init=False, repr=False)

    enabled: bool = True
    policy: Optional[Any] = None
    store: Optional[Any] = None
    transport: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        from aquilia.sessions import (
            SessionPolicy, MemoryStore, CookieTransport,
        )

        policy = self.policy
        if policy is None:
            policy = SessionPolicy.for_web_users().with_smart_defaults()

        store = self.store
        if store is None:
            store = MemoryStore.development_focused()

        transport = self.transport
        if transport is None:
            if hasattr(policy, "transport") and policy.transport:
                transport = CookieTransport.from_policy(policy.transport)
            else:
                transport = CookieTransport.with_aquilia_defaults()

        return {
            "_integration_type": "sessions",
            "enabled": self.enabled,
            "policy": policy,
            "store": store,
            "transport": transport,
            "aquilia_syntax_version": "2.0",
        }
