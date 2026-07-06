import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Hammer, Layers, Code, AlertCircle, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersCompiler() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Hammer className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                ControllerCompiler
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.compiler — Compile controllers to executable routes</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controllers.controllercompiler">ControllerCompiler</DocTerm> class scans controller classes, parses path chevrons, validates parameter types, evaluates route specificity, and identifies route conflicts.
        </p>
      </div>

      {/* Compiled Classes */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Data Structures
        </h2>

        <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>CompiledRoute</h3>
        <CodeBlock
          code={`@dataclass
class CompiledRoute:
    controller_class: type                # Controller class
    controller_metadata: ControllerMetadata   # Class metadata
    route_metadata: RouteMetadata            # Method metadata
    compiled_pattern: CompiledPattern        # Compiled regex + castors
    full_path: str                           # prefix + path
    http_method: str                         # GET, POST, etc.
    specificity: int                         # Priority score
    app_name: Optional[str] = None           # Fault namespace`}
          language="python"
        />
      </section>

      {/* Specificity */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          Route Specificity
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Each route is evaluated to assign a specificity score. Routes are evaluated from highest score to lowest:
        </p>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Segment Type</th>
                <th className="text-left px-4 py-3 font-semibold">Score</th>
                <th className="text-left px-4 py-3 font-semibold">Example</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['Static segment', '+100', '/users/active (Score: 200)'],
                ['Typed parameter', '+50', '/users/«id:int» (Score: 150)'],
                ['Untyped parameter', '+25', '/users/«id» (Score: 125)'],
                ['Wildcard', '+1', '/users/* (Score: 101)']
              ].map(([type_, score, example], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs">{type_}</td>
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{score}</td>
                  <td className="px-4 py-2 text-xs">{example}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Conflict Validation */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertCircle className="w-5 h-5 text-aquilia-400" />
          Conflict Detection
        </h2>
        <CodeBlock
          code={`# Validates route tree for overlaps:
conflicts = compiler.validate_route_tree(compiled_controllers)`}
          language="python"
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/engine" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>ControllerEngine</span>
        </Link>
        <Link to="/docs/controllers/router" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>ControllerRouter</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}