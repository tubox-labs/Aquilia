"""
Aquilia Typing — Auth & Session Protocols.

Defines structural protocols (``typing.Protocol``) and type aliases for the auth
and session subsystems.  These types replace bare ``Any`` annotations throughout
``aquilia.auth`` and ``aquilia.sessions`` and allow static type checkers
(mypy / pyright) to verify correctness without creating circular imports.

Protocols are ``runtime_checkable`` so ``isinstance()`` guards work in
middleware and guards without importing concrete classes.

Example::

    from aquilia.typing.auth import IdentityLike, PrincipalLike

    def process(identity: IdentityLike) -> str:
        return identity.id
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeAlias, runtime_checkable

# ---------------------------------------------------------------------------
# Scalar type aliases
# ---------------------------------------------------------------------------

IdentityID: TypeAlias = str
"""Opaque string identifier for an ``Identity``."""

TenantID: TypeAlias = str | None
"""Optional tenant identifier for multi-tenant deployments."""

RoleName: TypeAlias = str
"""A role string, e.g. ``"admin"`` or ``"moderator"``."""

ScopeName: TypeAlias = str
"""An OAuth 2.0 scope string, e.g. ``"orders:read"``."""

RoleSet: TypeAlias = frozenset[str]
"""Immutable set of role names attached to an identity or token."""

ScopeSet: TypeAlias = frozenset[str]
"""Immutable set of OAuth scope strings attached to a token."""


# ---------------------------------------------------------------------------
# Auth Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class IdentityLike(Protocol):
    """Structural protocol for anything that acts like an authenticated identity.

    Concrete implementations: ``aquilia.auth.core.Identity``.
    Used by guards, decorators, and middleware so they can accept any
    compliant identity object without a direct import of the auth package.

    Example::

        from aquilia.typing.auth import IdentityLike

        def require_role(identity: IdentityLike, role: str) -> bool:
            return identity.has_role(role)
    """

    @property
    def id(self) -> str:
        """Stable unique identifier. Never changes after creation."""
        ...

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Retrieve an attribute from the identity's attribute map."""
        ...

    def has_role(self, role: str) -> bool:
        """Return ``True`` if this identity holds the given role."""
        ...

    def has_scope(self, scope: str) -> bool:
        """Return ``True`` if this identity holds the given OAuth scope."""
        ...

    def is_active(self) -> bool:
        """Return ``True`` when the identity is in the ACTIVE status."""
        ...


@runtime_checkable
class PrincipalLike(Protocol):
    """Structural protocol for a session principal (who owns a session).

    Concrete implementations: ``aquilia.sessions.core.SessionPrincipal``,
    ``aquilia.auth.integration.aquila_sessions.AuthPrincipal``.

    Example::

        from aquilia.typing.auth import PrincipalLike

        def log_access(principal: PrincipalLike) -> None:
            print(f"{principal.kind}:{principal.id} accessed resource")
    """

    @property
    def kind(self) -> str:
        """Principal kind: ``"user"``, ``"service"``, ``"device"``, or ``"anonymous"``."""
        ...

    @property
    def id(self) -> str:
        """Opaque principal identifier."""
        ...

    @property
    def attributes(self) -> dict[str, Any]:
        """Extra attributes stored with the principal."""
        ...

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Look up a principal attribute by key."""
        ...


@runtime_checkable
class TokenClaimsLike(Protocol):
    """Structural protocol for JWT-like token claims.

    Concrete implementation: ``aquilia.auth.core.TokenClaims``.

    Example::

        from aquilia.typing.auth import TokenClaimsLike

        def check_access(claims: TokenClaimsLike, scope: str) -> bool:
            return not claims.is_expired() and claims.has_scope(scope)
    """

    @property
    def sub(self) -> str:
        """Subject — the identity ID this token belongs to."""
        ...

    @property
    def scopes(self) -> list[str]:
        """OAuth scopes granted to this token."""
        ...

    @property
    def roles(self) -> list[str]:
        """Roles embedded in the token at issuance."""
        ...

    @property
    def exp(self) -> int:
        """Unix timestamp at which the token expires."""
        ...

    def is_expired(self) -> bool:
        """Return ``True`` if the token has passed its ``exp`` claim."""
        ...

    def has_scope(self, scope: str) -> bool:
        """Return ``True`` if the token holds the given OAuth scope."""
        ...


@runtime_checkable
class SessionLike(Protocol):
    """Structural protocol for a session object.

    Concrete implementation: ``aquilia.sessions.core.Session``.
    Allows auth middleware and guards to reference sessions without
    creating circular imports with the sessions package.

    Example::

        from aquilia.typing.auth import SessionLike

        def is_user_authenticated(session: SessionLike) -> bool:
            return session.is_authenticated
    """

    @property
    def is_authenticated(self) -> bool:
        """``True`` when the session has a bound, authenticated principal."""
        ...

    @property
    def principal(self) -> PrincipalLike | None:
        """The principal bound to this session, or ``None`` for anonymous sessions."""
        ...

    @property
    def data(self) -> dict[str, Any]:
        """Mutable session data dictionary."""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the session data dictionary."""
        ...


# ---------------------------------------------------------------------------
# Guard callable types
# ---------------------------------------------------------------------------

FlowContext: TypeAlias = dict[str, Any]
"""Mutable flow context dict passed through guard chains."""

GuardCallable: TypeAlias = Callable[[FlowContext], Awaitable[FlowContext]]
"""Callable signature expected by Aquilia Flow guards."""


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Scalar aliases
    "IdentityID",
    "TenantID",
    "RoleName",
    "ScopeName",
    "RoleSet",
    "ScopeSet",
    # Protocols
    "IdentityLike",
    "PrincipalLike",
    "TokenClaimsLike",
    "SessionLike",
    # Guard types
    "FlowContext",
    "GuardCallable",
]
