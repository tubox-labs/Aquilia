import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Zap className="w-4 h-4" />
          <span>ADVANCED / EFFECTS SYSTEM</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Effects &amp; Composable Capabilities
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Effects system provides a declarative way to request side-effects (database transactions, caching, queue publishing). Rather than invoking hardcoded dependencies, handlers request capability tokens, which the <DocTerm id="effects.EffectRegistry">EffectRegistry</DocTerm> resolves at request time.
        </p>
      </div>

      {/* Concept Architecture */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>How Capabilities are Resolved</h2>
        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 leading-relaxed">
          <p className="mb-4">
            Instead of mock dependencies and test config drift, handlers declare capability tokens. The runtime resolves them through a clean three-step lifecycle:
          </p>
          <div className="flex flex-col md:flex-row gap-4 font-mono text-xs my-6">
            <div className="flex-1 p-4 bg-white/5 rounded border border-white/5">
              <span className="text-aquilia-500 font-bold block mb-1">1. DECLARE TOKEN</span>
              <p className="text-gray-400 text-xs font-sans">Handlers request capability via token classes like <DocTerm id="effects.DBTxHandle">DBTx["read"]</DocTerm>.</p>
            </div>
            <div className="flex-1 p-4 bg-white/5 rounded border border-white/5">
              <span className="text-aquilia-500 font-bold block mb-1">2. PROVIDER ACQUIRE</span>
              <p className="text-gray-400 text-xs font-sans">Before execution, <DocTerm id="effects.EffectProvider">EffectProvider</DocTerm> acquires connections, scopes, or topics.</p>
            </div>
            <div className="flex-1 p-4 bg-white/5 rounded border border-white/5">
              <span className="text-aquilia-500 font-bold block mb-1">3. AUTOMATIC RELEASE</span>
              <p className="text-gray-400 text-xs font-sans">On handler completion, the provider commits, rolls back, or closes handles automatically.</p>
            </div>
          </div>
        </div>
      </section>

      {/* The Provider Contract */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>The EffectProvider Contract</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Every effect resource must have a corresponding <DocTerm id="effects.EffectProvider">EffectProvider</DocTerm> implementation. It defines four hooks called by the registry:
        </p>

        <div className="space-y-6 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">initialize()</code>
            <p className="text-sm text-gray-400 mt-1">Invoked once at server startup. Ideal for setting up database connection pools or client sessions.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">acquire(mode)</code>
            <p className="text-sm text-gray-400 mt-1">Invoked per-request. Retrieves the target resource (e.g. acquiring a transaction instance or a bucket namespace).</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">release(resource, success)</code>
            <p className="text-sm text-gray-400 mt-1">Invoked when a request finishes. The <code className="text-aquilia-400">success</code> boolean flags whether to commit or rollback the state.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">finalize()</code>
            <p className="text-sm text-gray-400 mt-1">Invoked at server shutdown to safely drain connection pools and close active clients.</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Declaring Requirements</h2>
        <CodeBlock language="python" filename="effects_usage.py" highlightLines={[6, 9, 10]}>{`from aquilia.effects import DBTx, CacheEffect
from aquilia.controller import Controller

class OrderController(Controller):
    # Declare required capabilities for the controller routing
    effects = [
        DBTx["write"],          # Read-write database access
        CacheEffect("orders"),   # "orders" cache namespace
    ]

    @Post("/")
    async def create_order(self, ctx):
        # Access pre-acquired capabilities directly
        # ctx.effects.db is an active DBTxHandle
        await ctx.effects.db.execute("INSERT INTO orders ...")
        await ctx.effects.cache.set("recent", {"order_id": 123})`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/aquilary/fingerprint" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Fingerprinting
        </Link>
        <Link to="/docs/effects/dbtx" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          DBTx Effect <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}