import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { HardDrive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheBackends() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <HardDrive className="w-4 h-4" />
          Cache / Backends
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Cache Backends
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Aquilia ships four cache backends. All conform to the
          <code className="text-aquilia-500 mx-1">CacheBackend</code>
          contract and can be swapped behind the same <code className="text-aquilia-500">CacheService</code> API.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Backend Comparison</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Backend</th>
                  <th className="text-left pb-3 font-semibold">Persistence</th>
                  <th className="text-left pb-3 font-semibold">Distributed</th>
                  <th className="text-left pb-3 font-semibold">Primary Strength</th>
                  <th className="text-left pb-3 font-semibold">Best For</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {[
                  ['MemoryBackend', 'No', 'No', 'Low-latency in-process cache', 'Single-process apps, tests, dev'],
                  ['RedisBackend', 'Yes', 'Yes', 'Shared cache across workers/nodes', 'Production multi-worker deployments'],
                  ['CompositeBackend', 'L1 no + L2 maybe', 'Via L2', 'Fast local hits + shared fallback', 'High QPS with hot-key skew'],
                  ['NullBackend', 'No', 'No', 'Intentional no-op behavior', 'Disable cache without code changes'],
                ].map(([name, persist, dist, strength, best], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-400 text-xs">{name}</td>
                    <td className="py-2 text-xs">{persist}</td>
                    <td className="py-2 text-xs">{dist}</td>
                    <td className="py-2 text-xs">{strength}</td>
                    <td className="py-2 text-xs">{best}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CacheBackend Contract</h2>
        <CodeBlock language="python" filename="aquilia/cache/core.py">{`class CacheBackend(ABC):
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def get(self, key: str) -> CacheEntry | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None, tags: tuple[str, ...] = (), namespace: str = "default") -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def clear(self, namespace: str | None = None) -> int: ...
    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list[str]: ...
    async def stats(self) -> CacheStats: ...

    # Optional overrides with defaults in base class:
    async def delete_by_tags(self, tags: set[str]) -> int: ...
    async def get_many(self, keys: list[str]) -> dict[str, CacheEntry | None]: ...
    async def set_many(self, items: dict[str, Any], ttl: int | None = None, namespace: str = "default") -> None: ...
    async def delete_many(self, keys: list[str]) -> int: ...
    async def increment(self, key: str, delta: int = 1) -> int | None: ...
    async def decrement(self, key: str, delta: int = 1) -> int | None: ...

    @property
    def name(self) -> str: ...

    @property
    def is_distributed(self) -> bool: ...
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MemoryBackend</h2>
        <p className={`mb-4 ${subtle}`}>
          In-process cache with lock-based concurrency control, TTL sweeper task, inverted indices for tags/namespaces,
          and configurable eviction policy (<code className="text-aquilia-500">lru</code>, <code className="text-aquilia-500">lfu</code>, <code className="text-aquilia-500">fifo</code>, <code className="text-aquilia-500">ttl</code>, <code className="text-aquilia-500">random</code>).
        </p>
        <CodeBlock language="python" filename="memory_backend.py">{`from aquilia.cache import MemoryBackend, CacheService

backend = MemoryBackend(
    max_size=10_000,
    eviction_policy="lru",
    sweep_interval=30.0,
    max_memory_bytes=0,
    capacity_warning_threshold=0.85,
)

cache = CacheService(backend=backend)
await cache.initialize()`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Tracks per-entry metadata (<code className="text-aquilia-500">created_at</code>, <code className="text-aquilia-500">last_accessed</code>, <code className="text-aquilia-500">access_count</code>, tags, namespace, size).</li>
            <li>Background sweeper removes expired entries from a TTL heap.</li>
            <li>LFU policy uses frequency tracking; LRU/FIFO use ordered storage semantics.</li>
            <li>Reports latency samples and hit/miss stats through <code className="text-aquilia-500">CacheStats</code>.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RedisBackend</h2>
        <p className={`mb-4 ${subtle}`}>
          Distributed backend using <code className="text-aquilia-500">redis.asyncio</code> with connection pooling,
          serializer support, pipelined batch operations, and set-based indexes for tags/namespaces.
        </p>
        <CodeBlock language="python" filename="redis_backend.py">{`from aquilia.cache import RedisBackend, CacheService

backend = RedisBackend(
    url="redis://localhost:6379/0",
    max_connections=20,
    key_prefix="aq:",
    socket_timeout=5.0,
    connect_timeout=5.0,
    retry_on_timeout=True,
)

cache = CacheService(backend=backend)
await cache.initialize()`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Stores value payloads as serialized bytes.</li>
            <li>Uses prefixed keys and metadata sets: <code className="text-aquilia-500">{`_tags:<tag>`}</code> and <code className="text-aquilia-500">{`_ns:<namespace>`}</code>.</li>
            <li>Tag invalidation performs set lookup then key deletion in a pipeline.</li>
            <li>Batch reads use <code className="text-aquilia-500">MGET</code>; batch writes use pipelined <code className="text-aquilia-500">SET/SETEX</code> and namespace indexing.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CompositeBackend (L1/L2)</h2>
        <p className={`mb-4 ${subtle}`}>
          Two-level backend for low-latency reads with shared fallback. Read path is L1 then L2. L2 hits can be promoted to L1.
        </p>
        <CodeBlock language="python" filename="composite_backend.py">{`from aquilia.cache import (
    CompositeBackend, MemoryBackend, RedisBackend, CacheService,
)

l1 = MemoryBackend(max_size=1_000)
l2 = RedisBackend(url="redis://localhost:6379/0")

backend = CompositeBackend(
    l1=l1,
    l2=l2,
    promote_on_l2_hit=True,
    async_l2_write=False,
)

cache = CacheService(backend=backend)

# Reads: L1 → L2 → miss
# Writes: L1 + L2 simultaneously`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>L2 read/write failures are handled with graceful degradation where possible.</li>
            <li><code className="text-aquilia-500">l2_healthy</code> reports current L2 status.</li>
            <li>Increment operations are L2-authoritative and then mirrored into L1.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>NullBackend</h2>
        <p className={`mb-4 ${subtle}`}>
          No-op backend that always misses and never stores values. Useful when you want cache calls to remain in code paths
          while effectively disabling caching.
        </p>
        <CodeBlock language="python" filename="null_backend.py">{`from aquilia.cache import NullBackend, CacheService

cache = CacheService(backend=NullBackend())
# All gets return None, all sets are no-ops`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cache Serializers</h2>
        <p className={`mb-4 ${subtle}`}>
          Serializer selection is primarily relevant for Redis/composite L2 persistence.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { name: 'JsonCacheSerializer', desc: 'Default serializer. JSON bytes, safe and interoperable.' },
            { name: 'MsgpackCacheSerializer', desc: 'Compact binary format (requires msgpack package).' },
            { name: 'PickleCacheSerializer', desc: 'HMAC-signed pickle payloads. Powerful but security-sensitive; requires secret_key.' },
          ].map((s, i) => (
            <div key={i} className={box}>
              <h3 className={`font-mono font-bold text-xs mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{s.name}</h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{s.desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" filename="serializer_factory.py">{`from aquilia.cache.serializers import get_serializer

json_ser = get_serializer("json")
msgpack_ser = get_serializer("msgpack")
pickle_ser = get_serializer("pickle", secret_key="change-me")
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Builders</h2>
        <CodeBlock language="python" filename="key_builders.py">{`from aquilia.cache import DefaultKeyBuilder, HashKeyBuilder

default_builder = DefaultKeyBuilder(version=1)
print(default_builder.build(namespace="users", key="42", prefix="aq:"))
# aq:v1:users:42

hash_builder = HashKeyBuilder(hash_length=16, version=1)
print(hash_builder.build(namespace="search", key="long-query", prefix="aq:"))
# aq:v1:search:<hash>
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Implementing a Custom Backend</h2>
        <p className={`mb-4 ${subtle}`}>
          Implement the abstract methods from <code className="text-aquilia-500">CacheBackend</code>. Keep method signatures compatible.
        </p>
        <CodeBlock language="python" filename="custom_backend.py">{`from typing import Any
from aquilia.cache import CacheBackend, CacheEntry, CacheStats

class DynamoBackend(CacheBackend):
    @property
    def name(self) -> str:
        return "dynamo"

    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def get(self, key: str) -> CacheEntry | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None, tags: tuple[str, ...] = (), namespace: str = "default") -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def clear(self, namespace: str | None = None) -> int: ...
    async def keys(self, pattern: str = "*", namespace: str | None = None) -> list[str]: ...
    async def stats(self) -> CacheStats: ...
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'CacheService API', link: '/docs/cache/service' },
          { text: 'Decorators and Middleware', link: '/docs/cache/decorators' },
          { text: 'Configuration', link: '/docs/cache/configuration' },
          { text: 'API Reference', link: '/docs/cache/api-reference' },
        ]}
      />
    </div>
  )
}