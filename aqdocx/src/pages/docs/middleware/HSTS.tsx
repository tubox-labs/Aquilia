import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareHSTS() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / HSTS SECURITY</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          HSTSMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">HSTSMiddleware</code> enforces HTTPS-only communication by appending the HTTP Strict Transport Security header to responses.
        </p>
      </div>

      {/* Constructor Parameters */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The middleware constructor defines HSTS parameters standard across modern web security audits:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">max_age: int = 31536000</code> — The number of seconds browsers should remember this domain must only be accessed via HTTPS (defaults to 1 year).
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">include_subdomains: bool = True</code> — Applies the strict HTTPS directive recursively to all subdomains.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">preload: bool = False</code> — Opts the domain into major browser HSTS preload list registries (e.g. hstspreload.org).
          </div>
        </div>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="hsts_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import HSTSMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = Workspace("myapp").middleware(
    MiddlewareChain().use(
        "aquilia.middleware_ext.security:HSTSMiddleware",
        priority=10,
        max_age=63072000,             # 2 years
        include_subdomains=True,
        preload=True
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
