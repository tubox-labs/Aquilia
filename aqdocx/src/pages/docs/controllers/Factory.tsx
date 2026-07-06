import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Factory, Layers, Code, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersFactory() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Factory className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                ControllerFactory
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.factory — DI-powered controller instantiation</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controllers.controllerfactory">ControllerFactory</DocTerm> creates controller instances with full dependency injection support. It resolves constructor parameters and enforces singleton vs per-request scoping.
        </p>
      </div>

      {/* InstantiationMode */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          InstantiationMode Enum
        </h2>

        <CodeBlock
          code={`class InstantiationMode(str, Enum):
    PER_REQUEST = "per_request"  # New instance per HTTP request
    SINGLETON = "singleton"     # Single shared instance`}
          language="python"
        />
      </section>

      {/* ControllerFactory Class */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          ControllerFactory Class
        </h2>

        <CodeBlock
          code={`class ControllerFactory:
    # Class-level caches for constructor analysis
    _ctor_info_cache: Dict[Type, Any] = {}

    def __init__(self, app_container: Optional[Any] = None):
        self.app_container = app_container
        self._singletons: Dict[Type, Any] = {}
        self._startup_called: set = set()`}
          language="python"
        />

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Attribute</th>
                <th className="text-left px-4 py-3 font-semibold">Type</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['app_container', 'Container | None', 'Application-scope DI container.'],
                ['_singletons', 'dict', 'Cache of instantiated singletons.'],
                ['_startup_called', 'set', 'Set of initialized singleton classes.']
              ].map(([attr, type_, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{attr}</td>
                  <td className="px-4 py-2 font-mono text-xs">{type_}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Resolution Pipeline */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ArrowRight className="w-5 h-5 text-aquilia-400" />
          DI Resolution Pipeline
        </h2>

        <div className="space-y-4">
          {[
            { step: '1', title: 'Analyze Constructor', desc: 'Checks MRO and caches signature details in class-level cache to bypass inspect overhead.' },
            { step: '2', title: 'Scope Verification', desc: 'Validates that singleton controllers do not inject request-scoped dependencies (prevents memory leaks).' },
            { step: '3', title: 'Parameter Binding', desc: 'Resolves parameters from the DI container using type hints, annotations (Annotated[T, Inject(tag=...)]), or defaults.' }
          ].map(({ step, title, desc }) => (
            <div key={step} className="flex items-start gap-4">
              <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-aquilia-500/10 text-aquilia-500 flex items-center justify-center text-sm font-bold">{step}</span>
              <div>
                <h4 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h4>
                <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/request-ctx" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>RequestCtx</span>
        </Link>
        <Link to="/docs/controllers/engine" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>ControllerEngine</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}