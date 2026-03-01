import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Fingerprint, Lock, Database, Globe, Layers, Zap, Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Security / Sessions
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session System
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's session system provides server-side state management with cryptographically secure identifiers, pluggable stores, configurable transport layers, rich policy controls, and DI-integrated decorators — all built around a 7-phase lifecycle engine.
        </p>
      </div>

      {/* Architecture Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture Overview</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The session system is composed of several layers, each responsible for a distinct concern:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: <Zap className="w-5 h-5" />, name: 'SessionEngine', desc: 'Central orchestrator running the 7-phase lifecycle: Detection → Resolution → Validation → Binding → Mutation → Commit → Emission' },
            { icon: <Fingerprint className="w-5 h-5" />, name: 'SessionID', desc: '32-byte cryptographically secure identifier with sess_ prefix and URL-safe base64 encoding' },
            { icon: <Layers className="w-5 h-5" />, name: 'Session', desc: 'Dict-like state container with dirty tracking, principal binding, scope flags, and version control' },
            { icon: <Settings className="w-5 h-5" />, name: 'SessionPolicy', desc: 'Security configuration with TTL, idle timeout, rotation rules, persistence, concurrency, and transport sub-policies' },
            { icon: <Database className="w-5 h-5" />, name: 'SessionStore', desc: 'Protocol-based pluggable backends — MemoryStore (LRU), FileStore (JSON), extensible to Redis/DB' },
            { icon: <Globe className="w-5 h-5" />, name: 'SessionTransport', desc: 'Cookie or Header-based transport layer for extracting and injecting session identifiers' },
            { icon: <Lock className="w-5 h-5" />, name: 'SessionGuard', desc: 'Guard-based access control — AdminGuard, VerifiedEmailGuard, custom guards via @requires' },
            { icon: <Shield className="w-5 h-5" />, name: 'SessionDecorators', desc: 'DI-integrated decorators: session.require(), session.ensure(), session.optional(), @authenticated, @stateful' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-aquilia-500">{item.icon}</span>
                <code className="text-aquilia-500 font-mono text-sm font-bold">{item.name}</code>
              </div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Core Concepts */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Concepts</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionID</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Every session is identified by a <code className="text-aquilia-500">SessionID</code> — a 32-byte token generated from <code className="text-aquilia-500">os.urandom()</code>, encoded as URL-safe base64 with a <code className="text-aquilia-500">sess_</code> prefix:
        </p>
        <CodeBlock language="python" filename="session_id.py">{`from aquilia.sessions import SessionID

# Generate a new cryptographic session ID
sid = SessionID.generate()
print(sid)            # sess_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6...
print(sid.value)      # Raw string value
print(len(sid))       # 49 characters (5 prefix + 44 base64)

# Validate an existing session ID
sid2 = SessionID("sess_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6...")
sid2.validate()       # Raises if invalid

# SessionID is hashable and comparable
sessions = {sid: {"user": "alice"}}
assert sid == SessionID(sid.value)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session Object</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">Session</code> is a dataclass providing dict-like access to session data:
        </p>
        <CodeBlock language="python" filename="session_object.py">{`from aquilia.sessions import Session, SessionID, SessionScope, SessionFlag

# Session stores user-specific state
session = Session(
    id=SessionID.generate(),
    data={"cart": [], "theme": "dark"},
    scope=SessionScope.USER,
    flags={SessionFlag.AUTHENTICATED, SessionFlag.ROTATABLE},
)

# Dict-like access
session["cart"].append({"product": "Widget", "qty": 2})
session["locale"] = "en-US"
print(session.get("theme", "light"))  # "dark"

# Lifecycle
session.touch()                     # Update last_accessed_at
session.extend_expiry(minutes=30)   # Push expiry forward
print(session.is_expired)           # False
print(session.idle_duration)        # timedelta since last access

# Authentication markers
session.mark_authenticated(principal_kind="user", principal_id="42")
print(session.principal)            # SessionPrincipal(kind="user", id="42")
session.clear_authentication()

# Dirty tracking
print(session._dirty)               # True — data was modified

# Serialization
data = session.to_dict()            # Full JSON-serializable dict
restored = Session.from_dict(data)  # Reconstruct from dict`}</CodeBlock>
      </section>

      {/* Scopes and Flags */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scopes & Flags</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionScope</h3>
        <div className={`overflow-x-auto mb-6 ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Scope</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['REQUEST', 'Single request lifetime — discarded after response'],
                ['CONNECTION', 'WebSocket connection lifetime'],
                ['USER', 'Tied to a specific user across requests'],
                ['DEVICE', 'Tied to a specific device (fingerprint-based)'],
              ].map(([scope, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500">{scope}</code></td>
                  <td className="py-2">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionFlag</h3>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Flag</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['AUTHENTICATED', 'Session belongs to an authenticated user'],
                ['EPHEMERAL', 'Not persisted to store — in-memory only'],
                ['ROTATABLE', 'Session ID can be rotated on privilege change'],
                ['RENEWABLE', 'Session TTL can be extended'],
                ['READ_ONLY', 'Data cannot be modified'],
                ['LOCKED', 'Session is locked for concurrent access control'],
              ].map(([flag, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500">{flag}</code></td>
                  <td className="py-2">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Set up sessions in your Aquilia workspace:
        </p>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia import Workspace
from aquilia.sessions import (
    SessionEngine, SessionPolicy, SessionPolicyBuilder,
    MemoryStore, CookieTransport
)

# 1. Build a policy
policy = (
    SessionPolicyBuilder("web")
    .lasting(hours=2)
    .idle_timeout(minutes=30)
    .rotating_on_auth()
    .web_defaults()
    .build()
)

# 2. Create store + transport
store = MemoryStore.web_optimized(max_sessions=10_000)
transport = CookieTransport.for_web_browsers(domain="example.com")

# 3. Wire into the engine
engine = SessionEngine(
    policies={"web": policy},
    stores={"memory": store},
    transports={"cookie": transport},
    default_policy="web",
)

# 4. Register in workspace (session middleware auto-activates)
workspace = Workspace(
    session_engine=engine,
)`}</CodeBlock>

        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session


class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @session.require()
    async def view_cart(self, ctx, session: Session):
        return ctx.json({"items": session.get("cart", [])})

    @Post("/add")
    @session.ensure()
    async def add_to_cart(self, ctx, session: Session):
        body = await ctx.json_body()
        cart = session.get("cart", [])
        cart.append(body)
        session["cart"] = cart
        return ctx.json({"items": cart}, status=201)`}</CodeBlock>
      </section>

      {/* 7-Phase Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7-Phase Lifecycle</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The SessionEngine processes every request through a deterministic 7-phase pipeline:
        </p>
        <div className="space-y-2">
          {[
            { phase: '1', name: 'Detection', desc: 'Transport extracts session ID from cookie/header' },
            { phase: '2', name: 'Resolution', desc: 'Store loads session data by ID, or creates a new session' },
            { phase: '3', name: 'Validation', desc: 'Check expiry, idle timeout, principal consistency' },
            { phase: '4', name: 'Binding', desc: 'Attach session to request context for handler access' },
            { phase: '5', name: 'Mutation', desc: 'Handler modifies session data (dirty tracking records changes)' },
            { phase: '6', name: 'Commit', desc: 'If dirty, persist changes to store. Optionally rotate session ID' },
            { phase: '7', name: 'Emission', desc: 'Transport injects updated session ID into response cookie/header' },
          ].map((item, i) => (
            <div key={i} className={`flex items-center gap-4 ${boxClass}`}>
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-aquilia-500/20 flex items-center justify-center">
                <span className="text-aquilia-500 font-bold text-sm">{item.phase}</span>
              </div>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</span>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Deep-dive links */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Deep Dive</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: 'Engine', desc: 'Full 7-phase lifecycle, event system, observability', path: '/docs/sessions/engine' },
            { title: 'Policies', desc: 'TTL, idle timeout, rotation, concurrency, transport config', path: '/docs/sessions/policies' },
            { title: 'Stores', desc: 'MemoryStore, FileStore, custom backends', path: '/docs/sessions/stores' },
            { title: 'Transport', desc: 'CookieTransport, HeaderTransport, factory methods', path: '/docs/sessions/transport' },
            { title: 'Decorators', desc: 'session.require/ensure/optional, @authenticated, @stateful', path: '/docs/sessions/decorators' },
            { title: 'State', desc: 'Typed state with Field descriptors, CartState, UserPreferencesState', path: '/docs/sessions/state' },
            { title: 'Guards', desc: 'SessionGuard, @requires, AdminGuard, VerifiedEmailGuard', path: '/docs/sessions/guards' },
            { title: 'Faults', desc: 'Complete fault hierarchy — 14 security-domain faults', path: '/docs/sessions/faults' },
          ].map((item, i) => (
            <a key={i} href={item.path} className={`${boxClass} block hover:border-aquilia-500/30 transition-colors`}>
              <h3 className={`font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </a>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
