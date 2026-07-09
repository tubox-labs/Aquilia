import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsEngine() {
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
          <Zap className="w-4 h-4" />
          Sessions / Engine
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            SessionEngine
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          The <DocTerm id="sessions.engine">SessionEngine</DocTerm> orchestrates the entire session lifecycle, running a deterministic 7-phase execution pipeline, validating timeouts, enforcing concurrency, and broadcasting events.
        </p>
      </div>

      {/* Creating the Engine */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>Creating the Engine</h2>
        <p className={textClass}>
          The engine binds a policy, a storage backend, and a transport adapter together. It is typically registered as a singleton in the dependency injection container.
        </p>
        <CodeBlock language="python" filename="engine_setup.py" highlightLines={[12, 16, 20]}>{`from aquilia.sessions import (
    SessionEngine, SessionPolicyBuilder,
    MemoryStore, CookieTransport
)

# 1. Build a policy
policy = (
    SessionPolicyBuilder()
    .web_defaults()  # Setup web defaults first
    .lasting(hours=2) # Customize values afterward
    .build()
)

# 2. Setup store and transport
store = MemoryStore.web_optimized()
transport = CookieTransport.for_web_browsers()

# 3. Instantiate the engine
engine = SessionEngine(
    policy=policy,
    store=store,
    transport=transport,
)`}</CodeBlock>
      </section>

      {/* 7-Phase Lifecycle - Timeline list instead of box cards */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Zap className="w-5 h-5 text-aquilia-500" />
          The 7-Phase Lifecycle
        </h2>
        <p className={textClass}>
          Every request is resolved and committed through a structured, multi-phase pipeline in the session middleware:
        </p>

        <div className="space-y-12 relative pl-6 border-l border-zinc-200 dark:border-zinc-800">
          {[
            {
              phase: '1',
              name: 'Detection',
              detail: 'The transport extracts the raw session ID string from cookies or headers.',
              code: `# Done automatically in resolve():\nsession_id_str = self.transport.extract(request)`
            },
            {
              phase: '2',
              name: 'Resolution',
              detail: 'Loads the session from the database/memory store. If absent, a fresh anonymous session is initialized.',
              code: `# Done automatically in resolve():\nsession = await self._load_existing(session_id, now, request)\nif not session:\n    session = await self._create_new(now, request)`
            },
            {
              phase: '3',
              name: 'Validation',
              detail: 'Validates expiration, idle timeouts, absolute timeouts, and IP/User-Agent fingerprints for security.',
              code: `# Enforces policies and aborts if invalid:\nis_valid, reason = self.policy.is_valid(session, now)\n# Deletes hijacked sessions immediately to protect users:\nif not session.verify_fingerprint(client_ip, user_agent):\n    await self.store.delete(session_id)\n    raise SessionFingerprintMismatchFault()`
            },
            {
              phase: '4',
              name: 'Binding',
              detail: 'Binds the session to the request state and registers it into the active DI container scope.',
              code: `# Binds session to both request state and RequestCtx:\nrequest.state["session"] = session\nawait container.register_instance(Session, session, scope="request")`
            },
            {
              phase: '5',
              name: 'Mutation',
              detail: 'Route handlers read/write to the session. Dirty tracking detects any dict changes.',
              code: `# Session data wraps modifications instantly:\nsession["theme"] = "dark" # Marks session._dirty = True`
            },
            {
              phase: '6',
              name: 'Commit',
              detail: 'Checks concurrency limits, rotates session IDs on login/privilege changes, and saves the data back to storage. Concurrency checks are verified BEFORE saving.',
              code: `# Runs in commit() during response rendering:\nif self.policy.should_rotate(session, privilege_changed):\n    session = await self._rotate_session(session, now)\nif privilege_changed and session.is_authenticated:\n    await self.check_concurrency(session)\nif self.policy.should_persist(session) and session.is_dirty:\n    await self.store.save(session)`
            },
            {
              phase: '7',
              name: 'Emission',
              detail: 'Injects the session ID back into response headers or sets the response cookie.',
              code: `# Modifies response headers/cookies before sending:\nself.transport.inject(response, session)`
            },
          ].map((item, i) => (
            <div key={i} className="relative">
              {/* Dot */}
              <div className="absolute -left-[37px] top-1 w-5 h-5 rounded-full bg-zinc-100 dark:bg-zinc-900 border-2 border-aquilia-500 flex items-center justify-center">
                <span className="text-aquilia-500 font-bold text-[10px]">{item.phase}</span>
              </div>
              <h3 className={`font-mono text-base font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>
                Phase {item.phase}: {item.name}
              </h3>
              <p className={`text-sm mb-3 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{item.detail}</p>
              <CodeBlock language="python">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* Core Methods */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Core Lifecycle APIs</h2>

        <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          resolve()
        </h3>
        <p className={textClass}>
          Resolves a session from the request context. This executes phases 1–4 of the lifecycle.
        </p>
        <CodeBlock language="python" filename="resolve.py">{`session = await engine.resolve(request, container)`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          commit()
        </h3>
        <p className={textClass}>
          Runs ID rotation, checks concurrency limits, and persists modifications. This executes phases 6–7.
        </p>
        <CodeBlock language="python" filename="commit.py">{`await engine.commit(session, response, privilege_changed=True)`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          destroy()
        </h3>
        <p className={textClass}>
          Wipes the session from store and deletes the cookie/header references.
        </p>
        <CodeBlock language="python" filename="destroy.py">{`await engine.destroy(session, response)`}</CodeBlock>
      </section>

      {/* Concurrency Control */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Concurrency Control</h2>
        <p className={textClass}>
          The engine queries active sessions from the store to check concurrency constraints.
          This check is executed <strong>before</strong> the session is saved during commit.
        </p>
        <CodeBlock language="python" filename="concurrency.py" highlightLines={[1, 5]}>{`await engine.check_concurrency(session)

# Governed by policy concurrency configurations:
# - ConcurrencyPolicy.behavior_on_limit = "reject"       # Raises SessionConcurrencyViolationFault
# - ConcurrencyPolicy.behavior_on_limit = "evict_oldest" # Automatically deletes oldest session
# - ConcurrencyPolicy.behavior_on_limit = "evict_all"    # Deletes all other active sessions for user`}</CodeBlock>
      </section>

      {/* Observability */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Observability &amp; Event Hooking</h2>
        <p className={textClass}>
          Observe session state changes by registering a callable event handler. The engine broadcasts events for loading, timeout, hijacking, rotation, and destruction:
        </p>
        <CodeBlock language="python" filename="observability.py" highlightLines={[4, 6]}>{`def my_observability_observer(event_data: dict):
    print(f"Session Event: {event_data['event']} (Policy={event_data['policy']})")

engine.on_event(my_observability_observer)

# Sample event payload:
# {
#     "event": "session_rotated",
#     "timestamp": "2026-07-09T18:30:15Z",
#     "policy": "web",
#     "session_id_hash": "sha256:d8a5e3c7...",
#     "scope": "user",
#     "authenticated": True,
#     "principal": {"kind": "user", "id": "user_42"},
#     "request_path": "/auth/refresh",
#     "request_method": "POST",
#     "client_ip": "127.0.0.1"
# }`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
