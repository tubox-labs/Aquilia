"""
AquilAuth - Authentication Manager

Central coordinator for all authentication operations.
Orchestrates identity verification, token issuance, and session management.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from .core import (
    ApiKeyCredential,
    AuthResult,
    Identity,
    IdentityStatus,
    TokenClaims,
)
from .faults import (
    AUTH_ACCOUNT_LOCKED,
    AUTH_ACCOUNT_SUSPENDED,
    AUTH_INVALID_CREDENTIALS,
    AUTH_KEY_EXPIRED,
    AUTH_KEY_REVOKED,
    AUTH_MFA_REQUIRED,
)
from .hashing import PasswordHasher
from .stores import MemoryCredentialStore, MemoryIdentityStore
from .tokens import TokenManager

# ============================================================================
# Rate Limiter
# ============================================================================


class RateLimiter:
    """Simple in-memory rate limiter for authentication attempts."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,  # 15 minutes
        lockout_duration: int = 3600,  # 1 hour
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_duration = lockout_duration
        self._attempts: dict[str, list[datetime]] = {}
        self._lockouts: dict[str, datetime] = {}

    def _cleanup_old_attempts(self, key: str) -> None:
        """Remove attempts outside the time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        if key in self._attempts:
            self._attempts[key] = [ts for ts in self._attempts[key] if ts > cutoff]

    def record_attempt(self, key: str) -> None:
        """Record failed authentication attempt."""
        self._cleanup_old_attempts(key)

        if key not in self._attempts:
            self._attempts[key] = []

        self._attempts[key].append(datetime.now(timezone.utc))

        # Check if should lock out
        if len(self._attempts[key]) >= self.max_attempts:
            self._lockouts[key] = datetime.now(timezone.utc) + timedelta(seconds=self.lockout_duration)

    def is_locked_out(self, key: str) -> bool:
        """Check if key is currently locked out."""
        # Edge case: max_attempts <= 0 means always locked
        if self.max_attempts <= 0:
            return True

        if key in self._lockouts:
            if datetime.now(timezone.utc) < self._lockouts[key]:
                return True
            else:
                # Lockout expired
                del self._lockouts[key]
                self._attempts[key] = []
        return False

    def get_remaining_attempts(self, key: str) -> int:
        """Get remaining attempts before lockout."""
        self._cleanup_old_attempts(key)
        current = len(self._attempts.get(key, []))
        return max(0, self.max_attempts - current)

    def reset(self, key: str) -> None:
        """Reset attempts for key (successful auth)."""
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)


# ============================================================================
# Auth Manager
# ============================================================================


class AuthManager:
    """
    Central authentication manager.

    Coordinates all authentication operations:
    - Password authentication
    - API key authentication
    - Token refresh
    - Session management
    - Rate limiting
    """

    def __init__(
        self,
        identity_store: MemoryIdentityStore,
        credential_store: MemoryCredentialStore,
        token_manager: TokenManager,
        password_hasher: PasswordHasher | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.identity_store = identity_store
        self.credential_store = credential_store
        self.token_manager = token_manager
        self.password_hasher = password_hasher or PasswordHasher()
        self.rate_limiter = rate_limiter or RateLimiter()

    def _get_runtime_session(self) -> Any | None:
        """
        Best-effort access to request-scoped session set by auth middleware.

        This keeps AuthManager decoupled from sessions when integrations are not enabled.
        """
        try:
            from .integration.runtime_context import get_auth_runtime_context

            runtime_ctx = get_auth_runtime_context()
            if runtime_ctx is None:
                return None
            return runtime_ctx.session
        except Exception:
            return None

    def _derive_session_id(self, explicit_session_id: str | None) -> str:
        """Resolve session ID with runtime session fallback."""
        if explicit_session_id:
            return explicit_session_id

        runtime_session = self._get_runtime_session()
        if runtime_session is not None and hasattr(runtime_session, "id"):
            return str(runtime_session.id)

        return f"sess_{secrets.token_urlsafe(32)}"

    def _bind_identity_to_runtime_session(self, identity: Identity, explicit_session_id: str | None) -> None:
        """
        Bind authenticated identity to the current request session if available.

        Binding is skipped when caller provides a different explicit session ID.
        """
        runtime_session = self._get_runtime_session()
        if runtime_session is None or not hasattr(runtime_session, "id"):
            return

        runtime_session_id = str(runtime_session.id)
        if explicit_session_id and explicit_session_id != runtime_session_id:
            return

        try:
            from .integration.aquila_sessions import bind_identity

            bind_identity(runtime_session, identity)
        except Exception:
            # Auth should continue even if optional session integration is unavailable.
            return

    async def authenticate_password(
        self,
        username: str,
        password: str,
        scopes: list[str] | None = None,
        session_id: str | None = None,
        client_metadata: dict[str, Any] | None = None,
    ) -> AuthResult:
        """
        Authenticate using username/password.

        Args:
            username: Username or email
            password: Plain text password
            scopes: Requested scopes
            session_id: Optional session ID to bind token to
            client_metadata: Client info (IP, user agent, etc.)

        Returns:
            AuthResult with tokens

        Raises:
            AUTH_INVALID_CREDENTIALS: Invalid username or password
            AUTH_ACCOUNT_LOCKED: Too many failed attempts
            AUTH_ACCOUNT_SUSPENDED: Account is suspended
            AUTH_MFA_REQUIRED: MFA verification needed
        """
        # Rate limiting check
        rate_key = f"auth:password:{username}"
        if self.rate_limiter.is_locked_out(rate_key):
            raise AUTH_ACCOUNT_LOCKED(
                username=username,
                retry_after=self.rate_limiter.lockout_duration,
            )

        # Get identity by username/email
        identity = await self.identity_store.get_by_attribute("email", username)
        if not identity:
            identity = await self.identity_store.get_by_attribute("username", username)

        if not identity:
            self.rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Check identity status
        if identity.status == IdentityStatus.SUSPENDED:
            raise AUTH_ACCOUNT_SUSPENDED(identity_id=identity.id)

        if identity.status == IdentityStatus.DELETED:
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Get password credential
        password_cred = await self.credential_store.get_password(identity.id)
        if not password_cred:
            self.rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Verify password
        if not self.password_hasher.verify(password_cred.password_hash, password):
            self.rate_limiter.record_attempt(rate_key)
            raise AUTH_INVALID_CREDENTIALS(username=username)

        # Check if password needs rehash (algorithm upgrade)
        if self.password_hasher.check_needs_rehash(password_cred.password_hash):
            # Rehash with current parameters
            new_hash = self.password_hasher.hash(password)
            password_cred.password_hash = new_hash
            await self.credential_store.save_password(password_cred)

        # Reset rate limit on successful auth
        self.rate_limiter.reset(rate_key)

        # Check for MFA requirement
        mfa_creds = await self.credential_store.get_mfa(identity.id)
        if mfa_creds:
            # MFA is enrolled - should go through MFA flow
            raise AUTH_MFA_REQUIRED(
                identity_id=identity.id,
                available_methods=[c.mfa_type for c in mfa_creds],
            )

        # Resolve session ID from explicit value or active runtime session.
        session_id = self._derive_session_id(session_id)

        # Get roles from identity
        roles = identity.get_attribute("roles", [])
        if isinstance(roles, (set, tuple)):
            roles = list(roles)
        elif not isinstance(roles, list):
            roles = [roles] if roles else []

        # Issue tokens
        access_token = await self.token_manager.issue_access_token(
            identity_id=identity.id,
            scopes=scopes or ["profile"],
            roles=roles,
            session_id=session_id,
            tenant_id=identity.tenant_id,
        )

        refresh_token = await self.token_manager.issue_refresh_token(
            identity_id=identity.id,
            scopes=scopes or ["profile"],
            session_id=session_id,
        )

        # Django-like ergonomics for Aquilia: when auth runs inside request scope,
        # the identity is bound to the active session automatically.
        self._bind_identity_to_runtime_session(identity, explicit_session_id=session_id)

        return AuthResult(
            identity=identity,
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            expires_in=self.token_manager.config.access_token_ttl,
            metadata={
                "auth_method": "password",
                "client_metadata": client_metadata,
            },
        )

    async def authenticate_api_key(
        self,
        api_key: str,
        required_scopes: list[str] | None = None,
    ) -> AuthResult:
        """
        Authenticate using API key.

        Args:
            api_key: API key string
            required_scopes: Scopes required for this request

        Returns:
            AuthResult with identity and scopes

        Raises:
            AUTH_INVALID_CREDENTIALS: Invalid API key
            AUTH_KEY_EXPIRED: API key has expired
            AUTH_KEY_REVOKED: API key has been revoked
            AUTH_INSUFFICIENT_SCOPE: Missing required scopes
        """
        # Extract prefix (first 8 chars)
        if len(api_key) < 8:
            raise AUTH_INVALID_CREDENTIALS()

        prefix = api_key[:8]

        # Get credential by prefix
        credential = await self.credential_store.get_api_key_by_prefix(prefix)
        if not credential:
            raise AUTH_INVALID_CREDENTIALS()

        # Verify hash (constant-time comparison via HMAC)
        if not ApiKeyCredential.verify_key(api_key, credential.key_hash):
            raise AUTH_INVALID_CREDENTIALS()

        # Check expiration
        if credential.expires_at and datetime.now(timezone.utc) > credential.expires_at:
            raise AUTH_KEY_EXPIRED(key_id=credential.key_id)

        # Check status
        if credential.status.value == "revoked":
            raise AUTH_KEY_REVOKED(key_id=credential.key_id)

        # Check scopes
        if required_scopes:
            from .faults import AUTHZ_INSUFFICIENT_SCOPE

            missing_scopes = set(required_scopes) - set(credential.scopes)
            if missing_scopes:
                raise AUTHZ_INSUFFICIENT_SCOPE(
                    required_scopes=required_scopes,
                    available_scopes=credential.scopes,
                )

        # Get identity
        identity = await self.identity_store.get(credential.identity_id)
        if not identity:
            raise AUTH_INVALID_CREDENTIALS()

        # Check identity status
        if identity.status != IdentityStatus.ACTIVE:
            raise AUTH_ACCOUNT_SUSPENDED(identity_id=identity.id)

        # Bind identity to active runtime session if one exists.
        self._bind_identity_to_runtime_session(identity, explicit_session_id=None)

        # API keys don't get refresh tokens
        return AuthResult(
            identity=identity,
            access_token=api_key,  # API key IS the token
            refresh_token=None,
            session_id=None,
            expires_in=(
                int((credential.expires_at - datetime.now(timezone.utc)).total_seconds())
                if credential.expires_at
                else None
            ),
            metadata={
                "auth_method": "api_key",
                "key_id": credential.key_id,
                "scopes": credential.scopes,
            },
        )

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            AUTH_TOKEN_INVALID: Invalid refresh token
            AUTH_TOKEN_EXPIRED: Refresh token expired
            AUTH_TOKEN_REVOKED: Refresh token revoked
        """
        return await self.token_manager.refresh_access_token(refresh_token)

    async def revoke_token(self, token: str, token_type: str = "refresh") -> None:
        """
        Revoke a token.

        Args:
            token: Token to revoke
            token_type: Type of token ("refresh" or "access")
        """
        _logger = logging.getLogger("aquilia.auth.manager")
        if token_type == "refresh":
            await self.token_manager.revoke_token(token)
        else:
            # For access tokens, extract JTI and revoke
            try:
                claims = await self.token_manager.validate_access_token(token)
                if jti := claims.get("jti"):
                    await self.token_manager.revoke_token(jti)
            except Exception as e:
                # Log the error instead of silently swallowing it
                _logger.warning("Failed to revoke access token (may already be invalid): %s", e)

    async def logout(
        self,
        identity_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        Logout user by revoking all tokens.

        Args:
            identity_id: Revoke all tokens for this identity
            session_id: Revoke all tokens for this session
        """
        if identity_id:
            await self.token_manager.revoke_tokens_by_identity(identity_id)

        resolved_session_id = session_id
        runtime_session = self._get_runtime_session()
        if resolved_session_id is None and runtime_session is not None and hasattr(runtime_session, "id"):
            resolved_session_id = str(runtime_session.id)

        if resolved_session_id:
            await self.token_manager.revoke_tokens_by_session(resolved_session_id)

        if runtime_session is not None and hasattr(runtime_session, "clear_authentication"):
            try:
                runtime_session.clear_authentication()
            except Exception:
                pass

    async def verify_token(self, access_token: str) -> TokenClaims:
        """
        Verify and decode access token.

        Args:
            access_token: JWT access token

        Returns:
            Token claims

        Raises:
            AUTH_TOKEN_INVALID: Invalid token format
            AUTH_TOKEN_EXPIRED: Token expired
            AUTH_TOKEN_REVOKED: Token revoked
        """
        claims = await self.token_manager.validate_access_token(access_token)

        return TokenClaims(
            iss=claims["iss"],
            sub=claims["sub"],
            aud=claims["aud"],
            exp=claims["exp"],
            iat=claims["iat"],
            nbf=claims.get("nbf", claims["iat"]),
            jti=claims.get("jti", ""),
            scopes=claims.get("scopes", []),
            roles=claims.get("roles", []),
            sid=claims.get("sid"),
            tenant_id=claims.get("tenant_id"),
        )

    async def get_identity_from_token(self, access_token: str) -> Identity | None:
        """
        Extract identity from access token.

        Args:
            access_token: JWT access token

        Returns:
            Identity if token valid, None otherwise
        """
        try:
            claims = await self.verify_token(access_token)
            return await self.identity_store.get(claims.sub)
        except Exception:
            return None
