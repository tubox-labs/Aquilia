"""
AquilAuth — Canonical Request Auth State

Historically the per-request authentication result was mirrored into six
places (``request.state["identity"]``, ``request.state["authenticated"]``,
``ctx.identity``, the request-scoped DI registration, the
``AuthRuntimeContext`` contextvar, and the session bridge), each written by
hand inside the middleware — any consumer reading a different mirror could
observe a different truth during partial failures, and "is this request
authenticated?" had three different answers.

:class:`AuthState` is the **single canonical representation**. The auth
middleware creates exactly one per request and hangs it on
``request.state["auth_state"]`` / ``ctx.auth_state``. Everything else is a
derived compatibility view:

* ``request.state["identity"]`` / ``ctx.identity`` — ``auth_state.identity``
* ``request.state["authenticated"]`` — ``auth_state.authenticated``
* ``request.state["principal"]`` — ``auth_state.principal``
* ``request.state["token_claims"]`` — ``auth_state.claims``
* the request-scoped ``Identity`` DI registration

Resolution phase vs enforcement phase
-------------------------------------

The middleware **never** raises during authentication resolution: a failed
credential is recorded on ``auth_state.error`` and the request stays
anonymous. Enforcement happens later — the global ``require_auth`` flag
(honoring ``@Public()``) or a guard — and re-raises the recorded error so a
protected route with an invalid token still yields a precise 401, while a
public route with the same token simply proceeds anonymously.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.faults import Fault


@dataclass
class AuthState:
    """
    The canonical per-request authentication state.

    Attributes:
        identity:   Framework ``Identity`` (or ``None`` for anonymous).
        principal:  Application-defined principal when a ``principal_factory``
                    produced one; otherwise ``None`` (consumers fall back to
                    ``identity``).
        claims:     Verified token claims when a token strategy authenticated.
        strategy:   Name/path of the strategy that succeeded.
        session:    The resolved framework session, when sessions are mounted.
        error:      The fault raised during resolution, if any. Carried (not
                    raised) so public routes can degrade to anonymous while
                    protected routes can still surface the precise failure.
    """

    identity: Identity | None = None
    principal: Any = None
    claims: dict[str, Any] | None = None
    strategy: str | None = None
    session: Any = None
    error: Fault | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def authenticated(self) -> bool:
        """One answer to "is this request authenticated?"."""
        return self.identity is not None

    @property
    def user(self) -> Any:
        """The principal: app-defined principal when present, else Identity."""
        return self.principal if self.principal is not None else self.identity

    @property
    def user_id(self) -> str | None:
        ident = self.identity
        return getattr(ident, "id", None)

    def to_dict(self) -> dict[str, Any]:
        """Diagnostic serialization (never includes claim payloads)."""
        return {
            "authenticated": self.authenticated,
            "identity_id": self.user_id,
            "strategy": self.strategy,
            "has_principal": self.principal is not None,
            "has_claims": self.claims is not None,
            "error_code": getattr(self.error, "code", None),
        }


def apply_auth_state_views(state: AuthState, request: Any, ctx: Any) -> None:
    """
    Propagate the canonical state onto the legacy mirror locations.

    The single write point for every compatibility view — the mirrors can no
    longer drift because they are all assigned here, from ``state``, at once.
    """
    if request is not None:
        try:
            request.state["auth_state"] = state
            request.state["identity"] = state.identity
            request.state["authenticated"] = state.authenticated
            request.state["principal"] = state.principal
            if state.claims is not None:
                request.state["token_claims"] = state.claims
        except Exception:
            pass
    if ctx is not None:
        try:
            ctx.auth_state = state
            ctx.identity = state.identity
        except Exception:
            pass


def route_is_public(request: Any) -> bool:
    """
    Whether the matched route is marked public (``@Public()``).

    Route metadata is stashed on ``request.state["route_metadata"]`` by the
    ASGI adapter *before* middleware runs, so both middleware and guards can
    consult it. Accepts a :class:`~aquilia.controller.metadata.RouteMetadata`
    object, a plain dict (``{"public": True}`` or carrying a
    ``"_raw_metadata"`` dict), or ``None``.

    Deliberately strict comparisons (``is True``) so that test doubles whose
    attribute access auto-generates truthy values (``unittest.mock.Mock``)
    cannot silently mark routes public and disable enforcement.
    Falls back to the clearance system's ``@exempt`` marker.
    """
    route_metadata = None
    if request is not None:
        state = getattr(request, "state", None)
        if state is not None:
            route_metadata = state.get("route_metadata") if hasattr(state, "get") else None

    if route_metadata is None:
        return False

    # Plain-dict spelling.
    if isinstance(route_metadata, dict):
        raw = route_metadata.get("_raw_metadata")
        if isinstance(raw, dict) and raw.get("public") is True:
            return True
        return route_metadata.get("public") is True

    # RouteMetadata object spelling.
    raw = getattr(route_metadata, "_raw_metadata", None)
    if isinstance(raw, dict) and raw.get("public") is True:
        return True
    if getattr(route_metadata, "public", False) is True:
        return True

    # Clearance @exempt compatibility — a method clearance of PUBLIC.
    clearance = getattr(route_metadata, "clearance", None)
    if clearance is not None:
        level = getattr(clearance, "level", None)
        level_name = getattr(level, "name", None)
        if level_name == "PUBLIC":
            return True
    return False


__all__ = [
    "AuthState",
    "apply_auth_state_views",
    "route_is_public",
]
