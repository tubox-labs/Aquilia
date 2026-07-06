import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { FileText, Layers, Settings, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersOpenAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                OpenAPI Generation
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.openapi — OpenAPI 3.1.0 spec from controller metadata</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia automatically generates a complete <strong>OpenAPI 3.1.0</strong> specification from compiled controller routes, integrating Swagger UI and ReDoc rendering out-of-the-box.
        </p>
      </div>

      {/* OpenAPIConfig */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          OpenAPIConfig
        </h2>

        <CodeBlock
          code={`@dataclass
class OpenAPIConfig:
    title: str = "Aquilia API"
    version: str = "1.0.0"
    description: str = ""
    docs_path: str = "/docs"              # Swagger UI path
    openapi_json_path: str = "/openapi.json"  # JSON spec path
    redoc_path: str = "/redoc"            # ReDoc path
    enabled: bool = True`}
          language="python"
        />
      </section>

      {/* Type Mapping */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Python → JSON Schema Mapping
        </h2>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Python Type</th>
                <th className="text-left px-4 py-3 font-semibold">JSON Schema</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['str', '{"type": "string"}'],
                ['int', '{"type": "integer"}'],
                ['float', '{"type": "number", "format": "double"}'],
                ['bool', '{"type": "boolean"}'],
                ['None', '{"type": "null"}'],
                ['List[X]', '{"type": "array", "items": {X schema}}'],
                ['Dict[str, X]', '{"type": "object", "additionalProperties": {X schema}}']
              ].map(([python, json], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{python}</td>
                  <td className="px-4 py-2 font-mono text-xs">{json}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Swagger UI & ReDoc */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          Swagger UI & ReDoc
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Swagger UI</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Available at <code className="text-aquilia-500">/docs</code>, Swagger UI provides an interactive playground for exploring and testing endpoints directly from the browser.
            </p>
          </div>

          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>ReDoc</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Available at <code className="text-aquilia-500">/redoc</code>, ReDoc provides a clean, three-panel documentation layout optimized for reference and readability.
            </p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/router" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>ControllerRouter</span>
        </Link>
        <Link to="/docs/config/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>Configuration Overview</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}