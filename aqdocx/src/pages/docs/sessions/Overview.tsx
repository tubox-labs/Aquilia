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
          Aquilia's session subsystem provides server-side state management with cryptographically secure identifiers, pluggable stores, configurable transports, policies, and DI decorators.
        </p>
      </div>

      {/* Architecture Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: <Zap className="w-5 h-5" />, name: 'SessionEngine', desc: 'Central orchestrator running the 7-phase lifecycle: Detection → Resolution → Validation → Binding → Mutation → Commit → Emission' },
            { icon: <Fingerprint className="w-5 h-5" />, name: 'SessionID', desc: 'Cryptographically secure 256-bit identifier with sess_ prefix and URL-safe base64 encoding' },
            { icon: <Layers className="w-5 h-5" />, name: 'Session', desc: 'Dict-like state container with dirty tracking, principal binding, scope flags, and version control' },
            { icon: <Settings className="w-5 h-5" />, name: 'SessionPolicy', desc: 'Security configuration with TTL, idle timeout, rotation rules, persistence, concurrency, and transport sub-policies' },
            { icon: <Database className="w-5 h-5" />, name: 'SessionStore', desc: 'Protocol-based pluggable backends — MemoryStore (LRU), FileStore (JSON), extensible to Redis/DB' },
            { icon: <Globe className="w-5 h-5" />, name: 'SessionTransport', desc: 'Cookie or Header-based transport layer for extracting and injecting session identifiers' },
            { icon: <Lock className="w-5 h-5" />, name: 'SessionGuard', desc: 'Guard-based access control via @requires' },
            { icon: <Shield className="w-5 h-5" />, name: 'SessionDecorators', desc: 'DI-integrated decorators: session.require(), session.ensure(), session.optional(), @stateful' },
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
          Every session is identified by a <code className="text-aquilia-500">SessionID</code> — a 256-bit token generated from secure random bytes, starting with a <code className="text-aquilia-500">sess_</code> prefix:
        </p>
        <CodeBlock language="python" filename="session_id.py">{`from aquilia.sessions import SessionID

# Generate a new cryptographic session ID
sid = SessionID()
print(str(sid))        # sess_A1b2C3d4E5f6G7h8...
print(len(str(sid)))  # 49 characters (5 prefix + 44 base64)

# Reconstruct from string
sid2 = SessionID.from_string("sess_A1b2C3d4E5f6...")`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session Object</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">Session</code> is a dataclass providing dict-like access with nested mutation dirty-tracking:
        </p>
        <CodeBlock language="python" filename="session_object.py">{`from datetime import timedelta
from aquilia.sessions import Session, SessionID, SessionScope, SessionFlag, SessionPrincipal

# Session stores user-specific state
session = Session(
    id=SessionID(),
    data={"cart": [], "theme": "dark"},
    scope=SessionScope.USER,
    flags={SessionFlag.AUTHENTICATED, SessionFlag.RENEWABLE},
)

# Dict-like access
session["cart"].append({"product": "Widget", "qty": 2}) # Sets dirty flag automatically
session["locale"] = "en-US"

# Lifecycle methods
session.touch()
session.extend_expiry(ttl=timedelta(minutes=30))
print(session.is_expired())
print(session.idle_duration())

# Authentication principal binding
principal = SessionPrincipal(kind="user", id="42", roles=["admin"])
session.mark_authenticated(principal)

# Dirty tracking property
print(session.is_dirty) # True`}</CodeBlock>
      </section>

      {/* Scopes and Flags */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scopes &amp; Flags</h2>

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
                ['SINGLETON', 'Application singleton lifetime.'],
                ['APP', 'App instance scope.'],
                ['REQUEST', 'Single HTTP request scope.'],
                ['TRANSIENT', 'Short-lived ephemeral scope.'],
                ['POOLED', 'Pooled object scope.'],
                ['EPHEMERAL', 'Lightweight memory-only scope.'],
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
                ['AUTHENTICATED', 'Session belongs to an authenticated user.'],
                ['EPHEMERAL', 'Memory-only session that is not persisted to the store.'],
                ['RENEWABLE', 'Session TTL can be extended on touching.'],
                ['ROTATABLE', 'Session ID can be rotated.'],
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
          Initialize session management in your application startup:
        </p>
        <CodeBlock language="python" filename="app_setup.py">{`from datetime import timedelta
from aquilia.sessions import (
    SessionEngine, SessionPolicyBuilder,
    MemoryStore, CookieTransport
)

# 1. Build a policy
policy = (
    SessionPolicyBuilder()
    .named("web")
    .lasting(timedelta(hours=2))
    .idle_timeout(timedelta(minutes=30))
    .build()
)

# 2. Create store + transport
store = MemoryStore.web_optimized()
transport = CookieTransport.for_web_browsers()

# 3. Create the engine (SessionEngine is scoped to a single policy, store, and transport)
engine = SessionEngine(
    policy=policy,
    store=store,
    transport=transport,
)`}</CodeBlock>

        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session

class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @session.require()
    async def view_cart(self, ctx, session: Session):
        return {"items": session.get("cart", [])}

    @Post("/add")
    @session.ensure()
    async def add_to_cart(self, ctx, session: Session):
        body = await ctx.request.json()
        cart = session.get("cart", [])
        cart.append(body)
        session["cart"] = cart # Triggers dirty tracking
        return {"items": cart}`}</CodeBlock>
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
            { phase: '6', name: 'Commit', desc: 'If dirty, persist changes to store. Concurrency limits are checked BEFORE saving.' },
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

      {/* Next Steps */}
      <NextSteps />
    </div>
  )
}
