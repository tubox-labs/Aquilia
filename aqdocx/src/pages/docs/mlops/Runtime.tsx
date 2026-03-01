import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsRuntime() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Runtime Backends
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Runtime Backends
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The runtime layer provides a unified interface for model execution across multiple backends.
          A finite state machine manages model state transitions, while specialized adapters support
          PyTorch, ONNX, Triton Inference Server, TorchServe, and BentoML. The <code className="text-aquilia-500">DeviceManager</code> handles
          GPU auto-detection, and <code className="text-aquilia-500">InferenceExecutor</code> manages thread/process pools.
        </p>
      </div>

      {/* Model State FSM */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Model State Machine</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Every runtime uses a <code className="text-aquilia-500">ModelState</code> FSM that enforces legal transitions.
          Invalid transitions raise <code className="text-aquilia-500">InvalidStateTransition</code>.
        </p>
        <div className={boxClass}>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {[
              { from: 'UNLOADED', to: 'PREPARED', label: 'prepare()' },
              { from: 'PREPARED', to: 'LOADING', label: 'load()' },
              { from: 'LOADING', to: 'LOADED', label: 'success' },
              { from: 'LOADING', to: 'FAILED', label: 'error' },
              { from: 'LOADED', to: 'UNLOADING', label: 'unload()' },
              { from: 'UNLOADING', to: 'UNLOADED', label: 'complete' },
            ].map((t, i) => (
              <div key={i} className="flex items-center gap-1 mb-1">
                <span className={`px-2 py-0.5 rounded text-xs font-mono ${isDark ? 'bg-white/10 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>{t.from}</span>
                <span className="text-aquilia-500 text-xs">→ {t.label} →</span>
                <span className={`px-2 py-0.5 rounded text-xs font-mono ${isDark ? 'bg-white/10 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>{t.to}</span>
                {i < 5 && <span className={`mx-2 ${isDark ? 'text-gray-700' : 'text-gray-300'}`}>|</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* BaseRuntime */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>BaseRuntime</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Abstract base class with FSM state management, health checks, metrics, and memory introspection.
          <code className="text-aquilia-500"> BaseStreamingRuntime</code> extends it with <code className="text-aquilia-500">stream_infer()</code> for LLM token streaming.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.base import BaseRuntime, BaseStreamingRuntime, ModelState

class CustomRuntime(BaseRuntime):
    async def prepare(self, manifest=None, model_dir=""):
        """Initialize runtime resources (download weights, etc.)"""
        self._transition(ModelState.PREPARED)

    async def load(self):
        """Load model into memory."""
        self._transition(ModelState.LOADING)
        self.model = load_model()
        self._transition(ModelState.LOADED)

    async def infer(self, batch) -> list:
        """Execute inference on a batch of requests."""
        return [self.model.predict(req.inputs) for req in batch.requests]

    async def unload(self):
        """Release resources."""
        self._transition(ModelState.UNLOADING)
        del self.model
        self._transition(ModelState.UNLOADED)

    async def health(self) -> dict:
        return {"state": self._state.value, "healthy": self._state == ModelState.LOADED}

    async def metrics(self) -> dict:
        return {"inference_count": self._inference_count}

    async def memory_info(self) -> dict:
        return {"rss_mb": get_process_memory()}`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auto-Selection</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.base import select_runtime

# Automatically selects the best runtime based on manifest
runtime = select_runtime(manifest)

# Selection logic:
# 1. LLM model (VLLM/LlamaCpp/HuggingFace) → PythonRuntime (streaming)
# 2. ONNX framework → ONNXRuntimeAdapter
# 3. GPU-required + Triton available → TritonAdapter
# 4. Default fallback → PythonRuntime`} />
      </section>

      {/* PythonRuntime */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PythonRuntime</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The most versatile runtime, supporting PyTorch (<code className="text-aquilia-500">.pt/.pth</code>), scikit-learn (<code className="text-aquilia-500">.pkl/.joblib</code>),
          Python modules (<code className="text-aquilia-500">.py</code>), and HuggingFace LLMs with full streaming support.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.python_runtime import PythonRuntime

runtime = PythonRuntime()

# Prepare with manifest
await runtime.prepare(manifest, model_dir="./models/sentiment")

# Load model (auto-detects framework from file extension)
await runtime.load()
# .pt/.pth → torch.load()
# .pkl     → pickle.load()
# .joblib  → joblib.load()
# .py      → importlib.util (must have predict() function)
# HuggingFace → AutoModelForCausalLM.from_pretrained()

# Inference
results = await runtime.infer(batch)

# LLM Streaming (if model is LLM)
async for chunk in runtime.stream_infer(request):
    print(chunk.token, end="", flush=True)
    if chunk.is_finished:
        print(f"\\nTokens: {chunk.cumulative_tokens}")

# Token metrics
metrics = await runtime.metrics()
# {
#   "inference_count": 150,
#   "avg_latency_ms": 12.5,
#   "total_tokens_generated": 10000,
#   "total_prompt_tokens": 5000,
#   "total_stream_requests": 50,
# }

# GPU memory info
memory = await runtime.memory_info()
# {
#   "device": "cuda",
#   "gpu_memory_allocated_mb": 2048.5,
#   "gpu_memory_reserved_mb": 3000.0,
#   "gpu_memory_total_mb": 8192.0,
# }`} />
      </section>

      {/* Other Runtimes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Specialized Runtimes</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>ONNXRuntimeAdapter</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.onnx_runtime import ONNXRuntimeAdapter

runtime = ONNXRuntimeAdapter()
await runtime.prepare(manifest, model_dir="./models")
await runtime.load()
# Uses onnxruntime.InferenceSession with optimized execution providers
# Supports: CPUExecutionProvider, CUDAExecutionProvider, TensorrtExecutionProvider
results = await runtime.infer(batch)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>TritonAdapter</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.triton_adapter import TritonAdapter

runtime = TritonAdapter(
    server_url="localhost:8001",  # Triton gRPC endpoint
    model_name="sentiment",
    model_version="1",
)
await runtime.load()
# Connects to NVIDIA Triton Inference Server via gRPC/HTTP
# Supports dynamic batching on Triton's side
results = await runtime.infer(batch)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>TorchServeExporter</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.torchserve_exporter import TorchServeExporter

exporter = TorchServeExporter(
    model_name="sentiment",
    model_path="./model.pt",
    handler="text_classifier",
)
# Generates .mar archive + handler stub for TorchServe deployment
await exporter.export(output_dir="./torchserve")`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>BentoExporter</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.bento_exporter import BentoExporter

exporter = BentoExporter(
    model_name="sentiment",
    model_path="./model.pt",
)
# Generates BentoML service.py + bentofile.yaml for BentoML deployment
await exporter.export(output_dir="./bentoml")`} />
      </section>

      {/* DeviceManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DeviceManager</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handles GPU auto-detection, device selection with fallback chains, memory monitoring, and device locking.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.device_manager import DeviceManager

dm = DeviceManager()

# Auto-detect available devices
devices = dm.detect()
# [DeviceInfo(name="cpu", ...), DeviceInfo(name="cuda:0", memory_total_mb=8192, ...)]

# Select best device with fallback
device = dm.select_device(preferred="cuda:0")
# Falls back: cuda:0 → cuda → mps → cpu

# Device locking (async context manager)
async with dm.acquire("cuda:0") as device:
    # Exclusive access to cuda:0
    model = model.to(device)
    result = model(inputs)
# Device released automatically

# Memory monitoring
dm.refresh()  # Update memory stats
info = dm.device_info("cuda:0")
print(f"GPU memory: {info.memory_used_mb}/{info.memory_total_mb} MB")`} />
      </section>

      {/* InferenceExecutor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>InferenceExecutor</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Wraps ThreadPoolExecutor/ProcessPoolExecutor for async inference without blocking the event loop.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.runtime.executor import InferenceExecutor

executor = InferenceExecutor(
    max_workers=4,
    use_process_pool=False,  # True for CPU-bound, False for GPU-bound
)

# Submit inference job (runs in thread pool)
result = await executor.submit(model.predict, inputs)

# Graceful shutdown
await executor.shutdown(drain_timeout=30.0)

# Active task counter
active = executor.active_count  # For concurrency metrics`} />
      </section>

      <NextSteps
        items={[
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Orchestrator', link: '/docs/mlops/orchestrator' },
          { text: 'Optimizer', link: '/docs/mlops/optimizer' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
