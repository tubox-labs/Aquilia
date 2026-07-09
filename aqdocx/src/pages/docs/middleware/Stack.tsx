import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareStack() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / STACK & COMPOSITION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Middleware Stack
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm> manages middleware registration, verifies structural contracts at startup, and compiles the execution pipelines.
        </p>
      </div>

      {/* Strict Signature Validation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Startup Contract Validation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When you register middleware using <code className="text-aquilia-500">.middleware()</code> or direct <code className="text-aquilia-500">stack.add()</code>, Aquilia performs four rigorous inspection checks using Python's reflection APIs before running the server:
        </p>

        <div className="space-y-6 mb-8">
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">1. Inheritance Check</span>
            <p className="text-sm text-gray-400 mt-1">
              Class instances must inherit from the <code className="text-aquilia-400">Middleware</code> base class. Raw functions bypass this check if they are directly callable.
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">2. Callability Check</span>
            <p className="text-sm text-gray-400 mt-1">
              The registered object must be callable (i.e. possess an active <code className="text-aquilia-400">__call__</code> method or be a routine).
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">3. Parameter Count Check</span>
            <p className="text-sm text-gray-400 mt-1">
              Signature inspection (via <code className="text-aquilia-400">inspect.signature</code>) enforces exactly three parameters: <code className="text-aquilia-300">(request, ctx, next_handler)</code>. Binds are verified at registration.
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">4. Async Coroutine Check</span>
            <p className="text-sm text-gray-400 mt-1">
              The entrypoint MUST be a coroutine function (<code className="text-aquilia-400">async def</code>). Sync callables trigger a runtime <code className="text-aquilia-400">TypeError</code> at boot.
            </p>
          </div>
        </div>
      </section>

      {/* Fast Path Execution */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Performance Optimizations: Fast Path</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          For latency-critical routes, building the full middleware chain adds microsecond overhead. Aquilia resolves this via two methods:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-4">
          <div>
            <h3 className="font-mono font-bold text-white text-xs uppercase tracking-wider mb-1">build_handler(final_handler)</h3>
            <p>Compiles the complete chain. Outermost middleware runs first, tracing frames if enabled.</p>
          </div>
          <div>
            <h3 className="font-mono font-bold text-white text-xs uppercase tracking-wider mb-1">build_fast_handler(final_handler)</h3>
            <p>
              Compiles a minimal chain. Dynamically strips non-essential, purely informational middlewares (specifically <code className="text-aquilia-400">LoggingMiddleware</code> and <code className="text-aquilia-400">TimeoutMiddleware</code>) while preserving security boundaries like <DocTerm id="middleware.CORSMiddleware">CORSMiddleware</DocTerm> and <DocTerm id="middleware.ExceptionMiddleware">ExceptionMiddleware</DocTerm>.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Manipulating the Stack</h2>
        <CodeBlock language="python" filename="custom_stack.py" highlightLines={[6, 9, 13]}>{`from aquilia.middleware import MiddlewareStack
from my_middlewares import SecurityMiddleware, LoggingMiddleware, Handler

stack = MiddlewareStack()

# 1. Register with scopes and priority
stack.add(SecurityMiddleware(), scope="global", priority=10, name="security")
stack.add(LoggingMiddleware(), scope="global", priority=90, name="logging")

# 2. Build normal handler (executes: Security -> Logging -> Handler)
handler = stack.build_handler(final_handler=Handler)

# 3. Build fast handler (executes: Security -> Handler; skips Logging)
fast_handler = stack.build_fast_handler(final_handler=Handler)`}</CodeBlock>
      </section>

      {/* Table of Built-in Middlewares */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Core Middleware Manifest</h2>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Class</th>
                <th className="py-3 px-4">Priority Band</th>
                <th className="py-3 px-4">Fast-Path Skippable</th>
                <th className="py-3 px-4">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans text-gray-400">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-aquilia-300">
                  <DocTerm id="middleware.RequestIdMiddleware">RequestIdMiddleware</DocTerm>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs">5 (Outermost)</td>
                <td className="py-3.5 px-4 text-xs font-mono text-red-500">NO</td>
                <td className="py-3.5 px-4 text-xs">Injects stable identifiers per request</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-aquilia-300">
                  <DocTerm id="middleware.ExceptionMiddleware">ExceptionMiddleware</DocTerm>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs">10</td>
                <td className="py-3.5 px-4 text-xs font-mono text-red-500">NO</td>
                <td className="py-3.5 px-4 text-xs">Converts exceptions into structured HTML/JSON</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-aquilia-300">
                  <DocTerm id="middleware.TimeoutMiddleware">TimeoutMiddleware</DocTerm>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs">15</td>
                <td className="py-3.5 px-4 text-xs font-mono text-green-500">YES</td>
                <td className="py-3.5 px-4 text-xs">Enforces processing limits; raises Faults</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs text-aquilia-300">
                  <DocTerm id="middleware.CompressionMiddleware">CompressionMiddleware</DocTerm>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs">40</td>
                <td className="py-3.5 px-4 text-xs font-mono text-red-500">NO</td>
                <td className="py-3.5 px-4 text-xs">Gzip thread-offloaded compression</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/middleware/built-in" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Built-in Middleware <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}