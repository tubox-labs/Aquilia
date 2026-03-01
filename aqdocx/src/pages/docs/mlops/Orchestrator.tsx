import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsOrchestrator() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Orchestrator
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Orchestrator
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The orchestrator layer is the central coordinator for model lifecycle management. It combines
          the registry, loader, version manager, and routing into a single facade that handles routing
          requests to the correct model version, lazy loading, hot-reload, memory eviction, and
          persistence.
        </p>
      </div>

      {/* ModelOrchestrator Facade */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelOrchestrator Facade</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">ModelOrchestrator</code> is the primary entry point for inference.
          It resolves the model version, ensures it is loaded, and executes the inference pipeline.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator

orchestrator = ModelOrchestrator(
    registry=model_registry,
    loader=model_loader,
    pipeline=inference_pipeline,
    version_router=version_router,
)

# Single request
result = await orchestrator.predict("sentiment", request)
# 1. version_router.route("sentiment", request) → resolved version
# 2. loader.ensure_loaded("sentiment", version) → LoadedModel
# 3. pipeline.execute(loaded_model.runtime, request) → result

# Batch prediction
results = await orchestrator.predict_batch("sentiment", [req1, req2, req3])

# Streaming (LLM)
async for chunk in orchestrator.stream_predict("llama-7b", request):
    yield chunk

# Model lifecycle
await orchestrator.reload("sentiment")   # Hot-reload weights
await orchestrator.unload("sentiment")   # Free resources

# Health & metrics per model
health = await orchestrator.health("sentiment")
metrics = await orchestrator.metrics("sentiment")

# Graceful shutdown (unloads all models)
await orchestrator.shutdown()`} />
      </section>

      {/* ModelRegistry */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelRegistry</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          In-memory registry of model configurations and their active versions. Thread-safe via <code className="text-aquilia-500">asyncio.Lock</code>.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.registry import ModelRegistry, ModelConfig, ModelEntry

registry = ModelRegistry()

# Register a model configuration
config = ModelConfig(
    name="sentiment",
    version="2.1.0",
    model_dir="./models/sentiment",
    framework="pytorch",
    device="cuda:0",
    batch_size=32,
    max_batch_latency_ms=50.0,
)
registry.register(config)

# Get model entry
entry = registry.get("sentiment")
# ModelEntry(
#   config=ModelConfig(...),
#   active_version="2.1.0",
#   available_versions=["1.0.0", "2.0.0", "2.1.0"],
# )

# List all models
models = registry.list_models()

# Set active version
registry.set_active("sentiment", "2.0.0")

# Thread safety: all operations acquire asyncio.Lock
async with registry._lock:
    # Atomic multi-model operations`} />
      </section>

      {/* VersionManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>VersionManager</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Manages version promotion and rollback with a per-model rollback stack.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.versioning import VersionManager

vm = VersionManager(registry=model_registry)

# Promote a new version (pushes current to rollback stack)
await vm.promote("sentiment", new_version="3.0.0")
# Before: active="2.1.0", stack=[]
# After:  active="3.0.0", stack=["2.1.0"]

# Promote again
await vm.promote("sentiment", new_version="3.1.0")
# After: active="3.1.0", stack=["3.0.0", "2.1.0"]

# Rollback (pops from stack)
await vm.rollback("sentiment")
# After: active="3.0.0", stack=["2.1.0"]

# Rollback again
await vm.rollback("sentiment")
# After: active="2.1.0", stack=[]

# Rollback with empty stack → raises VersionRollbackFault`} />
      </section>

      {/* ModelLoader */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelLoader</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handles lazy loading, warmup, memory-pressure eviction, and zero-downtime hot-reload.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.loader import ModelLoader, LoadedModel

loader = ModelLoader(
    registry=model_registry,
    memory_tracker=memory_tracker,
    max_loaded_models=10,  # Evict LRU when exceeded
)

# Lazy loading (loads only on first request)
loaded: LoadedModel = await loader.ensure_loaded("sentiment", "2.1.0")
# Returns immediately if already loaded
# LoadedModel contains: runtime, config, load_time, last_used

# Warmup (synthetic inference after loading)
await loader.warmup("sentiment", n_requests=5)

# Hot-reload (zero-downtime weight swap)
await loader.hot_reload("sentiment", "3.0.0")
# 1. Load new version into separate runtime
# 2. Run warmup on new runtime
# 3. Atomic swap: replace old runtime reference
# 4. Unload old runtime
# Zero dropped requests during swap!

# Memory-pressure eviction
await loader.evict_if_needed()
# Evicts least-recently-used model when:
# - Number of loaded models > max_loaded_models
# - Memory usage exceeds threshold (via MemoryTracker)

# Unload specific model
await loader.unload("sentiment")

# Unload all models
await loader.unload_all()`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>_InstanceRuntimeAdapter</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When models are loaded from <code className="text-aquilia-500">AquiliaModel</code> instances (class-based API),
          the loader wraps them in <code className="text-aquilia-500">_InstanceRuntimeAdapter</code> to satisfy the
          <code className="text-aquilia-500"> Runtime</code> protocol.
        </p>
        <CodeBlock language="python" code={`# Internal adapter: wraps AquiliaModel instances
class _InstanceRuntimeAdapter(BaseStreamingRuntime):
    def __init__(self, model_instance: AquiliaModel):
        self._instance = model_instance

    async def infer(self, batch):
        return await self._instance.predict(batch)

    async def stream_infer(self, request):
        async for chunk in self._instance.stream(request):
            yield chunk`} />
      </section>

      {/* VersionRouter */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>VersionRouter</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Routes requests to the correct model version using header overrides, canary splits, or the default active version.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.router import VersionRouter, CanaryConfig

router = VersionRouter(registry=model_registry)

# Set canary configuration
router.set_canary("sentiment", CanaryConfig(
    canary_version="3.0.0",
    weight=0.10,  # 10% of traffic
))

# Route a request
version = router.route("sentiment", request)
# Priority:
# 1. X-Model-Version header → explicit version override
# 2. Canary split → random(0,1) < weight → canary_version
# 3. Default → registry.get("sentiment").active_version

# Remove canary (all traffic to default)
router.clear_canary("sentiment")`} />
      </section>

      {/* ModelPersistenceManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Persistence Manager</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Framework-agnostic save/load for model weights with metadata tracking.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.orchestrator.persistence import ModelPersistenceManager

pm = ModelPersistenceManager(base_dir="./model_store")

# Save a model (auto-detects framework)
await pm.save(
    name="sentiment",
    version="2.1.0",
    model=trained_model,
    framework="pytorch",
    metadata={"accuracy": 0.95, "dataset": "imdb"},
)
# Creates directory structure:
# ./model_store/sentiment/2.1.0/
#   ├── model.pt          (or model.pkl, model.joblib)
#   └── metadata.json     (version, framework, timestamp, custom metadata)

# Load a model
model, metadata = await pm.load("sentiment", "2.1.0")

# Framework-specific loaders:
# PyTorch  → torch.save() / torch.load()
# sklearn  → joblib.dump() / joblib.load()
# Generic  → pickle`} />
      </section>

      <NextSteps
        items={[
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'Release & Rollouts', link: '/docs/mlops/release' },
          { text: 'Scheduler', link: '/docs/mlops/scheduler' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
