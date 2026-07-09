import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsCacheEffect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / CACHE EFFECT</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Cache Effect
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="effects.CacheEffect">CacheEffect</DocTerm> enables scoped key-value caching in Aquilia request handlers. Managed by the <DocTerm id="effects.CacheProvider">CacheProvider</DocTerm>, it partitions cache keys by namespace to prevent key collisions across modules.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Namespace Isolation</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            Rather than mixing keys in a single flat database namespace (which leads to key collisions and complex prefixing logic), the <DocTerm id="effects.CacheEffect">CacheEffect</DocTerm> partitions operations. By requesting a namespace at initialization (e.g. <code className="text-white">CacheEffect("products")</code>), the handle transparently prefixes all operations, keeping caching logic localized.
          </p>
        </div>
      </section>

      {/* The Caching Handles */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Resource Handles</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Depending on the system state, the <DocTerm id="effects.CacheProvider">CacheProvider</DocTerm> yields one of two resource handles:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 text-sm">
          <div className="border-l border-aquilia-500/20 pl-6 py-2">
            <code className="text-white text-xs font-mono font-bold block mb-1">CacheServiceHandle</code>
            <p className="text-gray-400 leading-relaxed font-light">
              Acquired when the caching integration is enabled. It forwards operations to a central, DI-injected <code className="text-aquilia-400">CacheService</code> connected to Redis or Memcached.
            </p>
          </div>
          <div className="border-l border-blue-500/20 pl-6 py-2">
            <code className="text-white text-xs font-mono font-bold block mb-1">CacheHandle</code>
            <p className="text-gray-400 leading-relaxed font-light">
              A fallback handle backed by a standard Python dictionary. Used during unit testing or when the main cache backend is unconfigured, ensuring handlers run without throwing connection exceptions.
            </p>
          </div>
        </div>
      </section>

      {/* Handle API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">API Reference</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Both handles expose the same core async methods, making tests consistent with production:
        </p>

        <div className="space-y-8 pl-4 border-l border-purple-500/20 text-sm text-gray-400">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.get(key: str) -> Any | None`}</CodeBlock>
            <p className="mt-2 font-light">Retrieves the deserialized cache value. Returns <code className="text-aquilia-500">None</code> on a cache miss.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.set(key: str, value: Any, ttl: int | None = None) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Stores the value inside the namespace. Accepts an optional TTL (in seconds) that defaults to the config value if omitted.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.delete(key: str) -> bool`}</CodeBlock>
            <p className="mt-2 font-light">Deletes the value matching the key from the namespace. Returns <code className="text-aquilia-500">True</code> if the key existed and was deleted, <code className="text-aquilia-500">False</code> otherwise.</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Usage: Cache-Aside with Automatic Invalidation</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The example below demonstrates retrieving a user's permissions and profile metadata from cache, falling back to a database transaction on a miss, and caching it. We also show how to invalidate the cache key when updating user permissions:
        </p>

        <CodeBlock language="python" filename="controllers/security.py" highlightLines={[8, 14, 18, 30]}>{`from aquilia.controller import Controller, GET, PATCH, RequestCtx
from aquilia.flow import requires
from aquilia.effects import CacheEffect, DBTx

class SecurityController(Controller):
    # Require both cache and db transaction capabilities
    effects = [
        CacheEffect(namespace="permissions"),
        DBTx["write"]  # Write required for update, used as read for retrieve
    ]

    @GET("/users/:id/permissions")
    async def get_permissions(self, id: int, ctx: RequestCtx) -> dict:
        cache = ctx.get_effect("Cache")
        db = ctx.get_effect("DBTx")
        
        # 1. Attempt to load from the namespaced permissions cache
        cache_key = f"user:{id}:roles"
        roles = await cache.get(cache_key)
        
        if roles is None:
            # 2. Cache Miss - Fetch from Database
            roles = await db.fetch_all(
                "SELECT role_name FROM user_roles WHERE user_id = ?", 
                (id,)
            )
            # Normalize to basic dictionary list for serialization
            roles = [dict(r) for r in roles]
            
            # 3. Cache results for 1 hour
            await cache.set(cache_key, roles, ttl=3600)
            
        return ctx.json({"user_id": id, "roles": roles})

    @PATCH("/users/:id/permissions")
    async def update_permissions(self, id: int, ctx: RequestCtx) -> dict:
        body = await ctx.json()
        cache = ctx.get_effect("Cache")
        db = ctx.get_effect("DBTx")
        
        # 1. Update roles in DB
        await db.execute("DELETE FROM user_roles WHERE user_id = ?", (id,))
        await db.execute_many(
            "INSERT INTO user_roles (user_id, role_name) VALUES (?, ?)",
            [(id, role) for role in body["roles"]]
        )
        
        # 2. Invalidate cache key to ensure subsequent requests load fresh state
        cache_key = f"user:{id}:roles"
        await cache.delete(cache_key)
        
        return ctx.json({"status": "permissions_updated"})`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/effects/dbtx" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> DBTx Effect
        </Link>
        <Link to="/docs/effects/queue" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Queue Effect <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}