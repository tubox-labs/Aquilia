import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowRight, AlertTriangle, Workflow, Gauge } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaCache is Aquilia&apos;s async-native cache subsystem. It provides a DI-injectable{' '}
          <DocTerm id="cache.CacheService">CacheService</DocTerm>, pluggable backends (Memory, Redis, Composite L1/L2), HTTP response-caching middleware, decorators, and tag-based invalidation.
        </p>
      </div>

      {/* Runtime Wiring */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Workflow className="w-5 h-5 text-aquilia-500" />
          Runtime Wiring
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          The cache system initializes early in the server bootstrap lifecycle inside <code className="text-aquilia-500">_setup_cache()</code>, registers providers into all active DI containers, and binds lifecycle startup/shutdown handlers.
        </p>
        <CodeBlock language="python" filename="aquilia/server.py::cache_boot" highlightLines={[2, 6, 10, 15]}>{`# 1. Load configuration via ConfigLoader
cache_config = self.config.get_cache_config()
if not cache_config.get("enabled", False):
    return

# 2. Build configuration model and instantiate service
config_obj = build_cache_config(cache_config)
svc = create_cache_service(config_obj)

# 3. Register service inside all active DI containers
for container in self.runtime.di_containers.values():
    register_cache_providers(container, svc)

self._cache_service = svc

# 4. Conditionally add HTTP response-cache middleware
mw_cfg = cache_config.get("middleware", {})
if mw_cfg.get("enabled", False):
    self.middleware_stack.add(
        CacheMiddleware(cache_service=svc, ttl=mw_cfg.get("ttl", 300)),
        scope="global",
        priority=26,
        name="cache",
    )
`}</CodeBlock>
      </section>

      {/* Workspace-Level Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Workspace-Level Integration</h2>
        <p className={`mb-4 ${textMuted}`}>
          At the workspace level, you declare cache configurations globally in your <code className="text-aquilia-500">workspace.py</code>. This configures the default backend, serialization, default TTL, and middleware behaviors.
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 13]}>{`from aquilia import Workspace
from aquilia.integrations import CacheIntegration

workspace = (
    Workspace("product-service")
    .integrate(CacheIntegration(
        backend="composite",         # L1 Memory + L2 Redis composite backend
        default_ttl=300,
        serializer="json",
        redis_url="redis://localhost:6379/0",
        middleware_enabled=True,     # Activates CacheMiddleware
        middleware_default_ttl=60,
    ))
)
`}</CodeBlock>
      </section>

      {/* Manifest-Level Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manifest-Level & Controller Integration</h2>
        <p className={`mb-4 ${textMuted}`}>
          Modules declare services and controllers in their <code className="text-aquilia-500">AppManifest</code>. Because the cache service is pre-registered in the DI container, components can request <DocTerm id="cache.CacheService">CacheService</DocTerm> via constructor dependency injection automatically.
        </p>
        <CodeBlock language="python" filename="modules/catalog/manifest.py" highlightLines={[7]}>{`from aquilia import AppManifest
from .controllers import ProductController
from .services import ProductService

manifest = AppManifest(
    name="catalog",
    services=[ProductService],
    controllers=[ProductController],
)
`}</CodeBlock>
        <CodeBlock language="python" filename="modules/catalog/controllers.py" highlightLines={[8, 12]}>{`from aquilia import Controller, GET, RequestCtx
from aquilia.cache import CacheService

class ProductController(Controller):
    prefix = "/products"

    # Dependency Injection resolves CacheService automatically
    def __init__(self, cache: CacheService):
        self.cache = cache

    @GET("/{product_id}")
    async def get_product(self, ctx: RequestCtx):
        product_id = ctx.path_params["product_id"]
        
        # Load from cache, or invoke database loader on miss
        return await self.cache.get_or_set(
            key=f"product:{product_id}",
            loader=lambda: self.db_fetch(product_id),
            ttl=120,
            tags=("products", f"product:{product_id}")
        )
`}</CodeBlock>
      </section>

      {/* Current Behavior Notes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          Current Behavior Notes
        </h2>
        <div className="space-y-4 border-l-2 border-amber-500/30 pl-6 py-1">
          {[
            ['Flat Config Mapping', 'Server auto-wiring checks nested cache.middleware properties, whereas ConfigLoader parses flat keys (middleware_enabled).'],
            ['Middleware TTL SignatureMismatch', 'CacheMiddleware is instantiated with ttl=..., but its constructor expects default_ttl=... in the ASGI setup.'],
            ['Decorator Registry Resolver', 'Decorators resolve cache service from self.cache or self._cache in controllers. Standalone functions require manual set_default_cache_service.'],
            ['CLI Stats Command Bug', 'The aq cache stats command invokes svc.info(), but CacheService only exposes stats(), leading to empty outputs.'],
          ].map(([title, desc], i) => (
            <div key={i} className="text-sm">
              <strong className="font-mono text-amber-500 block mb-0.5">{title}</strong>
              <p className={textMuted}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dive Deeper</h2>
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
                  ? 'border-white/5 bg-zinc-950/40 text-gray-200 hover:border-aquilia-500/60 hover:bg-zinc-900/50'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-aquilia-500/60 hover:bg-gray-50'
              }`}
            >
              <span className="text-sm font-medium">{item.label}</span>
              <ArrowRight className="w-4 h-4 text-aquilia-500" />
            </Link>
          ))}
        </div>
      </section>

      <div className={`pt-8 mt-12 border-t ${borderSubtle}`}>
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