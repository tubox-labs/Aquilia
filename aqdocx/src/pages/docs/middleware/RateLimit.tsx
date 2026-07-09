import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareRateLimit() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / RATE LIMITING</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Rate Limiting Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.RateLimitMiddleware">RateLimitMiddleware</DocTerm> provides token bucket and sliding window rate limiting to protect services against denial-of-service and brute-force traffic.
        </p>
      </div>

      {/* Algorithms */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Supported Algorithms</h2>
        <div className="space-y-6">
          <div className="border-b border-white/5 pb-4">
            <span className="font-mono text-xs text-aquilia-500 font-bold uppercase">Sliding Window (Default)</span>
            <p className="text-sm text-gray-400 mt-1">
              Maintains high accuracy by inspecting the current and previous fixed-time windows. It computes a weighted request count based on overlap, eliminating spikes at window boundaries while using minimal <code className="text-aquilia-400">O(1)</code> space.
            </p>
          </div>
          <div className="pb-4">
            <span className="font-mono text-xs text-aquilia-500 font-bold uppercase">Token Bucket</span>
            <p className="text-sm text-gray-400 mt-1">
              Implements lazy refills on request arrival. Tolerates short-term burst traffic up to a configured capacity, enforcing smooth limits over time.
            </p>
          </div>
        </div>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Configuration</h2>
        <CodeBlock language="python" filename="rate_limit.py" highlightLines={[12, 13, 19, 20]}>{`from aquilia.middleware_ext import (
    RateLimitMiddleware,
    RateLimitRule,
    ip_key_extractor,
    api_key_extractor,
    user_key_extractor,
)

limiter = RateLimitMiddleware(
    rules=[
        # 1. Global IP Limit: 100 requests per minute
        RateLimitRule(
            limit=100,
            window=60.0,
            key_func=ip_key_extractor,
        ),
        # 2. Scoped API Key Limit: 1000 requests per hour on /api paths
        RateLimitRule(
            limit=1000,
            window=3600.0,
            key_func=api_key_extractor,
            scope="/api",
        ),
        # 3. Burst Tolerant Token Bucket for logins (POST only)
        RateLimitRule(
            limit=5,
            window=300.0,
            algorithm="token_bucket",
            burst=10,
            key_func=ip_key_extractor,
            scope="/auth/login",
            methods=["POST"],
        ),
    ],
    response_format="json",
)

server.middleware(limiter)`}</CodeBlock>
      </section>

      {/* Built-in Key Extractors */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Key Extractors</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The rate limiter groups requests by a unique string key. Aquilia ships with three built-in extractors:
        </p>

        <div className="space-y-4">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">ip_key_extractor(request)</code>
            <p className="text-sm text-gray-400 mt-1">Extracts the client IP address. Respects reverse proxies if <code className="text-aquilia-400">ProxyFixMiddleware</code> is active.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">api_key_extractor(request)</code>
            <p className="text-sm text-gray-400 mt-1">Extracts from the <code className="text-aquilia-400">X-API-Key</code> header or the Bearer token in the <code className="text-aquilia-400">Authorization</code> header.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <code className="text-white text-xs font-mono font-bold">user_key_extractor(request)</code>
            <p className="text-sm text-gray-400 mt-1">Extracts the authenticated user ID from request state or identity objects set by Auth middleware.</p>
          </div>
        </div>
      </section>

      {/* Rule Options */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>RateLimitRule Options</h2>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Option</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Default</th>
                <th className="py-3 px-4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans text-gray-400 text-xs">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">limit</td>
                <td className="py-3 px-4 font-mono">int</td>
                <td className="py-3 px-4 font-mono">100</td>
                <td className="py-3 px-4">Max requests allowed within the window.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">window</td>
                <td className="py-3 px-4 font-mono">float</td>
                <td className="py-3 px-4 font-mono">60.0</td>
                <td className="py-3 px-4">Duration of the rate limit window in seconds.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">algorithm</td>
                <td className="py-3 px-4 font-mono">str</td>
                <td className="py-3 px-4 font-mono">"sliding_window"</td>
                <td className="py-3 px-4">Limit algorithm ("sliding_window" or "token_bucket").</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">key_func</td>
                <td className="py-3 px-4 font-mono">Callable</td>
                <td className="py-3 px-4 font-mono">ip_key_extractor</td>
                <td className="py-3 px-4">Function mapping Request to a string rate limit key.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">burst</td>
                <td className="py-3 px-4 font-mono">int | None</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">Extra burst capacity (token_bucket only).</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">scope</td>
                <td className="py-3 px-4 font-mono">str</td>
                <td className="py-3 px-4 font-mono">"*"</td>
                <td className="py-3 px-4">Path prefix this rule applies to.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">methods</td>
                <td className="py-3 px-4 font-mono">list[str]</td>
                <td className="py-3 px-4 font-mono">[]</td>
                <td className="py-3 px-4">HTTP methods restricted by this rule (empty = all).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/cors" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> CORS
        </Link>
        <Link to="/docs/middleware/security" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Security Headers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}