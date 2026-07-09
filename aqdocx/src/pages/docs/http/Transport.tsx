import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPTransport() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Internals
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Transport Layer
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The NativeTransport implements HTTP/1.1 protocol handling using pure Python asyncio — no external HTTP client dependencies.
        </p>
      </div>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <p className={`mb-4 ${textMuted}`}>
          The transport layer is the foundation of Aquilia&apos;s HTTP client:
        </p>
        <div className="border-l-2 border-aquilia-500/20 pl-6 py-1">
          <div className={`font-mono text-sm space-y-2.5 ${textMuted}`}>
            <p className="text-aquilia-500 font-bold">HTTPClient</p>
            <p className="ml-4">↓ Uses</p>
            <p className="ml-4 text-aquilia-500 font-bold">Session</p>
            <p className="ml-8">↓ Uses</p>
            <p className="ml-8 text-aquilia-500 font-bold">NativeTransport</p>
            <p className="ml-12">├─ ConnectionPool (connection reuse)</p>
            <p className="ml-12">├─ HTTP/1.1 protocol implementation</p>
            <p className="ml-12">├─ Chunked transfer encoding</p>
            <p className="ml-12">├─ Gzip/deflate decompression</p>
            <p className="ml-12">├─ SSL/TLS handling</p>
            <p className="ml-12">└─ Fault conversion</p>
          </div>
        </div>
      </section>

      {/* Why Native Transport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why Native Transport?</h2>
        <div className="space-y-6">
          <div>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Zero External Dependencies</h3>
            <p className={`text-sm ${textMuted}`}>
              Built entirely on Python&apos;s standard library (asyncio, ssl, gzip, zlib). No need for aiohttp, httpx, or other third-party HTTP clients.
            </p>
          </div>
          <div>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Deep Integration</h3>
            <p className={`text-sm ${textMuted}`}>
              Tight coupling with Aquilia&apos;s fault system. Network errors are automatically converted to typed faults (<code className="text-aquilia-500">ConnectionFault</code>, <code className="text-aquilia-500">TimeoutFault</code>, <code className="text-aquilia-500">TLSFault</code>) with structured metadata.
            </p>
          </div>
        </div>
      </section>

      {/* HTTP/1.1 Implementation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HTTP/1.1 Protocol</h2>
        <p className={`mb-4 ${textMuted}`}>
          NativeTransport implements the HTTP/1.1 specification:
        </p>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2 mb-6">
          <p>• <strong>Persistent connections</strong> — Keep-alive for connection reuse.</p>
          <p>• <strong>Chunked encoding</strong> — Streaming without Content-Length headers.</p>
        </div>
        <CodeBlock language="python" filename="http_wire_format.py" highlightLines={[1, 5, 10, 11]}>{`# Request format (what NativeTransport sends)
GET /api/users HTTP/1.1\r
Host: api.example.com\r
User-Agent: Aquilia-HTTP/1.0\r
Connection: keep-alive\r
\r

# Response format (what NativeTransport receives)
HTTP/1.1 200 OK\r
Content-Type: application/json\r
Content-Length: 42\r
Connection: keep-alive\r
\r
{"users": ["alice", "bob"]}`}</CodeBlock>
      </section>

      {/* Connection Pooling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Pooling</h2>
        <CodeBlock language="python" filename="connection_pool.py" highlightLines={[10, 24, 29]}>{`# Internal structure (simplified)
class ConnectionPool:
    def __init__(self, max_connections: int, keepalive_expiry: float):
        self._pool: dict[str, list[ConnectionInfo]] = {}
        self._max_connections = max_connections
        self._keepalive_expiry = keepalive_expiry
    
    async def acquire(
        self,
        scheme: str,
        host: str,
        port: int,
        ssl_context: ssl.SSLContext | None,
    ) -> tuple[StreamReader, StreamWriter]:
        key = f"{scheme}://{host}:{port}"
        
        # Try pool first
        if key in self._pool:
            for conn in self._pool[key]:
                if self._is_alive(conn):
                    return conn.reader, conn.writer
        
        # Create new connection
        reader, writer = await asyncio.open_connection(
            host, port, ssl=ssl_context
        )
        return reader, writer
`}</CodeBlock>
      </section>

      {/* SSL/TLS Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SSL/TLS Handling</h2>
        <p className={`mb-4 ${textMuted}`}>
          HTTPS connections are managed via Python&apos;s native <code className="text-aquilia-500">ssl</code> context:
        </p>
        <CodeBlock language="python" filename="ssl_handling.py" highlightLines={[4, 6, 21, 22]}>{`import ssl

# Create SSL context from config
if config.verify_ssl:
    ssl_context = ssl.create_default_context()
else:
    ssl_context = ssl._create_unverified_context()

# Connect with TLS
reader, writer = await asyncio.open_connection(
    host,
    port,
    ssl=ssl_context,
    server_hostname=host,
)
`}</CodeBlock>
      </section>

      {/* Performance Characteristics */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance</h2>
        <div className="space-y-6">
          <div>
            <h4 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Reuse</h4>
            <p className={`text-xs ${textMuted}`}>Keep-alive sockets avoid TCP handshake (~100ms) and TLS negotiation (~200ms) on repeat requests.</p>
          </div>
          <div>
            <h4 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Memory Efficiency</h4>
            <p className={`text-xs ${textMuted}`}>Streaming response chunks prevents loading large file payloads fully into Python process memory.</p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
        <Link to="/docs/http/sessions" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Sessions
        </Link>
        <Link to="/docs/http/advanced" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Advanced Usage <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
