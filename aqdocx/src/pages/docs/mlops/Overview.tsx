import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Brain, ArrowRight, Layers, Box, Server, Activity, Shield, Zap, Eye, Plug, Rocket, Database, Cpu, GitBranch, BarChart3 } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          Advanced / MLOps
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            MLOps Platform
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's MLOps module is a comprehensive, production-grade machine learning operations platform
          built directly into the framework. It provides everything needed to package, register, serve, observe,
          optimize, secure, and manage ML models at scale — from traditional classifiers to large language models (LLMs).
          Every component is fully integrated with Aquilia's DI container, FaultEngine, CacheService, Artifacts system,
          and lifecycle hooks.
        </p>
      </div>

      {/* Architecture Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture Overview</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The MLOps module is organized into 17 sub-modules spanning the entire ML lifecycle. Each module
          is independently usable but designed to work together as a cohesive platform.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { name: 'API Layer', desc: 'Model definition via @model, @serve decorators and AquiliaModel base class with automatic route generation', icon: '🎯' },
            { name: 'Engine', desc: 'InferencePipeline with hooks, lifecycle management, MLOps module manifest, and 35+ fault types', icon: '⚙️' },
            { name: 'Pack', desc: 'ModelpackBuilder creates .aquilia TAR.GZ archives with content-addressable storage and cryptographic signing', icon: '📦' },
            { name: 'Registry', desc: 'RegistryService with async SQLite, versioning, immutability, LRU caching, and S3/filesystem storage backends', icon: '🗃️' },
            { name: 'Runtime', desc: 'Multi-backend execution: PythonRuntime, ONNX, Triton, TorchServe, BentoML with FSM state management', icon: '🏃' },
            { name: 'Serving', desc: 'ModelServingServer with dynamic batching, circuit breaker, rate limiting, streaming, and K8s health probes', icon: '🌐' },
            { name: 'Orchestrator', desc: 'ModelOrchestrator facade with lazy loading, hot-reload, version routing, and model persistence', icon: '🎭' },
            { name: 'Observe', desc: 'MetricsCollector (Prometheus-compatible), DriftDetector (PSI/KS/embedding), and PredictionLogger', icon: '👁️' },
            { name: 'Optimizer', desc: 'OptimizationPipeline for quantization (INT8/FP16) and EdgeExporter for TFLite/CoreML/TensorRT', icon: '🔧' },
            { name: 'Plugins', desc: 'PluginHost with entry-point discovery, lifecycle management, and PluginMarketplace for community plugins', icon: '🔌' },
            { name: 'Release', desc: 'RolloutEngine for canary/A/B deployments with metric-gated advancement and auto-rollback', icon: '🚀' },
            { name: 'Scheduler', desc: 'Autoscaler with GPU/token-based policies and PlacementScheduler with hardware-aware node scoring', icon: '📊' },
            { name: 'Security', desc: 'RBAC with 4 built-in roles, Fernet encryption at rest, HMAC/RSA artifact signing', icon: '🔒' },
            { name: 'Explain', desc: 'SHAP/LIME explainability wrappers, PII redaction, differential privacy noise, input sanitization', icon: '🔍' },
            { name: 'DI Providers', desc: '20+ singleton services wired via register_mlops_providers() with ecosystem integration', icon: '💉' },
            { name: 'Manifest', desc: 'TOML-based model configuration with schema validation and class-path resolution', icon: '📋' },
            { name: 'Deploy', desc: 'K8s manifests (Deployment, Service, HPA, PVC) and Grafana dashboard for production deployment', icon: '☁️' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{item.icon}</span>
                <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              </div>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Class-Based Model</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Define a model by subclassing <code className="text-aquilia-500">AquiliaModel</code> and decorating with <code className="text-aquilia-500">@model</code>.
          The decorator registers the model with the global <code className="text-aquilia-500">ModelRegistry</code> and auto-generates HTTP endpoints.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import AquiliaModel, model

@model(name="sentiment", version="v1", device="auto", batch_size=32)
class SentimentAnalyzer(AquiliaModel):
    async def load(self):
        # Load your model weights, tokenizer, etc.
        self.pipeline = load_sentiment_pipeline("./model.pt")

    async def predict(self, inputs: dict) -> dict:
        text = inputs.get("text", "")
        score = self.pipeline(text)
        return {"sentiment": "positive" if score > 0.5 else "negative", "score": score}

    async def preprocess(self, raw_input: dict) -> dict:
        # Optional: clean text, validate inputs
        raw_input["text"] = raw_input["text"].strip().lower()
        return raw_input

    async def postprocess(self, raw_output: dict) -> dict:
        # Optional: format output, add metadata
        raw_output["model_version"] = "v1"
        return raw_output`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Functional Model</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For simple models, use the <code className="text-aquilia-500">@serve</code> decorator to wrap a plain function.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import serve

@serve(name="echo", version="v1")
async def echo_model(inputs: dict) -> dict:
    return {"echo": inputs}`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Integration</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Wire all 20+ MLOps services into Aquilia's DI container with a single call.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace, Integration

workspace = (
    Workspace("my-ml-app")
    .integrate(Integration.mlops(
        registry_db="registry.db",
        blob_root="./blobs",
        drift_method="psi",
        drift_threshold=0.2,
        max_batch_size=32,
        rate_limit_rps=100.0,
        circuit_breaker_failure_threshold=5,
        memory_hard_limit_mb=8192,
        cache_enabled=True,
    ))
)`} />
      </section>

      {/* Type System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Type System</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The MLOps module defines a comprehensive type system in <code className="text-aquilia-500">_types.py</code> with 17 enums,
          12 dataclasses, and 4 protocols that provide type safety across all subsystems.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { name: 'DType', desc: '10 numeric types with framework-specific conversion (numpy, torch)' },
            { name: 'Framework', desc: '11 ML frameworks: PyTorch, TensorFlow, ONNX, JAX, VLLM, LlamaCpp, HuggingFace, etc.' },
            { name: 'RuntimeKind', desc: '8 runtime backends: Python, ONNX, Triton, TorchServe, BentoML, VLLM, LlamaCpp, Custom' },
            { name: 'QuantizePreset', desc: '12 quantization presets: INT8, FP16, DYNAMIC, STATIC, GGUF_Q4, AWQ, GPTQ, EDGE, etc.' },
            { name: 'ModelType', desc: '8 model types: SLM, LLM, VISION, MULTIMODAL, TABULAR, TIMESERIES, RECOMMENDER, CUSTOM' },
            { name: 'InferenceMode', desc: '4 modes: BATCH, STREAMING, REALTIME, OFFLINE' },
            { name: 'DeviceType', desc: '6 devices: CPU, CUDA, MPS, XLA, NPU, AUTO' },
            { name: 'BatchingStrategy', desc: '5 strategies: SIZE, TIME, HYBRID, CONTINUOUS, ADAPTIVE' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Data Structures */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Data Structures</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The module ships with 17 high-performance data structures in <code className="text-aquilia-500">_structures.py</code>,
          purpose-built for ML serving workloads.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { name: 'RingBuffer', desc: 'O(1) bounded circular buffer with percentile computation for metrics histograms' },
            { name: 'LRUCache', desc: 'O(1) eviction with hit-rate tracking, used by RegistryService for manifest lookups' },
            { name: 'CircuitBreaker', desc: '3-state FSM (CLOSED→OPEN→HALF_OPEN) with lifetime metrics and configurable thresholds' },
            { name: 'TokenBucketRateLimiter', desc: 'Lazy-refill token bucket for per-model or global rate limiting' },
            { name: 'ConsistentHash', desc: 'Jump-consistent hashing for sticky routing in TrafficRouter' },
            { name: 'AdaptiveBatchQueue', desc: 'Priority + token-budget draining queue for LLM continuous batching' },
            { name: 'ModelLineageDAG', desc: 'Directed acyclic graph with BFS traversal for model ancestry tracking' },
            { name: 'ExperimentLedger', desc: 'A/B experiment assignment with per-arm metrics and statistical summarization' },
            { name: 'BloomFilter', desc: 'Probabilistic set for request deduplication in serving' },
            { name: 'MemoryTracker', desc: 'Soft/hard limit tracking with eviction candidate selection' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Module Registration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Module Registration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The MLOps module registers itself with Aquilia's Aquilary system via <code className="text-aquilia-500">MLOpsManifest</code>,
          declaring controllers, 16 services, effects, 12 fault domains, and 4 middleware with scoped ordering.
        </p>
        <CodeBlock language="python" code={`# engine/module.py — MLOpsManifest (Aquilary Module)

class MLOpsManifest(AquilaryModule):
    name = "mlops"
    controllers = [MLOpsController]
    services = [
        MetricsCollector, DriftDetector, PredictionLogger,
        RegistryService, PluginHost, TrafficRouter, RolloutEngine,
        Autoscaler, PlacementScheduler, RBACManager,
        ArtifactSigner, EncryptionManager, BlobEncryptor,
        ModelOrchestrator, ModelLoader, ModelPersistenceManager,
    ]
    fault_domains = [
        "mlops.pack", "mlops.registry", "mlops.serving",
        "mlops.observe", "mlops.rollout", "mlops.scheduler",
        "mlops.security", "mlops.plugin", "mlops.circuit_breaker",
        "mlops.rate_limit", "mlops.streaming", "mlops.memory",
    ]
    middleware = [
        mlops_request_id_middleware,
        mlops_metrics_middleware,
        mlops_rate_limit_middleware,
        mlops_circuit_breaker_middleware,
    ]`} />
      </section>

      {/* Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Lifecycle</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className={boxClass}>
            <h3 className={`font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Startup (7 steps)</h3>
            <ol className={`text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>1. Register DI providers</li>
              <li>2. Initialize registry DB</li>
              <li>3. Discover plugins via entry points</li>
              <li>4. Initialize CacheService</li>
              <li>5. Create artifact store directory</li>
              <li>6. Wire FaultEngine → MetricsCollector listener</li>
              <li>7. Detect device capabilities (CUDA/MPS)</li>
            </ol>
          </div>
          <div className={boxClass}>
            <h3 className={`font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Shutdown (6 steps)</h3>
            <ol className={`text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>1. Open circuit breaker (reject new requests)</li>
              <li>2. Flush metrics</li>
              <li>3. Unload all models + release GPU cache</li>
              <li>4. Deactivate all plugins</li>
              <li>5. Shutdown CacheService</li>
              <li>6. Close registry DB connection</li>
            </ol>
          </div>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Types & Structures', link: '/docs/mlops/types' },
          { text: 'API Layer', link: '/docs/mlops/api' },
          { text: 'Engine & Pipeline', link: '/docs/mlops/engine' },
          { text: 'Modelpack Builder', link: '/docs/mlops/modelpack' },
          { text: 'Registry', link: '/docs/mlops/registry' },
          { text: 'Runtime Backends', link: '/docs/mlops/runtime' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Orchestrator', link: '/docs/mlops/orchestrator' },
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
