"""
AquilAuth - Credential and Token Stores

In-memory and Redis-backed storage implementations for identities,
credentials, OAuth clients, and tokens.

Stores:
- MemoryIdentityStore: Dev/testing identity storage
- MemoryCredentialStore: Dev/testing credential storage
- MemoryOAuthClientStore: Dev/testing OAuth client storage
- MemoryTokenStore: Dev/testing token storage
- RedisTokenStore: Production token revocation with bloom filter
"""

from __future__ import annotations

import asyncio
import json
import secrets
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from aquilia.auth.core import (
    ApiKeyCredential,
    CredentialStatus,
    Identity,
    IdentityStatus,
    MFACredential,
    OAuthClient,
    PasswordCredential,
)
from aquilia.auth.tokens import hash_token as _sha256
from aquilia.faults.domains import ConflictFault, NotFoundFault

# ============================================================================
# Memory Stores (for development and testing)
# ============================================================================


class MemoryIdentityStore:
    """In-memory identity storage for development/testing."""

    def __init__(self):
        self._identities: dict[str, Identity] = {}
        self._by_attribute: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        self._lock = asyncio.Lock()

    async def create(self, identity: Identity) -> Identity:
        """Create new identity."""
        async with self._lock:
            if identity.id in self._identities:
                raise ConflictFault(detail=f"Identity {identity.id} already exists")

            self._identities[identity.id] = identity

            # Index attributes for fast lookup
            for key, value in identity.attributes.items():
                if isinstance(value, (str, int, bool)):
                    self._by_attribute[key][str(value)].add(identity.id)

            return identity

    async def get(self, identity_id: str) -> Identity | None:
        """Get identity by ID."""
        return self._identities.get(identity_id)

    def _reindex(self, identity_id: str, attributes: dict[str, Any]) -> None:
        """Rebuild the attribute index for one identity (seed/bootstrap path).

        Clears the identity's previous index entries first so re-seeding
        with changed attributes cannot leave stale lookups behind.
        """
        # Remove the identity from every value-set it belongs to…
        for key in list(self._by_attribute.keys()):
            for value in list(self._by_attribute[key].keys()):
                self._by_attribute[key][value].discard(identity_id)
                if not self._by_attribute[key][value]:
                    del self._by_attribute[key][value]
        # …then add the current attributes.
        for key, value in attributes.items():
            if isinstance(value, (str, int, bool)):
                self._by_attribute[key][str(value)].add(identity_id)

    async def get_by_attribute(self, attribute: str, value: Any) -> Identity | None:
        """Get identity by attribute value."""
        identity_ids = self._by_attribute[attribute].get(str(value), set())
        if identity_ids:
            return self._identities.get(next(iter(identity_ids)))
        return None

    async def update(self, identity: Identity) -> Identity:
        """Update existing identity."""
        async with self._lock:
            if identity.id not in self._identities:
                raise NotFoundFault(detail=f"Identity {identity.id} not found")

            old_identity = self._identities[identity.id]

            # Update attribute indices
            for key, value in old_identity.attributes.items():
                if isinstance(value, (str, int, bool)):
                    self._by_attribute[key][str(value)].discard(identity.id)

            for key, value in identity.attributes.items():
                if isinstance(value, (str, int, bool)):
                    self._by_attribute[key][str(value)].add(identity.id)

            self._identities[identity.id] = identity
            return identity

    async def delete(self, identity_id: str) -> bool:
        """Delete identity (soft delete by setting status)."""
        async with self._lock:
            identity = self._identities.get(identity_id)
            if not identity:
                return False

            # Create new identity with DELETED status
            deleted_identity = Identity(
                id=identity.id,
                type=identity.type,
                attributes=identity.attributes,
                status=IdentityStatus.DELETED,
                tenant_id=identity.tenant_id,
                created_at=identity.created_at,
                updated_at=datetime.now(timezone.utc),
            )

            self._identities[identity_id] = deleted_identity
            return True

    async def list_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[Identity]:
        """List identities by tenant."""
        identities = [
            i for i in self._identities.values() if i.tenant_id == tenant_id and i.status != IdentityStatus.DELETED
        ]
        return identities[offset : offset + limit]


