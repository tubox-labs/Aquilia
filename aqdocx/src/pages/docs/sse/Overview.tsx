import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SSEOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Zap className="w-4 h-4" />
          <span>SSE SYSTEM / OVERVIEW</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Server-Sent Events (SSE)
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Unidirectional real-time server push for Aquilia applications. Learn how the SSE subsystem keeps connection channels open to stream updates dynamically over standard HTTP.
        </p>
      </div>

      {/* SSE Concept */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">What is SSE?</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            Server-Sent Events (SSE) is a web technology enabling servers to push real-time event updates to clients over a single long-lived TCP connection. Defined as part of the HTML5 standard, it is natively supported by all modern browsers via the <code className="text-white">EventSource</code> API.
          </p>
          <p>
            Unlike WebSockets, which are bi-directional and require custom handshake protocols, SSE operates over standard HTTP, making it simpler to deploy, compatible with HTTP/2 multiplexing, and highly resilient through automatic client-side reconnection.
          </p>
        </div>
      </section>

      {/* How it works in Aquilia */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Aquilia SSE Architecture</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            In Aquilia, SSE streams are managed by <DocTerm id="sse.SSEResponse">SSEResponse</DocTerm>. When returned from a controller method, it binds an asynchronous event iterator directly into the ASGI server write pipeline. The server streams bytes chunk-by-chunk, flushing buffers immediately after each event is written.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/sse_basic.py" highlightLines={[6, 10, 14]}>{`import asyncio
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse, SSEEvent

class LiveController(Controller):
    @GET("/sse/stream")
    async def stream_live(self, ctx: RequestCtx):
        # Wraps an async generator yielding SSEEvent objects
        return SSEResponse(self._event_source())

    async def _event_source(self):
        for i in range(5):
            yield SSEEvent(data=f"message {i}")
            await asyncio.sleep(1.0)`}</CodeBlock>
      </section>

      {/* Under The Hood Details */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Protocol Transport Headers</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            To prevent proxies and browsers from buffering or caching events, the <DocTerm id="sse.SSEResponse">SSEResponse</DocTerm> engine configures the following transport headers automatically:
          </p>
          <div className="border-l-2 border-aquilia-500/20 pl-6 space-y-4 py-1">
            <p>
              <strong className="font-semibold text-aquilia-500">Content-Type:</strong> set to <code className="text-white">text/event-stream; charset=utf-8</code>.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">Cache-Control:</strong> set to <code className="text-white">no-cache, no-transform</code> to bypass intermediate proxy memory caches.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">Connection:</strong> set to <code className="text-white">keep-alive</code> to instruct ASGI servers to preserve the request connection channel.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">X-Accel-Buffering:</strong> set to <code className="text-white">no</code>. This tells Nginx to disable buffering and stream output immediately.
            </p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/subsystem/custom" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Custom Effects
        </Link>
        <Link to="/docs/sse/standard" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Standard Events <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
