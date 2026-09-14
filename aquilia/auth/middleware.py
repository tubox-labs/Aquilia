"""
AquilAuth — HTTP Authentication Middleware

Resolves identity from pluggable strategies on every request and stores the
result on the canonical :class:`~aquilia.auth.state.AuthState`
(``ctx.auth_state`` / ``request.state["auth_state"]``) plus the legacy
mirrors (``ctx.identity`` / ``request.state["identity"]``).

This class is the application-facing spelling of the same pipeline the
server mounts as :class:`~aquilia.auth.integration.middleware.AquilAuthMiddleware`
— one implementation, two constructors. See that class for the phase-by-phase
architecture (optional authentication → principal → canonical state →
enforcement honoring ``@Public()`` → handler → session commit).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aquilia.auth.integration.middleware import AquilAuthMiddleware

if TYPE_CHECKING:
    from aquilia.auth.backends.base import AuthBackend
    from aquilia.auth.manager import AuthManager
    from aquilia.sessions import SessionEngine

_log = logging.getLogger("aquilia.auth.middleware")


class AuthMiddleware(AquilAuthMiddleware):
    """
    HTTP Middleware that authenticates incoming requests using strategies.

    Resolves identity from pluggable backends on every request.
    Stores the resolved identity on ``ctx.identity`` and
    ``request.state["identity"]`` (and the full canonical state on
    ``request.state["auth_state"]``).

    Args:
        auth_manager:    ``AuthManager`` instance for backend initialization.
        session_engine:  Optional ``SessionEngine``. Required when the
                         ``session`` strategy is configured.
        require_auth:    When ``True``, reject unauthenticated requests with
                         a 401 (routes marked ``@Public()`` are exempt).
                         Defaults to ``False`` (opt-in per route/guard).
        backends:        Ordered list of active backends (strategy names,
                         dotted paths, classes, or instances). Defaults to
                         ``token`` + ``session``.
        principal_factory: Optional ``callable(identity, claims) -> principal``.
        logger:          Optional logger.  Defaults to
                         ``aquilia.auth.middleware``.
    """

    def __init__(
        self,
        auth_manager: AuthManager,
        session_engine: SessionEngine | None = None,
        *,
        require_auth: bool = False,
        backends: list[AuthBackend] | None = None,
        principal_factory: Any = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            session_engine=session_engine,
            auth_manager=auth_manager,
            require_auth=require_auth,
            backends=backends,
            logger=logger,
            principal_factory=principal_factory,
        )


__all__ = ["AuthMiddleware"]
