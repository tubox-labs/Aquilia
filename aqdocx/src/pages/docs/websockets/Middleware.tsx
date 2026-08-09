import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Layers, AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function WebSocketMiddleware() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          WebSockets / Middleware
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Socket Middleware</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The WebSocket middleware subsystem is a robust, priority-based pipeline for intercepting and processing connection lifecycles and incoming messages. It is designed specifically for long-lived socket connections.
        </p>
      </div>

      {/* Security Parity Warning */}
      <div className={`mb-12 p-6 rounded-xl border ${isDark ? 'bg-amber-950/20 border-amber-900/50' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-3 mb-3">
          <AlertTriangle className={`w-5 h-5 ${isDark ? 'text-amber-500' : 'text-amber-600'}`} />
          <h3 className={`font-bold ${isDark ? 'text-amber-500' : 'text-amber-700'}`}>Security Parity Warning</h3>
        </div>
        <p className={`text-sm ${isDark ? 'text-amber-200/70' : 'text-amber-900/80'}`}>
          The WebSocket middleware system is <strong>completely separate</strong> from <code className="font-mono bg-black/10 px-1 py-0.5 rounded text-xs">aquilia.middleware</code>. HTTP middleware configured through <code className="font-mono bg-black/10 px-1 py-0.5 rounded text-xs">Workspace.security(...)</code> (such as CORS, rate limiting, CSRF, and HTTP auth) does <strong>NOT</strong> apply to WebSocket messages. A socket surface is protected only by middleware registered on its own <code className="font-mono bg-black/10 px-1 py-0.5 rounded text-xs">SocketMiddlewareChain</code>.
        </p>
      </div>

      {/* Base Class & Hooks */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          The SocketMiddleware Base Class
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Middleware in AquilaSockets is created by inheriting from <DocTerm id="sockets.middleware.SocketMiddleware">SocketMiddleware</DocTerm> and overriding any of three available hooks. You only need to override the hooks you plan to use—the stack automatically skips middleware for chains where the hook is not overridden. All hooks must be <code className="text-aquilia-400">async def</code>.
        </p>
        <CodeBlock language="python" filename="middleware/presence.py">{`from aquilia.sockets.middleware import SocketMiddleware
from aquilia.sockets import SocketCtx, MessageEnvelope

class PresenceMiddleware(SocketMiddleware):
    async def on_connect(self, ctx: SocketCtx, next):
        # Called when a connection is established
        ctx.state["connected_at"] = self.current_time()
        await self.redis.sadd("active_users", ctx.connection.id)
        return await next(ctx)

    async def on_message(self, envelope: MessageEnvelope, ctx: SocketCtx, next):
        # Called on every incoming message
        ctx.state["last_active"] = self.current_time()
        return await next(envelope, ctx)

    async def on_disconnect(self, ctx: SocketCtx, reason: str):
        # Called when the connection closes
        await self.redis.srem("active_users", ctx.connection.id)`}</CodeBlock>
        
        <div className="mt-6">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>SocketCtx (Context Object)</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            The <code className="text-aquilia-400">SocketCtx</code> provides access to the connection and a <code className="text-aquilia-400">state: dict</code> for storing per-connection mutable state across hooks.
          </p>
        </div>
      </section>

      {/* Middleware Stack & Priorities */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Stack & Registration
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The <DocTerm id="sockets.middleware.SocketMiddlewareStack">SocketMiddlewareStack</DocTerm> orchestrates execution. A single registration feeds into three distinct execution chains (connect, message, disconnect). The stack sorts middleware by scope rank and priority (ascending order).
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scope Hierarchy</h3>
        <p className={`text-sm mb-4 ${textMuted}`}>
          Scopes evaluate in the following order: <code className="text-aquilia-400">global</code> {'<'} <code className="text-aquilia-400">namespace:&lt;path&gt;</code> {'<'} <code className="text-aquilia-400">event:&lt;name&gt;</code>
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Priority Bands</h3>
        <div className={`overflow-hidden rounded-lg border ${borderMuted} mb-8`}>
          <table className="w-full text-sm text-left">
            <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-300' : 'bg-gray-50 text-gray-700'}`}>
              <tr>
                <th className="px-6 py-3">Band</th>
                <th className="px-6 py-3">Range</th>
                <th className="px-6 py-3">Purpose</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${borderMuted} ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              <tr><td className="px-6 py-4 font-mono">Framework Plumbing</td><td className="px-6 py-4">0-9</td><td className="px-6 py-4">Core mechanisms like fault handling and metrics</td></tr>
              <tr><td className="px-6 py-4 font-mono">Framework Security</td><td className="px-6 py-4">10-19</td><td className="px-6 py-4">Validation, rate limiting, and auth</td></tr>
              <tr><td className="px-6 py-4 font-mono">Reserved</td><td className="px-6 py-4">20-49</td><td className="px-6 py-4">Reserved for future framework extensions</td></tr>
              <tr><td className="px-6 py-4 font-mono">Application</td><td className="px-6 py-4">50-99</td><td className="px-6 py-4">Your custom middleware (default: 50)</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* SocketMiddlewareChain Builder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SocketMiddlewareChain Builder
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          You can configure the middleware pipeline fluently using <DocTerm id="sockets.middleware.SocketMiddlewareChain">SocketMiddlewareChain</DocTerm>. The framework provides several presets to get started quickly:
        </p>
        
        <CodeBlock language="python">{`from aquilia.sockets.middleware import SocketMiddlewareChain

# 1. Minimal (Fault handling only)
minimal_chain = SocketMiddlewareChain.minimal()

# 2. Defaults (Fault handling + Message Validation)
default_chain = SocketMiddlewareChain.defaults()

# 3. Production (Fault + Metrics + Validation + Rate Limiting)
prod_chain = SocketMiddlewareChain.production()

# Equivalent manual configuration for the Production preset:
chain = (
    SocketMiddlewareChain.chain()
    .use("aquilia.sockets.middleware.builtin.SocketFaultMiddleware", priority=2)
    .use("aquilia.sockets.middleware.builtin.SocketMetricsMiddleware", priority=6)
    .use("aquilia.sockets.middleware.builtin.MessageValidationMiddleware", priority=10, max_payload_size=32768)
    .use("aquilia.sockets.middleware.builtin.SocketRateLimitMiddleware", priority=12, messages_per_second=10, burst=20)
)`}</CodeBlock>
      </section>

      {/* Built-in Middleware List */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Socket Middleware
        </h2>
        <div className="space-y-6">
          {[
            { name: 'SocketFaultMiddleware', prio: 2, desc: 'Global exception handler for the socket chain.' },
            { name: 'SocketMetricsMiddleware', prio: 6, desc: 'Tracks connection and message counters. Provides a snapshot() method.' },
            { name: 'MessageValidationMiddleware', prio: 10, desc: 'Enforces payload size limits and basic structure checks.' },
            { name: 'SocketRateLimitMiddleware', prio: 12, desc: 'Token bucket rate limiting (key_by="client"). Releases bucket on disconnect.' },
            { name: 'SocketAuthMiddleware', prio: '10-19', desc: 'Periodically re-checks auth on long-lived connections. Stores timestamp on ctx.state.' },
            { name: 'SocketPermissionMiddleware', prio: '10-19', desc: 'Enforces role/permission requirements.' },
            { name: 'SocketLoggingMiddleware', prio: 'any', desc: 'Structured connection and message logging.' }
          ].map((item, i) => (
            <div key={i} className={`p-4 rounded-lg border ${borderMuted} ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
              <div className="flex items-center gap-3 mb-2">
                <code className={`font-mono font-bold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.name}</code>
                <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? 'bg-gray-800 text-gray-400' : 'bg-gray-200 text-gray-600'}`}>Priority: {item.prio}</span>
              </div>
              <p className={`text-sm ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workspace Registration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Workspace Configuration
        </h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          Apply the middleware chain globally to your WebSocket system in your <code className="text-aquilia-400">workspace.py</code>:
        </p>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia.workspace import Workspace
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = (
    Workspace("myapp")
    .socket_middleware(
        SocketMiddlewareChain.production()
    )
)`}</CodeBlock>
      </section>

      {/* Migrations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Removed Names & Migration Guide
        </h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          If you are upgrading to v1.4.0b2, note the following renames to distinguish from HTTP equivalents (importing old names will raise an ImportError):
        </p>
        <ul className={`list-disc list-inside space-y-2 text-sm ${textMuted} ml-4`}>
          <li><code className="text-aquilia-400">MiddlewareChain</code> → <code className="text-aquilia-400">SocketMiddlewareStack</code> or <code className="text-aquilia-400">SocketMiddlewareChain</code></li>
          <li><code className="text-aquilia-400">LoggingMiddleware</code> → <code className="text-aquilia-400">SocketLoggingMiddleware</code></li>
          <li><code className="text-aquilia-400">MetricsMiddleware</code> → <code className="text-aquilia-400">SocketMetricsMiddleware</code></li>
        </ul>
        <p className={`text-sm mt-4 ${textMuted}`}>
          <code className="text-aquilia-400">RateLimitMiddleware</code> is preserved as an alias for <code className="text-aquilia-400">SocketRateLimitMiddleware</code> for backward compatibility.
        </p>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/websockets/runtime" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Runtime
        </Link>
        <Link to="/docs/websockets/adapters" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Adapters <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'WebSocket Runtime Details', link: '/docs/websockets/runtime' },
          { text: 'Scaling Adapters', link: '/docs/websockets/adapters' },
        ]}
      />
    </div>
  )
}