class MemoryCredentialStore:
    """In-memory credential storage for development/testing."""

    def __init__(self):
        self._passwords: dict[str, PasswordCredential] = {}
        self._api_keys: dict[str, ApiKeyCredential] = {}
        self._api_keys_by_hash: dict[str, ApiKeyCredential] = {}
        self._mfa: dict[str, list[MFACredential]] = defaultdict(list)
        self._lock = asyncio.Lock()

    # Password credentials
    async def save_password(self, credential: PasswordCredential) -> None:
        """Save password credential (upsert)."""
        async with self._lock:
            self._passwords[credential.identity_id] = credential

    async def create_password(self, credential: PasswordCredential) -> None:
        """Create password credential (CredentialStore protocol)."""
        await self.save_password(credential)

    async def update_password(self, credential: PasswordCredential) -> None:
        """Update password credential (CredentialStore protocol)."""
        await self.save_password(credential)

    async def get_password(self, identity_id: str) -> PasswordCredential | None:
        """Get password credential."""
        return self._passwords.get(identity_id)

    async def delete_password(self, identity_id: str) -> bool:
        """Delete password credential."""
        async with self._lock:
            if identity_id in self._passwords:
                del self._passwords[identity_id]
                return True
            return False

    # API key credentials
    async def save_api_key(self, credential: ApiKeyCredential) -> None:
        """Save API key credential."""
        async with self._lock:
            self._api_keys[credential.key_id] = credential
            self._api_keys_by_hash[credential.key_hash] = credential

    async def create_api_key(self, credential: ApiKeyCredential) -> None:
        """Create API key credential (CredentialStore protocol)."""
        async with self._lock:
            if credential.key_id in self._api_keys:
                raise ConflictFault(detail=f"API key {credential.key_id} already exists")
            self._api_keys[credential.key_id] = credential
            self._api_keys_by_hash[credential.key_hash] = credential

    async def get_api_key(self, key_id: str) -> ApiKeyCredential | None:
        """Get API key credential."""
        return self._api_keys.get(key_id)

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKeyCredential | None:
        """Get API key by its HMAC hash (O(1) lookup, CredentialStore protocol)."""
        return self._api_keys_by_hash.get(key_hash)

    async def get_api_key_by_prefix(self, prefix: str) -> ApiKeyCredential | None:
        """Get API key by prefix (first 8 chars). Deprecated: prefer get_api_key_by_hash."""
        for credential in self._api_keys.values():
            if credential.prefix == prefix:
                return credential
        return None

    async def list_api_keys(self, identity_id: str) -> list[ApiKeyCredential]:
        """List all API keys for identity."""
        return [c for c in self._api_keys.values() if c.identity_id == identity_id]

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key (soft: marks status REVOKED, CredentialStore protocol)."""
        async with self._lock:
            credential = self._api_keys.get(key_id)
            if not credential:
                return False
            credential.status = CredentialStatus.REVOKED
            return True

    async def delete_api_key(self, key_id: str) -> bool:
        """Hard-delete API key credential."""
        async with self._lock:
            credential = self._api_keys.pop(key_id, None)
            if credential is None:
                return False
            self._api_keys_by_hash.pop(credential.key_hash, None)
            return True

    # MFA credentials
    async def save_mfa(self, credential: MFACredential) -> None:
        """Save MFA credential."""
        async with self._lock:
            credentials = self._mfa[credential.identity_id]
            # Remove existing credential of same type
            self._mfa[credential.identity_id] = [c for c in credentials if c.mfa_type != credential.mfa_type]
            self._mfa[credential.identity_id].append(credential)

    async def create_mfa(self, credential: MFACredential) -> None:
        """Create MFA credential (CredentialStore protocol)."""
        await self.save_mfa(credential)

    async def update_mfa(self, credential: MFACredential) -> None:
        """Update MFA credential (CredentialStore protocol)."""
        await self.save_mfa(credential)

    async def get_mfa(self, identity_id: str, mfa_type: str | None = None) -> list[MFACredential]:
        """Get MFA credentials for identity."""
        credentials = self._mfa.get(identity_id, [])
        if mfa_type:
            return [c for c in credentials if c.mfa_type == mfa_type]
        return credentials

    async def delete_mfa(self, identity_id: str, mfa_type: str | None = None) -> bool:
        """Delete MFA credentials."""
        async with self._lock:
            if identity_id not in self._mfa:
                return False

            if mfa_type:
                original_len = len(self._mfa[identity_id])
                self._mfa[identity_id] = [c for c in self._mfa[identity_id] if c.mfa_type != mfa_type]
                return len(self._mfa[identity_id]) < original_len
            else:
                del self._mfa[identity_id]
                return True


class MemoryOAuthClientStore:
    """In-memory OAuth client storage for development/testing."""

    def __init__(self):
        self._clients: dict[str, OAuthClient] = {}
        self._lock = asyncio.Lock()

    async def create(self, client: OAuthClient) -> OAuthClient:
        """Create OAuth client."""
        async with self._lock:
            if client.client_id in self._clients:
                raise ConflictFault(detail=f"Client {client.client_id} already exists")
            self._clients[client.client_id] = client
            return client

    async def get(self, client_id: str) -> OAuthClient | None:
        """Get OAuth client by ID."""
        return self._clients.get(client_id)

    async def update(self, client: OAuthClient) -> OAuthClient:
        """Update OAuth client."""
        async with self._lock:
            if client.client_id not in self._clients:
                raise NotFoundFault(detail=f"Client {client.client_id} not found")
            self._clients[client.client_id] = client
            return client

    async def delete(self, client_id: str) -> bool:
        """Delete OAuth client."""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                return True
            return False

    async def list(self, owner_id: str | None = None, limit: int = 100, offset: int = 0) -> list[OAuthClient]:
        """List OAuth clients, optionally filtered by owner (from metadata)."""
        clients = list(self._clients.values())
        if owner_id:
            clients = [c for c in clients if c.metadata.get("owner_id") == owner_id]
        return clients[offset : offset + limit]

    async def list_all(self) -> list[OAuthClient]:
        """List all OAuth clients (OAuthClientStore protocol)."""
        return await self.list()


class MemoryTokenStore:
    """
    In-memory token storage for development/testing.

    Implements both the base :class:`~aquilia.auth.tokens.TokenStore` protocol
    and the :class:`~aquilia.auth.tokens.RotatingTokenStore` rotation
    protocol, so refresh rotation with reuse detection works out of the box.
    """

    def __init__(self):
        self._refresh_tokens: dict[str, dict[str, Any]] = {}
        self._revoked_tokens: set[str] = set()
        self._revoked_by_identity: dict[str, set[str]] = defaultdict(set)
        self._revoked_by_session: dict[str, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()
        # Rotation families: family_id -> record; hash index for O(1) lookup.
        self._families: dict[str, dict[str, Any]] = {}
        self._families_by_hash: dict[str, str] = {}
        self._families_by_session: dict[str, list[str]] = defaultdict(list)

    async def save_refresh_token(
        self,
        token_id: str,
        identity_id: str,
        scopes: list[str],
        expires_at: datetime,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        roles: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Save refresh token."""
        async with self._lock:
            self._refresh_tokens[token_id] = {
                "identity_id": identity_id,
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
                "session_id": session_id,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "roles": roles or [],
                "tenant_id": tenant_id,
            }

            if session_id:
                self._revoked_by_session[session_id].add(token_id)

    async def get_refresh_token(self, token_id: str) -> dict[str, Any] | None:
        """Get refresh token data."""
        return self._refresh_tokens.get(token_id)

    async def revoke_refresh_token(self, token_id: str) -> None:
        """Revoke single refresh token (token-id path *and* rotation family)."""
        async with self._lock:
            self._revoked_tokens.add(token_id)

            # Track by identity and session for bulk revocation
            if token_id in self._refresh_tokens:
                data = self._refresh_tokens[token_id]
                self._revoked_by_identity[data["identity_id"]].add(token_id)

            # Rotation-family credentials are keyed by hash: revoke the
            # owning family so the raw token dies too.
            family_id = self._families_by_hash.get(_sha256(token_id))
            if family_id is not None:
                fam = self._families.get(family_id)
                if fam is not None and not fam.get("revoked"):
                    fam["revoked"] = True
                    fam["revocation_reason"] = "revoked"

    async def revoke_tokens_by_identity(self, identity_id: str) -> None:
        """Revoke all tokens for identity (token-ids *and* rotation families)."""
        async with self._lock:
            for token_id, data in self._refresh_tokens.items():
                if data["identity_id"] == identity_id:
                    self._revoked_tokens.add(token_id)
                    self._revoked_by_identity[identity_id].add(token_id)

            for fam in self._families.values():
                if fam.get("identity_id") == identity_id and not fam.get("revoked"):
                    fam["revoked"] = True
                    fam["revocation_reason"] = "identity_revoked"

    async def revoke_tokens_by_session(self, session_id: str) -> None:
        """Revoke all tokens for session (token-ids *and* rotation families)."""
        async with self._lock:
            token_ids = self._revoked_by_session.get(session_id, set())
            self._revoked_tokens.update(token_ids)

            for family_id in list(self._families_by_session.get(session_id, [])):
                fam = self._families.get(family_id)
                if fam is not None and not fam.get("revoked"):
                    fam["revoked"] = True
                    fam["revocation_reason"] = "session_revoked"

    async def is_token_revoked(self, token_id: str) -> bool:
        """Check if token is revoked (revocation set *or* revoked rotation family)."""
        if token_id in self._revoked_tokens:
            return True
        family_id = self._families_by_hash.get(_sha256(token_id))
        if family_id is not None:
            fam = self._families.get(family_id)
            if fam is not None and fam.get("revoked"):
                return True
        return False

    async def cleanup_expired(self) -> int:
        """Remove expired tokens (returns count removed)."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            expired = []

            for token_id, data in self._refresh_tokens.items():
                expires_at = datetime.fromisoformat(data["expires_at"])
                if expires_at < now:
                    expired.append(token_id)

            for token_id in expired:
                del self._refresh_tokens[token_id]
                self._revoked_tokens.discard(token_id)

            # Expired rotation families go too.
            expired_families = [
                fid for fid, fam in self._families.items() if datetime.fromisoformat(str(fam["expires_at"])) < now
            ]
            for fid in expired_families:
                self._drop_family(fid)

            return len(expired) + len(expired_families)

    # ── RotatingTokenStore protocol ─────────────────────────────────────

    def _drop_family(self, family_id: str) -> None:
        fam = self._families.pop(family_id, None)
        if fam is None:
            return
        self._families_by_hash.pop(fam.get("current_hash"), None)
        self._families_by_hash.pop(fam.get("previous_hash"), None)
        session_id = fam.get("session_id")
        if session_id:
            siblings = self._families_by_session.get(session_id)
            if siblings and family_id in siblings:
                siblings.remove(family_id)

    async def create_refresh_family(
        self,
        token_hash: str,
        *,
        identity_id: str,
        scopes: list[str],
        expires_at: datetime,
        session_id: str | None = None,
        roles: list[str] | None = None,
        tenant_id: str | None = None,
        device_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new refresh family whose current credential is *token_hash*."""
        async with self._lock:
            family_id = f"rf_{secrets.token_hex(16)}"
            self._families[family_id] = {
                "family_id": family_id,
                "identity_id": identity_id,
                "scopes": list(scopes),
                "roles": list(roles or []),
                "tenant_id": tenant_id,
                "session_id": session_id or family_id,
                "current_hash": token_hash,
                "previous_hash": None,
                "rotated_at": None,
                "device_metadata": device_metadata or {},
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "revoked": False,
                "revocation_reason": None,
            }
            self._families_by_hash[token_hash] = family_id
            session = session_id or family_id
            self._families_by_session[session].append(family_id)

    async def get_refresh_family(self, token_hash: str) -> dict[str, Any] | None:
        """Look up a refresh family by credential hash (current or previous)."""
        family_id = self._families_by_hash.get(token_hash)
        if family_id is None:
            return None
        return self._families.get(family_id)

    async def rotate_refresh_family(
        self,
        token_hash: str,
        new_hash: str,
        *,
        expires_at: datetime,
    ) -> dict[str, Any] | None:
        """
        Atomically rotate a family's credential under the store lock.

        Returns the family record on success, ``{"reuse": True, ...}`` when
        the hash matches the rotated-away previous credential (the family is
        revoked), or ``None`` when unknown.
        """
        async with self._lock:
            family_id = self._families_by_hash.get(token_hash)
            if family_id is None:
                return None
            fam = self._families.get(family_id)
            if fam is None:
                return None

            if fam.get("revoked"):
                return {"reuse": True, **fam}

            if token_hash == fam.get("current_hash"):
                # Winner: current credential rotates forward. The old hash
                # STAYS in the index — it is now the previous credential, and
                # its lookup is what makes reuse detection work.
                fam["previous_hash"] = fam["current_hash"]
                fam["current_hash"] = new_hash
                fam["rotated_at"] = datetime.now(timezone.utc).isoformat()
                fam["expires_at"] = expires_at.isoformat()
                self._families_by_hash[new_hash] = family_id
                return dict(fam)

            if token_hash == fam.get("previous_hash"):
                # Replay of a rotated-away credential: revoke the family.
                fam["revoked"] = True
                fam["revocation_reason"] = "reuse_detected"
                return {"reuse": True, **fam}

            return None

    async def revoke_refresh_family(self, session_id: str, reason: str = "revoked") -> None:
        """Revoke every credential in a session family."""
        async with self._lock:
            for family_id in list(self._families_by_session.get(session_id, [])):
                fam = self._families.get(family_id)
                if fam is not None and not fam.get("revoked"):
                    fam["revoked"] = True
                    fam["revocation_reason"] = reason


