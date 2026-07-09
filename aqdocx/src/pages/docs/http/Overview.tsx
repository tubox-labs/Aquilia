import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          A fully asynchronous, production-grade HTTP client built natively into Aquilia. Zero external dependencies, deep framework integration, and designed for high-performance async workloads.
        </p>
      </div>

      {/* Design Philosophy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Philosophy</h2>
        <p className={`mb-6 ${textMuted}`}>
          Aquilia&apos;s HTTP client is not a wrapper around existing libraries—it is a native implementation using Python&apos;s asyncio primitives, providing:
        </p>
        <div className="space-y-6">
          {[
            { title: 'Zero Dependencies', desc: 'Pure Python asyncio + ssl sockets. No need to install aiohttp, httpx, or requests.' },
            { title: 'Framework Integration', desc: 'Native use of Aquilia faults, config loaders, dependency injection container, and effects systems.' },
            { title: 'Connection Pooling', desc: 'HTTP/1.1 keep-alive with connection reuse and pool limits.' },
            { title: 'Async-First', desc: 'Built from the ground up for async/await. No blocking threads or calls.' },
          ].map((item, i) => (
            <div key={i} className="border-l-2 border-aquilia-500/20 pl-4 py-1">
              <h3 className={`font-mono text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Example</h2>
        <CodeBlock language="python" filename="controller.py" highlightLines={[11, 19, 25]}>{`from aquilia import Controller, GET
from aquilia.http import AsyncHTTPClient, HTTPClientConfig
from aquilia.http.config import TimeoutConfig

class WeatherController(Controller):
    prefix = "/weather"
    
    def __init__(self):
        self.http = AsyncHTTPClient(HTTPClientConfig(
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

      {/* Core Features */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Features</h2>
        <div className="space-y-6">
          {[
            { feature: 'HTTP/1.1 Protocol', desc: 'Native implementation supporting keep-alive, chunked transfers, and gzip/deflate compression.' },
            { feature: 'TLS/SSL Support', desc: 'Secure certificate verification, custom CA bundles, and SNI support.' },
            { feature: 'Connection Pooling', desc: 'TCP connection reuse with per-host and global locks.' },
            { feature: 'Request/Response Streaming', desc: 'Iterate bytes, text, or lines in chunks to process large uploads or downloads.' },
            { feature: 'Retry Logic', desc: 'Exponential backoff with jitter and Retry-After header compliance.' },
            { feature: 'Timeout Control', desc: 'Granular timeouts for connect, read, write, and pool phases.' },
            { feature: 'Interceptors & Middleware', desc: 'Onion-model middleware pipeline for logging, caching, and cookies.' },
            { feature: 'Cookie Management', desc: 'RFC 6265 cookie jar implementation tracking paths, domains, and security attributes.' },
            { feature: 'Authentication', desc: 'Basic, Bearer, API Key, Digest, OAuth2, and AWS Signature V4 schemes.' },
            { feature: 'Multipart Forms', desc: 'Streamed file uploads with progress monitoring callbacks.' },
          ].map((item, i) => (
            <div key={i} className="border-l-2 border-aquilia-500/20 pl-4 py-1">
              <h3 className={`font-mono text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.feature}</h3>
              <p className={`text-sm ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <p className={`mb-6 ${textMuted}`}>
          The HTTP client layers separate high-level APIs from low-level TCP/TLS transport protocols:
        </p>
        <div className="space-y-6">
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <h3 className={`font-mono text-aquilia-500 font-bold mb-1 text-sm`}><DocTerm id="http.AsyncHTTPClient">AsyncHTTPClient</DocTerm></h3>
            <p className={`text-xs ${textMuted}`}>
              Entry point API providing HTTP verb methods (<code className="text-aquilia-500">get()</code>, <code className="text-aquilia-500">post()</code>, etc.) wrapping the active session.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <h3 className={`font-mono text-aquilia-500 font-bold mb-1 text-sm`}><DocTerm id="http.HTTPSession">HTTPSession</DocTerm></h3>
            <p className={`text-xs ${textMuted}`}>
              Manages stateful cookies, headers, redirect limits, and executes the active middleware and interceptor chains.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <h3 className={`font-mono text-aquilia-500 font-bold mb-1 text-sm`}>RequestBuilder</h3>
            <p className={`text-xs ${textMuted}`}>
              Fluid API to validate headers, encode parameters, and serialize body contents.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <h3 className={`font-mono text-aquilia-500 font-bold mb-1 text-sm`}>NativeTransport</h3>
            <p className={`text-xs ${textMuted}`}>
              Handles async SSL/TCP socket connections, serializes HTTP headers, and parses responses in chunks.
            </p>
          </div>
        </div>
      </section>

      {/* Dive Deeper */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dive Deeper</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { label: 'HTTPClient Basics', to: '/docs/http/client' },
            { label: 'Sessions', to: '/docs/http/sessions' },
            { label: 'Transport Layer', to: '/docs/http/transport' },
            { label: 'Advanced Usage', to: '/docs/http/advanced' },
            { label: 'Structured Faults', to: '/docs/http/faults' },
            { label: 'Core API References', to: '/docs/http/api' },
          ].map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-colors ${
                isDark
                  ? 'border-white/5 bg-zinc-950/40 text-gray-200 hover:border-aquilia-500/60 hover:bg-zinc-900/50'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-aquilia-500/60 hover:bg-gray-50'
              }`}
            >
              <span className="text-sm font-medium">{item.label}</span>
              <ArrowRight className="w-4 h-4 text-aquilia-500" />
            </Link>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
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
