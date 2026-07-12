import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Cloud, Layers, Settings, Terminal, Shield, Zap, GitBranch } from 'lucide-react'
import { Link } from 'react-router-dom'

function DeploymentArchitecture() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="w-full flex justify-center py-6 bg-transparent">
      <svg viewBox="0 0 900 340" className="w-full h-auto drop-shadow-2xl font-mono select-none">
        <defs>
          <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
          </linearGradient>
          <radialGradient id="glowGreen" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
          </radialGradient>
          <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Glowing Halos Behind Nodes */}
        <circle cx="80" cy="170" r="50" fill="url(#glowGreen)" />
        <circle cx="240" cy="110" r="50" fill="url(#glowGreen)" />
        <circle cx="400" cy="90" r="50" fill="url(#glowBlue)" />
        <circle cx="560" cy="230" r="50" fill="url(#glowBlue)" />
        <circle cx="720" cy="190" r="50" fill="url(#glowPurple)" />
        <circle cx="840" cy="170" r="50" fill="url(#glowGreen)" />

        {/* Connecting Wave Lines (Bundle of Light Fibers) */}
        <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="url(#waveGrad)" strokeWidth="4.5" strokeLinecap="round" />
        <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 8" strokeLinecap="round" />

        {/* Node 1: Diagnostics */}
        <g transform="translate(80, 170)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">DIAGNOSTICS</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">aq doctor &amp; validate</text>
        </g>

        {/* Node 2: Compilation */}
        <g transform="translate(240, 110)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">COMPILATION</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">docker build amd64</text>
        </g>

        {/* Node 3: Registry Push */}
        <g transform="translate(400, 90)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#3b82f6" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">REGISTRY PUSH</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">docker push image</text>
        </g>

        {/* Node 4: Resolution */}
        <g transform="translate(560, 230)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#3b82f6" />
          <text x="0" y="-24" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">RESOLUTION</text>
          <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="#71717a">owner &amp; config lookup</text>
        </g>

        {/* Node 5: Provisioning */}
        <g transform="translate(720, 190)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#a855f7" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#a855f7" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">PROVISIONING</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">api deploy &amp; vars sync</text>
        </g>

        {/* Node 6: Liveness Poll */}
        <g transform="translate(840, 170)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">LIVENESS POLL</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">wait live or rollback</text>
        </g>
      </svg>
    </div>
  )
}

