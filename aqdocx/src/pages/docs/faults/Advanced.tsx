import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, AlertTriangle } from 'lucide-react'

import { NextSteps } from '../../../components/NextSteps'

export function FaultsAdvanced() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>FAULTS / ADVANCED TOPICS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Custom Domains &amp; Debugging
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Configure custom domains to group application-specific errors, and customize the HTML debug pages shown during local development.
        </p>
      </div>

      {/* Custom Fault Domains */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Custom Domains</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          By default, Aquilia includes domains like <code className="text-aquilia-500">FaultDomain.MODEL</code> or <code className="text-aquilia-500">FaultDomain.SECURITY</code>. To define your own application-specific domain, use the <code className="text-aquilia-500">FaultDomain.custom(name, description)</code> factory method:
        </p>

        <CodeBlock language="python" filename="custom_domain.py" highlightLines={[4, 7]}>{`from aquilia.faults import FaultDomain, Fault

# 1. Instantiate custom domain
BILLING_DOMAIN = FaultDomain.custom("billing", "Errors originating from the Stripe payment flows")

# 2. Use the domain in a Fault instantiation
raise Fault(
    code="PAYMENT_FAILED",
    message="Credit card transaction was declined by Stripe",
    domain=BILLING_DOMAIN,
    public=True,
)`}</CodeBlock>
      </section>

      {/* Debug Exception Page */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Development Debug Pages</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When running in local development mode (<code className="text-aquilia-500">debug=True</code>), unhandled Exceptions or Faults originating from HTML clients (<code className="text-aquilia-500">Accept: text/html</code>) render beautiful, interactive diagnostics:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-3 font-sans">
          <div>- <strong>Source Code View</strong>: Shows syntax-highlighted source code slices surrounding the line that raised the error.</div>
          <div>- <strong>Local Variables</strong>: Dumps variable values for every traceback stack frame.</div>
          <div>- <strong>Request Inspection</strong>: Displays raw ASGI scopes, headers, active cookies, and body sizes.</div>
        </div>

        <CodeBlock language="python" filename="debug_setup.py" highlightLines={[6]}>{`from aquilia.debug import DebugPageRenderer

# The ExceptionMiddleware instantiates the renderer automatically:
renderer = DebugPageRenderer(
    show_locals=True,      # Dump local variables in stack frames
    context_lines=7        # Number of surrounding lines of source code to display
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/faults/domains" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Fault Domains
        </Link>
        <Link to="/docs/cache" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Cache <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}