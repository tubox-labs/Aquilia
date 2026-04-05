import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { BookOpen } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheAPIReference() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const coreSymbols: Array<[string, string]> = [
    ['EvictionPolicy', 'Enum: lru, lfu, ttl, fifo, random.'],
    ['CacheEntry', 'Dataclass with value, timestamps, tags, namespace, version, and TTL helpers.'],
    ['CacheStats', 'Dataclass for hit/miss/set/delete/error/latency metrics.'],
    ['CacheConfig', 'Dataclass describing cache subsystem runtime config.'],
    ['CacheSerializer', 'Protocol with serialize(value)->bytes and deserialize(bytes)->Any.'],
    ['CacheKeyBuilder', 'Protocol with build(namespace, key, prefix).'],
    ['CacheBackend', 'Abstract async backend contract.'],
  ]

  const publicClasses: Array<[string, string]> = [
    ['CacheService', 'High-level app API for cache operations.'],
    ['MemoryBackend', 'In-process backend with eviction and sweeper.'],
    ['RedisBackend', 'Redis async backend with serializer and set indexes.'],
    ['CompositeBackend', 'L1/L2 backend with promotion and degrade behavior.'],
    ['NullBackend', 'No-op backend for disabled-cache paths.'],
    ['CacheMiddleware', 'HTTP response caching middleware.'],
    ['DefaultKeyBuilder', 'String key builder with optional version segment.'],
    ['HashKeyBuilder', 'SHA-256 key builder for bounded key length.'],
    ['JsonCacheSerializer', 'JSON serializer.'],
    ['MsgpackCacheSerializer', 'MessagePack serializer.'],
    ['PickleCacheSerializer', 'HMAC-signed pickle serializer.'],
  ]

  const decoratorFns: Array<[string, string]> = [
    ['cached(...)', 'Decorator for cached reads with keying, conditions, and tags.'],
    ['cache_aside(...)', 'Semantic alias of cached(...).'],
    ['invalidate(...)', 'Decorator for post-call key/tag invalidation.'],
    ['set_default_cache_service(service)', 'Register module-level decorator cache service fallback.'],
    ['get_default_cache_service()', 'Read module-level decorator cache service fallback.'],
  ]

  const faultClasses: Array<[string, string]> = [
    ['CacheFault', 'Base fault for cache domain.'],
    ['CacheMissFault', 'Informational miss fault.'],
    ['CacheConnectionFault', 'Backend connectivity failure.'],
    ['CacheSerializationFault', 'Serializer failure.'],
    ['CacheCapacityFault', 'Capacity exceeded warning fault.'],
    ['CacheBackendFault', 'Generic backend operation fault.'],
    ['CacheConfigFault', 'Invalid cache configuration fault.'],
    ['CacheStampedeFault', 'Concurrent load stampede fault.'],
    ['CacheHealthFault', 'Health-check failure fault.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          Cache / API Reference
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Cache API Reference
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Complete public symbol map for <code className="text-aquilia-500">aquilia.cache</code>
          and closely related DI/serializer helpers.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Module Export Surface</h2>
        <CodeBlock language="python" filename="aquilia/cache/__init__.py">{`from aquilia.cache import (
    # Core
    CacheBackend, CacheEntry, CacheStats, CacheConfig, CacheSerializer,
    CacheKeyBuilder, EvictionPolicy,

    # Backends
    MemoryBackend, RedisBackend, CompositeBackend, NullBackend,

    # Service and middleware
    CacheService, CacheMiddleware,

    # Decorators
    cached, cache_aside, invalidate,
    set_default_cache_service, get_default_cache_service,

    # Key builders
    DefaultKeyBuilder, HashKeyBuilder,

    # Serializers
    JsonCacheSerializer, MsgpackCacheSerializer, PickleCacheSerializer,

    # Faults
    CacheFault, CacheMissFault, CacheConnectionFault,
    CacheSerializationFault, CacheCapacityFault, CacheBackendFault,
    CacheConfigFault, CacheStampedeFault, CacheHealthFault,
)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Types</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Symbol</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {coreSymbols.map(([name, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Public Classes</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Class</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {publicClasses.map(([name, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorator Functions</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Function</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {decoratorFns.map(([name, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Types</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Fault</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {faultClasses.map(([name, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Provider Helpers</h2>
        <CodeBlock language="python" filename="aquilia/cache/di_providers.py">{`from aquilia.cache.di_providers import (
    build_cache_config,
    create_cache_backend,
    create_cache_service,
    register_cache_providers,
)

cache_config = build_cache_config(raw_config_dict)
cache_service = create_cache_service(cache_config)
register_cache_providers(container, cache_service)
`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>register_cache_providers adds CacheService and CacheBackend to app-scoped DI container providers.</li>
            <li>For redis/composite backends, serializer is selected via get_serializer(name).</li>
            <li>Current factory path does not pass pickle secret_key into serializer factory.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Related APIs</h2>
        <CodeBlock language="python" filename="related_modules.py">{`# Response cache middleware (server-side)
from aquilia.cache.middleware import CacheMiddleware

# Effects integration
from aquilia.effects import CacheEffect, CacheProvider, CacheServiceHandle

# Testing helpers
from aquilia.testing.cache import MockCacheBackend, CacheTestMixin
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Cache Overview', link: '/docs/cache' },
          { text: 'Configuration', link: '/docs/cache/configuration' },
          { text: 'CacheService', link: '/docs/cache/service' },
          { text: 'Backends', link: '/docs/cache/backends' },
        ]}
      />
    </div>
  )
}
