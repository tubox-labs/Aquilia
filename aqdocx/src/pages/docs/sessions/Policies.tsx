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
          A <code className="text-aquilia-500">SessionPolicy</code> defines the behavioral rules for a session. Policies govern expiration timeout windows, token rotation, multi-tenant persistence, concurrent principal session limits, and network transports.
        </p>
      </div>

      {/* SessionPolicy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionPolicy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionPolicy</code> is a frozen dataclass representing the full session configuration:
        </p>
        <CodeBlock language="python" filename="policy.py">{`from datetime import timedelta
from aquilia.sessions import SessionPolicy, PersistencePolicy, ConcurrencyPolicy, TransportPolicy

policy = SessionPolicy(
    name="web",
    ttl=timedelta(hours=2),
    idle_timeout=timedelta(minutes=30),
    absolute_timeout=timedelta(hours=12),
    rotate_on_use=False,
    rotate_on_privilege_change=True,
    fingerprint_binding=True,
    scope="user",
    
    # Sub-policies
    persistence=PersistencePolicy(
        enabled=True,
        store_name="default",
        write_through=True,
        compress=False,
    ),
    concurrency=ConcurrencyPolicy(
        max_sessions_per_principal=5,
        behavior_on_limit="evict_oldest", # "reject" | "evict_oldest" | "evict_all"
    ),
    transport=TransportPolicy(
        adapter="cookie",
        cookie_name="aquilia_session",
        cookie_httponly=True,
        cookie_secure=True,
        cookie_samesite="lax",
        cookie_path="/",
        header_name="X-Session-ID",
    ),
)`}</CodeBlock>
      </section>

      {/* SessionPolicyBuilder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionPolicyBuilder</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The fluent builder is used to construct <code className="text-aquilia-500">SessionPolicy</code> objects without manually defining nested sub-policy instances:
        </p>
        <CodeBlock language="python" filename="builder.py">{`from aquilia.sessions import SessionPolicyBuilder

# Web application policy
web_policy = (
    SessionPolicyBuilder()
    .named("web")
    .lasting(hours=2)
    .idle_timeout(minutes=30)
    .rotating_on_auth()
    .web_defaults() # applies standard cookie options
    .build()
)

# API token policy
api_policy = (
    SessionPolicyBuilder()
    .named("api")
    .lasting(hours=24)
    .api_defaults() # applies header adapter
    .build()
)

# Admin policy (strict, with fingerprint binding)
admin_policy = (
    SessionPolicyBuilder()
    .named("admin")
    .lasting(hours=8)
    .idle_timeout(minutes=15)
    .absolute_timeout(hours=12)
    .rotating_on_use()
    .with_fingerprint_binding()
    .max_concurrent(1)
    .admin_defaults()
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
                ['.named(name: str)', 'Set the policy name.'],
                ['.lasting(days=None, hours=None, minutes=None)', 'Set session TTL.'],
                ['.idle_timeout(days=None, hours=None, minutes=None)', 'Set idle timeout duration.'],
                ['.no_idle_timeout()', 'Disables idle timeouts.'],
                ['.absolute_timeout(days=None, hours=None, minutes=None)', 'Set absolute maximum session age.'],
                ['.with_fingerprint_binding()', 'Enable OWASP IP & User-Agent fingerprint binding.'],
                ['.rotating_on_auth()', 'Enables token ID rotation on privilege changes.'],
                ['.rotating_on_use()', 'Enables token ID rotation on every request.'],
                ['.scoped_to(scope: str)', 'Set session scope level.'],
                ['.max_concurrent(limit: int)', 'Set max concurrent sessions (applies evict_oldest on limit).'],
                ['.unlimited_concurrent()', 'Disable concurrency limits.'],
                ['.web_defaults()', 'Set named to web_session, lasts 7 days, max 5 concurrent.'],
                ['.api_defaults()', 'Set named to api_session, lasts 1 hour, header adapter, unlimited concurrent.'],
                ['.mobile_defaults()', 'Set named to mobile_session, lasts 90 days, max 3 concurrent.'],
                ['.admin_defaults()', 'Set named to admin_session, lasts 8 hours, absolute timeout 12 hours, rotate on use, fingerprint bound, max 1 concurrent.'],
                ['.build()', 'Build and return the final SessionPolicy.'],
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
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Policy Constants</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The following policies are pre-constructed and ready to use:
        </p>
        <CodeBlock language="python" filename="builtins.py">{`from aquilia.sessions.policy import (
    DEFAULT_USER_POLICY,   # 7d TTL, 30m idle, cookie transport, max 5 concurrent
    API_TOKEN_POLICY,      # 1h TTL, no idle, header transport ("X-API-Token")
    EPHEMERAL_POLICY,      # ephemeral scope, persistence disabled, cookie transport
    ADMIN_POLICY,          # 8h TTL, 15m idle, 12h absolute, fingerprint, max 1 concurrent
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
