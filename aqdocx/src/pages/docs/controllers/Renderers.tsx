import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Layers, ArrowLeft, Zap, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersRenderers() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Controllers
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Content Negotiation & Renderers
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia handles content negotiation dynamically by parsing the client's <code className="text-aquilia-500">Accept</code> header quality factors and dispatching response payloads to pluggable renderers.
        </p>
      </div>

      {/* Built-in Renderers */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Built-in Renderers
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia ships with a suite of highly-optimized, format-specific renderers:
        </p>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left py-3 px-4 font-semibold">Renderer Class</th>
                <th className="text-left py-3 px-4 font-semibold">Media Type</th>
                <th className="text-left py-3 px-4 font-semibold">Format Suffix</th>
                <th className="text-left py-3 px-4 font-semibold">Config Options</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                { name: 'JSONRenderer', type: 'application/json', suffix: 'json', opts: 'indent: int | None, ensure_ascii: bool' },
                { name: 'XMLRenderer', type: 'application/xml', suffix: 'xml', opts: 'root_tag: str, item_tag: str' },
                { name: 'YAMLRenderer', type: 'application/x-yaml', suffix: 'yaml', opts: 'None (uses pyyaml if installed, falls back to manual)' },
                { name: 'PlainTextRenderer', type: 'text/plain', suffix: 'txt', opts: 'None' },
                { name: 'HTMLRenderer', type: 'text/html', suffix: 'html', opts: 'None' },
                { name: 'MessagePackRenderer', type: 'application/msgpack', suffix: 'msgpack', opts: 'None' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-aquilia-500 font-semibold">{row.name}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.type}</td>
                  <td className="py-3 px-4 font-mono text-xs">{row.suffix}</td>
                  <td className="py-3 px-4 text-xs">{row.opts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Pluggable Renderers usage */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Declaring Renderers</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Renderers are registered on a Controller class or overridden for individual route handlers:
        </p>
        <CodeBlock
          language="python"
          filename="renderers_example.py"
          code={`from aquilia import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer, YAMLRenderer

class ProductsController(Controller):
    prefix = "/products"
    renderer_classes = [JSONRenderer, XMLRenderer, YAMLRenderer]

    @GET("/")
    async def list_products(self, ctx):
        # The engine picks the renderer dynamically matching Accept q-factors
        return {"products": ["Widget", "Tool"]}`}
        />
      </section>

      {/* Custom Renderers */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Authoring Custom Renderers
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          To build a custom format serializer, subclass <code className="text-aquilia-500">BaseRenderer</code> and implement the <code className="text-aquilia-500">render</code> method:
        </p>
        <CodeBlock
          language="python"
          filename="custom_renderer.py"
          code={`from aquilia.controller.renderers import BaseRenderer

class CSVRenderer(BaseRenderer):
    media_type = "text/csv"
    format_suffix = "csv"
    charset = "utf-8"

    def render(self, data, *, request=None, response_status=200, response_headers=None):
        if not isinstance(data, list):
            data = [data]
        # Direct CSV formatting
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        if data:
            writer.writerow(data[0].keys()) # Header
            for row in data:
                writer.writerow(row.values())
        return output.getvalue()`}
        />
      </section>

      {/* Negotiation Priority */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Negotiation Resolution Order</h2>
        <ol className={`list-decimal pl-6 space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Query parameter override:</strong> e.g., <code className="text-aquilia-500">?format=xml</code> or <code className="text-aquilia-500">?format=yaml</code></li>
          <li><strong>Accept Header quality factors:</strong> Parsed quality parameters (e.g. <code className="text-aquilia-500">Accept: application/xml;q=0.9, application/json;q=0.8</code>)</li>
          <li><strong>Default:</strong> Resolves to the first renderer defined in <code className="text-aquilia-500">renderer_classes</code> (typically JSON)</li>
        </ol>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Controllers Overview</span>
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
