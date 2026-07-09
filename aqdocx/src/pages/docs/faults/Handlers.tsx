import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function FaultsHandlers() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>FAULTS / FAULT HANDLERS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Fault Handlers
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Custom handlers resolve propagating Faults. By implementing a two-method contract, handlers can intercept errors, translate them, or format custom responses.
        </p>
      </div>

      {/* The Handler Contract */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>The FaultHandler Contract</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Every custom handler must inherit from <DocTerm id="faults.FaultHandler">FaultHandler</DocTerm> and implement exactly two methods:
        </p>

        <div className="space-y-6 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold block mb-1">{"can_handle(ctx) -> bool"}</code>
            <p className="text-gray-400 mt-1">
              Evaluates the <DocTerm id="faults.FaultContext">FaultContext</DocTerm> predicate. Returns <code className="text-white">True</code> if this handler claims responsibility for the fault, allowing <code className="text-white">.handle()</code> to run.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold block mb-1">{"handle(ctx) -> FaultResult"}</code>

            <p className="text-gray-400 mt-1">
              Executes the resolution logic. Must return <code className="text-white">Resolved(response)</code>, <code className="text-white">Transformed(new_fault)</code>, or <code className="text-white">Escalate()</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Writing a Custom Handler</h2>
        <CodeBlock language="python" filename="custom_handler.py" highlightLines={[9, 13, 21, 24]}>{`from aquilia.faults import FaultHandler, Resolved, Escalate, FaultResult
from aquilia.response import Response

class DatabaseConnectionFaultHandler(FaultHandler):
    """Custom handler for database outage faults."""

    def can_handle(self, ctx) -> bool:
        # Match only DB-related faults with severe status
        return ctx.fault.domain.value == "model" and ctx.fault.code.startswith("DB_")

    async def handle(self, ctx) -> FaultResult:
        # Log active request variables
        print(f"Database error on: {ctx.request_id} - {ctx.fault.message}")
        
        if ctx.fault.retryable:
            # Let it escalate to a retry middleware
            return Escalate()
            
        # Return a structured JSON response
        return Resolved(
            Response(
                {"error": "Database temporarily unavailable", "code": "DB_OUTAGE"},
                status=503
            )
        )`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/faults/engine" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> FaultEngine
        </Link>
        <Link to="/docs/faults/domains" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Fault Domains <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}