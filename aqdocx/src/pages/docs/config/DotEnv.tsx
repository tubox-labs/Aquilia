import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { FileText, Shield, CheckCircle, Layers, RefreshCcw, AlertTriangle, Search, Lock } from 'lucide-react'

export function ConfigDotEnv() {
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
            <FileText className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${head}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                .env Files
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.dotenv — zero-dependency, production-ready .env loader</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Aquilia ships its own <DocTerm id="config.dotenv">DotEnv</DocTerm> loader — no <code>python-dotenv</code> required. It loads <code>.env</code> files automatically before any <DocTerm id="config.env">Env</DocTerm> or <DocTerm id="config.secret">Secret</DocTerm> binding is first resolved. It supports variable interpolation, multiline values, the <code>export</code> keyword, and escape sequences in double-quoted strings. Values already in the process environment are <strong>never overwritten</strong> by default — Docker, Kubernetes, and CI/CD injected secrets always win.
        </p>
      </div>

      {/* How it loads — visual cascade */}
      <div className="w-full mb-12">
        <svg className="w-full" viewBox="0 0 680 120" fill="none">
          <defs>
            <linearGradient id="dotenvGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
            <marker id="dearrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="rgba(255,255,255,0.25)" />
            </marker>
          </defs>
          {/* Track */}
          <path d="M 40 60 L 640 60" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
          <path d="M 40 60 L 590 60" stroke="url(#dotenvGrad)" strokeWidth="2" strokeOpacity="0.4" />

          {/* Nodes */}
          {[
            { cx: 60,  label: '.env',            sub: 'base defaults',         color: '#10b981' },
            { cx: 185, label: '.env.local',       sub: 'local overrides',       color: '#34d399' },
            { cx: 320, label: '.env.{env}',       sub: 'env-specific',          color: '#f59e0b' },
            { cx: 460, label: '.env.{env}.local', sub: 'local env-specific',    color: '#3b82f6' },
            { cx: 590, label: 'os.environ',       sub: 'process — always wins', color: '#8b5cf6' },
          ].map(({ cx, label, sub, color }, i) => (
            <g key={i}>
              {i < 4 && (
                <line x1={cx + 18} y1={60} x2={cx + (i === 0 ? 111 : i === 1 ? 115 : i === 2 ? 122 : 110)} y2={60}
                  stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" markerEnd="url(#dearrow)" />
              )}
              <circle cx={cx} cy={60} r={14} fill={isDark ? '#18181b' : '#f9fafb'} stroke={color} strokeWidth="1.5" />
              <text x={cx} y={32} textAnchor="middle" fill={color} fontSize="8" fontWeight="600" fontFamily="monospace">{label}</text>
              <text x={cx} y={90} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">{sub}</text>
            </g>
          ))}
          <text x="340" y="112" textAnchor="middle" fill="rgba(255,255,255,0.18)" fontSize="7.5" fontFamily="sans-serif">← lower priority · · · · · · · · · · · · higher priority →</text>
        </svg>
      </div>

      {/* Quick start */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Quick start
        </h2>
        <p className={`mb-4 ${txt}`}>
          In most apps you never call <code>load_dotenv()</code> at all — loading fires automatically the first time any <DocTerm id="config.env">Env</DocTerm> or <DocTerm id="config.secret">Secret</DocTerm> descriptor is resolved. If you need explicit control:
        </p>
        <CodeBlock language="python" code={`from aquilia.dotenv import load_dotenv, DotEnv, is_dotenv_loaded

# ── Auto-load (idempotent — always safe to call multiple times) ───────────────
load_dotenv()                            # searches workspace root for .env

# ── Load a specific file ──────────────────────────────────────────────────────
load_dotenv(".env.production")           # returns True if any values were loaded

# ── Load with override (replace existing os.environ values) ──────────────────
load_dotenv(override=True)               # use only in tests

# ── Parse WITHOUT loading into os.environ ────────────────────────────────────
values: dict[str, str] = DotEnv.parse(".env")
print(values["DATABASE_URL"])            # reads the file, returns dict, no side effects

# ── Parse from a raw string ───────────────────────────────────────────────────
values = DotEnv.parse_string("HOST=localhost\nPORT=8000")

# ── Check if already loaded ───────────────────────────────────────────────────
if not is_dotenv_loaded():
    load_dotenv()`} />
      </section>

      {/* Full syntax reference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <FileText className="w-5 h-5 text-aquilia-400" />
          Complete syntax reference
        </h2>
        <p className={`mb-4 ${txt}`}>
          Aquilia's parser is a strict, safe subset of the de-facto <code>.env</code> standard. No shell expansion, no subshells, no <code>eval()</code>.
        </p>
        <CodeBlock language="bash" code={`# ── Comments ─────────────────────────────────────────────────────────────
# Lines starting with # are ignored

# ── Simple assignments ────────────────────────────────────────────────────
SIMPLE=value                             # unquoted — inline # starts a comment
QUOTED="value with spaces"              # double-quoted — escape sequences processed
SINGLE='literal value'                   # single-quoted — no escape processing

# ── The export keyword is accepted and silently stripped ─────────────────
export EXPOSED=something                 # same as EXPOSED=something
EXPORT=also valid                        # bare EXPORT=... also works

# ── Booleans (Env(cast=bool) understands all of these) ──────────────────
AQ_DEBUG=true                            # → True
AQ_DEBUG=false                           # → False
AQ_DEBUG=yes                             # → True
AQ_DEBUG=no                              # → False
AQ_DEBUG=on                              # → True
AQ_DEBUG=off                             # → False
AQ_DEBUG=1                               # → True
AQ_DEBUG=0                               # → False

# ── Auto-cast numbers (when no cast= on Env) ────────────────────────────
PORT=8000                                # → int 8000
RATIO=0.95                               # → float 0.95

# ── Variable interpolation ────────────────────────────────────────────────
# \${VAR} and $VAR are both supported. Lookup order:
#   already-resolved vars in this file → earlier lines → os.environ
BASE_URL=http://localhost:8000
API_URL=\${BASE_URL}/api                  # → "http://localhost:8000/api"
ALT_URL=$BASE_URL/v2                     # → same without braces
ESCAPE_DOLLAR=\$100                       # \\$ is a literal dollar sign

# ── Escape sequences (double-quoted only) ────────────────────────────────
NEWLINES="line1\nline2\nline3"           # \\n → actual newline
TABS="col1\tcol2"                        # \\t → actual tab
ESCAPED_QUOTE="He said \"hello\""        # \\" → literal double-quote
ESCAPED_DOLLAR="Price: \$50"             # \\$ → literal dollar sign

# ── Multiline values (double or single quotes) ───────────────────────────
PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA3jGkVFKA...
-----END RSA PRIVATE KEY-----"

# ── Inline comments (unquoted values only) ───────────────────────────────
HOST=localhost    # this part is stripped
FULL="value # not a comment"            # inside quotes → literal #`} />
      </section>

      {/* File precedence table */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>File precedence and environment cascade</h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          Aquilia searches for files in this exact order, resolved from the <strong>workspace root</strong> (the directory containing <code>workspace.py</code>). Later files override earlier ones. <code>os.environ</code> always wins regardless of <code>override</code> — that flag only controls whether dotenv values overwrite other dotenv-sourced values.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>File</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Priority</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Commit?</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Purpose</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['.env',                 '1 — Lowest',    'Yes — no secrets',     'Shared defaults committed to version control. Safe non-secret values only.'],
                ['.env.local',           '2',             'No — gitignore',       'Developer-local overrides. Never shared or committed. Add to .gitignore.'],
                ['.env.{env}',           '3',             'Usually yes',          'Environment-specific values (.env.dev, .env.staging, .env.prod). Non-sensitive settings committed here.'],
                ['.env.{env}.local',     '4 — Highest',   'No — gitignore',       'Local per-environment overrides for developer machines. Never committed.'],
                ['config/.env',          'Parallel',      'Yes',                  'Alternative location under config/ — same rules as .env.'],
                ['config/.env.{env}',    'Parallel',      'Usually yes',          'Alternative location for env-specific config under config/.'],
                ['os.environ (process)', 'Always wins',   '—',                    'CI/CD, Docker, Kubernetes. Never overwritten by .env files (override=False default).'],
                ['.env.example',         'Never loaded',  'Yes',                  'Template checked into VCS for onboarding. Not a config source — copy to .env to use.'],
              ].map(([file, priority, commit, purpose], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{file}</td>
                  <td className={`px-4 py-3 text-xs font-semibold whitespace-nowrap ${i === 6 ? 'text-purple-400' : i === 7 ? 'text-gray-500' : subtxt}`}>{priority}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{commit}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={`mt-4 p-3 rounded-xl border-l-4 border-amber-500/60 text-sm ${isDark ? 'bg-amber-950/15 text-amber-300' : 'bg-amber-50 text-amber-800'}`}>
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>Add <code>.env.local</code> and <code>.env.*.local</code> to your <code>.gitignore</code>. These files are for machine-specific secrets and should never reach version control.</span>
          </div>
        </div>
      </section>

      {/* How workspace root is found */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Search className="w-5 h-5 text-aquilia-400" />
          Workspace root discovery
        </h2>
        <p className={`mb-4 ${txt}`}>
          Before loading any file, Aquilia resolves the workspace root directory. The search order is:
        </p>
        <ol className={`space-y-2 text-sm pl-4 list-decimal ${txt}`}>
          <li><code>AQUILIA_WORKSPACE</code> environment variable — if set, used directly as the root path.</li>
          <li>Current working directory (<code>cwd</code>) — if it contains <code>workspace.py</code>.</li>
          <li>Walk up the directory tree — up to 10 levels, checking each parent for <code>workspace.py</code>.</li>
          <li>Fall back to <code>cwd</code> if no <code>workspace.py</code> is found anywhere.</li>
        </ol>
        <CodeBlock language="python" code={`from aquilia.dotenv import find_dotenv

# find_dotenv() applies the same workspace-root search
path = find_dotenv()                       # → Path("/path/to/project/.env") or None
path = find_dotenv(".env.staging")         # find a specific filename
path = find_dotenv(usecwd=True)            # restrict to current directory only
path = find_dotenv(raise_error=True)       # raise FileNotFoundError if not found`} />

        <p className={`mt-4 text-sm ${txt}`}>
          The environment mode used for <code>{'{env}'}</code> substitution in file paths is resolved from <code>AQUILIA_ENV</code> → <code>AQ_ENV</code> → <code>"dev"</code>. The value <code>"production"</code> is normalised to <code>"prod"</code> automatically.
        </p>
      </section>

      {/* DotEnv class — full API */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <FileText className="w-5 h-5 text-aquilia-400" />
          DotEnv class — parse and load
        </h2>
        <p className={`mb-4 ${txt}`}>
          The <code>DotEnv</code> class exposes two independent operations: <strong>parse</strong> (reads file → returns dict, no side effects) and <strong>load</strong> (reads file → writes to <code>os.environ</code>). Use parse when you need to inspect values without affecting the running process.
        </p>
        <CodeBlock language="python" code={`from aquilia.dotenv import DotEnv
from pathlib import Path

# ── Parse: read file, return dict, NO side effects ───────────────────────────
values = DotEnv.parse(".env")
values = DotEnv.parse(".env.prod", encoding="utf-8")
values = DotEnv.parse(".env", interpolate=False)   # disable \${VAR} expansion

# ── Parse from an in-memory string ───────────────────────────────────────────
values = DotEnv.parse_string("HOST=db\nPORT=5432")
values = DotEnv.parse_string(my_string, interpolate=True)

# ── Load: parse AND write to os.environ ──────────────────────────────────────
loaded = DotEnv.load(".env")                       # returns {key: value} of loaded vars
loaded = DotEnv.load(Path(".env.local"))            # accepts pathlib.Path
loaded = DotEnv.load(".env", override=True)         # replace existing env vars
loaded = DotEnv.load(".env", interpolate=False)     # skip \${VAR} expansion
loaded = DotEnv.load(None)                          # None → auto-finds .env via find_dotenv()`} />
      </section>

      {/* DotEnvLoader — singleton */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          DotEnvLoader — singleton for automatic loading
        </h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          <code>DotEnvLoader</code> is the framework's internal singleton that ensures <code>.env</code> files are loaded <strong>exactly once</strong>, thread-safely, regardless of how many concurrent requests access <code>Env</code> descriptors simultaneously. It uses a <code>threading.Lock</code> to protect the loaded-once state.
        </p>
        <CodeBlock language="python" code={`from aquilia.dotenv import DotEnvLoader

# ── Configure BEFORE first access (must be called before ensure_loaded) ───────
DotEnvLoader.configure(
    search_paths=[".env", ".env.local", ".env.{env}", ".env.{env}.local"],
    auto_load=True,      # trigger on first Env.resolve() call
    override=False,      # never overwrite existing process env vars
    interpolate=True,    # expand \${VAR} references in values
)

# ── Trigger loading explicitly (idempotent — no-op if already loaded) ─────────
loaded = DotEnvLoader.ensure_loaded()              # → dict[str, str]
loaded = DotEnvLoader.ensure_loaded(path=".env.custom")
loaded = DotEnvLoader.ensure_loaded(search_paths=[".env.test"])

# ── Inspect loader state ──────────────────────────────────────────────────────
DotEnvLoader.is_loaded()          # → bool: True after first load
DotEnvLoader.loaded_files()       # → list[Path]: every file that was read
DotEnvLoader.loaded_values()      # → dict[str, str]: all values loaded

# ── Reset (for testing only) ─────────────────────────────────────────────────
# WARNING: does NOT remove values from os.environ. Only resets loaded-once state.
DotEnvLoader.reset()              # next call to ensure_loaded() will re-parse`} />

        <div className={`mt-4 rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Class method</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Returns</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['configure(**kwargs)', 'None', 'Set search_paths, override, interpolate, auto_load. No-op if already loaded.'],
                ['ensure_loaded(path, search_paths)', 'dict[str, str]', 'Load all matching files exactly once. Returns all loaded key-value pairs.'],
                ['is_loaded()', 'bool', 'True if any .env file has been loaded. Thread-safe read.'],
                ['loaded_files()', 'list[Path]', 'Returns copies of all Path objects for files that were parsed.'],
                ['loaded_values()', 'dict[str, str]', 'Returns a copy of all values loaded into os.environ by this instance.'],
                ['reset()', 'None', 'Resets loaded-once state. Does NOT unset os.environ values. Use in tests only.'],
              ].map(([method, ret, desc], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{method}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt} whitespace-nowrap`}>{ret}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Module-level functions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Module-level functions
        </h2>
        <p className={`mb-4 ${txt}`}>
          These are convenience wrappers around <code>DotEnv</code> and <code>DotEnvLoader</code> for the most common use cases. Import them directly from <code>aquilia.dotenv</code>.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Function</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Returns</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['load_dotenv(path, override, interpolate, encoding)', 'bool', 'Load a .env file into os.environ. Returns True if any values were loaded. Main entry point.'],
                ['dotenv_values(path, interpolate, encoding)', 'dict[str, str]', 'Parse a .env file and return values WITHOUT loading into os.environ. No side effects.'],
                ['find_dotenv(filename, raise_error, usecwd)', 'Path | None', 'Search for a .env file using the workspace-root discovery logic.'],
                ['ensure_dotenv_loaded(path, auto_load)', 'None', 'Ensure dotenv is loaded — idempotent. Called automatically by AquilaConfig on first access.'],
                ['is_dotenv_loaded()', 'bool', 'True if ensure_dotenv_loaded or load_dotenv has been called and files were found.'],
                ['reset_dotenv_state()', 'None', 'Reset the DotEnvLoader singleton state. For testing only — does not clear os.environ.'],
              ].map(([fn, ret, desc], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">{fn}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt} whitespace-nowrap`}>{ret}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python" code={`from aquilia.dotenv import dotenv_values, ensure_dotenv_loaded, reset_dotenv_state

# Read .env.prod values for inspection (no mutation of os.environ)
prod_config = dotenv_values(".env.prod")
db_url = prod_config.get("DATABASE_URL")
print(f"Prod DB: {db_url}")

# Inspect which values are in .env vs which are live in the environment
all_dotenv = dotenv_values(".env")
live = {k: v for k, v in all_dotenv.items() if k in os.environ}
missing = {k: v for k, v in all_dotenv.items() if k not in os.environ}

# ensure_dotenv_loaded is what AquilaConfig calls internally on first Env access
# You typically never call this yourself
ensure_dotenv_loaded()        # auto_load controlled by AQUILIA_DOTENV_AUTO_LOAD env var`} />
      </section>

      {/* AquilaConfig.Dotenv — policy class */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          AquilaConfig.Dotenv — fine-grained policy
        </h2>
        <p className={`mb-4 ${txt}`}>
          For full control over which files are loaded and in what order, define a nested <code>Dotenv</code> class inside your <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclass. This is the declarative approach and the one that works best with IDE autocompletion.
        </p>
        <CodeBlock language="python" code={`from aquilia.pyconfig import AquilaConfig

class BaseEnv(AquilaConfig):
    class Dotenv(AquilaConfig.Dotenv):
        # Ordered list of files to search — later files override earlier ones.
        # AquilaConfig.EnvFile marks a file as optional (required=False by default).
        files = [
            ".env",                                              # shared defaults
            ".env.defaults",                                     # additional defaults
            AquilaConfig.EnvFile(".env.{env}"),                  # env-specific (dev/prod)
            AquilaConfig.EnvFile(".env.local", required=False),  # local overrides (optional)
            AquilaConfig.EnvFile(".env.{env}.local", required=False),
        ]

        auto_load   = True    # fire automatically on first Env/Secret access (default True)
        override    = False   # do NOT overwrite existing process env vars (default False)
        interpolate = True    # expand \${VAR} references within the file (default True)

        # strict=True: raise if any REQUIRED file in files[] is missing
        # (files marked required=False are always silently skipped)
        strict      = False

# Without a Dotenv class, Aquilia uses this default search sequence
# (auto-derived from AQ_ENV / AQUILIA_ENV):
#   .env
#   .env.local
#   .env.{env}          (e.g. .env.prod)
#   .env.{env}.local    (e.g. .env.prod.local)
#   config/.env
#   config/.env.{env}`} />
      </section>

      {/* Interpolation deep dive */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Variable interpolation
        </h2>
        <p className={`mb-4 ${txt}`}>
          Interpolation expands <code>{'${VAR}'}</code> and <code>$VAR</code> references inside values. The resolution order within a single file is: already-resolved keys from earlier lines → later keys in the same file → <code>os.environ</code>. This means forward references don't resolve — order matters.
        </p>
        <CodeBlock language="bash" code={`# ── Basic interpolation ───────────────────────────────────────────────────
BASE_URL=https://api.example.com
API_V1=\${BASE_URL}/v1             # → "https://api.example.com/v1"
API_V2=\${BASE_URL}/v2             # → "https://api.example.com/v2"

# ── Fallback from os.environ ─────────────────────────────────────────────
# If REGION is not defined in the .env file but IS in os.environ, it resolves:
BUCKET_URL=s3://\${REGION}/my-bucket

# ── Chains work if order is correct ───────────────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DATABASE_URL=postgresql://\${DB_HOST}:\${DB_PORT}/\${DB_NAME}

# ── Escape a literal dollar sign ──────────────────────────────────────────
PRICE="\$50"                       # → "$50" (backslash-dollar in double quotes)
LITERAL=\$100                       # → literal "$100" in unquoted values`} />
      </section>

      {/* Security */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Security guarantees
        </h2>
        <div className={`space-y-3 text-sm leading-relaxed ${txt}`}>
          {[
            ['No shell execution', 'Values are parsed as plain strings. No eval(), exec(), subshell expansion ($(...)), backticks, or glob patterns are ever processed.'],
            ['No pickle or eval', 'The parser is a pure Python state machine — purely string operations with no dynamic code execution of any kind.'],
            ['UTF-8 BOM stripping', 'BOM (\\ufeff) is automatically removed from the start of files to prevent invisible character corruption.'],
            ['Variable name validation', 'Variable names must match ^[a-zA-Z_][a-zA-Z0-9_]*$. Invalid names are logged as warnings and silently skipped.'],
            ['Process env always wins', 'override=False (the default) means variables already in os.environ can never be overwritten by .env files. CI/CD-injected secrets are always safe.'],
            ['Thread-safe loading', 'DotEnvLoader uses threading.Lock to guarantee the .env files are parsed and applied exactly once even under concurrent startup (multiple uvicorn workers).'],
          ].map(([title, body]) => (
            <div key={title as string} className="flex items-start gap-2">
              <Lock className="w-3.5 h-3.5 mt-0.5 shrink-0 text-aquilia-400" />
              <span><strong className={head}>{title}</strong> — {body}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Recommended .gitignore */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Recommended .gitignore entries</h2>
        <CodeBlock language="gitignore" code={`# ── .env files ───────────────────────────────────────────────────────────
# Local overrides — never commit these
.env.local
.env.*.local

# Per-environment secrets
.env.prod
.env.staging

# Keep in VCS (non-secret defaults only):
# .env                   ← shared defaults, no secrets
# .env.dev               ← dev defaults, no secrets
# .env.example           ← onboarding template`} />
      </section>

      {/* Real-world project layout */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Typical project layout</h2>
        <CodeBlock language="text" code={`myproject/
├── workspace.py                # Aquilia workspace — dotenv auto-searches from here
├── .env                        # ✅ committed — non-secret shared defaults
│     DATABASE_URL=sqlite:///dev.db
│     CACHE_BACKEND=memory
│     LOG_LEVEL=info
│
├── .env.dev                    # ✅ committed — dev-specific, no secrets
│     AQ_DEBUG=true
│     SERVER_RELOAD=true
│
├── .env.prod                   # ⚠️  consider excluding from VCS if any secrets present
│     LOG_LEVEL=warning
│     SERVER_WORKERS=4
│
├── .env.local                  # ❌ gitignored — machine-specific overrides
│     DATABASE_URL=postgresql://localhost/mydb_dev
│     AQ_SECRET_KEY=local-dev-key-not-for-prod
│
└── .env.example                # ✅ committed — template for new developers
      DATABASE_URL=postgresql://localhost/mydb
      AQ_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
      REDIS_URL=redis://localhost:6379/0`} />
      </section>

      {/* Testing */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <RefreshCcw className="w-5 h-5 text-aquilia-400" />
          Testing with .env files
        </h2>
        <p className={`mb-4 ${txt}`}>
          Reset loader state between tests using the <code>autouse</code> fixture pattern. Because <code>DotEnvLoader.reset()</code> does <strong>not</strong> remove values from <code>os.environ</code>, you also need <code>monkeypatch</code> to fully isolate environment variable state.
        </p>
        <CodeBlock language="python" code={`import os, pytest
from aquilia.dotenv import (
    reset_dotenv_state, load_dotenv,
    DotEnvLoader, DotEnv, dotenv_values,
)
from aquilia.pyconfig import AquilaConfig

# ── autouse fixture: reset all config + dotenv state ─────────────────────────
@pytest.fixture(autouse=True)
def reset_env():
    """Isolate .env and AquilaConfig state between tests."""
    yield
    reset_dotenv_state()            # reset DotEnvLoader singleton
    AquilaConfig.clear_all_caches() # clear Env/Secret descriptor caches

# ── tmp_path fixture: write a fresh .env for each test ───────────────────────
@pytest.fixture
def test_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)     # workspace root is now tmp_path
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=sqlite:///test.db\n"
        "AQ_DEBUG=true\n"
        "PORT=9000\n"
    )
    yield env_file

def test_load_reads_file(test_env, monkeypatch):
    loaded = load_dotenv(str(test_env), override=True)
    assert loaded is True
    assert os.environ["DATABASE_URL"] == "sqlite:///test.db"
    assert os.environ["PORT"] == "9000"

def test_parse_no_side_effects(test_env):
    # parse() should never touch os.environ
    before = dict(os.environ)
    values = DotEnv.parse(str(test_env))
    assert dict(os.environ) == before       # environment unchanged
    assert values["AQ_DEBUG"] == "true"

def test_dotenv_values(test_env):
    # dotenv_values is a named shorthand for DotEnv.parse() with find_dotenv search
    values = dotenv_values(str(test_env))
    assert values["DATABASE_URL"] == "sqlite:///test.db"

def test_idempotent_loading(test_env, monkeypatch):
    load_dotenv(str(test_env), override=True)
    load_dotenv(str(test_env), override=True)  # second call is a no-op (singleton)
    assert DotEnvLoader.is_loaded()

def test_interpolation():
    content = "BASE=http://example.com\nURL=\${BASE}/api"
    values = DotEnv.parse_string(content, interpolate=True)
    assert values["URL"] == "http://example.com/api"

def test_override_false(monkeypatch, test_env):
    monkeypatch.setenv("DATABASE_URL", "postgres://already-set")
    load_dotenv(str(test_env), override=False)  # default
    # os.environ value takes precedence — .env cannot overwrite it
    assert os.environ["DATABASE_URL"] == "postgres://already-set"`} />
      </section>

      {/* Related */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config/pyconfig', 'AquilaConfig & Env', 'Env descriptors that trigger auto-loading, Secret redaction, AquilaConfig.Dotenv policy'],
            ['/docs/config', 'Config Overview', 'Value resolution precedence: process env → .env → config defaults'],
            ['/docs/config/workspace', 'Workspace Builder', 'Wiring AquilaConfig and integrations into the application'],
            ['/docs/config/integrations', 'Integrations', 'Typed integration dataclasses — DatabaseIntegration, AuthIntegration, etc.'],
          ].map(([href, label, desc]) => (
            <Link key={href as string} to={href as string} className="flex flex-col gap-0.5 group">
              <span className={`text-sm font-semibold flex items-center gap-1 ${isDark ? 'text-aquilia-400 group-hover:text-aquilia-300' : 'text-aquilia-600 group-hover:text-aquilia-500'} transition-colors`}>
                → {label}
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
