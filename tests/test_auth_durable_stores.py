"""Durable stores and refresh-rotation adversarial scenarios.

Covers:

* **AG-05 / M-10** — refresh-token rotation with **reuse detection**: replay
  of a rotated-away credential revokes the whole session family; concurrent
  refresh races produce exactly one winner (CAS semantics).
* **AG-06** — durable identity/credential/token stores (database-backed);
  restart persistence; persistence across store instances sharing a DB.
* The ``RotatingTokenStore`` protocol across all three store families
  (memory, SQL; Redis is covered structurally by the same protocol).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from aquilia.auth.core import (
    ApiKeyCredential,
    Identity,
    IdentityStatus,
    IdentityType,
    MFACredential,
    PasswordCredential,
)
from aquilia.auth.faults import AUTH_TOKEN_INVALID, AUTH_TOKEN_REVOKED
from aquilia.auth.stores import MemoryTokenStore
from aquilia.auth.stores_db import (
    DatabaseCredentialStore,
    DatabaseIdentityStore,
    DatabaseTokenStore,
)
from aquilia.auth.tokens import (
    KeyDescriptor,
    KeyRing,
    TokenConfig,
    TokenManager,
    hash_token,
)
from aquilia.db.engine import AquiliaDatabase


def _manager(store, **overrides) -> TokenManager:
    ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="d" * 32)])
    config = TokenConfig(access_token_ttl=600, refresh_token_ttl=3600, **overrides)
    return TokenManager(key_ring=ring, token_store=store, config=config)


# ============================================================================
# Rotation + reuse detection — memory store
# ============================================================================


class TestRotationMemory:
    async def test_rotation_issues_new_pair(self):
        manager = _manager(MemoryTokenStore())
        rt1 = await manager.issue_refresh_token("u1", scopes=["read"], session_id="s1")
        access, rt2 = await manager.refresh_access_token(rt1)
        assert access
        assert rt2 != rt1

    async def test_reuse_of_rotated_token_revokes_family(self):
        manager = _manager(MemoryTokenStore())
        rt1 = await manager.issue_refresh_token("u1", scopes=[], session_id="s1")
        _, rt2 = await manager.refresh_access_token(rt1)

        # Replay the rotated-away credential.
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt1)

        # The whole family is dead: the winner's token too.
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt2)

    async def test_unknown_token_invalid(self):
        manager = _manager(MemoryTokenStore())
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.refresh_access_token("rt_totally_unknown")

    async def test_concurrent_refresh_exactly_one_winner(self):
        """The AG-05 race: N concurrent refreshes of one credential — exactly
        one rotation may win; the losers must fail closed (never corrupt)."""
        for _ in range(5):  # repeat: races are probabilistic
            manager = _manager(MemoryTokenStore())
            rt = await manager.issue_refresh_token("u1", scopes=[], session_id="race")
            results = await asyncio.gather(
                *[manager.refresh_access_token(rt) for _ in range(8)],
                return_exceptions=True,
            )
            winners = [r for r in results if not isinstance(r, Exception)]
            assert len(winners) == 1, f"expected exactly 1 winner, got {len(winners)}"
            # Store invariants: exactly one current hash, one previous.
            store = manager.token_store
            families = [f for f in store._families.values() if f["session_id"] == "race"]
            assert len(families) == 1

    async def test_multi_step_rotation_chain(self):
        manager = _manager(MemoryTokenStore())
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="chain")
        for i in range(10):
            access, rt = await manager.refresh_access_token(rt)
            assert access
        # Only the newest works; the immediately-previous one is reuse.
        _, newest = await manager.refresh_access_token(rt)
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt)

    async def test_session_scoped_revocation_kills_family(self):
        manager = _manager(MemoryTokenStore())
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="kill-me")
        await manager.revoke_tokens_by_session("kill-me")
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt)

    async def test_legacy_nonrotating_store_still_works(self):
        """A third-party TokenStore without the rotation protocol keeps the
        legacy behavior (revoke-old + issue-new)."""

        class LegacyStore:
            def __init__(self):
                self.tokens = {}
                self.revoked = set()

            async def save_refresh_token(self, token_id, identity_id, scopes, expires_at, **kw):
                self.tokens[token_id] = {"identity_id": identity_id, "scopes": scopes, "expires_at": expires_at.isoformat()}

            async def get_refresh_token(self, token_id):
                return self.tokens.get(token_id)

            async def revoke_refresh_token(self, token_id):
                self.revoked.add(token_id)

            async def revoke_tokens_by_identity(self, identity_id):
                for tid, data in self.tokens.items():
                    if data["identity_id"] == identity_id:
                        self.revoked.add(tid)

            async def revoke_tokens_by_session(self, session_id):
                pass

            async def is_token_revoked(self, token_id):
                return token_id in self.revoked

        manager = _manager(LegacyStore())
        rt = await manager.issue_refresh_token("u1", scopes=[])
        access, rt2 = await manager.refresh_access_token(rt)
        assert access and rt2 != rt
        # Old token revoked (legacy semantics: fails closed, no family concept)
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt)
        # New token works
        _, rt3 = await manager.refresh_access_token(rt2)
        assert rt3

    async def test_rotation_disabled_optout(self):
        manager = _manager(MemoryTokenStore(), refresh_rotation=False)
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="s")
        _, rt2 = await manager.refresh_access_token(rt)
        assert rt2 != rt

    async def test_device_metadata_persists_in_family(self):
        store = MemoryTokenStore()
        manager = _manager(store)
        device = {"user_agent": "iPhone", "ip": "10.0.0.1"}
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="s", device_metadata=device)
        family = await store.get_refresh_family(hash_token(rt))
        assert family["device_metadata"] == device


# ============================================================================
# Database stores — durability
# ============================================================================


@pytest.fixture
async def db(tmp_path):
    database = AquiliaDatabase(f"sqlite:///{tmp_path}/auth_test.sqlite3")
    await database.connect()
    yield database
    await database.disconnect()


class TestDatabaseIdentityStore:
    async def test_crud_round_trip(self, db):
        store = DatabaseIdentityStore(db)
        identity = Identity(
            id=str(uuid.uuid4()),
            type=IdentityType.USER,
            attributes={"email": "a@x.com", "roles": ["admin"], "nested": {"k": 1}},
        )
        created = await store.create(identity)
        assert created.id == identity.id

        fetched = await store.get(identity.id)
        assert fetched.attributes == identity.attributes
        assert fetched.type == IdentityType.USER

        fetched.attributes["email"] = "b@x.com"
        await store.update(fetched)
        assert (await store.get(identity.id)).attributes["email"] == "b@x.com"

        assert await store.delete(identity.id) is True
        assert (await store.get(identity.id)).status == IdentityStatus.DELETED

    async def test_duplicate_create_conflicts(self, db):
        store = DatabaseIdentityStore(db)
        identity = Identity(id="dup-1", type=IdentityType.USER, attributes={})
        await store.create(identity)
        from aquilia.faults.domains import ConflictFault

        with pytest.raises(ConflictFault):
            await store.create(identity)

    async def test_attribute_index_lookup(self, db):
        store = DatabaseIdentityStore(db)
        await store.create(Identity(id="u1", type=IdentityType.USER, attributes={"email": "one@x.com"}))
        await store.create(Identity(id="u2", type=IdentityType.USER, attributes={"email": "two@x.com"}))

        found = await store.get_by_attribute("email", "two@x.com")
        assert found is not None and found.id == "u2"
        assert await store.get_by_attribute("email", "nobody@x.com") is None

    async def test_persistence_across_store_instances(self, db):
        """The durability property (AG-06): a NEW store over the same DB sees
        everything the old one wrote — the restart-persistence scenario."""
        store_a = DatabaseIdentityStore(db)
        await store_a.create(Identity(id="survivor", type=IdentityType.USER, attributes={"email": "s@x.com"}))

        store_b = DatabaseIdentityStore(db)  # fresh instance, same DB
        assert (await store_b.get("survivor")).attributes["email"] == "s@x.com"
        assert (await store_b.get_by_attribute("email", "s@x.com")).id == "survivor"

    async def test_tenant_listing(self, db):
        store = DatabaseIdentityStore(db)
        for i in range(5):
            await store.create(
                Identity(id=f"t{i}", type=IdentityType.USER, attributes={}, tenant_id="acme")
            )
        rows = await store.list_by_tenant("acme")
        assert len(rows) == 5


class TestDatabaseCredentialStore:
    async def test_password_round_trip(self, db):
        store = DatabaseCredentialStore(db)
        cred = PasswordCredential(identity_id="u1", password_hash="$argon2id$fake")
        await store.save_password(cred)
        fetched = await store.get_password("u1")
        assert fetched.password_hash == cred.password_hash
        assert fetched.algorithm == "argon2id"

        await store.delete_password("u1")
        assert await store.get_password("u1") is None

    async def test_api_key_lifecycle(self, db):
        store = DatabaseCredentialStore(db)
        key = ApiKeyCredential(
            identity_id="u1",
            key_id="key_1",
            key_hash=ApiKeyCredential.hash_key("ak_live_secret"),
            prefix="ak_live_",
            scopes=["read"],
        )
        await store.create_api_key(key)

        assert (await store.get_api_key("key_1")).key_id == "key_1"
        assert (await store.get_api_key_by_hash(key.key_hash)).key_id == "key_1"

        from aquilia.faults.domains import ConflictFault

        with pytest.raises(ConflictFault):
            await store.create_api_key(key)

        assert await store.revoke_api_key("key_1") is True
        assert (await store.get_api_key("key_1")).status.value == "revoked"
        assert await store.revoke_api_key("key_1") is False  # already revoked

    async def test_mfa_round_trip(self, db):
        store = DatabaseCredentialStore(db)
        mfa = MFACredential(identity_id="u1", mfa_type="totp", mfa_secret="BASE32SECRET")
        await store.save_mfa(mfa)
        assert len(await store.get_mfa("u1")) == 1
        assert (await store.get_mfa("u1", "totp"))[0].mfa_secret == "BASE32SECRET"
        assert await store.delete_mfa("u1", "totp") is True
        assert await store.get_mfa("u1") == []


class TestDatabaseTokenStore:
    async def test_legacy_token_protocol(self, db):
        store = DatabaseTokenStore(db)
        await store.save_refresh_token(
            "rt_1", "u1", ["read"], datetime.now(timezone.utc) + timedelta(hours=1)
        )
        data = await store.get_refresh_token("rt_1")
        assert data["identity_id"] == "u1"
        await store.revoke_refresh_token("rt_1")
        assert await store.is_token_revoked("rt_1") is True

    async def test_rotation_reuse_and_family_revocation(self, db):
        store = DatabaseTokenStore(db)
        manager = _manager(store)

        rt1 = await manager.issue_refresh_token("u1", scopes=["read"], session_id="db-s1")
        _, rt2 = await manager.refresh_access_token(rt1)

        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt1)
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt2)

    async def test_concurrent_rotation_single_winner_sql_cas(self, db):
        """The SQL compare-and-set must serialize concurrent refreshes."""
        store = DatabaseTokenStore(db)
        manager = _manager(store)
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="db-race")

        results = await asyncio.gather(
            *[manager.refresh_access_token(rt) for _ in range(6)],
            return_exceptions=True,
        )
        winners = [r for r in results if not isinstance(r, Exception)]
        assert len(winners) == 1

    async def test_persistence_across_instances(self, db):
        """Rotation state survives a 'restart' (new store, same DB)."""
        store_a = DatabaseTokenStore(db)
        manager_a = _manager(store_a)
        rt = await manager_a.issue_refresh_token("u1", scopes=[], session_id="db-persist")

        # Simulate restart: fresh store + manager sharing the DB and keyring.
        store_b = DatabaseTokenStore(db)
        manager_b = _manager(store_b)
        access, rt2 = await manager_b.refresh_access_token(rt)
        assert access

        # …and the old token is now rotated-away in the durable state.
        with pytest.raises((AUTH_TOKEN_REVOKED, AUTH_TOKEN_INVALID)):
            await manager_b.refresh_access_token(rt)

    async def test_revocation_by_session_and_identity(self, db):
        store = DatabaseTokenStore(db)
        manager = _manager(store)
        rt_a = await manager.issue_refresh_token("u1", scopes=[], session_id="sess-a")
        rt_b = await manager.issue_refresh_token("u1", scopes=[], session_id="sess-b")

        await manager.revoke_tokens_by_session("sess-a")
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt_a)

        # Other session unaffected
        _, _ = await manager.refresh_access_token(rt_b)

        await manager.revoke_tokens_by_identity("u1")
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt_b)
