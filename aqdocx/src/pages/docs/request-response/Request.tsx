import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ArrowDownToLine, Shield, Globe, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function RequestPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <ArrowDownToLine className="w-4 h-4 animate-bounce" />
          Core
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Request
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="reqres.request">Request</DocTerm> class is a performance-optimized, class-based HTTP request wrapper built directly on the ASGI scope. It leverages <code className="text-aquilia-500">__slots__</code> for low memory overhead and features lazy, cached property accessors for headers, queries, cookies, and bodies.
        </p>
      </div>

      {/* SVG Architecture Diagram */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Lifecycle & Architecture</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The following low-level system design diagram illustrates how an incoming ASGI client payload traverses the lazy-evaluation and protection boundaries:
        </p>
        
        <div className="flex justify-center items-center overflow-x-auto py-6">
          <svg viewBox="0 0 800 240" className="w-full max-w-3xl" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Step 1: ASGI connection */}
            <rect x="10" y="70" width="130" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#10B981" strokeWidth="2" />
            <text x="75" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">ASGI Entry</text>
            <text x="75" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">Raw Connection Scope</text>

            <path d="M140 100 H180" stroke="#71717A" strokeWidth="2" strokeDasharray="4 4" markerEnd="url(#arrow)" />

            {/* Step 2: Protection filters */}
            <rect x="180" y="70" width="130" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#EF4444" strokeWidth="2" />
            <text x="245" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">Security Guards</text>
            <text x="245" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">Max Body / ReDoS limit</text>

            <path d="M310 100 H350" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 3: Lazy parser & cache */}
            <rect x="350" y="70" width="150" height="60" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#3B82F6" strokeWidth="2" />
            <text x="425" y="95" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="12" fontWeight="bold">Lazy Parser Cache</text>
            <text x="425" y="115" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="10">Headers/Cookies/Body</text>

            <path d="M500 100 H540" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 4: Downstream Controller */}
            <rect x="540" y="70" width="140" height="60" rx="10" fill={isDark ? '#27272A' : '#EFF6FF'} stroke="#2563EB" strokeWidth="2" />
            <text x="610" y="95" textAnchor="middle" fill={isDark ? '#FFFFFF' : '#1E40AF'} fontSize="12" fontWeight="bold">Controller Engine</text>
            <text x="610" y="115" textAnchor="middle" fill={isDark ? '#93C5FD' : '#1E40AF'} fontSize="10">RequestCtx Injection</text>

            {/* Definitions for arrow markers */}
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#71717A" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Slots & Architecture */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture & Slots</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          To eliminate dictionary overhead, <DocTerm id="reqres.request">Request</DocTerm> uses Python's <code className="text-aquilia-500">__slots__</code> mapping for all internal state fields.
        </p>
        <CodeBlock language="python" filename="aquilia/request.py">{`class Request:
    __slots__ = (
        "scope",
        "_receive",
        "_send",
        "max_body_size",
        "max_field_count",
        "max_file_size",
        "upload_tempdir",
        "trust_proxy",
        "chunk_size",
        "json_max_size",
        "json_max_depth",
        "form_memory_threshold",
        "state",
        "_body",
        "_body_consumed",
        "_json",
        "_surp",
        "_form_data",
        "_query_params",
        "_headers",
        "_cookies",
        "_url",
        "_disconnected",
        "_temp_files",
    )`}</CodeBlock>
      </section>

      {/* Request Faults */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Faults</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Request validation and parsing failures trigger structured exceptions mapped to the Aquilia Fault system:
        </p>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Fault Class</th>
                <th className="text-left py-3 px-4 font-semibold">Fault Code</th>
                <th className="text-left py-3 px-4 font-semibold">HTTP Status</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { cls: 'BadRequest', code: 'BAD_REQUEST', status: '400', desc: 'Malformed query, body, or form data.' },
                { cls: 'PayloadTooLarge', code: 'PAYLOAD_TOO_LARGE', status: '413', desc: 'Body or uploaded file exceeds size limits.' },
                { cls: 'UnsupportedMediaType', code: 'UNSUPPORTED_MEDIA_TYPE', status: '415', desc: 'Content-Type header mismatch.' },
                { cls: 'ClientDisconnect', code: 'CLIENT_DISCONNECT', status: '499', desc: 'Client aborted connection during processing.' },
                { cls: 'InvalidJSON', code: 'INVALID_JSON', status: '400', desc: 'JSON parsing failure or nesting depth exceeded.' },
                { cls: 'InvalidSurp', code: 'INVALID_SURP', status: '400', desc: 'SURP deserialization failure.' },
                { cls: 'InvalidHeader', code: 'INVALID_HEADER', status: '400', desc: 'Malformed or injection-suspicious headers.' },
                { cls: 'MultipartParseError', code: 'MULTIPART_PARSE_ERROR', status: '400', desc: 'python-multipart parser failure.' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-aquilia-500 font-semibold">{row.cls}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.code}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.status}</td>
                  <td className="py-3 px-4 text-xs">{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Constructor & Config */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Constructor & Config</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Request object is initialized with the ASGI scope, receive, and optional send callables:
        </p>
        <CodeBlock language="python" filename="request_init.py">{`Request(
    scope: dict,                       # ASGI scope
    receive: Callable,                 # ASGI receive channel
    send: Callable | None = None,      # ASGI send channel (optional)
    *,
    max_body_size: int = 10_485_760,   # 10 MB body limit
    max_field_count: int = 1000,        # Max form fields
    max_file_size: int = 2_147_483_648,# 2 GB uploaded file limit
    upload_tempdir: Path | None = None,# Path for temp files
    trust_proxy: bool | list[str] = False, # Blanket trust or trusted CIDRs list
    chunk_size: int = 65536,           # Byte streaming chunk size
    json_max_size: int = 10_485_760,   # 10 MB JSON size limit
    json_max_depth: int = 64,          # Max JSON nest depth
    form_memory_threshold: int = 1048576, # 1 MB memory limit before spilling uploads to disk
)`}</CodeBlock>
      </section>

      {/* Properties & Accessors */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Properties & Accessors</h2>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Attribute</th>
                <th className="text-left py-3 px-4 font-semibold">Type</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { name: 'method', type: 'str', desc: 'Uppercased HTTP method (e.g., "GET", "POST").' },
                { name: 'http_version', type: 'str', desc: 'HTTP protocol version (e.g., "1.1", "2").' },
                { name: 'path', type: 'str', desc: 'Decoded URL path.' },
                { name: 'raw_path', type: 'bytes', desc: 'Raw percent-encoded URL path.' },
                { name: 'query_string', type: 'str', desc: 'Raw query parameters string.' },
                { name: 'client', type: 'tuple | None', desc: 'Client address tuple (host, port).' },
                { name: 'query_params', type: 'MultiDict', desc: 'Lazy-parsed query parameters as MultiDict.' },
                { name: 'headers', type: 'Headers', desc: 'Lazy-parsed, case-insensitive headers collection.' },
                { name: 'cookies', type: 'Mapping[str, str]', desc: 'Lazy-parsed HTTP cookies.' },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-aquilia-500 font-semibold">{row.name}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.type}</td>
                  <td className="py-3 px-4 text-xs">{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Client IP & Proxy Trust */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <Globe className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Client IP & Proxy Trust</h2>
        </div>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">client_ip()</code> method determines the client's IP. When <code className="text-aquilia-500">trust_proxy</code> is configured with a list of networks, it walks the <code className="text-aquilia-500">X-Forwarded-For</code> list from right to left, returning the rightmost IP that is not in the trusted set to prevent client spoofing.
        </p>
        <CodeBlock language="python" filename="proxy_trust.py">{`# Initialize with trusted proxy CIDRs
req = Request(scope, receive, trust_proxy=["10.0.0.0/8", "192.168.1.0/24"])

# Client IP resolution
ip = req.client_ip()`}</CodeBlock>
      </section>

      {/* Body Reading & Streaming */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <Zap className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Body Reading & Streaming</h2>
        </div>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Reading the body is idempotent and cached. If the body is read via <code className="text-aquilia-500">await request.body()</code>, subsequent calls return the cached bytes instantly.
        </p>
        <CodeBlock language="python" filename="body_reading.py">{`# Read full body (cached)
body_bytes = await request.body()
body_text = await request.text(encoding="utf-8")

# Stream bytes in chunks
async for chunk in request.iter_bytes(chunk_size=16384):
    await process_chunk(chunk)

# Read exactly n bytes
header = await request.readexactly(1024)`}</CodeBlock>
        <div className="p-4 border-l-4 border-aquilia-500 bg-aquilia-500/5 rounded-r-xl">
          <p className={`text-xs ${isDark ? 'text-aquilia-300' : 'text-aquilia-700'}`}>
            <strong>Note:</strong> Calling <code className="text-aquilia-500">iter_bytes()</code> directly consumes the stream from ASGI. If you need to read the body both as a stream and as single-shot bytes, call <code className="text-aquilia-500">await request.body()</code> first to cache it.
          </p>
        </div>
      </section>

      {/* JSON & SURP Parsing */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>JSON & SURP Input Validation</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">json()</code> and <code className="text-aquilia-500">surp()</code> methods parse the request body and support direct model validation:
        </p>
        <CodeBlock language="python" filename="json_parsing.py">{`# Parse JSON as dict/list
data = await request.json()

# Parse and validate using a Pydantic model
user = await request.json(model=UserCreateRequest)`}</CodeBlock>
      </section>

      {/* Auth, Session & DI */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Auth, Session & DI Integration</h2>
        </div>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Request coordinates with middleware to expose authenticated identity, active sessions, and dependency injection scopes:
        </p>
        <CodeBlock language="python" filename="integration.py">{`# Get active identity
identity = request.identity
is_auth = request.authenticated

# Require auth (raises AUTH_REQUIRED structured fault if unauthenticated)
user = request.require_identity()

# Session integration
session = request.session
session["views"] = session.get("views", 0) + 1

# Dependency injection resolution
db_service = await request.resolve(DatabaseService)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/config/integrations" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Config Integrations</span>
        </Link>
        <Link to="/docs/request-response/response" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>Response</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}