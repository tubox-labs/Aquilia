import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Zap className="w-4 h-4" />
          Sessions / Engine
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            SessionEngine
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionEngine</code> is the central orchestrator for all session operations. It manages the full lifecycle of sessions through a deterministic 7-phase pipeline, handles concurrency control, session rotation, cleanup, and provides an event-based observability system.
        </p>
      </div>

      {/* Constructor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating the Engine</h2>
        <CodeBlock language="python" filename="engine_setup.py">{`from aquilia.sessions import (
    SessionEngine, SessionPolicy, SessionPolicyBuilder,
    MemoryStore, FileStore,
    CookieTransport, HeaderTransport,
)

# The engine wires together policies, stores, and transports
engine = SessionEngine(
    policies={
        "web": SessionPolicyBuilder("web")
            .lasting(hours=2)
            .idle_timeout(minutes=30)
            .rotating_on_auth()
            .web_defaults()
            .build(),
        "api": SessionPolicyBuilder("api")
            .lasting(hours=24)
            .api_defaults()
            .build(),
    },
    stores={
        "memory": MemoryStore.web_optimized(max_sessions=10_000),
        "file": FileStore(directory="/var/sessions"),
    },
    transports={
        "cookie": CookieTransport.for_web_browsers(domain="example.com"),
        "header": HeaderTransport.for_rest_apis(),
    },
    default_policy="web",
    default_store="memory",
    default_transport="cookie",
)`}</CodeBlock>
      </section>

      {/* 7-Phase Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7-Phase Lifecycle</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Every request that touches sessions passes through these 7 phases in order. Each phase is a discrete async operation that can emit events:
        </p>

        {[
          {
            phase: '1', name: 'Detection', detail: 'The transport layer inspects the incoming request (cookies or headers) to extract a session ID. If no ID is found, this phase returns None, signaling that a new session should be created.',
            code: `# Internally:
session_id = await transport.extract(request)
# Returns SessionID or None`
          },
          {
            phase: '2', name: 'Resolution', detail: 'If a session ID was detected, the engine loads the session data from the configured store. If the session is not found (expired, evicted), the engine creates a fresh session.',
            code: `# Internally:
if session_id:
    session = await store.load(session_id)
    if session is None:
        session = Session(id=SessionID.generate(), data={})
        await self._emit_event("session.created", session)
else:
    session = Session(id=SessionID.generate(), data={})
    await self._emit_event("session.created", session)`
          },
          {
            phase: '3', name: 'Validation', detail: 'The engine checks the session against the active policy — expiry, idle timeout, principal consistency, and scope requirements. Invalid sessions are destroyed and replaced.',
            code: `# Internally:
if session.is_expired:
    await self._emit_event("session.expired", session)
    raise SessionExpiredFault(session.id)

if policy.idle_timeout and session.idle_duration > policy.idle_timeout:
    await self._emit_event("session.idle_timeout", session)
    raise SessionIdleTimeoutFault(session.id)`
          },
          {
            phase: '4', name: 'Binding', detail: 'The validated session is attached to the request context, making it available to controllers and middleware via ctx.session or DI injection.',
            code: `# Internally:
request.state.session = session
# Now accessible as ctx.session in handlers`
          },
          {
            phase: '5', name: 'Mutation', detail: 'The handler modifies session data. All changes are tracked via the session\'s dirty flag. No I/O occurs during this phase — changes are batched.',
            code: `# In your handler:
session["cart"].append(item)      # session._dirty = True
session["last_page"] = "/checkout"  # session._dirty = True`
          },
          {
            phase: '6', name: 'Commit', detail: 'After the handler returns, if the session is dirty, the engine persists it to the store. If rotation is configured (e.g., after authentication), the session ID is regenerated.',
            code: `# Internally:
if session._dirty:
    if policy.rotate_on_use:
        old_id = session.id
        session.id = SessionID.generate()
        await store.delete(old_id)
        await self._emit_event("session.rotated", session, old_id)
    
    session.version += 1
    await store.save(session)
    await self._emit_event("session.committed", session)`
          },
          {
            phase: '7', name: 'Emission', detail: 'The transport layer injects the (possibly new) session ID into the outgoing response — as a Set-Cookie header or a custom response header.',
            code: `# Internally:
await transport.inject(response, session.id)
# Sets: Set-Cookie: aq_session=sess_...; HttpOnly; Secure; SameSite=Lax`
          },
        ].map((item, i) => (
          <div key={i} className={`mb-6 ${boxClass}`}>
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-aquilia-500/20 flex items-center justify-center">
                <span className="text-aquilia-500 font-bold text-sm">{item.phase}</span>
              </div>
              <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</h3>
            </div>
            <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.detail}</p>
            <CodeBlock language="python">{item.code}</CodeBlock>
          </div>
        ))}
      </section>

      {/* Resolve / Commit / Destroy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Methods</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>resolve()</h3>
        <CodeBlock language="python" filename="resolve.py">{`# Resolve loads or creates a session for the current request
session = await engine.resolve(request, policy_name="web")

# With explicit transport override:
session = await engine.resolve(
    request, 
    policy_name="api",
    transport_name="header",
    store_name="memory",
)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>commit()</h3>
        <CodeBlock language="python" filename="commit.py">{`# Commit persists dirty sessions and emits the session ID
await engine.commit(session, response)

# Force commit even if not dirty:
await engine.commit(session, response, force=True)

# With rotation:
await engine.commit(session, response, rotate=True)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>destroy()</h3>
        <CodeBlock language="python" filename="destroy.py">{`# Destroy removes the session from the store and clears the transport
await engine.destroy(session, response)

# This:
# 1. Deletes session from store
# 2. Clears the cookie/header on the response
# 3. Emits "session.destroyed" event`}</CodeBlock>
      </section>

      {/* Concurrency */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Concurrency Control</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine enforces concurrency limits per principal (user). When a user exceeds the maximum allowed concurrent sessions, the engine applies the configured behavior:
        </p>
        <CodeBlock language="python" filename="concurrency.py">{`# Check concurrent sessions for a principal
await engine.check_concurrency(session, policy)

# Behaviors on limit:
# ConcurrencyPolicy.behavior_on_limit = "reject"  → raise SessionConcurrencyViolationFault
# ConcurrencyPolicy.behavior_on_limit = "evict"   → destroy oldest session
# ConcurrencyPolicy.behavior_on_limit = "ignore"   → allow (no enforcement)

# Example policy with concurrency:
policy = (
    SessionPolicyBuilder("strict")
    .max_concurrent(sessions=3, behavior="evict")
    .build()
)`}</CodeBlock>
      </section>

      {/* Event System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Event System</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine emits events at every lifecycle transition, enabling logging, metrics, and custom side-effects:
        </p>
        <CodeBlock language="python" filename="events.py">{`# Register event handlers
engine.on_event("session.created", async_handler)
engine.on_event("session.committed", async_handler)
engine.on_event("session.expired", async_handler)
engine.on_event("session.rotated", async_handler)
engine.on_event("session.destroyed", async_handler)
engine.on_event("session.idle_timeout", async_handler)

# Example: Log all session creations
async def log_creation(event_name, session, **kwargs):
    logger.info(f"New session: {session.id.hashed}")  # Hashed for security

engine.on_event("session.created", log_creation)

# Example: Emit metrics on rotation
async def track_rotation(event_name, session, old_id, **kwargs):
    metrics.increment("session.rotations")

engine.on_event("session.rotated", track_rotation)`}</CodeBlock>

        <div className={`mt-4 ${boxClass}`}>
          <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Available Events</h4>
          <div className={`overflow-x-auto`}>
            <table className="w-full text-sm">
              <thead>
                <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                  <th className="text-left py-2 pr-4 font-semibold">Event</th>
                  <th className="text-left py-2 font-semibold">Payload</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
                {[
                  ['session.created', 'session'],
                  ['session.committed', 'session'],
                  ['session.expired', 'session'],
                  ['session.idle_timeout', 'session'],
                  ['session.rotated', 'session, old_id'],
                  ['session.destroyed', 'session'],
                  ['session.concurrency_exceeded', 'session, principal'],
                ].map(([event, payload], i) => (
                  <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{event}</code></td>
                    <td className="py-2 text-xs">{payload}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Cleanup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session Cleanup</h2>
        <CodeBlock language="python" filename="cleanup.py">{`# Periodically clean up expired sessions from the store
removed_count = await engine.cleanup_expired()
print(f"Cleaned up {removed_count} expired sessions")

# Schedule periodic cleanup (e.g., every 5 minutes)
# In your workspace lifecycle:
from aquilia.lifecycle import on_startup

@on_startup
async def start_session_cleanup(app):
    import asyncio
    
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)  # 5 minutes
            count = await engine.cleanup_expired()
            if count:
                logger.info(f"Cleaned {count} expired sessions")
    
    asyncio.create_task(cleanup_loop())`}</CodeBlock>
      </section>

      {/* Observability */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Observability</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine never logs raw session IDs. Instead, it uses a one-way hash for security:
        </p>
        <CodeBlock language="python" filename="observability.py">{`from aquilia.sessions import SessionID

sid = SessionID.generate()
print(sid.hashed)  # "sha256:a1b2c3d4..." — safe for logs

# In engine logs:
# [INFO] Session resolved: sha256:a1b2c3d4 (policy=web, scope=USER)
# [INFO] Session committed: sha256:a1b2c3d4 (dirty=True, version=3)
# [WARN] Session expired: sha256:a1b2c3d4 (ttl=7200s, age=7201s)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
