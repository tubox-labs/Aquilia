import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Zap, Layers, Settings, Fingerprint, Database, Globe, Lock } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

function SessionArchitecture() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="w-full flex justify-center py-6 bg-transparent">
      <svg viewBox="0 0 900 340" className="w-full h-auto drop-shadow-2xl font-mono select-none">
        <defs>
          <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
          </linearGradient>
          <radialGradient id="glowGreen" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
          </radialGradient>
          <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Glowing Halos Behind Nodes */}
        <circle cx="80" cy="170" r="50" fill="url(#glowGreen)" />
        <circle cx="240" cy="110" r="50" fill="url(#glowGreen)" />
        <circle cx="400" cy="90" r="50" fill="url(#glowBlue)" />
        <circle cx="560" cy="230" r="50" fill="url(#glowBlue)" />
        <circle cx="720" cy="190" r="50" fill="url(#glowPurple)" />
        <circle cx="840" cy="170" r="50" fill="url(#glowGreen)" />

        {/* Connecting Wave Lines (Bundle of Light Fibers) */}
        <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="url(#waveGrad)" strokeWidth="4.5" strokeLinecap="round" />
        <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 8" strokeLinecap="round" />

        {/* Node 1: Detection */}
        <g transform="translate(80, 170)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">DETECTION</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Cookie/Header extraction</text>
        </g>

        {/* Node 2: Resolution */}
        <g transform="translate(240, 110)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">RESOLUTION</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Store lookup by ID</text>
        </g>

        {/* Node 3: Verification */}
        <g transform="translate(400, 90)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#3b82f6" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">VERIFICATION</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">TTL &amp; Fingerprint checks</text>
        </g>

        {/* Node 4: DI Binding */}
        <g transform="translate(560, 230)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#3b82f6" />
          <text x="0" y="-24" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">DI BINDING</text>
          <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="#71717a">Register request-scope</text>
        </g>

        {/* Node 5: Mutation */}
        <g transform="translate(720, 190)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#a855f7" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#a855f7" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">MUTATION</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Route logic &amp; Dirty flag</text>
        </g>

        {/* Node 6: Commit */}
        <g transform="translate(840, 170)">
          <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
          <circle cx="0" cy="0" r="4" fill="#22c55e" />
          <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">COMMIT</text>
          <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">ID rotate &amp; Save store</text>
        </g>
      </svg>
    </div>
  )
}

