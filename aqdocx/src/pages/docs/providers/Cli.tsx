import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Terminal, Shield, Play, RefreshCw, Layers } from 'lucide-react'
import { Link } from 'react-router-dom'

export function CliPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Terminal className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                CLI Command Reference
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Detailed documentation for aq provider and aq deploy CLI commands</p>
          </div>
        </div>

        <p className={`text-lg ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>aq</code> command-line tool provides interactive terminal flows for managing cloud logins, 
          updating remote service variables, and deploying projects. All commands leverage structured terminal output, 
          featuring status indicators, execution phases, and diagnostic warnings.
        </p>
      </div>

      {/* Provider Auth CLI */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Provider Authentication Commands
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Authentication is the gatekeeper for all provider integrations. Use the following commands to check, establish, or purge 
          workspace credentials:
        </p>

        {/* aq provider login */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>aq provider login render</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Authenticates with the Render API using a personal API bearer key. The key is validated by listing account owners 
            and is then encrypted via <DocTerm id="provider.RenderCredentialStore">RenderCredentialStore</DocTerm>.
          </p>
          <div className="text-xs mb-4 space-y-1">
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Argument:</strong> <code>PROVIDER_NAME</code> (must be <code>render</code>)</div>
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Options:</strong></div>
            <ul className="list-disc list-inside pl-4">
              <li><code>--token, -t</code>: API bearer token. If omitted, prompts securely. If <code>-</code>, reads from standard input.</li>
              <li><code>--region, -r</code>: Default deployment region (e.g. <code>frankfurt</code>, <code>oregon</code>). Default is <code>oregon</code>.</li>
            </ul>
          </div>
          <CodeBlock
            language="bash"
            code={`# Run interactively (will prompt for token securely)
aq provider login render

# Run with inline arguments
aq provider login render --token rnd_xxxxxx --region frankfurt

# Pipe token from a secrets environment variable
echo $RENDER_TOKEN | aq provider login render --token -`}
          />
        </div>

        {/* aq provider status */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>aq provider status render</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
            Checks the state of your local credentials, runs decryption tests, queries connection speed to Render, and displays owner email metadata.
          </p>
          <CodeBlock
            language="bash"
            code={`aq provider status render`}
          />
        </div>

        {/* aq provider logout */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>aq provider logout render</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Erases stored credentials. To prevent recovery of secret key remnants on SSD controllers, the command 
            overwrites the local <code>credentials.surp</code> file with random bytes before deletion.
          </p>
          <CodeBlock
            language="bash"
            code={`aq provider logout render`}
          />
        </div>
      </section>

      {/* Provider Render Operational Group */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Render Operational Commands
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>aq provider render</code> subcommands allow direct management of Render services, deployments, and logs:
        </p>

        {/* Services */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            1. <code>aq provider render services</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Lists all services provisioned inside the active Render workspace owner account. Displays name, region, status, and type.
          </p>
          <CodeBlock language="bash" code="aq provider render services" />
        </div>

        {/* Deploys */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            2. <code>aq provider render deploys</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Lists deployment histories for a target service.
          </p>
          <div className="text-xs mb-3">
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Option:</strong> <code>--service, -s SERVICE_NAME</code>
          </div>
          <CodeBlock language="bash" code="aq provider render deploys --service my-web-service" />
        </div>

        {/* Deploy Trigger */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            3. <code>aq provider render deploy-trigger</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Triggers a new manual deployment for the target service on Render.
          </p>
          <div className="text-xs mb-3">
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Option:</strong> <code>--service, -s SERVICE_NAME</code>
          </div>
          <CodeBlock language="bash" code="aq provider render deploy-trigger --service my-web-service" />
        </div>

        {/* Deploy Cancel */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            4. <code>aq provider render deploy-cancel</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Cancels an active, ongoing build or deployment on Render.
          </p>
          <div className="text-xs mb-3 space-y-1">
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Argument:</strong> <code>DEPLOY_ID</code> (e.g. <code>dep-xxxx</code>)</div>
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Option:</strong> <code>--service, -s SERVICE_NAME</code></div>
          </div>
          <CodeBlock language="bash" code="aq provider render deploy-cancel dep-12345 --service my-web-service" />
        </div>

        {/* Deploy Rollback */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            5. <code>aq provider render deploy-rollback</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
            Rolls back a service to a previous deployment. Triggered automatically on failure during <code>aq deploy render</code> runs.
          </p>
          <div className="text-xs mb-3 space-y-1">
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Argument:</strong> <code>DEPLOY_ID</code></div>
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Option:</strong> <code>--service, -s SERVICE_NAME</code></div>
          </div>
          <CodeBlock language="bash" code="aq provider render deploy-rollback dep-old123 --service my-web-service" />
        </div>

        {/* Logs */}
        <div className="mb-8 border-l border-aquilia-500/25 pl-4">
          <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            6. <code>aq provider render logs</code>
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Retrieves recent application logs. Output is formatted with color-coded severity levels (INFO, WARN, ERROR).
          </p>
          <div className="text-xs mb-3 space-y-1">
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Required Option:</strong> <code>--service, -s SERVICE_NAME</code></div>
            <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Options:</strong></div>
            <ul className="list-disc list-inside pl-4">
              <li><code>--limit, -l</code>: Number of log lines to show (default: 50).</li>
              <li><code>--level</code>: Filter severity: <code>info</code> | <code>warn</code> | <code>error</code>.</li>
            </ul>
          </div>
          <CodeBlock language="bash" code="aq provider render logs --service my-web-service --limit 100 --level error" />
        </div>
      </section>

      {/* Env Var Sync CLI */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <RefreshCw className="w-5 h-5 text-aquilia-400" />
          Environment Variable Management
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Use the <code>aq provider render env</code> subcommand group to synchronize container environment variables:
        </p>

        {/* env list */}
        <div className="mb-6 border-l border-aquilia-500/25 pl-4">
          <h4 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>List Variables</h4>
          <CodeBlock language="bash" code="aq provider render env list --service my-web-service" />
        </div>

        {/* env set */}
        <div className="mb-6 border-l border-aquilia-500/25 pl-4">
          <h4 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>Set/Update Variable</h4>
          <CodeBlock language="bash" code="aq provider render env set STRIPE_API_KEY 'sk_live_...' --service my-web-service" />
        </div>

        {/* env delete */}
        <div className="mb-6 border-l border-aquilia-500/25 pl-4">
          <h4 className={`text-base font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>Delete Variable</h4>
          <CodeBlock language="bash" code="aq provider render env delete STRIPE_API_KEY --service my-web-service" />
        </div>
      </section>

      {/* Deployment CLI */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Play className="w-5 h-5 text-aquilia-400" />
          Deployment Commands
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Once authenticated, run <DocTerm id="cli.deploy_render">aq deploy render</DocTerm> to trigger the deployment run. 
          The CLI supports multiple options to customize and query services directly:
        </p>

        <h3 className={`text-base font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          1. <code>aq deploy render</code> (Standard Deployment)
        </h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Compiles, validates, builds, pushes, and provisions the workspace. It prints progress updates for each step.
        </p>
        <div className="text-xs mb-3 space-y-1">
          <div><strong className={isDark ? 'text-white' : 'text-gray-900'}>Options:</strong></div>
          <ul className="list-disc list-inside pl-4 space-y-1">
            <li><code>--image, -i</code>: Docker image path (e.g. <code>docker.io/user/repo:tag</code>).</li>
            <li><code>--region, -r</code>: Deployment datacenter (<code>oregon</code> | <code>frankfurt</code> | <code>ohio</code> | <code>virginia</code> | <code>singapore</code>).</li>
            <li><code>--plan</code>: Compute tier size (<code>free</code> | <code>starter</code> | <code>standard</code> | <code>pro</code> | <code>pro_plus</code>).</li>
            <li><code>--num-instances</code>: Explicit container scaling factor.</li>
            <li><code>--service-name</code>: Custom service name override on Render.</li>
            <li><code>--registry-credential-id</code>: Private registry credential ID (if pulling from a private registry).</li>
            <li><code>--force, -f</code>: Overwrite configuration without prompt checks.</li>
          </ul>
        </div>
        <CodeBlock
          language="bash"
          code={`aq deploy render --region frankfurt --plan standard --num-instances 2`}
        />

        <h3 className={`text-base font-semibold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          2. <code>aq deploy render --dry-run</code> (Dry Run Planning)
        </h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-655'}`}>
          Synthesizes the configuration properties, compiles the local OCI configuration, resolves dependency mappings, 
          and prints the target payload structure without writing any files or contacting Render endpoints.
        </p>
        <CodeBlock
          language="bash"
          code={`aq deploy render --dry-run`}
        />

        <h3 className={`text-base font-semibold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          3. <code>aq deploy render --status</code> (Query Live Status)
        </h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-650'}`}>
          Connects to the Render API and prints the active status (e.g. <code>creating</code>, <code>live</code>, or <code>suspended</code>), 
          public URL, deployment history logs, and healthy instance count.
        </p>
        <CodeBlock
          language="bash"
          code={`aq deploy render --status`}
        />

        <h3 className={`text-base font-semibold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          4. <code>aq deploy render --destroy</code> (Teardown Service)
        </h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Tears down and destroys the deployed Render web service and associated configuration. 
          To prevent accidental production data loss, this command requires interactive confirmation unless <code>--yes</code> is supplied.
        </p>
        <CodeBlock
          language="bash"
          code={`aq deploy render --destroy`}
        />
      </section>

      {/* Premium Next Steps */}
      <div className={`mt-14 border-t ${isDark ? 'border-white/10' : 'border-gray-250'} pt-8`}>
        <span className="font-mono text-xs font-bold text-aquilia-400 uppercase tracking-widest mb-4 block">Next Chapters</span>
        <div className="flex flex-col space-y-4">
          <Link
            to="/docs/providers/overview"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">01</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  Providers Overview
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Deployment strategy, container building pipelines, and configuration approaches.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>

          <Link
            to="/docs/providers/render"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">02</span>
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
