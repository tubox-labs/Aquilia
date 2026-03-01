import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Engine &amp; Pipeline
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Engine &amp; Pipeline
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine layer contains the <code className="text-aquilia-500">InferencePipeline</code> (5-stage request processing),
          <code className="text-aquilia-500"> HookRegistry</code> (7 lifecycle hook decorators), 35+ fault classes in a domain taxonomy,
          lifecycle management (startup/shutdown), and the <code className="text-aquilia-500">MLOpsManifest</code> Aquilary module registration.
        </p>
      </div>

      {/* InferencePipeline */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>InferencePipeline</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">InferencePipeline</code> orchestrates a 5-stage request processing pipeline
          with timing, tracing, and error handling at each stage.
        </p>

        <div className={boxClass}>
          <h4 className={`font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Pipeline Stages</h4>
          <div className="flex flex-wrap items-center gap-2">
            {['preprocess', 'before_predict', 'infer', 'after_predict', 'postprocess'].map((stage, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-lg text-sm font-mono ${isDark ? 'bg-aquilia-500/20 text-aquilia-400' : 'bg-aquilia-50 text-aquilia-600'}`}>
                  {stage}
                </span>
                {i < 4 && <span className={`${isDark ? 'text-gray-600' : 'text-gray-400'}`}>→</span>}
              </div>
            ))}
          </div>
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.engine.pipeline import InferencePipeline, PipelineContext

# PipelineContext carries trace ID and stage timing data
context = PipelineContext(
    trace_id="trace-abc123",
    stage_timings={},  # Populated automatically
)

# Create pipeline with runtime and hooks
pipeline = InferencePipeline(
    runtime=my_runtime,
    hooks=collected_hooks,
)

# Execute single request
result = await pipeline.execute(request, context=context)
# context.stage_timings → {"preprocess": 1.2, "infer": 45.3, ...}

