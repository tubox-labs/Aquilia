import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'


export function MiddlewareExtended() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / STATIC FILES</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Static Files Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.StaticMiddleware">StaticMiddleware</DocTerm> provides production-grade static asset serving directly at the ASGI level. It employs a custom radix trie prefix matcher for ultra-fast lookups, verifies canonical paths to prevent traversal exploits, and offloads file serving with conditional HTTP caching.
        </p>
      </div>

      {/* Radix Trie Prefix Matching */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Radix Trie Routing</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Unlike naive string-matching algorithms, <DocTerm id="middleware.StaticMiddleware">StaticMiddleware</DocTerm> constructs a compressed radix trie mapping URL prefixes to folder destinations. This ensures route matching operates in <code className="text-aquilia-500">O(k)</code> time complexity, where <code className="text-aquilia-500">k</code> is the length of the requested path. It easily supports multiple mount points:
        </p>

        <CodeBlock language="python" filename="static_mounts.py" highlightLines={[6, 7]}>{`from aquilia.middleware_ext import StaticMiddleware

# Configure multiple directories
server.middleware(
    StaticMiddleware(
        directories={
            "/static": "./assets/static",
            "/media": "./storage/uploads",
        },
        cache_max_age=31536000, # 1 year
        immutable=True
    )
)`}</CodeBlock>
      </section>

      {/* Security Traversal Hardening */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Security Hardening</h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          To block malicious directory traversal requests (e.g. <code className="text-red-400">/static/../../etc/passwd</code>), the middleware performs canonicalization:
        </p>
        
        <div className="border-l-2 border-red-500/30 pl-6 py-2 my-6 text-sm text-gray-400">
          It resolves target paths using Python's <code className="text-aquilia-400">os.path.realpath</code> and compares them against the canonicalized base directory. If a path escapes the base directory, the middleware immediately raises a <code className="text-white">SecurityFault</code> and blocks execution.
        </div>
      </section>

      {/* Pre-compression & Ranges */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Asset Optimization</h2>
        
        <div className="space-y-6">
          <div className="border-b border-white/5 pb-4">
            <span className="font-mono text-xs text-aquilia-500 font-bold uppercase">Pre-compressed Assets (.br, .gz)</span>
            <p className="text-sm text-gray-400 mt-1">
              If a client sends an <code className="text-aquilia-300">Accept-Encoding</code> header containing brotli or gzip, the middleware checks if a pre-compiled <code className="text-aquilia-300">.br</code> or <code className="text-aquilia-300">.gz</code> version of the file exists on disk. If found, it serves the compressed file directly, avoiding dynamic CPU overhead.
            </p>
          </div>
          <div className="border-b border-white/5 pb-4">
            <span className="font-mono text-xs text-aquilia-500 font-bold uppercase">HTTP Range Requests</span>
            <p className="text-sm text-gray-400 mt-1">
              Supports partial content requests (HTTP 206), enabling clients to stream video and audio files or resume interrupted file downloads efficiently.
            </p>
          </div>
          <div className="pb-4">
            <span className="font-mono text-xs text-aquilia-500 font-bold uppercase">In-memory Cache</span>
            <p className="text-sm text-gray-400 mt-1">
              Equipped with an LRU (Least Recently Used) cache for small, hot static files. Commonly accessed scripts or icons are served directly from RAM without disk I/O.
            </p>
          </div>
        </div>
      </section>

      {/* Configuration Reference */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Options</h2>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Parameter</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Default</th>
                <th className="py-3 px-4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans text-gray-400 text-xs">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">directories</td>
                <td className="py-3 px-4 font-mono">dict[str, str]</td>
                <td className="py-3 px-4 font-mono">None</td>
                <td className="py-3 px-4">Mapping of URL prefix to folders</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">cache_max_age</td>
                <td className="py-3 px-4 font-mono">int</td>
                <td className="py-3 px-4 font-mono">86400</td>
                <td className="py-3 px-4">Cache-Control max-age in seconds</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">immutable</td>
                <td className="py-3 px-4 font-mono">bool</td>
                <td className="py-3 px-4 font-mono">False</td>
                <td className="py-3 px-4">Adds Cache-Control: immutable directive</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">brotli / gzip</td>
                <td className="py-3 px-4 font-mono">bool</td>
                <td className="py-3 px-4 font-mono">True</td>
                <td className="py-3 px-4">Enable pre-compressed file checks</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">index_file</td>
                <td className="py-3 px-4 font-mono">str | None</td>
                <td className="py-3 px-4 font-mono">"index.html"</td>
                <td className="py-3 px-4">Default file returned for folder paths</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 font-mono text-aquilia-300">html5_history</td>
                <td className="py-3 px-4 font-mono">bool</td>
                <td className="py-3 px-4 font-mono">False</td>
                <td className="py-3 px-4">Fall back to index_file on 404s (for SPA routing)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/built-in" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Built-in Middleware
        </Link>
        <Link to="/docs/middleware/cors" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          CORS <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}