import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'


export function FaultsTaxonomy() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>FAULTS / TAXONOMY & RESULTS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Fault Taxonomy &amp; Outcomes
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Every error in Aquilia is categorized by its severity and domain, and processed by handlers returning a strict union type called <code className="text-aquilia-500">FaultResult</code>.
        </p>
      </div>

      {/* Severity Levels */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Severity Classification</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code className="text-aquilia-500">Severity</code> enum dictates logging urgency and retry capabilities:
        </p>

        <div className="space-y-4">
          <div className="border-l-2 border-blue-500/20 pl-4 py-1">
            <span className="text-blue-400 font-mono text-xs font-bold uppercase">Severity.INFO</span>
            <p className="text-sm text-gray-400 mt-1">Informational incidents. Logged at info level, requires no immediate correction.</p>
          </div>
          <div className="border-l-2 border-yellow-500/20 pl-4 py-1">
            <span className="text-yellow-400 font-mono text-xs font-bold uppercase">Severity.WARN</span>
            <p className="text-sm text-gray-400 mt-1">Degraded application behavior. Does not stop request execution.</p>
          </div>
          <div className="border-l-2 border-orange-500/20 pl-4 py-1">
            <span className="text-orange-400 font-mono text-xs font-bold uppercase">Severity.ERROR</span>
            <p className="text-sm text-gray-400 mt-1">Request failed. Aborts the thread, requires handling or returns error response.</p>
          </div>
          <div className="border-l-2 border-red-500/20 pl-4 py-1">
            <span className="text-red-400 font-mono text-xs font-bold uppercase">Severity.FATAL</span>
            <p className="text-sm text-gray-400 mt-1">System-level crash. Stops the process or aborts the entire ASGI lifespan.</p>
          </div>
        </div>
      </section>

      {/* FaultResult Union */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Handler outcomes: FaultResult</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          A custom fault handler determines propagation by returning one of three frozen dataclasses that comprise the <code className="text-aquilia-500">FaultResult</code> type:
        </p>

        <div className="space-y-6 mb-8 text-sm">
          <div className="border-b border-white/5 pb-4">
            <code className="text-white text-xs font-mono font-bold block mb-1">Resolved(response)</code>
            <p className="text-gray-400 mt-1">
              Instructs the engine that the fault is handled. It stops propagation and returns the enclosed <code className="text-aquilia-300">Response</code> object directly.
            </p>
          </div>
          <div className="border-b border-white/5 pb-4">
            <code className="text-white text-xs font-mono font-bold block mb-1">Transformed(new_fault, preserve_context=True)</code>
            <p className="text-gray-400 mt-1">
              Transforms the active error into a new fault class and continues bubbling it up the handler chain.
            </p>
          </div>
          <div className="pb-4">
            <code className="text-white text-xs font-mono font-bold block mb-1">Escalate()</code>
            <p className="text-gray-400 mt-1">
              Declines handling the fault. It escalates the error to the next outer handler in the parent scope.
            </p>
          </div>
        </div>

        <CodeBlock language="python" filename="fault_results.py" highlightLines={[6, 9, 12]}>{`from aquilia.faults import Resolved, Transformed, Escalate, FaultResult
from aquilia.response import Response

def handle_error(fault, ctx) -> FaultResult:
    if fault.code == "EXPIRED_SESSION":
        # Resolve error, return 401 response
        return Resolved(Response("Session expired", status=401))
        
    if fault.code == "RAW_DB_ERROR":
        # Transform error
        return Transformed(ApiFault("DATABASE_ERROR"))
        
    # Otherwise escalate
    return Escalate()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/faults/taxonomy" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/faults/engine" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          FaultEngine <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}