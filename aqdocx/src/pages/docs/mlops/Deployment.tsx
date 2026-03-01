import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsDeployment() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Deployment
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Deployment
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Production-ready Kubernetes manifests, Grafana dashboards, model optimization pipelines,
          and edge export for deploying Aquilia MLOps models at scale.
        </p>
      </div>

      {/* K8s Serving */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Kubernetes: Serving</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">deploy/k8s/serving.yaml</code> provides a complete Deployment,
          Service, and HorizontalPodAutoscaler for model serving.
        </p>
        <CodeBlock language="yaml" code={`# Deployment: 2 replicas with GPU support
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlops-serving
  labels:
    app: aquilia-mlops
    component: serving
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aquilia-mlops
  template:
    spec:
      containers:
        - name: serving
          image: aquilia/mlops-serving:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
              nvidia.com/gpu: "1"
            limits:
              memory: "8Gi"
              cpu: "4"
              nvidia.com/gpu: "1"
          # K8s health probes (mapped to MLOps endpoints)
          livenessProbe:
            httpGet:
              path: /mlops/healthz
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /mlops/readyz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
          env:
            - name: AQUILIA_MLOPS_DEVICE
              value: "cuda"
            - name: AQUILIA_MLOPS_MAX_BATCH_SIZE
              value: "32"`} />

        <CodeBlock language="yaml" code={`# Service: ClusterIP for internal access
apiVersion: v1
kind: Service
metadata:
  name: mlops-serving
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
  selector:
    app: aquilia-mlops

---
# HPA: Auto-scale based on CPU + GPU metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mlops-serving-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mlops-serving
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70`} />
      </section>

      {/* K8s Registry */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Kubernetes: Registry</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Deploy the model registry with persistent storage for model artifacts.
        </p>
        <CodeBlock language="yaml" code={`# Registry Deployment + PVCs
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlops-registry
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: registry
          image: aquilia/mlops-registry:latest
          ports:
            - containerPort: 8081
          volumeMounts:
            - name: registry-data
              mountPath: /data/registry
            - name: model-data
              mountPath: /data/models
      volumes:
        - name: registry-data
          persistentVolumeClaim:
            claimName: registry-pvc
        - name: model-data
          persistentVolumeClaim:
            claimName: model-pvc

---
# 50Gi for registry database + metadata
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: registry-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi

---
# 20Gi for model artifact storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 20Gi`} />
      </section>

      {/* Grafana Dashboard */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Grafana Dashboard</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Pre-built Grafana dashboard with 5 panels visualizing MLOps Prometheus metrics.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { panel: 'Inference RPS', type: 'Time Series', query: 'rate(aquilia_mlops_request_total[5m])' },
            { panel: 'Latency Distribution', type: 'Time Series', query: 'histogram_quantile(0.50/0.95/0.99, ...)' },
            { panel: 'Active Models', type: 'Gauge', query: 'aquilia_mlops_active_models' },
            { panel: 'Error Rate', type: 'Time Series', query: 'rate(aquilia_mlops_error_total[5m]) / rate(aquilia_mlops_request_total[5m])' },
            { panel: 'Batch Utilization', type: 'Bar Gauge', query: 'aquilia_mlops_batch_utilization_ratio' },
          ].map((p, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center justify-between mb-2">
                <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{p.panel}</h4>
                <span className={`text-xs px-2 py-0.5 rounded ${isDark ? 'bg-white/10 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>{p.type}</span>
              </div>
              <code className="text-xs text-aquilia-500 break-all">{p.query}</code>
            </div>
          ))}
        </div>
        <CodeBlock language="bash" code={`# Deploy Grafana dashboard
kubectl create configmap mlops-dashboard \\
  --from-file=aquilia/mlops/deploy/grafana/mlops-dashboard.json

# Or use Grafana provisioning:
cp aquilia/mlops/deploy/grafana/mlops-dashboard.json \\
  /etc/grafana/provisioning/dashboards/`} />
      </section>

      {/* Optimization Pipeline */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Model Optimization</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Quantize and optimize models before deployment for reduced memory and faster inference.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.optimizer.pipeline import OptimizationPipeline

pipeline = OptimizationPipeline()

# ONNX Quantization (INT8 or FP16)
result = await pipeline.quantize_onnx(
    model_path="./model.onnx",
    output_path="./model_int8.onnx",
    quantization_type="int8",  # "int8" | "fp16" | "dynamic"
)
# OptimizationResult(
#   original_size_mb=450.0,
#   optimized_size_mb=115.0,
#   compression_ratio=3.91,
# )

# PyTorch Quantization
result = await pipeline.quantize_pytorch(
    model=pytorch_model,
    output_path="./model_quantized.pt",
    quantization_type="dynamic",  # torch.quantization.quantize_dynamic
    dtype="qint8",
)

# Quantization presets available:
# INT8, FP16, DYNAMIC, INT4, GPTQ, AWQ, GGUF_Q4_0, GGUF_Q4_1,
# GGUF_Q5_0, GGUF_Q5_1, GGUF_Q8_0, NONE`} />
      </section>

      {/* Edge Export */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Edge Export</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Export models to edge formats for mobile, embedded, and specialized hardware deployment.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            { format: 'TFLite', desc: 'TensorFlow Lite for mobile/embedded. Uses tf.lite.TFLiteConverter.' },
            { format: 'CoreML', desc: 'Apple CoreML for iOS/macOS. Uses coremltools.' },
            { format: 'ONNX Quantized', desc: 'ONNX with INT8/FP16 quantization for edge inference.' },
            { format: 'TensorRT', desc: 'NVIDIA TensorRT for GPU-optimized inference.' },
          ].map((f, i) => (
            <div key={i} className={boxClass}>
              <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{f.format}</h4>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{f.desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" code={`from aquilia.mlops.optimizer.export import EdgeExporter, profile_model

exporter = EdgeExporter()

# Export to TFLite
await exporter.to_tflite(
    model_path="./model.h5",
    output_path="./model.tflite",
    quantize=True,  # Post-training INT8 quantization
)

# Export to CoreML
await exporter.to_coreml(
    model_path="./model.pt",
    output_path="./model.mlmodel",
    input_shape=[1, 3, 224, 224],
)

# Export to TensorRT
await exporter.to_tensorrt(
    model_path="./model.onnx",
    output_path="./model.trt",
    precision="fp16",  # "fp32" | "fp16" | "int8"
    max_batch_size=32,
)

# Profile model (heuristic size/speed estimation)
profile = profile_model("./model.pt")
# {
#   "file_size_mb": 450.0,
#   "estimated_params": 110_000_000,
#   "recommended_quantization": "int8",
#   "estimated_speedup": "3.5x",
# }`} />
      </section>

      {/* Full Deployment Workflow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Full Deployment Workflow</h2>
        <CodeBlock language="python" code={`# Complete deployment pipeline:

# 1. Optimize model
from aquilia.mlops.optimizer.pipeline import OptimizationPipeline
optimizer = OptimizationPipeline()
result = await optimizer.quantize_onnx("./model.onnx", "./model_int8.onnx", "int8")

# 2. Build modelpack
from aquilia.mlops.pack.builder import ModelpackBuilder
pack = ModelpackBuilder() \\
    .set_name("sentiment") \\
    .set_version("2.1.0") \\
    .add_artifact("./model_int8.onnx") \\
    .set_manifest(manifest) \\
    .build()

# 3. Sign the artifact
from aquilia.mlops.security.signing import ArtifactSigner
signer = ArtifactSigner(algorithm="hmac", secret_key=secret)
signature = signer.sign(pack.archive_path)

# 4. Publish to registry
await registry.publish(pack, signature=signature)

# 5. Generate CI/CD pipeline
from aquilia.mlops.release.ci import generate_ci_workflow, generate_dockerfile
generate_ci_workflow("sentiment", "registry.example.com", "production")
generate_dockerfile("python:3.11-slim", "sentiment", 8080)

# 6. Deploy to Kubernetes
# kubectl apply -f deploy/k8s/serving.yaml
# kubectl apply -f deploy/k8s/registry.yaml

# 7. Start canary rollout
from aquilia.mlops.release.rollout import RolloutEngine
await rollout_engine.start(rollout_config)

# 8. Monitor with Grafana dashboard
# Import deploy/grafana/mlops-dashboard.json`} />
      </section>

      <NextSteps
        items={[
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
          { text: 'Release & Rollouts', link: '/docs/mlops/release' },
          { text: 'Scheduler', link: '/docs/mlops/scheduler' },
          { text: 'Overview', link: '/docs/mlops' },
        ]}
      />
    </div>
  )
}
