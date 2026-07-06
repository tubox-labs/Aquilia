import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Database } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DataStructuresPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Database className="w-4 h-4" />
          Request / Data Structures
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Data Structures
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides performance-optimized, purpose-built data structures in <code className="text-aquilia-500">aquilia._datastructures</code> for request parsing:
          <code className="text-aquilia-500"> MultiDict</code> for multi-value dictionaries, <code className="text-aquilia-500">Headers</code> for case-insensitive header access, and
          <code className="text-aquilia-500"> URL</code> for immutable URL component parsing and manipulation.
        </p>
      </div>

      {/* MultiDict */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>MultiDict</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A dictionary that supports multiple values per key. Implements <code className="text-aquilia-500">MutableMapping</code>. Used internally for query parameters and form data where keys can repeat (e.g. <code className="text-aquilia-500">?tag=python&tag=async</code>).
        </p>
        <CodeBlock language="python" filename="multidict.py">{`from aquilia._datastructures import MultiDict

# Initialize from list of tuples
params = MultiDict([
    ("tag", "python"),
    ("tag", "async"),
    ("page", "1"),
])

# Standard dict access (returns FIRST value for key)
params["tag"]                  # → "python"
params.get("tag")              # → "python"

# Multi-value access
params.get_all("tag")          # → ["python", "async"]

# Add values (doesn't replace)
params.add("tag", "web")
params.get_all("tag")          # → ["python", "async", "web"]

# Convert to plain dict (first value per key)
params.to_dict()               # → {"tag": "python", "page": "1"}`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>API Reference</h3>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Method</th>
                <th className="text-left py-3 px-4 font-semibold">Returns</th>
                <th className="text-left py-3 px-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { m: 'get(key, default)', t: 'Any', d: 'Returns the first value for key, or default.' },
                { m: 'get_all(key)', t: 'List[str]', d: 'Returns all values for key as a list.' },
                { m: 'add(key, value)', t: 'None', d: 'Appends value to the key\'s list.' },
                { m: 'items_list()', t: 'List[Tuple[str, str]]', d: 'Returns all items as a flat list of tuples.' },
                { m: 'to_dict(multi=False)', t: 'Dict', d: 'Converts to a standard dict.' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.m}</code></td>
                  <td className="py-3 px-4 font-mono text-xs">{row.t}</td>
                  <td className="py-3 px-4 text-xs">{row.d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Headers */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Headers</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A case-insensitive header container built as a <code className="text-aquilia-500">@dataclass</code>. Eagerly processes and decodes raw header bytes from the ASGI scope while preserving original naming.
        </p>
        <CodeBlock language="python" filename="headers.py">{`from aquilia._datastructures import Headers

headers = Headers(raw=[
    (b"content-type", b"application/json"),
    (b"Authorization", b"Bearer abc123"),
])

# Case-insensitive lookup
headers.get("Content-Type")  # → "application/json"
headers.has("authorization")  # → True`}</CodeBlock>
      </section>

      {/* URL */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>URL</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          An immutable parsed URL component representation supporting modifications via copies.
        </p>
        <CodeBlock language="python" filename="url.py">{`from aquilia._datastructures import URL

url = URL.parse("https://api.example.com/users?page=2")
url.host    # → "api.example.com"
url.path    # → "/users"

# Immutable replacement pattern
url2 = url.replace(path="/articles")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/request-response/response" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Response</span>
        </Link>
        <Link to="/docs/request-response/uploads" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>File Uploads</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}