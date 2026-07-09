import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsFaults() {
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
          <AlertTriangle className="w-4 h-4" />
          Sessions / Faults
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Faults
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          All session errors are structured faults belonging to the <code className="text-aquilia-500">SECURITY</code> domain. 
          They provide precise status codes, severity indicators, and privacy-safe parameters.
        </p>
      </div>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionFault Hierarchy</h2>
        <CodeBlock language="python" filename="hierarchy.py" highlightLines={[1, 7, 8, 14, 15]}>{`SessionFault (base class)
├── SessionExpiredFault          # Session TTL duration has expired
├── SessionIdleTimeoutFault      # Session inactive too long
├── SessionAbsoluteTimeoutFault  # Absolute total session lifetime reached
├── SessionInvalidFault          # Session ID is malformed or invalid
├── SessionNotFoundFault         # Session ID not found in storage
├── SessionPolicyViolationFault  # Custom policy/guard check failed
├── SessionConcurrencyViolationFault  # Max concurrent sessions exceeded
├── SessionLockedFault           # Session is locked in transaction
├── SessionStoreUnavailableFault # Persistent store is unreachable
├── SessionStoreCorruptedFault   # Session data is corrupted
├── SessionRotationFailedFault   # Session ID rotation failed
├── SessionTransportFault        # HTTP transport extraction error
├── SessionForgeryAttemptFault   # Malformed/traversing ID token format
└── SessionHijackAttemptFault    # Fingerprint mismatch (IP/UA mismatch)`}</CodeBlock>
      </section>

      {/* Each Fault - Clean list instead of box cards */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Fault Registry Reference</h2>
        <p className={textClass}>
          The session subsystem throws these structured faults. Each has a specific default HTTP code, severity, and retryable flag:
        </p>
        <div className="space-y-6">
          {[
            { id: 'sessions.expired_fault', name: 'SessionExpiredFault', http: 401, desc: 'The session has exceeded its TTL (time-to-live). The client should re-authenticate.', severity: 'WARN', retryable: false },
            { id: 'sessions.idle_timeout_fault', name: 'SessionIdleTimeoutFault', http: 401, desc: 'The session has remained inactive longer than the policy allows. Common in admin panels.', severity: 'WARN', retryable: false },
            { id: 'sessions.absolute_timeout_fault', name: 'SessionAbsoluteTimeoutFault', http: 401, desc: 'Session total lifetime exceeded the maximum allowed limit, forcing re-login (OWASP compliant).', severity: 'WARN', retryable: false },
            { name: 'SessionInvalidFault', http: 400, desc: 'The session ID string contains invalid length or characters, violating entropy bounds.', severity: 'ERROR', retryable: false },
            { name: 'SessionNotFoundFault', http: 404, desc: 'The session ID is structured correctly, but does not match any entry in active storage.', severity: 'WARN', retryable: false },
            { name: 'SessionPolicyViolationFault', http: 403, desc: 'A session policy check has failed (such as writing to a read-only session).', severity: 'ERROR', retryable: false },
            { id: 'sessions.concurrency_fault', name: 'SessionConcurrencyViolationFault', http: 409, desc: 'The principal has logged into more concurrent sessions than the policy allows.', severity: 'ERROR', retryable: false },
            { name: 'SessionLockedFault', http: 423, desc: 'The session is currently locked by a write transaction on another concurrent request.', severity: 'WARN', retryable: true },
            { name: 'SessionStoreUnavailableFault', http: 503, desc: 'The persistent store backend (Redis, File System, Database) is unreachable.', severity: 'ERROR', retryable: true },
            { name: 'SessionStoreCorruptedFault', http: 500, desc: 'Session data pulled from persistent storage is corrupted and fails JSON deserialization.', severity: 'ERROR', retryable: false },
            { name: 'SessionRotationFailedFault', http: 500, desc: 'A failure occurred during ID rotation (could not delete the old key or save the new key).', severity: 'ERROR', retryable: true },
            { name: 'SessionTransportFault', http: 500, desc: 'The transport layer failed to extract or inject session keys (unsupported adapter format).', severity: 'ERROR', retryable: false },
            { name: 'SessionForgeryAttemptFault', http: 403, desc: 'Tampered session ID detected (violating prefixing or size constraints).', severity: 'ERROR', retryable: false },
            { id: 'sessions.hijack_fault', name: 'SessionHijackAttemptFault', http: 403, desc: 'Session hijacking suspected due to client IP or User-Agent fingerprint mismatches.', severity: 'ERROR', retryable: false },
          ].map((item, i) => (
            <div key={i} className="pb-6 border-b border-zinc-100 dark:border-zinc-900/50 last:border-b-0">
              <div className="flex items-center gap-3 flex-wrap mb-2">
                <h3 className="font-mono text-sm font-bold">
                  {item.id ? <DocTerm id={item.id}>{item.name}</DocTerm> : <code className={isDark ? 'text-white' : 'text-gray-900'}>{item.name}</code>}
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">HTTP {item.http}</span>
                <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                  item.severity === 'CRITICAL' || item.severity === 'ERROR'
                    ? 'bg-red-500/10 text-red-500'
                    : 'bg-yellow-500/10 text-yellow-600'
                }`}>{item.severity}</span>
                {item.retryable && (
                  <span className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-500">RETRYABLE</span>
                )}
              </div>
              <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Handling Faults */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Handling Session Faults</h2>
        <p className={textClass}>
          Register fault handlers using the <code className="text-aquilia-500">@fault_handler</code> decorator. 
          <strong>Important:</strong> Exception objects do not store a reference to the <code className="text-aquilia-500">Session</code> object. 
          Use the request context (<code className="text-aquilia-500">ctx.session</code>) to fetch session details inside handlers.
        </p>
        <CodeBlock language="python" filename="handling.py" highlightLines={[10, 20, 27, 29]}>{`from aquilia.faults import fault_handler
from aquilia.sessions.faults import (
    SessionFault,
    SessionExpiredFault,
    SessionHijackAttemptFault,
    SessionStoreUnavailableFault,
)

# Catch generic session faults
@fault_handler(SessionFault)
async def handle_session_fault(ctx, fault):
    return ctx.json({
        "error": fault.message,
        "code": fault.code,
        "retryable": fault.retryable,
    }, status=fault.http_status)


# Catch specific fault (graceful redirect)
@fault_handler(SessionExpiredFault)
async def handle_expired(ctx, fault):
    return ctx.redirect("/login?reason=expired")


# Catch security hijacking fault (terminate user sessions)
@fault_handler(SessionHijackAttemptFault)
async def handle_hijack(ctx, fault):
    # Retrieve active session from RequestCtx (fault has no .session property)
    session = ctx.session
    
    if session and session.principal:
        # Delete user sessions to mitigate attack
        active_sessions = await ctx.store.list_by_principal(session.principal.id)
        for s in active_sessions:
            await ctx.store.delete(s.id)
            
    return ctx.json({"error": "Access denied"}, status=403)`}</CodeBlock>
      </section>

      {/* Fault Properties */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Fault Properties</h2>
        <p className={textClass}>
          Session faults expose standardized diagnostic attributes. Session IDs are automatically hashed to prevent leaking secret keys in server logging trails:
        </p>
        <CodeBlock language="python" filename="properties.py" highlightLines={[6, 9, 13]}>{`from aquilia.sessions.faults import SessionExpiredFault

fault = SessionExpiredFault(session_id="sess_ABC123...")

# Inherited from Fault:
print(fault.message)        # "Session has expired"
print(fault.domain)         # FaultDomain.SECURITY
print(fault.severity)       # Severity.WARN
print(fault.public)         # True (safe to return to browser)
print(fault.retryable)      # False
print(fault.http_status)    # 401

# Session-specific properties:
print(fault.session_id_hash) # Hashed ID: "sha256:f124c..." (for safe logging)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
