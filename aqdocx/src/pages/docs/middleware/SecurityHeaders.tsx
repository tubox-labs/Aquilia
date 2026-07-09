import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'


export function MiddlewareSecurityHeaders() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / SECURITY</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Security Middleware Suite
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia incorporates a production-grade suite of security middlewares covering Content-Security-Policy (CSP), Cross-Site Request Forgery (CSRF), HTTP Strict Transport Security (HSTS), and Helmet-style security headers.
        </p>
      </div>

      {/* CSPMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>CSPMiddleware &amp; CSPPolicy</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Content-Security-Policy is built using a fluent builder class, <code className="text-aquilia-500">CSPPolicy</code>, which is then registered via <code className="text-aquilia-500">CSPMiddleware</code>. It generates secure cryptographically random nonces (<code className="text-aquilia-500">secrets.token_urlsafe(16)</code>) per-request and injects them to <code className="text-aquilia-400">request.state["csp_nonce"]</code>.
        </p>

        <CodeBlock language="python" filename="csp_setup.py" highlightLines={[6, 7, 8, 9, 13]}>{`from aquilia.middleware_ext import CSPMiddleware, CSPPolicy

# 1. Build the policy fluently
policy = (
    CSPPolicy()
    .default_src("'self'")
    .script_src("'self'", "'nonce-{nonce}'", "https://cdn.jsdelivr.net")
    .style_src("'self'", "'unsafe-inline'")
    .img_src("'self'", "data:", "https:")
)

# 2. Wire into middleware
server.middleware(CSPMiddleware(policy=policy, report_only=False))`}</CodeBlock>
      </section>

      {/* CSRFMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>CSRFMiddleware</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Defends against Cross-Site Request Forgery. It implements the primary <strong>Synchronizer Token Pattern</strong> using server-side sessions, falling back to a signed <strong>Double Submit Cookie</strong> fallback when sessions are disabled. It enforces constant-time string comparisons (<code className="text-aquilia-500">secrets.compare_digest</code>) to block timing attack vectors.
        </p>

        <CodeBlock language="python" filename="csrf_setup.py" highlightLines={[6, 7, 10]}>{`from aquilia.middleware_ext import CSRFMiddleware

server.middleware(
    CSRFMiddleware(
        secret_key="my-secure-hmac-key", # Required for cookie fallback integrity
        cookie_name="_csrf_cookie",
        header_name="X-CSRF-Token",
        cookie_secure=True,
        cookie_httponly=False,          # Set False to let JS read it for AJAX
        exempt_paths=["/api/v1/webhooks"] # Exempt endpoints like Stripe webhook paths
    )
)`}</CodeBlock>
      </section>

      {/* SecurityHeadersMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>SecurityHeadersMiddleware &amp; HSTS</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          A Helmet-style catch-all security header middleware. It applies standard production defaults to outgoing responses:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-2 font-mono text-xs">
          <div>- <code className="text-white">X-Content-Type-Options: nosniff</code> (prevents MIME sniffing)</div>
          <div>- <code className="text-white">X-Frame-Options: DENY</code> (defends against Clickjacking)</div>
          <div>- <code className="text-white">X-XSS-Protection: 1; mode=block</code> (legacy XSS filtering)</div>
          <div>- <code className="text-white">Strict-Transport-Security: max-age=31536000</code> (forces HTTPS connections)</div>
        </div>

        <CodeBlock language="python" filename="security_headers.py" highlightLines={[4]}>{`from aquilia.middleware_ext import SecurityHeadersMiddleware

server.middleware(
    SecurityHeadersMiddleware(
        x_content_type_options="nosniff",
        x_frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin"
    )
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/rate-limit" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Rate Limiting
        </Link>
        <Link to="/docs/middleware/request-scope" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Request Scope <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}