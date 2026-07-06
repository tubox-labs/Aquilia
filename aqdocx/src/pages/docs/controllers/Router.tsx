import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Navigation, Layers, Code, ArrowRight, Search, Link2 } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersRouter() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Navigation className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                ControllerRouter
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.router — Two-tier URL matching engine</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controllers.controllerrouter">ControllerRouter</DocTerm> matches incoming requests to compiled routes. It employs a two-tier matching strategy for maximum request throughput.
        </p>
      </div>

      {/* Architecture */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Two-Tier Architecture
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Tier 1: Static Routes</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Uses a direct dictionary key lookup offering <strong>O(1)</strong> matching performance. Routes without parameters (e.g. <code className="text-aquilia-500">GET /health</code>) bypass regular expressions entirely.
            </p>
          </div>

          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Tier 2: Dynamic Routes</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Uses compiled regex matching for routes with path chevrons (e.g. <code className="text-aquilia-500">GET /users/«id:int»</code>). Specificity sorting guarantees the correct route takes precedence.
            </p>
          </div>
        </div>
      </section>

      {/* Class definition */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          Class Definition
        </h2>

        <CodeBlock
          code={`class ControllerRouter:
    def __init__(self):
        self.compiled_controllers: List[CompiledController] = []
        self.routes_by_method: Dict[str, List[CompiledRoute]] = {}
        self.matcher = PatternMatcher()
        self._initialized = False

        # Fast-path indexes
        self._static_routes: Dict[str, Dict[str, Tuple]] = {}
        self._dynamic_routes: Dict[str, List[Tuple]] = {}`}
          language="python"
        />
      </section>

      {/* ControllerRouteMatch */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Search className="w-5 h-5 text-aquilia-400" />
          ControllerRouteMatch
        </h2>

        <CodeBlock
          code={`@dataclass
class ControllerRouteMatch:
    route: CompiledRoute       # Matched route
    params: Dict[str, Any]     # Type-cast path params
    query: Dict[str, Any]      # Validated query params`}
          language="python"
        />
      </section>

      {/* reverse URL */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Link2 className="w-5 h-5 text-aquilia-400" />
          Reverse URL Generation
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Generate paths dynamically using route names:
        </p>
        <CodeBlock
          code={`# In handler:
url = router.url_for("UsersController.get_user", id=42)
# → "/users/42"`}
          language="python"
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/compiler" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>ControllerCompiler</span>
        </Link>
        <Link to="/docs/controllers/openapi" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>OpenAPI Generation</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}