export function OverviewPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Cloud className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Providers Overview
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Cloud provider integrations, architecture, and deployment strategy</p>
          </div>
        </div>

        <p className={`text-lg ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia features a highly decoupled, container-first deployment pipeline. While the framework provides CLI commands 
          to generate raw configuration files for Kubernetes, Nginx, Docker Compose, and Makefiles, it also offers 
          first-class PaaS provider integrations, allowing developers to configure and deploy workspaces in a single command.
        </p>
      </div>

      {/* Deployment Strategy */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Container-First Strategy
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia treats containerization as a fundamental building block, rather than an afterthought. Because the runtime is built 
          around self-contained ASGI structures and manifest configurations, any Aquilia workspace can be packaged into an OCI-compliant 
          container image. The framework leverages this by exposing a two-tiered deployment strategy:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="border-l border-aquilia-500/25 pl-4">
            <h3 className={`text-lg font-semibold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Terminal className="w-4.5 h-4.5 text-aquilia-400" />
              1. Static Infrastructure-as-Code
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Generate local configs via commands like <code>aq deploy dockerfile</code>, <code>aq deploy k8s</code>, 
              or <code>aq deploy nginx</code>. This allows complete portability to custom cloud clusters, VPS nodes, or 
              in-house hardware.
            </p>
          </div>

          <div className="border-l border-aquilia-500/25 pl-4">
            <h3 className={`text-lg font-semibold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Cloud className="w-4.5 h-4.5 text-aquilia-400" />
              2. Managed PaaS Integration
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Direct, API-driven deployments to managed platforms like Render. The framework introspects your active workspace features 
              and maps them directly to cloud services, databases, cache layers, environment variables, and auto-scaling rules.
            </p>
          </div>
        </div>
      </section>

      {/* Deployment Pipeline Architecture Diagram */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <GitBranch className="w-5 h-5 text-aquilia-400" />
          Deployment Pipeline Architecture
        </h2>
        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The orchestration path flows sequentially from the local workstation to the cloud provider. 
          Here is how the pipeline connects local diagnostics, container building, registry synchronization, and API service provisioning:
        </p>

        {/* Sessions-Style SVG Architecture Diagram */}
        <DeploymentArchitecture />

        {/* Architecture Components - Clean List */}
        <div className="space-y-6 mt-10">
          {[
            { id: 'cli.validate', icon: <Shield className="w-4 h-4" />, name: 'Phase 1: Diagnostics', desc: 'Runs aq doctor and aq validate. Verifies code signature integrity, checks for circular dependencies in manifest graphs, and validates that configurations are correct.' },
            { id: 'cli.deploy_render', icon: <Terminal className="w-4 h-4" />, name: 'Phase 2: Compilation', desc: 'Spawns docker build to package the workspace. Forces the linux/amd64 target architecture to ensure the resulting image runs on standard cloud execution nodes.' },
            { id: 'cli.deploy_render', icon: <Cloud className="w-4 h-4" />, name: 'Phase 3: Registry Push', desc: 'Asserts authentication status via local Docker configuration headers. Pushes the compiled image to the remote container registry.' },
            { id: 'provider.RenderDeployConfig', icon: <Settings className="w-4 h-4" />, name: 'Phase 4: Resolution', desc: 'Resolves the account workspace owner ID, maps database/caching/auth integrations to remote variables, and pulls necessary credential tokens.' },
            { id: 'provider.RenderDeployer', icon: <Zap className="w-4 h-4" />, name: 'Phase 5: Provisioning', desc: 'Creates or patches the service on Render. Synchronizes variables and persistent disks, and injects HTTP security header rules directly to Render\'s ingress router.' },
            { id: 'provider.RenderClient', icon: <Cloud className="w-4 h-4" />, name: 'Phase 6: Liveness Poll', desc: 'Polls Render\'s deployment status API until the container is declared healthy and active. If liveness checks fail, the deployer triggers an automatic rollback.' },
          ].map((item, i) => (
            <div key={i} className="flex gap-4 items-start transition-transform duration-200 hover:translate-x-1">
              <div className="mt-1 flex-shrink-0 text-aquilia-400 p-2 rounded-lg bg-aquilia-500/5 dark:bg-aquilia-500/10">
                {item.icon}
              </div>
              <div>
                <h3 className={`font-mono text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>
                  <DocTerm id={item.id}>{item.name}</DocTerm>
                </h3>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-650'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Two Ways to Configure */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Configuration Approaches
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia supports two distinct ways to define Render integration settings in <code>workspace.py</code>: 
          the <strong>Fluent API Integration</strong> and the <strong>Class-Based Configuration (Recommended)</strong>.
        </p>

        {/* Method 1 */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Method 1: Class-Based Config (Recommended)
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
            Defined inside the environment layering configurations inheriting from <code>AquilaConfig</code>. 
            This is the recommended approach because it supports environment-specific overrides (e.g., using different 
            machine plans or ports in dev vs. production environments) and supports twelve-factor variables via <code>Env()</code>.
          </p>

          <CodeBlock
            filename="workspace.py"
            language="python"
            highlightLines={[8, 9, 10, 11, 12, 13, 14, 15]}
            code={`from aquilia import Workspace, AquilaConfig, Env, Secret

class BaseEnv(AquilaConfig):
    env = "dev"
    # General defaults here...

class ProdEnv(BaseEnv):
    env = "prod"

    class render(AquilaConfig.Render):
        service_name  = "my-prod-backend"
        region        = "frankfurt"              # Oregon is default
        plan          = "standard"               # Free, Starter, Standard, Pro...
        num_instances = 2
        image         = Env("RENDER_IMAGE", default="docker.io/myorg/myapp:latest")
        health_path   = "/_health"
        port          = 8000

workspace = (
    Workspace("my-production-app")
    .env_config(ProdEnv)
)`}
          />
        </div>

        {/* Method 2 */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Method 2: Fluent API Integration
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
            Defined by instantiating a <DocTerm id="provider.RenderIntegration">RenderIntegration</DocTerm> object 
            and passing it directly to the workspace's <code>integrate()</code> method. This is suitable for simpler, 
            monolithic configurations that do not use multi-environment config layering.
          </p>

          <CodeBlock
            filename="workspace.py"
            language="python"
            highlightLines={[8, 9, 10, 11, 12, 13, 14, 15, 16]}
            code={`from aquilia import Workspace, Module
from aquilia.integrations import RenderIntegration

workspace = (
    Workspace("my-production-app")
    .runtime(mode="prod", host="0.0.0.0", port=8000, workers=4)
    .integrate(
        RenderIntegration(
            service_name="my-prod-service",
            region="frankfurt",
            plan="standard",
            num_instances=2,
            image="docker.io/myorg/myapp:latest",
            health_path="/_health",
            auto_deploy="no",
        )
    )
)`}
          />
        </div>
      </section>

      {/* Premium Next Steps */}
      <div className={`mt-14 border-t ${isDark ? 'border-white/10' : 'border-gray-250'} pt-8`}>
        <span className="font-mono text-xs font-bold text-aquilia-400 uppercase tracking-widest mb-4 block">Next Chapters</span>
        <div className="flex flex-col space-y-4">
          <Link
            to="/docs/providers/render"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">01</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  Render PaaS Integration
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Deployment pipeline workflow details, API clients, and service configuration payloads.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>

          <Link
            to="/docs/providers/security"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">02</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  Secure Credential Store
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Key derivation cryptography, encrypted credentials payload formatting, and local audit logs.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>

          <Link
            to="/docs/providers/cli"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">03</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  CLI Reference Guide
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Complete command flags, environment variable synchronizations, and CLI diagnostics.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>
        </div>
      </div>
    </div>
  )
}

function ArrowRightIcon() {
  return (
    <svg
      className="w-5 h-5 text-gray-500 group-hover:text-aquilia-400 group-hover:translate-x-1 transition-all duration-300 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  )
}
