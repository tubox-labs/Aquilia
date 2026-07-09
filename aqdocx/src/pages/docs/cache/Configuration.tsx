import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Configure AquilaCache via workspace integrations, typed integration dataclasses,
          Python-native config classes, and <code className="text-aquilia-500">AQ_*</code> environment overlays.
        </p>
      </div>

      {/* Primary Configuration Paths */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Primary Configuration Paths</h2>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[7, 17]}>{`from aquilia import Workspace, Integration
from aquilia.integrations import CacheIntegration

workspace = (
    Workspace("myapp")
    # Dict-based API
    .integrate(Integration.cache(
        backend="redis",
        redis_url="redis://localhost:6379/0",
        default_ttl=300,
        serializer="json",
        middleware_enabled=True,
        middleware_default_ttl=60,
    ))

    # Typed Integration API
    .integrate(CacheIntegration(
        backend="memory",
        default_ttl=120,
        max_size=10000,
        eviction_policy="lru",
    ))
)
`}</CodeBlock>
      </section>

      {/* AquilaConfig.Cache (Python-native) */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>AquilaConfig.Cache (Python-native)</h2>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 7]}>{`from aquilia.config_builders import AquilaConfig, Env

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

      {/* Environment Mapping */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Environment Mapping</h2>
        <p className={`mb-4 ${textMuted}`}>
          ConfigLoader ingests <code className="text-aquilia-500">AQ_</code> prefixed variables and maps nested paths using double underscores:
        </p>
        <CodeBlock language="bash" filename=".env" highlightLines={[2, 6, 8]}>{`# Flat key
AQ_CACHE__BACKEND=redis
AQ_CACHE__DEFAULT_TTL=600
AQ_CACHE__REDIS_URL=redis://cache:6379/0

# Response cache middleware settings
AQ_CACHE__MIDDLEWARE_ENABLED=true
AQ_CACHE__MIDDLEWARE_DEFAULT_TTL=45
AQ_CACHE__MIDDLEWARE_STALE_WHILE_REVALIDATE=30
`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/30 pl-4 py-1 mt-4">
          <p className={`text-xs ${textMuted}`}>
            <strong>Configuration Precedence:</strong> environment variables have higher priority than defaults declared in Python configuration files, allowing seamless deployment adjustments.
          </p>
        </div>
      </section>

      {/* Field Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Field Reference</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse text-left">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Key</th>
                <th className="pb-3 font-semibold pr-4">Type</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {fields.map(([key, type, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{key}</td>
                  <td className="py-2.5 font-mono text-xs pr-4 text-zinc-500">{type}</td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* How Config Is Loaded */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>How Config Is Loaded</h2>
        <CodeBlock language="python" filename="config_resolution.py" highlightLines={[3, 4]}>{`from aquilia.config import ConfigLoader

loader = ConfigLoader.load()
cache_cfg = loader.get_cache_config()

# get_cache_config() behavior:
# 1) starts from built-in defaults
# 2) overlays root "cache" if present
# 3) falls back to "integrations.cache" if root cache is missing
# 4) forces enabled=True when user cache config exists
`}</CodeBlock>
      </section>

      {/* Current Behavior Notes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Current Behavior Notes</h2>
        <div className="border-l-2 border-amber-500/40 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            • Cache config keys are flat (e.g. <code className="text-aquilia-500">middleware_enabled</code>), whereas the ASGI server auto-wiring routine checks nested <code className="text-aquilia-500">cache.middleware</code> dict properties when enabling <DocTerm id="cache.CacheMiddleware">CacheMiddleware</DocTerm>.
          </p>
          <p>
            • The HMAC-signed <DocTerm id="cache.MemoryBackend">PickleCacheSerializer</DocTerm> requires a <code className="text-aquilia-500">secret_key</code> to decrypt payloads. Ensure this is passed during custom instantiation since the automated loader doesn't fetch it dynamically.
          </p>
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
