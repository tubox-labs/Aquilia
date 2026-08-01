"""
AquilaCache -- Redis backend for distributed caching.

Production-grade Redis integration with:
- Connection pooling
- Pipeline batching for get_many/set_many
- Lua scripts for atomic read-modify-write operations
- Tag-based invalidation via Redis sets, with self-pruning membership
- Health checks and reconnection
- Serialization via pluggable CacheSerializer

Tag and namespace sets are pruned opportunistically: reads through
``delete_by_tags``/``clear`` drop members whose underlying key has expired,
so sets do not accumulate indefinitely under natural TTL expiry.
"""

from __future__ import annotations

import builtins
import fnmatch
import logging
import time
import uuid
from typing import Any

from aquilia.cache.core import CacheBackend, CacheEntry, CacheStats

logger = logging.getLogger("aquilia.cache.redis")

#: Atomically increment a counter only when it already exists.
#:
#: Redis' plain ``INCRBY`` creates missing keys, and a separate ``EXISTS``
#: check-then-act is racy: two callers can both observe "missing" and both
#: return None while a third creates the key.  Evaluating both steps inside
#: one script makes the decision atomic.
_INCR_IF_EXISTS_LUA = """
if redis.call('EXISTS', KEYS[1]) == 0 then
  return nil
end
return redis.call('INCRBY', KEYS[1], ARGV[1])
"""

#: Return only those set members that still resolve to a live key, deleting
#: the rest from the set.  Keeps tag/namespace sets bounded when entries
#: disappear through Redis' own TTL expiry rather than an explicit delete.
_PRUNE_SET_LUA = """
local members = redis.call('SMEMBERS', KEYS[1])
local live = {}
local dead = {}
for i = 1, #members do
  if redis.call('EXISTS', members[i]) == 1 then
    live[#live + 1] = members[i]
  else
    dead[#dead + 1] = members[i]
  end
end
if #dead > 0 then
  redis.call('SREM', KEYS[1], unpack(dead))
end
return live
"""


#: Release a lock only when the caller still owns it.
#:
#: A naive DEL would let a worker whose lease already expired delete the lock
#: another worker has since acquired.
_RELEASE_LOCK_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


