import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareCORS() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / CORS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CORS Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.CORSMiddleware">CORSMiddleware</DocTerm> provides full RFC 6454 and Fetch Standard compliant Cross-Origin Resource Sharing. It is optimized with cached origin matching, distinct preflight routing, and vary-caching security headers.
        </p>
      </div>

      {/* LRU Cached Matching */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>LRU Cached Origin Matching</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          To avoid evaluating complex regular expressions or glob matches on every incoming request, <DocTerm id="middleware.CORSMiddleware">CORSMiddleware</DocTerm> delegates matching to a specialized <code className="text-aquilia-500">_OriginMatcher</code>. This matcher holds an LRU (Least Recently Used) cache with a maximum capacity of 512 entries, keeping origin verification down to <code className="text-aquilia-500">O(1)</code> for repeat clients.
        </p>
        
        <div className="border-l-2 border-aquilia-500/30 pl-6 py-2 my-6 text-sm text-gray-400">
          Supports glob wildcards (e.g. <code className="text-white">"https://*.domain.com"</code>) and pre-compiled regex objects for matching complex subdomains.
        </div>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Configuration</h2>
        <CodeBlock language="python" filename="cors_config.py" highlightLines={[4, 5, 8, 9]}>{`from aquilia.middleware_ext import CORSMiddleware
import re

server.middleware(
    CORSMiddleware(
        allow_origins=[
            "https://app.example.com",
            "https://*.internal.net",  # Glob subdomain wildcard
            re.compile(r"^https://[a-z0-9-]+\\.prod\\.com$")  # Regex object
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=True,
        max_age=3600
    )
)`}</CodeBlock>
      </section>

      {/* Skipping CORS */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Per-Route Bypassing</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          If a specific endpoint requires custom or dynamic cross-origin logic, you can instruct <DocTerm id="middleware.CORSMiddleware">CORSMiddleware</DocTerm> to bypass the request by setting <code className="text-aquilia-500">request.state["cors_skip"] = True</code>.
        </p>
      </section>

      {/* Option Reference */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Options Reference</h2>
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
                <td className="py-3 px-4 font-mono text-aquilia-300">allow_origins</td>
                <td className="py-3 px-4 font-mono">list[str | Pattern]</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">Allowed origins. Supports exact matches, globs, or regex.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">allow_methods</td>
                <td className="py-3 px-4 font-mono">list[str]</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">List of allowed HTTP methods (e.g. GET, POST).</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">allow_headers</td>
                <td className="py-3 px-4 font-mono">list[str]</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">Allowed request headers during preflight.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">expose_headers</td>
                <td className="py-3 px-4 font-mono">list[str]</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">Headers safe to expose to browser clients.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">allow_credentials</td>
                <td className="py-3 px-4 font-mono">bool</td>
                <td className="py-3 px-4 font-mono">False</td>
                <td className="py-3 px-4">Allows cookies and Authorization headers to pass.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">max_age</td>
                <td className="py-3 px-4 font-mono">int</td>
                <td className="py-3 px-4 font-mono">600</td>
                <td className="py-3 px-4">Preflight OPTIONS response cache duration (seconds).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/static" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Static Files
        </Link>
        <Link to="/docs/middleware/rate-limit" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Rate Limiting <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}