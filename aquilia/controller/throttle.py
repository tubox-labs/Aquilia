import asyncio
import logging
import time
from typing import Protocol

logger = logging.getLogger("aquilia.throttle")


class ThrottleBackend(Protocol):
    async def is_allowed(self, key: str, limit: int, window: int) -> bool: ...

    async def get_count(self, key: str, window: int) -> int: ...

    async def reset(self, key: str | None = None) -> None: ...

    async def close(self) -> None: ...


class MemoryThrottleBackend:
    def __init__(self, max_clients: int = 10000):
        self.max_clients = max_clients
        self._requests: dict[str, list[float]] = {}
        self._last_cleanup: float = 0.0
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()

        async with self._lock:
            if now - self._last_cleanup > window:
                self._cleanup_expired(now, window)
                self._last_cleanup = now

            if key not in self._requests:
                if len(self._requests) >= self.max_clients:
                    self._evict_oldest()
                self._requests[key] = []

            cutoff = now - window
            self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

            if len(self._requests[key]) >= limit:
                return False

            self._requests[key].append(now)
            return True

    async def get_count(self, key: str, window: int) -> int:
        now = time.monotonic()
        async with self._lock:
            if key not in self._requests:
                return 0
            cutoff = now - window
            return len([ts for ts in self._requests[key] if ts > cutoff])

    async def reset(self, key: str | None = None) -> None:
        async with self._lock:
            if key is None:
                self._requests.clear()
            elif key in self._requests:
                del self._requests[key]

    async def close(self) -> None:
        pass

    def _cleanup_expired(self, now: float, window: int) -> None:
        cutoff = now - window
        expired_keys = [k for k, timestamps in self._requests.items() if not timestamps or timestamps[-1] <= cutoff]
        for k in expired_keys:
            del self._requests[k]

    def _evict_oldest(self) -> None:
        if not self._requests:
            return
        oldest_key = min(self._requests.keys(), key=lambda k: self._requests[k][-1] if self._requests[k] else 0.0)
        del self._requests[oldest_key]


class RedisThrottleBackend:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "aq:throttle:",
        fail_open: bool = True,
        **kwargs,
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.fail_open = fail_open
        self.kwargs = kwargs
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as redis_async
            except ImportError:
                raise ImportError("redis is not installed. Please install it using `pip install aquilia[redis]`")

            self._redis = redis_async.from_url(self.redis_url, **self.kwargs)
        return self._redis

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        redis_key = f"{self.key_prefix}{key}"
        now = time.time()
        cutoff = now - window

        try:
            r = self.redis
            pipeline = r.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, cutoff)
            pipeline.zcard(redis_key)
            pipeline.zadd(redis_key, {str(now): now})
            pipeline.expire(redis_key, window)
            results = await pipeline.execute()

            count = results[1]
            if count >= limit:
                return False
            return True
        except Exception as e:
            logger.warning(f"RedisThrottleBackend error: {e}")
            if self.fail_open:
                return True
            raise

    async def get_count(self, key: str, window: int) -> int:
        redis_key = f"{self.key_prefix}{key}"
        now = time.time()
        cutoff = now - window

        try:
            r = self.redis
            pipeline = r.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, cutoff)
            pipeline.zcard(redis_key)
            results = await pipeline.execute()
            return results[1]
        except Exception as e:
            logger.warning(f"RedisThrottleBackend error in get_count: {e}")
            return 0

    async def reset(self, key: str | None = None) -> None:
        try:
            r = self.redis
            if key is None:
                # Not easily supported to clear all without scan, just do nothing or raise error?
                # A SCAN to delete all prefixed keys would work.
                cursor = "0"
                while cursor != 0:
                    cursor, keys = await r.scan(cursor=cursor, match=f"{self.key_prefix}*", count=100)
                    if keys:
                        await r.delete(*keys)
            else:
                redis_key = f"{self.key_prefix}{key}"
                await r.delete(redis_key)
        except Exception as e:
            logger.warning(f"RedisThrottleBackend error in reset: {e}")

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()


class ThrottleBackendFactory:
    _registry = {
        "memory": MemoryThrottleBackend,
    }

    @classmethod
    def register(cls, name: str, backend_class: type[ThrottleBackend]) -> None:
        cls._registry[name] = backend_class

    @classmethod
    def create(cls, config: str, **kwargs) -> ThrottleBackend:
        if config == "memory":
            return cls._registry["memory"](**kwargs)
        elif config.startswith("redis://") or config.startswith("rediss://"):
            return RedisThrottleBackend(redis_url=config, **kwargs)

        for name, backend_cls in cls._registry.items():
            if config.startswith(name):
                return backend_cls(**kwargs)

        raise ValueError(f"Unknown throttle backend config: {config}")
