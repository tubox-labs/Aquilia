"""
Authentication backend for JWT Bearer tokens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aquilia.auth.core import Authentication, Identity, IdentityType

if TYPE_CHECKING:
    from aquilia.auth.core import IdentityStore
    from aquilia.auth.tokens import TokenManager


class TokenBackend:
    """
    Authentication backend for JWT Bearer tokens.

    Validates the token signature, claims (``iss``, ``aud``, ``exp``,
    ``nbf``, ``jti`` revocation), then resolves the subject identity.

    Args:
        token_manager: ``TokenManager`` instance used for validation.
        identity_store: Store used to resolve ``Identity`` by subject claim.
    """

    def __init__(
        self,
        token_manager: TokenManager,
        identity_store: IdentityStore,
    ) -> None:
        self._token_manager = token_manager
        self._identity_store = identity_store

    # ── AuthBackend protocol ─────────────────────────────────────────────────

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Accept when a ``"token"`` key is present."""
        return "token" in credentials

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | Authentication | None:
        """
        Validate JWT access token and return the resolved ``Identity``.

        Args:
            credentials: Must contain ``"token"`` key with the raw JWT string.

        Returns:
            Authenticated ``Identity`` when the token is valid. The verified
            claims are attached to ``request.state["token_claims"]`` by the
            middleware via the returned :class:`Authentication` wrapper.

        Raises:
            ``AUTH_TOKEN_INVALID``: Malformed or signature mismatch.
            ``AUTH_TOKEN_EXPIRED``: Token has expired.
            ``AUTH_TOKEN_REVOKED``: Token was explicitly revoked.
        """
        if not self.accepts(credentials):
            return None

        token: str = credentials["token"]
        claims = await self._token_manager.validate_access_token(token)
        identity_id: str = claims["sub"]
        identity = await self._identity_store.get(identity_id)
        if identity is None:
            return None
        return Authentication(identity=identity, claims=claims)


class StatelessTokenBackend:
    """
    Verify Bearer JWTs and build the principal from verified claims.

    Unlike :class:`TokenBackend` there is **no identity-store lookup per
    request**: the signature and claims are verified, and the ``Identity`` is
    materialized from the claims themselves (``sub`` → id, ``roles`` /
    ``scopes`` → attributes). This is the passport-jwt default posture —
    revocation is bounded by the token TTL and by explicit ``jti``
    revocation checked during validation.

    Args:
        token_manager: ``TokenManager`` used for cryptographic validation.
        principal_builder: Optional ``callable(identity, claims) ->
            principal`` (the same signature as ``Auth.principal_factory``) —
            when set, an application-defined principal rides along on the
            :class:`Authentication` result.
    """

    def __init__(
        self,
        token_manager: TokenManager,
        principal_builder: Any | None = None,
    ) -> None:
        self._token_manager = token_manager
        self._principal_builder = principal_builder

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Accept when a ``"token"`` key is present."""
        return "token" in credentials

    async def authenticate(self, credentials: dict[str, Any]) -> Authentication | None:
        """Verify the token and build the principal from verified claims."""
        if not self.accepts(credentials):
            return None

        token: str = credentials["token"]
        claims = await self._token_manager.validate_access_token(token)

        attributes: dict[str, Any] = {}
        roles = claims.get("roles") or []
        scopes = claims.get("scopes") or []
        if roles:
            attributes["roles"] = roles
        if scopes:
            attributes["scopes"] = scopes

        identity = Identity(
            id=claims["sub"],
            type=IdentityType.USER,
            attributes=attributes,
            tenant_id=claims.get("tenant_id"),
        )

        principal = None
        if self._principal_builder is not None:
            principal = self._principal_builder(identity, claims)

        return Authentication(identity=identity, claims=claims, principal=principal)
