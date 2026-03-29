"""
AquilAuth - Authentication Manager

Central coordinator for all authentication operations.
Orchestrates identity verification, token issuance, and session management.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from aquilia.faults.domains import ConfigInvalidFault, ConflictFault, TooManyRequestsFault
from aquilia.sessions import SessionScope
from aquilia.typing import JSONObject

from .core import (
    ApiKeyCredential,
    AuthResult,
    CredentialStore,
    Identity,
    IdentityStatus,
    IdentityStore,
    IdentityType,
    PasswordCredential,
    TokenClaims,
)
from .faults import (
    AUTH_ACCOUNT_LOCKED,
    AUTH_ACCOUNT_SUSPENDED,
    AUTH_INVALID_CREDENTIALS,
    AUTH_KEY_EXPIRED,
    AUTH_KEY_REVOKED,
    AUTH_MFA_REQUIRED,
    AUTH_REQUIRED,
    AUTH_SESSION_REQUIRED,
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


@dataclass(frozen=True)
class SignInProvisionPolicy:
    """
    Provisioning policy for sign_in bootstrap behavior.

    Secure defaults:
    - Bootstrap is only used when a trusted Identity seed is provided.
    - Missing identity and password credential are backfilled once.
    - Existing credentials are never overwritten unless explicitly requested.
    """

    enable_identity_seed: bool = True
    create_identity_if_missing: bool = True
    backfill_password_credential: bool = True
    overwrite_password_credential: bool = False
    allow_username_bootstrap: bool = True

    @classmethod
    def secure_defaults(cls, env: str | None = None) -> SignInProvisionPolicy:
        """
        Environment-aware secure defaults.

        - prod/production: disable implicit username bootstrap.
        - dev/test/other: keep ergonomic bootstrap enabled.
        """
        normalized_env = (env or os.getenv("AQUILIA_ENV", "prod")).strip().lower()
        if normalized_env in {"prod", "production"}:
            return cls(allow_username_bootstrap=False)
        return cls()


class AuthManager:
    """
    Central authentication manager.

    Coordinates all authentication operations:
    - Password authentication
    - API key authentication
    - Token refresh
    - Session management
    - Rate limiting

    High-level Aquilia-native session APIs:
    - sign_in(...): ergonomic request-aware login
    - sign_out(...): scoped logout semantics (session/identity/all)
    - resume_identity(...): restore principal from token or session context
    """

    def __init__(
        self,
        token_manager: TokenManager,
        identity_store: IdentityStore | None = None,
        credential_store: CredentialStore | None = None,
        password_hasher: PasswordHasher | None = None,
        rate_limiter: RateLimiter | None = None,
        login_identifier_attributes: tuple[str, ...] | list[str] | None = None,
    ):
        # Auto-provision default in-memory stores when callers omit explicit storage wiring.
        # This keeps sign_in ergonomic in tests, scripts, and lightweight setups.
        self.identity_store = identity_store or MemoryIdentityStore()
        self.credential_store = credential_store or MemoryCredentialStore()
        self.token_manager = token_manager
        self.password_hasher = password_hasher or PasswordHasher()
        self.rate_limiter = rate_limiter or RateLimiter()
        default_identifiers = ("email", "username", "login", "identity_id")
        attrs = tuple(login_identifier_attributes or default_identifiers)
        if not attrs:
            attrs = default_identifiers
        self.login_identifier_attributes = attrs

    async def _resolve_target_identity_id_for_sign_in(
        self,
        username: str,
        identity_seed: Identity | None,
    ) -> str | None:
        """Resolve target identity id for a sign_in attempt."""
        if identity_seed is not None:
            return identity_seed.id

        identity = await self._resolve_identity_for_identifier(username)
        return identity.id if identity else None

    async def _resolve_identity_for_identifier(self, identifier: str) -> Identity | None:
        """
        Resolve an identity from a login identifier using configured lookup attributes.

        Supports direct ID lookups and attribute-based resolution. Raises ConflictFault
        if the identifier maps to multiple distinct identities.
        """
        candidates: dict[str, Identity] = {}

        # Direct id lookup path.
        direct = await self.identity_store.get(identifier)
        if direct is not None:
            candidates[direct.id] = direct

        for attr in self.login_identifier_attributes:
            if attr == "id":
                continue
            found = await self.identity_store.get_by_attribute(attr, identifier)
            if found is not None:
                candidates[found.id] = found

        if not candidates:
            return None

        if len(candidates) > 1:
            raise ConflictFault(detail="Ambiguous login identifier")

        return next(iter(candidates.values()))

    def _collect_identity_identifiers(self, identity: Identity | None, session: Any | None) -> set[str]:
        """Collect normalized login identifiers from runtime identity/session state."""
        values: set[str] = set()

        def _add(value: Any) -> None:
            if isinstance(value, str):
                normalized = self._normalize_username_identifier(value, key="auth.runtime.identifier")
                values.add(normalized)

        if identity is not None:
            _add(identity.id)
            for attr in self.login_identifier_attributes:
                _add(identity.get_attribute(attr))

        if session is None:
            return values

        data = getattr(session, "data", None)
        if isinstance(data, dict):
            _add(data.get("identity_id"))
            for attr in self.login_identifier_attributes:
                _add(data.get(attr))

            attrs = data.get("attributes")
            if isinstance(attrs, dict):
                for attr in self.login_identifier_attributes:
                    _add(attrs.get(attr))

        principal = getattr(session, "principal", None)
        if principal is not None:
            _add(getattr(principal, "id", None))

        return values

    def _normalize_username_identifier(self, username: str, *, key: str) -> str:
        """Normalize and validate username/email input."""
        if not isinstance(username, str):
            raise ConfigInvalidFault(
                key=key,
                reason="username must be a string",
            )

        normalized = username.strip()
        if not normalized:
            raise ConfigInvalidFault(
                key=key,
                reason="username cannot be empty",
            )

        # Email local-part may be case sensitive, but production identity stores are
        # almost always case-insensitive for email identifiers.
        if "@" in normalized:
            normalized = normalized.lower()

        return normalized

    def _validate_password_input(self, password: str, *, key: str) -> None:
        """Validate password input shape for auth entrypoints."""
        if not isinstance(password, str):
            raise ConfigInvalidFault(
                key=key,
                reason="password must be a string",
            )
        if not password:
            raise ConfigInvalidFault(
                key=key,
                reason="password cannot be empty",
            )

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

    def current_session(self) -> Any | None:
        """Return current runtime session if auth/session middleware is active."""
        return self._get_runtime_session()

    def has_active_session(self) -> bool:
        """Check whether a runtime session is currently available."""
        return self.current_session() is not None

    def current_identity_id(self) -> str | None:
        """
        Return identity_id bound to the current runtime session, if available.

        This is useful for service-layer checks without requiring token parsing.
        """
        session = self.current_session()
        if session is None:
            return None

        try:
            from .integration.aquila_sessions import get_identity_id

            return get_identity_id(session)
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

    def _normalize_scopes(
        self,
        scopes: SessionScope | str | list[SessionScope | str] | tuple[SessionScope | str, ...] | set[SessionScope | str] | None,
        *,
        key: str,
    ) -> list[str] | None:
        """Normalize mixed scope inputs into a list of non-empty string values."""
        if scopes is None:
            return None

        if isinstance(scopes, (SessionScope, str)):
            scope_items: list[SessionScope | str] = [scopes]
        elif isinstance(scopes, (list, tuple, set)):
            scope_items = list(scopes)
        else:
            raise ConfigInvalidFault(
                key=key,
                reason="Scopes must be a SessionScope, string, or an iterable of those values",
            )

        normalized: list[str] = []
        for item in scope_items:
            if isinstance(item, SessionScope):
                value = item.value
            elif isinstance(item, str):
                value = item
            else:
                raise ConfigInvalidFault(
                    key=key,
                    reason="Scopes must contain only SessionScope or string values",
                )

            trimmed = value.strip()
            if not trimmed:
                raise ConfigInvalidFault(
                    key=key,
                    reason="Scope values cannot be empty",
                )
            normalized.append(trimmed)

        return normalized

    async def authenticate_password(
        self,
        username: str,
        password: str,
        scopes: SessionScope | str | list[SessionScope | str] | tuple[SessionScope | str, ...] | set[SessionScope | str] | None = None,
        session_id: str | None = None,
        client_metadata: dict[str, Any] | None = None,
    ) -> AuthResult:
        """
        Authenticate using username/password.

        Args:
            username: Username or email
            password: Plain text password
            scopes: Requested scopes as SessionScope/string or collection of values
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
        username = self._normalize_username_identifier(username, key="auth.authenticate_password.username")
        self._validate_password_input(password, key="auth.authenticate_password.password")

        # Rate limiting check
        rate_key = f"auth:password:{username}"
        if self.rate_limiter.is_locked_out(rate_key):
            raise AUTH_ACCOUNT_LOCKED(
                username=username,
                retry_after=self.rate_limiter.lockout_duration,
            )

        # Resolve identity using configured identifier attributes.
        identity = await self._resolve_identity_for_identifier(username)

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
        normalized_scopes = self._normalize_scopes(scopes, key="auth.authenticate_password.scopes")

        # Get roles from identity
        roles = identity.get_attribute("roles", [])
        if isinstance(roles, (set, tuple)):
            roles = list(roles)
        elif not isinstance(roles, list):
            roles = [roles] if roles else []

        # Issue tokens
        access_token = await self.token_manager.issue_access_token(
            identity_id=identity.id,
            scopes=normalized_scopes or ["profile"],
            roles=roles,
            session_id=session_id,
            tenant_id=identity.tenant_id,
        )

        refresh_token = await self.token_manager.issue_refresh_token(
            identity_id=identity.id,
            scopes=normalized_scopes or ["profile"],
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

    async def sign_in(
        self,
        *,
        username: str,
        password: str,
        scopes: SessionScope | str | list[SessionScope | str] | tuple[SessionScope | str, ...] | set[SessionScope | str] | None = None,
        session: Literal["auto", "new"] | str = "auto",
        client_metadata: dict[str, Any] | None = None,
        identity: Identity | None = None,
        password_hash: str | None = None,
        provision: SignInProvisionPolicy | None = None,
    ) -> AuthResult:
        """
        Aquilia-native high-level sign-in API.

        Args:
            username: Username or email
            password: Plain text password
            scopes: Optional requested scopes as SessionScope/string or collection of values
            session:
                - "auto": bind to active runtime session if present, otherwise create one
                - "new": force a new synthetic session id
                - <str>: explicit session id
            client_metadata: Optional client context metadata
            identity: Optional trusted identity seed used to bootstrap auth stores
            password_hash: Optional pre-hashed password to store when backfilling credentials
            provision: Optional provisioning policy (secure defaults applied when omitted)

        Returns:
            AuthResult including issued tokens and resolved session_id
        """
        username = self._normalize_username_identifier(username, key="auth.sign_in.username")
        self._validate_password_input(password, key="auth.sign_in.password")

        runtime_identity_id = self.current_identity_id()
        if runtime_identity_id:
            target_identity_id = await self._resolve_target_identity_id_for_sign_in(username, identity)
            if target_identity_id == runtime_identity_id:
                raise ConflictFault(detail="Identity is already signed in for the current session")

            runtime_session = self.current_session()
            runtime_ctx_identity = None
            try:
                from .integration.runtime_context import get_auth_runtime_context

                runtime_ctx = get_auth_runtime_context()
                if runtime_ctx is not None:
                    runtime_ctx_identity = runtime_ctx.identity
            except Exception:
                runtime_ctx_identity = None

            runtime_identifiers = self._collect_identity_identifiers(runtime_ctx_identity, runtime_session)
            if username in runtime_identifiers:
                raise ConflictFault(detail="Identity is already signed in for the current session")

        if session == "auto":
            explicit_session_id = None
        elif session == "new":
            explicit_session_id = f"sess_{secrets.token_urlsafe(32)}"
        else:
            if not session.strip():
                raise ConfigInvalidFault(
                    key="auth.sign_in.session",
                    reason="Explicit session id cannot be empty",
                )
            explicit_session_id = session

        policy = provision or SignInProvisionPolicy.secure_defaults()
        if identity is not None and not isinstance(identity, Identity):
            raise ConfigInvalidFault(
                key="auth.sign_in.identity",
                reason="Identity seed must be an Identity instance",
            )

        if password_hash is not None:
            if not isinstance(password_hash, str) or not password_hash.strip():
                raise ConfigInvalidFault(
                    key="auth.sign_in.password_hash",
                    reason="password_hash must be a non-empty string when provided",
                )

        await self._provision_from_identity_seed(
            username=username,
            password=password,
            identity_seed=identity,
            password_hash=password_hash,
            policy=policy,
        )

        try:
            return await self.authenticate_password(
                username=username,
                password=password,
                scopes=scopes,
                session_id=explicit_session_id,
                client_metadata=client_metadata,
            )
        except AUTH_INVALID_CREDENTIALS:
            # Secure-default ergonomics: when auth stores are empty/misaligned,
            # bootstrap a local identity+credential from username/password once.
            # This makes sign_in(username, password) work out-of-the-box.
            if not policy.allow_username_bootstrap:
                raise

            provisioned = await self._provision_from_username_credentials(
                username=username,
                password=password,
                policy=policy,
            )
            if not provisioned:
                raise

            return await self.authenticate_password(
                username=username,
                password=password,
                scopes=scopes,
                session_id=explicit_session_id,
                client_metadata=client_metadata,
            )

    async def _provision_from_identity_seed(
        self,
        *,
        username: str,
        password: str,
        identity_seed: Identity | None,
        password_hash: str | None,
        policy: SignInProvisionPolicy,
    ) -> None:
        """Provision missing auth records from a trusted identity seed."""
        if not policy.enable_identity_seed or identity_seed is None:
            return

        runtime_identity_id = self.current_identity_id()
        if runtime_identity_id and runtime_identity_id != identity_seed.id:
            raise TooManyRequestsFault(
                detail="Active authenticated session cannot provision a different identity",
                retry_after=60,
                metadata={
                    "current_identity_id": runtime_identity_id,
                    "target_identity_id": identity_seed.id,
                },
            )

        existing_identity = await self.identity_store.get(identity_seed.id)
        if existing_identity is None and policy.create_identity_if_missing:
            try:
                await self.identity_store.create(identity_seed)
            except Exception:
                # Handle benign races where another worker creates the same seed.
                existing_identity = await self.identity_store.get(identity_seed.id)
                if existing_identity is None:
                    raise

        # Keep attribute indexes warm for username/email lookup in stores that rely on them.
        identity_for_lookup = await self.identity_store.get(identity_seed.id)
        if identity_for_lookup is not None:
            existing_by_email = await self.identity_store.get_by_attribute("email", username)
            existing_by_username = await self.identity_store.get_by_attribute("username", username)
            if existing_by_email is None and existing_by_username is None:
                # Best-effort consistency update for stores that support update().
                merged_attributes = dict(identity_for_lookup.attributes)
                if "@" in username and "email" not in merged_attributes:
                    merged_attributes["email"] = username
                if "@" not in username and "username" not in merged_attributes:
                    merged_attributes["username"] = username
                if "login" not in merged_attributes:
                    merged_attributes["login"] = username

                if merged_attributes != identity_for_lookup.attributes:
                    updated_identity = Identity(
                        id=identity_for_lookup.id,
                        type=identity_for_lookup.type,
                        attributes=merged_attributes,
                        status=identity_for_lookup.status,
                        tenant_id=identity_for_lookup.tenant_id,
                        created_at=identity_for_lookup.created_at,
                        updated_at=datetime.now(timezone.utc),
                    )
                    try:
                        await self.identity_store.update(updated_identity)
                    except Exception:
                        pass

        if not policy.backfill_password_credential:
            return

        identity_id = identity_seed.id
        existing_password = await self.credential_store.get_password(identity_id)

        if existing_password is not None and not policy.overwrite_password_credential:
            return

        materialized_hash = password_hash or self.password_hasher.hash(password)
        await self.credential_store.save_password(
            PasswordCredential(identity_id=identity_id, password_hash=materialized_hash)
        )

    async def _provision_from_username_credentials(
        self,
        *,
        username: str,
        password: str,
        policy: SignInProvisionPolicy,
    ) -> bool:
        """
        Bootstrap missing identity/password records directly from sign-in credentials.

        Returns True when provisioning changed store state and auth can be retried.
        Returns False when no safe provisioning action is possible.
        """
        runtime_identity_id = self.current_identity_id()

        # Resolve by configured login identifier attributes.
        identity = await self._resolve_identity_for_identifier(username)

        if runtime_identity_id and identity is not None and identity.id != runtime_identity_id:
            raise TooManyRequestsFault(
                detail="Active authenticated session cannot switch identity during sign-in",
                retry_after=60,
                metadata={
                    "current_identity_id": runtime_identity_id,
                    "target_identity_id": identity.id,
                    "username": username,
                },
            )

        changed = False

        if identity is None and policy.create_identity_if_missing:
            if runtime_identity_id:
                raise TooManyRequestsFault(
                    detail="Active authenticated session cannot create a new identity",
                    retry_after=60,
                    metadata={
                        "current_identity_id": runtime_identity_id,
                        "username": username,
                    },
                )

            # Stable, non-guessable deterministic ID for same username across retries.
            digest = hashlib.sha256(username.encode("utf-8")).hexdigest()[:24]
            identity_id = f"usr_{digest}"

            attributes: dict[str, Any]
            if "@" in username:
                attributes = {"email": username, "login": username}
            else:
                attributes = {"username": username, "login": username}

            identity = Identity(
                id=identity_id,
                type=IdentityType.USER,
                attributes=attributes,
                status=IdentityStatus.ACTIVE,
            )

            try:
                await self.identity_store.create(identity)
                changed = True
            except Exception:
                # Possible race with parallel bootstrap; re-load and continue.
                identity = await self.identity_store.get(identity_id)
                if identity is None:
                    return False

        if identity is None:
            return changed

        if not policy.backfill_password_credential:
            return changed

        password_cred = await self.credential_store.get_password(identity.id)
        if password_cred is not None and not policy.overwrite_password_credential:
            return changed

        await self.credential_store.save_password(
            PasswordCredential(identity_id=identity.id, password_hash=self.password_hasher.hash(password))
        )
        return True

    async def authenticate_api_key(
        self,
        api_key: str,
        required_scopes: SessionScope | str | list[SessionScope | str] | tuple[SessionScope | str, ...] | set[SessionScope | str] | None = None,
    ) -> AuthResult:
        """
        Authenticate using API key.

        Args:
            api_key: API key string
            required_scopes: Scopes required for this request as SessionScope/string or collection of values

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
        normalized_required_scopes = self._normalize_scopes(
            required_scopes,
            key="auth.authenticate_api_key.required_scopes",
        )
        if normalized_required_scopes:
            from .faults import AUTHZ_INSUFFICIENT_SCOPE

            missing_scopes = set(normalized_required_scopes) - set(credential.scopes)
            if missing_scopes:
                raise AUTHZ_INSUFFICIENT_SCOPE(
                    required_scopes=normalized_required_scopes,
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
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """
        Logout user by revoking all tokens.

        Args:
            identity_id: Revoke all tokens for this identity
            session_id: Revoke all tokens for this session
            access_token: Optional access token for deriving subject/session
            refresh_token: Optional refresh token to revoke directly
        """
        if identity_id and session_id:
            scope: Literal["session", "identity", "all"] = "all"
        elif identity_id:
            scope = "identity"
        else:
            scope = "session"

        await self.sign_out(
            scope=scope,
            identity_id=identity_id,
            session_id=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def _extract_token_subject_context(self, access_token: str | None) -> tuple[str | None, str | None, str | None]:
        """Best-effort extraction of identity/session/jti from an access token."""
        if not access_token:
            return (None, None, None)

        try:
            claims = await self.token_manager.validate_access_token(access_token)
        except Exception:
            return (None, None, None)

        return (
            claims.get("sub"),
            claims.get("sid"),
            claims.get("jti"),
        )

    def _clear_runtime_auth_state(self) -> dict[str, bool]:
        """Clear request/session auth state for current runtime context."""
        runtime_ctx = None
        try:
            from .integration.runtime_context import get_auth_runtime_context

            runtime_ctx = get_auth_runtime_context()
        except Exception:
            runtime_ctx = None

        if runtime_ctx is None:
            return {
                "runtime_context_cleared": False,
                "request_state_cleared": False,
                "session_state_cleared": False,
            }

        request_cleared = False
        request = getattr(runtime_ctx, "request", None)
        if request is not None:
            state = getattr(request, "state", None)
            if isinstance(state, dict):
                state.pop("identity", None)
                state.pop("auth", None)
                state["authenticated"] = False
                request_cleared = True
            elif state is not None:
                try:
                    if hasattr(state, "pop"):
                        state.pop("identity", None)
                        state.pop("auth", None)
                    if hasattr(state, "__setitem__"):
                        state["authenticated"] = False
                    elif hasattr(state, "authenticated"):
                        state.authenticated = False
                    request_cleared = True
                except Exception:
                    request_cleared = False

        session_cleared = False
        runtime_session = getattr(runtime_ctx, "session", None)
        if runtime_session is not None:
            if hasattr(runtime_session, "clear_authentication"):
                try:
                    runtime_session.clear_authentication()
                    session_cleared = True
                except Exception:
                    session_cleared = False

            # Remove auth-bound session payload keys to prevent stale auth context.
            data = getattr(runtime_session, "data", None)
            if data is not None and hasattr(data, "pop"):
                for key in (
                    "identity_id",
                    "tenant_id",
                    "roles",
                    "scopes",
                    "status",
                    "attributes",
                    "token_claims",
                    "mfa_verified",
                ):
                    try:
                        data.pop(key, None)
                        session_cleared = True
                    except Exception:
                        pass

        runtime_ctx.identity = None
        runtime_ctx.auth = None

        return {
            "runtime_context_cleared": True,
            "request_state_cleared": request_cleared,
            "session_state_cleared": session_cleared,
        }

    async def sign_out(
        self,
        *,
        scope: Literal["session", "identity", "all"] = "session",
        identity_id: str | None = None,
        session_id: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> JSONObject:
        """
        Aquilia-native sign-out API with explicit scope semantics.

        Args:
            scope:
                - "session": revoke tokens for current/target session only
                - "identity": revoke tokens for a single identity (all sessions)
                - "all": revoke by both identity and session when available
            identity_id: Optional explicit identity id override
            session_id: Optional explicit session id override
            access_token: Optional access token used to derive identity/session and revoke JTI
            refresh_token: Optional refresh token revoked directly

        Returns:
            Summary dict with resolved revocation scope.
        """
        valid_scopes = {"session", "identity", "all"}
        if scope not in valid_scopes:
            raise ConfigInvalidFault(
                key="auth.sign_out.scope",
                reason=f"Unsupported scope '{scope}'. Expected one of: {', '.join(sorted(valid_scopes))}",
            )

        token_identity_id, token_session_id, token_jti = await self._extract_token_subject_context(access_token)

        runtime_identity_id = self.current_identity_id()
        resolved_identity_id = identity_id or runtime_identity_id or token_identity_id

        runtime_session = self.current_session()
        resolved_session_id = session_id
        if resolved_session_id is None and runtime_session is not None and hasattr(runtime_session, "id"):
            resolved_session_id = str(runtime_session.id)
        if resolved_session_id is None:
            resolved_session_id = token_session_id

        if scope in ("identity", "all") and not resolved_identity_id:
            raise AUTH_REQUIRED()

        if scope in ("session", "all") and not resolved_session_id:
            raise AUTH_SESSION_REQUIRED()

        revoked_identity = False
        revoked_session = False
        revoked_access = False
        revoked_refresh = False

        try:
            if scope in ("identity", "all") and resolved_identity_id:
                await self.token_manager.revoke_tokens_by_identity(resolved_identity_id)
                revoked_identity = True

            if scope in ("session", "all") and resolved_session_id:
                await self.token_manager.revoke_tokens_by_session(resolved_session_id)
                revoked_session = True

            if token_jti:
                await self.token_manager.revoke_token(token_jti)
                revoked_access = True

            if refresh_token:
                await self.token_manager.revoke_token(refresh_token)
                revoked_refresh = True
        finally:
            cleanup = self._clear_runtime_auth_state()

        return {
            "scope": scope,
            "identity_id": resolved_identity_id,
            "session_id": resolved_session_id,
            "revoked_identity": revoked_identity,
            "revoked_session": revoked_session,
            "revoked_access": revoked_access,
            "revoked_refresh": revoked_refresh,
            **cleanup,
        }

    async def resume_identity(self, access_token: str | None = None) -> Identity | None:
        """
        Resolve the current identity from token or runtime session context.

        Resolution order:
        1) access token (if provided)
        2) current runtime session identity binding
        """
        if access_token:
            return await self.get_identity_from_token(access_token)

        identity_id = self.current_identity_id()
        if identity_id:
            return await self.identity_store.get(identity_id)

        return None

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
