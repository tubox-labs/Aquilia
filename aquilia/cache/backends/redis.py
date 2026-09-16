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
from urllib.parse import urlparse

from aquilia.cache.core import CacheBackend, CacheEntry, CacheStats

logger = logging.getLogger("aquilia.cache.redis")

#: Seconds a command may wait for a free connection before giving up.
#:
#: The pool is a ``BlockingConnectionPool``: when all connections are busy,
#: callers queue instead of failing instantly, so a short burst of requests
#: degrades to queuing rather than to silently dropped writes.
_POOL_ACQUIRE_TIMEOUT: float = 30.0

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
        decode_responses: Ask redis-py to decode replies as ``str``.  The
            default is ``False`` because values are handed to the configured
            serializer as bytes; replies are normalised either way.
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
        "_decode_responses",
        "_key_prefix",
        "_serializer",
        "_redis",
        "_pool",
        "_db",
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
        decode_responses: bool = False,
        key_prefix: str = "aq:",
        serializer: Any | None = None,
    ):
        self._url = url
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._connect_timeout = connect_timeout
        self._retry_on_timeout = retry_on_timeout
        self._decode_responses = decode_responses
        self._key_prefix = key_prefix
        self._db = self._parse_db_index(url)
        self._redis = None
        self._pool = None
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

    @staticmethod
    def _parse_db_index(url: str) -> int:
        """
        Extract the logical DB index from a Redis URL.

        Args:
            url: Connection URL such as ``redis://host:6379/15``.

        Returns:
            The DB number (0 when the URL carries no path segment).
        """
        path = urlparse(url).path
        if not path or path == "/":
            return 0
        try:
            return int(path.strip("/"))
        except ValueError:
            return 0

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
            # A blocking pool queues callers when all connections are busy
            # instead of raising "Too many connections" on the spot -- with
            # the never-raise contract on each operation, an eagerly-failing
            # pool turned every burst into silently dropped writes.
            self._pool = aioredis.BlockingConnectionPool.from_url(
                self._url,
                max_connections=self._max_connections,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._connect_timeout,
                retry_on_timeout=self._retry_on_timeout,
                decode_responses=self._decode_responses,
                timeout=_POOL_ACQUIRE_TIMEOUT,
            )
            self._redis = aioredis.Redis(connection_pool=self._pool)
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
            # redis-py 8 deprecates close() in favour of aclose(); support
            # both so a redis-py 5 install keeps working.
            closer = getattr(self._redis, "aclose", None) or self._redis.close
            await closer()
            # An explicitly supplied pool is not auto-closed by the client;
            # disconnect it ourselves so no sockets are leaked.
            if self._pool is not None:
                await self._pool.disconnect()
            self._redis = None
            self._pool = None
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

    @staticmethod
    def _as_bytes(value: Any) -> bytes:
        """Normalise a raw reply to ``bytes`` for the serializer."""
        return value.encode("utf-8") if isinstance(value, str) else value

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

            value = self._serializer.deserialize(self._as_bytes(raw))
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
                pipe.set(full_key, serialized, ex=ttl)
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

            # Register in namespace set.  Mirror the tag-set TTL so the
            # index self-prunes once its last member has expired; without
            # it, namespace sets grew without bound.
            ns_key = self._ns_set_key(namespace)
            pipe.sadd(ns_key, full_key)
            if ttl and ttl > 0:
                pipe.expire(ns_key, ttl + 60)

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
        Clear a namespace, or every entry this cache has registered.

        Args:
            namespace: Namespace to clear, or ``None`` for everything this
                backend itself wrote.

        Returns:
            Number of entries deleted.

        Note:
            A full clear never scans-and-deletes by raw prefix: a prefix is
            shared with any other user of the database, so a blind
            ``SCAN match <prefix>*`` deleted foreign keys that merely
            happened to share it.  Instead, only keys registered in the
            cache's own namespace index (and the index/sidecar keys derived
            from them) are removed.
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
                # Registry-driven full clear: the namespace index names
                # exactly the data keys this backend stored, so foreign keys
                # sharing the prefix are never touched.
                ns_sets = await self._scan_keys(f"{self._key_prefix}_ns:*")
                tag_sets = await self._scan_keys(f"{self._key_prefix}_tags:*")
                if not ns_sets and not tag_sets:
                    return 0

                pipe = self._redis.pipeline()
                count = 0
                for set_key in ns_sets:
                    for member in await self._live_members(set_key):
                        pipe.delete(member)
                        pipe.delete(self._meta_key(self._strip_prefix(member)))
                        count += 1
                    pipe.delete(set_key)
                for set_key in tag_sets:
                    pipe.delete(set_key)
                await pipe.execute()
                return count
        except Exception as e:
            logger.warning(f"Redis CLEAR error: {e}")
            self._stats.errors += 1
            return 0

    async def _scan_keys(self, match: str) -> list[str]:
        """
        Collect every key matching a glob pattern via SCAN.

        Args:
            match: Glob pattern (already fully qualified).

        Returns:
            Matching keys, decoded to ``str``.
        """
        result: list[str] = []
        cursor = 0
        while True:
            cursor, batch = await self._redis.scan(cursor=cursor, match=match, count=1000)
            result.extend(self._decode(k) for k in batch)
            if cursor == 0:
                break
        return result

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
                # Registry-driven, mirroring the namespace branch: only keys
                # this cache registered are listed, so foreign keys that
                # merely share a prefix never leak into diagnostics.
                keys = []
                seen: set[str] = set()
                for set_key in await self._scan_keys(f"{self._key_prefix}_ns:*"):
                    for member in await self._live_members(set_key):
                        stripped = self._strip_prefix(member)
                        if stripped not in seen:
                            seen.add(stripped)
                            keys.append(stripped)

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

                # Count keys in the DB this backend actually connects to,
                # parsed from the connection URL (db0 only by coincidence).
                db_info = info.get(f"db{self._db}", {})
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
        """
        Pipelined batch get, restoring tags, namespace, and expiry.

        Values, per-key TTLs, and per-key sidecar metadata are fetched in a
        single pipeline round trip so each hit yields the same fully
        populated entry a single ``get`` would -- tag-less, expiry-less
        entries poisoned L1 promotion in ``CompositeBackend``.
        """
        if not self._redis or not keys:
            return {k: None for k in keys}

        try:
            pipe = self._redis.pipeline()
            pipe.mget([self._full_key(k) for k in keys])
            for k in keys:
                pipe.pttl(self._full_key(k))
                pipe.hgetall(self._meta_key(k))
            replies = await pipe.execute()

            values = replies[0]
            per_key = replies[1:]  # (pttl, meta) pairs, in key order

            results = {}
            for i, key in enumerate(keys):
                raw = values[i]
                if raw is None:
                    self._stats.misses += 1
                    results[key] = None
                    continue

                pttl, meta = per_key[i * 2], per_key[i * 2 + 1]

                try:
                    value = self._serializer.deserialize(self._as_bytes(raw))
                except Exception:
                    self._stats.errors += 1
                    results[key] = None
                    continue

                self._stats.hits += 1

                expires_at = None
                if pttl and pttl > 0:
                    expires_at = time.monotonic() + pttl / 1000.0

                tags: tuple[str, ...] = ()
                namespace = "default"
                if meta:
                    decoded = {self._decode(k): self._decode(v) for k, v in meta.items()}
                    raw_tags = decoded.get("tags", "")
                    tags = tuple(t for t in raw_tags.split("\x1f") if t)
                    namespace = decoded.get("namespace", "default")

                results[key] = CacheEntry(
                    key=key,
                    value=value,
                    expires_at=expires_at,
                    tags=tags,
                    namespace=namespace,
                )

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
        tags: tuple[str, ...] = (),
    ) -> None:
        """
        Pipelined batch set.

        Every key receives the same sidecar/tag/namespace bookkeeping a
        single ``set`` performs, so ``set_many`` entries remain valid
        targets for tag and namespace invalidation.
        """
        if not self._redis or not items:
            return

        try:
            pipe = self._redis.pipeline()

            for key, value in items.items():
                full_key = self._full_key(key)
                meta_key = self._meta_key(key)
                serialized = self._serializer.serialize(value)

                if ttl and ttl > 0:
                    pipe.set(full_key, serialized, ex=ttl)
                else:
                    pipe.set(full_key, serialized)

                # Sidecar metadata so get()/get_many() can restore tags/namespace.
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
                        pipe.expire(tag_key, ttl + 60)

                # Register in namespace set, mirroring the entry's TTL.
                ns_key = self._ns_set_key(namespace)
                pipe.sadd(ns_key, full_key)
                if ttl and ttl > 0:
                    pipe.expire(ns_key, ttl + 60)

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

    async def touch(self, key: str, ttl: int) -> bool:
        """
        Refresh a key's TTL atomically via ``EXPIRE``.

        The stored value, its sidecar metadata, tags, and namespace are all
        preserved -- unlike a get+set cycle, nothing is re-serialised, so a
        touch can never corrupt or drop an entry's tags.

        Args:
            key: Unprefixed cache key.
            ttl: New TTL in seconds (<= 0 removes the expiry).

        Returns:
            True if the key existed and was refreshed, False on miss.
        """
        if not self._redis:
            return False

        full_key = self._full_key(key)

        try:
            pipe = self._redis.pipeline()
            if ttl > 0:
                # EXPIRE with 0 would DELETE the key -- never pass a non-positive TTL.
                pipe.expire(full_key, ttl)
            else:
                pipe.persist(full_key)
            # Keep the meta sidecar alive exactly as long as the entry, so
            # tags/namespace stay readable for the extended lifetime.
            if ttl > 0:
                pipe.expire(self._meta_key(key), ttl)
            else:
                pipe.persist(self._meta_key(key))
            renewed, _meta_renewed = await pipe.execute()
            return bool(renewed)
        except Exception as e:
            logger.warning(f"Redis TOUCH error for key '{key}': {e}")
            self._stats.errors += 1
            return False

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
