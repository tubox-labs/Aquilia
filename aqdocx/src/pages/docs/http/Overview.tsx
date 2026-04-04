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
            { feature: 'HTTP/1.1 Protocol', desc: 'Native implementation with keep-alive, chunked encoding, and compression.' },
            { feature: 'TLS/SSL Support', desc: 'Full certificate verification, custom CA bundles, client certs, TLS 1.2+.' },
            { feature: 'Connection Pooling', desc: 'Automatic connection reuse with configurable limits and keep-alive expiry.' },
            { feature: 'Request/Response Streaming', desc: 'Stream large payloads without loading into memory.' },
            { feature: 'Retry Logic', desc: 'Exponential backoff, constant delay, custom strategies with circuit breakers.' },
            { feature: 'Timeout Control', desc: 'Separate connect, read, write, and total timeouts per request.' },
            { feature: 'Interceptors & Middleware', desc: 'Hook into request/response lifecycle for logging, metrics, auth.' },
            { feature: 'Cookie Management', desc: 'Automatic cookie jar with domain/path matching and expiry tracking.' },
            { feature: 'Authentication', desc: 'Built-in Basic, Bearer, API Key, Digest, OAuth2, AWS Signature V4.' },
            { feature: 'Multipart Forms', desc: 'File uploads with progress tracking and streaming support.' },
            { feature: 'Compression', desc: 'Automatic gzip/deflate decompression for responses.' },
            { feature: 'Fault Integration', desc: 'All network errors map to structured Aquilia faults.' },
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
          The HTTP client is organized into several layers, each with specific responsibilities:
        </p>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>HTTPClient</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              High-level client interface. Provides <code>get()</code>, <code>post()</code>, <code>put()</code>, etc. methods with interceptor chain execution and retry logic.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>Session</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Stateful wrapper around HTTPClient. Manages cookies, default headers, base URLs, and persistent configuration across requests.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>NativeTransport</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Core HTTP/1.1 implementation using <code>asyncio.open_connection()</code>. Handles request building, response parsing, chunked encoding, compression, and connection pooling.
            </p>
          </div>
          <div className={boxClass}>
            <h3 className={`font-mono text-aquilia-500 font-bold mb-2`}>ConnectionPool</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Manages reusable TCP connections per host. Tracks connection age, enforces limits, and handles keep-alive expiry.
            </p>
          </div>
        </div>
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