class RedisBackend(CacheBackend):
    """
    Redis-backed cache using redis-py's asyncio client.

    Features:
    - Connection pool with configurable size
    - Pipeline batching for bulk operations
    - Lua-based atomic increment/decrement (no check-then-act race)
    - Tag index via Redis sets for O(1) tag invalidation, self-pruning
    - Tags round-trip through ``get()``, matching MemoryBackend semantics
    - Automatic reconnection on transient failures

    Args:
        url: Redis connection URL.
        max_connections: Connection pool size.
        socket_timeout: Per-command socket timeout in seconds.
        connect_timeout: Connection establishment timeout in seconds.
        retry_on_timeout: Retry commands that time out.
        key_prefix: Prefix applied to every key this backend writes.
        serializer: Value serializer; defaults to JSON.

    Usage::

        backend = RedisBackend(url="redis://localhost:6379/0")
        await backend.initialize()
        await backend.set("user:1", {"id": 1}, ttl=60, tags=("users",))
    """

    __slots__ = (
        "_url",
        "_max_connections",
        "_socket_timeout",
        "_connect_timeout",
        "_retry_on_timeout",
        "_key_prefix",
        "_serializer",
        "_redis",
        "_stats",
        "_start_time",
        "_initialized",
        "_incr_script",
        "_prune_script",
        "_release_script",
    )

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        key_prefix: str = "aq:",
        serializer: Any | None = None,
    ):
        self._url = url
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._connect_timeout = connect_timeout
        self._retry_on_timeout = retry_on_timeout
        self._key_prefix = key_prefix
        self._redis = None
        self._stats = CacheStats(backend="redis")
        self._start_time = time.monotonic()
        self._initialized = False
        self._incr_script: Any = None
        self._prune_script: Any = None
        self._release_script: Any = None

        # Use JSON serializer by default
        if serializer is None:
            from aquilia.cache.serializers import JsonCacheSerializer

            self._serializer = JsonCacheSerializer()
        else:
            self._serializer = serializer

    @property
    def name(self) -> str:
        return "redis"

    @property
    def is_distributed(self) -> bool:
        return True

    async def initialize(self) -> None:
        """Connect to Redis and create connection pool."""
        if self._initialized:
            return

        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError("Redis backend requires 'redis' package. Install with: pip install redis[hiredis]")

        try:
            self._redis = aioredis.from_url(
                self._url,
                max_connections=self._max_connections,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._connect_timeout,
                retry_on_timeout=self._retry_on_timeout,
                decode_responses=False,  # We handle serialization
            )
            # Verify connection
            await self._redis.ping()
            self._incr_script = self._redis.register_script(_INCR_IF_EXISTS_LUA)
            self._prune_script = self._redis.register_script(_PRUNE_SET_LUA)
            self._release_script = self._redis.register_script(_RELEASE_LOCK_LUA)
            self._start_time = time.monotonic()
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def shutdown(self) -> None:
        """Close Redis connection pool."""
        if self._redis:
            await self._redis.close()
            self._redis = None
        self._initialized = False

    def _full_key(self, key: str) -> str:
        """Build prefixed key."""
        return f"{self._key_prefix}{key}"

    def _tag_set_key(self, tag: str) -> str:
        """Build Redis set key for a tag."""
        return f"{self._key_prefix}_tags:{tag}"

    def _ns_set_key(self, namespace: str) -> str:
        """Build Redis set key for a namespace."""
        return f"{self._key_prefix}_ns:{namespace}"

    def _meta_key(self, key: str) -> str:
        """Build the sidecar key holding an entry's tags and namespace."""
        return f"{self._key_prefix}_meta:{key}"

    @staticmethod
    def _decode(value: Any) -> str:
        """Decode a Redis reply to ``str`` regardless of byte/str mode."""
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)

    async def get(self, key: str) -> CacheEntry | None:
        """
        Fetch an entry, restoring its tags and namespace.

        Args:
            key: Unprefixed cache key.

        Returns:
            The reconstructed :class:`CacheEntry`, or ``None`` on miss or error.

        Note:
            Tags and namespace are read from a sidecar key written by ``set``,
            so ``entry.tags`` is populated exactly as with ``MemoryBackend``.
        """
        if not self._redis:
            self._stats.errors += 1
            return None

        full_key = self._full_key(key)

        try:
            pipe = self._redis.pipeline()
            pipe.get(full_key)
            pipe.ttl(full_key)
            pipe.hgetall(self._meta_key(key))
            raw, ttl, meta = await pipe.execute()

            if raw is None:
                self._stats.misses += 1
                return None

            value = self._serializer.deserialize(raw)
            self._stats.hits += 1

            expires_at = None
            if ttl and ttl > 0:
                expires_at = time.monotonic() + ttl

            tags: tuple[str, ...] = ()
            namespace = "default"
            if meta:
                decoded = {self._decode(k): self._decode(v) for k, v in meta.items()}
                raw_tags = decoded.get("tags", "")
                tags = tuple(t for t in raw_tags.split("\x1f") if t)
                namespace = decoded.get("namespace", "default")

            return CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
                tags=tags,
                namespace=namespace,
            )
        except Exception as e:
            logger.warning(f"Redis GET error for key '{key}': {e}")
            self._stats.errors += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: tuple[str, ...] = (),
        namespace: str = "default",
    ) -> None:
        """
        Store a value with optional TTL, tags, and namespace.

        Args:
            key: Unprefixed cache key.
            value: Value to serialize and store.
            ttl: Time-to-live in seconds; ``None`` or ``0`` means no expiry.
            tags: Tags for group invalidation.
            namespace: Namespace for scoped clears.

        Returns:
            ``None``.

        Note:
            Tags/namespace are mirrored into a sidecar hash that carries the
            same TTL as the entry, so it disappears with the entry instead of
            leaking.
        """
        if not self._redis:
            self._stats.errors += 1
            return

        full_key = self._full_key(key)
        meta_key = self._meta_key(key)

        try:
            serialized = self._serializer.serialize(value)

            pipe = self._redis.pipeline()

            if ttl and ttl > 0:
                pipe.setex(full_key, ttl, serialized)
            else:
                pipe.set(full_key, serialized)

            # Sidecar metadata so get() can restore tags/namespace.
            pipe.delete(meta_key)
            pipe.hset(
                meta_key,
                mapping={"tags": "\x1f".join(tags), "namespace": namespace},
            )
            if ttl and ttl > 0:
                pipe.expire(meta_key, ttl)

            # Register in tag sets
            for tag in tags:
                tag_key = self._tag_set_key(tag)
                pipe.sadd(tag_key, full_key)
                if ttl and ttl > 0:
                    # Extend tag set TTL to at least match entry TTL
                    pipe.expire(tag_key, ttl + 60)

            # Register in namespace set
            ns_key = self._ns_set_key(namespace)
            pipe.sadd(ns_key, full_key)

            await pipe.execute()
            self._stats.sets += 1
        except Exception as e:
            logger.warning(f"Redis SET error for key '{key}': {e}")
            self._stats.errors += 1

    async def _live_members(self, set_key: str) -> list[str]:
        """
        Return the still-live members of a tag/namespace set, pruning dead ones.

        Args:
            set_key: Fully-qualified Redis set key.

        Returns:
            Members whose underlying cache key still exists.

        Note:
            Keys that expired via Redis' own TTL leave stale set membership
            behind; this removes them in the same round trip that reads them.
        """
        if not self._prune_script:
            members = await self._redis.smembers(set_key)
            return [self._decode(m) for m in members]
        members = await self._prune_script(keys=[set_key])
        return [self._decode(m) for m in members]

    async def delete(self, key: str) -> bool:
        """
        Delete a key and its sidecar metadata.

        Args:
            key: Unprefixed cache key.

        Returns:
            True if the entry existed.
        """
        if not self._redis:
            return False

        full_key = self._full_key(key)

        try:
            pipe = self._redis.pipeline()
            pipe.delete(full_key)
            pipe.delete(self._meta_key(key))
            results = await pipe.execute()
            if results and results[0]:
                self._stats.deletes += 1
                return True
            return False
        except Exception as e:
            logger.warning(f"Redis DELETE error for key '{key}': {e}")
            self._stats.errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._redis:
            return False

        try:
            return bool(await self._redis.exists(self._full_key(key)))
        except Exception as e:
            logger.warning(f"Redis EXISTS error for key '{key}': {e}")
            return False

    async def clear(self, namespace: str | None = None) -> int:
        """
        Clear a namespace, or every key carrying this backend's prefix.

        Args:
            namespace: Namespace to clear, or ``None`` for everything.

        Returns:
            Number of entries deleted.
        """
        if not self._redis:
            return 0

        try:
            if namespace:
                ns_key = self._ns_set_key(namespace)
                members = await self._live_members(ns_key)
                if members:
                    pipe = self._redis.pipeline()
                    for member in members:
                        pipe.delete(member)
                        pipe.delete(self._meta_key(self._strip_prefix(member)))
                    pipe.delete(ns_key)
                    await pipe.execute()
                    return len(members)
                await self._redis.delete(ns_key)
                return 0
            else:
                # Clear all keys with our prefix
                count = 0
                cursor = 0
                while True:
                    cursor, keys = await self._redis.scan(
                        cursor=cursor,
                        match=f"{self._key_prefix}*",
                        count=1000,
                    )
                    if keys:
                        await self._redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
                return count
        except Exception as e:
            logger.warning(f"Redis CLEAR error: {e}")
            self._stats.errors += 1
            return 0

    def _strip_prefix(self, full_key: str) -> str:
        """Return the unprefixed form of a fully-qualified key."""
        if full_key.startswith(self._key_prefix):
            return full_key[len(self._key_prefix) :]
        return full_key

    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list[str]:
        """List keys matching pattern."""
        if not self._redis:
            return []

        try:
            if namespace:
                ns_key = self._ns_set_key(namespace)
                raw_keys = await self._live_members(ns_key)
                # Strip prefix
                prefix_len = len(self._key_prefix)
                keys = [k[prefix_len:] for k in raw_keys if k.startswith(self._key_prefix)]
            else:
                full_pattern = f"{self._key_prefix}{pattern}"
                result = []
                cursor = 0
                while True:
                    cursor, batch = await self._redis.scan(
                        cursor=cursor,
                        match=full_pattern,
                        count=1000,
                    )
                    result.extend(batch)
                    if cursor == 0:
                        break
                prefix_len = len(self._key_prefix)
                internal = (
                    f"{self._key_prefix}_tags:",
                    f"{self._key_prefix}_ns:",
                    f"{self._key_prefix}_meta:",
                )
                keys = []
                for k in result:
                    s = self._decode(k)
                    if s.startswith(self._key_prefix) and not s.startswith(internal):
                        keys.append(s[prefix_len:])

            if pattern != "*":
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]

            return keys
        except Exception as e:
            logger.warning(f"Redis KEYS error: {e}")
            return []

    async def stats(self) -> CacheStats:
        """Get Redis stats."""
        self._stats.uptime_seconds = time.monotonic() - self._start_time

        if self._redis:
            try:
                info = await self._redis.info("memory", "keyspace")
                self._stats.memory_bytes = info.get("used_memory", 0)

                # Count keys
                db_info = info.get("db0", {})
                if isinstance(db_info, dict):
                    self._stats.size = db_info.get("keys", 0)
            except Exception:
                pass

        return self._stats

    async def delete_by_tags(self, tags: builtins.set[str]) -> int:
        """
        Delete every entry carrying any of the given tags.

        Args:
            tags: Tags to invalidate.

        Returns:
            Number of live entries deleted.

        Note:
            Membership of keys that already expired naturally is pruned as a
            side effect, keeping tag sets bounded.
        """
        if not self._redis:
            return 0

        try:
            keys_to_delete: set[str] = set()
            for tag in tags:
                keys_to_delete.update(await self._live_members(self._tag_set_key(tag)))

            if not keys_to_delete:
                # Still drop the (now empty) tag sets.
                pipe = self._redis.pipeline()
                for tag in tags:
                    pipe.delete(self._tag_set_key(tag))
                await pipe.execute()
                return 0

            # Delete all keys, their sidecars, and the tag sets
            pipe = self._redis.pipeline()
            for key in keys_to_delete:
                pipe.delete(key)
                pipe.delete(self._meta_key(self._strip_prefix(key)))
            for tag in tags:
                pipe.delete(self._tag_set_key(tag))
            await pipe.execute()

            self._stats.deletes += len(keys_to_delete)
            return len(keys_to_delete)
        except Exception as e:
            logger.warning(f"Redis tag deletion error: {e}")
            self._stats.errors += 1
            return 0

    async def get_many(self, keys: list[str]) -> dict[str, CacheEntry | None]:
        """Pipelined batch get."""
        if not self._redis or not keys:
            return {k: None for k in keys}

        try:
            full_keys = [self._full_key(k) for k in keys]
            values = await self._redis.mget(full_keys)

            results = {}
            for key, raw in zip(keys, values, strict=False):
                if raw is None:
                    self._stats.misses += 1
                    results[key] = None
                else:
                    try:
                        value = self._serializer.deserialize(raw)
                        self._stats.hits += 1
                        results[key] = CacheEntry(key=key, value=value)
                    except Exception:
                        self._stats.errors += 1
                        results[key] = None

            return results
        except Exception as e:
            logger.warning(f"Redis MGET error: {e}")
            self._stats.errors += 1
            return {k: None for k in keys}

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
        namespace: str = "default",
    ) -> None:
        """Pipelined batch set."""
        if not self._redis or not items:
            return

        try:
            pipe = self._redis.pipeline()

            for key, value in items.items():
                full_key = self._full_key(key)
                serialized = self._serializer.serialize(value)

                if ttl and ttl > 0:
                    pipe.setex(full_key, ttl, serialized)
                else:
                    pipe.set(full_key, serialized)

                ns_key = self._ns_set_key(namespace)
                pipe.sadd(ns_key, full_key)

            await pipe.execute()
            self._stats.sets += len(items)
        except Exception as e:
            logger.warning(f"Redis MSET error: {e}")
            self._stats.errors += 1

    async def increment(self, key: str, delta: int = 1) -> int | None:
        """
        Atomically increment an existing counter.

        Args:
            key: Unprefixed cache key.
            delta: Amount to add (may be negative).

        Returns:
            The new value, or ``None`` if the key does not exist.

        Note:
            The existence check and the ``INCRBY`` run inside one Lua script,
            so concurrent callers cannot both observe "missing" and race.
            Absent keys are never created, matching ``MemoryBackend``.
        """
        if not self._redis:
            return None

        try:
            full_key = self._full_key(key)
            if self._incr_script is None:
                self._incr_script = self._redis.register_script(_INCR_IF_EXISTS_LUA)
            result = await self._incr_script(keys=[full_key], args=[delta])
            return None if result is None else int(result)
        except Exception as e:
            logger.warning(f"Redis INCRBY error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        if not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False

    # ── Distributed locking ──────────────────────────────────────────

    @property
    def supports_distributed_lock(self) -> bool:
        """Redis locks are visible to every process sharing the server."""
        return True

    async def try_acquire_lock(self, key: str, ttl: float) -> str | None:
        """
        Acquire a cross-process lock via ``SET NX PX``.

        Args:
            key: Lock key (already namespaced by the caller).
            ttl: Lease duration in seconds.  The lock self-expires so a crashed
                holder cannot deadlock the fleet.

        Returns:
            A random ownership token, or ``None`` if the lock is held elsewhere.

        Usage::

            token = await backend.try_acquire_lock("lock:user:1", ttl=30.0)
        """
        if not self._redis:
            return None

        token = uuid.uuid4().hex
        try:
            acquired = await self._redis.set(
                self._full_key(key),
                token,
                nx=True,
                px=max(1, int(ttl * 1000)),
            )
        except Exception as e:
            logger.warning(f"Redis lock acquire error for '{key}': {e}")
            return None
        return token if acquired else None

    async def release_lock(self, key: str, token: str) -> bool:
        """
        Release a lock, but only if this caller still owns it.

        Args:
            key: Lock key.
            token: Token returned by ``try_acquire_lock``.

        Returns:
            True if the lock was owned by this caller and released.
        """
        if not self._redis:
            return False
        try:
            if self._release_script is None:
                self._release_script = self._redis.register_script(_RELEASE_LOCK_LUA)
            result = await self._release_script(keys=[self._full_key(key)], args=[token])
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis lock release error for '{key}': {e}")
            return False
