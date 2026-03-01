import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsRelease() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Release & Rollouts
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Release & Rollouts
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Safe model deployments with the <code className="text-aquilia-500">RolloutEngine</code> for canary releases
          with metric-gated advancement and automatic rollback, plus CI/CD template generation for
          GitHub Actions and Docker.
        </p>
      </div>

      {/* RolloutEngine */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RolloutEngine</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Rollout Phases</h3>
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { phase: 'PENDING', color: 'text-yellow-400' },
            { phase: 'IN_PROGRESS', color: 'text-blue-400' },
            { phase: 'PAUSED', color: 'text-orange-400' },
            { phase: 'COMPLETED', color: 'text-green-400' },
            { phase: 'ROLLED_BACK', color: 'text-red-400' },
            { phase: 'FAILED', color: 'text-red-500' },
          ].map((p) => (
            <span key={p.phase} className={`px-3 py-1 rounded-full text-xs font-mono ${p.color} ${isDark ? 'bg-white/10' : 'bg-gray-100'}`}>
              {p.phase}
            </span>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.release.rollout import RolloutEngine
from aquilia.mlops._types import RolloutConfig

engine = RolloutEngine(
    version_manager=version_manager,
    traffic_router=traffic_router,
    metrics_collector=metrics_collector,
)

# Configure rollout
config = RolloutConfig(
    model_name="sentiment",
    canary_version="3.0.0",
    initial_weight=0.05,      # Start with 5% traffic
    max_weight=1.0,            # Full rollout target
    step_weight=0.10,          # Increase by 10% per step
    error_rate_threshold=0.01, # Rollback if errors > 1%
    latency_p99_threshold=100, # Rollback if p99 > 100ms
    min_requests_per_step=100, # Minimum requests before advancing
)

# Start the rollout
await engine.start(config)
# Sets canary weight to 5%, phase → IN_PROGRESS`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Metric-Gated Advancement</h3>
        <CodeBlock language="python" code={`# Advance the rollout (checks metrics before advancing)
result = await engine.advance("sentiment")
# 1. Collect metrics for canary version
# 2. Check error_rate < error_rate_threshold
# 3. Check latency_p99 < latency_p99_threshold
# 4. Check request_count >= min_requests_per_step
# 5. If ALL pass → increase weight by step_weight
# 6. If ANY fail → auto-rollback

# result = {
#   "advanced": True,
#   "new_weight": 0.15,
#   "metrics": {"error_rate": 0.005, "latency_p99": 45.2}
# }

# Or if metrics fail:
# result = {
#   "advanced": False,
#   "rolled_back": True,
#   "reason": "error_rate 0.025 exceeds threshold 0.01"
# }`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Complete or Rollback</h3>
        <CodeBlock language="python" code={`# Complete the rollout (promote canary to active)
await engine.complete("sentiment")
# 1. version_manager.promote("sentiment", "3.0.0")
# 2. traffic_router.clear_canary("sentiment")
# 3. phase → COMPLETED

# Manual rollback
await engine.rollback("sentiment")
# 1. traffic_router.clear_canary("sentiment")
# 2. phase → ROLLED_BACK

# List active rollouts
rollouts = engine.list_active()
# [RolloutState(model="sentiment", phase=IN_PROGRESS, weight=0.15, ...)]`} />
      </section>

      {/* CI/CD Templates */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CI/CD Templates</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Generate production-ready CI/CD configurations for automated model deployments.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>GitHub Actions Workflow</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.release.ci import generate_ci_workflow

workflow = generate_ci_workflow(
    model_name="sentiment",
    registry_url="registry.example.com",
    deploy_target="staging",
)

# Generates a complete .github/workflows/mlops-deploy.yml:
# - Trigger: push to main, tags matching v*
# - Jobs:
#   1. build: Install deps, run tests, lint
#   2. publish: Build modelpack, push to registry
#   3. deploy-staging: Deploy to staging K8s cluster`} />
        <CodeBlock language="yaml" code={`# Generated workflow structure:
name: MLOps Model Deploy
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/

  publish:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: aquilia mlops pack build --name sentiment
      - run: aquilia mlops registry push --url registry.example.com

  deploy-staging:
    needs: publish
    runs-on: ubuntu-latest
    steps:
      - run: kubectl apply -f deploy/k8s/serving.yaml
      - run: kubectl rollout status deployment/mlops-serving`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dockerfile</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.release.ci import generate_dockerfile

dockerfile = generate_dockerfile(
    base_image="python:3.11-slim",
    model_name="sentiment",
    port=8080,
)`} />
        <CodeBlock language="dockerfile" code={`# Generated Dockerfile:
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:8080/mlops/healthz || exit 1

CMD ["python", "-m", "aquilia", "serve", "--host", "0.0.0.0", "--port", "8080"]`} />
      </section>

      <NextSteps
        items={[
          { text: 'Scheduler', link: '/docs/mlops/scheduler' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
          { text: 'Observability', link: '/docs/mlops/observability' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
