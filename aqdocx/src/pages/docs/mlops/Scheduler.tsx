import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsScheduler() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Scheduler
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Scheduler & Autoscaling
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Intelligent model placement and autoscaling. The <code className="text-aquilia-500">Autoscaler</code> evaluates
          GPU utilization, token throughput, concurrency, and latency to make scaling decisions,
          while the <code className="text-aquilia-500">PlacementScheduler</code> uses weighted scoring for
          optimal node selection.
        </p>
      </div>

      {/* Autoscaler */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Autoscaler</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scaling Policy</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.scheduler.autoscaler import Autoscaler, ScalingPolicy

policy = ScalingPolicy(
    # Replica bounds
    min_replicas=1,
    max_replicas=10,

    # GPU-based scaling (highest priority)
    gpu_utilization_target=0.75,     # Scale up above 75%
    gpu_scale_up_threshold=0.85,
    gpu_scale_down_threshold=0.30,

    # Token throughput (LLM-specific)
    tokens_per_second_target=100.0,
    token_scale_up_threshold=0.90,   # Scale up if near saturation

    # Concurrency-based
    max_concurrent_requests=50,
    concurrency_scale_up_threshold=0.80,

    # Latency-based
    latency_p99_target_ms=100.0,
    latency_scale_up_threshold=1.5,  # Scale up if 1.5x target

    # Scale-down cooldown
    cooldown_seconds=300,            # 5 min between scale-downs
    scale_down_delay_seconds=120,    # Wait 2 min before scaling down

    # Windowed metrics
    window_size=60,                  # 60-sample sliding window
)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Evaluation Priority</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The autoscaler evaluates metrics in priority order. The first trigger that fires determines
          the scaling action.
        </p>
        <div className={boxClass}>
          <ol className={`space-y-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            {[
              { priority: '1', metric: 'GPU Utilization', desc: 'Scale up if GPU util > 85%. Strongest signal for GPU-bound models.' },
              { priority: '2', metric: 'Token Throughput', desc: 'Scale up if tokens/sec nearing saturation. Critical for LLM serving.' },
              { priority: '3', metric: 'Concurrency', desc: 'Scale up if concurrent requests > 80% of limit. Prevents request queuing.' },
              { priority: '4', metric: 'Latency p99', desc: 'Scale up if p99 latency exceeds 1.5x target. User-experience driven.' },
              { priority: '5', metric: 'Scale Down', desc: 'Scale down if ALL metrics are well below thresholds AND cooldown elapsed.' },
            ].map((item) => (
              <li key={item.priority} className="flex gap-3">
                <span className="text-aquilia-500 font-mono font-bold">{item.priority}.</span>
                <div>
                  <span className="font-semibold">{item.metric}</span>
                  <span className={`ml-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>— {item.desc}</span>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <CodeBlock language="python" code={`autoscaler = Autoscaler(policy=policy, metrics=metrics_collector)

# Evaluate scaling decision
decision = autoscaler.evaluate(current_replicas=3)
# ScalingDecision(
#   action="scale_up",      # "scale_up" | "scale_down" | "no_change"
#   target_replicas=5,
#   reason="gpu_utilization 0.92 exceeds threshold 0.85",
#   metrics={"gpu_util": 0.92, "concurrency": 35, "latency_p99": 45.0},
# )

# Apply the decision
if decision.action == "scale_up":
    await scale_deployment(decision.target_replicas)`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Kubernetes HPA Manifest</h3>
        <CodeBlock language="python" code={`# Generate K8s HorizontalPodAutoscaler manifest
hpa_yaml = autoscaler.generate_hpa_manifest(
    deployment_name="mlops-serving",
    namespace="production",
)

# Output: Complete HPA YAML with custom metrics:
# - GPU utilization (nvidia.com/gpu_utilization)
# - Token throughput (aquilia.mlops/tokens_per_second)
# - Request concurrency (aquilia.mlops/concurrent_requests)`} />
        <CodeBlock language="yaml" code={`apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mlops-serving-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mlops-serving
  minReplicas: 1
  maxReplicas: 10
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
  metrics:
    - type: Pods
      pods:
        metric:
          name: nvidia.com/gpu_utilization
        target:
          type: AverageValue
          averageValue: "75"
    - type: Pods
      pods:
        metric:
          name: aquilia.mlops/tokens_per_second
        target:
          type: AverageValue
          averageValue: "100"`} />
      </section>

      {/* PlacementScheduler */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PlacementScheduler</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Selects the optimal node for model placement using a weighted scoring algorithm.
          Supports GPU-aware scheduling, affinity rules, and hard constraints.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>NodeInfo</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.scheduler.placement import PlacementScheduler, NodeInfo, PlacementRequest

nodes = [
    NodeInfo(
        node_id="gpu-node-1",
        cpu_available=8,
        memory_available_mb=32768,
        gpu_count=2,
        gpu_memory_available_mb=16384,
        gpu_compute_capability=8.0,  # Ampere
        load_average=0.3,
        labels={"zone": "us-east-1a", "tier": "gpu"},
    ),
    NodeInfo(
        node_id="cpu-node-1",
        cpu_available=16,
        memory_available_mb=65536,
        gpu_count=0,
        gpu_memory_available_mb=0,
        load_average=0.5,
        labels={"zone": "us-east-1b", "tier": "cpu"},
    ),
]`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Placement Request & Scoring</h3>
        <CodeBlock language="python" code={`request = PlacementRequest(
    model_name="llama-7b",
    memory_required_mb=8192,
    gpu_required=True,
    min_gpu_memory_mb=8000,
    min_compute_capability=7.0,  # Volta or better
    preferred_zone="us-east-1a",
    is_llm=True,                 # LLM hint: prefer GPU memory
)

scheduler = PlacementScheduler(nodes=nodes)

# Score and rank nodes
placement = scheduler.schedule(request)
# PlacementScore(
#   node_id="gpu-node-1",
#   score=0.87,
#   breakdown={
#     "affinity": 0.20,          # Zone match
#     "memory": 0.18,            # Available memory
#     "gpu_memory": 0.25,        # GPU memory headroom
#     "load": 0.12,              # Low load bonus
#     "cold_start": 0.12,        # No existing models → fast start
#   }
# )

# Hard constraints (automatic rejection):
# - GPU required but node has no GPUs → REJECTED
# - Insufficient GPU memory → REJECTED
# - Compute capability below minimum → REJECTED
# - Insufficient CPU memory → REJECTED`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scoring Weights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { factor: 'Affinity', weight: '0.25', desc: 'Label/zone matching. Prefer colocation.' },
            { factor: 'Memory', weight: '0.20', desc: 'Available CPU memory relative to requirement.' },
            { factor: 'GPU Memory', weight: '0.25', desc: 'GPU memory headroom. Highest weight for LLMs.' },
            { factor: 'Load', weight: '0.15', desc: 'Inverse of current load. Prefer idle nodes.' },
            { factor: 'Cold Start', weight: '0.15', desc: 'Prefer nodes with fewer loaded models.' },
          ].map((f, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center justify-between mb-1">
                <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{f.factor}</h4>
                <span className="text-aquilia-500 font-mono text-sm">{f.weight}</span>
              </div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{f.desc}</p>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Rebalancing</h3>
        <CodeBlock language="python" code={`# Suggest model moves to balance cluster load
suggestions = scheduler.rebalance()
# [
#   RebalanceSuggestion(
#     model="classifier",
#     from_node="gpu-node-1",   # Overloaded
#     to_node="gpu-node-2",     # Underutilized
#     reason="Load imbalance: 0.92 vs 0.25",
#   ),
# ]`} />
      </section>

      <NextSteps
        items={[
          { text: 'Security', link: '/docs/mlops/security' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
