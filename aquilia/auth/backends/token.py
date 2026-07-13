"""
Authentication backend for JWT Bearer tokens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core import Identity, IdentityStore
    from ..tokens import TokenManager


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

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """
        Validate JWT access token and return the resolved ``Identity``.

        Args:
            credentials: Must contain ``"token"`` key with the raw JWT string.

        Returns:
            Authenticated ``Identity`` when the token is valid.

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
        return await self._identity_store.get(identity_id)
