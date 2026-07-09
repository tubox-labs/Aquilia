import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function FaultsEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>FAULTS / FAULT ENGINE</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          FaultEngine Execution
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="faults.FaultEngine">FaultEngine</DocTerm> orchestrates runtime error resolution. It converts raw exceptions, coordinates scoped handlers, and enforces fallback policies.
        </p>
      </div>

      {/* Processing Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Engine Processing Stages</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When an uncaught exception is intercepted by the framework, <DocTerm id="faults.FaultEngine">FaultEngine</DocTerm> executes four sequential stages:
        </p>

        <div className="space-y-6 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">1. Context Capture</span>
            <p className="text-sm text-gray-400 mt-1">
              Wraps the exception inside a <DocTerm id="faults.FaultContext">FaultContext</DocTerm> object, capturing traceback frames, timestamp offsets, request identifiers, and trace IDs.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">2. Scoped Handler Lookup</span>
            <p className="text-sm text-gray-400 mt-1">
              Searches for matching handlers in a strict topological order: Route-specific handlers → App-specific handlers → Global handlers.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">3. Execution Loop</span>
            <p className="text-sm text-gray-400 mt-1">
              Runs candidate handlers in priority order. If a handler returns <code className="text-aquilia-400">Resolved(response)</code>, execution halts and the response returns. If it returns <code className="text-aquilia-400">Transformed(new_fault)</code>, the engine replaces the error and restarts the resolution loop.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">4. ASGI Fallback</span>
            <p className="text-sm text-gray-400 mt-1">
              If all handlers return <code className="text-aquilia-400">Escalate()</code> or decline (raising uncaught errors), the exception escapes to the ASGI <code className="text-aquilia-400">FaultMiddleware</code>, returning a masked 500 JSON response or rendering a debug traceback page.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Wiring Handlers</h2>
        <CodeBlock language="python" filename="fault_engine_wire.py" highlightLines={[6, 9]}>{`from aquilia.faults import FaultEngine

engine = FaultEngine()

# 1. Register a handler globally
engine.register_global(CustomGlobalHandler())

# 2. Register an app-specific handler (app name must match manifest name)
engine.register_app("auth", AuthModuleHandler())`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/faults/taxonomy" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Taxonomy
        </Link>
        <Link to="/docs/faults/handlers" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Fault Handlers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}