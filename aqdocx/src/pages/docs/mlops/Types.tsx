import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsTypes() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Types &amp; Structures
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Types &amp; Structures
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The MLOps type system (<code className="text-aquilia-500">_types.py</code>) defines 17 enums, 12 dataclasses,
          and 4 protocols. The structures module (<code className="text-aquilia-500">_structures.py</code>) provides 17 high-performance
          data structures purpose-built for ML serving.
        </p>
      </div>

      {/* Enums */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Enumerations</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>DType</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Numeric data types with framework-specific conversion. Each enum value maps to its numpy and torch equivalents.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import DType

# 10 numeric types
DType.FLOAT16   # half precision
DType.FLOAT32   # single precision (default)
DType.FLOAT64   # double precision
DType.INT8      # quantized integer
DType.INT16
DType.INT32
DType.INT64
DType.UINT8
DType.BOOL
DType.BFLOAT16  # brain floating point

# Framework conversion
np_type = DType.FLOAT32.to_numpy()    # numpy.float32
torch_type = DType.FLOAT16.to_torch() # torch.float16`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Framework</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Supported ML frameworks, including traditional frameworks and modern LLM runtimes.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import Framework

Framework.PYTORCH       # PyTorch (.pt, .pth)
Framework.TENSORFLOW    # TensorFlow / Keras
Framework.ONNX          # Open Neural Network Exchange
Framework.SKLEARN       # scikit-learn (.pkl, .joblib)
Framework.JAX           # Google JAX
Framework.HUGGINGFACE   # HuggingFace Transformers
Framework.VLLM          # vLLM engine
Framework.LLAMACPP      # llama.cpp (GGUF models)
Framework.CUSTOM        # Custom callable
Framework.XGBOOST       # XGBoost
Framework.LIGHTGBM      # LightGBM`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>QuantizePreset</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          12 quantization presets spanning traditional quantization and modern LLM quantization formats.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import QuantizePreset

# Traditional quantization
QuantizePreset.NONE        # No quantization
QuantizePreset.INT8        # INT8 quantization
QuantizePreset.FP16        # Half precision
QuantizePreset.DYNAMIC     # Dynamic quantization
QuantizePreset.STATIC      # Static quantization (requires calibration)

# LLM-specific quantization formats
QuantizePreset.GGUF_Q4     # llama.cpp 4-bit
QuantizePreset.GGUF_Q5     # llama.cpp 5-bit
QuantizePreset.GGUF_Q8     # llama.cpp 8-bit
QuantizePreset.AWQ          # Activation-aware Weight Quantization
QuantizePreset.GPTQ         # GPU Post-Training Quantization

# Deployment targets
QuantizePreset.EDGE         # Edge-optimized (mobile/embedded)
QuantizePreset.TENSORRT     # NVIDIA TensorRT`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Other Key Enums</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
          {[
            { name: 'RuntimeKind', values: 'PYTHON, ONNX, TRITON, TORCHSERVE, BENTOML, VLLM, LLAMACPP, CUSTOM' },
            { name: 'ExportTarget', values: 'ONNX, TFLITE, COREML, TENSORRT, ONNX_QUANTIZED, TORCHSCRIPT, SAFETENSORS' },
            { name: 'BatchingStrategy', values: 'SIZE, TIME, HYBRID, CONTINUOUS, ADAPTIVE' },
            { name: 'RolloutStrategy', values: 'CANARY, BLUE_GREEN, AB_TEST, SHADOW, ROLLING' },
            { name: 'DriftMethod', values: 'PSI, KS_TEST, DISTRIBUTION, EMBEDDING, PERPLEXITY' },
            { name: 'ModelType', values: 'SLM, LLM, VISION, MULTIMODAL, TABULAR, TIMESERIES, RECOMMENDER, CUSTOM' },
            { name: 'InferenceMode', values: 'BATCH, STREAMING, REALTIME, OFFLINE' },
            { name: 'DeviceType', values: 'CPU, CUDA, MPS, XLA, NPU, AUTO' },
            { name: 'CircuitState', values: 'CLOSED (accepting), OPEN (rejecting), HALF_OPEN (probing)' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.values}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Core Dataclasses */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Dataclasses</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>TensorSpec</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Describes the shape, dtype, and name of a tensor for input/output specification.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import TensorSpec, DType

spec = TensorSpec(
    name="input_ids",
    shape=[1, 512],        # [batch, sequence_length]
    dtype=DType.INT64,
    optional=False,
)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>LLMConfig</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Comprehensive LLM configuration with 25+ parameters covering generation, optimization, and serving.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import LLMConfig

config = LLMConfig(
    model_id="meta-llama/Llama-2-7b-chat-hf",
    max_tokens=4096,
    temperature=0.7,
    top_p=0.9,
    top_k=50,
    repetition_penalty=1.1,
    stop_sequences=["</s>", "[INST]"],
    # Optimization
    quantize=QuantizePreset.AWQ,
    tensor_parallel_size=2,
    # Speculative decoding
    speculative_model="distilgpt2",
    speculative_tokens=5,
    # Serving
    prefix_caching=True,
    rope_scaling={"type": "dynamic", "factor": 4.0},
    max_model_len=8192,
)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelpackManifest</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Metadata for a packed model, including model files, runtime requirements, and provenance.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import ModelpackManifest, Framework, RuntimeKind

manifest = ModelpackManifest(
    name="sentiment-v2",
    version="2.1.0",
    framework=Framework.PYTORCH,
    runtime=RuntimeKind.PYTHON,
    inputs=[TensorSpec(name="text", shape=[-1], dtype=DType.INT64)],
    outputs=[TensorSpec(name="score", shape=[1], dtype=DType.FLOAT32)],
    model_files=["model.pt", "tokenizer.json"],
    blobs=[BlobRef(digest="sha256:abc...", size=150_000_000, filename="model.pt")],
    metadata={"accuracy": 0.94, "dataset": "imdb"},
)

# Computed properties
digest = manifest.content_digest()  # SHA-256 of all blob digests
is_llm = manifest.is_llm            # True if framework is VLLM/LlamaCpp/HuggingFace`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>InferenceRequest / InferenceResult</h3>
        <CodeBlock language="python" code={`from aquilia.mlops import InferenceRequest, InferenceResult

# Request
request = InferenceRequest(
    request_id="req-001",
    inputs={"text": "Great product!"},
    parameters={"temperature": 0.7},
    max_tokens=100,
    stream=False,
    priority=5,       # Higher = more urgent (used by AdaptiveBatchQueue)
    token_budget=100,  # For continuous batching (LLM)
)

# Result
result = InferenceResult(
    request_id="req-001",
    outputs={"sentiment": "positive", "score": 0.92},
    latency_ms=12.5,
    finish_reason="stop",     # "stop", "length", "error"
    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=1, total_tokens=11),
    metadata={"model": "sentiment-v2"},
)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>StreamChunk</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A single chunk emitted during streaming LLM inference.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops import StreamChunk

chunk = StreamChunk(
    request_id="req-001",
    token="Hello",
    token_id=15496,
    is_finished=False,
    finish_reason="",
    cumulative_tokens=1,
    latency_ms=45.2,
)`} />
      </section>

      {/* Protocols */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Protocols</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Four protocols define the contracts that custom implementations must satisfy.
        </p>
        <div className="grid grid-cols-1 gap-4">
          {[
            { name: 'StorageAdapter', methods: 'put_blob(digest, data), get_blob(digest), has_blob(digest), delete_blob(digest), list_blobs()', desc: 'Backend for registry blob storage (filesystem, S3, etc.)' },
            { name: 'Runtime', methods: 'prepare(manifest, dir), load(), infer(batch), unload(), health(), metrics(), memory_info()', desc: 'Execution environment for model inference' },
            { name: 'StreamingRuntime', methods: 'stream_infer(request) → AsyncIterator[StreamChunk]', desc: 'Extension of Runtime for token-by-token LLM streaming' },
            { name: 'PluginHook', methods: 'activate(ctx), deactivate()', desc: 'Plugin lifecycle interface with name and version attributes' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
              <code className={`text-xs mt-2 block ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.methods}</code>
            </div>
          ))}
        </div>
      </section>

      {/* Data Structures Deep Dive */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Data Structures</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>RingBuffer</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          O(1) bounded circular buffer with percentile computation. Used by <code className="text-aquilia-500">MetricsCollector</code> for
          histogram storage instead of unbounded lists.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import RingBuffer

buf = RingBuffer(capacity=10_000)
buf.append(12.5)
buf.append(14.2)

p50 = buf.percentile(50)   # Median latency
p99 = buf.percentile(99)   # Tail latency
count = len(buf)            # Current element count`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>CircuitBreaker</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          3-state finite state machine that protects downstream services from cascading failures.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import CircuitBreaker

cb = CircuitBreaker(failure_threshold=5, timeout_seconds=30.0)

# Usage
if cb.allow():
    try:
        result = await call_model()
        cb.record_success()
    except Exception:
        cb.record_failure()
        # After 5 failures → OPEN state (rejects all requests for 30s)
        # After timeout → HALF_OPEN state (allows one probe)
        # If probe succeeds → CLOSED state

# Introspection
state = cb.state              # CircuitState.CLOSED
metrics = cb.lifetime_metrics  # {"total_requests": 100, "total_failures": 3, ...}`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>AdaptiveBatchQueue</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Priority queue with token-budget draining for LLM continuous batching.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import AdaptiveBatchQueue

queue = AdaptiveBatchQueue(
    max_batch_size=32,
    max_token_budget=2048,  # Total tokens per batch
    max_queue_depth=1000,
)

# Enqueue requests with priority and token budgets
queue.enqueue(request, priority=5, token_budget=100)

# Drain a batch respecting both size and token constraints
batch = queue.drain_batch()  # Returns up to 32 requests within 2048 tokens`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelLineageDAG</h3>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import ModelLineageDAG

dag = ModelLineageDAG()
dag.add_node("base-v1", metadata={"framework": "pytorch"})
dag.add_node("finetuned-v1", metadata={"dataset": "custom"})
dag.add_edge("base-v1", "finetuned-v1")

ancestors = dag.ancestors("finetuned-v1")    # ["base-v1"]
descendants = dag.descendants("base-v1")      # ["finetuned-v1"]
path = dag.path("base-v1", "finetuned-v1")   # ["base-v1", "finetuned-v1"]
roots = dag.roots()                            # ["base-v1"]
leaves = dag.leaves()                          # ["finetuned-v1"]`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>ExperimentLedger</h3>
        <CodeBlock language="python" code={`from aquilia.mlops._structures import ExperimentLedger

ledger = ExperimentLedger()

# Create an A/B experiment
exp = ledger.create(
    experiment_id="model-comparison",
    arms=["model-v1", "model-v2"],
    description="Compare v1 vs v2 accuracy",
)

# Assign users to arms (deterministic hashing)
arm = ledger.assign("model-comparison", user_id="user-123")  # → "model-v1"

# Record metrics per arm
ledger.record("model-comparison", arm="model-v1", metric="latency", value=12.5)
ledger.record("model-comparison", arm="model-v2", metric="latency", value=10.2)

# Summarize
summary = ledger.summary("model-comparison")
# {"arms": {"model-v1": {"count": 50, "avg_latency": 12.3}, ...}}

# Conclude
ledger.conclude("model-comparison", winner="model-v2")`} />
      </section>

      {/* Other Structures */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Other Structures</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { name: 'LRUCache', desc: 'O(1) eviction via OrderedDict. Tracks hit/miss rates. Used by RegistryService for manifest lookups.' },
            { name: 'AtomicCounter', desc: 'Thread-safe integer counter using threading.Lock. Used for metrics counters.' },
            { name: 'ExponentialDecay', desc: 'Exponentially Weighted Moving Average (EWMA) tracker for smoothed latency metrics.' },
            { name: 'SlidingWindow', desc: 'Time-bucketed metric aggregation. Used by Autoscaler for windowed RPS and latency tracking.' },
            { name: 'TopKHeap', desc: 'Space-efficient top-K tracker using a min-heap. Used by MetricsCollector for hot model tracking.' },
            { name: 'BloomFilter', desc: 'Probabilistic set membership with configurable false-positive rate. Used for request deduplication.' },
            { name: 'ConsistentHash', desc: 'Jump-consistent hashing for sticky session routing in TrafficRouter.' },
            { name: 'TokenBucketRateLimiter', desc: 'Token bucket with lazy refill. Configurable rate (tokens/sec) and capacity (burst).' },
            { name: 'MemoryTracker', desc: 'Tracks model memory usage with soft/hard limits. Provides eviction candidates sorted by LRU.' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'API Layer', link: '/docs/mlops/api' },
          { text: 'Engine & Pipeline', link: '/docs/mlops/engine' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Observability', link: '/docs/mlops/observability' },
        ]}
      />
    </div>
  )
}
