import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SSEResourceManagement() {
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
          <span>SSE SYSTEM / RESOURCE MANAGEMENT</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Resource &amp; Disconnect Management
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Prevent connection and file handle leaks in long-lived SSE streams. Manage client disconnects and clean up resources safely.
        </p>
      </div>

      {/* Connection Cancellation */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Client Disconnect Mechanics</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            Because Server-Sent Events can stream indefinitely, clients frequently close their connections abruptly (e.g. by closing the browser tab, navigating away, or experiencing a network dropout).
          </p>
          <p>
            When a connection is severed, the ASGI server fails to write the next byte chunk and terminates the handler task. In Python's <code className="text-white">asyncio</code>, this triggers a task cancellation, raising an <code className="text-white">asyncio.CancelledError</code> inside the active generator function.
          </p>
          <p>
            Failure to handle this cancellation will cause leased databases, connection pools, or file descriptors to remain open, leading to leakages.
          </p>
        </div>
      </section>

      {/* Safe Resource Cleanup Scenarios */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Safe Generator Pattern</h2>
        <p className={`mb-6 font-light leading-relaxed ${textMuted}`}>
          To guarantee cleanup operations execute, always wrap your streaming loop inside a <code className="text-white">try...finally</code> statement. When the task is cancelled, control flows automatically into the <code className="text-white">finally</code> block:
        </p>

        <CodeBlock language="python" filename="controllers/safe_stream.py" highlightLines={[12, 16, 21, 23]}>{`import asyncio
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse, SSEEvent

class SafeController(Controller):
    @GET("/sse/safe-metrics")
    async def get_metrics(self, ctx: RequestCtx):
        return SSEResponse(self._stream_safely())

    async def _stream_safely(self):
        # 1. Acquire connection or lock
        db_connection = await self.db_pool.acquire()
        try:
            while True:
                data = await db_connection.fetch_row("SELECT * FROM metrics ORDER BY id DESC LIMIT 1")
                yield SSEEvent(data=str(data))
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            # Caught automatically when browser closes connection
            print("Stream cancelled: Client disconnected.")
            raise
        finally:
            # 2. Guarantee releasing connection back to pool
            await self.db_pool.release(db_connection)
            print("Successfully released DB connection.")`}</CodeBlock>
      </section>

      {/* Timeout Safeguards */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Configuring Stream Timeouts</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            Allowing streams to run indefinitely is a security risk and can lead to resources drying up. You can configure a maximum lifetime for your streams by passing the <code className="text-white">timeout</code> parameter to <code className="text-white">SSEResponse</code> (measured in seconds).
          </p>
          <p>
            Once the timeout is reached, the response completes, and the client receives a finished connection. The browser will then trigger automatic reconnection according to spec.
          </p>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/sse/openai" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> OpenAI Streaming
        </Link>
        <Link to="/docs/subsystem/built-in" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Built-in Effects <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
