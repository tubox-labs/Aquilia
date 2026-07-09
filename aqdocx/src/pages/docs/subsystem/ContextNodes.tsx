import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function FlowContextNodes() {
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
          <span>EFFECTS &amp; FLOW / CONTEXT &amp; NODES</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Flow Context &amp; Nodes
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Deep-dive into the data carriers and execution units of the Flow system. Learn how <DocTerm id="effects.FlowContext">FlowContext</DocTerm> threads state and resources through <DocTerm id="effects.FlowNode">FlowNode</DocTerm> pipelines, returning detailed execution results.
        </p>
      </div>

      {/* FlowContext */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">FlowContext Anatomy</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <DocTerm id="effects.FlowContext">FlowContext</DocTerm> threads execution state, request parameters, dependency containers, and acquired effect resources through every stage of the pipeline.
          </p>
        </div>

        <div className={`border-t border-b ${borderMuted} divide-y ${borderMuted} mb-8`}>
          {[
            ['request', 'Any', 'The raw ASGI/HTTP request context (e.g. RequestCtx).'],
            ['container', 'Any', 'The request-scoped dependency injection container.'],
            ['state', 'dict[str, Any]', 'Arbitrary mutable key-value storage used by transforms and controllers.'],
            ['identity', 'Any', 'The authenticated principal, typically resolved and set by auth guards.'],
            ['session', 'Any', 'Active session state proxy if session middleware is active.'],
            ['effects', 'dict[str, Any]', 'Acquired capability resource handles (e.g. database transaction, cache client).'],
            ['metadata', 'dict[str, Any]', 'Telemetry logs tracking timings, executed node traces, and acquired effects.'],
          ].map(([attr, type, desc]) => (
            <div key={attr} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-2 text-sm">
              <div className="font-mono font-bold text-aquilia-400">{attr}</div>
              <div className="font-mono text-zinc-500 md:w-32">{type}</div>
              <div className={`font-light md:w-1/2 ${textMuted}`}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FlowContext Methods */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Context Method Reference</h2>
        
        <div className="space-y-6">
          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              get_effect(name: str) -&gt; Any
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Retrieves an acquired capability resource. If the resource is not active, it throws an <code className="text-white">EffectNotAcquiredFault</code>. Supports type overloading for standard effects.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              has_effect(name: str) -&gt; bool
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Returns whether the specified effect capability is currently acquired and bound to the context.
            </p>
          </div>

          <div className={`pb-6 border-b ${borderMuted}`}>
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              add_cleanup(callback: Callable[[], Awaitable[None]])
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Registers an asynchronous teardown callback. Cleanup actions are executed in Last-In-First-Out (LIFO) order during pipeline disposal.
            </p>
          </div>

          <div className="pb-6">
            <h3 className={`text-lg font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              dispose()
            </h3>
            <p className={`font-light text-sm mb-3 ${textMuted}`}>
              Drives the execution of all registered cleanup callbacks, ensuring database transactions roll back or temp files clean up on pipeline failure.
            </p>
          </div>
        </div>
      </section>

      {/* FlowNodes & Types */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Flow Nodes &amp; Node Types</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            A <DocTerm id="effects.FlowNode">FlowNode</DocTerm> represents a single callable unit in a pipeline. The pipeline compiler parses callables, extracts decorator metadata, and maps them to concrete nodes:
          </p>
        </div>

        <div className={`border-t border-b ${borderMuted} divide-y ${borderMuted} mb-8`}>
          {[
            ['FlowNodeType.GUARD', 'guard', 'Short-circuits execution. Used for authentication and validation.'],
            ['FlowNodeType.TRANSFORM', 'transform', 'Modifies request properties or updates context state values.'],
            ['FlowNodeType.HANDLER', 'handler', 'The core business logic method (usually a controller action).'],
            ['FlowNodeType.HOOK', 'hook', 'Post-processing operations that run after the main handler.'],
            ['FlowNodeType.EFFECT', 'effect', 'Custom node managing targeted capability resources.'],
            ['FlowNodeType.MIDDLEWARE', 'middleware', 'Wraps the execution path of the entire pipeline.'],
          ].map(([enumVal, stringVal, desc]) => (
            <div key={enumVal} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-2 text-sm">
              <div className="font-mono font-bold text-aquilia-400">{enumVal}</div>
              <div className="font-mono text-zinc-500 md:w-32">"{stringVal}"</div>
              <div className={`font-light md:w-1/2 ${textMuted}`}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* requires Decorator */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Declaring Requirements with @requires</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <DocTerm id="effects.requires">@requires</DocTerm> decorator binds capability metadata directly onto the decorated callable function. When a pipeline executes, it crawls the node list, inspects the callables for the <code className="text-white">__flow_effects__</code> property, and triggers batch acquisition before the handler runs.
          </p>
        </div>

        <CodeBlock language="python" filename="requires_decorator.py" highlightLines={[1, 5, 8]}>{`from aquilia.flow import requires, FlowContext

@requires("DBTx", "Cache")
async def process_payment(ctx: FlowContext):
    # Retrieve capabilities safely
    db = ctx.get_effect("DBTx")
    cache = ctx.get_effect("Cache")
    
    # execute database queries
    user_id = ctx.state["user_id"]
    balance = await db.fetch_val("SELECT balance FROM accounts WHERE user_id = ?", (user_id,))
    ...
    return {"balance": balance}`}</CodeBlock>
      </section>

      {/* FlowResult & FlowStatus */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">FlowResult &amp; Execution Outcomes</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            Triggering <code className="text-white">execute()</code> returns a structured <DocTerm id="effects.FlowResult">FlowResult</DocTerm> instance representing the final state:
          </p>
        </div>

        <div className={`border-t border-b ${borderMuted} divide-y ${borderMuted} mb-8`}>
          {[
            ['FlowStatus.SUCCESS', '"success"', 'Completed successfully. value contains the handler output.'],
            ['FlowStatus.GUARDED', '"guarded"', 'A guard returned False or a Response, stopping subsequent nodes.'],
            ['FlowStatus.ERROR', '"error"', 'An unhandled exception occurred, stored in error.'],
            ['FlowStatus.TIMEOUT', '"timeout"', 'Pipeline execution exceeded the configured duration.'],
            ['FlowStatus.CANCELLED', '"cancelled"', 'The task execution was cancelled before completing.'],
          ].map(([statusVal, strVal, desc]) => (
            <div key={statusVal} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-2 text-sm">
              <div className="font-mono font-bold text-aquilia-400">{statusVal}</div>
              <div className="font-mono text-zinc-500 md:w-32">{strVal}</div>
              <div className={`font-light md:w-1/2 ${textMuted}`}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Context Cleanup & LIFO Flow */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Context Cleanup Callback Flow</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            You can register custom teardown code directly onto the context. This guarantees cleanup runs even if subsequent nodes throw errors or timeout:
          </p>
        </div>

        <CodeBlock language="python" filename="cleanup_demo.py" highlightLines={[11, 14, 18]}>{`import os
from aquilia.flow import FlowContext, FlowError

async def write_temp_file(ctx: FlowContext):
    temp_path = f"/tmp/process_{ctx.request.id}.json"
    
    # 1. Write initial payload
    with open(temp_path, "w") as f:
        f.write(ctx.state["payload"])
        
    # 2. Register callback to delete file on teardown
    async def cleanup_temp():
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    ctx.add_cleanup(cleanup_temp)
    ctx.state["temp_file"] = temp_path

# Teardown triggers LIFO order
# await ctx.dispose()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/subsystem/pipelines" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Flow Pipelines
        </Link>
        <Link to="/docs/subsystem/layers" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Layers &amp; Compositions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
