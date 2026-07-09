import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareSession() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / SESSIONS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Session Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.SessionMiddleware">SessionMiddleware</DocTerm> orchestrates session state lifecycle binding per request. It handles token detection, DI container registration, user privilege rotation, and persistence sync.
        </p>
      </div>

      {/* Execution Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Session Lifecycle Stages</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          During request processing, the session middleware executes the following stages:
        </p>

        <div className="space-y-6 mb-8">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">1. Session Resolution</span>
            <p className="text-sm text-gray-400 mt-1">
              Extracts the session identifier using the transport backend, loads the session state from store (e.g. Memory, Redis), and validates integrity.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">2. State Binding</span>
            <p className="text-sm text-gray-400 mt-1">
              Stores the session in <code className="text-aquilia-300">request.state["session"]</code> and <code className="text-aquilia-300">ctx.session</code>, and registers the class <code className="text-aquilia-300">Session</code> inside the request-scoped DI container.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">3. Concurrency Checks</span>
            <p className="text-sm text-gray-400 mt-1">
              If the session is authenticated, verifies active session counts against policy limits (evicting older sessions or blocking the login).
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">4. Privilege Change &amp; Rotation</span>
            <p className="text-sm text-gray-400 mt-1">
              Tracks changes in authentication states during controller execution. If a login or logout occurs, the middleware triggers session identifier rotation to defend against session fixation attacks.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">5. Commit &amp; Sync</span>
            <p className="text-sm text-gray-400 mt-1">
              Saves updated variables to the session store and appends updated transport cookies/headers to the outgoing response.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Wiring Session Middleware</h2>
        <CodeBlock language="python" filename="session_setup.py" highlightLines={[6, 9, 10]}>{`from aquilia.sessions import SessionEngine, MemoryStore, CookieTransport, SessionPolicy
from aquilia.middleware_ext import SessionMiddleware, create_session_middleware

engine = SessionEngine(
    policy=SessionPolicy(max_age=3600),
    store=MemoryStore(),
    transport=CookieTransport()
)

# Option A: Direct registration
server.middleware(SessionMiddleware(session_engine=engine))

# Option B: Optional session middleware (gracefully handles missing engine)
server.middleware(create_session_middleware(session_engine=engine, optional=True))`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/request-scope" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Request Scope
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
