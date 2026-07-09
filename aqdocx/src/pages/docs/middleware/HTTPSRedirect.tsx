import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareHTTPSRedirect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / HTTPS REDIRECT</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          HTTPSRedirectMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">HTTPSRedirectMiddleware</code> intercepts incoming unsecured HTTP requests and redirects them to their equivalent HTTPS addresses.
        </p>
      </div>

      {/* Constructor Parameters */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Configure redirect responses and host exemptions to facilitate local development and health check pings:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">redirect_status: int = 301</code> — HTTP redirect status code (e.g. <code className="text-aquilia-300">301 Moved Permanently</code> or <code className="text-aquilia-300">307 Temporary Redirect</code>).
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">exclude_paths: list[str] | None = None</code> — Paths excluded from redirections. Use this to allow unsecured health checks (e.g. <code className="text-aquilia-300">["/healthz"]</code>).
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">exclude_hosts: list[str] | None = None</code> — Hostnames exempt from redirections (defaults to <code className="text-aquilia-300">["localhost", "127.0.0.1", "0.0.0.0"]</code>).
          </div>
        </div>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="https_redirect_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import HTTPSRedirectMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = Workspace("myapp").middleware(
    MiddlewareChain().use(
        "aquilia.middleware_ext.security:HTTPSRedirectMiddleware",
        priority=8,
        redirect_status=307,
        exclude_paths=["/ping"]
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
