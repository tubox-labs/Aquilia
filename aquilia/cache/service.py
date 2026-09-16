"""
AquilaCache -- CacheService: High-level API for cache operations.

DI-injectable service that wraps the configured backend with:
- Namespace isolation
- Automatic key building
- TTL jitter (thundering herd prevention)
- Stampede prevention (singleflight for get_or_set)
- Fault handling with structured fault emission
- Get-or-set (cache-aside) pattern
- Bulk warmup / preloading
- Health checks
- Statistics and diagnostics

Registered in DI as a singleton, available for injection in
controllers, services, and middleware.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from aquilia.cache.core import CacheBackend, CacheConfig, CacheEntry, CacheStats
from aquilia.cache.faults import CacheBackendFault, CacheConnectionFault
from aquilia.cache.key_builder import KeyBuilder, build_key_builder

logger = logging.getLogger("aquilia.cache")

T = TypeVar("T")


class CacheService:
    """
    High-level cache service -- the primary API for application code.

    Provides a clean, async interface for all cache operations with
    automatic key prefixing, namespace isolation, TTL jitter,
    stampede prevention, and fault handling.

    Usage::

        # Via DI injection
        class UserController(Controller):
            def __init__(self, cache: CacheService):
                self.cache = cache

            @GET("/users/{id}")
            async def get_user(self, ctx, id: int):
                user = await self.cache.get(f"user:{id}")
                if user is None:
                    user = await self.repo.find(id)
                    await self.cache.set(f"user:{id}", user, ttl=300)
                return user

        # Cache-aside with stampede prevention
        user = await cache.get_or_set(
            "user:123",
            loader=lambda: repo.find(123),
            ttl=300,
        )

    Key layout -- what actually lands in Redis:

        {key_prefix}{version}:{namespace}:{key}

        e.g. with ``key_prefix="backend:"``, ``key_version=1``,
        ``namespace="default"`` and ``key="cache:home:v1"`` the stored
        key is ``backend:v1:default:cache:home:v1``.  Backends built
        through ``create_cache_backend`` apply this service prefix only --
        a hand-constructed
        :class:`aquilia.cache.backends.redis.RedisBackend` still composes
        its own ``key_prefix`` in front.

    Error contract: cache operations (get/set/delete/exists/bulk
    helpers/invalidate/increment/clear/keys/touch) never raise -- they
    log a warning, emit a fault, and return a safe default.  Lifecycle
    (``initialize``) and user-supplied loaders are the exceptions.
    """

    __slots__ = (
        "_backend",
        "_config",
        "_key_builder",
        "_default_ttl",
        "_default_namespace",
        "_key_prefix",
        "_initialized",
        "_inflight",
        "_inflight_lock",
        "_health_task",
        "_healthy",
        "_stampede_joins",
        "_fault_tasks",
    )

    def __init__(
        self,
        backend: CacheBackend,
        config: CacheConfig | None = None,
    ):
        self._backend = backend
        self._config = config or CacheConfig()
        self._key_builder = build_key_builder(
            self._config.key_builder,
            version=self._config.key_version,
        )
        self._default_ttl = self._config.default_ttl
        self._default_namespace = self._config.namespace
        self._key_prefix = self._config.key_prefix
        self._initialized = False

        # Stampede prevention: in-flight computation futures
        self._inflight: dict[str, asyncio.Future] = {}
        self._inflight_lock = asyncio.Lock()

        # Process-local stampede-join counter; reported by stats() so join
        # coalescing stays observable without touching the backend in the
        # hot path.
        self._stampede_joins = 0

        # Fault-emission tasks (fire-and-forget, strongly referenced)
        self._fault_tasks: set[asyncio.Task] = set()

        # Health monitoring
        self._health_task: asyncio.Task | None = None
        self._healthy = True

    # ── Lifecycle ────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Initialize the cache service and its backend."""
        if self._initialized:
            return
        try:
            await self._backend.initialize()
            self._initialized = True
            self._healthy = True

            # Start health check loop
            if self._config.health_check_interval > 0:
                try:
                    loop = asyncio.get_running_loop()
                    self._health_task = loop.create_task(self._health_check_loop())
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"Cache service initialization failed: {e}")
            self._healthy = False
            raise

    async def shutdown(self) -> None:
        """Shutdown the cache service and its backend."""
        if not self._initialized:
            return

        # Cancel health check task
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_task

        # Cancel any in-flight computations
        async with self._inflight_lock:
            for _key, future in self._inflight.items():
                if not future.done():
                    future.cancel()
            self._inflight.clear()

        # Cancel any best-effort fault emissions still in flight
        for task in self._fault_tasks:
            task.cancel()
        self._fault_tasks.clear()

        await self._backend.shutdown()
        self._initialized = False

    # DI lifecycle aliases
    async def startup(self) -> None:
        """DI lifecycle startup hook."""
        await self.initialize()

    async def async_init(self) -> None:
        """DI async initialization hook."""
        await self.initialize()

    # ── Core Operations ──────────────────────────────────────────────

    async def get(
        self,
        key: str,
        namespace: str | None = None,
        default: Any = None,
    ) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key
            namespace: Optional namespace override
            default: Value to return on miss

        Returns:
            Cached value or default. Never raises -- returns default on error.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)

        t0 = None
        trace = None
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        hit = False
        entry = await self._get_entry(full_key)
        if entry is None:
            res = default
        else:
            hit = True
            res = entry.value

        if trace is not None and t0 is not None:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                trace.add_span(
                    lane=Lane.CACHE,
                    label=f"Cache GET: {key}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={"key": key, "namespace": ns, "hit": hit},
                )
            except Exception:
                pass

        return res

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            namespace: Optional namespace override
            tags: Tags for group invalidation
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)
        effective_ttl = ttl if ttl is not None else self._default_ttl

        # Apply TTL jitter to prevent thundering herd
        effective_ttl = self._config.apply_jitter(effective_ttl)

        t0 = None
        trace = None
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        try:
            await self._backend.set(
                full_key,
                value,
                ttl=effective_ttl,
                tags=tags,
                namespace=ns,
            )
        except Exception as e:
            logger.warning(f"Cache SET failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="set",
                    reason=str(e),
                )
            )

        if trace is not None and t0 is not None:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                trace.add_span(
                    lane=Lane.CACHE,
                    label=f"Cache SET: {key}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={"key": key, "namespace": ns, "ttl": effective_ttl, "tags": list(tags)},
                )
            except Exception:
                pass

    async def delete(self, key: str, namespace: str | None = None) -> bool:
        """
        Delete a value from cache.

        Returns:
            True if the key existed and was deleted.  False when the key
            did not exist OR the delete failed: like every cache operation
            this never raises -- failures are logged and reported through
            the fault engine instead.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)

        t0 = None
        trace = None
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        try:
            res = await self._backend.delete(full_key)
        except Exception as e:
            logger.warning(f"Cache DELETE failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="delete",
                    reason=str(e),
                )
            )
            res = False

        if trace is not None and t0 is not None:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                trace.add_span(
                    lane=Lane.CACHE,
                    label=f"Cache DELETE: {key}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={"key": key, "namespace": ns, "result": res},
                )
            except Exception:
                pass

        return res

    async def exists(self, key: str, namespace: str | None = None) -> bool:
        """
        Check if key exists in cache.

        Never raises -- returns False on error.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)

        t0 = None
        trace = None
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        try:
            res = await self._backend.exists(full_key)
        except Exception as e:
            logger.warning(f"Cache EXISTS failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="exists",
                    reason=str(e),
                )
            )
            res = False

        if trace is not None and t0 is not None:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                trace.add_span(
                    lane=Lane.CACHE,
                    label=f"Cache EXISTS: {key}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={"key": key, "namespace": ns, "result": res},
                )
            except Exception:
                pass

        return res

    # ── Advanced Operations ──────────────────────────────────────────

    async def get_or_set(
        self,
        key: str,
        loader: Callable[[], Coroutine[Any, Any, T]],
        ttl: int | None = None,
        namespace: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> T:
        """
        Cache-aside pattern with stampede prevention.

        On a cache miss, only ONE concurrent caller computes the value.
        All other callers for the same key wait for the first computation
        to finish and reuse the result. This prevents the "thundering herd"
        or "cache stampede" problem.

        Args:
            key: Cache key
            loader: Async callable to produce the value on miss
            ttl: TTL in seconds
            namespace: Optional namespace
            tags: Tags for group invalidation

        Returns:
            Cached or freshly computed value.  A cached ``None`` is a hit:
            the raw backend entry is inspected (not the value), so a
            legitimately ``None`` result is served from cache instead of
            recomputing on every call.

        Note:
            Coalescing is always process-local (an in-memory single-flight map).
            When the backend supports distributed locking *and*
            ``config.distributed_stampede_lock`` is enabled, the single winner
            of the local race additionally takes a cross-process lock, so only
            one worker in the whole fleet recomputes.  Workers that lose the
            distributed race wait briefly for the winner's value rather than
            duplicating the work; if it does not appear within
            ``stampede_timeout`` they compute independently rather than stall.
            Joins are counted process-locally and surfaced via ``stats()``.

        Usage::

            user = await cache.get_or_set("user:1", lambda: repo.find(1), ttl=300)
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)

        # Try cache first (fast path).  The raw entry distinguishes a cached
        # None from a miss; going through get() would conflate the two.
        entry = await self._get_entry(full_key)
        if entry is not None:
            return entry.value

        # Stampede prevention: check for in-flight computation
        if self._config.stampede_prevention:
            # Acquire lock once to atomically check-and-register
            existing_future = None
            async with self._inflight_lock:
                if full_key in self._inflight:
                    # Another coroutine is computing this value -- capture the future
                    existing_future = self._inflight[full_key]

            # Join bookkeeping happens OUTSIDE the lock: this is a
            # process-local counter, and touching the backend (whose
            # stats() may perform network I/O) while holding the global
            # in-flight lock stalled unrelated keys' registration.
            if existing_future is not None:
                self._stampede_joins += 1

            # Wait outside the lock if another coroutine is computing
            if existing_future is not None:
                try:
                    return await asyncio.wait_for(
                        asyncio.shield(existing_future),
                        timeout=self._config.stampede_timeout,
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning(f"Stampede wait timed out for key '{key}', computing independently")
                except Exception:
                    pass  # Fall through to compute independently

            # Register as the computing coroutine (atomically under lock)
            loop = asyncio.get_running_loop()
            future: asyncio.Future = loop.create_future()
            async with self._inflight_lock:
                # Double-check: another coroutine may have registered between
                # our first check and this point
                if full_key in self._inflight:
                    existing_future = self._inflight[full_key]
                else:
                    existing_future = None
                    self._inflight[full_key] = future

            # If someone else registered while we were waiting, join them
            if existing_future is not None:
                self._stampede_joins += 1
                try:
                    return await asyncio.wait_for(
                        asyncio.shield(existing_future),
                        timeout=self._config.stampede_timeout,
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning(f"Stampede wait timed out for key '{key}', computing independently")
                except Exception:
                    pass

            try:
                # Compute the value, coordinating with other processes when
                # the backend can offer a cross-process lock.
                value = await self._compute_single_flight(
                    key,
                    full_key,
                    loader,
                    ttl=ttl,
                    namespace=namespace,
                    tags=tags,
                )

                # Resolve the future for waiting coroutines
                if not future.done():
                    future.set_result(value)

                return value
            except Exception as e:
                # Propagate exception to waiting coroutines
                if not future.done():
                    future.set_exception(e)
                raise
            finally:
                # Clean up in-flight entry
                async with self._inflight_lock:
                    self._inflight.pop(full_key, None)
        else:
            # No stampede prevention -- simple get-or-set
            value = await self._call_loader(loader)
            await self.set(key, value, ttl=ttl, namespace=namespace, tags=tags)
            return value

    async def get_many(
        self,
        keys: list[str],
        namespace: str | None = None,
    ) -> dict[str, Any]:
        """
        Batch get multiple keys.

        Returns:
            Dict mapping keys to values (None for misses).  Never raises --
            a failed batch reports every key as a miss.
        """
        ns = namespace or self._default_namespace
        full_keys = [self._key_builder.build(ns, k, self._key_prefix) for k in keys]

        try:
            entries = await self._backend.get_many(full_keys)
        except Exception as e:
            logger.warning(f"Cache GET_MANY failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="get_many",
                    reason=str(e),
                )
            )
            entries = {}

        result = {}
        for original_key, full_key in zip(keys, full_keys, strict=False):
            entry = entries.get(full_key)
            result[original_key] = entry.value if entry else None
        return result

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
        namespace: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> None:
        """
        Batch set multiple key-value pairs.

        Args:
            items: Key-value pairs to store
            ttl: TTL for all entries (uses default if None)
            namespace: Optional namespace override
            tags: Tags for group invalidation

        Never raises -- failures are logged and reported through the fault
        engine.
        """
        ns = namespace or self._default_namespace
        effective_ttl = ttl if ttl is not None else self._default_ttl

        prefixed = {self._key_builder.build(ns, k, self._key_prefix): v for k, v in items.items()}

        try:
            await self._backend.set_many(prefixed, ttl=effective_ttl, namespace=ns, tags=tags)
        except Exception as e:
            logger.warning(f"Cache SET_MANY failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="set_many",
                    reason=str(e),
                )
            )

    async def delete_many(self, keys: list[str], namespace: str | None = None) -> int:
        """
        Batch delete multiple keys.

        Never raises -- returns the number actually deleted (0 on error).
        """
        ns = namespace or self._default_namespace
        full_keys = [self._key_builder.build(ns, k, self._key_prefix) for k in keys]
        try:
            return await self._backend.delete_many(full_keys)
        except Exception as e:
            logger.warning(f"Cache DELETE_MANY failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="delete_many",
                    reason=str(e),
                )
            )
            return 0

    async def invalidate_tags(self, *tags: str) -> int:
        """
        Invalidate all entries matching given tags.

        Never raises -- returns the number invalidated (0 on error).
        """
        try:
            return await self._backend.delete_by_tags(set(tags))
        except Exception as e:
            logger.warning(f"Cache INVALIDATE_TAGS failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="invalidate_tags",
                    reason=str(e),
                )
            )
            return 0

    async def invalidate_namespace(self, namespace: str) -> int:
        """
        Clear all entries in a namespace.

        Never raises -- returns the number cleared (0 on error).
        """
        try:
            return await self._backend.clear(namespace)
        except Exception as e:
            logger.warning(f"Cache INVALIDATE_NAMESPACE failed for '{namespace}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="invalidate_namespace",
                    reason=str(e),
                )
            )
            return 0

    async def increment(
        self,
        key: str,
        delta: int = 1,
        namespace: str | None = None,
    ) -> int | None:
        """
        Atomically increment a numeric value.

        Never raises -- returns the new value, or None on miss/error.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)
        try:
            return await self._backend.increment(full_key, delta)
        except Exception as e:
            logger.warning(f"Cache INCREMENT failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="increment",
                    reason=str(e),
                )
            )
            return None

    async def decrement(
        self,
        key: str,
        delta: int = 1,
        namespace: str | None = None,
    ) -> int | None:
        """
        Atomically decrement a numeric value.

        Never raises -- returns the new value, or None on miss/error.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)
        try:
            return await self._backend.decrement(full_key, delta)
        except Exception as e:
            logger.warning(f"Cache DECREMENT failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="decrement",
                    reason=str(e),
                )
            )
            return None

    async def clear(self, namespace: str | None = None) -> int:
        """
        Clear all or namespace-scoped entries.

        Never raises -- returns the number cleared (0 on error).
        """
        try:
            return await self._backend.clear(namespace)
        except Exception as e:
            logger.warning(f"Cache CLEAR failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="clear",
                    reason=str(e),
                )
            )
            return 0

    async def keys(
        self,
        pattern: str = "*",
        namespace: str | None = None,
    ) -> list[str]:
        """
        List keys matching pattern.

        Never raises -- returns an empty list on error.
        """
        try:
            return await self._backend.keys(pattern, namespace)
        except Exception as e:
            logger.warning(f"Cache KEYS failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="keys",
                    reason=str(e),
                )
            )
            return []

    async def stats(self) -> CacheStats:
        """
        Get cache statistics.

        Never raises -- falls back to an empty stats snapshot on error.
        Process-local stampede joins are folded into ``stampede_joins``.
        """
        try:
            stats = await self._backend.stats()
        except Exception as e:
            logger.warning(f"Cache STATS failed: {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="stats",
                    reason=str(e),
                )
            )
            stats = CacheStats(backend=self._backend.name)
        stats.stampede_joins += self._stampede_joins
        return stats

    # ── Properties ───────────────────────────────────────────────────

    @property
    def backend(self) -> CacheBackend:
        """Access underlying backend."""
        return self._backend

    @property
    def config(self) -> CacheConfig:
        """Access cache configuration."""
        return self._config

    @property
    def key_builder(self) -> KeyBuilder:
        """
        The key builder shared by this service and the decorator layer.

        Returns:
            The configured :class:`KeyBuilder`, already carrying
            ``config.key_version``.

        Usage::

            full = cache.key_builder.build("users", "user:1", cache.key_prefix)
        """
        return self._key_builder

    @property
    def key_prefix(self) -> str:
        """Global key prefix applied to every generated key."""
        return self._key_prefix

    @property
    def default_namespace(self) -> str:
        """Namespace used when a call site does not supply one."""
        return self._default_namespace

    @property
    def is_distributed(self) -> bool:
        """Whether the backend supports distributed caching."""
        return self._backend.is_distributed

    @property
    def is_healthy(self) -> bool:
        """Whether the cache service is healthy."""
        return self._healthy and self._initialized

    # ── Extended Operations ──────────────────────────────────────────

    async def touch(self, key: str, ttl: int, namespace: str | None = None) -> bool:
        """
        Refresh the TTL of a key without changing its value.

        Useful for extending cache lifetime on access patterns
        like session tokens or rate-limit counters.

        Backends with an atomic ``touch`` (memory, redis, composite) use it,
        preserving value, tags, and namespace in place.  Custom backends
        without one fall back to a read-modify-write that re-stores the
        fetched entry together with its tags.

        Args:
            key: Cache key
            ttl: New TTL in seconds
            namespace: Optional namespace override

        Returns:
            True if key existed and was refreshed.  Never raises -- returns
            False on error.
        """
        ns = namespace or self._default_namespace
        full_key = self._key_builder.build(ns, key, self._key_prefix)

        backend_touch = getattr(self._backend, "touch", None)
        if backend_touch is not None:
            try:
                return await backend_touch(full_key, ttl)
            except Exception as e:
                logger.warning(f"Cache TOUCH failed for key '{key}': {e}")
                self._emit_fault(
                    CacheBackendFault(
                        backend=self._backend.name,
                        operation="touch",
                        reason=str(e),
                    )
                )
                return False

        # Fallback for custom backends without an atomic touch: re-store the
        # fetched entry, carrying its tags so group invalidation still works.
        try:
            entry = await self._get_entry(full_key)
            if entry is None:
                return False
            await self._backend.set(full_key, entry.value, ttl=ttl, tags=entry.tags, namespace=entry.namespace)
            return True
        except Exception as e:
            logger.warning(f"Cache TOUCH failed for key '{key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="touch",
                    reason=str(e),
                )
            )
            return False

    async def warm(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
        namespace: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> int:
        """
        Bulk-preload cache entries (cache warming).

        Used during application startup to preload hot data
        and avoid cold-start cache misses.

        Args:
            items: Dict of key→value pairs to preload
            ttl: TTL for all entries (uses default if None)
            namespace: Namespace for all entries
            tags: Tags for all entries

        Returns:
            Number of entries successfully warmed

        Usage::

            # Warm up on startup
            products = await db.fetch_hot_products()
            await cache.warm(
                {f"product:{p.id}": p.to_dict() for p in products},
                ttl=600,
                namespace="products",
                tags=("products",),
            )
        """
        count = 0
        for key, value in items.items():
            try:
                await self.set(key, value, ttl=ttl, namespace=namespace, tags=tags)
                count += 1
            except Exception as e:
                logger.warning(f"Cache warm failed for key '{key}': {e}")

        return count

    async def health_check(self) -> bool:
        """
        Check if the cache backend is reachable and functioning.

        Returns:
            True if backend is healthy
        """
        try:
            # Test write + read + delete
            health_key = f"{self._key_prefix}__health_check__"
            await self._backend.set(health_key, "ok", ttl=10)
            entry = await self._backend.get(health_key)
            await self._backend.delete(health_key)
            self._healthy = entry is not None and entry.value == "ok"
            return self._healthy
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            self._healthy = False
            return False

    async def get_or_default(
        self,
        key: str,
        default_factory: Callable[[], T],
        namespace: str | None = None,
    ) -> T:
        """
        Get a cached value, or compute default (without caching it).

        Unlike ``get_or_set``, this does NOT store the result.
        Useful when you want fallback behavior without polluting cache.

        Args:
            key: Cache key
            default_factory: Callable to produce default value
            namespace: Optional namespace override

        Returns:
            Cached value or default
        """
        value = await self.get(key, namespace=namespace)
        if value is not None:
            return value
        if inspect.iscoroutinefunction(default_factory):
            return await default_factory()
        return default_factory()

    # ── Internal ─────────────────────────────────────────────────────

    async def _get_entry(self, full_key: str) -> CacheEntry | None:
        """
        Fetch a raw backend entry, distinguishing a hit from a miss.

        Args:
            full_key: Fully-qualified cache key.

        Returns:
            The backend entry -- whose value may legitimately be ``None`` --
            or ``None`` on miss or backend error.  Never raises: errors are
            logged and emitted as faults, then reported as a miss.
        """
        try:
            return await self._backend.get(full_key)
        except Exception as e:
            logger.warning(f"Cache GET failed for key '{full_key}': {e}")
            self._emit_fault(
                CacheBackendFault(
                    backend=self._backend.name,
                    operation="get",
                    reason=str(e),
                )
            )
            return None

    async def _call_loader(self, loader: Callable[[], Coroutine[Any, Any, T]]) -> T:
        """
        Invoke a loader that may be sync or async.

        Args:
            loader: Callable producing the value.

        Returns:
            The loader's result.
        """
        if inspect.iscoroutinefunction(loader):
            return await loader()
        result = loader()
        if inspect.isawaitable(result):
            return await result
        return result

    async def _compute_single_flight(
        self,
        key: str,
        full_key: str,
        loader: Callable[[], Coroutine[Any, Any, T]],
        *,
        ttl: int | None,
        namespace: str | None,
        tags: tuple[str, ...],
    ) -> T:
        """
        Compute and store a value, holding a cross-process lock when available.

        Args:
            key: Caller-facing cache key.
            full_key: Fully-qualified key, used to derive the lock name.
            loader: Callable producing the value on miss.
            ttl: TTL for the stored value.
            namespace: Namespace for the stored value.
            tags: Tags for the stored value.

        Returns:
            The computed (or peer-computed) value.

        Note:
            Losing the distributed race is not an error: the loser polls
            briefly for the winner's value and falls back to computing
            independently rather than blocking the request indefinitely.
        """
        backend = self._backend
        if not (self._config.distributed_stampede_lock and backend.supports_distributed_lock):
            value = await self._call_loader(loader)
            await self.set(key, value, ttl=ttl, namespace=namespace, tags=tags)
            return value

        lock_key = f"_lock:{full_key}"
        lease = self._config.stampede_lock_ttl
        token = await backend.try_acquire_lock(lock_key, lease)

        if token is None:
            peer_entry = await self._await_peer_value(full_key)
            if peer_entry is not None:
                # A cached None from the winner is a real value here, not
                # a miss -- polling entry values (not get()) is what keeps
                # joiners from stalling the full stampede timeout.
                return peer_entry.value
            # Winner died or is slow -- compute rather than stall the request.
            value = await self._call_loader(loader)
            await self.set(key, value, ttl=ttl, namespace=namespace, tags=tags)
            return value

        try:
            value = await self._call_loader(loader)
            await self.set(key, value, ttl=ttl, namespace=namespace, tags=tags)
            return value
        finally:
            with contextlib.suppress(Exception):
                await backend.release_lock(lock_key, token)

    async def _await_peer_value(self, full_key: str) -> CacheEntry | None:
        """
        Poll for a value being computed by another process.

        Args:
            full_key: Fully-qualified cache key.

        Returns:
            The peer-computed entry (whose value may be ``None``), or
            ``None`` if it did not appear within ``config.stampede_timeout``.
            Polling raw entries -- rather than ``get()``, which flattens a
            cached ``None`` into an indistinguishable miss -- is what keeps
            joiners from stalling the full timeout when the winner's value
            legitimately is ``None``.
        """
        deadline = time.monotonic() + self._config.stampede_timeout
        interval = self._config.stampede_poll_interval
        while time.monotonic() < deadline:
            await asyncio.sleep(interval)
            entry = await self._get_entry(full_key)
            if entry is not None:
                return entry
        return None

    def _emit_fault(self, fault: Any) -> None:
        """
        Emit a fault to the fault engine if available.

        Emission is best-effort and fire-and-forget: the fault is processed
        through the default engine on the running loop, and this method
        never raises -- a broken observability path must not turn into a
        cache failure.
        """
        try:
            from aquilia.faults.engine import get_default_engine

            engine = get_default_engine()
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._process_fault(engine, fault))
            # Hold a strong reference so the loop cannot garbage-collect
            # the emission before it runs.
            self._fault_tasks.add(task)
            task.add_done_callback(self._fault_tasks.discard)
        except Exception:
            pass  # Fault emission is best-effort

    @staticmethod
    async def _process_fault(engine: Any, fault: Any) -> None:
        """Run a fault through the engine, swallowing emission errors."""
        try:
            await engine.process(fault)
        except Exception:
            pass  # Fault emission is best-effort

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self._config.health_check_interval)
                was_healthy = self._healthy
                await self.health_check()

                if was_healthy and not self._healthy:
                    logger.error("Cache backend became unhealthy")
                    self._emit_fault(
                        CacheConnectionFault(
                            backend=self._backend.name,
                            reason="Health check failed",
                        )
                    )
                elif not was_healthy and self._healthy:
                    pass
            except asyncio.CancelledError:
                break
            except Exception:
                pass
