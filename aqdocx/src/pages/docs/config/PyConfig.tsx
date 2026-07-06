import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Settings, Lock, Eye, Layers, ArrowRight, CheckCircle } from 'lucide-react'

export function ConfigPyConfig() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const txt = isDark ? 'text-gray-300' : 'text-gray-600'
  const subtxt = isDark ? 'text-gray-400' : 'text-gray-500'
  const head = isDark ? 'text-white' : 'text-gray-900'
  const divider = isDark ? 'divide-white/5' : 'divide-gray-100'
  const thead = isDark ? 'bg-zinc-800/80' : 'bg-gray-50'
  const th = isDark ? 'text-gray-300' : 'text-gray-700'
  const hover = isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
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
                AquilaConfig
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.pyconfig — Python-native, zero-YAML environment config</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Aquilia's configuration system is pure Python — no YAML, no TOML, no JSON files. You define nested classes that inherit from <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm>, drop in <DocTerm id="config.env">Env</DocTerm> bindings for live env-var overlay, protect sensitive values with <DocTerm id="config.secret">Secret</DocTerm>, and wire everything into the <DocTerm id="config.workspace">Workspace</DocTerm> with a single call. Your IDE auto-completes it, <code>git blame</code> tracks every change, and <code>mypy</code> type-checks it.
        </p>
      </div>

      {/* Why Python-native */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Why Python-native config?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {[
            { icon: '🔍', title: 'IDE Autocomplete', body: 'Pyright and Pylance know every field. Rename a section and all references update automatically.' },
            { icon: '🔒', title: 'Type Safety', body: 'Mypy catches a missing required Secret or a mistyped port before you ship.' },
            { icon: '⚡', title: 'Zero Parsing', body: 'No YAML indentation errors, no JSON commas. Config is just evaluated Python.' },
          ].map(({ icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2">
              <span className="text-2xl">{icon}</span>
              <strong className={`text-sm font-semibold ${head}`}>{title}</strong>
              <p className={`text-xs leading-relaxed ${subtxt}`}>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AquilaConfig base class */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          AquilaConfig — base class
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Subclass <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> once per environment. Override only the nested section classes you need to change — everything else is inherited. The <code>env</code> string on each class is matched against the <code>AQ_ENV</code> environment variable at boot.
        </p>
        <CodeBlock language="python" code={`from aquilia import AquilaConfig, Env, Secret

# ─── Shared baseline ────────────────────────────────────────
class BaseEnv(AquilaConfig):
    env = "base"

    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = 8000
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key      = Secret(env="AQ_SECRET_KEY", required=True)
        password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")

    class database(AquilaConfig.Database):
        url = Env("DATABASE_URL", default="sqlite:///dev.db")

# ─── Development overrides ─────────────────────────────────
class DevEnv(BaseEnv):
    env = "dev"

    class server(BaseEnv.server):
        reload = True
        debug  = True

# ─── Production overrides ──────────────────────────────────
class ProdEnv(BaseEnv):
    env = "prod"

    class server(BaseEnv.server):
        host    = "0.0.0.0"
        workers = Env("WEB_WORKERS", default=4, cast=int)

    class auth(BaseEnv.auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        password_hasher = AquilaConfig.PasswordHasher(
            algorithm="argon2id",
            time_cost=3,
            memory_cost=131072,   # 128 MiB
        )

# Wire into Workspace — reads AQ_ENV at runtime to pick the right class
workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)   # resolves via AQ_ENV
    .module(...)
)`} />
      </section>

      {/* Built-in sections */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Built-in Section Types
        </h2>
        <p className={`mb-4 ${txt}`}>
          Each section type gives you typed defaults, IDE hover docs, and a clean interface to override only what changes. Extend any of them inside your <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclass.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={thead}>
                <th className={`text-left px-4 py-3 font-semibold ${th}`}>Section</th>
                <th className={`text-left px-4 py-3 font-semibold ${th}`}>Key fields</th>
                <th className={`text-left px-4 py-3 font-semibold ${th}`}>Purpose</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['AquilaConfig.Server', 'host, port, workers, reload, debug, timeout_keep_alive, ssl_certfile, proxy_headers…', 'ASGI server (uvicorn) — every field maps 1-to-1 to uvicorn.Config'],
                ['AquilaConfig.Auth', 'secret_key (Secret), algorithm, password_hasher', 'JWT signing key and password hashing policy'],
                ['AquilaConfig.PasswordHasher', 'algorithm, time_cost, memory_cost, parallelism', 'Argon2id / bcrypt / scrypt tuning params'],
                ['AquilaConfig.Database', 'url, pool_size, echo, auto_migrate', 'Database connection URL and pool settings'],
                ['AquilaConfig.Cache', 'backend, url, ttl', 'Cache backend (memory / redis)'],
                ['AquilaConfig.Sessions', 'secret_key, max_age, store, transport', 'Session signing key, TTL, and transport'],
                ['AquilaConfig.Mail', 'host, port, username, password (Secret), use_tls', 'SMTP connection settings'],
                ['AquilaConfig.Security', 'cors_origins, csrf_enabled, hsts_enabled, csp_policy', 'Security middleware toggles'],
                ['AquilaConfig.Logging', 'level, format, access_log', 'Application log verbosity and format'],
                ['AquilaConfig.I18n', 'locale, timezone, fallback_locale', 'Internationalisation defaults'],
                ['AquilaConfig.Apps', '(nested per-module classes)', 'Module-specific config namespaces — accessed as config.apps.users.max_items'],
              ].map(([section, fields, purpose], i) => (
                <tr key={i} className={hover}>
                  <td className={`px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap`}>{section}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{fields}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* AquilaConfig.Server deep-dive */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-3 ${head}`}>AquilaConfig.Server — full reference</h2>
        <p className={`mb-4 text-sm leading-relaxed ${txt}`}>
          Every attribute maps directly to a <code>uvicorn.Config</code> parameter and is forwarded automatically. Adding a new field here is all you need — no glue code required.
        </p>
        <CodeBlock language="python" code={`class server(AquilaConfig.Server):
    # Core
    host    = "0.0.0.0"
    port    = Env("PORT", default=8000, cast=int)
    workers = Env("WEB_WORKERS", default=4, cast=int)
    debug   = False

    # Reload (dev only)
    reload         = False
    reload_dirs    = ["app/", "modules/"]
    reload_delay   = 0.25           # seconds between checks

    # Protocol
    http      = "auto"              # "auto" | "h11" | "httptools"
    lifespan  = "auto"              # "auto" | "on" | "off"

    # Timeouts & limits
    timeout_keep_alive      = 5     # seconds
    timeout_graceful_shutdown = 30  # seconds, None = wait forever
    limit_concurrency       = None  # max concurrent connections
    limit_max_requests      = None  # restart worker after N requests

    # Proxy
    proxy_headers        = True
    forwarded_allow_ips  = "*"      # trust all upstream proxies

    # Logging
    access_log = True
    log_level  = "info"             # critical|error|warning|info|debug|trace

    # WebSocket
    ws_ping_interval   = 20.0       # seconds
    ws_ping_timeout    = 20.0       # seconds

    # TLS
    ssl_certfile = "/etc/certs/cert.pem"
    ssl_keyfile  = "/etc/certs/key.pem"`} />
      </section>

      {/* Env */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Eye className="w-5 h-5 text-aquilia-400" />
          Env — live environment variable binding
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          <DocTerm id="config.env">Env</DocTerm> is a descriptor that reads from <code>os.environ</code> at attribute access time, so runtime injection (CI/CD, Docker, Kubernetes) always wins over source-code defaults. It automatically triggers the built-in dotenv loader, so you don't need to call <code>load_dotenv()</code> manually.
        </p>
        <CodeBlock language="python" code={`from aquilia import AquilaConfig, Env

class ProdEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        # cast=int  → converts "8000" string to integer 8000
        port    = Env("PORT",        default=8000,        cast=int)
        # cast=bool → "true"/"yes"/"on"/"1" → True
        debug   = Env("AQ_DEBUG",    default=False,       cast=bool)
        workers = Env("WEB_WORKERS", default=4,           cast=int)
        host    = Env("AQ_HOST",     default="127.0.0.1")

    class database(AquilaConfig.Database):
        # No cast needed — URLs stay as strings
        url = Env("DATABASE_URL", default="sqlite:///app.db", required=True)`} />

        <div className="mt-4 mb-4">
          <p className={`text-sm font-semibold mb-3 ${head}`}>Auto-cast rules (no <code>cast=</code> specified)</p>
          <div className={`rounded-xl border overflow-hidden ${border}`}>
            <table className="w-full text-sm">
              <thead><tr className={thead}>
                <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Raw string</th>
                <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Resolved value</th>
              </tr></thead>
              <tbody className={`divide-y ${divider}`}>
                {[
                  ['"42"', '42 (int)'],
                  ['"3.14"', '3.14 (float)'],
                  ['"[1,2,3]"', '[1, 2, 3] (list via JSON)'],
                  ['"{"key":"val"}"', '{"key": "val"} (dict via JSON)'],
                  ['"hello"', '"hello" (str fallback)'],
                ].map(([raw, out], i) => (
                  <tr key={i} className={hover}>
                    <td className="px-4 py-2 font-mono text-xs text-aquilia-400">{raw}</td>
                    <td className={`px-4 py-2 font-mono text-xs ${subtxt}`}>{out}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Secret */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Lock className="w-5 h-5 text-aquilia-400" />
          Secret — redacted sensitive values
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          <DocTerm id="config.secret">Secret</DocTerm> wraps any sensitive value — API keys, database passwords, signing keys. The underlying value never appears in <code>repr()</code>, <code>str()</code>, log output, or <code>to_dict()</code> serialisation. Only an explicit call to <code>.reveal()</code> returns the real string, making it obvious in code reviews where secrets are consumed.
        </p>
        <CodeBlock language="python" code={`from aquilia import AquilaConfig, Secret

class BaseEnv(AquilaConfig):
    class auth(AquilaConfig.Auth):
        # Sources: env var → literal → default (in this order)
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        api_key    = Secret(env="THIRD_PARTY_API_KEY", default=None)

        # Inline literal (dev only — never commit real secrets)
        dev_token  = Secret(value="dev-only-token-abc123")

# repr never leaks the value:
# >>> BaseEnv.auth.secret_key
# Secret(env='AQ_SECRET_KEY', *required*)

# Retrieve deliberately:
key = BaseEnv.auth.secret_key.reveal()   # → "actual-key-value"`} />

        <div className={`mt-4 p-4 rounded-xl border-l-4 border-rose-500/50 ${isDark ? 'bg-rose-950/10' : 'bg-rose-50/50'}`}>
          <p className={`text-sm font-bold text-rose-400 mb-1`}>⚠ Never commit literal Secret values</p>
          <p className={`text-xs leading-relaxed ${subtxt}`}>
            <code>Secret(value="...")</code> is for local dev only. In staging and production always point to an env var: <code>Secret(env="MY_KEY", required=True)</code> and inject the value via CI/CD secrets or a secrets manager.
          </p>
        </div>
      </section>

      {/* @section decorator */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>@section — custom config grouping</h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          The <code>@section</code> decorator marks any arbitrary nested class as a named config section, included in the deep-merged dict returned by <code>to_dict()</code>. Use it for subsystems that don't map to a built-in section type.
        </p>
        <CodeBlock language="python" code={`from aquilia import AquilaConfig
from aquilia.pyconfig import section

class MyConfig(AquilaConfig):

    @section
    class stripe:
        api_key       = Secret(env="STRIPE_API_KEY", required=True)
        webhook_secret = Secret(env="STRIPE_WEBHOOK_SECRET", required=True)
        test_mode     = Env("STRIPE_TEST_MODE", default=True, cast=bool)

    @section
    class feature_flags:
        new_dashboard = Env("FF_NEW_DASHBOARD", default=False, cast=bool)
        beta_api      = Env("FF_BETA_API",      default=False, cast=bool)`} />
      </section>

      {/* Dotenv class */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>AquilaConfig.Dotenv — file loading policy</h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Control exactly which <code>.env</code> files are loaded and in what order. Define a nested <code>Dotenv</code> class inside your <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclass.
        </p>
        <CodeBlock language="python" code={`class MyConfig(AquilaConfig):
    class Dotenv(AquilaConfig.Dotenv):
        # Ordered list of files to load (later files override earlier ones)
        files = [
            ".env",
            ".env.defaults",
            AquilaConfig.EnvFile(".env.{env}"),           # interpolated with AQ_ENV
            AquilaConfig.EnvFile(".env.local", required=False),
        ]
        auto_load   = True    # load automatically when Env/Secret is first accessed
        override    = False   # never overwrite existing process env vars
        interpolate = True    # expand ${'$'}{VAR} / $VAR syntax inside .env files
        strict      = False   # True → raise if any file in files[] is missing`} />

        <div className="mt-4 flex items-start gap-2">
          <ArrowRight className="w-4 h-4 text-aquilia-400 mt-0.5 shrink-0" />
          <p className={`text-sm leading-relaxed ${txt}`}>
            If no <code>Dotenv</code> class is defined, Aquilia searches for <code>.env</code>, <code>.env.local</code>, <code>.env.{'{'}env{'}'}</code>, <code>.env.{'{'}env{'}'}.local</code> automatically.
          </p>
        </div>
      </section>

      {/* Loading */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Loading config at runtime</h2>
        <CodeBlock language="python" code={`# Option 1: Wire into workspace — automatic, recommended
workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)     # reads AQ_ENV to pick DevEnv / ProdEnv / BaseEnv
)

# Option 2: Load manually
loader = BaseEnv.from_env_var().to_loader()   # reads AQ_ENV
loader = ProdEnv.to_loader()                  # explicit class

# Option 3: Pick by class directly
from aquilia.pyconfig import AquilaConfig
loader = AquilaConfig.load(ProdEnv)

# Access loaded values via ConfigLoader (used internally by subsystems)
config = ConfigLoader()
port = config.get("server.port")          # → int
db   = config.get("database.url")         # → str`} />
      </section>

      {/* Related */}
      <section className="mb-12 border-t border-white/5 pt-8">
        <div className="flex flex-col gap-2">
          <Link to="/docs/config/dotenv" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → .env files: DotEnv loader, syntax, and precedence
          </Link>
          <Link to="/docs/config/workspace" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Workspace: wiring AquilaConfig into the app
          </Link>
          <Link to="/docs/config/integrations" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Integrations: typed subsystem configuration
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
