import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { AlertTriangle, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function FaultsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>ADVANCED / FAULTS SYSTEM</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Structured Faults
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          In Aquilia, errors are first-class structured values called Faults. Inheriting from Python's base <code className="text-aquilia-500">Exception</code> class, every <DocTerm id="faults.Fault">Fault</DocTerm> carries stable identifiers, classification domains, severity ratings, and recovery strategies.
        </p>
      </div>

      {/* Structured exceptions vs raw */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Why Structured Faults?</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Raw Python exceptions lack consistent structures, making it difficult for downstream HTTP middlewares or background workers to parse error details safely. A <DocTerm id="faults.Fault">Fault</DocTerm> encapsulates these properties:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-1">
            <span className="font-mono text-xs text-white font-bold uppercase tracking-wider">Classification Domains</span>
            <p className="text-gray-400 mt-1 leading-relaxed">
              Organizes errors by subsystem (e.g. CONFIG, DI, MODEL, CACHE), defining default severity and retry rules automatically.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-1">
            <span className="font-mono text-xs text-white font-bold uppercase tracking-wider">Public Exposure Controls</span>
            <p className="text-gray-400 mt-1 leading-relaxed">
              The <code className="text-aquilia-400">public</code> boolean flag controls whether error messages can be returned directly to JSON clients or must be masked as 500 errors.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Creating Faults</h2>
        <CodeBlock language="python" filename="fault_usage.py" highlightLines={[6, 9, 13]}>{`from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy

# Instantiating a structured fault
raise Fault(
    code="USER_NOT_FOUND",
    message="Requested user ID does not exist",
    domain=FaultDomain.MODEL,
    severity=Severity.ERROR,
    public=True,
    retryable=False,
    user_id=123 # Arbitrary metadata fields are merged automatically
)`}</CodeBlock>
      </section>

      {/* Transform chain operator */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Preserving Causality: Transform Chain</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Faults support the right shift operator <code className="text-aquilia-500">&gt;&gt;</code>. This allows handlers to catch lower-level errors (like database exceptions) and transform them into higher-level API faults while preserving causality:
        </p>

        <CodeBlock language="python" filename="fault_chain.py" highlightLines={[6]}>{`try:
    await db.execute("INSERT ...")
except DatabaseError as err:
    # Transform lower-level database error to public API fault
    # Preserves the cause and updates the '_transform_chain' key in metadata
    raise DatabaseFault(code="DB_FAIL", message=str(err)) >> ApiFault("USER_CREATE_FAILED")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <span />
        <Link to="/docs/faults/taxonomy" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Fault Taxonomy <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}