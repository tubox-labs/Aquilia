import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight, AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function SocketMiddlewareOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / SOCKET MIDDLEWARE</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Socket Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The WebSocket middleware subsystem (<DocTerm id="sockets.SocketMiddlewareStack">SocketMiddlewareStack</DocTerm>) operates completely independently from the HTTP stack. It intercepts connection lifecycle events and incoming socket messages using a distinct set of primitives designed specifically for persistent connections.
        </p>
      </div>

      <div className={`mb-12 p-5 rounded-lg border flex gap-4 items-start ${isDark ? 'border-amber-500/20 bg-amber-500/5 text-amber-200' : 'border-amber-600/30 bg-amber-50 text-amber-800'}`}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold mb-1">Security Parity Warning</h4>
          <p className="text-sm">
            HTTP middleware <strong>DOES NOT</strong> apply to WebSocket messages. While the initial upgrade request passes through your HTTP middleware stack (so you can use HTTP sessions and auth for the handshake), once the connection is established, all subsequent frames bypass the HTTP router. You must explicitly configure SocketMiddleware for rate limiting, validation, and authorization of incoming frames.
          </p>
        </div>
      </div>

      {/* Base Class & Hooks */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>SocketMiddleware Hooks</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code>SocketMiddleware</code> base class (from <code>aquilia.sockets.middleware</code>) defines three distinct hooks that you can override to intercept different stages of a socket connection:
        </p>

        <div className="space-y-4 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def on_connect(self, socket, ctx, next_handler)</code>
            <p className="text-gray-400 mt-1">Intercepts the initial WebSocket connection post-upgrade. Throwing an exception here terminates the connection immediately. Access connection context via <code className="text-aquilia-400">SocketCtx</code>.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def on_message(self, message, ctx, next_handler)</code>
            <p className="text-gray-400 mt-1">Intercepts every incoming message frame. Useful for validation, rate limiting, and decoding.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def on_disconnect(self, socket, ctx, next_handler)</code>
            <p className="text-gray-400 mt-1">Runs when the connection is closed, cleanly or forcefully. Useful for resource cleanup.</p>
          </div>
        </div>
      </section>

      {/* Configuration & Chain */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Configure your socket middleware globally in <code>workspace.py</code> using the fluent <code>SocketMiddlewareChain</code> builder.
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 7]}>{`from aquilia import Workspace
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = Workspace(
    # Register global socket middleware
    socket_middleware=SocketMiddlewareChain.production()
        .use("my_app.sockets.CustomAuthMiddleware", priority=15)
)`}</CodeBlock>

        <div className="mt-8 space-y-4">
          <h3 className="font-mono text-sm uppercase text-white mb-2">Built-in Presets</h3>
          <div className="border-l-2 border-white/10 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">.minimal()</code>
            <p className="text-sm text-gray-400 mt-1">Includes only the critical framework plumbing (SocketFaultMiddleware).</p>
          </div>
          <div className="border-l-2 border-white/10 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">.defaults()</code>
            <p className="text-sm text-gray-400 mt-1">Adds SocketMetricsMiddleware and MessageValidationMiddleware.</p>
          </div>
          <div className="border-l-2 border-white/10 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">.production()</code>
            <p className="text-sm text-gray-400 mt-1">Adds SocketRateLimitMiddleware and standard security guards.</p>
          </div>
        </div>
      </section>

      {/* Scope System & Priority Bands */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Scope & Priority Bands</h2>
        
        <h3 className="text-lg font-semibold mb-3 mt-8">Scopes</h3>
        <p className={`mb-4 leading-relaxed text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Socket middlewares evaluate their target based on a hierarchical scope matching system: <code className="text-aquilia-400">global</code> &lt; <code className="text-aquilia-400">namespace:*</code> &lt; <code className="text-aquilia-400">event:*</code>. Event-specific middleware runs closest to the handler.
        </p>

        <h3 className="text-lg font-semibold mb-3 mt-8">Priority Bands</h3>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Band</th>
                <th className="py-3 px-4">Range</th>
                <th className="py-3 px-4">Built-ins</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans text-gray-400">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs">FRAMEWORK_PLUMBING_BAND</td>
                <td className="py-3.5 px-4 font-mono text-xs">0-9</td>
                <td className="py-3.5 px-4 text-xs">SocketFaultMiddleware (2)<br/>SocketMetricsMiddleware (6)</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs">FRAMEWORK_SECURITY_BAND</td>
                <td className="py-3.5 px-4 font-mono text-xs">10-19</td>
                <td className="py-3.5 px-4 text-xs">MessageValidationMiddleware (10)<br/>SocketRateLimitMiddleware (12)<br/>SocketAuthMiddleware<br/>SocketPermissionMiddleware</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-xs">APPLICATION_BAND</td>
                <td className="py-3.5 px-4 font-mono text-xs">50-99</td>
                <td className="py-3.5 px-4 text-xs">SocketLoggingMiddleware<br/>User Middlewares</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/built-in" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Built-in Middleware
        </Link>
        <Link to="/docs/sockets" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          WebSockets <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
