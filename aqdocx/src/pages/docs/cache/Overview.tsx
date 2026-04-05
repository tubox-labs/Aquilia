import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowRight, AlertTriangle, Layers, Workflow, Gauge } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtleClass = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Gauge className="w-4 h-4" />
          Advanced / Cache
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            AquilaCache Overview
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtleClass}`}>
          AquilaCache is Aquilia&apos;s async-native cache subsystem. It provides a DI-injectable
          <code className="text-aquilia-500 mx-1">CacheService</code>, multiple backends,
          response-caching middleware, decorators, typed faults, and namespace/tag invalidation.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Workflow className="w-5 h-5 text-aquilia-500" />
          Runtime Wiring
        </h2>
        <p className={`mb-4 ${subtleClass}`}>
          Cache configuration is loaded first, then the service is created and registered in DI,
          and finally initialized on server startup.
        </p>
        <CodeBlock language="text" filename="cache-boot-sequence.txt">{`Integration.cache(...) / CacheIntegration(...)
  -> Workspace.to_dict()
  -> ConfigLoader.get_cache_config()
  -> Server._setup_cache()
     -> build_cache_config(...)
     -> create_cache_service(...)
     -> register_cache_providers(...) into each app DI container
     -> optional CacheMiddleware registration
  -> server.startup()
     -> CacheService.initialize()
  -> server.shutdown()
     -> CacheService.shutdown()`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Feature Map
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              title: 'Backends',
              body: 'Memory, Redis, Composite (L1 + L2), and Null backend for disabled-cache flows.',
            },
            {
              title: 'High-level API',
              body: 'CacheService supports get/set, batch operations, cache-aside get_or_set, namespace and tag invalidation, and health checks.',
            },
            {
              title: 'HTTP Response Cache',
              body: 'CacheMiddleware supports GET/HEAD caching, ETag handling, stale-while-revalidate, and secure bypass token support.',
            },
            {
              title: 'Developer Ergonomics',
              body: 'Decorators (@cached, @cache_aside, @invalidate), typed faults, pluggable serializers, and deterministic key builders.',
            },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <h3 className={`font-mono text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${subtleClass}`}>{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Enable Cache</h2>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia import Workspace, Integration
from aquilia.integrations import CacheIntegration

workspace = (
    Workspace("myapp")
    # Legacy dict builder API
    .integrate(Integration.cache(
        backend="redis",
        redis_url="redis://localhost:6379/0",
        default_ttl=300,
        serializer="json",
        middleware_enabled=True,
        middleware_default_ttl=60,
    ))

    # Typed integration API (also supported)
    .integrate(CacheIntegration(
        backend="memory",
        max_size=10000,
        default_ttl=120,
        eviction_policy="lru",
    ))
)`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleClass}`}>
          Cache config can also be provided through
          <code className="mx-1 text-aquilia-500">AquilaConfig.Cache</code>
          and environment overlays. For exact key mapping and precedence, see the Configuration page.
        </p>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Use CacheService In Controllers</h2>
        <CodeBlock language="python" filename="modules/catalog/controllers.py">{`from aquilia import Controller, GET
from aquilia.cache import CacheService


class ProductController(Controller):
    prefix = "/products"

    def __init__(self, cache: CacheService):
        self.cache = cache

    @GET("/")
    async def list_products(self, ctx):
        products = await self.cache.get_or_set(
            key="products:list:v1",
            loader=lambda: self.service.list_products(),
            ttl=90,
            namespace="catalog",
            tags=("products", "catalog:list"),
        )
        return {"products": products}
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          Current Behavior Notes
        </h2>
        <div className={`p-5 rounded-xl border ${isDark ? 'border-amber-500/30 bg-amber-500/10' : 'border-amber-300 bg-amber-50'}`}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtleClass}`}>
            <li>Server auto-wiring for response cache middleware currently checks nested <code className="text-aquilia-500">cache.middleware</code> keys, while canonical cache config is flat (<code className="text-aquilia-500">middleware_enabled</code>, <code className="text-aquilia-500">middleware_default_ttl</code>, etc.).</li>
            <li>In the same auto-wiring path, <code className="text-aquilia-500">CacheMiddleware</code> is called with <code className="text-aquilia-500">ttl=...</code>, but middleware constructor expects <code className="text-aquilia-500">default_ttl=...</code>.</li>
            <li><code className="text-aquilia-500">@cached</code> decorators can resolve cache from <code className="text-aquilia-500">self.cache</code> / <code className="text-aquilia-500">self._cache</code>. The module-level default service helper exists but is not automatically registered by server setup in current code.</li>
            <li><code className="text-aquilia-500">aq cache stats</code> currently calls <code className="text-aquilia-500">svc.info()</code> if present; <code className="text-aquilia-500">CacheService</code> does not expose <code className="text-aquilia-500">info()</code>, so stats output may be empty.</li>
          </ul>
        </div>
      </section>

      <section className="mb-8">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dive Deeper</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { label: 'Cache Configuration', to: '/docs/cache/configuration' },
            { label: 'Cache CLI', to: '/docs/cache/cli' },
            { label: 'CacheService API', to: '/docs/cache/service' },
            { label: 'Backend Semantics', to: '/docs/cache/backends' },
            { label: 'Decorators and Middleware', to: '/docs/cache/decorators' },
            { label: 'Full API Reference', to: '/docs/cache/api-reference' },
          ].map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-colors ${
                isDark
                  ? 'border-white/10 bg-[#0A0A0A] text-gray-200 hover:border-aquilia-500/60'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-aquilia-500/60'
              }`}
            >
              <span className="text-sm font-medium">{item.label}</span>
              <ArrowRight className="w-4 h-4 text-aquilia-500" />
            </Link>
          ))}
        </div>
      </section>

      <div className={`pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <NextSteps
          items={[
            { text: 'Cache Configuration', link: '/docs/cache/configuration' },
            { text: 'CacheService API', link: '/docs/cache/service' },
            { text: 'Cache CLI', link: '/docs/cache/cli' },
            { text: 'Backends', link: '/docs/cache/backends' },
          ]}
        />
      </div>
    </div>
  )
}