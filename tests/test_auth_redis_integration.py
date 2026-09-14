"""Live-Redis integration: rotating tokens and the Redis session store.

Runs against a real Redis when one is reachable (dev Redis on :6379 or the
AniWave dev Redis on :6380); otherwise every test skips. These verify the
Redis-specific machinery that unit fakes cannot: the Lua CAS rotation script
and the session store's key layout / TTL behavior.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from aquilia.auth.faults import AUTH_TOKEN_INVALID, AUTH_TOKEN_REVOKED
from aquilia.auth.stores import RedisTokenStore
from aquilia.auth.tokens import (
    KeyDescriptor,
    KeyRing,
    TokenConfig,
    TokenManager,
    hash_token,
)
from aquilia.sessions.core import Session
from aquilia.sessions.store import RedisStore

REDIS_URL_CANDIDATES = ("redis://localhost:6380/15", "redis://localhost:6379/15")

# Cache keyed by event loop: redis-py clients bind to the loop they were
# created on, and pytest-asyncio gives each test a fresh loop (the shared
# :memory: footgun's cousin — see aquilia-repo-environment notes).
_clients_by_loop: dict[int, Any] = {}
_unavailable = False


async def _redis():
    global _unavailable
    loop = asyncio.get_running_loop()
    if loop.__hash__ and id(loop) in _clients_by_loop:
        return _clients_by_loop[id(loop)]
    if _unavailable:
        return None
    import redis.asyncio as aioredis

    for url in REDIS_URL_CANDIDATES:
        try:
            client = aioredis.from_url(url, decode_responses=False)
            await asyncio.wait_for(client.ping(), timeout=0.5)
            # Isolate: flush only the dedicated test DB.
            await client.flushdb()
            _clients_by_loop[id(loop)] = client
            return client
        except Exception:
            continue
    _unavailable = True
    return None


def _manager(store, **overrides) -> TokenManager:
    ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="r" * 32)])
    config = TokenConfig(access_token_ttl=600, refresh_token_ttl=3600, **overrides)
    return TokenManager(key_ring=ring, token_store=store, config=config)


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
class TestRedisTokenRotation:
    async def test_rotation_and_reuse_detection(self):
        redis = await _redis()
        if redis is None:
            pytest.skip("no local Redis")

        store = RedisTokenStore(redis, key_prefix="t:rot:")
        manager = _manager(store)

        rt1 = await manager.issue_refresh_token("u1", scopes=[], session_id="redis-s1")
        _, rt2 = await manager.refresh_access_token(rt1)

        # Replay → reuse detected, family revoked.
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt1)
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt2)

    async def test_lua_cas_single_winner_under_concurrency(self):
        redis = await _redis()
        if redis is None:
            pytest.skip("no local Redis")

        store = RedisTokenStore(redis, key_prefix="t:race:")
        manager = _manager(store)
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="redis-race")

        results = await asyncio.gather(
            *[manager.refresh_access_token(rt) for _ in range(8)],
            return_exceptions=True,
        )
        winners = [r for r in results if not isinstance(r, Exception)]
        assert len(winners) == 1

    async def test_revocation_by_session(self):
        redis = await _redis()
        if redis is None:
            pytest.skip("no local Redis")

        store = RedisTokenStore(redis, key_prefix="t:revoke:")
        manager = _manager(store)
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="redis-kill")
        await manager.revoke_tokens_by_session("redis-kill")
        with pytest.raises((AUTH_TOKEN_REVOKED, AUTH_TOKEN_INVALID)):
            await manager.refresh_access_token(rt)

    async def test_is_token_revoked_sees_family_revocation(self):
        redis = await _redis()
        if redis is None:
            pytest.skip("no local Redis")

        store = RedisTokenStore(redis, key_prefix="t:flag:")
        manager = _manager(store)
        rt = await manager.issue_refresh_token("u1", scopes=[], session_id="redis-flag")
        _, rt2 = await manager.refresh_access_token(rt)
        # Replaying rt revokes the family…
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.refresh_access_token(rt)
        # …so the WINNER's token also reports revoked.
        assert await store.is_token_revoked(rt2) is True


@pytest.mark.asyncio
class TestRedisSessionStore:
    async def _store(self):
        redis = await _redis()
        if redis is None:
            pytest.skip("no local Redis")
        return RedisStore(redis, key_prefix="t:sess:")

    @staticmethod
    def _session(**overrides) -> Session:
        from aquilia.sessions.core import SessionID, SessionScope

        now = datetime.now(timezone.utc)
        base = dict(
            id=SessionID(),
            created_at=now,
            last_accessed_at=now,
            expires_at=now + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        base.update(overrides)
        return Session(**base)

    async def test_save_load_round_trip(self):
        store = await self._store()
        session = self._session()
        await store.save(session)

        loaded = await store.load(session.id)
        assert loaded is not None
        assert loaded.id == session.id

    async def test_delete_and_exists(self):
        store = await self._store()
        session = self._session()
        await store.save(session)
        assert await store.exists(session.id) is True
        await store.delete(session.id)
        assert await store.exists(session.id) is False
        assert await store.load(session.id) is None

    async def test_missing_session_returns_none(self):
        store = await self._store()
        assert await store.load("sess_does_not_exist") is None

    async def test_redis_ttl_set_on_save(self):
        """Redis owns expiry — the key carries a TTL close to the session's."""
        store = await self._store()
        session = self._session()
        await store.save(session)
        ttl = await store.redis.ttl(f"{store.prefix}sess:{session.id}")
        assert 0 < ttl <= 3600
