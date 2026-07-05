import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Blocks, FolderOpen, FileCode, Settings, Database, Terminal } from 'lucide-react'

export function ProjectStructurePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Blocks className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Project Structure
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>File layout, conventions, and generated artifacts</p>
          </div>
        </div>
      </div>

      {/* Standard Layout */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FolderOpen className="w-5 h-5 text-aquilia-400" />
          Standard Workspace Layout
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          A workspace created with <DocTerm id="cli.init_workspace">aq init workspace my-api</DocTerm> produces the following structure.
          Every directory and file has a specific purpose:
        </p>

        <CodeBlock
          code={`my-api/
├── workspace.py              # Root configuration (Workspace/Module/Integration/Environment config)
├── starter.py                # Welcome-page controller (StarterController)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Gitignore configuration (ignores secrets & trace directories)
│
├── modules/                  # Application modules (empty by default; add using aq add module)
│
├── tests/                    # Top-level test directory
│   ├── conftest.py           # Shared testing fixtures
│   └── test_smoke.py         # Smoke/verification tests
│
└── LICENSE                   # Selected license file (MIT, Apache-2.0, etc.)`}
          language="text"
        />
      </section>

      {/* Key Files */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileCode className="w-5 h-5 text-aquilia-400" />
          Key Files Explained
        </h2>

        <div className="space-y-6">
          {/* workspace.py */}
          <div>
            <h3 className={`font-bold text-lg mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.workspace_py">workspace.py</DocTerm>
            </h3>
            <p className={`mb-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              The root configuration file. Aquilia's ConfigLoader looks for this file first (Python-first config).
              It must export a <DocTerm id="cli.workspace_py">workspace</DocTerm> variable containing the Workspace configuration object.
            </p>
            <CodeBlock
              code={`from aquilia import Workspace, Module
from aquilia import AquilaConfig, Secret, Env
from aquilia.integrations import (
    MiddlewareChain,
    DiIntegration,
    RegistryIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    DatabaseIntegration,
    CacheIntegration,
    TemplatesIntegration,
    StaticFilesIntegration,
)

# ── Environment Configuration ────────────────────────────────────
class BaseEnv(AquilaConfig):
    """Shared defaults — every environment inherits these."""
    env = "dev"

    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = 8000
        workers = 1
        reload  = False

    class auth(AquilaConfig.Auth):
        secret_key      = Secret(env="AQ_SECRET_KEY", default="change-me-in-prod")
        password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")

class DevEnv(BaseEnv):
    """Development — hot-reload, debug pages, single worker."""
    env = "dev"

    class server(BaseEnv.server):
        debug   = True
        reload  = True
        workers = 1

class ProdEnv(BaseEnv):
    """Production — multi-worker, no reload, no debug."""
    env = "prod"

    class server(BaseEnv.server):
        host               = Env("AQ_HOST", default="0.0.0.0")
        port               = Env("AQ_PORT", default=8000, cast=int)
        workers            = Env("AQ_WORKERS", default=4, cast=int)
        reload             = False
        access_log         = False

    class auth(BaseEnv.auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)

# ── Workspace Structure ──────────────────────────────────────────
workspace = (
    Workspace(
        name="my-api",
        version="1.0.0",
        description="Aquilia workspace",
    )
    # Wire environment config (resolved by AQ_ENV at runtime)
    .env_config(BaseEnv)

    # Starter module for welcome page
    .starter("starter")

    # Middleware chain
    .middleware(MiddlewareChain.defaults())
    .build()
)`}
              language="python"
            />
          </div>

          {/* .env */}
          <div>
            <h3 className={`font-bold text-lg mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.dotenv_file">.env</DocTerm>
            </h3>
            <p className={`mb-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Environment variables with the <code>AQ_</code> prefix are automatically loaded. Nested keys
              use double underscores. Higher priority than config files but lower than CLI arguments.
            </p>
            <CodeBlock
              code={`# .env
AQ_ENV=dev
AQ_SECRET_KEY=some-highly-secure-secret-key-string
AQ_DATABASE__URL=sqlite:///db.sqlite3`}
              language="bash"
            />
          </div>
        </div>
      </section>

      {/* Module Structure */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Module Conventions
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Each module directory follows conventions that <code>Module.auto_discover()</code> uses to find components:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>File</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Discovery Scans For</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Registration</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['manifest.py', 'Module metadata & declarations', 'Compiled & registered by the discovery engine'],
                ['controllers.py', 'Classes extending Controller', 'Compiled routes registered with ControllerRouter'],
                ['services.py', 'Classes decorated with @service or @factory', 'Providers registered in DI Container'],
                ['models.py', 'Classes extending Model', 'ORM schemas compiled, database tables validated/created'],
                ['blueprints.py', 'Classes extending Blueprint', 'Input schemas available for controller endpoint binding'],
                ['faults.py', 'Custom structured Fault classes', 'Added to module-scoped FaultDomain'],
                ['test_routes.py', 'Integration and route level tests', 'Verified during aq test execution'],
              ].map(([file, scans, reg], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{file}</td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{scans}</td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{reg}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Trace Directory */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-400" />
          The .aquilia/ Trace Directory
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>.aquilia/</code> directory is automatically generated at boot/runtime and contains
          diagnostic artifacts, credentials, caches, and logs. It should be added to <code>.gitignore</code>:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>File</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Contents</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['discovery_cache.surp', 'AST discovery cache mapping file hashes to avoid redundant scans'],
                ['audit.surp', 'Binary SURP format admin audit log logging all administrator actions'],
                ['admin/profile/', 'Directory containing profile avatar images uploaded via the admin portal'],
                ['mcp/index.json', 'Local MCP server knowledge index containing codebase schemas'],
                ['mcp/server.pid', 'Process ID file of the active Model Context Protocol daemon'],
                ['mcp/server.log', 'Execution log file containing output of the active MCP daemon'],
                ['providers/render/credentials.surp', 'AES-256-GCM encrypted Render deployment API tokens'],
                ['providers/render/config.json', 'Non-sensitive Render deployment settings (region, owner name, TTL)'],
                ['providers/render/audit.log', 'Render credential access audit trail'],
              ].map(([file, contents], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{file}</td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{contents}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={`mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Use <DocTerm id="cli.inspect">aq inspect</DocTerm> to query trace artifacts from the command line, or use
          <DocTerm id="cli.trace">aq trace</DocTerm> for interactive exploration.
        </p>
      </section>

      {/* CLI-generated files */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-400" />
          CLI-Generated Files
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="cli.aq">aq</DocTerm> CLI generates various files. Understanding where they go:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Command</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Generates</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                { cmd: 'aq init workspace <name>', id: 'cli.init_workspace', gen: 'Full project scaffolding with workspace.py, starter.py, modules/ directory' },
                { cmd: 'aq add module <name>', id: 'cli.add_module', gen: 'modules/<name>/ with manifest.py, controllers.py, services.py, models.py, blueprints.py, faults.py' },
                { cmd: 'aq validate', id: 'cli.validate', gen: 'Performs static check of imports, wiring, schemas, and configurations' },
                { cmd: 'aq db makemigrations', id: 'cli.db_makemigrations', gen: 'Scans ORM models and generates numbered database migration files' },
                { cmd: 'aq db migrate', id: 'cli.db_migrate', gen: 'Applies pending schema migrations to the configured SQLite/PostgreSQL database' },
                { cmd: 'aq deploy all', id: 'cli.deploy', gen: 'Generates deployment templates: Dockerfile, docker-compose.yml, Kubernetes manifests, and Render configuration' },
                { cmd: 'aq freeze', id: 'cli.freeze', gen: 'Generates frozen.surp manifest integrity snapshot, disabling auto-discovery' },
              ].map(({ cmd, id, gen }, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className="px-4 py-2 text-xs">
                    <DocTerm id={id}>{cmd}</DocTerm>
                  </td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{gen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Next Steps */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Next Steps</h2>
        <div className="flex flex-col gap-2">
          <Link to="/docs/config/workspace" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Workspace Builder: All configuration options
          </Link>
          <Link to="/docs/controllers/overview" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Controllers: Writing request handlers
          </Link>
          <Link to="/docs/cli/commands" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → CLI Reference: All commands in detail
          </Link>
        </div>
      </section>
    </div>
  )
}
