import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareCSP() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / CONTENT SECURITY POLICY</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CSPMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">CSPMiddleware</code> restricts resource loading, defending applications against Cross-Site Scripting (XSS) and data injection attacks.
        </p>
      </div>

      {/* Fluent CSPPolicy Builder */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Fluent CSPPolicy Builder</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Rather than building manual policy strings, Aquilia provides the fluent <code className="text-aquilia-500">CSPPolicy</code> class to configure resource loading policies:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">.default_src(*sources)</code> — Default fallback sources for most resource types.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">.script_src(*sources)</code> — Specifies valid sources for JavaScript scripts.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">.style_src(*sources)</code> — Specifies valid sources for style sheets.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">.img_src(*sources)</code> — Specifies valid sources for images.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">.font_src(*sources)</code> — Specifies valid sources for fonts.
          </div>
        </div>
      </section>

      {/* Nonce Generation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Request Nonce Generation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When <code className="text-aquilia-500">nonce=True</code> is configured, the middleware automatically generates a cryptographically secure, per-request nonce (via <code className="text-aquilia-400">secrets.token_urlsafe(16)</code>).
        </p>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The nonce is injected into the policy string wherever <code className="text-aquilia-400">'nonce-{"{nonce}"}'</code> is declared, and is made accessible in templates via the request context:
        </p>
        <CodeBlock language="html" filename="index.html" highlightLines={[2]}>{`<!-- Inject nonce dynamically in templates -->
<script nonce="{{ request.state.csp_nonce }}">
    console.log("Safe script execution");
</script>`}</CodeBlock>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="csp_setup.py" highlightLines={[6, 14, 15]}>{`from aquilia.middleware_ext import CSPMiddleware, CSPPolicy
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

# Build policy fluently
policy = (
    CSPPolicy()
    .default_src("'self'")
    .script_src("'self'", "'nonce-{nonce}'")
    .style_src("'self'", "'unsafe-inline'")
)

workspace = Workspace("myapp").middleware(
    MiddlewareChain().use(
        "aquilia.middleware_ext.security:CSPMiddleware",
        priority=12,
        policy=policy,
        nonce=True
    )
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
