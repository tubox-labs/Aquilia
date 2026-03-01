import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal, Package, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIDeployCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = 'mb-16 scroll-mt-24'
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const codeClass = 'text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400'
  const Table = ({ children }: { children: React.ReactNode }) => (
    <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
      <table className="w-full text-sm text-left">
        <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
          <tr>
            <th className="px-4 py-3 font-medium">Option</th>
            <th className="px-4 py-3 font-medium">Description</th>
            <th className="px-4 py-3 font-medium w-32">Default</th>
          </tr>
        </thead>
        <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
          {children}
        </tbody>
      </table>
    </div>
  )

  const Row = ({ opt, desc, def: defaultVal }: { opt: string; desc: string; def?: string }) => (
    <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
      <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
      <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
      <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{defaultVal || '-'}</td>
    </tr>
  )

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Package className="w-4 h-4" />
          CLI / Deploy Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Deploy &amp; Production Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className={codeClass}>aq deploy</code> command group generates production-ready deployment files by introspecting your workspace. Every output is tailored to the components you actually use — DB, cache, sessions, auth, mail, MLOps, WebSockets, and effects.
        </p>
      </div>

      {/* Overview Grid */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Package className="w-6 h-6 text-aquilia-500" />
          Sub-Commands
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { cmd: 'aq deploy dockerfile', desc: 'Multi-stage Dockerfile — production, dev, and MLOps variants' },
            { cmd: 'aq deploy compose', desc: 'docker-compose.yml with auto-detected services (DB, Redis, Nginx)' },
            { cmd: 'aq deploy kubernetes', desc: 'Full Kubernetes manifest suite — Deployment, Service, Ingress, HPA, PDB' },
            { cmd: 'aq deploy nginx', desc: 'Nginx reverse-proxy configuration for upstream Aquilia servers' },
            { cmd: 'aq deploy ci', desc: 'CI/CD pipeline templates (GitHub Actions / GitLab CI)' },
            { cmd: 'aq deploy monitoring', desc: 'Prometheus + Grafana provisioning with Aquilia dashboards' },
            { cmd: 'aq deploy env', desc: '.env.example template with all configurable environment variables' },
            { cmd: 'aq deploy makefile', desc: 'Makefile with dev, build, test, and deploy targets' },
            { cmd: 'aq deploy all', desc: 'Generate everything at once — all deployment files in one command' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className={`font-bold text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.cmd}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Global Flags */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Global Flags</h2>
        <p className={pClass}>
          All <code className={codeClass}>aq deploy</code> sub-commands share these flags, set on the group or per command:
        </p>
        <Table>
          <Row opt="--force, -f" desc="Overwrite existing files (by default, existing files are skipped)" def="false" />
          <Row opt="--dry-run" desc="Preview what would be generated without writing any files" def="false" />
        </Table>
      </section>

      {/* Dockerfile */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy dockerfile
        </h2>
        <p className={pClass}>
          Generates a production-optimized, multi-stage Dockerfile with non-root user, health checks, tini init, BuildKit cache mounts, and artifact compilation baked in.
        </p>
        <Table>
          <Row opt="--dev" desc="Generate Dockerfile.dev with hot-reload support" def="false" />
          <Row opt="--mlops" desc="Generate Dockerfile.mlops for model-serving workloads" def="false" />
          <Row opt="--output, -o" desc="Output directory" def="." />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Production Dockerfile + .dockerignore
aq deploy dockerfile

# Development Dockerfile with hot-reload
aq deploy dockerfile --dev

# MLOps model-serving Dockerfile
aq deploy dockerfile --mlops

# Generate all variants at once
aq deploy dockerfile --dev --mlops

# Force overwrite existing
aq deploy -f dockerfile`}</CodeBlock>
        <h3 className={h3Class}>What Gets Generated</h3>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Dockerfile</strong> — production multi-stage with pip install, artifact compilation, non-root user</li>
          <li><strong>.dockerignore</strong> — excludes venv, __pycache__, .git, tests, docs</li>
          <li><strong>Dockerfile.dev</strong> — dev variant with watchfiles hot-reload, debug mode</li>
          <li><strong>Dockerfile.mlops</strong> — model-serving variant with MLOps dependencies, model volume mounts</li>
        </ul>
      </section>

      {/* Compose */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy compose
        </h2>
        <p className={pClass}>
          Generates <code className={codeClass}>docker-compose.yml</code> with auto-detected services based on your workspace configuration. Uses compose profiles for optional services.
        </p>
        <Table>
          <Row opt="--dev" desc="Also generate docker-compose.dev.yml with volume mounts" def="false" />
          <Row opt="--monitoring" desc="Include Prometheus + Grafana services" def="false" />
          <Row opt="--output, -o" desc="Output directory" def="." />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Standard compose file
aq deploy compose

# With monitoring stack
aq deploy compose --monitoring

# With dev overrides
aq deploy compose --dev

# Typical usage after generation
docker compose up -d
docker compose --profile proxy up -d        # Include Nginx
docker compose --profile monitoring up -d   # Include Prometheus + Grafana`}</CodeBlock>
        <h3 className={h3Class}>Auto-Detected Services</h3>
        <p className={pClass}>
          The generator introspects <code className={codeClass}>workspace.py</code>, <code className={codeClass}>config/</code>, and <code className={codeClass}>modules/</code> to detect:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li>PostgreSQL / MySQL database with proper healthchecks</li>
          <li>Redis for cache, sessions, or WebSocket adapter</li>
          <li>MLOps model server container</li>
          <li>Nginx reverse proxy with upstream configuration</li>
          <li>Prometheus + Grafana monitoring stack</li>
          <li>Mail services (if configured)</li>
        </ul>
      </section>

      {/* Kubernetes */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy kubernetes
        </h2>
        <p className={pClass}>
          Generates a complete Kubernetes manifest suite for production deployments, including all standard resources.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Output directory for K8s manifests" def="k8s" />
          <Row opt="--mlops" desc="Force include MLOps-specific manifests" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Generate K8s manifests in k8s/ directory
aq deploy kubernetes

# Custom output directory
aq deploy kubernetes -o deploy/k8s

# Force MLOps manifests
aq deploy kubernetes --mlops`}</CodeBlock>
        <h3 className={h3Class}>Generated Resources</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
          {[
            'Namespace', 'Deployment', 'Service', 'Ingress',
            'HPA (Horizontal Pod Autoscaler)', 'PDB (Pod Disruption Budget)',
            'Network Policy', 'ConfigMap', 'Secret',
            'ServiceAccount', 'PVC (Persistent Volume Claim)',
            'CronJob (maintenance)', 'Init containers (DB readiness)',
          ].map((r, i) => (
            <div key={i} className={`flex items-center gap-2 p-2 rounded-lg text-sm ${isDark ? 'text-gray-300 bg-white/5' : 'text-gray-700 bg-gray-50'}`}>
              <ArrowRight className="w-3 h-3 text-aquilia-500 flex-shrink-0" />
              {r}
            </div>
          ))}
        </div>
      </section>

      {/* Nginx */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy nginx
        </h2>
        <p className={pClass}>
          Generates an Nginx reverse-proxy configuration file that routes traffic to your Aquilia application, including WebSocket upgrade handling, static file serving, security headers, and upstream health checks.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Output directory" def="deploy/nginx" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`aq deploy nginx
aq deploy nginx --output deploy/

# Dry-run preview
aq deploy nginx --dry-run`}</CodeBlock>
      </section>

      {/* CI */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy ci
        </h2>
        <p className={pClass}>
          Generates CI/CD pipeline templates for GitHub Actions or GitLab CI. Includes stages for linting, testing, building Docker images, and deploying.
        </p>
        <Table>
          <Row opt="--provider" desc="CI provider (github, gitlab)" def="github" />
          <Row opt="--output, -o" desc="Output directory" def="auto" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# GitHub Actions (default)
aq deploy ci

# GitLab CI
aq deploy ci --provider gitlab

# Custom output directory
aq deploy ci --output .github/workflows/`}</CodeBlock>
      </section>

      {/* Monitoring */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy monitoring
        </h2>
        <p className={pClass}>
          Generates Prometheus scrape configuration and Grafana dashboard provisioning files pre-configured for Aquilia metrics.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Output directory" def="deploy" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`aq deploy monitoring
aq deploy monitoring --output monitoring/`}</CodeBlock>
      </section>

      {/* Env */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy env
        </h2>
        <p className={pClass}>
          Generates a <code className={codeClass}>.env.example</code> template with all configurable environment variables detected from your workspace, with sensible defaults and documentation comments.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Output directory" def="." />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`aq deploy env`}</CodeBlock>
      </section>

      {/* Makefile */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy makefile
        </h2>
        <p className={pClass}>
          Generates a <code className={codeClass}>Makefile</code> with common development, build, test, and deployment targets.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Output directory" def="." />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`aq deploy makefile`}</CodeBlock>
      </section>

      {/* All */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq deploy all
        </h2>
        <p className={pClass}>
          Generate every deployment file at once — Dockerfile, Compose, Kubernetes, Nginx, CI, monitoring, .env, and Makefile.
        </p>
        <Table>
          <Row opt="--output, -o" desc="Base output directory" def="." />
          <Row opt="--monitoring" desc="Include Prometheus + Grafana services" def="true" />
          <Row opt="--ci-provider" desc="CI provider: github, gitlab, or both" def="github" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Generate everything
aq deploy all

# With both CI providers
aq deploy all --ci-provider both

# Force overwrite all existing files
aq deploy all --force

# Preview what would be generated
aq deploy all --dry-run`}</CodeBlock>
      </section>

      {/* Workspace Introspection */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Workspace Introspection</h2>
        <p className={pClass}>
          All deploy generators use <code className={codeClass}>WorkspaceIntrospector</code> to build a context dictionary from your workspace. It reads:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><code className={codeClass}>workspace.py</code> — modules, integrations, name, version</li>
          <li><code className={codeClass}>config/</code> — YAML config files for each environment</li>
          <li><code className={codeClass}>modules/</code> — manifest.py in each module for component detection</li>
          <li><code className={codeClass}>pyproject.toml</code> — Python version, dependencies</li>
        </ul>
        <p className={pClass}>
          This context determines which services to include in Compose, which K8s resources to generate, and what the Dockerfile installs.
        </p>
      </section>

      <NextSteps
        items={[
          { text: 'Core Commands', link: '/docs/cli/core' },
          { text: 'Artifact Commands', link: '/docs/cli/artifacts' },
          { text: 'Database Commands', link: '/docs/cli/database' },
          { text: 'MLOps Commands', link: '/docs/cli/mlops' },
        ]}
      />
    </div>
  )
}
