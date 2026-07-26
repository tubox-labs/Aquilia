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
        <div className={`mt-6 rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
          <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Changed in 1.3.4 — key generation and <code className="text-aquilia-500">None</code> results</h3>
          <p className={`text-sm mb-3 ${textMuted}`}>
            Two decorator behaviors were corrected. Before 1.3.4 the first positional argument was
            excluded from every generated key, so all calls to a single-argument function collapsed
            onto one entry and returned another call&apos;s value. Keys are now built from the full
            call signature.
          </p>
          <CodeBlock language="python" filename="key_correctness.py">{`@cached(ttl=60, namespace="users")
async def fetch(user_id: int):
    return {"id": user_id}

await fetch(1)   # {'id': 1}
await fetch(2)   # before 1.3.4: {'id': 1}  <-- wrong value, served silently
                 # 1.3.4+:       {'id': 2}
`}</CodeBlock>
          <p className={`text-sm mt-4 mb-3 ${textMuted}`}>
            Results of <code className="text-aquilia-500">None</code> are also cached now (previously
            they were recomputed on every call, forever). Use <code className="text-aquilia-500">condition</code> to
            opt out where recomputation is intended.
          </p>
          <CodeBlock language="python" filename="none_caching.py">{`# 1.3.4+: the negative result is cached for its TTL
@cached(ttl=60, namespace="lookups")
async def find_user(email: str) -> User | None:
    return await User.objects.filter(email=email).first()

# Opt out: recompute on every call, as before 1.3.4
@cached(ttl=60, namespace="lookups", condition=lambda r: r is not None)
async def find_user_strict(email: str) -> User | None:
    return await User.objects.filter(email=email).first()
`}</CodeBlock>
          <p className={`text-sm mt-4 ${textMuted}`}>
            Decorator keys now also carry the configured <code className="text-aquilia-500">key_prefix</code> and{' '}
            <code className="text-aquilia-500">key_version</code> and embed the namespace exactly once,
            matching keys built by <code className="text-aquilia-500">CacheService</code> directly.
            Existing entries written under the old layout become unreachable and expire under their
            own TTL. If you use <code className="text-aquilia-500">@cached</code> on plain functions with a
            distributed backend, flush the affected namespaces after upgrading.
          </p>
        </div>
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
        <CodeBlock language="python" filename="cache_middleware_signature.py" highlightLines={[2, 5, 8]}>{`CacheMiddleware(
    cache_service,
    default_ttl: int = 60,
    cacheable_methods: tuple[str, ...] = ("GET", "HEAD"),
    vary_headers: tuple[str, ...] = ("Accept", "Accept-Encoding"),
    namespace: str = "http_response",
    stale_while_revalidate: int = 0,
    cache_authenticated: bool = False,   # 1.3.4+
)`}</CodeBlock>
        <div className={`my-6 rounded-xl border p-5 ${isDark ? 'border-amber-500/30 bg-amber-500/5' : 'border-amber-300 bg-amber-50'}`}>
          <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Security — identity-aware caching (changed in 1.3.4)</h3>
          <p className={`text-sm mb-3 ${textMuted}`}>
            The response cache is <strong>shared</strong>. Before 1.3.4 the default cache key varied
            only on <code className="text-aquilia-500">Accept</code> and{' '}
            <code className="text-aquilia-500">Accept-Encoding</code>, so on a per-user route the first
            authenticated visitor&apos;s response was cached and served to everyone else hitting that
            path until the TTL expired.
          </p>
          <p className={`text-sm mb-3 ${textMuted}`}>
            Two safeguards now apply, and neither can be disabled implicitly:
          </p>
          <ol className={`list-decimal pl-6 space-y-1 text-sm mb-3 ${textMuted}`}>
            <li>
              A request carrying <code className="text-aquilia-500">Cookie</code> or{' '}
              <code className="text-aquilia-500">Authorization</code> bypasses the cache unless that
              header is listed in <code className="text-aquilia-500">vary_headers</code> <em>and</em>{' '}
              <code className="text-aquilia-500">cache_authenticated=True</code> is passed.
            </li>
            <li>
              A response that sets <code className="text-aquilia-500">Set-Cookie</code> is never stored.
            </li>
          </ol>
          <p className={`text-sm ${textMuted}`}>
            Both paths mark the response <code className="text-aquilia-500">X-Cache: PRIVATE</code>.
            Anonymous traffic caches exactly as before. Expect a hit-rate drop on authenticated
            routes after upgrading — that drop is the leak closing.
          </p>
        </div>
        <CodeBlock language="python" filename="server_setup.py" highlightLines={[3, 16]}>{`from aquilia.cache.middleware import CacheMiddleware

# Anonymous / public routes -- safe default, nothing extra required
server.middleware_stack.add(
    CacheMiddleware(
        cache_service=cache_service,
        default_ttl=60,
        cacheable_methods=("GET", "HEAD"),
        vary_headers=("Accept", "Accept-Encoding"),
        namespace="http",
        stale_while_revalidate=30,
    ),
    scope="global",
    priority=26,
    name="cache",
)

# Deliberate per-identity caching -- opt in AND vary on the identity header
CacheMiddleware(
    cache_service=cache_service,
    default_ttl=30,
    vary_headers=("Accept", "Cookie"),
    cache_authenticated=True,
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