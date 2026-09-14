"""
AquilAuth — Durable Database Stores

SQL-backed implementations of the auth store protocols, built on the
framework's native :class:`~aquilia.db.engine.AquilaDatabase` layer
(SQLite / PostgreSQL / MySQL — portable ``?`` placeholders, backend-adapted).

Ships the durability the memory stores lack (AG-06: every restart used to
lose all identities and credentials in the enforced path):

* :class:`DatabaseIdentityStore` — :class:`~aquilia.auth.core.IdentityStore`
* :class:`DatabaseCredentialStore` — :class:`~aquilia.auth.core.CredentialStore`
  (passwords, API keys, MFA credentials)
* :class:`DatabaseTokenStore` — :class:`~aquilia.auth.tokens.TokenStore`
  **and** the :class:`~aquilia.auth.tokens.RotatingTokenStore` rotation
  protocol, with compare-and-set rotation enforced by the database itself
  (``UPDATE ... WHERE current_hash = ?`` rowcount decides the winner), so
  refresh rotation with reuse detection is race-safe across processes.

Schemas are auto-created on first use (``auto_create=True``, the default) —
plain tables with JSON columns for flexible attributes, plus an attribute
index table for ``get_by_attribute`` lookups. Point the store at your
application database or a dedicated one::

    from aquilia.db import AquiliaDatabase
    from aquilia.auth.stores_db import DatabaseIdentityStore, DatabaseCredentialStore

    db = AquiliaDatabase("postgresql://user:pass@host/auth")
    identities = DatabaseIdentityStore(db)
    credentials = DatabaseCredentialStore(db)

    # Or via config:
    #   class auth(AquilaConfig.Auth):
    #       store_type = "database"            # uses the app database
    #       # identity_store = {"type": "database", "url": "sqlite:///auth.db"}

Rows are serialized as JSON strings in TEXT columns — identical semantics on
every backend, no backend-specific JSON types required.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from aquilia.auth.core import (
    ApiKeyCredential,
    CredentialStatus,
    Identity,
    IdentityStatus,
    IdentityType,
    MFACredential,
    PasswordCredential,
)
from aquilia.faults.domains import ConflictFault

if TYPE_CHECKING:
    from aquilia.db.engine import AquiliaDatabase


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class DatabaseIdentityStore:
    """
    Durable identity storage on any Aquilia-supported database.

    Implements the full :class:`~aquilia.auth.core.IdentityStore` protocol
    with the same semantics as :class:`~aquilia.auth.stores.MemoryIdentityStore`
    (conflict on duplicate create, soft delete, attribute indexing).
    """

    def __init__(
        self,
        database: AquiliaDatabase,
        *,
        table: str = "aquilia_auth_identities",
        attr_table: str = "aquilia_auth_identity_attrs",
        auto_create: bool = True,
    ) -> None:
        self.db = database
        self.table = table
        self.attr_table = attr_table
        self._created = False
        self._auto_create = auto_create

    async def _ensure_schema(self) -> None:
        if self._created or not self._auto_create:
            return
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                tenant_id TEXT,
                attributes TEXT NOT NULL DEFAULT '{{}}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """.strip()
        )
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.attr_table} (
                attr_key TEXT NOT NULL,
                attr_value TEXT NOT NULL,
                identity_id TEXT NOT NULL,
                PRIMARY KEY (attr_key, attr_value, identity_id)
            )
            """.strip()
        )
        await self.db.execute(
            f"CREATE INDEX IF NOT EXISTS ix_{self.attr_table}_kv ON {self.attr_table} (attr_key, attr_value)"
        )
        self._created = True

    def _row_to_identity(self, row: dict[str, Any]) -> Identity:
        return Identity(
            id=row["id"],
            type=IdentityType(row["type"]),
            status=IdentityStatus(row["status"]),
            tenant_id=row.get("tenant_id"),
            attributes=json.loads(row.get("attributes") or "{}"),
            created_at=_parse_dt(row.get("created_at")) or datetime.now(timezone.utc),
            updated_at=_parse_dt(row.get("updated_at")) or datetime.now(timezone.utc),
        )

    async def _reindex_attributes(self, identity_id: str, attributes: dict[str, Any]) -> None:
        await self.db.execute(f"DELETE FROM {self.attr_table} WHERE identity_id = ?", [identity_id])
        rows = [
            (key, str(value), identity_id)
            for key, value in attributes.items()
            if isinstance(value, (str, int, bool))
        ]
        for key, value, ident in rows:
            await self.db.execute(
                f"INSERT OR IGNORE INTO {self.attr_table} (attr_key, attr_value, identity_id) VALUES (?, ?, ?)",
                [key, value, ident],
            )

    async def create(self, identity: Identity) -> Identity:
        await self._ensure_schema()
        existing = await self.db.fetch_one(f"SELECT id FROM {self.table} WHERE id = ?", [identity.id])
        if existing:
            raise ConflictFault(detail=f"Identity {identity.id} already exists")
        await self.db.execute(
            f"""
            INSERT INTO {self.table} (id, type, status, tenant_id, attributes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """.strip(),
            [
                identity.id,
                identity.type.value,
                identity.status.value,
                identity.tenant_id,
                json.dumps(identity.attributes),
                identity.created_at.isoformat(),
                identity.updated_at.isoformat(),
            ],
        )
        await self._reindex_attributes(identity.id, identity.attributes)
        return identity

    async def get(self, identity_id: str) -> Identity | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(f"SELECT * FROM {self.table} WHERE id = ?", [identity_id])
        return self._row_to_identity(row) if row else None

    async def get_by_attribute(self, attribute: str, value: Any) -> Identity | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(
            f"""
            SELECT i.* FROM {self.table} i
            JOIN {self.attr_table} a ON a.identity_id = i.id
            WHERE a.attr_key = ? AND a.attr_value = ?
              AND i.status != 'deleted'
            LIMIT 1
            """.strip(),
            [attribute, str(value)],
        )
        return self._row_to_identity(row) if row else None

    async def update(self, identity: Identity) -> Identity:
        await self._ensure_schema()
        existing = await self.db.fetch_one(f"SELECT id FROM {self.table} WHERE id = ?", [identity.id])
        if not existing:
            from aquilia.faults.domains import NotFoundFault

            raise NotFoundFault(detail=f"Identity {identity.id} not found")
        await self.db.execute(
            f"""
            UPDATE {self.table}
            SET type = ?, status = ?, tenant_id = ?, attributes = ?, updated_at = ?
            WHERE id = ?
            """.strip(),
            [
                identity.type.value,
                identity.status.value,
                identity.tenant_id,
                json.dumps(identity.attributes),
                identity.updated_at.isoformat(),
                identity.id,
            ],
        )
        await self._reindex_attributes(identity.id, identity.attributes)
        return identity

    async def delete(self, identity_id: str) -> bool:
        """Soft delete (status → deleted), mirroring the memory store."""
        await self._ensure_schema()
        existing = await self.db.fetch_one(f"SELECT id FROM {self.table} WHERE id = ?", [identity_id])
        if not existing:
            return False
        await self.db.execute(
            f"UPDATE {self.table} SET status = 'deleted', updated_at = ? WHERE id = ?",
            [_now(), identity_id],
        )
        return True

    async def list_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[Identity]:
        await self._ensure_schema()
        rows = await self.db.fetch_all(
            f"""
            SELECT * FROM {self.table}
            WHERE tenant_id = ? AND status != 'deleted'
            ORDER BY created_at
            LIMIT ? OFFSET ?
            """.strip(),
            [tenant_id, limit, offset],
        )
        return [self._row_to_identity(r) for r in rows]


class DatabaseCredentialStore:
    """
    Durable credential storage (passwords, API keys, MFA) on any
    Aquilia-supported database.

    Mirrors :class:`~aquilia.auth.stores.MemoryCredentialStore` semantics:
    upsert-style saves, conflict on duplicate API-key create, soft revoke,
    one MFA credential per (identity, type).
    """

    def __init__(
        self,
        database: AquiliaDatabase,
        *,
        password_table: str = "aquilia_auth_passwords",
        api_key_table: str = "aquilia_auth_api_keys",
        mfa_table: str = "aquilia_auth_mfa",
        auto_create: bool = True,
    ) -> None:
        self.db = database
        self.password_table = password_table
        self.api_key_table = api_key_table
        self.mfa_table = mfa_table
        self._created = False
        self._auto_create = auto_create

    async def _ensure_schema(self) -> None:
        if self._created or not self._auto_create:
            return
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.password_table} (
                identity_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                algorithm TEXT NOT NULL DEFAULT 'argon2id',
                created_at TEXT NOT NULL,
                last_changed_at TEXT NOT NULL,
                last_used_at TEXT,
                must_change INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """.strip()
        )
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.api_key_table} (
                key_id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                scopes TEXT NOT NULL DEFAULT '[]',
                rate_limit INTEGER,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                metadata TEXT NOT NULL DEFAULT '{{}}'
            )
            """.strip()
        )
        await self.db.execute(
            f"CREATE INDEX IF NOT EXISTS ix_{self.api_key_table}_identity ON {self.api_key_table} (identity_id)"
        )
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.mfa_table} (
                identity_id TEXT NOT NULL,
                mfa_type TEXT NOT NULL,
                mfa_secret TEXT,
                backup_codes TEXT NOT NULL DEFAULT '[]',
                webauthn_credentials TEXT NOT NULL DEFAULT '[]',
                phone_number TEXT,
                email TEXT,
                created_at TEXT NOT NULL,
                verified_at TEXT,
                last_used_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                PRIMARY KEY (identity_id, mfa_type)
            )
            """.strip()
        )
        self._created = True

    # ── Passwords ────────────────────────────────────────────────────────

    async def save_password(self, credential: PasswordCredential) -> None:
        await self._ensure_schema()
        await self.db.execute(
            f"""
            INSERT INTO {self.password_table}
                (identity_id, password_hash, algorithm, created_at, last_changed_at,
                 last_used_at, must_change, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(identity_id) DO UPDATE SET
                password_hash = excluded.password_hash,
                algorithm = excluded.algorithm,
                last_changed_at = excluded.last_changed_at,
                last_used_at = excluded.last_used_at,
                must_change = excluded.must_change,
                status = excluded.status
            """.strip(),
            [
                credential.identity_id,
                credential.password_hash,
                credential.algorithm,
                credential.created_at.isoformat(),
                credential.last_changed_at.isoformat(),
                credential.last_used_at.isoformat() if credential.last_used_at else None,
                1 if credential.must_change else 0,
                credential.status.value,
            ],
        )

    async def create_password(self, credential: PasswordCredential) -> None:
        await self.save_password(credential)

    async def update_password(self, credential: PasswordCredential) -> None:
        await self.save_password(credential)

    async def get_password(self, identity_id: str) -> PasswordCredential | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(
            f"SELECT * FROM {self.password_table} WHERE identity_id = ?", [identity_id]
        )
        if not row:
            return None
        return PasswordCredential(
            identity_id=row["identity_id"],
            password_hash=row["password_hash"],
            algorithm=row["algorithm"],
            created_at=_parse_dt(row["created_at"]) or datetime.now(timezone.utc),
            last_changed_at=_parse_dt(row["last_changed_at"]) or datetime.now(timezone.utc),
            last_used_at=_parse_dt(row.get("last_used_at")),
            must_change=bool(row.get("must_change")),
            status=CredentialStatus(row["status"]),
        )

    async def delete_password(self, identity_id: str) -> bool:
        await self._ensure_schema()
        cursor = await self.db.execute(
            f"DELETE FROM {self.password_table} WHERE identity_id = ?", [identity_id]
        )
        return bool(getattr(cursor, "rowcount", 0))

    # ── API keys ─────────────────────────────────────────────────────────

    async def save_api_key(self, credential: ApiKeyCredential) -> None:
        await self._ensure_schema()
        await self.db.execute(
            f"""
            INSERT INTO {self.api_key_table}
                (key_id, identity_id, key_hash, prefix, scopes, rate_limit, expires_at,
                 created_at, last_used_at, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key_id) DO UPDATE SET
                key_hash = excluded.key_hash,
                scopes = excluded.scopes,
                rate_limit = excluded.rate_limit,
                expires_at = excluded.expires_at,
                last_used_at = excluded.last_used_at,
                status = excluded.status,
                metadata = excluded.metadata
            """.strip(),
            [
                credential.key_id,
                credential.identity_id,
                credential.key_hash,
                credential.prefix,
                json.dumps(credential.scopes),
                credential.rate_limit,
                credential.expires_at.isoformat() if credential.expires_at else None,
                credential.created_at.isoformat(),
                credential.last_used_at.isoformat() if credential.last_used_at else None,
                credential.status.value,
                json.dumps(credential.metadata),
            ],
        )

    async def create_api_key(self, credential: ApiKeyCredential) -> None:
        await self._ensure_schema()
        existing = await self.db.fetch_one(
            f"SELECT key_id FROM {self.api_key_table} WHERE key_id = ?", [credential.key_id]
        )
        if existing:
            raise ConflictFault(detail=f"API key {credential.key_id} already exists")
        await self.save_api_key(credential)

    def _row_to_api_key(self, row: dict[str, Any]) -> ApiKeyCredential:
        return ApiKeyCredential(
            identity_id=row["identity_id"],
            key_id=row["key_id"],
            key_hash=row["key_hash"],
            prefix=row["prefix"],
            scopes=json.loads(row.get("scopes") or "[]"),
            rate_limit=row.get("rate_limit"),
            expires_at=_parse_dt(row.get("expires_at")),
            created_at=_parse_dt(row.get("created_at")) or datetime.now(timezone.utc),
            last_used_at=_parse_dt(row.get("last_used_at")),
            status=CredentialStatus(row["status"]),
            metadata=json.loads(row.get("metadata") or "{}"),
        )

    async def get_api_key(self, key_id: str) -> ApiKeyCredential | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(f"SELECT * FROM {self.api_key_table} WHERE key_id = ?", [key_id])
        return self._row_to_api_key(row) if row else None

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKeyCredential | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(
            f"SELECT * FROM {self.api_key_table} WHERE key_hash = ?", [key_hash]
        )
        return self._row_to_api_key(row) if row else None

    async def get_api_key_by_prefix(self, prefix: str) -> ApiKeyCredential | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(
            f"SELECT * FROM {self.api_key_table} WHERE prefix = ? LIMIT 1", [prefix]
        )
        return self._row_to_api_key(row) if row else None

    async def list_api_keys(self, identity_id: str) -> list[ApiKeyCredential]:
        await self._ensure_schema()
        rows = await self.db.fetch_all(
            f"SELECT * FROM {self.api_key_table} WHERE identity_id = ? ORDER BY created_at",
            [identity_id],
        )
        return [self._row_to_api_key(r) for r in rows]

    async def revoke_api_key(self, key_id: str) -> bool:
        await self._ensure_schema()
        cursor = await self.db.execute(
            f"UPDATE {self.api_key_table} SET status = 'revoked' WHERE key_id = ? AND status != 'revoked'",
            [key_id],
        )
        return bool(getattr(cursor, "rowcount", 0))

    async def delete_api_key(self, key_id: str) -> bool:
        await self._ensure_schema()
        cursor = await self.db.execute(f"DELETE FROM {self.api_key_table} WHERE key_id = ?", [key_id])
        return bool(getattr(cursor, "rowcount", 0))

    # ── MFA ──────────────────────────────────────────────────────────────

    async def save_mfa(self, credential: MFACredential) -> None:
        await self._ensure_schema()
        await self.db.execute(
            f"""
            INSERT INTO {self.mfa_table}
                (identity_id, mfa_type, mfa_secret, backup_codes, webauthn_credentials,
                 phone_number, email, created_at, verified_at, last_used_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(identity_id, mfa_type) DO UPDATE SET
                mfa_secret = excluded.mfa_secret,
                backup_codes = excluded.backup_codes,
                webauthn_credentials = excluded.webauthn_credentials,
                phone_number = excluded.phone_number,
                email = excluded.email,
                verified_at = excluded.verified_at,
                last_used_at = excluded.last_used_at,
                status = excluded.status
            """.strip(),
            [
                credential.identity_id,
                credential.mfa_type,
                credential.mfa_secret,
                json.dumps(credential.backup_codes),
                json.dumps(credential.webauthn_credentials),
                credential.phone_number,
                credential.email,
                credential.created_at.isoformat(),
                credential.verified_at.isoformat() if credential.verified_at else None,
                credential.last_used_at.isoformat() if credential.last_used_at else None,
                credential.status.value,
            ],
        )

    async def create_mfa(self, credential: MFACredential) -> None:
        await self.save_mfa(credential)

    async def update_mfa(self, credential: MFACredential) -> None:
        await self.save_mfa(credential)

    async def get_mfa(self, identity_id: str, mfa_type: str | None = None) -> list[MFACredential]:
        await self._ensure_schema()
        if mfa_type:
            rows = await self.db.fetch_all(
                f"SELECT * FROM {self.mfa_table} WHERE identity_id = ? AND mfa_type = ?",
                [identity_id, mfa_type],
            )
        else:
            rows = await self.db.fetch_all(
                f"SELECT * FROM {self.mfa_table} WHERE identity_id = ?", [identity_id]
            )
        return [
            MFACredential(
                identity_id=r["identity_id"],
                mfa_type=r["mfa_type"],
                mfa_secret=r.get("mfa_secret"),
                backup_codes=json.loads(r.get("backup_codes") or "[]"),
                webauthn_credentials=json.loads(r.get("webauthn_credentials") or "[]"),
                phone_number=r.get("phone_number"),
                email=r.get("email"),
                created_at=_parse_dt(r.get("created_at")) or datetime.now(timezone.utc),
                verified_at=_parse_dt(r.get("verified_at")),
                last_used_at=_parse_dt(r.get("last_used_at")),
                status=CredentialStatus(r["status"]),
            )
            for r in rows
        ]

    async def delete_mfa(self, identity_id: str, mfa_type: str | None = None) -> bool:
        await self._ensure_schema()
        if mfa_type:
            cursor = await self.db.execute(
                f"DELETE FROM {self.mfa_table} WHERE identity_id = ? AND mfa_type = ?",
                [identity_id, mfa_type],
            )
        else:
            cursor = await self.db.execute(
                f"DELETE FROM {self.mfa_table} WHERE identity_id = ?", [identity_id]
            )
        return bool(getattr(cursor, "rowcount", 0))


