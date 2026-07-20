import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import {
  Settings, Lock, Eye, Layers, ArrowRight, CheckCircle,
  Shield, Code, Hash, RefreshCcw, AlertTriangle, Cpu,
} from 'lucide-react'

export function ConfigPyConfig() {
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
                AquilaConfig
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.pyconfig — Python-native, zero-YAML environment configuration</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> is the base class for environment-specific configuration. Subclass it once per environment, override only what changes, and use <DocTerm id="config.env">Env</DocTerm> to bind fields to OS environment variables or <DocTerm id="config.secret">Secret</DocTerm> to protect sensitive values. All of this lives directly in <code>workspace.py</code>.
        </p>
      </div>

      {/* Why section */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-5 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Why Python-native config
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { icon: <Code className="w-4 h-4 text-aquilia-400" />, title: 'IDE Autocomplete', body: 'Pyright and Pylance know every field. Ctrl-click navigates to the definition. Rename refactoring works across the whole project.' },
            { icon: <Shield className="w-4 h-4 text-aquilia-400" />, title: 'Type Safety', body: 'Mypy catches a missing required Secret, a wrong port type, or a misspelled section name before the process starts.' },
            { icon: <Hash className="w-4 h-4 text-aquilia-400" />, title: 'Zero Parsing', body: 'No YAML indentation errors, no JSON commas. Config is just evaluated Python — fast and deterministic.' },
          ].map(({ icon, title, body }) => (
            <div key={title} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">{icon}<strong className={`text-sm font-semibold ${head}`}>{title}</strong></div>
              <p className={`text-xs leading-relaxed ${subtxt}`}>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AquilaConfig base class */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          AquilaConfig — layered inheritance
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Subclass <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> once per deployment environment. The <code>env</code> attribute is the identifier — <code>AQ_ENV=prod</code> selects the class whose <code>env = "prod"</code>. Only override the nested sections that change between environments; everything else is inherited from the base class automatically.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace, Module
from aquilia.pyconfig import AquilaConfig, Env, Secret

# ─── Shared baseline ────────────────────────────────────────────────────────
class BaseEnv(AquilaConfig):
    """Shared across all environments — only changed fields are redefined."""

    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = Env("PORT", default=8000, cast=int)
        workers = 1
        timeout_keep_alive = 5

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm  = "HS256"            # Zero-dependency HMAC-SHA-256
        access_token_ttl_minutes = 60
        refresh_token_ttl_days   = 30

    class database(AquilaConfig.Database):
        url         = Env("DATABASE_URL", default="sqlite:///dev.db")
        pool_size   = 5
        auto_migrate = False

    class cache(AquilaConfig.Cache):
        backend     = "memory"
        default_ttl = 300

    class di(AquilaConfig.DI):
        scope_enforcement   = "warn"    # "warn" | "raise" | "off"
        parallel_resolution = False

    class signing(AquilaConfig.Signing):
        secret = Secret(env="AQ_SECRET_KEY", required=True)

# ─── Development overrides ───────────────────────────────────────────────────
class DevEnv(BaseEnv):
    env = "dev"                         # selected by AQ_ENV=dev

    class server(BaseEnv.server):
        reload = True
        debug  = True
        log_level = "debug"

    class di(BaseEnv.di):
        diagnostics_enabled = True      # trace every resolution in dev

# ─── Staging overrides ───────────────────────────────────────────────────────
class StagingEnv(BaseEnv):
    env = "staging"                     # selected by AQ_ENV=staging

    class server(BaseEnv.server):
        host    = "0.0.0.0"
        workers = 2
        debug   = False

# ─── Production overrides ────────────────────────────────────────────────────
class ProdEnv(BaseEnv):
    env = "prod"                        # selected by AQ_ENV=prod

    class server(BaseEnv.server):
        host    = "0.0.0.0"
        workers = Env("WEB_WORKERS", default=4, cast=int)
        timeout_keep_alive        = 30
        timeout_graceful_shutdown = 30
        proxy_headers             = True
        forwarded_allow_ips       = "*"

    class auth(BaseEnv.auth):
        password_hasher = AquilaConfig.PasswordHasher.argon2id(
            time_cost=3, memory_cost=131072
        )

    class database(BaseEnv.database):
        pool_size   = 20
        auto_migrate = True

    class di(BaseEnv.di):
        scope_enforcement   = "raise"   # fail-fast on captive deps
        parallel_resolution = True      # resolve independent deps concurrently

# ─── Wire into Workspace ─────────────────────────────────────────────────────
workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)                # reads AQ_ENV → selects DevEnv / ProdEnv
    .module(...)
)`} />
      </section>

      {/* Built-in sections */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Built-in section types
        </h2>
        <p className={`mb-4 ${txt}`}>
          Each section type provides typed defaults, IDE hover docs, and a clean interface for overriding only what changes. Extend any of them inside your <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclass.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Section</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Key fields</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Purpose</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['AquilaConfig.Server', 'host, port, workers, reload, debug, timeout_keep_alive, timeout_graceful_shutdown, proxy_headers, ssl_certfile, log_level…', 'ASGI/uvicorn server — every field maps 1-to-1 to uvicorn.Config'],
                ['AquilaConfig.Auth', 'secret_key, algorithm, issuer, audience, access_token_ttl_minutes, refresh_token_ttl_days, require_auth_by_default, password_hasher', 'JWT signing key, token TTLs, and password hashing policy'],
                ['AquilaConfig.PasswordHasher', 'algorithm, time_cost, memory_cost, parallelism, bcrypt_rounds, scrypt_n', 'Argon2id / bcrypt / scrypt / PBKDF2 tuning — class-method shortcuts available'],
                ['AquilaConfig.Database', 'url, pool_size, echo, auto_migrate, auto_connect, migrations_dir', 'Database connection URL and pool/migration settings'],
                ['AquilaConfig.Cache', 'backend, default_ttl, max_size, eviction_policy, namespace, key_prefix, redis_url', 'Cache backend (memory / redis / composite)'],
                ['AquilaConfig.DI', 'scope_enforcement, parallel_resolution, diagnostics_enabled, disposal_strategy, pool_max_waiters, enable_plugins, strict_service_registration…', 'Dependency-injection container runtime knobs — populates DISettings at boot'],
                ['AquilaConfig.Sessions', 'enabled, store_type, cookie_name, cookie_secure, cookie_httponly, ttl_days, idle_timeout_minutes', 'Session store and cookie transport settings'],
                ['AquilaConfig.Mail', 'enabled, default_from, console_backend, require_tls, retry_max_attempts', 'SMTP connection settings'],
                ['AquilaConfig.Security', 'cors_enabled, csrf_protection, helmet_enabled, rate_limiting, https_redirect, hsts', 'Security middleware feature flags'],
                ['AquilaConfig.Logging', 'level, colorize, slow_threshold_ms, include_headers', 'Application log verbosity and format'],
                ['AquilaConfig.I18n', 'default_locale, available_locales, fallback_locale, catalog_dirs, catalog_format', 'Internationalisation settings'],
                ['AquilaConfig.Signing', 'secret, fallback_secrets, algorithm, salt, session_salt, csrf_salt, activation_salt, cache_salt', 'Cryptographic signing — sessions, CSRF tokens, activation links, cache integrity'],
                ['AquilaConfig.Render', 'service_name, region, plan, num_instances, image, health_path, auto_deploy, port', 'Render PaaS deployment config — used by aq deploy render'],
                ['AquilaConfig.Apps', '(nested per-module classes)', 'Module-specific config namespaces — accessed as config.apps.users.max_items'],
                ['AquilaConfig.Dotenv', 'file, files, auto_load, override, interpolate, strict', 'Dotenv file loading policy — which files to load and in what order'],
              ].map(([section, fields, purpose], i) => (
                <tr key={i} className={hov}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{section}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{fields}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Server section deep-dive */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-3 flex items-center gap-2 ${head}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          AquilaConfig.Server — full reference
        </h2>
        <p className={`mb-4 text-sm leading-relaxed ${txt}`}>
          Every attribute maps directly to a <code>uvicorn.Config</code> parameter and is forwarded automatically. No glue code required — adding a new field here is all you need.
        </p>
        <CodeBlock language="python" code={`class server(AquilaConfig.Server):
    # ── Core ──────────────────────────────────────────────
    host    = "0.0.0.0"
    port    = Env("PORT", default=8000, cast=int)
    workers = Env("WEB_WORKERS", default=4, cast=int)
    uds     = None           # Unix domain socket path (alternative to host:port)
    fd      = None           # File descriptor to bind
    debug   = False
    mode    = "prod"

    # ── Hot reload (dev only) ─────────────────────────────
    reload          = False
    reload_dirs     = ["app/", "modules/"]
    reload_delay    = 0.25      # seconds between checks
    reload_includes = ["*.py"]  # glob patterns to include
    reload_excludes = ["*.pyc"] # glob patterns to exclude

    # ── Protocol ─────────────────────────────────────────
    http      = "auto"   # "auto" | "h11" | "httptools"
    ws        = "auto"   # "auto" | "wsproto" | "websockets" | "none"
    lifespan  = "auto"   # "auto" | "on" | "off"
    interface = "auto"   # "auto" | "asgi3" | "asgi2" | "wsgi"
    loop      = "auto"   # "auto" | "asyncio" | "uvloop"

    # ── Timeouts ─────────────────────────────────────────
    timeout_keep_alive        = 5    # seconds (HTTP keep-alive idle)
    timeout_graceful_shutdown = 30   # None = wait forever
    timeout_worker_healthcheck = 30  # seconds before worker is restarted

    # ── Limits ───────────────────────────────────────────
    backlog           = 2048
    limit_concurrency = None   # max concurrent connections
    limit_max_requests = None  # restart worker after N requests

    # ── Proxy / Headers ──────────────────────────────────
    proxy_headers       = True
    forwarded_allow_ips = "*"   # comma-separated or "*" (trust all)
    server_header       = True
    date_header         = True
    root_path           = ""    # ASGI root_path for reverse proxy

    # ── Logging ──────────────────────────────────────────
    access_log = True
    log_level  = "info"         # critical|error|warning|info|debug|trace
    use_colors = None           # None = auto-detect terminal

    # ── WebSocket ────────────────────────────────────────
    ws_max_size            = 16_777_216   # 16 MiB
    ws_max_queue           = 32
    ws_ping_interval       = 20.0         # seconds
    ws_ping_timeout        = 20.0         # seconds
    ws_per_message_deflate = True

    # ── TLS / SSL ────────────────────────────────────────
    ssl_certfile         = "/etc/certs/cert.pem"
    ssl_keyfile          = "/etc/certs/key.pem"
    ssl_keyfile_password = None
    ssl_ca_certs         = None
    ssl_ciphers          = "TLSv1"

    # ── HTTP/1.1 ─────────────────────────────────────────
    h11_max_incomplete_event_size = None  # bytes; None = h11 default (16 KiB)`} />
      </section>

      {/* Env descriptor */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Eye className="w-5 h-5 text-aquilia-400" />
          Env — live environment variable binding
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          <DocTerm id="config.env">Env</DocTerm> is a descriptor that reads from <code>os.environ</code> at attribute access time. Values already in the process environment (from Docker, Kubernetes, or CI/CD) always win over source-code defaults. The dotenv loader is triggered automatically on first access — you never call <code>load_dotenv()</code> manually.
        </p>
        <CodeBlock language="python" code={`from aquilia.pyconfig import Env

class server(AquilaConfig.Server):
    # cast=int  → "8000" string becomes integer 8000
    port    = Env("PORT",        default=8000,        cast=int)
    workers = Env("WEB_WORKERS", default=4,           cast=int)

    # cast=bool → "true"/"yes"/"on"/"1" → True; "false"/"no"/"off"/"0" → False
    debug   = Env("AQ_DEBUG",    default=False,       cast=bool)

    # No cast — auto-casts: int → float → JSON → str
    host    = Env("AQ_HOST",     default="127.0.0.1")

    # required=True → raises ConfigMissingFault if unset and no default
    db_url  = Env("DATABASE_URL", required=True)

class auth(AquilaConfig.Auth):
    # Access via descriptor protocol: no .resolve() call needed
    access_token_ttl_minutes = Env("JWT_TTL_MINUTES", default=60, cast=int)

# ── Advanced: disable auto-load for explicit control ─────────────────────────
from aquilia.pyconfig import Env
Env.disable_auto_load()
from aquilia.dotenv import load_dotenv
load_dotenv(".env.custom")         # Load manually
Env.enable_auto_load()             # Re-enable for subsequent accesses`} />

        <p className={`mt-4 mb-3 text-sm font-semibold ${head}`}>Auto-cast rules (no <code>cast=</code> specified)</p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Raw string value</th>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Resolved Python value</th>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Type</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['"42"',          '42',             'int'],
                ['"3.14"',        '3.14',           'float'],
                ['"[1,2,3]"',    '[1, 2, 3]',      'list (JSON)'],
                ['\'{"k":"v"}\'', '{"k": "v"}',    'dict (JSON)'],
                ['"hello"',       '"hello"',        'str (fallback)'],
              ].map(([raw, out, t], i) => (
                <tr key={i} className={hov}>
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-400">{raw}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${subtxt}`}>{out}</td>
                  <td className={`px-4 py-2 text-xs ${subtxt}`}>{t}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Secret */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Lock className="w-5 h-5 text-aquilia-400" />
          Secret — redacted sensitive values
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          <DocTerm id="config.secret">Secret</DocTerm> wraps any sensitive value — API keys, database passwords, signing keys. The underlying value <strong>never</strong> appears in <code>repr()</code>, <code>str()</code>, log output, or serialised config until you call <code>.reveal()</code> deliberately. The resolution order is: env var → literal value → default.
        </p>
        <CodeBlock language="python" code={`from aquilia.pyconfig import Secret

class auth(AquilaConfig.Auth):
    # Source from env var — required, will raise ConfigMissingFault if unset
    secret_key = Secret(env="AQ_SECRET_KEY", required=True)

    # Env var with a fallback default (non-required)
    api_key = Secret(env="THIRD_PARTY_API_KEY", default=None)

    # Inline literal — dev only, never commit real values
    dev_token = Secret(value="dev-only-token-abc123")

class signing(AquilaConfig.Signing):
    secret          = Secret(env="AQ_SECRET_KEY", required=True)
    # Key rotation: old tokens still verify against fallback keys
    fallback_secrets = [Secret(env="AQ_OLD_SECRET_KEY")]

# repr() and str() always return <secret> — safe to log
# >>> repr(BaseEnv.auth.secret_key)
# "Secret(env='AQ_SECRET_KEY', *required*)"

# Only .reveal() returns the actual value
key = BaseEnv.auth.secret_key.reveal()   # → "actual-key-value-from-env"

# Properties
is_required = BaseEnv.auth.secret_key.is_required   # → True
env_var_name = BaseEnv.auth.secret_key.env_name      # → "AQ_SECRET_KEY"`} />

        <div className={`mt-4 p-3 rounded-xl border-l-4 border-rose-500/60 text-sm ${isDark ? 'bg-rose-950/15 text-rose-300' : 'bg-rose-50 text-rose-700'}`}>
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <div><strong>Never commit literal Secret values.</strong> <code>Secret(value="...")</code> is for local dev only. In staging and production always point to an env var: <code>Secret(env="MY_KEY", required=True)</code>.</div>
          </div>
        </div>
      </section>

      {/* PasswordHasher */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          AquilaConfig.PasswordHasher
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Controls the password hashing algorithm used by the auth subsystem. Class-method shortcuts provide sensible defaults for each algorithm.
        </p>
        <CodeBlock language="python" code={`class auth(AquilaConfig.Auth):
    # ── Factory shortcuts (recommended) ──────────────────────────────────
    password_hasher = AquilaConfig.PasswordHasher.argon2id(
        time_cost=3, memory_cost=131072  # 128 MiB
    )

    # Other algorithms:
    # password_hasher = AquilaConfig.PasswordHasher.bcrypt(rounds=14)
    # password_hasher = AquilaConfig.PasswordHasher.scrypt(n=65536, r=8, p=1)
    # password_hasher = AquilaConfig.PasswordHasher.pbkdf2_sha512(iterations=260000)

    # ── Full constructor (all params) ─────────────────────────────────────
    password_hasher = AquilaConfig.PasswordHasher(
        algorithm="argon2id",
        time_cost=2,            # iterations
        memory_cost=65536,      # KiB (64 MiB default)
        parallelism=4,          # threads
        hash_len=32,            # output bytes
        salt_len=16,            # random salt bytes
    )`} />

        <div className={`mt-4 rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Algorithm</th>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Factory method</th>
              <th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Notes</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['argon2id', 'PasswordHasher.argon2id(time_cost, memory_cost, parallelism)', 'Recommended — winner of Password Hashing Competition, memory-hard'],
                ['bcrypt', 'PasswordHasher.bcrypt(rounds=12)', 'Widely-supported, CPU-bound. Use rounds ≥ 12 for production'],
                ['scrypt', 'PasswordHasher.scrypt(n, r, p, dklen)', 'Memory-hard like Argon2. Older but mature'],
                ['pbkdf2_sha512', 'PasswordHasher.pbkdf2_sha512(iterations=210000)', 'FIPS-compliant, stdlib-only (no extra packages)'],
                ['pbkdf2_sha256', 'PasswordHasher.pbkdf2_sha256(iterations=600000)', 'Legacy fallback — migrate to pbkdf2_sha512 or argon2id'],
              ].map(([algo, method, note], i) => (
                <tr key={i} className={hov}>
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-400">{algo}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${subtxt}`}>{method}</td>
                  <td className={`px-4 py-2 text-xs ${txt}`}>{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Signing section */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Lock className="w-5 h-5 text-aquilia-400" />
          AquilaConfig.Signing — cryptographic signing
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Controls the <code>aquilia.signing</code> module that backs session cookies, CSRF tokens, one-time activation links, cache integrity checks, and signed cookies. Each subsystem uses an isolated namespace salt so cross-subsystem token reuse is cryptographically impossible.
        </p>
        <CodeBlock language="python" code={`class signing(AquilaConfig.Signing):
    # Primary signing secret — required in production
    secret           = Secret(env="AQ_SECRET_KEY", required=True)

    # Key rotation: old tokens verified against fallback keys,
    # new tokens always signed with 'secret'
    fallback_secrets = [Secret(env="AQ_OLD_SECRET_KEY")]

    # Algorithm: "HS256" (default) | "HS384" | "HS512" — all stdlib, no deps
    algorithm = "HS256"

    # ── Per-subsystem salts (rarely need to change) ──────────────────────
    # Each salt isolates token forgery across subsystems
    session_salt    = "aquilia.sessions"    # session cookies
    csrf_salt       = "aquilia.csrf"        # CSRF tokens
    activation_salt = "aquilia.activation"  # password-reset / activation links
    cache_salt      = "aquilia.cache"       # signed cache values`} />
      </section>

      {/* @section decorator */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          @section — custom config grouping
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          The <code>@section</code> decorator marks any arbitrary nested class as a named config section included in the serialised <code>to_dict()</code> output. Use it for app-specific subsystems that don't map to a built-in section type.
        </p>
        <CodeBlock language="python" code={`from aquilia.pyconfig import AquilaConfig, section, Env, Secret

class MyConfig(AquilaConfig):

    @section
    class stripe:
        publishable_key = Env("STRIPE_PK", required=True)
        secret_key      = Secret(env="STRIPE_SK", required=True)
        webhook_secret  = Secret(env="STRIPE_WEBHOOK_SECRET", required=True)
        test_mode       = Env("STRIPE_TEST_MODE", default=True, cast=bool)

    @section
    class feature_flags:
        new_dashboard   = Env("FF_NEW_DASHBOARD",  default=False, cast=bool)
        beta_api        = Env("FF_BETA_API",        default=False, cast=bool)
        dark_mode_only  = Env("FF_DARK_MODE",       default=False, cast=bool)

    @section
    class rate_limits:
        api_requests_per_minute = Env("RATE_API_RPM", default=60, cast=int)
        auth_attempts_per_hour  = Env("RATE_AUTH_APH", default=10, cast=int)`} />
      </section>

      {/* AquilaConfig.Dotenv */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          AquilaConfig.Dotenv — file loading policy
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Control exactly which <code>.env</code> files are loaded and in what order. Define a nested <code>Dotenv</code> class inside your <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclass.
        </p>
        <CodeBlock language="python" code={`class MyConfig(AquilaConfig):
    class Dotenv(AquilaConfig.Dotenv):
        # Ordered list — later files override earlier ones
        files = [
            ".env",
            ".env.defaults",
            AquilaConfig.EnvFile(".env.{env}"),              # e.g. .env.prod
            AquilaConfig.EnvFile(".env.local", required=False),
        ]
        auto_load   = True    # trigger automatically on first Env/Secret access
        override    = False   # never overwrite existing process env vars
        interpolate = True    # expand $VAR and ${'$'}{VAR} references inside .env files
        strict      = False   # True → raise if any file in files[] is missing

# Without a Dotenv class, Aquilia searches for:
# .env, .env.defaults, .env.local, .env.{env}, .env.{env}.local`} />
      </section>

      {/* AquilaConfig.Apps */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>AquilaConfig.Apps — per-module namespaces</h2>
        <p className={`mb-4 ${txt}`}>
          Place module-specific settings inside a nested class named after the module. Access them via <code>config.apps.&lt;module_name&gt;.&lt;field&gt;</code> inside that module's services or controllers.
        </p>
        <CodeBlock language="python" code={`class apps(AquilaConfig.Apps):
    class auth:
        max_login_attempts  = Env("AUTH_MAX_ATTEMPTS", default=5, cast=int)
        lockout_minutes     = Env("AUTH_LOCKOUT_MIN",  default=15, cast=int)
        mfa_required        = Env("AUTH_MFA_REQUIRED", default=False, cast=bool)

    class users:
        cache_ttl           = 300        # seconds
        max_upload_mb       = 10
        avatar_formats      = ["jpg", "png", "webp"]

    class payments:
        webhook_tolerance_s = 300        # seconds Stripe webhook window
        retry_on_failure    = True

# Consuming inside a service (resolved at boot via ConfigLoader):
class UsersService:
    def __init__(self, config: ConfigLoader):
        self.cache_ttl = config.apps.users.cache_ttl`} />
      </section>

      {/* Runtime API */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <RefreshCcw className="w-5 h-5 text-aquilia-400" />
          Runtime API — to_dict, to_loader, get, for_env
        </h2>
        <CodeBlock language="python" code={`from workspace import BaseEnv, ProdEnv

# Serialise to a plain nested dict (all Env resolved, all Secrets revealed)
cfg = ProdEnv.to_dict()

# Dot-path read without a full loader
port = ProdEnv.get("server.port")         # → int
host = ProdEnv.get("server.host")         # → str
miss = ProdEnv.get("does.not.exist", 42)  # → 42 (default)

# Produce a ConfigLoader (used internally by the framework)
loader = ProdEnv.to_loader()

# Select by name (reads subclass tree recursively)
Config = BaseEnv.for_env("prod")          # → ProdEnv class
loader = Config.to_loader()

# Select by AQ_ENV env var (default: "dev")
Config = BaseEnv.from_env_var("AQ_ENV", default="dev")
loader = Config.to_loader()

# Cache management
ProdEnv.invalidate_cache()                # re-resolve on next access
AquilaConfig.clear_all_caches()           # clear all subclasses + dotenv state`} />
      </section>

      {/* Testing */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Testing patterns</h2>
        <CodeBlock language="python" code={`import pytest, os
from aquilia.pyconfig import AquilaConfig

@pytest.fixture(autouse=True)
def reset_config():
    """Isolate config state between tests."""
    yield
    AquilaConfig.clear_all_caches()   # clears Env caches + dotenv loader state

def test_prod_workers(monkeypatch):
    monkeypatch.setenv("WEB_WORKERS", "8")
    ProdEnv.invalidate_cache()
    assert ProdEnv.get("server.workers") == 8

def test_secret_required(monkeypatch):
    monkeypatch.delenv("AQ_SECRET_KEY", raising=False)
    ProdEnv.invalidate_cache()
    with pytest.raises(Exception):     # raises ConfigMissingFault
        ProdEnv.get("auth.secret_key")

def test_dev_env_selected():
    os.environ["AQ_ENV"] = "dev"
    Config = BaseEnv.from_env_var("AQ_ENV")
    assert Config is DevEnv`} />
      </section>

      {/* Related */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config/dotenv', '.env Files', 'File precedence, syntax, DotEnvLoader API'],
            ['/docs/config/workspace', 'Workspace Builder', 'Wiring AquilaConfig into the application'],
            ['/docs/config/integrations', 'Integrations', 'Typed DatabaseIntegration, AuthIntegration, etc.'],
            ['/docs/config/manifest', 'AppManifest', 'Per-module component registry'],
          ].map(([href, label, desc]) => (
            <Link key={href as string} to={href as string} className={`flex flex-col gap-0.5 group`}>
              <span className={`text-sm font-semibold flex items-center gap-1 ${isDark ? 'text-aquilia-400 group-hover:text-aquilia-300' : 'text-aquilia-600 group-hover:text-aquilia-500'} transition-colors`}>
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