# Execute batch (concurrent)
results = await pipeline.execute_batch(requests, context=context)`} />

        <div className={`${boxClass} mt-4`}>
          <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Stage Details</h4>
          <ol className={`text-sm space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li><strong>1. preprocess</strong> — Calls runtime's <code className="text-aquilia-500">preprocess()</code> + all <code className="text-aquilia-500">@preprocess</code> hooks. Transforms raw input.</li>
            <li><strong>2. before_predict</strong> — Calls all <code className="text-aquilia-500">@before_predict</code> hooks. Useful for logging, validation, caching checks.</li>
            <li><strong>3. infer</strong> — Calls runtime's <code className="text-aquilia-500">infer()</code> with the processed batch. This is the actual model execution.</li>
            <li><strong>4. after_predict</strong> — Calls all <code className="text-aquilia-500">@after_predict</code> hooks. Post-inference metadata, metrics recording.</li>
            <li><strong>5. postprocess</strong> — Calls runtime's <code className="text-aquilia-500">postprocess()</code> + all <code className="text-aquilia-500">@postprocess</code> hooks. Formats output.</li>
          </ol>
        </div>
      </section>

      {/* Hook System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Hook System</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          7 hook decorators allow you to attach custom logic at any point in the model lifecycle.
          The <code className="text-aquilia-500">HookRegistry</code> collects hooks per kind, and <code className="text-aquilia-500">collect_hooks()</code> scans
          model instances for decorated methods.
        </p>

        <CodeBlock language="python" code={`from aquilia.mlops.engine.hooks import (
    on_load, on_unload,
    preprocess, postprocess,
    before_predict, after_predict,
    on_error,
)

@model(name="my-model", version="v1")
class MyModel(AquiliaModel):
    @on_load
    async def setup_cache(self):
        """Called after model weights are loaded."""
        self.cache = {}

    @on_unload
    async def cleanup(self):
        """Called before model is unloaded."""
        self.cache.clear()

    @preprocess
    async def validate_input(self, raw_input: dict) -> dict:
        """Called before predict() — validate/transform input."""
        if "text" not in raw_input:
            raise ValueError("Missing 'text' field")
        return raw_input

    @postprocess
    async def add_metadata(self, raw_output: dict) -> dict:
        """Called after predict() — enrich output."""
        raw_output["model_version"] = "v1"
        return raw_output

    @before_predict
    async def log_request(self, inputs):
        """Called just before inference."""
        logger.info("Predicting for: %s", inputs.get("request_id"))

    @after_predict
    async def record_latency(self, result):
        """Called just after inference."""
        metrics.observe("custom_latency", result.latency_ms)

    @on_error
    async def handle_error(self, error: Exception):
        """Called when any stage raises an exception."""
        logger.error("Model error: %s", error)
        return {"error": str(error), "fallback": True}`} />

        <div className={`${boxClass} mt-4`}>
          <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>HookRegistry Internals</h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Each decorator sets a <code className="text-aquilia-500">_hook_kind</code> attribute on the method.
            When a model is loaded, <code className="text-aquilia-500">collect_hooks(instance)</code> scans all methods for this
            attribute and groups them by kind into a <code className="text-aquilia-500">CollectedHooks</code> dataclass
            with fields: <code className="text-aquilia-500">on_load</code>, <code className="text-aquilia-500">on_unload</code>,
            <code className="text-aquilia-500">preprocess</code>, <code className="text-aquilia-500">postprocess</code>,
            <code className="text-aquilia-500">before_predict</code>, <code className="text-aquilia-500">after_predict</code>,
            <code className="text-aquilia-500">on_error</code>.
          </p>
        </div>
      </section>

      {/* Fault System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Taxonomy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The MLOps module defines 35+ fault classes organized into 12 domains. All extend <code className="text-aquilia-500">MLOpsFault(Fault)</code>
          from Aquilia's FaultEngine, enabling structured error handling, domain-based routing, and metrics collection.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { domain: 'Pack', faults: 'PackBuildFault, PackIntegrityFault, PackSignatureFault' },
            { domain: 'Registry', faults: 'RegistryConnectionFault, RegistryNotFoundFault, RegistryImmutabilityFault' },
            { domain: 'Serving', faults: 'RuntimeLoadFault, InferenceFault, BatchTimeoutFault, WarmupFault' },
            { domain: 'Observe', faults: 'DriftDetectionFault, MetricsExportFault' },
            { domain: 'Rollout', faults: 'RolloutAdvanceFault, AutoRollbackFault' },
            { domain: 'Scheduler', faults: 'PlacementFault, ScalingFault' },
            { domain: 'Security', faults: 'SigningFault, PermissionDeniedFault, EncryptionFault' },
            { domain: 'Plugin', faults: 'PluginLoadFault, PluginHookFault' },
            { domain: 'CircuitBreaker', faults: 'CircuitBreakerOpenFault, CircuitBreakerExhaustedFault' },
            { domain: 'RateLimit', faults: 'RateLimitFault (429 Too Many Requests)' },
            { domain: 'Streaming', faults: 'StreamInterruptedFault, TokenLimitExceededFault' },
            { domain: 'Memory', faults: 'SoftLimitFault (eviction warning), HardLimitFault (reject)' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.domain}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.faults}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.engine.faults import (
    MLOpsFault,
    RuntimeLoadFault,
    InferenceFault,
    CircuitBreakerOpenFault,
    RateLimitFault,
)

# All faults carry domain, code, message, and optional metadata
try:
    result = await runtime.infer(batch)
except RuntimeLoadFault as e:
    # e.domain = "mlops.serving"
    # e.code = "RUNTIME_LOAD"
    # e.message = "Failed to load model weights"
    logger.error("Load failed: %s", e)
except InferenceFault as e:
    # e.domain = "mlops.serving"
    # e.code = "INFERENCE"
    logger.error("Inference failed: %s", e)

# FaultEngine integration (automatic in MLOpsController)
# Faults are routed to the FaultEngine which:
# 1. Logs the fault with structured metadata
# 2. Records fault metrics via MetricsCollector listener
# 3. Routes to domain-specific handlers
# 4. Optionally triggers alerts/effects`} />
      </section>

      {/* Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Lifecycle Management</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">engine/lifecycle.py</code> defines <code className="text-aquilia-500">mlops_on_startup</code> (7 steps)
          and <code className="text-aquilia-500">mlops_on_shutdown</code> (6 steps) that integrate with Aquilia's application lifecycle.
        </p>

        <CodeBlock language="python" code={`# engine/lifecycle.py

async def mlops_on_startup(app, container, config):
    """Called during Aquilia app startup."""
    # 1. Register all DI providers via register_mlops_providers()
    # 2. Initialize async SQLite registry DB (create tables/indexes)
    # 3. Discover plugins via importlib.metadata entry points
    # 4. Initialize CacheService (memory backend if not pre-registered)
    # 5. Create artifact store directory structure
    # 6. Wire FaultEngine → MetricsCollector listener (fault metrics)
    # 7. Detect device capabilities: CUDA (torch.cuda), MPS (torch.backends.mps)

async def mlops_on_shutdown(app, container):
    """Called during Aquilia app shutdown."""
    # 1. Open circuit breaker → reject new inference requests
    # 2. Flush all buffered metrics to collectors
    # 3. Unload ALL loaded models + torch.cuda.empty_cache()
    # 4. Deactivate all plugins (call deactivate() on each)
    # 5. Shutdown CacheService (flush + close)
    # 6. Close registry DB connection (commit + close SQLite)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Device Detection</h3>
        <CodeBlock language="python" code={`# Automatic device capability detection at startup

def _detect_device_capabilities() -> dict:
    capabilities = {"cpu": True, "cuda": False, "mps": False}
    try:
        import torch
        if torch.cuda.is_available():
            capabilities["cuda"] = True
            capabilities["cuda_device_count"] = torch.cuda.device_count()
            capabilities["cuda_device_name"] = torch.cuda.get_device_name(0)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            capabilities["mps"] = True
    except ImportError:
        pass
    return capabilities`} />
      </section>

      {/* Module Registration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MLOps Module Manifest</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">MLOpsManifest</code> registers the entire MLOps subsystem with Aquilia's Aquilary
          module system. It declares controllers, services, fault domains, and middleware.
        </p>
        <CodeBlock language="python" code={`# engine/module.py

class MLOpsManifest(AquilaryModule):
    name = "mlops"

    # HTTP controller with 30+ endpoints
    controllers = [MLOpsController]

    # 16 singleton services registered with DI
    services = [
        MetricsCollector, DriftDetector, PredictionLogger,
        RegistryService, PluginHost, TrafficRouter,
        RolloutEngine, Autoscaler, PlacementScheduler,
        RBACManager, ArtifactSigner, EncryptionManager,
        BlobEncryptor, ModelOrchestrator, ModelLoader,
        ModelPersistenceManager,
    ]

    # 12 fault domains for structured error handling
    fault_domains = [
        "mlops.pack", "mlops.registry", "mlops.serving",
        "mlops.observe", "mlops.rollout", "mlops.scheduler",
        "mlops.security", "mlops.plugin", "mlops.circuit_breaker",
        "mlops.rate_limit", "mlops.streaming", "mlops.memory",
    ]

    # 4 middleware in priority order
    middleware = [
        ("mlops_request_id", mlops_request_id_middleware, 100),
        ("mlops_metrics", mlops_metrics_middleware, 200),
        ("mlops_rate_limit", mlops_rate_limit_middleware, 300),
        ("mlops_circuit_breaker", mlops_circuit_breaker_middleware, 400),
    ]`} />
      </section>

      <NextSteps
        items={[
          { text: 'Modelpack Builder', link: '/docs/mlops/modelpack' },
          { text: 'Runtime Backends', link: '/docs/mlops/runtime' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Observability', link: '/docs/mlops/observability' },
        ]}
      />
    </div>
  )
}
