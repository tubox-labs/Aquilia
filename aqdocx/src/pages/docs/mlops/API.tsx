import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / API Layer
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            API Layer
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The API layer provides three ways to define models: the <code className="text-aquilia-500">AquiliaModel</code> base class
          for full lifecycle control, the <code className="text-aquilia-500">@model</code> decorator for class-based registration,
          and the <code className="text-aquilia-500">@serve</code> decorator for functional models. All models get automatic HTTP
          endpoint generation via <code className="text-aquilia-500">RouteGenerator</code> and type-safe validation via 19 Blueprint subclasses.
        </p>
      </div>

      {/* AquiliaModel */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>AquiliaModel Base Class</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The base class provides a complete model lifecycle with hooks for loading, unloading,
          preprocessing, postprocessing, inference, health checks, and metrics.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import AquiliaModel

class MyModel(AquiliaModel):
    """Full lifecycle model with all available hooks."""

    async def load(self):
        """Called once when the model is loaded into memory.
        Load weights, initialize tokenizers, warm up caches.
        """
        self.model = load_my_model("./weights.pt")

    async def unload(self):
        """Called when the model is unloaded (shutdown or eviction).
        Release GPU memory, close connections.
        """
        del self.model

    async def predict(self, inputs: dict) -> dict:
        """Core inference method. Called for every request.
        
        Args:
            inputs: Dict with model-specific input data.
        Returns:
            Dict with prediction outputs.
        """
        return {"prediction": self.model(inputs["data"])}

    async def preprocess(self, raw_input: dict) -> dict:
        """Optional: Transform raw request into model-ready input.
        Called before predict(). Default: identity pass-through.
        """
        return raw_input

    async def postprocess(self, raw_output: dict) -> dict:
        """Optional: Transform model output into API response.
        Called after predict(). Default: identity pass-through.
        """
        return raw_output

    async def health(self) -> dict:
        """Optional: Custom health check endpoint data.
        Returns: Dict with health status information.
        """
        return {"status": "healthy", "model_loaded": self.model is not None}

    async def metrics(self) -> dict:
        """Optional: Custom metrics endpoint data.
        Returns: Dict with metric name→value pairs.
        """
        return {"custom_metric": 42.0}`} />
      </section>

      {/* @model Decorator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@model Decorator</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">@model</code> decorator registers a class with the global
          <code className="text-aquilia-500"> ModelRegistry</code> and configures serving parameters. It accepts 10 configuration
          parameters.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import AquiliaModel, model

@model(
    name="sentiment",              # Unique model identifier
    version="v1",                  # Semantic version string
    device="auto",                 # "auto", "cpu", "cuda", "cuda:0", "mps"
    batch_size=32,                 # Max batch size for dynamic batching
    max_batch_latency_ms=50.0,     # Max wait time before flushing a batch
    warmup_requests=3,             # Number of synthetic warmup requests on load
    workers=4,                     # Thread/process pool size
    timeout_ms=30000,              # Inference timeout per request
    tags=["nlp", "production"],    # Searchable tags
    supports_streaming=False,      # Enable token-by-token streaming
)
class SentimentModel(AquiliaModel):
    async def load(self):
        self.pipeline = load_pipeline("sentiment-analysis")

    async def predict(self, inputs: dict) -> dict:
        text = inputs["text"]
        result = self.pipeline(text)
        return {"label": result["label"], "score": result["score"]}`} />

        <div className={`${boxClass} mt-4`}>
          <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registration Flow</h4>
          <ol className={`text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>1. <code className="text-aquilia-500">@model</code> creates a <code className="text-aquilia-500">ModelConfig</code> dataclass with all parameters</li>
            <li>2. Creates a <code className="text-aquilia-500">ModelEntry</code> with name, version, class reference, config, and tags</li>
            <li>3. Calls <code className="text-aquilia-500">ModelRegistry.register_sync(entry)</code> on the global registry</li>
            <li>4. The class is returned unchanged — it can still be instantiated normally</li>
          </ol>
        </div>
      </section>

      {/* @serve Decorator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@serve Decorator</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">@serve</code> decorator wraps a plain function (sync or async) into a full
          <code className="text-aquilia-500"> AquiliaModel</code> subclass and registers it. Ideal for simple models or quick prototyping.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import serve

# Async function
@serve(name="classifier", version="v1", device="cpu")
async def classify(inputs: dict) -> dict:
    features = inputs["features"]
    prediction = my_classifier.predict([features])
    return {"class": int(prediction[0]), "confidence": 0.95}

# Sync function (automatically wrapped)
@serve(name="echo", version="v1")
def echo(inputs: dict) -> dict:
    return {"echo": inputs}

# The decorator creates a class like:
# class _classifier_model(AquiliaModel):
#     async def predict(self, inputs):
#         return await classify(inputs)  # calls original function`} />
      </section>

      {/* RouteGenerator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RouteGenerator</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">RouteGenerator</code> auto-creates per-model and global HTTP endpoints.
          It reads the <code className="text-aquilia-500">ModelRegistry</code> and produces <code className="text-aquilia-500">RouteDefinition</code> objects
          compatible with Aquilia's router.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.api.route_generator import RouteGenerator

gen = RouteGenerator(prefix="/mlops")
routes = gen.generate(registry)

# Per-model routes generated:
# POST /mlops/models/{name}/predict    — Inference endpoint
# POST /mlops/models/{name}/stream     — Streaming inference (if supports_streaming)
# GET  /mlops/models/{name}/health     — Model health check
# GET  /mlops/models/{name}/metrics    — Model-specific metrics

# Global routes generated:
# GET  /mlops/models                   — List all registered models
# GET  /mlops/health                   — Aggregate health
# GET  /mlops/metrics                  — Prometheus-compatible metrics`} />
      </section>

      {/* Blueprints */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MLOps Blueprints</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          19 <code className="text-aquilia-500">Blueprint</code> subclasses provide type-safe validation and HTML rendering
          for all MLOps data types. Each blueprint defines <code className="text-aquilia-500">validate()</code> and <code className="text-aquilia-500">render()</code> methods.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            'TensorSpecBlueprint', 'BlobRefBlueprint', 'ProvenanceBlueprint',
            'ModelpackManifestBlueprint', 'InferenceRequestBlueprint', 'InferenceResultBlueprint',
            'DriftReportBlueprint', 'RolloutConfigBlueprint', 'RolloutStateBlueprint',
            'ScalingPolicyBlueprint', 'NodeInfoBlueprint', 'PlacementRequestBlueprint',
            'PluginDescriptorBlueprint', 'MetricsSummaryBlueprint', 'LLMConfigBlueprint',
            'StreamChunkBlueprint', 'TokenUsageBlueprint', 'LLMInferenceRequestBlueprint',
            'LLMInferenceResultBlueprint',
          ].map((name, i) => (
            <div key={i} className={`px-3 py-2 rounded-lg border text-center ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
              <code className={`text-xs font-mono ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{name}</code>
            </div>
          ))}
        </div>
        <CodeBlock language="python" code={`from aquilia.mlops.api.blueprints import InferenceRequestBlueprint

bp = InferenceRequestBlueprint()

# Validate
errors = bp.validate(data)   # Returns list of validation errors

# Render
html = bp.render(request)    # Returns HTML representation`} />
      </section>

      <NextSteps
        items={[
          { text: 'Engine & Pipeline', link: '/docs/mlops/engine' },
          { text: 'Runtime Backends', link: '/docs/mlops/runtime' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
