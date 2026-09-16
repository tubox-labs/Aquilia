"""
Regression tests for the cache subsystem forensic audit (v1.4.2).

Each test pins one confirmed finding (F-CA-xx / N-x) so the defect cannot
silently return.  Memory-backend tests need no Redis; Redis-dependent tests
run against the live dev Redis on 127.0.0.1:6379 (db 15 only, flushed
before and after) and skip when it is unreachable.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time

import pytest

from aquilia.cache import CacheConfig, CacheMiddleware, CacheService, CompositeBackend, MemoryBackend, RedisBackend
from aquilia.cache.core import CacheBackend
from aquilia.cache.decorators import _NONE_SENTINEL_LEGACY, cached, set_default_cache_service
from aquilia.cache.di_providers import build_cache_config, create_cache_backend, create_cache_service
from aquilia.cache.key_builder import call_signature
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.faults.engine import get_default_engine
from aquilia.response import Response

REDIS_URL = "redis://127.0.0.1:6379/15"


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


async def _live_client():
    """Flush db 15 and return a raw client; skip when Redis is unavailable."""
    try:
        import redis.asyncio as aioredis
    except (ImportError, ModuleNotFoundError):
        pytest.skip("redis package not installed")
    client = aioredis.from_url(REDIS_URL, decode_responses=False)
    try:
        await asyncio.wait_for(client.ping(), timeout=1.0)
    except Exception:
        await client.aclose()
        pytest.skip("live Redis not reachable at 127.0.0.1:6379")
    await client.flushdb()
    return client


async def _teardown(client, *owners):
    """Shut down backends/services, flush db 15, close the raw client."""
    for owner in owners:
        with contextlib.suppress(Exception):
            await owner.shutdown()
    with contextlib.suppress(Exception):
        await client.flushdb()
    with contextlib.suppress(Exception):
        await client.aclose()


class _Headers(dict):
    def get(self, key, default=""):
        return super().get(key.lower(), default)


class _Request:
    def __init__(self, path="/me", method="GET", headers=None):
        self.path = path
        self.method = method
        self.query_string = ""
        self.headers = _Headers({k.lower(): v for k, v in (headers or {}).items()})


def _handler(body: bytes, headers: dict | None = None):
    async def handler(_request, _ctx):
        return Response(content=body, status=200, headers=dict(headers or {}))

    return handler


class _ExplodingBackend(CacheBackend):
    """Backend whose every data operation raises, for never-raise pinning."""

    __slots__ = ()

    @property
    def name(self) -> str:
        return "exploding"

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def get(self, key: str):
        raise RuntimeError("boom-get")

    async def set(self, key: str, value, ttl=None, tags=(), namespace="default") -> None:
        raise RuntimeError("boom-set")

    async def delete(self, key: str) -> bool:
        raise RuntimeError("boom-delete")

    async def exists(self, key: str) -> bool:
        raise RuntimeError("boom-exists")

    async def clear(self, namespace: str | None = None) -> int:
        raise RuntimeError("boom-clear")

    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list:
        raise RuntimeError("boom-keys")

    async def stats(self):
        raise RuntimeError("boom-stats")


class _SpyBackend(CacheBackend):
    """
    Minimal backend delegating to memory, recording set() calls.

    Deliberately does NOT override ``set_many`` (exercises the base-class
    default) and does NOT define ``touch`` (exercises the service fallback).
    """

    __slots__ = ("_inner", "set_calls")

    def __init__(self):
        self._inner = MemoryBackend()
        self.set_calls: list[tuple] = []

    @property
    def name(self) -> str:
        return "spy"

    async def initialize(self) -> None:
        await self._inner.initialize()

    async def shutdown(self) -> None:
        await self._inner.shutdown()

    async def get(self, key: str):
        return await self._inner.get(key)

    async def set(self, key: str, value, ttl=None, tags=(), namespace="default") -> None:
        self.set_calls.append((key, value, ttl, tags, namespace))
        await self._inner.set(key, value, ttl=ttl, tags=tags, namespace=namespace)

    async def delete(self, key: str) -> bool:
        return await self._inner.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._inner.exists(key)

    async def clear(self, namespace: str | None = None) -> int:
        return await self._inner.clear(namespace)

    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list:
        return await self._inner.keys(pattern, namespace)

    async def stats(self):
        return await self._inner.stats()


class _LockBackend(MemoryBackend):
    """Memory L2 stand-in with cross-process lock semantics."""

    __slots__ = ("_held",)

    def __init__(self):
        super().__init__()
        self._held: dict[str, str] = {}

    @property
    def supports_distributed_lock(self) -> bool:
        return True

    async def try_acquire_lock(self, key: str, ttl: float) -> str | None:
        if key in self._held:
            return None
        self._held[key] = "token-1"
        return "token-1"

    async def release_lock(self, key: str, token: str) -> bool:
        if self._held.get(key) == token:
            del self._held[key]
            return True
        return False


class _StatsSpyBackend(MemoryBackend):
    """Memory backend counting stats() calls, to pin N-8."""

    __slots__ = ("stats_calls",)

    def __init__(self):
        super().__init__()
        self.stats_calls = 0

    async def stats(self):
        self.stats_calls += 1
        return await super().stats()


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-01 — get_or_set cannot cache None
# ═══════════════════════════════════════════════════════════════════════════


class TestGetOrSetNone:
    @pytest.mark.asyncio
    async def test_f_ca_01_cached_none_is_a_hit(self):
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        calls = {"n": 0}

        async def loader():
            calls["n"] += 1
            return None

        assert await service.get_or_set("k", loader, ttl=60) is None
        assert await service.get_or_set("k", loader, ttl=60) is None
        assert calls["n"] == 1  # second call served from cache, not recomputed

    @pytest.mark.asyncio
    async def test_f_ca_01_concurrent_none_loaders_compute_once(self):
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False, stampede_timeout=5))
        calls = {"n": 0}

        async def loader():
            calls["n"] += 1
            await asyncio.sleep(0.02)
            return None

        results = await asyncio.gather(*(service.get_or_set("k", loader, ttl=60) for _ in range(5)))
        assert results == [None] * 5
        assert calls["n"] == 1

    @pytest.mark.asyncio
    async def test_f_ca_01_await_peer_value_returns_cached_none_without_stalling(self):
        """Joiners must not stall the full stampede timeout on a cached None."""
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            service = CacheService(
                backend,
                CacheConfig(stampede_timeout=2.0, stampede_poll_interval=0.01, ttl_jitter=False),
            )
            full_key = service.key_builder.build("default", "peer:none", service.key_prefix)
            await backend.set(full_key, None, ttl=60)

            started = time.monotonic()
            entry = await service._await_peer_value(full_key)
            elapsed = time.monotonic() - started

            assert entry is not None and entry.value is None
            assert elapsed < 1.5  # returned on first poll, not after the 2s timeout
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-02 — fault emission was dead code
# ═══════════════════════════════════════════════════════════════════════════


class TestFaultEmission:
    @pytest.mark.asyncio
    async def test_f_ca_02_backend_fault_reaches_default_engine(self):
        engine = get_default_engine()
        seen: list[str] = []
        engine.on_fault(lambda ctx: seen.append(ctx.fault.code))

        service = CacheService(_ExplodingBackend(), CacheConfig(ttl_jitter=False))

        # Never-raise contract holds...
        assert await service.get("k") is None
        assert await service.get("k", default="fallback") == "fallback"

        # ...and the failure is actually emitted through the real engine API.
        for _ in range(5):
            await asyncio.sleep(0)  # let the best-effort emission task run
        assert "CACHE_BACKEND_ERROR" in seen


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-03 — l1_ttl never reached the memory backend
# ═══════════════════════════════════════════════════════════════════════════


class TestL1TtlWiring:
    @pytest.mark.asyncio
    async def test_f_ca_03_memory_backend_default_ttl_bounds_unset_writes(self):
        backend = MemoryBackend(default_ttl=20)
        await backend.set("k", "v")  # no explicit TTL
        entry = await backend.get("k")
        assert entry.ttl_remaining is not None and entry.ttl_remaining <= 20

    @pytest.mark.asyncio
    async def test_f_ca_03_composite_clamps_l1_on_set_but_not_l2(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2, l1_ttl=30)
        await composite.set("k", "v", ttl=300)

        assert (await l1.get("k")).ttl_remaining <= 30
        assert (await l2.get("k")).ttl_remaining > 200  # L2 keeps the full TTL

    @pytest.mark.asyncio
    async def test_f_ca_03_composite_clamps_l1_on_promotion(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2, l1_ttl=30)

        await l2.set("p", "v", ttl=300)
        assert (await composite.get("p")).value == "v"  # promotes into L1
        assert (await l1.get("p")).ttl_remaining <= 30

    @pytest.mark.asyncio
    async def test_f_ca_03_composite_bounds_unbounded_promotions(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2, l1_ttl=30)

        await l2.set("u", "v")  # no expiry in L2
        await composite.get("u")
        promoted = await l1.get("u")
        assert promoted.ttl_remaining is not None and promoted.ttl_remaining <= 30

    @pytest.mark.asyncio
    async def test_f_ca_03_composite_clamps_l1_on_set_many(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2, l1_ttl=30)
        await composite.set_many({"m": 1}, ttl=300)
        assert (await l1.get("m")).ttl_remaining <= 30

    @pytest.mark.asyncio
    async def test_f_ca_03_di_wires_l1_ttl_into_composite(self):
        composite = create_cache_backend(
            CacheConfig(backend="composite", l2_backend="memory", l1_ttl=45)
        )
        assert isinstance(composite, CompositeBackend)
        await composite.initialize()
        await composite.set("k", "v", ttl=300)
        # l1 is an internal detail, but this is the direct pin that
        # config.l1_ttl actually reached the L1 layer.
        assert (await composite._l1.get("k")).ttl_remaining <= 45
        await composite.shutdown()


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-04 — set_many dropped tags
# ═══════════════════════════════════════════════════════════════════════════


class TestSetManyTags:
    @pytest.mark.asyncio
    async def test_f_ca_04_base_backend_set_many_passes_tags(self):
        backend = _SpyBackend()
        await backend.set_many({"a": 1}, ttl=30, namespace="n", tags=("t",))
        assert backend.set_calls == [("a", 1, 30, ("t",), "n")]

    @pytest.mark.asyncio
    async def test_f_ca_04_memory_set_many_stores_tags(self):
        backend = MemoryBackend()
        await backend.set_many({"a": 1, "b": 2}, ttl=30, namespace="n", tags=("t",))
        entry = await backend.get("a")
        assert entry.tags == ("t",) and entry.namespace == "n"
        assert await backend.delete_by_tags({"t"}) == 2

    @pytest.mark.asyncio
    async def test_f_ca_04_service_set_many_accepts_tags(self):
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        await service.set_many({"a": 1, "b": 2}, ttl=30, tags=("group",))
        assert await service.invalidate_tags("group") == 2

    @pytest.mark.asyncio
    async def test_f_ca_04_redis_set_many_writes_meta_and_tag_sets(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            await backend.set_many({"a": 1, "b": 2}, ttl=60, namespace="ns1", tags=("t",))

            entry = await backend.get("a")
            assert entry.tags == ("t",) and entry.namespace == "ns1"
            assert await backend.delete_by_tags({"t"}) == 2
        finally:
            await _teardown(client, backend)

    @pytest.mark.asyncio
    async def test_f_ca_04_composite_set_many_carries_tags_to_both_levels(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2)
        await composite.set_many({"a": 1}, ttl=30, namespace="n", tags=("t",))
        assert (await l1.get("a")).tags == ("t",)
        assert (await l2.get("a")).tags == ("t",)


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-05 — CompositeBackend lacked distributed-lock delegation
# ═══════════════════════════════════════════════════════════════════════════


class TestCompositeLockDelegation:
    @pytest.mark.asyncio
    async def test_f_ca_05_lock_capability_and_ops_delegate_to_l2(self):
        lock_l2 = _LockBackend()
        composite = CompositeBackend(MemoryBackend(), lock_l2)

        assert composite.supports_distributed_lock is True
        token = await composite.try_acquire_lock("lock:k", 5.0)
        assert token == "token-1"
        assert await composite.try_acquire_lock("lock:k", 5.0) is None  # held
        assert await composite.release_lock("lock:k", token) is True
        assert await composite.try_acquire_lock("lock:k", 5.0) == "token-1"

    @pytest.mark.asyncio
    async def test_f_ca_05_in_process_l2_reports_no_distributed_lock(self):
        composite = CompositeBackend(MemoryBackend(), MemoryBackend())
        assert composite.supports_distributed_lock is False

    @pytest.mark.asyncio
    async def test_f_ca_05_redis_l2_lock_visible_through_composite(self):
        client = await _live_client()
        l2 = RedisBackend(url=REDIS_URL, key_prefix="")
        composite = CompositeBackend(MemoryBackend(), l2)
        try:
            await composite.initialize()
            assert composite.supports_distributed_lock is True
            token = await composite.try_acquire_lock("lock:delegated", 5.0)
            assert token is not None
            assert await composite.try_acquire_lock("lock:delegated", 5.0) is None
            assert await composite.release_lock("lock:delegated", token) is True
        finally:
            await _teardown(client, composite)


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-06 — touch was get+set, losing tags
# ═══════════════════════════════════════════════════════════════════════════


class TestTouch:
    @pytest.mark.asyncio
    async def test_f_ca_06_memory_touch_preserves_value_tags_and_namespace(self):
        backend = MemoryBackend()
        await backend.set("k", "v", ttl=5, tags=("t",), namespace="n")
        assert await backend.touch("k", 300) is True
        entry = await backend.get("k")
        assert entry.value == "v"
        assert entry.tags == ("t",) and entry.namespace == "n"
        assert entry.ttl_remaining > 250

    @pytest.mark.asyncio
    async def test_f_ca_06_memory_touch_missing_key_returns_false(self):
        assert await MemoryBackend().touch("nope", 10) is False

    @pytest.mark.asyncio
    async def test_f_ca_06_redis_touch_is_atomic_and_preserves_meta(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            await backend.set("k", {"v": 1}, ttl=10, tags=("t",), namespace="n")

            assert await backend.touch("k", 300) is True
            entry = await backend.get("k")
            assert entry.value == {"v": 1}
            assert entry.tags == ("t",) and entry.namespace == "n"
            assert entry.ttl_remaining > 250

            assert await backend.touch("missing", 60) is False
        finally:
            await _teardown(client, backend)

    @pytest.mark.asyncio
    async def test_f_ca_06_composite_touch_refreshes_both_levels(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2)
        await composite.set("k", "v", ttl=5, tags=("t",))
        assert await composite.touch("k", 300) is True
        assert (await l1.get("k")).ttl_remaining > 250
        assert (await l2.get("k")).ttl_remaining > 250

    @pytest.mark.asyncio
    async def test_f_ca_06_service_touch_uses_backend_atomic_path(self):
        backend = MemoryBackend()
        service = CacheService(backend, CacheConfig(ttl_jitter=False))
        await service.set("k", "v", ttl=5, tags=("t",), namespace="ns")
        assert await service.touch("k", 300, namespace="ns") is True

        full_key = service.key_builder.build("ns", "k", service.key_prefix)
        entry = await backend.get(full_key)
        assert entry.tags == ("t",) and entry.ttl_remaining > 250

    @pytest.mark.asyncio
    async def test_f_ca_06_service_touch_fallback_preserves_tags(self):
        """Custom backends without touch fall back to a tag-preserving re-set."""
        backend = _SpyBackend()
        service = CacheService(backend, CacheConfig(ttl_jitter=False))
        await service.set("k", "v", ttl=10, tags=("keep",), namespace="ns")
        backend.set_calls.clear()

        assert await service.touch("k", 120, namespace="ns") is True
        full_key = service.key_builder.build("ns", "k", service.key_prefix)
        assert backend.set_calls == [(full_key, "v", 120, ("keep",), "ns")]


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-06r — CompositeBackend.increment L1 race
# ═══════════════════════════════════════════════════════════════════════════


class TestCompositeIncrementRace:
    @pytest.mark.asyncio
    async def test_f_ca_06r_increment_invalidates_l1_and_reads_true_value(self):
        shared_l2 = MemoryBackend()
        c1 = CompositeBackend(MemoryBackend(), shared_l2)
        c2 = CompositeBackend(MemoryBackend(), shared_l2)

        await c1.set("n", 0, ttl=300)
        # Promote stale L1 copies in both composites.
        assert (await c1.get("n")).value == 0
        assert (await c2.get("n")).value == 0

        results = await asyncio.gather(
            *(c1.increment("n") for _ in range(10)),
            *(c2.increment("n") for _ in range(10)),
        )
        assert sorted(results) == list(range(1, 21))

        # Each composite must observe the authoritative L2 value, not a
        # stale L1 copy pinned to one caller's own increment result.
        assert (await c1.get("n")).value == 20
        assert (await c2.get("n")).value == 20

    @pytest.mark.asyncio
    async def test_f_ca_06r_increment_drops_the_l1_copy(self):
        l1, l2 = MemoryBackend(), MemoryBackend()
        composite = CompositeBackend(l1, l2)
        await composite.set("n", 5, ttl=300)
        await composite.get("n")  # promote
        assert await composite.increment("n") == 6
        assert await l1.get("n") is None  # invalidated, not refreshed with a racy value


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-07 — Redis get_many lost tags/namespace/ttl
# ═══════════════════════════════════════════════════════════════════════════


class TestRedisGetMany:
    @pytest.mark.asyncio
    async def test_f_ca_07_get_many_returns_full_entries(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            await backend.set("a", {"v": 1}, ttl=60, tags=("t",), namespace="ns1")
            await backend.set("b", [1, 2], ttl=60, namespace="ns1")

            entries = await backend.get_many(["a", "b", "missing"])
            assert entries["a"].value == {"v": 1}
            assert entries["a"].tags == ("t",)
            assert entries["a"].namespace == "ns1"
            assert entries["a"].expires_at is not None
            assert entries["b"].value == [1, 2]
            assert entries["b"].namespace == "ns1"
            assert entries["missing"] is None
        finally:
            await _teardown(client, backend)

    @pytest.mark.asyncio
    async def test_f_ca_07_composite_promotion_carries_expiry_and_tags(self):
        client = await _live_client()
        l2 = RedisBackend(url=REDIS_URL, key_prefix="")
        composite = CompositeBackend(MemoryBackend(), l2)
        try:
            await composite.initialize()
            await l2.set("c", "v", ttl=50, tags=("t",))  # L2-only entry

            results = await composite.get_many(["c"])
            assert results["c"].value == "v"

            promoted = await composite._l1.get("c")
            assert promoted is not None
            assert promoted.expires_at is not None  # used to be None (never expires)
            assert promoted.ttl_remaining <= 50
            assert promoted.tags == ("t",)
        finally:
            await _teardown(client, composite)


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-08 — redis_decode_responses config ignored
# ═══════════════════════════════════════════════════════════════════════════


class TestDecodeResponses:
    def test_f_ca_08_backend_defaults_to_bytes(self):
        assert RedisBackend()._decode_responses is False

    def test_f_ca_08_config_default_keeps_effective_default_false(self):
        assert CacheConfig().redis_decode_responses is False
        assert build_cache_config({}).redis_decode_responses is False

    def test_f_ca_08_di_passes_config_through(self):
        config = CacheConfig(backend="redis", redis_decode_responses=True)
        assert create_cache_backend(config)._decode_responses is True
        config = CacheConfig(backend="redis", redis_decode_responses=False)
        assert create_cache_backend(config)._decode_responses is False

    @pytest.mark.asyncio
    async def test_f_ca_08_decode_responses_opt_in_round_trips(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, decode_responses=True, key_prefix="")
        try:
            await backend.initialize()
            await backend.set("k", {"a": 1}, ttl=30, tags=("t",), namespace="n")

            entry = await backend.get("k")
            assert entry.value == {"a": 1} and entry.tags == ("t",)

            many = await backend.get_many(["k"])
            assert many["k"].value == {"a": 1} and many["k"].tags == ("t",)
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# F-CA-09 — double key prefixing and prefix-scan clear()
# ═══════════════════════════════════════════════════════════════════════════


class TestKeyPrefixingAndClear:
    @pytest.mark.asyncio
    async def test_f_ca_09_di_backend_applies_prefix_exactly_once(self):
        client = await _live_client()
        service = create_cache_service(
            CacheConfig(backend="redis", key_prefix="shared:", redis_url=REDIS_URL, ttl_jitter=False)
        )
        try:
            await service.initialize()
            await service.set("u", "v", namespace="users", ttl=60, tags=("t1",))

            keys = sorted(k.decode() for k in await client.keys("*"))
            assert "shared:v1:users:u" in keys
            assert not any(k.startswith("shared:shared:") for k in keys)  # was doubled
        finally:
            await _teardown(client, service)

    @pytest.mark.asyncio
    async def test_f_ca_09_clear_never_deletes_foreign_keys_sharing_the_prefix(self):
        client = await _live_client()
        service = create_cache_service(
            CacheConfig(backend="redis", key_prefix="shared:", redis_url=REDIS_URL, ttl_jitter=False)
        )
        try:
            await service.initialize()
            await service.set("u", "v", namespace="users", ttl=60, tags=("t1",))
            # A foreign key (another app's session) sharing the prefix.
            await client.set("shared:other-app:session:xyz", "do-not-delete")

            removed = await service.clear()
            assert removed == 1

            remaining = sorted(k.decode() for k in await client.keys("*"))
            assert "shared:other-app:session:xyz" in remaining
            assert "shared:v1:users:u" not in remaining
        finally:
            await _teardown(client, service)

    @pytest.mark.asyncio
    async def test_f_ca_09_clear_cleans_internal_bookkeeping_too(self):
        client = await _live_client()
        service = create_cache_service(
            CacheConfig(backend="redis", key_prefix="shared:", redis_url=REDIS_URL, ttl_jitter=False)
        )
        try:
            await service.initialize()
            await service.set("u", "v", namespace="users", ttl=60, tags=("t1",))
            await service.clear()
            # Data key, _meta sidecar, _ns set and _tags set are all gone.
            assert await client.dbsize() == 0
        finally:
            await _teardown(client, service)

    @pytest.mark.asyncio
    async def test_f_ca_09_service_invalidation_still_works_without_double_prefix(self):
        client = await _live_client()
        service = create_cache_service(
            CacheConfig(backend="redis", key_prefix="shared:", redis_url=REDIS_URL, ttl_jitter=False)
        )
        try:
            await service.initialize()
            await service.set("u", "v", namespace="users", ttl=60, tags=("t1",))

            assert await service.invalidate_tags("t1") == 1
            assert await service.get("u", namespace="users") is None

            await service.set("u2", "v", namespace="users", ttl=60)
            assert await service.invalidate_namespace("users") == 1
            assert await service.get("u2", namespace="users") is None
        finally:
            await _teardown(client, service)

    @pytest.mark.asyncio
    async def test_f_ca_09_directly_constructed_backend_still_prefixes(self):
        """Hand-constructed RedisBackends keep their own key_prefix (back-compat)."""
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="x:")
        try:
            await backend.initialize()
            await backend.set("k", "v", ttl=30)
            assert await client.exists("x:k") == 1
            assert await backend.get("k") is not None
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# N-1 — pool exhaustion silently dropped writes
# ═══════════════════════════════════════════════════════════════════════════


class TestRedisPoolExhaustion:
    @pytest.mark.asyncio
    async def test_n_1_concurrent_increments_have_zero_silent_failures(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, max_connections=10, key_prefix="")
        try:
            await backend.initialize()
            await backend.set("ctr", 0, ttl=60)

            results = await asyncio.gather(*(backend.increment("ctr") for _ in range(40)))
            assert all(r is not None for r in results), f"silent failures: {results}"

            final = await backend.get("ctr")
            assert final.value == 40

            stats = await backend.stats()
            assert stats.errors == 0
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# N-2 — MemoryBackend(max_size=0) hung the event loop
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryMaxSizeZero:
    @pytest.mark.asyncio
    async def test_n_2_max_size_zero_means_unlimited(self):
        backend = MemoryBackend(max_size=0)
        await backend.initialize()

        async def fill():
            for i in range(20):
                await backend.set(f"k{i}", i)
            await backend.set_many({f"m{i}": i for i in range(10)})

        # The old unawaited eviction loop hung the loop; wait_for turns a
        # regression back into a failure.
        await asyncio.wait_for(fill(), timeout=5)
        assert len(await backend.keys()) == 30
        await backend.shutdown()

    def test_n_2_config_rejects_negative_capacity(self):
        with pytest.raises(ConfigInvalidFault):
            CacheConfig(max_size=-1)
        with pytest.raises(ConfigInvalidFault):
            CacheConfig(l1_max_size=-1)

    def test_n_2_config_allows_zero_as_unlimited(self):
        CacheConfig(max_size=0, l1_max_size=0)  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# N-3 — CacheMiddleware corrupted bodies through JSON backends
# ═══════════════════════════════════════════════════════════════════════════


class TestMiddlewareBody:
    @pytest.mark.asyncio
    async def test_n_3_binary_body_survives_json_serializing_backend(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        service = CacheService(backend, CacheConfig(ttl_jitter=False))
        await service.initialize()
        middleware = CacheMiddleware(service, default_ttl=60)
        body = b"\x00\x01binary\xff\xfe"

        try:
            first = await middleware(_Request(path="/bin"), None, _handler(body))
            assert first.headers["x-cache"] == "MISS"

            second = await middleware(_Request(path="/bin"), None, _handler(b"replaced"))
            assert second.headers["x-cache"] == "HIT"
            assert second.content == body
        finally:
            await _teardown(client, service)

    @pytest.mark.asyncio
    async def test_n_3_legacy_body_entries_are_treated_as_misses(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        service = CacheService(backend, CacheConfig(ttl_jitter=False))
        await service.initialize()
        middleware = CacheMiddleware(service, default_ttl=60)

        try:
            # Entry in the pre-fix format: raw bytes went through
            # json.dumps(default=str) and came back as their repr string.
            legacy = {
                "body": "b'legacy'",
                "status": 200,
                "headers": {},
                "etag": "e",
                "cached_at": time.time(),
                "ttl": 60,
            }
            await service.set("GET:/legacy", legacy, namespace="http_response", ttl=60)

            response = await middleware(_Request(path="/legacy"), None, _handler(b"fresh"))
            assert response.headers["x-cache"] == "MISS"  # undecodable -> miss
            assert response.content == b"fresh"
        finally:
            await _teardown(client, service)


# ═══════════════════════════════════════════════════════════════════════════
# N-4 — @cached sentinel collided with a legitimate string value
# ═══════════════════════════════════════════════════════════════════════════


class TestCachedSentinel:
    @pytest.mark.asyncio
    async def test_n_4_none_result_is_cached(self):
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        set_default_cache_service(service)
        calls = {"n": 0}

        @cached(ttl=60, namespace="users")
        async def fetch_none() -> None:
            calls["n"] += 1
            return None

        assert await fetch_none() is None
        assert await fetch_none() is None
        assert calls["n"] == 1

    @pytest.mark.asyncio
    async def test_n_4_literal_marker_string_never_becomes_none(self):
        """The string that collided with the old sentinel round-trips as itself."""
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        set_default_cache_service(service)
        calls = {"n": 0}

        @cached(ttl=60, namespace="users")
        async def fetch_marker() -> str:
            calls["n"] += 1
            return "__aquilia_cache_none__"

        assert await fetch_marker() == "__aquilia_cache_none__"
        assert await fetch_marker() == "__aquilia_cache_none__"
        # The legacy string is indistinguishable from an old-format entry, so
        # it is never cached -- but it is NEVER misread as None either.
        assert calls["n"] == 2

    @pytest.mark.asyncio
    async def test_n_4_legacy_string_sentinel_entry_recomputes(self):
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        set_default_cache_service(service)
        calls = {"n": 0}

        @cached(ttl=60, namespace="users")
        async def wrapped() -> str:
            calls["n"] += 1
            return "real"

        # Pre-seed an old-format sentinel under the decorator's exact key.
        key = call_signature(wrapped.__qualname__, (), {})
        await service.set(key, _NONE_SENTINEL_LEGACY, namespace="users")

        assert await wrapped() == "real"  # old code returned None here
        assert calls["n"] == 1

    @pytest.mark.asyncio
    async def test_n_4_dict_marker_result_round_trips(self):
        """A function returning the marker-shaped dict itself is not swallowed."""
        service = CacheService(MemoryBackend(), CacheConfig(ttl_jitter=False))
        set_default_cache_service(service)
        marker = {"__aquilia_cache_none__": True}

        @cached(ttl=60, namespace="users")
        async def fetch_dict():
            return marker

        assert await fetch_dict() == marker


# ═══════════════════════════════════════════════════════════════════════════
# N-5 — RedisBackend stats().size always read db0
# ═══════════════════════════════════════════════════════════════════════════


class TestRedisStatsDb:
    def test_n_5_db_index_parsed_from_url(self):
        assert RedisBackend(url="redis://localhost:6379/15")._db == 15
        assert RedisBackend(url="redis://localhost:6379/0")._db == 0
        assert RedisBackend(url="redis://localhost:6379")._db == 0
        assert RedisBackend(url="redis://localhost:6379/notanumber")._db == 0

    @pytest.mark.asyncio
    async def test_n_5_stats_size_reads_the_configured_db(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            for i in range(3):
                await backend.set(f"k{i}", i, ttl=60)

            stats = await backend.stats()
            keyspace = await client.info("keyspace")
            db15_keys = keyspace["db15"]["keys"]
            assert db15_keys > 0
            assert stats.size == db15_keys  # old code read db0's count
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# N-6 — namespace sets grew without bound
# ═══════════════════════════════════════════════════════════════════════════


class TestNamespaceSetExpiry:
    @pytest.mark.asyncio
    async def test_n_6_namespace_set_gets_an_expiry(self):
        client = await _live_client()
        backend = RedisBackend(url=REDIS_URL, key_prefix="")
        try:
            await backend.initialize()
            await backend.set("k", "v", ttl=30, namespace="ns")

            ttl = await client.ttl(backend._ns_set_key("ns"))
            assert ttl > 0  # was -1 (no expiry) before
        finally:
            await _teardown(client, backend)


# ═══════════════════════════════════════════════════════════════════════════
# N-7 — CacheService.delete (and friends) raised where get/set swallow
# ═══════════════════════════════════════════════════════════════════════════


class TestNeverRaisePolicy:
    @pytest.mark.asyncio
    async def test_n_7_all_public_operations_swallow_backend_errors(self):
        service = CacheService(_ExplodingBackend(), CacheConfig(ttl_jitter=False))

        assert await service.get("k") is None
        assert await service.get("k", default="d") == "d"
        await service.set("k", "v")
        assert await service.delete("k") is False
        assert await service.exists("k") is False
        assert await service.get_many(["k"]) == {"k": None}
        await service.set_many({"k": "v"})
        assert await service.delete_many(["k"]) == 0
        assert await service.invalidate_tags("t") == 0
        assert await service.invalidate_namespace("n") == 0
        assert await service.increment("k") is None
        assert await service.decrement("k") is None
        assert await service.clear() == 0
        assert await service.clear(namespace="n") == 0
        assert await service.keys() == []
        assert await service.touch("k", 30) is False

        stats = await service.stats()
        assert stats.backend == "exploding"  # fallback snapshot, not an raise

    @pytest.mark.asyncio
    async def test_n_7_failures_log_warnings(self, caplog):
        service = CacheService(_ExplodingBackend(), CacheConfig(ttl_jitter=False))
        with caplog.at_level(logging.WARNING, logger="aquilia.cache"):
            await service.delete("k")
            await service.exists("k")
        messages = [record.message for record in caplog.records]
        assert any("DELETE failed" in m for m in messages)
        assert any("EXISTS failed" in m for m in messages)

    @pytest.mark.asyncio
    async def test_n_7_touch_with_broken_backend_atomic_path_returns_false(self):
        class _BrokenTouchBackend(MemoryBackend):
            async def touch(self, key: str, ttl: int) -> bool:
                raise RuntimeError("boom-touch")

        service = CacheService(_BrokenTouchBackend(), CacheConfig(ttl_jitter=False))
        assert await service.touch("k", 30) is False


# ═══════════════════════════════════════════════════════════════════════════
# N-8 — stampede join awaited stats() under the global in-flight lock
# ═══════════════════════════════════════════════════════════════════════════


class TestStampedeJoinAccounting:
    @pytest.mark.asyncio
    async def test_n_8_join_does_not_touch_backend_stats_and_counts_locally(self):
        backend = _StatsSpyBackend()
        service = CacheService(
            backend,
            CacheConfig(stampede_prevention=True, stampede_timeout=5, ttl_jitter=False),
        )
        calls = {"n": 0}

        async def loader():
            calls["n"] += 1
            await asyncio.sleep(0.02)
            return "v"

        results = await asyncio.gather(*(service.get_or_set("k", loader, ttl=60) for _ in range(5)))
        assert results == ["v"] * 5
        assert calls["n"] == 1

        # No backend stats() call ran while joining (the old code performed
        # network I/O under the global in-flight lock, once per joiner).
        assert backend.stats_calls == 0

        # Joins are counted process-locally and surfaced through stats().
        stats = await service.stats()
        assert stats.stampede_joins == 4
        assert backend.stats_calls == 1
