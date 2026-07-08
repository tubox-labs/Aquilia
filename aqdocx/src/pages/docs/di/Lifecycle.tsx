import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DILifecycle() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Lifecycle
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Lifecycle Hooks &amp; Disposal
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          The lifecycle engine under <code className="text-aquilia-500">aquilia/di/lifecycle.py</code> manages priority-ordered startup transitions, LIFO finalization hooks, and disposal strategies.
        </p>
      </div>

      {/* DisposalStrategy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DisposalStrategy</h2>
        <p className={`mb-4 ${subtleText}`}>
          Governs the execution behavior of registered finalizers during container teardown:
        </p>
        <CodeBlock language="python" filename="DisposalStrategy Enum">{`from aquilia.di import DisposalStrategy

class DisposalStrategy(str, Enum):
    LIFO     = "lifo"      # Last-in, first-out (default)
    FIFO     = "fifo"      # First-in, first-out
    PARALLEL = "parallel"  # Concurrent teardown via asyncio.gather`}</CodeBlock>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mt-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Strategy</th>
                <th className="py-4 px-6 text-left font-semibold">Order</th>
                <th className="py-4 px-6 text-left font-semibold">Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['LIFO', 'Last registered → first disposed', 'Default. Ensures dependent components tear down before their parent databases (e.g. models close before db pool).'],
                ['FIFO', 'First registered → first disposed', 'When cleanup must strictly match startup order.'],
                ['PARALLEL', 'All at once via asyncio.gather', 'Teardown independent services in parallel for maximum shutdown speed.'],
              ].map(([strategy, order, usecase], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{strategy}</td>
                  <td className="py-3.5 px-6 font-semibold text-xs">{order}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{usecase}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* LifecycleHook */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>LifecycleHook</h2>
        <p className={`mb-4 ${subtleText}`}>
          Dataclass wrapping startup or teardown callbacks:
        </p>
        <CodeBlock language="python" filename="LifecycleHook Dataclass">{`from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class LifecycleHook:
    name: str                    # Hook identifier
    callback: Callable           # Async callable to execute
    priority: int = 0            # Ascending execution order (lower runs first)
    phase: Optional[str] = None  # Hook phase category`}</CodeBlock>
      </section>

      {/* Auto-Detection of Lifecycle Methods */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auto-Detection of Lifecycle Methods</h2>
        <p className={`mb-4 ${subtleText}`}>
          The container scans registered services automatically. If a class exposes <code className="text-aquilia-500">on_startup</code> or <code className="text-aquilia-500">on_shutdown</code>, it is bound as a lifecycle hook:
        </p>
        <CodeBlock language="python" filename="Auto-detected Lifecycle Methods">{`@service(scope="singleton")
class DatabasePool:
    def __init__(self, config: AppConfig):
        self.config = config
        self.pool = None
    
    async def on_startup(self):
        """Discovered automatically: registered as a startup hook."""
        self.pool = await asyncpg.create_pool(dsn=self.config.db_url)
    
    async def on_shutdown(self):
        """Discovered automatically: registered as a shutdown hook."""
        if self.pool:
            await self.pool.close()`}</CodeBlock>
      </section>

      {/* Request vs App Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request vs App Lifecycle</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Aspect</th>
                <th className="py-4 px-6 text-left font-semibold">App Container</th>
                <th className="py-4 px-6 text-left font-semibold">Request Container</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['Lifecycle instance', 'Full Lifecycle object', '_NullLifecycleType (no-op singleton)'],
                ['Startup hooks', 'Run on container.startup()', 'None — no startup for requests'],
                ['Shutdown hooks', 'Run on container.shutdown()', 'None — only finalizers run'],
                ['Finalizers', 'LIFO disposal of app instances', 'LIFO disposal of request-scoped instances'],
                ['Cache clearing', 'Clears all cached instances', 'Clears request-scoped cache only'],
                ['Typical lifetime', 'Process lifetime', 'Single HTTP request (~ms)'],
              ].map(([aspect, app, request], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6"><strong>{aspect}</strong></td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{app}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{request}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Full Lifecycle Context */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Full Lifecycle Context</h2>
        <CodeBlock language="python" filename="Lifecycle Setup">{`from aquilia.di import LifecycleContext

# Build and run the app server inside a LifecycleContext
container = registry.build_container()

async with LifecycleContext(container):
    # 1. Triggers container.startup()
    # 2. Runs all startup hooks
    await run_server()
    # 3. Triggers container.shutdown() on block exit
    # 4. Cleans finalizers LIFO → shutdown hooks priority`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/decorators" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Decorators
        </Link>
        <Link to="/docs/di/diagnostics" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Diagnostics <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}