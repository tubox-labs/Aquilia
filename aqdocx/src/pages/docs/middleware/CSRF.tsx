import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareCSRF() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / CSRF PROTECTION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CSRFMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">CSRFMiddleware</code> blocks Cross-Site Request Forgery attacks. It uses the Synchronizer Token Pattern backed by server-side sessions, falling back to a signed Double Submit Cookie when sessions are unavailable.
        </p>
      </div>

      {/* Constructor Parameters */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The middleware is highly configurable to suit standard SPA or MVC page rendering layouts:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">secret_key: str | None = None</code> — HMAC key for double-submit cookie validation. Generates an ephemeral key per-process if omitted.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">header_name: str = "X-CSRF-Token"</code> — The request header name containing the validation token.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">field_name: str = "_csrf_token"</code> — The form field name containing the validation token.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">exempt_paths: list[str] | None = None</code> — List of URL prefixes exempted from CSRF validation (e.g. webhooks).
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">exempt_content_types: list[str] | None = None</code> — Exempts requests carrying matching content types (e.g. <code className="text-aquilia-300">"application/json"</code>).
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">trust_ajax: bool = False</code> — Bypasses validation if <code className="text-white">X-Requested-With: XMLHttpRequest</code> is present, trusting the browser's same-origin boundary.
          </div>
        </div>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="csrf_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import CSRFMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = Workspace("myapp").middleware(
    MiddlewareChain().use(
        "aquilia.middleware_ext.security:CSRFMiddleware",
        priority=15,
        secret_key="production-only-secure-key-phrase",
        exempt_paths=["/stripe/webhooks"],
        trust_ajax=True
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
