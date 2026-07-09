import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { BookOpen } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheAPIReference() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

  const coreSymbols: Array<[string, string]> = [
    ['EvictionPolicy', 'Enum representing cache eviction strategies: lru, lfu, ttl, fifo, random.'],
    ['CacheEntry', 'Dataclass representing a cached entry. Tracks value, timestamps, tags, and namespaces.'],
    ['CacheStats', 'Dataclass tracking hits, misses, sets, deletes, errors, and latency metrics.'],
    ['CacheConfig', 'Dataclass describing cache subsystem runtime options.'],
    ['CacheSerializer', 'Protocol defining serialize(value)->bytes and deserialize(bytes)->Any methods.'],
    ['CacheKeyBuilder', 'Protocol defining build(namespace, key, prefix) methods.'],
    ['CacheBackend', 'Abstract base class describing the backend implementation contract.'],
  ]

  const publicClasses: Array<[string, string]> = [
    ['CacheService', 'High-level client API orchestrator for caching operations.'],
    ['MemoryBackend', 'In-process memory backend with eviction policy support.'],
    ['RedisBackend', 'Redis distributed backend supporting pipeline batching.'],
    ['CompositeBackend', 'L1 local memory + L2 distributed Redis composite backend.'],
    ['NullBackend', 'No-op cache backend for disabling cache actions.'],
    ['CacheMiddleware', 'HTTP response caching middleware.'],
    ['DefaultKeyBuilder', 'Canonical key builder combining namespaces and prefixes.'],
    ['HashKeyBuilder', 'Key builder utilizing SHA-256 hashes to enforce bounded key lengths.'],
    ['JsonCacheSerializer', 'Default serializer using JSON conversion.'],
    ['MsgpackCacheSerializer', 'Compact binary serializer using MessagePack.'],
    ['PickleCacheSerializer', 'HMAC-signed pickle serializer for arbitrary Python types.'],
  ]

  const decoratorFns: Array<[string, string]> = [
    ['cached(...)', 'Decorator for cached reads with keys, conditions, and tags.'],
    ['cache_aside(...)', 'Semantic alias for the @cached decorator.'],
    ['invalidate(...)', 'Decorator to invalidate keys or tags after function execution.'],
    ['set_default_cache_service(service)', 'Registers a module-level CacheService for decorator fallback resolution.'],
    ['get_default_cache_service()', 'Gets the registered module-level CacheService fallback.'],
  ]

  const faultClasses: Array<[string, string]> = [
    ['CacheFault', 'Base class for all Cache subsystem faults.'],
    ['CacheMissFault', 'Informational fault emitted during cache misses.'],
    ['CacheConnectionFault', 'Backend connection failure fault.'],
    ['CacheSerializationFault', 'Serialization or deserialization failure fault.'],
    ['CacheCapacityFault', 'Capacity warning fault emitted when backend reaches max_size.'],
    ['CacheBackendFault', 'Generic backend operational failure fault.'],
    ['CacheConfigFault', 'Invalid configuration parameter fault.'],
    ['CacheStampedeFault', 'Thundering herd wait timeout fault.'],
    ['CacheHealthFault', 'Health probe write/read/delete check failure fault.'],
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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Complete public symbol map for <code className="text-aquilia-500">aquilia.cache</code>
          and related DI and serializer helpers.
        </p>
      </div>

      {/* Module Export Surface */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Module Export Surface</h2>
        <CodeBlock language="python" filename="aquilia/cache/__init__.py" highlightLines={[3, 6, 9, 12, 15, 18]}>{`from aquilia.cache import (
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

      {/* Core Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Types</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Symbol</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {coreSymbols.map(([name, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Public Classes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Public Classes</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Class</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {publicClasses.map(([name, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">
                    <DocTerm id={`cache.${name}`}>{name}</DocTerm>
                  </td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Decorator Functions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorator Functions</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Function</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {decoratorFns.map(([name, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">
                    <DocTerm id={`cache.${name.split('(')[0]}`}>{name}</DocTerm>
                  </td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Fault Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Types</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Fault</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {faultClasses.map(([name, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Provider Helpers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Provider Helpers</h2>
        <CodeBlock language="python" filename="aquilia/cache/di_providers.py" highlightLines={[7, 8, 9]}>{`from aquilia.cache.di_providers import (
    build_cache_config,
    create_cache_backend,
    create_cache_service,
    register_cache_providers,
)

cache_config = build_cache_config(raw_config_dict)
cache_service = create_cache_service(cache_config)
register_cache_providers(container, cache_service)
`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2 mt-4">
          <p>• <code className="text-aquilia-500">register_cache_providers</code> adds CacheService and CacheBackend definitions to the application container scope.</p>
          <p>• Serialization configurations resolve active serializer mappings via <code className="text-aquilia-500">get_serializer(name)</code>.</p>
        </div>
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
