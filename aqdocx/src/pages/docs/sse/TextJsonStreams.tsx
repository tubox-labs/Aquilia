import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SSETextJsonStreams() {
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
          <span>SSE SYSTEM / TEXT &amp; JSON STREAMS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Text &amp; JSON Streaming
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Stream tokens or serializable payloads without wrapping elements manually. Leverage the SSEResponse.text() and SSEResponse.json() constructor overloads.
        </p>
      </div>

      {/* SSEResponse.text overload */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">SSEResponse.text()</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            When streaming simple character files, LLM completion tokens, or raw console logs, wrapping strings inside <DocTerm id="sse.SSEEvent">SSEEvent</DocTerm> objects is verbose.
          </p>
          <p>
            The <code className="text-white">SSEResponse.text()</code> constructor accepts an <code className="text-white">AsyncGenerator[str, None]</code>. It intercepts each string output from the generator, wraps it in a standard event payload, and writes it directly to the response socket.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/text_stream.py" highlightLines={[6, 9, 13]}>{`import asyncio
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse

class LogStreamController(Controller):
    @GET("/sse/logs")
    async def stream_logs(self, ctx: RequestCtx):
        # Simply returns the text-based generator
        return SSEResponse.text(self._log_generator())

    async def _log_generator(self):
        for line in ["Initialize boot...", "Load integrations...", "Compile routes..."]:
            yield line + "\\n"
            await asyncio.sleep(0.5)`}</CodeBlock>
      </section>

      {/* SSEResponse.json overload */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">SSEResponse.json()</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            For richer dashboards, updates must often be structured JSON payloads. Manual JSON encoding within generator functions adds boilerplates and risks runtime faults.
          </p>
          <p>
            The <code className="text-white">SSEResponse.json()</code> constructor takes an <code className="text-white">AsyncGenerator[Any, None]</code>. Each object yielded is encoded using <code className="text-white">json.dumps()</code> and sent as an event. If serialization fails, the stream throws an <DocTerm id="sse.SSESerializationFault">SSESerializationFault</DocTerm>.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/json_stream.py" highlightLines={[6, 9, 12, 13]}>{`import asyncio
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse

class IngestController(Controller):
    @GET("/sse/ingest/status")
    async def ingest_status(self, ctx: RequestCtx):
        # Returns the JSON object generator
        return SSEResponse.json(self._generate_status())

    async def _generate_status(self):
        yield {"step": "read", "rows": 1200, "status": "processing"}
        await asyncio.sleep(0.8)
        yield {"step": "validate", "rows": 1200, "status": "processing"}
        await asyncio.sleep(0.8)
        yield {"step": "done", "rows": 1200, "status": "completed"}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/sse/standard" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Standard Events
        </Link>
        <Link to="/docs/sse/openai" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          OpenAI Streaming <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
