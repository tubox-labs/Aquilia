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

        {/* Premium SVG Flow-Based Architecture Diagram */}
        <div className="w-full flex justify-center py-6 bg-transparent">
          <svg viewBox="0 0 900 340" className="w-full h-auto drop-shadow-2xl font-mono select-none">
            <defs>
              <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
              </linearGradient>
              <radialGradient id="glowGreen" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
              </radialGradient>
              <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Glowing Halos Behind Nodes */}
            <circle cx="80" cy="170" r="50" fill="url(#glowGreen)" />
            <circle cx="240" cy="110" r="50" fill="url(#glowGreen)" />
            <circle cx="400" cy="90" r="50" fill="url(#glowBlue)" />
            <circle cx="560" cy="230" r="50" fill="url(#glowBlue)" />
            <circle cx="720" cy="190" r="50" fill="url(#glowPurple)" />
            <circle cx="840" cy="170" r="50" fill="url(#glowGreen)" />

            {/* Connecting Wave Lines (Bundle of Light Fibers) */}
            <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="url(#waveGrad)" strokeWidth="4.5" strokeLinecap="round" />
            <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 8" strokeLinecap="round" />

            {/* Node 1: Origin */}
            <g transform="translate(80, 170)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">1. ORIGIN</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Exception/Fault raised</text>
            </g>

            {/* Node 2: Annotation */}
            <g transform="translate(240, 110)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">2. ANNOTATION</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">FaultContext wrapped</text>
            </g>

            {/* Node 3: Emission */}
            <g transform="translate(400, 90)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">3. EMISSION</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Logs &amp; listener dispatch</text>
            </g>

            {/* Node 4: Propagation */}
            <g transform="translate(560, 230)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="-24" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">4. PROPAGATION</text>
              <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="#71717a">Scope handler routing</text>
            </g>

            {/* Node 5: Resolution */}
            <g transform="translate(720, 190)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#a855f7" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#a855f7" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">5. RESOLUTION</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Resolved/Transformed result</text>
            </g>

            {/* Node 6: Response */}
            <g transform="translate(840, 170)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">6. RESPONSE</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Safe HTTP serialization</text>
            </g>
          </svg>
        </div>

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