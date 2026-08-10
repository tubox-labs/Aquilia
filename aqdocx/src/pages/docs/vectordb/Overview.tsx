import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Boxes, Cpu, Layers, Shield, Zap } from 'lucide-react'

const features = [
  {
    icon: <Layers className="w-5 h-5" />,
    title: 'Declarative models',
    desc: 'Declare a collection as a class with Annotated field metadata. Key, Text, Dimension and Payload replace hand-written index wiring.',
  },
  {
    icon: <Boxes className="w-5 h-5" />,
    title: 'Chainable queries',
    desc: 'filter(), exclude(), limit(), top() and search() compose the same way the SQL ORM does, and every method clones instead of mutating.',
  },
  {
    icon: <Zap className="w-5 h-5" />,
    title: 'Embedders and chunking',
    desc: 'Text embeds on write and on query. Long documents split into chunks that keep a parent key, so retrieval stays paragraph-sized.',
  },
  {
    icon: <Cpu className="w-5 h-5" />,
    title: 'Optional GPU',
    desc: 'A per-store policy decides whether the GPU index is used, with an explicit fallback rule. A CPU-only build never touches a GPU symbol.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Structured faults',
    desc: 'Every failure is a Fault subclass in the vectordb domain, carrying a stable code — never a raw ValueError.',
  },
  {
    icon: <Layers className="w-5 h-5" />,
    title: 'SQL interop',
    desc: 'Link a vector record to an ORM row, resolve hits back to rows, and mirror a table into a collection. The dependency stays one-way.',
  },
]

