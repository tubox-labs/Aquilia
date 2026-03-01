import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <AlertTriangle className="w-4 h-4" />
          Sessions / Faults
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Faults
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All session errors are structured faults in the <code className="text-aquilia-500">SECURITY</code> domain. Each fault type represents a specific failure mode, making it easy to build precise error handlers and observability.
        </p>
      </div>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Hierarchy</h2>
        <CodeBlock language="python" filename="hierarchy.py">{`SessionFault (base)
├── SessionExpiredFault          # Session TTL exceeded
├── SessionIdleTimeoutFault      # Session idle too long
├── SessionInvalidFault          # Session data is malformed
├── SessionNotFoundFault         # Session ID not in store
├── SessionPolicyViolationFault  # Policy constraint violated
├── SessionConcurrencyViolationFault  # Too many concurrent sessions
├── SessionLockedFault           # Session is locked by another request
├── SessionStoreUnavailableFault # Store backend is unreachable
├── SessionStoreCorruptedFault   # Store data is corrupted
├── SessionRotationFailedFault   # Session ID rotation failed
├── SessionTransportFault        # Transport layer error
├── SessionForgeryAttemptFault   # Forged session ID detected
└── SessionHijackAttemptFault    # Session hijacking detected`}</CodeBlock>
      </section>

      {/* Each Fault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Reference</h2>
        <div className="space-y-3">
          {[
            { name: 'SessionExpiredFault', http: 401, desc: 'The session has exceeded its TTL (time-to-live). The client should re-authenticate.', severity: 'WARN', retryable: false },
            { name: 'SessionIdleTimeoutFault', http: 401, desc: 'The session has been idle longer than the policy allows. Common with admin panels and banking apps.', severity: 'WARN', retryable: false },
            { name: 'SessionInvalidFault', http: 400, desc: 'The session data is malformed, missing required fields, or structurally invalid.', severity: 'ERROR', retryable: false },
            { name: 'SessionNotFoundFault', http: 404, desc: 'The session ID is valid in format but not found in the store (evicted, manually deleted, or wrong store).', severity: 'WARN', retryable: true },
            { name: 'SessionPolicyViolationFault', http: 403, desc: 'A guard or policy check failed — insufficient permissions, wrong role, or custom policy constraint.', severity: 'WARN', retryable: false },
            { name: 'SessionConcurrencyViolationFault', http: 429, desc: 'The user has exceeded the maximum allowed concurrent sessions. The oldest session may be evicted.', severity: 'WARN', retryable: true },
            { name: 'SessionLockedFault', http: 423, desc: 'The session is locked by another concurrent request. Try again after the lock is released.', severity: 'WARN', retryable: true },
            { name: 'SessionStoreUnavailableFault', http: 503, desc: 'The session store backend (Redis, database, filesystem) is unreachable.', severity: 'CRITICAL', retryable: true },
            { name: 'SessionStoreCorruptedFault', http: 500, desc: 'The session data in the store is corrupted and cannot be deserialized.', severity: 'CRITICAL', retryable: false },
            { name: 'SessionRotationFailedFault', http: 500, desc: 'Failed to rotate the session ID — the new ID could not be saved or the old ID could not be deleted.', severity: 'ERROR', retryable: true },
            { name: 'SessionTransportFault', http: 500, desc: 'The transport layer failed to extract or inject the session ID (malformed cookie, missing header).', severity: 'ERROR', retryable: false },
            { name: 'SessionForgeryAttemptFault', http: 403, desc: 'A forged or tampered session ID was detected — entropy validation failed or signature mismatch.', severity: 'CRITICAL', retryable: false },
            { name: 'SessionHijackAttemptFault', http: 403, desc: 'Session hijacking detected — the session is being used from a different IP, device, or user-agent than expected.', severity: 'CRITICAL', retryable: false },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-3 flex-wrap">
                <code className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</code>
                <span className="text-xs px-2 py-0.5 rounded-full bg-aquilia-500/10 text-aquilia-500">HTTP {item.http}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  item.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400' :
                  item.severity === 'ERROR' ? 'bg-orange-500/10 text-orange-400' :
                  'bg-yellow-500/10 text-yellow-400'
                }`}>{item.severity}</span>
                {item.retryable && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">RETRYABLE</span>
                )}
              </div>
              <p className={`text-sm mt-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Handling Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Handling Session Faults</h2>
        <CodeBlock language="python" filename="handling.py">{`from aquilia.faults import fault_handler
from aquilia.sessions.faults import (
    SessionFault,
    SessionExpiredFault,
    SessionForgeryAttemptFault,
    SessionHijackAttemptFault,
    SessionStoreUnavailableFault,
)


# Catch all session faults
@fault_handler(SessionFault)
async def handle_session_fault(ctx, fault):
    return ctx.json({
        "error": fault.message,
        "fault_type": type(fault).__name__,
        "retryable": fault.retryable,
    }, status=fault.http_status)


# Catch specific fault types
@fault_handler(SessionExpiredFault)
async def handle_expired(ctx, fault):
    """Redirect to login on expiry."""
    return ctx.redirect("/login?reason=expired")


# Security-critical faults
@fault_handler(SessionForgeryAttemptFault)
async def handle_forgery(ctx, fault):
    """Log and block forged sessions."""
    logger.critical(f"Session forgery attempt: {ctx.request.client.host}")
    # Optionally ban the IP
    return ctx.json({"error": "Forbidden"}, status=403)


@fault_handler(SessionHijackAttemptFault)
async def handle_hijack(ctx, fault):
    """Log and destroy all sessions for the principal."""
    logger.critical(f"Session hijack attempt detected")
    # Destroy all sessions for this user
    if fault.session and fault.session.principal:
        sessions = await store.find_by_principal(
            fault.session.principal.kind,
            fault.session.principal.id,
        )
        for s in sessions:
            await store.delete(s.id)
    return ctx.json({"error": "Forbidden"}, status=403)


# Infrastructure fault
@fault_handler(SessionStoreUnavailableFault)
async def handle_store_down(ctx, fault):
    """Graceful degradation when store is down."""
    logger.error(f"Session store unavailable: {fault.message}")
    # Optionally serve with degraded functionality
    return ctx.json({
        "error": "Service temporarily unavailable",
        "retryable": True,
    }, status=503)`}</CodeBlock>
      </section>

      {/* Fault Properties */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Properties</h2>
        <CodeBlock language="python" filename="properties.py">{`from aquilia.sessions.faults import SessionExpiredFault

fault = SessionExpiredFault(session_id="sess_...")

# Common properties (inherited from Fault):
fault.message        # Human-readable error message
fault.domain         # FaultDomain.SECURITY
fault.severity       # Severity.WARN / ERROR / CRITICAL
fault.public         # True — safe to show to user
fault.retryable      # True/False — should client retry?
fault.http_status    # HTTP status code (401, 403, 500, etc.)

# Session-specific properties:
fault.session_id     # The session ID involved (hashed in logs)
fault.policy_name    # The policy that was violated (if applicable)
fault.session        # The Session object (if available)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
