import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Gauge } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheDecorators() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Gauge className="w-4 h-4" />
          Cache / Decorators
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Cache Decorators
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          AquilaCache includes function decorators for declarative read caching and invalidation,
          plus an HTTP response-cache middleware.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@cached</h2>
        <p className={`mb-4 ${subtle}`}>
          Caches function results by key. On miss it executes the function, optionally validates the result,
          then stores with TTL and tags.
        </p>
        <CodeBlock language="python" filename="aquilia/cache/decorators.py">{`@cached(
    ttl: int = 300,
    namespace: str = "default",
    key: str | None = None,
    key_func: Callable[..., str] | None = None,   # (func, args, kwargs) -> key
    tags: tuple[str, ...] = (),
    unless: Callable[..., bool] | None = None,    # skip caching if True
    condition: Callable[[Any], bool] | None = None, # cache only if True
)`}</CodeBlock>
        <CodeBlock language="python" filename="cached_usage.py">{`from aquilia.cache import cached

@cached(ttl=60, namespace="api")
async def get_popular_products():
    return await db.fetch_all("SELECT * FROM products ORDER BY views DESC LIMIT 20")

@cached(
    ttl=300,
    key_func=lambda func, args, kwargs: f"user:{kwargs.get('user_id', args[0])}",
    condition=lambda result: result is not None,
)
async def get_user_profile(user_id: int):
    return await User.objects.get(id=user_id)

@cached(
    ttl=120,
    namespace="feed",
    unless=lambda *args, **kwargs: kwargs.get("no_cache", False),
)
async def get_feed(user_id: str, *, no_cache: bool = False):
    return await feed_repo.fetch(user_id)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@cache_aside</h2>
        <p className={`mb-4 ${subtle}`}>
          Semantic alias for <code className="text-aquilia-500">@cached</code> with the same runtime behavior.
          Use it when you want to communicate cache-aside intent explicitly.
        </p>
        <CodeBlock language="python" filename="cache_aside.py">{`from aquilia.cache import cache_aside

@cache_aside(ttl=180, namespace="products", tags=("products",))
async def find_product(product_id: int):
    return await Product.objects.get(id=product_id)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@invalidate</h2>
        <p className={`mb-4 ${subtle}`}>
          Executes the wrapped function first, then invalidates explicit keys and/or tags.
        </p>
        <CodeBlock language="python" filename="aquilia/cache/decorators.py">{`@invalidate(
    *keys: str,
    namespace: str = "default",
    tags: tuple[str, ...] = (),
)`}</CodeBlock>
        <CodeBlock language="python" filename="invalidate_usage.py">{`from aquilia.cache import invalidate

@invalidate("products:list:v1", namespace="catalog", tags=("products",))
async def create_product(data: dict):
    return await product_repo.create(data)

@invalidate(tags=("products", "catalog:list"), namespace="catalog")
async def import_products(batch: list[dict]):
    return await product_repo.bulk_insert(batch)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CacheMiddleware</h2>
        <p className={`mb-4 ${subtle}`}>
          HTTP response cache middleware in <code className="text-aquilia-500">aquilia.cache.middleware.CacheMiddleware</code>.
          Supports GET/HEAD response caching, ETag checks, stale-while-revalidate, and secure bypass token support.
        </p>
        <CodeBlock language="python" filename="cache_middleware_signature.py">{`CacheMiddleware(
    cache_service,
    default_ttl: int = 60,
    cacheable_methods: tuple[str, ...] = ("GET", "HEAD"),
    vary_headers: tuple[str, ...] = ("Accept", "Accept-Encoding"),
    namespace: str = "http_response",
    stale_while_revalidate: int = 0,
)`}</CodeBlock>
        <CodeBlock language="python" filename="server_setup.py">{`from aquilia.cache.middleware import CacheMiddleware

server.middleware_stack.add(
    CacheMiddleware(
        cache_service=cache_service,
        default_ttl=60,
        cacheable_methods=("GET", "HEAD"),
        vary_headers=("Accept", "Accept-Encoding", "Authorization"),
        namespace="http",
        stale_while_revalidate=30,
    ),
    scope="global",
    priority=26,
    name="cache",
)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorator Cache Resolution</h2>
        <div className={box}>
          <p className={`text-sm mb-3 ${subtle}`}>
            Decorator wrappers resolve cache service in this order:
          </p>
          <ol className={`list-decimal pl-6 space-y-2 text-sm ${subtle}`}>
            <li><code className="text-aquilia-500">self.cache</code> on first argument.</li>
            <li><code className="text-aquilia-500">self._cache</code> on first argument.</li>
            <li>Module-level default via <code className="text-aquilia-500">set_default_cache_service(...)</code>.</li>
          </ol>
          <CodeBlock language="python" filename="default_cache_service.py">{`from aquilia.cache.decorators import set_default_cache_service

# Optional manual setup if using decorators outside DI-bound classes
set_default_cache_service(cache_service)
`}</CodeBlock>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Important Notes</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Current server auto-wiring for response middleware reads nested <code className="text-aquilia-500">cache.middleware</code> keys, while primary cache config is flat.</li>
            <li>Current auto-wiring call uses <code className="text-aquilia-500">ttl=...</code> but middleware constructor expects <code className="text-aquilia-500">default_ttl=...</code>.</li>
            <li>HTTP client middleware cache in <code className="text-aquilia-500">aquilia/http/middleware.py</code> is separate from this response cache middleware.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'CacheService API', link: '/docs/cache/service' },
          { text: 'Backends', link: '/docs/cache/backends' },
          { text: 'Configuration', link: '/docs/cache/configuration' },
          { text: 'Cache CLI', link: '/docs/cache/cli' },
        ]}
      />
    </div>
  )
}