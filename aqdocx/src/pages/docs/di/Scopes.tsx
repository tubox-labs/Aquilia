import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIScopes() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Scopes
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Service Scopes &amp; Lifetimes
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Scopes define instance lifetimes and validation constraints. Aquilia enforces strict boundary checking to prevent memory leaks and concurrency race conditions.
        </p>
      </div>

      {/* ServiceScope Enum */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ServiceScope Enum</h2>
        <p className={`mb-4 ${subtleText}`}>
          Defined in <code className="text-aquilia-500">aquilia/di/scopes.py</code> as a string-based enum for simple manifest and decorator configurations:
        </p>
        <CodeBlock language="python" filename="ServiceScope Definition">{`from aquilia.di.scopes import ServiceScope

class ServiceScope(str, Enum):
    SINGLETON = "singleton"   # Process-wide lifetime
    APP       = "app"         # Application container lifetime
    REQUEST   = "request"     # Isolated request lifetime
    TRANSIENT = "transient"   # Uncached, new instance per resolution
    POOLED    = "pooled"      # Managed by asyncio.Queue instance pool
    EPHEMERAL = "ephemeral"   # Request-scoped temporary lifetime`}</CodeBlock>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mt-8">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Scope</th>
                <th className="py-4 px-6 text-left font-semibold">Lifetime</th>
                <th className="py-4 px-6 text-left font-semibold">Cached</th>
                <th className="py-4 px-6 text-left font-semibold">Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['SINGLETON', 'Process-wide', 'Yes (root)', 'Database connection pools, global configuration parameters, and shared memory clients.'],
                ['APP', 'App container', 'Yes (root)', 'Module service instances. Behaves identically to singleton in single-app structures.'],
                ['REQUEST', 'Per-request', 'Yes (child)', 'HTTP request-scoped handlers, user session details, context loggers, and blueprints.'],
                ['TRANSIENT', 'None', 'No', 'Stateless formatters, calculations, validation constraints, and helpers.'],
                ['POOLED', 'Pool-managed', 'Queue', 'Concurrency pools or heavy workers. Acquired/released via PoolProvider.'],
                ['EPHEMERAL', 'None', 'No', 'Lightweight temporary request-parented tasks.'],
              ].map(([scope, lifetime, cached, usecase], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{scope}</td>
                  <td className="py-3.5 px-6 text-xs font-medium">{lifetime}</td>
                  <td className="py-3.5 px-6 text-xs">{cached}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{usecase}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Scope Dataclass */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Injection Validation</h2>
        <p className={`mb-4 ${subtleText}`}>
          To enforce structural safety, Aquilia checks scope compatibility at startup:
        </p>
        <div className="space-y-2 mb-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span>Longer-lived scopes can always inject into shorter-lived scopes.</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span>Shorter-lived scopes <strong>CANNOT</strong> inject into longer-lived scopes (prevents memory leak state capture).</span>
          </div>
        </div>
      </section>

      {/* Injection Rules Matrix */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Injection Compatibility Matrix</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm text-center ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Provider ↓ / Consumer →</th>
                <th className="py-4 px-3 font-semibold">singleton</th>
                <th className="py-4 px-3 font-semibold">app</th>
                <th className="py-4 px-3 font-semibold">request</th>
                <th className="py-4 px-3 font-semibold">transient</th>
                <th className="py-4 px-3 font-semibold">ephemeral</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['singleton', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
                ['app', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
                ['request', 'No', 'No', 'Yes', 'Yes', 'Yes'],
                ['transient', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
                ['pooled', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
                ['ephemeral', 'No', 'No', 'No', 'Yes', 'Yes'],
              ].map(([scope, ...cells], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 text-left font-mono text-aquilia-500 text-xs">{scope}</td>
                  {cells.map((cell, j) => (
                    <td key={j} className={`py-3.5 px-3 font-medium ${cell === 'Yes' ? 'text-green-500' : 'text-red-500'}`}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Scope Violation Examples */}
      <section className="mb-16 border-l-2 border-red-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scope Violation Example</h2>
        <CodeBlock language="python" filename="Invalid — request-scoped into singleton">{`@service(scope="request")
class RequestLogger:
    def __init__(self, req: Request):
        self.req = req

@service(scope="singleton")
class GlobalAnalytics:
    # ❌ ScopeViolationError raised at startup:
    # Singleton cannot depend on short-lived request scope!
    def __init__(self, logger: RequestLogger):
        self.logger = logger`}</CodeBlock>

        <CodeBlock language="python" filename="Fix — Change consumer scope or resolve lazily">{`# Option A: Make the consumer request-scoped:
@service(scope="request")
class GlobalAnalytics:
    def __init__(self, logger: RequestLogger):
        self.logger = logger

# Option B: Access lazily via the context container
@service(scope="singleton")
class GlobalAnalytics:
    def __init__(self):
        pass
        
    async def track(self, ctx_container, event: str):
        logger = await ctx_container.resolve_async(RequestLogger)
        logger.info(event)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/providers" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Providers
        </Link>
        <Link to="/docs/di/decorators" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Decorators <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}