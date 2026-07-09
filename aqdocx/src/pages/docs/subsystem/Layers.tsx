import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function FlowLayers() {
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
          <span>SUBSYSTEM / LAYERS &amp; COMPOSITIONS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Layers &amp; Compositions
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Manage complex capability graph initialization using <DocTerm id="effects.Layer">Layer</DocTerm> and <DocTerm id="effects.EffectScope">EffectScope</DocTerm>. Decouple construction from usage, sort dependencies topologically, and acquire resources safely outside pipelines.
        </p>
      </div>

      {/* Layer System Concept */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">The Layer Architecture</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted}`}>
          <p>
            In large microservice applications, capability providers (like database connection pools or cache servers) have complex initialization graphs. A database provider might depend on a configuration provider, while a metrics service might require both configuration and database logging connections.
          </p>
          <p>
            Inspired by Effect-TS, the <DocTerm id="effects.Layer">Layer</DocTerm> system allows you to build modular constructors that declare explicit dependencies. The framework's dependency compiler sorts these layers topologically at startup, resolving, building, and registering providers automatically.
          </p>
        </div>
      </section>

      {/* Layer Constructor Reference */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Layer API Reference</h2>
        
        <div className="space-y-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`class Layer:
    def __init__(self, name: str, factory: Callable, deps: list[str] = [], scope: str = "app")`}</CodeBlock>
            <p className={`font-light text-sm mt-2 mb-6 ${textMuted}`}>
              Constructs a composable layer. <code className="text-white">factory</code> is a callable that receives resolved dependencies as keyword arguments and returns a provider. <code className="text-white">scope</code> dictates whether the provider has application or request lifetime.
            </p>
          </div>

          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`@staticmethod
def merge(*layers: Layer) -> LayerComposition`}</CodeBlock>
            <p className={`font-light text-sm mt-2 mb-6 ${textMuted}`}>
              Combines multiple layers into a unified composition. The compiler automatically resolves inter-layer dependencies and orders initialization topologically.
            </p>
          </div>

          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`@staticmethod
def provide(layer: Layer, *providers: Layer) -> LayerComposition`}</CodeBlock>
            <p className={`font-light text-sm mt-2 ${textMuted}`}>
              Expresses dependency injections explicitly. Builds the list of <code className="text-white">providers</code> first, then feeds their constructed values as dependencies into the target <code className="text-white">layer</code>.
            </p>
          </div>
        </div>
      </section>

      {/* LayerComposition */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">LayerComposition API</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            Merging or chaining layers creates a <code className="text-white">LayerComposition</code>. It manages sorting and mount operations:
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def build_all(self, initial_deps: dict | None = None) -> dict[str, Any]`}</CodeBlock>
            <p className={`font-light text-sm mt-2 mb-6 ${textMuted}`}>
              Builds all layers in computed topological order. Returns a dictionary mapping capability names to constructed provider instances. Raises <code className="text-white">FlowError</code> if circular dependencies are detected.
            </p>
          </div>

          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def register_with(self, registry: EffectRegistry, initial_deps: dict | None = None) -> None`}</CodeBlock>
            <p className={`font-light text-sm mt-2 ${textMuted}`}>
              Builds all layers and mounts the output providers directly into the active <DocTerm id="effects.EffectRegistry">EffectRegistry</DocTerm> registry.
            </p>
          </div>
        </div>
      </section>

      {/* EffectScope */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Manual Capability Management: EffectScope</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            While pipelines acquire capabilities automatically based on annotations, you can manage them manually using the <DocTerm id="effects.EffectScope">EffectScope</DocTerm> context manager. This is ideal for background tasks, CLI commands, or scripts that require scoped resource access:
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`class EffectScope:
    def __init__(self, registry: EffectRegistry, effect_names: list[str], *, context = None, modes = None)`}</CodeBlock>
            <p className={`font-light text-sm mt-2 ${textMuted}`}>
              Async context manager. On enter (<code className="text-white">__aenter__</code>), it calls <code className="text-white">acquire()</code> on all listed providers. On exit (<code className="text-white">__aexit__</code>), it releases them, tracking whether exceptions occurred to trigger rollbacks or commits automatically.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example: Defining and Bootstrapping Layers */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Topological Bootstrap Walkthrough</h2>
        <p className={`mb-6 font-light leading-relaxed ${textMuted}`}>
          The following code defines configuration, database, and cache capability layers. The layers are merged, resolved topologically, registered, and accessed inside an <DocTerm id="effects.EffectScope">EffectScope</DocTerm>.
        </p>

        <CodeBlock language="python" filename="layers_setup.py" highlightLines={[13, 19, 25, 28, 31, 35]}>{`from aquilia.flow import Layer, EffectScope
from aquilia.effects import EffectRegistry, DBTxProvider, CacheProvider

# 1. Define capability layers
config_layer = Layer(
    name="Config",
    factory=lambda: {"db_url": "sqlite:///app.db", "cache_host": "localhost"}
)

db_layer = Layer(
    name="DBTx",
    # Receives constructed config layer output as keyword argument 'Config'
    factory=lambda Config: DBTxProvider(Config["db_url"]),
    deps=["Config"]
)

cache_layer = Layer(
    name="Cache",
    # Receives config output as 'Config'
    factory=lambda Config: CacheProvider(Config["cache_host"]),
    deps=["Config"]
)

# 2. Merge Layers (Sorted Topologically: Config -> DBTx -> Cache)
app_composition = Layer.merge(db_layer, cache_layer, config_layer)

# 3. Mount providers to registry
registry = EffectRegistry()
await app_composition.register_with(registry)

# 4. Access resources manually via EffectScope
async def process_jobs():
    async with EffectScope(registry, ["DBTx", "Cache"]) as effects:
        db = effects["DBTx"]
        cache = effects["Cache"]
        
        # Safe transaction execution
        await db.execute("UPDATE stats SET runs = runs + 1")
        await cache.set("last_run", "now")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/subsystem/context-nodes" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Flow Context &amp; Nodes
        </Link>
        <Link to="/docs/subsystem/built-in" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Built-in Effects <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