class DatabaseTokenStore:
    """
    Durable token storage implementing the base ``TokenStore`` protocol and
    the ``RotatingTokenStore`` rotation protocol.

    Rotation is a single conditional ``UPDATE ... WHERE current_hash = ?`` —
    the database serializes concurrent refreshes, so exactly one racer wins
    and the losers observe the rotated-away hash (reuse detection). Works
    across processes and restarts.
    """

    def __init__(
        self,
        database: AquiliaDatabase,
        *,
        token_table: str = "aquilia_auth_refresh_tokens",
        family_table: str = "aquilia_auth_refresh_families",
        revoked_table: str = "aquilia_auth_revoked",
        auto_create: bool = True,
    ) -> None:
        self.db = database
        self.token_table = token_table
        self.family_table = family_table
        self.revoked_table = revoked_table
        self._created = False
        self._auto_create = auto_create

    async def _ensure_schema(self) -> None:
        if self._created or not self._auto_create:
            return
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.token_table} (
                token_id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                scopes TEXT NOT NULL DEFAULT '[]',
                expires_at TEXT NOT NULL,
                session_id TEXT,
                roles TEXT NOT NULL DEFAULT '[]',
                tenant_id TEXT,
                created_at TEXT NOT NULL
            )
            """.strip()
        )
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.family_table} (
                family_id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                scopes TEXT NOT NULL DEFAULT '[]',
                roles TEXT NOT NULL DEFAULT '[]',
                tenant_id TEXT,
                session_id TEXT NOT NULL,
                current_hash TEXT NOT NULL UNIQUE,
                previous_hash TEXT,
                rotated_at TEXT,
                device_metadata TEXT NOT NULL DEFAULT '{{}}',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                revocation_reason TEXT
            )
            """.strip()
        )
        await self.db.execute(
            f"CREATE INDEX IF NOT EXISTS ix_{self.family_table}_session ON {self.family_table} (session_id)"
        )
        await self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.revoked_table} (
                token_id TEXT PRIMARY KEY,
                revoked_at TEXT NOT NULL
            )
            """.strip()
        )
        self._created = True

    # ── Base TokenStore protocol ─────────────────────────────────────────

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
        await self._ensure_schema()
        await self.db.execute(
            f"""
            INSERT OR REPLACE INTO {self.token_table}
                (token_id, identity_id, scopes, expires_at, session_id, roles, tenant_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """.strip(),
            [
                token_id,
                identity_id,
                json.dumps(scopes),
                expires_at.isoformat(),
                session_id,
                json.dumps(roles or []),
                tenant_id,
                _now(),
            ],
        )

    async def get_refresh_token(self, token_id: str) -> dict[str, Any] | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(f"SELECT * FROM {self.token_table} WHERE token_id = ?", [token_id])
        if not row:
            return None
        return {
            "identity_id": row["identity_id"],
            "scopes": json.loads(row.get("scopes") or "[]"),
            "expires_at": row["expires_at"],
            "session_id": row.get("session_id"),
            "roles": json.loads(row.get("roles") or "[]"),
            "tenant_id": row.get("tenant_id"),
        }

    async def revoke_refresh_token(self, token_id: str) -> None:
        await self._ensure_schema()
        await self.db.execute(
            f"INSERT OR IGNORE INTO {self.revoked_table} (token_id, revoked_at) VALUES (?, ?)",
            [token_id, _now()],
        )

    async def revoke_tokens_by_identity(self, identity_id: str) -> None:
        await self._ensure_schema()
        rows = await self.db.fetch_all(
            f"SELECT token_id FROM {self.token_table} WHERE identity_id = ?", [identity_id]
        )
        for row in rows:
            await self.revoke_refresh_token(row["token_id"])
        await self.db.execute(
            f"UPDATE {self.family_table} SET revoked = 1, revocation_reason = 'identity_revoked' WHERE identity_id = ?",
            [identity_id],
        )

    async def revoke_tokens_by_session(self, session_id: str) -> None:
        await self._ensure_schema()
        await self.revoke_refresh_family(session_id, reason="session_revoked")

    async def is_token_revoked(self, token_id: str) -> bool:
        await self._ensure_schema()
        row = await self.db.fetch_one(f"SELECT token_id FROM {self.revoked_table} WHERE token_id = ?", [token_id])
        return row is not None

    # ── RotatingTokenStore protocol ──────────────────────────────────────

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
        await self._ensure_schema()
        family_id = f"rf_{secrets.token_hex(16)}"
        await self.db.execute(
            f"""
            INSERT INTO {self.family_table}
                (family_id, identity_id, scopes, roles, tenant_id, session_id,
                 current_hash, previous_hash, rotated_at, device_metadata, expires_at,
                 created_at, revoked, revocation_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, 0, NULL)
            """.strip(),
            [
                family_id,
                identity_id,
                json.dumps(scopes),
                json.dumps(roles or []),
                tenant_id,
                session_id or family_id,
                token_hash,
                json.dumps(device_metadata or {}),
                expires_at.isoformat(),
                _now(),
            ],
        )

    def _row_to_family(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "family_id": row["family_id"],
            "identity_id": row["identity_id"],
            "scopes": json.loads(row.get("scopes") or "[]"),
            "roles": json.loads(row.get("roles") or "[]"),
            "tenant_id": row.get("tenant_id"),
            "session_id": row.get("session_id"),
            "current_hash": row.get("current_hash"),
            "previous_hash": row.get("previous_hash"),
            "rotated_at": row.get("rotated_at"),
            "device_metadata": json.loads(row.get("device_metadata") or "{}"),
            "expires_at": row.get("expires_at"),
            "created_at": row.get("created_at"),
            "revoked": bool(row.get("revoked")),
            "revocation_reason": row.get("revocation_reason"),
        }

    async def get_refresh_family(self, token_hash: str) -> dict[str, Any] | None:
        await self._ensure_schema()
        row = await self.db.fetch_one(
            f"""
            SELECT * FROM {self.family_table}
            WHERE current_hash = ? OR previous_hash = ?
            LIMIT 1
            """.strip(),
            [token_hash, token_hash],
        )
        return self._row_to_family(row) if row else None

    async def rotate_refresh_family(
        self,
        token_hash: str,
        new_hash: str,
        *,
        expires_at: datetime,
    ) -> dict[str, Any] | None:
        """
        Atomic compare-and-set rotation.

        The conditional UPDATE is the serialization point: among concurrent
        racers exactly one matches ``current_hash`` and wins; the rest match
        ``previous_hash`` (reuse → family revoked) or nothing (unknown).
        """
        await self._ensure_schema()

        # Fast rejection of unknown hashes.
        family = await self.get_refresh_family(token_hash)
        if family is None:
            return None

        if family.get("revoked"):
            return {"reuse": True, **family}

        if token_hash == family.get("current_hash"):
            cursor = await self.db.execute(
                f"""
                UPDATE {self.family_table}
                SET previous_hash = current_hash,
                    current_hash = ?,
                    rotated_at = ?,
                    expires_at = ?
                WHERE family_id = ? AND current_hash = ? AND revoked = 0
                """.strip(),
                [new_hash, _now(), expires_at.isoformat(), family["family_id"], token_hash],
            )
            if getattr(cursor, "rowcount", 0):
                refreshed = await self.get_refresh_family(new_hash)
                return refreshed or family
            # Lost the race — re-read to classify.
            refreshed = await self.get_refresh_family(token_hash)
            if refreshed is None:
                return None
            if token_hash == refreshed.get("current_hash"):
                return refreshed
            return {"reuse": True, **refreshed}

        if token_hash == family.get("previous_hash"):
            await self.db.execute(
                f"""
                UPDATE {self.family_table}
                SET revoked = 1, revocation_reason = 'reuse_detected'
                WHERE family_id = ? AND revoked = 0
                """.strip(),
                [family["family_id"]],
            )
            return {"reuse": True, **family}

        return None

    async def revoke_refresh_family(self, session_id: str, reason: str = "revoked") -> None:
        await self._ensure_schema()
        await self.db.execute(
            f"""
            UPDATE {self.family_table}
            SET revoked = 1, revocation_reason = ?
            WHERE session_id = ? AND revoked = 0
            """.strip(),
            [reason, session_id],
        )


__all__ = [
    "DatabaseIdentityStore",
    "DatabaseCredentialStore",
    "DatabaseTokenStore",
]
