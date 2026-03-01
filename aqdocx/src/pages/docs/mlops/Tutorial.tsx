import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain, BookOpen, Layers, Shield, Gauge, Rocket, Eye, Puzzle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsTutorial() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          MLOps / Tutorial
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            MLOps Tutorial
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Build a complete ML-powered application from scratch using Aquilia MLOps with Blueprints,
          Dependency Injection, Controllers, Middleware, Sessions, and the full ML lifecycle. This
          tutorial covers model definition through production deployment with monitoring.
        </p>
      </div>

      {/* What We'll Build */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>What We'll Build</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A sentiment analysis API with:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { icon: <Brain className="w-5 h-5" />, title: 'Model Serving', desc: 'PyTorch model with streaming, batching, and warmup' },
            { icon: <Layers className="w-5 h-5" />, title: 'DI Integration', desc: 'Full dependency injection for all MLOps services' },
            { icon: <Shield className="w-5 h-5" />, title: 'Auth & RBAC', desc: 'Secured endpoints with role-based access control' },
            { icon: <Gauge className="w-5 h-5" />, title: 'Observability', desc: 'Prometheus metrics, drift detection, prediction logging' },
            { icon: <Rocket className="w-5 h-5" />, title: 'Canary Rollouts', desc: 'Safe deployments with metric-gated advancement' },
            { icon: <Eye className="w-5 h-5" />, title: 'Explainability', desc: 'SHAP explanations with PII redaction' },
            { icon: <Puzzle className="w-5 h-5" />, title: 'Plugin System', desc: 'Custom health check plugin' },
            { icon: <BookOpen className="w-5 h-5" />, title: 'Blueprints', desc: 'Type-safe request/response validation' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-aquilia-500">{item.icon}</span>
                <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h4>
              </div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Step 1: Project Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 1: Project Setup</h2>
        <CodeBlock language="bash" code={`# Create project
mkdir sentiment-api && cd sentiment-api

# Install Aquilia
pip install aquilia[mlops]

# Project structure:
# sentiment-api/
# ├── app.py              # Application entry point
# ├── models/
# │   └── sentiment.py    # Model definition
# ├── controllers/
# │   └── predict.py      # Custom controller
# ├── blueprints/
# │   └── schemas.py      # Request/response schemas
# ├── plugins/
# │   └── health.py       # Custom plugin
# ├── middleware/
# │   └── auth.py         # Auth middleware
# └── pyproject.toml`} />

        <CodeBlock language="toml" code={`# pyproject.toml
[tool.aquilia]
name = "sentiment-api"
port = 8080

[tool.aquilia.mlops]
device = "cuda"
max_batch_size = 32
max_batch_latency_ms = 50
warmup_requests = 5

[[tool.aquilia.mlops.models]]
name = "sentiment"
class = "models.sentiment.SentimentModel"
version = "1.0.0"
device = "cuda:0"
batch_size = 32`} />
      </section>

      {/* Step 2: Define the Model */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 2: Define the Model</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use the class-based API with hooks for preprocessing, postprocessing, and error handling.
        </p>
        <CodeBlock language="python" code={`# models/sentiment.py
from aquilia.mlops import AquiliaModel, model
from aquilia.mlops.engine.hooks import on_load, on_unload, preprocess, postprocess, on_error

@model(
    name="sentiment",
    version="1.0.0",
    device="cuda:0",
    batch_size=32,
    max_batch_latency_ms=50,
    warmup_requests=5,
    tags=["nlp", "sentiment", "production"],
)
class SentimentModel(AquiliaModel):

    @on_load
    async def load_model(self):
        """Load model weights and tokenizer."""
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "./weights/sentiment-distilbert"
        ).to(self.device)
        self.model.eval()
        self.labels = ["negative", "neutral", "positive"]

    @on_unload
    async def unload_model(self):
        """Free GPU memory."""
        del self.model
        del self.tokenizer
        import torch
        torch.cuda.empty_cache()

    @preprocess
    async def tokenize(self, request):
        """Tokenize input text."""
        text = request.inputs.get("text", "")
        tokens = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)
        request.inputs["tokens"] = tokens
        return request

    async def predict(self, batch):
        """Run inference on a batch."""
        import torch
        results = []
        for request in batch:
            tokens = request.inputs["tokens"]
            with torch.no_grad():
                logits = self.model(**tokens).logits
                probs = torch.softmax(logits, dim=-1)
                label_idx = probs.argmax().item()
                results.append({
                    "label": self.labels[label_idx],
                    "confidence": probs[0][label_idx].item(),
                    "scores": {
                        label: probs[0][i].item()
                        for i, label in enumerate(self.labels)
                    },
                })
        return results

    @postprocess
    async def format_response(self, result):
        """Add metadata to response."""
        result["model_version"] = self.version
        return result

    @on_error
    async def handle_error(self, error, request):
        """Log errors with request context."""
        print(f"Error processing request {request.request_id}: {error}")
        return {"error": str(error), "label": "unknown", "confidence": 0.0}`} />
      </section>

      {/* Step 3: Blueprints */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 3: Request/Response Blueprints</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Define type-safe request and response schemas using Aquilia Blueprints.
        </p>
        <CodeBlock language="python" code={`# blueprints/schemas.py
from aquilia.blueprints import Blueprint, Field, Annotated

class PredictRequest(Blueprint):
    """Sentiment prediction request."""
    text: Annotated[str, Field(
        min_length=1,
        max_length=10000,
        description="Text to analyze for sentiment",
    )]
    explain: Annotated[bool, Field(
        default=False,
        description="Include SHAP explanations",
    )]

class PredictResponse(Blueprint):
    """Sentiment prediction response."""
    label: str
    confidence: float
    scores: dict[str, float]
    model_version: str
    explanation: dict | None = None

class BatchPredictRequest(Blueprint):
    """Batch prediction request."""
    texts: Annotated[list[str], Field(
        min_length=1,
        max_length=100,
        description="List of texts to analyze",
    )]

class DriftStatusResponse(Blueprint):
    """Drift detection status."""
    drifted: bool
    psi_scores: dict[str, float]
    timestamp: str`} />
      </section>

      {/* Step 4: DI Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 4: Dependency Injection</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Register all MLOps services with Aquilia's DI container. The <code className="text-aquilia-500">register_mlops_providers()</code> function
          registers 20+ singletons automatically.
        </p>
        <CodeBlock language="python" code={`# app.py — DI configuration
from aquilia import Aquilia
from aquilia.di import Container, Singleton
from aquilia.mlops.di.providers import register_mlops_providers, MLOpsConfig
from aquilia.mlops.observe.metrics import MetricsCollector
from aquilia.mlops.observe.drift import DriftDetector
from aquilia.mlops.security.rbac import RBACManager
from aquilia.mlops.explain.hooks import create_explainer, ExplainMethod
from aquilia.mlops.explain.privacy import InputSanitiser

app = Aquilia()
container = Container()

# Register all MLOps providers (20+ services)
config = MLOpsConfig(
    device="cuda",
    max_batch_size=32,
    max_batch_latency_ms=50,
    registry_db_path="./data/registry.db",
    registry_storage_dir="./data/models",
    metrics_histogram_size=1000,
    drift_psi_threshold=0.1,
    rate_limit_rate=100.0,
    rate_limit_capacity=200.0,
    circuit_breaker_threshold=5,
    circuit_breaker_recovery=30.0,
)
register_mlops_providers(container, config)

# Register additional custom providers
container.register(Singleton, InputSanitiser, lambda: InputSanitiser())
container.register(Singleton, "shap_explainer", lambda: create_explainer(
    method=ExplainMethod.SHAP_KERNEL,
    background_data=load_background_data(),
))

# What register_mlops_providers() registers:
# - MLOpsConfig, MetricsCollector, DriftDetector, PredictionLogger
# - RegistryService, ModelPersistenceManager, ModelLoader
# - PluginHost, TrafficRouter, ModelOrchestrator
# - RolloutEngine, Autoscaler, PlacementScheduler
# - RBACManager, ArtifactSigner, EncryptionManager, BlobEncryptor
# - CircuitBreaker, TokenBucketRateLimiter, MemoryTracker
# - ModelLineageDAG, ExperimentLedger
# - MLOpsController (with FaultEngine + CacheService integration)`} />
      </section>

      {/* Step 5: Custom Controller */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 5: Custom Controller</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          While <code className="text-aquilia-500">MLOpsController</code> provides 30+ endpoints automatically,
          you can create custom controllers for business-specific logic.
        </p>
        <CodeBlock language="python" code={`# controllers/predict.py
from aquilia.controller import Controller, get, post
from aquilia.di import Inject
from aquilia.request import Request
from aquilia.response import JsonResponse

from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.observe.drift import DriftDetector
from aquilia.mlops.security.rbac import RBACManager, Permission
from aquilia.mlops.explain.hooks import SHAPExplainer
from aquilia.mlops.explain.privacy import InputSanitiser
from aquilia.mlops._types import InferenceRequest

from blueprints.schemas import PredictRequest, PredictResponse, DriftStatusResponse

class SentimentController(Controller):
    """Custom controller with Blueprint validation and RBAC."""

    prefix = "/api/v1/sentiment"

    def __init__(
        self,
        orchestrator: Inject[ModelOrchestrator],
        rbac: Inject[RBACManager],
        drift: Inject[DriftDetector],
        explainer: Inject[SHAPExplainer],
        sanitiser: Inject[InputSanitiser],
    ):
        self.orchestrator = orchestrator
        self.rbac = rbac
        self.drift = drift
        self.explainer = explainer
        self.sanitiser = sanitiser

    @post("/predict")
    async def predict(self, request: Request) -> JsonResponse:
        """Predict sentiment with Blueprint validation."""
        # Validate request with Blueprint
        body = PredictRequest.from_dict(await request.json())

        # Check RBAC
        user = request.headers.get("X-User-ID", "anonymous")
        if not self.rbac.check_permission(user, Permission.MODEL_READ):
            return JsonResponse({"error": "Forbidden"}, status=403)

        # Sanitize input (PII redaction)
        clean_text = self.sanitiser.sanitize(body.text)

        # Build inference request
        inference_req = InferenceRequest(
            model="sentiment",
            inputs={"text": clean_text},
            request_id=request.headers.get("X-Request-ID", ""),
        )

        # Run inference via orchestrator
        result = await self.orchestrator.predict("sentiment", inference_req)

        # Optional: add SHAP explanations
        explanation = None
        if body.explain:
            explanation = self.explainer.explain(
                model=self.orchestrator._loader.get("sentiment").runtime,
                inputs=clean_text,
            )
            explanation = {
                "top_features": [
                    {"feature": fa.feature, "importance": fa.importance}
                    for fa in explanation.top_k(5)
                ],
            }

        # Validate response with Blueprint
        response = PredictResponse(
            label=result.outputs["label"],
            confidence=result.outputs["confidence"],
            scores=result.outputs["scores"],
            model_version=result.outputs.get("model_version", "1.0.0"),
            explanation=explanation,
        )

        return JsonResponse(response.to_dict())

    @get("/drift")
    async def drift_status(self, request: Request) -> JsonResponse:
        """Check drift status for the sentiment model."""
        report = self.drift.detect(current_features)
        response = DriftStatusResponse(
            drifted=report.drifted,
            psi_scores=report.psi_scores,
            timestamp=report.timestamp.isoformat(),
        )
        return JsonResponse(response.to_dict())`} />
      </section>

      {/* Step 6: Middleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 6: Middleware Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Combine Aquilia's auth middleware with MLOps middleware for a complete security + observability stack.
        </p>
        <CodeBlock language="python" code={`# middleware/auth.py
from aquilia.middleware import Middleware
from aquilia.auth import verify_jwt
from aquilia.mlops.security.rbac import RBACManager

class AuthMiddleware(Middleware):
    """JWT authentication + RBAC injection."""

    def __init__(self, rbac: RBACManager):
        self.rbac = rbac

    async def __call__(self, request, next_handler):
        # Verify JWT
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        claims = verify_jwt(token)
        request.user_id = claims["sub"]
        request.user_role = claims.get("role", "VIEWER")

        # Inject RBAC role
        self.rbac.assign_role(request.user_id, request.user_role)

        return await next_handler(request)`} />

        <CodeBlock language="python" code={`# app.py — Register middleware stack
from aquilia.mlops.serving.middleware import (
    mlops_request_id,
    mlops_metrics,
    mlops_rate_limit,
    mlops_circuit_breaker,
)
from middleware.auth import AuthMiddleware

# Middleware execution order (outermost → innermost):
# 1. mlops_request_id   → Generate X-Request-ID
# 2. mlops_rate_limit   → Token bucket rate limiting
# 3. AuthMiddleware      → JWT + RBAC
# 4. mlops_circuit_breaker → Circuit breaker protection
# 5. mlops_metrics       → Record latency/count/errors

app.use(mlops_request_id)
app.use(mlops_rate_limit(rate_limiter))
app.use(AuthMiddleware(rbac))
app.use(mlops_circuit_breaker(circuit_breaker))
app.use(mlops_metrics(metrics_collector))`} />
      </section>

      {/* Step 7: Sessions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 7: Sessions for User History</h2>
        <CodeBlock language="python" code={`# Track prediction history per user session
from aquilia.sessions import SessionMiddleware, Session

app.use(SessionMiddleware(secret_key="your-secret", max_age=3600))

@post("/api/v1/sentiment/predict-with-history")
async def predict_with_history(request: Request):
    session: Session = request.session

    # Get prediction history from session
    history = session.get("predictions", [])

    # Run prediction
    result = await orchestrator.predict("sentiment", inference_req)

    # Store in session (last 10 predictions)
    history.append({
        "text": request_body["text"][:100],
        "label": result.outputs["label"],
        "confidence": result.outputs["confidence"],
    })
    session["predictions"] = history[-10:]

    return JsonResponse({
        **result.outputs,
        "history_count": len(history),
    })`} />
      </section>

      {/* Step 8: Plugin */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 8: Custom Plugin</h2>
        <CodeBlock language="python" code={`# plugins/health.py
from aquilia.mlops._types import PluginHook

class ModelHealthPlugin:
    """Plugin that monitors model health and alerts on degradation."""

    name = "model-health-monitor"
    version = "1.0.0"

    def __init__(self):
        self.alert_threshold = 0.05  # 5% error rate
        self.alerts: list[dict] = []

    async def activate(self, host):
        host.on("on_inference", self.check_health)
        host.on("on_drift_detected", self.on_drift)
        host.on("on_circuit_open", self.on_circuit_open)

    async def deactivate(self, host):
        self.alerts.clear()

    async def check_health(self, model_name: str, latency_ms: float, **kwargs):
        error = kwargs.get("error", False)
        if error:
            self.alerts.append({
                "type": "inference_error",
                "model": model_name,
                "latency_ms": latency_ms,
            })

    async def on_drift(self, model_name: str, drift_report, **kwargs):
        self.alerts.append({
            "type": "drift_detected",
            "model": model_name,
            "psi_scores": drift_report.psi_scores,
        })
        # Could send Slack/email alert here

    async def on_circuit_open(self, model_name: str, failure_count: int, **kwargs):
        self.alerts.append({
            "type": "circuit_breaker_open",
            "model": model_name,
            "failures": failure_count,
        })

# Register in app.py
plugin_host.register(ModelHealthPlugin())
await plugin_host.activate_all()`} />
      </section>

      {/* Step 9: Canary Rollout */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 9: Canary Rollout</h2>
        <CodeBlock language="python" code={`# Deploy a new model version with canary rollout
from aquilia.mlops.release.rollout import RolloutEngine
from aquilia.mlops._types import RolloutConfig

rollout_config = RolloutConfig(
    model_name="sentiment",
    canary_version="2.0.0",
    initial_weight=0.05,       # 5% of traffic
    max_weight=1.0,
    step_weight=0.10,          # +10% per step
    error_rate_threshold=0.01, # Rollback if > 1% errors
    latency_p99_threshold=100, # Rollback if p99 > 100ms
    min_requests_per_step=200, # Need 200 reqs before advancing
)

# Start the rollout
await rollout_engine.start(rollout_config)
# → 5% of traffic goes to v2.0.0

# Automated advancement (call periodically or via cron)
result = await rollout_engine.advance("sentiment")
# Checks metrics → advances to 15%, 25%, 35%, ...
# Auto-rollbacks if error_rate or latency exceed thresholds

# Or complete manually
await rollout_engine.complete("sentiment")
# → 100% traffic to v2.0.0, v1.0.0 pushed to rollback stack`} />
      </section>

      {/* Step 10: Full App */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 10: Full Application</h2>
        <CodeBlock language="python" code={`# app.py — Complete application
from aquilia import Aquilia
from aquilia.di import Container, Singleton
from aquilia.mlops.di.providers import register_mlops_providers, MLOpsConfig
from aquilia.mlops.serving.middleware import (
    mlops_request_id, mlops_metrics, mlops_rate_limit, mlops_circuit_breaker,
)
from aquilia.mlops.plugins.host import PluginHost

from controllers.predict import SentimentController
from plugins.health import ModelHealthPlugin
from middleware.auth import AuthMiddleware

# Initialize
app = Aquilia()
container = Container()

# Configure MLOps
config = MLOpsConfig(
    device="cuda",
    max_batch_size=32,
    max_batch_latency_ms=50,
    registry_db_path="./data/registry.db",
    registry_storage_dir="./data/models",
)
register_mlops_providers(container, config)

# Resolve services from DI
metrics = container.resolve("MetricsCollector")
rate_limiter = container.resolve("TokenBucketRateLimiter")
circuit_breaker = container.resolve("CircuitBreaker")
rbac = container.resolve("RBACManager")
plugin_host = container.resolve("PluginHost")

# Middleware stack
app.use(mlops_request_id)
app.use(mlops_rate_limit(rate_limiter))
app.use(AuthMiddleware(rbac))
app.use(mlops_circuit_breaker(circuit_breaker))
app.use(mlops_metrics(metrics))

# Register controllers
app.controller(SentimentController)

# Register plugins
plugin_host.register(ModelHealthPlugin())

# Startup hook
@app.on_startup
async def startup():
    # MLOps lifecycle handles model loading, warmup, etc.
    await plugin_host.activate_all()

    # Set up RBAC roles
    rbac.assign_role("admin-user", "ADMIN")
    rbac.assign_role("ml-engineer", "DEPLOYER")

@app.on_shutdown
async def shutdown():
    await plugin_host.deactivate_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)`} />
      </section>

      {/* API Examples */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Testing the API</h2>
        <CodeBlock language="bash" code={`# Health check
curl http://localhost:8080/mlops/healthz
# {"alive": true}

# Predict sentiment
curl -X POST http://localhost:8080/api/v1/sentiment/predict \\
  -H "Authorization: Bearer <jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Aquilia MLOps is incredible!", "explain": true}'

# Response:
# {
#   "label": "positive",
#   "confidence": 0.96,
#   "scores": {"negative": 0.02, "neutral": 0.02, "positive": 0.96},
#   "model_version": "1.0.0",
#   "explanation": {
#     "top_features": [
#       {"feature": "incredible", "importance": 0.72},
#       {"feature": "Aquilia", "importance": 0.15}
#     ]
#   }
# }

# Prometheus metrics
curl http://localhost:8080/mlops/metrics
# aquilia_mlops_request_total{model="sentiment"} 42
# aquilia_mlops_latency_seconds_bucket{model="sentiment",le="0.025"} 38

# Drift status
curl http://localhost:8080/api/v1/sentiment/drift
# {"drifted": false, "psi_scores": {"text_length": 0.03}, "timestamp": "..."}

# List models
curl http://localhost:8080/mlops/models
# [{"name": "sentiment", "version": "1.0.0", "state": "LOADED", "device": "cuda:0"}]

# Hot models
curl http://localhost:8080/mlops/hot-models
# [{"model": "sentiment", "request_count": 42}]`} />
      </section>

      {/* Deployment */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Deploy to Production</h2>
        <CodeBlock language="bash" code={`# 1. Build modelpack
aquilia mlops pack build \\
  --name sentiment \\
  --version 1.0.0 \\
  --model-dir ./weights \\
  --output ./dist

# 2. Sign the artifact
aquilia mlops sign ./dist/sentiment-1.0.0.aquilia --key ./keys/private.pem

# 3. Push to registry
aquilia mlops registry push \\
  --archive ./dist/sentiment-1.0.0.aquilia \\
  --url https://registry.example.com

# 4. Deploy to Kubernetes
kubectl apply -f aquilia/mlops/deploy/k8s/serving.yaml
kubectl apply -f aquilia/mlops/deploy/k8s/registry.yaml

# 5. Import Grafana dashboard
kubectl create configmap mlops-dashboard \\
  --from-file=aquilia/mlops/deploy/grafana/mlops-dashboard.json

# 6. Verify deployment
kubectl get pods -l app=aquilia-mlops
kubectl rollout status deployment/mlops-serving`} />
      </section>

      <NextSteps
        items={[
          { text: 'MLOps Overview', link: '/docs/mlops' },
          { text: 'API Reference', link: '/docs/mlops/api' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
        ]}
      />
    </div>
  )
}