export function VectorDBOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Boxes className="w-4 h-4 animate-pulse" />
          Vector Database / Overview
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          AquilaVectorDB
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          New in 1.4.0b3. <code className="text-aquilia-500">aquilia.vectordb</code> is a typed,
          ORM-shaped layer over the embedded <code className="text-aquilia-500">elips</code> vector
          database. You declare a collection as a class, and similarity search, metadata filtering,
          embedding, chunking and compaction all become async calls on a manager.
        </p>
      </div>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          Quick Example
        </h2>
        <p className={`text-sm mb-4 ${subtleText}`}>
          A model needs a key, a vector dimension, and — if you want text search — one text field.
          Everything else is payload used for filtering.
        </p>
        <CodeBlock language="python" highlightLines={[5, 6, 7, 8, 11, 12, 18, 21]}>{`from typing import Annotated
from aquilia.vectordb import VectorModel, Key, Text, Payload, Dimension

class Document(VectorModel):
    key:    Annotated[str, Key()]
    body:   Annotated[str, Text()]
    vector: Annotated[list[float], Dimension(384)]
    source: Annotated[str, Payload()]

    class Meta:
        collection = "documents"
        store = "default"

# Write. The vector is embedded from \`body\` because the field is empty
# and the store has an embedder.
await Document(key="doc:1", body="Aquilia release notes", source="docs").save()

# Search. Returns Hit objects ordered by descending score.
hits = await Document.vectors.search("release notes", limit=10)

for hit in hits:
    print(hit.score, hit.source, hit.body)   # Hit proxies to the record`}</CodeBlock>
      </section>

      {/* Install */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Installation
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">elips</code> is an optional extra and requires Python
          3.11 or newer. Importing <code className="text-aquilia-500">aquilia.vectordb</code> without
          it succeeds — the fault surfaces at first <em>use</em>, as{' '}
          <code className="text-aquilia-500">VectorNotInstalledFault</code> carrying the install
          hint. That is deliberate: <code className="text-aquilia-500">aquilia</code> still imports
          cleanly on an install that never asked for vector support.
        </p>
        <CodeBlock language="bash">{`pip install 'aquilia[vectordb]'

# Confirm the driver and the declared stores agree
aq vectordb status`}</CodeBlock>
        <div className={`mt-6 rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
          <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Catch the missing driver before deploy</h3>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <code className="text-aquilia-500">aq doctor</code> and{' '}
            <code className="text-aquilia-500">aq validate</code> run the{' '}
            <code className="text-aquilia-500">vectordb.driver</code> check, which reports an error
            when a workspace declares vector stores on an install without{' '}
            <code className="text-aquilia-500">elips</code>. Without it the first symptom is a fault
            at request time, long after the deploy.
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Subsystem Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{feature.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Declaring a store
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Stores are declared on the workspace. <code className="text-aquilia-500">stores</code> maps
          an alias to that store&apos;s settings, and a model picks its store by alias through{' '}
          <code className="text-aquilia-500">Meta.store</code> — defaulting to{' '}
          <code className="text-aquilia-500">&quot;default&quot;</code>.
        </p>
        <CodeBlock language="python" highlightLines={[6, 7, 8, 9, 10, 11, 12, 13]}>{`# workspace.py
from aquilia.workspace import Workspace
from aquilia.vectordb import GpuOptions

workspace = (
    Workspace("search-api")
    .vectordb(
        path="./.aquilia/vectors",
        stores={
            "default": {"dimension": 384, "metric": "cosine", "index": "hnsw"},
            "images":  {"dimension": 512, "metric": "l2"},
        },
        gpu=GpuOptions(policy="prefer_gpu", fallback="warn"),
    )
)`}</CodeBlock>
        <p className={`mt-4 mb-4 text-sm ${subtleText}`}>
          <code className="text-aquilia-500">.vectordb()</code> is shorthand for{' '}
          <code className="text-aquilia-500">integrate(VectorDatabaseIntegration(...))</code>. The
          equivalent typed form, and the <code className="text-aquilia-500">aquilia.config.py</code>{' '}
          block, both produce the same config:
        </p>
        <CodeBlock language="python">{`from aquilia.integrations import VectorDatabaseIntegration
from aquilia.pyconfig import AquilaConfig

workspace.integrate(VectorDatabaseIntegration(
    path="./.aquilia/vectors",
    stores={"default": {"dimension": 384, "metric": "cosine"}},
))

# ...or declaratively, where the single-store shorthand applies
class BaseEnv(AquilaConfig):
    class vectordb(AquilaConfig.VectorDB):
        enabled   = True
        path      = "./.aquilia/vectors"
        dimension = 384
        metric    = "cosine"`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          <code className="text-aquilia-500">path</code> is a directory prefix, not a URL — elips is
          embedded, so a store is a local directory holding one writer lock. Each alias gets its own
          subdirectory unless it declares an absolute{' '}
          <code className="text-aquilia-500">path</code>. Outer{' '}
          <code className="text-aquilia-500">dimension</code>,{' '}
          <code className="text-aquilia-500">metric</code>,{' '}
          <code className="text-aquilia-500">gpu</code> and{' '}
          <code className="text-aquilia-500">embedder</code> values are defaults: a store that sets
          them explicitly wins. Declaring no{' '}
          <code className="text-aquilia-500">stores</code> at all but setting{' '}
          <code className="text-aquilia-500">dimension</code> builds one default store from the outer
          values.
        </p>
        <div className={`mt-6 rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
          <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Disabled unless declared</h3>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <code className="text-aquilia-500">AquilaConfig.VectorDB.enabled</code> defaults to{' '}
            <code className="text-aquilia-500">False</code>, and so does{' '}
            <code className="text-aquilia-500">ConfigLoader.get_vectordb_config()</code>. An absent
            block never makes the subsystem try to load the extension — which is what keeps the extra
            genuinely optional.
          </p>
        </div>
      </section>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          How it fits together
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-52">Layer</th>
                <th className="text-left py-4 px-6 font-semibold">Responsibility</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['VectorModel', 'Declares fields and Meta. Instances save(), delete_instance() and refresh().'],
                ['VectorManager', 'Model.vectors — search, get, add, remove, count, health, quantize, rebuild.'],
                ['VectorQuery', 'Chainable, cloning query. Compiles filters into a native predicate plus residuals.'],
                ['VectorRegistry', 'Resolves the engine for a model from its store alias.'],
                ['VectorEngine', 'Wraps elips. Owns the writer lock, read/write dispatch and pooling.'],
                ['VectorDBSubsystem', 'Boots stores with the rest of the app and reports health.'],
              ].map(([name, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{name}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={`mt-4 text-sm ${subtleText}`}>
          The dependency runs one way: vectordb may import{' '}
          <code className="text-aquilia-500">aquilia.models</code>, the SQL ORM never imports
          vectordb. The interop edge is lazy for exactly that reason.
        </p>
      </section>

      {/* Limitations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Limitations
        </h2>
        <ul className={`space-y-2 text-sm list-disc pl-5 ${subtleText}`}>
          <li>Requires Python 3.11+, so it is unavailable on a 3.10 install even with the extra.</li>
          <li>
            <code className="text-aquilia-500">elips</code> is embedded and single-writer. One process
            holds the writer lock per store path; a second writer waits rather than corrupting.
          </li>
          <li>
            An unfiltered <code className="text-aquilia-500">delete()</code> is refused with{' '}
            <code className="text-aquilia-500">VectorQueryFault</code> — emptying a whole collection
            is almost never what a chained call meant. Add a filter.
          </li>
          <li>
            Compressed vectors make distances estimates. Check{' '}
            <code className="text-aquilia-500">hit.approximate</code> before thresholding on score.
          </li>
        </ul>
      </section>


      <NextSteps />
    </div>
  )
}
