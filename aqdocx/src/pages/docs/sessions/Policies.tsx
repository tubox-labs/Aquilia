import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsPolicies() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          Sessions / Policies
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Policies
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A <code className="text-aquilia-500">SessionPolicy</code> defines the complete security and behavioral configuration for a session — TTL, idle timeouts, rotation rules, persistence, concurrency limits, and transport settings. Policies are composable via sub-policies and can be built using the fluent <code className="text-aquilia-500">SessionPolicyBuilder</code>.
        </p>
      </div>

      {/* SessionPolicy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionPolicy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionPolicy</code> is a frozen dataclass containing all session configuration:
        </p>
        <CodeBlock language="python" filename="policy.py">{`from aquilia.sessions import SessionPolicy, SessionScope
from datetime import timedelta

policy = SessionPolicy(
    name="web",
    ttl=timedelta(hours=2),              # Session expires after 2 hours
    idle_timeout=timedelta(minutes=30),   # Expire if idle for 30 minutes
    rotate_on_use=False,                  # Don't rotate ID on every request
    rotate_on_privilege_change=True,      # Rotate ID on login/logout
    scope=SessionScope.USER,              # User-scoped sessions
    
    # Sub-policies
    persistence=PersistencePolicy(
        enabled=True,
        store_name="memory",
        write_through=False,
        compress=False,
    ),
    concurrency=ConcurrencyPolicy(
        max_sessions_per_principal=5,
        behavior_on_limit="evict",        # "evict" | "reject" | "ignore"
    ),
    transport=TransportPolicy(
        adapter="cookie",
        cookie_name="aq_session",
        cookie_path="/",
        cookie_httponly=True,
        cookie_secure=True,
        cookie_samesite="lax",
        header_name="X-Session-ID",
    ),
)`}</CodeBlock>
      </section>

      {/* Sub-Policies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Sub-Policies</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>PersistencePolicy</h3>
        <div className={`overflow-x-auto mb-6 ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Field</th>
                <th className="text-left py-2 pr-4 font-semibold">Type</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['enabled', 'bool', 'Whether sessions are persisted to a store'],
                ['store_name', 'str', 'Name of the store backend to use'],
                ['write_through', 'bool', 'Write to store on every mutation (not just commit)'],
                ['compress', 'bool', 'Compress session data before storing'],
              ].map(([field, type, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{field}</code></td>
                  <td className="py-2 pr-4 text-xs"><code>{type}</code></td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>ConcurrencyPolicy</h3>
        <div className={`overflow-x-auto mb-6 ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Field</th>
                <th className="text-left py-2 pr-4 font-semibold">Type</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['max_sessions_per_principal', 'int', 'Maximum concurrent sessions per user'],
                ['behavior_on_limit', 'str', '"evict" oldest, "reject" new, or "ignore"'],
              ].map(([field, type, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{field}</code></td>
                  <td className="py-2 pr-4 text-xs"><code>{type}</code></td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>TransportPolicy</h3>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Field</th>
                <th className="text-left py-2 pr-4 font-semibold">Type</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['adapter', 'str', '"cookie" or "header"'],
                ['cookie_name', 'str', 'Cookie name (default: "aq_session")'],
                ['cookie_path', 'str', 'Cookie path (default: "/")'],
                ['cookie_httponly', 'bool', 'HttpOnly flag (default: True)'],
                ['cookie_secure', 'bool', 'Secure flag (default: True)'],
                ['cookie_samesite', 'str', '"strict", "lax", or "none"'],
                ['header_name', 'str', 'Header name for header transport'],
              ].map(([field, type, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{field}</code></td>
                  <td className="py-2 pr-4 text-xs"><code>{type}</code></td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SessionPolicyBuilder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionPolicyBuilder</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The fluent builder makes it easy to compose policies without constructing deeply nested dataclasses:
        </p>
        <CodeBlock language="python" filename="builder.py">{`from aquilia.sessions import SessionPolicyBuilder

# Web application policy
web_policy = (
    SessionPolicyBuilder("web")
    .lasting(hours=2)                    # TTL
    .idle_timeout(minutes=30)            # Idle timeout
    .rotating_on_auth()                  # Rotate ID on login/logout
    .rotating_on_use()                   # Rotate ID every request (paranoid)
    .scoped_to("user")                   # SessionScope.USER
    .max_concurrent(sessions=5, behavior="evict")
    .web_defaults()                      # Cookie: HttpOnly, Secure, SameSite=Lax
    .build()
)

# API token policy
api_policy = (
    SessionPolicyBuilder("api")
    .lasting(hours=24)
    .idle_timeout(hours=1)
    .scoped_to("user")
    .api_defaults()                      # Header-based transport
    .build()
)

# Mobile application policy
mobile_policy = (
    SessionPolicyBuilder("mobile")
    .lasting(days=30)
    .idle_timeout(days=7)
    .rotating_on_auth()
    .scoped_to("device")
    .mobile_defaults()                   # Long-lived, device-scoped
    .build()
)

# Admin panel policy (strict)
admin_policy = (
    SessionPolicyBuilder("admin")
    .lasting(minutes=30)
    .idle_timeout(minutes=10)
    .rotating_on_auth()
    .rotating_on_use()
    .max_concurrent(sessions=1, behavior="reject")
    .admin_defaults()                    # Strictest settings
    .build()
)`}</CodeBlock>
      </section>

      {/* Builder Methods Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Builder Methods Reference</h2>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Method</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['.named(name)', 'Set the policy name'],
                ['.lasting(**kwargs)', 'Set TTL via timedelta kwargs (hours=, minutes=, days=)'],
                ['.idle_timeout(**kwargs)', 'Set idle timeout via timedelta kwargs'],
                ['.rotating_on_auth()', 'Enable rotation on privilege change'],
                ['.rotating_on_use()', 'Enable rotation on every request'],
                ['.scoped_to(scope)', 'Set session scope: "request", "connection", "user", "device"'],
                ['.max_concurrent(sessions, behavior)', 'Set concurrency limits and behavior'],
                ['.web_defaults()', 'Apply web browser defaults (cookie transport, secure flags)'],
                ['.api_defaults()', 'Apply API defaults (header transport)'],
                ['.mobile_defaults()', 'Apply mobile defaults (long TTL, device scope)'],
                ['.admin_defaults()', 'Apply admin defaults (short TTL, strict rotation)'],
                ['.build()', 'Finalize and return the SessionPolicy'],
              ].map(([method, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{method}</code></td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Built-in Policies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Policies</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia ships with pre-configured policies for common use cases:
        </p>
        <CodeBlock language="python" filename="builtins.py">{`from aquilia.sessions.policy import (
    DEFAULT_USER_POLICY,   # 2h TTL, 30min idle, cookie transport
    API_TOKEN_POLICY,      # 24h TTL, 1h idle, header transport
    EPHEMERAL_POLICY,      # Request-scoped, no persistence
)

# Use directly:
engine = SessionEngine(
    policies={
        "web": DEFAULT_USER_POLICY,
        "api": API_TOKEN_POLICY,
        "temp": EPHEMERAL_POLICY,
    },
    # ...
)`}</CodeBlock>
      </section>

      {/* Multiple Policies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Using Multiple Policies</h2>
        <CodeBlock language="python" filename="multi_policy.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session


class PublicController(Controller):
    prefix = "/public"

    @Get("/")
    @session.ensure(policy="web")  # Use web policy (cookie, 2h TTL)
    async def index(self, ctx, session):
        return ctx.json({"theme": session.get("theme", "light")})


class APIController(Controller):
    prefix = "/api/v1"

    @Get("/data")
    @session.require(policy="api")  # Use API policy (header, 24h TTL)
    async def get_data(self, ctx, session):
        return ctx.json({"user": session.principal.id})`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
