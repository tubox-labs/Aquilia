"""
Regression tests for the cache / filesystem / storage architecture audit.

Each test pins the behaviour of one confirmed audit finding so the defect
cannot silently return.  Test names carry the audit's finding IDs.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from aquilia.cache.backends.composite import CompositeBackend
from aquilia.cache.backends.memory import MemoryBackend
from aquilia.cache.core import CacheConfig
from aquilia.cache.decorators import cached, set_default_cache_service
from aquilia.cache.di_providers import build_cache_config, create_cache_backend, create_cache_service
from aquilia.cache.key_builder import DefaultKeyBuilder, HashKeyBuilder, build_key_builder
from aquilia.cache.middleware import CacheMiddleware
from aquilia.cache.service import CacheService
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.filesystem import FileSystem, FileSystemConfig
from aquilia.filesystem._errors import PathTraversalFault
from aquilia.response import Response
from aquilia.storage.backends.local import LocalStorage
from aquilia.storage.base import PermissionError as StoragePermissionError
from aquilia.storage.configs import LocalConfig

# ═══════════════════════════════════════════════════════════════════════════
# A3.1 / A3.2 — key_version wiring and a single shared key builder
# ═══════════════════════════════════════════════════════════════════════════


class TestCacheKeyBuilding:
    def test_a3_1_key_version_reaches_generated_keys(self):
        service = CacheService(MemoryBackend(), CacheConfig(key_version=5, key_prefix="aq:"))
        assert service.key_builder.build("users", "user:1", "aq:") == "aq:v5:users:user:1"

    def test_a3_1_key_version_zero_omits_version_segment(self):
        service = CacheService(MemoryBackend(), CacheConfig(key_version=0))
        assert service.key_builder.build("users", "user:1", "aq:") == "aq:users:user:1"

    def test_a3_1_bumping_key_version_invalidates_old_keys(self):
        v1 = CacheService(MemoryBackend(), CacheConfig(key_version=1))
        v2 = CacheService(MemoryBackend(), CacheConfig(key_version=2))
        assert v1.key_builder.build("n", "k") != v2.key_builder.build("n", "k")

    def test_a3_2_from_args_embeds_namespace_once(self):
        builder = DefaultKeyBuilder(version=3)
        key = builder.from_args(namespace="users", func_name="get", args=(1,), prefix="aq:")
        assert key == "aq:v3:users:get:1"
        assert key.count("users") == 1

    def test_a3_2_hash_builder_shares_signature_layout(self):
        a = HashKeyBuilder(version=1).from_args("ns", "fn", (1,), {"b": 2})
        b = HashKeyBuilder(version=1).from_args("ns", "fn", (1,), {"b": 2})
        assert a == b
        assert HashKeyBuilder(version=2).from_args("ns", "fn", (1,)) != a

    def test_a3_2_kwargs_order_does_not_change_key(self):
        builder = DefaultKeyBuilder()
        assert builder.from_args("ns", "fn", (), {"a": 1, "b": 2}) == builder.from_args(
            "ns", "fn", (), {"b": 2, "a": 1}
        )

    def test_build_key_builder_rejects_unknown_strategy(self):
        with pytest.raises(ConfigInvalidFault):
            build_key_builder("nope")

    @pytest.mark.asyncio
    async def test_a3_2_decorator_and_manual_keys_match(self):
        backend = MemoryBackend()
        service = CacheService(backend, CacheConfig(key_version=2, key_prefix="aq:"))
        set_default_cache_service(service)

        @cached(ttl=60, namespace="users")
        async def fetch(user_id: int) -> dict:
            return {"id": user_id}

        try:
            await fetch(7)
            stored = await backend.keys()
            expected = service.key_builder.build("users", f"{fetch.__qualname__}:7", "aq:")
            assert stored == [expected]
            assert expected.startswith("aq:v2:users:")
        finally:
            set_default_cache_service(None)


# ═══════════════════════════════════════════════════════════════════════════
# A3.3 — functions returning None are cached
# ═══════════════════════════════════════════════════════════════════════════


class TestCachedNoneResults:
    @pytest.mark.asyncio
    async def test_a3_3_none_result_is_cached_not_recomputed(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        set_default_cache_service(service)
        calls = {"n": 0}

        @cached(ttl=60, namespace="lookups")
        async def missing(_key: str) -> None:
            calls["n"] += 1
            return None

        try:
            assert await missing("a") is None
            assert await missing("a") is None
            assert calls["n"] == 1
        finally:
            set_default_cache_service(None)

    @pytest.mark.asyncio
    async def test_a3_3_condition_still_suppresses_caching(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        set_default_cache_service(service)
        calls = {"n": 0}

        @cached(ttl=60, namespace="lookups", condition=lambda r: r is not None)
        async def missing(_key: str) -> None:
            calls["n"] += 1
            return None

        try:
            await missing("a")
            await missing("a")
            assert calls["n"] == 2
        finally:
            set_default_cache_service(None)


# ═══════════════════════════════════════════════════════════════════════════
# A3.4 / A3.5 — LFU eviction and bounded heaps
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryBackendHeaps:
    @pytest.mark.asyncio
    async def test_a3_5_ttl_heap_does_not_grow_on_repeated_overwrite(self):
        backend = MemoryBackend(max_size=100)
        for i in range(2000):
            await backend.set("session", i, ttl=60)
        assert len(backend._store) == 1
        assert backend.ttl_heap_size <= 16

    @pytest.mark.asyncio
    async def test_a3_5_ttl_heap_shrinks_after_deletes(self):
        backend = MemoryBackend(max_size=1000)
        for i in range(500):
            await backend.set(f"k{i}", i, ttl=60)
        for i in range(500):
            await backend.delete(f"k{i}")
        await backend.set("final", 1, ttl=60)
        assert backend.ttl_heap_size <= 64

    @pytest.mark.asyncio
    async def test_a3_4_lfu_heap_stays_proportional_to_store(self):
        backend = MemoryBackend(max_size=50, eviction_policy="lfu")
        for i in range(3000):
            await backend.set(f"k{i % 80}", i)
            await backend.get(f"k{i % 80}")
        assert backend.lfu_heap_size <= 4 * len(backend._store)

    @pytest.mark.asyncio
    async def test_a3_4_lfu_evicts_the_least_frequently_used_key(self):
        backend = MemoryBackend(max_size=3, eviction_policy="lfu")
        await backend.set("hot", 1)
        await backend.set("warm", 2)
        for _ in range(10):
            await backend.get("hot")
        for _ in range(5):
            await backend.get("warm")

        await backend.set("cold", 3)
        await backend.set("evictor", 4)

        assert await backend.get("hot") is not None
        assert await backend.get("cold") is None

    @pytest.mark.asyncio
    async def test_sweeper_removes_expired_and_compacts(self):
        import time

        backend = MemoryBackend(max_size=100)
        await backend.set("gone", 1, ttl=1)
        expired_at = time.monotonic() - 1
        backend._store["gone"].expires_at = expired_at
        backend._ttl_heap[0] = (expired_at, "gone")

        assert await backend._sweep_expired() == 1
        assert backend.ttl_heap_size == 0
        assert await backend.get("gone") is None


# ═══════════════════════════════════════════════════════════════════════════
# A3.9 — composite fire-and-forget L2 writes are tracked
# ═══════════════════════════════════════════════════════════════════════════


class _SlowBackend(MemoryBackend):
    """Memory backend whose writes yield, to expose shutdown races."""

    async def set(self, key, value, ttl=None, tags=(), namespace="default"):
        await asyncio.sleep(0.02)
        await super().set(key, value, ttl=ttl, tags=tags, namespace=namespace)


class TestCompositeAsyncWrites:
    @pytest.mark.asyncio
    async def test_a3_9_shutdown_drains_pending_l2_writes(self):
        l1 = MemoryBackend(max_size=10)
        l2 = _SlowBackend(max_size=10)
        backend = CompositeBackend(l1=l1, l2=l2, async_l2_write=True)
        await backend.initialize()

        await backend.set("k", "v", ttl=60)
        assert backend.pending_writes == 1

        await backend.drain()
        assert backend.pending_writes == 0
        assert await l2.get("k") is not None

    @pytest.mark.asyncio
    async def test_a3_9_scheduled_writes_are_strongly_referenced(self):
        backend = CompositeBackend(l1=MemoryBackend(), l2=_SlowBackend(), async_l2_write=True)
        await backend.initialize()
        await backend.set_many({"a": 1, "b": 2}, ttl=30)
        assert backend.pending_writes == 1
        await backend.shutdown()
        assert backend.pending_writes == 0


# ═══════════════════════════════════════════════════════════════════════════
# A3.10 — pickle serializer reachable, and refused without a key
# ═══════════════════════════════════════════════════════════════════════════


class TestSerializerWiring:
    def test_a3_10_pickle_without_secret_key_fails_with_actionable_fault(self):
        config = CacheConfig(backend="redis", serializer="pickle")
        with pytest.raises(ConfigInvalidFault) as exc:
            create_cache_backend(config)
        assert "serializer_secret_key" in str(exc.value)

    def test_a3_10_secret_key_is_parsed_from_config_dict(self):
        config = build_cache_config({"serializer": "pickle", "serializer_secret_key": "s3cret"})
        assert config.serializer_secret_key == "s3cret"

    def test_a3_10_json_backend_still_builds_without_secret(self):
        service = create_cache_service(CacheConfig(backend="memory"))
        assert service.backend.name.startswith("memory")


# ═══════════════════════════════════════════════════════════════════════════
# A3.11 — stampede scope
# ═══════════════════════════════════════════════════════════════════════════


class TestStampedeProtection:
    @pytest.mark.asyncio
    async def test_in_process_coalescing_calls_loader_once(self):
        service = CacheService(MemoryBackend(), CacheConfig(stampede_prevention=True))
        calls = {"n": 0}

        async def loader():
            calls["n"] += 1
            await asyncio.sleep(0.02)
            return "value"

        results = await asyncio.gather(*(service.get_or_set("k", loader, ttl=60) for _ in range(10)))
        assert results == ["value"] * 10
        assert calls["n"] == 1

    def test_a3_11_memory_backend_declares_no_distributed_lock(self):
        assert MemoryBackend().supports_distributed_lock is False

    @pytest.mark.asyncio
    async def test_a3_11_default_lock_helpers_are_inert(self):
        backend = MemoryBackend()
        assert await backend.try_acquire_lock("k", 1.0) is None
        assert await backend.release_lock("k", "token") is False


# ═══════════════════════════════════════════════════════════════════════════
# A4 — HTTP response cache must not leak across identities
# ═══════════════════════════════════════════════════════════════════════════


class _Headers(dict):
    def get(self, key, default=""):
        return super().get(key.lower(), default)


class _Request:
    def __init__(self, path="/me", method="GET", headers=None):
        self.path = path
        self.method = method
        self.query_string = ""
        self.headers = _Headers({k.lower(): v for k, v in (headers or {}).items()})


async def _handler_factory(body: bytes, headers: dict | None = None):
    async def handler(_request, _ctx):
        return Response(content=body, status=200, headers=dict(headers or {}))

    return handler


class TestCacheMiddlewareIdentity:
    @pytest.mark.asyncio
    async def test_a4_cookie_request_is_not_served_from_shared_cache(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        middleware = CacheMiddleware(service, default_ttl=60)

        anon = await middleware(_Request(), None, await _handler_factory(b"anonymous"))
        assert anon.headers["x-cache"] == "MISS"

        authed = await middleware(
            _Request(headers={"Cookie": "session=alice"}),
            None,
            await _handler_factory(b"alice-private"),
        )
        assert authed.headers["x-cache"] == "PRIVATE"
        assert authed.content == b"alice-private"

    @pytest.mark.asyncio
    async def test_a4_authorization_request_bypasses_cache(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        middleware = CacheMiddleware(service, default_ttl=60)
        response = await middleware(
            _Request(headers={"Authorization": "Bearer t"}),
            None,
            await _handler_factory(b"secret"),
        )
        assert response.headers["x-cache"] == "PRIVATE"

    @pytest.mark.asyncio
    async def test_a4_set_cookie_response_is_never_stored(self):
        backend = MemoryBackend()
        service = CacheService(backend, CacheConfig())
        middleware = CacheMiddleware(service, default_ttl=60)

        response = await middleware(
            _Request(),
            None,
            await _handler_factory(b"body", {"Set-Cookie": "session=bob"}),
        )
        assert response.headers["x-cache"] == "PRIVATE"
        assert await backend.keys() == []

    @pytest.mark.asyncio
    async def test_a4_opt_in_caches_authenticated_when_cookie_varies(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        middleware = CacheMiddleware(
            service,
            default_ttl=60,
            vary_headers=("Accept", "Cookie"),
            cache_authenticated=True,
        )
        request = _Request(headers={"Cookie": "session=alice"})

        first = await middleware(request, None, await _handler_factory(b"alice"))
        assert first.headers["x-cache"] == "MISS"

        second = await middleware(request, None, await _handler_factory(b"should-not-be-used"))
        assert second.headers["x-cache"] == "HIT"
        assert second.content == b"alice"

    @pytest.mark.asyncio
    async def test_a4_opt_in_still_partitions_by_cookie_value(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        middleware = CacheMiddleware(
            service,
            default_ttl=60,
            vary_headers=("Cookie",),
            cache_authenticated=True,
        )

        await middleware(_Request(headers={"Cookie": "s=alice"}), None, await _handler_factory(b"alice"))
        bob = await middleware(_Request(headers={"Cookie": "s=bob"}), None, await _handler_factory(b"bob"))
        assert bob.content == b"bob"
        assert bob.headers["x-cache"] == "MISS"


# ═══════════════════════════════════════════════════════════════════════════
# B3.1 — LocalStorage containment uses component comparison, not prefixes
# ═══════════════════════════════════════════════════════════════════════════


class TestLocalStorageContainment:
    @pytest.mark.asyncio
    async def test_b3_1_sibling_directory_prefix_is_rejected(self, tmp_path):
        root = tmp_path / "data"
        sibling = tmp_path / "data-private"
        root.mkdir()
        sibling.mkdir()
        (sibling / "secret.txt").write_text("LEAK")

        storage = LocalStorage(LocalConfig(root=str(root)))
        await storage.initialize()
        os.symlink(sibling, root / "link")

        with pytest.raises(StoragePermissionError):
            await storage.open("link/secret.txt")

    @pytest.mark.asyncio
    async def test_b3_1_symlinked_file_outside_root_is_rejected(self, tmp_path):
        root = tmp_path / "data"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        (outside / "passwd").write_text("root:x:0:0")

        storage = LocalStorage(LocalConfig(root=str(root)))
        await storage.initialize()
        os.symlink(outside / "passwd", root / "passwd")

        with pytest.raises(StoragePermissionError):
            await storage.stat("passwd")

    @pytest.mark.asyncio
    async def test_b3_1_normal_nested_paths_still_work(self, tmp_path):
        storage = LocalStorage(LocalConfig(root=str(tmp_path / "data")))
        await storage.initialize()
        name = await storage.save("a/b/c.txt", b"ok")
        async with await storage.open(name) as handle:
            assert await handle.read() == b"ok"


# ═══════════════════════════════════════════════════════════════════════════
# B3.5 — LocalStorage streams instead of buffering whole files
# ═══════════════════════════════════════════════════════════════════════════


class TestLocalStorageStreaming:
    @pytest.mark.asyncio
    async def test_b3_5_open_yields_multiple_chunks(self, tmp_path):
        storage = LocalStorage(LocalConfig(root=str(tmp_path / "data")))
        await storage.initialize()
        await storage.save("big.bin", b"x" * 200_000, overwrite=True)

        chunks = []
        async with await storage.open("big.bin") as handle:
            async for chunk in handle:
                chunks.append(chunk)

        assert len(chunks) > 1
        assert sum(len(c) for c in chunks) == 200_000

    @pytest.mark.asyncio
    async def test_b3_5_open_does_not_materialise_until_read(self, tmp_path):
        storage = LocalStorage(LocalConfig(root=str(tmp_path / "data")))
        await storage.initialize()
        await storage.save("f.bin", b"y" * 1000, overwrite=True)

        handle = await storage.open("f.bin")
        assert handle.content is None
        assert handle.size == 1000  # from metadata, without reading
        assert await handle.read() == b"y" * 1000

    @pytest.mark.asyncio
    async def test_b3_5_copy_streams_content(self, tmp_path):
        storage = LocalStorage(LocalConfig(root=str(tmp_path / "data")))
        await storage.initialize()
        await storage.save("src.bin", b"z" * 150_000, overwrite=True)
        await storage.copy("src.bin", "dst.bin")

        async with await storage.open("dst.bin") as handle:
            assert await handle.read() == b"z" * 150_000

    @pytest.mark.asyncio
    async def test_b3_5_save_accepts_async_iterator(self, tmp_path):
        storage = LocalStorage(LocalConfig(root=str(tmp_path / "data")))
        await storage.initialize()

        async def chunks():
            for _ in range(3):
                yield b"a" * 10

        await storage.save("iter.bin", chunks(), overwrite=True)
        assert await storage.size("iter.bin") == 30


# ═══════════════════════════════════════════════════════════════════════════
# B3.2 — the streaming path enforces the sandbox
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def fs():
    filesystem = FileSystem()
    await filesystem.initialize()
    yield filesystem
    await filesystem.shutdown()


class TestStreamingSandbox:
    @pytest.mark.asyncio
    async def test_b3_2_stream_read_honours_sandbox(self, fs, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        outside = tmp_path / "etc"
        outside.mkdir()
        (outside / "passwd").write_text("secret")

        with pytest.raises(PathTraversalFault):
            async for _ in fs.stream_read(str(outside / "passwd"), sandbox=str(root)):
                pass

    @pytest.mark.asyncio
    async def test_b3_2_stream_copy_honours_sandbox_for_source(self, fs, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        (outside / "data.bin").write_bytes(b"secret")

        with pytest.raises(PathTraversalFault):
            await fs.stream_copy(str(outside / "data.bin"), str(root / "copy.bin"), sandbox=str(root))

    @pytest.mark.asyncio
    async def test_b3_2_stream_copy_honours_sandbox_for_destination(self, fs, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        (root / "in.bin").write_bytes(b"data")
        outside = tmp_path / "other"
        outside.mkdir()

        with pytest.raises(PathTraversalFault):
            await fs.stream_copy(str(root / "in.bin"), str(outside / "out.bin"), sandbox=str(root))

    @pytest.mark.asyncio
    async def test_b3_2_sibling_prefix_does_not_satisfy_sandbox(self, fs, tmp_path):
        root = tmp_path / "data"
        root.mkdir()
        sibling = tmp_path / "data-evil"
        sibling.mkdir()
        (sibling / "f.bin").write_bytes(b"nope")

        with pytest.raises(PathTraversalFault):
            async for _ in fs.stream_read(str(sibling / "f.bin"), sandbox=str(root)):
                pass

    @pytest.mark.asyncio
    async def test_b3_2_in_sandbox_streaming_still_works(self, fs, tmp_path):
        root = tmp_path / "uploads"
        root.mkdir()
        (root / "in.bin").write_bytes(b"payload" * 100)

        copied = await fs.stream_copy(str(root / "in.bin"), str(root / "out.bin"), sandbox=str(root))
        assert copied == 700

        chunks = [c async for c in fs.stream_read(str(root / "out.bin"), sandbox=str(root))]
        assert b"".join(chunks) == b"payload" * 100


# ═══════════════════════════════════════════════════════════════════════════
# B3.2 (facade) — directory helpers accept and honour sandbox/config
# ═══════════════════════════════════════════════════════════════════════════


class TestDirectorySandbox:
    @pytest.mark.asyncio
    async def test_directory_helpers_do_not_raise_typeerror(self, fs, tmp_path):
        target = tmp_path / "d"
        target.mkdir()
        (target / "f.txt").write_text("x")

        assert await fs.list_dir(str(target)) == ["f.txt"]
        assert [e.name for e in await fs.scan_dir(str(target))] == ["f.txt"]

        await fs.make_dir(str(target / "sub"))
        await fs.remove_dir(str(target / "sub"))

    @pytest.mark.asyncio
    async def test_list_dir_rejects_path_outside_sandbox(self, fs, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        with pytest.raises(PathTraversalFault):
            await fs.list_dir(str(outside), sandbox=str(root))

    @pytest.mark.asyncio
    async def test_make_dir_rejects_path_outside_sandbox(self, fs, tmp_path):
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(PathTraversalFault):
            await fs.make_dir(str(tmp_path / "elsewhere"), sandbox=str(root))

    @pytest.mark.asyncio
    async def test_remove_tree_rejects_path_outside_sandbox(self, fs, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        victim = tmp_path / "victim"
        victim.mkdir()

        with pytest.raises(PathTraversalFault):
            await fs.remove_tree(str(victim), sandbox=str(root))
        assert victim.exists()

    @pytest.mark.asyncio
    async def test_walk_and_copy_tree_are_exposed_and_sandboxed(self, fs, tmp_path):
        root = tmp_path / "root"
        (root / "a").mkdir(parents=True)
        (root / "a" / "f.txt").write_text("x")

        seen = [entry async for entry in fs.walk(str(root), sandbox=str(root))]
        assert any("f.txt" in files for _dir, _dirs, files in seen)

        await fs.copy_tree(str(root / "a"), str(root / "b"), sandbox=str(root))
        assert (root / "b" / "f.txt").read_text() == "x"


# ═══════════════════════════════════════════════════════════════════════════
# B3.3 / B3.4 — secure-by-default posture and symlink semantics
# ═══════════════════════════════════════════════════════════════════════════


class TestFileSystemConfigSecurity:
    def test_b3_3_disallowing_unsandboxed_requires_a_root(self):
        with pytest.raises(ConfigInvalidFault) as exc:
            FileSystemConfig(allow_unsandboxed=False)
        assert "sandbox_root" in str(exc.value)

    def test_b3_3_explicit_sandbox_root_satisfies_the_requirement(self, tmp_path):
        config = FileSystemConfig(allow_unsandboxed=False, sandbox_root=str(tmp_path))
        assert config.sandbox_root == str(tmp_path)

    def test_b3_3_default_config_remains_permissive_for_tooling(self):
        assert FileSystemConfig().allow_unsandboxed is True

    @pytest.mark.asyncio
    async def test_b3_3_unsandboxed_operation_fails_loudly_when_disallowed(self, tmp_path):
        from aquilia.filesystem._errors import PermissionDeniedFault
        from aquilia.filesystem._security import validate_path

        config = FileSystemConfig(allow_unsandboxed=False, sandbox_root=str(tmp_path))
        # Explicitly clearing the sandbox at the call site must not silently pass.
        object.__setattr__(config, "sandbox_root", None)
        with pytest.raises(PermissionDeniedFault):
            validate_path(str(tmp_path / "f"), config=config, operation="read")

    def test_b3_4_security_resolution_ignores_follow_symlinks(self, tmp_path):
        from aquilia.filesystem._security import validate_path

        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "f").write_text("x")
        os.symlink(outside / "f", root / "link")

        for follow in (True, False):
            config = FileSystemConfig(follow_symlinks=follow, sandbox_root=str(root))
            with pytest.raises(PathTraversalFault):
                validate_path(str(root / "link"), config=config, operation="read")


# ═══════════════════════════════════════════════════════════════════════════
# B3.6 — storage uses a dedicated, bounded executor
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageExecutor:
    @pytest.mark.asyncio
    async def test_b3_6_run_blocking_uses_named_storage_threads(self):
        import threading

        from aquilia.storage.executor import get_executor, run_blocking, shutdown_executor

        try:
            name = await run_blocking(lambda: threading.current_thread().name)
            assert name.startswith("aquilia-storage")
            assert get_executor() is get_executor()
        finally:
            shutdown_executor()

    @pytest.mark.asyncio
    async def test_b3_6_executor_recreates_after_shutdown(self):
        from aquilia.storage.executor import run_blocking, shutdown_executor

        await run_blocking(lambda: None)
        shutdown_executor()
        assert await run_blocking(lambda: 42) == 42
        shutdown_executor()

    def test_b3_6_pool_size_honours_environment_override(self, monkeypatch):
        from aquilia.storage import executor

        monkeypatch.setenv("AQUILIA_STORAGE_MAX_WORKERS", "3")
        executor.shutdown_executor()
        try:
            assert executor.get_executor()._max_workers == 3
        finally:
            executor.shutdown_executor()

    def test_b3_6_no_backend_uses_the_default_executor(self):
        import pathlib

        for name in ("s3", "gcs", "azure", "sftp"):
            source = pathlib.Path(f"aquilia/storage/backends/{name}.py").read_text()
            assert "run_in_executor(None" not in source
            assert "get_event_loop()" not in source


# ═══════════════════════════════════════════════════════════════════════════
# B3.7 / B4 — registry resilience and lifecycle
# ═══════════════════════════════════════════════════════════════════════════


class _BrokenBackend(LocalStorage):
    async def initialize(self) -> None:
        raise RuntimeError("cannot connect")

    async def ping(self) -> bool:
        raise RuntimeError("unreachable")


class TestRegistryLifecycle:
    @pytest.mark.asyncio
    async def test_b4_optional_backend_failure_does_not_abort_boot(self, tmp_path):
        from aquilia.storage.registry import StorageRegistry

        registry = StorageRegistry()
        registry.register("default", LocalStorage(LocalConfig(root=str(tmp_path / "ok"))))
        registry.register("broken", _BrokenBackend(LocalConfig(root=str(tmp_path / "bad"))))

        await registry.initialize_all()
        health = await registry.health_check()
        assert health["default"] is True
        assert health["broken"] is False

    @pytest.mark.asyncio
    async def test_b4_default_backend_failure_is_fatal(self, tmp_path):
        from aquilia.storage.base import BackendUnavailableError
        from aquilia.storage.registry import StorageRegistry

        registry = StorageRegistry()
        registry.register("default", _BrokenBackend(LocalConfig(root=str(tmp_path / "bad"))))

        with pytest.raises(BackendUnavailableError):
            await registry.initialize_all()

    @pytest.mark.asyncio
    async def test_b4_shutdown_continues_past_a_failing_backend(self, tmp_path):
        from aquilia.storage.registry import StorageRegistry

        class _BadShutdown(LocalStorage):
            async def shutdown(self) -> None:
                raise RuntimeError("boom")

        registry = StorageRegistry()
        registry.register("bad", _BadShutdown(LocalConfig(root=str(tmp_path / "a"))))
        registry.register("good", LocalStorage(LocalConfig(root=str(tmp_path / "b"))))

        await registry.shutdown_all()  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# Server wiring — cache middleware construction and health reporting
# ═══════════════════════════════════════════════════════════════════════════


class TestServerWiring:
    def test_cache_middleware_is_constructed_with_valid_arguments(self):
        from aquilia.config import ConfigLoader
        from aquilia.manifest import AppManifest
        from aquilia.server import AquiliaServer
        from aquilia.workspace import Workspace

        workspace = Workspace("cache-ws")
        config = workspace.to_dict()
        config.setdefault("integrations", {})["cache"] = {
            "enabled": True,
            "backend": "memory",
            "middleware": {"enabled": True, "ttl": 30},
        }

        loader = ConfigLoader()
        loader.config_data = config
        loader._build_apps_namespace()

        server = AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)
        cache_layers = [mw for mw in server.middleware_stack.middlewares if isinstance(mw.middleware, CacheMiddleware)]
        assert len(cache_layers) == 1
        assert cache_layers[0].middleware._default_ttl == 30

    @pytest.mark.asyncio
    async def test_storage_health_reports_each_backend(self, tmp_path):
        from aquilia.config import ConfigLoader
        from aquilia.manifest import AppManifest
        from aquilia.server import AquiliaServer
        from aquilia.storage.registry import StorageRegistry
        from aquilia.workspace import Workspace

        loader = ConfigLoader()
        loader.config_data = Workspace("storage-ws").to_dict()
        loader._build_apps_namespace()
        server = AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)

        registry = StorageRegistry()
        registry.register("default", LocalStorage(LocalConfig(root=str(tmp_path / "ok"))))
        registry.register("broken", _BrokenBackend(LocalConfig(root=str(tmp_path / "bad"))))
        await registry.initialize_all()

        await server._register_storage_health(registry)

        statuses = server.health_registry.to_dict()["subsystems"]
        assert "storage.default" in statuses
        assert statuses["storage.broken"]["status"] == "unhealthy"
        assert statuses["storage"]["status"] == "degraded"


# ═══════════════════════════════════════════════════════════════════════════
# Filesystem subsystem — configuration integration and DI wiring
# ═══════════════════════════════════════════════════════════════════════════


class TestFileSystemIntegration:
    def test_integration_builder_emits_filesystem_config(self):
        from aquilia.integrations import Integration

        config = Integration.filesystem(
            enabled=True,
            sandbox_root="/srv/uploads",
            allow_unsandboxed=False,
        )
        assert config["_integration_type"] == "filesystem"
        assert config["enabled"] is True
        assert config["sandbox_root"] == "/srv/uploads"
        assert config["allow_unsandboxed"] is False

    def test_loader_supplies_safe_defaults(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader()
        loader.config_data = {}
        defaults = loader.get_filesystem_config()
        assert defaults["enabled"] is False
        assert defaults["allow_unsandboxed"] is True

    def test_config_round_trips_into_filesystem_config(self):
        from aquilia.integrations import Integration

        raw = Integration.filesystem(enabled=True, sandbox_root="/srv/uploads", max_pool_threads=4)
        config = FileSystemConfig.from_dict(raw)
        assert config.sandbox_root == "/srv/uploads"
        assert config.max_pool_threads == 4

    @pytest.mark.asyncio
    async def test_server_registers_filesystem_in_di(self, tmp_path):
        from aquilia.config import ConfigLoader
        from aquilia.integrations import Integration
        from aquilia.manifest import AppManifest
        from aquilia.server import AquiliaServer
        from aquilia.workspace import Workspace

        root = str(tmp_path / "uploads")
        (tmp_path / "uploads").mkdir()

        workspace = Workspace("fs-ws").integrate(
            Integration.filesystem(enabled=True, sandbox_root=root, allow_unsandboxed=False)
        )
        loader = ConfigLoader()
        loader.config_data = workspace.to_dict()
        loader._build_apps_namespace()

        server = AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)
        assert server._filesystem is not None
        assert server._filesystem.config.sandbox_root == root

        for container in server.runtime.di_containers.values():
            resolved = await container.resolve_async(FileSystem)
            assert isinstance(resolved, FileSystem)
            break

    def test_server_skips_filesystem_when_disabled(self):
        from aquilia.config import ConfigLoader
        from aquilia.manifest import AppManifest
        from aquilia.server import AquiliaServer
        from aquilia.workspace import Workspace

        loader = ConfigLoader()
        loader.config_data = Workspace("fs-off").to_dict()
        loader._build_apps_namespace()
        server = AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)
        assert server._filesystem is None


# ═══════════════════════════════════════════════════════════════════════════
# CLI — `aq cache stats` reads the API that actually exists
# ═══════════════════════════════════════════════════════════════════════════


class TestCacheStatsCommand:
    def test_cache_service_exposes_stats_not_info(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        assert hasattr(service, "stats")
        assert not hasattr(service, "info")

    @pytest.mark.asyncio
    async def test_stats_payload_is_serializable_for_cli_output(self):
        service = CacheService(MemoryBackend(), CacheConfig())
        await service.set("k", "v", ttl=30)
        payload = (await service.stats()).to_dict()
        assert payload["backend"].startswith("memory")
        assert payload["sets"] >= 1
