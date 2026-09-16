"""
AquilaCache -- Composite (L1/L2) backend.

Implements a two-level cache architecture:
- **L1** (Memory): Fast, small, short TTL
- **L2** (Redis/other): Distributed, larger, longer TTL

Read path:  L1 → L2 → miss
Write path: Write to both L1 and L2 (optionally async L2)
Delete path: Invalidate both L1 and L2

This provides sub-microsecond reads for hot data while maintaining
consistency across multiple server instances via the distributed L2.

Resilience:
- L2 failures on read degrade gracefully to L1 only
- L2 failures on write are logged but don't break the request
- Async L2 write mode available for lowest latency.  Scheduled writes are
  tracked and awaited during ``shutdown``, so a shutdown that races an
  in-flight L2 write does not silently drop it.
"""

from __future__ import annotations

import asyncio
import builtins
import contextlib
import logging
from typing import Any

from aquilia.cache.core import CacheBackend, CacheEntry, CacheStats

logger = logging.getLogger("aquilia.cache.composite")

#: Seconds to wait for pending async L2 writes during shutdown.
_DRAIN_TIMEOUT = 5.0


class CompositeBackend(CacheBackend):
    """
    Two-level cache: L1 (fast/local) + L2 (distributed/persistent).

    Read-through: L1 → L2 → miss (promote to L1 on L2 hit)
    Write-through: Write to both L1 and L2

    Features:
    - L2 error resilience (degrades to L1 on failure)
    - Optional async L2 writes, tracked so they survive to completion
    - Promotion of L2 hits into L1

    Args:
        l1: Fast local backend (typically ``MemoryBackend``).
        l2: Distributed backend (typically ``RedisBackend``).
        promote_on_l2_hit: Promote L2 hits into L1.
        async_l2_write: Schedule L2 writes in the background for lower latency.
        l1_ttl: Cap on the TTL used for L1 entries (seconds).  Promotions
            and write-throughs never outlive ``min(l1_ttl, ttl)``; L1 is a
            hot-key buffer, not a second source of truth.

    Usage::

        backend = CompositeBackend(MemoryBackend(), RedisBackend(), async_l2_write=True)
        await backend.initialize()
        await backend.set("k", "v", ttl=60)
        await backend.shutdown()   # pending L2 writes are drained here
    """

    __slots__ = ("_l1", "_l2", "_promote_on_l2_hit", "_async_l2_write", "_l1_ttl", "_l2_healthy", "_pending")

    def __init__(
        self,
        l1: CacheBackend,
        l2: CacheBackend,
        promote_on_l2_hit: bool = True,
        async_l2_write: bool = False,
        l1_ttl: int | None = None,
    ):
        self._l1 = l1
        self._l2 = l2
        self._promote_on_l2_hit = promote_on_l2_hit
        self._async_l2_write = async_l2_write
        self._l1_ttl = l1_ttl
        self._l2_healthy = True
        self._pending: set[asyncio.Task[None]] = set()

    @property
    def name(self) -> str:
        return f"composite({self._l1.name}+{self._l2.name})"

    @property
    def is_distributed(self) -> bool:
        return self._l2.is_distributed

    @property
    def pending_writes(self) -> int:
        """Number of L2 writes currently in flight."""
        return len(self._pending)

    def _schedule_l2(self, coro: Any) -> None:
        """
        Run an L2 write in the background, retaining a strong reference.

        Args:
            coro: Coroutine performing the L2 write.

        Returns:
            ``None``.

        Note:
            Untracked ``ensure_future`` tasks can be garbage-collected before
            completion; holding the task in ``_pending`` until its done-callback
            fires is what makes ``drain`` (and therefore ``shutdown``) correct.
        """
        task = asyncio.ensure_future(coro)
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def drain(self, timeout: float = _DRAIN_TIMEOUT) -> None:
        """
        Wait for in-flight async L2 writes to finish.

        Args:
            timeout: Maximum seconds to wait before cancelling stragglers.

        Returns:
            ``None``.

        Usage::

            await backend.drain(timeout=2.0)
        """
        while self._pending:
            pending = tuple(self._pending)
            _done, still_pending = await asyncio.wait(pending, timeout=timeout)
            if still_pending:
                for task in still_pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError, Exception):
                        await task
                return

    async def initialize(self) -> None:
        """Initialize both backends."""
        await self._l1.initialize()
        await self._l2.initialize()

    async def shutdown(self) -> None:
        """Drain pending L2 writes, then shut down both backends."""
        await self.drain()
        await self._l1.shutdown()
        await self._l2.shutdown()

    def _l1_effective_ttl(self, ttl: int | None) -> int | None:
        """
        Clamp a TTL for L1 storage.

        Args:
            ttl: TTL requested for the entry (``None`` = no expiry).

        Returns:
            ``min(l1_ttl, ttl)`` when both are set, ``l1_ttl`` alone when the
            requested TTL is unbounded, otherwise the requested TTL.  L1 is a
            short-lived hot-key buffer -- a promoted entry must never outlive
            ``l1_ttl``, and an unbounded one must never live forever in L1.
        """
        if self._l1_ttl is None:
            return ttl
        if ttl is None:
            return self._l1_ttl
        return min(ttl, self._l1_ttl)

    async def get(self, key: str) -> CacheEntry | None:
        """Read-through: L1 → L2, promoting on L2 hit. L2 errors degrade gracefully."""
        # Try L1 first
        entry = await self._l1.get(key)
        if entry is not None:
            return entry

        # Try L2 with error resilience
        try:
            entry = await self._l2.get(key)
        except Exception as e:
            logger.warning(f"L2 GET failed (degrading to L1-only): {e}")
            self._l2_healthy = False
            return None

        if entry is not None:
            self._l2_healthy = True
            # Promote to L1
            if self._promote_on_l2_hit:
                ttl = int(entry.ttl_remaining) if entry.ttl_remaining else None
                await self._l1.set(
                    key,
                    entry.value,
                    ttl=self._l1_effective_ttl(ttl),
                    tags=entry.tags,
                    namespace=entry.namespace,
                )
            return entry

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: tuple[str, ...] = (),
        namespace: str = "default",
    ) -> None:
        """Write-through: write to L1 always, L2 with optional async mode."""
        # L1 always synchronous, capped at l1_ttl
        await self._l1.set(key, value, ttl=self._l1_effective_ttl(ttl), tags=tags, namespace=namespace)

        # L2: async fire-and-forget or synchronous with error handling
        if self._async_l2_write:
            self._schedule_l2(self._safe_l2_set(key, value, ttl, tags, namespace))
        else:
            await self._safe_l2_set(key, value, ttl, tags, namespace)

    async def _safe_l2_set(
        self,
        key: str,
        value: Any,
        ttl: int | None,
        tags: tuple[str, ...],
        namespace: str,
    ) -> None:
        """L2 set with error resilience."""
        try:
            await self._l2.set(key, value, ttl=ttl, tags=tags, namespace=namespace)
            self._l2_healthy = True
        except Exception as e:
            logger.warning(f"L2 SET failed for key '{key}': {e}")
            self._l2_healthy = False

    async def delete(self, key: str) -> bool:
        """Invalidate in both levels."""
        l1_result = await self._l1.delete(key)
        l2_result = await self._l2.delete(key)
        return l1_result or l2_result

    async def exists(self, key: str) -> bool:
        """Check existence in either level."""
        if await self._l1.exists(key):
            return True
        return await self._l2.exists(key)

    async def clear(self, namespace: str | None = None) -> int:
        """Clear both levels."""
        l1_count = await self._l1.clear(namespace)
        l2_count = await self._l2.clear(namespace)
        return l1_count + l2_count

    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list[str]:
        """Union of keys from both levels."""
        l1_keys = set(await self._l1.keys(pattern, namespace))
        l2_keys = set(await self._l2.keys(pattern, namespace))
        return list(l1_keys | l2_keys)

    async def stats(self) -> CacheStats:
        """Combined stats from both levels."""
        l1_stats = await self._l1.stats()
        l2_stats = await self._l2.stats()

        return CacheStats(
            hits=l1_stats.hits + l2_stats.hits,
            misses=l2_stats.misses,  # Only L2 misses are true misses
            sets=l2_stats.sets,  # L2 sets == total sets
            deletes=l2_stats.deletes,
            evictions=l1_stats.evictions + l2_stats.evictions,
            errors=l1_stats.errors + l2_stats.errors,
            size=l1_stats.size + l2_stats.size,
            max_size=l1_stats.max_size + l2_stats.max_size,
            memory_bytes=l1_stats.memory_bytes + l2_stats.memory_bytes,
            backend=f"composite({l1_stats.backend}+{l2_stats.backend})",
            uptime_seconds=max(l1_stats.uptime_seconds, l2_stats.uptime_seconds),
        )

    async def delete_by_tags(self, tags: builtins.set[str]) -> int:
        """Invalidate by tags in both levels."""
        l1_count = await self._l1.delete_by_tags(tags)
        l2_count = await self._l2.delete_by_tags(tags)
        return max(l1_count, l2_count)

    async def get_many(self, keys: list[str]) -> dict[str, CacheEntry | None]:
        """Batch get with L1 → L2 fallback."""
        # Get from L1
        l1_results = await self._l1.get_many(keys)

        # Find L1 misses
        missed_keys = [k for k, v in l1_results.items() if v is None]

        if not missed_keys:
            return l1_results

        # Get misses from L2
        l2_results = await self._l2.get_many(missed_keys)

        # Promote L2 hits to L1
        if self._promote_on_l2_hit:
            for key, entry in l2_results.items():
                if entry is not None:
                    ttl = int(entry.ttl_remaining) if entry.ttl_remaining else None
                    await self._l1.set(
                        key,
                        entry.value,
                        ttl=self._l1_effective_ttl(ttl),
                        tags=entry.tags,
                        namespace=entry.namespace,
                    )

        # Merge results
        final = {}
        for key in keys:
            final[key] = l1_results.get(key) or l2_results.get(key)
        return final

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
        namespace: str = "default",
        tags: tuple[str, ...] = (),
    ) -> None:
        """Write-through batch set with async L2 option."""
        await self._l1.set_many(items, ttl=self._l1_effective_ttl(ttl), namespace=namespace, tags=tags)
        if self._async_l2_write:
            self._schedule_l2(self._safe_l2_set_many(items, ttl, namespace, tags))
        else:
            await self._safe_l2_set_many(items, ttl, namespace, tags)

    async def _safe_l2_set_many(
        self,
        items: dict[str, Any],
        ttl: int | None,
        namespace: str,
        tags: tuple[str, ...],
    ) -> None:
        """L2 batch set with error resilience."""
        try:
            await self._l2.set_many(items, ttl=ttl, namespace=namespace, tags=tags)
            self._l2_healthy = True
        except Exception as e:
            logger.warning(f"L2 SET_MANY failed: {e}")
            self._l2_healthy = False

    async def increment(self, key: str, delta: int = 1) -> int | None:
        """
        Increment in L2 (authoritative) and invalidate L1.

        L1 is dropped rather than refreshed: a promoted copy is stale the
        moment the L2 counter moves, and re-reading L2 to refresh it still
        races with concurrent increments (the reader would cache a value
        that is already outdated).  The next ``get`` re-promotes.
        """
        result = await self._l2.increment(key, delta)
        if result is not None:
            await self._l1.delete(key)
        return result

    async def touch(self, key: str, ttl: int) -> bool:
        """
        Refresh a key's TTL in both levels.

        Args:
            key: Key to refresh.
            ttl: New TTL in seconds.

        Returns:
            True if either level held the entry and was refreshed.
        """
        l1_touch = getattr(self._l1, "touch", None)
        l2_touch = getattr(self._l2, "touch", None)
        l1_result = bool(await l1_touch(key, ttl)) if l1_touch is not None else False
        l2_result = bool(await l2_touch(key, ttl)) if l2_touch is not None else False
        return l1_result or l2_result

    async def health_check(self) -> bool:
        """Check health of both levels."""
        l1_ok = True
        l2_ok = True

        if hasattr(self._l1, "health_check"):
            l1_ok = await self._l1.health_check()
        if hasattr(self._l2, "health_check"):
            l2_ok = await self._l2.health_check()

        self._l2_healthy = l2_ok
        return l1_ok  # L1 health is critical; L2 degradation is acceptable

    # ── Distributed locking ──────────────────────────────────────────

    @property
    def supports_distributed_lock(self) -> bool:
        """Locks are coordinated through L2, the level visible to every process."""
        return self._l2.supports_distributed_lock

    async def try_acquire_lock(self, key: str, ttl: float) -> str | None:
        """
        Attempt a cross-process lock via L2.

        Args:
            key: Lock key, already fully qualified.
            ttl: Lock lease in seconds.

        Returns:
            An opaque token from L2, or ``None`` if another holder owns it.
        """
        return await self._l2.try_acquire_lock(key, ttl)

    async def release_lock(self, key: str, token: str) -> bool:
        """
        Release a previously acquired L2 lock.

        Args:
            key: Lock key.
            token: Token returned by the matching acquire call.

        Returns:
            True if this caller held the lock and released it.
        """
        return await self._l2.release_lock(key, token)

    @property
    def l2_healthy(self) -> bool:
        """Whether the L2 backend is currently healthy."""
        return self._l2_healthy
