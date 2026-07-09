import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Package } from 'lucide-react'

export function CLIDeployCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const listClass = "space-y-2 pl-5 list-disc"
  const itemClass = `text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Package className="w-4 h-4" />
          CLI / Deploy
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Deploy &amp; Production Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq deploy</code> command group generates production-ready deployment configurations (Docker, Kubernetes, reverse-proxy configs, monitoring dashboards) by scanning your active workspace modules.
        </p>
      </div>

      {/* aq deploy dockerfile */}
      <section id="deploy-dockerfile" className={sectionClass}>
        <h2 className={h2Class}>aq deploy dockerfile</h2>
        <p className={pClass}>
          Generates optimized multi-stage Dockerfiles configured for compiled Aquilia artifacts.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Generate standard production Dockerfile
aq deploy dockerfile

# Generate development Dockerfile with hot reload
aq deploy dockerfile --dev`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--dev', 'Creates a Dockerfile.dev configuration enabling watchfiles hot-reload.'],
                ['--mlops', 'Creates multi-stage GPU-compatible Docker containers for ML serving.'],
                ['--output, -o', 'Destination directory (defaults to .).']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq deploy compose */}
      <section id="deploy-compose" className={sectionClass}>
        <h2 className={h2Class}>aq deploy compose</h2>
        <p className={pClass}>
          Generates a <code className="text-aquilia-500 font-mono">docker-compose.yml</code> file containing configuration details of databases, caches, proxies, and schedulers matching your modules.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Generate docker-compose config
aq deploy compose

# Include Prometheus and Grafana monitoring stacks
aq deploy compose --monitoring`}</CodeBlock>
      </section>

      {/* aq deploy kubernetes */}
      <section id="deploy-kubernetes" className={sectionClass}>
        <h2 className={h2Class}>aq deploy kubernetes</h2>
        <p className={pClass}>
          Generates a complete suite of Kubernetes manifest templates, including:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>Deployments &amp; Services:</strong> Standard ASGI app process pod declarations.</li>
          <li className={itemClass}><strong>Ingress &amp; HPA:</strong> Auto-scaler resources and routing maps.</li>
          <li className={itemClass}><strong>Secrets &amp; ConfigMaps:</strong> Safe storage injection mapping environment variables.</li>
        </ul>
        <CodeBlock language="bash" filename="Terminal">aq deploy kubernetes --output=deploy/k8s</CodeBlock>
      </section>

      {/* aq deploy nginx */}
      <section id="deploy-nginx" className={sectionClass}>
        <h2 className={h2Class}>aq deploy nginx</h2>
        <p className={pClass}>
          Scaffolds an Nginx reverse proxy server block, pre-configured with security headers, SSL directives, gzip compression, and websocket connection upgrades.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq deploy nginx</CodeBlock>
      </section>

      {/* aq deploy ci */}
      <section id="deploy-ci" className={sectionClass}>
        <h2 className={h2Class}>aq deploy ci</h2>
        <p className={pClass}>
          Creates automated continuous integration pipeline configurations (GitHub Actions or GitLab CI) to test, compile manifests, run doctor diagnostics, and build images.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# GitHub Actions workflow
aq deploy ci --provider=github

# GitLab CI configuration
aq deploy ci --provider=gitlab`}</CodeBlock>
      </section>

      {/* aq deploy monitoring */}
      <section id="deploy-monitoring" className={sectionClass}>
        <h2 className={h2Class}>aq deploy monitoring</h2>
        <p className={pClass}>
          Generates Prometheus scrape configurations and Grafana dashboard files to monitor request counts, latency, memory use, cache hits, and queue metrics.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq deploy monitoring</CodeBlock>
      </section>

      {/* aq deploy env */}
      <section id="deploy-env" className={sectionClass}>
        <h2 className={h2Class}>aq deploy env</h2>
        <p className={pClass}>
          Scaffolds a clean <code className="text-aquilia-500 font-mono">.env.example</code> file populated with all configurable configuration keys detected in your modules and workspace settings.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq deploy env</CodeBlock>
      </section>

      {/* aq deploy makefile */}
      <section id="deploy-makefile" className={sectionClass}>
        <h2 className={h2Class}>aq deploy makefile</h2>
        <p className={pClass}>
          Generates a convenience <code className="text-aquilia-500 font-mono">Makefile</code> with standard targets: <code className="text-aquilia-500 font-mono">make run</code>, <code className="text-aquilia-500 font-mono">make test</code>, <code className="text-aquilia-500 font-mono">make compile</code>, <code className="text-aquilia-500 font-mono">make build</code>, and <code className="text-aquilia-500 font-mono">make migrate</code>.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq deploy makefile</CodeBlock>
      </section>

      {/* aq deploy all */}
      <section id="deploy-all" className={sectionClass}>
        <h2 className={h2Class}>aq deploy all</h2>
        <p className={pClass}>
          Utility command that runs all deploy command generators at once, outputting a complete, ready-to-run deploy folder.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq deploy all --monitoring --ci-provider=github</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
