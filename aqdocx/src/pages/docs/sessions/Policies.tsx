import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsPolicies() {
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
          <Settings className="w-4 h-4" />
          Sessions / Policies
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Policies
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          A <DocTerm id="sessions.policy">SessionPolicy</DocTerm> defines the rules that govern session lifetimes, timeouts, rotation, concurrency, persistence, and network transport details.
        </p>
      </div>

      {/* SessionPolicy */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionPolicy Data Class</h2>
        <p className={textClass}>
          The policy is constructed using three sub-policies: <DocTerm id="sessions.policy">PersistencePolicy</DocTerm>, <DocTerm id="sessions.policy">ConcurrencyPolicy</DocTerm>, and <DocTerm id="sessions.policy">TransportPolicy</DocTerm>.
        </p>
        <CodeBlock language="python" filename="policy.py" highlightLines={[3, 49, 55, 59]}>{`from datetime import timedelta
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
        <h2 className={sectionHeaderClass}>SessionPolicyBuilder (Fluent Interface)</h2>
        <p className={textClass}>
          Use the fluent builder <DocTerm id="sessions.policy_builder">SessionPolicyBuilder</DocTerm> to construct policies. 
          <strong>Important:</strong> Call preset defaults first (such as <code className="text-aquilia-500">.web_defaults()</code> or <code className="text-aquilia-500">.admin_defaults()</code>), 
          then chain your overrides. Calling presets at the end of the chain will override your custom values.
        </p>
        <CodeBlock language="python" filename="builder.py" highlightLines={[4, 5, 12, 13, 20, 21]}>{`from aquilia.sessions import SessionPolicyBuilder

# Web application policy (Web defaults, custom TTL overrides)
web_policy = (
    SessionPolicyBuilder()
    .web_defaults()  # Loads web defaults first
    .lasting(hours=2) # Then overrides lasting TTL
    .idle_timeout(minutes=30)
    .build()
)

# API token policy (Header transport defaults, extended lasting time)
api_policy = (
    SessionPolicyBuilder()
    .api_defaults()  # Loads API defaults first
    .lasting(hours=24) # Customize afterward
    .build()
)

# Admin policy (Strict single-session limit, rotated on use, fingerprint bound)
admin_policy = (
    SessionPolicyBuilder()
    .admin_defaults()  # Setup strict admin defaults first
    .lasting(hours=8)  # Customize properties next
    .idle_timeout(minutes=15)
    .absolute_timeout(hours=12)
    .rotating_on_use()
    .with_fingerprint_binding()
    .max_concurrent(1)
    .build()
)`}</CodeBlock>
      </section>

      {/* Builder Methods Reference - Clean Table */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>Builder Methods Reference</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Method</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['.named(name: str)', 'Sets the unique policy registration identifier name.'],
                ['.lasting(days=None, hours=None, minutes=None)', 'Configures the session time-to-live (TTL).'],
                ['.idle_timeout(hours=None, minutes=None, days=None)', 'Configures the idle inactivity expiration timeout window.'],
                ['.no_idle_timeout()', 'Disables the idle expiration checks.'],
                ['.absolute_timeout(hours=None, minutes=None, days=None)', 'Sets the absolute maximum session lifetime (OWASP compliance).'],
                ['.with_fingerprint_binding()', 'Enables IP + User-Agent fingerprint binding for hijack detection.'],
                ['.rotating_on_auth()', 'Forces session ID rotation whenever authentication state changes.'],
                ['.rotating_on_use()', 'Forces session ID rotation on every incoming request.'],
                ['.scoped_to(scope: str)', 'Binds the session to a SessionScope enum value.'],
                ['.max_concurrent(limit: int)', 'Sets the concurrent active session limits per user principal.'],
                ['.unlimited_concurrent()', 'Disables concurrency constraints.'],
                ['.web_defaults()', 'Web defaults: Named web_session, lasts 7 days, 2h idle, max 5 concurrent.'],
                ['.api_defaults()', 'API defaults: Named api_session, lasts 1 hour, header adapter, unlimited concurrent.'],
                ['.mobile_defaults()', 'Mobile defaults: Named mobile_session, lasts 90 days, 30d idle, max 3 concurrent.'],
                ['.admin_defaults()', 'Admin defaults: Named admin_session, lasts 8h, 15m idle, 12h absolute, fingerprint, max 1 concurrent.'],
                ['.build()', 'Constructs and returns the finalized SessionPolicy object.'],
              ].map(([method, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-mono text-xs"><code className="text-aquilia-500">{method}</code></td>
                  <td className="py-3 text-xs leading-relaxed">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Built-in Policies */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Built-in Policy Presets</h2>
        <p className={textClass}>
          Aquilia exports pre-configured policies to handle standard development, API, and administrative session constraints:
        </p>
        <CodeBlock language="python" filename="builtins.py" highlightLines={[2, 3, 4, 5]}>{`from aquilia.sessions.policy import (
    DEFAULT_USER_POLICY,   # 7d TTL, 30m idle, cookie transport, max 5 concurrent
    API_TOKEN_POLICY,      # 1h TTL, no idle, header transport ("X-API-Token")
    EPHEMERAL_POLICY,      # Request-scoped, persistence disabled, cookie transport
    ADMIN_POLICY,          # 8h TTL, 15m idle, 12h absolute, fingerprint, max 1 concurrent
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
