import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Gauge } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheDecorators() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'

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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaCache includes function decorators for declarative read caching and invalidation,
          plus an HTTP response-cache middleware.
        </p>
      </div>

      {/* @cached */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}><DocTerm id="cache.cached">@cached</DocTerm></h2>
        <p className={`mb-4 ${textMuted}`}>
          Caches function results by key. On a cache miss, it executes the target function, optionally validates the result, and stores it in the cache with the specified TTL and tags.
        </p>
        <CodeBlock language="python" filename="aquilia/cache/decorators.py" highlightLines={[2, 3, 5]}>{`@cached(
    ttl: int = 300,
    namespace: str = "default",
    key: str | None = None,
    key_func: Callable[..., str] | None = None,   # (func, args, kwargs) -> key
    tags: tuple[str, ...] = (),
    unless: Callable[..., bool] | None = None,    # skip caching if True
    condition: Callable[[Any], bool] | None = None, # cache only if True
)`}</CodeBlock>
        <CodeBlock language="python" filename="cached_usage.py" highlightLines={[3, 8, 14]}>{`from aquilia.cache import cached

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

      {/* @cache_aside */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}><DocTerm id="cache.cache_aside">@cache_aside</DocTerm></h2>
        <p className={`mb-4 ${textMuted}`}>
          A semantic alias for <DocTerm id="cache.cached">@cached</DocTerm> with identical runtime behavior. Use it to indicate that the decorated function is the authoritative source of truth for the cached data.
        </p>
        <CodeBlock language="python" filename="cache_aside.py" highlightLines={[3]}>{`from aquilia.cache import cache_aside

@cache_aside(ttl=180, namespace="products", tags=("products",))
async def find_product(product_id: int):
    return await Product.objects.get(id=product_id)
`}</CodeBlock>
      </section>

      {/* @invalidate */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}><DocTerm id="cache.invalidate">@invalidate</DocTerm></h2>
        <p className={`mb-4 ${textMuted}`}>
          Executes the wrapped function first (typically a write operation), and then invalidates specified keys and/or tags.
        </p>
        <CodeBlock language="python" filename="aquilia/cache/decorators.py" highlightLines={[2, 4]}>{`@invalidate(
    *keys: str,
    namespace: str = "default",
    tags: tuple[str, ...] = (),
)`}</CodeBlock>
        <CodeBlock language="python" filename="invalidate_usage.py" highlightLines={[3, 7]}>{`from aquilia.cache import invalidate

@invalidate("products:list:v1", namespace="catalog", tags=("products",))
async def create_product(data: dict):
    return await product_repo.create(data)

@invalidate(tags=("products", "catalog:list"), namespace="catalog")
async def import_products(batch: list[dict]):
    return await product_repo.bulk_insert(batch)
`}</CodeBlock>
      </section>

      {/* CacheMiddleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}><DocTerm id="cache.CacheMiddleware">CacheMiddleware</DocTerm></h2>
        <p className={`mb-4 ${textMuted}`}>
          HTTP response cache middleware. Intercepts incoming requests, generates and validates ETags, vary headers, and serves cached response payloads for GET/HEAD methods.
        </p>
        <CodeBlock language="python" filename="cache_middleware_signature.py" highlightLines={[2, 5]}>{`CacheMiddleware(
    cache_service,
    default_ttl: int = 60,
    cacheable_methods: tuple[str, ...] = ("GET", "HEAD"),
    vary_headers: tuple[str, ...] = ("Accept", "Accept-Encoding"),
    namespace: str = "http_response",
    stale_while_revalidate: int = 0,
)`}</CodeBlock>
        <CodeBlock language="python" filename="server_setup.py" highlightLines={[3]}>{`from aquilia.cache.middleware import CacheMiddleware

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

      {/* Decorator Cache Resolution */}
      <section className="mb-16 border-l-2 border-aquilia-500/20 pl-6 py-1">
        <h2 className={`text-xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorator Cache Resolution</h2>
        <p className={`text-sm mb-3 ${textMuted}`}>
          Decorators automatically resolve the active <DocTerm id="cache.CacheService">CacheService</DocTerm> in the following order:
        </p>
        <ol className={`list-decimal pl-6 space-y-2 text-sm ${textMuted}`}>
          <li>Checks for a <code className="text-aquilia-500">self.cache</code> attribute on the first argument (typical for controllers).</li>
          <li>Checks for a <code className="text-aquilia-500">self._cache</code> attribute on the first argument.</li>
          <li>Falls back to the module-level default cache service registered via <code className="text-aquilia-500">set_default_cache_service(...)</code>.</li>
        </ol>
        <CodeBlock language="python" filename="default_cache_service.py" highlightLines={[3]}>{`from aquilia.cache.decorators import set_default_cache_service

# Optional manual setup if using decorators on standalone helper functions
set_default_cache_service(cache_service)
`}</CodeBlock>
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