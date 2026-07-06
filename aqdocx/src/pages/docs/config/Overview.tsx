import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Settings, Layers, Zap, ArrowRight, Code, Lock, Server, GitBranch } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ConfigOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const txt = isDark ? 'text-gray-300' : 'text-gray-600'
  const subtxt = isDark ? 'text-gray-400' : 'text-gray-500'
  const head = isDark ? 'text-white' : 'text-gray-900'
  const divider = isDark ? 'divide-white/5' : 'divide-gray-100'
  const thead = isDark ? 'bg-zinc-800/80' : 'bg-gray-50'
  const th = isDark ? 'text-gray-300' : 'text-gray-700'
  const hov = isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
  const border = isDark ? 'border-white/10' : 'border-gray-200'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Settings className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${head}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Configuration System
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.pyconfig — Pure Python, zero YAML</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Aquilia's configuration system is pure Python. There is no YAML, no TOML, no JSON. Everything — application structure, modules, integrations, and environment-specific settings — lives in a single <code>workspace.py</code> file. <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclasses carry the environment config; the <DocTerm id="config.workspace">Workspace</DocTerm> builder wires it all together.
        </p>
      </div>

      {/* Architecture overview diagram */}
      <div className="w-full h-36 flex items-center justify-center my-4 mb-10">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 130" fill="none">
          <defs>
            <linearGradient id="cfgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
          </defs>
          {/* Central workspace.py */}
          <ellipse cx="300" cy="65" rx="70" ry="32" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.6" />
          <text x="300" y="60" textAnchor="middle" fill="#a78bfa" fontSize="10" fontWeight="bold" fontFamily="monospace">workspace.py</text>
          <text x="300" y="75" textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="7.5" fontFamily="sans-serif">single source of truth</text>

          {/* Satellites */}
          {[
            { cx: 90,  cy: 30,  label: 'AquilaConfig', sub: 'env config',    color: '#f59e0b' },
            { cx: 90,  cy: 100, label: 'Workspace()',   sub: 'app structure', color: '#10b981' },
            { cx: 510, cy: 30,  label: '.integrate()',  sub: 'integrations',  color: '#3b82f6' },
            { cx: 510, cy: 100, label: '.module()',     sub: 'modules',       color: '#ec4899' },
          ].map(({ cx, cy, label, sub, color }, i) => (
            <g key={i}>
              <line x1={cx < 300 ? cx + 48 : cx - 48} y1={cy} x2={cx < 300 ? 230 : 370} y2={65} stroke={color} strokeWidth="1" strokeOpacity="0.3" strokeDasharray="4 3" />
              <rect x={cx - 44} y={cy - 18} width="88" height="36" rx="8" fill="none" stroke={color} strokeWidth="1" strokeOpacity="0.4" />
              <text x={cx} y={cy - 2} textAnchor="middle" fill={color} fontSize="8.5" fontWeight="bold" fontFamily="monospace">{label}</text>
              <text x={cx} y={cy + 11} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">{sub}</text>
            </g>
          ))}
        </svg>
      </div>

      {/* Why pure Python */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-5 flex items-center gap-2 ${head}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          Why pure Python config?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { icon: <Code className="w-4 h-4 text-aquilia-400" />, title: 'IDE-native', body: 'Pyright and Pylance know every field. Ctrl-click navigates to the definition. Rename refactoring works across the whole project.' },
            { icon: <Lock className="w-4 h-4 text-aquilia-400" />, title: 'Type-checked', body: 'Mypy catches a missing required Secret, a wrong port type, or a misspelled section name before the process starts.' },
            { icon: <GitBranch className="w-4 h-4 text-aquilia-400" />, title: 'Git-native', body: 'Config changes appear in git diff, git blame, and pull-request reviews just like any other code change.' },
          ].map(({ icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">{icon}<strong className={`text-sm font-semibold ${head}`}>{title}</strong></div>
              <p className={`text-xs leading-relaxed ${subtxt}`}>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* workspace.py — the single file */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          workspace.py — the single file
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Everything lives in <code>workspace.py</code> at the project root. The <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclasses declare environment-specific settings with <DocTerm id="config.env">Env</DocTerm> bindings and <DocTerm id="config.secret">Secret</DocTerm> fields. The <DocTerm id="config.workspace">Workspace</DocTerm> builder wires modules and typed integration dataclasses. At runtime, <code>.env_config(BaseEnv)</code> reads <code>AQ_ENV</code> to select the right subclass automatically.
        </p>
        <CodeBlock language="python" code={`# workspace.py — everything in one file
from aquilia import Workspace, Module
from aquilia.pyconfig import AquilaConfig, Env, Secret
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    CacheIntegration,
    SessionIntegration,
    OpenAPIIntegration,
    MailIntegration, SmtpProvider, MailAuth,
    TasksIntegration,
    CorsIntegration,
)

# ─── Environment Config ─────────────────────────────────────────────────────

class BaseEnv(AquilaConfig):
    """Shared baseline — all environments inherit from this."""

    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = Env("PORT", default=8000, cast=int)
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm  = "HS256"

    class database(AquilaConfig.Database):
        url = Env("DATABASE_URL", default="sqlite:///dev.db")

class DevEnv(BaseEnv):
    env = "dev"

    class server(BaseEnv.server):
        reload = True
        debug  = True

class ProdEnv(BaseEnv):
    env = "prod"

    class server(BaseEnv.server):
        host    = "0.0.0.0"
        workers = Env("WEB_WORKERS", default=4, cast=int)
        timeout_graceful_shutdown = 30

    class auth(BaseEnv.auth):
        password_hasher = AquilaConfig.PasswordHasher.argon2id(time_cost=3, memory_cost=131072)

# ─── Application Structure ──────────────────────────────────────────────────

workspace = (
    Workspace("myapp", version="1.0.0")
    .env_config(BaseEnv)                      # reads AQ_ENV → picks DevEnv / ProdEnv

    .module(Module("auth").route_prefix("/auth"))
    .module(Module("users").route_prefix("/users").depends_on("auth"))
    .module(Module("blog").route_prefix("/blog"))

    .integrate(DatabaseIntegration(
        url=Env("DATABASE_URL", default="sqlite:///app.db"),
        auto_migrate=True,
        pool_size=10,
    ))
    .integrate(AuthIntegration(
        secret_key=Secret(env="AQ_SECRET_KEY", required=True).reveal(),
        algorithm="HS256",
        access_token_ttl_minutes=60,
        refresh_token_ttl_days=30,
    ))
    .integrate(CacheIntegration(backend="redis", redis_url="redis://localhost:6379/0"))
    .integrate(OpenAPIIntegration(title="My App API", version="1.0.0"))
)`} />
      </section>

      {/* ConfigLoader bridge */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          ConfigLoader — the internal bridge
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          When the server starts, <code>AquilaConfig.to_loader()</code> converts your class hierarchy into a <code>ConfigLoader</code> instance that all internal subsystems read from. You never instantiate <code>ConfigLoader</code> directly — the framework does it during boot. You interact with it only in advanced scenarios (tests, plugins, custom CLI commands).
        </p>
        <CodeBlock language="python" code={`# Aquilia does this internally during boot.
# You only need this for custom tooling or tests.

loader = ProdEnv.to_loader()

# Dot-path access
port    = loader.get("server.port")      # → int
db_url  = loader.get("database.url")    # → str

# Typed subsystem accessors
auth_cfg  = loader.get_auth_config()
sess_cfg  = loader.get_session_config()
cache_cfg = loader.get_cache_config()

# Invalidate cache after env changes (useful in tests)
ProdEnv.invalidate_cache()
AquilaConfig.clear_all_caches()         # clears all subclass caches + resets dotenv state`} />
      </section>

      {/* Precedence */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Value resolution precedence
        </h2>
        <p className={`mb-3 ${txt}`}>
          When multiple sources define the same key, this order wins. Higher rows always take priority — the process environment (Docker, Kubernetes, CI/CD) always wins over source defaults.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Priority</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Source</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>How</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['1 — Highest', 'Process environment (os.environ)', 'Env("MY_VAR") reads os.environ.get("MY_VAR") at access time'],
                ['2', '.env files (auto-loaded)', 'DotEnvLoader searches .env, .env.local, .env.{env} and loads before first access'],
                ['3', 'AquilaConfig literal fields', 'Class-level assignments in your section subclasses'],
                ['4 — Lowest', 'Built-in defaults', 'Aquilia\'s defaults inside AquilaConfig.Server, .Auth, .Database, etc.'],
              ].map(([priority, source, how], i) => (
                <tr key={i} className={hov}>
                  <td className={`px-4 py-3 text-xs font-semibold ${i === 0 ? 'text-aquilia-400' : subtxt}`}>{priority}</td>
                  <td className={`px-4 py-3 text-sm font-mono text-xs ${subtxt}`}>{source}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{how}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* env selection */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Server className="w-5 h-5 text-aquilia-400" />
          Environment selection at runtime
        </h2>
        <p className={`mb-4 ${txt}`}>
          <code>.env_config(BaseEnv)</code> scans all subclasses of <code>BaseEnv</code> and picks the one whose <code>env</code> attribute matches the <code>AQ_ENV</code> environment variable. If <code>AQ_ENV</code> is not set, it falls back to <code>"dev"</code>.
        </p>
        <CodeBlock language="python" code={`# In workspace.py:
workspace = Workspace("myapp").env_config(BaseEnv)

# At runtime the framework calls:
#   AQ_ENV=prod → uses ProdEnv
#   AQ_ENV=dev  → uses DevEnv  (also the default if unset)

# You can also select manually (useful in scripts and tests):
loader = BaseEnv.from_env_var("AQ_ENV", default="dev").to_loader()
# or by explicit class:
loader = ProdEnv.to_loader()
# or by name:
loader = AquilaConfig.for_env("prod").to_loader()   # → resolves ProdEnv`} />
      </section>

      {/* Inspect config */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Inspecting config values
        </h2>
        <p className={`mb-4 ${txt}`}>
          Use <code>.to_dict()</code> to see the fully-resolved, serialised config at any point. All <DocTerm id="config.env">Env</DocTerm> descriptors are resolved and all <DocTerm id="config.secret">Secret</DocTerm> values are revealed in the dict — handle it accordingly.
        </p>
        <CodeBlock language="python" code={`import pprint, json
from workspace import ProdEnv

# Full resolved dict (resolves all Env bindings, reveals all Secrets)
cfg = ProdEnv.to_dict()
pprint.pprint(cfg)

# Dot-path access without building a full loader
port    = ProdEnv.get("server.port")       # → 8000
db_url  = ProdEnv.get("database.url")     # → "postgresql://..."
missing = ProdEnv.get("nonexistent", 42)  # → 42 (default)`} />
      </section>

      {/* Testing */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Testing config</h2>
        <p className={`mb-4 ${txt}`}>
          Use <code>AquilaConfig.clear_all_caches()</code> between tests to reset all resolved caches and the dotenv loader state. Combine with <code>monkeypatch.setenv()</code> to simulate different environments.
        </p>
        <CodeBlock language="python" code={`import pytest
from aquilia.pyconfig import AquilaConfig

@pytest.fixture(autouse=True)
def reset_config():
    yield
    AquilaConfig.clear_all_caches()    # Clears Env caches + dotenv state

def test_prod_workers(monkeypatch):
    monkeypatch.setenv("WEB_WORKERS", "8")
    ProdEnv.invalidate_cache()
    assert ProdEnv.get("server.workers") == 8

def test_secret_required(monkeypatch):
    monkeypatch.delenv("AQ_SECRET_KEY", raising=False)
    ProdEnv.invalidate_cache()
    with pytest.raises(Exception):   # ConfigMissingFault
        ProdEnv.get("auth.secret_key")`} />
      </section>

      {/* Navigation links */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config/pyconfig', 'AquilaConfig & Env', 'Env, Secret, section, PasswordHasher — full reference'],
            ['/docs/config/dotenv', '.env Files', 'File precedence, syntax, DotEnvLoader API'],
            ['/docs/config/workspace', 'Workspace Builder', 'Fluent .module(), .integrate(), .env_config()'],
            ['/docs/config/manifest', 'AppManifest', 'Per-module component registry'],
            ['/docs/config/integrations', 'Integrations', 'All typed integration dataclasses'],
            ['/docs/config/module', 'Module Builder', 'Module routing, tags, dependencies'],
          ].map(([href, label, desc]) => (
            <Link key={href as string} to={href as string} className={`flex flex-col gap-0.5 group ${isDark ? 'hover:text-aquilia-300' : 'hover:text-aquilia-600'} transition-colors`}>
              <span className={`text-sm font-semibold flex items-center gap-1 ${isDark ? 'text-aquilia-400 group-hover:text-aquilia-300' : 'text-aquilia-600 group-hover:text-aquilia-500'}`}>
                <ArrowRight className="w-3 h-3" />{label}
              </span>
              <span className={`text-xs ${subtxt}`}>{desc}</span>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}