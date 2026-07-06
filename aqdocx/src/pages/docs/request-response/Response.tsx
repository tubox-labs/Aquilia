import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ArrowUpFromLine, Zap, Cookie } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ResponsePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <ArrowUpFromLine className="w-4 h-4 animate-bounce" />
          Core
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Response
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="reqres.response">Response</DocTerm> class is the core HTTP response builder for Aquilia, designed for performance-critical streaming and flexible serialization. It supports content negotiation, block compression (Gzip/Brotli), Range requests (HTTP 206), cookie signing, and background tasks.
        </p>
      </div>

      {/* SVG Architecture Diagram */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Response Transmission Pipeline</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The following low-level system design diagram illustrates how outbound data is negotiated, encoded, and dispatched to the ASGI channel:
        </p>
        
        <div className="flex justify-center items-center overflow-x-auto py-6">
          <svg viewBox="0 0 800 240" className="w-full max-w-3xl" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Step 1: Controller Return */}
            <rect x="10" y="70" width="130" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#3B82F6" strokeWidth="2" />
            <text x="75" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">Handler Yield</text>
            <text x="75" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">Dict / Model / Bytes</text>

            <path d="M140 100 H180" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 2: Content Negotiation / Molding */}
            <rect x="180" y="70" width="140" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#10B981" strokeWidth="2" />
            <text x="250" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">Content Negotiation</text>
            <text x="250" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">JSON / XML / SURP molding</text>

            <path d="M320 100 H360" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 3: Encoding & Compressor */}
            <rect x="360" y="70" width="140" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#8B5CF6" strokeWidth="2" />
            <text x="430" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">Compression / Range</text>
            <text x="430" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">Gzip/Brotli/Range headers</text>

            <path d="M500 100 H540" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 4: ASGI Client Transmission */}
            <rect x="540" y="70" width="130" height="60" rx="10" fill={isDark ? '#27272A' : '#D1FAE5'} stroke="#059669" strokeWidth="2" />
            <text x="605" y="95" textAnchor="middle" fill={isDark ? '#FFFFFF' : '#065F46'} fontSize="12" fontWeight="bold">ASGI Send</text>
            <text x="605" y="115" textAnchor="middle" fill={isDark ? '#A7F3D0' : '#065F46'} fontSize="10">Background Tasks run</text>

            {/* Definitions for arrow markers */}
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#71717A" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Response Faults */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Response Faults</h2>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Fault Class</th>
                <th className="text-left py-3 px-4 font-semibold">Fault Code</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { cls: 'ResponseStreamError', code: 'RESPONSE_STREAM_ERROR', desc: 'Failure during ASGI response body transmission.' },
                { cls: 'TemplateRenderError', code: 'TEMPLATE_RENDER_ERROR', desc: 'Template rendering engine exception.' },
                { cls: 'InvalidHeaderError', code: 'INVALID_HEADER', desc: 'Header name/value verification failure (prevents header injection).' },
                { cls: 'ClientDisconnectError', code: 'CLIENT_DISCONNECT', desc: 'Client closed connection before transfer completed.' },
                { cls: 'RangeNotSatisfiableError', code: 'RANGE_NOT_SATISFIABLE', desc: 'Requested byte range cannot be satisfied (HTTP 416).' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-aquilia-500 font-semibold">{row.cls}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.code}</td>
                  <td className="py-3 px-4 text-xs">{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Constructor */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Constructor</h2>
        <CodeBlock language="python" filename="response_init.py">{`Response(
    content: Any = b"",                  # Response payload (bytes, str, list/dict, iterator)
    status: int = 200,                   # HTTP status code
    headers: Mapping | None = None,      # Key-value response headers
    media_type: str | None = None,       # Media type override
    *,
    background: BackgroundTask | None = None, # Task to run post-transmission
    encoding: str = "utf-8",             # Text body encoding
    validate_headers: bool = True,       # Guard against header injection
)`}</CodeBlock>
      </section>

      {/* Factory Methods */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Factory Methods</h2>
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Standard Formats</h3>
          <CodeBlock language="python" filename="standard_factories.py">{`# JSON (optimized using orjson/ujson automatically)
Response.json({"data": "value"}, status=200)

# HTML
Response.html("<h1>Welcome</h1>", status=200)

# Plain Text
Response.text("OK", status=200)

# Redirect
Response.redirect("/new-location", status=307)`}</CodeBlock>
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Binary & Content Negotiation (SURP)</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Aquilia supports the SURP binary format. <code className="text-aquilia-500">Response.negotiated()</code> automatically parses quality factors from the client's <code className="text-aquilia-500">Accept</code> header to choose between SURP and JSON:
          </p>
          <CodeBlock language="python" filename="surp_factories.py">{`# Explicit SURP Response (falls back to JSON if surp is missing)
Response.surp({"nodes": [...]}, status=200, compression="lz4")

# Content-negotiated Response
Response.negotiated({"payload": data}, ctx.request)`}</CodeBlock>
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming & SSE</h3>
          <CodeBlock language="python" filename="streaming_factories.py">{`# Stream raw bytes from an async generator
Response.stream(async_bytes_generator(), media_type="application/octet-stream")

# Server-Sent Events (SSE)
Response.sse(sse_event_generator())`}</CodeBlock>
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>HLS Media Streaming</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Aquilia provides native helpers to serve HLS playlists (.m3u8) and MPEG-TS media segments:
          </p>
          <CodeBlock language="python" filename="hls_factories.py">{`from aquilia.response import HLSSegment, HLSVariant

# Serve HLS Media Playlist
Response.hls_playlist(
    segments=[
        HLSSegment(uri="seg1.ts", duration=4.0),
        HLSSegment(uri="seg2.ts", duration=3.8)
    ],
    target_duration=4
)

# Serve HLS Master Playlist
Response.hls_master_playlist(
    variants=[
        HLSVariant(uri="low/index.m3u8", bandwidth=800000, resolution="480x270"),
        HLSVariant(uri="high/index.m3u8", bandwidth=2400000, resolution="1280x720")
    ]
)`}</CodeBlock>
        </div>
      </section>

      {/* Cookie Management */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <Cookie className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Management</h2>
        </div>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Cookies can be signed using <DocTerm id="reqres.cookiesigner">CookieSigner</DocTerm> to prevent client-side tampering.
        </p>
        <CodeBlock language="python" filename="cookies.py">{`# Initialize signer with key
signer = CookieSigner(secret_key="secure-random-key")

response = Response.text("Hello")

# Set signed cookie
response.set_cookie(
    "session_id", "value",
    secure=True,
    httponly=True,
    samesite="Lax",
    signed=True,
    signer=signer
)

# Delete cookie
response.delete_cookie("session_id")`}</CodeBlock>
      </section>

      {/* Background Tasks */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Background Tasks</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Background tasks execute sequentially after the response bytes have been completely flushed to the client:
        </p>
        <CodeBlock language="python" filename="background_tasks.py">{`from aquilia.response import CallableBackgroundTask

async def send_welcome_email():
    await email_service.send("Welcome!")

response = Response.json({"status": "user created"})
response._background_tasks.append(
    CallableBackgroundTask(send_welcome_email)
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/request-response/request" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Request</span>
        </Link>
        <Link to="/docs/request-response/data-structures" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>Data Structures</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}