import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareLogging() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / ACCESS LOGGING</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          LoggingMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">LoggingMiddleware</code> handles high-performance HTTP access logging. It supports multiple layout formatters, timing tracking with microsecond precision, and slow request alerting.
        </p>
      </div>

      {/* Constructor Signature */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The middleware constructor accepts several parameters to customize how access logs are gathered:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">logger_name: str = "aquilia.access"</code> — The logger instance name used to dispatch output.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">format: str = "dev"</code> — The log line template. Select from <code className="text-aquilia-300">"dev"</code> (color-coded terminal), <code className="text-aquilia-300">"combined"</code> (standard Nginx/Apache Combined Log Format), or <code className="text-aquilia-300">"structured"</code> (JSON output for observability aggregators).
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">slow_threshold_ms: float = 1000.0</code> — Warns (at Warning log level) if a request duration exceeds this value.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">skip_paths: set[str] | None = None</code> — Paths excluded from logging (defaults to <code className="text-aquilia-300">{"{\"/health\", \"/healthz\", \"/ready\", \"/favicon.ico\"}"}</code>).

          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">log_request_body: bool = False</code> — Captures and logs request body byte length.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">include_headers: list[str] | None = None</code> — List of HTTP request headers to extract and append to the log line extras.
          </div>
        </div>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="logging_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import LoggingMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = (
    Workspace("myapp")
    .middleware(
        MiddlewareChain()
        .use(
            "aquilia.middleware_ext.logging:LoggingMiddleware",
            priority=20,
            format="structured",          # JSON outputs
            slow_threshold_ms=500.0,       # Alert on delays > 500ms
            include_headers=["User-Agent", "Referer"]
        )
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
