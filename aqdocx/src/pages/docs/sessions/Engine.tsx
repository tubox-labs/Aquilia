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
          The <code className="text-aquilia-500">SessionEngine</code> is the central orchestrator for all session operations. It executes a 7-phase pipeline, manages session rotation and concurrency control, cleans up expired sessions, and runs an event-based observability system.
        </p>
      </div>

      {/* Constructor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating the Engine</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionEngine</code> wraps a single policy, a single store, and a single transport. It is registered as a singleton (application-scoped dependency).
        </p>
        <CodeBlock language="python" filename="engine_setup.py">{`from aquilia.sessions import (
    SessionEngine, SessionPolicyBuilder,
    MemoryStore, CookieTransport
)

# 1. Build policy
policy = (
    SessionPolicyBuilder()
    .named("web")
    .lasting(hours=2)
    .build()
)

# 2. Create store and transport
store = MemoryStore.web_optimized()
transport = CookieTransport.for_web_browsers()

# 3. Instantiate the engine
engine = SessionEngine(
    policy=policy,
    store=store,
    transport=transport,
)`}</CodeBlock>
      </section>

      {/* 7-Phase Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7-Phase Lifecycle</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine coordinates session state via the following pipeline during the request lifespan:
        </p>

        {[
          {
            phase: '1', name: 'Detection', detail: 'The transport extracts the session ID string from request headers or cookies.',
            code: `# Internally:
session_id_str = self.transport.extract(request)`
          },
          {
            phase: '2', name: 'Resolution', detail: 'The engine attempts to load the existing session from the store. If not found or invalid, it initializes a fresh Session instance.',
            code: `# Internally:
session = await self._load_existing(session_id, now, request)
if not session:
    session = await self._create_new(now, request)`
          },
          {
            phase: '3', name: 'Validation', detail: 'The engine validates parameters (idle timeout, absolute timeout, and client fingerprint bindings to prevent session hijacking).',
            code: `# Internally checks:
is_valid, reason = self.policy.is_valid(session, now)
# If fingerprint mismatch, deletes the hijacked session from store:
if not session.verify_fingerprint(client_ip, user_agent):
    await self.store.delete(session_id)
    raise SessionFingerprintMismatchFault()`
          },
          {
            phase: '4', name: 'Binding', detail: 'The resolved session is bound to the request state and the dependency injection context.',
            code: `# Bound request context:
request.state["session"] = session`
          },
          {
            phase: '5', name: 'Mutation', detail: 'The route handler reads or writes session data. Mutations are intercepted by the nested dictionary wrapper to track dirty state.',
            code: `# Inside handler:
session["cart"].append(new_item) # Sets session._dirty = True automatically`
          },
          {
            phase: '6', name: 'Commit', detail: 'If the session data was modified, the engine persists changes. ID rotation and concurrency limit validation occur BEFORE saving.',
            code: `# Internally checks:
if self.policy.should_rotate(session, privilege_changed):
    session = await self._rotate_session(session, now)

if privilege_changed and session.is_authenticated:
    await self.check_concurrency(session)

if self.policy.should_persist(session) and session.is_dirty:
    await self.store.save(session)`
          },
          {
            phase: '7', name: 'Emission', detail: 'The transport injects the session ID back into the HTTP response cookies or headers.',
            code: `# Internally:
self.transport.inject(response, session)`
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

      {/* Core Methods */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Methods</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>resolve()</h3>
        <p className={`mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Extracts and resolves the request session.
        </p>
        <CodeBlock language="python" filename="resolve.py">{`session = await engine.resolve(request, container)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>commit()</h3>
        <p className={`mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Saves modified data, verifies concurrency, and injects the session into the response headers/cookies.
        </p>
        <CodeBlock language="python" filename="commit.py">{`await engine.commit(session, response, privilege_changed=True)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>destroy()</h3>
        <p className={`mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Deletes the session from the backend store and removes cookies/headers from the HTTP client.
        </p>
        <CodeBlock language="python" filename="destroy.py">{`await engine.destroy(session, response)`}</CodeBlock>
      </section>

      {/* Concurrency */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Concurrency Control</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The engine validates concurrency constraints against active sessions from the store:
        </p>
        <CodeBlock language="python" filename="concurrency.py">{`# Asserts that the authenticated principal does not exceed policy limits
await engine.check_concurrency(session)

# Configured in builder:
# ConcurrencyPolicy.behavior_on_limit = "reject"          # raises SessionConcurrencyViolationFault
# ConcurrencyPolicy.behavior_on_limit = "evict_oldest"    # deletes the oldest session
# ConcurrencyPolicy.behavior_on_limit = "evict_all"       # deletes all other active sessions`}</CodeBlock>
      </section>

      {/* Observability */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Observability &amp; Events</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          You can register a single event handler that intercepts all session events (e.g. for structured logging or metrics aggregation):
        </p>
        <CodeBlock language="python" filename="observability.py">{`def my_event_handler(event_data: dict):
    print(f"Event: {event_data['event']} for session {event_data.get('session_id_hash')}")

engine.on_event(my_event_handler)

# Sample event data payload:
# {
#     "event": "session_rotated",
#     "timestamp": "2026-07-08T12:00:00Z",
#     "policy": "web",
#     "session_id_hash": "a1b2c3d4...",  # fingerprint hash
#     "scope": "user",
#     "authenticated": True,
#     "principal": {"kind": "user", "id": "42"},
#     "request_path": "/login",
#     "request_method": "POST"
# }`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
