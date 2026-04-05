import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const fields: Array<[string, string, string]> = [
    ['enabled', 'bool', 'Enable/disable cache subsystem.'],
    ['backend', 'memory | redis | composite | null', 'Select backend implementation.'],
    ['default_ttl', 'int', 'Default TTL in seconds.'],
    ['max_size', 'int', 'Memory backend max entries.'],
    ['eviction_policy', 'lru | lfu | fifo | ttl | random', 'Memory backend eviction strategy.'],
    ['namespace', 'str', 'Default logical namespace.'],
    ['key_prefix', 'str', 'Global key prefix (backend-level).'],
    ['serializer', 'json | msgpack | pickle', 'Serializer for Redis/composite payloads.'],
    ['ttl_jitter', 'bool', 'Enable jitter to reduce synchronized expirations.'],
    ['ttl_jitter_percent', 'float', 'Jitter range fraction (for example 0.1 = +/-10%).'],
    ['stampede_prevention', 'bool', 'Enable local singleflight in get_or_set.'],
    ['stampede_timeout', 'float', 'Wait timeout (seconds) for in-flight key load.'],
    ['redis_url', 'str', 'Redis connection URL.'],
    ['redis_max_connections', 'int', 'Redis pool size.'],
    ['redis_socket_timeout', 'float', 'Socket timeout (seconds).'],
    ['redis_socket_connect_timeout', 'float', 'Connect timeout (seconds).'],
    ['redis_retry_on_timeout', 'bool', 'Retry on socket timeout.'],
    ['l1_max_size', 'int', 'Composite backend L1 memory size.'],
    ['l1_ttl', 'int', 'Composite backend L1 TTL.'],
    ['l2_backend', 'str', 'Composite backend L2 type.'],
    ['l2_async_write', 'bool', 'If true, writes to L2 asynchronously.'],
    ['middleware_enabled', 'bool', 'Enable response cache middleware config flag.'],
    ['middleware_default_ttl', 'int', 'Response cache default max-age.'],
    ['middleware_cacheable_methods', 'list[str]', 'HTTP methods cacheable by middleware.'],
    ['middleware_vary_headers', 'list[str]', 'Headers included in middleware cache key.'],
    ['middleware_stale_while_revalidate', 'int', 'Allow stale serving window in seconds.'],
    ['trace_enabled', 'bool', 'Trace-level cache diagnostics toggle.'],
    ['metrics_enabled', 'bool', 'Metrics-level cache diagnostics toggle.'],
    ['log_level', 'str', 'Cache subsystem log level.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          Cache / Configuration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Cache Configuration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Configure AquilaCache via workspace integrations, typed integration dataclasses,
          Python-native config classes, and AQ_* environment overlays.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Primary Configuration Paths</h2>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia import Workspace, Integration
from aquilia.integrations import CacheIntegration

workspace = (
    Workspace("myapp")
    # Legacy dict-based API
    .integrate(Integration.cache(
        backend="redis",
        redis_url="redis://localhost:6379/0",
        default_ttl=300,
        serializer="json",
        middleware_enabled=True,
        middleware_default_ttl=60,
    ))

    # Typed API
    .integrate(CacheIntegration(
        backend="memory",
        default_ttl=120,
        max_size=10000,
        eviction_policy="lru",
    ))
)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>AquilaConfig.Cache (Python-native)</h2>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia.config_builders import AquilaConfig, Env

class BaseEnv(AquilaConfig):
    class Cache(AquilaConfig.Cache):
        backend = Env("AQ_CACHE_BACKEND", default="memory")
        default_ttl = 300
        max_size = 10000
        eviction_policy = "lru"
        namespace = "default"
        key_prefix = "aq:"
        redis_url = Env("AQ_CACHE_REDIS_URL", default="redis://localhost:6379/0")
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Environment Mapping</h2>
        <p className={`mb-4 ${subtle}`}>
          ConfigLoader ingests AQ_ prefixed variables and maps nested paths using double underscores.
        </p>
        <CodeBlock language="bash" filename=".env">{`# Flat key
AQ_CACHE__BACKEND=redis
AQ_CACHE__DEFAULT_TTL=600
AQ_CACHE__REDIS_URL=redis://cache:6379/0

# Middleware settings
AQ_CACHE__MIDDLEWARE_ENABLED=true
AQ_CACHE__MIDDLEWARE_DEFAULT_TTL=45
AQ_CACHE__MIDDLEWARE_STALE_WHILE_REVALIDATE=30
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Note: scaffold files may include unprefixed examples like CACHE_BACKEND or REDIS_URL.
            Those do not map into ConfigLoader cache keys unless explicitly consumed elsewhere.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Field Reference</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Key</th>
                  <th className="text-left pb-3 font-semibold">Type</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {fields.map(([key, type, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{key}</td>
                    <td className="py-2 font-mono text-xs pr-4">{type}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>How Config Is Loaded</h2>
        <CodeBlock language="python" filename="config_resolution.py">{`from aquilia.config import ConfigLoader

loader = ConfigLoader.load()
cache_cfg = loader.get_cache_config()

# get_cache_config() behavior:
# 1) starts from built-in defaults
# 2) overlays root "cache" if present
# 3) falls back to "integrations.cache" if root cache is missing
# 4) forces enabled=True when user cache config exists
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Current Behavior Notes</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Cache config keys are primarily flat (for example middleware_enabled), not nested middleware dicts.</li>
            <li>Server auto-wiring currently checks nested cache.middleware keys for response cache middleware.</li>
            <li>Pickle serializer requires a secret_key, but cache service factory does not currently pass one from config.</li>
            <li>Some fields exist in CacheConfig (for example key_version, redis_decode_responses) but are not fully consumed end-to-end in current runtime wiring.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Cache Overview', link: '/docs/cache' },
          { text: 'CacheService API', link: '/docs/cache/service' },
          { text: 'Backends', link: '/docs/cache/backends' },
          { text: 'Cache CLI', link: '/docs/cache/cli' },
        ]}
      />
    </div>
  )
}
