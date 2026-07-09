import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function FlowPipelines() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Zap className="w-4 h-4" />
          <span>EFFECTS &amp; FLOW / FLOW PIPELINES</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Flow Pipelines
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          The <DocTerm id="effects.FlowPipeline">FlowPipeline</DocTerm> class compiles and executes a sequence of execution nodes under strict priority bands. It acts as the backbone of request execution and route-specific middleware, orchestrating capability acquisition and safe resource release.
        </p>
      </div>

      {/* Anatomy of a Pipeline */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Pipeline Anatomy &amp; Execution</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            A pipeline structures your request processing into discrete, composable phases:
          </p>
          <div className="border-l-2 border-aquilia-500/20 pl-6 space-y-4 py-1">
            <p>
              <strong className="font-semibold text-aquilia-500">1. Guards:</strong> Run first to perform security checks, access control, and rate limiting. If a guard returns <code className="text-white">False</code> or a <code className="text-white">Response</code>, execution short-circuits.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">2. Transforms:</strong> Modify request parameters, deserialize payloads, and thread state changes into the context.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">3. Effect Acquisition:</strong> Automatically lease resource handles from the registry for any capabilities required by subsequent nodes.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">4. Handler:</strong> Executes core business logic. A pipeline can have exactly one primary handler.
            </p>
            <p>
              <strong className="font-semibold text-aquilia-500">5. Hooks (Post-Handler):</strong> Execute post-processing, logging, metrics collection, and can optionally modify the handler's return value.
            </p>
          </div>
        </div>
      </section>

      {/* Execution Priority Bands */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Priority Bands</h2>
        <p className={`mb-6 font-light leading-relaxed ${textMuted}`}>
          When nodes are added to a pipeline, they are sorted first by their node type band, and then by their individual numeric priority. Aquilia defines standard priority bands as constant integers:
        </p>

        <div className={`border-t border-b ${borderMuted} divide-y ${borderMuted} mb-8`}>
          {[
            ['PRIORITY_CRITICAL', '10', 'Security checks, CORS validation, global rate limiting.'],
            ['PRIORITY_AUTH', '20', 'Authentication guards, session lookups, permission validations.'],
            ['PRIORITY_VALIDATE', '30', 'Input validation schema checks (Blueprints).'],
            ['PRIORITY_TRANSFORM', '40', 'Payload transformations, parameter binding.'],
            ['PRIORITY_DEFAULT', '50', 'Primary request handler execution.'],
            ['PRIORITY_ENRICH', '60', 'Response enrichment, wrapping structures.'],
            ['PRIORITY_LOG', '70', 'Audit log generation, performance metrics emission.'],
            ['PRIORITY_CLEANUP', '80', 'Post-request teardowns, resource recycling.'],
          ].map(([constant, priority, desc]) => (
            <div key={constant} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-2 text-sm">
              <div className="font-mono font-bold text-aquilia-400">{constant}</div>
              <div className="font-mono text-zinc-500 md:w-20">Priority {priority}</div>
              <div className={`font-light md:w-1/2 ${textMuted}`}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* API Reference */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">API Builder Reference</h2>
        
        <div className="space-y-6">
          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              pipeline(name: str = "pipeline", *, timeout: float | None = None) -&gt; FlowPipeline
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Helper function that instantiates a new <DocTerm id="effects.FlowPipeline">FlowPipeline</DocTerm> builder.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              .guard(node, *, name: str | None = None, priority: int = 20, effects: list[str] | None = None, condition: Callable | None = None)
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Adds a guard node to the pipeline. Guards return <code className="text-white">True</code> to proceed, or <code className="text-white">False</code>/a <code className="text-white">Response</code> to short-circuit.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              .transform(node, *, name: str | None = None, priority: int = 40, effects: list[str] | None = None)
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Adds a transformation node that runs after guards. Modifies or enriches context variables.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              .handler(node, *, name: str | None = None, priority: int = 50, effects: list[str] | None = None)
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Sets the main execution handler. Receives the context and yields the core response value.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              .hook(node, *, name: str | None = None, priority: int = 70, effects: list[str] | None = None)
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Registers post-execution hooks to log telemetry or adjust the resolved response.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              .compose(*other: FlowPipeline) -&gt; FlowPipeline
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Merges nodes from multiple pipelines, returning a new pipeline with all nodes sorted by priority. Can also be invoked using the <code className="text-white">|</code> operator.
            </p>
          </div>

          <div className="pb-6">
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              from_pipeline_list(nodes: Sequence[Any], *, name: str) -&gt; FlowPipeline
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Utility converting controller pipeline lists into a unified <DocTerm id="effects.FlowPipeline">FlowPipeline</DocTerm>. Automatically materializes zero-argument factory functions.
            </p>
          </div>
        </div>
      </section>

      {/* Code Examples */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Building &amp; Executing Pipelines</h2>
        <p className={`mb-6 font-light leading-relaxed ${textMuted}`}>
          Below is a detailed guide showing how to create a pipeline manually, compose it with operators, and trigger execution within a request context.
        </p>

        <CodeBlock language="python" filename="pipeline_demo.py" highlightLines={[17, 23, 29, 32, 33]}>{`from aquilia.flow import pipeline, FlowContext, requires
from aquilia.response import Response

# 1. Define nodes
async def check_api_key(ctx: FlowContext):
    api_key = ctx.request.headers.get("X-API-Key")
    if api_key != "secret-token":
        # Returning a Response short-circuits execution
        return Response.json({"error": "Unauthorized"}, status=401)
    return True

async def sanitize_payload(ctx: FlowContext):
    # Transforms modify state dictionaries in context
    if "email" in ctx.state:
        ctx.state["email"] = ctx.state["email"].strip().lower()

@requires("DBTx")
async def save_record(ctx: FlowContext):
    # Automatically acquired DB connection
    db = ctx.get_effect("DBTx")
    await db.execute(
        "INSERT INTO leads (email) VALUES (?)", 
        (ctx.state["email"],)
    )
    return {"status": "created"}

# 2. Build Pipeline
lead_pipeline = (
    pipeline("create_lead")
    .guard(check_api_key, priority=10)
    .transform(sanitize_payload)
    .handler(save_record)
)

# 3. Execute Pipeline
# registry contains registered EffectProviders (e.g. DBTxProvider)
ctx = FlowContext(request=request, state={"email": " USER@EXAMPLE.com "})
result = await lead_pipeline.execute(ctx, effect_registry=registry)

if result.is_success:
    print(f"Success! Response: {result.value}")
elif result.is_guarded:
    print(f"Guarded (Short-circuited): {result.value}")`}</CodeBlock>
      </section>

      {/* Composition and Controller Pipelines */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Controller Integrations &amp; Composition</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            You can compose pipelines using the bitwise OR (<code className="text-white">|</code>) operator. This allows you to define reusable segments (e.g., auth checks) and merge them with route-specific handlers.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/users.py" highlightLines={[14, 21, 23]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import pipeline, requires

# Reusable security segment
auth_pipeline = pipeline("auth_guard").guard(verify_jwt, priority=10)

class UserController(Controller):
    # Controller routes accept pipeline lists
    @POST(
        "/users",
        pipeline=[
            auth_pipeline,         # Reusable pipeline
            validate_user_schema,  # Plain function (wraps as guard)
        ]
    )
    @requires("DBTx")
    async def create_user(self, ctx: RequestCtx) -> dict:
        # Executes within the compiled pipeline context
        db = ctx.get_effect("DBTx")
        ...
        return {"status": "ok"}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/subsystem/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/subsystem/context-nodes" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Flow Context &amp; Nodes <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