# ============================================================================
# Redis Token Store (for production)
# ============================================================================


class RedisTokenStore:
    """
    Redis-backed token store with bloom filter for fast revocation checks.

    Uses:
    - Sorted sets for refresh tokens (with expiration as score)
    - Bloom filter for revoked tokens (probabilistic, fast)
    - Sets for identity/session token tracking
    """

    def __init__(self, redis_client: Any, key_prefix: str = "aquilauth:"):
        """
        Initialize Redis token store.

        Args:
            redis_client: Redis async client (e.g., aioredis)
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis_client
        self.prefix = key_prefix

    def _key(self, *parts: str) -> str:
        """Build Redis key."""
        return self.prefix + ":".join(parts)

    async def save_refresh_token(
        self,
        token_id: str,
        identity_id: str,
        scopes: list[str],
        expires_at: datetime,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        roles: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Save refresh token to Redis."""
        data = {
            "identity_id": identity_id,
            "scopes": json.dumps(scopes),
            "expires_at": expires_at.isoformat(),
            "session_id": session_id or "",
            "metadata": json.dumps(metadata or {}),
            "roles": json.dumps(roles or []),
            "tenant_id": tenant_id or "",
        }

        # Store token data as hash
        await self.redis.hset(
            self._key("token", token_id),
            mapping=data,
        )

        # Set expiration (Redis auto-cleanup)
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        await self.redis.expire(self._key("token", token_id), ttl)

        # Track by identity
        await self.redis.sadd(self._key("identity", identity_id, "tokens"), token_id)
        await self.redis.expire(
            self._key("identity", identity_id, "tokens"),
            ttl + 86400,  # Extra day for cleanup
        )

        # Track by session
        if session_id:
            await self.redis.sadd(self._key("session", session_id, "tokens"), token_id)
            await self.redis.expire(
                self._key("session", session_id, "tokens"),
                ttl + 86400,
            )

    async def get_refresh_token(self, token_id: str) -> dict[str, Any] | None:
        """Get refresh token data from Redis."""
        data = await self.redis.hgetall(self._key("token", token_id))
        if not data:
            return None

        return {
            "identity_id": data[b"identity_id"].decode(),
            "scopes": json.loads(data[b"scopes"].decode()),
            "expires_at": data[b"expires_at"].decode(),
            "session_id": data[b"session_id"].decode() or None,
            "metadata": json.loads(data[b"metadata"].decode()),
            "roles": json.loads(data[b"roles"].decode()) if b"roles" in data else [],
            "tenant_id": (data[b"tenant_id"].decode() or None) if b"tenant_id" in data else None,
        }

    async def revoke_refresh_token(self, token_id: str) -> None:
        """Revoke single refresh token (token-id path *and* rotation family)."""
        # Add to revoked set (bloom filter alternative)
        await self.redis.sadd(self._key("revoked"), token_id)

        # Set expiration on revoked set (cleanup after 30 days)
        await self.redis.expire(self._key("revoked"), 30 * 86400)

        # Rotation-family credentials: revoke the owning family so the raw
        # token dies too.
        family_id = await self.redis.get(self._key("famidx", _sha256(token_id)))
        if family_id:
            if isinstance(family_id, bytes):
                family_id = family_id.decode()
            await self.redis.hset(
                self._key("family", family_id),
                mapping={"revoked": "1", "revocation_reason": "revoked"},
            )

    async def revoke_tokens_by_identity(self, identity_id: str) -> None:
        """Revoke all tokens for identity (token-ids *and* rotation families)."""
        token_ids = await self.redis.smembers(self._key("identity", identity_id, "tokens"))

        if token_ids:
            # Add all to revoked set
            await self.redis.sadd(self._key("revoked"), *[t.decode() for t in token_ids])

        for family_id in await self._family_ids_by("identity_id", identity_id):
            await self.redis.hset(
                self._key("family", family_id),
                mapping={"revoked": "1", "revocation_reason": "identity_revoked"},
            )

    async def revoke_tokens_by_session(self, session_id: str) -> None:
        """Revoke all tokens for session (token-ids *and* rotation families)."""
        token_ids = await self.redis.smembers(self._key("session", session_id, "tokens"))

        if token_ids:
            await self.redis.sadd(self._key("revoked"), *[t.decode() for t in token_ids])
        await self.revoke_refresh_family(session_id, reason="session_revoked")

    async def _family_ids_by(self, field: str, value: str) -> list[str]:
        """Scan families for ``field == value`` (families are few; promote to a
        secondary index only if profiling ever demands it)."""
        family_ids: list[str] = []
        keys = await self.redis.keys(self._key("family", "*"))
        for raw_key in keys or []:
            key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
            fam = await self.redis.hgetall(key)
            if not fam:
                continue

            def _dec(v: Any) -> str:
                return v.decode() if isinstance(v, bytes) else v

            if _dec(fam.get(field, "")) == value and _dec(fam.get("revoked", "0")) != "1":
                family_ids.append(key.rsplit(":", 1)[-1])
        return family_ids

    async def is_token_revoked(self, token_id: str) -> bool:
        """Check if token is revoked (set membership *or* revoked rotation family)."""
        if await self.redis.sismember(self._key("revoked"), token_id):
            return True
        family_id = await self.redis.get(self._key("famidx", _sha256(token_id)))
        if family_id:
            if isinstance(family_id, bytes):
                family_id = family_id.decode()
            revoked = await self.redis.hget(self._key("family", family_id), "revoked")
            if revoked is not None:
                revoked = revoked.decode() if isinstance(revoked, bytes) else revoked
                if revoked == "1":
                    return True
        return False

    async def cleanup_expired(self) -> int:
        """Redis handles expiration automatically, return 0."""
        return 0

    # ── RotatingTokenStore protocol ─────────────────────────────────────
    #
    # Layout:
    #   <prefix>family:<family_id>       — hash: family record
    #   <prefix>famidx:<token_hash>      — string: family_id (current+previous)
    #   <prefix>famsess:<session_id>     — set: family_ids in the session

    _ROTATE_LUA = """
    local famkey = KEYS[1]
    local idxkey_current = KEYS[2]
    local idxkey_new = KEYS[3]
    local new_hash = ARGV[1]
    local expires_at = ARGV[2]
    local now = ARGV[3]

    local fam = redis.call('HGETALL', famkey)
    if #fam == 0 then
        return {'0', 'unknown'}
    end
    local record = {}
    for i = 1, #fam, 2 do record[fam[i]] = fam[i+1] end

    if record['revoked'] == '1' then
        return {'1', 'reuse'}
    end

    if record['current_hash'] == ARGV[4] then
        redis.call('HSET', famkey,
            'previous_hash', record['current_hash'],
            'current_hash', new_hash,
            'rotated_at', now,
            'expires_at', expires_at)
        -- The old hash's index entry STAYS: lookups of the rotated-away
        -- credential must still reach this family (reuse detection).
        redis.call('SET', idxkey_new, record['family_id'])
        return {'1', 'ok'}
    end

    if record['previous_hash'] == ARGV[4] then
        redis.call('HSET', famkey, 'revoked', '1',
            'revocation_reason', 'reuse_detected')
        return {'1', 'reuse'}
    end

    return {'0', 'unknown'}
    """

    async def create_refresh_family(
        self,
        token_hash: str,
        *,
        identity_id: str,
        scopes: list[str],
        expires_at: datetime,
        session_id: str | None = None,
        roles: list[str] | None = None,
        tenant_id: str | None = None,
        device_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new refresh family whose current credential is *token_hash*."""
        family_id = f"rf_{secrets.token_hex(16)}"
        session = session_id or family_id
        record = {
            "family_id": family_id,
            "identity_id": identity_id,
            "scopes": json.dumps(list(scopes)),
            "roles": json.dumps(list(roles or [])),
            "tenant_id": tenant_id or "",
            "session_id": session,
            "current_hash": token_hash,
            "previous_hash": "",
            "rotated_at": "",
            "device_metadata": json.dumps(device_metadata or {}),
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "revoked": "0",
            "revocation_reason": "",
        }
        ttl = max(1, int((expires_at - datetime.now(timezone.utc)).total_seconds()))

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(self._key("family", family_id), mapping=record)
            pipe.set(self._key("famidx", token_hash), family_id, ex=ttl + 86400)
            pipe.sadd(self._key("famsess", session), family_id)
            pipe.expire(self._key("family", family_id), ttl + 86400)
            pipe.expire(self._key("famsess", session), ttl + 86400)
            await pipe.execute()

    async def get_refresh_family(self, token_hash: str) -> dict[str, Any] | None:
        """Look up a refresh family by credential hash (current or previous)."""
        family_id = await self.redis.get(self._key("famidx", token_hash))
        if not family_id:
            return None
        if isinstance(family_id, bytes):
            family_id = family_id.decode()
        data = await self.redis.hgetall(self._key("family", family_id))
        if not data:
            return None

        def _get(key: str) -> Any:
            raw = data.get(key, data.get(key.encode(), b""))
            return raw.decode() if isinstance(raw, bytes) else raw

        return {
            "family_id": family_id,
            "identity_id": _get("identity_id"),
            "scopes": json.loads(_get("scopes") or "[]"),
            "roles": json.loads(_get("roles") or "[]"),
            "tenant_id": _get("tenant_id") or None,
            "session_id": _get("session_id") or None,
            "current_hash": _get("current_hash"),
            "previous_hash": _get("previous_hash") or None,
            "rotated_at": _get("rotated_at") or None,
            "device_metadata": json.loads(_get("device_metadata") or "{}"),
            "expires_at": _get("expires_at"),
            "created_at": _get("created_at"),
            "revoked": _get("revoked") == "1",
            "revocation_reason": _get("revocation_reason") or None,
        }

    async def rotate_refresh_family(
        self,
        token_hash: str,
        new_hash: str,
        *,
        expires_at: datetime,
    ) -> dict[str, Any] | None:
        """
        Atomically rotate a family's credential via a server-side Lua script.

        The compare-and-set runs inside Redis, so two concurrent refreshes
        with the same credential are serialized: exactly one wins, the loser
        observes the rotated-away hash and triggers family revocation.
        """
        family_id = await self.redis.get(self._key("famidx", token_hash))
        if not family_id:
            return None
        if isinstance(family_id, bytes):
            family_id = family_id.decode()

        now = datetime.now(timezone.utc).isoformat()
        result = await self.redis.eval(
            self._ROTATE_LUA,
            3,
            self._key("family", family_id),
            self._key("famidx", token_hash),
            self._key("famidx", new_hash),
            new_hash,
            expires_at.isoformat(),
            now,
            token_hash,
        )
        status = result[1].decode() if isinstance(result[1], bytes) else result[1]
        if status == "unknown":
            return None

        family = await self.get_refresh_family(new_hash if status == "ok" else token_hash)
        if family is None:
            # Family record vanished between the CAS and the read.
            return None
        if status == "reuse":
            family["reuse"] = True
        return family

    async def revoke_refresh_family(self, session_id: str, reason: str = "revoked") -> None:
        """Revoke every credential in a session family."""
        family_ids = await self.redis.smembers(self._key("famsess", session_id))
        if not family_ids:
            return
        async with self.redis.pipeline(transaction=True) as pipe:
            for raw in family_ids:
                fid = raw.decode() if isinstance(raw, bytes) else raw
                pipe.hset(self._key("family", fid), mapping={"revoked": "1", "revocation_reason": reason})
            await pipe.execute()


# ============================================================================
# Authorization Code Store (for OAuth2)
# ============================================================================


class MemoryAuthorizationCodeStore:
    """In-memory authorization code storage for OAuth2 flows."""

    def __init__(self):
        self._codes: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def save_code(
        self,
        code: str,
        client_id: str,
        identity_id: str,
        redirect_uri: str,
        scopes: list[str],
        expires_at: datetime,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> None:
        """Save authorization code."""
        async with self._lock:
            self._codes[code] = {
                "client_id": client_id,
                "identity_id": identity_id,
                "redirect_uri": redirect_uri,
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "used": False,
            }

    async def get_code(self, code: str) -> dict[str, Any] | None:
        """Get authorization code data."""
        return self._codes.get(code)

    async def consume_code(self, code: str) -> bool:
        """Mark code as used (one-time use)."""
        async with self._lock:
            if code in self._codes and not self._codes[code]["used"]:
                self._codes[code]["used"] = True
                return True
            return False

    async def cleanup_expired(self) -> int:
        """Remove expired codes."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            expired = []

            for code, data in self._codes.items():
                expires_at = datetime.fromisoformat(data["expires_at"])
                if expires_at < now or data["used"]:
                    expired.append(code)

            for code in expired:
                del self._codes[code]

            return len(expired)


# ============================================================================
# Device Code Store (for device flow)
# ============================================================================


class MemoryDeviceCodeStore:
    """In-memory device code storage for device authorization flow."""

    def __init__(self):
        self._codes: dict[str, dict[str, Any]] = {}
        self._user_codes: dict[str, str] = {}  # user_code -> device_code
        self._lock = asyncio.Lock()

    async def save_device_code(
        self,
        device_code: str,
        user_code: str,
        client_id: str,
        scopes: list[str],
        expires_at: datetime,
    ) -> None:
        """Save device code."""
        async with self._lock:
            self._codes[device_code] = {
                "user_code": user_code,
                "client_id": client_id,
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
                "identity_id": None,  # Set when user authorizes
                "status": "pending",  # pending, authorized, denied
            }
            self._user_codes[user_code] = device_code

    async def get_by_device_code(self, device_code: str) -> dict[str, Any] | None:
        """Get device code data."""
        return self._codes.get(device_code)

    async def get_by_user_code(self, user_code: str) -> dict[str, Any] | None:
        """Get device code data by user code."""
        device_code = self._user_codes.get(user_code)
        if device_code:
            return self._codes.get(device_code)
        return None

    async def authorize_device_code(self, user_code: str, identity_id: str) -> bool:
        """Authorize device code (user approved)."""
        async with self._lock:
            device_code = self._user_codes.get(user_code)
            if device_code and device_code in self._codes:
                self._codes[device_code]["identity_id"] = identity_id
                self._codes[device_code]["status"] = "authorized"
                return True
            return False

    async def deny_device_code(self, user_code: str) -> bool:
        """Deny device code (user rejected)."""
        async with self._lock:
            device_code = self._user_codes.get(user_code)
            if device_code and device_code in self._codes:
                self._codes[device_code]["status"] = "denied"
                return True
            return False
