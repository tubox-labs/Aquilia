import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SSEStandardEvents() {
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
          <span>SSE SYSTEM / STANDARD EVENTS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Standard Events &amp; Spec
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Understand the structure of <DocTerm id="sse.SSEEvent">SSEEvent</DocTerm>, custom event namespaces, retry options, and client reconnection behaviors.
        </p>
      </div>

      {/* SSEEvent class anatomy */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">SSEEvent Structure</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            An <DocTerm id="sse.SSEEvent">SSEEvent</DocTerm> represents a structured data payload formatted strictly according to the W3C Server-Sent Events specification. The properties of the class translate directly to fields in the event stream:
          </p>
        </div>

        <CodeBlock language="python" filename="sse_event_anatomy.py" compact showLineNumbers={false}>{`class SSEEvent:
    data: str               # The raw data payload. Splits multi-line strings automatically.
    id: str | None = None   # Event identifier. Used by browsers to query missing events.
    event: str | None = None # Event name tag. Used on client to filter events.
    retry: int | None = None # Reconnect retry delay in milliseconds.`}</CodeBlock>
      </section>

      {/* Custom Event Namespacing */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Custom Event Filters</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            By default, events pushed through an SSE stream have no event name, and are caught by the browser's generic <code className="text-white">onmessage</code> handler. Specifying the <code className="text-white">event</code> string parameter allows you to partition streams. The browser will then trigger specific event listeners registered for that name.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/namespaces.py" highlightLines={[12, 17]}>{`import asyncio
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse, SSEEvent

class FeedController(Controller):
    @GET("/sse/news")
    async def news_feed(self, ctx: RequestCtx):
        return SSEResponse(self._generate_feed())

    async def _generate_feed(self):
        # Push to 'sports' listener
        yield SSEEvent(data="Local match won 3-1", event="sports")
        await asyncio.sleep(0.5)
        
        # Push to 'weather' listener
        yield SSEEvent(data="Heavy rain warning", event="weather")`}</CodeBlock>
      </section>

      {/* Reconnect & Caching */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Reconnections &amp; Caching (Last-Event-ID)</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            When a connection drops (due to network changes or server restarts), the browser's `EventSource` client attempts to reconnect automatically.
          </p>
          <p>
            To prevent data loss, the client sends the last received event ID in the <code className="text-white">Last-Event-ID</code> header. The server can read this header and stream missing logs starting from that ID.
          </p>
          <p>
            Using the <code className="text-white">retry</code> parameter, the server can dynamically change the browser's reconnect cooldown interval.
          </p>
        </div>
      </section>

      {/* Javascript client snippet */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Consuming on the Client (JavaScript)</h2>
        <p className={`mb-6 font-light leading-relaxed ${textMuted}`}>
          Register event listeners on the browser client for custom namespaces:
        </p>

        <CodeBlock language="javascript" filename="client.js" highlightLines={[3, 9, 14]}>{`const eventSource = new EventSource('/sse/news');

// 1. Listen to the generic stream (unnamed events)
eventSource.onmessage = (event) => {
    console.log("Generic message:", event.data);
};

// 2. Listen to custom namespace updates
eventSource.addEventListener('sports', (event) => {
    console.log("Sports flash:", event.data);
});

eventSource.addEventListener('weather', (event) => {
    console.log("Weather update:", event.data);
});

// 3. Handle connection errors
eventSource.onerror = (err) => {
    console.error("Stream error occurred:", err);
};`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/sse/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/sse/streams" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Text &amp; JSON Streams <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
