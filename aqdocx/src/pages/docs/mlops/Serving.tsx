import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsServing() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Serving
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Serving Infrastructure
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The serving layer handles model inference at scale with dynamic batching, circuit breakers,
          rate limiting, traffic routing, streaming, deduplication, and Kubernetes-native health probes.
          The <code className="text-aquilia-500">ModelServingServer</code> orchestrates the full lifecycle,
          while <code className="text-aquilia-500">MLOpsController</code> exposes 30+ REST endpoints.
        </p>
      </div>

      {/* ModelServingServer */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelServingServer</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The core serving engine that wraps a runtime with batching, resilience, and observability layers.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.serving.server import ModelServingServer, WarmupStrategy

server = ModelServingServer(
    runtime=python_runtime,
    batcher=dynamic_batcher,         # DynamicBatcher instance
    metrics=metrics_collector,       # MetricsCollector
    bloom_filter=bloom_filter,       # BloomFilter for deduplication
    circuit_breaker=circuit_breaker, # CircuitBreaker instance
    rate_limiter=rate_limiter,       # TokenBucketRateLimiter
    memory_tracker=memory_tracker,   # MemoryTracker for OOM prevention
    warmup=WarmupStrategy.EAGER,     # EAGER | LAZY | NONE
    warmup_requests=5,               # Number of warmup requests
)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Server Lifecycle</h3>
        <CodeBlock language="python" code={`# Start the serving server
await server.start()
# 1. runtime.prepare() + runtime.load()
# 2. Run warmup requests (synthetic data through pipeline)
# 3. Mark circuit breaker as CLOSED
# 4. Set readiness probe to True

# Predict (single request)
result = await server.predict(inference_request)
# Flow: dedup check → rate limit → circuit breaker → batcher → runtime.infer()

# Stream (LLM token streaming)
async for chunk in server.stream(inference_request):
    yield chunk.token

# K8s Health Probes
liveness = await server.liveness()   # {"alive": True}
readiness = await server.readiness() # {"ready": True, "model_loaded": True}

# Graceful shutdown
await server.stop()
# 1. Mark readiness as False (K8s stops sending traffic)
# 2. Drain in-flight requests
# 3. Unload runtime
# 4. Flush metrics`} />
      </section>

      {/* DynamicBatcher */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dynamic Batching</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">DynamicBatcher</code> collects individual requests into
          optimally-sized batches to maximize GPU utilization. Supports 5 batching strategies.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { name: 'Size-Based', desc: 'Flush when batch reaches max_batch_size' },
            { name: 'Time-Based', desc: 'Flush when max_batch_latency_ms elapses' },
            { name: 'Hybrid', desc: 'Flush on whichever trigger fires first' },
            { name: 'Continuous (Token Budget)', desc: 'LLM-optimized: flush when token budget is reached' },
            { name: 'Priority Queue', desc: 'High-priority requests bypass queue and flush immediately' },
          ].map((s, i) => (
            <div key={i} className={boxClass}>
              <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{s.name}</h4>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{s.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.serving.batching import DynamicBatcher

# Standard batcher (hybrid: size + time)
batcher = DynamicBatcher(
    max_batch_size=32,
    max_batch_latency_ms=50.0,
)

# Continuous batcher for LLMs (token-budget based)
llm_batcher = DynamicBatcher(
    max_batch_size=8,
    max_batch_latency_ms=100.0,
    continuous=True,          # Enable continuous batching
    token_budget=4096,        # Max tokens per batch
)

# Submit request (returns awaitable result)
future = batcher.submit(request, priority=5)
result = await future

# Adaptive batch sizing (auto-adjusts based on latency)
# Shrinks batch size if latency exceeds target
# Grows batch size if latency is well below target
batcher.adaptive_resize(measured_latency_ms=35.0, target_latency_ms=50.0)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>PendingRequest</h3>
        <CodeBlock language="python" code={`# Internal: Each submitted request becomes a _PendingRequest
# with priority ordering (higher priority = dequeued first)
# and an asyncio.Future for the result

# Priority ordering:
# _PendingRequest(priority=10) > _PendingRequest(priority=5)
# Equal priority → FIFO by insertion order`} />
      </section>

      {/* MLOpsController */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MLOpsController</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">MLOpsController</code> is an Aquilia <code className="text-aquilia-500">Controller</code> subclass
          that exposes 30+ HTTP endpoints. It integrates with <code className="text-aquilia-500">FaultEngine</code> for
          error handling and <code className="text-aquilia-500">CacheService</code> for response caching.
        </p>

        <div className={boxClass}>
          <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Endpoint Reference</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={`text-left ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <th className="pb-2 pr-4">Method</th>
                  <th className="pb-2 pr-4">Path</th>
                  <th className="pb-2">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {[
                  ['GET', '/mlops/health', 'Platform health status'],
                  ['GET', '/mlops/healthz', 'K8s liveness probe'],
                  ['GET', '/mlops/readyz', 'K8s readiness probe'],
                  ['POST', '/mlops/predict', 'Inference (single request)'],
                  ['POST', '/mlops/stream', 'LLM streaming inference'],
                  ['POST', '/mlops/chat', 'Chat-style LLM inference'],
                  ['GET', '/mlops/capabilities', 'Device & framework capabilities'],
                  ['GET', '/mlops/metrics', 'Prometheus-format metrics'],
                  ['GET', '/mlops/models', 'List all registered models'],
                  ['GET', '/mlops/models/:name', 'Model detail (version, state)'],
                  ['POST', '/mlops/models/:name/load', 'Load a model into memory'],
                  ['POST', '/mlops/models/:name/unload', 'Unload model, free resources'],
                  ['POST', '/mlops/models/:name/reload', 'Hot-reload model weights'],
                  ['GET', '/mlops/models/:name/health', 'Per-model health check'],
                  ['GET', '/mlops/models/:name/metrics', 'Per-model inference metrics'],
                  ['GET', '/mlops/circuit-breaker', 'Circuit breaker state'],
                  ['GET', '/mlops/rate-limit', 'Rate limiter status + remaining tokens'],
                  ['GET', '/mlops/memory', 'Memory usage (RSS + GPU)'],
                  ['POST', '/mlops/rollout/start', 'Start a canary rollout'],
                  ['GET', '/mlops/rollout', 'List active rollouts'],
                  ['GET', '/mlops/drift', 'Drift detection status + report'],
                  ['GET', '/mlops/plugins', 'List installed plugins'],
                  ['GET', '/mlops/lineage', 'Full model lineage DAG'],
                  ['GET', '/mlops/lineage/:name/ancestors', 'Upstream lineage for a model'],
                  ['GET', '/mlops/lineage/:name/descendants', 'Downstream lineage for a model'],
                  ['POST', '/mlops/experiments', 'Create A/B experiment'],
                  ['POST', '/mlops/experiments/:id/conclude', 'Conclude experiment with winner'],
                  ['GET', '/mlops/experiments', 'List all experiments'],
                  ['GET', '/mlops/hot-models', 'Top-K most-invoked models'],
                  ['GET', '/mlops/artifacts', 'List registered artifacts'],
                  ['GET', '/mlops/artifacts/:name', 'Inspect artifact metadata'],
                ].map(([method, path, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-1.5 pr-4">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${
                        method === 'POST'
                          ? 'bg-blue-500/10 text-blue-400'
                          : 'bg-green-500/10 text-green-400'
                      }`}>{method}</span>
                    </td>
                    <td className="py-1.5 pr-4 font-mono text-xs text-aquilia-500">{path}</td>
                    <td className={`py-1.5 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Controller Usage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Controller Examples</h2>
        <CodeBlock language="python" code={`# POST /mlops/predict
# Request body:
{
    "model": "sentiment-v2",
    "inputs": {"text": "Aquilia MLOps is amazing!"},
    "parameters": {"temperature": 0.7}
}

# Response:
{
    "model": "sentiment-v2",
    "version": "2.1.0",
    "outputs": {"label": "positive", "confidence": 0.95},
    "latency_ms": 12.3,
    "request_id": "req-abc123"
}`} />

        <CodeBlock language="python" code={`# POST /mlops/stream (Server-Sent Events)
# Request body:
{
    "model": "llama-7b",
    "inputs": {"prompt": "Explain quantum computing"},
    "parameters": {"max_tokens": 256, "temperature": 0.8}
}

# SSE response (chunked):
# data: {"token": "Quantum", "cumulative_tokens": 1, "is_finished": false}
# data: {"token": " computing", "cumulative_tokens": 2, "is_finished": false}
# ...
# data: {"token": "", "cumulative_tokens": 150, "is_finished": true}`} />
      </section>

      {/* Middleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Serving Middleware</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Four dedicated middleware functions are registered by the MLOps module for all serving endpoints.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { name: 'mlops_request_id', desc: 'Generates a unique X-Request-ID header for tracing. Propagates through the entire pipeline.' },
            { name: 'mlops_metrics', desc: 'Records per-request latency, count, and error rate. Feeds MetricsCollector for Prometheus export.' },
            { name: 'mlops_rate_limit', desc: 'Token-bucket rate limiting. Returns 429 Too Many Requests with Retry-After header when exhausted.' },
            { name: 'mlops_circuit_breaker', desc: 'Circuit breaker pattern. Returns 503 Service Unavailable when circuit is OPEN. Auto-transitions HALF_OPEN → CLOSED on success.' },
          ].map((mw, i) => (
            <div key={i} className={boxClass}>
              <h4 className="text-aquilia-500 font-mono text-sm mb-2">{mw.name}</h4>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{mw.desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" code={`from aquilia.mlops.serving.middleware import (
    mlops_request_id,
    mlops_metrics,
    mlops_rate_limit,
    mlops_circuit_breaker,
)

# These are registered automatically by the MLOps module.
# Manual registration (if needed):
app.use(mlops_request_id)
app.use(mlops_metrics(metrics_collector))
app.use(mlops_rate_limit(rate_limiter))
app.use(mlops_circuit_breaker(circuit_breaker))`} />
      </section>

      {/* TrafficRouter */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Traffic Router</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">TrafficRouter</code> handles advanced traffic splitting
          for canary deployments, A/B testing, shadow traffic, and sticky sessions.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.serving.router import TrafficRouter

router = TrafficRouter(
    models={"v1": runtime_v1, "v2": runtime_v2},
    default_version="v1",
)

# Canary: route 10% of traffic to v2
router.set_canary("v2", weight=0.10)

# A/B test: route based on user segment
router.set_ab_test("v2", segment="premium_users")

# Shadow: mirror all traffic to v2 (fire-and-forget, no response)
router.set_shadow("v2")

# Sticky sessions: same user always gets same version
router.enable_sticky(consistent_hash_key="user_id")

# Route a request
version = router.route(request)
# Priority: 1. Header override (X-Model-Version)
#           2. Canary split (random by weight)
#           3. Default version

# Rollback detection
if router.should_rollback(error_rate=0.05, latency_p99=500):
    router.rollback()  # Removes canary, routes all to default`} />
      </section>

      {/* Resilience */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Resilience Patterns</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Circuit Breaker</h3>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import CircuitBreaker
from aquilia.mlops._types import CircuitBreakerConfig

cb = CircuitBreaker(CircuitBreakerConfig(
    failure_threshold=5,       # Open after 5 consecutive failures
    recovery_timeout=30.0,     # Try half-open after 30 seconds
    half_open_max_calls=3,     # Allow 3 test calls in half-open
))

# States: CLOSED → OPEN → HALF_OPEN → CLOSED
# CLOSED:    Normal operation, counting failures
# OPEN:      Rejecting all requests (503)
# HALF_OPEN: Allowing limited test requests

result = await cb.call(runtime.infer, batch)
# Raises CircuitBreakerOpenFault if circuit is OPEN`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Rate Limiter</h3>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(
    rate=100.0,      # 100 tokens per second
    capacity=200.0,  # Burst capacity
)

if limiter.consume():
    # Request allowed
    result = await runtime.infer(batch)
else:
    # Rate limited — return 429
    raise RateLimitExceededFault("Rate limit exceeded")`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>BloomFilter Dedup</h3>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import BloomFilter

bloom = BloomFilter(expected_items=100_000, fp_rate=0.01)

request_hash = hash(request.inputs)
if bloom.contains(request_hash):
    return cached_result  # Likely duplicate, serve from cache
bloom.add(request_hash)`} />
      </section>

      <NextSteps
        items={[
          { text: 'Orchestrator', link: '/docs/mlops/orchestrator' },
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'Release & Rollouts', link: '/docs/mlops/release' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
