"""
Authentication backend for API Keys.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core import CredentialStore, Identity, IdentityStore


class ApiKeyBackend:
    """
    Authentication backend for opaque API keys.

    Looks up the key by its ``HMAC-SHA256`` hash (``O(1)`` lookup),
    verifies status and expiration, then resolves the bound identity.

    Args:
        credential_store: Store that provides ``get_api_key_by_hash`` lookup.
        identity_store:   Store used to resolve the bound ``Identity``.
    """

    def __init__(
        self,
        credential_store: CredentialStore,
        identity_store: IdentityStore,
    ) -> None:
        self._credential_store = credential_store
        self._identity_store = identity_store

    # ── AuthBackend protocol ─────────────────────────────────────────────────

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Accept when an ``"api_key"`` key is present."""
        return "api_key" in credentials

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """
        Validate an API key and return the bound ``Identity``.

        Args:
            credentials: Must contain ``"api_key"`` with the raw key string.

        Returns:
            Bound ``Identity`` when the key is valid and not revoked.

        Raises:
            ``AUTH_INVALID_CREDENTIALS``: Key not found or hash mismatch.
            ``AUTH_KEY_EXPIRED``:  Key has passed its expiration date.
            ``AUTH_KEY_REVOKED``:  Key was explicitly revoked.
            ``AUTHZ_INSUFFICIENT_SCOPE``: Required scopes are absent.
        """
        if not self.accepts(credentials):
            return None

        from datetime import datetime, timezone

        from ..core import ApiKeyCredential, CredentialStatus, IdentityStatus
        from ..faults import (
            AUTH_ACCOUNT_SUSPENDED,
            AUTH_INVALID_CREDENTIALS,
            AUTH_KEY_EXPIRED,
            AUTH_KEY_REVOKED,
        )

        api_key: str = credentials["api_key"]
        if len(api_key) < 8:
            raise AUTH_INVALID_CREDENTIALS()

        key_hash = ApiKeyCredential.hash_key(api_key)
        cred: ApiKeyCredential | None = await self._credential_store.get_api_key_by_hash(key_hash)
        if cred is None:
            raise AUTH_INVALID_CREDENTIALS()

        if not ApiKeyCredential.verify_key(api_key, cred.key_hash):
            raise AUTH_INVALID_CREDENTIALS()

        if cred.expires_at and datetime.now(timezone.utc) > cred.expires_at:
            raise AUTH_KEY_EXPIRED(key_id=cred.key_id)

        if cred.status in (CredentialStatus.REVOKED, CredentialStatus.SUSPENDED, CredentialStatus.EXPIRED):
            raise AUTH_KEY_REVOKED(key_id=cred.key_id)

        # Scope gate (optional — caller passes required_scopes via credentials)
        required_scopes: list[str] = credentials.get("required_scopes", [])
        if required_scopes:
            from ..faults import AUTHZ_INSUFFICIENT_SCOPE

            missing = set(required_scopes) - set(cred.scopes)
            if missing:
                raise AUTHZ_INSUFFICIENT_SCOPE(required_scopes=required_scopes)

        identity = await self._identity_store.get(cred.identity_id)
        if identity is None:
            raise AUTH_INVALID_CREDENTIALS()

        if identity.status != IdentityStatus.ACTIVE:
            raise AUTH_ACCOUNT_SUSPENDED(identity_id=identity.id)

        return identity
