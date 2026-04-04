import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            HTTP Client
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A fully asynchronous, production-grade HTTP client built natively into Aquilia. Zero external dependencies, deep framework integration, and designed for high-performance async workloads.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Philosophy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's HTTP client is not a wrapper around existing libraries—it's a native implementation using Python's asyncio primitives. This design choice provides:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { title: 'Zero Dependencies', desc: 'Pure Python asyncio + ssl. No aiohttp, no httpx, no requests.' },
            { title: 'Framework Integration', desc: 'Native use of Aquilia faults, config, DI, and effects systems.' },
            { title: 'Connection Pooling', desc: 'HTTP/1.1 keep-alive with intelligent connection reuse.' },
            { title: 'Async-First', desc: 'Built from the ground up for async/await. No sync blocking.' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Example</h2>
        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, GET
from aquilia.http import HTTPClient, HTTPClientConfig

class WeatherController(Controller):
    prefix = "/weather"
    
    def __init__(self):
        self.http = HTTPClient(HTTPClientConfig(
            timeout=TimeoutConfig(total=5.0),
            user_agent="Aquilia/1.0",
        ))
    
    @GET("/{city}")
    async def get_weather(self, ctx, city: str):
        # Make HTTP request
        response = await self.http.get(
            f"https://api.weather.com/v1/current/{city}",
            headers={"API-Key": "your-key"},
        )
        
        # Parse JSON response
        data = await response.json()
        return ctx.json(data)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *exc):
        await self.http.close()`}</CodeBlock>
      </section>

      {/* Features */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Features</h2>
        <div className="space-y-3">
          {[
            { feature: 'HTTP/1.1 Protocol', desc: 'Native implementation with keep-alive, chunked encoding, compression, and pipelined requests.' },
            { feature: 'TLS/SSL Support', desc: 'Full certificate verification, custom CA bundles, client certs, TLS 1.2+, SNI support.' },
            { feature: 'Connection Pooling', desc: 'Automatic connection reuse with per-host limits (default 10), global limits (default 100), keepalive expiry (60s), health tracking, and background cleanup.' },
            { feature: 'Request/Response Streaming', desc: 'Stream large payloads without loading into memory. Progress callbacks, backpressure handling, iter_bytes(), iter_text(), iter_lines().' },
            { feature: 'Retry Logic', desc: 'Exponential backoff, constant delay, RetryAfter header support, composite strategies, configurable per-method retry (idempotent only by default).' },
            { feature: 'Timeout Control', desc: 'Separate connect (10s), read, write, total (30s), and pool timeouts. Per-request overrides. Preset configs: fast(), slow(), no_timeout().' },
            { feature: 'Interceptors & Middleware', desc: '10+ middleware types (logging, caching, compression, cookies, error handling, retry, base URL, headers). 8+ interceptors (auth, redirect, cache, metrics, timeout). Composable pipeline with onion model.' },
            { feature: 'Cookie Management', desc: 'Automatic cookie jar with RFC 6265 compliance, domain/path matching (with subdomain support), expiry tracking, SameSite/Secure/HttpOnly flags, Set-Cookie parsing.' },
            { feature: 'Authentication', desc: '6 built-in schemes: BasicAuth (RFC 7617), BearerAuth (static/dynamic tokens), APIKeyAuth (header/query), DigestAuth (RFC 7616 challenge-response), OAuth2Auth (automatic token refresh, 401 retry), AWSSignatureV4Auth (AWS request signing).' },
            { feature: 'Multipart Forms', desc: 'File uploads with progress tracking, streaming support, boundary generation, content-type auto-detection, Path/bytes/file-like/async iterator support, content-length calculation.' },
            { feature: 'Compression', desc: 'Automatic gzip/deflate decompression for responses. Accept-Encoding header management via CompressionMiddleware.' },
            { feature: 'Fault Integration', desc: '20+ fault types in HTTP_CLIENT_DOMAIN: connection (ConnectionFault, ConnectionPoolExhaustedFault, ConnectionClosedFault), timeout (ConnectTimeout, ReadTimeout, WriteTimeout, RequestTimeout), TLS (TLSFault, CertificateVerifyFault), response (InvalidResponseFault, DecodingFault, HTTPStatusFault, ClientErrorFault, ServerErrorFault), retry (RetryExhaustedFault), request (RequestBuildFault, InvalidURLFault, InvalidHeaderFault), transport (TransportFault, ProxyFault), redirect (TooManyRedirectsFault), and config (ConfigurationFault). All faults include retryable metadata, severity levels, and structured error codes.' },
            { feature: 'Proxy Support', desc: 'HTTP and HTTPS proxy configuration with environment variable support (HTTP_PROXY, HTTPS_PROXY, NO_PROXY), per-request proxy override.' },
            { feature: 'JSON Handling', desc: 'Intelligent JSON parser selection: prefers orjson > ujson > stdlib json for performance. Automatic Content-Type detection.' },
            { feature: 'Redirect Handling', desc: 'Automatic redirect following (max 10 by default), 303/301/302 method conversion (POST→GET), loop detection, history tracking.' },
            { feature: 'Request Building', desc: 'Fluent RequestBuilder API with method chaining. Query param encoding (with array support), header validation (RFC 7230), automatic body serialization (JSON/form/multipart).' },
            { feature: 'DI Integration', desc: 'HTTPClientProvider with configurable scopes (singleton/app/request). Automatic lifecycle management. HTTPClientBuilder for fluent config in workspace.py via Integration.http_client().' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-start gap-3">
                <div className="mt-1 w-1.5 h-1.5 rounded-full bg-aquilia-500 flex-shrink-0" />
                <div>
                  <h3 className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.feature}</h3>
                  <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The HTTP client is organized into several layers, each with specific responsibilities. The architecture follows a clean separation of concerns with composable pipelines:
        </p>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>AsyncHTTPClient</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              High-level client interface providing <code>get()</code>, <code>post()</code>, <code>put()</code>, <code>patch()</code>, <code>delete()</code>, <code>head()</code>, <code>options()</code>. 
              Wraps HTTPSession for request execution. Supports context manager protocol for automatic cleanup. Entry point for most use cases.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>HTTPSession</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Stateful wrapper managing cookies, default headers, base URLs, and persistent configuration across requests. 
              Executes middleware chain (onion model) and interceptor chain (before/after hooks). Handles automatic redirect following (up to 10 redirects with loop detection). 
              Integrates cookies from CookieJar into requests and extracts Set-Cookie headers from responses. Optionally raises for HTTP error statuses.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>RequestBuilder</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Fluent API for constructing requests. Validates headers per RFC 7230 (no null bytes, control chars). 
              Encodes query parameters with array support (<code>?ids=1&amp;ids=2</code>). Automatically serializes JSON bodies (prefers orjson &gt; ujson &gt; stdlib). 
              Handles form-encoded data (<code>application/x-www-form-urlencoded</code>) and multipart form data. Merges base URL with relative paths. 
              Produces immutable <code>HTTPClientRequest</code> objects.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>Middleware Stack</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Composable onion-model pipeline wrapping requests. Middleware execute in order for requests, reverse order for responses. 
              Built-in middleware: <code>LoggingMiddleware</code>, <code>HeadersMiddleware</code>, <code>TimeoutMiddleware</code>, <code>ErrorHandlingMiddleware</code>, 
              <code>RetryMiddleware</code>, <code>CompressionMiddleware</code>, <code>CacheMiddleware</code>, <code>BaseURLMiddleware</code>, <code>CookieMiddleware</code>. 
              Factory: <code>create_middleware_stack()</code> with feature flags for easy composition.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>Interceptor Chain</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Before/after hook pattern for request/response processing. Interceptors: <code>LoggingInterceptor</code>, <code>HeaderInterceptor</code>, 
              <code>UserAgentInterceptor</code>, <code>AcceptInterceptor</code>, <code>MetricsInterceptor</code>, <code>TimeoutInterceptor</code>, 
              <code>RedirectInterceptor</code>, <code>CacheInterceptor</code>, all auth interceptors (<code>BasicAuth</code>, <code>BearerAuth</code>, 
              <code>APIKeyAuth</code>, <code>DigestAuth</code>, <code>OAuth2Auth</code>, <code>AWSSignatureV4Auth</code>). 
              Uses <code>InterceptorChain</code> to link handlers.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>NativeTransport</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Core HTTP/1.1 implementation using <code>asyncio.open_connection()</code>. 
              Builds raw HTTP requests (method line, headers, body), writes to StreamWriter. 
              Parses HTTP responses (status line, headers, body/chunked) from StreamReader. 
              Supports chunked transfer encoding (<code>ChunkedEncoder</code>, <code>ChunkedDecoder</code>). 
              Handles gzip/deflate compression/decompression. Manages TLS handshake via <code>ssl.SSLContext</code>. 
              Integrates with <code>ConnectionPool</code> for connection reuse. Respects connect/read/write/total timeouts via <code>asyncio.wait_for()</code>.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>ConnectionPool</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Manages reusable TCP connections per (scheme, host, port) tuple. Per-host limit (default 10), global limit (default 100). 
              Tracks connection age and idle time. Expires connections after <code>keepalive_expiry</code> (default 60s). 
              Background cleanup task runs every 30s removing stale connections. 
              Provides <code>acquire()</code> (reuse or create new), <code>add()</code> (register new), <code>release()</code> (return for reuse), <code>cleanup()</code> (expire old). 
              Thread-safe with per-host locks and global lock. Tracks statistics: <code>ConnectionStats</code> with total_created, total_closed, total_reused, active_connections, idle_connections, failed_acquisitions, pool_exhausted_count.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>HTTPClientResponse</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Immutable response object with status code, reason phrase, headers (case-insensitive MultiDict), body (bytes). 
              Properties: <code>is_success</code> (2xx), <code>is_error</code> (4xx/5xx), <code>is_client_error</code> (4xx), <code>is_server_error</code> (5xx), <code>is_redirect</code> (3xx). 
              Methods: <code>json()</code> (auto-parse), <code>text()</code> (decode with charset from Content-Type), <code>iter_bytes(chunk_size)</code>, <code>iter_text(chunk_size, encoding)</code>, <code>iter_lines(chunk_size)</code>. 
              Cookies extracted from <code>Set-Cookie</code> headers via <code>extract_cookies()</code>. 
              Redirect history tracked in <code>history</code> list. <code>raise_for_status()</code> throws <code>HTTPStatusFault</code> for errors.
            </p>
          </div>
        </div>
      </section>

      {/* Configuration Presets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration Presets</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides preset configurations for common scenarios. All configs are fully serializable via <code>to_dict()</code> and <code>from_dict()</code>:
        </p>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-mono text-sm text-aquilia-500 font-bold mb-2`}>TimeoutConfig.fast()</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
              For low-latency internal APIs: <code>total=5.0</code>, <code>connect=2.0</code>
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-sm text-aquilia-500 font-bold mb-2`}>TimeoutConfig.slow()</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
              For slow external APIs: <code>total=60.0</code>, <code>connect=15.0</code>
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-sm text-aquilia-500 font-bold mb-2`}>TimeoutConfig.no_timeout()</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
              For long-running operations like downloads: all timeouts set to <code>None</code>
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-sm text-aquilia-500 font-bold mb-2`}>RetryConfig.no_retry()</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
              Disable retries: <code>max_attempts=0</code>
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-sm text-aquilia-500 font-bold mb-2`}>RetryConfig.aggressive()</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
              Maximum retries for resilience: <code>max_attempts=5</code>, <code>backoff_base=0.5</code>, <code>backoff_max=30.0</code>
            </p>
          </div>
        </div>
        <CodeBlock language="python" filename="config_example.py">{`from aquilia.http import HTTPClientConfig, TimeoutConfig, RetryConfig

# Fast config for internal microservices
fast_config = HTTPClientConfig(
    timeout=TimeoutConfig.fast(),
    retry=RetryConfig.no_retry(),
)

# Resilient config for external APIs
resilient_config = HTTPClientConfig(
    timeout=TimeoutConfig.slow(),
    retry=RetryConfig.aggressive(),
    follow_redirects=True,
    max_redirects=10,
)

# Serialize/deserialize
config_dict = fast_config.to_dict()
restored = HTTPClientConfig.from_dict(config_dict)`}</CodeBlock>
      </section>

      {/* Comparison */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why Not Use aiohttp/httpx?</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's HTTP client is purpose-built for framework integration:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Aquilia HTTP Client</h3>
            <ul className={`text-sm space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>✓ Zero external dependencies</li>
              <li>✓ Native fault system integration</li>
              <li>✓ DI-aware with provider pattern</li>
              <li>✓ Async-only (no sync overhead)</li>
              <li>✓ Framework-specific optimizations</li>
              <li>✓ Smaller footprint for deployment</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>External Libraries</h3>
            <ul className={`text-sm space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>× Additional dependencies to manage</li>
              <li>× Generic error handling</li>
              <li>× Manual DI integration required</li>
              <li>× May include sync compatibility layers</li>
              <li>× General-purpose design</li>
              <li>× Larger dependency tree</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Getting Started */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Getting Started</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The HTTP client is included with Aquilia—no additional installation required. Jump to the pages below to learn more:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link to="/docs/http/client" className={`${boxClass} hover:border-aquilia-500/50 transition-colors`}>
            <h3 className={`font-bold mb-2 text-aquilia-500`}>HTTPClient Basics</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Learn the core HTTP client API, configuration, and request/response handling.
            </p>
          </Link>
          <Link to="/docs/http/transport" className={`${boxClass} hover:border-aquilia-500/50 transition-colors`}>
            <h3 className={`font-bold mb-2 text-aquilia-500`}>Transport Layer</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Understand the native HTTP/1.1 transport and connection pooling internals.
            </p>
          </Link>
          <Link to="/docs/http/sessions" className={`${boxClass} hover:border-aquilia-500/50 transition-colors`}>
            <h3 className={`font-bold mb-2 text-aquilia-500`}>Sessions</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Use stateful sessions for cookie management and persistent configuration.
            </p>
          </Link>
          <Link to="/docs/http/advanced" className={`${boxClass} hover:border-aquilia-500/50 transition-colors`}>
            <h3 className={`font-bold mb-2 text-aquilia-500`}>Advanced Usage</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Streaming, retries, interceptors, middleware, and performance tuning.
            </p>
          </Link>
          <Link to="/docs/http/api" className={`${boxClass} hover:border-aquilia-500/50 transition-colors`}>
            <h3 className={`font-bold mb-2 text-aquilia-500`}>Core API Reference</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Deep technical references for request, response, auth, cookies, middleware, multipart, and streaming modules.
            </p>
          </Link>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/templates" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Templates
        </Link>
        <Link to="/docs/http/client" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          HTTPClient Basics <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
