"""SocketPermissionMiddleware — per-event role and scope requirements.

Authorization, as distinct from the authentication in :mod:`.auth`: by the time
this runs the caller is known, and the question is whether *this* identity may
send *this* event.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope

    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.authorization")


class SocketPermissionMiddleware(SocketMiddleware):
    """
    Requires roles or scopes per event name.

    Registered at **priority 18**: after auth (15) has established identity,
    before application middleware (50+).

    Rules map an event name to the roles/scopes it needs. Events with no rule are
    allowed by default — an allow-by-default posture is chosen deliberately
    because the alternative silently breaks every event the moment this
    middleware is added, which trains people to remove it. Set
    ``default_deny=True`` when you want the stricter posture and are prepared to
    enumerate every event.

    Args:
        require_roles: ``{event_name: [role, ...]}``. Identity must have at least
            one listed role (``mode="any"``) or all of them (``mode="all"``).
        require_scopes: ``{event_name: [scope, ...]}``, same matching rule.
        mode: ``"any"`` (default) or ``"all"``.
        default_deny: Reject events that have no rule at all.
        exempt_events: Events always allowed, even under ``default_deny``.

    Example::

        SocketPermissionMiddleware(
            require_roles={"room.moderate": ["moderator", "admin"]},
            require_scopes={"metrics.subscribe": ["metrics:read"]},
        )
    """

    def __init__(
        self,
        *,
        require_roles: dict[str, list[str]] | None = None,
        require_scopes: dict[str, list[str]] | None = None,
        mode: str = "any",
        default_deny: bool = False,
        exempt_events: list[str] | None = None,
    ):
        if mode not in ("any", "all"):
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                "socket.permissions.mode",
                f"expected 'any' or 'all', got {mode!r}",
            )

        self.require_roles = require_roles or {}
        self.require_scopes = require_scopes or {}
        self.mode = mode
        self.default_deny = default_deny
        self.exempt_events = set(exempt_events or ())

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        from aquilia.sockets.faults import WS_AUTH_REQUIRED, WS_FORBIDDEN

        event = envelope.event

        if event in self.exempt_events:
            return await next_handler(envelope, ctx)

        needed_roles = self.require_roles.get(event)
        needed_scopes = self.require_scopes.get(event)

        if needed_roles is None and needed_scopes is None:
            if self.default_deny:
                raise WS_FORBIDDEN(f"event '{event}' has no permission rule and default_deny is set")
            return await next_handler(envelope, ctx)

        identity = ctx.identity
        if identity is None:
            raise WS_AUTH_REQUIRED()

        if needed_roles and not self._satisfies(needed_roles, identity.has_role):
            raise WS_FORBIDDEN(f"event '{event}' requires {self.mode} of roles {needed_roles}")

        if needed_scopes and not self._satisfies(needed_scopes, identity.has_scope):
            raise WS_FORBIDDEN(f"event '{event}' requires {self.mode} of scopes {needed_scopes}")

        return await next_handler(envelope, ctx)

    def _satisfies(self, required: list[str], check: Callable[[str], bool]) -> bool:
        if self.mode == "all":
            return all(check(item) for item in required)
        return any(check(item) for item in required)


__all__ = ["SocketPermissionMiddleware"]
