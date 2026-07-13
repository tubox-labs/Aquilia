"""
Authentication backend for username + password credentials.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core import CredentialStore, Identity, IdentityStore
    from ..hashing import PasswordHasher


class PasswordBackend:
    """
    Authentication backend for username + password credentials.

    Performs Argon2id (or configured algorithm) hash verification, handles
    auto-rehash on algorithm upgrade, checks identity status, and signals
    when MFA is required.

    The backend does **not** auto-provision accounts.  If the identity does
    not exist in ``identity_store`` the credentials are rejected.

    Args:
        identity_store:  Store used to resolve ``Identity`` by login attribute.
        credential_store: Store used to fetch the ``PasswordCredential``.
        password_hasher:  Configured ``PasswordHasher`` (Argon2id by default).
        rate_limiter:    Optional ``RateLimiter``.  Defaults to no rate
                         limiting when ``None`` is supplied.
        login_attributes: Ordered list of identity attributes tried when
                          resolving the ``username`` to an ``Identity``.
                          Defaults to ``("email", "username", "login")``.
    """

    def __init__(
        self,
        identity_store: IdentityStore,
        credential_store: CredentialStore,
        password_hasher: PasswordHasher,
        rate_limiter: Any | None = None,
        login_attributes: tuple[str, ...] = ("email", "username", "login"),
    ) -> None:
        self._identity_store = identity_store
        self._credential_store = credential_store
        self._hasher = password_hasher
        self._rate_limiter = rate_limiter
        self._login_attributes = login_attributes

    # ── AuthBackend protocol ─────────────────────────────────────────────────

    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Accept when ``username`` and ``password`` are both present."""
        return "username" in credentials and "password" in credentials

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """
        Verify username/password and return the resolved ``Identity``.

        Args:
            credentials: Must contain ``"username"`` and ``"password"`` keys.

        Returns:
            Authenticated ``Identity``.

        Raises:
            ``AUTH_INVALID_CREDENTIALS``: Wrong password or unknown username.
            ``AUTH_ACCOUNT_SUSPENDED``: Identity is suspended.
            ``AUTH_ACCOUNT_LOCKED``:    Too many failed attempts.
            ``AUTH_MFA_REQUIRED``:      MFA enrolled; token step required.
        """
        if not self.accepts(credentials):
            return None

        from ..core import IdentityStatus
        from ..faults import (
            AUTH_ACCOUNT_LOCKED,
            AUTH_ACCOUNT_SUSPENDED,
            AUTH_INVALID_CREDENTIALS,
            AUTH_MFA_REQUIRED,
        )

        username: str = (
            credentials["username"].strip().lower()
            if "@" in credentials["username"]
            else credentials["username"].strip()
        )
        password: str = credentials["password"]
        rate_key = f"auth:password:{username}"

        # Rate limit check
        if self._rate_limiter and self._rate_limiter.is_locked_out(rate_key):
            raise AUTH_ACCOUNT_LOCKED()

        # Resolve identity
        identity = await self._resolve_identity(username)
        if identity is None:
            if self._rate_limiter:
                self._rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Status check
        if identity.status == IdentityStatus.SUSPENDED:
            raise AUTH_ACCOUNT_SUSPENDED(identity_id=identity.id)
        if identity.status == IdentityStatus.DELETED:
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Password credential
        cred = await self._credential_store.get_password(identity.id)
        if cred is None:
            if self._rate_limiter:
                self._rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Hash verification
        if not self._hasher.verify(cred.password_hash, password):
            if self._rate_limiter:
                self._rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Auto-rehash on algorithm upgrade
        if self._hasher.check_needs_rehash(cred.password_hash):
            cred.password_hash = self._hasher.hash(password)
            await self._credential_store.update_password(cred)

        # Clear rate limit on success
        if self._rate_limiter:
            self._rate_limiter.reset(rate_key)

        # MFA check
        mfa_creds = await self._credential_store.get_mfa(identity.id)
        if mfa_creds:
            raise AUTH_MFA_REQUIRED(
                identity_id=identity.id,
                available_methods=[c.mfa_type for c in mfa_creds],
            )

        return identity

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _resolve_identity(self, identifier: str) -> Identity | None:
        """Try direct ID then each configured login attribute."""
        direct = await self._identity_store.get(identifier)
        if direct is not None:
            return direct
        for attr in self._login_attributes:
            found = await self._identity_store.get_by_attribute(attr, identifier)
            if found is not None:
                return found
        return None
