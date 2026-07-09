import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Gauge } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheService() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

  const methods = [
    ['initialize()', 'Initialize backend and start background health task (if enabled).'],
    ['shutdown()', 'Stop health task, cancel in-flight stampede futures, shutdown backend.'],
    ['startup()', 'DI lifecycle alias for initialize().'],
    ['async_init()', 'DI async-init alias for initialize().'],
    ['get(key, namespace=None, default=None)', 'Read value by key. Returns default on miss or backend error.'],
    ['set(key, value, ttl=None, namespace=None, tags=())', 'Write value with optional TTL and tags; applies TTL jitter.'],
    ['delete(key, namespace=None)', 'Delete one key.'],
    ['exists(key, namespace=None)', 'Existence check without returning value.'],
    ['get_or_set(key, loader, ttl=None, namespace=None, tags=())', 'Cache-aside with optional singleflight stampede prevention.'],
    ['get_many(keys, namespace=None)', 'Batch read. Returns {original_key: value_or_none}.'],
    ['set_many(items, ttl=None, namespace=None)', 'Batch write.'],
    ['delete_many(keys, namespace=None)', 'Batch delete. Returns deleted count.'],
    ['invalidate_tags(*tags)', 'Delete entries matching any tag.'],
    ['invalidate_namespace(namespace)', 'Clear a namespace.'],
    ['increment(key, delta=1, namespace=None)', 'Increment numeric value. Backend-specific atomicity.'],
    ['decrement(key, delta=1, namespace=None)', 'Decrement numeric value.'],
    ['clear(namespace=None)', 'Clear all entries or one namespace.'],
    ['keys(pattern="*", namespace=None)', 'List keys matching a glob-like pattern.'],
    ['stats()', 'Return CacheStats snapshot from backend.'],
    ['touch(key, ttl, namespace=None)', 'Refresh TTL by reading and rewriting existing value.'],
    ['warm(items, ttl=None, namespace=None, tags=())', 'Preload many keys. Returns warmed count.'],
    ['health_check()', 'Write/read/delete probe key and update health state.'],
    ['get_or_default(key, default_factory, namespace=None)', 'Compute fallback without writing to cache.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Gauge className="w-4 h-4" />
          Cache / CacheService
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            CacheService
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          <DocTerm id="cache.CacheService">CacheService</DocTerm> is the primary app-facing API. It wraps a{' '}
          <DocTerm id="cache.MemoryBackend">CacheBackend</DocTerm> with namespacing, key prefixing, TTL jitter, stampede prevention, and structured fault emission.
        </p>
      </div>

      {/* Constructor and Properties */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Constructor and Properties</h2>
        <CodeBlock language="python" filename="aquilia/cache/service.py" highlightLines={[3, 4, 8]}>{`from aquilia.cache import CacheService, CacheConfig

service = CacheService(
    backend=my_backend,
    config=CacheConfig(default_ttl=300, namespace="default"),
)

# Properties
service.backend         # Returns the CacheBackend
service.config          # Returns the CacheConfig
service.is_distributed  # bool (delegates to backend)
service.is_healthy      # bool (checks initialized + health state)
`}</CodeBlock>
      </section>

      {/* Method Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Method Reference</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Signature</th>
                <th className="pb-3 font-semibold">Behavior</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {methods.map(([signature, description], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{signature}</td>
                  <td className="py-2.5 text-xs">{description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cache-Aside and Stampede Prevention */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cache-Aside and Stampede Prevention</h2>
        <p className={`mb-4 ${textMuted}`}>
          The <code className="text-aquilia-500">get_or_set(...)</code> pattern supports thundering-herd stampede prevention using a process-local in-memory singleflight futures map. While a key is being fetched, concurrent duplicate reads wait on the primary loader:
        </p>
        <CodeBlock language="python" filename="modules/users/service.py" highlightLines={[8, 12]}>{`from aquilia.cache import CacheService

class UserService:
    def __init__(self, cache: CacheService, repo):
        self.cache = cache
        self.repo = repo

    async def get_user(self, user_id: str):
        return await self.cache.get_or_set(
            key=f"user:{user_id}",
            loader=lambda: self.repo.find_user(user_id),
            ttl=300,
            namespace="users",
            tags=("users", f"user:{user_id}"),
        )
`}</CodeBlock>
      </section>

      {/* Batch and Invalidation Operations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Batch and Invalidation Operations</h2>
        <CodeBlock language="python" filename="modules/catalog/cache_ops.py" highlightLines={[4, 10, 13, 16]}>{`from aquilia.cache import CacheService

async def refresh_catalog(cache: CacheService, catalog_items: dict[str, dict]):
    await cache.set_many(
        items={f"product:{k}": v for k, v in catalog_items.items()},
        ttl=120,
        namespace="catalog",
    )

    values = await cache.get_many(["product:1", "product:2"], namespace="catalog")

    # Invalidate by tags (group invalidation)
    await cache.invalidate_tags("products")

    # Invalidate whole namespace
    await cache.invalidate_namespace("catalog")

    return values
`}</CodeBlock>
      </section>

      {/* Observability and Health */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Observability and Health</h2>
        <CodeBlock language="python" filename="cache_health.py" highlightLines={[1, 4]}>{`stats = await cache.stats()
print(stats.to_dict())

ok = await cache.health_check()
print("cache healthy:", ok)
`}</CodeBlock>
      </section>

      {/* Behavior Notes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Behavior Notes</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            • <code className="text-aquilia-500">get(...)</code> and <code className="text-aquilia-500">get_many(...)</code> degrade gracefully, returning default values on connection errors rather than raising exceptions.
          </p>
          <p>
            • <code className="text-aquilia-500">set(...)</code> and <code className="text-aquilia-500">set_many(...)</code> log errors and emit a structured cache fault, but do not raise, ensuring data persistence errors do not block the request.
          </p>
          <p>
            • Stampede prevention is local to the current python worker process. Coalescence does not occur across separate host nodes or parallel server processes.
          </p>
        </div>
      </section>

      {/* DI Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Example</h2>
        <p className={`mb-4 ${textMuted}`}>
          Inject <DocTerm id="cache.CacheService">CacheService</DocTerm> directly into controllers through dependency injection:
        </p>
        <CodeBlock language="python" filename="modules/products/controllers.py" highlightLines={[7, 13]}>{`from aquilia import Controller, GET
from aquilia.cache import CacheService

class ProductController(Controller):
    prefix = "/products"

    def __init__(self, cache: CacheService):
        self.cache = cache

    @GET("/{id}")
    async def get_product(self, ctx, id: int):
        product = await self.cache.get_or_set(
            f"product:{id}",
            lambda: self.repo.find(id),
            ttl=300,
            namespace="catalog",
        )
        return product
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Backends', link: '/docs/cache/backends' },
          { text: 'Decorators and Middleware', link: '/docs/cache/decorators' },
          { text: 'Configuration', link: '/docs/cache/configuration' },
          { text: 'API Reference', link: '/docs/cache/api-reference' },
        ]}
      />
    </div>
  )
}