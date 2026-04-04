import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPTransport() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

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
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The NativeTransport implements HTTP/1.1 protocol handling using pure Python asyncio — no external HTTP client dependencies.
        </p>
      </div>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The transport layer is the foundation of Aquilia's HTTP client:
        </p>
        <div className={boxClass}>
          <div className={`font-mono text-sm space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
        <div className={boxClass}>
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Zero External Dependencies</h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Built entirely on Python's standard library (asyncio, ssl, gzip, zlib). No need for aiohttp, httpx, or other third-party HTTP clients.
          </p>
          
          <h3 className={`font-bold mb-4 mt-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Deep Integration</h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Tight coupling with Aquilia's fault system. Network errors are automatically converted to typed faults (ConnectionFault, TimeoutFault, TLSFault) with structured metadata.
          </p>

          <h3 className={`font-bold mb-4 mt-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Full Control</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Complete ownership of the HTTP protocol layer. Enables custom optimizations, debugging, and behavior tailored to Aquilia's needs.
          </p>
        </div>
      </section>

      {/* HTTP/1.1 Implementation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HTTP/1.1 Protocol</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          NativeTransport implements the HTTP/1.1 specification:
        </p>
        <div className={boxClass}>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Persistent connections</strong> — Keep-alive for connection reuse</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Chunked encoding</strong> — Streaming without Content-Length</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Compression</strong> — Gzip and deflate encoding</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Host header</strong> — Automatic from URL</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Content-Length</strong> — Automatic for request bodies</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Transfer-Encoding</strong> — Parse chunked responses</li>
          </ul>
        </div>
        <CodeBlock language="python" filename="http_wire_format.py">{`# Request format (what NativeTransport sends)
GET /api/users HTTP/1.1\r
Host: api.example.com\r
User-Agent: Aquilia-HTTP/1.0\r
Accept: */*\r
Connection: keep-alive\r
\r
# (no body for GET)

# Response format (what NativeTransport receives)
HTTP/1.1 200 OK\r
Content-Type: application/json\r
Content-Length: 42\r
Connection: keep-alive\r
\r
{"users": ["alice", "bob", "charlie"]}

# Chunked response
HTTP/1.1 200 OK\r
Transfer-Encoding: chunked\r
\r
10\r
chunk of data...\r
0\r
\r`}</CodeBlock>
      </section>

      {/* Connection Pooling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Pooling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The ConnectionPool manages TCP connections for reuse:
        </p>
        <CodeBlock language="python" filename="connection_pool.py">{`# Internal structure (simplified)
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
    
    def release(
        self,
        scheme: str,
        host: str,
        port: int,
        reader: StreamReader,
        writer: StreamWriter,
    ):
        key = f"{scheme}://{host}:{port}"
        conn = ConnectionInfo(reader, writer, time.time())
        
        if key not in self._pool:
            self._pool[key] = []
        
        self._pool[key].append(conn)
    
    def _is_alive(self, conn: ConnectionInfo) -> bool:
        # Check if connection is still valid
        if time.time() - conn.created_at > self._keepalive_expiry:
            return False
        if conn.writer.is_closing():
            return False
        return True`}</CodeBlock>
      </section>

      {/* SSL/TLS Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SSL/TLS Handling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTPS connections use Python's ssl module:
        </p>
        <CodeBlock language="python" filename="ssl_handling.py">{`import ssl

# Create SSL context from config
if config.verify_ssl:
    ssl_context = ssl.create_default_context()
else:
    ssl_context = ssl._create_unverified_context()

# Optional: custom CA certificate
if config.ca_cert_path:
    ssl_context.load_verify_locations(cafile=config.ca_cert_path)

# Optional: client certificate
if config.client_cert_path and config.client_key_path:
    ssl_context.load_cert_chain(
        certfile=config.client_cert_path,
        keyfile=config.client_key_path,
    )

# Connect with TLS
reader, writer = await asyncio.open_connection(
    host,
    port,
    ssl=ssl_context,  # Enables TLS
    server_hostname=host,  # For SNI
)

# TLS errors are caught and converted to faults
try:
    reader, writer = await asyncio.open_connection(...)
except ssl.SSLError as e:
    raise TLSFault(
        code="TLS_ERROR",
        message=f"TLS error: {e}",
        reason=str(e),
    )`}</CodeBlock>
      </section>

      {/* Chunked Transfer Encoding */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Chunked Transfer Encoding</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handles responses without Content-Length:
        </p>
        <CodeBlock language="python" filename="chunked_encoding.py">{`# Chunked response format:
# {hex-size}\r\n
# {data}\r\n
# {hex-size}\r\n
# {data}\r\n
# 0\r\n
# \r\n

async def read_chunked_body(reader: StreamReader) -> bytes:
    chunks = []
    
    while True:
        # Read chunk size line (hex)
        size_line = await reader.readline()
        if not size_line:
            break
        
        # Parse hex size
        chunk_size = int(size_line.strip(), 16)
        
        # Size 0 means end of chunks
        if chunk_size == 0:
            await reader.readline()  # Read trailing \r\n
            break
        
        # Read exact chunk_size bytes
        chunk_data = await reader.readexactly(chunk_size)
        chunks.append(chunk_data)
        
        # Read trailing \r\n after chunk
        await reader.readline()
    
    return b"".join(chunks)

# Example chunked response:
# Transfer-Encoding: chunked
# 
# 5\r\n
# hello\r\n
# 6\r\n
#  world\r\n
# 0\r\n
# \r\n
# Result: b"hello world"`}</CodeBlock>
      </section>

      {/* Compression */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Compression</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Automatic decompression for gzip and deflate:
        </p>
        <CodeBlock language="python" filename="compression.py">{`import gzip
import zlib

def decompress(body: bytes, encoding: str) -> bytes:
    if encoding == "gzip":
        return gzip.decompress(body)
    
    elif encoding == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            # Some servers use raw deflate (no zlib header)
            return zlib.decompress(body, -zlib.MAX_WBITS)
    
    else:
        # Unknown encoding, return as-is
        return body

# Usage in transport
content_encoding = headers.get("Content-Encoding", "")
if content_encoding:
    body = decompress(body, content_encoding)

# Request compression (client sends gzip)
import gzip
compressed_body = gzip.compress(body)
headers["Content-Encoding"] = "gzip"
headers["Content-Length"] = str(len(compressed_body))`}</CodeBlock>
      </section>

      {/* Fault Conversion */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Conversion</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All low-level errors are converted to Aquilia faults:
        </p>
        <CodeBlock language="python" filename="fault_conversion.py">{`import ssl
import asyncio

try:
    reader, writer = await asyncio.open_connection(host, port, ssl=ssl_context)
    
except ssl.SSLError as e:
    # TLS/SSL errors
    raise TLSFault(
        code="TLS_ERROR",
        message=f"TLS connection failed: {e}",
        reason=str(e),
        metadata={"host": host, "port": port},
    )

except asyncio.TimeoutError:
    # Timeout errors
    raise TimeoutFault(
        code="CONNECT_TIMEOUT",
        message=f"Connection timeout after {timeout}s",
        timeout=timeout,
        metadata={"host": host, "port": port},
    )

except (OSError, ConnectionError) as e:
    # Network errors
    raise ConnectionFault(
        code="CONNECTION_FAILED",
        message=f"Connection failed: {e}",
        reason=str(e),
        metadata={"host": host, "port": port},
    )

except Exception as e:
    # Unexpected errors
    raise TransportFault(
        code="TRANSPORT_ERROR",
        message=f"Transport error: {e}",
        reason=str(e),
    )`}</CodeBlock>
      </section>

      {/* Request/Response Flow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request/Response Flow</h2>
        <div className={boxClass}>
          <div className={`font-mono text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <p className="font-bold text-aquilia-500">1. Connection Acquisition</p>
            <p className="ml-4">├─ Check connection pool for existing connection</p>
            <p className="ml-4">├─ If found and alive, reuse it</p>
            <p className="ml-4">└─ Otherwise, create new TCP connection</p>
            
            <p className="font-bold text-aquilia-500 mt-3">2. Request Building</p>
            <p className="ml-4">├─ Format request line: "GET /path HTTP/1.1"</p>
            <p className="ml-4">├─ Add Host header from URL</p>
            <p className="ml-4">├─ Add Content-Length if body exists</p>
            <p className="ml-4">├─ Merge user headers with defaults</p>
            <p className="ml-4">└─ Write request to socket</p>
            
            <p className="font-bold text-aquilia-500 mt-3">3. Response Parsing</p>
            <p className="ml-4">├─ Read status line: "HTTP/1.1 200 OK"</p>
            <p className="ml-4">├─ Parse headers until blank line</p>
            <p className="ml-4">├─ Check Transfer-Encoding for chunked</p>
            <p className="ml-4">├─ Read body (chunked or Content-Length)</p>
            <p className="ml-4">└─ Decompress if Content-Encoding is set</p>
            
            <p className="font-bold text-aquilia-500 mt-3">4. Connection Release</p>
            <p className="ml-4">├─ If Connection: close, close the socket</p>
            <p className="ml-4">├─ If keep-alive, return to pool</p>
            <p className="ml-4">└─ Pool evicts old connections on next acquire</p>
          </div>
        </div>
      </section>

      {/* Timeouts */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Timeout Handling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Separate timeouts for each phase:
        </p>
        <CodeBlock language="python" filename="timeouts.py">{`from asyncio import wait_for, TimeoutError

# Connect timeout
try:
    reader, writer = await wait_for(
        asyncio.open_connection(host, port, ssl=ssl_context),
        timeout=config.timeout.connect,
    )
except TimeoutError:
    raise ConnectTimeoutFault(...)

# Write timeout
try:
    await wait_for(
        writer.write(request_bytes),
        timeout=config.timeout.write,
    )
except TimeoutError:
    raise WriteTimeoutFault(...)

# Read timeout
try:
    status_line = await wait_for(
        reader.readline(),
        timeout=config.timeout.read,
    )
except TimeoutError:
    raise ReadTimeoutFault(...)

# Total timeout (wraps entire request)
try:
    response = await wait_for(
        transport.request(...),
        timeout=config.timeout.total,
    )
except TimeoutError:
    raise TimeoutFault(...)`}</CodeBlock>
      </section>

      {/* MockTransport for Testing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MockTransport for Testing</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The HTTP module includes MockTransport for testing without real network calls:
        </p>
        <CodeBlock language="python" filename="mock_transport.py">{`from aquilia.http._transport import MockTransport
from aquilia.http import HTTPResponse

# Create mock transport with canned responses
mock = MockTransport()
mock.add_response(
    "GET",
    "https://api.example.com/users",
    HTTPResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=b'{"users": []}',
    ),
)

# Use in HTTPClient
client = HTTPClient(transport=mock)
response = await client.get("https://api.example.com/users")
assert response.status_code == 200

# Mock can also simulate faults
mock.add_fault(
    "GET",
    "https://api.example.com/fail",
    ConnectionFault(code="CONNECTION_FAILED", message="Network error"),
)

try:
    await client.get("https://api.example.com/fail")
except ConnectionFault:
    print("Fault triggered as expected")`}</CodeBlock>
      </section>

      {/* Performance Characteristics */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance Characteristics</h2>
        <div className={boxClass}>
          <div className="space-y-4">
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Reuse</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Keep-alive connections avoid TCP handshake (~100ms) and TLS negotiation (~200ms) on subsequent requests.
              </p>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Memory Efficiency</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Streaming responses avoid loading entire response into memory. Chunked encoding allows processing as data arrives.
              </p>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Concurrency</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Async I/O allows thousands of concurrent requests with minimal overhead. Connection pool limits prevent resource exhaustion.
              </p>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Compression</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Gzip/deflate reduces bandwidth usage by 70-90% for text responses. Decompression is handled transparently.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
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
