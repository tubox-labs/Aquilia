import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from aquilia.controller.base import Throttle
from aquilia.controller.throttle import (
    MemoryThrottleBackend,
    RedisThrottleBackend,
    ThrottleBackendFactory,
)


class DummyRequest:
    def __init__(self, ip="127.0.0.1"):
        self._ip = ip

    def client_ip(self):
        return self._ip


@pytest.mark.asyncio
async def test_memory_throttle_backend():
    backend = MemoryThrottleBackend(max_clients=10)

    # Under limit
    assert await backend.is_allowed("test1", limit=2, window=10) is True
    assert await backend.is_allowed("test1", limit=2, window=10) is True

    # Over limit
    assert await backend.is_allowed("test1", limit=2, window=10) is False

    # Check count
    assert await backend.get_count("test1", window=10) == 2
    assert await backend.get_count("test2", window=10) == 0

    # Reset
    await backend.reset("test1")
    assert await backend.get_count("test1", window=10) == 0


@pytest.mark.asyncio
async def test_redis_throttle_backend_fail_open(monkeypatch):
    backend = RedisThrottleBackend(redis_url="redis://localhost:6379", fail_open=True)

    # Mock redis to raise error
    backend._redis = MagicMock()
    mock_pipeline = MagicMock()  # pipeline queuing calls are sync
    mock_pipeline.execute = AsyncMock(side_effect=Exception("Redis connection error"))
    backend._redis.pipeline.return_value = mock_pipeline

    # Should allow request when fail_open is True
    assert await backend.is_allowed("test1", limit=2, window=10) is True
    assert await backend.get_count("test1", window=10) == 0


@pytest.mark.asyncio
async def test_redis_throttle_backend_fail_closed(monkeypatch):
    backend = RedisThrottleBackend(redis_url="redis://localhost:6379", fail_open=False)

    # Mock redis to raise error
    backend._redis = MagicMock()
    mock_pipeline = MagicMock()  # pipeline queuing calls are sync
    mock_pipeline.execute = AsyncMock(side_effect=Exception("Redis connection error"))
    backend._redis.pipeline.return_value = mock_pipeline

    # Should raise error when fail_open is False
    with pytest.raises(Exception, match="Redis connection error"):
        await backend.is_allowed("test1", limit=2, window=10)



@pytest.mark.asyncio
async def test_redis_throttle_backend_success(monkeypatch):
    backend = RedisThrottleBackend(redis_url="redis://localhost:6379")

    # Mock redis — pipeline queuing calls are sync; only execute() is async
    backend._redis = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[1, 1, 1, 1])
    backend._redis.pipeline.return_value = mock_pipeline

    # limit=2, count=1, should be True
    assert await backend.is_allowed("test1", limit=2, window=10) is True

    # Mock ZCARD returning 2
    mock_pipeline.execute = AsyncMock(return_value=[1, 2, 1, 1])

    # limit=2, count=2, should be False
    assert await backend.is_allowed("test1", limit=2, window=10) is False


def test_throttle_backend_factory():
    mem_backend = ThrottleBackendFactory.create("memory")
    assert isinstance(mem_backend, MemoryThrottleBackend)

    redis_backend = ThrottleBackendFactory.create("redis://localhost:6379")
    assert isinstance(redis_backend, RedisThrottleBackend)


@pytest.mark.asyncio
async def test_throttle_with_memory_factory():
    throttle = Throttle.with_memory(limit=5, window=10)
    assert isinstance(throttle.backend, MemoryThrottleBackend)

    req = DummyRequest("10.0.0.1")
    for _ in range(5):
        assert await throttle.acheck(req) is True
    assert await throttle.acheck(req) is False


@pytest.mark.asyncio
async def test_throttle_with_redis_factory():
    throttle = Throttle.with_redis("redis://localhost:6379", limit=5, window=10)
    assert isinstance(throttle.backend, RedisThrottleBackend)

    throttle.backend._redis = MagicMock()
    mock_pipeline = MagicMock()  # pipeline queuing calls are sync
    mock_pipeline.execute = AsyncMock(return_value=[1, 0, 1, 1])
    throttle.backend._redis.pipeline.return_value = mock_pipeline

    req = DummyRequest("10.0.0.2")
    assert await throttle.acheck(req) is True


@pytest.mark.asyncio
async def test_concurrent_stress():
    throttle = Throttle.with_memory(limit=10, window=60)
    req = DummyRequest("stress_ip")

    async def make_request():
        return await throttle.acheck(req)

    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)

    allowed = sum(1 for r in results if r)
    assert allowed == 10
