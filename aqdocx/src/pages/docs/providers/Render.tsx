import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Cloud, Layers, Workflow, Globe, Shield, Key } from 'lucide-react'
import { Link } from 'react-router-dom'

export function RenderPage() {
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
                Render PaaS Deployments
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Full lifecycle deployment orchestration, client libraries, and payloads</p>
          </div>
        </div>

        <p className={`text-lg ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The Render integration facilitates zero-downtime, fully-configured deployments. 
          When you execute a deployment, Aquilia compiles your code, packages it inside a production-ready Docker container, 
          wires dependency-injected integrations, configures security headers, provisions Render services, and polls until the system is healthy.
        </p>
      </div>

      {/* Deployment Prerequisites */}
      <section className="mb-12 border-l-2 border-aquilia-500/50 pl-4 py-1">
        <h2 className={`text-xl font-bold mb-3 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Key className="w-5 h-5 text-aquilia-400" />
          Deployment Prerequisites
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-300' : 'text-gray-605'}`}>
          To orchestrate deployments to the Render cloud platform, you must establish two distinct trust endpoints beforehand:
        </p>
        <ol className={`list-decimal list-inside space-y-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-650'}`}>
          <li>
            <strong className={`${isDark ? 'text-white' : 'text-gray-900'}`}>Render API Authentication:</strong> 
            You must configure your Render API token locally. This can be accomplished either via the 
            interactive <DocTerm id="cli.provider_login_render">aq provider login render</DocTerm> command or 
            via the Aquilia Admin Panel configuration settings.
          </li>
          <li>
            <strong className={`${isDark ? 'text-white' : 'text-gray-900'}`}>Docker Registry Authorization:</strong> 
            Because Render does not host custom container images directly, it relies on pulling built images from an external registry 
            (e.g., Docker Hub, GitHub Container Registry). You must run <code>docker login</code> on your workstation so the deployer 
            can push the compiled image to your repository.
          </li>
        </ol>
      </section>

      {/* Deployment Workflow Timeline (1-7 Connected) */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Workflow className="w-5 h-5 text-aquilia-400" />
          Deployment Pipeline Workflow
        </h2>
        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Deploying an application executes a structured multi-phase orchestration pipeline managed 
          by <DocTerm id="provider.RenderDeployer">RenderDeployer</DocTerm>:
        </p>

        {/* Connected Vertical Timeline */}
        <div className="relative pl-6 border-l-2 border-aquilia-500/20 space-y-10 ml-3">
          {/* Phase 1 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">1</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-955'}`}>Pre-flight Diagnostics</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Runs <code>aq doctor</code> and <code>aq validate</code>. The system inspects your dependency injection graph for 
                unresolved services, checks module manifests for routing conflicts, and verifies that the local configuration is valid.
              </p>
            </div>
          </div>

          {/* Phase 2 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">2</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-955'}`}>Container Compilation</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                If the workspace contains a <code>Dockerfile</code> (or if one is generated on the fly via <code>aq deploy dockerfile</code>), 
                the deployer spawns a Docker build process to compile your local workspace into a target image with 
                the <code>linux/amd64</code> architecture.
              </p>
            </div>
          </div>

          {/* Phase 3 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">3</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-955'}`}>Docker Registry Push</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-650'}`}>
                Validates Docker registry login credentials. The deployer pushes the compiled image to the remote container registry 
                (such as Docker Hub or GHCR), so that Render can pull the image during its deployment run.
              </p>
            </div>
          </div>

          {/* Phase 4 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">4</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-950'}`}>Owner and Context Introspection</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
                Retrieves workspace owner info from Render's API. The deployer inspects your active workspace integrations. 
                If the workspace has <code>has_db</code>, <code>has_cache</code>, or <code>has_auth</code> modules active, 
                Aquilia automatically structures corresponding environment variables:
              </p>
              <ul className={`list-disc list-inside mt-2 text-xs space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <li><code>DATABASE_URL</code> for PostgreSQL integrations</li>
                <li><code>REDIS_URL</code> for Redis integrations</li>
                <li><code>AQ_AUTH_SECRET</code> (cryptographically generated crypt-secure value for token validations)</li>
                <li><code>AQ_SIGNING_SECRET</code> (cryptographically generated signing seed)</li>
              </ul>
            </div>
          </div>

          {/* Phase 5 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">5</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-950'}`}>Render Provisioning & Webhook Setup</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Creates the service in Render (or patches the existing configuration if already provisioned). 
                Synchronizes environment variables and attaches persistent disks if specified.
              </p>
            </div>
          </div>

          {/* Phase 6 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">6</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-950'}`}>HTTP Headers Injection</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Injects standard security headers to secure the service (e.g. <code>Strict-Transport-Security</code>, <code>X-Content-Type-Options</code>, 
                and <code>X-Frame-Options: DENY</code>) directly into Render's ingress routers.
              </p>
            </div>
          </div>

          {/* Phase 7 */}
          <div className="relative">
            <div className="absolute -left-[35px] top-1 w-5 h-5 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-md shadow-aquilia-500/30">
              <span className="text-[9px] font-bold text-white">7</span>
            </div>
            <div>
              <h3 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-950'}`}>Autoscaling & Deployment Wait</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Applies scaling targets and triggers the deployment. The pipeline loops, polling the Render deployment endpoint 
                until the service status goes <code>live</code>. In the event of a build or start failure, the deployer aborts 
                and rolls back to the previous deployment ID.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* RenderClient */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          The Render API Client
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="provider.RenderClient">RenderClient</DocTerm> class is a synchronous Python client implementing the 
          official Render API v1. To prevent dependency bloat and eliminate supply-chain vulnerabilities, the client is written 
          using Python's standard library <code>urllib.request</code>.
        </p>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          It incorporates transient failure retries, cursor-based pagination, and automatic rate-limit throttling (by respecting 
          the API's <code>Retry-After</code> headers with exponential backoff).
        </p>

        <CodeBlock
          filename="client.py"
          language="python"
          highlightLines={[7, 10, 11, 13, 14, 15]}
          code={`from aquilia.providers.render import RenderClient

# Instantiating client
client = RenderClient(token="rnd_xxxxxxxxxxxx")

# Querying services
services = client.list_services(limit=20)
for svc in services:
    print(f"Service: {svc.name} | Status: {svc.status} | Region: {svc.region}")

# Fetching deploy status
deploy_info = client.get_deploy(service_id="srv-abc123xyz", deploy_id="dep-12345")
print(f"Deploy State: {deploy_info.status}")`}
        />
      </section>

      {/* RenderDeployer */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          The Render Deployer
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="provider.RenderDeployer">RenderDeployer</DocTerm> orchestrates the deployment process. 
          It takes the credentials token from the secure credential store, reads configuration from <code>workspace.py</code>, 
          and coordinates the compilation, upload, and verification phases.
        </p>

        <CodeBlock
          filename="deploy.py"
          language="python"
          highlightLines={[12, 13, 14]}
          code={`from pathlib import Path
from aquilia.providers.render import RenderClient, RenderDeployer, RenderDeployConfig

# 1. Initialize API Client
client = RenderClient(token="rnd_xxxxxxxxxxxx")

# 2. Build deployment config contract
config = RenderDeployConfig(
    service_name="production-backend",
    image="docker.io/myorg/backend:v1.0.0",
    region="oregon",
    num_instances=2,
)

# 3. Create deployer and run
deployer = RenderDeployer(client, workspace_root=Path("/app"), config=config)
result = deployer.deploy()

if result.success:
    print(f"Successfully deployed! Live URL: {result.url}")
else:
    print(f"Deployment failed. Steps completed: {result.steps_completed}")
    print(f"Errors encountered: {result.errors}")`}
        />
      </section>

      {/* API Payloads */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Payload Architecture
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          When creating or patching services, the <DocTerm id="provider.RenderDeployConfig">RenderDeployConfig</DocTerm> converts 
          snake_case structures into camelCase JSON properties required by the Render REST endpoints:
        </p>

        <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>POST /v1/services (Service Creation)</h3>
        <CodeBlock
          language="json"
          highlightLines={[5, 6, 7, 8, 9, 13]}
          code={`{
  "name": "my-prod-service",
  "type": "web_service",
  "autoDeploy": "no",
  "image": {
    "imagePath": "docker.io/myorg/myapp:latest",
    "registryCredentialId": "rc-123456"
  },
  "serviceDetails": {
    "plan": "starter",
    "region": "oregon",
    "numInstances": 2,
    "healthCheckPath": "/_health",
    "envVars": [
      { "key": "AQUILIA_ENV", "value": "prod" },
      { "key": "AQ_SERVER_PORT", "value": "8000" }
    ]
  }
}`}
        />
      </section>

      {/* Premium Next Steps */}
      <div className={`mt-14 border-t ${isDark ? 'border-white/10' : 'border-gray-250'} pt-8`}>
        <span className="font-mono text-xs font-bold text-aquilia-400 uppercase tracking-widest mb-4 block">Next Chapters</span>
        <div className="flex flex-col space-y-4">
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
