import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { FileText, Shield, CheckCircle } from 'lucide-react'

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
          Aquilia ships its own <DocTerm id="config.dotenv">DotEnv</DocTerm> loader — no <code>python-dotenv</code> required. It loads <code>.env</code> files automatically before any <DocTerm id="config.env">Env</DocTerm> or <DocTerm id="config.secret">Secret</DocTerm> binding is first resolved, supports variable interpolation, multiline values, and strict required-file validation. Values already present in the process environment are never overwritten by default.
        </p>
      </div>

      {/* How it loads — visual flow */}
      <div className="w-full h-28 flex items-center justify-center my-6">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 100" fill="none">
          <defs>
            <linearGradient id="dotenvGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#3b82f6" />
            </linearGradient>
          </defs>
          <path d="M 30 50 L 570 50" stroke="rgba(255,255,255,0.06)" strokeWidth="3" strokeLinecap="round" />
          <path d="M 30 50 L 400 50" stroke="url(#dotenvGrad)" strokeWidth="3" strokeLinecap="round" />

          {[
            { cx: 70,  label: '.env',        sub: 'base',    color: '#10b981' },
            { cx: 190, label: '.env.local',  sub: 'local',   color: '#10b981' },
            { cx: 310, label: '.env.{env}',  sub: 'env-specific', color: '#f59e0b' },
            { cx: 430, label: '.env.{env}.local', sub: 'highest priority', color: '#3b82f6' },
            { cx: 540, label: 'os.environ',  sub: 'process', color: '#8b5cf6' },
          ].map(({ cx, label, sub, color }, i) => (
            <g key={i}>
              <circle cx={cx} cy={50} r={12} fill="#18181b" stroke={color} strokeWidth="2" />
              <text x={cx} y={25} textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="8" fontFamily="sans-serif">{label}</text>
              <text x={cx} y={78} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">{sub}</text>
            </g>
          ))}

          <text x="300" y="94" textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize="8" fontFamily="sans-serif">← lower priority    higher priority →</text>
        </svg>
      </div>

      {/* Quick start */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Quick start
        </h2>
        <p className={`mb-4 ${txt}`}>
          In most apps you never call <code>load_dotenv()</code> at all — it fires automatically the first time any <DocTerm id="config.env">Env</DocTerm> or <DocTerm id="config.secret">Secret</DocTerm> is resolved. If you need explicit control:
        </p>
        <CodeBlock language="python" code={`from aquilia.dotenv import load_dotenv, DotEnv

# Auto-load .env from workspace root (idempotent — safe to call multiple times)
load_dotenv()

# Load a specific file
load_dotenv(".env.production")

# Override existing process env vars (rare — useful in testing)
load_dotenv(override=True)

# Parse without loading into os.environ
values: dict[str, str] = DotEnv.parse(".env")
print(values["DATABASE_URL"])

# Check if already loaded
from aquilia.dotenv import is_dotenv_loaded
if not is_dotenv_loaded():
    load_dotenv()`} />
      </section>

      {/* Syntax reference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <FileText className="w-5 h-5 text-aquilia-400" />
          .env syntax reference
        </h2>
        <p className={`mb-4 ${txt}`}>
          Aquilia's parser is a strict subset of the de-facto <code>.env</code> standard — no shell expansion, no subshells, no <code>eval()</code>.
        </p>
        <CodeBlock language="bash" code={`# Comments start with #
SIMPLE=value
QUOTED="value with spaces"
SINGLE='single quoted'
EXPORT=exported value
export ALSO_WORKS=true          # export keyword is accepted and stripped

# Boolean values (resolved by cast=bool in Env)
AQ_DEBUG=true                   # → True
AQ_DEBUG=false                  # → False
AQ_DEBUG=yes / no / on / off    # all understood

# Numbers (auto-cast when no cast= specified)
PORT=8000                       # → int 8000
RATIO=0.95                      # → float 0.95

# Variable interpolation
BASE_URL=http://localhost:8000
API_URL=\${BASE_URL}/api         # → "http://localhost:8000/api"
ALT=\$BASE_URL/v2                 # → same ($ without braces also works)

# Multiline values (use double quotes)
PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"`} />
      </section>

      {/* Precedence */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>File precedence and environment cascade</h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          By default, Aquilia searches for files in this order. Later files override earlier ones. Values already in <code>os.environ</code> (from your shell, Docker, or Kubernetes) are <strong>never overwritten</strong> unless <code>override=True</code>.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>File</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Priority</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Committed?</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Purpose</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['.env',                   'Lowest',     'Yes — no secrets', 'Shared defaults checked into version control'],
                ['.env.defaults',          'Low',        'Yes',              'Additional fallback defaults'],
                ['.env.example',           'Reference',  'Yes',              'Documentation template — never loaded'],
                ['.env.{env}',             'Medium',     'Usually yes',      'Per-environment overrides (dev/staging/prod)'],
                ['.env.local',             'High',       '❌ gitignore it',  'Developer-local overrides, never shared'],
                ['.env.{env}.local',       'Highest',    '❌ gitignore it',  'Local per-environment overrides'],
                ['os.environ (process)',   'Always wins','—',                'CI/CD secrets, Docker env, Kubernetes secrets'],
              ].map(([file, priority, committed, purpose], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">{file}</td>
                  <td className={`px-4 py-3 text-xs font-semibold ${subtxt}`}>{priority}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{committed}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DotEnvLoader class */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>DotEnvLoader — low-level API</h2>
        <p className={`mb-4 leading-relaxed ${txt}`}>
          For advanced use cases — custom search paths, CI bootstrap scripts, or test harnesses — use the <code>DotEnvLoader</code> singleton directly.
        </p>
        <CodeBlock language="python" code={`from aquilia.dotenv import DotEnvLoader

# Configure the global loader (call once, at startup)
DotEnvLoader.configure(
    search_paths=[".env", ".env.local", ".env.\${env}"],
    auto_load=True,
    override=False,
    interpolate=True,
)

# Manually trigger loading for a specific file list
DotEnvLoader.ensure_loaded(search_paths=[".env.test", ".env.local"])

# Reset state (useful in tests to allow re-loading)
DotEnvLoader.reset()

# Low-level: find the workspace root (walks up from cwd looking for workspace.py)
from aquilia.dotenv import find_dotenv
path = find_dotenv()    # → "/path/to/project/.env" or None`} />
      </section>

      {/* Security */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Security guarantees
        </h2>
        <ul className={`space-y-3 text-sm leading-relaxed ${txt}`}>
          {[
            ['No shell execution', 'Values are parsed as plain strings. No eval(), exec(), subshell expansion, or backtick substitution.'],
            ['No pickle or eval', 'Pure string parsing — the parser is a deterministic state machine.'],
            ['BOM handling', 'UTF-8 BOM is stripped automatically from the start of files.'],
            ['Variable name validation', 'Only alphanumeric characters and underscores are accepted as variable names.'],
            ['Existing vars respected', 'override=False (the default) means process environment always wins — CI/CD injected secrets are safe.'],
          ].map(([title, body]) => (
            <li key={title as string} className="flex items-start gap-2">
              <span className="text-aquilia-400 mt-0.5">•</span>
              <div><strong>{title}</strong> — {body}</div>
            </li>
          ))}
        </ul>
      </section>

      {/* Testing */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Testing with .env files</h2>
        <p className={`mb-4 ${txt}`}>Reset the loader state between tests to allow clean re-loading with different fixtures:</p>
        <CodeBlock language="python" code={`import pytest
from aquilia.dotenv import reset_dotenv_state, load_dotenv
from aquilia.pyconfig import reset_dotenv_state as reset_pyconfig_state

@pytest.fixture(autouse=True)
def reset_env(tmp_path):
    """Isolate .env state between tests."""
    reset_dotenv_state()
    reset_pyconfig_state()
    # Write a fresh .env for the test
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///test.db\\nAQ_DEBUG=true\\n")
    load_dotenv(str(env_file), override=True)
    yield
    reset_dotenv_state()`} />
      </section>

      {/* Related */}
      <section className="mb-12 border-t border-white/5 pt-8">
        <div className="flex flex-col gap-2">
          <Link to="/docs/config/pyconfig" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → AquilaConfig: Python-native config class
          </Link>
          <Link to="/docs/config/workspace" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Workspace: wiring config into the app
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
