import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Cpu, Layers, Zap, ArrowRight, Code } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                ControllerEngine
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.engine — Route dispatch and execution</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controller.controllerengine">ControllerEngine</DocTerm> orchestrates the route execution pipeline. It coordinates dependency injection, clearance evaluations, pipeline middleware flow execution, parameter binding, response contract casting/molding, and content negotiation.
        </p>
      </div>

      {/* Class definition */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          Class Definition
        </h2>

        <CodeBlock
          code={`class ControllerEngine:
    # Class-level caches shared across instances
    _signature_cache: Dict[Any, inspect.Signature] = {}
    _pipeline_param_cache: Dict[int, set] = {}  # id(callable) -> param names
    _has_lifecycle_hooks: Dict[type, tuple] = {} # class -> (has_on_request, has_on_response)
    _simple_route_cache: Dict[int, bool] = {}    # id(route) -> is_simple
    _clearance_cache: Dict[int, Any] = {}        # id(route) -> merged Clearance or None

    def __init__(
        self,
        factory: ControllerFactory,
        enable_lifecycle: bool = True,
        fault_engine: Optional[Any] = None,
        effect_registry: Optional[Any] = None,
        clearance_engine: Optional[Any] = None,
    ):
        self.factory = factory
        self.enable_lifecycle = enable_lifecycle
        self.fault_engine = fault_engine
        self.effect_registry = effect_registry
        self.clearance_engine = clearance_engine`}
          language="python"
        />
      </section>

      {/* execute() method */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          execute() — The Main Entry Point
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">execute()</code> method is the entrypoint called by ASGI adapters to run a matched route:
        </p>

        <CodeBlock
          code={`async def execute(
    self,
    route: CompiledRoute,
    request: Request,
    path_params: Dict[str, Any],
    container: Container,
) -> Response:`}
          language="python"
        />

        <div className="space-y-4 pt-4">
          {[
            { step: '1', title: 'Fast Path Check', desc: 'Checks if the handler is monkeypatched (e.g. OpenAPI doc routes) and invokes it directly.' },
            { step: '2', title: 'Build Context', desc: 'Initializes RequestCtx with Request, Identity, Session, and request-scoped DI container.' },
            { step: '3', title: 'Enforce Throttling', desc: 'Enforces controller-level and route-level rate limits.' },
            { step: '4', title: 'Body Size Check', desc: 'Validates that the content-length does not exceed class-level max_body_size.' },
            { step: '5', title: 'Flow Pipelines', desc: 'Executes class-level and method-level FlowPipelines (guards, transforms).' },
            { step: '6', title: 'Evaluate Clearance', desc: 'Checks declarative access control permissions against the request.' },
            { step: '7', title: 'Parameter Binding & Contract Casting', desc: 'Parses body parameters, casting and sealing them against the request_contract.' },
            { step: '8', title: 'Post-processing & Negotiation', desc: 'Applies query filtering, ordering, pagination, response contract molding, and Accept-header content negotiation.' }
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

      {/* Parameter binding */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Parameter Binding & Contract Context
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The engine binds path parameters, query parameters, body parameters, and dependencies automatically. If a parameter is typed as a Contract subclass, the engine parses the body and validates it:
        </p>

        <CodeBlock
          code={`# When a parameter is typed as a Contract:
@POST("/")
async def create(self, ctx: RequestCtx, body: UserContract):
    # 'body' receives UserContract.validated_data (dict)
    # If named with _contract or _bp suffix, receives the full Contract instance
    pass`}
          language="python"
        />

        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          During contract validation, the engine creates a <code className="text-aquilia-500">ContractContext</code> wrapping the request container. This context provides lazy resolution via <code className="text-aquilia-500">LazyServiceProxy</code>, allowing contracts to access DI services asynchronously:
        </p>

        <CodeBlock
          code={`# Inside a Contract field validator:
def validate_username(self, value, context):
    # Context contains the DI container lazily resolved via proxy
    db = context["DatabaseService"]
    if db.exists(value):
        raise ValidationError("Username already taken")`}
          language="python"
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/factory" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>ControllerFactory</span>
        </Link>
        <Link to="/docs/controllers/compiler" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>ControllerCompiler</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}