export function SessionsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionHeaderClass = `text-2xl font-mono font-bold tracking-tight mb-6 flex items-center gap-3 ${
    isDark ? 'text-white' : 'text-gray-900'
  }`
  const textClass = `text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-aquilia-500 mb-4">
          <Shield className="w-4 h-4" />
          Security / Sessions / Overview
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session System
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Aquilia provides an explicit, policy-driven session subsystem featuring cryptographically secure identifiers,
          pluggable storage backends, transport-agnostic delivery, and deep integration with the Dependency Injection (DI) system.
        </p>
      </div>

      {/* Architecture Design Component */}
      <SessionArchitecture />

      {/* Architecture Components - Clean List */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Zap className="w-5 h-5 text-aquilia-500" />
          Architecture Components
        </h2>
        <p className={textClass}>
          The session subsystem consists of multiple decoupled interfaces working together to manage server-side user state:
        </p>
        <div className="space-y-6 mt-6">
          {[
            { id: 'sessions.engine', icon: <Zap className="w-4 h-4" />, name: 'SessionEngine', desc: 'The central orchestrator running the 7-phase lifecycle: Detection → Resolution → Validation → Binding → Mutation → Commit → Emission.' },
            { id: 'sessions.session_id', icon: <Fingerprint className="w-4 h-4" />, name: 'SessionID', desc: 'An opaque, cryptographically secure 256-bit identifier generated using secrets.token_bytes with a sess_ prefix.' },
            { id: 'sessions.session', icon: <Layers className="w-4 h-4" />, name: 'Session', desc: 'The state container. Features nested dictionary tracking that marks the session dirty automatically on mutations.' },
            { id: 'sessions.policy', icon: <Settings className="w-4 h-4" />, name: 'SessionPolicy', desc: 'Frozen configuration defining expiration windows, rotation triggers, concurrency checks, and transport rules.' },
            { id: 'sessions.store', icon: <Database className="w-4 h-4" />, name: 'SessionStore', desc: 'Pluggable backend storage protocol (implemented by MemoryStore and FileStore out-of-the-box).' },
            { id: 'sessions.transport', icon: <Globe className="w-4 h-4" />, name: 'SessionTransport', desc: 'HTTP adapter interface resolving IDs from Cookie headers or injecting them back into outgoing responses.' },
            { id: 'sessions.guard', icon: <Lock className="w-4 h-4" />, name: 'SessionGuard', desc: 'Access control guard returning True to authorize requests, or raising structured Security Faults.' },
            { id: 'sessions.decorator_require', icon: <Shield className="w-4 h-4" />, name: 'SessionDecorators', desc: 'DI-aware route decorators (session.require, session.ensure, session.optional, and @stateful).' },
          ].map((item, i) => (
            <div key={i} className="flex gap-4 items-start transition-transform duration-200 hover:translate-x-1">
              <div className="mt-1 flex-shrink-0 text-aquilia-500 p-2 rounded-lg bg-aquilia-500/5 dark:bg-aquilia-500/10">
                {item.icon}
              </div>
              <div>
                <h3 className={`font-mono text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>
                  <DocTerm id={item.id}>{item.name}</DocTerm>
                </h3>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Core Concepts */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Core Data Primitives
        </h2>

        <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="sessions.session_id">SessionID</DocTerm>
        </h3>
        <p className={textClass}>
          A <code className="text-aquilia-500">SessionID</code> does not encode any identity or timestamps (preventing info leaks).
          It has 256 bits of entropy and is encoded into a URL-safe Base64 string:
        </p>
        <CodeBlock language="python" filename="session_id.py" highlightLines={[4, 8]}>{`from aquilia.sessions import SessionID

# Generate a new cryptographic session ID
sid = SessionID()
print(str(sid))        # sess_A1b2C3d4E5f6G7h8...
print(len(str(sid)))  # 49 characters (5 prefix + 44 base64)

# Reconstruct from string (enforces length & structure guards)
sid2 = SessionID.from_string("sess_A1b2C3d4E5f6G7h8...")`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="sessions.session">Session Object</DocTerm>
        </h3>
        <p className={textClass}>
          The <code className="text-aquilia-500">Session</code> is a dataclass storing session data. It uses custom dictionary tracking
          to detect when nested properties change, automatically flagging the session as dirty for persistence.
        </p>
        <CodeBlock language="python" filename="session_object.py" highlightLines={[12, 22, 26]}>{`from datetime import timedelta
from aquilia.sessions import Session, SessionID, SessionScope, SessionFlag, SessionPrincipal

# Session stores user-specific state
session = Session(
    id=SessionID(),
    data={"cart": [], "theme": "dark"},
    scope=SessionScope.USER,
    flags={SessionFlag.AUTHENTICATED, SessionFlag.RENEWABLE},
)

# Dict-like access (triggers dirty tracking automatically)
session["theme"] = "light"
session["cart"].append({"product": "Gizmo", "qty": 1})

# Lifecycle checking
session.touch()
session.extend_expiry(ttl=timedelta(minutes=30))
print(session.is_expired())  # False

# Bind principal identity (for audits and concurrency)
principal = SessionPrincipal(kind="user", id="user_99", attributes={"roles": ["member"]})
session.mark_authenticated(principal)

print(session.is_dirty)  # True (marks dirty on principal change or data mutation)`}</CodeBlock>
      </section>

      {/* Scopes and Flags - Clean borderless tables */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Settings className="w-5 h-5 text-aquilia-500" />
          Lifetimes & Boundaries
        </h2>

        <h3 className={`text-lg font-bold font-mono mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="sessions.scope">SessionScope</DocTerm>
        </h3>
        <p className={textClass}>
          SessionScope defines the lifecycle and persistence rules. Ephemeral scopes reside in memory and do not write to persistent stores.
        </p>
        <div className="overflow-x-auto mb-8">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Scope</th>
                <th className="text-left py-3 pr-4">Requires Persistence</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['REQUEST', '❌ No', 'Short-lived request scope. Discarded immediately after HTTP response is returned.'],
                ['CONNECTION', '✅ Yes', 'Tied to active client network connections (such as persistent SSE or WebSocket links).'],
                ['USER', '✅ Yes', 'Tied to the authenticated user principal. Persists across multiple sessions and devices.'],
                ['DEVICE', '✅ Yes', 'Tied to a specific hardware or client browser device installation.'],
              ].map(([scope, persist, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-mono text-xs"><code className="text-aquilia-500">{scope}</code></td>
                  <td className="py-3 pr-4 text-xs font-medium">{persist}</td>
                  <td className="py-3 text-xs leading-relaxed">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-bold font-mono mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="sessions.flag">SessionFlag</DocTerm>
        </h3>
        <p className={textClass}>
          Flags provide fine-grained status indicators used by components to toggle locking, expiration rotation, and read-only status.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Flag</th>
                <th className="text-left py-3">Behavior & Purpose</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['AUTHENTICATED', 'Indicates session has successfully bound an active identity principal.'],
                ['EPHEMERAL', 'Indicates the session is not saved to persistent stores, even if the scope requires it.'],
                ['ROTATABLE', 'Allows the session ID to be regenerated during privilege alterations.'],
                ['RENEWABLE', 'Enables the sliding session expiration window (touch resets expiration TTL).'],
                ['READ_ONLY', 'Blocks all mutations to the session data dictionary, raising SessionLockedFault.'],
                ['LOCKED', 'Indicates the session is currently acquired in a transactional write operation.'],
              ].map(([flag, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-mono text-xs"><code className="text-aquilia-500">{flag}</code></td>
                  <td className="py-3 text-xs leading-relaxed">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Shield className="w-5 h-5 text-aquilia-500" />
          Quick Start Setup
        </h2>
        <p className={textClass}>
          To enable sessions, register the session integration and declare policies on your Workspace builder in <code className="text-aquilia-500">workspace.py</code>:
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[8, 12, 23, 27]}>{`from datetime import timedelta
from aquilia import Workspace
from aquilia.sessions import SessionPolicy, PersistencePolicy, ConcurrencyPolicy, TransportPolicy

# Configure the workspace with custom session policies
workspace = (
    Workspace("my-app")
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                idle_timeout=timedelta(hours=1),
                absolute_timeout=timedelta(days=30),
                rotate_on_use=False,
                rotate_on_privilege_change=True,
                fingerprint_binding=False,
                scope="user",
                persistence=PersistencePolicy(
                    enabled=True,
                    store_name="default",
                    write_through=True,
                    compress=False,
                ),
                concurrency=ConcurrencyPolicy(
                    max_sessions_per_principal=5,
                    behavior_on_limit="evict_oldest",
                ),
                transport=TransportPolicy(
                    cookie_name="workspace_session",
                    cookie_secure=False,
                    cookie_httponly=True,
                    cookie_samesite="lax",
                ),
            ),
        ],
    )
    .build()
)`}</CodeBlock>

        <p className={textClass}>
          Inject and require sessions inside your controllers using decorators:
        </p>
        <CodeBlock language="python" filename="controllers.py" highlightLines={[9, 15]}>{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session

class ShoppingController(Controller):
    prefix = "/shop"

    @Get("/cart")
    @session.require()
    async def view_cart(self, ctx, session: Session):
        """Require an existing session."""
        return ctx.json({"items": session.get("cart", [])})

    @Post("/cart")
    @session.ensure()
    async def add_item(self, ctx, session: Session):
        """Creates session if missing, then writes item."""
        body = await ctx.request.json()
        cart = session.get("cart", [])
        cart.append(body)
        session["cart"] = cart # Triggers dirty state
        return ctx.json({"cart": cart})`}</CodeBlock>
      </section>

      {/* Next Steps */}
      <NextSteps />
    </div>
  )
}
