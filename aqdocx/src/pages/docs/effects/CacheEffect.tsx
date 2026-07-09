import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Workflow } from 'lucide-react'

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
          The <code className="text-aquilia-500">CacheEffect</code> handles key-value caching namespaces. It delegates to the active cache integrations (Redis, Memcached, or In-Memory), allowing handlers to get, set, and expire data cleanly.
        </p>
      </div>

      {/* Namespace Isolation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Namespace Isolation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Rather than mixing keys in a single flat namespace, <code className="text-aquilia-500">CacheEffect</code> partitions cache operations by namespace. At request start, the provider creates a scoped <code className="text-aquilia-400">CacheServiceHandle</code> which transparently prefixes keys with the namespace.
        </p>
      </section>

      {/* CacheServiceHandle API */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Using CacheServiceHandle</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The acquired caching resource provides a structured, async interface to perform caching operations:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.get(key)</code> — Resolves the deserialized cache payload, or returns <code className="text-aquilia-500">None</code> on a cache miss.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.set(key, value, ttl=None)</code> — Stores a value. Optional TTL specifies lifespan in seconds.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.delete(key)</code> — Removes a value from the cache.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.has(key)</code> — Returns a boolean indicating key existence without loading the payload.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.get_many(keys)</code> — Batch lookup, returning a key-to-value dictionary.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">await handle.set_many(mapping, ttl=None)</code> — Efficiently stores multiple key-value pairs in a single operation.
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Code Implementation</h2>
        <CodeBlock language="python" filename="cache_usage.py" highlightLines={[2, 6, 9]}>{`class ProductController(Controller):
    effects = [CacheEffect(namespace="products")]

    @Get("/:id")
    async def get_product(self, id: int, ctx):
        # 1. Attempt to resolve from namespace cache
        cache_key = f"detail:{id}"
        product = await ctx.effects.cache.get(cache_key)
        
        if product is None:
            # Cache miss - load from DB and populate cache
            product = await Product.objects.get(id=id)
            await ctx.effects.cache.set(cache_key, product.to_dict(), ttl=600)
            
        return ctx.json(product)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/effects/dbtx" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> DBTx Effect
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}