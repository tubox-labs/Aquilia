import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsObservability() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Observability
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Observability
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Full-stack observability for ML models in production. The <code className="text-aquilia-500">MetricsCollector</code> provides
          Prometheus-compatible metrics with LLM-specific telemetry, <code className="text-aquilia-500">DriftDetector</code> monitors
          statistical shifts in input distributions, and <code className="text-aquilia-500">PredictionLogger</code> records
          sampled predictions for audit and debugging.
        </p>
      </div>

      {/* MetricsCollector */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MetricsCollector</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Collects inference metrics using lock-free data structures: <code className="text-aquilia-500">AtomicCounter</code> for
          counts, <code className="text-aquilia-500">RingBuffer</code> for histograms, <code className="text-aquilia-500">ExponentialDecay</code> for
          EWMA smoothing, and <code className="text-aquilia-500">TopKHeap</code> for hot model tracking.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Metric Types</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { name: 'Counters', desc: 'Monotonically increasing via AtomicCounter. request_count, error_count, total_tokens.' },
            { name: 'Gauges', desc: 'Point-in-time values. active_models, loaded_model_count, gpu_utilization.' },
            { name: 'Histograms', desc: 'Distribution tracking via RingBuffer. latency_ms, batch_size, tokens_per_second.' },
            { name: 'EWMA', desc: 'Exponentially weighted moving average via ExponentialDecay. smoothed_latency, smoothed_throughput.' },
          ].map((m, i) => (
            <div key={i} className={boxClass}>
              <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{m.name}</h4>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.observe.metrics import MetricsCollector

collector = MetricsCollector(
    histogram_size=1000,  # RingBuffer capacity per metric
    ewma_alpha=0.1,       # Smoothing factor
    top_k=10,             # Track top 10 hot models
)

# Record an inference event (convenience method)
collector.record_inference(
    model="sentiment",
    latency_ms=12.5,
    batch_size=16,
    error=False,
)
# Increments: request_count, model-scoped request_count
# Records:    latency_ms histogram, batch_size histogram
# Updates:    EWMA smoothed_latency, hot model counter

# LLM-specific recording
collector.record_tokens(
    model="llama-7b",
    prompt_tokens=128,
    completion_tokens=256,
    time_to_first_token_ms=45.0,
    tokens_per_second=85.0,
)

# Per-model scoped metrics
model_metrics = collector.model_metrics("sentiment")
# {
#   "request_count": 1500,
#   "error_count": 3,
#   "latency_p50": 11.2,
#   "latency_p95": 18.7,
#   "latency_p99": 35.2,
#   "avg_batch_size": 14.8,
#   "ewma_latency": 12.1,
# }

# Hot models (top-K by request count)
hot = collector.hot_models()
# [("sentiment", 1500), ("classifier", 800), ...]`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Prometheus Export</h3>
        <CodeBlock language="python" code={`# Export all metrics in Prometheus text format
prometheus_text = collector.to_prometheus()

# Output:
# # HELP aquilia_mlops_request_total Total inference requests
# # TYPE aquilia_mlops_request_total counter
# aquilia_mlops_request_total{model="sentiment"} 1500
# aquilia_mlops_request_total{model="classifier"} 800
#
# # HELP aquilia_mlops_latency_seconds Inference latency
# # TYPE aquilia_mlops_latency_seconds histogram
# aquilia_mlops_latency_seconds_bucket{model="sentiment",le="0.01"} 450
# aquilia_mlops_latency_seconds_bucket{model="sentiment",le="0.025"} 1200
# aquilia_mlops_latency_seconds_bucket{model="sentiment",le="0.05"} 1480
# aquilia_mlops_latency_seconds_bucket{model="sentiment",le="+Inf"} 1500
#
# # HELP aquilia_mlops_tokens_per_second Token generation rate
# # TYPE aquilia_mlops_tokens_per_second gauge
# aquilia_mlops_tokens_per_second{model="llama-7b"} 85.0

# Served via MLOpsController at GET /mlops/metrics`} />
      </section>

      {/* DriftDetector */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DriftDetector</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Monitors statistical shifts in model input distributions to detect data drift in production.
          Supports 4 detection methods for different data types.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { name: 'PSI (Population Stability Index)', desc: 'Compares binned distributions. PSI > 0.1 = moderate drift, > 0.25 = significant drift. Best for tabular features.' },
            { name: 'KS Test (Kolmogorov-Smirnov)', desc: 'Non-parametric statistical test comparing CDFs. p-value < threshold → drift detected. Best for continuous features.' },
            { name: 'Embedding Drift', desc: 'Cosine distance between reference and current embedding centroids. Best for text/image/NLP models.' },
            { name: 'Perplexity Drift', desc: 'Monitors log-perplexity shift for language models. Detects distribution shift in generated text quality.' },
          ].map((d, i) => (
            <div key={i} className={boxClass}>
              <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</h4>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.observe.drift import DriftDetector

detector = DriftDetector(
    psi_threshold=0.1,         # PSI above this = drift
    ks_alpha=0.05,             # KS test significance level
    embedding_threshold=0.15,  # Cosine distance threshold
    window_size=1000,          # Sliding window for current data
)

# Set reference distribution (from training data)
detector.set_reference(
    features={
        "age": [25, 30, 35, 40, 45, ...],      # Numeric features
        "income": [50000, 60000, 70000, ...],
    },
    embeddings=reference_embeddings,  # np.ndarray for embedding drift
)

# Full drift detection (all methods)
report = detector.detect(
    features={
        "age": [28, 33, 55, 60, 65, ...],      # Production data
        "income": [45000, 55000, 80000, ...],
    },
    embeddings=current_embeddings,
)
# DriftReport(
#   drifted=True,
#   psi_scores={"age": 0.08, "income": 0.23},
#   ks_results={"age": KSResult(stat=0.12, p=0.09), "income": KSResult(stat=0.31, p=0.001)},
#   embedding_distance=0.18,
#   timestamp=datetime(...)
# )

# Single-feature quick check
is_drifted = detector.check("income", current_values)

# Perplexity drift for LLMs
perplexity_report = detector.detect_perplexity(
    reference_logprobs=[-2.1, -1.8, -2.3, ...],
    current_logprobs=[-3.5, -4.0, -3.8, ...],
)
# High perplexity shift → model is seeing out-of-distribution text`} />
      </section>

      {/* PredictionLogger */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PredictionLogger</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Records sampled predictions to JSONL files for audit trails, debugging, and retraining dataset creation.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.observe.logger import PredictionLogger

logger = PredictionLogger(
    output_dir="./prediction_logs",
    sample_rate=0.1,  # Log 10% of predictions
)

# Log a prediction (sampled automatically)
logger.log(
    model="sentiment",
    version="2.1.0",
    request_id="req-abc123",
    inputs={"text": "Great product!"},
    outputs={"label": "positive", "confidence": 0.95},
    latency_ms=12.5,
)
# If sampled, writes JSONL line:
# {"model": "sentiment", "version": "2.1.0", "request_id": "req-abc123",
#  "inputs": {...}, "outputs": {...}, "latency_ms": 12.5,
#  "timestamp": "2024-01-15T10:30:00Z"}

# Custom sink (pluggable)
class KafkaSink:
    async def write(self, record: dict):
        await kafka_producer.send("predictions", record)

logger.set_sink(KafkaSink())

# Flush pending writes
await logger.flush()

# File output structure:
# ./prediction_logs/
#   └── sentiment/
#       └── 2024-01-15.jsonl  (one JSON object per line)`} />
      </section>

      {/* Grafana Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Grafana Dashboard</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia MLOps ships with a pre-built Grafana dashboard JSON that visualizes the Prometheus metrics.
        </p>
        <div className={boxClass}>
          <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dashboard Panels</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { panel: 'Inference RPS', query: 'rate(aquilia_mlops_request_total[5m])' },
              { panel: 'Latency p50/p95/p99', query: 'histogram_quantile(0.95, ...)' },
              { panel: 'Active Models', query: 'aquilia_mlops_active_models' },
              { panel: 'Error Rate', query: 'rate(aquilia_mlops_error_total[5m])' },
              { panel: 'Batch Utilization', query: 'aquilia_mlops_batch_size / max_batch_size' },
              { panel: 'GPU Memory', query: 'aquilia_mlops_gpu_memory_used_bytes' },
            ].map((p, i) => (
              <div key={i} className={`p-3 rounded-lg ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
                <div className={`font-medium text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{p.panel}</div>
                <code className="text-xs text-aquilia-500 break-all">{p.query}</code>
              </div>
            ))}
          </div>
        </div>
        <CodeBlock language="bash" code={`# Import the dashboard
cp aquilia/mlops/deploy/grafana/mlops-dashboard.json /var/lib/grafana/dashboards/

# Or import via Grafana API
curl -X POST http://localhost:3000/api/dashboards/db \\
  -H "Content-Type: application/json" \\
  -d @aquilia/mlops/deploy/grafana/mlops-dashboard.json`} />
      </section>

      <NextSteps
        items={[
          { text: 'Release & Rollouts', link: '/docs/mlops/release' },
          { text: 'Scheduler', link: '/docs/mlops/scheduler' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
